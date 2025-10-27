"""
Backend API for Ilana Protocol Intelligence
Handles AI analysis using PubMedBERT, Pinecone, and Azure OpenAI
"""

import os
import json
import logging
import time
from typing import Dict, List, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from openai import AzureOpenAI
from pinecone import Pinecone
from protocol_intelligence_db import (
    get_phrase_suggestions, 
    categorize_reviewer_comment, 
    assess_feasibility_concerns
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Ilana Protocol Intelligence API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://zealous-dune-00e524d0f.3.azurestaticapps.net", "https://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "clinical-protocols")
PINECONE_HOST = os.getenv("PINECONE_HOST")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://protocol-talk.openai.azure.com/")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-deployment")
PUBMEDBERT_ENDPOINT_URL = os.getenv("PUBMEDBERT_ENDPOINT_URL", "https://usz78oxlybv4xfh2.eastus.azure.endpoints.huggingface.cloud")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Initialize Pinecone
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    if PINECONE_HOST:
        # For serverless indexes, specify the host
        index = pc.Index(PINECONE_INDEX_NAME, host=PINECONE_HOST)
    else:
        # For pod-based indexes
        index = pc.Index(PINECONE_INDEX_NAME)
    logger.info("Pinecone initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Pinecone: {e}")
    index = None

# Initialize Azure OpenAI
try:
    azure_client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version="2024-02-15-preview",
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    logger.info("Azure OpenAI initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Azure OpenAI: {e}")
    azure_client = None

class AnalysisRequest(BaseModel):
    text: str

class FeedbackRequest(BaseModel):
    finding_id: str
    action: str  # "accept", "ignore", "improve"
    user_feedback: str = ""
    protocol_text: str = ""

class Finding(BaseModel):
    id: str
    type: str
    severity: str
    title: str
    description: str
    citation: str
    location: Dict[str, int]
    suggestions: List[str]

class AnalysisResponse(BaseModel):
    scores: Dict[str, str]
    amendmentRisk: str
    findings: List[Finding]

# New models for Intelligent Authoring Assistant
class PhraseRequest(BaseModel):
    text: str
    context: str = "general"  # general, dosing, endpoints, etc.

class PhraseSuggestion(BaseModel):
    original: str
    suggestions: List[str]
    rationale: str
    category: str
    severity: str
    position: int

class CommentRequest(BaseModel):
    comment_text: str

class CommentCategory(BaseModel):
    category: str
    confidence: str
    suggested_actions: List[str]

class FeasibilityRequest(BaseModel):
    text: str

class FeasibilityConcern(BaseModel):
    type: str
    concern: str
    suggestions: List[str]
    position: int

class IntelligentSuggestionsResponse(BaseModel):
    phrase_suggestions: List[PhraseSuggestion]
    feasibility_concerns: List[FeasibilityConcern]
    regulatory_flags: List[str]

async def get_azure_openai_embeddings(text: str) -> List[float]:
    """Fallback: Get embeddings from Azure OpenAI"""
    try:
        if not azure_client:
            return []
            
        response = azure_client.embeddings.create(
            model="text-embedding-ada-002",  # Standard Azure OpenAI embedding model
            input=text[:8000]  # Azure OpenAI has higher token limit
        )
        
        if response.data and len(response.data) > 0:
            embedding = response.data[0].embedding
            # Pad or truncate to 768 dimensions to match Pinecone index
            if len(embedding) > 768:
                return embedding[:768]
            elif len(embedding) < 768:
                return embedding + [0.0] * (768 - len(embedding))
            return embedding
        return []
        
    except Exception as e:
        logger.error(f"Azure OpenAI embedding failed: {e}")
        return []

async def get_pubmedbert_embeddings(text: str) -> List[float]:
    """Get embeddings from PubMedBERT with Azure OpenAI fallback"""
    try:
        response = requests.post(
            PUBMEDBERT_ENDPOINT_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {HUGGINGFACE_API_KEY}"
            },
            json={"inputs": text[:512]},
            timeout=30
        )
        response.raise_for_status()
        
        # Handle different response formats
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], list):
                return result[0]  # [[embedding]] format
            return result  # [embedding] format
        elif isinstance(result, dict) and "embeddings" in result:
            return result["embeddings"]
        else:
            logger.error(f"Unexpected PubMedBERT response format: {result}")
            return []
            
    except Exception as e:
        logger.error(f"PubMedBERT embedding failed: {e}")
        logger.info("Falling back to Azure OpenAI embeddings...")
        return await get_azure_openai_embeddings(text)

async def query_pinecone(embeddings: List[float]) -> Dict:
    """Query Pinecone for similar protocols"""
    try:
        if not index or not embeddings:
            return {"matches": []}
            
        response = index.query(
            vector=embeddings,
            top_k=10,
            include_metadata=True
        )
        return response
    except Exception as e:
        logger.error(f"Pinecone query failed: {e}")
        return {"matches": []}

async def analyze_with_azure_openai(text: str, similar_findings: Dict) -> Dict:
    if not azure_client:
        logger.error("Azure OpenAI client not initialized")
        return {"error": "Azure OpenAI client not available"}
    """Analyze protocol with Azure OpenAI using RAG system"""
    try:
        # Extract relevant passages from similar findings
        retrieved_passages = []
        for i, match in enumerate(similar_findings.get('matches', [])[:6]):
            if hasattr(match, 'metadata') and match.metadata:
                retrieved_passages.append(f"{i+1}) [Source: {match.metadata.get('source', 'Unknown')}]: \"{match.metadata.get('text', '')}\"")
        
        passages_text = "\n".join(retrieved_passages) if retrieved_passages else "No similar protocols found in database."
        
        # Check if we have meaningful regulatory context
        has_regulatory_context = any("regulation" in p.lower() or "ich" in p.lower() or "fda" in p.lower() 
                                    for p in retrieved_passages)
        
        # Enhanced prompt with better scoring logic  
        context_note = "Note: Analysis based on clinical protocol best practices as limited regulatory guidance available." if not has_regulatory_context else ""
        
        prompt = f"""You are a clinical protocol compliance expert. Analyze the protocol text and provide intelligent, nuanced scoring.

PROTOCOL TEXT TO ANALYZE:
{text[:3000]}

SIMILAR PROTOCOLS IN DATABASE:
{passages_text}

{context_note}

INTELLIGENT SCORING CRITERIA (Give realistic scores, not always F):
- CLARITY (A-F): Structure, readability, definitions, methodology description
  A: Excellent clarity, all terms defined, methodology clear
  B: Good clarity with minor ambiguities  
  C: Adequate clarity but some unclear sections
  D: Poor clarity, multiple ambiguous sections
  F: Very poor clarity, difficult to understand

- REGULATORY (A-F): ICH-GCP and FDA compliance
  A: Full compliance with all requirements
  B: Minor compliance gaps that are easily fixed
  C: Some compliance issues requiring attention
  D: Major compliance gaps
  F: Significant non-compliance

- FEASIBILITY (A-F): Operational practicality
  A: Highly feasible design
  B: Generally feasible with minor challenges
  C: Moderate feasibility challenges
  D: Significant operational hurdles
  F: Impractical or unfeasible design

IMPORTANT: 
- Score based on actual protocol quality, not just presence of issues
- Well-written protocols should get A/B grades
- Only poorly written protocols should get D/F grades  
- Be realistic - most protocols are C or better
- Focus on substantial issues, not nitpicking

Respond in this exact JSON format:
{{
  "scores": {{
    "clarity": "A|B|C|D|F",
    "regulatory": "A|B|C|D|F", 
    "feasibility": "A|B|C|D|F"
  }},
  "amendmentRisk": "low|medium|high",
  "findings": [
    {{
      "id": "finding-001",
      "type": "compliance|feasibility|clarity",
      "severity": "high|medium|low",
      "title": "Issue Title",
      "description": "Specific issue description with actionable guidance",
      "citation": "Regulatory citation or best practice reference", 
      "location": {{"start": 0, "length": 50}},
      "suggestions": ["Specific improvement suggestion"],
      "quoted_text": "Relevant text from protocol if applicable",
      "evidence": "Supporting evidence or reasoning"
    }}
  ]
}}"""

        response = azure_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert clinical protocol compliance reviewer. Use only the evidence in retrieved passages. If passages don't provide evidence, say 'insufficient evidence'. Always include specific quotes and character positions."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=3000,
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        
        # Parse and validate the response
        try:
            # Clean up the content first
            content = content.strip()
            if not content:
                raise ValueError("Empty response from Azure OpenAI")
            
            # Remove any markdown code blocks if present
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
            result = json.loads(content)
            
            # Validate and clean up findings
            validated_findings = []
            for finding in result.get('findings', []):
                # More lenient validation - require at least title and description
                if finding.get('title') and finding.get('description'):
                    # Ensure required fields have defaults
                    finding.setdefault('quoted_text', '')
                    finding.setdefault('evidence', 'Analysis-based finding')
                    finding.setdefault('citation', 'Best practice guidance')
                    finding.setdefault('suggestions', ['Review and improve this section'])
                    
                    # Fix location coordinates if they're arrays
                    if 'location' in finding:
                        location = finding['location']
                        if isinstance(location.get('start'), list) and location['start']:
                            location['start'] = location['start'][0]
                        if isinstance(location.get('length'), list) and location['length']:
                            location['length'] = location['length'][0]
                    else:
                        finding['location'] = {'start': 0, 'length': 10}
                    
                    validated_findings.append(finding)
                    
            result['findings'] = validated_findings
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            logger.error(f"Raw content: {content[:500]}...")
            # Return a structured error response instead of crashing
            return {
                "scores": {
                    "clarity": "C",
                    "regulatory": "C", 
                    "feasibility": "C"
                },
                "amendmentRisk": "medium",
                "findings": [
                    {
                        "id": "json-parse-error",
                        "type": "compliance",
                        "severity": "medium",
                        "title": "Analysis Response Format Error",
                        "description": f"The AI analysis returned an incorrectly formatted response. This may be due to complex protocol content. Please retry with a shorter text or contact support.",
                        "citation": "Technical issue with response parsing",
                        "location": {"start": 0, "length": 10},
                        "suggestions": ["Try analyzing a shorter section of the protocol", "Contact support if issue persists"],
                        "quoted_text": "",
                        "evidence": f"JSON parsing failed: {str(e)}"
                    }
                ]
            }
        
    except Exception as e:
        logger.error(f"Azure OpenAI analysis failed: {e}")
        # Return empty findings if AI fails - no generic mock data
        return {
            "scores": {
                "clarity": "C",
                "regulatory": "C", 
                "feasibility": "C"
            },
            "amendmentRisk": "medium",
            "findings": [
                {
                    "id": "analysis-error",
                    "type": "compliance",
                    "severity": "medium",
                    "title": "Analysis Service Unavailable",
                    "description": f"Protocol analysis service is currently unavailable: {str(e)}. Please retry or consult regulatory counsel.",
                    "citation": "Manual review recommended when automated analysis fails",
                    "location": {"start": 0, "length": 10},
                    "suggestions": ["Retry analysis", "Consult regulatory expert"],
                    "quoted_text": "",
                    "evidence": "Service unavailable"
                }
            ]
        }

@app.get("/")
async def root():
    return {"message": "Ilana Protocol Intelligence API", "status": "running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "pinecone": index is not None,
        "azure_openai": azure_client is not None,
        "azure_openai_key": bool(AZURE_OPENAI_API_KEY),
        "pubmedbert": bool(PUBMEDBERT_ENDPOINT_URL)
    }

@app.post("/api/analyze-protocol", response_model=AnalysisResponse)
async def analyze_protocol(request: AnalysisRequest):
    """Main endpoint for protocol analysis"""
    try:
        logger.info(f"Analyzing protocol text of length: {len(request.text)}")
        
        # Step 1: Get embeddings from PubMedBERT
        embeddings = await get_pubmedbert_embeddings(request.text)
        logger.info(f"Got embeddings of length: {len(embeddings)}")
        
        # Step 2: Query Pinecone for similar protocols
        similar_findings = await query_pinecone(embeddings)
        logger.info(f"Found {len(similar_findings.get('matches', []))} similar protocols")
        
        # Step 3: Analyze with Azure OpenAI
        analysis = await analyze_with_azure_openai(request.text, similar_findings)
        logger.info("Analysis completed successfully")
        
        return AnalysisResponse(**analysis)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Collect user feedback to improve AI analysis"""
    try:
        logger.info(f"Received feedback: {request.action} for finding {request.finding_id}")
        
        # Store feedback for future model improvement
        feedback_data = {
            "timestamp": json.dumps({"$date": {"$numberLong": str(int(time.time() * 1000))}}),
            "finding_id": request.finding_id,
            "action": request.action,
            "user_feedback": request.user_feedback,
            "protocol_text_sample": request.protocol_text[:200] if request.protocol_text else ""
        }
        
        # Store in Pinecone as feedback vector for future learning
        if index and request.protocol_text:
            try:
                # Get embeddings for the feedback context
                embeddings = await get_pubmedbert_embeddings(request.user_feedback + " " + request.protocol_text[:500])
                
                # Store feedback with metadata
                feedback_vector = {
                    "id": f"feedback_{request.finding_id}_{int(time.time())}",
                    "values": embeddings,
                    "metadata": {
                        "type": "user_feedback",
                        "action": request.action,
                        "finding_id": request.finding_id,
                        "feedback_text": request.user_feedback,
                        "source": "user_feedback_loop"
                    }
                }
                
                index.upsert(vectors=[feedback_vector])
                logger.info("Feedback stored in vector database")
                
            except Exception as e:
                logger.warning(f"Could not store feedback in vector DB: {e}")
        
        return {"status": "success", "message": "Feedback received and will improve future analysis"}
        
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")

# NEW INTELLIGENT AUTHORING ASSISTANT ENDPOINTS

@app.post("/api/intelligent-suggestions", response_model=IntelligentSuggestionsResponse)
async def get_intelligent_suggestions(request: PhraseRequest):
    """Real-time intelligent writing suggestions"""
    try:
        logger.info(f"Getting intelligent suggestions for text length: {len(request.text)}")
        
        # Get phrase suggestions
        phrase_suggestions = get_phrase_suggestions(request.text, request.context)
        
        # Get feasibility concerns
        feasibility_concerns = assess_feasibility_concerns(request.text)
        
        # Basic regulatory flags (can be enhanced with AI later)
        regulatory_flags = []
        regulatory_red_flags = ["safe", "guaranteed", "proven", "100%", "no side effects"]
        text_lower = request.text.lower()
        
        for flag in regulatory_red_flags:
            if flag in text_lower:
                regulatory_flags.append(f"Avoid absolute claim: '{flag}' - use evidence-based language")
        
        return IntelligentSuggestionsResponse(
            phrase_suggestions=[PhraseSuggestion(**s) for s in phrase_suggestions],
            feasibility_concerns=[FeasibilityConcern(**c) for c in feasibility_concerns],
            regulatory_flags=regulatory_flags
        )
        
    except Exception as e:
        logger.error(f"Intelligent suggestions failed: {e}")
        raise HTTPException(status_code=500, detail=f"Intelligent suggestions failed: {str(e)}")

@app.post("/api/categorize-comment", response_model=CommentCategory)
async def categorize_comment(request: CommentRequest):
    """Categorize reviewer comments and suggest actions"""
    try:
        logger.info(f"Categorizing comment: {request.comment_text[:50]}...")
        
        result = categorize_reviewer_comment(request.comment_text)
        
        return CommentCategory(**result)
        
    except Exception as e:
        logger.error(f"Comment categorization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Comment categorization failed: {str(e)}")

@app.post("/api/phrase-suggestions")
async def get_phrase_suggestions_endpoint(request: PhraseRequest):
    """Get specific phrase improvement suggestions"""
    try:
        suggestions = get_phrase_suggestions(request.text, request.context)
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Phrase suggestions failed: {e}")
        raise HTTPException(status_code=500, detail=f"Phrase suggestions failed: {str(e)}")

@app.post("/api/feasibility-check")
async def check_feasibility(request: FeasibilityRequest):
    """Check operational feasibility concerns"""
    try:
        concerns = assess_feasibility_concerns(request.text)
        return {"concerns": concerns}
        
    except Exception as e:
        logger.error(f"Feasibility check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Feasibility check failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
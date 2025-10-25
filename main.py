"""
Backend API for Ilana Protocol Intelligence
Handles AI analysis using PubMedBERT, Pinecone, and Azure OpenAI
"""

import os
import json
import logging
from typing import Dict, List, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from openai import AzureOpenAI
from pinecone import Pinecone

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
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "llama-text-embed-v2-index")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://protocol-talk.openai.azure.com/")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-deployment")
PUBMEDBERT_ENDPOINT_URL = os.getenv("PUBMEDBERT_ENDPOINT_URL", "https://usz78oxlybv4xfh2.eastus.azure.endpoints.huggingface.cloud")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Initialize Pinecone
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
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

async def get_pubmedbert_embeddings(text: str) -> List[float]:
    """Get embeddings from PubMedBERT"""
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
        return []

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
        
        # Advanced RAG prompt with provenance and specific analysis
        prompt = f"""You are a clinical protocol compliance assistant specializing in ICH-GCP and FDA regulatory requirements. 

INSTRUCTIONS:
1. Analyze the protocol text below for specific compliance issues
2. Use ONLY the retrieved regulatory passages to identify violations
3. For each finding, cite the specific passage and explain WHY it's non-compliant
4. Identify exact text locations that need revision
5. Provide specific, actionable recommendations based on the evidence

PROTOCOL TEXT TO ANALYZE:
{text[:3000]}

RETRIEVED REGULATORY PASSAGES:
{passages_text}

ANALYSIS REQUIREMENTS:
- If passages don't provide evidence for a finding, don't make that finding
- Quote specific phrases from the protocol that violate regulations
- Explain exactly WHY each violation matters for compliance
- Provide specific rewrite suggestions based on the regulatory guidance
- Include character positions for highlighting problematic text

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
      "id": "specific-issue-id",
      "type": "compliance|feasibility|clarity",
      "severity": "high|medium|low",
      "title": "Specific Issue Found in Protocol",
      "description": "Detailed explanation of WHY this specific text violates regulations, quoting the problematic phrase",
      "citation": "Exact regulatory citation from retrieved passages",
      "location": {{"start": [character_position], "length": [number_of_characters]}},
      "suggestions": ["Specific rewrite based on regulatory guidance", "Additional compliance step"],
      "quoted_text": "Exact text from protocol that has the issue",
      "evidence": "Quote from retrieved passage that shows this is a violation"
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
            result = json.loads(content)
            
            # Validate that findings have specific evidence
            validated_findings = []
            for finding in result.get('findings', []):
                if finding.get('quoted_text') and finding.get('evidence'):
                    validated_findings.append(finding)
                    
            result['findings'] = validated_findings
            return result
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse OpenAI response: {content}")
            raise
        
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
        "azure_openai": bool(AZURE_OPENAI_API_KEY),
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

# For gunicorn compatibility
application = app
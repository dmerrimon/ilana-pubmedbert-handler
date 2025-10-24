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
import openai
import pinecone

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
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
    index = pinecone.Index(PINECONE_INDEX_NAME)
    logger.info("Pinecone initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Pinecone: {e}")
    index = None

# Initialize Azure OpenAI
openai.api_type = "azure"
openai.api_base = AZURE_OPENAI_ENDPOINT
openai.api_version = "2024-02-15-preview"
openai.api_key = AZURE_OPENAI_API_KEY

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
    """Analyze protocol with Azure OpenAI"""
    try:
        prompt = f"""Analyze this clinical protocol for ICH-GCP and FDA compliance:

PROTOCOL TEXT:
{text[:2000]}

SIMILAR KNOWN ISSUES:
{json.dumps(similar_findings.get('matches', [])[:3])}

Provide analysis in this exact JSON format:
{{
  "scores": {{
    "clarity": "A|B|C|D|F",
    "regulatory": "A|B|C|D|F", 
    "feasibility": "A|B|C|D|F"
  }},
  "amendmentRisk": "low|medium|high",
  "findings": [
    {{
      "id": "unique-id",
      "type": "compliance|feasibility|clarity",
      "severity": "high|medium|low",
      "title": "Issue Title",
      "description": "Detailed description",
      "citation": "ICH E6 R3 or FDA guideline reference",
      "location": {{"start": 0, "length": 20}},
      "suggestions": ["suggestion1", "suggestion2"]
    }}
  ]
}}"""

        response = openai.ChatCompletion.create(
            engine=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert clinical protocol reviewer specializing in ICH-GCP and FDA compliance. Always respond with valid JSON only."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=2000,
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
        
    except Exception as e:
        logger.error(f"Azure OpenAI analysis failed: {e}")
        # Return fallback analysis
        return {
            "scores": {
                "clarity": "B",
                "regulatory": "C", 
                "feasibility": "B"
            },
            "amendmentRisk": "medium",
            "findings": [
                {
                    "id": "ai-analysis-failed",
                    "type": "compliance",
                    "severity": "medium",
                    "title": "AI Analysis Unavailable",
                    "description": "Could not complete full AI analysis. Manual review recommended.",
                    "citation": "ICH E6 (R3): Good Clinical Practice guidelines require thorough protocol review.",
                    "location": {"start": 0, "length": 50},
                    "suggestions": ["Conduct manual compliance review", "Retry analysis later"]
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
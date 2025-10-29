"""
Clinical Analysis Client for Custom PubMedBERT Handler
Specialized client for your custom clinical intelligence endpoint
"""

import os
import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ClinicalAnalysisResult:
    """Result from clinical analysis"""
    embeddings: List[float]
    clinical_score: float
    compliance_risk: float
    text_classification: str
    confidence: float
    
class ClinicalAnalysisClient:
    """Client for your custom PubMedBERT Clinical Analysis Handler"""
    
    def __init__(self):
        self.endpoint_url = os.getenv("PUBMEDBERT_ENDPOINT_URL", 
            "https://usz78oxlybv4xfh2.eastus.azure.endpoints.huggingface.cloud")
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.azure_key = os.getenv("AZURE_ML_ENDPOINT_KEY")
        
        self.session = None
        self._init_session()
        
        # Cache for expensive clinical analysis
        self.analysis_cache = {}
        self.cache_max_size = 500
    
    def _init_session(self):
        """Initialize HTTP session with proper authentication"""
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=30)
        
        # Try different authentication methods for your custom endpoint
        headers = {"Content-Type": "application/json"}
        
        if self.azure_key:
            # Azure ML authentication
            headers["Authorization"] = f"Bearer {self.azure_key}"
        elif self.api_key:
            # Hugging Face authentication
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
    
    async def analyze_clinical_text(self, text: str) -> Optional[ClinicalAnalysisResult]:
        """Analyze clinical text using your custom handler"""
        
        # Check cache first
        cache_key = f"clinical_{hash(text)}"
        if cache_key in self.analysis_cache:
            logger.info("Using cached clinical analysis")
            return self.analysis_cache[cache_key]
        
        try:
            # Payload for your custom clinical handler
            payload = {
                "inputs": text[:1000],  # Clinical text limit
                "parameters": {
                    "return_embeddings": True,
                    "analyze_compliance": True,
                    "classify_text": True,
                    "clinical_domain": "protocol"
                }
            }
            
            # Try multiple authentication methods
            auth_methods = [
                {"Authorization": f"Bearer {self.azure_key}"} if self.azure_key else None,
                {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None,
                {"Ocp-Apim-Subscription-Key": self.azure_key} if self.azure_key else None,
                {"X-API-Key": self.azure_key} if self.azure_key else None,
            ]
            
            for auth_header in auth_methods:
                if not auth_header:
                    continue
                
                try:
                    # Update session headers
                    self.session.headers.update(auth_header)
                    
                    async with self.session.post(self.endpoint_url, json=payload) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            
                            # Parse your custom handler response
                            analysis = self._parse_clinical_response(result)
                            
                            if analysis:
                                # Cache successful result
                                self._cache_analysis(cache_key, analysis)
                                
                                logger.info(f"✅ Clinical analysis successful: {analysis.clinical_score:.3f} clinical score")
                                return analysis
                        
                        elif response.status == 401:
                            logger.warning(f"Authentication failed with {list(auth_header.keys())[0]}")
                            continue
                        
                        elif response.status == 503:
                            logger.warning("Custom endpoint loading, waiting...")
                            await asyncio.sleep(5)
                            continue
                        
                        else:
                            error_text = await response.text()
                            logger.warning(f"Endpoint error {response.status}: {error_text[:100]}...")
                            
                except aiohttp.ClientError as e:
                    logger.warning(f"Request failed: {e}")
                    continue
            
            # All authentication methods failed
            logger.error("All authentication methods failed for custom clinical endpoint")
            return None
            
        except Exception as e:
            logger.error(f"Clinical analysis failed: {e}")
            return None
    
    def _parse_clinical_response(self, response: Dict) -> Optional[ClinicalAnalysisResult]:
        """Parse response from your custom clinical handler"""
        try:
            # Handle your custom response format
            if isinstance(response, dict):
                # Direct format
                embeddings = response.get("embeddings", [])
                clinical_analysis = response.get("clinical_analysis", {})
                
                return ClinicalAnalysisResult(
                    embeddings=embeddings,
                    clinical_score=clinical_analysis.get("clinical_score", 0.5),
                    compliance_risk=clinical_analysis.get("compliance_risk", 0.5),
                    text_classification=clinical_analysis.get("text_classification", "unknown"),
                    confidence=clinical_analysis.get("confidence", 0.7)
                )
            
            elif isinstance(response, list) and len(response) > 0:
                # Array format
                result = response[0]
                if isinstance(result, dict):
                    return self._parse_clinical_response(result)
            
            logger.warning(f"Unexpected response format: {type(response)}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to parse clinical response: {e}")
            return None
    
    def _cache_analysis(self, key: str, analysis: ClinicalAnalysisResult):
        """Cache analysis with size limit"""
        if len(self.analysis_cache) >= self.cache_max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.analysis_cache))
            del self.analysis_cache[oldest_key]
        
        self.analysis_cache[key] = analysis
    
    async def get_clinical_embeddings(self, text: str) -> List[float]:
        """Get clinical embeddings from analysis"""
        analysis = await self.analyze_clinical_text(text)
        return analysis.embeddings if analysis else []
    
    async def assess_compliance_risk(self, text: str) -> Dict[str, float]:
        """Assess compliance risk using clinical analysis"""
        analysis = await self.analyze_clinical_text(text)
        
        if analysis:
            return {
                "compliance_risk": analysis.compliance_risk,
                "clinical_score": analysis.clinical_score,
                "confidence": analysis.confidence,
                "safe_language": 1.0 - analysis.compliance_risk
            }
        
        return {"compliance_risk": 0.5, "clinical_score": 0.5, "confidence": 0.3, "safe_language": 0.5}
    
    async def classify_clinical_text(self, text: str) -> Dict[str, str]:
        """Classify clinical text type"""
        analysis = await self.analyze_clinical_text(text)
        
        if analysis:
            return {
                "classification": analysis.text_classification,
                "confidence": f"{analysis.confidence:.3f}",
                "clinical_domain": "protocol" if analysis.clinical_score > 0.7 else "general"
            }
        
        return {"classification": "unknown", "confidence": "0.300", "clinical_domain": "general"}
    
    async def enhance_protocol_suggestions(self, suggestions: List[Dict], context: str) -> List[Dict]:
        """Enhance suggestions using clinical analysis"""
        try:
            enhanced_suggestions = []
            
            for suggestion in suggestions:
                original_text = suggestion.get("original", "")
                
                # Analyze original text for clinical context
                analysis = await self.analyze_clinical_text(original_text)
                
                enhanced_suggestion = dict(suggestion)
                
                if analysis:
                    # Boost confidence based on clinical analysis
                    clinical_boost = analysis.clinical_score * 0.2
                    compliance_penalty = analysis.compliance_risk * 0.3
                    
                    new_confidence = suggestion.get("confidence", 0.7) + clinical_boost - compliance_penalty
                    enhanced_suggestion["confidence"] = max(0.1, min(1.0, new_confidence))
                    
                    # Add clinical metadata
                    enhanced_suggestion.update({
                        "clinical_score": analysis.clinical_score,
                        "compliance_risk": analysis.compliance_risk,
                        "text_classification": analysis.text_classification,
                        "clinical_enhanced": True,
                        "intelligence_level": "clinical_analysis_9.5"
                    })
                
                enhanced_suggestions.append(enhanced_suggestion)
            
            # Sort by clinical-enhanced confidence
            enhanced_suggestions.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            
            logger.info(f"✅ Clinical enhancement complete: {len(enhanced_suggestions)} suggestions")
            return enhanced_suggestions
            
        except Exception as e:
            logger.error(f"Clinical enhancement failed: {e}")
            return suggestions
    
    def get_client_status(self) -> Dict:
        """Get client status"""
        return {
            "client_type": "clinical_analysis",
            "endpoint_url": self.endpoint_url,
            "has_azure_key": bool(self.azure_key),
            "has_hf_key": bool(self.api_key),
            "cache_size": len(self.analysis_cache),
            "intelligence_level": "clinical_analysis_9.5",
            "features": [
                "clinical_embeddings",
                "compliance_risk_assessment", 
                "clinical_text_classification",
                "protocol_enhancement"
            ]
        }
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()

# Global client
_clinical_client = None

async def get_clinical_client() -> ClinicalAnalysisClient:
    """Get or create global clinical client"""
    global _clinical_client
    if _clinical_client is None:
        _clinical_client = ClinicalAnalysisClient()
    return _clinical_client

async def cleanup_clinical_client():
    """Cleanup clinical client"""
    global _clinical_client
    if _clinical_client:
        await _clinical_client.close()
        _clinical_client = None
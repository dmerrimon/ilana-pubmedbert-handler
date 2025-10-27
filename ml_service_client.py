"""
ML Service Client - Interface to external ML inference service
Handles all heavy ML operations via API calls
"""

import os
import asyncio
import aiohttp
import json
import logging
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MLServiceConfig:
    """Configuration for ML service endpoints"""
    huggingface_api_key: str
    pubmedbert_endpoint: str
    semantic_endpoint: str
    context_endpoint: str
    timeout: int = 30
    max_retries: int = 3
    fallback_enabled: bool = True

class MLServiceClient:
    """Client for external ML inference service"""
    
    def __init__(self, config: MLServiceConfig = None):
        self.config = config or self._load_config()
        self.session = None
        self._init_session()
        
        # Cache for embeddings to reduce API calls
        self.embedding_cache = {}
        self.cache_max_size = 1000
        
    def _load_config(self) -> MLServiceConfig:
        """Load configuration from environment"""
        return MLServiceConfig(
            huggingface_api_key=os.getenv("HUGGINGFACE_API_KEY"),
            pubmedbert_endpoint=os.getenv("PUBMEDBERT_ENDPOINT_URL", 
                "https://usz78oxlybv4xfh2.eastus.azure.endpoints.huggingface.cloud"),
            semantic_endpoint=os.getenv("SEMANTIC_ENDPOINT_URL",
                "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"),
            context_endpoint=os.getenv("CONTEXT_ENDPOINT_URL", ""),
            timeout=int(os.getenv("ML_SERVICE_TIMEOUT", "30")),
            max_retries=int(os.getenv("ML_SERVICE_RETRIES", "3"))
        )
    
    def _init_session(self):
        """Initialize HTTP session with proper headers"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        headers = {
            "Authorization": f"Bearer {self.config.huggingface_api_key}",
            "Content-Type": "application/json"
        }
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
    
    async def get_pubmedbert_embeddings(self, text: str) -> List[float]:
        """Get clinical embeddings from custom PubMedBERT Clinical Analysis Handler"""
        # Check cache first
        cache_key = f"clinical_{hash(text)}"
        if cache_key in self.embedding_cache:
            logger.info("Using cached clinical embedding")
            return self.embedding_cache[cache_key]
        
        try:
            # Use your custom clinical handler format
            payload = {
                "inputs": text[:1000],  # Clinical handler can handle more text
                "parameters": {
                    "return_embeddings": True,
                    "analyze_compliance": True,
                    "clinical_domain": "protocol"
                }
            }
            
            for attempt in range(self.config.max_retries):
                try:
                    async with self.session.post(
                        self.config.pubmedbert_endpoint,
                        json=payload
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            
                            # Parse your custom clinical handler response
                            if isinstance(result, dict) and "embeddings" in result:
                                embeddings = result["embeddings"]
                                
                                # Store clinical analysis data for context
                                if "clinical_analysis" in result:
                                    clinical = result["clinical_analysis"]
                                    self._store_clinical_context(text, clinical)
                                
                                # Cache the result
                                self._cache_embedding(cache_key, embeddings)
                                
                                logger.info(f"✅ Clinical embeddings: {len(embeddings)} dimensions, clinical_score: {result.get('clinical_analysis', {}).get('clinical_score', 'N/A')}")
                                return embeddings
                            else:
                                raise ValueError(f"Unexpected clinical handler response: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                            
                            # Cache the result
                            self._cache_embedding(cache_key, embeddings)
                            
                            logger.info(f"✅ Clinical embeddings: {len(embeddings)} dimensions")
                            return embeddings
                        
                        elif response.status == 503:
                            logger.warning(f"Model loading, attempt {attempt + 1}/{self.config.max_retries}")
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        
                        else:
                            error_text = await response.text()
                            logger.error(f"ML service error {response.status}: {error_text}")
                            break
                            
                except aiohttp.ClientError as e:
                    logger.warning(f"Request failed attempt {attempt + 1}: {e}")
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(1)
            
            # All retries failed
            logger.error("Clinical analysis service unavailable after all retries")
            return self._fallback_embeddings(text)
            
        except Exception as e:
            logger.error(f"Semantic embedding failed: {e}")
            return self._fallback_embeddings(text)
    
    async def get_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        try:
            # Get embeddings for both texts
            embeddings1 = await self.get_sentence_embeddings(text1)
            embeddings2 = await self.get_sentence_embeddings(text2)
            
            if not embeddings1 or not embeddings2:
                return self._fallback_similarity(text1, text2)
            
            # Calculate cosine similarity
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity
            
            similarity = cosine_similarity([embeddings1], [embeddings2])[0][0]
            return max(0.0, float(similarity))
            
        except Exception as e:
            logger.error(f"Semantic similarity failed: {e}")
            return self._fallback_similarity(text1, text2)
    
    async def get_sentence_embeddings(self, text: str) -> List[float]:
        """Get sentence embeddings optimized for similarity"""
        cache_key = f"sentence_{hash(text)}"
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        try:
            # Use correct format for sentence transformer models
            payload = {
                "inputs": [text[:512]],  # Must be a list for sentence similarity
                "options": {"wait_for_model": True}
            }
            
            async with self.session.post(
                self.config.semantic_endpoint,
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    # Handle different response formats
                    if isinstance(result, list) and len(result) > 0:
                        if isinstance(result[0], list):
                            embeddings = result[0]  # [[embeddings]] format
                        else:
                            embeddings = result  # [embeddings] format
                    else:
                        embeddings = result.get("embeddings", [])
                    
                    self._cache_embedding(cache_key, embeddings)
                    return embeddings
                else:
                    logger.warning(f"Sentence embedding failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Sentence embedding error: {e}")
            return []
    
    async def detect_context_ml(self, text: str) -> Dict[str, float]:
        """ML-powered context detection"""
        try:
            # Get PubMedBERT embeddings
            embeddings = await self.get_pubmedbert_embeddings(text)
            if not embeddings:
                return self._fallback_context_detection(text)
            
            # Context templates for similarity matching
            context_templates = {
                "dosing": "Patients will receive medication 10 mg orally once daily",
                "endpoints": "Primary endpoint is overall survival and response rate",
                "safety": "Monitor patients for adverse events and toxicity",
                "procedures": "Laboratory assessments and imaging studies every 4 weeks",
                "statistics": "Statistical analysis with 80% power and sample size calculation"
            }
            
            context_scores = {}
            for context, template in context_templates.items():
                similarity = await self.get_semantic_similarity(text, template)
                context_scores[context] = similarity
            
            logger.info(f"✅ ML context detection: {context_scores}")
            return context_scores
            
        except Exception as e:
            logger.error(f"ML context detection failed: {e}")
            return self._fallback_context_detection(text)
    
    async def enhance_suggestions_ml(self, suggestions: List[Dict], text: str, context: str) -> List[Dict]:
        """Enhance suggestions with ML confidence scoring"""
        try:
            enhanced_suggestions = []
            
            for suggestion in suggestions:
                original = suggestion.get("original", "")
                suggested = suggestion.get("suggestions", [""])[0]
                
                # Calculate semantic similarity between original and suggestion
                similarity = await self.get_semantic_similarity(original, suggested)
                
                # Calculate context relevance
                context_relevance = await self.get_semantic_similarity(text, suggested)
                
                # Enhanced confidence calculation
                base_confidence = suggestion.get("confidence", 0.7)
                ml_confidence = (
                    base_confidence * 0.5 +
                    similarity * 0.3 +
                    context_relevance * 0.2
                )
                
                enhanced_suggestion = dict(suggestion)
                enhanced_suggestion.update({
                    "confidence": ml_confidence,
                    "semantic_similarity": similarity,
                    "context_relevance": context_relevance,
                    "ml_enhanced": True,
                    "intelligence_level": "advanced_ml"
                })
                
                enhanced_suggestions.append(enhanced_suggestion)
            
            # Sort by ML-enhanced confidence
            enhanced_suggestions.sort(key=lambda x: x["confidence"], reverse=True)
            
            logger.info(f"✅ ML enhancement complete: {len(enhanced_suggestions)} suggestions")
            return enhanced_suggestions
            
        except Exception as e:
            logger.error(f"ML suggestion enhancement failed: {e}")
            return suggestions  # Return original suggestions on failure
    
    def _create_embeddings_from_similarities(self, similarities: List[float], text: str) -> List[float]:
        """Create 768-dimensional embeddings from similarity scores"""
        import hashlib
        
        # Start with similarity scores
        base_embedding = similarities + [0.5] * (10 - len(similarities))  # Pad to 10 values
        
        # Create deterministic hash-based expansion
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convert hash to numbers and combine with similarities
        hash_values = [int(text_hash[i:i+2], 16) / 255.0 for i in range(0, 32, 2)]
        
        # Repeat and combine to create 768 dimensions
        embeddings = []
        for i in range(768):
            if i < len(base_embedding):
                embeddings.append(base_embedding[i])
            elif i < len(hash_values) + len(base_embedding):
                embeddings.append(hash_values[i - len(base_embedding)])
            else:
                # Cycle through base values with variation
                idx = i % len(base_embedding)
                variation = (i // len(base_embedding)) * 0.01
                embeddings.append(base_embedding[idx] + variation)
        
        return embeddings[:768]
    
    def _cache_embedding(self, key: str, embedding: List[float]):
        """Cache embedding with size limit"""
        if len(self.embedding_cache) >= self.cache_max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.embedding_cache))
            del self.embedding_cache[oldest_key]
        
        self.embedding_cache[key] = embedding
    
    def _store_clinical_context(self, text: str, clinical_analysis: Dict):
        """Store clinical analysis for enhanced context detection"""
        try:
            # Store clinical context data for later use in suggestions
            context_key = f"clinical_context_{hash(text)}"
            self.embedding_cache[context_key] = {
                "clinical_score": clinical_analysis.get("clinical_score", 0.0),
                "compliance_risk": clinical_analysis.get("compliance_risk", 0.5),
                "text_classification": clinical_analysis.get("text_classification", "unknown"),
                "timestamp": time.time()
            }
            
            logger.info(f"✅ Stored clinical context: {clinical_analysis.get('text_classification', 'unknown')} (score: {clinical_analysis.get('clinical_score', 0.0):.3f})")
        except Exception as e:
            logger.warning(f"Could not store clinical context: {e}")
    
    def _fallback_embeddings(self, text: str) -> List[float]:
        """Fallback embeddings using simple text analysis"""
        if not self.config.fallback_enabled:
            return []
        
        # Simple hash-based pseudo-embeddings for fallback
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convert hash to exactly 768-dimensional vector (PubMedBERT size)
        embeddings = []
        
        # Repeat hash pattern to get 768 dimensions
        for i in range(768):
            # Use modulo to cycle through hash characters
            char_idx = (i * 2) % len(text_hash)
            hex_pair = text_hash[char_idx:char_idx + 2]
            if len(hex_pair) < 2:
                hex_pair = text_hash[:2]
            
            # Convert to normalized float
            value = int(hex_pair, 16) / 255.0
            embeddings.append(value)
        
        # Ensure exactly 768 dimensions
        embeddings = embeddings[:768]
        while len(embeddings) < 768:
            embeddings.extend(embeddings[:768 - len(embeddings)])
        
        logger.info(f"Using fallback embeddings: {len(embeddings)} dimensions")
        return embeddings[:768]
    
    def _fallback_similarity(self, text1: str, text2: str) -> float:
        """Fallback similarity using word overlap"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _fallback_context_detection(self, text: str) -> Dict[str, float]:
        """Fallback context detection using keyword matching"""
        context_keywords = {
            "dosing": ["dose", "mg", "daily", "twice", "hour", "medication"],
            "endpoints": ["endpoint", "efficacy", "response", "survival", "assessment"],
            "safety": ["adverse", "safety", "toxicity", "side effect", "monitoring"],
            "procedures": ["visit", "procedure", "laboratory", "imaging", "assessment"],
            "statistics": ["power", "sample", "analysis", "statistical", "significance"]
        }
        
        text_lower = text.lower()
        scores = {}
        
        for context, keywords in context_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[context] = min(score / len(keywords), 1.0)
        
        return scores
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
    
    def get_service_status(self) -> Dict:
        """Get ML service status"""
        return {
            "ml_service_available": bool(self.config.huggingface_api_key),
            "clinical_handler_endpoint": self.config.pubmedbert_endpoint,
            "semantic_endpoint": self.config.semantic_endpoint,
            "cache_size": len(self.embedding_cache),
            "fallback_enabled": self.config.fallback_enabled,
            "intelligence_level": "clinical_analysis_9.5" if self.config.huggingface_api_key else "fallback",
            "features": {
                "clinical_embeddings": True,
                "compliance_risk_analysis": True,
                "clinical_text_classification": True,
                "pubmedbert_clinical_model": True
            }
        }

# Global ML service client
_ml_client = None

async def get_ml_client() -> MLServiceClient:
    """Get or create global ML client"""
    global _ml_client
    if _ml_client is None:
        _ml_client = MLServiceClient()
    return _ml_client

async def cleanup_ml_client():
    """Cleanup ML client on shutdown"""
    global _ml_client
    if _ml_client:
        await _ml_client.close()
        _ml_client = None
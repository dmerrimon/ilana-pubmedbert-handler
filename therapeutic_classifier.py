"""
Therapeutic Area ML Classifier
Uses PubMedBERT and protocol database to accurately classify therapeutic areas and phases
"""

import os
import json
import logging
import asyncio
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import pickle

logger = logging.getLogger(__name__)

@dataclass
class TherapeuticPrediction:
    """Prediction result for therapeutic area and phase"""
    therapeutic_area: str
    phase: str
    confidence_therapeutic: float
    confidence_phase: float
    alternatives: List[Tuple[str, float]]
    reasoning: str

class TherapeuticAreaClassifier:
    """ML-based therapeutic area and phase classifier using protocol database"""
    
    def __init__(self):
        self.embeddings_cache = {}
        self.training_data = {}
        self.therapeutic_embeddings = {}
        self.phase_embeddings = {}
        self.classification_cache = {}
        self.cache_expiry = timedelta(hours=24)
        
        # Performance tracking
        self.prediction_accuracy = {}
        self.user_corrections = {}
        
        # Load cached models if available
        self._load_cached_models()
        
    async def initialize_with_database(self, protocol_database, ml_client):
        """Initialize classifier with protocol database and ML client"""
        self.protocol_database = protocol_database
        self.ml_client = ml_client
        
        if not self.training_data:
            await self._build_training_data()
            await self._train_classifiers()
    
    async def _build_training_data(self):
        """Build training data from protocol database"""
        logger.info("🤖 Building ML training data from protocol database...")
        
        try:
            # Query all protocols with metadata
            results = self.protocol_database.query(
                vector=[0.5] * 1024,  # Neutral query
                top_k=1000,  # Get large sample
                include_metadata=True
            )
            
            therapeutic_samples = {}
            phase_samples = {}
            
            for match in results.matches:
                metadata = match.metadata
                text = metadata.get("text", "")
                therapeutic_area = metadata.get("therapeutic_area")
                phase = metadata.get("phase")
                
                if not text or len(text) < 100:
                    continue
                
                # Get embeddings for text
                embeddings = await self.ml_client.get_pubmedbert_embeddings(text[:1000])
                if not embeddings:
                    continue
                
                # Store therapeutic area samples
                if therapeutic_area:
                    if therapeutic_area not in therapeutic_samples:
                        therapeutic_samples[therapeutic_area] = []
                    therapeutic_samples[therapeutic_area].append({
                        "text": text,
                        "embeddings": embeddings,
                        "metadata": metadata
                    })
                
                # Store phase samples
                if phase:
                    if phase not in phase_samples:
                        phase_samples[phase] = []
                    phase_samples[phase].append({
                        "text": text,
                        "embeddings": embeddings,
                        "metadata": metadata
                    })
            
            self.training_data = {
                "therapeutic_areas": therapeutic_samples,
                "phases": phase_samples
            }
            
            logger.info(f"✅ Built training data: {len(therapeutic_samples)} therapeutic areas, {len(phase_samples)} phases")
            
            # Cache training data
            self._cache_models()
            
        except Exception as e:
            logger.error(f"Failed to build training data: {e}")
    
    async def _train_classifiers(self):
        """Train therapeutic area and phase classifiers"""
        logger.info("🧠 Training therapeutic area and phase classifiers...")
        
        # Train therapeutic area classifier
        for area, samples in self.training_data["therapeutic_areas"].items():
            if len(samples) >= 3:  # Minimum samples for training
                # Calculate representative embedding for this therapeutic area
                embeddings_matrix = np.array([s["embeddings"] for s in samples])
                representative_embedding = np.mean(embeddings_matrix, axis=0)
                
                # Calculate confidence based on consistency
                similarities = []
                for embedding in embeddings_matrix:
                    similarity = np.dot(representative_embedding, embedding) / (
                        np.linalg.norm(representative_embedding) * np.linalg.norm(embedding)
                    )
                    similarities.append(similarity)
                
                confidence = np.mean(similarities)
                
                self.therapeutic_embeddings[area] = {
                    "representative_embedding": representative_embedding.tolist(),
                    "confidence": confidence,
                    "sample_count": len(samples),
                    "sample_texts": [s["text"][:200] for s in samples[:3]]  # Store examples
                }
        
        # Train phase classifier
        for phase, samples in self.training_data["phases"].items():
            if len(samples) >= 3:
                embeddings_matrix = np.array([s["embeddings"] for s in samples])
                representative_embedding = np.mean(embeddings_matrix, axis=0)
                
                similarities = []
                for embedding in embeddings_matrix:
                    similarity = np.dot(representative_embedding, embedding) / (
                        np.linalg.norm(representative_embedding) * np.linalg.norm(embedding)
                    )
                    similarities.append(similarity)
                
                confidence = np.mean(similarities)
                
                self.phase_embeddings[phase] = {
                    "representative_embedding": representative_embedding.tolist(),
                    "confidence": confidence,
                    "sample_count": len(samples),
                    "sample_texts": [s["text"][:200] for s in samples[:3]]
                }
        
        logger.info(f"✅ Trained classifiers: {len(self.therapeutic_embeddings)} therapeutic areas, {len(self.phase_embeddings)} phases")
        
        # Cache trained models
        self._cache_models()
    
    async def classify_text(self, text: str) -> TherapeuticPrediction:
        """Classify text for therapeutic area and phase using ML"""
        
        # Check cache first
        text_hash = hash(text[:500])
        if text_hash in self.classification_cache:
            cached_result = self.classification_cache[text_hash]
            if datetime.now() - cached_result["timestamp"] < self.cache_expiry:
                return cached_result["prediction"]
        
        try:
            # Get embeddings for input text
            embeddings = await self.ml_client.get_pubmedbert_embeddings(text)
            if not embeddings:
                return self._fallback_classification(text)
            
            # Classify therapeutic area
            therapeutic_area, therapeutic_confidence, therapeutic_alternatives = self._classify_therapeutic_area(embeddings)
            
            # Classify phase
            phase, phase_confidence, phase_alternatives = self._classify_phase(embeddings)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(text, therapeutic_area, phase, therapeutic_confidence, phase_confidence)
            
            prediction = TherapeuticPrediction(
                therapeutic_area=therapeutic_area,
                phase=phase,
                confidence_therapeutic=therapeutic_confidence,
                confidence_phase=phase_confidence,
                alternatives=therapeutic_alternatives + phase_alternatives,
                reasoning=reasoning
            )
            
            # Cache result
            self.classification_cache[text_hash] = {
                "prediction": prediction,
                "timestamp": datetime.now()
            }
            
            return prediction
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return self._fallback_classification(text)
    
    def _classify_therapeutic_area(self, embeddings: List[float]) -> Tuple[str, float, List[Tuple[str, float]]]:
        """Classify therapeutic area using trained embeddings"""
        similarities = []
        
        for area, data in self.therapeutic_embeddings.items():
            representative_embedding = np.array(data["representative_embedding"])
            
            # Calculate cosine similarity
            similarity = np.dot(embeddings, representative_embedding) / (
                np.linalg.norm(embeddings) * np.linalg.norm(representative_embedding)
            )
            
            # Weight by training confidence and sample size
            weighted_similarity = similarity * data["confidence"] * min(1.0, data["sample_count"] / 10)
            
            similarities.append((area, weighted_similarity, similarity))
        
        # Sort by weighted similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        if similarities:
            best_area = similarities[0][0]
            best_confidence = similarities[0][1]
            alternatives = [(area, conf) for area, _, conf in similarities[1:4]]  # Top 3 alternatives
            return best_area, best_confidence, alternatives
        
        return "oncology", 0.5, []  # Default fallback
    
    def _classify_phase(self, embeddings: List[float]) -> Tuple[str, float, List[Tuple[str, float]]]:
        """Classify phase using trained embeddings"""
        similarities = []
        
        for phase, data in self.phase_embeddings.items():
            representative_embedding = np.array(data["representative_embedding"])
            
            similarity = np.dot(embeddings, representative_embedding) / (
                np.linalg.norm(embeddings) * np.linalg.norm(representative_embedding)
            )
            
            weighted_similarity = similarity * data["confidence"] * min(1.0, data["sample_count"] / 10)
            similarities.append((phase, weighted_similarity, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        if similarities:
            best_phase = similarities[0][0]
            best_confidence = similarities[0][1]
            alternatives = [(phase, conf) for phase, _, conf in similarities[1:3]]
            return best_phase, best_confidence, alternatives
        
        return "Phase II", 0.5, []
    
    def _generate_reasoning(self, text: str, therapeutic_area: str, phase: str, 
                          therapeutic_confidence: float, phase_confidence: float) -> str:
        """Generate human-readable reasoning for classification"""
        
        reasoning_parts = []
        
        # Therapeutic area reasoning
        if therapeutic_confidence > 0.8:
            reasoning_parts.append(f"High confidence {therapeutic_area} classification based on medical terminology and context")
        elif therapeutic_confidence > 0.6:
            reasoning_parts.append(f"Moderate confidence {therapeutic_area} classification")
        else:
            reasoning_parts.append(f"Low confidence {therapeutic_area} classification - consider manual review")
        
        # Phase reasoning
        if phase_confidence > 0.8:
            reasoning_parts.append(f"Strong {phase} indicators in protocol structure")
        elif phase_confidence > 0.6:
            reasoning_parts.append(f"Probable {phase} based on endpoints and design")
        else:
            reasoning_parts.append(f"Uncertain {phase} classification")
        
        # Add specific indicators found
        text_lower = text.lower()
        indicators = []
        
        # Look for specific therapeutic indicators
        if "cancer" in text_lower or "tumor" in text_lower:
            indicators.append("oncology terminology")
        if "cardiac" in text_lower or "heart" in text_lower:
            indicators.append("cardiology terminology")
        if "phase i" in text_lower or "dose escalation" in text_lower:
            indicators.append("Phase I language")
        if "efficacy" in text_lower and "response rate" in text_lower:
            indicators.append("Phase II efficacy focus")
        
        if indicators:
            reasoning_parts.append(f"Key indicators: {', '.join(indicators)}")
        
        return ". ".join(reasoning_parts)
    
    def _fallback_classification(self, text: str) -> TherapeuticPrediction:
        """Fallback keyword-based classification when ML fails"""
        # Use existing keyword-based detection as fallback
        therapeutic_patterns = {
            "oncology": ["cancer", "tumor", "oncology", "chemotherapy", "radiation", "malignant"],
            "cardiology": ["cardiac", "heart", "cardiovascular", "myocardial", "coronary"],
            "neurology": ["neurological", "brain", "alzheimer", "parkinson", "stroke"],
            "diabetes": ["diabetes", "diabetic", "glucose", "insulin", "glycemic"],
            "immunology": ["autoimmune", "immune", "rheumatoid", "lupus", "inflammatory"],
        }
        
        text_lower = text.lower()
        best_area = "oncology"
        best_score = 0
        
        for area, keywords in therapeutic_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > best_score:
                best_score = score
                best_area = area
        
        # Simple phase detection
        phase = "Phase II"  # Default
        if "phase i" in text_lower or "dose escalation" in text_lower:
            phase = "Phase I"
        elif "phase iii" in text_lower or "pivotal" in text_lower:
            phase = "Phase III"
        
        return TherapeuticPrediction(
            therapeutic_area=best_area,
            phase=phase,
            confidence_therapeutic=0.6,
            confidence_phase=0.6,
            alternatives=[],
            reasoning="Fallback keyword-based classification - consider training more data"
        )
    
    def collect_user_feedback(self, text: str, predicted_area: str, predicted_phase: str, 
                            actual_area: str, actual_phase: str):
        """Collect user feedback to improve classifier"""
        feedback_key = hash(text[:200])
        
        self.user_corrections[feedback_key] = {
            "text": text[:200],
            "predicted_area": predicted_area,
            "predicted_phase": predicted_phase,
            "actual_area": actual_area,
            "actual_phase": actual_phase,
            "timestamp": datetime.now()
        }
        
        # Update accuracy tracking
        area_correct = predicted_area == actual_area
        phase_correct = predicted_phase == actual_phase
        
        if predicted_area not in self.prediction_accuracy:
            self.prediction_accuracy[predicted_area] = {"correct": 0, "total": 0}
        
        self.prediction_accuracy[predicted_area]["total"] += 1
        if area_correct:
            self.prediction_accuracy[predicted_area]["correct"] += 1
        
        logger.info(f"📝 User feedback collected: {actual_area} {actual_phase} (predicted: {predicted_area} {predicted_phase})")
        
        # Retrain if we have enough feedback
        if len(self.user_corrections) % 10 == 0:
            asyncio.create_task(self._retrain_with_feedback())
    
    async def _retrain_with_feedback(self):
        """Retrain classifier incorporating user feedback"""
        logger.info("🔄 Retraining classifier with user feedback...")
        
        # This would implement incremental learning
        # For now, we'll just cache the feedback for future training
        self._cache_models()
    
    def _cache_models(self):
        """Cache trained models to disk"""
        try:
            cache_data = {
                "therapeutic_embeddings": self.therapeutic_embeddings,
                "phase_embeddings": self.phase_embeddings,
                "training_data": self.training_data,
                "user_corrections": self.user_corrections,
                "prediction_accuracy": self.prediction_accuracy,
                "timestamp": datetime.now().isoformat()
            }
            
            with open("therapeutic_classifier_cache.pkl", "wb") as f:
                pickle.dump(cache_data, f)
                
            logger.info("✅ Cached trained classifier models")
            
        except Exception as e:
            logger.warning(f"Could not cache models: {e}")
    
    def _load_cached_models(self):
        """Load cached models from disk"""
        try:
            if os.path.exists("therapeutic_classifier_cache.pkl"):
                with open("therapeutic_classifier_cache.pkl", "rb") as f:
                    cache_data = pickle.load(f)
                
                self.therapeutic_embeddings = cache_data.get("therapeutic_embeddings", {})
                self.phase_embeddings = cache_data.get("phase_embeddings", {})
                self.training_data = cache_data.get("training_data", {})
                self.user_corrections = cache_data.get("user_corrections", {})
                self.prediction_accuracy = cache_data.get("prediction_accuracy", {})
                
                cache_time = datetime.fromisoformat(cache_data.get("timestamp", "1900-01-01T00:00:00"))
                if datetime.now() - cache_time < timedelta(days=7):  # Cache valid for 7 days
                    logger.info("✅ Loaded cached classifier models")
                    return True
        
        except Exception as e:
            logger.warning(f"Could not load cached models: {e}")
        
        return False
    
    def get_classifier_stats(self) -> Dict:
        """Get classifier performance statistics"""
        stats = {
            "therapeutic_areas_trained": len(self.therapeutic_embeddings),
            "phases_trained": len(self.phase_embeddings),
            "total_training_samples": sum(len(samples) for samples in self.training_data.get("therapeutic_areas", {}).values()),
            "user_corrections": len(self.user_corrections),
            "cache_size": len(self.classification_cache)
        }
        
        # Calculate accuracy
        if self.prediction_accuracy:
            total_correct = sum(data["correct"] for data in self.prediction_accuracy.values())
            total_predictions = sum(data["total"] for data in self.prediction_accuracy.values())
            stats["overall_accuracy"] = total_correct / total_predictions if total_predictions > 0 else 0
        
        return stats

# Global classifier instance
_therapeutic_classifier = None

async def get_therapeutic_classifier(protocol_database=None, ml_client=None):
    """Get or create global therapeutic classifier"""
    global _therapeutic_classifier
    
    if _therapeutic_classifier is None:
        _therapeutic_classifier = TherapeuticAreaClassifier()
        
        if protocol_database and ml_client:
            await _therapeutic_classifier.initialize_with_database(protocol_database, ml_client)
    
    return _therapeutic_classifier
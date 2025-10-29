"""
Enhanced Intelligence System - Rival Grammarly
Machine learning-powered protocol writing assistant
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import spacy
from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import openai
from dataclasses import dataclass
import json
import re

@dataclass
class ContextualSuggestion:
    """Enhanced suggestion with ML confidence and context"""
    original: str
    suggestions: List[str]
    confidence: float
    rationale: str
    category: str
    severity: str
    position: int
    context_factors: Dict[str, float]
    user_profile_match: float
    writing_style_score: float

class EnhancedProtocolIntelligence:
    """Machine learning-powered protocol writing intelligence"""
    
    def __init__(self, model_name="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.nlp = spacy.load("en_core_web_sm")
        
        # User adaptation system
        self.user_profiles = {}
        self.correction_patterns = {}
        self.writing_style_vectors = {}
        
        # Advanced feature extractors
        self.tfidf = TfidfVectorizer(max_features=5000, stop_words='english')
        self.protocol_embeddings = {}
        
        # Context understanding
        self.section_classifiers = {
            'background': self._load_section_classifier('background'),
            'methods': self._load_section_classifier('methods'),
            'endpoints': self._load_section_classifier('endpoints'),
            'statistics': self._load_section_classifier('statistics'),
            'safety': self._load_section_classifier('safety')
        }
        
    def _load_section_classifier(self, section_type):
        """Load pre-trained section classifiers (placeholder for actual models)"""
        # In production, these would be trained models
        return {
            'patterns': self._get_section_patterns(section_type),
            'keywords': self._get_section_keywords(section_type)
        }
    
    def _get_section_patterns(self, section_type):
        """Get regex patterns for section identification"""
        patterns = {
            'background': [r'background', r'rationale', r'previous studies', r'literature'],
            'methods': [r'methods', r'procedures', r'protocol', r'administration'],
            'endpoints': [r'endpoint', r'outcome', r'measurement', r'assessment'],
            'statistics': [r'statistical', r'power', r'sample size', r'analysis'],
            'safety': [r'safety', r'adverse', r'monitoring', r'toxicity']
        }
        return patterns.get(section_type, [])
    
    def _get_section_keywords(self, section_type):
        """Get keywords for section identification"""
        keywords = {
            'background': ['hypothesis', 'objective', 'aim', 'goal', 'evidence'],
            'methods': ['randomized', 'blinded', 'placebo', 'intervention', 'procedure'],
            'endpoints': ['primary', 'secondary', 'exploratory', 'efficacy', 'response'],
            'statistics': ['power', 'alpha', 'significance', 'confidence', 'sample'],
            'safety': ['adverse', 'serious', 'monitoring', 'dsmb', 'stopping']
        }
        return keywords.get(section_type, [])
    
    def extract_semantic_features(self, text: str) -> Dict[str, float]:
        """Extract semantic features using PubMedBERT"""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()
        
        # Convert to feature dictionary
        features = {
            'complexity_score': self._calculate_complexity(text),
            'technical_density': self._calculate_technical_density(text),
            'regulatory_compliance': self._assess_regulatory_language(text),
            'operational_feasibility': self._assess_feasibility(text),
            'clarity_score': self._assess_clarity(text)
        }
        
        return features
    
    def _calculate_complexity(self, text: str) -> float:
        """Calculate text complexity using linguistic features"""
        doc = self.nlp(text)
        
        # Linguistic complexity indicators
        avg_sentence_length = len([token for token in doc if not token.is_space]) / len(list(doc.sents))
        unique_words = len(set([token.lemma_ for token in doc if token.is_alpha]))
        total_words = len([token for token in doc if token.is_alpha])
        
        complexity = (avg_sentence_length / 20.0) + (unique_words / total_words)
        return min(complexity, 1.0)
    
    def _calculate_technical_density(self, text: str) -> float:
        """Calculate density of technical/medical terms"""
        technical_terms = [
            'efficacy', 'pharmacokinetic', 'biomarker', 'endpoint', 'randomized',
            'blinded', 'placebo', 'adverse', 'toxicity', 'dose', 'administration',
            'statistical', 'significance', 'confidence', 'power', 'sample'
        ]
        
        words = text.lower().split()
        technical_count = sum(1 for word in words if any(term in word for term in technical_terms))
        
        return min(technical_count / len(words), 1.0) if words else 0.0
    
    def _assess_regulatory_language(self, text: str) -> float:
        """Assess compliance with regulatory language patterns"""
        regulatory_good = ['demonstrated', 'well-tolerated', 'established', 'validated']
        regulatory_bad = ['safe', 'proven', 'guaranteed', '100%', 'no side effects']
        
        text_lower = text.lower()
        good_score = sum(1 for term in regulatory_good if term in text_lower)
        bad_score = sum(1 for term in regulatory_bad if term in text_lower)
        
        return max(0.0, (good_score - bad_score * 2) / 10.0)
    
    def _assess_feasibility(self, text: str) -> float:
        """Assess operational feasibility indicators"""
        feasibility_concerns = ['daily', 'extensive', 'complex', 'specialized', 'frequent']
        feasibility_good = ['weekly', 'standard', 'established', 'routine', 'manageable']
        
        text_lower = text.lower()
        concern_score = sum(1 for term in feasibility_concerns if term in text_lower)
        good_score = sum(1 for term in feasibility_good if term in text_lower)
        
        return max(0.0, (good_score - concern_score) / 5.0)
    
    def _assess_clarity(self, text: str) -> float:
        """Assess text clarity using readability metrics"""
        doc = self.nlp(text)
        
        # Simple clarity indicators
        avg_word_length = np.mean([len(token.text) for token in doc if token.is_alpha])
        passive_voice_count = len([token for token in doc if token.dep_ == "auxpass"])
        total_verbs = len([token for token in doc if token.pos_ == "VERB"])
        
        clarity = 1.0 - (avg_word_length / 15.0) - (passive_voice_count / max(total_verbs, 1))
        return max(0.0, min(clarity, 1.0))
    
    def detect_writing_context(self, text: str) -> Dict[str, float]:
        """Detect the context/section type of the text"""
        context_scores = {}
        
        for section_type, classifier in self.section_classifiers.items():
            score = 0.0
            
            # Pattern matching
            for pattern in classifier['patterns']:
                if re.search(pattern, text.lower()):
                    score += 0.3
            
            # Keyword matching
            for keyword in classifier['keywords']:
                if keyword in text.lower():
                    score += 0.2
            
            context_scores[section_type] = min(score, 1.0)
        
        return context_scores
    
    def learn_from_user_correction(self, user_id: str, original: str, 
                                 user_correction: str, context: str):
        """Learn from user corrections to personalize suggestions"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'corrections': [],
                'preferences': {},
                'style_vector': np.zeros(100)  # Simplified style representation
            }
        
        correction_data = {
            'original': original,
            'correction': user_correction,
            'context': context,
            'timestamp': np.datetime64('now')
        }
        
        self.user_profiles[user_id]['corrections'].append(correction_data)
        
        # Update user preferences
        self._update_user_preferences(user_id, correction_data)
    
    def _update_user_preferences(self, user_id: str, correction_data: Dict):
        """Update user preferences based on corrections"""
        # Analyze correction patterns
        original_features = self.extract_semantic_features(correction_data['original'])
        corrected_features = self.extract_semantic_features(correction_data['correction'])
        
        # Update preference scores
        for feature, value in corrected_features.items():
            if feature not in self.user_profiles[user_id]['preferences']:
                self.user_profiles[user_id]['preferences'][feature] = []
            
            self.user_profiles[user_id]['preferences'][feature].append(value)
    
    def generate_contextual_suggestions(self, text: str, user_id: str = None) -> List[ContextualSuggestion]:
        """Generate intelligent, contextual suggestions"""
        suggestions = []
        
        # Extract semantic features
        features = self.extract_semantic_features(text)
        context = self.detect_writing_context(text)
        
        # Get user profile
        user_profile = self.user_profiles.get(user_id, {})
        
        # Enhanced phrase analysis with ML
        enhanced_suggestions = self._get_ml_suggestions(text, features, context, user_profile)
        
        for suggestion_data in enhanced_suggestions:
            suggestion = ContextualSuggestion(
                original=suggestion_data['original'],
                suggestions=suggestion_data['suggestions'],
                confidence=suggestion_data['confidence'],
                rationale=suggestion_data['rationale'],
                category=suggestion_data['category'],
                severity=suggestion_data['severity'],
                position=suggestion_data['position'],
                context_factors=context,
                user_profile_match=suggestion_data['user_match'],
                writing_style_score=suggestion_data['style_score']
            )
            suggestions.append(suggestion)
        
        # Sort by confidence and relevance
        suggestions.sort(key=lambda x: (x.confidence * x.user_profile_match), reverse=True)
        
        return suggestions[:10]  # Return top 10 suggestions
    
    def _get_ml_suggestions(self, text: str, features: Dict, context: Dict, 
                          user_profile: Dict) -> List[Dict]:
        """Generate ML-powered suggestions"""
        suggestions = []
        
        # Use Azure OpenAI for intelligent rewriting
        enhanced_suggestions = self._get_ai_rewrite_suggestions(text, context)
        
        # Add traditional rule-based suggestions with ML confidence scoring
        rule_suggestions = self._get_enhanced_rule_suggestions(text, features, context)
        
        # Combine and score all suggestions
        all_suggestions = enhanced_suggestions + rule_suggestions
        
        # Apply user personalization
        personalized_suggestions = self._personalize_suggestions(all_suggestions, user_profile)
        
        return personalized_suggestions
    
    def _get_ai_rewrite_suggestions(self, text: str, context: Dict) -> List[Dict]:
        """Use Azure OpenAI for intelligent text improvement"""
        # This would integrate with Azure OpenAI for advanced rewriting
        # Placeholder for now
        return []
    
    def _get_enhanced_rule_suggestions(self, text: str, features: Dict, 
                                     context: Dict) -> List[Dict]:
        """Enhanced rule-based suggestions with ML confidence"""
        suggestions = []
        
        # Example: Enhanced "as needed" detection with context
        if "as needed" in text.lower():
            confidence = 0.8
            
            # Adjust confidence based on context
            if context.get('methods', 0) > 0.5:
                confidence += 0.1
            if features.get('clarity_score', 0) < 0.5:
                confidence += 0.1
            
            suggestions.append({
                'original': 'as needed',
                'suggestions': [
                    "every 12 hours ± 1 hour",
                    "as clinically indicated (maximum twice daily)",
                    "PRN with minimum 6-hour interval"
                ],
                'confidence': min(confidence, 1.0),
                'rationale': 'Vague timing creates implementation variability',
                'category': 'clarity',
                'severity': 'medium',
                'position': text.lower().find('as needed'),
                'user_match': 0.7,
                'style_score': 0.8
            })
        
        return suggestions
    
    def _personalize_suggestions(self, suggestions: List[Dict], 
                               user_profile: Dict) -> List[Dict]:
        """Personalize suggestions based on user history"""
        if not user_profile or 'preferences' not in user_profile:
            return suggestions
        
        # Adjust suggestion scores based on user preferences
        for suggestion in suggestions:
            # Example personalization logic
            if 'clarity' in user_profile.get('preferences', {}):
                clarity_pref = np.mean(user_profile['preferences']['clarity'])
                if suggestion['category'] == 'clarity':
                    suggestion['user_match'] = clarity_pref
        
        return suggestions

# Integration functions for existing system
def enhance_existing_suggestions(text: str, user_id: str = None) -> Dict:
    """Enhanced version of existing get_phrase_suggestions"""
    intelligence = EnhancedProtocolIntelligence()
    suggestions = intelligence.generate_contextual_suggestions(text, user_id)
    
    return {
        'suggestions': [
            {
                'original': s.original,
                'suggestions': s.suggestions,
                'confidence': s.confidence,
                'rationale': s.rationale,
                'category': s.category,
                'severity': s.severity,
                'position': s.position,
                'ml_enhanced': True
            }
            for s in suggestions
        ],
        'intelligence_level': 'enhanced',
        'personalized': user_id is not None
    }
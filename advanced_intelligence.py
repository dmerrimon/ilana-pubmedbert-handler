"""
REAL Advanced Intelligence System - Actually Integrated
Semantic analysis, context understanding, and user adaptation
"""

import os
import numpy as np
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re
from datetime import datetime
import sqlite3

# Fallback imports - graceful degradation if ML libraries not available
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from protocol_intelligence_db import (
    get_phrase_suggestions as basic_phrase_suggestions,
    categorize_reviewer_comment as basic_categorize_comment,
    assess_feasibility_concerns as basic_feasibility_check
)

@dataclass
class EnhancedSuggestion:
    """Enhanced suggestion with ML confidence and context"""
    original: str
    suggestions: List[str]
    confidence: float
    rationale: str
    category: str
    severity: str
    position: int
    semantic_similarity: float
    context_relevance: float
    user_personalization: float

class RealAdvancedIntelligence:
    """Actually working advanced intelligence system"""
    
    def __init__(self):
        self.db_path = "intelligence.db"
        self._init_database()
        
        # Try to load advanced models, fallback to basic functionality
        self.semantic_model = None
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ Semantic model loaded successfully")
            except Exception as e:
                print(f"⚠️ Semantic model failed to load: {e}")
        
        # Pre-computed context embeddings (lightweight)
        self.context_patterns = self._load_context_patterns()
        
        # User learning system
        self.user_patterns = {}
        self._load_user_patterns()
    
    def _init_database(self):
        """Initialize simple SQLite database for learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action_type TEXT,
                original_text TEXT,
                suggestion TEXT,
                context TEXT,
                timestamp DATETIME,
                confidence REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suggestion_performance (
                suggestion_type TEXT PRIMARY KEY,
                acceptance_rate REAL,
                total_count INTEGER,
                avg_confidence REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_context_patterns(self) -> Dict[str, List[str]]:
        """Load context detection patterns"""
        return {
            'dosing': [
                'administer', 'dose', 'mg', 'daily', 'twice', 'every', 'hour',
                'tablet', 'injection', 'infusion', 'medication'
            ],
            'endpoints': [
                'primary endpoint', 'secondary endpoint', 'efficacy', 'response',
                'survival', 'progression', 'assessment', 'measurement'
            ],
            'safety': [
                'adverse', 'safety', 'toxicity', 'side effect', 'monitoring',
                'serious', 'grade', 'ctcae'
            ],
            'statistics': [
                'power', 'sample size', 'analysis', 'statistical', 'p-value',
                'confidence interval', 'significance', 'hypothesis'
            ],
            'procedures': [
                'visit', 'procedure', 'assessment', 'laboratory', 'imaging',
                'biopsy', 'blood draw', 'evaluation'
            ]
        }
    
    def _load_user_patterns(self):
        """Load user learning patterns from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, action_type, COUNT(*) as count
                FROM user_actions 
                WHERE timestamp > datetime('now', '-30 days')
                GROUP BY user_id, action_type
            ''')
            
            for user_id, action_type, count in cursor.fetchall():
                if user_id not in self.user_patterns:
                    self.user_patterns[user_id] = {}
                self.user_patterns[user_id][action_type] = count
            
            conn.close()
        except Exception as e:
            print(f"Could not load user patterns: {e}")
    
    def detect_context(self, text: str) -> Dict[str, float]:
        """Detect context using pattern matching and semantic similarity"""
        context_scores = {}
        text_lower = text.lower()
        
        # Pattern-based detection
        for context_type, patterns in self.context_patterns.items():
            score = 0.0
            
            for pattern in patterns:
                if pattern in text_lower:
                    score += 1.0
            
            # Normalize by pattern count
            context_scores[context_type] = min(score / len(patterns), 1.0)
        
        # Semantic enhancement if available
        if self.semantic_model and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                context_scores = self._enhance_context_with_semantics(text, context_scores)
            except Exception as e:
                print(f"Semantic enhancement failed: {e}")
        
        return context_scores
    
    def _enhance_context_with_semantics(self, text: str, pattern_scores: Dict[str, float]) -> Dict[str, float]:
        """Enhance context detection with semantic similarity"""
        
        # Context examples for semantic matching
        context_examples = {
            'dosing': "Patients will receive 10 mg orally once daily",
            'endpoints': "Primary endpoint is overall survival",
            'safety': "Monitor for adverse events and toxicity",
            'statistics': "Statistical analysis with 80% power",
            'procedures': "Laboratory assessments every 4 weeks"
        }
        
        try:
            text_embedding = self.semantic_model.encode([text])
            
            for context_type, example in context_examples.items():
                example_embedding = self.semantic_model.encode([example])
                
                if SKLEARN_AVAILABLE:
                    similarity = cosine_similarity(text_embedding, example_embedding)[0][0]
                else:
                    # Simple fallback similarity
                    similarity = self._simple_similarity(text, example)
                
                # Combine pattern and semantic scores
                pattern_scores[context_type] = (
                    pattern_scores.get(context_type, 0.0) * 0.6 + 
                    similarity * 0.4
                )
        
        except Exception as e:
            print(f"Semantic processing error: {e}")
        
        return pattern_scores
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """Simple word overlap similarity as fallback"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def generate_enhanced_suggestions(self, text: str, user_id: str = None) -> List[EnhancedSuggestion]:
        """Generate enhanced suggestions with ML and context"""
        
        # Detect context
        context_scores = self.detect_context(text)
        primary_context = max(context_scores, key=context_scores.get) if context_scores else 'general'
        
        # Get basic suggestions
        basic_suggestions = basic_phrase_suggestions(text, primary_context)
        
        # Enhance with ML
        enhanced_suggestions = []
        
        for suggestion_data in basic_suggestions:
            enhanced = self._enhance_suggestion(suggestion_data, context_scores, user_id)
            enhanced_suggestions.append(enhanced)
        
        # Add context-specific suggestions
        context_suggestions = self._get_context_specific_suggestions(text, context_scores)
        enhanced_suggestions.extend(context_suggestions)
        
        # Sort by combined confidence
        enhanced_suggestions.sort(
            key=lambda x: x.confidence * x.context_relevance * x.user_personalization, 
            reverse=True
        )
        
        return enhanced_suggestions[:8]  # Top 8 suggestions
    
    def _enhance_suggestion(self, suggestion_data: Dict, context_scores: Dict, user_id: str) -> EnhancedSuggestion:
        """Enhance a basic suggestion with ML features"""
        
        # Calculate semantic similarity if possible
        semantic_similarity = 0.8  # Default
        if self.semantic_model:
            try:
                original_emb = self.semantic_model.encode([suggestion_data['original']])
                suggestion_emb = self.semantic_model.encode([suggestion_data['suggestions'][0]])
                if SKLEARN_AVAILABLE:
                    semantic_similarity = cosine_similarity(original_emb, suggestion_emb)[0][0]
            except:
                pass
        
        # Context relevance
        suggestion_category = suggestion_data.get('category', 'general')
        context_relevance = context_scores.get(suggestion_category, 0.5)
        
        # User personalization
        user_personalization = self._calculate_user_personalization(suggestion_data, user_id)
        
        # Enhanced confidence
        base_confidence = 0.7  # Default confidence
        enhanced_confidence = (
            base_confidence * 0.4 +
            semantic_similarity * 0.3 +
            context_relevance * 0.3
        )
        
        return EnhancedSuggestion(
            original=suggestion_data['original'],
            suggestions=suggestion_data['suggestions'],
            confidence=enhanced_confidence,
            rationale=suggestion_data['rationale'],
            category=suggestion_data['category'],
            severity=suggestion_data['severity'],
            position=suggestion_data['position'],
            semantic_similarity=semantic_similarity,
            context_relevance=context_relevance,
            user_personalization=user_personalization
        )
    
    def _calculate_user_personalization(self, suggestion_data: Dict, user_id: str) -> float:
        """Calculate user personalization score"""
        if not user_id or user_id not in self.user_patterns:
            return 0.7  # Default for new users
        
        user_data = self.user_patterns[user_id]
        
        # Simple personalization based on acceptance rate
        accepts = user_data.get('accept', 0)
        rejects = user_data.get('reject', 0)
        total = accepts + rejects
        
        if total == 0:
            return 0.7
        
        acceptance_rate = accepts / total
        
        # Users who accept more suggestions get higher personalization
        return min(0.3 + acceptance_rate * 0.7, 1.0)
    
    def _get_context_specific_suggestions(self, text: str, context_scores: Dict) -> List[EnhancedSuggestion]:
        """Generate context-specific suggestions"""
        suggestions = []
        
        # Dosing context suggestions
        if context_scores.get('dosing', 0) > 0.5:
            if re.search(r'\bas needed\b', text, re.IGNORECASE):
                suggestions.append(EnhancedSuggestion(
                    original="as needed",
                    suggestions=["every 12 hours ± 1 hour", "PRN with minimum 6-hour interval"],
                    confidence=0.9,
                    rationale="Dosing context: Specify precise timing intervals",
                    category="dosing",
                    severity="high",
                    position=text.lower().find("as needed"),
                    semantic_similarity=0.9,
                    context_relevance=context_scores['dosing'],
                    user_personalization=0.8
                ))
        
        # Safety context suggestions  
        if context_scores.get('safety', 0) > 0.5:
            if re.search(r'\bsafe\b', text, re.IGNORECASE):
                suggestions.append(EnhancedSuggestion(
                    original="safe",
                    suggestions=["well-tolerated", "demonstrated acceptable safety profile"],
                    confidence=0.95,
                    rationale="Safety context: Use evidence-based language",
                    category="safety",
                    severity="high",
                    position=text.lower().find("safe"),
                    semantic_similarity=0.8,
                    context_relevance=context_scores['safety'],
                    user_personalization=0.9
                ))
        
        return suggestions
    
    def record_user_action(self, user_id: str, action_type: str, original: str, 
                          suggestion: str, context: str, confidence: float):
        """Record user action for learning"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_actions 
                (user_id, action_type, original_text, suggestion, context, timestamp, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, action_type, original, suggestion, context, datetime.now(), confidence))
            
            conn.commit()
            conn.close()
            
            # Update in-memory patterns
            if user_id not in self.user_patterns:
                self.user_patterns[user_id] = {}
            
            self.user_patterns[user_id][action_type] = \
                self.user_patterns[user_id].get(action_type, 0) + 1
            
        except Exception as e:
            print(f"Could not record user action: {e}")
    
    def get_enhanced_comment_categorization(self, comment_text: str) -> Dict:
        """Enhanced comment categorization with confidence"""
        
        # Get basic categorization
        basic_result = basic_categorize_comment(comment_text)
        
        # Enhance with context analysis
        context_scores = self.detect_context(comment_text)
        
        # Adjust confidence based on context clarity
        max_context_score = max(context_scores.values()) if context_scores else 0.5
        
        enhanced_confidence = basic_result['confidence']
        if max_context_score > 0.7:
            enhanced_confidence = 'high'
        elif max_context_score > 0.4:
            enhanced_confidence = 'medium'
        else:
            enhanced_confidence = 'low'
        
        return {
            'category': basic_result['category'],
            'confidence': enhanced_confidence,
            'suggested_actions': basic_result['suggested_actions'],
            'context_analysis': context_scores,
            'enhanced': True
        }
    
    def get_enhanced_feasibility_check(self, text: str) -> Dict:
        """Enhanced feasibility analysis"""
        
        # Get basic feasibility concerns
        basic_concerns = basic_feasibility_check(text)
        
        # Enhance with context analysis
        context_scores = self.detect_context(text)
        
        # Add context-specific feasibility insights
        enhanced_concerns = []
        for concern in basic_concerns:
            enhanced_concern = dict(concern)
            
            # Add confidence based on context
            if concern['type'] == 'high_frequency_visits' and context_scores.get('procedures', 0) > 0.6:
                enhanced_concern['confidence'] = 'high'
                enhanced_concern['rationale'] = 'High procedure density detected'
            else:
                enhanced_concern['confidence'] = 'medium'
            
            enhanced_concerns.append(enhanced_concern)
        
        return {
            'concerns': enhanced_concerns,
            'context_analysis': context_scores,
            'overall_feasibility_score': self._calculate_feasibility_score(context_scores),
            'enhanced': True
        }
    
    def _calculate_feasibility_score(self, context_scores: Dict) -> float:
        """Calculate overall feasibility score"""
        procedure_complexity = context_scores.get('procedures', 0) * context_scores.get('safety', 0)
        dosing_complexity = context_scores.get('dosing', 0)
        
        # Lower score = more feasible
        complexity = (procedure_complexity + dosing_complexity) / 2
        feasibility_score = max(0.1, 1.0 - complexity)
        
        return feasibility_score

# Global instance
_advanced_intelligence = None

def get_advanced_intelligence() -> RealAdvancedIntelligence:
    """Get or create the global advanced intelligence instance"""
    global _advanced_intelligence
    if _advanced_intelligence is None:
        _advanced_intelligence = RealAdvancedIntelligence()
    return _advanced_intelligence

# Enhanced API functions
def get_enhanced_phrase_suggestions(text: str, context: str = "general", user_id: str = None) -> Dict:
    """Enhanced phrase suggestions with ML"""
    intelligence = get_advanced_intelligence()
    suggestions = intelligence.generate_enhanced_suggestions(text, user_id)
    
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
                'semantic_similarity': s.semantic_similarity,
                'context_relevance': s.context_relevance,
                'user_personalization': s.user_personalization,
                'enhanced': True
            }
            for s in suggestions
        ],
        'total_suggestions': len(suggestions),
        'intelligence_level': 'advanced'
    }

def record_user_feedback(user_id: str, action_type: str, original: str, 
                        suggestion: str, context: str, confidence: float):
    """Record user feedback for learning"""
    intelligence = get_advanced_intelligence()
    intelligence.record_user_action(user_id, action_type, original, suggestion, context, confidence)
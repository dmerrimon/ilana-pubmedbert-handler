"""
Adaptive Learning System - Real-time user adaptation
Learns from corrections, writing patterns, and user preferences
"""

import numpy as np
import torch
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json
from datetime import datetime, timedelta
from collections import defaultdict
import sqlite3
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd

@dataclass
class UserAction:
    """Represents a user action for learning"""
    user_id: str
    action_type: str  # 'accept', 'reject', 'modify', 'ignore'
    original_text: str
    suggested_text: str
    final_text: str
    context: str
    timestamp: datetime
    confidence_before: float
    user_satisfaction: Optional[float] = None

@dataclass
class WritingPattern:
    """User's writing pattern profile"""
    user_id: str
    preferred_complexity: float
    preferred_formality: float
    domain_expertise: Dict[str, float]
    common_phrases: List[str]
    avoided_phrases: List[str]
    correction_patterns: Dict[str, int]
    writing_velocity: float  # words per minute
    active_sessions: int

class AdaptiveLearningEngine:
    """Real-time learning and adaptation system"""
    
    def __init__(self, db_path: str = "user_learning.db"):
        self.db_path = db_path
        self.user_profiles = {}
        self.suggestion_history = defaultdict(list)
        self.learning_models = {}
        
        # Initialize database
        self._init_database()
        
        # Load existing user profiles
        self._load_user_profiles()
        
        # Real-time learning parameters
        self.min_actions_for_learning = 10
        self.learning_rate = 0.1
        self.forgetting_factor = 0.95  # Recent actions weighted more
        
    def _init_database(self):
        """Initialize SQLite database for persistent learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User actions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                original_text TEXT,
                suggested_text TEXT,
                final_text TEXT,
                context TEXT,
                timestamp DATETIME,
                confidence_before REAL,
                user_satisfaction REAL
            )
        ''')
        
        # User profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                profile_data TEXT,
                last_updated DATETIME
            )
        ''')
        
        # Suggestion performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suggestion_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suggestion_type TEXT,
                context TEXT,
                acceptance_rate REAL,
                avg_confidence REAL,
                total_suggestions INTEGER,
                last_updated DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_user_profiles(self):
        """Load existing user profiles from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, profile_data FROM user_profiles')
        for user_id, profile_json in cursor.fetchall():
            try:
                profile_data = json.loads(profile_json)
                self.user_profiles[user_id] = WritingPattern(**profile_data)
            except:
                continue
        
        conn.close()
    
    def record_user_action(self, action: UserAction):
        """Record a user action for learning"""
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_actions 
            (user_id, action_type, original_text, suggested_text, final_text, 
             context, timestamp, confidence_before, user_satisfaction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            action.user_id, action.action_type, action.original_text,
            action.suggested_text, action.final_text, action.context,
            action.timestamp, action.confidence_before, action.user_satisfaction
        ))
        
        conn.commit()
        conn.close()
        
        # Update in-memory learning
        self._update_user_profile(action)
        self._update_suggestion_performance(action)
    
    def _update_user_profile(self, action: UserAction):
        """Update user profile based on action"""
        user_id = action.user_id
        
        # Initialize profile if doesn't exist
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = WritingPattern(
                user_id=user_id,
                preferred_complexity=0.5,
                preferred_formality=0.5,
                domain_expertise={},
                common_phrases=[],
                avoided_phrases=[],
                correction_patterns={},
                writing_velocity=0.0,
                active_sessions=0
            )
        
        profile = self.user_profiles[user_id]
        
        # Update based on action type
        if action.action_type == 'accept':
            self._reinforce_suggestion(profile, action)
        elif action.action_type == 'reject':
            self._penalize_suggestion(profile, action)
        elif action.action_type == 'modify':
            self._learn_from_modification(profile, action)
        
        # Update profile in database
        self._save_user_profile(profile)
    
    def _reinforce_suggestion(self, profile: WritingPattern, action: UserAction):
        """Reinforce patterns from accepted suggestions"""
        # Analyze the accepted suggestion
        complexity = self._calculate_text_complexity(action.suggested_text)
        formality = self._calculate_text_formality(action.suggested_text)
        
        # Update preferences with learning rate
        profile.preferred_complexity = (
            profile.preferred_complexity * (1 - self.learning_rate) +
            complexity * self.learning_rate
        )
        
        profile.preferred_formality = (
            profile.preferred_formality * (1 - self.learning_rate) +
            formality * self.learning_rate
        )
        
        # Add to common phrases
        key_phrases = self._extract_key_phrases(action.suggested_text)
        for phrase in key_phrases:
            if phrase not in profile.common_phrases:
                profile.common_phrases.append(phrase)
        
        # Update domain expertise
        domain = self._identify_domain(action.context)
        if domain not in profile.domain_expertise:
            profile.domain_expertise[domain] = 0.0
        profile.domain_expertise[domain] = min(1.0, profile.domain_expertise[domain] + 0.1)
    
    def _penalize_suggestion(self, profile: WritingPattern, action: UserAction):
        """Learn from rejected suggestions"""
        # Add rejected phrases to avoided list
        key_phrases = self._extract_key_phrases(action.suggested_text)
        for phrase in key_phrases:
            if phrase not in profile.avoided_phrases:
                profile.avoided_phrases.append(phrase)
        
        # Record rejection pattern
        suggestion_type = self._classify_suggestion_type(action.suggested_text)
        if suggestion_type not in profile.correction_patterns:
            profile.correction_patterns[suggestion_type] = 0
        profile.correction_patterns[suggestion_type] += 1
    
    def _learn_from_modification(self, profile: WritingPattern, action: UserAction):
        """Learn from user modifications"""
        # Analyze what the user changed
        original_complexity = self._calculate_text_complexity(action.suggested_text)
        final_complexity = self._calculate_text_complexity(action.final_text)
        
        # Update preferences based on user's modification direction
        complexity_preference = final_complexity - original_complexity
        profile.preferred_complexity = max(0, min(1, 
            profile.preferred_complexity + complexity_preference * self.learning_rate
        ))
        
        # Learn phrase preferences from modifications
        original_phrases = self._extract_key_phrases(action.suggested_text)
        final_phrases = self._extract_key_phrases(action.final_text)
        
        # Phrases user kept
        kept_phrases = set(original_phrases) & set(final_phrases)
        for phrase in kept_phrases:
            if phrase not in profile.common_phrases:
                profile.common_phrases.append(phrase)
        
        # Phrases user removed
        removed_phrases = set(original_phrases) - set(final_phrases)
        for phrase in removed_phrases:
            if phrase not in profile.avoided_phrases:
                profile.avoided_phrases.append(phrase)
    
    def _calculate_text_complexity(self, text: str) -> float:
        """Calculate text complexity score (0-1)"""
        words = text.split()
        if not words:
            return 0.0
        
        # Simple complexity metrics
        avg_word_length = np.mean([len(word) for word in words])
        sentence_count = len([s for s in text.split('.') if s.strip()])
        avg_sentence_length = len(words) / max(sentence_count, 1)
        
        complexity = (avg_word_length / 10.0 + avg_sentence_length / 20.0) / 2.0
        return min(complexity, 1.0)
    
    def _calculate_text_formality(self, text: str) -> float:
        """Calculate text formality score (0-1)"""
        formal_indicators = ['shall', 'must', 'will', 'defined', 'specified', 'according to']
        informal_indicators = ['can', 'might', 'could', 'maybe', 'pretty', 'quite']
        
        text_lower = text.lower()
        formal_count = sum(1 for indicator in formal_indicators if indicator in text_lower)
        informal_count = sum(1 for indicator in informal_indicators if indicator in text_lower)
        
        total_indicators = formal_count + informal_count
        if total_indicators == 0:
            return 0.5  # Neutral
        
        return formal_count / total_indicators
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        # Simple phrase extraction (can be enhanced with NLP)
        words = text.lower().split()
        phrases = []
        
        # Extract 2-3 word phrases
        for i in range(len(words) - 1):
            if len(words[i]) > 3 and len(words[i+1]) > 3:
                phrases.append(f"{words[i]} {words[i+1]}")
        
        for i in range(len(words) - 2):
            if all(len(word) > 3 for word in words[i:i+3]):
                phrases.append(f"{words[i]} {words[i+1]} {words[i+2]}")
        
        return phrases[:5]  # Return top 5 phrases
    
    def _identify_domain(self, context: str) -> str:
        """Identify domain from context"""
        domain_keywords = {
            'oncology': ['cancer', 'tumor', 'chemotherapy'],
            'cardiology': ['heart', 'cardiac', 'blood pressure'],
            'neurology': ['brain', 'neurological', 'cognitive'],
            'statistics': ['power', 'sample', 'analysis'],
            'regulatory': ['fda', 'ich', 'compliance']
        }
        
        context_lower = context.lower()
        for domain, keywords in domain_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                return domain
        
        return 'general'
    
    def _classify_suggestion_type(self, text: str) -> str:
        """Classify type of suggestion"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['every', 'hour', 'daily', 'weekly']):
            return 'timing_precision'
        elif any(word in text_lower for word in ['well-tolerated', 'demonstrated', 'established']):
            return 'regulatory_language'
        elif any(word in text_lower for word in ['assess', 'monitor', 'evaluate']):
            return 'procedure_clarification'
        else:
            return 'general_improvement'
    
    def get_personalized_suggestions(self, text: str, user_id: str, context: str) -> List[Dict]:
        """Generate personalized suggestions based on user profile"""
        if user_id not in self.user_profiles:
            return []  # Use default suggestions
        
        profile = self.user_profiles[user_id]
        suggestions = []
        
        # Filter suggestions based on user preferences
        base_suggestions = self._get_base_suggestions(text, context)
        
        for suggestion in base_suggestions:
            # Calculate personalization score
            personalization_score = self._calculate_personalization_score(
                suggestion, profile, context
            )
            
            if personalization_score > 0.5:  # Threshold for inclusion
                suggestion['personalization_score'] = personalization_score
                suggestion['confidence'] *= personalization_score
                suggestions.append(suggestion)
        
        # Sort by personalized confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return suggestions[:5]  # Return top 5 personalized suggestions
    
    def _calculate_personalization_score(self, suggestion: Dict, 
                                       profile: WritingPattern, context: str) -> float:
        """Calculate how well suggestion matches user profile"""
        score_factors = []
        
        # Check against avoided phrases
        suggestion_text = suggestion.get('suggestion', '')
        suggestion_phrases = self._extract_key_phrases(suggestion_text)
        
        avoided_penalty = sum(1 for phrase in suggestion_phrases 
                            if phrase in profile.avoided_phrases)
        score_factors.append(max(0, 1.0 - avoided_penalty * 0.2))
        
        # Check complexity preference
        suggestion_complexity = self._calculate_text_complexity(suggestion_text)
        complexity_diff = abs(suggestion_complexity - profile.preferred_complexity)
        complexity_score = max(0, 1.0 - complexity_diff)
        score_factors.append(complexity_score)
        
        # Check formality preference
        suggestion_formality = self._calculate_text_formality(suggestion_text)
        formality_diff = abs(suggestion_formality - profile.preferred_formality)
        formality_score = max(0, 1.0 - formality_diff)
        score_factors.append(formality_score)
        
        # Check domain expertise
        domain = self._identify_domain(context)
        domain_score = profile.domain_expertise.get(domain, 0.5)
        score_factors.append(domain_score)
        
        # Check correction patterns
        suggestion_type = suggestion.get('category', 'general')
        rejection_count = profile.correction_patterns.get(suggestion_type, 0)
        rejection_penalty = min(rejection_count * 0.1, 0.5)
        score_factors.append(max(0, 1.0 - rejection_penalty))
        
        return np.mean(score_factors)
    
    def _get_base_suggestions(self, text: str, context: str) -> List[Dict]:
        """Get base suggestions (placeholder - would use existing system)"""
        # This would integrate with the existing suggestion system
        return []
    
    def _save_user_profile(self, profile: WritingPattern):
        """Save user profile to database"""
        profile_data = {
            'user_id': profile.user_id,
            'preferred_complexity': profile.preferred_complexity,
            'preferred_formality': profile.preferred_formality,
            'domain_expertise': profile.domain_expertise,
            'common_phrases': profile.common_phrases,
            'avoided_phrases': profile.avoided_phrases,
            'correction_patterns': profile.correction_patterns,
            'writing_velocity': profile.writing_velocity,
            'active_sessions': profile.active_sessions
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_profiles (user_id, profile_data, last_updated)
            VALUES (?, ?, ?)
        ''', (profile.user_id, json.dumps(profile_data), datetime.now()))
        
        conn.commit()
        conn.close()
    
    def _update_suggestion_performance(self, action: UserAction):
        """Update global suggestion performance metrics"""
        suggestion_type = self._classify_suggestion_type(action.suggested_text)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current performance data
        cursor.execute('''
            SELECT acceptance_rate, avg_confidence, total_suggestions
            FROM suggestion_performance 
            WHERE suggestion_type = ? AND context = ?
        ''', (suggestion_type, action.context))
        
        result = cursor.fetchone()
        
        if result:
            old_acceptance_rate, old_avg_confidence, total_suggestions = result
            
            # Update metrics
            new_total = total_suggestions + 1
            acceptance = 1.0 if action.action_type == 'accept' else 0.0
            new_acceptance_rate = (old_acceptance_rate * total_suggestions + acceptance) / new_total
            new_avg_confidence = (old_avg_confidence * total_suggestions + action.confidence_before) / new_total
            
            cursor.execute('''
                UPDATE suggestion_performance 
                SET acceptance_rate = ?, avg_confidence = ?, total_suggestions = ?, last_updated = ?
                WHERE suggestion_type = ? AND context = ?
            ''', (new_acceptance_rate, new_avg_confidence, new_total, datetime.now(),
                  suggestion_type, action.context))
        else:
            # Insert new record
            acceptance_rate = 1.0 if action.action_type == 'accept' else 0.0
            cursor.execute('''
                INSERT INTO suggestion_performance 
                (suggestion_type, context, acceptance_rate, avg_confidence, total_suggestions, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (suggestion_type, action.context, acceptance_rate, 
                  action.confidence_before, 1, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_learning_insights(self, user_id: str) -> Dict:
        """Get insights about user's learning and preferences"""
        if user_id not in self.user_profiles:
            return {'message': 'Insufficient data for insights'}
        
        profile = self.user_profiles[user_id]
        
        # Get recent actions
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT action_type, COUNT(*) as count
            FROM user_actions 
            WHERE user_id = ? AND timestamp > datetime('now', '-30 days')
            GROUP BY action_type
        ''', (user_id,))
        
        recent_actions = dict(cursor.fetchall())
        conn.close()
        
        insights = {
            'user_id': user_id,
            'preferred_complexity': profile.preferred_complexity,
            'preferred_formality': profile.preferred_formality,
            'domain_expertise': profile.domain_expertise,
            'recent_activity': recent_actions,
            'learning_status': 'active' if sum(recent_actions.values()) > 10 else 'limited',
            'top_domains': sorted(profile.domain_expertise.items(), 
                                key=lambda x: x[1], reverse=True)[:3],
            'suggestion_acceptance_rate': recent_actions.get('accept', 0) / 
                                        max(sum(recent_actions.values()), 1)
        }
        
        return insights

# Integration functions
def setup_adaptive_learning(db_path: str = "user_learning.db") -> AdaptiveLearningEngine:
    """Initialize the adaptive learning system"""
    return AdaptiveLearningEngine(db_path)

def record_user_feedback(learning_engine: AdaptiveLearningEngine, 
                        user_id: str, action_type: str, 
                        original: str, suggested: str, final: str,
                        context: str, confidence: float):
    """Simplified function to record user feedback"""
    action = UserAction(
        user_id=user_id,
        action_type=action_type,
        original_text=original,
        suggested_text=suggested,
        final_text=final,
        context=context,
        timestamp=datetime.now(),
        confidence_before=confidence
    )
    
    learning_engine.record_user_action(action)
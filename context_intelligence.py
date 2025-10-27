"""
Advanced Context Understanding System
Deep semantic analysis for protocol writing
"""

import torch
from transformers import AutoTokenizer, AutoModel, pipeline
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Tuple, Optional
import spacy
from dataclasses import dataclass
import re

@dataclass
class ContextualInsight:
    """Rich contextual understanding of text"""
    section_type: str
    intent: str
    medical_domain: str
    complexity_level: str
    stakeholder_audience: List[str]
    regulatory_implications: List[str]
    operational_concerns: List[str]
    confidence: float

class AdvancedContextAnalyzer:
    """Deep contextual understanding for clinical protocols"""
    
    def __init__(self):
        # Load specialized models
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.medical_ner = pipeline("ner", 
                                   model="d4data/biomedical-ner-all", 
                                   aggregation_strategy="simple")
        self.nlp = spacy.load("en_core_web_sm")
        
        # Protocol section embeddings (pre-computed from high-quality protocols)
        self.section_embeddings = self._load_section_embeddings()
        
        # Stakeholder language patterns
        self.stakeholder_patterns = self._load_stakeholder_patterns()
        
        # Regulatory context patterns
        self.regulatory_contexts = self._load_regulatory_contexts()
    
    def _load_section_embeddings(self) -> Dict[str, np.ndarray]:
        """Load pre-computed embeddings for protocol sections"""
        # In production, these would be computed from thousands of protocols
        section_examples = {
            'background': [
                "The primary objective of this study is to evaluate the efficacy and safety",
                "Previous clinical trials have demonstrated that the investigational agent",
                "The rationale for this study is based on preclinical evidence showing"
            ],
            'inclusion_criteria': [
                "Patients must be 18 years of age or older with histologically confirmed",
                "Eastern Cooperative Oncology Group performance status of 0 or 1",
                "Adequate organ function as defined by laboratory values"
            ],
            'primary_endpoint': [
                "The primary endpoint is overall survival defined as time from randomization",
                "Primary efficacy endpoint is objective response rate per RECIST v1.1",
                "The primary safety endpoint is the incidence of dose-limiting toxicities"
            ],
            'statistical_plan': [
                "A total of 300 patients will provide 80% power to detect a hazard ratio",
                "The primary analysis will be performed on the intent-to-treat population",
                "Interim analyses will be performed when 50% and 75% of events occur"
            ],
            'safety_monitoring': [
                "All adverse events will be graded according to CTCAE version 5.0",
                "A Data Safety Monitoring Board will review safety data quarterly",
                "Serious adverse events must be reported within 24 hours"
            ]
        }
        
        embeddings = {}
        for section, examples in section_examples.items():
            section_vectors = [self.sentence_model.encode(example) for example in examples]
            embeddings[section] = np.mean(section_vectors, axis=0)
        
        return embeddings
    
    def _load_stakeholder_patterns(self) -> Dict[str, Dict]:
        """Load language patterns for different stakeholders"""
        return {
            'pi_investigator': {
                'keywords': ['clinical', 'patient', 'safety', 'efficacy', 'enrollment'],
                'concerns': ['patient_safety', 'enrollment_feasibility', 'scientific_rigor'],
                'language_style': 'clinical_focused'
            },
            'statistician': {
                'keywords': ['power', 'sample_size', 'analysis', 'endpoint', 'significance'],
                'concerns': ['statistical_power', 'endpoint_clarity', 'analysis_plan'],
                'language_style': 'quantitative_precise'
            },
            'regulatory': {
                'keywords': ['compliance', 'guidance', 'approval', 'submission', 'gcp'],
                'concerns': ['regulatory_compliance', 'audit_readiness', 'submission_quality'],
                'language_style': 'formal_compliant'
            },
            'operations': {
                'keywords': ['feasible', 'site', 'capacity', 'timeline', 'resources'],
                'concerns': ['operational_feasibility', 'site_burden', 'resource_allocation'],
                'language_style': 'practical_focused'
            },
            'medical_monitor': {
                'keywords': ['safety', 'adverse', 'monitoring', 'risk', 'benefit'],
                'concerns': ['safety_monitoring', 'risk_mitigation', 'benefit_risk'],
                'language_style': 'safety_focused'
            }
        }
    
    def _load_regulatory_contexts(self) -> Dict[str, Dict]:
        """Load regulatory context patterns"""
        return {
            'fda_submission': {
                'language_requirements': ['evidence_based', 'qualified_claims', 'validated_methods'],
                'avoid_patterns': ['safe', 'proven', 'guaranteed', '100%_effective'],
                'preferred_patterns': ['demonstrated', 'well_tolerated', 'established', 'validated']
            },
            'ich_gcp_compliance': {
                'required_elements': ['informed_consent', 'adverse_event_reporting', 'data_integrity'],
                'documentation_standards': ['detailed_procedures', 'clear_responsibilities', 'audit_trail']
            },
            'endpoint_definition': {
                'must_include': ['operational_definition', 'measurement_method', 'timing_specification'],
                'fda_preferences': ['clinically_meaningful', 'validated_instruments', 'pre_specified']
            }
        }
    
    def analyze_deep_context(self, text: str) -> ContextualInsight:
        """Perform deep contextual analysis"""
        
        # Encode text
        text_embedding = self.sentence_model.encode(text)
        
        # Identify section type
        section_type = self._identify_section_type(text_embedding)
        
        # Extract medical entities
        medical_entities = self.medical_ner(text)
        
        # Determine intent and complexity
        intent = self._determine_intent(text, medical_entities)
        complexity = self._assess_complexity_level(text, medical_entities)
        
        # Identify relevant stakeholders
        stakeholders = self._identify_stakeholders(text)
        
        # Assess regulatory implications
        regulatory_implications = self._assess_regulatory_implications(text, section_type)
        
        # Identify operational concerns
        operational_concerns = self._identify_operational_concerns(text)
        
        # Determine medical domain
        medical_domain = self._determine_medical_domain(medical_entities)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(text, section_type, medical_entities)
        
        return ContextualInsight(
            section_type=section_type,
            intent=intent,
            medical_domain=medical_domain,
            complexity_level=complexity,
            stakeholder_audience=stakeholders,
            regulatory_implications=regulatory_implications,
            operational_concerns=operational_concerns,
            confidence=confidence
        )
    
    def _identify_section_type(self, text_embedding: np.ndarray) -> str:
        """Identify protocol section using embedding similarity"""
        similarities = {}
        
        for section, section_embedding in self.section_embeddings.items():
            similarity = np.dot(text_embedding, section_embedding) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(section_embedding)
            )
            similarities[section] = similarity
        
        return max(similarities, key=similarities.get)
    
    def _determine_intent(self, text: str, entities: List[Dict]) -> str:
        """Determine the intent of the text"""
        text_lower = text.lower()
        
        # Intent patterns
        if any(word in text_lower for word in ['define', 'specify', 'describe']):
            return 'definition'
        elif any(word in text_lower for word in ['evaluate', 'assess', 'measure']):
            return 'evaluation'
        elif any(word in text_lower for word in ['administer', 'dose', 'treatment']):
            return 'intervention'
        elif any(word in text_lower for word in ['monitor', 'track', 'observe']):
            return 'monitoring'
        elif any(word in text_lower for word in ['analyze', 'calculate', 'statistical']):
            return 'analysis'
        else:
            return 'general'
    
    def _assess_complexity_level(self, text: str, entities: List[Dict]) -> str:
        """Assess the complexity level of the text"""
        # Complexity indicators
        doc = self.nlp(text)
        
        avg_sentence_length = len([token for token in doc if not token.is_space]) / len(list(doc.sents))
        entity_density = len(entities) / len(text.split())
        technical_terms = len([ent for ent in entities if ent['entity_group'] in ['Disease', 'Drug', 'Test']])
        
        complexity_score = (
            (avg_sentence_length / 25.0) * 0.4 +
            entity_density * 0.3 +
            (technical_terms / max(len(entities), 1)) * 0.3
        )
        
        if complexity_score > 0.7:
            return 'high'
        elif complexity_score > 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _identify_stakeholders(self, text: str) -> List[str]:
        """Identify relevant stakeholders based on content"""
        relevant_stakeholders = []
        text_lower = text.lower()
        
        for stakeholder, patterns in self.stakeholder_patterns.items():
            # Check for relevant keywords
            keyword_matches = sum(1 for keyword in patterns['keywords'] if keyword in text_lower)
            
            if keyword_matches >= 2:  # Threshold for relevance
                relevant_stakeholders.append(stakeholder)
        
        return relevant_stakeholders if relevant_stakeholders else ['general']
    
    def _assess_regulatory_implications(self, text: str, section_type: str) -> List[str]:
        """Assess regulatory implications"""
        implications = []
        text_lower = text.lower()
        
        # Check for regulatory red flags
        for context, rules in self.regulatory_contexts.items():
            if 'avoid_patterns' in rules:
                for pattern in rules['avoid_patterns']:
                    if pattern.replace('_', ' ') in text_lower:
                        implications.append(f"{context}_violation_{pattern}")
        
        # Check for missing required elements
        if section_type == 'primary_endpoint':
            endpoint_rules = self.regulatory_contexts['endpoint_definition']
            for requirement in endpoint_rules['must_include']:
                if requirement.replace('_', ' ') not in text_lower:
                    implications.append(f"missing_{requirement}")
        
        return implications
    
    def _identify_operational_concerns(self, text: str) -> List[str]:
        """Identify operational feasibility concerns"""
        concerns = []
        text_lower = text.lower()
        
        # Frequency concerns
        if any(word in text_lower for word in ['daily', 'twice daily', 'frequent']):
            concerns.append('high_frequency_procedures')
        
        # Complexity concerns
        if any(word in text_lower for word in ['extensive', 'complex', 'specialized']):
            concerns.append('complex_procedures')
        
        # Resource concerns
        if any(word in text_lower for word in ['certified', 'expert', 'specialized equipment']):
            concerns.append('specialized_resources')
        
        # Timeline concerns
        if any(word in text_lower for word in ['immediate', 'urgent', 'stat']):
            concerns.append('tight_timelines')
        
        return concerns
    
    def _determine_medical_domain(self, entities: List[Dict]) -> str:
        """Determine the medical domain/therapeutic area"""
        # Simplified domain classification based on entities
        domain_keywords = {
            'oncology': ['cancer', 'tumor', 'chemotherapy', 'radiation', 'oncologic'],
            'cardiology': ['heart', 'cardiac', 'cardiovascular', 'blood pressure'],
            'neurology': ['brain', 'neurological', 'cognitive', 'seizure'],
            'infectious_disease': ['infection', 'antibiotic', 'viral', 'bacterial'],
            'psychiatry': ['depression', 'anxiety', 'psychiatric', 'mental health'],
            'endocrinology': ['diabetes', 'hormone', 'thyroid', 'insulin']
        }
        
        entity_text = ' '.join([ent['word'] for ent in entities]).lower()
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in entity_text for keyword in keywords):
                return domain
        
        return 'general_medicine'
    
    def _calculate_confidence(self, text: str, section_type: str, entities: List[Dict]) -> float:
        """Calculate confidence in the contextual analysis"""
        confidence_factors = []
        
        # Text length factor
        text_length_factor = min(len(text) / 200.0, 1.0)
        confidence_factors.append(text_length_factor)
        
        # Entity density factor
        entity_density = len(entities) / max(len(text.split()), 1)
        confidence_factors.append(min(entity_density * 10, 1.0))
        
        # Section type certainty (would be based on embedding similarity in practice)
        confidence_factors.append(0.8)  # Placeholder
        
        return np.mean(confidence_factors)

def generate_context_aware_suggestions(text: str, context_insight: ContextualInsight) -> List[Dict]:
    """Generate suggestions based on deep contextual understanding"""
    suggestions = []
    
    # Stakeholder-specific suggestions
    for stakeholder in context_insight.stakeholder_audience:
        stakeholder_suggestions = _get_stakeholder_suggestions(text, stakeholder, context_insight)
        suggestions.extend(stakeholder_suggestions)
    
    # Regulatory-specific suggestions
    for implication in context_insight.regulatory_implications:
        regulatory_suggestions = _get_regulatory_suggestions(text, implication)
        suggestions.extend(regulatory_suggestions)
    
    # Operational-specific suggestions  
    for concern in context_insight.operational_concerns:
        operational_suggestions = _get_operational_suggestions(text, concern)
        suggestions.extend(operational_suggestions)
    
    return suggestions

def _get_stakeholder_suggestions(text: str, stakeholder: str, context: ContextualInsight) -> List[Dict]:
    """Get suggestions tailored to specific stakeholders"""
    suggestions = []
    
    if stakeholder == 'statistician' and 'sample size' in text.lower():
        suggestions.append({
            'type': 'stakeholder_specific',
            'stakeholder': 'statistician',
            'suggestion': 'Include power calculation details and statistical assumptions',
            'rationale': 'Statisticians need explicit power calculations for sample size justification',
            'confidence': 0.9
        })
    
    elif stakeholder == 'regulatory' and context.section_type == 'primary_endpoint':
        suggestions.append({
            'type': 'stakeholder_specific', 
            'stakeholder': 'regulatory',
            'suggestion': 'Ensure endpoint definition includes operational details and validation',
            'rationale': 'Regulatory reviewers require detailed endpoint specifications',
            'confidence': 0.95
        })
    
    return suggestions

def _get_regulatory_suggestions(text: str, implication: str) -> List[Dict]:
    """Get suggestions for regulatory implications"""
    suggestions = []
    
    if 'fda_submission_violation' in implication:
        suggestions.append({
            'type': 'regulatory_compliance',
            'violation': implication,
            'suggestion': 'Replace absolute safety claims with evidence-based language',
            'rationale': 'FDA guidance recommends avoiding absolute safety claims',
            'confidence': 0.9
        })
    
    return suggestions

def _get_operational_suggestions(text: str, concern: str) -> List[Dict]:
    """Get suggestions for operational concerns"""
    suggestions = []
    
    if concern == 'high_frequency_procedures':
        suggestions.append({
            'type': 'operational_feasibility',
            'concern': concern,
            'suggestion': 'Consider site capacity and propose alternative monitoring strategies',
            'rationale': 'High-frequency procedures may exceed site operational capacity',
            'confidence': 0.85
        })
    
    return suggestions
"""
Protocol Success Scoring System
Analyzes protocol database to identify successful patterns and language
"""

import json
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

@dataclass
class ProtocolSuccess:
    """Protocol success metrics"""
    protocol_id: str
    success_score: float
    approval_status: str
    amendment_count: int
    timeline_efficiency: float
    regulatory_compliance_score: float
    recruitment_success: float
    success_factors: List[str]
    risk_factors: List[str]

@dataclass
class SuccessPattern:
    """Successful language/structure pattern"""
    pattern_id: str
    pattern_type: str  # language, structure, endpoint, etc.
    pattern_text: str
    success_correlation: float
    therapeutic_area: str
    phase: str
    frequency: int
    confidence: float
    examples: List[str]

class ProtocolSuccessScorer:
    """Analyzes protocol database to identify success patterns"""
    
    def __init__(self):
        self.success_cache = {}
        self.pattern_cache = {}
        self.success_metrics = {}
        self.learning_data = {}
        
        # Success indicators
        self.success_indicators = {
            "approval_keywords": [
                "approved", "successful", "met primary endpoint", "statistically significant",
                "regulatory approval", "FDA approval", "EMA approval", "positive results"
            ],
            "failure_keywords": [
                "failed", "terminated early", "futility", "failed to meet endpoint",
                "safety concerns", "discontinued", "negative results", "no significant difference"
            ],
            "amendment_indicators": [
                "protocol amendment", "substantial amendment", "protocol modification",
                "change in", "revised protocol", "protocol update"
            ]
        }
        
        # Language quality indicators
        self.quality_indicators = {
            "clear_language": [
                "will be", "must be", "defined as", "according to", "per protocol",
                "within ± ", "every", "at least", "no more than", "exactly"
            ],
            "vague_language": [
                "as needed", "appropriate", "reasonable", "sufficient", "adequate",
                "regular", "frequent", "occasional", "as tolerated", "if necessary"
            ],
            "regulatory_language": [
                "ICH-GCP", "FDA guidance", "regulatory requirement", "CFR", "good clinical practice",
                "standard of care", "institutional review board", "IRB", "ethics committee"
            ]
        }
    
    async def analyze_protocol_success(self, protocol_database, ml_client):
        """Analyze all protocols in database for success patterns"""
        logger.info("📊 Analyzing protocol database for success patterns...")
        
        try:
            # Query all protocols
            results = protocol_database.query(
                vector=[0.5] * 1024,
                top_k=2000,  # Analyze large sample
                include_metadata=True
            )
            
            protocol_successes = []
            
            for match in results.matches:
                metadata = match.metadata
                text = metadata.get("text", "")
                
                if len(text) < 200:
                    continue
                
                # Calculate success score
                success_data = await self._calculate_success_score(metadata, text, ml_client)
                if success_data:
                    protocol_successes.append(success_data)
            
            # Analyze patterns from successful protocols
            await self._identify_success_patterns(protocol_successes, ml_client)
            
            logger.info(f"✅ Analyzed {len(protocol_successes)} protocols for success patterns")
            
        except Exception as e:
            logger.error(f"Protocol success analysis failed: {e}")
    
    async def _calculate_success_score(self, metadata: Dict, text: str, ml_client) -> Optional[ProtocolSuccess]:
        """Calculate success score for a single protocol"""
        try:
            protocol_id = metadata.get("protocol_id", hash(text[:100]))
            
            # Calculate individual metrics
            approval_score = self._calculate_approval_score(metadata, text)
            amendment_score = self._calculate_amendment_score(metadata, text)
            timeline_score = self._calculate_timeline_score(metadata, text)
            compliance_score = self._calculate_compliance_score(text)
            recruitment_score = self._calculate_recruitment_score(metadata, text)
            
            # Overall success score (weighted average)
            success_score = (
                approval_score * 0.35 +
                amendment_score * 0.25 +
                timeline_score * 0.15 +
                compliance_score * 0.15 +
                recruitment_score * 0.10
            )
            
            # Identify success and risk factors
            success_factors = self._identify_success_factors(text, success_score)
            risk_factors = self._identify_risk_factors(text, success_score)
            
            return ProtocolSuccess(
                protocol_id=str(protocol_id),
                success_score=success_score,
                approval_status=metadata.get("approval_status", "unknown"),
                amendment_count=self._count_amendments(text),
                timeline_efficiency=timeline_score,
                regulatory_compliance_score=compliance_score,
                recruitment_success=recruitment_score,
                success_factors=success_factors,
                risk_factors=risk_factors
            )
            
        except Exception as e:
            logger.warning(f"Could not calculate success score: {e}")
            return None
    
    def _calculate_approval_score(self, metadata: Dict, text: str) -> float:
        """Calculate approval success score"""
        # Check metadata for explicit approval status
        approval_status = metadata.get("approval_status", "").lower()
        if "approved" in approval_status:
            return 0.9
        elif "failed" in approval_status or "terminated" in approval_status:
            return 0.1
        
        # Analyze text for success/failure indicators
        text_lower = text.lower()
        
        success_count = sum(1 for keyword in self.success_indicators["approval_keywords"] 
                           if keyword in text_lower)
        failure_count = sum(1 for keyword in self.success_indicators["failure_keywords"] 
                           if keyword in text_lower)
        
        if success_count > failure_count:
            return min(0.8, 0.5 + (success_count - failure_count) * 0.1)
        elif failure_count > success_count:
            return max(0.2, 0.5 - (failure_count - success_count) * 0.1)
        
        return 0.5  # Neutral if no clear indicators
    
    def _calculate_amendment_score(self, metadata: Dict, text: str) -> float:
        """Calculate amendment/modification score (fewer amendments = higher score)"""
        amendment_count = self._count_amendments(text)
        
        # Score based on amendment frequency
        if amendment_count == 0:
            return 0.9
        elif amendment_count <= 2:
            return 0.7
        elif amendment_count <= 5:
            return 0.5
        else:
            return 0.3
    
    def _count_amendments(self, text: str) -> int:
        """Count protocol amendments mentioned in text"""
        amendment_count = 0
        for indicator in self.success_indicators["amendment_indicators"]:
            amendment_count += len(re.findall(indicator, text, re.IGNORECASE))
        return amendment_count
    
    def _calculate_timeline_score(self, metadata: Dict, text: str) -> float:
        """Calculate timeline efficiency score"""
        # Look for timeline-related issues
        text_lower = text.lower()
        
        efficiency_indicators = [
            "ahead of schedule", "on time", "completed as planned", "met timeline",
            "efficient recruitment", "rapid enrollment"
        ]
        
        delay_indicators = [
            "delayed", "behind schedule", "extended timeline", "recruitment challenges",
            "slow enrollment", "timeline extension"
        ]
        
        efficiency_score = sum(1 for indicator in efficiency_indicators if indicator in text_lower)
        delay_score = sum(1 for indicator in delay_indicators if indicator in text_lower)
        
        if efficiency_score > delay_score:
            return min(0.9, 0.6 + efficiency_score * 0.1)
        elif delay_score > efficiency_score:
            return max(0.2, 0.6 - delay_score * 0.1)
        
        return 0.6  # Default neutral score
    
    def _calculate_compliance_score(self, text: str) -> float:
        """Calculate regulatory compliance score"""
        text_lower = text.lower()
        
        # Count regulatory language usage
        regulatory_count = sum(1 for phrase in self.quality_indicators["regulatory_language"] 
                              if phrase in text_lower)
        
        # Count clear vs vague language
        clear_count = sum(1 for phrase in self.quality_indicators["clear_language"] 
                         if phrase in text_lower)
        vague_count = sum(1 for phrase in self.quality_indicators["vague_language"] 
                         if phrase in text_lower)
        
        # Calculate compliance score
        regulatory_score = min(0.4, regulatory_count * 0.05)
        clarity_score = min(0.6, (clear_count - vague_count) * 0.02) if clear_count > vague_count else 0
        
        return max(0.1, regulatory_score + clarity_score)
    
    def _calculate_recruitment_score(self, metadata: Dict, text: str) -> float:
        """Calculate recruitment success score"""
        text_lower = text.lower()
        
        recruitment_success = [
            "successful recruitment", "met enrollment", "completed recruitment",
            "rapid enrollment", "enrollment exceeded", "target achieved"
        ]
        
        recruitment_issues = [
            "recruitment challenges", "slow enrollment", "enrollment difficulties",
            "failed to recruit", "recruitment terminated", "enrollment suspended"
        ]
        
        success_indicators = sum(1 for phrase in recruitment_success if phrase in text_lower)
        issue_indicators = sum(1 for phrase in recruitment_issues if phrase in text_lower)
        
        if success_indicators > issue_indicators:
            return min(0.9, 0.6 + success_indicators * 0.1)
        elif issue_indicators > success_indicators:
            return max(0.2, 0.6 - issue_indicators * 0.1)
        
        return 0.6
    
    def _identify_success_factors(self, text: str, success_score: float) -> List[str]:
        """Identify factors contributing to protocol success"""
        factors = []
        text_lower = text.lower()
        
        if success_score > 0.7:
            # Look for specific success factors
            if any(phrase in text_lower for phrase in ["clear objectives", "well-defined", "specific criteria"]):
                factors.append("Clear objectives and criteria")
            
            if any(phrase in text_lower for phrase in ["adequate sample size", "statistical power", "power calculation"]):
                factors.append("Appropriate statistical design")
            
            if any(phrase in text_lower for phrase in ["experienced investigator", "qualified site", "established center"]):
                factors.append("Experienced investigation team")
            
            if any(phrase in text_lower for phrase in ["regulatory guidance", "ICH-GCP", "standard of care"]):
                factors.append("Strong regulatory compliance")
            
            if any(phrase in text_lower for phrase in ["patient-centric", "patient reported", "quality of life"]):
                factors.append("Patient-focused design")
        
        return factors
    
    def _identify_risk_factors(self, text: str, success_score: float) -> List[str]:
        """Identify factors that may contribute to protocol risk"""
        factors = []
        text_lower = text.lower()
        
        if success_score < 0.5:
            # Look for risk factors
            if any(phrase in text_lower for phrase in ["complex design", "multiple endpoints", "complicated"]):
                factors.append("Complex protocol design")
            
            if any(phrase in text_lower for phrase in ["as needed", "appropriate", "reasonable"]):
                factors.append("Vague language and criteria")
            
            if any(phrase in text_lower for phrase in ["rare disease", "limited population", "difficult recruitment"]):
                factors.append("Recruitment challenges")
            
            if any(phrase in text_lower for phrase in ["novel endpoint", "exploratory", "experimental"]):
                factors.append("High-risk endpoints")
        
        return factors
    
    async def _identify_success_patterns(self, protocol_successes: List[ProtocolSuccess], ml_client):
        """Identify successful language and structure patterns"""
        logger.info("🔍 Identifying successful patterns from high-performing protocols...")
        
        # Separate high and low performing protocols
        high_performers = [p for p in protocol_successes if p.success_score > 0.7]
        low_performers = [p for p in protocol_successes if p.success_score < 0.4]
        
        logger.info(f"Analyzing {len(high_performers)} high-performers vs {len(low_performers)} low-performers")
        
        # Extract patterns from high performers
        success_patterns = []
        pattern_id = 0
        
        # Language patterns
        for protocol in high_performers:
            patterns = self._extract_language_patterns(protocol)
            for pattern in patterns:
                success_patterns.append(SuccessPattern(
                    pattern_id=f"lang_{pattern_id}",
                    pattern_type="language",
                    pattern_text=pattern["text"],
                    success_correlation=protocol.success_score,
                    therapeutic_area=pattern.get("therapeutic_area", "general"),
                    phase=pattern.get("phase", "general"),
                    frequency=1,
                    confidence=0.8,
                    examples=[pattern["text"]]
                ))
                pattern_id += 1
        
        # Consolidate similar patterns
        self.pattern_cache = self._consolidate_patterns(success_patterns)
        
        logger.info(f"✅ Identified {len(self.pattern_cache)} success patterns")
    
    def _extract_language_patterns(self, protocol: ProtocolSuccess) -> List[Dict]:
        """Extract successful language patterns from high-performing protocol"""
        # This would extract specific successful phrases
        # For now, return success factors as patterns
        patterns = []
        
        for factor in protocol.success_factors:
            patterns.append({
                "text": factor,
                "type": "success_factor",
                "score": protocol.success_score
            })
        
        return patterns
    
    def _consolidate_patterns(self, patterns: List[SuccessPattern]) -> Dict[str, SuccessPattern]:
        """Consolidate similar patterns to avoid duplicates"""
        consolidated = {}
        
        for pattern in patterns:
            # Simple consolidation based on pattern text similarity
            key = pattern.pattern_text.lower().strip()
            
            if key in consolidated:
                # Update frequency and confidence
                existing = consolidated[key]
                existing.frequency += 1
                existing.confidence = min(0.95, existing.confidence + 0.05)
                existing.examples.append(pattern.pattern_text)
            else:
                consolidated[key] = pattern
        
        return consolidated
    
    def get_success_recommendations(self, therapeutic_area: str, phase: str, 
                                  current_text: str) -> List[Dict]:
        """Get recommendations based on successful patterns"""
        recommendations = []
        
        # Filter patterns by therapeutic area and phase
        relevant_patterns = [
            pattern for pattern in self.pattern_cache.values()
            if (pattern.therapeutic_area == therapeutic_area or pattern.therapeutic_area == "general")
            and (pattern.phase == phase or pattern.phase == "general")
            and pattern.success_correlation > 0.7
        ]
        
        # Sort by success correlation and frequency
        relevant_patterns.sort(key=lambda x: (x.success_correlation, x.frequency), reverse=True)
        
        # Generate recommendations
        for pattern in relevant_patterns[:5]:  # Top 5 recommendations
            if pattern.pattern_text.lower() not in current_text.lower():
                recommendations.append({
                    "type": "success_pattern",
                    "recommendation": f"Consider including: {pattern.pattern_text}",
                    "rationale": f"This pattern appears in {pattern.frequency} high-performing {therapeutic_area} protocols",
                    "confidence": pattern.confidence,
                    "success_correlation": pattern.success_correlation
                })
        
        return recommendations
    
    def get_scorer_stats(self) -> Dict:
        """Get success scorer statistics"""
        return {
            "protocols_analyzed": len(self.success_cache),
            "success_patterns_identified": len(self.pattern_cache),
            "high_performers": len([p for p in self.success_cache.values() if p.success_score > 0.7]),
            "low_performers": len([p for p in self.success_cache.values() if p.success_score < 0.4]),
            "average_success_score": np.mean([p.success_score for p in self.success_cache.values()]) if self.success_cache else 0
        }

# Global success scorer instance  
_success_scorer = None

async def get_success_scorer():
    """Get or create global success scorer"""
    global _success_scorer
    if _success_scorer is None:
        _success_scorer = ProtocolSuccessScorer()
    return _success_scorer
"""
Sophisticated Intelligent Authoring Assistant
Real-time inline writing guidance with clinical intelligence
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class WritingGuidance:
    """Sophisticated writing guidance with clinical intelligence"""
    suggestion_id: str
    text_span: Tuple[int, int]  # (start, end) positions
    original_text: str
    suggestion_type: str  # clarity, feasibility, regulatory, style
    severity: str  # critical, high, medium, low
    title: str
    description: str
    suggestions: List[str]
    rationale: str
    evidence: str
    clinical_score: float
    compliance_risk: float
    confidence: float
    examples: List[str]
    
@dataclass
class ChangeIntelligence:
    """Smart change tracking and analysis"""
    change_id: str
    change_type: str  # substantive, formatting, editorial
    impact_level: str  # critical, moderate, minor
    affects_compliance: bool
    affects_feasibility: bool
    reviewer_category: str
    suggested_response: str
    stakeholder_alignment: float

class SophisticatedAuthoringEngine:
    """Advanced real-time writing guidance system"""
    
    def __init__(self):
        self.guidance_patterns = self._load_sophisticated_patterns()
        self.regulatory_database = self._load_regulatory_patterns()
        self.feasibility_rules = self._load_feasibility_rules()
        self.style_guidelines = self._load_style_guidelines()
        self.reviewer_patterns = self._load_reviewer_patterns()
        
        # Clinical intelligence integration
        self.clinical_client = None
        
    def _load_sophisticated_patterns(self) -> Dict:
        """Load sophisticated writing guidance patterns"""
        return {
            "clarity_improvements": {
                "vague_terms": {
                    "patterns": [
                        (r"\bas\s+needed\b", "Specify exact timing: 'every 12 hours ± 1 hour' or 'PRN with minimum 6-hour interval'"),
                        (r"\bappropriate\b", "Define specific criteria: 'meeting inclusion criteria' or 'as per protocol guidelines'"),
                        (r"\bsufficient\b", "Quantify: 'adequate sample size (n≥20)' or 'minimum 72-hour washout period'"),
                        (r"\breasonable\b", "Use objective criteria: 'within protocol-defined parameters' or 'medically acceptable'"),
                        (r"\bas\s+tolerated\b", "Specify: 'with dose reduction per protocol if Grade 2+ toxicity'"),
                        (r"\bregular\b(?:\s+(?:monitoring|assessment))", "Define frequency: 'weekly for first month, then monthly'"),
                        (r"\bclose\s+monitoring\b", "Specify: 'vital signs every 4 hours for 24 hours post-dose'")
                    ],
                    "examples": [
                        "❌ 'Monitor as needed' → ✅ 'Monitor vital signs every 4 hours during infusion and for 2 hours post-infusion'",
                        "❌ 'Appropriate dose' → ✅ 'Starting dose of 100 mg/m² with escalation per protocol Table 3'"
                    ]
                },
                "precision_language": {
                    "patterns": [
                        (r"\bmay\s+be\s+given\b", "Use definitive language: 'will be administered' or 'should be given'"),
                        (r"\bshould\s+consider\b", "Be specific: 'must evaluate' or 'will assess'"),
                        (r"\bif\s+possible\b", "Define conditions: 'when medically appropriate' or 'per investigator discretion'"),
                        (r"\bunless\s+contraindicated\b", "List specific contraindications or reference protocol section")
                    ]
                }
            },
            "operational_feasibility": {
                "site_burden": {
                    "patterns": [
                        (r"daily\s+(?:visits|assessments)", "Consider site capacity: suggest weekly or twice-weekly schedule"),
                        (r"every\s+\d+\s+hours", "Verify 24/7 staffing availability at participating sites"),
                        (r"continuous\s+monitoring", "Ensure sites have appropriate monitoring capabilities"),
                        (r"real[- ]time\s+reporting", "Confirm sites have electronic reporting systems")
                    ],
                    "feasibility_flags": [
                        "High-frequency visits may exceed site capacity",
                        "Complex procedures require specialized training",
                        "Multiple simultaneous assessments create scheduling conflicts"
                    ]
                },
                "timeline_realism": {
                    "patterns": [
                        (r"within\s+24\s+hours", "Verify sites can meet rapid turnaround requirements"),
                        (r"same\s+day", "Consider time zone differences and site operating hours"),
                        (r"immediate(?:ly)?", "Define acceptable timeframe: 'within 2 hours' or 'during business hours'")
                    ]
                }
            },
            "regulatory_compliance": {
                "fda_guidance": {
                    "patterns": [
                        (r"\bsafe(?:ty)?\b(?!\s+(?:population|profile|assessment))", "Use evidence-based language: 'well-tolerated' or 'acceptable safety profile'"),
                        (r"\bproven\b", "Replace with: 'demonstrated' or 'evidence supports'"),
                        (r"\bguaranteed?\b", "Use: 'expected based on prior studies' or 'anticipated outcome'"),
                        (r"\b100%\s+(?:safe|effective)\b", "Avoid absolute claims: 'high response rate observed'"),
                        (r"\bno\s+side\s+effects\b", "Use: 'manageable safety profile' or 'expected adverse events'")
                    ],
                    "evidence_requirements": [
                        "Claims must be supported by clinical data",
                        "Absolute statements require substantial evidence",
                        "Safety language must be qualified and evidence-based"
                    ]
                },
                "ich_gcp": {
                    "patterns": [
                        (r"\bconsent\b(?!\s+(?:form|process))", "Specify: 'written informed consent' per ICH-GCP"),
                        (r"\bdocument(?:ation)?\b", "Ensure: 'source document verification' and 'audit trail'"),
                        (r"\btraining\b", "Include: 'GCP-compliant training with documented competency'")
                    ]
                }
            }
        }
    
    def _load_regulatory_patterns(self) -> Dict:
        """Load regulatory compliance patterns from major guidance documents"""
        return {
            "fda_guidance_patterns": {
                "clinical_trial_endpoints": [
                    "Primary endpoints must be clearly defined and clinically meaningful",
                    "Surrogate endpoints require validation for regulatory acceptance",
                    "Patient-reported outcomes need validated instruments"
                ],
                "safety_reporting": [
                    "Serious adverse events require 24-hour reporting",
                    "Safety run-in phases recommended for novel therapies",
                    "Data monitoring committee oversight for Phase II/III trials"
                ]
            },
            "ema_guidance_patterns": {
                "pediatric_considerations": [
                    "Pediatric investigation plans required for new drugs",
                    "Age-appropriate formulations and dosing strategies",
                    "Ethical considerations for pediatric trial design"
                ]
            }
        }
    
    def _load_feasibility_rules(self) -> Dict:
        """Load operational feasibility assessment rules"""
        return {
            "site_capacity_rules": {
                "visit_frequency": {
                    "daily_visits": {"max_sustainable": 30, "warning_threshold": 20},
                    "weekly_visits": {"max_sustainable": 100, "warning_threshold": 75},
                    "monthly_visits": {"optimal_range": (50, 200)}
                },
                "procedure_complexity": {
                    "high_complexity": ["cardiac catheterization", "bone marrow biopsy", "lumbar puncture"],
                    "moderate_complexity": ["echocardiogram", "CT scan", "endoscopy"],
                    "low_complexity": ["blood draw", "vital signs", "questionnaire"]
                }
            },
            "timeline_feasibility": {
                "recruitment_rates": {
                    "rare_disease": {"monthly_rate": (1, 3), "screening_failure": 0.4},
                    "common_disease": {"monthly_rate": (5, 15), "screening_failure": 0.25},
                    "healthy_volunteers": {"monthly_rate": (10, 30), "screening_failure": 0.15}
                }
            }
        }
    
    def _load_style_guidelines(self) -> Dict:
        """Load protocol writing style guidelines"""
        return {
            "protocol_sections": {
                "objectives": {
                    "style_requirements": [
                        "Use active voice: 'This study will evaluate' not 'This study is designed to evaluate'",
                        "Be specific about outcomes: 'assess efficacy by measuring tumor response'",
                        "Avoid redundancy: don't repeat primary/secondary in objective statements"
                    ]
                },
                "inclusion_criteria": {
                    "style_requirements": [
                        "Use positive language: 'Patients with' not 'Patients must have'",
                        "Order by importance: most critical criteria first",
                        "Be specific about measurements: 'ECOG PS ≤2' not 'good performance status'"
                    ]
                }
            }
        }
    
    def _load_reviewer_patterns(self) -> Dict:
        """Load patterns from experienced protocol reviewers"""
        return {
            "common_reviewer_comments": {
                "statistical_issues": [
                    "Sample size justification unclear",
                    "Primary endpoint not suitable for intended analysis",
                    "Multiple comparisons not addressed",
                    "Interim analysis plan missing"
                ],
                "operational_concerns": [
                    "Timeline unrealistic for projected enrollment",
                    "Site selection criteria too restrictive",
                    "Training requirements excessive",
                    "Data collection burden too high"
                ],
                "regulatory_gaps": [
                    "Safety stopping rules inadequately defined",
                    "Informed consent language unclear",
                    "Drug accountability procedures missing",
                    "Quality assurance plan insufficient"
                ]
            },
            "reviewer_expertise_areas": {
                "biostatistician": ["sample_size", "endpoints", "analysis_plan", "interim_analysis"],
                "regulatory_affairs": ["safety", "compliance", "labeling", "post_market"],
                "clinical_operations": ["feasibility", "site_selection", "training", "logistics"],
                "medical_affairs": ["clinical_rationale", "safety_profile", "dosing", "indication"]
            }
        }
    
    async def analyze_text_sophisticated(self, text: str, context: str = "protocol") -> List[WritingGuidance]:
        """Provide sophisticated real-time writing guidance"""
        
        guidance_items = []
        
        # 1. Clinical Intelligence Analysis
        if self.clinical_client:
            try:
                clinical_analysis = await self.clinical_client.analyze_clinical_text(text)
                if clinical_analysis:
                    # Use clinical scores to enhance guidance
                    base_clinical_score = clinical_analysis.clinical_score
                    compliance_risk = clinical_analysis.compliance_risk
                else:
                    base_clinical_score = 0.5
                    compliance_risk = 0.3
            except:
                base_clinical_score = 0.5
                compliance_risk = 0.3
        else:
            base_clinical_score = 0.5
            compliance_risk = 0.3
        
        # 2. Clarity Improvements
        clarity_guidance = self._analyze_clarity(text, base_clinical_score)
        guidance_items.extend(clarity_guidance)
        
        # 3. Feasibility Assessment
        feasibility_guidance = self._analyze_feasibility(text, base_clinical_score)
        guidance_items.extend(feasibility_guidance)
        
        # 4. Regulatory Compliance
        regulatory_guidance = self._analyze_regulatory_compliance(text, compliance_risk)
        guidance_items.extend(regulatory_guidance)
        
        # 5. Style and Best Practices
        style_guidance = self._analyze_style(text, context)
        guidance_items.extend(style_guidance)
        
        # Sort by priority (critical issues first)
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        guidance_items.sort(key=lambda x: (priority_order.get(x.severity, 4), -x.confidence))
        
        return guidance_items[:10]  # Top 10 most important guidance items
    
    def _analyze_clarity(self, text: str, clinical_score: float) -> List[WritingGuidance]:
        """Analyze text for clarity improvements"""
        guidance_items = []
        
        clarity_patterns = self.guidance_patterns["clarity_improvements"]
        
        for category, pattern_data in clarity_patterns.items():
            for pattern, suggestion in pattern_data["patterns"]:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    start, end = match.span()
                    original = match.group()
                    
                    guidance = WritingGuidance(
                        suggestion_id=f"clarity_{start}_{end}",
                        text_span=(start, end),
                        original_text=original,
                        suggestion_type="clarity",
                        severity="high" if clinical_score > 0.7 else "medium",
                        title=f"Clarify '{original}'",
                        description=suggestion,
                        suggestions=self._generate_specific_suggestions(original, pattern),
                        rationale="Vague language creates implementation variability and potential protocol deviations",
                        evidence="DMID reviewer feedback: 'Specific timing requirements reduce site confusion'",
                        clinical_score=clinical_score,
                        compliance_risk=0.2,
                        confidence=0.85 + (clinical_score * 0.1),
                        examples=pattern_data.get("examples", [])
                    )
                    guidance_items.append(guidance)
        
        return guidance_items
    
    def _analyze_feasibility(self, text: str, clinical_score: float) -> List[WritingGuidance]:
        """Analyze operational feasibility concerns"""
        guidance_items = []
        
        feasibility_patterns = self.guidance_patterns["operational_feasibility"]
        
        # Check for high-frequency visits
        daily_pattern = r"daily\s+(?:visits|assessments|monitoring)"
        for match in re.finditer(daily_pattern, text, re.IGNORECASE):
            start, end = match.span()
            
            guidance = WritingGuidance(
                suggestion_id=f"feasibility_{start}_{end}",
                text_span=(start, end),
                original_text=match.group(),
                suggestion_type="feasibility",
                severity="critical",
                title="High site burden detected",
                description="Daily visits create significant operational burden and may limit site participation",
                suggestions=[
                    "Consider weekly visits with remote monitoring",
                    "Implement home nursing for routine assessments",
                    "Use digital health tools for daily data collection"
                ],
                rationale="Sites report difficulty maintaining daily visit schedules beyond 2-3 weeks",
                evidence="Site feasibility surveys show 60% reduction in participation for daily visit protocols",
                clinical_score=clinical_score,
                compliance_risk=0.7,
                confidence=0.9,
                examples=[
                    "✅ 'Weekly visits with daily patient-reported symptom diaries'",
                    "✅ 'Days 1-3: daily visits, then weekly through Week 12'"
                ]
            )
            guidance_items.append(guidance)
        
        return guidance_items
    
    def _analyze_regulatory_compliance(self, text: str, compliance_risk: float) -> List[WritingGuidance]:
        """Analyze regulatory compliance issues"""
        guidance_items = []
        
        regulatory_patterns = self.guidance_patterns["regulatory_compliance"]["fda_guidance"]
        
        for pattern, replacement in regulatory_patterns["patterns"]:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start, end = match.span()
                
                guidance = WritingGuidance(
                    suggestion_id=f"regulatory_{start}_{end}",
                    text_span=(start, end),
                    original_text=match.group(),
                    suggestion_type="regulatory",
                    severity="critical" if compliance_risk > 0.5 else "high",
                    title="Regulatory compliance issue",
                    description=f"FDA guidance recommends avoiding absolute claims. {replacement}",
                    suggestions=self._generate_regulatory_alternatives(match.group()),
                    rationale="Absolute safety/efficacy claims require substantial evidence and may trigger FDA scrutiny",
                    evidence="FDA Guidance: 'Clinical Trial Considerations' (2022)",
                    clinical_score=0.9,
                    compliance_risk=compliance_risk,
                    confidence=0.95,
                    examples=[
                        "❌ 'This drug is safe' → ✅ 'Demonstrated acceptable safety profile in Phase I'",
                        "❌ 'Proven effective' → ✅ 'Evidence supports efficacy in target population'"
                    ]
                )
                guidance_items.append(guidance)
        
        return guidance_items
    
    def _analyze_style(self, text: str, context: str) -> List[WritingGuidance]:
        """Analyze writing style and best practices"""
        guidance_items = []
        
        # Check for passive voice
        passive_patterns = [
            r"\bis\s+(?:being\s+)?(?:conducted|performed|administered|given)",
            r"\bwill\s+be\s+(?:conducted|performed|administered|given)",
            r"\bare\s+(?:being\s+)?(?:conducted|performed|administered|given)"
        ]
        
        for pattern in passive_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start, end = match.span()
                
                guidance = WritingGuidance(
                    suggestion_id=f"style_{start}_{end}",
                    text_span=(start, end),
                    original_text=match.group(),
                    suggestion_type="style",
                    severity="low",
                    title="Consider active voice",
                    description="Active voice improves clarity and reduces ambiguity about responsibility",
                    suggestions=[
                        "Investigators will conduct...",
                        "Study staff will perform...",
                        "Participants will receive..."
                    ],
                    rationale="Active voice clearly identifies who performs each action",
                    evidence="Protocol writing best practices recommend active voice for clarity",
                    clinical_score=0.6,
                    compliance_risk=0.1,
                    confidence=0.7,
                    examples=[
                        "❌ 'Assessments will be conducted' → ✅ 'Investigators will conduct assessments'",
                        "❌ 'Drug will be administered' → ✅ 'Study staff will administer study drug'"
                    ]
                )
                guidance_items.append(guidance)
        
        return guidance_items
    
    def _generate_specific_suggestions(self, original: str, pattern: str) -> List[str]:
        """Generate context-specific suggestions for improvements"""
        
        suggestion_map = {
            r"\bas\s+needed\b": [
                "every 12 hours ± 1 hour",
                "PRN with minimum 6-hour interval", 
                "when clinically indicated (maximum twice daily)",
                "per institutional guidelines"
            ],
            r"\bappropriate\b": [
                "meeting protocol-defined criteria",
                "as per investigator assessment",
                "according to standard practice guidelines",
                "within acceptable clinical parameters"
            ],
            r"\bsufficient\b": [
                "adequate sample size (n≥20 per group)",
                "minimum 72-hour washout period",
                "at least 3 months follow-up",
                "≥80% power to detect clinically meaningful difference"
            ]
        }
        
        for pattern_key, suggestions in suggestion_map.items():
            if re.search(pattern_key, pattern, re.IGNORECASE):
                return suggestions
        
        return ["Specify exact criteria", "Define measurable parameters", "Use objective language"]
    
    def _generate_regulatory_alternatives(self, original: str) -> List[str]:
        """Generate regulatory-compliant alternatives"""
        
        alternatives_map = {
            "safe": ["well-tolerated", "demonstrated acceptable safety profile", "manageable safety profile"],
            "proven": ["demonstrated efficacy", "evidence supports", "clinical data indicate"], 
            "guaranteed": ["expected based on prior studies", "anticipated outcome", "projected result"],
            "100%": ["high response rate", "majority of patients", "substantial proportion"],
            "no side effects": ["manageable adverse events", "expected safety profile", "tolerable side effect profile"]
        }
        
        original_lower = original.lower()
        for key, alternatives in alternatives_map.items():
            if key in original_lower:
                return alternatives
        
        return ["Use evidence-based language", "Qualify with supporting data", "Avoid absolute claims"]

# Integration function for main API
async def get_sophisticated_authoring_guidance(text: str, context: str = "protocol") -> List[Dict]:
    """Get sophisticated authoring guidance (API integration function)"""
    
    engine = SophisticatedAuthoringEngine()
    
    # Get clinical client if available
    try:
        from clinical_analysis_client import get_clinical_client
        engine.clinical_client = await get_clinical_client()
    except:
        pass
    
    guidance_items = await engine.analyze_text_sophisticated(text, context)
    
    # Convert to API response format
    return [
        {
            "suggestion_id": item.suggestion_id,
            "text_span": item.text_span,
            "original": item.original_text,
            "type": item.suggestion_type,
            "severity": item.severity,
            "title": item.title,
            "description": item.description,
            "suggestions": item.suggestions,
            "rationale": item.rationale,
            "evidence": item.evidence,
            "clinical_score": item.clinical_score,
            "compliance_risk": item.compliance_risk,
            "confidence": item.confidence,
            "examples": item.examples,
            "intelligence_level": "sophisticated_9.5"
        }
        for item in guidance_items
    ]
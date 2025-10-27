"""
Protocol Intelligence Database
Comprehensive database of phrase improvements, regulatory guidance, and reviewer patterns
"""

# Real-time Writing Suggestions Database
PHRASE_IMPROVEMENTS = {
    # Timing & Dosing Precision
    "as needed": {
        "suggestions": [
            "every 12 hours ± 1 hour",
            "as clinically indicated (maximum twice daily)",
            "PRN with minimum 6-hour interval"
        ],
        "rationale": "Vague timing creates implementation variability",
        "category": "clarity",
        "severity": "medium",
        "context": "dosing, administration"
    },
    
    "as tolerated": {
        "suggestions": [
            "with dose reduction per protocol schedule if Grade 2+ toxicity",
            "with specified stopping criteria (see Section 6.3)",
            "with pre-defined dose modification guidelines"
        ],
        "rationale": "Requires specific criteria for dose modifications",
        "category": "clarity",
        "severity": "medium",
        "context": "dosing, safety"
    },
    
    "frequent monitoring": {
        "suggestions": [
            "weekly laboratory assessments for first 4 weeks",
            "monitoring per attached schedule (Table 3)",
            "assessments every 2 weeks ± 3 days"
        ],
        "rationale": "Operational teams need specific schedules",
        "category": "feasibility",
        "severity": "high",
        "context": "monitoring, procedures"
    },

    # Regulatory-Compliant Language
    "safe": {
        "suggestions": [
            "well-tolerated",
            "demonstrated acceptable safety profile",
            "safety findings consistent with known profile"
        ],
        "rationale": "FDA avoids absolute safety claims",
        "category": "regulatory",
        "severity": "high",
        "context": "safety, conclusions"
    },
    
    "proven": {
        "suggestions": [
            "demonstrated efficacy in",
            "shown to be effective in",
            "evidence supports efficacy in"
        ],
        "rationale": "Avoid absolute efficacy claims without specific evidence",
        "category": "regulatory",
        "severity": "high",
        "context": "efficacy, background"
    },
    
    "significant": {
        "suggestions": [
            "statistically significant (p<0.05)",
            "clinically meaningful",
            "pre-specified difference of X%"
        ],
        "rationale": "Define statistical vs clinical significance",
        "category": "regulatory",
        "severity": "medium",
        "context": "statistics, endpoints"
    },

    # Operational Feasibility
    "daily visits": {
        "suggestions": [
            "visits on Days 1, 3, 7, then weekly",
            "intensive monitoring phase (Days 1-7) then per schedule",
            "consider site capacity - maximum 2 study visits/week"
        ],
        "rationale": "Daily visits often exceed site capacity",
        "category": "feasibility",
        "severity": "high",
        "context": "visits, procedures"
    },
    
    "extensive testing": {
        "suggestions": [
            "core laboratory assessments per Table X",
            "specified biomarker panel (see Appendix A)",
            "focused assessment battery (estimated 45 minutes)"
        ],
        "rationale": "Define scope to assess feasibility",
        "category": "feasibility",
        "severity": "medium",
        "context": "procedures, assessments"
    },

    # Endpoint Clarity
    "symptom improvement": {
        "suggestions": [
            "≥30% reduction in [Specific Scale] score",
            "improvement defined as decrease of ≥10 points on [Scale]",
            "clinical response per established criteria (Reference X)"
        ],
        "rationale": "Endpoints must be measurable and validated",
        "category": "clarity",
        "severity": "high",
        "context": "endpoints, outcomes"
    },
    
    "quality of life": {
        "suggestions": [
            "quality of life per EORTC QLQ-C30",
            "health-related quality of life (HRQOL) using validated instrument",
            "patient-reported outcomes via [specific questionnaire]"
        ],
        "rationale": "Specify validated instruments for QOL assessment",
        "category": "regulatory",
        "severity": "medium",
        "context": "endpoints, PRO"
    },

    # Statistical Language
    "appropriate sample size": {
        "suggestions": [
            "sample size of N=X provides 80% power to detect...",
            "based on power calculation (see Section 8.1)",
            "justified sample size assuming X% response rate"
        ],
        "rationale": "Sample size must be justified with calculations",
        "category": "regulatory",
        "severity": "high",
        "context": "statistics, design"
    },
    
    "statistical analysis": {
        "suggestions": [
            "statistical analysis per pre-specified plan (Section 8)",
            "primary analysis using intent-to-treat population",
            "statistical methods detailed in SAP"
        ],
        "rationale": "Analysis plan must be pre-specified",
        "category": "regulatory",
        "severity": "medium",
        "context": "statistics, analysis"
    }
}

# Regulatory Phrase Patterns
REGULATORY_PATTERNS = {
    "avoid_absolute_claims": {
        "triggers": ["guaranteed", "completely safe", "100% effective", "no side effects"],
        "replacement_guidance": "Use evidence-based language with appropriate qualifiers",
        "examples": {
            "guaranteed": "expected based on prior studies",
            "completely safe": "demonstrated acceptable safety profile",
            "100% effective": "high response rate (X%) observed",
            "no side effects": "well-tolerated with manageable safety profile"
        }
    },
    
    "endpoint_specificity": {
        "triggers": ["improved", "better", "reduced", "increased"],
        "replacement_guidance": "Quantify improvements with specific thresholds",
        "examples": {
            "improved symptoms": "≥30% reduction in symptom severity score",
            "better outcomes": "increased overall survival (hazard ratio <0.7)",
            "reduced toxicity": "Grade 3+ adverse events <15%",
            "increased response": "objective response rate ≥40%"
        }
    }
}

# Operational Feasibility Flags
FEASIBILITY_CONCERNS = {
    "high_frequency_visits": {
        "patterns": ["daily", "twice daily", "every day", "continuous"],
        "concern": "Visit frequency may exceed site capacity",
        "suggestions": [
            "Consider remote monitoring options",
            "Cluster procedures to minimize visits",
            "Assess site capacity during feasibility"
        ]
    },
    
    "complex_procedures": {
        "patterns": ["multiple biopsies", "extensive imaging", "complex PK sampling"],
        "concern": "Procedure complexity may impact enrollment",
        "suggestions": [
            "Provide detailed procedure manual",
            "Consider central vs local assessment",
            "Include procedure training requirements"
        ]
    },
    
    "specialized_expertise": {
        "patterns": ["specialized equipment", "certified technician", "expert assessment"],
        "concern": "May limit site eligibility",
        "suggestions": [
            "Define minimum site qualifications",
            "Consider central reading/assessment",
            "Include training and certification plan"
        ]
    }
}

# Comment Categorization Patterns
REVIEWER_COMMENT_CATEGORIES = {
    "design_clarification": {
        "keywords": ["unclear", "specify", "define", "clarify", "ambiguous"],
        "patterns": ["What is meant by", "Please clarify", "This is unclear"],
        "action_templates": [
            "Add definition to Section X",
            "Clarify in protocol text",
            "Provide detailed explanation"
        ]
    },
    
    "feasibility_concern": {
        "keywords": ["feasible", "capacity", "realistic", "achievable", "practical"],
        "patterns": ["Is this feasible", "Consider site capacity", "This may be challenging"],
        "action_templates": [
            "Conduct site capacity assessment",
            "Revise procedures to be more practical",
            "Add feasibility considerations"
        ]
    },
    
    "regulatory_compliance": {
        "keywords": ["FDA", "ICH", "GCP", "guidance", "regulation", "compliant"],
        "patterns": ["Per FDA guidance", "ICH requires", "Consider regulatory"],
        "action_templates": [
            "Update per regulatory guidance",
            "Add regulatory justification",
            "Ensure compliance with standards"
        ]
    },
    
    "statistical_concern": {
        "keywords": ["power", "sample size", "analysis", "statistical", "endpoint"],
        "patterns": ["Statistical plan", "Power calculation", "Primary endpoint"],
        "action_templates": [
            "Revise statistical analysis plan",
            "Update power calculations",
            "Clarify primary endpoint definition"
        ]
    },
    
    "safety_consideration": {
        "keywords": ["safety", "adverse", "toxicity", "monitoring", "risk"],
        "patterns": ["Safety concern", "Consider monitoring", "Risk mitigation"],
        "action_templates": [
            "Add safety monitoring procedures",
            "Update risk mitigation strategies",
            "Enhance safety assessments"
        ]
    }
}

# High-Quality Protocol Examples (for pattern learning)
EXEMPLARY_PHRASES = {
    "precise_timing": [
        "Study drug administered orally once daily at approximately the same time each day (±2 hours)",
        "Assessments performed within 7 days prior to each cycle (28-day cycles)",
        "Blood samples collected at pre-dose, 1, 2, 4, 8, and 24 hours post-dose"
    ],
    
    "clear_endpoints": [
        "Primary endpoint: Overall survival defined as time from randomization to death from any cause",
        "Objective response rate per RECIST v1.1 criteria assessed every 8 weeks ± 1 week",
        "Time to progression defined as time from randomization to first documented disease progression"
    ],
    
    "regulatory_compliant": [
        "This study will be conducted in accordance with ICH-GCP, applicable regulatory requirements, and institutional policies",
        "Safety monitoring will include continuous assessment of adverse events per CTCAE v5.0",
        "Data Safety Monitoring Board will review safety data after every 10 patients"
    ]
}

def get_phrase_suggestions(text_segment, context="general"):
    """
    Get intelligent suggestions for a text segment
    """
    suggestions = []
    
    for phrase, data in PHRASE_IMPROVEMENTS.items():
        if phrase.lower() in text_segment.lower():
            if context == "general" or context in data.get("context", ""):
                suggestions.append({
                    "original": phrase,
                    "suggestions": data["suggestions"],
                    "rationale": data["rationale"],
                    "category": data["category"],
                    "severity": data["severity"],
                    "position": text_segment.lower().find(phrase.lower())
                })
    
    return suggestions

def categorize_reviewer_comment(comment_text):
    """
    Categorize reviewer comments and suggest actions
    """
    comment_lower = comment_text.lower()
    
    for category, data in REVIEWER_COMMENT_CATEGORIES.items():
        # Check for keywords
        if any(keyword in comment_lower for keyword in data["keywords"]):
            return {
                "category": category,
                "confidence": "high",
                "suggested_actions": data["action_templates"]
            }
        
        # Check for patterns
        if any(pattern.lower() in comment_lower for pattern in data["patterns"]):
            return {
                "category": category,
                "confidence": "medium",
                "suggested_actions": data["action_templates"]
            }
    
    return {
        "category": "general_comment",
        "confidence": "low",
        "suggested_actions": ["Review and address comment", "Consider protocol revision"]
    }

def assess_feasibility_concerns(text_segment):
    """
    Identify potential operational feasibility issues
    """
    concerns = []
    text_lower = text_segment.lower()
    
    for concern_type, data in FEASIBILITY_CONCERNS.items():
        for pattern in data["patterns"]:
            if pattern in text_lower:
                concerns.append({
                    "type": concern_type,
                    "concern": data["concern"],
                    "suggestions": data["suggestions"],
                    "position": text_lower.find(pattern)
                })
    
    return concerns
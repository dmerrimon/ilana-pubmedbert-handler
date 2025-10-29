"""
Protocol Data Analyzer
Processes 16,730 real anonymized protocols to extract training data for robust ML system
"""

import os
import re
import json
import logging
import asyncio
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import glob
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ProtocolMetadata:
    """Extracted metadata from real protocol files"""
    protocol_id: str
    title: str
    phase: str
    therapeutic_area: str
    compound_name: str
    indication: str
    study_type: str
    sponsor: str
    
    # Timeline data
    original_date: Optional[datetime]
    current_date: Optional[datetime]
    development_duration: Optional[int]  # days
    
    # Amendment data
    version: str
    amendment_count: int
    amendment_history: List[Dict]
    
    # Success indicators
    success_score: float
    completion_status: str
    
    # Text characteristics
    total_length: int
    sections: List[str]
    endpoint_types: List[str]
    

class ProtocolDataAnalyzer:
    """Analyzes 16,730 real anonymized protocols to extract ML training data"""
    
    def __init__(self, data_path: str = "/Users/donmerriman/Ilana Labs/ilana-core/data/anonymized_texts"):
        self.data_path = Path(data_path)
        self.protocols = {}
        self.therapeutic_patterns = {}
        self.phase_patterns = {}
        self.success_patterns = {}
        
        # Processing configuration for large dataset
        self.total_protocols = 16730  # Total real protocols available
        self.batch_size = 100  # Process in batches to manage memory
        self.sample_size = 2000  # Sample for initial analysis (can be increased)
        
        # Classification patterns
        self.phase_indicators = {
            "Phase I": [
                "phase i", "phase 1", "first in human", "dose escalation", "maximum tolerated dose",
                "mtd", "dose limiting toxicity", "dlt", "safety run-in", "dose finding"
            ],
            "Phase II": [
                "phase ii", "phase 2", "efficacy", "response rate", "objective response",
                "progression free survival", "preliminary efficacy", "proof of concept"
            ],
            "Phase III": [
                "phase iii", "phase 3", "pivotal", "registration", "confirmatory",
                "superiority", "non-inferiority", "overall survival", "randomized controlled"
            ],
            "Phase IV": [
                "phase iv", "phase 4", "post-marketing", "real world", "observational",
                "registry", "post-approval", "pharmacovigilance"
            ]
        }
        
        self.therapeutic_indicators = {
            "oncology": [
                "cancer", "tumor", "oncology", "carcinoma", "lymphoma", "melanoma", "sarcoma",
                "metastatic", "malignant", "neoplasm", "chemotherapy", "targeted therapy",
                "immunotherapy", "solid tumor", "hematologic", "leukemia"
            ],
            "neurology": [
                "neurological", "alzheimer", "parkinson", "multiple sclerosis", "epilepsy",
                "stroke", "dementia", "cognitive", "neurodegeneration", "brain", "cns"
            ],
            "cardiology": [
                "cardiac", "cardiovascular", "heart", "myocardial", "coronary", "hypertension",
                "heart failure", "arrhythmia", "atherosclerosis", "vascular"
            ],
            "diabetes": [
                "diabetes", "diabetic", "glucose", "insulin", "glycemic", "hba1c",
                "type 1 diabetes", "type 2 diabetes", "metabolic"
            ],
            "immunology": [
                "autoimmune", "rheumatoid arthritis", "lupus", "inflammatory bowel",
                "crohn", "psoriasis", "immune", "immunosuppressive"
            ],
            "infectious_disease": [
                "infection", "infectious", "antimicrobial", "antibiotic", "antiviral",
                "hepatitis", "hiv", "tuberculosis", "bacterial", "viral"
            ],
            "respiratory": [
                "asthma", "copd", "pulmonary", "respiratory", "lung", "bronchial",
                "cystic fibrosis", "pneumonia", "pulmonary fibrosis"
            ]
        }
    
    async def analyze_all_protocols(self, sample_size: Optional[int] = None):
        """Analyze protocols from 16,730 real anonymized protocol files"""
        logger.info(f"🔍 Analyzing protocols in {self.data_path}")
        
        protocol_files = list(self.data_path.glob("protocol_*.txt"))
        total_files = len(protocol_files)
        logger.info(f"Found {total_files} protocol files (16,730 real anonymized protocols)")
        
        # Use sample size if specified, otherwise use configured sample size
        analysis_size = sample_size or self.sample_size
        if analysis_size < total_files:
            # Sample randomly for representative analysis
            import random
            protocol_files = random.sample(protocol_files, analysis_size)
            logger.info(f"Analyzing random sample of {analysis_size} protocols for efficiency")
        
        # Process in batches to manage memory
        processed_count = 0
        failed_count = 0
        
        for i in range(0, len(protocol_files), self.batch_size):
            batch = protocol_files[i:i + self.batch_size]
            logger.info(f"Processing batch {i//self.batch_size + 1}/{(len(protocol_files)-1)//self.batch_size + 1} ({len(batch)} protocols)")
            
            for file_path in batch:
                try:
                    metadata = await self._analyze_single_protocol(file_path)
                    if metadata:
                        self.protocols[metadata.protocol_id] = metadata
                        processed_count += 1
                    
                    if processed_count % 100 == 0:
                        logger.info(f"Successfully processed {processed_count} protocols...")
                        
                except Exception as e:
                    failed_count += 1
                    logger.warning(f"Failed to analyze {file_path}: {e}")
        
        logger.info(f"✅ Successfully analyzed {processed_count} protocols ({failed_count} failures)")
        logger.info(f"📊 Dataset: {total_files} total protocols, {processed_count} analyzed")
        
        # Build classification patterns from this rich dataset
        self._build_therapeutic_patterns()
        self._build_phase_patterns()
        self._build_success_patterns()
        
        return self.protocols
    
    async def _analyze_single_protocol(self, file_path: Path) -> Optional[ProtocolMetadata]:
        """Analyze a single protocol file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if len(content) < 1000:  # Skip very short files
                return None
            
            # Extract basic info
            protocol_id = file_path.stem
            title = self._extract_title(content)
            
            # Extract phase
            phase = self._classify_phase(content)
            
            # Extract therapeutic area
            therapeutic_area = self._classify_therapeutic_area(content)
            
            # Extract compound/drug info
            compound_name = self._extract_compound_name(content)
            indication = self._extract_indication(content)
            study_type = self._extract_study_type(content)
            sponsor = self._extract_sponsor(content)
            
            # Extract timeline data
            dates = self._extract_dates(content)
            original_date = dates.get("original")
            current_date = dates.get("current")
            development_duration = None
            if original_date and current_date:
                development_duration = (current_date - original_date).days
            
            # Extract amendment data
            version = self._extract_version(content)
            amendment_history = self._extract_amendment_history(content)
            amendment_count = len(amendment_history)
            
            # Calculate success score
            success_score = self._calculate_success_score(content, amendment_count, development_duration)
            completion_status = self._determine_completion_status(content)
            
            # Extract text characteristics
            sections = self._extract_sections(content)
            endpoint_types = self._extract_endpoint_types(content)
            
            return ProtocolMetadata(
                protocol_id=protocol_id,
                title=title,
                phase=phase,
                therapeutic_area=therapeutic_area,
                compound_name=compound_name,
                indication=indication,
                study_type=study_type,
                sponsor=sponsor,
                original_date=original_date,
                current_date=current_date,
                development_duration=development_duration,
                version=version,
                amendment_count=amendment_count,
                amendment_history=amendment_history,
                success_score=success_score,
                completion_status=completion_status,
                total_length=len(content),
                sections=sections,
                endpoint_types=endpoint_types
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
            return None
    
    def _extract_title(self, content: str) -> str:
        """Extract protocol title"""
        # Look for official title
        title_match = re.search(r"Official Title:\s*([^\n]+)", content, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
        
        # Look for first meaningful line
        lines = content.split('\n')
        for line in lines[2:10]:  # Skip first couple lines
            line = line.strip()
            if len(line) > 20 and not line.startswith(('Document', 'Study', 'Version')):
                return line[:200]  # Limit length
        
        return "Unknown Title"
    
    def _classify_phase(self, content: str) -> str:
        """Classify study phase"""
        content_lower = content.lower()
        
        # Count indicators for each phase
        phase_scores = {}
        for phase, indicators in self.phase_indicators.items():
            score = sum(content_lower.count(indicator) for indicator in indicators)
            phase_scores[phase] = score
        
        # Return phase with highest score
        if phase_scores:
            best_phase = max(phase_scores, key=phase_scores.get)
            if phase_scores[best_phase] > 0:
                return best_phase
        
        return "Unknown Phase"
    
    def _classify_therapeutic_area(self, content: str) -> str:
        """Classify therapeutic area"""
        content_lower = content.lower()
        
        # Count indicators for each area
        area_scores = {}
        for area, indicators in self.therapeutic_indicators.items():
            score = sum(content_lower.count(indicator) for indicator in indicators)
            area_scores[area] = score
        
        # Return area with highest score
        if area_scores:
            best_area = max(area_scores, key=area_scores.get)
            if area_scores[best_area] > 0:
                return best_area
        
        return "general"
    
    def _extract_compound_name(self, content: str) -> str:
        """Extract compound/drug name"""
        # Look for test drug or compound mentions
        patterns = [
            r"Test drug:\s*([^\n/]+)",
            r"Study drug:\s*([^\n/]+)",
            r"Compound:\s*([^\n/]+)",
            r"Drug:\s*([^\n/]+)",
            r"([A-Z]{2,}[-\s]?\d{4,})",  # Pattern like BAY 1163877
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                compound = match.group(1).strip()
                if len(compound) > 2 and len(compound) < 50:
                    return compound
        
        return "Unknown Compound"
    
    def _extract_indication(self, content: str) -> str:
        """Extract medical indication"""
        # Look for indication patterns
        patterns = [
            r"in (?:subjects|patients) with ([^.]+)",
            r"indication:\s*([^\n]+)",
            r"disease:\s*([^\n]+)",
            r"condition:\s*([^\n]+)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                indication = match.strip()
                if len(indication) > 5 and len(indication) < 100:
                    return indication
        
        return "Unknown Indication"
    
    def _extract_study_type(self, content: str) -> str:
        """Extract study design type"""
        content_lower = content.lower()
        
        if "randomized" in content_lower:
            if "controlled" in content_lower:
                return "Randomized Controlled Trial"
            return "Randomized Trial"
        elif "open label" in content_lower or "open-label" in content_lower:
            return "Open-Label"
        elif "double blind" in content_lower or "double-blind" in content_lower:
            return "Double-Blind"
        elif "single arm" in content_lower:
            return "Single-Arm"
        elif "dose escalation" in content_lower:
            return "Dose Escalation"
        
        return "Unknown Design"
    
    def _extract_sponsor(self, content: str) -> str:
        """Extract sponsor information"""
        patterns = [
            r"Sponsor:\s*([^\n]+)",
            r"Company:\s*([^\n]+)",
            r"Manufacturer:\s*([^\n]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                sponsor = match.group(1).strip()
                if len(sponsor) > 2:
                    return sponsor
        
        # Look for pharmaceutical company patterns in text
        pharma_patterns = [
            r"(Bayer|Novartis|Pfizer|Roche|GSK|Merck|AstraZeneca|BMS|J&J|Sanofi)"
        ]
        
        for pattern in pharma_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Unknown Sponsor"
    
    def _extract_dates(self, content: str) -> Dict[str, Optional[datetime]]:
        """Extract relevant dates"""
        dates = {"original": None, "current": None}
        
        # Look for date patterns
        date_patterns = [
            r"(\d{1,2}\s+\w+\s+\d{4})",  # 17 Oct 2018
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})",  # 17/10/2018
            r"(\w+\s+\d{1,2},?\s+\d{4})"  # October 17, 2018
        ]
        
        found_dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    # Try different date formats
                    for fmt in ["%d %b %Y", "%d/%m/%Y", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"]:
                        try:
                            date_obj = datetime.strptime(match, fmt)
                            found_dates.append(date_obj)
                            break
                        except ValueError:
                            continue
                except:
                    continue
        
        if found_dates:
            found_dates.sort()
            dates["original"] = found_dates[0]
            dates["current"] = found_dates[-1]
        
        return dates
    
    def _extract_version(self, content: str) -> str:
        """Extract protocol version"""
        version_match = re.search(r"Version\s+(\d+\.?\d*)", content, re.IGNORECASE)
        if version_match:
            return version_match.group(1)
        
        return "1.0"
    
    def _extract_amendment_history(self, content: str) -> List[Dict]:
        """Extract amendment history"""
        amendments = []
        
        # Look for amendment patterns
        amendment_patterns = [
            r"Amendment\s+no\.?\s*(\d+)[^)]*\(([^)]+)\)",
            r"Amendment\s+(\d+)[^,]*,\s*([^,\n]+)"
        ]
        
        for pattern in amendment_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                amendments.append({
                    "number": match[0],
                    "description": match[1].strip() if len(match) > 1 else "",
                    "type": "global" if "global" in match[1].lower() else "local" if len(match) > 1 and "local" in match[1].lower() else "unknown"
                })
        
        return amendments
    
    def _calculate_success_score(self, content: str, amendment_count: int, development_duration: Optional[int]) -> float:
        """Calculate protocol success score"""
        score = 0.5  # Base score
        
        # Amendment penalty (more amendments = lower score)
        if amendment_count == 0:
            score += 0.3
        elif amendment_count <= 2:
            score += 0.1
        elif amendment_count <= 5:
            score -= 0.1
        else:
            score -= 0.3
        
        # Timeline efficiency
        if development_duration:
            if development_duration < 365:  # Less than 1 year
                score += 0.2
            elif development_duration < 1095:  # Less than 3 years
                score += 0.1
            elif development_duration > 2190:  # More than 6 years
                score -= 0.2
        
        # Success indicators in text
        content_lower = content.lower()
        success_terms = ["completed", "successful", "approved", "positive results", "met endpoint"]
        failure_terms = ["terminated", "failed", "discontinued", "negative results", "futility"]
        
        success_count = sum(1 for term in success_terms if term in content_lower)
        failure_count = sum(1 for term in failure_terms if term in content_lower)
        
        score += (success_count - failure_count) * 0.1
        
        return max(0.0, min(1.0, score))
    
    def _determine_completion_status(self, content: str) -> str:
        """Determine protocol completion status"""
        content_lower = content.lower()
        
        if any(term in content_lower for term in ["completed", "finished", "concluded"]):
            return "completed"
        elif any(term in content_lower for term in ["ongoing", "recruiting", "active"]):
            return "ongoing"
        elif any(term in content_lower for term in ["terminated", "discontinued", "suspended"]):
            return "terminated"
        
        return "unknown"
    
    def _extract_sections(self, content: str) -> List[str]:
        """Extract protocol sections"""
        sections = []
        
        section_patterns = [
            r"^\s*(\d+\.?\d*\.?\s*[A-Z][^.\n]+)$",
            r"^\s*([A-Z][A-Z\s]{5,30})$"
        ]
        
        lines = content.split('\n')
        for line in lines:
            for pattern in section_patterns:
                if re.match(pattern, line):
                    section = line.strip()
                    if len(section) > 5 and len(section) < 100:
                        sections.append(section)
                    break
        
        return sections[:20]  # Limit to first 20 sections
    
    def _extract_endpoint_types(self, content: str) -> List[str]:
        """Extract endpoint types"""
        endpoints = []
        content_lower = content.lower()
        
        endpoint_patterns = {
            "primary": r"primary\s+endpoint[s]?:\s*([^.]{10,200})",
            "secondary": r"secondary\s+endpoint[s]?:\s*([^.]{10,200})",
            "exploratory": r"exploratory\s+endpoint[s]?:\s*([^.]{10,200})"
        }
        
        for endpoint_type, pattern in endpoint_patterns.items():
            matches = re.findall(pattern, content_lower)
            for match in matches:
                endpoints.append(f"{endpoint_type}: {match.strip()[:100]}")
        
        return endpoints
    
    def _build_therapeutic_patterns(self):
        """Build therapeutic area patterns from analyzed protocols"""
        for protocol in self.protocols.values():
            area = protocol.therapeutic_area
            if area not in self.therapeutic_patterns:
                self.therapeutic_patterns[area] = {
                    "protocols": [],
                    "compounds": set(),
                    "indications": set(),
                    "success_score": 0.0
                }
            
            self.therapeutic_patterns[area]["protocols"].append(protocol.protocol_id)
            self.therapeutic_patterns[area]["compounds"].add(protocol.compound_name)
            self.therapeutic_patterns[area]["indications"].add(protocol.indication)
        
        # Calculate average success scores
        for area, data in self.therapeutic_patterns.items():
            protocols = [self.protocols[pid] for pid in data["protocols"]]
            if protocols:
                data["success_score"] = sum(p.success_score for p in protocols) / len(protocols)
                data["compounds"] = list(data["compounds"])
                data["indications"] = list(data["indications"])
    
    def _build_phase_patterns(self):
        """Build phase-specific patterns"""
        for protocol in self.protocols.values():
            phase = protocol.phase
            if phase not in self.phase_patterns:
                self.phase_patterns[phase] = {
                    "protocols": [],
                    "study_types": set(),
                    "endpoints": [],
                    "success_score": 0.0
                }
            
            self.phase_patterns[phase]["protocols"].append(protocol.protocol_id)
            self.phase_patterns[phase]["study_types"].add(protocol.study_type)
            self.phase_patterns[phase]["endpoints"].extend(protocol.endpoint_types)
        
        # Calculate average success scores
        for phase, data in self.phase_patterns.items():
            protocols = [self.protocols[pid] for pid in data["protocols"]]
            if protocols:
                data["success_score"] = sum(p.success_score for p in protocols) / len(protocols)
                data["study_types"] = list(data["study_types"])
    
    def _build_success_patterns(self):
        """Build success patterns from high-performing protocols"""
        high_performers = [p for p in self.protocols.values() if p.success_score > 0.7]
        low_performers = [p for p in self.protocols.values() if p.success_score < 0.4]
        
        self.success_patterns = {
            "high_performers": {
                "count": len(high_performers),
                "avg_amendments": sum(p.amendment_count for p in high_performers) / len(high_performers) if high_performers else 0,
                "common_therapeutic_areas": {},
                "common_phases": {},
                "common_study_types": {}
            },
            "low_performers": {
                "count": len(low_performers),
                "avg_amendments": sum(p.amendment_count for p in low_performers) / len(low_performers) if low_performers else 0,
                "common_therapeutic_areas": {},
                "common_phases": {},
                "common_study_types": {}
            }
        }
        
        # Analyze patterns in high vs low performers
        for category, protocols in [("high_performers", high_performers), ("low_performers", low_performers)]:
            for protocol in protocols:
                # Count therapeutic areas
                area = protocol.therapeutic_area
                if area not in self.success_patterns[category]["common_therapeutic_areas"]:
                    self.success_patterns[category]["common_therapeutic_areas"][area] = 0
                self.success_patterns[category]["common_therapeutic_areas"][area] += 1
                
                # Count phases
                phase = protocol.phase
                if phase not in self.success_patterns[category]["common_phases"]:
                    self.success_patterns[category]["common_phases"][phase] = 0
                self.success_patterns[category]["common_phases"][phase] += 1
                
                # Count study types
                study_type = protocol.study_type
                if study_type not in self.success_patterns[category]["common_study_types"]:
                    self.success_patterns[category]["common_study_types"][study_type] = 0
                self.success_patterns[category]["common_study_types"][study_type] += 1
    
    def save_analysis_results(self, output_file: str = "protocol_analysis_results.json"):
        """Save analysis results to JSON file"""
        results = {
            "summary": {
                "total_protocols": len(self.protocols),
                "therapeutic_areas": len(self.therapeutic_patterns),
                "phases": len(self.phase_patterns),
                "avg_success_score": sum(p.success_score for p in self.protocols.values()) / len(self.protocols) if self.protocols else 0
            },
            "protocols": {pid: asdict(protocol) for pid, protocol in self.protocols.items()},
            "therapeutic_patterns": self.therapeutic_patterns,
            "phase_patterns": self.phase_patterns,
            "success_patterns": self.success_patterns
        }
        
        # Convert datetime objects to strings for JSON serialization
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=convert_datetime)
        
        logger.info(f"✅ Saved analysis results to {output_file}")
        return results
    
    def get_analysis_summary(self) -> Dict:
        """Get summary of analysis results"""
        if not self.protocols:
            return {"error": "No protocols analyzed yet"}
        
        return {
            "total_protocols": len(self.protocols),
            "therapeutic_areas": list(self.therapeutic_patterns.keys()),
            "phases": list(self.phase_patterns.keys()),
            "high_performers": len([p for p in self.protocols.values() if p.success_score > 0.7]),
            "low_performers": len([p for p in self.protocols.values() if p.success_score < 0.4]),
            "avg_success_score": sum(p.success_score for p in self.protocols.values()) / len(self.protocols),
            "avg_amendment_count": sum(p.amendment_count for p in self.protocols.values()) / len(self.protocols),
            "completion_status_distribution": {
                status: len([p for p in self.protocols.values() if p.completion_status == status])
                for status in set(p.completion_status for p in self.protocols.values())
            }
        }

# Global analyzer instance
_protocol_analyzer = None

async def get_protocol_analyzer():
    """Get or create global protocol analyzer"""
    global _protocol_analyzer
    if _protocol_analyzer is None:
        _protocol_analyzer = ProtocolDataAnalyzer()
    return _protocol_analyzer
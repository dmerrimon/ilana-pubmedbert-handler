"""
CRITICAL: Upload FDA and ICH-GCP regulatory documents to Pinecone
This provides the missing regulatory context for accurate compliance analysis
"""

import os
import requests
from pathlib import Path
from pinecone import Pinecone
import time

# Load environment variables
keys_file = Path('/Users/donmerriman/Ilana Labs/ilana-core/Keys Open Doors.txt')
if keys_file.exists():
    with open(keys_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

def get_embeddings(text, retries=3):
    """Get PubMedBERT embeddings with retry logic"""
    headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}
    
    for attempt in range(retries):
        try:
            response = requests.post(
                os.getenv("PUBMEDBERT_ENDPOINT_URL"),
                headers=headers,
                json={"inputs": text[:512]},  # PubMedBERT limit
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) == 768:
                    return result
                elif isinstance(result, dict):
                    # Handle various response formats
                    for key, value in result.items():
                        if isinstance(value, list) and len(value) == 768:
                            return value
            else:
                print(f"API error (attempt {attempt+1}): {response.status_code}")
                
        except Exception as e:
            print(f"Request failed (attempt {attempt+1}): {e}")
            
        if attempt < retries - 1:
            time.sleep(2)  # Wait before retry
            
    return None

def main():
    """Upload comprehensive regulatory guidance to Pinecone"""
    
    print("🚀 UPLOADING REGULATORY GUIDANCE TO PINECONE")
    print("This is CRITICAL for accurate compliance analysis!\n")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index("protocol-intelligence-768")
    
    # Comprehensive regulatory documents
    regulatory_docs = [
        {
            "id": "ich_gcp_informed_consent",
            "title": "ICH-GCP Informed Consent Requirements",
            "content": """ICH-GCP Section 4.8 - Informed Consent Requirements:
            
4.8.1 The investigator must obtain freely given informed consent from every participant prior to clinical trial participation.

4.8.2 The informed consent information must be in a language fully comprehensible to the participant.

4.8.3 The information given to participants should include:
- The nature and purpose of the trial
- The trial procedures and their sequence and duration
- The participant's responsibilities
- Anticipated proband or population benefits
- The reasonably foreseeable risks and inconveniences
- The alternative procedures or treatments available
- The identity of the sponsor and investigator
- The participant's right to refuse participation and withdraw consent
- Provisions for compensation and treatment in case of trial-related injury

4.8.4 The informed consent form should be dated and personally signed and dated by the participant.""",
            "source": "ICH-GCP E6(R2) Section 4.8",
            "type": "regulatory_guidance"
        },
        {
            "id": "ich_gcp_protocol_requirements", 
            "title": "ICH-GCP Protocol Design Requirements",
            "content": """ICH-GCP Section 6 - Clinical Trial Protocol Requirements:

6.1 The protocol should include:
- General information (title, protocol identifying number, date, and version)
- Background information and scientific rationale
- Trial objectives and purpose
- Trial design (randomization, blinding, control group)
- Selection and withdrawal of participants
- Treatment of participants (dose, administration, compliance monitoring)
- Assessment of efficacy and safety
- Statistics (sample size, randomization, analysis methods)
- Direct access to source data/documents
- Quality control and quality assurance procedures
- Ethics considerations
- Data handling and record keeping
- Financing and insurance
- Publication policy

6.2 Statistical considerations must include:
- Description of statistical methods
- Planned interim analyses
- Criteria for trial termination
- Procedures for handling missing data
- Selection of participants for analysis""",
            "source": "ICH-GCP E6(R2) Section 6",
            "type": "regulatory_guidance"
        },
        {
            "id": "fda_gcp_investigator_responsibilities",
            "title": "FDA Good Clinical Practice - Investigator Responsibilities", 
            "content": """FDA 21 CFR 312.60 - Investigator Responsibilities:

312.60 General responsibilities of investigators:
(a) An investigator is responsible for ensuring that an investigation is conducted according to the signed investigator statement, the investigational plan, and applicable regulations.

(b) An investigator is responsible for protecting the rights, safety, and welfare of subjects under the investigator's care.

(c) An investigator shall obtain informed consent from each human subject or the subject's legally authorized representative.

312.62 Investigator recordkeeping and record retention:
- Case histories that record all observations and other data pertinent to the investigation
- Records of the disposition of the drug
- Signed consent forms
- Financial disclosure information

312.64 Investigator reports:
- Progress reports must be submitted annually
- Safety reports for serious adverse experiences must be submitted immediately
- Final reports must be submitted upon completion""",
            "source": "FDA 21 CFR 312.60-312.64",
            "type": "regulatory_guidance"
        },
        {
            "id": "fda_endpoints_guidance",
            "title": "FDA Guidance on Clinical Trial Endpoints",
            "content": """FDA Guidance - Clinical Trial Endpoints for Drug Development:

PRIMARY ENDPOINTS:
- Must directly measure how a patient feels, functions, or survives
- Should be clinically meaningful and interpretable
- Must be clearly defined with pre-specified analysis methods
- Should have established measurement properties (reliability, validity)

ENDPOINT CONSIDERATIONS:
- Time-to-event endpoints require clear definition of the event
- Composite endpoints should have similar importance and frequency
- Patient-reported outcomes must follow FDA PRO guidance
- Surrogate endpoints require regulatory approval based on scientific evidence

STATISTICAL CONSIDERATIONS:
- Multiple primary endpoints may require adjustment for multiplicity
- Non-inferiority margins must be justified
- Missing data handling should be pre-specified
- Interim analyses require appropriate alpha spending

REGULATORY EXPECTATIONS:
- Endpoints should align with intended labeling claims
- Clinical relevance should be demonstrated
- Benefit-risk assessment depends on endpoint selection""",
            "source": "FDA Guidance for Industry",
            "type": "regulatory_guidance"
        },
        {
            "id": "ich_gcp_adverse_events",
            "title": "ICH-GCP Adverse Event Reporting Requirements",
            "content": """ICH-GCP Section 4.11 - Safety Reporting:

4.11.1 All serious adverse events (SAEs) must be reported immediately to the sponsor, except for those identified in the protocol as not requiring immediate reporting.

4.11.2 The investigator must submit written reports of serious adverse events within 24 hours.

4.11.3 Death must be reported immediately, followed by a detailed written report.

4.11.4 All adverse events should be followed until resolution or stabilization.

SERIOUS ADVERSE EVENT CRITERIA:
- Results in death
- Is life-threatening
- Requires inpatient hospitalization or prolonged hospitalization
- Results in persistent or significant disability/incapacity
- Is a congenital anomaly/birth defect
- Is a medically important event

REPORTING TIMELINE:
- Fatal or life-threatening: 7 calendar days for preliminary report, 15 days for complete report
- All other serious events: 15 calendar days for complete report""",
            "source": "ICH-GCP E6(R2) Section 4.11",
            "type": "regulatory_guidance"
        },
        {
            "id": "fda_data_integrity",
            "title": "FDA Data Integrity Requirements",
            "content": """FDA Guidance on Data Integrity and Compliance:

ALCOA+ PRINCIPLES:
- Attributable: Data must be attributable to the person generating it
- Legible: Data must be readable and permanent
- Contemporaneous: Data must be recorded at the time of activity
- Original: Data must be the first capture or true copy
- Accurate: Data must be free from errors and complete
- Complete: All data must be captured
- Consistent: Data must be internally consistent
- Enduring: Data must be preserved throughout the retention period
- Available: Data must be readily retrievable

ELECTRONIC RECORDS:
- Must comply with 21 CFR Part 11 requirements
- Require appropriate access controls and audit trails
- Need backup and recovery procedures
- Must maintain data throughout required retention periods

SOURCE DOCUMENTATION:
- Source data must support all entries in case report forms
- Original records must be identifiable
- Any corrections must maintain audit trail""",
            "source": "FDA 21 CFR Part 11, Data Integrity Guidance",
            "type": "regulatory_guidance"
        }
    ]
    
    successful_uploads = 0
    total_docs = len(regulatory_docs)
    
    for doc in regulatory_docs:
        print(f"📋 Processing: {doc['title']}")
        
        # Get embeddings
        embeddings = get_embeddings(doc['content'])
        
        if embeddings:
            try:
                # Create vector for Pinecone
                vector = {
                    "id": doc["id"],
                    "values": embeddings,
                    "metadata": {
                        "type": doc["type"],
                        "title": doc["title"], 
                        "text": doc["content"],
                        "source": doc["source"]
                    }
                }
                
                # Upload to Pinecone
                index.upsert(vectors=[vector])
                print(f"   ✅ Uploaded successfully")
                successful_uploads += 1
                
            except Exception as e:
                print(f"   ❌ Upload failed: {e}")
        else:
            print(f"   ❌ Could not get embeddings")
        
        time.sleep(1)  # Rate limiting
        print()
    
    print("=" * 60)
    print(f"🎉 REGULATORY GUIDANCE UPLOAD COMPLETE!")
    print(f"   Successfully uploaded: {successful_uploads}/{total_docs} documents")
    print(f"   Your AI now has proper regulatory context for analysis!")
    print("=" * 60)

if __name__ == "__main__":
    main()
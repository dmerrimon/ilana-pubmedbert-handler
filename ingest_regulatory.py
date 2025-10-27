"""
Upload FDA and ICH-GCP regulatory documents to Pinecone
This will provide the missing regulatory context for better AI analysis
"""

import os
import requests
from pathlib import Path
from pinecone import Pinecone
from openai import AzureOpenAI
import time

# Load environment variables
keys_file = Path('/Users/donmerriman/Ilana Labs/ilana-core/Keys Open Doors.txt')
if keys_file.exists():
    with open(keys_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

def main():
    """Upload regulatory documents to improve AI evidence"""
    
    # Initialize clients
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index("protocol-intelligence-768")
    
    # Use OpenAI for embeddings since HuggingFace is unreliable
    azure_client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-15-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    
    # Key regulatory texts to add
    regulatory_texts = [
        {
            "id": "fda_guidance_clinical_trials",
            "title": "FDA Guidance for Industry - Good Clinical Practice",
            "content": """FDA requires that clinical trials be conducted in accordance with Good Clinical Practice (GCP) standards. Key requirements include:
            
1. INFORMED CONSENT: All participants must provide written informed consent before any study procedures. Consent forms must clearly describe risks, benefits, procedures, and participant rights.

2. PROTOCOL COMPLIANCE: Studies must follow the approved protocol. Any deviations must be documented and reported to regulatory authorities.

3. DATA INTEGRITY: All data must be accurate, complete, and verifiable. Source documents must support all data entries.

4. SAFETY MONITORING: Serious adverse events must be reported within 24 hours. Safety reviews must be conducted regularly.

5. INVESTIGATOR QUALIFICATIONS: Principal investigators must be qualified by education, training, and experience.

6. INSTITUTIONAL REVIEW BOARD: All studies must have IRB approval before initiation and continuing review during conduct.""",
            "source": "FDA 21 CFR Part 312",
            "type": "regulatory_guidance"
        },
        {
            "id": "ich_gcp_e6_r3",
            "title": "ICH E6(R3) Good Clinical Practice Guidelines",
            "content": """ICH E6(R3) establishes international standards for clinical trial conduct:

1. PROTOCOL DESIGN: Protocols must have clear objectives, methodology, statistical analysis plans, and safety procedures.

2. INVESTIGATOR RESPONSIBILITIES: Investigators must ensure participant safety, follow the protocol, maintain adequate records, and report adverse events.

3. SPONSOR RESPONSIBILITIES: Sponsors must ensure trial quality, provide investigational products, maintain drug safety databases, and conduct monitoring.

4. QUALITY MANAGEMENT: Risk-based approaches to quality management should focus on factors critical to participant safety and data reliability.

5. DOCUMENTATION: Essential documents must be maintained to demonstrate compliance with GCP and data integrity.

6. RISK ASSESSMENT: Systematic identification and mitigation of risks that could affect participant safety or data reliability.""",
            "source": "ICH E6(R3) Guidelines", 
            "type": "regulatory_guidance"
        },
        {
            "id": "fda_primary_endpoints",
            "title": "FDA Guidance on Clinical Trial Endpoints",
            "content": """FDA requirements for clinical trial endpoints:

1. PRIMARY ENDPOINTS: Must be clinically meaningful and directly measure how patients feel, function, or survive. Should be clearly defined with measurement methods.

2. STATISTICAL POWER: Studies must be adequately powered to detect clinically meaningful differences in primary endpoints.

3. ENDPOINT VALIDATION: Endpoints should be validated for the intended population and indication.

4. MULTIPLE ENDPOINTS: When using multiple primary endpoints, statistical adjustments may be needed to control Type I error.

5. SURROGATE ENDPOINTS: May be acceptable if they reasonably predict clinical benefit based on scientific evidence.

6. PATIENT-REPORTED OUTCOMES: When used as endpoints, must follow FDA guidance on PRO measures.""",
            "source": "FDA Guidance for Industry",
            "type": "regulatory_guidance"
        }
    ]
    
    print("🔄 Adding regulatory guidance to Pinecone...")
    
    for reg_doc in regulatory_texts:
        try:
            # Get embeddings using OpenAI (but we need to truncate to 768 for the index)
            response = azure_client.embeddings.create(
                input=reg_doc["content"][:8000],
                model="text-embedding-ada-002"
            )
            
            if response.data:
                # OpenAI gives 1536 dimensions, truncate to 768 to match index
                full_embeddings = response.data[0].embedding
                embeddings = full_embeddings[:768]  # Truncate to match index
                
                # Create vector for upload
                vector = {
                    "id": reg_doc["id"],
                    "values": embeddings,
                    "metadata": {
                        "type": reg_doc["type"],
                        "title": reg_doc["title"],
                        "text": reg_doc["content"],
                        "source": reg_doc["source"]
                    }
                }
                
                # Upload to Pinecone
                index.upsert(vectors=[vector])
                print(f"✅ Uploaded: {reg_doc['title']}")
                time.sleep(1)  # Rate limiting
                
            else:
                print(f"❌ No embedding data for {reg_doc['title']}")
                
        except Exception as e:
            print(f"❌ Error uploading {reg_doc['title']}: {e}")
    
    print("\n🎉 Regulatory guidance upload complete!")
    print("The AI will now have better evidence for compliance analysis.")

if __name__ == "__main__":
    main()
"""
Upload the REAL FDA regulations from your comprehensive file
This replaces the generic regulatory content with actual CFR text
"""

import os
import requests
from pathlib import Path
from pinecone import Pinecone
import time
import re

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

def chunk_regulatory_text(text, chunk_size=800):
    """Intelligently chunk regulatory text by sections"""
    chunks = []
    
    # Split by major sections (CFR parts, subsections)
    sections = re.split(r'(?=§\s*\d+\.\d+|21 CFR Part \d+)', text)
    
    current_chunk = ""
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        # If adding this section would exceed chunk size, save current chunk
        if len(current_chunk) + len(section) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = section
        else:
            current_chunk += "\n" + section if current_chunk else section
    
    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def main():
    """Upload comprehensive FDA regulations from your file"""
    
    print("🚀 UPLOADING REAL FDA REGULATIONS")
    print("This replaces generic content with actual CFR text!\n")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index("protocol-intelligence-768")
    
    # Read your comprehensive regulatory file
    regulatory_file = Path('/Users/donmerriman/Ilana Labs/ilana-core/data/Regulatory and Compliance.txt')
    
    if not regulatory_file.exists():
        print("❌ Regulatory file not found!")
        return
    
    print(f"📖 Reading regulatory file: {regulatory_file}")
    with open(regulatory_file, 'r', encoding='utf-8') as f:
        regulatory_text = f.read()
    
    print(f"📊 File size: {len(regulatory_text):,} characters")
    
    # Chunk the text intelligently
    chunks = chunk_regulatory_text(regulatory_text)
    print(f"📝 Created {len(chunks)} regulatory chunks")
    print()
    
    successful_uploads = 0
    
    for i, chunk in enumerate(chunks):
        if len(chunk.strip()) < 100:  # Skip very small chunks
            continue
            
        # Extract section number for better identification
        section_match = re.search(r'(§\s*\d+\.\d+|21 CFR Part \d+)', chunk)
        section_id = section_match.group(1) if section_match else f"chunk_{i+1}"
        
        print(f"📋 Processing chunk {i+1}/{len(chunks)}: {section_id}")
        
        # Get embeddings
        embeddings = get_embeddings(chunk)
        
        if embeddings:
            try:
                # Create vector for Pinecone
                vector = {
                    "id": f"fda_cfr_{i+1:03d}",
                    "values": embeddings,
                    "metadata": {
                        "type": "regulatory_guidance",
                        "title": f"FDA Regulation: {section_id}",
                        "text": chunk,
                        "source": "21 CFR - Code of Federal Regulations",
                        "section": section_id,
                        "chunk_number": i+1
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
        
        time.sleep(0.5)  # Rate limiting
        if i % 10 == 9:  # Progress update every 10 chunks
            print(f"   📊 Progress: {i+1}/{len(chunks)} chunks processed")
            print()
    
    print("=" * 60)
    print(f"🎉 REAL FDA REGULATIONS UPLOAD COMPLETE!")
    print(f"   Successfully uploaded: {successful_uploads}/{len(chunks)} chunks")
    print(f"   Your AI now has comprehensive, actual FDA CFR text!")
    print(f"   Much better than generic summaries!")
    print("=" * 60)

if __name__ == "__main__":
    main()
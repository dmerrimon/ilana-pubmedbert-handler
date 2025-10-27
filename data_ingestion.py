"""
Data Ingestion Pipeline for Pinecone Vector Database
Processes regulatory content and clinical protocols for RAG system
"""

import os
import json
import time
import hashlib
from typing import List, Dict, Any
from pathlib import Path
import requests
from pinecone import Pinecone
from tqdm import tqdm
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIngestionPipeline:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index_name = os.getenv("PINECONE_INDEX_NAME", "protocol-intelligence-768")
        self.index = self.pc.Index(index_name)
        self.pubmedbert_url = os.getenv("PUBMEDBERT_ENDPOINT_URL", 
                                       "https://usz78oxlybv4xfh2.eastus.azure.endpoints.huggingface.cloud")
        self.hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
        
    def get_embeddings(self, text: str, retries: int = 3) -> List[float]:
        """Get PubMedBERT embeddings for text with retry logic"""
        for attempt in range(retries):
            try:
                headers = {"Authorization": f"Bearer {self.hf_api_key}"}
                response = requests.post(
                    self.pubmedbert_url,
                    headers=headers,
                    json={"inputs": text[:512]},  # Truncate to model limit
                    timeout=120  # Increased timeout to 2 minutes
                )
                response.raise_for_status()
                result = response.json()
                
                # Handle different response formats
                if isinstance(result, dict):
                    if 'embeddings' in result:
                        return result['embeddings']
                    elif 'data' in result:
                        return result['data']
                elif isinstance(result, list):
                    return result
                    
                logger.error(f"Unexpected embedding format: {type(result)}")
                return []
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}/{retries}, retrying...")
                if attempt < retries - 1:
                    time.sleep(5 * (attempt + 1))  # Exponential backoff
                continue
            except Exception as e:
                logger.error(f"Embedding failed on attempt {attempt + 1}: {e}")
                if attempt < retries - 1:
                    time.sleep(2)
                continue
                
        logger.error(f"All {retries} attempts failed for embedding")
        return []
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if len(chunk.strip()) > 50:  # Skip tiny chunks
                chunks.append(chunk.strip())
                
        return chunks
    
    def process_regulatory_content(self):
        """Process regulatory guidelines and upload to Pinecone"""
        logger.info("Processing regulatory content...")
        
        # ICH-GCP content
        ich_content = [
            {
                "text": "Informed consent is a process by which a subject voluntarily confirms his or her willingness to participate in a particular trial, after having been informed of all aspects of the trial that are relevant to the subject's decision to participate.",
                "source": "ICH-GCP E6(R2) Section 1.28",
                "type": "regulatory",
                "category": "informed_consent"
            },
            {
                "text": "Before implementing any change to the conduct of the trial or to the protocol, the investigator should obtain prior written approval from the sponsor and the IRB/IEC, except when necessary to eliminate immediate hazards to the trial subjects.",
                "source": "ICH-GCP E6(R2) Section 4.5.2",
                "type": "regulatory", 
                "category": "protocol_amendments"
            },
            {
                "text": "All clinical trial information should be recorded, handled, and stored in a way that allows its accurate reporting, interpretation and verification.",
                "source": "ICH-GCP E6(R2) Section 5.0",
                "type": "regulatory",
                "category": "data_integrity"
            },
            {
                "text": "The investigator should ensure that adequate medical care is provided to a subject for any adverse events, including clinically significant laboratory values, related to the trial.",
                "source": "ICH-GCP E6(R2) Section 4.3.1",
                "type": "regulatory",
                "category": "safety_monitoring"
            }
        ]
        
        # FDA content
        fda_content = [
            {
                "text": "No investigator may involve a human being as a subject in research covered by these regulations unless the investigator has obtained the legally effective informed consent of the subject or the subject's legally authorized representative.",
                "source": "FDA 21 CFR 50.20",
                "type": "regulatory",
                "category": "informed_consent"
            },
            {
                "text": "An IRB shall review and have authority to approve, require modifications in (to secure approval), or disapprove all research activities covered by these regulations.",
                "source": "FDA 21 CFR 56.109",
                "type": "regulatory",
                "category": "irb_oversight"
            },
            {
                "text": "Each investigator shall report to the sponsor adverse experiences that occur in the course of the investigation in accordance with the investigational plan.",
                "source": "FDA 21 CFR 312.64",
                "type": "regulatory",
                "category": "adverse_events"
            }
        ]
        
        all_regulatory = ich_content + fda_content
        vectors_to_upload = []
        
        for item in all_regulatory:
            # Generate embeddings for each regulatory text
            embeddings = self.get_embeddings(item["text"])
            if embeddings:
                vector_id = hashlib.md5(item["text"].encode()).hexdigest()
                vectors_to_upload.append({
                    "id": f"reg_{vector_id}",
                    "values": embeddings,
                    "metadata": item
                })
        
        # Upload in batches
        self.batch_upload(vectors_to_upload, "regulatory content")
        
    def process_protocol_file(self, file_path: str) -> List[Dict]:
        """Process a single protocol file and return vectors"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata from filename or content
            protocol_id = Path(file_path).stem
            
            # Chunk the protocol into smaller pieces
            chunks = self.chunk_text(content)
            vectors = []
            
            for i, chunk in enumerate(chunks):
                embeddings = self.get_embeddings(chunk)
                if embeddings:
                    vector_id = f"protocol_{protocol_id}_chunk_{i}"
                    vectors.append({
                        "id": vector_id,
                        "values": embeddings,
                        "metadata": {
                            "text": chunk,
                            "source": f"Protocol {protocol_id}",
                            "type": "protocol",
                            "protocol_id": protocol_id,
                            "chunk_index": i,
                            "file_path": file_path
                        }
                    })
            
            return vectors
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return []
    
    def batch_upload(self, vectors: List[Dict], description: str = "vectors"):
        """Upload vectors to Pinecone in batches"""
        batch_size = 100  # Pinecone batch limit
        
        for i in tqdm(range(0, len(vectors), batch_size), desc=f"Uploading {description}"):
            batch = vectors[i:i + batch_size]
            try:
                self.index.upsert(vectors=batch)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Batch upload failed: {e}")
                time.sleep(5)  # Wait longer on error
    
    def process_protocols_directory(self, protocols_dir: str):
        """Process all protocol files in a directory"""
        logger.info(f"Processing protocols from {protocols_dir}...")
        
        protocol_files = []
        for ext in ['*.txt', '*.pdf', '*.docx', '*.json']:
            protocol_files.extend(Path(protocols_dir).glob(f"**/{ext}"))
        
        logger.info(f"Found {len(protocol_files)} protocol files")
        
        all_vectors = []
        for file_path in tqdm(protocol_files, desc="Processing protocols"):
            vectors = self.process_protocol_file(str(file_path))
            all_vectors.extend(vectors)
            
            # Upload in batches to avoid memory issues
            if len(all_vectors) >= 1000:
                self.batch_upload(all_vectors, f"protocol batch")
                all_vectors = []
        
        # Upload remaining vectors
        if all_vectors:
            self.batch_upload(all_vectors, "final protocol batch")
    
    def get_index_stats(self):
        """Get current index statistics"""
        try:
            stats = self.index.describe_index_stats()
            logger.info(f"Index stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return None

def main():
    """Main ingestion pipeline"""
    pipeline = DataIngestionPipeline()
    
    # Get initial stats
    logger.info("=== Starting Data Ingestion ===")
    pipeline.get_index_stats()
    
    # Process regulatory content first
    pipeline.process_regulatory_content()
    
    # Process protocols (you'll need to specify the directory)
    protocols_directory = input("Enter path to protocols directory: ").strip()
    if protocols_directory and Path(protocols_directory).exists():
        pipeline.process_protocols_directory(protocols_directory)
    else:
        logger.warning("Protocols directory not provided or doesn't exist. Skipping protocol processing.")
    
    # Final stats
    logger.info("=== Ingestion Complete ===")
    pipeline.get_index_stats()

if __name__ == "__main__":
    main()
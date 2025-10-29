"""
FAST Upload Script - Optimized for speed
Much larger batches and parallel processing
"""

import os
import asyncio
from typing import List, Dict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import logging
import time
import requests
from openai import AzureOpenAI
from pinecone import Pinecone
from tqdm import tqdm

# Load environment variables from Keys Open Doors file
keys_file = Path('/Users/donmerriman/Ilana Labs/ilana-core/Keys Open Doors.txt')
if keys_file.exists():
    with open(keys_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FastUploadPipeline:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        
        # Use the existing 768-dimension index that has data
        index_name = "protocol-intelligence-768"
        self.index = self.pc.Index(index_name)
        self.embedding_dimension = 768
        logger.info(f"Using existing index: {index_name} (768 dimensions)")
        
        # Set up embedding client based on index dimension
        if self.embedding_dimension == 768:
            # Use HuggingFace PubMedBERT for 768 dimensions
            self.use_huggingface = True
            self.hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
            self.pubmedbert_url = os.getenv("PUBMEDBERT_ENDPOINT_URL", 
                                          "https://usz78oxlybv4xfh2.eastus.azure.endpoints.huggingface.cloud")
        else:
            # Use OpenAI for 1536 dimensions
            self.use_huggingface = False
            self.azure_client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version="2024-02-15-preview",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts at once"""
        try:
            if self.use_huggingface:
                # Use HuggingFace endpoint (process one at a time for now)
                embeddings = []
                headers = {"Authorization": f"Bearer {self.hf_api_key}"}
                
                for text in texts:
                    # Skip empty or very short texts
                    if not text or len(text.strip()) < 10:
                        logger.warning("Skipping empty or very short text")
                        continue
                        
                    response = requests.post(
                        self.pubmedbert_url,
                        headers=headers,
                        json={"inputs": text[:512]},  # PubMedBERT limit
                        timeout=30
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if isinstance(result, list) and len(result) > 0:
                            embeddings.append(result)
                        elif isinstance(result, dict):
                            # Handle various HuggingFace response formats
                            if 'embeddings' in result:
                                embeddings.append(result['embeddings'])
                            elif 'data' in result:
                                embeddings.append(result['data'])
                            elif 'embedding' in result:
                                embeddings.append(result['embedding'])
                            else:
                                # Try to extract the first array value from dict
                                for key, value in result.items():
                                    if isinstance(value, list) and len(value) == 768:
                                        embeddings.append(value)
                                        break
                                else:
                                    # Check if there's an error in the response
                                    if 'error' in result:
                                        logger.error(f"HF API error: {result['error']}")
                                    else:
                                        logger.warning(f"No valid embedding in response: {list(result.keys())}")
                                    # Skip this embedding rather than adding zeros
                                    continue
                        else:
                            logger.warning(f"Unexpected HF response format: {type(result)}")
                            continue  # Skip this embedding
                    else:
                        logger.error(f"HF API error: {response.status_code} - {response.text}")
                        continue  # Skip this embedding
                        
                return embeddings
            else:
                # Use OpenAI
                response = self.azure_client.embeddings.create(
                    input=texts,  # Send multiple texts
                    model="text-embedding-ada-002"
                )
                return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            return []
    
    def process_protocol_fast(self, file_path: str) -> Dict:
        """Process file with minimal chunking for speed"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            protocol_id = Path(file_path).stem
            
            # Single chunk per file for speed (first 6000 chars)
            chunk = content[:6000] if len(content) > 6000 else content
            
            return {
                "file_path": file_path,
                "protocol_id": protocol_id, 
                "text": chunk,
                "content": content
            }
            
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return None

async def fast_upload(protocols_dir: str, batch_size: int = 100, resume: bool = True):
    """Ultra-fast upload with large batches and resume capability"""
    pipeline = FastUploadPipeline()
    
    protocol_files = list(Path(protocols_dir).glob("*.txt"))
    total_files = len(protocol_files)
    logger.info(f"🚀 FAST MODE: Processing {total_files} files in batches of {batch_size}")
    
    # Check for already processed files if resume is enabled
    already_processed = set()
    if resume:
        logger.info("🔍 Checking for already processed files...")
        try:
            # Query Pinecone to get existing protocol IDs
            query_response = pipeline.index.query(
                vector=[0.0] * pipeline.embedding_dimension,  # Use correct dimension
                top_k=10000,  # get many results
                include_metadata=True,
                filter={"type": {"$eq": "protocol"}}
            )
            
            for match in query_response.matches:
                if 'protocol_id' in match.metadata:
                    already_processed.add(match.metadata['protocol_id'])
            
            logger.info(f"✅ Found {len(already_processed)} already processed protocols")
            
        except Exception as e:
            logger.warning(f"Could not check existing files: {e}")
            already_processed = set()
    
    # Filter out already processed files
    files_to_process = []
    for file_path in protocol_files:
        protocol_id = file_path.stem
        if not resume or protocol_id not in already_processed:
            files_to_process.append(file_path)
    
    skipped_count = total_files - len(files_to_process)
    logger.info(f"📋 Processing {len(files_to_process)} new files (skipping {skipped_count} already processed)")
    
    processed_count = skipped_count  # Start count from already processed
    
    for i in range(0, len(files_to_process), batch_size):
        batch_files = files_to_process[i:i + batch_size]
        batch_num = i//batch_size + 1
        total_batches = (len(files_to_process) + batch_size - 1)//batch_size
        
        logger.info(f"⚡ Processing MEGA-batch {batch_num}/{total_batches} ({len(batch_files)} files)")
        
        # Process files in parallel
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=8) as executor:  # More workers
            tasks = [
                loop.run_in_executor(executor, pipeline.process_protocol_fast, str(f))
                for f in batch_files
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        valid_results = [r for r in results if r and isinstance(r, dict)]
        
        if valid_results:
            # Get embeddings for all texts at once
            texts = [r["text"] for r in valid_results]
            logger.info(f"🧠 Getting {len(texts)} embeddings...")
            
            embeddings = pipeline.get_embeddings_batch(texts)
            
            if embeddings:
                # Handle case where some embeddings failed and were skipped
                if len(embeddings) != len(valid_results):
                    logger.warning(f"Got {len(embeddings)} embeddings for {len(valid_results)} texts, some failed")
                    # Only process the ones we have embeddings for
                    valid_results = valid_results[:len(embeddings)]
                # Create vectors - filter out invalid embeddings
                vectors = []
                for result, embedding in zip(valid_results, embeddings):
                    # Check if embedding is valid (not all zeros)
                    if isinstance(embedding, list) and len(embedding) == 768 and any(x != 0.0 for x in embedding):
                        vectors.append({
                            "id": f"fast_{result['protocol_id']}",
                            "values": embedding,
                            "metadata": {
                                "text": result["text"],
                                "source": f"Protocol {result['protocol_id']}",
                                "type": "protocol",
                                "protocol_id": result["protocol_id"],
                                "file_path": result["file_path"]
                            }
                        })
                    else:
                        logger.warning(f"Skipping invalid embedding for {result['protocol_id']}")
                
                # Upload to Pinecone in chunks
                logger.info(f"📤 Uploading {len(vectors)} vectors...")
                for j in range(0, len(vectors), 100):
                    chunk = vectors[j:j + 100]
                    pipeline.index.upsert(vectors=chunk)
                    
                processed_count += len(valid_results)
                logger.info(f"✅ MEGA-batch {batch_num} complete! Processed {processed_count}/{total_files} files ({len(files_to_process) - (i + len(batch_files))} remaining)")
            
        await asyncio.sleep(0.5)  # Brief pause
    
    logger.info(f"🎉 FAST UPLOAD COMPLETE! Processed {processed_count} files")

async def main():
    # Default settings for fast execution
    protocols_dir = "/Users/donmerriman/Ilana Labs/ilana-core/data/anonymized_texts"
    batch_size = 100
    resume = True
    
    logger.info(f"🚀 Starting FAST upload with:")
    logger.info(f"   Directory: {protocols_dir}")
    logger.info(f"   Batch size: {batch_size}")
    logger.info(f"   Resume mode: {resume}")
    
    await fast_upload(protocols_dir, batch_size, resume)

if __name__ == "__main__":
    asyncio.run(main())
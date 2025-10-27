"""
Batch Upload Script using OpenAI Embeddings (more reliable)
Optimized for handling 16,000+ protocols efficiently
"""

import os
import json
import asyncio
from typing import List, Dict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import logging
import hashlib
import time
from openai import AzureOpenAI
from pinecone import Pinecone
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIDataPipeline:
    def __init__(self):
        # Pinecone setup
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index_name = os.getenv("PINECONE_INDEX_NAME", "protocol-intelligence-768")
        self.index = self.pc.Index(index_name)
        
        # OpenAI setup
        self.azure_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-15-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
    def get_embeddings(self, text: str) -> List[float]:
        """Get embeddings using OpenAI text-embedding-ada-002"""
        try:
            response = self.azure_client.embeddings.create(
                input=text[:8000],  # OpenAI limit
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            return []
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if len(chunk.strip()) > 50:
                chunks.append(chunk.strip())
                
        return chunks
    
    def process_protocol_file(self, file_path: str) -> List[Dict]:
        """Process a single protocol file and return vectors"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            protocol_id = Path(file_path).stem
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
        batch_size = 100
        
        for i in tqdm(range(0, len(vectors), batch_size), desc=f"Uploading {description}"):
            batch = vectors[i:i + batch_size]
            try:
                self.index.upsert(vectors=batch)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.error(f"Batch upload failed: {e}")
                time.sleep(2)

class BatchProtocolProcessor:
    def __init__(self, max_workers: int = 2):  # Reduced workers for stability
        self.pipeline = OpenAIDataPipeline()
        self.max_workers = max_workers
        self.processed_count = 0
        
    async def process_protocol_batch(self, file_paths: List[str]) -> List[Dict]:
        """Process a batch of protocol files concurrently"""
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            tasks = [
                loop.run_in_executor(executor, self.pipeline.process_protocol_file, file_path)
                for file_path in file_paths
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        all_vectors = []
        for result in results:
            if isinstance(result, list):
                all_vectors.extend(result)
            else:
                logger.error(f"Processing error: {result}")
                
        return all_vectors
    
    async def upload_large_dataset(self, protocols_dir: str, batch_size: int = 10):
        """Upload large protocol dataset efficiently"""
        logger.info(f"Starting large dataset upload from {protocols_dir}")
        
        protocol_files = list(Path(protocols_dir).glob("*.txt"))
        total_files = len(protocol_files)
        logger.info(f"Found {total_files} protocol files to process")
        
        for i in range(0, total_files, batch_size):
            batch_files = protocol_files[i:i + batch_size]
            batch_num = i//batch_size + 1
            total_batches = (total_files + batch_size - 1)//batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches}")
            
            vectors = await self.process_protocol_batch([str(f) for f in batch_files])
            
            if vectors:
                self.pipeline.batch_upload(vectors, f"batch {batch_num}")
                self.processed_count += len(batch_files)
                logger.info(f"✅ Processed {self.processed_count}/{total_files} files")
            
            await asyncio.sleep(1)
        
        logger.info(f"🎉 Completed processing {self.processed_count} protocol files")

async def main():
    """Main async function"""
    processor = BatchProtocolProcessor(max_workers=2)
    
    protocols_dir = input("Enter path to protocols directory: ").strip()
    if not protocols_dir or not Path(protocols_dir).exists():
        logger.error("Invalid protocols directory")
        return
    
    batch_size = int(input("Enter batch size (default 10): ").strip() or "10")
    
    await processor.upload_large_dataset(protocols_dir, batch_size)

if __name__ == "__main__":
    asyncio.run(main())
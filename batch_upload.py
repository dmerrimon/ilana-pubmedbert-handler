"""
Batch Upload Script for Large Protocol Datasets
Optimized for handling 16,000+ protocols efficiently
"""

import os
import json
import asyncio
from typing import List, Dict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import logging
from data_ingestion import DataIngestionPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BatchProtocolProcessor:
    def __init__(self, max_workers: int = 4):
        self.pipeline = DataIngestionPipeline()
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
            
        # Flatten results and filter out errors
        all_vectors = []
        for result in results:
            if isinstance(result, list):
                all_vectors.extend(result)
            else:
                logger.error(f"Processing error: {result}")
                
        return all_vectors
    
    async def upload_large_dataset(self, protocols_dir: str, batch_size: int = 50):
        """Upload large protocol dataset efficiently"""
        logger.info(f"Starting large dataset upload from {protocols_dir}")
        
        # Find all protocol files
        protocol_files = []
        for ext in ['*.txt', '*.pdf', '*.docx', '*.json']:
            protocol_files.extend(Path(protocols_dir).glob(f"**/{ext}"))
        
        total_files = len(protocol_files)
        logger.info(f"Found {total_files} protocol files to process")
        
        # Process in batches
        for i in range(0, total_files, batch_size):
            batch_files = protocol_files[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_files + batch_size - 1)//batch_size}")
            
            # Process batch concurrently
            vectors = await self.process_protocol_batch([str(f) for f in batch_files])
            
            # Upload to Pinecone
            if vectors:
                self.pipeline.batch_upload(vectors, f"batch {i//batch_size + 1}")
                self.processed_count += len(batch_files)
                logger.info(f"Processed {self.processed_count}/{total_files} files")
            
            # Small delay to avoid overwhelming the system
            await asyncio.sleep(1)
        
        logger.info(f"Completed processing {self.processed_count} protocol files")

async def main():
    """Main async function"""
    processor = BatchProtocolProcessor(max_workers=4)
    
    protocols_dir = input("Enter path to protocols directory: ").strip()
    if not protocols_dir or not Path(protocols_dir).exists():
        logger.error("Invalid protocols directory")
        return
    
    batch_size = int(input("Enter batch size (default 50): ").strip() or "50")
    
    await processor.upload_large_dataset(protocols_dir, batch_size)

if __name__ == "__main__":
    asyncio.run(main())
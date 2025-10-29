#!/usr/bin/env python3
"""
Real Protocol Data Ingestion Pipeline
Ingests 16,730 real anonymized protocols into Pinecone with smart deduplication
"""

import os
import json
import logging
import asyncio
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealProtocolIngestion:
    """Ingest real protocol data into Pinecone with smart integration"""
    
    def __init__(self):
        self.namespace = "real_protocols"  # Separate namespace for real protocol data
        self.batch_size = 50  # Smaller batches for complex data
        self.total_ingested = 0
        self.duplicate_count = 0
        self.error_count = 0
        
        # Initialize clients
        self._initialize_clients()
        
    def _initialize_clients(self):
        """Initialize Pinecone and ML clients"""
        try:
            from pinecone import Pinecone
            self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            index_name = os.getenv("PINECONE_INDEX_NAME", "clinical-protocols")
            self.index = self.pc.Index(index_name)
            logger.info(f"✅ Connected to Pinecone index: {index_name}")
        except Exception as e:
            logger.error(f"❌ Pinecone initialization failed: {e}")
            raise
            
        try:
            from ml_service_client import get_ml_client
            self.ml_client = None  # Will be set async
            logger.info("✅ ML service client available")
        except ImportError:
            logger.warning("⚠️ ML service client not available, using fallback")
            self.ml_client = None
    
    async def check_existing_data(self) -> Dict:
        """Check what's already in Pinecone and avoid duplicates"""
        logger.info("🔍 Checking existing data in Pinecone...")
        
        try:
            # Get index stats
            stats = self.index.describe_index_stats()
            
            existing_data = {
                'total_vectors': stats.get('total_vector_count', 0),
                'index_fullness': stats.get('index_fullness', 0),
                'dimension': stats.get('dimension', 768),
                'namespaces': {}
            }
            
            # Check namespaces
            if 'namespaces' in stats:
                for ns_name, ns_data in stats['namespaces'].items():
                    existing_data['namespaces'][ns_name] = {
                        'vector_count': ns_data.get('vector_count', 0)
                    }
            
            logger.info(f"📊 Existing Pinecone Data:")
            logger.info(f"   Total vectors: {existing_data['total_vectors']:,}")
            logger.info(f"   Index fullness: {existing_data['index_fullness']:.2%}")
            logger.info(f"   Real protocols namespace: {existing_data['namespaces'].get(self.namespace, {}).get('vector_count', 0):,} vectors")
            
            # Sample existing real protocols to check for duplicates
            existing_ids = set()
            if self.namespace in existing_data['namespaces']:
                try:
                    # Query to get existing real protocol IDs
                    sample_query = self.index.query(
                        namespace=self.namespace,
                        vector=[0.1] * existing_data['dimension'],
                        top_k=10000,  # Get many IDs to check for duplicates
                        include_metadata=False  # Just need IDs
                    )
                    
                    for match in sample_query.matches:
                        existing_ids.add(match.id)
                    
                    logger.info(f"📋 Found {len(existing_ids)} existing real protocol IDs")
                    
                except Exception as e:
                    logger.warning(f"Could not sample existing IDs: {e}")
            
            existing_data['existing_protocol_ids'] = existing_ids
            return existing_data
            
        except Exception as e:
            logger.error(f"❌ Error checking existing data: {e}")
            return {'total_vectors': 0, 'existing_protocol_ids': set()}
    
    async def ingest_real_protocols(self, sample_size: Optional[int] = None):
        """Ingest real protocol data with smart deduplication"""
        logger.info("🚀 Starting real protocol ingestion...")
        
        # Initialize ML client
        if not self.ml_client:
            try:
                from ml_service_client import get_ml_client
                self.ml_client = await get_ml_client()
            except:
                logger.warning("⚠️ ML client not available, using fallback embeddings")
        
        # Check existing data
        existing_data = await self.check_existing_data()
        existing_ids = existing_data.get('existing_protocol_ids', set())
        
        # Load protocol analysis
        try:
            with open('real_protocol_analysis.json', 'r') as f:
                protocol_data = json.load(f)
            logger.info("✅ Loaded real protocol analysis data")
        except FileNotFoundError:
            logger.error("❌ real_protocol_analysis.json not found. Run protocol analysis first.")
            return
        
        protocols = protocol_data.get('protocols', {})
        therapeutic_patterns = protocol_data.get('therapeutic_patterns', {})
        
        # Determine which protocols to ingest
        protocols_to_ingest = []
        for protocol_id, protocol_info in protocols.items():
            # Skip if already exists
            if protocol_id in existing_ids:
                self.duplicate_count += 1
                continue
                
            # Add enriched metadata
            protocol_info['ingestion_timestamp'] = datetime.now().isoformat()
            protocol_info['data_source'] = 'real_anonymized_protocols'
            protocol_info['namespace'] = self.namespace
            
            # Add therapeutic area success rate
            therapeutic_area = protocol_info.get('therapeutic_area', 'general')
            if therapeutic_area in therapeutic_patterns:
                protocol_info['therapeutic_success_rate'] = therapeutic_patterns[therapeutic_area].get('success_score', 0.5)
                protocol_info['therapeutic_protocol_count'] = len(therapeutic_patterns[therapeutic_area].get('protocols', []))
            
            protocols_to_ingest.append((protocol_id, protocol_info))
        
        # Apply sample size if specified
        if sample_size and len(protocols_to_ingest) > sample_size:
            protocols_to_ingest = protocols_to_ingest[:sample_size]
            logger.info(f"📊 Limited to {sample_size} protocols for testing")
        
        logger.info(f"📋 Protocols to ingest: {len(protocols_to_ingest):,}")
        logger.info(f"📋 Duplicates skipped: {self.duplicate_count:,}")
        
        # Process in batches
        batches = [protocols_to_ingest[i:i + self.batch_size] 
                  for i in range(0, len(protocols_to_ingest), self.batch_size)]
        
        logger.info(f"🔄 Processing {len(batches)} batches...")
        
        for i, batch in enumerate(tqdm(batches, desc="Ingesting batches")):
            try:
                await self._process_batch(batch, i + 1, len(batches))
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Batch {i + 1} failed: {e}")
                self.error_count += len(batch)
        
        logger.info(f"✅ Real protocol ingestion completed!")
        logger.info(f"   Successfully ingested: {self.total_ingested:,}")
        logger.info(f"   Duplicates skipped: {self.duplicate_count:,}")
        logger.info(f"   Errors: {self.error_count:,}")
    
    async def _process_batch(self, batch: List[tuple], batch_num: int, total_batches: int):
        """Process a batch of protocols"""
        vectors = []
        
        for protocol_id, protocol_info in batch:
            try:
                # Create text for embedding - combine key fields
                text_components = [
                    protocol_info.get('title', ''),
                    f"Phase: {protocol_info.get('phase', '')}",
                    f"Therapeutic area: {protocol_info.get('therapeutic_area', '')}",
                    f"Study type: {protocol_info.get('study_type', '')}",
                    f"Compound: {protocol_info.get('compound_name', '')}",
                    f"Indication: {protocol_info.get('indication', '')}",
                ]
                
                # Add sections if available
                sections = protocol_info.get('sections', [])
                if sections:
                    text_components.extend(sections[:5])  # First 5 sections
                
                text_for_embedding = " | ".join([comp for comp in text_components if comp])
                
                # Get embeddings
                embeddings = await self._get_embeddings(text_for_embedding)
                if not embeddings:
                    logger.warning(f"⚠️ No embeddings for {protocol_id}")
                    continue
                
                # Create vector with comprehensive metadata
                vector = {
                    'id': protocol_id,
                    'values': embeddings,
                    'metadata': {
                        # Core protocol info
                        'title': protocol_info.get('title', '')[:1000],  # Limit length
                        'phase': protocol_info.get('phase', ''),
                        'therapeutic_area': protocol_info.get('therapeutic_area', ''),
                        'compound_name': protocol_info.get('compound_name', ''),
                        'study_type': protocol_info.get('study_type', ''),
                        'sponsor': protocol_info.get('sponsor', ''),
                        
                        # Success metrics
                        'success_score': float(protocol_info.get('success_score', 0)),
                        'amendment_count': int(protocol_info.get('amendment_count', 0)),
                        'completion_status': protocol_info.get('completion_status', ''),
                        
                        # Therapeutic intelligence
                        'therapeutic_success_rate': float(protocol_info.get('therapeutic_success_rate', 0.5)),
                        'therapeutic_protocol_count': int(protocol_info.get('therapeutic_protocol_count', 0)),
                        
                        # Technical metadata
                        'protocol_length': int(protocol_info.get('total_length', 0)),
                        'data_source': 'real_anonymized_protocols',
                        'ingestion_timestamp': protocol_info.get('ingestion_timestamp', ''),
                        'text': text_for_embedding[:2000]  # Store text for retrieval
                    }
                }
                
                vectors.append(vector)
                
            except Exception as e:
                logger.error(f"❌ Error processing {protocol_id}: {e}")
                self.error_count += 1
        
        # Upsert batch to Pinecone
        if vectors:
            try:
                self.index.upsert(
                    vectors=vectors,
                    namespace=self.namespace
                )
                self.total_ingested += len(vectors)
                logger.info(f"✅ Batch {batch_num}/{total_batches}: {len(vectors)} vectors ingested")
                
            except Exception as e:
                logger.error(f"❌ Pinecone upsert failed for batch {batch_num}: {e}")
                self.error_count += len(vectors)
    
    async def _get_embeddings(self, text: str) -> Optional[List[float]]:
        """Get embeddings using ML service or fallback"""
        try:
            if self.ml_client:
                # Use PubMedBERT via ML service
                embeddings = await self.ml_client.get_pubmedbert_embeddings(text)
                if embeddings and len(embeddings) == 768:
                    return embeddings
            
            # Fallback to direct API call
            import requests
            headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}
            response = requests.post(
                os.getenv('PUBMEDBERT_ENDPOINT_URL'),
                headers=headers,
                json={"inputs": text[:512]},  # Single text input
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                # Handle {"embeddings": [vector]} format
                if isinstance(result, dict) and "embeddings" in result:
                    embeddings = result["embeddings"]
                    if isinstance(embeddings, list) and len(embeddings) == 768:
                        return embeddings
                # Handle legacy list format
                elif isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], list) and len(result[0]) == 768:
                        return result[0]
            
            logger.warning(f"⚠️ Embedding API returned unexpected format")
            return None
            
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {e}")
            return None
    
    async def verify_ingestion(self):
        """Verify the ingested data"""
        logger.info("🔍 Verifying ingested real protocol data...")
        
        try:
            # Check namespace stats
            stats = self.index.describe_index_stats()
            real_protocol_count = stats.get('namespaces', {}).get(self.namespace, {}).get('vector_count', 0)
            
            logger.info(f"📊 Real protocols in Pinecone: {real_protocol_count:,}")
            
            # Sample some data
            sample_query = self.index.query(
                namespace=self.namespace,
                vector=[0.1] * 768,
                top_k=5,
                include_metadata=True
            )
            
            logger.info("🔍 Sample ingested protocols:")
            for i, match in enumerate(sample_query.matches[:3]):
                metadata = match.metadata
                logger.info(f"   {i+1}. {metadata.get('title', 'No title')[:100]}...")
                logger.info(f"      Phase: {metadata.get('phase', 'Unknown')}")
                logger.info(f"      Therapeutic: {metadata.get('therapeutic_area', 'Unknown')}")
                logger.info(f"      Success Score: {metadata.get('success_score', 0):.2f}")
                logger.info(f"      Amendments: {metadata.get('amendment_count', 0)}")
            
            return real_protocol_count
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return 0

async def main():
    """Main ingestion function"""
    import sys
    
    ingestion = RealProtocolIngestion()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--full":
            logger.info("🚀 Running full ingestion of 16,730 protocols...")
            await ingestion.ingest_real_protocols(sample_size=None)  # All protocols
        elif sys.argv[1] == "--sample":
            logger.info("🧪 Running sample ingestion (100 protocols)...")
            await ingestion.ingest_real_protocols(sample_size=100)
        elif sys.argv[1] == "--verify":
            logger.info("🔍 Verifying existing ingestion...")
            await ingestion.verify_ingestion()
            return
        else:
            print("Usage: python3 real_protocol_ingestion.py [--full|--sample|--verify]")
            return
    else:
        # Default: sample ingestion
        logger.info("🧪 Running default sample ingestion (100 protocols)...")
        await ingestion.ingest_real_protocols(sample_size=100)
    
    # Verify results
    await ingestion.verify_ingestion()
    
    logger.info("🎉 Real protocol ingestion pipeline completed!")

if __name__ == "__main__":
    asyncio.run(main())
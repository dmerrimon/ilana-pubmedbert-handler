"""
Test script to process a single protocol file and see what's happening
"""

import os
from data_ingestion import DataIngestionPipeline

def test_single_file():
    """Test processing a single protocol file"""
    
    # Set environment variables
    os.environ["PINECONE_INDEX_NAME"] = "protocol-intelligence-768"
    
    pipeline = DataIngestionPipeline()
    
    # Test with the first protocol file
    test_file = "/Users/donmerriman/Ilana Labs/ilana-core/data/anonymized_texts/protocol_000001.txt"
    
    print(f"Testing single file: {test_file}")
    print("Reading file...")
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"File size: {len(content)} characters")
        
        print("Chunking text...")
        chunks = pipeline.chunk_text(content)
        print(f"Created {len(chunks)} chunks")
        
        print("Getting embeddings for first chunk...")
        if chunks:
            embeddings = pipeline.get_embeddings(chunks[0][:200] + "...")
            if embeddings:
                print(f"✅ Embeddings successful! Length: {len(embeddings)}")
                print(f"First 5 values: {embeddings[:5]}")
            else:
                print("❌ No embeddings returned")
        
        print("Testing Pinecone connection...")
        stats = pipeline.get_index_stats()
        print(f"✅ Pinecone stats: {stats}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_single_file()
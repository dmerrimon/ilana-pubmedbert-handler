#!/usr/bin/env python3
"""
Test script to analyze real protocol dataset and build ML training data
Processes sample from 16,730 real anonymized protocols
"""

import asyncio
import logging
import sys
import json
from protocol_data_analyzer import get_protocol_analyzer
from protocol_success_scorer import get_success_scorer
from therapeutic_classifier import get_therapeutic_classifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_real_protocol_analysis():
    """Test analysis of real protocol dataset"""
    logger.info("🚀 Starting analysis of 16,730 real anonymized protocols...")
    
    try:
        # Initialize protocol analyzer
        analyzer = await get_protocol_analyzer()
        
        # Run analysis on sample (start with 500 protocols for testing)
        logger.info("📊 Analyzing sample of real protocols...")
        protocols = await analyzer.analyze_all_protocols(sample_size=500)
        
        # Get analysis summary
        summary = analyzer.get_analysis_summary()
        logger.info("📈 Analysis Summary:")
        for key, value in summary.items():
            if isinstance(value, dict):
                logger.info(f"  {key}: {len(value)} items")
            elif isinstance(value, list):
                logger.info(f"  {key}: {value}")
            else:
                logger.info(f"  {key}: {value}")
        
        # Save detailed results
        results = analyzer.save_analysis_results("real_protocol_analysis.json")
        logger.info(f"✅ Saved detailed analysis to real_protocol_analysis.json")
        
        # Extract some interesting findings
        logger.info("\n🔍 Key Findings from Real Protocols:")
        
        # Therapeutic area distribution
        if analyzer.therapeutic_patterns:
            logger.info("  Top Therapeutic Areas:")
            for area, data in list(analyzer.therapeutic_patterns.items())[:5]:
                protocol_count = len(data.get('protocols', []))
                avg_success = data.get('success_score', 0)
                logger.info(f"    {area}: {protocol_count} protocols, avg success: {avg_success:.2f}")
        
        # Phase distribution
        if analyzer.phase_patterns:
            logger.info("  Study Phase Distribution:")
            for phase, data in analyzer.phase_patterns.items():
                protocol_count = len(data.get('protocols', []))
                logger.info(f"    {phase}: {protocol_count} protocols")
        
        # Success patterns
        if analyzer.success_patterns:
            high_performers = analyzer.success_patterns.get('high_performers', {})
            low_performers = analyzer.success_patterns.get('low_performers', {})
            logger.info(f"  High performers: {high_performers.get('count', 0)} protocols")
            logger.info(f"  Low performers: {low_performers.get('count', 0)} protocols")
            logger.info(f"  High performer avg amendments: {high_performers.get('avg_amendments', 0):.1f}")
            logger.info(f"  Low performer avg amendments: {low_performers.get('avg_amendments', 0):.1f}")
        
        return summary
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise

async def test_sample_protocols():
    """Test analysis on a few individual protocols"""
    logger.info("🔬 Testing individual protocol analysis...")
    
    try:
        analyzer = await get_protocol_analyzer()
        
        # Test first few protocols
        test_files = [
            "/Users/donmerriman/Ilana Labs/ilana-core/data/anonymized_texts/protocol_000001.txt",
            "/Users/donmerriman/Ilana Labs/ilana-core/data/anonymized_texts/protocol_000002.txt",
            "/Users/donmerriman/Ilana Labs/ilana-core/data/anonymized_texts/protocol_000003.txt"
        ]
        
        for file_path in test_files:
            try:
                from pathlib import Path
                metadata = await analyzer._analyze_single_protocol(Path(file_path))
                if metadata:
                    logger.info(f"✅ {metadata.protocol_id}:")
                    logger.info(f"    Title: {metadata.title[:100]}...")
                    logger.info(f"    Phase: {metadata.phase}")
                    logger.info(f"    Therapeutic Area: {metadata.therapeutic_area}")
                    logger.info(f"    Compound: {metadata.compound_name}")
                    logger.info(f"    Amendment Count: {metadata.amendment_count}")
                    logger.info(f"    Success Score: {metadata.success_score:.2f}")
                    logger.info(f"    Protocol Length: {metadata.total_length:,} chars")
                else:
                    logger.warning(f"❌ Failed to analyze {file_path}")
            except Exception as e:
                logger.error(f"❌ Error analyzing {file_path}: {e}")
        
    except Exception as e:
        logger.error(f"❌ Sample testing failed: {e}")
        raise

if __name__ == "__main__":
    # Test individual protocols first
    asyncio.run(test_sample_protocols())
    
    # Then run larger analysis
    asyncio.run(test_real_protocol_analysis())
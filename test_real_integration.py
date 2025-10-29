#!/usr/bin/env python3
"""
Test integration of real protocol data with sophisticated authoring system
"""

import asyncio
import logging
import json
from sophisticated_authoring import get_sophisticated_authoring_guidance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_real_protocol_integration():
    """Test that sophisticated authoring uses real protocol data"""
    
    logger.info("🧪 Testing real protocol data integration with sophisticated authoring...")
    
    # Test protocol text samples
    test_cases = [
        {
            "text": "This is a Phase II randomized controlled trial in oncology patients with metastatic solid tumors.",
            "therapeutic_area": "oncology",
            "phase": "Phase II",
            "description": "Oncology Phase II trial"
        },
        {
            "text": "This study will evaluate the safety and efficacy of a new cardiac intervention in patients with heart failure.",
            "therapeutic_area": "cardiology", 
            "phase": "Phase II",
            "description": "Cardiology intervention study"
        },
        {
            "text": "A Phase I dose escalation study to determine the maximum tolerated dose in subjects with refractory disease.",
            "therapeutic_area": "oncology",
            "phase": "Phase I", 
            "description": "Phase I dose escalation"
        }
    ]
    
    for i, case in enumerate(test_cases):
        logger.info(f"\n📋 Test Case {i+1}: {case['description']}")
        
        try:
            # Get sophisticated guidance including real protocol insights
            guidance = await get_sophisticated_authoring_guidance(
                text=case["text"],
                therapeutic_area=case["therapeutic_area"],
                phase=case["phase"]
            )
            
            logger.info(f"✅ Generated {len(guidance)} guidance items")
            
            # Look specifically for real data intelligence
            real_data_items = [g for g in guidance if hasattr(g, 'suggestion_type') and g.suggestion_type == "real_data_intelligence"]
            
            if real_data_items:
                logger.info(f"🎯 Found {len(real_data_items)} real protocol data insights:")
                for item in real_data_items:
                    logger.info(f"    📊 Title: {item.title}")
                    logger.info(f"    📈 Description: {item.description}")
                    logger.info(f"    💡 Rationale: {item.rationale}")
                    logger.info(f"    🔬 Evidence: {item.evidence}")
                    logger.info(f"    📈 Clinical Score: {item.clinical_score:.2f}")
                    logger.info(f"    ⚠️  Compliance Risk: {item.compliance_risk:.2f}")
                    if item.suggestions:
                        logger.info(f"    ✅ Best Practices: {len(item.suggestions)} items")
                        for suggestion in item.suggestions[:2]:  # Show first 2
                            logger.info(f"      - {suggestion}")
                    if item.examples:
                        logger.info(f"    ⚠️  Risk Factors: {len(item.examples)} items")
                        for example in item.examples[:2]:  # Show first 2
                            logger.info(f"      - {example}")
            else:
                logger.warning(f"❌ No real protocol data insights found for {case['description']}")
                
            # Show other guidance types for comparison
            other_items = [g for g in guidance if hasattr(g, 'suggestion_type') and g.suggestion_type != "real_data_intelligence"]
            if other_items:
                logger.info(f"📝 Other guidance types: {', '.join(set(g.suggestion_type for g in other_items))}")
                
        except Exception as e:
            logger.error(f"❌ Test case {i+1} failed: {e}")
            
    logger.info("\n🏁 Real protocol integration test completed!")

async def test_protocol_insights_directly():
    """Test protocol insights extraction directly"""
    
    logger.info("\n🔬 Testing direct protocol insights extraction...")
    
    try:
        from sophisticated_authoring import SophisticatedAuthoringEngine
        
        engine = SophisticatedAuthoringEngine()
        await engine._initialize_with_real_data()
        
        # Test different therapeutic areas and phases
        test_combinations = [
            ("oncology", "Phase I"),
            ("cardiology", "Phase II"), 
            ("neurology", "Phase II"),
            ("diabetes", "Phase III")
        ]
        
        for therapeutic_area, phase in test_combinations:
            logger.info(f"\n📋 Testing {therapeutic_area} {phase}...")
            
            insights = await engine.get_real_protocol_insights(
                text="Sample protocol text",
                therapeutic_area=therapeutic_area,
                phase=phase
            )
            
            if insights:
                logger.info(f"✅ Got insights for {therapeutic_area} {phase}:")
                for key, value in insights.items():
                    if isinstance(value, list) and value:
                        logger.info(f"    {key}: {len(value)} items")
                        for item in value[:2]:  # Show first 2
                            logger.info(f"      - {item}")
                    elif isinstance(value, (int, float)):
                        logger.info(f"    {key}: {value}")
                    elif value:
                        logger.info(f"    {key}: {value}")
            else:
                logger.warning(f"❌ No insights found for {therapeutic_area} {phase}")
                
    except Exception as e:
        logger.error(f"❌ Direct insights test failed: {e}")

if __name__ == "__main__":
    # Test direct insights first
    asyncio.run(test_protocol_insights_directly())
    
    # Then test full integration
    asyncio.run(test_real_protocol_integration())
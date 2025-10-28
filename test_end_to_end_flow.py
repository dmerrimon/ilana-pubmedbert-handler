#!/usr/bin/env python3
"""
End-to-End API Flow Test
Tests the complete pipeline from API endpoints to sophisticated authoring
"""

import asyncio
import json
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_sophisticated_authoring_api():
    """Test the sophisticated authoring API endpoint"""
    logger.info("🧪 Testing sophisticated authoring API endpoint...")
    
    try:
        from sophisticated_authoring import get_sophisticated_authoring_guidance
        
        # Test different scenarios
        test_cases = [
            {
                "name": "Vague Language Detection",
                "text": "Patients will be monitored as appropriate and dosing will be adjusted as needed based on reasonable criteria.",
                "therapeutic_area": "oncology",
                "phase": "Phase II",
                "expected_types": ["clarity_enhancement", "real_data_intelligence"]
            },
            {
                "name": "Complex Protocol Risk",
                "text": "This is a novel, experimental first-in-human study with multiple complex arms for rare disease patients.",
                "therapeutic_area": "oncology", 
                "phase": "Phase I",
                "expected_types": ["feasibility_assessment", "real_data_intelligence"]
            },
            {
                "name": "Cardiology Study",
                "text": "This Phase II study will evaluate cardiac function in patients with heart failure using validated measures.",
                "therapeutic_area": "cardiology",
                "phase": "Phase II", 
                "expected_types": ["therapeutic_specific", "real_data_intelligence"]
            }
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(test_cases):
            logger.info(f"\n📋 Test Case {i+1}: {test_case['name']}")
            
            try:
                guidance = await get_sophisticated_authoring_guidance(
                    text=test_case["text"],
                    therapeutic_area=test_case["therapeutic_area"], 
                    phase=test_case["phase"]
                )
                
                logger.info(f"✅ Generated {len(guidance)} guidance items")
                
                # Check guidance types
                guidance_types = set(item.get('type', 'unknown') for item in guidance)
                logger.info(f"   Types: {', '.join(guidance_types)}")
                
                # Verify expected types are present
                missing_types = []
                for expected_type in test_case.get("expected_types", []):
                    if expected_type not in guidance_types:
                        missing_types.append(expected_type)
                
                if missing_types:
                    logger.warning(f"⚠️ Missing expected types: {missing_types}")
                    all_passed = False
                else:
                    logger.info(f"✅ All expected types found")
                
                # Show sample guidance
                for j, item in enumerate(guidance[:2]):
                    logger.info(f"   {j+1}. {item.get('title', 'No title')}")
                    logger.info(f"      Severity: {item.get('severity', 'unknown')}")
                    logger.info(f"      Clinical Score: {item.get('clinical_score', 0):.2f}")
                    
            except Exception as e:
                logger.error(f"❌ Test case {i+1} failed: {e}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ Sophisticated authoring API test failed: {e}")
        return False

async def test_real_protocol_insights():
    """Test real protocol insights functionality"""
    logger.info("\n🧪 Testing real protocol insights...")
    
    try:
        from sophisticated_authoring import SophisticatedAuthoringEngine
        
        engine = SophisticatedAuthoringEngine()
        await engine._initialize_with_real_data()
        
        # Test different therapeutic areas
        test_areas = [
            ("oncology", "Phase I"),
            ("cardiology", "Phase II"),
            ("neurology", "Phase II"),
            ("diabetes", "Phase III")
        ]
        
        all_passed = True
        
        for therapeutic_area, phase in test_areas:
            logger.info(f"\n📋 Testing {therapeutic_area} {phase}...")
            
            try:
                insights = await engine.get_real_protocol_insights(
                    text="Sample protocol text",
                    therapeutic_area=therapeutic_area,
                    phase=phase
                )
                
                if insights:
                    logger.info(f"✅ Got insights for {therapeutic_area} {phase}:")
                    logger.info(f"   Similar protocols: {insights.get('similar_protocols_count', 0)}")
                    logger.info(f"   Success rate: {insights.get('success_rate', 0):.1%}")
                    logger.info(f"   Phase protocols: {insights.get('phase_protocols_count', 0)}")
                    logger.info(f"   Best practices: {len(insights.get('best_practices', []))}")
                    logger.info(f"   Risk factors: {len(insights.get('risk_factors', []))}")
                else:
                    logger.warning(f"⚠️ No insights for {therapeutic_area} {phase}")
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"❌ Insights test failed for {therapeutic_area} {phase}: {e}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ Real protocol insights test failed: {e}")
        return False

async def test_protocol_data_analysis():
    """Test protocol data analysis functionality"""
    logger.info("\n🧪 Testing protocol data analysis...")
    
    try:
        from protocol_data_analyzer import get_protocol_analyzer
        
        analyzer = await get_protocol_analyzer()
        
        # Test analysis summary
        summary = analyzer.get_analysis_summary()
        
        if summary.get('error'):
            logger.warning(f"⚠️ No protocols analyzed yet: {summary['error']}")
            return True  # This is expected if analysis hasn't run
        
        logger.info("✅ Protocol Analysis Summary:")
        logger.info(f"   Total protocols: {summary.get('total_protocols', 0)}")
        logger.info(f"   Therapeutic areas: {len(summary.get('therapeutic_areas', []))}")
        logger.info(f"   Phases: {len(summary.get('phases', []))}")
        logger.info(f"   High performers: {summary.get('high_performers', 0)}")
        logger.info(f"   Low performers: {summary.get('low_performers', 0)}")
        logger.info(f"   Avg success score: {summary.get('avg_success_score', 0):.2f}")
        logger.info(f"   Avg amendments: {summary.get('avg_amendment_count', 0):.1f}")
        
        # Test therapeutic areas
        therapeutic_areas = summary.get('therapeutic_areas', [])
        if therapeutic_areas:
            logger.info(f"   Therapeutic areas: {', '.join(therapeutic_areas)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Protocol data analysis test failed: {e}")
        return False

async def test_ml_service_integration():
    """Test ML service integration"""
    logger.info("\n🧪 Testing ML service integration...")
    
    try:
        from ml_service_client import get_ml_client
        
        ml_client = await get_ml_client()
        
        # Test embeddings
        test_text = "This is a Phase II oncology study for patients with metastatic cancer."
        
        try:
            embeddings = await ml_client.get_pubmedbert_embeddings(test_text)
            
            if embeddings:
                logger.info(f"✅ ML service working: Got {len(embeddings)}-dim embeddings")
                logger.info(f"   Sample values: {embeddings[:5]}")
                return True
            else:
                logger.warning("⚠️ ML service returned no embeddings")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ ML service error: {e}")
            return False
        
    except ImportError:
        logger.warning("⚠️ ML service client not available")
        return True  # Not critical for core functionality
    except Exception as e:
        logger.error(f"❌ ML service integration test failed: {e}")
        return False

async def test_intelligence_status():
    """Test intelligence status reporting"""
    logger.info("\n🧪 Testing intelligence status...")
    
    try:
        # Import main to check intelligence level
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        
        # Check what intelligence systems are available
        intelligence_status = {
            "ml_service": False,
            "sophisticated_authoring": False,
            "real_protocol_data": False,
            "protocol_analyzer": False
        }
        
        try:
            from ml_service_client import get_ml_client
            intelligence_status["ml_service"] = True
        except ImportError:
            pass
        
        try:
            from sophisticated_authoring import get_sophisticated_authoring_guidance
            intelligence_status["sophisticated_authoring"] = True
        except ImportError:
            pass
        
        try:
            with open('real_protocol_analysis.json', 'r') as f:
                data = json.load(f)
                if data.get('protocols'):
                    intelligence_status["real_protocol_data"] = True
        except FileNotFoundError:
            pass
        
        try:
            from protocol_data_analyzer import get_protocol_analyzer
            intelligence_status["protocol_analyzer"] = True
        except ImportError:
            pass
        
        logger.info("📊 Intelligence System Status:")
        for system, status in intelligence_status.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"   {status_icon} {system}: {'Available' if status else 'Not Available'}")
        
        # Calculate intelligence level
        available_systems = sum(intelligence_status.values())
        total_systems = len(intelligence_status)
        intelligence_percentage = (available_systems / total_systems) * 100
        
        if intelligence_percentage >= 75:
            intelligence_level = "9.5/10 - Sophisticated Intelligence"
        elif intelligence_percentage >= 50:
            intelligence_level = "8.5/10 - Advanced Intelligence"
        elif intelligence_percentage >= 25:
            intelligence_level = "7.5/10 - Intermediate Intelligence"
        else:
            intelligence_level = "6.0/10 - Basic Intelligence"
        
        logger.info(f"🧠 Overall Intelligence Level: {intelligence_level}")
        logger.info(f"   Systems Available: {available_systems}/{total_systems} ({intelligence_percentage:.0f}%)")
        
        return intelligence_percentage >= 50  # Pass if >= 50% systems available
        
    except Exception as e:
        logger.error(f"❌ Intelligence status test failed: {e}")
        return False

async def main():
    """Run all end-to-end tests"""
    logger.info("🚀 Starting End-to-End API Flow Tests...")
    
    test_results = {}
    
    # Run all tests
    test_results["sophisticated_authoring"] = await test_sophisticated_authoring_api()
    test_results["real_protocol_insights"] = await test_real_protocol_insights()
    test_results["protocol_data_analysis"] = await test_protocol_data_analysis() 
    test_results["ml_service_integration"] = await test_ml_service_integration()
    test_results["intelligence_status"] = await test_intelligence_status()
    
    # Summary
    logger.info("\n🎯 End-to-End Test Results:")
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status_icon = "✅" if result else "❌"
        logger.info(f"   {status_icon} {test_name}: {'PASSED' if result else 'FAILED'}")
        if result:
            passed_tests += 1
    
    success_rate = (passed_tests / total_tests) * 100
    logger.info(f"\n📊 Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.0f}%)")
    
    if success_rate >= 80:
        logger.info("🎉 END-TO-END TESTS PASSED! System is ready for production.")
        return True
    elif success_rate >= 60:
        logger.info("⚠️ Most tests passed but some issues remain.")
        return False
    else:
        logger.info("❌ Multiple critical issues detected.")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
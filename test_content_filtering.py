#!/usr/bin/env python3
"""
Test the content filtering for administrative vs. protocol content
"""

import asyncio
from sophisticated_authoring import get_sophisticated_authoring_guidance

async def test_content_filtering():
    print("🧪 Testing Content Filtering...")
    
    # Test case 1: Administrative content (should be filtered out)
    admin_text = """Exposure-Response Evaluation of IV Artesunate in Children with Severe Malaria DMID Protocol Number: 19-0007 DMID Funding Mechanism: VTEU Contract HHSN2722013000221 Principal Investigator: Matthew B. Laurens, MD, MPH DMID Clinical Protocol Manager: Walt Jones, RN, MPH DMID Medical Officer: Gregory A. Deye, MD DMID Medical Monitor: Mo Elsafy, MD, MSc DMID Contracting Officer's Representative: Ranjodh S. Gill, RN, MPH  Draft or Version Number: 0.9 20 May 2021 Statement of Compliance The study will be carried out in accordance with Good Clinical Practice (GCP)"""
    
    # Test case 2: Actual protocol content (should be analyzed)
    protocol_text = """The primary objective of this study is to evaluate the pharmacokinetics and safety of intravenous artesunate in pediatric patients with severe malaria. Secondary objectives include assessment of efficacy through parasite clearance times and clinical outcomes. Inclusion criteria include children aged 2-15 years with confirmed severe malaria diagnosis and written informed consent from parents or guardians."""
    
    print("\n📋 Test 1: Administrative Content")
    print(f"Text length: {len(admin_text)} characters")
    admin_results = await get_sophisticated_authoring_guidance(
        text=admin_text,
        therapeutic_area="infectious_disease",
        phase="Phase II"
    )
    print(f"Results: {len(admin_results)} suggestions")
    if len(admin_results) == 0:
        print("✅ PASS: Administrative content correctly filtered out")
    else:
        print("❌ FAIL: Administrative content should have been filtered")
        for result in admin_results:
            print(f"   - {result.get('type')}: {result.get('title')}")
    
    print("\n📋 Test 2: Actual Protocol Content")  
    print(f"Text length: {len(protocol_text)} characters")
    protocol_results = await get_sophisticated_authoring_guidance(
        text=protocol_text,
        therapeutic_area="infectious_disease", 
        phase="Phase II"
    )
    print(f"Results: {len(protocol_results)} suggestions")
    if len(protocol_results) > 0:
        print("✅ PASS: Protocol content correctly analyzed")
        for result in protocol_results:
            print(f"   - {result.get('type')}: {result.get('title')}")
    else:
        print("❌ FAIL: Protocol content should have been analyzed")
    
    # Test case 3: Table of contents (should be filtered)
    toc_text = """Table of Contents Statement of Compliance 2 Signature Page 3 Table of Contents 4 List of Tables 7 List of Figures 8 List of Abbreviations 9 Protocol Summary 11 1 Key Roles 15 2 Background Information and Scientific Rationale 18 2.1 Background Information 18 2.2 Rationale 19"""
    
    print("\n📋 Test 3: Table of Contents")
    print(f"Text length: {len(toc_text)} characters")
    toc_results = await get_sophisticated_authoring_guidance(
        text=toc_text,
        therapeutic_area="infectious_disease",
        phase="Phase II"
    )
    print(f"Results: {len(toc_results)} suggestions")
    if len(toc_results) == 0:
        print("✅ PASS: Table of contents correctly filtered out")
    else:
        print("❌ FAIL: Table of contents should have been filtered")
        for result in toc_results:
            print(f"   - {result.get('type')}: {result.get('title')}")

if __name__ == "__main__":
    asyncio.run(test_content_filtering())
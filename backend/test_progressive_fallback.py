#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical.settings')
django.setup()

from patients.models import Patient
from patients.recommendation_engine import AntibioticRecommendationEngine

print("🧪 Testing Progressive Fallback System")
print("=" * 60)

# Test with Patient_28 (should work normally)
print("\n1️⃣ Testing Patient_28 (Normal Case):")
print("-" * 40)
try:
    # Find patient with name Patient_28
    patient_28 = Patient.objects.filter(name='Patient_28').first()
    if not patient_28:
        # Try finding by partial name match
        patient_28 = Patient.objects.filter(name__icontains='Patient_28').first()
    
    if patient_28:
        engine = AntibioticRecommendationEngine()
        result = engine.get_recommendations(patient_28)
        
        print(f"✅ Success: {result['success']}")
        print(f"📊 Recommendations: {len(result['recommendations'])}")
        print(f"🔍 Filter Steps: {len(result['filter_steps'])}")
        
        # Show fallback steps
        fallback_steps = [step for step in result['filter_steps'] if 'fallback' in step['name'].lower()]
        if fallback_steps:
            print("🔄 Fallback steps used:")
            for step in fallback_steps:
                print(f"   {step['step']}: {step['name']} - {step['output']}")
        else:
            print("✅ No fallback needed")
    else:
        print("❌ Patient_28 not found")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Create a hypothetical patient that might need fallbacks
print("\n2️⃣ Testing Hypothetical Edge Case Patient:")
print("-" * 40)

# Find a patient we can modify for testing
try:
    test_patient = Patient.objects.first()
    if test_patient:
        # Temporarily modify patient data to create edge case
        original_diagnosis = test_patient.diagnosis1
        original_pathogen = getattr(test_patient, 'pathogen', '')
        original_crcl = test_patient.crcl
        
        # Create edge case: rare diagnosis, low CrCl
        test_patient.diagnosis1 = "rare_infection_not_in_db"
        test_patient.crcl = 5.0  # Very low CrCl
        
        engine = AntibioticRecommendationEngine()
        result = engine.get_recommendations(test_patient)
        
        print(f"✅ Success: {result['success']}")
        print(f"📊 Recommendations: {len(result['recommendations'])}")
        
        # Show all filter steps
        print("🔍 Filter Steps:")
        for step in result['filter_steps']:
            status_emoji = "✅" if step['result'] == 'success' else "⚠️" if step['result'] == 'fallback' else "❌"
            print(f"   {status_emoji} Step {step['step']}: {step['name']}")
            print(f"      Input: {step['input']}")
            print(f"      Output: {step['output']}")
            print()
        
        # Restore original data
        test_patient.diagnosis1 = original_diagnosis
        test_patient.crcl = original_crcl
        if hasattr(test_patient, 'pathogen'):
            test_patient.pathogen = original_pathogen
        
    else:
        print("❌ No test patient available")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("🎯 Progressive Fallback Testing Complete!")

#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical.settings')
django.setup()

from patients.models import Patient
from patients.recommendation_engine import AntibioticRecommendationEngine

def test_clinical_recommendations():
    """Test the clinical recommendations engine"""
    try:
        # Test with Patient_28 specifically
        patient = Patient.objects.filter(name='Patient_28').first()
        
        if not patient:
            print("❌ Patient_28 not found in database")
            return
            
        print(f"🧪 Testing Clinical Recommendations Engine with Patient_28")
        print(f"Patient: {patient.patient_id} - {patient.name}")
        print(f"Diagnosis: {patient.diagnosis1}")
        print(f"Pathogen: {patient.pathogen}")
        print(f"Current antibiotic: {patient.antibiotics}")
        print(f"CrCl: {patient.cockcroft_gault_crcl}")
        print("-" * 50)
        
        # Test recommendation engine
        engine = AntibioticRecommendationEngine()
        result = engine.get_recommendations(patient)
        
        if result.get('success', False):
            print(f"✅ Engine Success!")
            print(f"Total matches: {result.get('total_matches', 0)}")
            recommendations = result.get('recommendations', [])
            print(f"Top recommendations: {len(recommendations)}")
            
            for i, rec in enumerate(recommendations[:5]):
                print(f"{i+1}. {rec.get('antibiotic_name')} "
                      f"(Score: {rec.get('preference_score')}, "
                      f"Priority: {rec.get('clinical_priority')})")
                      
            print("\n✅ Clinical recommendations engine working correctly!")
        else:
            print(f"❌ Engine Failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"Details: {result.get('details', 'No details available')}")
            
            # Print filter steps to debug
            filter_steps = result.get('filter_steps', [])
            if filter_steps:
                print("\nFilter steps:")
                for step in filter_steps:
                    print(f"  {step.get('step')}: {step.get('name')} - {step.get('result')}")
                    if step.get('result') == 'failed':
                        print(f"    Input: {step.get('input', 'N/A')}")
                        print(f"    Output: {step.get('output', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_clinical_recommendations()

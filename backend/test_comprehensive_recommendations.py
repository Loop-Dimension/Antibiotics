#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical.settings')
django.setup()

from patients.models import Patient
from patients.recommendation_engine import AntibioticRecommendationEngine

def test_recommendation_system():
    """Test the complete recommendation system with various cases"""
    
    print("🧪 Comprehensive Clinical Recommendations Test")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {
            'name': 'Patient_28 (Klebsiella pneumoniae)',
            'filter': {'name': 'Patient_28'}
        },
        {
            'name': 'First pneumonia patient',
            'filter': {'diagnosis1__icontains': 'pneumonia'}
        },
        {
            'name': 'First pyelonephritis patient',
            'filter': {'diagnosis1__icontains': 'pyelonephritis'}
        },
        {
            'name': 'Patient with unknown pathogen',
            'filter': {'pathogen__icontains': 'Unknown'}
        }
    ]
    
    engine = AntibioticRecommendationEngine()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print("-" * 40)
        
        try:
            patient = Patient.objects.filter(**test_case['filter']).first()
            
            if not patient:
                print("❌ No patient found matching criteria")
                continue
                
            print(f"Patient: {patient.patient_id} - {patient.name}")
            print(f"Diagnosis: {patient.diagnosis1}")
            print(f"Pathogen: {patient.pathogen}")
            print(f"CrCl: {patient.cockcroft_gault_crcl}")
            
            result = engine.get_recommendations(patient)
            
            if result.get('success', False):
                recommendations = result.get('recommendations', [])
                print(f"✅ Success! {len(recommendations)} recommendations")
                
                if result.get('is_fallback'):
                    print("⚠️  Fallback recommendations (general empirical therapy)")
                    print(f"   Message: {result.get('message', 'N/A')}")
                
                if recommendations:
                    print("Top 3 recommendations:")
                    for j, rec in enumerate(recommendations[:3], 1):
                        priority = rec.get('clinical_priority', 'N/A')
                        score = rec.get('preference_score', 'N/A')
                        therapy = rec.get('therapy_type', 'N/A')
                        print(f"   {j}. {rec.get('antibiotic_name')} - {rec.get('dose')}")
                        print(f"      Priority: {priority}, Score: {score}, Type: {therapy}")
                else:
                    print("   No specific recommendations")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                if result.get('reason'):
                    print(f"   Reason: {result.get('reason')}")
                    
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Comprehensive test completed!")

if __name__ == "__main__":
    test_recommendation_system()

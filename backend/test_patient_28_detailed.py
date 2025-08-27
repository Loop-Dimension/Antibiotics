#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical.settings')
django.setup()

from patients.models import Patient, Pathogen, Condition, AntibioticDosing
from patients.recommendation_engine import AntibioticRecommendationEngine

def test_patient_28_id_69():
    """Test specifically with Patient_28 (ID 69, female)"""
    
    print("🧪 Testing Patient_28 (ID 69, ♀)")
    print("=" * 50)
    
    try:
        # Find Patient_28 with ID 69
        patient = Patient.objects.filter(patient_id=69).first()
        
        if not patient:
            print("❌ Patient with ID 69 not found")
            # Try finding by name instead
            patient = Patient.objects.filter(name='Patient_28').first()
            if patient:
                print(f"Found Patient_28 with ID {patient.patient_id} instead")
            else:
                print("❌ No Patient_28 found at all")
                return
        
        print(f"Patient: {patient.patient_id} - {patient.name}")
        print(f"Gender: {patient.gender} ({69 if patient.gender == 'F' else 'Age not specified'})")
        print(f"Diagnosis: {patient.diagnosis1}")
        print(f"Pathogen: {patient.pathogen}")
        print(f"Current antibiotic: {patient.antibiotics}")
        print(f"CrCl: {patient.cockcroft_gault_crcl}")
        print()
        
        # Check database relationships first
        print("🔍 Database Analysis:")
        print("-" * 30)
        
        # Check if K. pneumoniae exists and has relationships
        try:
            kp = Pathogen.objects.get(name='K. pneumoniae')
            print(f"✅ K. pneumoniae found in database")
            
            # Check pneumonia condition
            pneumonia = Condition.objects.get(name='Pneumonia, community-acquired')
            print(f"✅ Pneumonia condition found")
            
            # Check dosing guidelines for this combination
            dosings = AntibioticDosing.objects.filter(
                condition=pneumonia,
                pathogens=kp
            )
            print(f"📊 Dosing guidelines for pneumonia + K. pneumoniae: {len(dosings)}")
            
            if dosings.exists():
                for d in dosings[:3]:
                    print(f"   - {d.antibiotic} ({d.dose}, {d.route})")
            else:
                print("   ⚠️  No specific guidelines for K. pneumoniae + pneumonia")
                
                # Check general pneumonia guidelines
                general_dosings = AntibioticDosing.objects.filter(condition=pneumonia)
                print(f"   📊 General pneumonia guidelines: {len(general_dosings)}")
                
                # Check which pathogens are covered
                covered_pathogens = set()
                for d in general_dosings:
                    for p in d.pathogens.all():
                        covered_pathogens.add(p.name)
                print(f"   🦠 Covered pathogens: {', '.join(sorted(covered_pathogens))}")
                
        except Exception as e:
            print(f"❌ Database check failed: {e}")
        
        print()
        print("🔬 Testing Recommendation Engine:")
        print("-" * 30)
        
        # Test recommendation engine
        engine = AntibioticRecommendationEngine()
        result = engine.get_recommendations(patient)
        
        print(f"Success: {result.get('success', False)}")
        print(f"Total matches: {result.get('total_matches', 0)}")
        
        if result.get('success', False):
            recommendations = result.get('recommendations', [])
            print(f"Recommendations count: {len(recommendations)}")
            
            if result.get('is_fallback'):
                print("⚠️  Using fallback recommendations")
                print(f"Message: {result.get('message', 'N/A')}")
            
            if recommendations:
                print("\nTop recommendations:")
                for i, rec in enumerate(recommendations[:5], 1):
                    priority = rec.get('clinical_priority', 'N/A')
                    score = rec.get('preference_score', 'N/A')
                    therapy = rec.get('therapy_type', 'N/A')
                    print(f"{i}. {rec.get('antibiotic_name')} - {rec.get('dose')}")
                    print(f"   Priority: {priority}, Score: {score}, Type: {therapy}")
                    print(f"   Route: {rec.get('route', 'N/A')}")
                    if rec.get('medical_rationale'):
                        print(f"   Rationale: {rec.get('medical_rationale')[:100]}...")
            else:
                print("❌ No recommendations generated")
        else:
            print(f"❌ Engine failed: {result.get('error', 'Unknown error')}")
            print(f"Reason: {result.get('reason', 'N/A')}")
        
        # Show filter steps for debugging
        filter_steps = result.get('filter_steps', [])
        if filter_steps:
            print(f"\n📋 Filter Steps ({len(filter_steps)}):")
            for step in filter_steps:
                status = "✅" if step.get('result') == 'success' else "❌"
                print(f"{status} Step {step.get('step')}: {step.get('name')}")
                print(f"   Input: {step.get('input', 'N/A')}")
                print(f"   Output: {step.get('output', 'N/A')}")
        
        print("\n" + "=" * 50)
        print("✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_patient_28_id_69()

#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical.settings')
django.setup()

from patients.models import Patient
from patients.recommendation_engine import AntibioticRecommendationEngine

print("🧪 Testing Patient_6 (ID: 7)")
print("=" * 50)

try:
    # Get Patient_6
    patient = Patient.objects.get(patient_id=7)
    
    print(f"Patient: {patient.name if hasattr(patient, 'name') else 'Patient_6'}")
    print(f"ID: {patient.patient_id}")
    print(f"Age: {patient.age} years")
    print(f"Gender: {patient.gender} ({'♂' if patient.gender == 'M' else '♀' if patient.gender == 'F' else patient.gender})")
    if hasattr(patient, 'date_recorded'):
        print(f"Recorded: {patient.date_recorded}")
    print()
    
    print("📋 Clinical Details:")
    print(f"Diagnosis: {patient.diagnosis1}")
    print(f"Pathogen: {patient.pathogen}")
    print(f"Current Treatment: {patient.antibiotics}")
    print(f"Allergies: {patient.allergies}")
    print(f"Sample Type: {patient.sample_type}")
    print()
    
    print("🔬 Lab Values:")
    print(f"Weight: {patient.body_weight} kg")
    print(f"Temperature: {patient.body_temperature}°C")
    print(f"SCr: {patient.scr} mg/dL")
    print(f"CrCl: {patient.cockcroft_gault_crcl} mL/min")
    if patient.wbc:
        print(f"WBC: {patient.wbc}")
    if patient.crp:
        print(f"CRP: {patient.crp} mg/L")
    print()
    
    # Get recommendations
    print("🔍 Getting Clinical Recommendations...")
    print("-" * 40)
    
    engine = AntibioticRecommendationEngine()
    result = engine.get_recommendations(patient)
    
    print(f"Success: {result.get('success', False)}")
    print(f"Total matches: {result.get('total_matches', 0)}")
    print(f"Recommendations count: {len(result.get('recommendations', []))}")
    
    if result.get('is_fallback'):
        print(f"⚠️ Fallback Mode: {result.get('message', 'Using general recommendations')}")
    
    print()
    
    if result.get('recommendations'):
        print("📋 Top 3 Clinical Recommendations:")
        print("-" * 40)
        for i, rec in enumerate(result.get('recommendations', []), 1):
            print(f"{i}. {rec.get('antibiotic_name')} - {rec.get('dose')}")
            print(f"   Priority: {rec.get('clinical_priority')}")
            print(f"   Score: {rec.get('preference_score')}")
            print(f"   Route: {rec.get('route')}")
            print(f"   Type: {rec.get('therapy_type')}")
            if rec.get('medical_rationale'):
                rationale = rec.get('medical_rationale')
                if len(rationale) > 80:
                    rationale = rationale[:77] + "..."
                print(f"   Rationale: {rationale}")
            print()
    else:
        print("❌ No recommendations found")
        if result.get('reason'):
            print(f"Reason: {result.get('reason')}")
    
    # Show filter steps
    if result.get('filter_steps'):
        print("📊 Filter Steps Summary:")
        print("-" * 40)
        for step in result.get('filter_steps', []):
            status = "✅" if step.get('result') == 'success' else "⚠️"
            print(f"{status} Step {step.get('step')}: {step.get('name')}")
            if 'input' in step:
                input_text = step['input']
                if len(input_text) > 60:
                    input_text = input_text[:57] + "..."
                print(f"   Input: {input_text}")
            if 'output' in step:
                output_text = step['output']
                if len(output_text) > 60:
                    output_text = output_text[:57] + "..."
                print(f"   Output: {output_text}")
            print()

except Patient.DoesNotExist:
    print(f"❌ Patient with ID 7 not found")
    
    # Show available patients around that ID
    print("\nAvailable patients:")
    nearby_patients = Patient.objects.filter(patient_id__in=[5, 6, 7, 8, 9])
    for p in nearby_patients:
        print(f"  ID: {p.patient_id}, Age: {p.age}, Gender: {p.gender}")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)
print("✅ Patient_6 test completed!")

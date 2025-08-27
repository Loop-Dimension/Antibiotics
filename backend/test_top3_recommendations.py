#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical.settings')
django.setup()

from patients.models import Patient
from patients.recommendation_engine import AntibioticRecommendationEngine

print("🧪 Testing Top 3 Recommendations")
print("=" * 50)

# Test with Patient_28
patient_28 = Patient.objects.get(patient_id=29)  # Patient_28 has ID 29
print(f"Testing Patient_28 (ID: {patient_28.patient_id})")
print(f"Diagnosis: {patient_28.diagnosis1}")
print(f"Pathogen: {patient_28.pathogen}")

engine = AntibioticRecommendationEngine()
result = engine.get_recommendations(patient_28)

print(f"\n🔬 Results:")
print(f"Success: {result.get('success', False)}")
print(f"Total matches: {result.get('total_matches', 0)}")
print(f"Recommendations count: {len(result.get('recommendations', []))}")

print(f"\n📋 Top 3 Recommendations:")
for i, rec in enumerate(result.get('recommendations', []), 1):
    print(f"{i}. {rec.get('antibiotic_name')} - {rec.get('dose')}")
    print(f"   Priority: {rec.get('clinical_priority')}, Score: {rec.get('preference_score')}")
    print(f"   Route: {rec.get('route')}")
    print()

# Test with new test2 patient
print("\n" + "=" * 50)
test2_patient = Patient.objects.get(patient_id=44)  # Use the latest test2 patient
print(f"Testing test2 Patient (ID: {test2_patient.patient_id})")
print(f"Diagnosis: {test2_patient.diagnosis1}")
print(f"Pathogen: {test2_patient.pathogen}")
print(f"Current Treatment: {test2_patient.antibiotics}")

result2 = engine.get_recommendations(test2_patient)

print(f"\n🔬 Results:")
print(f"Success: {result2.get('success', False)}")
print(f"Total matches: {result2.get('total_matches', 0)}")
print(f"Recommendations count: {len(result2.get('recommendations', []))}")

if result2.get('recommendations'):
    print(f"\n📋 Top 3 Recommendations:")
    for i, rec in enumerate(result2.get('recommendations', []), 1):
        print(f"{i}. {rec.get('antibiotic_name')} - {rec.get('dose')}")
        print(f"   Priority: {rec.get('clinical_priority')}, Score: {rec.get('preference_score')}")
        print(f"   Route: {rec.get('route')}")
        print()
else:
    print(f"\n⚠️ No recommendations found")
    print(f"Reason: {result2.get('reason', 'Unknown')}")

print("=" * 50)
print("✅ Top 3 recommendations test completed!")

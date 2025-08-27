#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical.settings')
django.setup()

from patients.models import Patient
from patients.recommendation_engine import AntibioticRecommendationEngine

print("🧪 Testing Deduplication with Pyelonephritis (Multiple Duplicates Expected)")
print("=" * 70)

# Find a patient with pyelonephritis (should have lots of duplicates)
pyelonephritis_patient = Patient.objects.filter(diagnosis1__icontains='pyelonephritis').first()

if not pyelonephritis_patient:
    print("❌ No pyelonephritis patient found")
    exit()

print(f"Patient: {pyelonephritis_patient.patient_id}")
print(f"Diagnosis: {pyelonephritis_patient.diagnosis1}")
print(f"Pathogen: {pyelonephritis_patient.pathogen}")
print(f"Age: {pyelonephritis_patient.age}")
print(f"Gender: {pyelonephritis_patient.gender}")

# Calculate CrCl if possible
from decimal import Decimal
if hasattr(pyelonephritis_patient, 'creatinine') and pyelonephritis_patient.creatinine:
    # Calculate using the formula from the engine
    if pyelonephritis_patient.gender == 'F':
        crcl = ((140 - pyelonephritis_patient.age) * float(pyelonephritis_patient.body_weight) * 0.85) / (72 * float(pyelonephritis_patient.creatinine))
    else:
        crcl = ((140 - pyelonephritis_patient.age) * float(pyelonephritis_patient.body_weight)) / (72 * float(pyelonephritis_patient.creatinine))
    print(f"Calculated CrCl: {crcl:.2f}")
else:
    print(f"CrCl: Not calculable")

# Get recommendations
engine = AntibioticRecommendationEngine()
result = engine.get_recommendations(pyelonephritis_patient)

print(f"\n🔬 Recommendation Results:")
print(f"Success: {result.get('success', False)}")
print(f"Total matches: {result.get('total_matches', 0)}")
print(f"Recommendations count: {len(result.get('recommendations', []))}")

print(f"\n📋 Unique Antibiotic Recommendations:")
for i, rec in enumerate(result.get('recommendations', []), 1):
    print(f"{i}. {rec.get('antibiotic_name')} - {rec.get('dose')}")
    print(f"   Priority: {rec.get('clinical_priority')}, Score: {rec.get('preference_score')}")
    print(f"   Route: {rec.get('route')}")
    print()

# Verify uniqueness
antibiotic_names = [rec.get('antibiotic_name') for rec in result.get('recommendations', [])]
unique_names = set(antibiotic_names)

print(f"📊 Deduplication Verification:")
print(f"Total recommendations: {len(antibiotic_names)}")
print(f"Unique antibiotics: {len(unique_names)}")
print(f"Duplicates removed: {len(antibiotic_names) - len(unique_names)}")

if len(antibiotic_names) == len(unique_names):
    print("✅ Deduplication successful - all antibiotics are unique!")
else:
    print(f"❌ Still have duplicates: {[name for name in antibiotic_names if antibiotic_names.count(name) > 1]}")

print("\n" + "=" * 70)
print("✅ Deduplication test completed!")

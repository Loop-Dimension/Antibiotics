#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical.settings')
django.setup()

from patients.recommendation_engine import AntibioticRecommendationEngine

# Test the base name extraction function
engine = AntibioticRecommendationEngine()

print("🧪 Testing Base Antibiotic Name Extraction")
print("=" * 50)

test_cases = [
    "Levofloxacin  750mg",
    "Levofloxacin 500mg", 
    "Ciprofloxacin 1000mg",
    "Ciprofloxacin 500mg",
    "Amoxicillin/clavulanate 1.2 g",
    "Ampicillin/sulbactam 3 g",
    "Ceftriaxone 2 g",
    "Vancomycin 40-60 mg",
    "Ampicillin 150-200 or 300-400 mg",
    "Cefpodoxime 200 mg"
]

print("Original Name → Base Name")
print("-" * 40)
for name in test_cases:
    base_name = engine._extract_base_antibiotic_name(name)
    print(f"{name:<35} → {base_name}")

print("\n📊 Grouping Test:")
grouped = {}
for name in test_cases:
    base_name = engine._extract_base_antibiotic_name(name)
    if base_name not in grouped:
        grouped[base_name] = []
    grouped[base_name].append(name)

for base_name, variants in grouped.items():
    if len(variants) > 1:
        print(f"\n{base_name}:")
        for variant in variants:
            print(f"  - {variant}")

print(f"\n✅ Deduplication would reduce {len(test_cases)} entries to {len(grouped)} unique antibiotics")

#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical.settings')
django.setup()

from patients.models import AntibioticDosing
from collections import defaultdict

print("🔍 Examining Duplicate Antibiotic Entries")
print("=" * 50)

# Group by antibiotic name
antibiotic_groups = defaultdict(list)
for dosing in AntibioticDosing.objects.all():
    antibiotic_groups[dosing.antibiotic].append(dosing)

# Show duplicates
for antibiotic, dosings in antibiotic_groups.items():
    if len(dosings) > 1:
        print(f"\n📋 {antibiotic} ({len(dosings)} entries):")
        for i, d in enumerate(dosings[:3], 1):  # Show first 3
            print(f"  {i}. Dose: {d.dose}")
            print(f"     Route: {d.route}")
            print(f"     CrCl: {d.crcl_min}-{d.crcl_max} mL/min")
            print(f"     Condition: {d.condition}")
            print(f"     Pathogens: {[p.name for p in d.pathogens.all()]}")
            print()
        if len(dosings) > 3:
            print(f"     ... and {len(dosings) - 3} more entries")
        print("-" * 40)

print(f"\n📊 Summary:")
print(f"Total unique antibiotics: {len(antibiotic_groups)}")
duplicate_count = sum(1 for dosings in antibiotic_groups.values() if len(dosings) > 1)
print(f"Antibiotics with duplicates: {duplicate_count}")

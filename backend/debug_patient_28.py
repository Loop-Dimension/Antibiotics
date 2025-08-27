#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical.settings')
django.setup()

from patients.models import AntibioticDosing, Condition, Pathogen

def check_patient_28_issue():
    """Check why Patient_28 isn't getting recommendations"""
    
    print("🔍 Investigating Patient_28 recommendation issue")
    print("-" * 50)
    
    # Check pneumonia guidelines
    print("1. Checking pneumonia guidelines:")
    condition = Condition.objects.filter(name__icontains='pneumonia').first()
    if condition:
        dosings = AntibioticDosing.objects.filter(condition=condition)
        print(f"   Found {len(dosings)} guidelines for {condition.name}")
        for d in dosings[:5]:
            print(f"   - {d.antibiotic}")
    else:
        print("   ❌ No pneumonia condition found")
    
    # Check Klebsiella pathogens
    print("\n2. Checking Klebsiella pathogens:")
    kleb_pathogens = Pathogen.objects.filter(name__icontains='Klebsiella')
    print(f"   Found {len(kleb_pathogens)} Klebsiella entries")
    for p in kleb_pathogens:
        print(f"   - {p.name}")
    
    # Check if any guidelines match Klebsiella
    print("\n3. Checking guidelines with Klebsiella coverage:")
    if condition and kleb_pathogens.exists():
        for pathogen in kleb_pathogens:
            matching_dosings = AntibioticDosing.objects.filter(
                condition=condition,
                pathogens=pathogen
            )
            print(f"   Guidelines for {condition.name} + {pathogen.name}: {len(matching_dosings)}")
            for d in matching_dosings[:3]:
                print(f"     - {d.antibiotic}")
    
    # Check all available pathogens for pneumonia
    print("\n4. All pathogens available for pneumonia:")
    if condition:
        all_dosings = AntibioticDosing.objects.filter(condition=condition).prefetch_related('pathogens')
        pathogen_names = set()
        for dosing in all_dosings:
            for pathogen in dosing.pathogens.all():
                pathogen_names.add(pathogen.name)
        
        print(f"   Available pathogens ({len(pathogen_names)}):")
        for name in sorted(pathogen_names):
            print(f"     - {name}")

if __name__ == "__main__":
    check_patient_28_issue()

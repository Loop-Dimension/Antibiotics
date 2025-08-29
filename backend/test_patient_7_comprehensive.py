#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical.settings')
django.setup()

from patients.models import Patient, AntibioticDosing, Condition, Severity
from patients.recommendation_engine import AntibioticRecommendationEngine

try:
    # Get Patient_7
    patient = Patient.objects.get(name="Patient_7")
    print(f'=== {patient.name} (ID: {patient.patient_id}) ===')
    print(f'Diagnosis: {patient.diagnosis1}')
    print(f'Pathogen: {patient.pathogen}')
    print(f'Age: {patient.age} years')
    print(f'CrCl: {patient.cockcroft_gault_crcl} mL/min')
    print(f'Allergies: {patient.allergies}')
    print(f'Current antibiotics: {patient.antibiotics}')
    print()
    
    # Test recommendation engine
    engine = AntibioticRecommendationEngine()
    result = engine.get_recommendations(patient)
    
    print("=== RECOMMENDATION ENGINE RESULTS ===")
    if result.get('success'):
        recommendations = result.get('recommendations', [])
        print(f'Generated {len(recommendations)} recommendations:')
        
        for i, rec in enumerate(recommendations, 1):
            print(f'{i}. {rec.get("antibiotic_name")}')
            print(f'   Dose: {rec.get("dose")}')
            print(f'   Route: {rec.get("route")}')
            print(f'   Interval: {rec.get("interval")}')
            print(f'   Duration: {rec.get("duration")}')
            print(f'   Medical Rationale: {rec.get("medical_rationale")}')
            print(f'   Preference Score: {rec.get("preference_score")}')
            print()
        
        # Show filter steps
        print("=== FILTER STEPS ===")
        for step in result.get('filter_steps', []):
            print(f"Step {step.get('step')}: {step.get('name')}")
            print(f"  Input: {step.get('input')}")
            print(f"  Output: {step.get('output')}")
            print(f"  Result: {step.get('result')}")
            if step.get('note'):
                print(f"  Note: {step.get('note')}")
            print()
    else:
        print(f'Error: {result.get("error")}')
    
    # Now let's check what's available in the database for this patient's condition
    print("=== AVAILABLE GUIDELINES IN DATABASE ===")
    
    # Find the matched condition
    diagnosis = patient.diagnosis1.lower().strip()
    matched_condition = None
    
    # Try to match condition using the same logic as the engine
    diagnosis_mapping = {
        'pyelonephritis': 'Pyelonephritis',
        'acute pyelonephritis': 'Pyelonephritis',
        'pneumonia': 'Pneumonia, community-acquired',
        'community-acquired pneumonia': 'Pneumonia, community-acquired',
    }
    
    for key, condition_name in diagnosis_mapping.items():
        if key in diagnosis:
            try:
                matched_condition = Condition.objects.get(name=condition_name)
                break
            except Condition.DoesNotExist:
                continue
    
    if matched_condition:
        print(f"Matched condition: {matched_condition.name}")
        
        # Get all severities for this condition
        severities = Severity.objects.filter(condition=matched_condition)
        print(f"Available severities: {[s.level for s in severities]}")
        
        # Get all guidelines for this condition and patient type
        patient_type = 'adult' if patient.age >= 18 else 'child'
        crcl = float(patient.cockcroft_gault_crcl)
        
        all_guidelines = AntibioticDosing.objects.filter(
            condition=matched_condition,
            patient_type=patient_type,
            crcl_min__lte=crcl,
            crcl_max__gte=crcl,
            dialysis_type='none'
        ).order_by('antibiotic')
        
        print(f"\nAll available guidelines for {matched_condition.name}, {patient_type}, CrCl {crcl}:")
        print(f"Total guidelines found: {all_guidelines.count()}")
        
        for guideline in all_guidelines:
            print(f"- {guideline.antibiotic}")
            print(f"  Dose: {guideline.dose}")
            print(f"  Route: {', '.join(guideline.route) if guideline.route else 'Not specified'}")
            print(f"  Interval: {guideline.interval}")
            print(f"  Duration: {guideline.duration}")
            print(f"  Severity: {guideline.severity.level}")
            print(f"  CrCl range: {guideline.crcl_min}-{guideline.crcl_max}")
            print(f"  Pathogens: {[p.name for p in guideline.pathogens.all()]}")
            if guideline.remark:
                print(f"  Remark: {guideline.remark}")
            
            # Check if this would be filtered out
            should_filter = False
            if guideline.dose and "no dosage adjustment" in guideline.dose.lower():
                should_filter = True
                print(f"  >>> FILTERED OUT: Contains 'no dosage adjustment' in dose")
            if guideline.remark and "no dosage adjustment" in guideline.remark.lower():
                should_filter = True
                print(f"  >>> FILTERED OUT: Contains 'no dosage adjustment' in remark")
            print()
    else:
        print("No matching condition found in database")
        print("Available conditions:")
        for condition in Condition.objects.all():
            print(f"- {condition.name}")

except Patient.DoesNotExist:
    print("Patient_7 not found")
    print("Available patients:")
    for patient in Patient.objects.all().order_by('patient_id'):
        print(f"- {patient.name} (ID: {patient.patient_id})")
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()

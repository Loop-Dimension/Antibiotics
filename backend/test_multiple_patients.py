#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical.settings')
django.setup()

from patients.models import Patient
from patients.recommendation_engine import AntibioticRecommendationEngine

# Test with multiple patients to verify filtering
test_patients = [42, 43, 44]  # These should be the test patients from the attachments

for patient_id in test_patients:
    try:
        patient = Patient.objects.get(pk=patient_id)
        print(f'\n=== Patient {patient.patient_id}: {patient.name} ===')
        print(f'Diagnosis: {patient.diagnosis1}')
        print(f'Pathogen: {patient.pathogen}')
        print(f'Age: {patient.age}')
        print(f'CrCl: {patient.cockcroft_gault_crcl}')
        
        engine = AntibioticRecommendationEngine()
        result = engine.get_recommendations(patient)
        
        if result.get('success'):
            recommendations = result.get('recommendations', [])
            print(f'Successfully generated {len(recommendations)} recommendations')
            for i, rec in enumerate(recommendations[:3], 1):
                print(f'{i}. {rec.get("antibiotic_name")} - {rec.get("dose")} - {rec.get("route")}')
                
            # Check filter steps for pathogen handling
            filter_steps = result.get('filter_steps', [])
            pathogen_step = next((step for step in filter_steps if step.get('name') == 'Pathogen Identification'), None)
            if pathogen_step:
                print(f'Pathogen handling: {pathogen_step.get("note", pathogen_step.get("output"))}')
        else:
            print(f'Error: {result.get("error")}')
            
    except Patient.DoesNotExist:
        print(f'Patient {patient_id} not found')
    except Exception as e:
        print(f'Error with patient {patient_id}: {e}')
        import traceback
        traceback.print_exc()

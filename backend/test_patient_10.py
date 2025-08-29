#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical.settings')
django.setup()

from patients.models import Patient
from patients.recommendation_engine import AntibioticRecommendationEngine

try:
    patient = Patient.objects.get(pk=10)
    print(f'Patient {patient.patient_id}: {patient.name}')
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
    else:
        print(f'Error: {result.get("error")}')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()

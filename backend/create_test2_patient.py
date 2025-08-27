#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical.settings')
django.setup()

from patients.models import Patient
from datetime import date
from decimal import Decimal

# Create test2 patient
try:
    # Calculate CrCl for 20-year-old male, 70kg, SCr 1.0
    # Cockcroft-Gault: CrCl = ((140-age) * weight) / (72 * SCr)
    age = 20
    weight = 70.0
    scr = 1.0
    crcl = ((140 - age) * weight) / (72 * scr)
    
    patient = Patient.objects.create(
        name='test2',
        date_recorded=date(2025, 8, 27),
        age=20,
        gender='M',
        body_weight=Decimal('70.0'),
        diagnosis1='asdag',
        body_temperature=Decimal('37.0'),  # Normal temp
        scr=Decimal('1.0'),
        cockcroft_gault_crcl=Decimal(str(round(crcl, 2))),
        pathogen='Unknown',
        sample_type='Not specified',
        antibiotics='PO ciprofloxacin 500mg bid',
        allergies='None'
    )
    
    print(f"✅ Created patient: {patient.name}")
    print(f"   ID: {patient.patient_id}")
    print(f"   Age: {patient.age} years")
    print(f"   Gender: {patient.gender}")
    print(f"   Weight: {patient.body_weight} kg")
    print(f"   Diagnosis: {patient.diagnosis1}")
    print(f"   Pathogen: {patient.pathogen}")
    print(f"   Current Treatment: {patient.antibiotics}")
    print(f"   SCr: {patient.scr} mg/dL")
    print(f"   CrCl: {patient.cockcroft_gault_crcl} mL/min")
    print(f"   Recorded: {patient.date_recorded}")
    
except Exception as e:
    print(f"❌ Error creating patient: {e}")

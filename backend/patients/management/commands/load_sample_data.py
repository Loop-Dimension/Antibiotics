from django.core.management.base import BaseCommand
from patients.models import Patient, Medication
from datetime import date
from decimal import Decimal


class Command(BaseCommand):
    help = 'Load sample patient data'

    def handle(self, *args, **options):
        # Create the sample patient from your data
        patient_data = {
            'date_recorded': date(2025, 1, 16),
            'age': 51,
            'gender': 'M',
            'body_weight': Decimal('80'),
            'height': Decimal('171'),
            'body_temperature': None,  # Not provided in sample
            'diagnosis1': 'acute pyelonephritis',
            'diagnosis2': 'acute pyelonephritis',
            'wbc': Decimal('7500'),
            'hb': Decimal('12.2'),
            'platelet': Decimal('226000'),
            'ast': Decimal('22'),
            'alt': Decimal('12'),
            'scr': Decimal('1.10'),
            'cockcroft_gault_crcl': Decimal('89.8989899'),
            'crp': Decimal('122.35'),
            'pathogen': 'Escherichia coli',
            'sample_type': 'urine',
            'antibiotics': 'PO amoxicillin/clavulanate 1g bid',
            'current_medications': 'PO amoxicillin/clavulanate 1g bid'
        }
        
        # Create or update the patient
        patient, created = Patient.objects.get_or_create(
            date_recorded=patient_data['date_recorded'],
            age=patient_data['age'],
            gender=patient_data['gender'],
            defaults=patient_data
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created patient {patient.patient_id}')
            )
            
            # Create medication record
            medication = Medication.objects.create(
                patient=patient,
                medication_name='amoxicillin/clavulanate',
                dosage='1g',
                frequency='bid',
                route='PO',
                start_date=date(2025, 1, 16),
                is_antibiotic=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created medication record for patient {patient.patient_id}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Patient {patient.patient_id} already exists')
            )
        
        # Display patient info
        self.stdout.write(f'\nPatient Information:')
        self.stdout.write(f'ID: {patient.patient_id}')
        self.stdout.write(f'Date: {patient.date_recorded}')
        self.stdout.write(f'Age: {patient.age}, Gender: {patient.get_gender_display()}')
        self.stdout.write(f'Weight: {patient.body_weight}kg, Height: {patient.height}cm')
        if patient.bmi:
            self.stdout.write(f'BMI: {patient.bmi}')
        self.stdout.write(f'Diagnosis: {patient.diagnosis1}')
        self.stdout.write(f'Pathogen: {patient.pathogen} ({patient.sample_type})')
        self.stdout.write(f'Treatment: {patient.antibiotics}')

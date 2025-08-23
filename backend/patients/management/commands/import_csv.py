import csv
import os
from django.core.management.base import BaseCommand
from patients.models import Patient
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.db import transaction


class Command(BaseCommand):
    help = 'Import patient data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='CSV file path', default='sheet.csv')

    def handle(self, *args, **options):
        csv_file = options['file']
        
        # Check if file exists
        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'File {csv_file} does not exist'))
            return
        
        # Clear existing data (optional - remove if you want to keep existing data)
        self.stdout.write('Clearing existing patient data...')
        Patient.objects.all().delete()
        
        imported_count = 0
        error_count = 0
        
        with open(csv_file, 'r', encoding='utf-8-sig') as file:  # utf-8-sig handles BOM
            reader = csv.DictReader(file)
            
            with transaction.atomic():
                for row_num, row in enumerate(reader, start=2):  # Start at 2 because header is row 1
                    try:
                        # Debug: print the row keys to see what we're getting
                        if row_num == 2:  # First data row
                            self.stdout.write(f'CSV columns: {list(row.keys())}')
                        
                        # Parse date
                        date_str = row['Date'].strip()
                        if '.' in date_str:
                            # Handle format like 2025.01.16
                            date_obj = datetime.strptime(date_str, '%Y.%m.%d').date()
                        else:
                            # Handle other formats
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                        
                        # Handle gender (1=Male, 0=Female)
                        gender = 'M' if str(row['Male']).strip() == '1' else 'F'
                        
                        # Clean and convert numeric fields
                        def safe_decimal(value, default=0):
                            if not value or str(value).strip() == '' or str(value).strip().upper() == 'NA':
                                return Decimal(str(default))
                            try:
                                # Remove any extra quotes or special characters
                                clean_value = str(value).strip().replace('"', '').replace(',', '')
                                return Decimal(clean_value)
                            except (InvalidOperation, ValueError):
                                return Decimal(str(default))
                        
                        # Handle special CRP case with comma
                        crp_value = str(row['CRP(mg/L)']).strip()
                        if '"' in crp_value and ',' in crp_value:
                            # Handle cases like "192.,15" - take the first part
                            crp_value = crp_value.replace('"', '').split(',')[0]
                        
                        # Clean pathogen and sample fields
                        pathogen = str(row['Pathogen']).strip()
                        if pathogen.upper() == 'NA' or not pathogen:
                            pathogen = 'No pathogen identified'
                        elif pathogen == 'pending':
                            pathogen = 'Culture pending'
                        
                        sample_type = str(row['Sample']).strip()
                        if not sample_type:
                            sample_type = 'Unknown'
                        
                        # Handle age conversion
                        age = int(float(str(row['Age']).strip()))
                        
                        # Create patient record
                        patient = Patient.objects.create(
                            gender=gender,
                            date_recorded=date_obj,
                            age=age,
                            body_weight=safe_decimal(row['BW']),
                            height=safe_decimal(row['Height']),
                            wbc=safe_decimal(row['WBC']),
                            hb=safe_decimal(row['Hb']),
                            platelet=safe_decimal(row['PLT']),
                            ast=safe_decimal(row['AST(IU/L)']),
                            alt=safe_decimal(row['ALT(IU/L)']),
                            scr=safe_decimal(row['SCr (mg/dL)']),
                            cockcroft_gault_crcl=safe_decimal(row['Cockcroft-Gault CrCl']),
                            crp=safe_decimal(crp_value),
                            diagnosis1=str(row['Diagnosis1']).strip(),
                            diagnosis2=str(row['Diagnosis2']).strip() if str(row['Diagnosis2']).strip() else None,
                            pathogen=pathogen,
                            sample_type=sample_type,
                            antibiotics=str(row['Antibiotics']).strip(),
                            name=f"Patient_{imported_count + 1}",
                            allergies="Penicillin" if imported_count == 0 else "None"  # First patient has penicillin allergy
                        )
                        
                        imported_count += 1
                        
                        if imported_count % 10 == 0:
                            self.stdout.write(f'Imported {imported_count} patients...')
                            
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'Error importing row {row_num}: {str(e)}')
                        )
                        # Print the problematic row for debugging
                        if error_count <= 3:  # Only show first 3 errors in detail
                            self.stdout.write(f'Row data: {dict(row)}')
                        continue
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(f'Import completed!')
        )
        self.stdout.write(f'Successfully imported: {imported_count} patients')
        if error_count > 0:
            self.stdout.write(f'Errors encountered: {error_count} rows')
        
        # Show sample of imported data
        if imported_count > 0:
            sample_patient = Patient.objects.first()
            self.stdout.write(f'\nSample imported patient:')
            self.stdout.write(f'ID: {sample_patient.patient_id}')
            self.stdout.write(f'Age: {sample_patient.age}, Gender: {sample_patient.get_gender_display()}')
            self.stdout.write(f'Diagnosis: {sample_patient.diagnosis1}')
            self.stdout.write(f'Pathogen: {sample_patient.pathogen}')
            self.stdout.write(f'Treatment: {sample_patient.antibiotics}')

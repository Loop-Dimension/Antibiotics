import csv
import os
from django.core.management.base import BaseCommand
from patients.models import Patient
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.db import transaction


class Command(BaseCommand):
    help = 'Import patient data from fil1.csv and fil2.csv'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='CSV file path (fil1.csv or fil2.csv)', required=True)
        parser.add_argument('--clear', action='store_true', help='Clear existing patient data before import')

    def safe_decimal(self, value, default=None):
        """Safely convert value to Decimal, handling various edge cases"""
        if not value or str(value).strip() == '' or str(value).strip().upper() == 'NA':
            return default
        try:
            # Remove quotes, spaces, and handle multiple dots
            clean_value = str(value).strip().replace('"', '').replace(',', '').replace(' ', '')
            # Handle cases like "179..94" - take only the first part before double dots
            if '..' in clean_value:
                clean_value = clean_value.split('..')[0] + '.' + clean_value.split('..')[-1]
            return Decimal(clean_value)
        except (InvalidOperation, ValueError) as e:
            self.stdout.write(self.style.WARNING(f'Could not convert "{value}" to Decimal: {e}'))
            return default

    def safe_string(self, value, default=''):
        """Safely convert value to string, handling None and NA"""
        if not value or str(value).strip().upper() in ['NA', 'NONE', '']:
            return default
        return str(value).strip()

    def get_row_value(self, row, column_name, column_map):
        """Get value from row using normalized column name"""
        actual_column = column_map.get(column_name, column_name)
        return row.get(actual_column, '')

    def handle(self, *args, **options):
        csv_file = options['file']

        # Check if file exists
        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'File {csv_file} does not exist'))
            return

        # Clear existing data if requested
        if options['clear']:
            self.stdout.write('Clearing existing patient data...')
            Patient.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing data'))

        imported_count = 0
        error_count = 0
        errors = []

        with open(csv_file, 'r', encoding='utf-8-sig') as file:  # utf-8-sig handles BOM
            reader = csv.DictReader(file)

            # Detect CSV columns and normalize them (strip spaces)
            columns = reader.fieldnames
            self.stdout.write(f'Detected columns: {columns}')

            # Create a mapping for column names (handle trailing/leading spaces)
            column_map = {col.strip(): col for col in columns}

            # Determine file type based on columns
            has_admission = 'Admission' in column_map
            has_antibiogram = 'Antibiogram' in column_map
            has_antibiotics1 = 'Antibiotics1' in column_map
            has_antibiotics2 = 'Antibiotics2' in column_map or 'Antibiotics2' in column_map
            has_antibiotics = 'Antibiotics' in column_map

            file_type = "fil1.csv" if has_admission else "fil2.csv"
            self.stdout.write(f'Detected file type: {file_type}')

            with transaction.atomic():
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    try:
                        # Skip empty rows
                        if not self.get_row_value(row, 'Date', column_map) or not self.get_row_value(row, 'Age', column_map):
                            continue

                        # Parse date
                        date_str = self.safe_string(self.get_row_value(row, 'Date', column_map))
                        if not date_str:
                            raise ValueError("Date is required")

                        if '.' in date_str:
                            # Handle format like 2025.12.17 or 2025.8.12 or 2022.11.30
                            parts = date_str.split('.')
                            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                            date_obj = datetime(year, month, day).date()
                        else:
                            # Handle other formats
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                        # Handle gender (1=Male, 0=Female)
                        male_value = self.safe_string(self.get_row_value(row, 'Male', column_map))
                        gender = 'M' if male_value == '1' else 'F' if male_value == '0' else None

                        # Handle admission (default to 1 if not present)
                        admission = int(self.get_row_value(row, 'Admission', column_map) or 1) if has_admission else 1

                        # Handle age
                        age_value = self.safe_string(self.get_row_value(row, 'Age', column_map))
                        if not age_value:
                            raise ValueError("Age is required")
                        age = int(float(age_value))

                        # Handle required fields with defaults
                        body_weight = self.safe_decimal(self.get_row_value(row, 'BW', column_map))
                        if body_weight is None:
                            raise ValueError("Body weight is required")

                        scr = self.safe_decimal(self.get_row_value(row, 'SCr (mg/dL)', column_map))
                        if scr is None:
                            raise ValueError("Serum creatinine (SCr) is required")

                        crcl = self.safe_decimal(self.get_row_value(row, 'Cockcroft-Gault CrCl', column_map))
                        if crcl is None:
                            raise ValueError("Creatinine clearance (CrCl) is required")

                        # Handle diagnosis
                        diagnosis1 = self.safe_string(self.get_row_value(row, 'Diagnosis1', column_map), 'Unknown diagnosis')
                        diagnosis2 = self.safe_string(self.get_row_value(row, 'Diagnosis2', column_map)) or None

                        # Handle pathogen
                        pathogen = self.safe_string(self.get_row_value(row, 'Pathogen', column_map), 'Unknown')
                        if pathogen.upper() == 'NA' or pathogen.lower() == 'pending':
                            pathogen = 'Unknown' if pathogen.upper() == 'NA' else 'Culture pending'

                        # Handle sample type
                        sample_type = self.safe_string(self.get_row_value(row, 'Sample', column_map), 'Not specified')

                        # Handle antibiotics based on file type
                        if has_antibiotics1:
                            # fil1.csv format
                            antibiotics = self.safe_string(self.get_row_value(row, 'Antibiotics1', column_map), 'None')
                            antibiotics2 = self.safe_string(self.get_row_value(row, 'Antibiotics2', column_map)) or None
                        else:
                            # fil2.csv format
                            antibiotics = self.safe_string(self.get_row_value(row, 'Antibiotics', column_map), 'None')
                            antibiotics2 = None

                        # Handle antibiogram (only in fil1.csv)
                        antibiogram = None
                        if has_antibiogram:
                            antibiogram = self.safe_string(self.get_row_value(row, 'Antibiogram', column_map)) or None

                        # Handle case number
                        case_no = None
                        case_no_str = self.safe_string(self.get_row_value(row, 'Case_no', column_map))
                        if case_no_str:
                            try:
                                case_no = int(float(case_no_str))
                            except (ValueError, TypeError):
                                pass

                        # Create patient record
                        patient = Patient.objects.create(
                            case_no=case_no,
                            name=f"Patient_{case_no if case_no else imported_count + 1}",
                            date_recorded=date_obj,
                            age=age,
                            gender=gender,
                            admission=admission,
                            body_weight=body_weight,
                            height=self.safe_decimal(self.get_row_value(row, 'Height', column_map)),
                            diagnosis1=diagnosis1,
                            diagnosis2=diagnosis2,
                            scr=scr,
                            cockcroft_gault_crcl=crcl,
                            wbc=self.safe_decimal(self.get_row_value(row, 'WBC', column_map)),
                            hb=self.safe_decimal(self.get_row_value(row, 'Hb', column_map)),
                            platelet=self.safe_decimal(self.get_row_value(row, 'PLT', column_map)),
                            ast=self.safe_decimal(self.get_row_value(row, 'AST(IU/L)', column_map)),
                            alt=self.safe_decimal(self.get_row_value(row, 'ALT(IU/L)', column_map)),
                            crp=self.safe_decimal(self.get_row_value(row, 'CRP(mg/L)', column_map)),
                            pathogen=pathogen,
                            antibiogram=antibiogram,
                            sample_type=sample_type,
                            antibiotics=antibiotics,
                            antibiotics2=antibiotics2,
                        )

                        imported_count += 1

                        if imported_count % 5 == 0:
                            self.stdout.write(f'Imported {imported_count} patients...')

                    except Exception as e:
                        error_count += 1
                        error_msg = f'Row {row_num}: {str(e)}'
                        errors.append(error_msg)
                        self.stdout.write(self.style.WARNING(f'Error importing {error_msg}'))

                        # Print the problematic row for debugging (first 3 errors only)
                        if error_count <= 3:
                            self.stdout.write(f'Row data: {dict(row)}')
                        continue

        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS(f'Import completed!'))
        self.stdout.write(self.style.SUCCESS(f'{"="*60}'))
        self.stdout.write(f'Successfully imported: {imported_count} patients')

        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'Errors encountered: {error_count} rows'))
            if len(errors) <= 10:
                for error in errors:
                    self.stdout.write(self.style.WARNING(f'  - {error}'))

        # Show sample of imported data
        if imported_count > 0:
            self.stdout.write(f'\n{"-"*60}')
            self.stdout.write('Sample imported patients:')
            self.stdout.write(f'{"-"*60}')

            for patient in Patient.objects.all()[:3]:
                self.stdout.write(f'\nPatient ID: {patient.patient_id} (Case #{patient.case_no})')
                self.stdout.write(f'  Name: {patient.name}')
                self.stdout.write(f'  Age: {patient.age}, Gender: {patient.get_gender_display() if patient.gender else "Unknown"}')
                self.stdout.write(f'  Admission: {patient.get_admission_display()}')
                self.stdout.write(f'  Date: {patient.date_recorded}')
                self.stdout.write(f'  Diagnosis: {patient.diagnosis1}')
                self.stdout.write(f'  Pathogen: {patient.pathogen}')
                self.stdout.write(f'  CrCl: {patient.cockcroft_gault_crcl} mL/min')
                self.stdout.write(f'  Treatment: {patient.antibiotics}')
                if patient.antibiotics2:
                    self.stdout.write(f'  Alternative: {patient.antibiotics2[:100]}...')

            self.stdout.write(f'\nTotal patients in database: {Patient.objects.count()}')

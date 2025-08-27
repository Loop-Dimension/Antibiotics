#!/usr/bin/env python
"""
Management command to fix and import the remaining antibiotic dosing data.
"""
import pandas as pd
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from patients.models import (
    Condition, Severity, Pathogen, SeverityPathogen, AntibioticDosing
)


class Command(BaseCommand):
    help = 'Fix and import the remaining antibiotic dosing data from CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='Antibiotics.csv',
            help='CSV file path to import (default: Antibiotics.csv)'
        )

    def handle(self, *args, **options):
        csv_file = options['file']

        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file}')
            )
            return

        try:
            self.import_remaining_data(csv_file)
            self.stdout.write(
                self.style.SUCCESS('Successfully imported remaining antibiotic dosing data!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing data: {str(e)}')
            )
            raise

    def import_remaining_data(self, csv_file):
        """Import the remaining data, fixing problematic records"""
        self.stdout.write(f'Reading CSV file: {csv_file}')
        
        # Try different encodings
        encodings = ['latin-1', 'utf-8', 'cp1252', 'iso-8859-1']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(csv_file, encoding=encoding)
                self.stdout.write(f'Successfully read with encoding: {encoding}')
                break
            except Exception as e:
                continue
        
        if df is None:
            raise Exception('Could not read CSV file with any encoding')

        # Clean up column names and data
        df.columns = df.columns.str.strip()
        
        # Remove empty rows
        df = df.dropna(subset=['Antibiotics', 'Condition'])
        
        self.stdout.write(f'Found {len(df)} records to process')

        with transaction.atomic():
            self.import_antibiotic_dosing_fixed(df)

    def import_antibiotic_dosing_fixed(self, df):
        """Import antibiotic dosing guidelines with fixes for problematic data"""
        self.stdout.write('Importing antibiotic dosing guidelines with fixes...')
        
        created_count = 0
        skipped_count = 0
        fixed_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Extract and clean data
                antibiotic = str(row['Antibiotics']).strip() if pd.notna(row['Antibiotics']) else ''
                condition_name = str(row['Condition']).strip() if pd.notna(row['Condition']) else ''
                severity_level = str(row['Severity']).strip() if pd.notna(row['Severity']) else ''
                dose = str(row['Dose']).strip() if pd.notna(row['Dose']) else ''
                route_str = str(row['Route']).strip() if pd.notna(row['Route']) else ''
                interval = str(row['Interval']).strip() if pd.notna(row['Interval']) else ''
                duration = str(row['Duration']).strip() if pd.notna(row['Duration']) else ''
                crcl_min = row['CcCl_min'] if pd.notna(row['CcCl_min']) else None
                crcl_max = row['CcCl_max'] if pd.notna(row['CcCl_max']) else None
                dialysis_type = str(row['DialysisType']).strip().upper() if pd.notna(row['DialysisType']) else ''
                patient_type = str(row['PatientType']).strip().lower() if pd.notna(row['PatientType']) else 'adult'
                remark = str(row['Remark']).strip() if pd.notna(row['Remark']) else ''
                pathogens_str = str(row['Pathogens']).strip() if pd.notna(row['Pathogens']) else ''
                
                # Clean special characters from data
                dose = dose.replace('\t', '').replace('\xa0', '')
                interval = interval.replace('\t', '').replace('\xa0', '')
                duration = duration.replace('\t', '').replace('\xa0', '')
                
                # Skip if essential fields are missing
                if not all([antibiotic, condition_name, severity_level]):
                    skipped_count += 1
                    continue
                
                # Fix problematic Levofloxacin data where Route contains antibiotic name
                if 'Levofloxacin' in route_str and '750mg' in route_str:
                    # These records have data shifted - fix them
                    if antibiotic == 'Levofloxacin  750mg':
                        # Restore proper route based on the pattern
                        if dose == 'No dose adjustment':
                            route_str = 'PO/IV'  # Standard route for no adjustment
                        elif '750 mg' in dose:
                            route_str = 'PO/IV'  # Standard route for 750mg
                        elif '500 mg' in dose:
                            route_str = 'PO/IV'  # Standard route for 500mg
                        else:
                            route_str = 'PO/IV'  # Default to PO/IV
                        
                        fixed_count += 1
                        self.stdout.write(f'  Fixed Levofloxacin record #{idx + 2}: Route set to {route_str}')
                
                # Get condition and severity
                try:
                    condition = Condition.objects.get(name=condition_name)
                    severity = Severity.objects.get(condition=condition, level=severity_level)
                except (Condition.DoesNotExist, Severity.DoesNotExist) as e:
                    self.stdout.write(
                        self.style.WARNING(f'Condition/Severity not found: {condition_name} - {severity_level}')
                    )
                    skipped_count += 1
                    continue
                
                # Process routes
                routes = []
                if route_str and route_str not in ['nan', 'None']:
                    if '/' in route_str:
                        routes = [r.strip() for r in route_str.split('/')]
                    else:
                        routes = [route_str]
                
                # Map dialysis types
                dialysis_mapping = {
                    'HD': 'hd',
                    'PD': 'pd',
                    'CRRT': 'crrt',
                    'ECMO': 'ecmo',
                    '': 'none'
                }
                dialysis_type_mapped = dialysis_mapping.get(dialysis_type, 'none')
                
                # Set default CrCl values if not provided and no dialysis
                if crcl_min is None and crcl_max is None and dialysis_type_mapped == 'none':
                    crcl_min = 0.0
                    crcl_max = 999.0
                elif crcl_min is None:
                    crcl_min = 0.0
                elif crcl_max is None:
                    crcl_max = 999.0
                
                # Skip if we have NaN CrCl values and no dialysis
                if pd.isna(crcl_min) and pd.isna(crcl_max) and dialysis_type_mapped == 'none':
                    crcl_min = 0.0
                    crcl_max = 999.0
                
                # Check if similar record exists (more relaxed check)
                similar_records = AntibioticDosing.objects.filter(
                    antibiotic=antibiotic,
                    condition=condition,
                    severity=severity,
                    crcl_min=crcl_min or 0.0,
                    crcl_max=crcl_max or 999.0,
                    dialysis_type=dialysis_type_mapped,
                    patient_type=patient_type,
                    dose=dose,
                    interval=interval,
                    duration=duration
                )
                
                # If a very similar record exists, skip
                if similar_records.exists():
                    skipped_count += 1
                    continue
                
                # Create antibiotic dosing record
                dosing = AntibioticDosing.objects.create(
                    antibiotic=antibiotic,
                    condition=condition,
                    severity=severity,
                    crcl_min=crcl_min or 0.0,
                    crcl_max=crcl_max or 999.0,
                    dialysis_type=dialysis_type_mapped,
                    dose=dose,
                    route=routes,
                    interval=interval,
                    duration=duration,
                    remark=remark,
                    patient_type=patient_type
                )
                
                # Add pathogen relationships
                if pathogens_str:
                    pathogens = [p.strip() for p in pathogens_str.split(',')]
                    for pathogen_name in pathogens:
                        if pathogen_name:
                            try:
                                pathogen = Pathogen.objects.get(name=pathogen_name)
                                dosing.pathogens.add(pathogen)
                            except Pathogen.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(f'Pathogen not found for dosing: {pathogen_name}')
                                )
                
                created_count += 1
                
                if created_count % 5 == 0:
                    self.stdout.write(f'  Processed {created_count} dosing guidelines...')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing row {idx + 2}: {str(e)}')
                )
                skipped_count += 1
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} new antibiotic dosing guidelines')
        )
        if fixed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Fixed {fixed_count} problematic records')
            )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Skipped {skipped_count} records (duplicates or invalid data)')
            )

#!/usr/bin/env python
"""
Management command to import antibiotic dosing data from CSV file.
"""
import pandas as pd
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from patients.models import (
    Condition, Severity, Pathogen, SeverityPathogen, AntibioticDosing
)


class Command(BaseCommand):
    help = 'Import antibiotic dosing data from Antibiotics.csv'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='Antibiotics.csv',
            help='CSV file path to import (default: Antibiotics.csv)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before import'
        )

    def handle(self, *args, **options):
        csv_file = options['file']
        clear_existing = options['clear']

        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file}')
            )
            return

        if clear_existing:
            self.clear_existing_data()

        try:
            self.import_csv_data(csv_file)
            self.stdout.write(
                self.style.SUCCESS('Successfully imported antibiotic dosing data!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing data: {str(e)}')
            )
            raise

    def clear_existing_data(self):
        """Clear existing antibiotic dosing data"""
        self.stdout.write('Clearing existing data...')
        
        # Delete in correct order to respect foreign key constraints
        AntibioticDosing.objects.all().delete()
        SeverityPathogen.objects.all().delete()
        Severity.objects.all().delete()
        Condition.objects.all().delete()
        Pathogen.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

    def import_csv_data(self, csv_file):
        """Import data from CSV file"""
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
            # Step 1: Create conditions
            self.create_conditions(df)
            
            # Step 2: Create pathogens
            self.create_pathogens(df)
            
            # Step 3: Create severities and severity-pathogen relationships
            self.create_severities_and_relationships(df)
            
            # Step 4: Create antibiotic dosing guidelines
            self.create_antibiotic_dosing(df)

    def create_conditions(self, df):
        """Create condition records"""
        self.stdout.write('Creating conditions...')
        
        conditions = df['Condition'].dropna().unique()
        for condition_name in conditions:
            condition_name = condition_name.strip()
            if condition_name:
                condition, created = Condition.objects.get_or_create(
                    name=condition_name
                )
                if created:
                    self.stdout.write(f'  Created condition: {condition_name}')

    def create_pathogens(self, df):
        """Create pathogen records"""
        self.stdout.write('Creating pathogens...')
        
        all_pathogens = set()
        pathogen_data = df['Pathogens'].dropna()
        
        for pathogens_str in pathogen_data:
            if isinstance(pathogens_str, str):
                pathogens = [p.strip() for p in pathogens_str.split(',')]
                all_pathogens.update(pathogens)

        for pathogen_name in all_pathogens:
            if pathogen_name:
                pathogen, created = Pathogen.objects.get_or_create(
                    name=pathogen_name
                )
                if created:
                    self.stdout.write(f'  Created pathogen: {pathogen_name}')

    def create_severities_and_relationships(self, df):
        """Create severity records and severity-pathogen relationships"""
        self.stdout.write('Creating severities and pathogen relationships...')
        
        # Get unique condition-severity combinations
        combinations = df[['Condition', 'Severity', 'Pathogens']].dropna().drop_duplicates()
        
        for _, row in combinations.iterrows():
            condition_name = row['Condition'].strip()
            severity_level = row['Severity'].strip()
            pathogens_str = row['Pathogens'].strip()
            
            if not all([condition_name, severity_level, pathogens_str]):
                continue
                
            # Get the condition
            try:
                condition = Condition.objects.get(name=condition_name)
            except Condition.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Condition not found: {condition_name}')
                )
                continue
            
            # Create or get severity
            severity, created = Severity.objects.get_or_create(
                condition=condition,
                level=severity_level
            )
            if created:
                self.stdout.write(f'  Created severity: {condition_name} - {severity_level}')
            
            # Create pathogen relationships
            pathogens = [p.strip() for p in pathogens_str.split(',')]
            for pathogen_name in pathogens:
                if pathogen_name:
                    try:
                        pathogen = Pathogen.objects.get(name=pathogen_name)
                        severity_pathogen, created = SeverityPathogen.objects.get_or_create(
                            severity=severity,
                            pathogen=pathogen
                        )
                        if created:
                            self.stdout.write(f'  Linked: {severity_level} -> {pathogen_name}')
                    except Pathogen.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f'Pathogen not found: {pathogen_name}')
                        )

    def create_antibiotic_dosing(self, df):
        """Create antibiotic dosing guidelines"""
        self.stdout.write('Creating antibiotic dosing guidelines...')
        
        created_count = 0
        skipped_count = 0
        
        for _, row in df.iterrows():
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
                
                # Skip records with problematic data (like Route in wrong column)
                if 'Levofloxacin' in route_str and '750mg' in route_str:
                    skipped_count += 1
                    continue
                
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
                dialysis_type = dialysis_mapping.get(dialysis_type, 'none')
                
                # Set default CrCl values if not provided and no dialysis
                if crcl_min is None and crcl_max is None and dialysis_type == 'none':
                    crcl_min = 0.0
                    crcl_max = 999.0
                elif crcl_min is None:
                    crcl_min = 0.0
                elif crcl_max is None:
                    crcl_max = 999.0
                
                # Skip if we have NaN CrCl values and no dialysis
                if pd.isna(crcl_min) and pd.isna(crcl_max) and dialysis_type == 'none':
                    crcl_min = 0.0
                    crcl_max = 999.0
                
                # Check for existing record with same unique constraint
                existing = AntibioticDosing.objects.filter(
                    antibiotic=antibiotic,
                    condition=condition,
                    severity=severity,
                    crcl_min=crcl_min or 0.0,
                    crcl_max=crcl_max or 999.0,
                    dialysis_type=dialysis_type,
                    patient_type=patient_type,
                    dose=dose,
                    interval=interval
                ).exists()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Create antibiotic dosing record
                dosing = AntibioticDosing.objects.create(
                    antibiotic=antibiotic,
                    condition=condition,
                    severity=severity,
                    crcl_min=crcl_min or 0.0,
                    crcl_max=crcl_max or 999.0,
                    dialysis_type=dialysis_type,
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
                
                if created_count % 10 == 0:
                    self.stdout.write(f'  Processed {created_count} dosing guidelines...')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing row: {str(e)}')
                )
                # Comment out the row data print to avoid clutter
                # self.stdout.write(f'Row data: {dict(row)}')
                skipped_count += 1
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} antibiotic dosing guidelines')
        )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Skipped {skipped_count} records due to missing/invalid data')
            )

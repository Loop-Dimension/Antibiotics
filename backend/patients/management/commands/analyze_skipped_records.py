#!/usr/bin/env python
"""
Management command to analyze skipped records during CSV import.
"""
import pandas as pd
import os
from django.core.management.base import BaseCommand
from patients.models import (
    Condition, Severity, Pathogen, SeverityPathogen, AntibioticDosing
)


class Command(BaseCommand):
    help = 'Analyze skipped records from Antibiotics.csv import'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='Antibiotics.csv',
            help='CSV file path to analyze (default: Antibiotics.csv)'
        )

    def handle(self, *args, **options):
        csv_file = options['file']

        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file}')
            )
            return

        try:
            self.analyze_skipped_records(csv_file)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error analyzing data: {str(e)}')
            )
            raise

    def analyze_skipped_records(self, csv_file):
        """Analyze which records would be skipped and why"""
        self.stdout.write(f'Analyzing CSV file: {csv_file}')
        
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
        
        self.stdout.write(f'Found {len(df)} records to analyze')
        self.stdout.write('\n=== ANALYZING ALL RECORDS ===')

        skipped_records = []
        processed_count = 0
        
        for idx, row in df.iterrows():
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
            
            skip_reason = None
            
            # Check skip conditions
            if not all([antibiotic, condition_name, severity_level]):
                skip_reason = f"Missing essential fields - antibiotic: '{antibiotic}', condition: '{condition_name}', severity: '{severity_level}'"
            
            elif 'Levofloxacin' in route_str and '750mg' in route_str:
                skip_reason = f"Problematic data - Route contains antibiotic name: '{route_str}'"
            
            else:
                # Check if condition and severity exist
                try:
                    condition = Condition.objects.get(name=condition_name)
                    severity = Severity.objects.get(condition=condition, level=severity_level)
                    
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
                    
                    # Check for existing record with same unique constraint
                    existing = AntibioticDosing.objects.filter(
                        antibiotic=antibiotic,
                        condition=condition,
                        severity=severity,
                        crcl_min=crcl_min or 0.0,
                        crcl_max=crcl_max or 999.0,
                        dialysis_type=dialysis_type_mapped,
                        patient_type=patient_type,
                        dose=dose,
                        interval=interval
                    ).exists()
                    
                    if existing:
                        skip_reason = f"Duplicate record already exists in database"
                    
                except (Condition.DoesNotExist, Severity.DoesNotExist) as e:
                    skip_reason = f"Condition/Severity not found: {condition_name} - {severity_level}"
            
            if skip_reason:
                skipped_records.append({
                    'index': idx,
                    'antibiotic': antibiotic,
                    'condition': condition_name,
                    'severity': severity_level,
                    'dose': dose,
                    'route': route_str,
                    'interval': interval,
                    'duration': duration,
                    'crcl_min': crcl_min,
                    'crcl_max': crcl_max,
                    'dialysis_type': dialysis_type,
                    'patient_type': patient_type,
                    'remark': remark,
                    'pathogens': pathogens_str,
                    'reason': skip_reason
                })
            else:
                processed_count += 1

        self.stdout.write(f'\n=== SUMMARY ===')
        self.stdout.write(f'Total records: {len(df)}')
        self.stdout.write(f'Would be processed: {processed_count}')
        self.stdout.write(f'Would be skipped: {len(skipped_records)}')
        
        if skipped_records:
            self.stdout.write(f'\n=== SKIPPED RECORDS DETAILS ===')
            for i, record in enumerate(skipped_records, 1):
                self.stdout.write(f'\n--- Skipped Record #{i} (Row {record["index"] + 2}) ---')
                self.stdout.write(f'Antibiotic: {record["antibiotic"]}')
                self.stdout.write(f'Condition: {record["condition"]}')
                self.stdout.write(f'Severity: {record["severity"]}')
                self.stdout.write(f'Dose: {record["dose"]}')
                self.stdout.write(f'Route: {record["route"]}')
                self.stdout.write(f'Interval: {record["interval"]}')
                self.stdout.write(f'Duration: {record["duration"]}')
                self.stdout.write(f'CrCl Min: {record["crcl_min"]}')
                self.stdout.write(f'CrCl Max: {record["crcl_max"]}')
                self.stdout.write(f'Dialysis: {record["dialysis_type"]}')
                self.stdout.write(f'Patient Type: {record["patient_type"]}')
                self.stdout.write(f'Remark: {record["remark"]}')
                self.stdout.write(f'Pathogens: {record["pathogens"]}')
                self.stdout.write(self.style.ERROR(f'SKIP REASON: {record["reason"]}'))
        else:
            self.stdout.write(self.style.SUCCESS('No records would be skipped!'))

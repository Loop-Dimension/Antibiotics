#!/usr/bin/env python
"""
Import patient data from both CSV files and create AntibioticDosing recommendations
- File 1 (Patient data_0106.csv): Has Antibiotics1 (current) and Antibiotics2 (recommendations)
- File 2 (fil2.csv): Has Antibiotics (current), recommendations will be created from dosing rules
"""
import os
import sys
import csv
import django
from datetime import datetime
from decimal import Decimal

# Set up Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical.settings')
django.setup()

from patients.models import Patient, AntibioticDosing, Condition, Severity, Pathogen


def parse_date(date_str):
    """Parse date from format YYYY.MM.DD"""
    if not date_str:
        return None
    try:
        date_str = date_str.strip().replace('/', '.').replace('-', '.')
        parts = date_str.split('.')
        if len(parts) == 3:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            return datetime(year, month, day).date()
    except (ValueError, IndexError):
        pass
    return None


def clean_numeric(value, decimal_places=2):
    """Clean and parse numeric value"""
    if not value:
        return None
    try:
        clean = str(value).strip().replace(',', '').replace(' ', '')
        if not clean:
            return None
        return round(float(clean), decimal_places)
    except (ValueError, TypeError):
        return None


def get_value(row, key_variants):
    """Get value from row handling BOM and spaces in keys"""
    for key in key_variants:
        for actual_key in row.keys():
            if actual_key.strip().replace('\ufeff', '').lower() == key.lower():
                return row[actual_key]
    return None


def read_csv_file(csv_path):
    """Read CSV file with proper encoding"""
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(csv_path, 'r', encoding=encoding) as f:
                content = f.read()
                print(f"  ✅ Read file with encoding: {encoding}")
                return content
        except UnicodeDecodeError:
            continue
    
    print(f"  ❌ Could not read file with any encoding")
    return None


def create_antibiotic_dosing_from_recommendations(diagnosis, recommendations_text, patient_crcl):
    """Create AntibioticDosing records from recommendation text"""
    if not recommendations_text or not diagnosis:
        return 0
    
    # Get or create condition based on diagnosis
    condition_name = diagnosis.strip()
    condition, _ = Condition.objects.get_or_create(
        name=condition_name,
        defaults={'description': f'Condition: {condition_name}'}
    )
    
    # Get or create default severity
    severity, _ = Severity.objects.get_or_create(
        condition=condition,
        level='Standard',
        defaults={'severity_order': 1}
    )
    
    # Parse recommendation lines
    lines = recommendations_text.strip().split('\n')
    created_count = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Parse antibiotic recommendation (e.g., "IV ceftriaxone 1-2g q24hr")
        parts = line.split()
        if len(parts) < 2:
            continue
        
        # Extract route, antibiotic name, dose, interval
        route = []
        antibiotic_name = line
        dose = ''
        interval = ''
        
        # Check for route prefix
        if parts[0].upper() in ['IV', 'PO', 'IM', 'SC']:
            route = [parts[0].upper()]
            antibiotic_name = ' '.join(parts[1:])
        
        # Try to extract interval (e.g., q8hr, q12hr, q24hr, bid, tid)
        for i, part in enumerate(parts):
            if part.lower().startswith('q') and any(c.isdigit() for c in part):
                interval = part
            elif part.lower() in ['bid', 'tid', 'qid', 'daily']:
                interval = part
        
        # Check if this dosing already exists
        existing = AntibioticDosing.objects.filter(
            antibiotic=antibiotic_name,
            condition=condition,
            severity=severity
        ).first()
        
        if not existing:
            # Determine CrCl range based on patient's CrCl
            crcl_min = None
            crcl_max = None
            if patient_crcl:
                if patient_crcl >= 50:
                    crcl_min = 50
                    crcl_max = 999
                elif patient_crcl >= 30:
                    crcl_min = 30
                    crcl_max = 49
                elif patient_crcl >= 10:
                    crcl_min = 10
                    crcl_max = 29
                else:
                    crcl_min = 0
                    crcl_max = 9
            
            AntibioticDosing.objects.create(
                antibiotic=antibiotic_name,
                condition=condition,
                severity=severity,
                crcl_min=crcl_min,
                crcl_max=crcl_max,
                dialysis_type='none',
                dose=dose or 'As prescribed',
                route=route,
                interval=interval,
                duration='',
                remark='Imported from patient data',
                patient_type='adult'
            )
            created_count += 1
    
    return created_count


def import_file1():
    """Import fil1.csv with Antibiotics1 and Antibiotics2"""
    print("\n📁 Importing File 1: fil1.csv")
    
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'fil1.csv')
    csv_path = os.path.abspath(csv_path)
    
    if not os.path.exists(csv_path):
        print(f"  ❌ File not found: {csv_path}")
        return 0, 0
    
    content = read_csv_file(csv_path)
    if not content:
        return 0, 0
    
    import io
    csv_file = io.StringIO(content)
    reader = csv.DictReader(csv_file)
    
    patients_imported = 0
    dosings_created = 0
    
    for row_num, row in enumerate(reader, start=2):
        try:
            case_no_str = get_value(row, ['Case_no', 'case_no', 'Case_no '])
            if not case_no_str:
                continue
            case_no = int(str(case_no_str).strip())
            
            diagnosis1 = str(get_value(row, ['Diagnosis1', 'diagnosis1']) or '').strip()
            if not diagnosis1:
                continue
            
            # Parse all fields
            male_val = get_value(row, ['Male', 'male'])
            gender = 'M' if str(male_val).strip() == '1' else 'F'
            
            admission_val = get_value(row, ['Admission', 'admission'])
            admission = int(str(admission_val).strip()) if admission_val else 1
            
            age = int(float(str(get_value(row, ['Age', 'age']) or 0).strip()))
            body_weight = clean_numeric(get_value(row, ['BW', 'bw'])) or 70.0
            height = clean_numeric(get_value(row, ['Height', 'height']))
            date_recorded = parse_date(get_value(row, ['Date', 'date'])) or datetime.now().date()
            
            # Lab values
            wbc = clean_numeric(get_value(row, ['WBC', 'wbc']))
            hb = clean_numeric(get_value(row, ['Hb', 'hb']), 1)
            platelet = clean_numeric(get_value(row, ['PLT', 'plt']), 0)
            ast = clean_numeric(get_value(row, ['AST(IU/L)', 'ast']))
            alt = clean_numeric(get_value(row, ['ALT(IU/L)', 'alt']))
            scr = clean_numeric(get_value(row, ['SCr (mg/dL)', 'scr'])) or 1.0
            crcl = clean_numeric(get_value(row, ['Cockcroft-Gault CrCl', 'crcl'])) or 60.0
            crp = clean_numeric(get_value(row, ['CRP(mg/L)', 'crp']))
            
            # Clinical data
            pathogen = str(get_value(row, ['Pathogen', 'pathogen']) or 'Unknown').strip()
            antibiogram = str(get_value(row, ['Antibiogram', 'antibiogram']) or '').strip()
            sample = str(get_value(row, ['Sample', 'sample']) or 'Not specified').strip()
            
            # Antibiotics
            antibiotics1 = str(get_value(row, ['Antibiotics1', 'antibiotics1']) or 'None').strip()
            antibiotics2 = str(get_value(row, ['Antibiotics2', 'antibiotics2']) or '').strip()
            diagnosis2 = str(get_value(row, ['Diagnosis2', 'diagnosis2']) or '').strip()
            
            # Create patient
            patient = Patient.objects.create(
                case_no=case_no,
                name=f"Patient {case_no}",
                date_recorded=date_recorded,
                age=age,
                gender=gender,
                admission=admission,
                body_weight=body_weight,
                height=height,
                diagnosis1=diagnosis1,
                diagnosis2=diagnosis2,
                scr=scr,
                cockcroft_gault_crcl=crcl,
                wbc=wbc,
                hb=hb,
                platelet=platelet,
                ast=ast,
                alt=alt,
                crp=crp,
                pathogen=pathogen,
                antibiogram=antibiogram,
                sample_type=sample,
                antibiotics=antibiotics1,  # Current antibiotic
                antibiotics2=antibiotics2,  # Alternative recommendations (stored for reference)
            )
            patients_imported += 1
            
            # Create AntibioticDosing entries from Antibiotics2
            if antibiotics2:
                dosings_created += create_antibiotic_dosing_from_recommendations(diagnosis1, antibiotics2, crcl)
            
        except Exception as e:
            print(f"  ❌ Error row {row_num}: {e}")
    
    print(f"  ✅ Imported {patients_imported} patients, created {dosings_created} dosing records")
    return patients_imported, dosings_created


def import_file2():
    """Import fil2.csv with single Antibiotics field"""
    print("\n📁 Importing File 2: fil2.csv")
    
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'fil2.csv')
    csv_path = os.path.abspath(csv_path)
    
    if not os.path.exists(csv_path):
        print(f"  ❌ File not found: {csv_path}")
        return 0, 0
    
    content = read_csv_file(csv_path)
    if not content:
        return 0, 0
    
    import io
    csv_file = io.StringIO(content)
    reader = csv.DictReader(csv_file)
    
    patients_imported = 0
    dosings_created = 0
    
    # Get existing max case_no to offset
    max_case = Patient.objects.order_by('-case_no').values_list('case_no', flat=True).first() or 0
    case_offset = max_case + 100  # Offset file2 case numbers by 100
    
    for row_num, row in enumerate(reader, start=2):
        try:
            case_no_str = get_value(row, ['Case_no', 'case_no', 'Case_no '])
            if not case_no_str:
                continue
            original_case_no = int(str(case_no_str).strip())
            case_no = case_offset + original_case_no  # Unique case number
            
            diagnosis1 = str(get_value(row, ['Diagnosis1', 'diagnosis1']) or '').strip()
            if not diagnosis1:
                continue
            
            # Parse all fields
            male_val = get_value(row, ['Male', 'male'])
            gender = 'M' if str(male_val).strip() == '1' else 'F'
            
            age = int(float(str(get_value(row, ['Age', 'age']) or 0).strip()))
            body_weight = clean_numeric(get_value(row, ['BW', 'bw'])) or 70.0
            height = clean_numeric(get_value(row, ['Height', 'height']))
            date_recorded = parse_date(get_value(row, ['Date', 'date'])) or datetime.now().date()
            
            # Lab values
            wbc = clean_numeric(get_value(row, ['WBC', 'wbc']))
            hb = clean_numeric(get_value(row, ['Hb', 'hb']), 1)
            platelet = clean_numeric(get_value(row, ['PLT', 'plt']), 0)
            ast = clean_numeric(get_value(row, ['AST(IU/L)', 'ast']))
            alt = clean_numeric(get_value(row, ['ALT(IU/L)', 'alt']))
            scr = clean_numeric(get_value(row, ['SCr (mg/dL)', 'scr'])) or 1.0
            crcl = clean_numeric(get_value(row, ['Cockcroft-Gault CrCl', 'crcl'])) or 60.0
            crp = clean_numeric(get_value(row, ['CRP(mg/L)', 'crp']))
            
            # Clinical data
            pathogen = str(get_value(row, ['Pathogen', 'pathogen']) or 'Unknown').strip()
            sample = str(get_value(row, ['Sample', 'sample']) or 'Not specified').strip()
            
            # Antibiotics (current treatment)
            antibiotics = str(get_value(row, ['Antibiotics', 'antibiotics']) or 'None').strip()
            diagnosis2 = str(get_value(row, ['Diagnosis2', 'diagnosis2']) or '').strip()
            
            # Create patient (no Admission field in file2, default to 1)
            patient = Patient.objects.create(
                case_no=case_no,
                name=f"Patient {case_no}",
                date_recorded=date_recorded,
                age=age,
                gender=gender,
                admission=1,  # Default to inpatient
                body_weight=body_weight,
                height=height,
                diagnosis1=diagnosis1,
                diagnosis2=diagnosis2,
                scr=scr,
                cockcroft_gault_crcl=crcl,
                wbc=wbc,
                hb=hb,
                platelet=platelet,
                ast=ast,
                alt=alt,
                crp=crp,
                pathogen=pathogen,
                antibiogram='',  # No antibiogram in file2
                sample_type=sample,
                antibiotics=antibiotics,  # Current antibiotic
                antibiotics2='',
            )
            patients_imported += 1
            
            # Create AntibioticDosing entry for this diagnosis with the current antibiotic as recommendation
            dosings_created += create_antibiotic_dosing_from_recommendations(diagnosis1, antibiotics, crcl)
            
        except Exception as e:
            print(f"  ❌ Error row {row_num}: {e}")
    
    print(f"  ✅ Imported {patients_imported} patients, created {dosings_created} dosing records")
    return patients_imported, dosings_created


def main():
    print("=" * 60)
    print("IMPORTING PATIENT DATA AND ANTIBIOTIC DOSING RECOMMENDATIONS")
    print("=" * 60)
    
    # Clear existing data
    print("\n🗑️ Clearing existing data...")
    Patient.objects.all().delete()
    AntibioticDosing.objects.all().delete()
    Condition.objects.all().delete()
    Severity.objects.all().delete()
    Pathogen.objects.all().delete()
    print("  ✅ All tables cleared")
    
    # Import both files
    p1, d1 = import_file1()
    p2, d2 = import_file2()
    
    # Summary
    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(f"Total Patients: {Patient.objects.count()}")
    print(f"Total AntibioticDosing: {AntibioticDosing.objects.count()}")
    print(f"Total Conditions: {Condition.objects.count()}")
    print(f"Total Severities: {Severity.objects.count()}")
    
    # Show conditions
    print("\nConditions created:")
    for c in Condition.objects.all():
        dosing_count = AntibioticDosing.objects.filter(condition=c).count()
        print(f"  - {c.name}: {dosing_count} dosing recommendations")


if __name__ == '__main__':
    main()

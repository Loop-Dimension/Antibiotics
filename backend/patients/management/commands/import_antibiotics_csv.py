import csv
import os
from django.core.management.base import BaseCommand
from patients.models import AntibioticDosing, Condition, Severity, Pathogen


class Command(BaseCommand):
    help = 'Import antibiotic dosing data from Antibiotics.csv with proper handling of CrCl ranges'

    def handle(self, *args, **options):
        # Clear existing data
        self.stdout.write(self.style.WARNING('Flushing existing AntibioticDosing data...'))
        AntibioticDosing.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully flushed AntibioticDosing table'))
        
        csv_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'Antibiotics.csv')
        
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'CSV file not found at {csv_file_path}'))
            return
            
        imported_count = 0
        error_count = 0
        
        # Try different encodings
        encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        file_content = None
        
        for encoding in encodings:
            try:
                with open(csv_file_path, 'r', encoding=encoding) as file:
                    file_content = file.read()
                    self.stdout.write(f'Successfully read file with encoding: {encoding}')
                    break
            except UnicodeDecodeError:
                continue
        
        if file_content is None:
            self.stdout.write(self.style.ERROR('Could not read file with any encoding'))
            return
            
        # Parse CSV content
        import io
        csv_file = io.StringIO(file_content)
        reader = csv.DictReader(csv_file)
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 because header is row 1
            try:
                # Clean and parse data
                antibiotic = row['Antibiotics'].strip()
                dose = row['Dose'].strip()
                route_str = row['Route'].strip()
                interval = row['Interval'].strip()
                duration = row['Duration'].strip()
                condition_name = row['Condition'].strip()
                severity_level = row[' Severity'].strip()  # Note space in column name
                pathogens_str = row[' Pathogens'].strip()  # Note space in column name
                crcl_min_str = row[' CcCl_min'].strip()  # Note space in column name
                crcl_max_str = row[' CcCl_max'].strip()  # Note space in column name
                dialysis_type_str = row[' DialysisType'].strip()  # Note space in column name
                patient_type = row[' PatientType'].strip()  # Note space in column name
                remark = row['Remark'].strip()
                
                # Skip empty rows
                if not antibiotic:
                    continue
                
                # Parse route (can be multiple, e.g., "PO/IV")
                routes = []
                if route_str:
                    route_parts = route_str.replace('/', ',').split(',')
                    for route in route_parts:
                        route = route.strip()
                        if route in ['PO', 'IV', 'IM', 'SC']:
                            routes.append(route)
                
                # Parse CrCl ranges - allow nulls
                crcl_min = None
                crcl_max = None
                
                if crcl_min_str and crcl_min_str != '':
                    try:
                        crcl_min = float(crcl_min_str)
                    except ValueError:
                        self.stdout.write(self.style.WARNING(f'Row {row_num}: Invalid CrCl_min value: {crcl_min_str}'))
                
                if crcl_max_str and crcl_max_str != '':
                    try:
                        crcl_max = float(crcl_max_str)
                    except ValueError:
                        self.stdout.write(self.style.WARNING(f'Row {row_num}: Invalid CrCl_max value: {crcl_max_str}'))
                
                # Parse dialysis type
                dialysis_type = 'none'
                if dialysis_type_str:
                    dialysis_mapping = {
                        'HD': 'hd',
                        'PD': 'pd', 
                        'CRRT': 'crrt',
                        'ECMO': 'ecmo'
                    }
                    dialysis_type = dialysis_mapping.get(dialysis_type_str.upper(), 'none')
                
                # Get or create condition
                condition, created = Condition.objects.get_or_create(
                    name=condition_name,
                    defaults={'description': f'Auto-imported condition: {condition_name}'}
                )
                
                # Get or create severity
                severity, created = Severity.objects.get_or_create(
                    condition=condition,
                    level=severity_level,
                    defaults={
                        'severity_order': 1
                    }
                )
                
                # Parse pathogens (comma-separated)
                pathogen_objects = []
                if pathogens_str:
                    pathogen_names = [p.strip() for p in pathogens_str.split(',')]
                    for pathogen_name in pathogen_names:
                        if pathogen_name:
                            pathogen, created = Pathogen.objects.get_or_create(
                                name=pathogen_name,
                                defaults={'description': f'Auto-imported pathogen: {pathogen_name}'}
                            )
                            pathogen_objects.append(pathogen)
                
                # Create the antibiotic dosing record
                antibiotic_dosing = AntibioticDosing.objects.create(
                    antibiotic=antibiotic,
                    condition=condition,
                    severity=severity,
                    crcl_min=crcl_min,  # Can be None
                    crcl_max=crcl_max,  # Can be None
                    dialysis_type=dialysis_type,
                    dose=dose,
                    route=routes,
                    interval=interval,
                    duration=duration,
                    remark=remark,
                    patient_type=patient_type.lower() if patient_type else 'adult'
                )
                
                # Add pathogens to the record
                if pathogen_objects:
                    antibiotic_dosing.pathogens.set(pathogen_objects)
                
                imported_count += 1
                
                if imported_count % 10 == 0:
                    self.stdout.write(f'Imported {imported_count} records...')
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Error importing row {row_num}: {str(e)}')
                )
                self.stdout.write(f'Row data: {row}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully imported {imported_count} antibiotic dosing records')
        )
        
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Encountered {error_count} errors during import')
            )
        
        # Show summary statistics
        total_records = AntibioticDosing.objects.count()
        records_with_crcl = AntibioticDosing.objects.filter(crcl_min__isnull=False, crcl_max__isnull=False).count()
        records_without_crcl = total_records - records_with_crcl
        
        self.stdout.write(
            self.style.SUCCESS(f'Summary:')
        )
        self.stdout.write(f'  Total records: {total_records}')
        self.stdout.write(f'  Records with CrCl ranges: {records_with_crcl}')
        self.stdout.write(f'  Records without CrCl ranges: {records_without_crcl}')
        
        # Show conditions and severities created
        conditions_count = Condition.objects.count()
        severities_count = Severity.objects.count()
        pathogens_count = Pathogen.objects.count()
        
        self.stdout.write(f'  Conditions: {conditions_count}')
        self.stdout.write(f'  Severities: {severities_count}')
        self.stdout.write(f'  Pathogens: {pathogens_count}')

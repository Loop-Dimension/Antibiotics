import csv
import os
from django.core.management.base import BaseCommand
from patients.models import AntibioticDosing


class Command(BaseCommand):
    help = 'Import antibiotic dosing data from Antibiotics.csv'

    def handle(self, *args, **options):
        # Clear existing data
        AntibioticDosing.objects.all().delete()
        
        csv_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'Antibiotics.csv')
        
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'CSV file not found at {csv_file_path}'))
            return
            
        imported_count = 0
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # Clean and parse data
                antibiotic = row['Antibiotics'].strip()
                crcl_range = row['CcCl (mL/m)'].strip()
                dose = row['Dose'].strip()
                route = row['Route'].strip()
                interval = row['Interval'].strip()
                remark = row['Remark'].strip()
                
                # Skip empty rows
                if not antibiotic:
                    continue
                
                # Fix common data issues
                if crcl_range.startswith('?'):
                    crcl_range = crcl_range.replace('?', '>=')
                elif crcl_range == '29-May':  # Excel converted range to date
                    crcl_range = '5-29'
                elif crcl_range == 'Oct-50':  # Excel converted range to date
                    crcl_range = '10-50'
                elif crcl_range == '30-Oct':  # Excel converted range to date
                    crcl_range = '10-30'
                
                # Determine pathogen effectiveness based on antibiotic type
                pathogen_effectiveness = []
                infection_types = []
                contraindications = []
                severity_score = 1
                
                antibiotic_lower = antibiotic.lower()
                
                # Define pathogen effectiveness
                if 'ciprofloxacin' in antibiotic_lower or 'levofloxacin' in antibiotic_lower:
                    pathogen_effectiveness = [
                        'Escherichia coli', 'Klebsiella pneumoniae', 'Pseudomonas aeruginosa',
                        'Staphylococcus epidermidis', 'Enterococcus faecalis'
                    ]
                    infection_types = ['UTI', 'pneumonia', 'intra-abdominal']
                    contraindications = ['fluoroquinolone allergy']
                    severity_score = 3
                
                elif 'ceftriaxone' in antibiotic_lower:
                    pathogen_effectiveness = [
                        'Escherichia coli', 'Klebsiella pneumoniae', 'Streptococcus pneumoniae',
                        'Haemophilus influenzae'
                    ]
                    infection_types = ['pneumonia', 'UTI', 'meningitis']
                    contraindications = ['cephalosporin allergy', 'penicillin allergy']
                    severity_score = 4
                
                elif 'cefepime' in antibiotic_lower:
                    pathogen_effectiveness = [
                        'Escherichia coli', 'Klebsiella pneumoniae', 'Pseudomonas aeruginosa',
                        'Streptococcus pneumoniae'
                    ]
                    infection_types = ['pneumonia', 'sepsis', 'neutropenia']
                    contraindications = ['cephalosporin allergy']
                    severity_score = 4
                
                elif 'piperacillin' in antibiotic_lower:
                    pathogen_effectiveness = [
                        'Pseudomonas aeruginosa', 'Escherichia coli', 'Klebsiella pneumoniae',
                        'Enterococcus faecalis', 'Streptococcus pneumoniae'
                    ]
                    infection_types = ['pneumonia', 'sepsis', 'intra-abdominal']
                    contraindications = ['penicillin allergy']
                    severity_score = 5
                
                elif 'ertapenem' in antibiotic_lower:
                    pathogen_effectiveness = [
                        'Escherichia coli', 'Klebsiella pneumoniae', 'Enterococcus faecalis'
                    ]
                    infection_types = ['UTI', 'intra-abdominal', 'pneumonia']
                    contraindications = ['carbapenem allergy', 'penicillin allergy']
                    severity_score = 4
                
                elif 'vancomycin' in antibiotic_lower:
                    pathogen_effectiveness = [
                        'Staphylococcus epidermidis', 'Enterococcus faecalis', 'MRSA'
                    ]
                    infection_types = ['sepsis', 'pneumonia', 'skin infection']
                    contraindications = ['vancomycin allergy']
                    severity_score = 5
                
                elif 'ceftazidime' in antibiotic_lower:
                    pathogen_effectiveness = [
                        'Klebsiella pneumoniae (CRE)', 'Pseudomonas aeruginosa',
                        'Carbapenem-resistant organisms'
                    ]
                    infection_types = ['sepsis', 'pneumonia', 'UTI']
                    contraindications = ['cephalosporin allergy']
                    severity_score = 5
                
                elif 'amoxicillin' in antibiotic_lower:
                    pathogen_effectiveness = [
                        'Escherichia coli', 'Enterococcus faecalis', 'Streptococcus pneumoniae'
                    ]
                    infection_types = ['UTI', 'pneumonia']
                    contraindications = ['penicillin allergy']
                    severity_score = 2
                
                else:
                    # Generic broad-spectrum
                    pathogen_effectiveness = ['Escherichia coli', 'Klebsiella pneumoniae']
                    infection_types = ['UTI', 'pneumonia']
                    severity_score = 2
                
                # Create or update the record
                antibiotic_dosing, created = AntibioticDosing.objects.get_or_create(
                    antibiotic=antibiotic,
                    crcl_range=crcl_range,
                    defaults={
                        'dose': dose,
                        'route': route,
                        'interval': interval,
                        'remark': remark,
                        'pathogen_effectiveness': pathogen_effectiveness,
                        'infection_types': infection_types,
                        'contraindications': contraindications,
                        'severity_score': severity_score
                    }
                )
                
                if created:
                    imported_count += 1
                else:
                    # Update existing record with new data
                    antibiotic_dosing.dose = dose
                    antibiotic_dosing.route = route
                    antibiotic_dosing.interval = interval
                    antibiotic_dosing.remark = remark
                    antibiotic_dosing.pathogen_effectiveness = pathogen_effectiveness
                    antibiotic_dosing.infection_types = infection_types
                    antibiotic_dosing.contraindications = contraindications
                    antibiotic_dosing.severity_score = severity_score
                    antibiotic_dosing.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully imported {imported_count} antibiotic dosing records')
        )

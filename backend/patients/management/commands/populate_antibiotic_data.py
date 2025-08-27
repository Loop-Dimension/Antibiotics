from django.core.management.base import BaseCommand
from patients.models import Condition, Severity, Pathogen, SeverityPathogen, AntibioticDosing


class Command(BaseCommand):
    help = 'Populate initial antibiotic dosing data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate antibiotic data...'))

        # Create Condition
        pyelonephritis, created = Condition.objects.get_or_create(
            name='Pyelonephritis',
            defaults={
                'description': 'Kidney infection affecting the renal pelvis and parenchyma'
            }
        )
        if created:
            self.stdout.write(f'Created condition: {pyelonephritis.name}')
        else:
            self.stdout.write(f'Condition already exists: {pyelonephritis.name}')

        # Create Severity
        severity, created = Severity.objects.get_or_create(
            condition=pyelonephritis,
            level='Uncomplicated, community-acquired, mild to moderate',
            defaults={
                'severity_order': 2  # Mild=1, Moderate=2, Severe=3, etc.
            }
        )
        if created:
            self.stdout.write(f'Created severity: {severity.level}')
        else:
            self.stdout.write(f'Severity already exists: {severity.level}')

        # Create Pathogens
        pathogens_data = [
            {'name': 'E. coli', 'gram_type': 'negative', 'description': 'Escherichia coli'},
            {'name': 'K. pneumoniae', 'gram_type': 'negative', 'description': 'Klebsiella pneumoniae'},
            {'name': 'P. mirabilis', 'gram_type': 'negative', 'description': 'Proteus mirabilis'},
            {'name': 'Enterococci', 'gram_type': 'positive', 'description': 'Enterococcus species'},
            {'name': 'S. saprophyticus', 'gram_type': 'positive', 'description': 'Staphylococcus saprophyticus'},
        ]

        pathogens = []
        for pathogen_data in pathogens_data:
            pathogen, created = Pathogen.objects.get_or_create(
                name=pathogen_data['name'],
                defaults={
                    'gram_type': pathogen_data['gram_type'],
                    'description': pathogen_data['description']
                }
            )
            pathogens.append(pathogen)
            if created:
                self.stdout.write(f'Created pathogen: {pathogen.name}')
            else:
                self.stdout.write(f'Pathogen already exists: {pathogen.name}')

        # Link pathogens to severity
        for pathogen in pathogens:
            severity_pathogen, created = SeverityPathogen.objects.get_or_create(
                severity=severity,
                pathogen=pathogen,
                defaults={'prevalence': 'common'}
            )
            if created:
                self.stdout.write(f'Linked {pathogen.name} to {severity.level}')

        # Create sample antibiotic dosing guidelines with JSONField routes
        dosing_data = [
            # Ciprofloxacin - can be given both PO and IV
            {
                'antibiotic': 'Ciprofloxacin',
                'crcl_min': 60.0,
                'crcl_max': 150.0,
                'dose': '500mg PO / 400mg IV',
                'route': ['PO', 'IV'],  # Multiple routes
                'interval': 'q12h',
                'remark': 'Can be given orally or IV. Adjust dose based on route.',
                'dialysis_type': 'none',
                'patient_type': 'adult'
            },
            # Reduced dose for renal impairment
            {
                'antibiotic': 'Ciprofloxacin',
                'crcl_min': 30.0,
                'crcl_max': 59.0,
                'dose': '250mg PO / 200mg IV',
                'route': ['PO', 'IV'],  # Multiple routes
                'interval': 'q12h',
                'remark': 'Reduced dose for moderate renal impairment. Can be given orally or IV.',
                'dialysis_type': 'none',
                'patient_type': 'adult'
            },
            {
                'antibiotic': 'Levofloxacin',
                'crcl_min': 50.0,
                'crcl_max': 150.0,
                'dose': '750mg PO / 750mg IV',
                'route': ['PO', 'IV'],  # Multiple routes
                'interval': 'q24h',
                'remark': 'Alternative fluoroquinolone, available in oral and IV forms',
                'dialysis_type': 'none',
                'patient_type': 'adult'
            },
            {
                'antibiotic': 'Ceftriaxone',
                'crcl_min': 10.0,
                'crcl_max': 150.0,
                'dose': '1-2g',
                'route': ['IV'],  # IV only
                'interval': 'q24h',
                'remark': 'Broad-spectrum cephalosporin, IV only',
                'dialysis_type': 'none',
                'patient_type': 'adult'
            },
            {
                'antibiotic': 'Trimethoprim-Sulfamethoxazole',
                'crcl_min': 60.0,
                'crcl_max': 150.0,
                'dose': '160/800mg',
                'route': ['PO'],  # PO only
                'interval': 'q12h',
                'remark': 'Oral alternative if fluoroquinolone resistance',
                'dialysis_type': 'none',
                'patient_type': 'adult'
            },
            # Pediatric dosing guidelines
            {
                'antibiotic': 'Ceftriaxone',
                'crcl_min': 60.0,
                'crcl_max': 150.0,
                'dose': '50-75 mg/kg',
                'route': ['IV'],  # IV only
                'interval': 'q24h',
                'remark': 'Pediatric dose for pyelonephritis (max 2g/day)',
                'dialysis_type': 'none',
                'patient_type': 'child'
            },
            {
                'antibiotic': 'Cephalexin',
                'crcl_min': 60.0,
                'crcl_max': 150.0,
                'dose': '25-50 mg/kg',
                'route': ['PO'],  # PO only
                'interval': 'q6h',
                'remark': 'Pediatric oral option for uncomplicated UTI',
                'dialysis_type': 'none',
                'patient_type': 'child'
            },
            {
                'antibiotic': 'Trimethoprim-Sulfamethoxazole',
                'crcl_min': 60.0,
                'crcl_max': 150.0,
                'dose': '6-12 mg/kg TMP',
                'route': ['PO'],  # PO only
                'interval': 'q12h',
                'remark': 'Pediatric dose based on trimethoprim component',
                'dialysis_type': 'none',
                'patient_type': 'child'
            }
        ]

        for dosing in dosing_data:
            antibiotic_dosing, created = AntibioticDosing.objects.get_or_create(
                antibiotic=dosing['antibiotic'],
                condition=pyelonephritis,
                severity=severity,
                crcl_min=dosing['crcl_min'],
                crcl_max=dosing['crcl_max'],
                dialysis_type=dosing['dialysis_type'],
                patient_type=dosing['patient_type'],
                defaults={
                    'dose': dosing['dose'],
                    'route': dosing['route'],
                    'interval': dosing['interval'],
                    'remark': dosing['remark']
                }
            )
            
            if created:
                # Add all pathogens to this dosing guideline
                antibiotic_dosing.pathogens.set(pathogens)
                self.stdout.write(f'Created dosing guideline: {dosing["antibiotic"]} - {dosing["dose"]} {dosing["route"]} {dosing["interval"]}')
            else:
                self.stdout.write(f'Dosing guideline already exists: {dosing["antibiotic"]}')

        self.stdout.write(self.style.SUCCESS('Successfully populated antibiotic data!'))
        self.stdout.write(self.style.SUCCESS(f'Created:'))
        self.stdout.write(f'- {Condition.objects.count()} conditions')
        self.stdout.write(f'- {Severity.objects.count()} severity levels')
        self.stdout.write(f'- {Pathogen.objects.count()} pathogens')
        self.stdout.write(f'- {SeverityPathogen.objects.count()} severity-pathogen relationships')
        self.stdout.write(f'- {AntibioticDosing.objects.count()} antibiotic dosing guidelines')

from django.core.management.base import BaseCommand
from django.db import connection
from patients.models import (
    AntibioticDosing, SeverityPathogen, Severity, Condition, Pathogen,
    CultureTest, Medication, EMROrder, EMRSession, EMRSystem
)


class Command(BaseCommand):
    help = 'Flush database except users and patients'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('This will delete all data except users and patients!'))
        
        # Get counts before deletion
        self.stdout.write('Current data counts:')
        self.stdout.write(f'- AntibioticDosing: {AntibioticDosing.objects.count()}')
        self.stdout.write(f'- SeverityPathogen: {SeverityPathogen.objects.count()}')
        self.stdout.write(f'- Severity: {Severity.objects.count()}')
        self.stdout.write(f'- Condition: {Condition.objects.count()}')
        self.stdout.write(f'- Pathogen: {Pathogen.objects.count()}')
        self.stdout.write(f'- CultureTest: {CultureTest.objects.count()}')
        self.stdout.write(f'- Medication: {Medication.objects.count()}')
        self.stdout.write(f'- EMROrder: {EMROrder.objects.count()}')
        self.stdout.write(f'- EMRSession: {EMRSession.objects.count()}')
        self.stdout.write(f'- EMRSystem: {EMRSystem.objects.count()}')
        
        # Delete in correct order to avoid foreign key constraints
        self.stdout.write(self.style.SUCCESS('Starting deletion...'))
        
        # Delete antibiotic dosing data first (has FK to many tables)
        count = AntibioticDosing.objects.count()
        AntibioticDosing.objects.all().delete()
        self.stdout.write(f'Deleted {count} AntibioticDosing records')
        
        # Delete severity-pathogen relationships
        count = SeverityPathogen.objects.count()
        SeverityPathogen.objects.all().delete()
        self.stdout.write(f'Deleted {count} SeverityPathogen records')
        
        # Delete severities
        count = Severity.objects.count()
        Severity.objects.all().delete()
        self.stdout.write(f'Deleted {count} Severity records')
        
        # Delete conditions
        count = Condition.objects.count()
        Condition.objects.all().delete()
        self.stdout.write(f'Deleted {count} Condition records')
        
        # Delete pathogens
        count = Pathogen.objects.count()
        Pathogen.objects.all().delete()
        self.stdout.write(f'Deleted {count} Pathogen records')
        
        # Delete patient-related data (but keep patients themselves)
        count = CultureTest.objects.count()
        CultureTest.objects.all().delete()
        self.stdout.write(f'Deleted {count} CultureTest records')
        
        count = Medication.objects.count()
        Medication.objects.all().delete()
        self.stdout.write(f'Deleted {count} Medication records')
        
        # Delete EMR data
        count = EMROrder.objects.count()
        EMROrder.objects.all().delete()
        self.stdout.write(f'Deleted {count} EMROrder records')
        
        count = EMRSession.objects.count()
        EMRSession.objects.all().delete()
        self.stdout.write(f'Deleted {count} EMRSession records')
        
        count = EMRSystem.objects.count()
        EMRSystem.objects.all().delete()
        self.stdout.write(f'Deleted {count} EMRSystem records')
        
        # Reset auto-increment sequences for cleared tables
        with connection.cursor() as cursor:
            tables_to_reset = [
                'antibiotic_dosing',
                'severity_pathogens', 
                'severities',
                'conditions',
                'pathogens',
                'culture_tests',
                'medications',
                'patients_emrorder',
                'patients_emrsession',
                'patients_emrsystem'
            ]
            
            for table in tables_to_reset:
                try:
                    cursor.execute(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1;")
                    self.stdout.write(f'Reset sequence for {table}')
                except Exception as e:
                    self.stdout.write(f'Could not reset sequence for {table}: {e}')
        
        self.stdout.write(self.style.SUCCESS('Database flush completed!'))
        self.stdout.write(self.style.SUCCESS('Users and Patients have been preserved.'))

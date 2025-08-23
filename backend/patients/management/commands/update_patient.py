from django.core.management.base import BaseCommand
from patients.models import Patient
from decimal import Decimal


class Command(BaseCommand):
    help = 'Update sample patient with allergy information'

    def handle(self, *args, **options):
        try:
            # Get the first patient
            patient = Patient.objects.first()
            if patient:
                # Update with proper data to match the frontend
                patient.name = "Kim"
                patient.age = 65
                patient.allergies = "Penicillin" 
                patient.cockcroft_gault_crcl = Decimal('50')
                patient.body_temperature = Decimal('38.3')
                patient.wbc = Decimal('14200')
                patient.crp = Decimal('92')
                patient.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated patient {patient.patient_id}')
                )
                
                # Display updated info
                self.stdout.write(f'\nUpdated Patient Information:')
                self.stdout.write(f'Name: {patient.name}')
                self.stdout.write(f'Age: {patient.age}, Gender: {patient.get_gender_display()}')
                self.stdout.write(f'Allergies: {patient.allergies}')
                self.stdout.write(f'CrCl: {patient.cockcroft_gault_crcl} mL/min')
                self.stdout.write(f'Temperature: {patient.body_temperature}°C')
                self.stdout.write(f'WBC: {patient.wbc}')
                self.stdout.write(f'CRP: {patient.crp} mg/L')
            else:
                self.stdout.write(
                    self.style.ERROR('No patient found')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating patient: {str(e)}')
            )

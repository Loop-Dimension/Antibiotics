from rest_framework import serializers
from .models import Patient, CultureTest, Medication, AntibioticDosing, Condition


# Diagnosis-to-condition mapping (must match recommendation_engine.py)
DIAGNOSIS_MAPPING = {
    'pyelonephritis': 'Pyelonephritis',
    'acute pyelonephritis': 'Pyelonephritis',
    'acute pyelitis': 'Pyelonephritis',
    'kidney infection': 'Pyelonephritis',
    'upper uti': 'Pyelonephritis',
    'uti': 'Pyelonephritis',
    'urinary tract infection': 'Pyelonephritis',
    'urinary track infection': 'Pyelonephritis',
    'complicated urinary track infection': 'Pyelonephritis',
    'bladder infection': 'Pyelonephritis',
    'cystitis': 'Pyelonephritis',
    'pneumonia': 'Pneumonia, community-acquired',
    'community-acquired pneumonia': 'Pneumonia, community-acquired',
    'cap': 'Pneumonia, community-acquired',
    'lung infection': 'Pneumonia, community-acquired',
    'respiratory tract infection': 'Pneumonia, community-acquired',
    'lower respiratory tract infection': 'Pneumonia, community-acquired',
}


class PatientSerializer(serializers.ModelSerializer):
    bmi = serializers.ReadOnlyField()
    has_recommendations = serializers.SerializerMethodField()
    body_temperature = serializers.DecimalField(
        max_digits=4,
        decimal_places=1,
        required=False,
        help_text="Temperature in Celsius"
    )

    class Meta:
        model = Patient
        fields = '__all__'

    def get_has_recommendations(self, obj):
        patient_type = 'adult' if obj.age >= 18 else 'child'

        # Check diagnosis1 and diagnosis2
        for diag_field in [obj.diagnosis1, obj.diagnosis2]:
            diagnosis = (diag_field or '').lower().strip()
            if not diagnosis:
                continue
            for key, cname in DIAGNOSIS_MAPPING.items():
                if key in diagnosis:
                    if AntibioticDosing.objects.filter(
                        condition__name=cname,
                        patient_type=patient_type,
                    ).exists():
                        return True
                    break

        # Check pathogen-based matching (e.g. "Klebsiella pneumoniae" -> Pneumonia)
        pathogen = (obj.pathogen or '').lower().strip()
        if 'pneumoniae' in pathogen:
            if AntibioticDosing.objects.filter(
                condition__name='Pneumonia, community-acquired',
                patient_type=patient_type,
            ).exists():
                return True

        return False
    
    def validate_body_temperature(self, value):
        """Override body temperature validation to allow values below 30"""
        if value is not None:
            # Allow any reasonable temperature value (remove minimum validation)
            if value > 50:  # Keep maximum validation for safety
                raise serializers.ValidationError("Temperature cannot exceed 50°C")
        return value


class CultureTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CultureTest
        fields = '__all__'


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'

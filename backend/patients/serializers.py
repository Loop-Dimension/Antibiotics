from rest_framework import serializers
from .models import Patient, CultureTest, Medication


class PatientSerializer(serializers.ModelSerializer):
    bmi = serializers.ReadOnlyField()
    body_temperature = serializers.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        required=False,
        help_text="Temperature in Celsius"
    )
    
    class Meta:
        model = Patient
        fields = '__all__'
    
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

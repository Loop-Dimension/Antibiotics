from rest_framework import serializers
from .models import Patient, CultureTest, Medication


class PatientSerializer(serializers.ModelSerializer):
    bmi = serializers.ReadOnlyField()
    
    class Meta:
        model = Patient
        fields = '__all__'


class CultureTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CultureTest
        fields = '__all__'


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'

from rest_framework import serializers
from .models import EMRSystem, EMROrder, EMRSession

class EMRSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EMRSystem
        fields = ['id', 'name', 'base_url', 'is_active', 'created_at']
        read_only_fields = ['created_at']

class EMROrderSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = EMROrder
        fields = [
            'id', 'patient', 'patient_name', 'order_type', 
            'medication_name', 'dosage', 'frequency', 'duration',
            'instructions', 'status', 'created_by', 'created_by_name',
            'created_at', 'sent_to_emr_at', 'emr_order_id', 'emr_response'
        ]
        read_only_fields = ['created_at', 'sent_to_emr_at', 'emr_order_id', 'emr_response']

class EMROrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EMROrder
        fields = [
            'patient', 'order_type', 'medication_name', 'dosage', 
            'frequency', 'duration', 'instructions'
        ]

class EMRSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EMRSession
        fields = ['id', 'session_token', 'expires_at', 'created_at', 'is_active']
        read_only_fields = ['created_at']

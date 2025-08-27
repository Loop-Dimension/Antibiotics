from rest_framework import serializers
from .models import Condition, Severity, Pathogen, SeverityPathogen, AntibioticDosing


class PathogenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pathogen
        fields = ['id', 'name', 'gram_type', 'description']


class SeverityPathogenSerializer(serializers.ModelSerializer):
    pathogen = PathogenSerializer(read_only=True)
    
    class Meta:
        model = SeverityPathogen
        fields = ['pathogen', 'prevalence']


class SeveritySerializer(serializers.ModelSerializer):
    pathogens = SeverityPathogenSerializer(many=True, read_only=True)
    
    class Meta:
        model = Severity
        fields = ['id', 'level', 'severity_order', 'pathogens']


class ConditionSerializer(serializers.ModelSerializer):
    severities = SeveritySerializer(many=True, read_only=True)
    
    class Meta:
        model = Condition
        fields = ['id', 'name', 'description', 'severities']


class AntibioticDosingSerializer(serializers.ModelSerializer):
    condition = ConditionSerializer(read_only=True)
    severity = SeveritySerializer(read_only=True)
    pathogens = PathogenSerializer(many=True, read_only=True)
    crcl_range = serializers.SerializerMethodField()
    
    class Meta:
        model = AntibioticDosing
        fields = [
            'id', 'antibiotic', 'condition', 'severity', 'pathogens',
            'crcl_min', 'crcl_max', 'crcl_range', 'dialysis_type',
            'dose', 'route', 'interval', 'remark', 'patient_type'
        ]
    
    def get_crcl_range(self, obj):
        """Return formatted CrCl range"""
        return f"{obj.crcl_min}-{obj.crcl_max} mL/min"


class AntibioticDosingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating antibiotic dosing guidelines"""
    
    class Meta:
        model = AntibioticDosing
        fields = [
            'antibiotic', 'condition', 'severity', 'pathogens',
            'crcl_min', 'crcl_max', 'dialysis_type',
            'dose', 'route', 'interval', 'remark', 'patient_type'
        ]

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Condition, Severity, Pathogen, AntibioticDosing
from .antibiotic_serializers import (
    ConditionSerializer, SeveritySerializer, PathogenSerializer,
    AntibioticDosingSerializer, AntibioticDosingCreateSerializer
)


class ConditionViewSet(viewsets.ModelViewSet):
    """API viewset for medical conditions"""
    queryset = Condition.objects.all()
    serializer_class = ConditionSerializer
    
    def get_queryset(self):
        queryset = Condition.objects.all()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset.order_by('name')


class SeverityViewSet(viewsets.ModelViewSet):
    """API viewset for severity levels"""
    queryset = Severity.objects.all()
    serializer_class = SeveritySerializer
    
    def get_queryset(self):
        queryset = Severity.objects.all()
        condition_id = self.request.query_params.get('condition', None)
        if condition_id:
            queryset = queryset.filter(condition_id=condition_id)
        return queryset.order_by('condition', 'severity_order')


class PathogenViewSet(viewsets.ModelViewSet):
    """API viewset for pathogens"""
    queryset = Pathogen.objects.all()
    serializer_class = PathogenSerializer
    
    def get_queryset(self):
        queryset = Pathogen.objects.all()
        gram_type = self.request.query_params.get('gram_type', None)
        search = self.request.query_params.get('search', None)
        
        if gram_type:
            queryset = queryset.filter(gram_type=gram_type)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset.order_by('name')


class AntibioticDosingViewSet(viewsets.ModelViewSet):
    """API viewset for antibiotic dosing guidelines"""
    queryset = AntibioticDosing.objects.all()
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AntibioticDosingCreateSerializer
        return AntibioticDosingSerializer
    
    def get_queryset(self):
        queryset = AntibioticDosing.objects.select_related(
            'condition', 'severity'
        ).prefetch_related('pathogens')
        
        # Filter parameters
        antibiotic = self.request.query_params.get('antibiotic', None)
        condition_id = self.request.query_params.get('condition', None)
        severity_id = self.request.query_params.get('severity', None)
        patient_type = self.request.query_params.get('patient_type', None)
        route = self.request.query_params.get('route', None)
        dialysis_type = self.request.query_params.get('dialysis_type', None)
        
        if antibiotic:
            queryset = queryset.filter(antibiotic__icontains=antibiotic)
        if condition_id:
            queryset = queryset.filter(condition_id=condition_id)
        if severity_id:
            queryset = queryset.filter(severity_id=severity_id)
        if patient_type:
            queryset = queryset.filter(patient_type=patient_type)
        if route:
            queryset = queryset.filter(route=route)
        if dialysis_type:
            queryset = queryset.filter(dialysis_type=dialysis_type)
            
        return queryset.order_by('antibiotic', 'condition', 'severity__severity_order')
    
    @action(detail=False, methods=['get'])
    def for_patient(self, request):
        """Get antibiotic recommendations for a specific patient based on their CrCl and condition"""
        crcl = request.query_params.get('crcl', None)
        condition_name = request.query_params.get('condition', None)
        patient_type = request.query_params.get('patient_type', 'adult')
        dialysis_type = request.query_params.get('dialysis_type', 'none')
        
        if not crcl or not condition_name:
            return Response(
                {'error': 'crcl and condition parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            crcl = float(crcl)
        except ValueError:
            return Response(
                {'error': 'crcl must be a valid number'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find matching dosing guidelines
        queryset = AntibioticDosing.objects.filter(
            condition__name__icontains=condition_name,
            crcl_min__lte=crcl,
            crcl_max__gte=crcl,
            patient_type=patient_type,
            dialysis_type=dialysis_type
        ).select_related('condition', 'severity').prefetch_related('pathogens')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'patient_criteria': {
                'crcl': crcl,
                'condition': condition_name,
                'patient_type': patient_type,
                'dialysis_type': dialysis_type
            },
            'recommendations': serializer.data,
            'count': len(serializer.data)
        })
    
    @action(detail=False, methods=['get'])
    def antibiotics_list(self, request):
        """Get list of unique antibiotics"""
        antibiotics = AntibioticDosing.objects.values_list('antibiotic', flat=True).distinct().order_by('antibiotic')
        return Response({'antibiotics': list(antibiotics)})
    
    @action(detail=False, methods=['get'])
    def routes_list(self, request):
        """Get list of available routes"""
        routes = [choice[0] for choice in AntibioticDosing.ROUTE_CHOICES]
        return Response({'routes': routes})
    
    @action(detail=False, methods=['get'])
    def patient_types_list(self, request):
        """Get list of available patient types"""
        patient_types = [choice[0] for choice in AntibioticDosing.PATIENT_TYPE_CHOICES]
        return Response({'patient_types': patient_types})

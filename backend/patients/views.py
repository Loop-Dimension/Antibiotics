from rest_framework import viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import Patient, CultureTest, Medication, AntibioticDosing
from .serializers import PatientSerializer, CultureTestSerializer, MedicationSerializer
from .antibiotic_service import AntibioticRecommendationService


class PatientPagination(PageNumberPagination):
    page_size = 12  # Number of patients per page
    page_size_query_param = 'page_size'
    max_page_size = 50


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by('patient_id')
    serializer_class = PatientSerializer
    pagination_class = PatientPagination
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search patients by name with limit of 10 results"""
        query = request.query_params.get('q', '').strip()
        if query:
            patients = Patient.objects.filter(
                name__icontains=query
            ).order_by('name')[:10]  # Limit to 10 results
            serializer = self.get_serializer(patients, many=True)
            return Response(serializer.data)
        return Response([])
    
    @action(detail=False, methods=['get'])
    def search_by_pathogen(self, request):
        pathogen = request.query_params.get('pathogen', None)
        if pathogen:
            patients = Patient.objects.filter(pathogen__icontains=pathogen)
            serializer = self.get_serializer(patients, many=True)
            return Response(serializer.data)
        return Response({'error': 'Please provide a pathogen parameter'})
    
    @action(detail=False, methods=['get'])
    def antibiotics_usage(self, request):
        antibiotic = request.query_params.get('antibiotic', None)
        if antibiotic:
            patients = Patient.objects.filter(antibiotics__icontains=antibiotic)
            serializer = self.get_serializer(patients, many=True)
            return Response(serializer.data)
        return Response({'error': 'Please provide an antibiotic parameter'})
    
    @action(detail=True, methods=['get'])
    def lab_summary(self, request, pk=None):
        patient = self.get_object()
        lab_data = {
            'patient_id': patient.patient_id,
            'lab_results': {
                'WBC': str(patient.wbc),
                'Hemoglobin': str(patient.hb),
                'Platelet': str(patient.platelet),
                'AST': str(patient.ast),
                'ALT': str(patient.alt),
                'Creatinine': str(patient.scr),
                'CrCl': str(patient.cockcroft_gault_crcl),
                'CRP': str(patient.crp),
            },
            'bmi': patient.bmi,
            'pathogen': patient.pathogen,
            'treatment': patient.antibiotics
        }
        return Response(lab_data)
    
    @action(detail=True, methods=['get'])
    @permission_classes([AllowAny])  # Allow testing without authentication
    def antibiotic_recommendations(self, request, pk=None):
        """Get AI-powered antibiotic recommendations for a specific patient"""
        try:
            patient = self.get_object()
            
            # Get recommendations using improved service
            result = AntibioticRecommendationService.get_recommendations_for_patient(patient)
            
            # Extract data from new response format
            recommendations = result.get('recommendations', [])
            message = result.get('message', 'Recommendations generated successfully')
            status = result.get('status', 'success')
            
            response_data = {
                'patient_id': patient.patient_id,
                'patient_name': patient.name,
                'recommendations': recommendations,
                'message': message,
                'status': status,
                'patient_data': {
                    'crcl': float(patient.cockcroft_gault_crcl) if patient.cockcroft_gault_crcl else None,
                    'pathogen': patient.pathogen,
                    'diagnosis': patient.diagnosis1,
                    'allergies': patient.allergies,
                    'age': patient.age,
                    'weight': float(patient.body_weight) if patient.body_weight else None,
                    'temperature': float(patient.body_temperature) if patient.body_temperature else None,
                    'wbc': float(patient.wbc) if patient.wbc else None,
                    'crp': float(patient.crp) if patient.crp else None
                },
                'timestamp': patient.updated_at.isoformat() if hasattr(patient, 'updated_at') else None
            }
            
            # Set appropriate HTTP status based on result
            http_status = 200
            if status == 'no_match':
                http_status = 200  # Still successful, just no matches
            elif status == 'error':
                http_status = 400
            elif status == 'emergency_fallback':
                http_status = 500
                
            return Response(response_data, status=http_status)
            
        except Exception as e:
            # Handle any unexpected errors
            return Response({
                'patient_id': pk,
                'patient_name': 'Unknown',
                'recommendations': [],
                'message': f'Error retrieving recommendations: {str(e)}',
                'status': 'system_error',
                'patient_data': {},
                'timestamp': None
            }, status=500)


class CultureTestViewSet(viewsets.ModelViewSet):
    queryset = CultureTest.objects.all()
    serializer_class = CultureTestSerializer


class MedicationViewSet(viewsets.ModelViewSet):
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer

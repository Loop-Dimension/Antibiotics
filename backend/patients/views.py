from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Case, When, IntegerField, DecimalField, Count
from django.db.models.functions import Cast
from decimal import Decimal
import logging
from .models import Patient, CultureTest, Medication, AntibioticDosing
from .serializers import PatientSerializer, CultureTestSerializer, MedicationSerializer
from .antibiotic_service import AntibioticRecommendationService
from .recommendation_engine import AntibioticRecommendationEngine

logger = logging.getLogger(__name__)


class PatientPagination(PageNumberPagination):
    page_size = 12  # Number of patients per page
    page_size_query_param = 'page_size'
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'results': data
        })


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()  # Required for DRF router
    serializer_class = PatientSerializer
    pagination_class = PatientPagination
    
    def get_queryset(self):
        """Enhanced queryset with filtering, search, and sorting"""
        queryset = Patient.objects.all()
        
        # Search by name (case-insensitive)
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(patient_id__icontains=search) |
                Q(diagnosis1__icontains=search) |
                Q(diagnosis2__icontains=search)
            )
        
        # Risk level filtering
        risk_level = self.request.query_params.get('risk_level', '')
        if risk_level:
            if risk_level.lower() == 'high':
                queryset = self._filter_high_risk(queryset)
            elif risk_level.lower() == 'medium':
                queryset = self._filter_medium_risk(queryset)
            elif risk_level.lower() == 'low':
                queryset = self._filter_low_risk(queryset)
        
        # Culture status filtering
        culture_status = self.request.query_params.get('culture_status', '')
        if culture_status:
            if culture_status.lower() == 'positive':
                queryset = queryset.exclude(Q(pathogen__isnull=True) | Q(pathogen__exact='') | Q(pathogen__iexact='unknown'))
            elif culture_status.lower() == 'negative':
                queryset = queryset.filter(Q(pathogen__isnull=True) | Q(pathogen__exact='') | Q(pathogen__iexact='unknown'))
        
        # Treatment status filtering
        treatment_status = self.request.query_params.get('treatment_status', '')
        if treatment_status:
            if treatment_status.lower() == 'on_treatment':
                queryset = queryset.exclude(Q(antibiotics__isnull=True) | Q(antibiotics__exact='') | Q(antibiotics__iexact='none'))
            elif treatment_status.lower() == 'no_treatment':
                queryset = queryset.filter(Q(antibiotics__isnull=True) | Q(antibiotics__exact='') | Q(antibiotics__iexact='none'))
        
        # Patient type filtering (adult/child based on age, defaults to adult)
        patient_type = self.request.query_params.get('patient_type', 'adult')
        if patient_type == 'adult':
            queryset = queryset.filter(age__gte=18)
        elif patient_type == 'child':
            queryset = queryset.filter(age__lt=18)
        # patient_type == 'all' shows both

        # Age range filtering
        age_min = self.request.query_params.get('age_min', '')
        age_max = self.request.query_params.get('age_max', '')
        if age_min:
            try:
                queryset = queryset.filter(age__gte=int(age_min))
            except ValueError:
                pass
        if age_max:
            try:
                queryset = queryset.filter(age__lte=int(age_max))
            except ValueError:
                pass
        
        # Gender filtering
        gender = self.request.query_params.get('gender', '')
        if gender and gender.upper() in ['M', 'F', 'O']:
            queryset = queryset.filter(gender=gender.upper())
        
        # Diagnosis filtering
        diagnosis = self.request.query_params.get('diagnosis', '')
        if diagnosis:
            queryset = queryset.filter(
                Q(diagnosis1__icontains=diagnosis) | Q(diagnosis2__icontains=diagnosis)
            )
        
        # Pathogen filtering
        pathogen = self.request.query_params.get('pathogen', '')
        if pathogen:
            queryset = queryset.filter(pathogen__icontains=pathogen)
        
        # Antibiotic filtering
        antibiotic = self.request.query_params.get('antibiotic', '')
        if antibiotic:
            queryset = queryset.filter(antibiotics__icontains=antibiotic)
        
        # Allergy filtering
        allergy = self.request.query_params.get('allergy', '')
        if allergy:
            queryset = queryset.filter(allergies__icontains=allergy)
        
        # Date range filtering
        date_from = self.request.query_params.get('date_from', '')
        date_to = self.request.query_params.get('date_to', '')
        if date_from:
            try:
                queryset = queryset.filter(date_recorded__gte=date_from)
            except ValueError:
                pass
        if date_to:
            try:
                queryset = queryset.filter(date_recorded__lte=date_to)
            except ValueError:
                pass
        
        # Lab value filtering
        temp_min = self.request.query_params.get('temp_min', '')
        temp_max = self.request.query_params.get('temp_max', '')
        if temp_min:
            try:
                queryset = queryset.filter(body_temperature__gte=Decimal(temp_min))
            except (ValueError, TypeError):
                pass
        if temp_max:
            try:
                queryset = queryset.filter(body_temperature__lte=Decimal(temp_max))
            except (ValueError, TypeError):
                pass
        
        # CRP filtering
        crp_min = self.request.query_params.get('crp_min', '')
        crp_max = self.request.query_params.get('crp_max', '')
        if crp_min:
            try:
                queryset = queryset.filter(crp__gte=Decimal(crp_min))
            except (ValueError, TypeError):
                pass
        if crp_max:
            try:
                queryset = queryset.filter(crp__lte=Decimal(crp_max))
            except (ValueError, TypeError):
                pass
        
        # WBC filtering
        wbc_min = self.request.query_params.get('wbc_min', '')
        wbc_max = self.request.query_params.get('wbc_max', '')
        if wbc_min:
            try:
                queryset = queryset.filter(wbc__gte=Decimal(wbc_min))
            except (ValueError, TypeError):
                pass
        if wbc_max:
            try:
                queryset = queryset.filter(wbc__lte=Decimal(wbc_max))
            except (ValueError, TypeError):
                pass
        
        # CrCl filtering
        crcl_min = self.request.query_params.get('crcl_min', '')
        crcl_max = self.request.query_params.get('crcl_max', '')
        if crcl_min:
            try:
                queryset = queryset.filter(cockcroft_gault_crcl__gte=Decimal(crcl_min))
            except (ValueError, TypeError):
                pass
        if crcl_max:
            try:
                queryset = queryset.filter(cockcroft_gault_crcl__lte=Decimal(crcl_max))
            except (ValueError, TypeError):
                pass
        
        # Apply sorting
        ordering = self.request.query_params.get('ordering', '-date_recorded')
        valid_orderings = [
            'patient_id', '-patient_id',
            'name', '-name',
            'age', '-age',
            'date_recorded', '-date_recorded',
            'body_temperature', '-body_temperature',
            'wbc', '-wbc',
            'crp', '-crp',
            'cockcroft_gault_crcl', '-cockcroft_gault_crcl',
            'diagnosis1', '-diagnosis1'
        ]
        
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)
        else:
            # Default ordering
            queryset = queryset.order_by('-date_recorded', '-created_at')
        
        return queryset
    
    def _filter_high_risk(self, queryset):
        """Filter for high-risk patients based on clinical criteria"""
        high_risk_conditions = Q()
        
        # Age > 80
        high_risk_conditions |= Q(age__gt=80)
        
        # High CRP (> 100)
        high_risk_conditions |= Q(crp__gt=100)
        
        # High WBC (> 15000)
        high_risk_conditions |= Q(wbc__gt=15000)
        
        # Low CrCl (< 30)
        high_risk_conditions |= Q(cockcroft_gault_crcl__lt=30)
        
        # High fever (> 38.5)
        high_risk_conditions |= Q(body_temperature__gt=38.5)
        
        # Multiple conditions for very elderly with infection markers
        high_risk_conditions |= Q(age__gt=65, crp__gt=50, body_temperature__gt=38.0)
        
        return queryset.filter(high_risk_conditions)
    
    def _filter_medium_risk(self, queryset):
        """Filter for medium-risk patients"""
        medium_risk_conditions = Q()
        
        # Age 50-80 with some risk factors
        medium_risk_conditions |= Q(age__range=(50, 80), crp__gt=20)
        medium_risk_conditions |= Q(age__range=(50, 80), wbc__gt=10000)
        medium_risk_conditions |= Q(age__range=(50, 80), body_temperature__gt=37.5)
        
        # Moderate CrCl impairment
        medium_risk_conditions |= Q(cockcroft_gault_crcl__range=(30, 60))
        
        # Moderate inflammatory markers
        medium_risk_conditions |= Q(crp__range=(50, 100))
        medium_risk_conditions |= Q(wbc__range=(10000, 15000))
        
        # Exclude high-risk patients
        high_risk_queryset = self._filter_high_risk(Patient.objects.all())
        high_risk_ids = high_risk_queryset.values_list('patient_id', flat=True)
        
        return queryset.filter(medium_risk_conditions).exclude(patient_id__in=high_risk_ids)
    
    def _filter_low_risk(self, queryset):
        """Filter for low-risk patients"""
        # Exclude high and medium risk patients
        high_risk_queryset = self._filter_high_risk(Patient.objects.all())
        medium_risk_queryset = self._filter_medium_risk(Patient.objects.all())
        
        high_risk_ids = high_risk_queryset.values_list('patient_id', flat=True)
        medium_risk_ids = medium_risk_queryset.values_list('patient_id', flat=True)
        
        return queryset.exclude(patient_id__in=high_risk_ids).exclude(patient_id__in=medium_risk_ids)
    
    def list(self, request, *args, **kwargs):
        """Enhanced list endpoint with filtering and search"""
        try:
            # Get filtered queryset
            queryset = self.filter_queryset(self.get_queryset())
            
            # Apply pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                response_data = self.get_paginated_response(serializer.data)
                
                # Add summary statistics
                total_queryset = self.get_queryset()  # Get base queryset for stats
                stats = {
                    'total_patients': total_queryset.count(),
                    'filtered_patients': queryset.count(),
                    'high_risk_count': self._filter_high_risk(total_queryset).count(),
                    'culture_positive_count': total_queryset.exclude(
                        Q(pathogen__isnull=True) | Q(pathogen__exact='') | Q(pathogen__iexact='unknown')
                    ).count(),
                    'on_treatment_count': total_queryset.exclude(
                        Q(antibiotics__isnull=True) | Q(antibiotics__exact='') | Q(antibiotics__iexact='none')
                    ).count(),
                }
                
                # Add stats to response
                response_data.data['stats'] = stats
                return response_data
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error in patient list endpoint: {str(e)}")
            return Response({
                'error': 'An error occurred while fetching patients',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Enhanced search patients with autocomplete support"""
        query = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 10))
        
        if not query:
            return Response([])
        
        if len(query) < 2:
            return Response({'message': 'Query too short, minimum 2 characters'})
        
        try:
            # Search across multiple fields
            patients = Patient.objects.filter(
                Q(name__icontains=query) |
                Q(patient_id__icontains=query) |
                Q(diagnosis1__icontains=query) |
                Q(diagnosis2__icontains=query) |
                Q(pathogen__icontains=query)
            ).order_by('name')[:limit]
            
            serializer = self.get_serializer(patients, many=True)
            return Response({
                'query': query,
                'count': patients.count(),
                'results': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error in patient search: {str(e)}")
            return Response({
                'error': 'Search failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def filter_options(self, request):
        """Get available filter options for frontend dropdowns"""
        try:
            # Get unique values for dropdowns
            diagnoses = list(Patient.objects.exclude(
                Q(diagnosis1__isnull=True) | Q(diagnosis1__exact='')
            ).values_list('diagnosis1', flat=True).distinct())
            
            pathogens = list(Patient.objects.exclude(
                Q(pathogen__isnull=True) | Q(pathogen__exact='') | Q(pathogen__iexact='unknown')
            ).values_list('pathogen', flat=True).distinct())
            
            antibiotics = list(Patient.objects.exclude(
                Q(antibiotics__isnull=True) | Q(antibiotics__exact='') | Q(antibiotics__iexact='none')
            ).values_list('antibiotics', flat=True).distinct())
            
            allergies = list(Patient.objects.exclude(
                Q(allergies__isnull=True) | Q(allergies__exact='') | Q(allergies__iexact='none')
            ).values_list('allergies', flat=True).distinct())
            
            return Response({
                'diagnoses': sorted(diagnoses),
                'pathogens': sorted(pathogens),
                'antibiotics': sorted(antibiotics),
                'allergies': sorted(allergies),
                'risk_levels': ['low', 'medium', 'high'],
                'culture_statuses': ['positive', 'negative'],
                'treatment_statuses': ['on_treatment', 'no_treatment'],
                'patient_types': [{'value': 'adult', 'label': 'Adult'}, {'value': 'child', 'label': 'Child'}, {'value': 'all', 'label': 'All'}],
                'genders': [{'value': 'M', 'label': 'Male'}, {'value': 'F', 'label': 'Female'}, {'value': 'O', 'label': 'Other'}],
                'ordering_options': [
                    {'value': '-date_recorded', 'label': 'Most Recent'},
                    {'value': 'date_recorded', 'label': 'Oldest First'},
                    {'value': 'name', 'label': 'Name A-Z'},
                    {'value': '-name', 'label': 'Name Z-A'},
                    {'value': '-age', 'label': 'Age (Oldest First)'},
                    {'value': 'age', 'label': 'Age (Youngest First)'},
                    {'value': '-body_temperature', 'label': 'Temperature (High to Low)'},
                    {'value': '-crp', 'label': 'CRP (High to Low)'},
                    {'value': '-wbc', 'label': 'WBC (High to Low)'},
                    {'value': 'cockcroft_gault_crcl', 'label': 'CrCl (Low to High)'}
                ]
            })
            
        except Exception as e:
            logger.error(f"Error getting filter options: {str(e)}")
            return Response({
                'error': 'Failed to get filter options',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive patient statistics"""
        try:
            total_patients = Patient.objects.count()
            
            # Risk level statistics
            high_risk_count = self._filter_high_risk(Patient.objects.all()).count()
            medium_risk_count = self._filter_medium_risk(Patient.objects.all()).count()
            low_risk_count = self._filter_low_risk(Patient.objects.all()).count()
            
            # Culture statistics
            culture_positive = Patient.objects.exclude(
                Q(pathogen__isnull=True) | Q(pathogen__exact='') | Q(pathogen__iexact='unknown')
            ).count()
            
            # Treatment statistics
            on_treatment = Patient.objects.exclude(
                Q(antibiotics__isnull=True) | Q(antibiotics__exact='') | Q(antibiotics__iexact='none')
            ).count()
            
            # Age group statistics
            age_groups = {
                'pediatric': Patient.objects.filter(age__lt=18).count(),
                'adult': Patient.objects.filter(age__range=(18, 64)).count(),
                'elderly': Patient.objects.filter(age__gte=65).count()
            }
            
            # Gender statistics
            gender_stats = {
                'male': Patient.objects.filter(gender='M').count(),
                'female': Patient.objects.filter(gender='F').count(),
                'other': Patient.objects.filter(gender='O').count(),
                'unknown': Patient.objects.filter(Q(gender__isnull=True) | Q(gender__exact='')).count()
            }
            
            # Top diagnoses
            top_diagnoses = list(Patient.objects.exclude(
                Q(diagnosis1__isnull=True) | Q(diagnosis1__exact='')
            ).values('diagnosis1').annotate(
                count=Count('diagnosis1')
            ).order_by('-count')[:10])
            
            # Top pathogens
            top_pathogens = list(Patient.objects.exclude(
                Q(pathogen__isnull=True) | Q(pathogen__exact='') | Q(pathogen__iexact='unknown')
            ).values('pathogen').annotate(
                count=Count('pathogen')
            ).order_by('-count')[:10])
            
            return Response({
                'total_patients': total_patients,
                'risk_levels': {
                    'high': high_risk_count,
                    'medium': medium_risk_count,
                    'low': low_risk_count
                },
                'culture_status': {
                    'positive': culture_positive,
                    'negative': total_patients - culture_positive
                },
                'treatment_status': {
                    'on_treatment': on_treatment,
                    'no_treatment': total_patients - on_treatment
                },
                'age_groups': age_groups,
                'gender_distribution': gender_stats,
                'top_diagnoses': top_diagnoses,
                'top_pathogens': top_pathogens
            })
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return Response({
                'error': 'Failed to get statistics',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
    


    @permission_classes([AllowAny])
    @action(detail=True, methods=['get'])
    def clinical_recommendations(self, request, pk=None):
        """Get clinical decision support recommendations using the new engine"""
        try:
            patient = self.get_object()
            logger.info(f"Getting clinical recommendations for patient {patient.patient_id}")
            
            # Initialize the recommendation engine
            engine = AntibioticRecommendationEngine()
            
            # Get recommendations
            result = engine.get_recommendations(patient)
            logger.info(f"Engine returned result: {result.get('success', False)}")
            
            # Check if successful
            if not result.get('success', False):
                error_msg = result.get('error', 'Unknown error during recommendation generation')
                logger.error(f"Recommendation engine failed for patient {patient.patient_id}: {error_msg}")
                
                return Response({
                    'patient_id': patient.patient_id,
                    'patient_name': patient.name,
                    'success': False,
                    'error': 'Failed to generate clinical recommendations',
                    'details': error_msg,
                    'status': 'error',
                    'recommendations': [],
                    'total_matches': 0,
                    'message': 'Unable to generate recommendations due to system error'
                }, status=500)
            
            # Format response for the frontend
            recommendations = result.get('recommendations', [])
            response_data = {
                'patient_id': patient.patient_id,
                'patient_name': patient.name,
                'success': True,
                'total_matches': result.get('total_matches', 0),
                'recommendations': recommendations,
                'patient_summary': result.get('patient_summary', {}),
                'filter_steps': result.get('filter_steps', []),
                'status': 'success',
                'message': f'Generated {len(recommendations)} clinical recommendations',
                'timestamp': patient.updated_at.isoformat() if hasattr(patient, 'updated_at') else None
            }
            
            # Add patient context for reference
            response_data['patient_context'] = {
                'age': patient.age,
                'diagnosis': patient.diagnosis1,
                'pathogen': patient.pathogen,
                'allergies': patient.allergies,
                'current_antibiotic': patient.antibiotics,
                'crcl': float(patient.cockcroft_gault_crcl) if patient.cockcroft_gault_crcl else None,
                'weight': float(patient.body_weight) if patient.body_weight else None,
                'temperature': float(patient.body_temperature) if patient.body_temperature else None,
                'wbc': float(patient.wbc) if patient.wbc else None,
                'crp': float(patient.crp) if patient.crp else None
            }
            
            # Log successful response
            logger.info(f"Successfully generated {len(recommendations)} recommendations for patient {patient.patient_id}")
            
            return Response(response_data, status=200)
            
        except Patient.DoesNotExist:
            logger.error(f"Patient {pk} not found")
            return Response({
                'patient_id': pk,
                'error': 'Patient not found',
                'details': f'No patient exists with ID {pk}',
                'status': 'not_found',
                'success': False
            }, status=404)
            
        except Exception as e:
            logger.error(f"Unexpected error in clinical recommendations for patient {pk}: {str(e)}", exc_info=True)
            return Response({
                'patient_id': pk,
                'error': 'System error while generating recommendations',
                'details': f'An unexpected error occurred: {str(e)}',
                'status': 'system_error',
                'success': False,
                'recommendations': [],
                'total_matches': 0
            }, status=500)

    @action(detail=True, methods=['post'])
    def save_recommendations(self, request, pk=None):
        """Save selected and modified recommendations for a patient"""
        try:
            patient = self.get_object()
            recommendations = request.data.get('recommendations', [])
            
            if not recommendations:
                return Response({
                    'error': 'No recommendations provided',
                    'success': False
                }, status=400)
            
            # Here you can save the recommendations to a new model or update patient record
            # For now, we'll just log them and return success
            logger.info(f"Saving {len(recommendations)} recommendations for patient {patient.patient_id}")
            
            for rec in recommendations:
                logger.info(f"Recommendation: {rec.get('antibiotic_name', rec.get('antibiotic'))} - "
                           f"Dose: {rec.get('dose')} - "
                           f"Interval: {rec.get('interval')} - "
                           f"Duration: {rec.get('duration')}")
            
            return Response({
                'success': True,
                'message': f'Successfully saved {len(recommendations)} recommendations',
                'patient_id': patient.patient_id,
                'recommendations_count': len(recommendations)
            }, status=200)
            
        except Patient.DoesNotExist:
            logger.error(f"Patient {pk} not found")
            return Response({
                'error': 'Patient not found',
                'success': False
            }, status=404)
            
        except Exception as e:
            logger.error(f"Error saving recommendations for patient {pk}: {str(e)}", exc_info=True)
            return Response({
                'error': 'Failed to save recommendations',
                'details': str(e),
                'success': False
            }, status=500)

    @permission_classes([AllowAny])
    @action(detail=False, methods=['get'])
    def prescription_analysis(self, request):
        """
        Analyze all patients comparing their actual prescriptions vs AI recommendations.
        Returns match statistics and detailed comparison for each patient.
        """
        try:
            patients = Patient.objects.all()
            engine = AntibioticRecommendationEngine()
            
            analysis_results = []
            total_patients = 0
            exact_matches = 0
            partial_matches = 0
            no_matches = 0
            no_recommendations = 0
            
            for patient in patients:
                total_patients += 1
                actual_prescription = patient.antibiotics or ""
                
                # Get AI recommendations
                result = engine.get_recommendations(patient)
                ai_recommendations = result.get('recommendations', [])
                
                # Extract antibiotic names from recommendations
                recommended_antibiotics = []
                for rec in ai_recommendations:
                    antibiotic = rec.get('antibiotic', '')
                    if antibiotic:
                        recommended_antibiotics.append(antibiotic)
                
                # Normalize prescriptions for comparison
                actual_normalized = self._normalize_antibiotic(actual_prescription)
                
                # Check match status
                match_status = 'no_recommendation'
                matched_recommendation = None
                similarity_score = 0
                
                if recommended_antibiotics:
                    for rec_antibiotic in recommended_antibiotics:
                        rec_normalized = self._normalize_antibiotic(rec_antibiotic)
                        score = self._calculate_similarity(actual_normalized, rec_normalized)
                        
                        if score > similarity_score:
                            similarity_score = score
                            matched_recommendation = rec_antibiotic
                    
                    if similarity_score >= 0.8:
                        match_status = 'exact_match'
                        exact_matches += 1
                    elif similarity_score >= 0.4:
                        match_status = 'partial_match'
                        partial_matches += 1
                    else:
                        match_status = 'no_match'
                        no_matches += 1
                else:
                    no_recommendations += 1
                
                analysis_results.append({
                    'patient_id': patient.patient_id,
                    'case_no': patient.case_no,
                    'diagnosis': patient.diagnosis1,
                    'crcl': float(patient.cockcroft_gault_crcl) if patient.cockcroft_gault_crcl else None,
                    'pathogen': patient.pathogen,
                    'actual_prescription': actual_prescription,
                    'ai_recommendations': recommended_antibiotics[:5],  # Top 5
                    'best_match': matched_recommendation,
                    'similarity_score': round(similarity_score * 100, 1),
                    'match_status': match_status
                })
            
            # Calculate statistics
            matched_count = exact_matches + partial_matches
            match_rate = (matched_count / total_patients * 100) if total_patients > 0 else 0
            
            return Response({
                'success': True,
                'summary': {
                    'total_patients': total_patients,
                    'exact_matches': exact_matches,
                    'partial_matches': partial_matches,
                    'no_matches': no_matches,
                    'no_recommendations': no_recommendations,
                    'match_rate': round(match_rate, 1),
                    'exact_match_rate': round((exact_matches / total_patients * 100) if total_patients > 0 else 0, 1),
                },
                'analysis': analysis_results
            })
            
        except Exception as e:
            logger.error(f"Error in prescription analysis: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _normalize_antibiotic(self, antibiotic_str):
        """Normalize antibiotic name for comparison"""
        if not antibiotic_str:
            return ""
        
        # Convert to lowercase and remove common prefixes
        normalized = antibiotic_str.lower().strip()
        normalized = normalized.replace('iv ', '').replace('po ', '').replace('oral ', '')
        
        # Extract just the antibiotic name (before dose)
        import re
        # Match antibiotic name (letters, /, -)
        match = re.match(r'^([a-z/\-]+)', normalized)
        if match:
            return match.group(1)
        return normalized
    
    def _calculate_similarity(self, str1, str2):
        """Calculate similarity between two strings using various methods"""
        if not str1 or not str2:
            return 0
        
        # Exact match
        if str1 == str2:
            return 1.0
        
        # One contains the other
        if str1 in str2 or str2 in str1:
            return 0.9
        
        # Check for common antibiotic base name
        common_bases = [
            'ceftriaxone', 'cefepime', 'ceftazidime', 'cefotaxime', 'cefuroxime', 'cefpodoxime',
            'piperacillin', 'tazobactam', 'amoxicillin', 'clavulanate',
            'levofloxacin', 'ciprofloxacin', 'moxifloxacin',
            'ertapenem', 'meropenem', 'imipenem',
            'vancomycin', 'teicoplanin'
        ]
        
        for base in common_bases:
            if base in str1 and base in str2:
                return 0.85
        
        # Levenshtein-like simple similarity
        longer = str1 if len(str1) > len(str2) else str2
        shorter = str2 if len(str1) > len(str2) else str1
        
        if len(longer) == 0:
            return 1.0
        
        # Count matching characters
        matches = sum(1 for c in shorter if c in longer)
        return matches / len(longer)


class CultureTestViewSet(viewsets.ModelViewSet):
    queryset = CultureTest.objects.all()
    serializer_class = CultureTestSerializer


class MedicationViewSet(viewsets.ModelViewSet):
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer

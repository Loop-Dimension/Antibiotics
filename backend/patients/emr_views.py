from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from .models import EMRSystem, EMROrder, EMRSession, Patient
from .emr_serializers import (
    EMRSystemSerializer, 
    EMROrderSerializer, 
    EMROrderCreateSerializer,
    EMRSessionSerializer
)


class EMRViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]  # Remove authentication requirement

    @action(detail=False, methods=['post'])
    def authenticate(self, request):
        """Authenticate with EMR system"""
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Username and password required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mock EMR authentication for now
        return Response({
            'success': True,
            'message': 'EMR authentication successful',
            'emr_system': 'Mock EMR System',
            'expires_at': timezone.now().isoformat()
        })

    @action(detail=False, methods=['get'])
    def session_status(self, request):
        """Check EMR session status"""
        # Return mock session status without authentication
        return Response({
            'authenticated': False,
            'emr_system': None,
            'expires_at': None,
            'message': 'EMR session not active'
        })

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Logout from EMR"""
        return Response({
            'success': True,
            'message': 'EMR logout successful'
        })

    @action(detail=False, methods=['post'])
    def open_patient_record(self, request):
        """Open patient record in EMR"""
        patient_id = request.data.get('patient_id')
        
        if not patient_id:
            return Response(
                {'error': 'Patient ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mock patient record opening
        return Response({
            'success': True,
            'message': f'Opening patient {patient_id} in EMR',
            'url': f'http://mock-emr.com/patient/{patient_id}',
            'emr_system': 'Mock EMR System'
        })


class EMROrderViewSet(viewsets.ModelViewSet):
    queryset = EMROrder.objects.all()
    serializer_class = EMROrderSerializer
    permission_classes = [AllowAny]  # Remove authentication requirement

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EMROrderCreateSerializer
        return EMROrderSerializer

    @action(detail=False, methods=['post'])
    def create_medication_order(self, request):
        """Create a medication order"""
        try:
            patient_id = request.data.get('patient_id')
            medication_name = request.data.get('medication_name')
            dosage = request.data.get('dosage')
            frequency = request.data.get('frequency')
            duration = request.data.get('duration')
            instructions = request.data.get('instructions', '')

            if not all([patient_id, medication_name, dosage, frequency]):
                return Response(
                    {'error': 'Patient ID, medication name, dosage, and frequency are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            patient = Patient.objects.get(patient_id=patient_id)
            
            # Create mock order without authentication
            order = EMROrder.objects.create(
                patient=patient,
                order_type='medication',
                medication_name=medication_name,
                dosage=dosage,
                frequency=frequency,
                duration=duration,
                instructions=instructions,
                created_by_id=1,  # Use default user ID
                status='pending'
            )

            serializer = EMROrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def send_to_emr(self, request, pk=None):
        """Send order to EMR system"""
        try:
            order = self.get_object()
            
            # Mock sending to EMR
            order.status = 'sent'
            order.sent_to_emr_at = timezone.now()
            order.emr_order_id = f'EMR_{order.id}_{timezone.now().strftime("%Y%m%d%H%M%S")}'
            order.emr_response = {'status': 'sent', 'confirmation': 'MOCK123456'}
            order.save()

            return Response({
                'success': True,
                'message': 'Order sent to EMR successfully',
                'confirmation_number': order.emr_order_id,
                'emr_response': order.emr_response
            })

        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class EMRSystemViewSet(viewsets.ModelViewSet):
    queryset = EMRSystem.objects.all()
    serializer_class = EMRSystemSerializer
    permission_classes = [AllowAny]  # Remove authentication requirement

    @action(detail=False, methods=['post'])
    def bulk_send_orders(self, request):
        """Send multiple orders to EMR"""
        order_ids = request.data.get('order_ids', [])
        
        if not order_ids:
            return Response(
                {'error': 'No order IDs provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        for order_id in order_ids:
            try:
                order = EMROrder.objects.get(id=order_id)
                # Mock sending to EMR
                order.status = 'sent'
                order.sent_to_emr_at = timezone.now()
                order.emr_order_id = f'EMR_{order.id}_{timezone.now().strftime("%Y%m%d%H%M%S")}'
                order.save()
                
                results.append({
                    'order_id': order_id,
                    'success': True,
                    'confirmation_number': order.emr_order_id
                })
            except EMROrder.DoesNotExist:
                results.append({
                    'order_id': order_id,
                    'success': False,
                    'error': 'Order not found'
                })

        return Response({
            'results': results,
            'total_processed': len(order_ids),
            'successful': len([r for r in results if r['success']])
        })

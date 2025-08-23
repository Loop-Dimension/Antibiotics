import requests
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import EMRSystem, EMROrder, EMRSession

class EMRService:
    @staticmethod
    def get_active_emr_system():
        """Get the active EMR system"""
        try:
            return EMRSystem.objects.filter(is_active=True).first()
        except EMRSystem.DoesNotExist:
            return None

    @staticmethod
    def authenticate_emr_user(user, username, password):
        """Authenticate user with EMR system and create session"""
        emr_system = EMRService.get_active_emr_system()
        
        if not emr_system:
            return {'success': False, 'error': 'No active EMR system configured'}

        # Mock EMR authentication - replace with actual EMR API call
        try:
            # In a real implementation, this would call the actual EMR authentication API
            # auth_response = requests.post(f"{emr_system.base_url}/api/auth/login", {
            #     'username': username,
            #     'password': password,
            #     'api_key': emr_system.api_key
            # })
            
            # Mock successful authentication
            session_token = f"emr_session_{user.id}_{timezone.now().timestamp()}"
            expires_at = timezone.now() + timedelta(hours=8)
            
            # Create or update EMR session
            session, created = EMRSession.objects.update_or_create(
                user=user,
                defaults={
                    'session_token': session_token,
                    'expires_at': expires_at,
                    'is_active': True
                }
            )
            
            return {
                'success': True,
                'session_token': session_token,
                'expires_at': expires_at.isoformat(),
                'emr_system': emr_system.name
            }
            
        except Exception as e:
            return {'success': False, 'error': f'EMR authentication failed: {str(e)}'}

    @staticmethod
    def send_order_to_emr(order_id):
        """Send order to EMR system"""
        try:
            order = EMROrder.objects.get(id=order_id)
            emr_system = EMRService.get_active_emr_system()
            
            if not emr_system:
                return {'success': False, 'error': 'No active EMR system'}

            # Check if user has active EMR session
            try:
                session = EMRSession.objects.get(
                    user=order.created_by,
                    is_active=True,
                    expires_at__gt=timezone.now()
                )
            except EMRSession.DoesNotExist:
                return {'success': False, 'error': 'EMR session expired. Please authenticate again.'}

            # Prepare order data for EMR
            order_data = {
                'patient_id': order.patient.patient_id,
                'patient_name': order.patient.name,
                'order_type': order.order_type,
                'medication': {
                    'name': order.medication_name,
                    'dosage': order.dosage,
                    'frequency': order.frequency,
                    'duration': order.duration
                },
                'instructions': order.instructions,
                'prescriber': order.created_by.get_full_name(),
                'timestamp': order.created_at.isoformat()
            }

            # Mock EMR API call - replace with actual EMR API
            # In a real implementation:
            # response = requests.post(
            #     f"{emr_system.base_url}/api/orders",
            #     headers={
            #         'Authorization': f'Bearer {session.session_token}',
            #         'Content-Type': 'application/json'
            #     },
            #     json=order_data
            # )

            # Mock successful response
            mock_response = {
                'emr_order_id': f'EMR_{order.id}_{timezone.now().timestamp()}',
                'status': 'received',
                'timestamp': timezone.now().isoformat(),
                'confirmation_number': f'CONF_{order.id}'
            }

            # Update order status
            order.status = 'sent'
            order.sent_to_emr_at = timezone.now()
            order.emr_order_id = mock_response['emr_order_id']
            order.emr_response = mock_response
            order.save()

            return {
                'success': True,
                'emr_order_id': mock_response['emr_order_id'],
                'confirmation_number': mock_response['confirmation_number']
            }

        except EMROrder.DoesNotExist:
            return {'success': False, 'error': 'Order not found'}
        except Exception as e:
            return {'success': False, 'error': f'Failed to send order: {str(e)}'}

    @staticmethod
    def open_emr_patient_record(patient_id, user):
        """Generate URL to open patient record in EMR"""
        emr_system = EMRService.get_active_emr_system()
        
        if not emr_system:
            return {'success': False, 'error': 'No active EMR system'}

        # Check EMR session
        try:
            session = EMRSession.objects.get(
                user=user,
                is_active=True,
                expires_at__gt=timezone.now()
            )
        except EMRSession.DoesNotExist:
            return {'success': False, 'error': 'EMR session expired'}

        # Generate EMR URL (mock implementation)
        emr_url = f"{emr_system.base_url}/patient/{patient_id}?session={session.session_token}"
        
        return {
            'success': True,
            'url': emr_url,
            'emr_system': emr_system.name
        }

    @staticmethod
    def get_user_emr_session(user):
        """Get user's active EMR session"""
        try:
            session = EMRSession.objects.get(
                user=user,
                is_active=True,
                expires_at__gt=timezone.now()
            )
            return {
                'authenticated': True,
                'expires_at': session.expires_at.isoformat(),
                'emr_system': EMRService.get_active_emr_system().name if EMRService.get_active_emr_system() else 'Unknown'
            }
        except EMRSession.DoesNotExist:
            return {'authenticated': False}

    @staticmethod
    def logout_emr(user):
        """Logout user from EMR"""
        EMRSession.objects.filter(user=user, is_active=True).update(is_active=False)
        return {'success': True}

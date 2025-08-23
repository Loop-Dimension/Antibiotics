from django.db import models
from django.contrib.auth.models import User
from .models import Patient

class EMRSystem(models.Model):
    name = models.CharField(max_length=100)
    base_url = models.URLField()
    api_key = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class EMROrder(models.Model):
    ORDER_TYPES = [
        ('medication', 'Medication'),
        ('lab', 'Laboratory'),
        ('imaging', 'Imaging'),
        ('consult', 'Consultation'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent to EMR'),
        ('acknowledged', 'Acknowledged by EMR'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='emr_orders')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES)
    medication_name = models.CharField(max_length=200, blank=True)
    dosage = models.CharField(max_length=100, blank=True)
    frequency = models.CharField(max_length=100, blank=True)
    duration = models.CharField(max_length=100, blank=True)
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_to_emr_at = models.DateTimeField(null=True, blank=True)
    emr_order_id = models.CharField(max_length=100, blank=True)
    emr_response = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_type} for {self.patient.name} - {self.status}"

class EMRSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_token = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"EMR Session for {self.user.username}"

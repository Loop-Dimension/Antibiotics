from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from decimal import Decimal


class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    # Basic patient information
    patient_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, default="Patient", blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_recorded = models.DateField()
    age = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(150)])
    
    # Physical measurements
    body_weight = models.DecimalField(max_digits=6, decimal_places=2, help_text="Weight in kg (BW)")
    height = models.DecimalField(max_digits=6, decimal_places=2, help_text="Height in cm")
    
    # Lab Test Results
    wbc = models.DecimalField(max_digits=10, decimal_places=2, help_text="White Blood Cell count")
    hb = models.DecimalField(max_digits=5, decimal_places=2, help_text="Hemoglobin level (Hb)")
    platelet = models.DecimalField(max_digits=10, decimal_places=0, help_text="Platelet count (PLT)")
    ast = models.DecimalField(max_digits=6, decimal_places=2, help_text="Aspartate Aminotransferase (IU/L)")
    alt = models.DecimalField(max_digits=6, decimal_places=2, help_text="Alanine Aminotransferase (IU/L)")
    scr = models.DecimalField(max_digits=5, decimal_places=2, help_text="Serum Creatinine (mg/dL)")
    cockcroft_gault_crcl = models.DecimalField(max_digits=12, decimal_places=8, help_text="Cockcroft-Gault Creatinine Clearance")
    crp = models.DecimalField(max_digits=8, decimal_places=2, help_text="C-reactive Protein (mg/L)")
    
    # Diagnoses
    diagnosis1 = models.CharField(max_length=255, help_text="Primary diagnosis")
    diagnosis2 = models.CharField(max_length=255, blank=True, null=True, help_text="Secondary diagnosis")
    
    # Culture and pathogen information
    pathogen = models.CharField(max_length=500, help_text="Identified pathogen")
    sample_type = models.CharField(max_length=100, help_text="Sample type (e.g., urine, blood, sputum)")
    
    # Current medications and antibiotics
    antibiotics = models.CharField(max_length=500, help_text="Current antibiotic treatment")
    
    # Additional fields for compatibility
    allergies = models.CharField(max_length=500, default="None", help_text="Patient allergies")
    body_temperature = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, help_text="Temperature in Celsius")
    current_medications = models.TextField(blank=True, null=True, help_text="List of current medications")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patients'
        ordering = ['-date_recorded', '-created_at']
    
    def __str__(self):
        return f"Patient {self.patient_id} - {self.get_gender_display()}, Age {self.age} - {self.diagnosis1}"
    
    @property
    def bmi(self):
        """Calculate BMI from height and weight"""
        if self.height and self.body_weight:
            height_m = self.height / 100  # Convert cm to meters
            return round(self.body_weight / (height_m ** 2), 2)
        return None


class CultureTest(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='culture_tests')
    test_date = models.DateField()
    sample_type = models.CharField(max_length=100)
    pathogen = models.CharField(max_length=255)
    sensitivity_results = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'culture_tests'
        
    def __str__(self):
        return f"{self.patient.patient_id} - {self.pathogen} ({self.test_date})"


class Medication(models.Model):
    ROUTE_CHOICES = [
        ('PO', 'Oral'),
        ('IV', 'Intravenous'),
        ('IM', 'Intramuscular'),
        ('SC', 'Subcutaneous'),
        ('TOP', 'Topical'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medications')
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    route = models.CharField(max_length=10, choices=ROUTE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_antibiotic = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'medications'
        
    def __str__(self):
        return f"{self.medication_name} - {self.dosage} {self.frequency}"


# EMR Integration Models
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


class AntibioticDosing(models.Model):
    antibiotic = models.CharField(max_length=100)
    crcl_range = models.CharField(max_length=50)  # Increased from 20 to 50
    dose = models.CharField(max_length=200, blank=True)  # Increased to handle longer doses
    route = models.CharField(max_length=10, blank=True)  # PO, IV
    interval = models.CharField(max_length=50, blank=True)  # Increased from 20 to 50
    remark = models.TextField(blank=True)
    
    # Additional fields for better matching
    pathogen_effectiveness = models.JSONField(default=list, blank=True)  # List of pathogens this antibiotic is effective against
    infection_types = models.JSONField(default=list, blank=True)  # UTI, pneumonia, etc.
    contraindications = models.JSONField(default=list, blank=True)  # Allergies or conditions
    severity_score = models.IntegerField(default=1)  # 1-5, for ranking recommendations
    
    class Meta:
        unique_together = ['antibiotic', 'crcl_range']
    
    def __str__(self):
        return f"{self.antibiotic} - CrCl: {self.crcl_range}"

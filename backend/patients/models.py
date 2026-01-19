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
    
    ADMISSION_CHOICES = [
        (0, 'Outpatient'),
        (1, 'Inpatient'),
    ]
    
    # Essential patient information - REQUIRED
    patient_id = models.AutoField(primary_key=True)
    case_no = models.IntegerField(blank=True, null=True, help_text="Case number from CSV")
    name = models.CharField(max_length=255, help_text="Patient name")
    date_recorded = models.DateField(help_text="Date when patient data was recorded")
    
    # Demographics - Age required, Gender optional (sometimes unknown)
    age = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(150)], help_text="Patient age")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True, help_text="Patient gender")
    admission = models.IntegerField(choices=ADMISSION_CHOICES, default=1, help_text="Admission type: 0=Outpatient, 1=Inpatient")
    
    # Physical measurements - Weight required for dosing, Height optional
    body_weight = models.DecimalField(max_digits=6, decimal_places=2, help_text="Weight in kg (required for antibiotic dosing)")
    height = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Height in cm (optional)")
    
    # Essential clinical data - Required for antibiotic decisions
    diagnosis1 = models.CharField(max_length=255, help_text="Primary diagnosis (required)")
    body_temperature = models.DecimalField(max_digits=4, decimal_places=1, validators=[MinValueValidator(30), MaxValueValidator(50)], blank=True, null=True, help_text="Temperature in Celsius")
    
    # Essential lab values - Required for antibiotic selection and dosing
    scr = models.DecimalField(max_digits=5, decimal_places=2, help_text="Serum Creatinine (mg/dL) - required for dosing")
    cockcroft_gault_crcl = models.DecimalField(max_digits=12, decimal_places=2, help_text="Creatinine Clearance (mL/min) - required for dosing")
    
    # Important lab values - Should be available but may be optional
    wbc = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="White Blood Cell count")
    crp = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text="C-reactive Protein (mg/L)")
    
    # Additional lab values - Optional but useful
    hb = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text="Hemoglobin level (g/dL)")
    platelet = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, help_text="Platelet count")
    ast = models.DecimalField(max_digits=6, decimal_places=1, blank=True, null=True, help_text="AST (IU/L)")
    alt = models.DecimalField(max_digits=6, decimal_places=1, blank=True, null=True, help_text="ALT (IU/L)")
    
    # Clinical information - Important for antibiotic selection
    pathogen = models.CharField(max_length=500, blank=True, default="Unknown", help_text="Identified pathogen (use 'Unknown' if not identified)")
    antibiogram = models.TextField(blank=True, null=True, help_text="Antibiogram/sensitivity test results")
    sample_type = models.CharField(max_length=100, blank=True, default="Not specified", help_text="Sample type (blood, urine, sputum, etc.)")
    
    # Current treatment - Important for recommendations
    antibiotics = models.CharField(max_length=500, blank=True, default="None", help_text="Primary antibiotic treatment")
    antibiotics2 = models.TextField(blank=True, null=True, help_text="Secondary/alternative antibiotic recommendations")
    allergies = models.CharField(max_length=500, blank=True, default="None", help_text="Patient allergies")
    
    # Secondary information - Optional
    diagnosis2 = models.CharField(max_length=255, blank=True, null=True, help_text="Secondary diagnosis")
    current_medications = models.TextField(blank=True, null=True, help_text="Other current medications")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patients'
        ordering = ['-date_recorded', '-created_at']
    
    def __str__(self):
        return f"Patient {self.patient_id} - {self.name}, Age {self.age} - {self.diagnosis1}"
    
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


# New models for dynamic antibiotic dosing system
class Condition(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Condition name (e.g., Pyelonephritis)")
    description = models.TextField(blank=True, help_text="Additional description of the condition")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'conditions'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Severity(models.Model):
    condition = models.ForeignKey(Condition, on_delete=models.CASCADE, related_name='severities')
    level = models.CharField(max_length=200, help_text="Severity description (e.g., 'Uncomplicated, community-acquired, mild to moderate')")
    severity_order = models.PositiveIntegerField(default=1, help_text="Order for severity ranking (1=mild, 5=severe)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'severities'
        unique_together = ['condition', 'level']
        ordering = ['condition', 'severity_order']
    
    def __str__(self):
        return f"{self.condition.name} - {self.level}"


class Pathogen(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Pathogen name (e.g., E. coli)")
    gram_type = models.CharField(max_length=20, choices=[
        ('positive', 'Gram Positive'),
        ('negative', 'Gram Negative'),
        ('other', 'Other')
    ], blank=True, help_text="Gram staining classification")
    description = models.TextField(blank=True, help_text="Additional pathogen information")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'pathogens'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class SeverityPathogen(models.Model):
    """Many-to-many relationship between severity levels and pathogens"""
    severity = models.ForeignKey(Severity, on_delete=models.CASCADE, related_name='pathogens')
    pathogen = models.ForeignKey(Pathogen, on_delete=models.CASCADE, related_name='severities')
    prevalence = models.CharField(max_length=20, choices=[
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare')
    ], default='common', help_text="Prevalence of this pathogen in this severity")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'severity_pathogens'
        unique_together = ['severity', 'pathogen']
    
    def __str__(self):
        return f"{self.severity} - {self.pathogen.name}"


class AntibioticDosing(models.Model):
    DIALYSIS_CHOICES = [
        ('none', 'None'),
        ('hd', 'Hemodialysis'),
        ('pd', 'Peritoneal Dialysis'),
        ('crrt', 'CRRT'),
        ('ecmo', 'ECMO'),
    ]
    
    ROUTE_CHOICES = [
        ('PO', 'Oral'),
        ('IV', 'Intravenous'),
        ('IM', 'Intramuscular'),
        ('SC', 'Subcutaneous'),
    ]
    
    PATIENT_TYPE_CHOICES = [
        ('adult', 'Adult'),
        ('child', 'Child'),
    ]
    
    antibiotic = models.CharField(max_length=100, help_text="Antibiotic name")
    condition = models.ForeignKey(Condition, on_delete=models.CASCADE, related_name='dosing_guidelines')
    severity = models.ForeignKey(Severity, on_delete=models.CASCADE, related_name='dosing_guidelines')
    pathogens = models.ManyToManyField(Pathogen, related_name='dosing_guidelines', help_text="Target pathogens")
    
    # Creatinine Clearance range
    crcl_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Minimum CrCl (mL/min)")
    crcl_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Maximum CrCl (mL/min)")
    
    # Dialysis type
    dialysis_type = models.CharField(max_length=10, choices=DIALYSIS_CHOICES, default='none')
    
    # Dosing information
    dose = models.CharField(max_length=200, help_text="Dose (e.g., '500mg', '1-2g')")
    route = models.JSONField(default=list, help_text="Administration routes (e.g., ['PO', 'IV'])")
    interval = models.CharField(max_length=50, help_text="Dosing interval (e.g., 'q12h', 'q8h')")
    duration = models.CharField(max_length=50, blank=True, help_text="Treatment duration (e.g., '7d', '10-14d')")
    
    # Additional information
    remark = models.TextField(blank=True, help_text="Additional dosing remarks or considerations")
    patient_type = models.CharField(max_length=20, choices=PATIENT_TYPE_CHOICES, default='adult')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'antibiotic_dosing'
        # Remove the unique constraint to allow more flexible dosing guidelines
        # unique_together = ['antibiotic', 'condition', 'severity', 'crcl_min', 'crcl_max', 'dialysis_type', 'patient_type', 'dose', 'interval']
        ordering = ['antibiotic', 'condition', 'severity__severity_order']
    
    def __str__(self):
        return f"{self.antibiotic} - {self.condition.name} ({self.severity.level}) - CrCl: {self.crcl_min}-{self.crcl_max}"

from django.contrib import admin
from .models import (
    Patient, CultureTest, Medication, EMRSystem, EMROrder, 
    EMRSession, AntibioticDosing, Condition, Severity, Pathogen, SeverityPathogen
)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = [
        'patient_id', 'name', 'date_recorded', 'age', 'gender', 'body_weight', 
        'diagnosis1', 'pathogen', 'antibiotics'
    ]
    list_filter = ['gender', 'date_recorded', 'pathogen']
    search_fields = ['patient_id', 'name', 'diagnosis1', 'diagnosis2', 'pathogen']
    ordering = ['-date_recorded']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'date_recorded', 'age', 'gender')
        }),
        ('Physical Measurements', {
            'fields': ('body_weight', 'height', 'body_temperature')
        }),
        ('Diagnoses', {
            'fields': ('diagnosis1', 'diagnosis2')
        }),
        ('Lab Results', {
            'fields': (
                ('wbc', 'hb', 'platelet'),
                ('ast', 'alt', 'scr'),
                ('cockcroft_gault_crcl', 'crp')
            )
        }),
        ('Culture & Treatment', {
            'fields': ('pathogen', 'sample_type', 'antibiotics', 'current_medications')
        }),
        ('Additional Information', {
            'fields': ('allergies',),
            'classes': ('collapse',)
        })
    )


@admin.register(CultureTest)
class CultureTestAdmin(admin.ModelAdmin):
    list_display = ['patient', 'test_date', 'sample_type', 'pathogen']
    list_filter = ['test_date', 'sample_type', 'pathogen']
    search_fields = ['patient__patient_id', 'pathogen']


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ['patient', 'medication_name', 'dosage', 'frequency', 'route', 'is_antibiotic', 'start_date']
    list_filter = ['route', 'is_antibiotic', 'start_date']
    search_fields = ['patient__patient_id', 'medication_name']


@admin.register(EMRSystem)
class EMRSystemAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_url', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'base_url']
    
    fieldsets = (
        ('System Information', {
            'fields': ('name', 'base_url', 'is_active')
        }),
        ('Authentication', {
            'fields': ('api_key',),
            'classes': ('collapse',)
        })
    )


@admin.register(EMROrder)
class EMROrderAdmin(admin.ModelAdmin):
    list_display = ['patient', 'order_type', 'medication_name', 'status', 'created_by', 'created_at']
    list_filter = ['order_type', 'status', 'created_at']
    search_fields = ['patient__patient_id', 'patient__name', 'medication_name']
    readonly_fields = ['emr_order_id', 'emr_response', 'sent_to_emr_at']
    
    fieldsets = (
        ('Order Details', {
            'fields': ('patient', 'order_type', 'created_by')
        }),
        ('Medication Information', {
            'fields': ('medication_name', 'dosage', 'frequency', 'duration', 'instructions'),
            'classes': ('collapse',)
        }),
        ('Status & EMR Integration', {
            'fields': ('status', 'emr_order_id', 'emr_response', 'sent_to_emr_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(EMRSession)
class EMRSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_active', 'expires_at', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['session_token', 'created_at']


@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Severity)
class SeverityAdmin(admin.ModelAdmin):
    list_display = ['condition', 'level', 'severity_order', 'created_at']
    list_filter = ['condition', 'severity_order']
    search_fields = ['level', 'condition__name']
    ordering = ['condition', 'severity_order']


@admin.register(Pathogen)
class PathogenAdmin(admin.ModelAdmin):
    list_display = ['name', 'gram_type', 'created_at']
    list_filter = ['gram_type', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(SeverityPathogen)
class SeverityPathogenAdmin(admin.ModelAdmin):
    list_display = ['severity', 'pathogen', 'prevalence', 'created_at']
    list_filter = ['prevalence', 'pathogen__gram_type', 'severity__condition']
    search_fields = ['severity__level', 'pathogen__name']
    ordering = ['severity', 'pathogen']


@admin.register(AntibioticDosing)
class AntibioticDosingAdmin(admin.ModelAdmin):
    list_display = ['antibiotic', 'condition', 'severity', 'crcl_range_display', 'dose', 'route_display', 'interval', 'duration', 'dialysis_type', 'patient_type']
    list_filter = ['patient_type', 'dialysis_type', 'condition', 'severity__severity_order']
    search_fields = ['antibiotic', 'dose', 'condition__name']
    filter_horizontal = ['pathogens']
    
    def crcl_range_display(self, obj):
        return f"{obj.crcl_min}-{obj.crcl_max}"
    crcl_range_display.short_description = 'CrCl Range'
    
    def route_display(self, obj):
        if isinstance(obj.route, list):
            return ', '.join(obj.route)
        return str(obj.route)
    route_display.short_description = 'Routes'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('antibiotic', 'condition', 'severity', 'patient_type')
        }),
        ('Creatinine Clearance & Dialysis', {
            'fields': ('crcl_min', 'crcl_max', 'dialysis_type')
        }),
        ('Dosing Information', {
            'fields': ('dose', 'route', 'interval', 'duration')
        }),
        ('Target Pathogens', {
            'fields': ('pathogens',)
        }),
        ('Additional Notes', {
            'fields': ('remark',),
            'classes': ('collapse',)
        })
    )

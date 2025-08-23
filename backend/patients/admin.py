from django.contrib import admin
from .models import (
    Patient, CultureTest, Medication, EMRSystem, EMROrder, 
    EMRSession, AntibioticDosing
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


@admin.register(AntibioticDosing)
class AntibioticDosingAdmin(admin.ModelAdmin):
    list_display = ['antibiotic', 'crcl_range', 'dose', 'route', 'interval', 'severity_score']
    list_filter = ['route', 'severity_score', 'crcl_range']
    search_fields = ['antibiotic', 'dose']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('antibiotic', 'crcl_range', 'dose', 'route', 'interval')
        }),
        ('Clinical Information', {
            'fields': ('pathogen_effectiveness', 'infection_types', 'contraindications', 'severity_score')
        }),
        ('Additional Notes', {
            'fields': ('remark',),
            'classes': ('collapse',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Make pathogen_effectiveness, infection_types, contraindications read-only if they contain data
        readonly = []
        if obj and (obj.pathogen_effectiveness or obj.infection_types or obj.contraindications):
            readonly.extend(['pathogen_effectiveness', 'infection_types', 'contraindications'])
        return readonly

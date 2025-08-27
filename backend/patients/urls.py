from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .emr_views import EMRViewSet, EMROrderViewSet, EMRSystemViewSet
from .antibiotic_views import (
    ConditionViewSet, SeverityViewSet, PathogenViewSet, AntibioticDosingViewSet
)

router = DefaultRouter()
router.register(r'patients', views.PatientViewSet)
router.register(r'culture-tests', views.CultureTestViewSet)
router.register(r'medications', views.MedicationViewSet)
router.register(r'emr', EMRViewSet, basename='emr')
router.register(r'emr-orders', EMROrderViewSet, basename='emr-orders')
router.register(r'emr-systems', EMRSystemViewSet, basename='emr-systems')

# New antibiotic dosing endpoints
router.register(r'conditions', ConditionViewSet, basename='conditions')
router.register(r'severities', SeverityViewSet, basename='severities')
router.register(r'pathogens', PathogenViewSet, basename='pathogens')
router.register(r'antibiotic-dosing', AntibioticDosingViewSet, basename='antibiotic-dosing')

urlpatterns = [
    path('api/', include(router.urls)),
]

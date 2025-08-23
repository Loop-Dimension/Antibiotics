from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .emr_views import EMRViewSet, EMROrderViewSet, EMRSystemViewSet

router = DefaultRouter()
router.register(r'patients', views.PatientViewSet)
router.register(r'culture-tests', views.CultureTestViewSet)
router.register(r'medications', views.MedicationViewSet)
router.register(r'emr', EMRViewSet, basename='emr')
router.register(r'emr-orders', EMROrderViewSet, basename='emr-orders')
router.register(r'emr-systems', EMRSystemViewSet, basename='emr-systems')

urlpatterns = [
    path('api/', include(router.urls)),
]

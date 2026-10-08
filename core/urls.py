from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="patient_list", permanent=False)),
    path("patients/", views.patient_list, name="patient_list"),
    path("patients/add/", views.patient_create, name="patient_create"),
    path("patients/<int:pk>/", views.patient_detail, name="patient_detail"),
    path("patients/<int:pk>/visits/add/", views.visit_create, name="visit_create"),
]
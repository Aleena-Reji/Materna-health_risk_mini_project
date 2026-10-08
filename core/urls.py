from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("patients/", views.patient_list, name="patient_list"),
    path("patients/add/", views.patient_create, name="patient_create"),
    path("patients/<int:pk>/", views.patient_detail, name="patient_detail"),
    path("patients/<int:pk>/edit/", views.patient_update, name="patient_update"),
    path("patients/<int:pk>/delete/", views.patient_delete, name="patient_delete"),
    path("patients/<int:pk>/visits/add/", views.visit_create, name="visit_create"),
    path("visits/<int:pk>/", views.visit_detail, name="visit_detail"),
    path("visits/<int:pk>/edit/", views.visit_update, name="visit_update"),
    path("visits/<int:pk>/delete/", views.visit_delete, name="visit_delete"),
]
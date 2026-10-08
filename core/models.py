from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Health worker account. Extends Django's built-in user."""
    DESIGNATION_CHOICES = [
        ("doctor", "Doctor"),
        ("nurse", "Nurse"),
        ("midwife", "Midwife"),
        ("senior_health_worker", "Senior Health Worker"),
    ]
    designation = models.CharField(
        max_length=30, choices=DESIGNATION_CHOICES, default="nurse"
    )


class Patient(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="patients"
    )  # health worker who registered the patient
    patient_id = models.CharField(
        "Patient ID", max_length=30, unique=True,
        help_text="Hospital or clinic registration number",
    )
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(null=True, blank=True)
    contact = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient_id} - {self.name}"


class Visit(models.Model):
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="visits"
    )
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="recorded_visits",
    )  # health worker who recorded this visit
    visit_date = models.DateField()

    # clinical inputs (to be added once the model features are final)
    symptoms = models.TextField(blank=True)

    # merged from Prediction
    predicted_result = models.CharField(max_length=100, blank=True)
    prediction_confidence = models.FloatField(null=True, blank=True)
    model_version = models.CharField(max_length=50, blank=True)

    # merged from Recommendation
    recommendation_text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.name} - {self.visit_date}"
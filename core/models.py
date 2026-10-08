from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Login account. Extends Django's built-in user."""
    ROLE_CHOICES = [
        ("doctor", "Doctor"),
        ("admin", "Admin"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="doctor")


class Patient(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="patients"
    )  # who registered/manages this patient
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(null=True, blank=True)
    contact = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Visit(models.Model):
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="visits"
    )
    visit_date = models.DateField()

    # clinical inputs (replace with your real fields)
    symptoms = models.TextField(blank=True)
    # blood_pressure = models.FloatField(null=True, blank=True)
    # glucose = models.FloatField(null=True, blank=True)

    # merged from Prediction
    predicted_result = models.CharField(max_length=100, blank=True)
    prediction_confidence = models.FloatField(null=True, blank=True)
    model_version = models.CharField(max_length=50, blank=True)

    # merged from Recommendation
    recommendation_text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.name} - {self.visit_date}"
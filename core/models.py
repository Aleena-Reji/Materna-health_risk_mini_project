from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


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
    age = models.PositiveIntegerField()
    contact = models.CharField(max_length=20, blank=True)

    # medical history (model inputs)
    previous_complications = models.BooleanField(
        "Previous pregnancy complications", default=False
    )
    preexisting_diabetes = models.BooleanField(
        "Pre-existing diabetes", default=False
    )

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

    # clinical readings (model inputs)
    systolic_bp = models.PositiveIntegerField(
        "Systolic BP (mmHg)", validators=[MinValueValidator(60), MaxValueValidator(250)]
    )
    diastolic_bp = models.PositiveIntegerField(
        "Diastolic BP (mmHg)", validators=[MinValueValidator(30), MaxValueValidator(150)]
    )
    blood_sugar = models.FloatField(
        "Blood sugar (mmol/L)", validators=[MinValueValidator(1), MaxValueValidator(30)]
    )
    body_temp = models.FloatField(
        "Body temperature (°F)", validators=[MinValueValidator(90), MaxValueValidator(110)]
    )
    bmi = models.FloatField(
        "BMI", validators=[MinValueValidator(10), MaxValueValidator(60)]
    )
    heart_rate = models.PositiveIntegerField(
        "Heart rate (bpm)", validators=[MinValueValidator(30), MaxValueValidator(200)]
    )
    gestational_diabetes = models.BooleanField("Gestational diabetes", default=False)
    mental_health = models.BooleanField(
        "Mental health concerns", default=False
    )

    symptoms = models.TextField(blank=True)

    # model output
    predicted_result = models.CharField(max_length=100, blank=True)
    prediction_confidence = models.FloatField(null=True, blank=True)
    model_version = models.CharField(max_length=50, blank=True)
    feature_importance = models.JSONField(null=True, blank=True)

    # rule-based recommendation
    recommendation_text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.name} - {self.visit_date}"

    @property
    def risk_class(self):
        text = (self.predicted_result or "").lower()
        if "high" in text:
            return "high"
        if "mid" in text or "medium" in text or "moderate" in text:
            return "mid"
        if "low" in text:
            return "low"
        return ""

    @property
    def risk_score(self):
        return {"low": 1, "mid": 2, "high": 3}.get(self.risk_class)

    @property
    def top_feature(self):
        if self.feature_importance:
            return max(self.feature_importance, key=self.feature_importance.get)
        return None
import json

import joblib
import pandas as pd
from django.conf import settings

MODEL_PATH = settings.BASE_DIR / "risk_model.joblib"
ORDER_PATH = settings.BASE_DIR / "feature_order.json"
MODEL_VERSION = "v1"

    # Assumption: class 0 = low risk, class 1 = high risk
LABELS = {0: "High Risk", 1: "Low Risk"}

_model = None
_order = None


def _load():
    global _model, _order
    if _model is None:
        _model = joblib.load(MODEL_PATH)
        with open(ORDER_PATH) as f:
            _order = json.load(f)
    return _model, _order


def build_recommendation(label, visit):
    patient = visit.patient
    if label == "High Risk":
        lines = [
            "High risk: refer the patient to a doctor or obstetric specialist for review.",
            "Arrange close monitoring and a follow-up visit within one week.",
        ]
    else:
        lines = [
            "Low risk: continue routine antenatal care.",
            "Advise a balanced diet, rest, hydration and regular scheduled checkups.",
        ]

    if visit.systolic_bp >= 140 or visit.diastolic_bp >= 90:
        lines.append("Blood pressure is raised (140/90 mmHg or above): recheck, and ask about headache, blurred vision or swelling.")
    if visit.blood_sugar >= 7.8:
        lines.append("Blood sugar is high: review diet and glucose monitoring.")
    if visit.body_temp >= 100.4:
        lines.append("Temperature suggests a fever: look for signs of infection.")
    if visit.heart_rate > 100:
        lines.append("Heart rate is above 100 bpm: recheck after rest.")
    if visit.bmi >= 30:
        lines.append("BMI is in the obese range: nutrition and weight-gain counselling.")
    elif visit.bmi < 18.5:
        lines.append("BMI is low: nutrition support and weight-gain monitoring.")
    if visit.gestational_diabetes or patient.preexisting_diabetes:
        lines.append("Diabetes noted: keep glucose monitoring regular.")
    if visit.mental_health:
        lines.append("Mental health concern noted: offer counselling or a support referral.")
    if patient.previous_complications:
        lines.append("Previous complications: plan delivery at a facility that can manage them.")
    return "\n".join(lines)


def predict_visit(visit):
    """Fill the prediction fields on an (unsaved or saved) Visit."""
    model, order = _load()
    patient = visit.patient

    values = {
        "Age": patient.age,
        "Systolic BP": visit.systolic_bp,
        "Diastolic": visit.diastolic_bp,
        "BS": visit.blood_sugar,
        "Body Temp": visit.body_temp,
        "BMI": visit.bmi,
        "Previous Complications": int(patient.previous_complications),
        "Preexisting Diabetes": int(patient.preexisting_diabetes),
        "Gestational Diabetes": int(visit.gestational_diabetes),
        "Mental Health": int(visit.mental_health),
        "Heart Rate": visit.heart_rate,
    }
    frame = pd.DataFrame([values], columns=order)

    probabilities = model.predict_proba(frame)[0]
    best = int(probabilities.argmax())
    label = LABELS[int(model.classes_[best])]

    visit.predicted_result = label
    visit.prediction_confidence = round(float(probabilities[best]), 3)
    visit.model_version = MODEL_VERSION
    visit.feature_importance = None
    visit.recommendation_text = build_recommendation(label, visit)
    return label
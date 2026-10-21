import json
import joblib
import pandas as pd
from django.conf import settings

BASE_DIR = settings.BASE_DIR
MODEL = joblib.load(BASE_DIR / "maternal_health_random_forest.pkl")
FEATURES = list(MODEL.feature_names_in_)
HIGH_IDX = list(MODEL.classes_).index("High")

# Global importance (kept for the report / optional insights page)
try:
    with open(BASE_DIR / "feature_importance.json") as f:
        GLOBAL_IMPORTANCE = json.load(f)
except FileNotFoundError:
    GLOBAL_IMPORTANCE = None

# A typical Low-risk patient (median values from the training data)
REFERENCE = {"Age": 25, "Systolic BP": 120, "Diastolic": 70, "BS": 6.5, "Body Temp": 98,
             "BMI": 22, "Heart Rate": 72, "Previous Complications": 0,
             "Preexisting Diabetes": 0, "Gestational Diabetes": 0, "Mental Health": 0}

LABELS = {"Age": ("Age", "years"), "Systolic BP": ("Systolic BP", "mmHg"),
          "Diastolic": ("Diastolic BP", "mmHg"), "BS": ("Blood sugar", "mmol/L"),
          "Body Temp": ("Body temperature", "°F"), "BMI": ("BMI", ""),
          "Heart Rate": ("Heart rate", "bpm"),
          "Previous Complications": ("Previous complications", ""),
          "Preexisting Diabetes": ("Pre-existing diabetes", ""),
          "Gestational Diabetes": ("Gestational diabetes", ""),
          "Mental Health": ("Mental health concern", "")}

BINARY_KEYS = {"Previous Complications", "Preexisting Diabetes",
               "Gestational Diabetes", "Mental Health"}


def explain(inputs):
    """Readings that raised this patient's risk, strongest first."""
    row = pd.DataFrame([inputs], columns=FEATURES)
    base = MODEL.predict_proba(row)[0][HIGH_IDX]
    items = []
    for key in FEATURES:
        alt = row.copy()
        alt[key] = REFERENCE[key]
        effect = base - MODEL.predict_proba(alt)[0][HIGH_IDX]
        if effect >= 0.02:
            name, unit = LABELS[key]
            v = inputs[key]
            shown = "Yes" if key in BINARY_KEYS else (f"{float(v):g} {unit}").strip()
            items.append({"name": name, "value": shown, "effect": round(float(effect), 3)})
    items.sort(key=lambda x: -x["effect"])
    return items[:6]


def build_recommendation(label, visit):
    patient = visit.patient
    notes = []
    if visit.systolic_bp >= 140 or visit.diastolic_bp >= 90:
        notes.append("Blood pressure is high; recheck and monitor for signs of preeclampsia.")
    if float(visit.blood_sugar) >= 7.8:
        notes.append("Blood sugar is raised; arrange glucose monitoring and dietary advice.")
    if float(visit.body_temp) >= 100.4:
        notes.append("Temperature suggests fever; look for signs of infection.")
    if visit.heart_rate > 100:
        notes.append("Heart rate is above 100 bpm; review and recheck.")
    bmi = float(visit.bmi)
    if bmi >= 30:
        notes.append("BMI is in the obese range; nutrition and activity guidance advised.")
    elif bmi < 18.5:
        notes.append("BMI is low; nutritional support advised.")
    if patient.preexisting_diabetes or visit.gestational_diabetes:
        notes.append("Diabetes is present; needs regular glucose follow-up.")
    if visit.mental_health:
        notes.append("Mental health concern noted; offer counselling or screening.")
    if patient.previous_complications:
        notes.append("Previous complications recorded; closer antenatal monitoring advised.")

    if label.startswith("High"):
        head = "High risk: refer to a doctor or hospital for closer monitoring."
    else:
        head = "Low risk: continue routine antenatal care and regular check-ups."
    return head + ("\n" + "\n".join("- " + n for n in notes) if notes else "")


def predict_visit(visit):
    patient = visit.patient
    inputs = {
        "Age": patient.age,
        "Systolic BP": visit.systolic_bp,
        "Diastolic": visit.diastolic_bp,
        "BS": float(visit.blood_sugar),
        "Body Temp": float(visit.body_temp),
        "BMI": float(visit.bmi),
        "Previous Complications": int(patient.previous_complications),
        "Preexisting Diabetes": int(patient.preexisting_diabetes),
        "Gestational Diabetes": int(visit.gestational_diabetes),
        "Mental Health": int(visit.mental_health),
        "Heart Rate": visit.heart_rate,
    }
    df = pd.DataFrame([inputs], columns=FEATURES)

    proba = MODEL.predict_proba(df)[0]
    idx = int(proba.argmax())
    label = f"{MODEL.classes_[idx]} Risk"        # "High Risk" or "Low Risk"

    visit.predicted_result = label
    visit.prediction_confidence = round(float(proba[idx]), 3)
    visit.model_version = "random_forest_v2"
    visit.feature_importance = explain(inputs)
    visit.recommendation_text = build_recommendation(label, visit)
    visit.save()
    return label
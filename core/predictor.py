import json
import joblib
import pandas as pd
from django.conf import settings

BASE_DIR = settings.BASE_DIR
MODEL = joblib.load(BASE_DIR / "maternal_health_random_forest.pkl")
FEATURES = list(MODEL.feature_names_in_)

try:
    with open(BASE_DIR / "feature_importance.json") as f:
        GLOBAL_IMPORTANCE = json.load(f)
except FileNotFoundError:
    GLOBAL_IMPORTANCE = None

BINARY_KEYS = {"Previous Complications", "Preexisting Diabetes",
               "Gestational Diabetes", "Mental Health"}


def explain(inputs):
    """Top 5 model factors, each shown with this patient's own value."""
    if not GLOBAL_IMPORTANCE:
        return None
    rows = []
    for f in GLOBAL_IMPORTANCE["features"][:5]:
        v = inputs.get(f["key"])
        if f["key"] in BINARY_KEYS:
            v = "Yes" if v else "No"
        else:
            v = float(v)
        rows.append({"name": f["name"], "percent": f["percent"], "value": v})
    return rows


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
from django import forms
from .models import Patient, Visit


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ["name", "age", "contact"]
        widgets = {
            "gender": forms.Select(
                choices=[("", "Select"), ("Female", "Female"), ("Male", "Male"), ("Other", "Other")]
            ),
        }


class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ["visit_date", "symptoms"]
        widgets = {
            "visit_date": forms.DateInput(attrs={"type": "date"}),
            "symptoms": forms.Textarea(attrs={"rows": 4}),
        }
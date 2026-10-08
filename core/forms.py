import re

from django import forms
from django.utils import timezone

from .models import Patient, Visit


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ["name", "age", "contact"]
        widgets = {
            "age": forms.NumberInput(attrs={"min": 10, "max": 70}),
            "contact": forms.TextInput(attrs={"placeholder": "e.g. 9876543210"}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 2:
            raise forms.ValidationError("Please enter the patient's full name.")
        return name

    def clean_age(self):
        age = self.cleaned_data.get("age")
        if age is not None and not (10 <= age <= 70):
            raise forms.ValidationError("Age must be between 10 and 70.")
        return age

    def clean_contact(self):
        contact = self.cleaned_data.get("contact", "").strip()
        if contact:
            digits = re.sub(r"[\s-]", "", contact)
            if not re.fullmatch(r"\+?\d{10,15}", digits):
                raise forms.ValidationError(
                    "Enter a valid phone number (10 to 15 digits)."
                )
            return digits
        return contact


class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ["visit_date", "symptoms"]
        widgets = {
            "visit_date": forms.DateInput(attrs={"type": "date"}),
            "symptoms": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_visit_date(self):
        visit_date = self.cleaned_data["visit_date"]
        if visit_date > timezone.localdate():
            raise forms.ValidationError("Visit date cannot be in the future.")
        return visit_date
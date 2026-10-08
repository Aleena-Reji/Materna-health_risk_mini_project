from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import PatientForm, VisitForm
from .models import Patient


def patients_for(user):
    """Admins/superusers see everyone; doctors see only their own patients."""
    if user.is_superuser or user.role == "admin":
        return Patient.objects.all()
    return Patient.objects.filter(user=user)


@login_required
def patient_list(request):
    patients = patients_for(request.user).order_by("-created_at")
    return render(request, "core/patient_list.html", {"patients": patients})


@login_required
def patient_create(request):
    if request.method == "POST":
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.user = request.user
            patient.save()
            return redirect("patient_list")
    else:
        form = PatientForm()
    return render(request, "core/patient_form.html", {"form": form})


@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(patients_for(request.user), pk=pk)
    visits = patient.visits.order_by("-visit_date")
    return render(request, "core/patient_detail.html", {"patient": patient, "visits": visits})


@login_required
def visit_create(request, pk):
    patient = get_object_or_404(patients_for(request.user), pk=pk)
    if request.method == "POST":
        form = VisitForm(request.POST)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.patient = patient
            visit.save()
            return redirect("patient_detail", pk=patient.pk)
    else:
        form = VisitForm(initial={"visit_date": timezone.localdate()})
    return render(request, "core/visit_form.html", {"form": form, "patient": patient})
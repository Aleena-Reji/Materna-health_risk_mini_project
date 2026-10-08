from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from .models import Patient, Visit
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import PatientForm, VisitForm


def patients_for(user):
    """Admins/superusers see everyone; doctors see only their own patients."""
    if user.is_superuser or user.role == "admin":
        return Patient.objects.all()
    return Patient.objects.filter(user=user)


@login_required
def patient_list(request):
    patients = patients_for(request.user).order_by("-created_at")
    q = request.GET.get("q", "").strip()
    if q:
        patients = patients.filter(Q(name__icontains=q) | Q(contact__icontains=q))
    return render(request, "core/patient_list.html", {"patients": patients, "q": q})


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
    return render(request, "core/patient_form.html", {"form": form, "title": "Add Patient"})


@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(patients_for(request.user), pk=pk)
    visits = patient.visits.order_by("-visit_date")
    return render(request, "core/patient_detail.html", {"patient": patient, "visits": visits})


@login_required
def patient_update(request, pk):
    patient = get_object_or_404(patients_for(request.user), pk=pk)
    if request.method == "POST":
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            return redirect("patient_detail", pk=patient.pk)
    else:
        form = PatientForm(instance=patient)
    return render(request, "core/patient_form.html", {"form": form, "title": "Edit Patient"})


@login_required
def patient_delete(request, pk):
    patient = get_object_or_404(patients_for(request.user), pk=pk)
    if request.method == "POST":
        patient.delete()
        return redirect("patient_list")
    return render(request, "core/patient_confirm_delete.html", {"patient": patient})


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
    return render(request, "core/visit_form.html", {"form": form, "patient": patient, "title": "Add Visit"})


@login_required
def dashboard(request):
    patients = patients_for(request.user)
    visits = Visit.objects.filter(patient__in=patients)
    today = timezone.localdate()
    context = {
        "patient_count": patients.count(),
        "visit_count": visits.count(),
        "month_visits": visits.filter(
            visit_date__year=today.year, visit_date__month=today.month
        ).count(),
        "recent_visits": visits.select_related("patient").order_by(
            "-visit_date", "-created_at"
        )[:5],
        "risk_summary": visits.exclude(predicted_result="")
        .values("predicted_result")
        .annotate(total=Count("id"))
        .order_by("-total"),
    }
    return render(request, "core/dashboard.html", context)
def visits_for(user):
    """Visits that belong to patients this user is allowed to see."""
    return Visit.objects.filter(patient__in=patients_for(user)).select_related("patient")

@login_required
def visit_detail(request, pk):
    visit = get_object_or_404(visits_for(request.user), pk=pk)
    return render(request, "core/visit_detail.html", {"visit": visit})


@login_required
def visit_update(request, pk):
    visit = get_object_or_404(visits_for(request.user), pk=pk)
    if request.method == "POST":
        form = VisitForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            return redirect("visit_detail", pk=visit.pk)
    else:
        form = VisitForm(instance=visit)
    return render(
        request,
        "core/visit_form.html",
        {"form": form, "patient": visit.patient, "title": "Edit Visit"},
    )


@login_required
def visit_delete(request, pk):
    visit = get_object_or_404(visits_for(request.user), pk=pk)
    patient_pk = visit.patient.pk
    if request.method == "POST":
        visit.delete()
        return redirect("patient_detail", pk=patient_pk)
    return render(request, "core/visit_confirm_delete.html", {"visit": visit})
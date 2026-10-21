from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from .forms import PatientForm, VisitForm
from .models import Patient, Visit
from . import predictor
from django.core.paginator import Paginator


def patients_for(user):
    """All health workers share access to patient records (continuity of care)."""
    return Patient.objects.all()


def visits_for(user):
    return Visit.objects.filter(patient__in=patients_for(user)).select_related("patient")
def apply_prediction(request, visit):
    try:
        label = predictor.predict_visit(visit)
        messages.success(request, f"Visit saved. Predicted risk: {label}.")
    except Exception:
        messages.warning(
            request,
            "Visit saved, but the risk prediction could not be run. Check the model files.",
        )

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
        "recent_visits": visits.select_related("patient", "recorded_by").order_by(
            "-visit_date", "-created_at"
        )[:5],
        "risk_summary": visits.exclude(predicted_result="")
        .values("predicted_result")
        .annotate(total=Count("id"))
        .order_by("-total"),
    }
    return render(request, "core/dashboard.html", context)


@login_required
def patient_lookup(request):
    pid = request.GET.get("pid", "").strip().upper()
    if not pid:
        return redirect("patient_list")
    patient = patients_for(request.user).filter(patient_id__iexact=pid).first()
    if patient:
        return redirect("patient_detail", pk=patient.pk)
    messages.error(request, f"No patient found with ID {pid}. You can register her below.")
    return redirect(f"{reverse('patient_create')}?patient_id={pid}")


@login_required
def patient_list(request):
    patients = patients_for(request.user).order_by("-created_at")
    q = request.GET.get("q", "").strip()
    if q:
        patients = patients.filter(
            Q(patient_id__icontains=q) | Q(name__icontains=q) | Q(contact__icontains=q)
        )
    page_obj = Paginator(patients, 10).get_page(request.GET.get("page"))
    return render(request, "core/patient_list.html", {
        "patients": page_obj,
        "page_obj": page_obj,
        "q": q,
    })


@login_required
def patient_create(request):
    if request.method == "POST":
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.user = request.user
            patient.save()
            messages.success(request, f"Patient {patient.name} was added.")
            return redirect("patient_detail", pk=patient.pk)
    else:
        form = PatientForm(initial={"patient_id": request.GET.get("patient_id", "")})
    return render(request, "core/patient_form.html", {"form": form, "title": "Add Patient"})

@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(patients_for(request.user), pk=pk)
    visits = patient.visits.select_related("recorded_by").order_by("-visit_date", "-created_at")
    latest = visits.first()

    trend = []
    for v in reversed(list(visits)):          # oldest to newest for the chart
        text = (v.predicted_result or "").lower()
        if text.startswith("high"):
            trend.append({"date": v.visit_date.strftime("%d %b %Y"), "score": 2})
        elif text.startswith("low"):
            trend.append({"date": v.visit_date.strftime("%d %b %Y"), "score": 1})

    return render(request, "core/patient_detail.html", {
        "patient": patient,
        "visits": visits,
        "latest": latest,
        "trend": trend,
    })


@login_required
def patient_update(request, pk):
    patient = get_object_or_404(patients_for(request.user), pk=pk)
    if request.method == "POST":
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "Patient details updated.")
            return redirect("patient_detail", pk=patient.pk)
    else:
        form = PatientForm(instance=patient)
    return render(request, "core/patient_form.html", {"form": form, "title": "Edit Patient"})


@login_required
def patient_delete(request, pk):
    patient = get_object_or_404(patients_for(request.user), pk=pk)
    if request.method == "POST":
        name = patient.name
        patient.delete()
        messages.success(request, f"Patient {name} was deleted.")
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
            visit.recorded_by = request.user
            apply_prediction(request, visit)
            visit.save()
            return redirect("patient_detail", pk=patient.pk)
    else:
        form = VisitForm(initial={"visit_date": timezone.localdate()})
    return render(
        request,
        "core/visit_form.html",
        {"form": form, "patient": patient, "title": "Add Visit"},
    )


@login_required
def visit_detail(request, pk):
    visit = get_object_or_404(visits_for(request.user), pk=pk)
    return render(request, "core/visit_detail.html", {"visit": visit})



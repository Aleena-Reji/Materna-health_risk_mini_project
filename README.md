# Materna – Maternal Health Risk Web App

A Django web application for managing maternal patients and their clinic visits. Doctors register patients, record visits, and track activity from a dashboard. Machine-learning-based risk prediction is planned and will be integrated into the visit workflow.

## Features

- Doctor login and logout, with admin access for staff
- Each doctor sees only their own patients (admins see all)
- Add, view, edit, delete and search patients
- Record visits for each patient and view visit history
- Dashboard with patient and visit counts, recent visits and a risk summary
- Django admin panel for managing users and records

## Tech stack

- Python 3.13
- Django 6.1
- SQLite
- HTML and CSS (Django templates)

## Database design

| Table | Purpose |
|-------|---------|
| **User** | Login account (extends Django's `AbstractUser`) with a `role` of doctor or admin |
| **Patient** | Patient details (name, age, contact), linked to the doctor who registered them |
| **Visit** | One clinic visit per record, linked to a patient, with symptoms, predicted result, confidence, model version and recommendation |

Relationships: one User has many Patients, and one Patient has many Visits.

## Setup (Windows)

1. Clone the repository:
```
   git clone https://github.com/Aleena-Reji/Materna-health_risk_mini_project.git
   cd Materna-health_risk_mini_project
```
2. Create and activate a virtual environment:
```
   python -m venv venv
   venv\Scripts\Activate.ps1
```
3. Install dependencies:
```
   pip install -r requirements.txt
```
4. Create the database tables:
```
   python manage.py migrate
```
5. Create an admin account:
```
   python manage.py createsuperuser
```
6. Start the server:
```
   python manage.py runserver
```
7. Open http://127.0.0.1:8000/ and log in.

## Project structure

```
config/      Project settings and root URLs
core/        App: models, views, forms, URLs
templates/   HTML templates (core/ pages and registration/ login)
manage.py    Django management script
```

## Status and roadmap

- [x] Database models and migrations
- [x] Authentication and per-doctor access
- [x] Patient management (CRUD and search)
- [x] Visit recording
- [x] Dashboard
- [ ] Clinical input fields on visits (to match the trained model)
- [ ] Integration of the maternal health risk prediction model
- [ ] Automatic recommendations based on predicted risk

## Author

Aleena Reji
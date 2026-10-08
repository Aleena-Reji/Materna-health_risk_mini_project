from django.contrib import admin
from .models import User, Patient, Visit

admin.site.register(User)
admin.site.register(Patient)
admin.site.register(Visit)
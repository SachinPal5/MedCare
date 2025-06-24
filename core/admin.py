from django.contrib import admin
from .models import Prescription
# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, TimeSlot, Appointment

# Customizing UserAdmin to show role in admin
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Role Info", {"fields": ("role",)}),
    )
    list_display = ["username", "email", "role", "is_staff"]

admin.site.register(User, CustomUserAdmin)
admin.site.register(TimeSlot)
admin.site.register(Appointment)

admin.site.register(Prescription)

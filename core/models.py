from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import io
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas

# --------------------------
# 1. Custom User Model
# --------------------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
 # ✅ Add this

    def __str__(self):
        return self.username
# --------------------------
# 2. Doctor's Available Time Slots
# --------------------------
class TimeSlot(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'doctor'})
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return f"{self.doctor.username} - {self.date} {self.time}"

# --------------------------
# 3. Appointments Booked by Patients
# --------------------------
class Appointment(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_appointments')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_appointments')
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return f"{self.patient.username} → {self.doctor.username} @ {self.timeslot.date} {self.timeslot.time}"

# --------------------------
# 4. Medical Record Uploads (PDFs, Scans)
# --------------------------
class MedicalRecord(models.Model):
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'patient'},
        related_name='patient_medical_records'
    )
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'doctor'},
        related_name='doctor_medical_records'
    )
    file = models.FileField(upload_to='medical_records/')
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.patient.username} → {self.doctor.username} ({self.uploaded_at.date()})"

# --------------------------
# 5. Prescription with PDF Generator
# --------------------------
class Prescription(models.Model):
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'patient'},
        related_name='patient_prescriptions'
    )
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'doctor'},
        related_name='doctor_prescriptions'
    )
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    pdf = models.FileField(upload_to='prescriptions/', blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        p.drawString(100, 800, f"Prescription for: {self.patient.username}")
        p.drawString(100, 780, f"Doctor: {self.doctor.username}")
        p.drawString(100, 760, f"Appointment ID: {self.appointment.id}")
        p.drawString(100, 740, f"Date: {self.created_at.strftime('%Y-%m-%d')}")
        p.drawString(100, 700, "Notes:")
        text_object = p.beginText(100, 680)
        for line in self.notes.split('\n'):
            text_object.textLine(line)
        p.drawText(text_object)
        p.showPage()
        p.save()

        buffer.seek(0)
        filename = f'prescription_{self.id}.pdf'
        self.pdf.save(filename, ContentFile(buffer.read()), save=False)
        buffer.close()

        super().save(update_fields=['pdf'])

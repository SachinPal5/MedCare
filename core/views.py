from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User
from django.contrib import messages
from django.db import IntegrityError

def home(request):
    return render(request, 'core/home.html')
 

   
def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        mobile_number = request.POST['mobile_number']
        role = request.POST['role']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            messages.error(request, 'Email already registered.')
            return redirect('signup')

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            mobile_number=mobile_number,
            role=role
        )
        messages.success(request, 'User registered successfully. Please log in.')
        return redirect('login')
        
    return render(request, 'core/signup.html')



def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'core/login.html')

@login_required
def dashboard(request):
    if request.user.role == 'doctor':
        return render(request, 'core/dashboard_doctor.html')  # ✅ fixed here
    elif request.user.role == 'patient':
        return render(request, 'core/dashboard_patient.html')
    return redirect('login')
from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('home')

from .forms import TimeSlotForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

@login_required
def create_timeslot(request):
    if request.user.role != 'doctor':
        return HttpResponseForbidden("Only doctors can create time slots.")

    if request.method == 'POST':
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            timeslot = form.save(commit=False)
            timeslot.doctor = request.user
            timeslot.save()
            messages.success(request, 'Time slot created!')
            return redirect('dashboard')
    else:
        form = TimeSlotForm()
        
    return render(request, 'core/create_timeslot.html', {'form': form}) 
from .models import TimeSlot, Appointment
from django.contrib import messages

@login_required
def book_appointment(request):
    if request.user.role != 'patient':
        return HttpResponseForbidden("Only patients can book appointments.")

    available_slots = TimeSlot.objects.exclude(
        id__in=Appointment.objects.values_list('timeslot_id', flat=True)
    ).order_by('date', 'time')

    if request.method == 'POST':
        slot_id = request.POST.get('slot_id')
        try:
            slot = TimeSlot.objects.get(id=slot_id)
            Appointment.objects.create(
                doctor=slot.doctor,
                patient=request.user,
                timeslot=slot,
                status='Pending'
            )
            messages.success(request, "Appointment booked successfully!")
            return redirect('dashboard')
        except TimeSlot.DoesNotExist:
            messages.error(request, "Invalid slot selected.")

    return render(request, 'core/book_appointment.html', {'slots': available_slots})
from .models import Appointment
from django.contrib.auth.decorators import login_required

@login_required
def appointment_history(request):
    if request.user.role != 'patient':
        return HttpResponseForbidden("Only patients can view this page.")
    
    appointments = Appointment.objects.filter(patient=request.user).select_related('doctor', 'timeslot').order_by('-timeslot__date', '-timeslot__time')

    return render(request, 'core/appointment_history.html', {'appointments': appointments})
from .models import MedicalRecord
from django.core.files.storage import FileSystemStorage
from django import forms

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['doctor', 'file', 'description']

@login_required
def upload_medical_record(request):
    if request.user.role != 'patient':
        return HttpResponseForbidden("Only patients can upload medical records.")

    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES)
        if form.is_valid():
            record = form.save(commit=False)
            record.patient = request.user
            record.save()
            messages.success(request, "Medical record uploaded successfully.")
            return redirect('dashboard')
    else:
        form = MedicalRecordForm()

    return render(request, 'core/upload_record.html', {'form': form})
@login_required
def doctor_appointment(request):
    if request.user.role != 'doctor':
        return HttpResponseForbidden("Only doctors can access this page.")
    
    appointments = Appointment.objects.filter(doctor=request.user).select_related('patient', 'timeslot').order_by('timeslot__date', 'timeslot__time')
    return render(request, 'core/doctor_appointment.html', {'appointment': appointments})

from .forms import PrescriptionForm
from .models import Prescription

@login_required
def add_prescription(request):
    if request.user.role != 'doctor':
        return HttpResponseForbidden("Only doctors can add prescriptions.")

    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.doctor = request.user
            prescription.patient = prescription.appointment.patient
            prescription.save()
            messages.success(request, "Prescription saved and PDF generated.")
            return redirect('dashboard')
    else:
        form = PrescriptionForm()

    return render(request, 'core/add_prescription.html', {'form': form})

from .models import Prescription

@login_required
def view_prescriptions(request):
    if request.user.role == 'doctor':
        prescriptions = Prescription.objects.filter(doctor=request.user).select_related('patient', 'appointment')
    elif request.user.role == 'patient':
        prescriptions = Prescription.objects.filter(patient=request.user).select_related('doctor', 'appointment')
    else:
        prescriptions = []

    return render(request, 'core/view_prescriptions.html', {'prescriptions': prescriptions})

from .models import Appointment, MedicalRecord
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_dashboard(request):
    all_appointments = Appointment.objects.select_related('doctor', 'patient', 'timeslot').order_by('-timeslot__date')
    all_records = MedicalRecord.objects.select_related('patient', 'doctor').order_by('-uploaded_at')

    return render(request, 'core/admin_dashboard.html', {
        'appointments': all_appointments,
        'records': all_records
    })
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def doctor_patient_chart(request):
    data = (
        User.objects
        .filter(role='doctor')
        .annotate(patient_count=Count('doctor_appointments'))
        .values('username', 'patient_count')
    )
    return JsonResponse(list(data), safe=False)
    

from .models import MedicalRecord
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

@login_required
def view_medical_records(request):
    if request.user.role != 'doctor':
        return HttpResponseForbidden("Only doctors can view this page.")
    
    records = MedicalRecord.objects.filter(doctor=request.user).select_related('patient').order_by('-uploaded_at')
    return render(request, 'core/view_medical_records.html', {'records': records})
@login_required
def patient_medical_records(request):
    if request.user.role != 'patient':
        return HttpResponseForbidden("Only patients can access this page.")

    records = MedicalRecord.objects.filter(patient=request.user).select_related('doctor').order_by('-uploaded_at')
    return render(request, 'core/patient_medical_records.html', {'records': records})
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_chart_view(request):
    return render(request, 'core/chart.html')
from django.shortcuts import redirect

@login_required
def dashboard(request):
    if request.user.role == 'doctor':
        return render(request, 'core/dashboard_doctor.html')
    elif request.user.role == 'patient':
        return render(request, 'core/dashboard_patient.html')
    elif request.user.is_staff:
        return redirect('admin_dashboard')
    return redirect('login')

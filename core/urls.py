from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-timeslot/', views.create_timeslot, name='create_timeslot'),
    path('book-appointment/', views.book_appointment, name='book_appointment'),
    path('appointment-history/', views.appointment_history, name='appointment_history'),
    path('upload-record/', views.upload_medical_record, name='upload_record'),
    path('doctor-appointment/', views.doctor_appointment, name='doctor_appointment'),
    path('add-prescription/', views.add_prescription, name='add_prescription'),
    path('prescriptions/', views.view_prescriptions, name='view_prescriptions'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('chart-data/', views.doctor_patient_chart, name='chart_data'),  # ✅ only once
    path('medical-records/', views.view_medical_records, name='view_medical_records'),
    path('my-medical-records/', views.patient_medical_records, name='patient_medical_records'),
    path('admin-chart/', views.admin_chart_view, name='admin_chart'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('dashboard/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('register/', views.register_employee, name='register_employee'),
    path('attendance/', views.mark_attendance, name='mark_attendance'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('api/employees/', views.get_employees, name='api_employees'),
    path('api/attendance/daily/', views.get_today_attendance, name='api_today_attendance'),
    path('api/employee-encodings/', views.employee_encodings_api, name='employee_encodings_api'),
]
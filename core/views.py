import numpy as np
import face_recognition
import cv2
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from .models import Supervisor, Employee, Attendance
from .serializers import EmployeeSerializer, AttendanceSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import date, datetime, timedelta
import csv
from django.template.loader import render_to_string
import math
import base64
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
from django.core.files.base import ContentFile
import os

# --- Utility Functions ---

def compress_image(image_file, max_size_kb=200):
    img = Image.open(image_file)
    img = img.convert('RGB')
    quality = 85
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=quality)
    while buffer.tell() > max_size_kb * 1024 and quality > 10:
        quality -= 5
        buffer.seek(0)
        buffer.truncate()
        img.save(buffer, format='JPEG', quality=quality)
    buffer.seek(0)
    return buffer

def is_blurry(image_file, threshold=100):
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    image_file.seek(0)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    fm = cv2.Laplacian(gray, cv2.CV_64F).var()
    return fm < threshold

def detect_blink_from_image(image_file):
    import numpy as np
    import face_recognition
    from scipy.spatial import distance as dist

    def eye_aspect_ratio(eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear

    img = face_recognition.load_image_file(image_file)
    face_landmarks_list = face_recognition.face_landmarks(img)
    if not face_landmarks_list:
        return False  # No face detected

    landmarks = face_landmarks_list[0]
    left_eye = landmarks['left_eye']
    right_eye = landmarks['right_eye']
    left_ear = eye_aspect_ratio(left_eye)
    right_ear = eye_aspect_ratio(right_eye)
    ear = (left_ear + right_ear) / 2.0
    BLINK_THRESHOLD = 0.33
    return ear < BLINK_THRESHOLD

def can_mark_attendance(user):
    return user.is_superuser or hasattr(user, 'supervisor')

def is_supervisor(user):
    return hasattr(user, 'supervisor')

# --- API Views ---

@api_view(['GET'])
def get_employees(request):
    data = EmployeeSerializer(Employee.objects.all(), many=True).data
    return Response(data)

@api_view(['GET'])
def get_today_attendance(request):
    data = AttendanceSerializer(Attendance.objects.filter(date=date.today()), many=True).data
    return Response(data)

# --- Export Views ---

def is_admin(user):
    return user.is_superuser or user.groups.filter(name='Admin').exists()

@user_passes_test(is_admin)
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance.csv"'
    writer = csv.writer(response)
    writer.writerow(['Employee Number', 'Employee Name', 'Date', 'Time', 'Marked By'])
    for att in Attendance.objects.all():
        writer.writerow([
            att.employee.employee_number,
            att.employee.name,
            att.date,
            att.time,
            att.marked_by.full_name if att.marked_by else ''
        ])
    return response

def export_pdf(request):
    html = render_to_string('attendance_pdf.html', {'records': Attendance.objects.all()})
    # ... your PDF logic here ...
    return HttpResponse("PDF export not implemented in this snippet.")

# --- Supervisor Dashboard ---

@login_required
@user_passes_test(is_supervisor)
def supervisor_dashboard(request):
    if request.user.is_superuser:
        return redirect('/admin/')
    supervisor = request.user.supervisor
    employees = Employee.objects.filter(supervisor=supervisor)
    attendance_records = Attendance.objects.filter(employee__in=employees).order_by('-date', '-time')[:20]
    return render(request, 'supervisor_dashboard.html', {
        'employees': employees,
        'attendance_records': attendance_records,
    })

# --- Employee Registration (by Supervisor) ---

@login_required
@user_passes_test(is_supervisor)
def register_employee(request):
    supervisor = request.user.supervisor
    if request.method == 'POST':
        employee_number = request.POST.get('employee_number')
        name = request.POST.get('name')
        job_title_id = request.POST.get('job_title')
        address = request.POST.get('address')
        contact_number = request.POST.get('contact_number')
        email = request.POST.get('email')
        image_file = request.FILES.get('image')
        captured_image_data = request.POST.get('captured_image')
        # If no file uploaded, but captured image exists, convert it to file
        if not image_file and captured_image_data:
            format, imgstr = captured_image_data.split(';base64,')
            img_bytes = base64.b64decode(imgstr)
            image_file = InMemoryUploadedFile(
                BytesIO(img_bytes), None, 'captured.png', 'image/png', len(img_bytes), None
            )
        job_title = None
        if job_title_id:
            from .models import JobTitle
            try:
                job_title = JobTitle.objects.get(id=job_title_id)
            except JobTitle.DoesNotExist:
                job_title = None
        if image_file:
            if is_blurry(image_file):
                return render(request, 'register_employee.html', {'error': 'Image is too blurry. Please upload a clearer photo.'})
            # Reset file pointer for encoding
            image_file.seek(0)
            img = face_recognition.load_image_file(image_file)
            encodings = face_recognition.face_encodings(img)
            if encodings:
                encoding = encodings[0]
                # Compress image before saving
                image_file.seek(0)
                compressed_buffer = compress_image(image_file, max_size_kb=200)
                from django.core.files.base import ContentFile
                compressed_image = ContentFile(compressed_buffer.read(), name=f"{employee_number}.jpg")
                Employee.objects.create(
                    employee_number=employee_number,
                    name=name,
                    job_title=job_title,
                    address=address,
                    contact_number=contact_number,
                    email=email,
                    supervisor=supervisor,
                    face_encoding=encoding.tobytes(),
                    face_image=compressed_image
                )
                return redirect('supervisor_dashboard')
            else:
                return render(request, 'register_employee.html', {'error': 'No face detected.'})
    from .models import JobTitle
    job_titles = JobTitle.objects.all()
    return render(request, 'register_employee.html', {'job_titles': job_titles})

# --- Attendance Marking (by Supervisor) ---

@login_required
@user_passes_test(can_mark_attendance)
def mark_attendance(request):
    if request.user.is_superuser:
        employees = Employee.objects.all()
        supervisor = None
    else:
        supervisor = request.user.supervisor
        employees = Employee.objects.filter(supervisor=supervisor)
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        captured_image_data = request.POST.get('captured_image')
        status = request.POST.get('status')
        if not (employee_id and captured_image_data and status):
            return render(request, 'mark_attendance.html', {
                'employees': employees,
                'error': 'All fields are required.'
            })
        latitude = None
        longitude = None
        try:
            if supervisor:
                emp = Employee.objects.get(id=employee_id, supervisor=supervisor)
            else:
                emp = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return render(request, 'mark_attendance.html', {
                'employees': employees,
                'error': 'Employee not found.'
            })
        # Convert base64 image to file-like object
        format, imgstr = captured_image_data.split(';base64,')
        img_bytes = base64.b64decode(imgstr)
        img_file = BytesIO(img_bytes)
        img = face_recognition.load_image_file(img_file)
        encodings = face_recognition.face_encodings(img)
        if encodings:
            encoding = encodings[0]
            known_encoding = np.frombuffer(emp.face_encoding, dtype=np.float64)
            face_dist = face_recognition.face_distance([known_encoding], encoding)[0]
            if face_dist < 0.45:  # Lower threshold = stricter match (try 0.4-0.5)
                today = date.today()
                # --- 1 minute gap logic ---
                last_attendance = Attendance.objects.filter(employee=emp, date=today, status=status).order_by('-time').first()
                if last_attendance:
                    now = datetime.now().time()
                    last_time = last_attendance.time
                    now_dt = datetime.combine(today, now)
                    last_dt = datetime.combine(today, last_time)
                    if (now_dt - last_dt) < timedelta(minutes=1):
                        return render(request, 'mark_attendance.html', {
                            'employees': employees,
                            'error': f'Attendance already marked for {emp.name} ({status}) within the last 1 minute.'
                        })
                # --- end 1 minute gap logic ---
                img_file.seek(0)
                if detect_blink_from_image(img_file):
                    # Compress and save attendance image
                    compressed_buffer = compress_image(BytesIO(img_bytes), max_size_kb=200)
                    attendance_image = ContentFile(compressed_buffer.read(), name=f"{emp.employee_number}_{today}_{status}.jpg")
                    Attendance.objects.create(
                        employee=emp,
                        latitude=latitude,
                        longitude=longitude,
                        marked_by=supervisor,
                        status=status,
                        image=attendance_image
                    )
                    # No need to delete temp file as we use in-memory objects
                    return render(request, 'mark_attendance.html', {
                        'employees': employees,
                        'success': f'Attendance marked for {emp.name} ({status}, blink detected).'
                    })
                else:
                    return render(request, 'mark_attendance.html', {
                        'employees': employees,
                        'error': 'Blink not detected. Please blink and try again.'
                    })
            else:
                return render(request, 'mark_attendance.html', {
                    'employees': employees,
                    'error': 'Face not recognized. Please try again with a clear face.'
                })
        else:
            return render(request, 'mark_attendance.html', {
                'employees': employees,
                'error': 'No face detected.'
            })
    return render(request, 'mark_attendance.html', {'employees': employees})

# --- Employee Encodings API ---

@login_required
def employee_encodings_api(request):
    employees = Employee.objects.all()
    data = []
    for emp in employees:
        encoding = np.frombuffer(emp.face_encoding, dtype=np.float64).tolist()
        data.append({
            'id': emp.id,
            'name': emp.name,
            'encoding': encoding,
        })
    return JsonResponse(data, safe=False)


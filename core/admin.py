from django.contrib import admin
from .models import (
    CompanyProfile,
    JobCategory,
    JobTitle,
    Supervisor,
    Employee,
    Attendance,
)

@admin.register(Supervisor)
class SupervisorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'get_assigned_categories']
    filter_horizontal = ['assigned_categories']
    
    def get_assigned_categories(self, obj):
        return ", ".join([cat.name for cat in obj.assigned_categories.all()])
    get_assigned_categories.short_description = 'Assigned Categories'

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_number', 'name', 'job_title', 'supervisor']
    list_filter = ['job_title__category', 'supervisor']
    search_fields = ['employee_number', 'name']

admin.site.register(CompanyProfile)
admin.site.register(JobCategory)
admin.site.register(JobTitle)
admin.site.register(Attendance)
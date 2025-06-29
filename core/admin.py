from django.contrib import admin
from .models import (
    CompanyProfile,
    JobCategory,
    JobTitle,
    Supervisor,
    Employee,
    Attendance,
)

admin.site.register(CompanyProfile)
admin.site.register(JobCategory)
admin.site.register(JobTitle)
admin.site.register(Supervisor)
admin.site.register(Employee)
admin.site.register(Attendance)
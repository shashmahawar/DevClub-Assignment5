from django.contrib import admin
from .models import Announcement, Assignment, Course, CourseGrade, Grade, Material, Message, Profile, SemesterLog, Submission

# Register your models here.

admin.site.register(Assignment)
admin.site.register(Grade)
admin.site.register(CourseGrade)
admin.site.register(Profile)
admin.site.register(SemesterLog)
admin.site.register(Message)
admin.site.register(Submission)
admin.site.register(Course)
admin.site.register(Announcement)
admin.site.register(Material)
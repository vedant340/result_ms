from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Student, Teacher, Subject, Result, Department, Announcement


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'first_name', 'last_name', 'is_active')
    list_filter = ('role', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Info', {'fields': ('role', 'phone', 'profile_pic')}),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('roll_number', 'user', 'department', 'semester', 'batch_year')
    list_filter = ('department', 'semester', 'batch_year')
    search_fields = ('roll_number', 'user__username', 'user__first_name')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'department', 'qualification')
    list_filter = ('department',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'teacher', 'semester', 'credit_hours')
    list_filter = ('department', 'semester', 'subject_type')


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'marks_obtained', 'grade', 'grade_points', 'semester')
    list_filter = ('grade', 'semester', 'academic_year')
    search_fields = ('student__user__username', 'subject__name')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'target_role', 'is_active', 'created_at')

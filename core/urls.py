from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('analytics/', views.teacher_analytics, name='teacher_analytics'),
    # Admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.manage_users, name='manage_users'),
    path('admin/users/add/', views.add_user, name='add_user'),
    path('admin/users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admin/departments/', views.manage_departments, name='manage_departments'),
    path('admin/departments/delete/<int:dept_id>/', views.delete_department, name='delete_department'),
    path('admin/announcements/', views.manage_announcements, name='manage_announcements'),
    path('admin/announcements/delete/<int:ann_id>/', views.delete_announcement, name='delete_announcement'),
    path('admin/results/', views.all_students_results, name='all_students_results'),

    # Teacher
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('subjects/', views.manage_subjects, name='manage_subjects'),
    path('subjects/delete/<int:subject_id>/', views.delete_subject, name='delete_subject'),
    path('results/', views.manage_results, name='manage_results'),
    path('results/edit/<int:result_id>/', views.edit_result, name='edit_result'),
    path('results/delete/<int:result_id>/', views.delete_result, name='delete_result'),

    # Student
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/result/<int:student_id>/', views.student_result_detail, name='student_result_detail'),
    path('student/result/<int:student_id>/pdf/', views.download_result_pdf, name='download_result_pdf'),
    
]

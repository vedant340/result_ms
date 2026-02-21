"""
Demo Data Setup Script for EduNova Result Management System
Run with: python setup_demo.py (after migrate)
Or: python manage.py shell < setup_demo.py
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'result_management.settings')
django.setup()

from core.models import User, Student, Teacher, Subject, Result, Department, Announcement

print("🚀 Setting up EduNova demo data...")

# Clear existing data
Result.objects.all().delete()
Subject.objects.all().delete()
Student.objects.all().delete()
Teacher.objects.all().delete()
Department.objects.all().delete()
Announcement.objects.all().delete()
User.objects.exclude(is_superuser=True).delete()

# 1. Create Departments
depts = [
    Department.objects.create(name="Computer Science & Engineering", code="CSE", description="Modern computing and software engineering"),
    Department.objects.create(name="Electronics & Communication", code="ECE", description="Electronics, signals and communications"),
    Department.objects.create(name="Mechanical Engineering", code="ME", description="Machines, thermodynamics and manufacturing"),
    Department.objects.create(name="Business Administration", code="MBA", description="Management, finance and entrepreneurship"),
]
print(f"✅ Created {len(depts)} departments")

# 2. Create Admin
admin = User.objects.create_user(username='admin', password='admin123', role='admin',
    first_name='Super', last_name='Admin', email='admin@edunova.com')
admin.is_staff = True
admin.save()

# 3. Create Teachers
teacher_users = [
    User.objects.create_user(username='teacher1', password='teacher123', role='teacher',
        first_name='Dr. Priya', last_name='Sharma', email='priya@edunova.com'),
    User.objects.create_user(username='teacher2', password='teacher123', role='teacher',
        first_name='Prof. Rahul', last_name='Verma', email='rahul@edunova.com'),
    User.objects.create_user(username='teacher3', password='teacher123', role='teacher',
        first_name='Dr. Anjali', last_name='Singh', email='anjali@edunova.com'),
]
teachers = [
    Teacher.objects.create(user=teacher_users[0], department=depts[0], employee_id='EMP001', qualification='Ph.D Computer Science', joining_date='2020-07-01'),
    Teacher.objects.create(user=teacher_users[1], department=depts[1], employee_id='EMP002', qualification='M.Tech Electronics', joining_date='2021-01-15'),
    Teacher.objects.create(user=teacher_users[2], department=depts[2], employee_id='EMP003', qualification='Ph.D Mechanical', joining_date='2019-08-01'),
]
print(f"✅ Created {len(teachers)} teachers")

# 4. Create Students
student_data = [
    ('student1', 'Aarav', 'Kumar', 'CS2024001', 'EN2024CS001', depts[0], 1, 2024),
    ('student2', 'Priya', 'Patel', 'CS2024002', 'EN2024CS002', depts[0], 1, 2024),
    ('student3', 'Vikram', 'Singh', 'CS2023001', 'EN2023CS001', depts[0], 3, 2023),
    ('student4', 'Neha', 'Sharma', 'EC2024001', 'EN2024EC001', depts[1], 1, 2024),
    ('student5', 'Rahul', 'Gupta', 'ME2024001', 'EN2024ME001', depts[2], 2, 2024),
]
students = []
for username, first, last, roll, enroll, dept, sem, batch in student_data:
    u = User.objects.create_user(username=username, password='student123', role='student',
        first_name=first, last_name=last, email=f'{username}@edunova.com')
    s = Student.objects.create(user=u, department=dept, roll_number=roll,
        enrollment_number=enroll, semester=sem, batch_year=batch, guardian_name=f'{first}\'s Parent')
    students.append(s)
print(f"✅ Created {len(students)} students")

# 5. Create Subjects
subjects = [
    Subject.objects.create(name='Data Structures & Algorithms', code='CS301', department=depts[0], teacher=teachers[0], semester=1, credit_hours=4, max_marks=100, passing_marks=40),
    Subject.objects.create(name='Database Management Systems', code='CS302', department=depts[0], teacher=teachers[0], semester=1, credit_hours=3, max_marks=100, passing_marks=40),
    Subject.objects.create(name='Object Oriented Programming', code='CS303', department=depts[0], teacher=teachers[0], semester=1, credit_hours=4, max_marks=100, passing_marks=40),
    Subject.objects.create(name='Computer Networks', code='CS304', department=depts[0], teacher=teachers[0], semester=1, credit_hours=3, max_marks=100, passing_marks=40),
    Subject.objects.create(name='Mathematics III', code='MA301', department=depts[0], teacher=teachers[0], semester=1, credit_hours=4, max_marks=100, passing_marks=40),
    Subject.objects.create(name='Circuit Theory', code='EC301', department=depts[1], teacher=teachers[1], semester=1, credit_hours=3, max_marks=100, passing_marks=40),
    Subject.objects.create(name='Digital Electronics', code='EC302', department=depts[1], teacher=teachers[1], semester=1, credit_hours=4, max_marks=100, passing_marks=40),
    Subject.objects.create(name='Thermodynamics', code='ME301', department=depts[2], teacher=teachers[2], semester=2, credit_hours=4, max_marks=100, passing_marks=40),
    # Semester 3 subjects for student3
    Subject.objects.create(name='Operating Systems', code='CS501', department=depts[0], teacher=teachers[0], semester=3, credit_hours=4, max_marks=100, passing_marks=40),
    Subject.objects.create(name='Software Engineering', code='CS502', department=depts[0], teacher=teachers[0], semester=3, credit_hours=3, max_marks=100, passing_marks=40),
]
print(f"✅ Created {len(subjects)} subjects")

# 6. Create Results
import random
results_data = [
    # Student 1 (Aarav) - Semester 1 CSE subjects
    (students[0], subjects[0], 88, 20, 68, 1),
    (students[0], subjects[1], 72, 16, 56, 1),
    (students[0], subjects[2], 95, 23, 72, 1),
    (students[0], subjects[3], 65, 15, 50, 1),
    (students[0], subjects[4], 78, 18, 60, 1),
    # Student 2 (Priya) - Semester 1
    (students[1], subjects[0], 92, 22, 70, 1),
    (students[1], subjects[1], 85, 20, 65, 1),
    (students[1], subjects[2], 88, 21, 67, 1),
    (students[1], subjects[3], 79, 19, 60, 1),
    (students[1], subjects[4], 35, 10, 25, 1),  # Fail
    # Student 3 (Vikram) - Multi-semester
    (students[2], subjects[0], 75, 18, 57, 1),
    (students[2], subjects[1], 68, 15, 53, 1),
    (students[2], subjects[2], 82, 19, 63, 1),
    (students[2], subjects[8], 88, 20, 68, 3),
    (students[2], subjects[9], 91, 22, 69, 3),
    # Student 4 (Neha) - ECE
    (students[3], subjects[5], 94, 23, 71, 1),
    (students[3], subjects[6], 87, 20, 67, 1),
    # Student 5 (Rahul) - ME
    (students[4], subjects[7], 70, 16, 54, 2),
]

for student, subject, total, internal, external, semester in results_data:
    Result.objects.create(
        student=student, subject=subject,
        marks_obtained=total, internal_marks=internal, external_marks=external,
        semester=semester, academic_year='2024-25',
        added_by=admin
    )
print(f"✅ Created {len(results_data)} results")

# 7. Announcements
Announcement.objects.create(title='Semester Exams Schedule Released', content='The examination schedule for the upcoming semester exams has been published. Please check the academic calendar for dates and prepare accordingly.', created_by=admin, target_role='all')
Announcement.objects.create(title='Result Declaration', content='Results for Semester 1 (2024-25) have been declared. Students can view their results in the portal.', created_by=admin, target_role='student')
Announcement.objects.create(title='Faculty Meeting', content='All faculty members are requested to attend the curriculum review meeting on Friday at 3 PM in Conference Hall.', created_by=admin, target_role='teacher')
print("✅ Created 3 announcements")

print("\n" + "="*50)
print("🎉 EduNova Demo Setup Complete!")
print("="*50)
print("\n📋 LOGIN CREDENTIALS:")
print(f"  Admin:    admin / admin123")
print(f"  Teacher:  teacher1 / teacher123")
print(f"  Student:  student1 / student123")
print(f"  More students: student2, student3, student4, student5")
print("\n🌐 Run server: python manage.py runserver")
print("🔗 Open: http://127.0.0.1:8000/")

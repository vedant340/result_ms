from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

    def is_admin(self):
        return self.role == 'admin'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student_role(self):
        return self.role == 'student'


class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    employee_id = models.CharField(max_length=20, unique=True)
    qualification = models.CharField(max_length=100, blank=True)
    joining_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Teacher: {self.user.get_full_name() or self.user.username}"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    roll_number = models.CharField(max_length=20, unique=True)
    enrollment_number = models.CharField(max_length=30, unique=True)
    semester = models.IntegerField(default=1)
    batch_year = models.IntegerField(default=2024)
    date_of_birth = models.DateField(null=True, blank=True)
    guardian_name = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.roll_number} - {self.user.get_full_name() or self.user.username}"

    def get_cgpa(self):
        results = Result.objects.filter(student=self)
        if not results.exists():
            return 0.0
        total_points = sum(r.grade_points * r.subject.credit_hours for r in results if r.grade_points is not None)
        total_credits = sum(r.subject.credit_hours for r in results if r.grade_points is not None)
        if total_credits == 0:
            return 0.0
        return round(total_points / total_credits, 2)

    def get_percentage(self):
        results = Result.objects.filter(student=self)
        if not results.exists():
            return 0.0
        total_marks = sum(r.marks_obtained for r in results if r.marks_obtained is not None)
        total_max = sum(r.subject.max_marks for r in results if r.marks_obtained is not None)
        if total_max == 0:
            return 0.0
        return round((total_marks / total_max) * 100, 2)


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='subjects')
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='subjects')
    semester = models.IntegerField(default=1)
    credit_hours = models.IntegerField(default=3)
    max_marks = models.IntegerField(default=100)
    passing_marks = models.IntegerField(default=40)
    subject_type = models.CharField(max_length=20, choices=[('theory', 'Theory'), ('practical', 'Practical'), ('lab', 'Lab')], default='theory')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Result(models.Model):
    GRADE_CHOICES = (
        ('O', 'Outstanding (10)'),
        ('A+', 'Excellent (9)'),
        ('A', 'Very Good (8)'),
        ('B+', 'Good (7)'),
        ('B', 'Above Average (6)'),
        ('C', 'Average (5)'),
        ('P', 'Pass (4)'),
        ('F', 'Fail (0)'),
        ('Ab', 'Absent (0)'),
    )

    GRADE_POINT_MAP = {
        'O': 10, 'A+': 9, 'A': 8, 'B+': 7,
        'B': 6, 'C': 5, 'P': 4, 'F': 0, 'Ab': 0
    }

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='results')
    marks_obtained = models.FloatField(null=True, blank=True)
    internal_marks = models.FloatField(default=0, null=True, blank=True)
    external_marks = models.FloatField(default=0, null=True, blank=True)
    grade = models.CharField(max_length=5, choices=GRADE_CHOICES, blank=True)
    grade_points = models.FloatField(null=True, blank=True)
    semester = models.IntegerField(default=1)
    academic_year = models.CharField(max_length=10, default='2024-25')
    exam_date = models.DateField(null=True, blank=True)
    remarks = models.CharField(max_length=200, blank=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='added_results')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'subject', 'semester', 'academic_year')

    def save(self, *args, **kwargs):
        if self.marks_obtained is not None:
            pct = (self.marks_obtained / self.subject.max_marks) * 100
            if pct >= 90:
                self.grade = 'O'
            elif pct >= 80:
                self.grade = 'A+'
            elif pct >= 70:
                self.grade = 'A'
            elif pct >= 60:
                self.grade = 'B+'
            elif pct >= 50:
                self.grade = 'B'
            elif pct >= 45:
                self.grade = 'C'
            elif pct >= 40:
                self.grade = 'P'
            else:
                self.grade = 'F'
            self.grade_points = self.GRADE_POINT_MAP.get(self.grade, 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.grade}"

    def get_status(self):
        if self.marks_obtained is None:
            return 'Pending'
        return 'Pass' if self.marks_obtained >= self.subject.passing_marks else 'Fail'


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    target_role = models.CharField(max_length=20, choices=[('all', 'All'), ('student', 'Students'), ('teacher', 'Teachers')], default='all')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

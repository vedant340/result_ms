from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from .models import User, Student, Teacher, Subject, Result, Department, Announcement
from .forms import (LoginForm, UserCreateForm, StudentProfileForm, TeacherProfileForm,
                    SubjectForm, ResultForm, DepartmentForm, AnnouncementForm)


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials. Please try again.')
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def dashboard_view(request):
    user = request.user
    if user.role == 'admin':
        return redirect('admin_dashboard')
    elif user.role == 'teacher':
        return redirect('teacher_dashboard')
    elif user.role == 'student':
        return redirect('student_dashboard')
    return redirect('login')


# ===================== ADMIN VIEWS =====================

def admin_required(func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('login')
        return func(request, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


def teacher_required(func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ['admin', 'teacher']:
            messages.error(request, 'Access denied.')
            return redirect('login')
        return func(request, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


@admin_required
def admin_dashboard(request):
    stats = {
        'total_students': Student.objects.count(),
        'total_teachers': Teacher.objects.count(),
        'total_subjects': Subject.objects.count(),
        'total_departments': Department.objects.count(),
        'total_results': Result.objects.count(),
        'pass_count': Result.objects.filter(grade__in=['O', 'A+', 'A', 'B+', 'B', 'C', 'P']).count(),
        'fail_count': Result.objects.filter(grade='F').count(),
    }
    recent_results = Result.objects.select_related('student__user', 'subject').order_by('-created_at')[:10]
    departments = Department.objects.annotate(student_count=Count('student')).all()
    announcements = Announcement.objects.filter(is_active=True)[:5]
    recent_students = Student.objects.select_related('user', 'department').order_by('-user__created_at')[:5]
    context = {
        'stats': stats,
        'recent_results': recent_results,
        'departments': departments,
        'announcements': announcements,
        'recent_students': recent_students,
    }
    return render(request, 'core/admin_dashboard.html', context)


@admin_required
def manage_users(request):
    users = User.objects.all().order_by('-created_at')
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    return render(request, 'core/manage_users.html', {'users': users, 'role_filter': role_filter})


@admin_required
def add_user(request):
    user_form = UserCreateForm()
    student_form = StudentProfileForm()
    teacher_form = TeacherProfileForm()

    if request.method == 'POST':
        user_form = UserCreateForm(request.POST)
        if user_form.is_valid():
            user = user_form.save()
            role = user.role
            if role == 'student':
                try:
                    from datetime import date
                    dept_id = request.POST.get('department')
                    dept = Department.objects.get(id=dept_id) if dept_id else None
                    dob_str = request.POST.get('date_of_birth', '')
                    dob = None
                    if dob_str:
                        from datetime import datetime
                        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                    Student.objects.create(
                        user=user,
                        department=dept,
                        roll_number=request.POST.get('roll_number', f'ROLL{user.id}'),
                        enrollment_number=request.POST.get('enrollment_number', f'EN{user.id}'),
                        semester=int(request.POST.get('semester', 1)),
                        batch_year=int(request.POST.get('batch_year', 2024)),
                        guardian_name=request.POST.get('guardian_name', ''),
                        date_of_birth=dob,
                    )
                    messages.success(request, f'Student {user.username} created successfully!')
                except Exception as e:
                    messages.warning(request, f'Student {user.username} created but profile incomplete: {e}')
                return redirect('manage_users')
            elif role == 'teacher':
                try:
                    dept_id = request.POST.get('teacher_department')
                    dept = Department.objects.get(id=dept_id) if dept_id else None
                    jd_str = request.POST.get('joining_date', '')
                    jd = None
                    if jd_str:
                        from datetime import datetime
                        jd = datetime.strptime(jd_str, '%Y-%m-%d').date()
                    Teacher.objects.create(
                        user=user,
                        department=dept,
                        employee_id=request.POST.get('employee_id', f'EMP{user.id}'),
                        qualification=request.POST.get('qualification', ''),
                        joining_date=jd,
                    )
                    messages.success(request, f'Teacher {user.username} created successfully!')
                except Exception as e:
                    messages.warning(request, f'Teacher {user.username} created but profile incomplete: {e}')
                return redirect('manage_users')
            else:
                messages.success(request, f'Admin {user.username} created successfully!')
                return redirect('manage_users')
        else:
            messages.error(request, 'Please fix the errors below.')

    return render(request, 'core/add_user.html', {
        'user_form': user_form,
        'student_form': student_form,
        'teacher_form': teacher_form,
        'departments': Department.objects.all(),
    })


@admin_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('manage_users')
    name = user.get_full_name() or user.username
    user.delete()
    messages.success(request, f'User {name} deleted successfully.')
    return redirect('manage_users')


@admin_required
def manage_departments(request):
    departments = Department.objects.annotate(
        student_count=Count('student'),
        subject_count=Count('subjects')
    )
    form = DepartmentForm()
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department added successfully!')
            return redirect('manage_departments')
    return render(request, 'core/manage_departments.html', {'departments': departments, 'form': form})


@admin_required
def delete_department(request, dept_id):
    dept = get_object_or_404(Department, id=dept_id)
    dept.delete()
    messages.success(request, 'Department deleted.')
    return redirect('manage_departments')


@admin_required
def manage_announcements(request):
    announcements = Announcement.objects.all()
    form = AnnouncementForm()
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.created_by = request.user
            ann.save()
            messages.success(request, 'Announcement posted!')
            return redirect('manage_announcements')
    return render(request, 'core/manage_announcements.html', {'announcements': announcements, 'form': form})


@admin_required
def delete_announcement(request, ann_id):
    ann = get_object_or_404(Announcement, id=ann_id)
    ann.delete()
    messages.success(request, 'Announcement deleted.')
    return redirect('manage_announcements')


# ===================== SUBJECT MANAGEMENT =====================

@teacher_required
def manage_subjects(request):
    user = request.user
    if user.role == 'admin':
        subjects = Subject.objects.select_related('department', 'teacher__user').all()
    else:
        teacher = get_object_or_404(Teacher, user=user)
        subjects = Subject.objects.filter(teacher=teacher)

    form = SubjectForm()
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Subject "{subject.name}" added successfully!')
            return redirect('manage_subjects')
        else:
            messages.error(request, 'Please fix the errors below.')

    return render(request, 'core/manage_subjects.html', {'subjects': subjects, 'form': form})


@teacher_required
def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    user = request.user
    if user.role == 'teacher':
        teacher = get_object_or_404(Teacher, user=user)
        if subject.teacher != teacher:
            messages.error(request, 'You can only delete your own subjects.')
            return redirect('manage_subjects')
    subject.delete()
    messages.success(request, 'Subject deleted.')
    return redirect('manage_subjects')


# ===================== RESULT MANAGEMENT =====================

@teacher_required
def manage_results(request):
    user = request.user
    if user.role == 'admin':
        results = Result.objects.select_related('student__user', 'subject').all().order_by('-created_at')
        subjects = Subject.objects.all()
    else:
        teacher = get_object_or_404(Teacher, user=user)
        subjects = Subject.objects.filter(teacher=teacher)
        results = Result.objects.filter(subject__in=subjects).select_related('student__user', 'subject').order_by('-created_at')

    form = ResultForm()
    if user.role == 'teacher':
        teacher = Teacher.objects.get(user=user)
        form.fields['subject'].queryset = Subject.objects.filter(teacher=teacher)

    if request.method == 'POST':
        form = ResultForm(request.POST)
        if user.role == 'teacher':
            teacher = Teacher.objects.get(user=user)
            form.fields['subject'].queryset = Subject.objects.filter(teacher=teacher)
        if form.is_valid():
            result = form.save(commit=False)
            result.added_by = request.user
            result.save()
            messages.success(request, f'Result added for {result.student}!')
            return redirect('manage_results')
        else:
            messages.error(request, 'Error adding result. Check for duplicates.')

    return render(request, 'core/manage_results.html', {'results': results, 'form': form})


@teacher_required
def edit_result(request, result_id):
    result = get_object_or_404(Result, id=result_id)
    form = ResultForm(request.POST or None, instance=result)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Result updated!')
        return redirect('manage_results')
    return render(request, 'core/edit_result.html', {'form': form, 'result': result})


@teacher_required
def delete_result(request, result_id):
    result = get_object_or_404(Result, id=result_id)
    result.delete()
    messages.success(request, 'Result deleted.')
    return redirect('manage_results')


# ===================== TEACHER VIEWS =====================

@login_required
def teacher_dashboard(request):
    if request.user.role != 'teacher':
        return redirect('dashboard')
    teacher = get_object_or_404(Teacher, user=request.user)
    subjects = Subject.objects.filter(teacher=teacher)
    results = Result.objects.filter(subject__in=subjects)
    stats = {
        'total_subjects': subjects.count(),
        'total_results': results.count(),
        'pass_count': results.filter(grade__in=['O', 'A+', 'A', 'B+', 'B', 'C', 'P']).count(),
        'fail_count': results.filter(grade='F').count(),
        'avg_marks': results.aggregate(avg=Avg('marks_obtained'))['avg'] or 0,
    }
    recent_results = results.select_related('student__user', 'subject').order_by('-created_at')[:8]
    announcements = Announcement.objects.filter(is_active=True, target_role__in=['all', 'teacher'])[:5]
    return render(request, 'core/teacher_dashboard.html', {
        'teacher': teacher,
        'subjects': subjects,
        'stats': stats,
        'recent_results': recent_results,
        'announcements': announcements,
    })


# ===================== STUDENT VIEWS =====================

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('dashboard')
    student = get_object_or_404(Student, user=request.user)
    results = Result.objects.filter(student=student).select_related('subject').order_by('semester', 'subject__name')

    semester_data = {}
    for result in results:
        sem = result.semester
        if sem not in semester_data:
            semester_data[sem] = {'results': [], 'total_marks': 0, 'max_marks': 0, 'credits': 0, 'grade_points': 0}
        semester_data[sem]['results'].append(result)
        if result.marks_obtained:
            semester_data[sem]['total_marks'] += result.marks_obtained
            semester_data[sem]['max_marks'] += result.subject.max_marks
            semester_data[sem]['credits'] += result.subject.credit_hours
            semester_data[sem]['grade_points'] += (result.grade_points or 0) * result.subject.credit_hours

    for sem, data in semester_data.items():
        if data['max_marks'] > 0:
            data['percentage'] = round((data['total_marks'] / data['max_marks']) * 100, 2)
        else:
            data['percentage'] = 0
        if data['credits'] > 0:
            data['sgpa'] = round(data['grade_points'] / data['credits'], 2)
        else:
            data['sgpa'] = 0

    cgpa = student.get_cgpa()
    overall_pct = student.get_percentage()
    announcements = Announcement.objects.filter(is_active=True, target_role__in=['all', 'student'])[:5]

    grade_dist = {}
    for result in results:
        if result.grade:
            grade_dist[result.grade] = grade_dist.get(result.grade, 0) + 1

    return render(request, 'core/student_dashboard.html', {
        'student': student,
        'results': results,
        'semester_data': dict(sorted(semester_data.items())),
        'cgpa': cgpa,
        'overall_percentage': overall_pct,
        'announcements': announcements,
        'grade_dist': grade_dist,
        'total_subjects': results.count(),
        'pass_count': results.filter(grade__in=['O', 'A+', 'A', 'B+', 'B', 'C', 'P']).count(),
        'fail_count': results.filter(grade='F').count(),
    })


@login_required
def student_result_detail(request, student_id):
    if request.user.role == 'student' and request.user.student_profile.id != student_id:
        messages.error(request, 'Access denied.')
        return redirect('student_dashboard')
    student = get_object_or_404(Student, id=student_id)
    results = Result.objects.filter(student=student).select_related('subject').order_by('semester')
    return render(request, 'core/student_result_detail.html', {
        'student': student,
        'results': results,
        'cgpa': student.get_cgpa(),
        'percentage': student.get_percentage(),
    })


@admin_required
def all_students_results(request):
    students = Student.objects.select_related('user', 'department').all()
    dept_filter = request.GET.get('dept', '')
    if dept_filter:
        students = students.filter(department_id=dept_filter)
    departments = Department.objects.all()
    student_data = []
    for s in students:
        student_data.append({
            'student': s,
            'cgpa': s.get_cgpa(),
            'percentage': s.get_percentage(),
            'result_count': Result.objects.filter(student=s).count(),
        })
    return render(request, 'core/all_students_results.html', {
        'student_data': student_data,
        'departments': departments,
        'dept_filter': dept_filter,
    })

    
import json
from django.db.models import Avg, Count, Max, Min

@login_required
def teacher_analytics(request):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('dashboard')

    user = request.user
    if user.role == 'teacher':
        teacher = get_object_or_404(Teacher, user=user)
        subjects = Subject.objects.filter(teacher=teacher)
        results = Result.objects.filter(subject__in=subjects).select_related('student__user', 'subject')
    else:
        subjects = Subject.objects.all()
        results = Result.objects.all().select_related('student__user', 'subject')

    # --- Grade Distribution (Pie) ---
    grade_order = ['O', 'A+', 'A', 'B+', 'B', 'C', 'P', 'F', 'Ab']
    grade_counts = {g: 0 for g in grade_order}
    for r in results:
        if r.grade in grade_counts:
            grade_counts[r.grade] += 1
    grade_labels = [g for g in grade_order if grade_counts[g] > 0]
    grade_data   = [grade_counts[g] for g in grade_labels]

    # --- Pass vs Fail (Doughnut) ---
    pass_count = results.filter(grade__in=['O','A+','A','B+','B','C','P']).count()
    fail_count = results.filter(grade='F').count()
    ab_count   = results.filter(grade='Ab').count()

    # --- Subject-wise Average Marks (Bar) ---
    subject_avg = (
        results.values('subject__name', 'subject__code')
               .annotate(avg=Avg('marks_obtained'))
               .order_by('subject__code')
    )
    subj_labels = [f"{s['subject__code']}" for s in subject_avg]
    subj_avgs   = [round(s['avg'] or 0, 2) for s in subject_avg]
    subj_full   = [s['subject__name'] for s in subject_avg]

    # --- Student CGPA Distribution (Bar) ---
    students_qs = Student.objects.all() if user.role == 'admin' else \
                  Student.objects.filter(department=teacher.department)
    cgpa_buckets = {'0-4': 0, '4-5': 0, '5-6': 0, '6-7': 0, '7-8': 0, '8-9': 0, '9-10': 0}
    student_cgpa_list = []
    for s in students_qs:
        cgpa = s.get_cgpa()
        student_cgpa_list.append({'name': s.user.get_full_name() or s.user.username, 'cgpa': cgpa, 'roll': s.roll_number})
        if cgpa < 4:   cgpa_buckets['0-4'] += 1
        elif cgpa < 5: cgpa_buckets['4-5'] += 1
        elif cgpa < 6: cgpa_buckets['5-6'] += 1
        elif cgpa < 7: cgpa_buckets['6-7'] += 1
        elif cgpa < 8: cgpa_buckets['7-8'] += 1
        elif cgpa < 9: cgpa_buckets['8-9'] += 1
        else:           cgpa_buckets['9-10'] += 1

    # --- Marks Range Distribution (Histogram-style Bar) ---
    marks_ranges = {'0-20': 0, '21-40': 0, '41-60': 0, '61-75': 0, '76-90': 0, '91-100': 0}
    for r in results:
        if r.marks_obtained is None:
            continue
        m = r.marks_obtained
        if m <= 20:   marks_ranges['0-20'] += 1
        elif m <= 40: marks_ranges['21-40'] += 1
        elif m <= 60: marks_ranges['41-60'] += 1
        elif m <= 75: marks_ranges['61-75'] += 1
        elif m <= 90: marks_ranges['76-90'] += 1
        else:          marks_ranges['91-100'] += 1

    # --- Subject-wise Pass Rate (Horizontal Bar) ---
    subj_pass_data = []
    for subj in subjects:
        subj_results = results.filter(subject=subj)
        total = subj_results.count()
        if total == 0:
            continue
        passed = subj_results.filter(grade__in=['O','A+','A','B+','B','C','P']).count()
        subj_pass_data.append({
            'name': subj.code,
            'full': subj.name,
            'pass_rate': round((passed / total) * 100, 1),
            'total': total,
        })

    # --- Semester-wise Average (Line) ---
    sem_avg = (
        results.values('semester')
               .annotate(avg=Avg('marks_obtained'))
               .order_by('semester')
    )
    sem_labels = [f"Sem {s['semester']}" for s in sem_avg]
    sem_avgs   = [round(s['avg'] or 0, 2) for s in sem_avg]

    # --- Top 10 Students ---
    top_students = sorted(student_cgpa_list, key=lambda x: x['cgpa'], reverse=True)[:10]

    # --- Summary Stats ---
    stats = {
        'total_students': students_qs.count(),
        'total_results':  results.count(),
        'avg_marks':      round(results.aggregate(avg=Avg('marks_obtained'))['avg'] or 0, 2),
        'highest_marks':  results.aggregate(m=Max('marks_obtained'))['m'] or 0,
        'lowest_marks':   results.aggregate(m=Min('marks_obtained'))['m'] or 0,
        'pass_rate':      round((pass_count / results.count() * 100), 1) if results.count() > 0 else 0,
        'avg_cgpa':       round(sum(s['cgpa'] for s in student_cgpa_list) / len(student_cgpa_list), 2) if student_cgpa_list else 0,
    }

    context = {
        'stats': stats,
        'grade_labels':    json.dumps(grade_labels),
        'grade_data':      json.dumps(grade_data),
        'pass_count':      pass_count,
        'fail_count':      fail_count,
        'ab_count':        ab_count,
        'subj_labels':     json.dumps(subj_labels),
        'subj_avgs':       json.dumps(subj_avgs),
        'subj_full':       json.dumps(subj_full),
        'cgpa_labels':     json.dumps(list(cgpa_buckets.keys())),
        'cgpa_data':       json.dumps(list(cgpa_buckets.values())),
        'marks_labels':    json.dumps(list(marks_ranges.keys())),
        'marks_data':      json.dumps(list(marks_ranges.values())),
        'sem_labels':      json.dumps(sem_labels),
        'sem_avgs':        json.dumps(sem_avgs),
        'subj_pass_data':  subj_pass_data,
        'top_students':    top_students,
        'subjects':        subjects,
    }
    return render(request, 'core/teacher_analytics.html', context)

    # ===================== PDF RESULT DOWNLOAD =====================

from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.colors import HexColor


# ── Colour palette ────────────────────────────────────────────
PDF_PRIMARY   = HexColor('#6C3BF5')
PDF_DARK      = HexColor('#1A1A2E')
PDF_ACCENT    = HexColor('#F59E0B')
PDF_GREEN     = HexColor('#10B981')
PDF_RED       = HexColor('#EF4444')
PDF_BLUE      = HexColor('#3B82F6')
PDF_LIGHT_BG  = HexColor('#F3F4F8')
PDF_BORDER    = HexColor('#E2E4EF')
PDF_TEXT      = HexColor('#1F2937')
PDF_MUTED     = HexColor('#6B7280')
PDF_WHITE     = colors.white
PDF_HEADER_BG = HexColor('#0F0F1A')

GRADE_COLOURS = {
    'O':   (HexColor('#FEF3C7'), HexColor('#D97706')),
    'A+':  (HexColor('#EDE9FE'), PDF_PRIMARY),
    'A':   (HexColor('#DBEAFE'), PDF_BLUE),
    'B+':  (HexColor('#D1FAE5'), PDF_GREEN),
    'B':   (HexColor('#D1FAE5'), HexColor('#059669')),
    'C':   (HexColor('#F3F4F6'), PDF_MUTED),
    'P':   (HexColor('#F3F4F6'), HexColor('#9CA3AF')),
    'F':   (HexColor('#FEE2E2'), PDF_RED),
    'Ab':  (HexColor('#F3F4F6'), PDF_MUTED),
    '':    (PDF_LIGHT_BG, PDF_MUTED),
}


def _grade_colour(grade):
    return GRADE_COLOURS.get(grade, (PDF_LIGHT_BG, PDF_MUTED))


def _status_colour(marks, passing):
    if marks is None:
        return HexColor('#F59E0B'), HexColor('#FEF3C7')
    return (PDF_GREEN, HexColor('#D1FAE5')) if marks >= passing else (PDF_RED, HexColor('#FEE2E2'))


def _cgpa_colour(cgpa):
    if cgpa >= 8:  return PDF_GREEN
    if cgpa >= 6:  return PDF_PRIMARY
    if cgpa >= 4:  return PDF_ACCENT
    return PDF_RED


@login_required
def download_result_pdf(request, student_id):
    # Permission check
    if request.user.role == 'student':
        try:
            if request.user.student_profile.id != student_id:
                messages.error(request, 'Access denied.')
                return redirect('student_dashboard')
        except Exception:
            return redirect('student_dashboard')

    student = get_object_or_404(Student, id=student_id)
    results  = Result.objects.filter(student=student).select_related('subject').order_by('semester', 'subject__name')

    # ── Group by semester ─────────────────────────────────────
    from collections import defaultdict
    sem_map = defaultdict(list)
    for r in results:
        sem_map[r.semester].append(r)

    # ── Computed totals ───────────────────────────────────────
    cgpa       = student.get_cgpa()
    overall_pct= student.get_percentage()
    pass_count = sum(1 for r in results if r.grade in ('O','A+','A','B+','B','C','P'))
    fail_count = sum(1 for r in results if r.grade == 'F')

    # ── PDF setup ─────────────────────────────────────────────
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14*mm, rightMargin=14*mm,
        topMargin=12*mm,  bottomMargin=14*mm,
    )
    W = A4[0] - 28*mm   # usable width
    story = []

    # ── Styles ───────────────────────────────────────────────
    ss = getSampleStyleSheet()

    def ps(name, **kw):
        return ParagraphStyle(name, **kw)

    sty_inst_name = ps('inst', fontSize=18, textColor=PDF_WHITE,
                       fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=2)
    sty_inst_sub  = ps('isub', fontSize=9,  textColor=HexColor('#A78BFA'),
                       fontName='Helvetica', alignment=TA_CENTER, spaceAfter=0)
    sty_doc_title = ps('dtit', fontSize=13, textColor=PDF_ACCENT,
                       fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=0)
    sty_label     = ps('lbl',  fontSize=8,  textColor=PDF_MUTED,
                       fontName='Helvetica', alignment=TA_LEFT)
    sty_value     = ps('val',  fontSize=10, textColor=PDF_TEXT,
                       fontName='Helvetica-Bold', alignment=TA_LEFT)
    sty_sem_head  = ps('semh', fontSize=11, textColor=PDF_WHITE,
                       fontName='Helvetica-Bold', alignment=TA_LEFT)
    sty_footer    = ps('ftr',  fontSize=8,  textColor=PDF_MUTED,
                       fontName='Helvetica', alignment=TA_CENTER)
    sty_center    = ps('ctr',  fontSize=9,  textColor=PDF_TEXT,
                       fontName='Helvetica', alignment=TA_CENTER)

    # ════════════════════════════════════════════════════════
    # HEADER BANNER
    # ════════════════════════════════════════════════════════
    header_data = [[
        Paragraph('EduNova', sty_inst_name),
    ]]
    header_sub = [[
        Paragraph('Result Management System  ·  Academic Performance Report', sty_inst_sub),
    ]]
    doc_title = [[
        Paragraph('OFFICIAL MARK SHEET', sty_doc_title),
    ]]

    banner = Table(
        [
            [Paragraph('EduNova', sty_inst_name)],
            [Paragraph('Result Management System  ·  Academic Performance Report', sty_inst_sub)],
            [Paragraph('✦  OFFICIAL MARK SHEET  ✦', sty_doc_title)],
        ],
        colWidths=[W]
    )
    banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PDF_HEADER_BG),
        ('TOPPADDING',    (0,0), (-1,0), 14),
        ('BOTTOMPADDING', (0,2), (-1,-1), 14),
        ('TOPPADDING',    (0,1), (-1,1), 2),
        ('BOTTOMPADDING', (0,1), (-1,1), 2),
        ('TOPPADDING',    (0,2), (-1,2), 8),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('RIGHTPADDING',  (0,0), (-1,-1), 10),
        ('ROUNDEDCORNERS', [8]),
    ]))
    story.append(banner)
    story.append(Spacer(1, 5*mm))

    # ════════════════════════════════════════════════════════
    # STUDENT INFO GRID
    # ════════════════════════════════════════════════════════
    # ════════════════════════════════════════════════════════
    # STUDENT INFO GRID  (flat — no nested tables)
    # ════════════════════════════════════════════════════════
    full_name   = student.user.get_full_name() or student.user.username
    dept_name   = student.department.name if student.department else 'N/A'
    enroll_no   = student.enrollment_number
    roll_no     = student.roll_number
    semester_no = student.semester
    batch       = student.batch_year
    email       = student.user.email or 'N/A'

    def lbl(text):
        return Paragraph(text, ParagraphStyle('lbl', fontSize=7, textColor=PDF_MUTED,
                         fontName='Helvetica', alignment=TA_LEFT, spaceAfter=2))

    def val(text, colour=PDF_TEXT):
        return Paragraph(str(text), ParagraphStyle('val', fontSize=10, textColor=colour,
                         fontName='Helvetica-Bold', alignment=TA_LEFT))

    # Each cell = [label paragraph, value paragraph] stacked via inner single-col table
    def info_cell(label, value, colour=PDF_TEXT):
        t = Table([[lbl(label)], [val(value, colour)]],
                  colWidths=['100%'])
        t.setStyle(TableStyle([
            ('TOPPADDING',    (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING',   (0,0), (-1,-1), 0),
            ('RIGHTPADDING',  (0,0), (-1,-1), 0),
        ]))
        return t

    # Column widths for the 4-column info grid
    cw = [W*0.30, W*0.20, W*0.28, W*0.22]

    info_data = [
        [
            info_cell('STUDENT NAME',    full_name,   PDF_PRIMARY),
            info_cell('ROLL NUMBER',     roll_no,     PDF_DARK),
            info_cell('ENROLLMENT NO.',  enroll_no,   PDF_DARK),
            info_cell('BATCH YEAR',      batch,       PDF_DARK),
        ],
        [
            info_cell('DEPARTMENT',      dept_name,   PDF_DARK),
            info_cell('SEMESTER',        semester_no, PDF_DARK),
            info_cell('EMAIL',           email,       PDF_DARK),
            info_cell('TOTAL SUBJECTS',  results.count(), PDF_BLUE),
        ],
    ]

    info_table = Table(info_data, colWidths=cw)
    info_table.setStyle(TableStyle([
        ('BOX',           (0,0), (-1,-1), 0.75, PDF_BORDER),
        ('INNERGRID',     (0,0), (-1,-1), 0.5,  PDF_BORDER),
        ('TOPPADDING',    (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 9),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('RIGHTPADDING',  (0,0), (-1,-1), 10),
        ('BACKGROUND',    (0,0), (-1,-1), PDF_WHITE),
        ('ROWBACKGROUNDS',(0,0), (-1,-1), [PDF_WHITE, PDF_LIGHT_BG]),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('ROUNDEDCORNERS',[6]),
    ]))

    story.append(info_table)
    story.append(Spacer(1, 4*mm))

    # ════════════════════════════════════════════════════════
    # RESULTS TABLE — per semester
    # ════════════════════════════════════════════════════════
    col_w = [W*0.28, W*0.09, W*0.07, W*0.08, W*0.08, W*0.10, W*0.07, W*0.07, W*0.09, W*0.07]

    th_style = ParagraphStyle('th', fontSize=7.5, textColor=PDF_WHITE,
                               fontName='Helvetica-Bold', alignment=TA_CENTER)
    td_style = ParagraphStyle('td', fontSize=8,   textColor=PDF_TEXT,
                               fontName='Helvetica', alignment=TA_CENTER)
    td_left  = ParagraphStyle('tdl', fontSize=8,  textColor=PDF_TEXT,
                               fontName='Helvetica', alignment=TA_LEFT)
    td_bold  = ParagraphStyle('tdb', fontSize=8.5,textColor=PDF_TEXT,
                               fontName='Helvetica-Bold', alignment=TA_CENTER)

    headers = [
        Paragraph('SUBJECT', th_style),
        Paragraph('CODE',    th_style),
        Paragraph('CREDITS', th_style),
        Paragraph('INT',     th_style),
        Paragraph('EXT',     th_style),
        Paragraph('TOTAL',   th_style),
        Paragraph('MAX',     th_style),
        Paragraph('GRADE',   th_style),
        Paragraph('GP',      th_style),
        Paragraph('STATUS',  th_style),
    ]

    for sem_num in sorted(sem_map.keys()):
        sem_results = sem_map[sem_num]

        # Semester header row
        sem_total_marks = sum(r.marks_obtained or 0 for r in sem_results)
        sem_max_marks   = sum(r.subject.max_marks for r in sem_results)
        sem_credits     = sum(r.subject.credit_hours for r in sem_results)
        sem_gp_sum      = sum((r.grade_points or 0) * r.subject.credit_hours for r in sem_results)
        sem_sgpa        = round(sem_gp_sum / sem_credits, 2) if sem_credits else 0
        sem_pct         = round((sem_total_marks / sem_max_marks) * 100, 1) if sem_max_marks else 0

        sem_banner = Table([[
            Paragraph(f'  SEMESTER {sem_num}', sty_sem_head),
            Paragraph(
                f'SGPA: {sem_sgpa}   |   Percentage: {sem_pct}%   |   Credits: {sem_credits}',
                ParagraphStyle('sr', fontSize=9, textColor=PDF_ACCENT,
                               fontName='Helvetica-Bold', alignment=TA_RIGHT)
            ),
        ]], colWidths=[W*0.45, W*0.55])
        sem_banner.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), PDF_PRIMARY),
            ('TOPPADDING',    (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING',   (0,0), (-1,-1), 10),
            ('RIGHTPADDING',  (0,0), (-1,-1), 10),
            ('ROUNDEDCORNERS',[6]),
        ]))
        story.append(sem_banner)
        story.append(Spacer(1, 1.5*mm))

        # Table with header + data rows
        tbl_data = [headers]

        for r in sem_results:
            grade        = r.grade or ''
            g_bg, g_fg   = _grade_colour(grade)
            marks        = r.marks_obtained
            passing      = r.subject.passing_marks
            s_fg, s_bg   = _status_colour(marks, passing)

            grade_para = Paragraph(
                grade or 'N/A',
                ParagraphStyle('grd', fontSize=8.5, textColor=g_fg,
                               fontName='Helvetica-Bold', alignment=TA_CENTER)
            )
            status_txt = 'Pass' if marks and marks >= passing else ('Fail' if marks else 'Pending')
            status_para = Paragraph(
                status_txt,
                ParagraphStyle('sts', fontSize=8, textColor=s_fg,
                               fontName='Helvetica-Bold', alignment=TA_CENTER)
            )

            tbl_data.append([
                Paragraph(r.subject.name, td_left),
                Paragraph(r.subject.code, ParagraphStyle('cod', fontSize=7.5,
                          textColor=PDF_PRIMARY, fontName='Helvetica-Bold', alignment=TA_CENTER)),
                Paragraph(str(r.subject.credit_hours), td_style),
                Paragraph(str(r.internal_marks or '—'), td_style),
                Paragraph(str(r.external_marks or '—'), td_style),
                Paragraph(str(marks or '—'), td_bold),
                Paragraph(str(r.subject.max_marks), td_style),
                grade_para,
                Paragraph(str(r.grade_points or '—'), td_bold),
                status_para,
            ])

        # Semester subtotal row
        tbl_data.append([
            Paragraph('SEMESTER TOTAL', ParagraphStyle('st', fontSize=8.5,
                      textColor=PDF_PRIMARY, fontName='Helvetica-Bold', alignment=TA_LEFT)),
            Paragraph('', td_style),
            Paragraph(str(sem_credits), ParagraphStyle('stv', fontSize=8.5,
                      textColor=PDF_PRIMARY, fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph('', td_style),
            Paragraph('', td_style),
            Paragraph(f'{sem_total_marks:.1f}', ParagraphStyle('stv2', fontSize=8.5,
                      textColor=PDF_PRIMARY, fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph(str(sem_max_marks), td_style),
            Paragraph('', td_style),
            Paragraph(str(sem_sgpa), ParagraphStyle('stv3', fontSize=8.5,
                      textColor=PDF_ACCENT, fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph(f'{sem_pct}%', ParagraphStyle('stv4', fontSize=8.5,
                      textColor=PDF_GREEN if sem_pct >= 40 else PDF_RED,
                      fontName='Helvetica-Bold', alignment=TA_CENTER)),
        ])

        result_tbl = Table(tbl_data, colWidths=col_w, repeatRows=1)
        n = len(tbl_data)

        base_cmds = [
            # Header
            ('BACKGROUND',    (0,0),  (-1,0),   PDF_DARK),
            ('TEXTCOLOR',     (0,0),  (-1,0),   PDF_WHITE),
            ('FONTNAME',      (0,0),  (-1,0),   'Helvetica-Bold'),
            ('FONTSIZE',      (0,0),  (-1,0),   7.5),
            ('ALIGN',         (0,0),  (-1,0),   'CENTER'),
            ('TOPPADDING',    (0,0),  (-1,0),   7),
            ('BOTTOMPADDING', (0,0),  (-1,0),   7),
            # Data rows
            ('FONTSIZE',      (0,1),  (-1,-2),  8),
            ('TOPPADDING',    (0,1),  (-1,-2),  5),
            ('BOTTOMPADDING', (0,1),  (-1,-2),  5),
            ('LEFTPADDING',   (0,0),  (-1,-1),  5),
            ('RIGHTPADDING',  (0,0),  (-1,-1),  5),
            ('ALIGN',         (1,1),  (-1,-1),  'CENTER'),
            ('ALIGN',         (0,1),  (0,-1),   'LEFT'),
            # Grid
            ('BOX',           (0,0),  (-1,-1),  0.75, PDF_BORDER),
            ('INNERGRID',     (0,0),  (-1,-1),  0.4,  PDF_BORDER),
            # Alternating rows
            *[('BACKGROUND', (0,i), (-1,i), PDF_LIGHT_BG if i % 2 == 0 else PDF_WHITE)
              for i in range(1, n-1)],
            # Subtotal row
            ('BACKGROUND',    (0,n-1),(-1,n-1), HexColor('#EDE9FE')),
            ('TOPPADDING',    (0,n-1),(-1,n-1), 6),
            ('BOTTOMPADDING', (0,n-1),(-1,n-1), 6),
            ('LINEABOVE',     (0,n-1),(-1,n-1), 1.5, PDF_PRIMARY),
        ]
        result_tbl.setStyle(TableStyle(base_cmds))
        story.append(KeepTogether([result_tbl]))
        story.append(Spacer(1, 5*mm))

    # ════════════════════════════════════════════════════════
    # GRADE LEGEND TABLE
    # ════════════════════════════════════════════════════════
    legend_title = Paragraph('GRADE SCALE REFERENCE', ParagraphStyle(
        'lt', fontSize=8, textColor=PDF_MUTED, fontName='Helvetica-Bold',
        alignment=TA_CENTER))

    legend_pairs = [
        ('O — Outstanding', '90–100%', '10 GP'),
        ('A+ — Excellent',  '80–89%',  '9 GP'),
        ('A — Very Good',   '70–79%',  '8 GP'),
        ('B+ — Good',       '60–69%',  '7 GP'),
        ('B — Above Avg',   '50–59%',  '6 GP'),
        ('C — Average',     '45–49%',  '5 GP'),
        ('P — Pass',        '40–44%',  '4 GP'),
        ('F — Fail',        'Below 40%','0 GP'),
    ]
    legend_row = []
    for grade_text, pct_text, gp_text in legend_pairs:
        legend_row.append(
            Paragraph(f'<b>{grade_text}</b><br/><font color="#6B7280" size="7">{pct_text} · {gp_text}</font>',
                      ParagraphStyle('lg', fontSize=7.5, textColor=PDF_TEXT,
                                     fontName='Helvetica', alignment=TA_CENTER))
        )

    legend_tbl = Table(
        [[legend_title], [legend_row]],
        colWidths=[W],
    )
    # Inner legend row needs its own column widths
    legend_inner = Table([legend_row], colWidths=[W/8]*8)
    legend_inner.setStyle(TableStyle([
        ('BOX',           (0,0), (-1,-1), 0.5, PDF_BORDER),
        ('INNERGRID',     (0,0), (-1,-1), 0.5, PDF_BORDER),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND',    (0,0), (0,0),   HexColor('#FEF3C7')),  # O
        ('BACKGROUND',    (1,0), (1,0),   HexColor('#EDE9FE')),  # A+
        ('BACKGROUND',    (2,0), (2,0),   HexColor('#DBEAFE')),  # A
        ('BACKGROUND',    (3,0), (3,0),   HexColor('#D1FAE5')),  # B+
        ('BACKGROUND',    (4,0), (4,0),   HexColor('#D1FAE5')),  # B
        ('BACKGROUND',    (5,0), (5,0),   PDF_LIGHT_BG),         # C
        ('BACKGROUND',    (6,0), (6,0),   PDF_LIGHT_BG),         # P
        ('BACKGROUND',    (7,0), (7,0),   HexColor('#FEE2E2')),  # F
        ('ROUNDEDCORNERS',[4]),
    ]))

    story.append(Table([[legend_title]], colWidths=[W]))
    story.append(Spacer(1, 1.5*mm))
    story.append(legend_inner)
    story.append(Spacer(1, 4*mm))

    # ════════════════════════════════════════════════════════
    # SIGNATURE + FOOTER
    # ════════════════════════════════════════════════════════
    from django.utils import timezone
    generated_on = timezone.now().strftime('%d %B %Y, %I:%M %p')

    sig_tbl = Table([[
        Table([
            [Paragraph('_________________________', sty_center)],
            [Paragraph('Student Signature', ParagraphStyle('ss', fontSize=8,
             textColor=PDF_MUTED, fontName='Helvetica', alignment=TA_CENTER))],
        ], colWidths=[W*0.3]),
        Table([
            [Paragraph('_________________________', sty_center)],
            [Paragraph('Class Teacher', ParagraphStyle('ct', fontSize=8,
             textColor=PDF_MUTED, fontName='Helvetica', alignment=TA_CENTER))],
        ], colWidths=[W*0.3]),
        Table([
            [Paragraph('_________________________', sty_center)],
            [Paragraph('Principal / HOD', ParagraphStyle('pr', fontSize=8,
             textColor=PDF_MUTED, fontName='Helvetica', alignment=TA_CENTER))],
        ], colWidths=[W*0.3]),
    ]], colWidths=[W*0.33, W*0.34, W*0.33])
    sig_tbl.setStyle(TableStyle([
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
    ]))
    story.append(sig_tbl)
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width=W, thickness=0.5, color=PDF_BORDER))
    story.append(Spacer(1, 2*mm))

    footer_tbl = Table([[
        Paragraph(f'Generated on {generated_on}', sty_footer),
        Paragraph('EduNova Result Management System', ParagraphStyle(
            'fb', fontSize=8, textColor=PDF_PRIMARY,
            fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph('This is a computer-generated document.', sty_footer),
    ]], colWidths=[W*0.35, W*0.3, W*0.35])
    footer_tbl.setStyle(TableStyle([
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
    ]))
    story.append(footer_tbl)

    # ── Build & return ────────────────────────────────────────
    doc.build(story)
    buffer.seek(0)
    safe_name = f"result_{student.roll_number}_{student.user.get_full_name() or student.user.username}".replace(' ', '_')
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{safe_name}.pdf"'
    return response
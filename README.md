# 🎓 EduNova — Result Management System
### SaaS B2B Grade & Academic Performance Platform

A modern, full-stack Result Management System built with Django and a stunning dark UI. Designed for educational institutions with role-based access control for Admins, Teachers, and Students.

---

## ✨ Features

### 🔐 Role-Based Access
| Role | Capabilities |
|------|-------------|
| **Admin** | Full system control — manage users, departments, subjects, results, announcements |
| **Teacher** | Add/remove subjects, enter/edit student marks, view result analytics |
| **Student** | View results by semester, CGPA, percentage, grade distribution |

### 📊 Academic Intelligence
- **Automatic Grade Calculation** (O/A+/A/B+/B/C/P/F based on percentage)
- **SGPA per Semester** with credit-weighted calculation
- **CGPA Computation** across all semesters
- **Percentage Tracking** at subject and overall level
- **Pass/Fail Status** with configurable passing marks

### 🎨 Design Highlights
- Dark glassmorphism UI with neon purple/amber accents
- Smooth CSS animations & transitions
- Animated modal dialogs
- Progress bars with grade-based color coding
- Responsive sidebar with role-aware navigation
- Live clock in topbar
- Card hover effects with glow shadows

---

## 🚀 Quick Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Database Setup
```bash
python manage.py makemigrations core
python manage.py migrate
```

### 4. Load Demo Data
```bash
python setup_demo.py
```

### 5. Run Server
```bash
python manage.py runserver
```

### 6. Open Browser
```
http://127.0.0.1:8000/
```

---

## 🔑 Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Teacher | `teacher1` | `teacher123` |
| Teacher | `teacher2` | `teacher123` |
| Student | `student1` | `student123` |
| Student | `student2` | `student123` |
| Student | `student3` | `student123` |

---

## 📁 Project Structure

```
result_ms/
├── manage.py
├── requirements.txt
├── setup_demo.py              # Demo data loader
├── result_management/
│   ├── settings.py
│   └── urls.py
└── core/
    ├── models.py              # User, Student, Teacher, Subject, Result, etc.
    ├── views.py               # All views (admin/teacher/student)
    ├── urls.py
    ├── forms.py
    ├── admin.py
    └── templates/core/
        ├── base.html          # Master layout with sidebar
        ├── login.html         # Animated login page
        ├── admin_dashboard.html
        ├── teacher_dashboard.html
        ├── student_dashboard.html
        ├── manage_users.html
        ├── add_user.html
        ├── manage_subjects.html
        ├── manage_results.html
        ├── manage_departments.html
        ├── manage_announcements.html
        ├── all_students_results.html
        ├── student_result_detail.html
        └── edit_result.html
```

---

## 📐 Grade Scale (Auto-Calculated)

| Percentage | Grade | Grade Points |
|------------|-------|-------------|
| ≥ 90% | O (Outstanding) | 10 |
| ≥ 80% | A+ (Excellent) | 9 |
| ≥ 70% | A (Very Good) | 8 |
| ≥ 60% | B+ (Good) | 7 |
| ≥ 50% | B (Above Avg) | 6 |
| ≥ 45% | C (Average) | 5 |
| ≥ 40% | P (Pass) | 4 |
| < 40% | F (Fail) | 0 |

### CGPA Formula
```
CGPA = Σ(Grade Points × Credit Hours) / Σ(Credit Hours)
```

---

## 🛠 Tech Stack

- **Backend**: Django 4.2 (Python)
- **Database**: SQLite (dev) → PostgreSQL (prod)
- **Frontend**: HTML5 + CSS3 + Vanilla JS
- **Fonts**: Syne (headings) + DM Sans (body)
- **Icons**: Font Awesome 6
- **Auth**: Django's built-in auth with custom User model

---

## 🏭 Production Checklist

- [ ] Change `SECRET_KEY` in settings.py
- [ ] Set `DEBUG = False`
- [ ] Configure PostgreSQL database
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Run `python manage.py collectstatic`
- [ ] Use gunicorn + nginx for deployment

---

*Built as an internship project demonstrating SaaS B2B architecture with Django.*

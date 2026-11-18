# Newgate University Minna — Web-Based Student Final-Year Clearance System

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Django](https://img.shields.io/badge/Django-6.1-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

A web-based system that replaces the manual, paper-based final-year clearance 
process at Newgate University Minna with a digital, role-based, multi-unit 
approval workflow with real-time status tracking and email notifications.

---

## Table of Contents

- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [User Roles and Credentials](#user-roles-and-credentials)
- [How to Use the System](#how-to-use-the-system)
  - [Administrator](#1-administrator)
  - [Bursary Officer](#2-bursary-officer)
  - [Unit Officer](#3-unit-officer)
  - [Student](#4-student)
- [Clearance Workflow](#clearance-workflow)
- [HOD Routing Logic](#hod-routing-logic)
- [Deployment on Render](#deployment-on-render)
- [Project Structure](#project-structure)
- [Author](#author)

---

## Features

- Role-based access control (Student, Bursary, Unit Officer, Admin)
- Admin-managed academic sessions
- Sequential 5-unit digital approval workflow
- Intelligent HOD routing by student department
- Real-time per-unit clearance status tracking
- In-app notifications with bell counter
- Email notifications at every workflow stage
- PDF clearance certificate with NUM logo and approver details
- Admin dashboard with cohort-level reports
- Hosted on Render (free tier) with PostgreSQL

---

## System Requirements

- Python 3.10+
- pip
- Git
- A Gmail account with App Password enabled

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Famous005/newgate-clearance.git
cd newgate-clearance
```

### 2. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create environment file

Create a `.env` file in the project root:

```
SECRET_KEY=your-secret-key-here
DEBUG=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
```

To generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

Then set the role to admin:

```bash
python manage.py shell
```

```python
from accounts.models import CustomUser
u = CustomUser.objects.get(username='your-username')
u.role = 'admin'
u.save()
exit()
```

### 7. Run the development server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

---

## User Roles and Credentials

| Role | Description |
|---|---|
| `admin` | Manages sessions, units, users, and views reports |
| `bursary` | Confirms student payment to activate clearance |
| `unit_officer` | Approves or declines clearance at their assigned unit |
| `student` | Submits clearance request and tracks progress |

---

## How to Use the System

### 1. Administrator

**First-time setup (do this before any student uses the system):**

**Step 1 — Create Academic Session**
1. Log in as admin
2. Click **Sessions** in the sidebar
3. Click **Add New Session**
4. Enter the session name e.g. `2024/2025`
5. Tick **Set as active session**
6. Click **Add Session**

**Step 2 — Verify Clearance Units**
1. Click **Manage Units** in the sidebar
2. Confirm all 5 units are listed in order:
   - 1. Library
   - 2. Medical Unit
   - 3. Head of Department
   - 4. Dean of Faculty
   - 5. Academic Unit
3. Each unit must have an officer assigned

**Step 3 — Create Staff Accounts**
1. Go to Django Admin at `/admin/`
2. Create user accounts for each officer
3. Set the correct role (unit_officer or bursary)
4. For HOD officers, use the exact usernames:
   - `hod_cs` for Cyber Security and Software Engineering
   - `hod_ict` for Artificial Intelligence and Information Technology

**Ongoing — Monitor Clearance Progress**
1. Click **Dashboard** to see cleared, pending, and declined counts
2. Click **All Requests** to filter by status
3. Click **Reports** for department-level breakdown

---

### 2. Bursary Officer

**Step 1 — Log in**
Go to `http://your-domain/` and log in with your bursary credentials.

**Step 2 — Confirm student payment**
1. Click **Confirm Payments** in the sidebar
2. The **Pending Confirmation** table shows students who have submitted
   a clearance request and are waiting for payment confirmation
3. Verify the student's payment receipt physically or in the payment system
4. Click **Confirm** next to the student's name
5. Click **OK** in the confirmation dialog
6. The student's clearance workflow starts immediately
7. The Library officer is notified automatically

**Step 3 — Track confirmations**
The **Already Confirmed** table shows all students whose payments have
been confirmed, with their current clearance status.

---

### 3. Unit Officer

**Step 1 — Log in**
Go to `http://your-domain/` and log in with your officer credentials.

**Step 2 — Check your queue**
1. Click **My Queue** in the sidebar
2. The table shows all students whose clearance is currently at your unit
3. You will also receive an email and an in-app notification for each
   new request

**Step 3 — Review a request**
1. Click **Review** next to a student's name
2. Read the student's details carefully:
   - Full name and matric number
   - Department
   - Session
3. Check your unit's records for this student:
   - Library: check for outstanding book loans or fines
   - Medical: check for outstanding medical obligations
   - HOD: check for academic irregularities
   - Dean: endorse departmental clearance
   - Academic Unit: perform final check

**Step 4 — Approve or Decline**

To approve:
1. Add an optional remark in the remarks box
2. Click **Approve**
3. The system automatically forwards the request to the next unit
4. The student is notified by email and in-app

To decline:
1. Type a clear reason in the remarks box (required)
2. Click **Decline**
3. The student is notified with your reason
4. The student must resolve the issue and contact the administrator
   to reactivate the request

**Step 5 — View history**
Click **History** in the sidebar to see all past approvals and declines.

---

### 4. Student

**Step 1 — Create an account**
1. Go to `http://your-domain/`
2. Click **Create an account**
3. Fill in your details:
   - First name and last name
   - Email address
   - Matric number (e.g. NUM/2021/CS/001)
   - Phone number
   - Department — select from the dropdown
   - Username and password
4. Click **Create Account**
5. You will be logged in automatically

**Step 2 — Pay your clearance fee**
Before submitting, pay the clearance fee at the Bursary physically.
Keep your receipt. The system starts only after the Bursary confirms
your payment.

**Step 3 — Submit clearance request**
1. Click **Submit Clearance** in the sidebar
2. Confirm your details are correct
3. Select your academic session from the dropdown
4. Click **Submit Clearance Request**
5. You will see your status page showing all 5 units as pending

**Step 4 — Track your progress**
1. Click **My Status** in the sidebar at any time
2. You will see the approval progress for each unit:
   - 🕐 Amber clock — pending
   - ✅ Green tick — approved with date and officer name
   - ❌ Red cross — declined with reason
3. The progress bar shows your overall percentage
4. You will receive email and in-app notifications at each stage

**Step 5 — Download your certificate**
1. When all 5 units approve, your status changes to **Cleared**
2. A **Download Clearance Certificate** button appears
3. Click it to download a PDF certificate containing:
   - Your full details
   - Session year
   - Date cleared
   - All 5 unit approvals with officer names and dates
4. Present this certificate to the Academic Registry

---

## Clearance Workflow

```
Student submits request
        ↓
Bursary confirms payment
        ↓
  1. Library
        ↓
  2. Medical Unit
        ↓
  3. Head of Department  ←── routed by department
        ↓
  4. Dean of Faculty
        ↓
  5. Academic Unit
        ↓
  Certificate generated
```

If any unit declines, the workflow stops and the student is notified.
The administrator can reset the request after the issue is resolved.

---

## HOD Routing Logic

The system automatically routes clearance requests to the correct HOD
based on the student's department:

| Department | Routed to |
|---|---|
| Cyber Security Science | HOD — Computer Science School |
| Software Engineering | HOD — Computer Science School |
| Artificial Intelligence | HOD — ICT School |
| Information Technology | HOD — ICT School |

---

## Deployment on Render

### Step 1 — Create a Render account
Go to `https://render.com` and sign up with your GitHub account.

### Step 2 — Create a PostgreSQL database
1. Click **New** → **PostgreSQL**
2. Name: `newgate-clearance-db`
3. Plan: **Free**
4. Click **Create Database**
5. Copy the **Internal Database URL**

### Step 3 — Create a Web Service
1. Click **New** → **Web Service**
2. Connect your GitHub repository: `Famous005/newgate-clearance`
3. Fill in:
   - Name: `newgate-clearance`
   - Runtime: **Python**
   - Build Command: `./build.sh`
   - Start Command: `gunicorn newgate_clearance.wsgi`
4. Click **Advanced** and add these environment variables:

| Key | Value |
|---|---|
| `SECRET_KEY` | generate a new one |
| `DEBUG` | `False` |
| `DATABASE_URL` | paste from step 2 |
| `EMAIL_HOST_USER` | your Gmail |
| `EMAIL_HOST_PASSWORD` | your App Password |
| `ALLOWED_HOSTS` | `your-app-name.onrender.com` |

5. Click **Create Web Service**

### Step 4 — Update settings for production
See the production settings section below.

---

## Project Structure

```
newgate-clearance/
├── accounts/                  # User management app
│   ├── models.py              # CustomUser model
│   ├── views.py               # Login, register, dashboard, profile
│   ├── forms.py               # Login, register, profile forms
│   └── urls.py                # Account URLs
├── clearance/                 # Core clearance app
│   ├── models.py              # Unit, ClearanceRequest, Approval,
│   │                          # AcademicSession, Notification
│   ├── views.py               # All clearance views and workflow engine
│   ├── urls.py                # Clearance URLs
│   ├── notifications.py       # Email and in-app notification helpers
│   └── templatetags/
│       └── clearance_tags.py  # Unread notification count tag
├── templates/
│   ├── base.html              # Master layout with NUM branding
│   ├── accounts/              # Login, register, profile templates
│   └── clearance/             # All clearance templates
├── static/
│   └── images/
│       └── num-logo.webp      # NUM official logo
├── newgate_clearance/
│   ├── settings.py            # Django settings
│   ├── urls.py                # Root URL config
│   └── wsgi.py                # WSGI config for Render
├── .env                       # Environment variables (not committed)
├── .gitignore                 # Git ignore rules
├── build.sh                   # Render build script
├── Procfile                   # Gunicorn process file
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## Author

**Badamasi Sherif Audu**
Assistant Lecturer — Software Development and Cybersecurity
Faculty of Computing and Information Technology
Newgate University Minna

BTech Cyber Security Science (Second Class Upper) — FUT Minna, 2019
MTech Cyber Security Science — FUT Minna

GitHub: [Famous005](https://github.com/Famous005)
Email: Badamasisherif12@gmail.com

---

*Newgate University Minna — Explore to Excel*
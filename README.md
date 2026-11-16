# College ERP System

An enterprise-grade, multi-role Academic & Institutional Resource Planning (ERP) platform built with Python, Django, and PostgreSQL. Designed to streamline academic administration, faculty workload, student tracking, finance ledgers, and accreditation compliance within higher education institutions.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-college--erp--xwqr.onrender.com-success?style=for-the-badge&logo=render&logoColor=white)](https://college-erp-xwqr.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-3.1.1-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon%20Serverless-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.tech/)
[![Hosting](https://img.shields.io/badge/Hosting-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://render.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

---

## 🌐 Live Demo

The application is deployed and publicly accessible for evaluation:

* **Live Application:** [https://college-erp-xwqr.onrender.com](https://college-erp-xwqr.onrender.com)
* **Hosting:** [Render](https://render.com/) (Web Service)
* **Database:** [Neon Serverless PostgreSQL](https://neon.tech/)

> [!NOTE]
> **Important Evaluation Notes:**
> * **Cold Start Delay:** Because this deployment runs on Render's free tier, the web service automatically spins down after periods of inactivity. If the service is asleep, the first request may take approximately **45–60 seconds** to wake up. Subsequent requests will respond normally.
> * **Demo Data & Sandbox Environment:** This project is intended solely for demonstration and evaluation purposes. Demo data may be periodically modified, refreshed, or reset.
> * **Security & Privacy:** The provided demo accounts are shared publicly. **Please do not enter real personal, confidential, or sensitive institutional information.**

---

## 🔑 Demo Login Credentials

You can test each of the six role dashboards using the following pre-configured demo accounts:

| Role | Email | Password | Landing Dashboard |
| :--- | :--- | :--- | :--- |
| **Admin** | [admin@admin.com](mailto:admin@admin.com) | `admin123` | `/admin/home/` |
| **Principal** | [principal@college.edu](mailto:principal@college.edu) | `principal123` | `/principal/home/` |
| **Faculty** | [dr.sharma@college.edu](mailto:dr.sharma@college.edu) | `faculty123` | `/staff/home/` |
| **Student** | [aryan.kapoor@student.edu](mailto:aryan.kapoor@student.edu) | `student123` | `/student/home/` |
| **Finance Officer** | [finance@college.edu](mailto:finance@college.edu) | `finance123` | `/finance/home/` |
| **Accreditation Coordinator** | [accreditation@college.edu](mailto:accreditation@college.edu) | `accreditation123` | `/accreditation/home/` |

> [!IMPORTANT]
> These are shared demo credentials intended for evaluation and testing. Please ensure you solve the interactive Google reCAPTCHA checkbox on the login page when signing in.

---

## 📑 Table of Contents

- [Live Demo](#-live-demo)
- [Demo Login Credentials](#-demo-login-credentials)
- [1. Project Overview](#1-project-overview)
- [2. Problem Statement](#2-problem-statement)
- [3. Objectives](#3-objectives)
- [4. System Architecture](#4-system-architecture)
- [5. Role-Based Access Control (RBAC)](#5-role-based-access-control-rbac)
- [6. Module-Wise Functionality](#6-module-wise-functionality)
- [7. Technology Stack](#7-technology-stack)
- [8. Database Design & Models](#8-database-design--models)
- [9. Repository Structure](#9-repository-structure)
- [10. Local Development Setup (Windows)](#10-local-development-setup-windows)
- [11. Environment Variable Configuration](#11-environment-variable-configuration)
- [12. Deployment Architecture (Render + Neon)](#12-deployment-architecture-render--neon)
- [13. Automated Testing & Verification](#13-automated-testing--verification)
- [14. Future Enhancements](#14-future-enhancements)
- [15. License & Attribution](#15-license--attribution)

---

## 1. Project Overview

The **College ERP System** provides a centralized, data-driven management system for modern colleges and universities. Unlike basic academic record managers, this ERP integrates executive institutional oversight, role-segregated student and faculty administration, attendance audits, continuous internal evaluation (CIE), fee accounts with pure-Python PDF receipt generation, alumni lifecycle tracking, and accreditation data aggregation (NAAC SSR & NBA Outcome-Based Education).

---

## 2. Problem Statement

Higher education institutions often suffer from fragmented software silos:
* Academic departments track attendance and internal marks in isolated spreadsheets.
* Administrative offices struggle to maintain accurate faculty workloads, research records, and student progression data.
* Finance offices spend excessive time reconciling fee payments, waivers, and issuing verifiable payment receipts.
* Accreditation committees (NAAC and NBA) face cumbersome manual data collection drills across years of dispersed institutional records.
* Graduating students are often deleted or orphaned from the system, losing connection with the institutional alumni network.

---

## 3. Objectives

* **Role Isolation:** Provide dedicated interfaces for six institutional roles without data leaks.
* **Academic Integrity:** Enforce non-destructive student progression and prevent tampering of finalized marks.
* **Financial Precision:** Automate fee ledger calculations (`Net Fee = Total Fee - Scholarship - Concession`) with instantaneous balance recalculation and downloadable binary PDF receipts.
* **Accreditation Readiness:** Automatically aggregate academic metrics for NAAC (Criteria 1–7) and NBA Program Outcomes (POs) / Course Outcomes (COs).
* **Alumni Continuity:** Transition graduating students into a searchable Alumni Registry rather than deleting historical records.
* **Production Resilience:** Support zero-downtime serverless database hosting (Neon PostgreSQL) and containerized deployment (Render) with complete local development fallback.

---

## 4. System Architecture

```text
       +----------------------------------------------------------------+
       |               Client Web Browsers (Desktop & Mobile)           |
       +----------------------------------------------------------------+
                                       | HTTPS
                                       v
       +----------------------------------------------------------------+
       |                     Render Reverse Proxy (SSL)                 |
       +----------------------------------------------------------------+
                                       | HTTP (X-Forwarded-Proto)
                                       v
       +----------------------------------------------------------------+
       |              Gunicorn WSGI Application Server                  |
       +----------------------------------------------------------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
+------------------------------------+   +------------------------------------+
|         WhiteNoise Engine          |   |          Django Framework          |
|    - 550+ Bundled Static Assets    |   |    - Role Routing Middleware       |
|    - Caching & Gzip Compression    |   |    - RBAC Decorators (6 Roles)     |
+------------------------------------+   |    - Pure-Python PDF Generator     |
                                         |    - NAAC / NBA Sync Engine        |
                                         +------------------------------------+
                                                           |
                                                           v
                                         +------------------------------------+
                                         |        Database Abstraction        |
                                         |   (dj-database-url / psycopg2)     |
                                         +------------------------------------+
                                            /                              \
                      (Production: DATABASE_URL)             (Local Dev: Fallback)
                                          /                                  \
                                         v                                    v
                       +-----------------------------+          +---------------------------+
                       |    Neon PostgreSQL Cloud    |          |    Local SQLite Engine    |
                       |    - Managed Serverless     |          |    - db.sqlite3           |
                       |    - Enforced SSL Mode      |          |    - Offline Testing      |
                       +-----------------------------+          +---------------------------+
```

---

## 5. Role-Based Access Control (RBAC)

The application implements strict role-based access control across **six primary institutional roles**:

| Role | Access Level | Primary Responsibilities |
| :--- | :--- | :--- |
| **1. Administrator** | Full Administrative Control | Academic setup (Courses, Subjects, Sessions), Student & Faculty directory management, document verification, system audit logs, and alumni records. |
| **2. Principal** | Executive Institutional Visibility | High-level metrics, Student-Faculty Ratio (SFR), finance collections vs. dues, placement analytics, NAAC/NBA readiness, department breakdowns, and audit trails. |
| **3. Faculty / Staff** | Academic Operations | Daily student attendance marking, attendance correction requests with audit trails, continuous internal marks entry, marks finalization lock, and research portfolio curation. |
| **4. Student** | Self-Service Portal | Personal attendance tracking, semester examination results, fee account ledger, instant PDF receipt download, and portfolio management. |
| **5. Finance Officer** | Financial Administration | Course fee structures, student fee ledgers, recording online/cash payments, fee refund processing, staff payroll, college expenses, and financial reporting. |
| **6. Accreditation Coordinator** | Compliance & Quality Assurance | NAAC Self-Study Report (SSR) metric verification and live synchronization, NBA programs, Program Outcomes (POs), Course Outcomes (COs), and CO-PO mapping matrix. |

---

## 6. Module-Wise Functionality

### 🏛️ Executive Principal Dashboard
* Institution-wide statistical KPIs: Total enrolled students, active faculty, and Student-to-Faculty Ratio (SFR).
* Real-time financial summary: Collected fees, outstanding dues, and institutional net balance.
* Research contributions tracker: Faculty publications, patents filed, and FDPs conducted.
* NAAC readiness progress bar and centralized institutional report generator.

### 👥 Student & Faculty Management (Admin)
* Filterable Student Registry: Search by name, roll number, admission number, department, session, semester, and active/alumni/inactive status.
* Non-destructive deletion: Deactivating a student or faculty marks them `Inactive` or `Resigned` to preserve historical academic and financial ledgers.
* Faculty assignment: Assign faculty members to subjects, departments, and academic sessions.

### 🎓 Academic & Examination Engine (Faculty)
* **Attendance Workflow:** Faculty select academic session, subject, and section; student rosters are populated automatically for quick attendance logging.
* **Attendance Auditing:** Post-dated corrections record the reason and timestamp in audit logs.
* **Marks Finalization:** Once test and practical marks are finalized by the faculty member, they are locked from further editing unless unlocked by an administrator.

### 💳 Finance & Fee Ledger (Finance Officer)
* **Dual-Entry Ledger:** Calculates `Net Fee = Total Fee - Scholarship - Concession`.
* **Automated Status:** Balances automatically transition between `Unpaid`, `Partially Paid`, and `Paid`.
* **Pure-Python PDF Receipt Generator:** Generates compliant, downloadable PDF 1.4 receipts directly in memory without requiring external native dependencies. Includes student details, transaction reference, amount in words, and authorized signatures.

### 🏅 Accreditation Compliance (NAAC & NBA)
* **NAAC SSR Automation:** Auto-synchronization engine that scans current student enrollments, faculty counts, research papers, and placements to populate NAAC metrics.
* **NBA OBE Mapping:** Define Program Outcomes (PO1–PO12), Course Outcomes (CO1–CO6), and map their correlation levels (1: Low, 2: Medium, 3: High).

### 🎓 Alumni Management
* **Graduation Workflow:** Active students transition to alumni status upon graduation without data deletion.
* **Alumni Registry:** Tracks graduation year, degree awarded, current company, designation, city, higher education institutions, and notable alumni status.

---

## 7. Technology Stack

* **Backend:** Python 3.11.9, Django 3.1.1
* **Database:** PostgreSQL (Neon Serverless via `psycopg2-binary`) with SQLite fallback for offline local development
* **Application Server:** Gunicorn 20.0.4
* **Static Assets:** WhiteNoise 5.2.0 (Gzip & Manifest Caching)
* **PDF Generation:** Pure-Python PDF 1.4 stream generator (`pdf_generator.py`)
* **Security & Auth:** Django Auth System, CSRF protection, Google reCAPTCHA v2 with institutional test token support
* **Frontend:** Bootstrap 4, AdminLTE 3, FontAwesome 5, jQuery, DataTables

---

## 8. Database Design & Models

```text
CustomUser (AbstractUser)
  ├── Admin (1-to-1)
  ├── Principal (1-to-1)
  ├── Staff (1-to-1) ───────────► Subject (Assigned Faculty)
  ├── Student (1-to-1)
  │     ├── StudentFeeAccount ──► FeePayment (Receipts, Transaction ID)
  │     ├── StudentResult ──────► Subject
  │     ├── AttendanceReport ───► Attendance ──► Subject & Session
  │     └── AlumniProfile (1-to-1)
  ├── FinanceOfficer (1-to-1)
  └── AccreditationCoordinator (1-to-1)

Accreditation Entities:
  ├── NAACCriterion (1–7) ──────► NAACMetricData
  └── NBAProgram ───────────────► CourseOutcome ──► COPOMapping ──► ProgramOutcome
```

---

## 9. Repository Structure

```text
College_ERP/
├── .github/
│   └── workflows/
│       └── django.yml              # GitHub Actions CI workflow
├── college_management_system/
│   ├── __init__.py
│   ├── asgi.py
│   ├── context_processors.py       # Global context processors (reCAPTCHA)
│   ├── settings.py                 # Dual-mode production & local settings
│   ├── urls.py                     # Root URL routing
│   └── wsgi.py                     # WSGI entrypoint for Gunicorn
├── main_app/
│   ├── migrations/                 # Schema migrations (0001, 0002, 0003)
│   ├── static/                     # Bundled AdminLTE, Bootstrap, CSS, JS
│   ├── templates/                  # Role-segregated UI templates
│   │   ├── accreditation_template/ # NAAC & NBA views
│   │   ├── finance_template/       # Fee accounts, ledgers, payroll
│   │   ├── hod_template/           # Admin dashboard, students, staff, alumni
│   │   ├── main_app/               # Base layout, login, sidebar
│   │   ├── principal_template/     # Executive dashboard & reports
│   │   ├── staff_template/         # Faculty attendance & marks
│   │   └── student_template/       # Student portal & fee views
│   ├── admin.py
│   ├── EmailBackend.py             # Case-insensitive email authentication backend
│   ├── forms.py                    # Extended student & staff forms
│   ├── middleware.py               # RBAC & login enforcement middleware
│   ├── models.py                   # Complete institutional data model
│   ├── pdf_generator.py            # In-memory binary PDF receipt engine
│   ├── views.py                    # Login & authentication handlers
│   ├── hod_views.py                # Admin & Alumni views
│   ├── staff_views.py              # Faculty views
│   ├── student_views.py            # Student views
│   ├── principal_views.py          # Principal views
│   ├── finance_views.py            # Finance views
│   └── accreditation_views.py      # Accreditation views
├── media/                          # Default demo avatar assets
├── .gitignore                      # Excludes db.sqlite3, static/, .env
├── manage.py
├── Procfile                        # Render start command
├── render-build.sh                 # Render build script
├── requirements.txt                # Production dependencies
├── runtime.txt                     # python-3.11.9
├── seed_demo_data.py               # Fictional institutional data seeder
├── seed_system.py                  # Baseline 6-role seeder
└── verify_all_roles.py             # 25-test integration & RBAC suite
```

---

## 10. Local Development Setup (Windows)

### Prerequisites
* Python 3.11.x installed and added to PATH
* Git for Windows

### Step-by-Step Instructions

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/varshini200502/college-erp.git
   cd college-erp
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Apply database migrations:**
   ```powershell
   python manage.py migrate
   ```

5. **Populate demo data (Optional):**
   ```powershell
   python seed_system.py
   python seed_demo_data.py
   ```

6. **Start the local server:**
   ```powershell
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000` in your browser.

---

## 11. Environment Variable Configuration

Create a `.env` file in the project root for custom local configurations (optional, as defaults allow immediate local development out-of-the-box):

```env
# General
SECRET_KEY=your-custom-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database (Leave blank to use local SQLite)
DATABASE_URL=postgresql://user:password@neon-host/neondb?sslmode=require

# Google reCAPTCHA (Optional in local dev; falls back to testing token)
RECAPTCHA_SITE_KEY=your-recaptcha-site-key
RECAPTCHA_SECRET_KEY=your-recaptcha-secret-key

# Email (Optional)
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-app-password
```

---

## 12. Deployment Architecture (Render + Neon)

### A. Neon Managed PostgreSQL Setup
1. Sign up for a free account at [neon.tech](https://neon.tech).
2. Create a new project (e.g., `college-erp-db`).
3. Copy the PostgreSQL connection string from your Neon dashboard:
   ```text
   postgresql://[user]:[password]@[neon-host]/neondb?sslmode=require
   ```

### B. Render Web Service Deployment
1. Sign in to [render.com](https://render.com) using your GitHub account.
2. Click **New +** $\rightarrow$ **Web Service**.
3. Select your repository: `varshini200502/college-erp`.
4. Configure the service:
   * **Runtime:** `Python 3`
   * **Branch:** `main`
   * **Build Command:**
     ```bash
     ./render-build.sh
     ```
   * **Start Command:**
     ```bash
     gunicorn college_management_system.wsgi:application
     ```
   * **Instance Type:** `Free`
5. Under **Environment Variables**, configure:
   * `DATABASE_URL`: *(Your Neon PostgreSQL connection string)*
   * `SECRET_KEY`: *(A strong random 50+ character string)*
   * `DEBUG`: `False`
   * `RECAPTCHA_SITE_KEY`: *(Your Google reCAPTCHA v2 site key)*
   * `RECAPTCHA_SECRET_KEY`: *(Your Google reCAPTCHA v2 secret key)*
   * `PYTHON_VERSION`: `3.11.9`
6. Click **Create Web Service**.

> [!NOTE]
> **Free-Tier Operational Behavior:**
> * **Render Inactivity Sleep:** Free web services spin down after 15 minutes of inactivity. When accessed after sleep, the first request takes ~45–60 seconds to wake up.
> * **Ephemeral Disk:** Any runtime file uploads (e.g., custom avatar photos uploaded by users) are stored on Render's ephemeral filesystem and reset on redeploy. Static files (CSS, JS, AdminLTE) are pre-compiled and served permanently via WhiteNoise.
> * **Neon Auto-Suspend:** Neon free tier compute suspends after 5 minutes of inactivity and wakes up in ~1–2 seconds upon an incoming query.

---

## 13. Automated Testing & Verification

The repository includes an automated integration and RBAC test suite (`verify_all_roles.py`).

To run the verification suite:
```powershell
python verify_all_roles.py
```

### Verified Test Results (25 Passed, 0 Failed):
* **Authentication & Dashboard Rendering:**
  * Admin, Principal, Faculty, Student, Finance, and Accreditation dashboards load with HTTP 200.
  * Decommissioned HR role redirected cleanly to login.
* **Role-Based Access Control (RBAC):**
  * Student blocked from `/admin/home/`, `/principal/home/`, `/finance/home/`, `/accreditation/home/` (HTTP 302).
  * Faculty blocked from `/finance/home/` (HTTP 302).
  * Principal granted cross-module executive visibility to `/principal/finance/` and `/principal/accreditation/` (HTTP 200).
* **Financial Ledger Verification:**
  * Dual-entry ledger recalculation verified (`Net: ₹87,000`, `Paid: ₹50,000`, `Due: ₹37,000`, Status: `Partially Paid`).
* **Accreditation Sync Engine:**
  * Auto-sync engine executes and populates criterion metrics.
* **NBA Attainment Engine:**
  * Course Outcomes (COs) and Program Outcomes (POs) verified with correlation matrix.

---

## 14. Future Enhancements

Features planned for future iterations:
- [ ] Integration with cloud object storage (AWS S3 or Cloudinary) for persistent user uploads on serverless hosting.
- [ ] Automated SMS / WhatsApp gateway integration for attendance alerts to guardians.
- [ ] Biometric & RFID machine integration for campus gate attendance synchronization.
- [ ] Online student payment gateway integration (Razorpay / Stripe) alongside the existing ledger.

---

## 15. License & Attribution

This project is open-source software licensed under the **[MIT License](LICENSE)**.

### Upstream Project Attribution
This application is extended from the open-source foundational project [College-ERP](https://github.com/Ansarimajid/College-ERP) originally created by Owonubi Job Sunday and modified by Ansari Majid. All original MIT copyright notices have been preserved in accordance with the MIT License terms.

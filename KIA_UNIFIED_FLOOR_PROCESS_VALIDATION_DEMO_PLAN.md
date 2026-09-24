# KIA – UNIFIED FLOOR PROCESS VALIDATION DEMO
## Executive Summary & Technical Delivery Plan

---

### 1. Overview & Architecture

The **KIA Unified Floor Process Validation System** consolidates the seven legacy floor process applications into a modern, unified web application built using **Python 3.14**, **Django 6.1**, **SQL Server architecture mapping**, **Bootstrap 5**, and **Chart.js**.

The system includes an **Ultra-Premium Split-Screen Login Page**, **Interactive Password Eye Toggle**, **Admin Password Viewer**, **Request Management & Interlocks**, **Admin Live Controls (Pause, Stop, Pass to Next, Assign)**, and **Operator Status Interlock Screens**.

---

### 2. Login Page Design & Admin Password Visibility

- **Split-Screen Login Interface (`/login/`)**:
  - **Left Showcase**: High-tech factory background image, 4 feature cards (*Sequential Process Control*, *Real-time Validation*, *Production Tracking*, *Role Based Access*), console product rendering, bottom process node pipeline (`P10` → `P51`), and *"KIA | INDIA ANANTAPUR PLANT"*.
  - **Right Sign In Card**: Language dropdown (`🌐 English v`), Red Kia emblem, `Welcome Back` heading, Employee ID & Password inputs, **Interactive Show/Hide Password Eye Button**, `[Login →]` blue submit button, **Authorized Personnel Only** notice, and Kia manufacturing plant building photo footer.
- **Admin Password Viewer (`/users/`)**:
  - In User Management, administrators can view all employee account details including **Employee ID**, **Assigned Station**, and **Password** with an interactive **Show/Hide Eye Toggle** (`toggleUserPassword()`).

---

### 3. Registered Demo Accounts & Admin Credentials

| Employee ID | Full Name | Role | Station Access | Password (Admin Visible) |
| :--- | :--- | :---: | :---: | :---: |
| **`admin`** | Administrator | **ADMIN** | **All Processes (P10–P51)** | `password` |
| **`EMP010`** | P10 Operator | **OPERATOR** | **P10 – Assembly #10** | `password` |
| **`EMP030`** | P30 Operator | **OPERATOR** | **P30 – Assembly #30** | `password` |
| **`EMP040`** | P40 Operator | **OPERATOR** | **P40 – Assembly #40** | `password` |
| **`EMP050`** | P50 Operator | **OPERATOR** | **P50 – Assembly #50** | `password` |
| **`EMP060`** | P60 Operator | **OPERATOR** | **P60 – Assembly #60** | `password` |
| **`EMP041`** | Garnish Operator | **OPERATOR** | **P41 – Garnish** | `password` |
| **`EMP051`** | RRCVR Operator | **OPERATOR** | **P51 – RRCVR** | `password` |

---

### 4. Running the Application Locally

1. **Start Django Server**:
   ```bash
   cd d:\projects\kia\demo
   .\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
   ```
2. **Access Links**:
   - **Login Page**: [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/)
   - **Admin Dashboard**: [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)
   - **User Management & Passwords**: [http://127.0.0.1:8000/users/](http://127.0.0.1:8000/users/)
   - **Logout**: [http://127.0.0.1:8000/logout/](http://127.0.0.1:8000/logout/)

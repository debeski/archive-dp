<div align="center">
<pre>
 █████╗ ██████╗  ██████╗██╗  ██╗██╗██╗   ██╗███████╗
██╔══██╗██╔══██╗██╔════╝██║  ██║██║██║   ██║██╔════╝
███████║██████╔╝██║     ███████║██║██║   ██║█████╗  
██╔══██║██╔══██╗██║     ██╔══██║██║╚██╗ ██╔╝██╔══╝  
██║  ██║██║  ██║╚██████╗██║  ██║██║ ╚████╔╝ ███████╗
╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝
                                                    
</pre>
</div>

> **IMPORTANT:** Only files required for deployment are **start.py**, **start_deps.ps1** (for windows), **start_deps.sh** (for linux/macOS), **secrets.enc**, and **compose.yml**. Everything else is included inside the **Docker Images**.

# ♾ OVERVIEW

A comprehensive document management platform for educational/research institutes, featuring centralized mail archiving with specialized workflows for director and ministerial decrees. The system organizes institutional correspondence, policy directives, and administrative decisions with role-based access controls, advanced search capabilities, and audit trails for complete document lifecycle management.

---

## 🔐 Key Features

  - **User Management System** - Staff administration, Linear Permissions, Activity log, Profile Management..

  - **Documents Management** - Different Types of Mail and Decrees Archive System ..

  - **Advanced Reporting** - Dynamic dropdowns, Excel exports, Calculated summaries..

  - **Security** - SOPS encryption, Django Auth, Container Network Isolation..

  - **Backups** - Automated database backup service.

---

## 💻  Platform Support

  ✅ Linux (amd64 & arm64)

  ✅ macOS (arm64)

  ✅ Windows (**WSL 2+ Required**)

---

## 📝 Core Requirements:

  - **Python 3.11+** required (for the universal start script)
  - Docker Compose 2.30.0+ required
  - Must first encrypt your .env file into secrets.enc
  - Private Key (SOPS_AGE_KEY) is required for every Deployment or Update
  - Always use **start.py** - 'docker compose up' will fail due to missing env vars

> There is no docker method to decrypt files and inject them into container environment variables on launch AFAIK, without having the .env file physically exposed on the disk. Hence the need for a decryption script. The start script decrypts the secrets.enc file and injects the secrets directly inside the containers environments **without the need to use .env file**, making the app secrets and deployment process more secure and private.

---

## ⚙️ Technologies Used

**Docker Compose [Containerization]**
- **Container Base OS (Linux Debian)**
  - **Backend Language [Python 3.13]**
    - Django 5.2.8 (Web Framework)
    - gunicorn 23.0.0 (WSGI Server)
    - django-tables2 2.8.0 (Table Views)
    - django-crispy-forms 2.5.0 (Form Rendering)
    - django-filter 25.2 (Query Filters)
    - celery 5.4.0 (Background Tasks)
    - redis 7.1.0 (cache server interpreter)
    - django-redis 6.0.0 (Redis Adapter)
    - psycopg2-binary 2.9.11 (PostgreSQL Adapter)

  - **Frontend Components**
    - Django 5.2.8 (Web Framework)
    - HTML + CSS + JavaScript (Django Templates)
    - Bootstrap 5 (Visual Framework)
    - AJAX (Real-time Requests to Server)
    - Flatpickr (Date Picker)
    - Plotly (Interactive Charts)

- **Database Service**
  - PostgreSQL 17 (Main Database)

- **Cache Service**
  - Redis 7 (Cache Server)

- **Tasks Service**
  - Celery 5.4.0 (Background Tasks)

- **Reverse Proxy Service**
  - nginx (Reverse Proxy)

- **pgAdmin Service**
  - pgAdmin 4 (Database GUI)

- **Backup Service**
  - PostgreSQL 17 (Database Periodic Backup Service)

---

# 🚀 Deployment Instructions

## First-Time Deployment

### 1. Set Up Your Environment Variables

First, create your `.env` file using the provided `secrets.enc` as a reference template. The encrypted file contains the structure of all required environment variables for the application to function.

> .env file MUST NOT contain any quotes, comments, spaces, or empty lines. it must follow this exact structure

    VAR=VAL
    VAR=VAL
    VAR=VAL
    ....

---

### 2. Encrypt Your Environment File

You may use the **included SOPS Compose** to encrypt your `.env` file:

> If you do so, **note** that you need to either execute inside the docker container using Docker-desktop, Portainer, etc. or append the prefix "docker exec -it sops bash" to each command in your terminal. `this guide assumes you are executing directly inside that container.`

- Generate a new age key if you don't have one
```bash
age-keygen -o /secrets/.key
# Generated .key file will be inside "./.sops/secrets/" by default.
```

- Place your `.env` file inside `./.sops/secrets/`

- Export your PUBLIC_KEY from .key into session environment

**Linux/macOS:**
```bash
PUBLIC_KEY=$(age-keygen -y /secrets/.key)
# or go old school and use a Text editor, copy the part after public_key: , and export it to environment
```

**Windows (PowerShell):**
```powershell
$PUBLIC_KEY = age-keygen -y /secrets/.key
# same as above
```

- Encrypt your .env file
```bash
sops -e -a "$PUBLIC_KEY" --input-type dotenv --output /secrets/secrets.enc /secrets/.env
```

- Move `secrets.enc` to the application directory replacing the one already there.

> **⚠️ Important**: Keep your `.key` file secure! It contains both your public key for encryption, and your private key needed for decryption. Alternatively, open the file with a Text editor, copy its content, store it somewhere safe, and destroy the file.

---

## App-Update Deployment

### 3. Deploy the Application

Before deploying, you need to provide your **Private Key** (SOPS_AGE_KEY) *from your `.key` file* using **one** of these methods:

#### **Option A: Command-line** (Recommended)
```bash
python start.py 'your_private_key_here'
# or with flags
python start.py -k 'your_private_key_here' --key='your_private_key_here'
```

#### **Option B: Environment variable**
```bash
export SOPS_AGE_KEY="AGE-SECRET-KEY-your_private_key_here"  # Linux/macOS
$env:SOPS_AGE_KEY="AGE-SECRET-KEY-your_private_key_here"    # Windows PowerShell
```

#### **Option C: Interactive prompt**
The script will prompt you if the key is invalid or not provided.

> **Tip:** Use the same method as during initial setup. The key always starts with `AGE-SECRET-KEY-...`

---

The script will automatically:
- Detect your operating system (Linux, macOS, Windows)
- Install dependencies based on your OS
- Decrypt `secrets.enc` using your provided key
- Start all Docker containers with proper configuration
- Verify the application is running and healthy

---

## 🔄 Updating Secrets

To modify or add environment variables later:
1. **Private Key:** exec inside sops container `export SOPS_AGE_KEY="your_private_key"`
2. **Decrypt:** exec inside sops container `sops -d --input-type dotenv --output-type dotenv /secrets/secrets.enc > /secrets/.env`
3. **Edit:** `nano ./secrets/.env`
4. **Public Key:** exec inside sops container `age-keygen -y /secrets/.key`
5. **Encrypt:** exec inside sops container `sops -e -a "$PUBLIC_KEY" --input-type dotenv --output /secrets/secrets.enc /secrets/.env`
6. **Move:** `mv /secrets/secrets.enc ../secrets.enc`
7. **Re-deploy:** `python start.py 'your_private_key'`

---

# ⚙️ Configuration Notes

* If you are familiar with Python Scripting Language You can edit the configuration directly inside `start.py` (e.g., paths, SOPS version).
* Common application settings are set via environment variables in `compose.yml` (e.g., BASE_URL, ALLOWED_HOSTS, DEBUG_STATUS, etc.). Modify these to match your desired setup for deployment. `note: setting DEBUG_STATUS to False automatically enables SSL related options.`
* Sensitive application settings are de-crypted from secrets.enc and injected directly inside the containers environments upon deployment using start.py script. `therefore conventional deployment using docker is not possible unless you are willing to inject all the required environment variables manually before deployment.`
* **Do not modify the start.py script unless you know what you are doing.**

---

## 📜 Version History

| Version  | Changes |
|----------|---------|
| v0.1.0  | • Initial deployment: Django project initialized with Dockerfile and initial git commit |
| v0.1.5  | • Main app structure established<br>• Added django-tables2, crispy-forms, django-filter<br>• Frontend added Bootstrap 5, flatpickr, Plotly.js<br>• Basic views, pagination, tables, forms, filters implemented |
| v0.1.8  | • Advanced search features reused and adjusted<br>• Report function improved<br>• Downloader and excel_export implemented |
| v0.1.13 | • Reports section finalized with dynamic dropdowns<br>• Index page reworked<br>• Models fully integrated<br>• Client and server-side validation improved<br>• Number fields allow backslash '\' input (max 2) |
| v0.2.4  | • Optimized reports backend<br>• Fixed circular Import issue in user system app<br>• Rewrote production compose file for stability<br>• Added network isolation<br>• Improved DB migrations<br>• Added SOPS encryption<br>• Switched to start.sh for deployment (Linux/Debian only) |
| v0.2.6  | • Upgraded start.sh for multi-OS support (WSL required for Windows)<br>• Improved error handling |
| v0.2.7  | • Stable release |
| v0.2.8  | • Added a start.ps1 "Powershell 7 script" for an easy setup on Windows without the need for WSL or GIT BASH |
| v0.2.10 | • Updated user system app to v1.3.2<br>• Improved compatibility for the ps1 script |
| v0.2.13 | • Updated start script to start.py for cross-platform compatibility<br> • Improved error handling<br>• Created a small standalone app to bridge TWAIN scanners on the client side with the Archive Django App Backend |
| v0.3.2  | • Added 'Regulation' (اللوائح) model and section<br>• Integrated Regulations into Reports and Sidebar<br>• Added Excel export for Regulations |
| v0.3.10 | • Dependent dropdowns for Affiliate → SubAffiliate in forms<br>• Conditional "Save & Add More" buttons (new records only)<br>• Real-time duplicate detection with generic AJAX endpoint<br>• Permission-based UI controls (view, manage, download)<br>• Modal popup to view registered affiliate sub-departments<br>• Refactored populate.py with default data plus unified type/name handling for models<br>• Fixed messages alert auto-close behavior |
| v0.4.4 | • Switched to Generating Version History using MCP <br>• Refactored direct model imports to `apps.get_model()` across tables, forms, filters, and views<br>• Enhanced forms responsive layout (Incoming/Outgoing)<br>• Added `ProtectedError` handling and disabled "in-use" sub-affiliates<br>• Added stats to sub-affiliate popup<br>• Automated dependency installation (Linux/Mac/Win) via `start_deps` scripts<br>• Improved `start.py` UI and service status monitoring<br>• Docker Compose optimization (restart policies, volume cleanup) |
| v0.4.8 | • **Feature: Mail Rerouting**: Added rerouting logic for `Incoming` mail (fields: `is_rerouted`, `rerouted_from`), including tab-based filtering (All/Rerouted) and dynamic form visibility<br>• **UI Consistency**: Refactored `Decree` list tabs to match `Incoming` style and logic<br>• **Excel Export Fix**: Resolved `AffiliateDepartment` FK export issue in `fetcher.py` and restored correct field mapping in `utils.py`<br>• **Permissions**: Refined UI permission checks for sidebar and tables (view vs manage sections) |
| v0.4.11 | • **Feature: Annotated Reply**: Added workflow to attach replies (scanned notes/files) directly to Incoming mail via new "Reply" action and Modal<br>• **Form & Layout**: Merged Rerouting fields into single row, added conditional validation, and fixed responsive layout for Sub-affiliate selection<br>• **UI**: Updated page titles for Ministry branding |
| v0.5.3 | • **Core Restructure**: Merged `Regulation` into `Decree` model (types: Decree/Regulation) and repurposed `Regulation` model to `Report` (types: Report/Publication)<br>• **Feature Rename**: Renamed legacy Reports feature to `gen_report` (Yearly Reports)<br>• **UI/UX Overhaul**: Redesigned `Decree` and `Report` forms with improved layouts and field positioning<br>• **Dynamic Forms**: Implemented real-time field visibility toggling for Regulation type (hiding Category)<br>• **Tab Navigation**: Implemented consistent, harmonious two-level tab system (Type -> Category) for Decrees and pluralized terminology<br>• **Security**: Added protection for first two `DecreeCategory` items (hidden in manage UI) and implemented server-side validation to block direct URL edits for protected Departments and Categories |
| v0.5.6  | • **Navigation**: Implemented smart "Back" button logic in detail views (uses HTTP Referrer) and fixed navigation loops (ignoring Edit/Add referrers)<br>• **Decrees**: Added reverse status alerts (showing "Cancels/Withdraws Decree X") and fixed Category persistence bug when switching Types<br>• **Search & Filters**: Fixed "Clear" button and Search submission to preserve active tabs (Type/Category/Rerouted) across Decree, Report, and Incoming lists |
| v0.5.9  | • **UI/UX**: Refined `Decree Detail` page with a cleaner layout, removing redundant headers/buttons and optimizing metadata display<br>• **PDF Preview**: Enhanced PDF viewer integration by hiding toolbar/navpanes for a "scroll-read" experience across all document types<br>• **Sidebar**: Integrated responsive PDF preview sidebar for Desktop (d-lg-block) with side-by-side download actions, while maintaining standard mobile accessibility |
| v0.5.13 | • **Feature: Multi-PDF Preview**: Implemented tabbed previews for `Decrees` (Decree/Attachment) and `Incoming` mail (Original/Annotated Response) to toggle documents instantly<br>• **Feature: Response Metadata**: Added `Response Date` to Incoming details and updated verification tooltips<br>• **Logic Update**: Refined `gen_report` with strict Type filtering (Decrees/Reports) and Reroute status checks<br>• **Quality of Life**: Enhanced `Duplicate Check` to respect document types (e.g. separate checks for Decrees vs Regulations) |
| v0.6.2  | • **Index Dashboard Overhaul**: Integrated `Internal` and `Report` models into main stats/charts<br>• **Granular Analytics**: Added detailed breakdown for Decrees (Decisions/Regulations), Reports (Reports/Publications), and Incoming (Normal/Rerouted)<br>• **UI/UX**: Redesigned Dashboard to 5-column layout for better density and added dynamic "Type" labels to Recent Activity table |
| v0.6.4  | • **Feature: Interactive Tutorial**: Implemented context-aware onboarding tour for Dashboard, Lists, and Forms using Driver.js, with aggressive RTL positioning fixes<br>• **Dashboard Refinement**: Consolidated statistics into a streamlined 3-column key card layout (Decrees, Correspondence, Reports) for better readability |
| v0.6.7  | • **Refactor**: Extracted Sidebar into a standalone reusable pip package (`micro-sidebar`) for modularity<br>• **Deployment**: Integrated `micro-sidebar` into build process (requirements.txt) and baked it into the Docker image<br>• **UX/UI**: Fixed tooltip persistence on small screens, refined sidebar resizing logic, and enabled internal scrolling for better accessibility on smaller viewports |
| v0.6.12 | • **Core Architecture**: Implemented full project-wide data isolation based on `Department Group` (Tenant), enabling multi-department support with strict data separation<br>• **Refactor**: Unified `Internal` and `Incoming` models to use `users.Department` for all internal destinations<br>• **Automation**: Implemented auto-detection and field hiding for user Department across all forms (Incoming/Outgoing/Internal)<br>• **Security**: Added "Edit Lock" logic 🔒 for Departments and Governments with related entries (Incoming/Internal/Decree) to preserve data integrity<br>• **Fixes**: Resolved `IntegrityError` in Outgoing and `TypeError` in auxiliary forms by unified user context handling |
| v0.7.0 | • **Mail Rerouting**: Fixed visibility of `is_rerouted` and `rerouted_from` in Incoming forms, allowing proper rerouting designation with auto-clear logic<br>• **Permissions**: Resolved permission logic preventing scoped users (Departments) from managing authorized Section Models (`manage_sections`) |
| v0.7.6 | • **Refactor**: Renamed `department_group` to `scope` project-wide for unified terminology<br>• **Fixes**: Resolved `AttributeError` on saving blank dates and fixed scope assignment for new documents<br>• **Dashboards**: Fixed scoped user chart data visualization<br>• **Chart Fix**: Resolved RTL text overlap issues by decoupling chart container direction and forcing LTR SVG rendering with end-anchored text<br>• **Analytics**: Split `Decree` (Decisions/Regulations) and `Report` (Reports/Publications) into distinct data series in the main dashboard chart for granular tracking<br>• **UI Tweak**: Repositioned chart modebar to top-left for better accessibility |
| v0.7.10 | • **CSS Architecture**: Refactored monolithic `style.css` into modular components (`main`, `titlebar`, `tables`, `dropdowns`, `pagination`, `charts`) with a unified glassmorphism theme<br>• **Users App Redesign**: Completely modernized `login.html` (glassmorphism cards, removed legacy SVG) and `manage_users.html` (responsive tables), syncing styles with the main app to resolve titlebar layout conflicts<br>• **Dashboard & UX**: Merged charts/tables for density, fixed RTL chart legends, and applied "soft pill" design to sidebar items<br>• **Fixes**: Eliminated persistent tooltips, FOUC during sidebar load, and layout shifts |
| v0.8.0 | • **User Activity Log**: Added `Scope` filter for admins and fixed sorting reset bug on filtering<br>• **Filter Logic**: Implemented global sort persistence across all document filters (Decree, Incoming, etc.)<br>• **App-wide Fix**: Resolved `TypeError` in filter initialization and ensured `model` parameter persistence for Section filters<br>• **UX**: Improved "Clear" button logic to preserve sort order |
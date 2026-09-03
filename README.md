# Visitor Management System (SQL Server edition)

[![Version](https://img.shields.io/badge/version-4.3.0-blue.svg)](https://github.com/meytiii/visitor_management_sqlserver)
[![Python](https://img.shields.io/badge/python-3.9%2B-green.svg)](https://www.python.org/)
[![SQL Server](https://img.shields.io/badge/SQL%20Server-2019%2B-red.svg)](https://www.microsoft.com/sql-server)
[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)

Visitor management desktop application with a Microsoft SQL Server backend. Built for multi-workstation environments that require shared access, role-based accounts, and centralized logging.

> Note: This repository is the active release. The previous SQLite-based project is [archived and unsupported](https://github.com/meytiii/visitor_management_edu).

---

## Changes from the SQLite edition

- Multi-client access: Multiple workstations connect to a central SQL Server instance without database file locks.
- Security: SQL Server authentication with support for encrypted connections.
- Native maintenance: Works with standard SQL Server backup and restore tools.
- Data migration: Includes a migration script to copy existing records from SQLite.

---

## Requirements

- Windows 10, Windows 11, or Windows Server
- Microsoft SQL Server 2019 or later (including SQL Server Express)
- ODBC Driver 18 for SQL Server (or SQL Server Native Client 11.0)
- Python 3.9 or later (if running from source)

---

## Installation and setup

### 1. Prepare SQL Server

Create a database (such as `VisitorSystem`) and a SQL login (such as `VisitorAppUser`) with `SELECT`, `INSERT`, `UPDATE`, and `DELETE` permissions. The application creates required tables automatically on first startup.

### 2. Configure the application

Update the connection settings in `config.py`:

```python
SQL_SERVER = r"10.15.2.26\visitormanager"
SQL_DATABASE = "VisitorSystem"
SQL_USER = "VisitorAppUser"
SQL_PASSWORD = "password"
SQL_DRIVER = "{ODBC Driver 18 for SQL Server}"
```

### 3. Run from source

```bash
git clone https://github.com/meytiii/visitor_management_sqlserver.git
cd visitor_management_sqlserver
pip install -r requirements.txt
python main.py
```

### 4. Build a standalone executable

```bash
pyinstaller --noconsole --onefile --icon=assets/app_icon.ico --add-data "assets;assets" main.py
```

---

## Data migration from SQLite

If you are upgrading from the SQLite version, use `assets/migrate_old_DB.py` to copy visitor records, user accounts, and audit logs into SQL Server.

### Running the migration

1. Confirm your existing SQLite database file is accessible. By default, it is located at:
   `C:\ProgramData\VisitorSystem\visitor_log.db`

2. Ensure SQL Server is running and the target database exists.

3. Open `assets/migrate_old_DB.py` and verify connection details:

```python
SQL_SERVER = r"10.15.2.26\visitormanager"
SQL_USER = "VisitorAppUser"
SQL_PASSWORD = "password"
SQL_DATABASE = "VisitorSystem"
CONN_STR = f"DRIVER={{SQL Server Native Client 11.0}};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USER};PWD={SQL_PASSWORD};Trusted_Connection=no;"
```

4. Run the script:

```bash
python assets/migrate_old_DB.py
```

### Migration details

The migration script:
- Recreates the target tables (`visitors`, `users`, and `audit_log`) in SQL Server.
- Reads data from the SQLite database file.
- Copies existing rows into SQL Server.
- Skips duplicate usernames in the `users` table.
- Retains original timestamp and Shamsi date fields.

> Important: The script drops existing tables in the target database before importing. If you have already recorded new entries in SQL Server, back up your database before running the script.

### Verification

Open the application to search for migrated records, or query the database directly in SQL Server Management Studio.

---

## Tech stack

| Layer | Tool |
|---|---|
| Language | Python 3.9+ |
| Interface | Tkinter, ttkbootstrap |
| Database | Microsoft SQL Server |
| Database driver | pyodbc (ODBC Driver 18 / Native Client 11.0) |
| Persian calendar | jdatetime |
| Printing | pywin32 (`win32print`, `win32ui`) |
| Data analysis and charts | pandas, matplotlib |
| Persian and Arabic text | arabic-reshaper, python-bidi |
| Image processing | Pillow |

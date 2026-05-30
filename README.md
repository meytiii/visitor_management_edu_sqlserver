# 🛡️ Visitor Management System – SQL Server Edition

[![Version](https://img.shields.io/badge/version-4.1.2-blue.svg)](https://github.com/meytiii/visitor_management_sqlserver)
[![Python](https://img.shields.io/badge/python-3.9%2B-green.svg)](https://www.python.org/)
[![SQL Server](https://img.shields.io/badge/SQL%20Server-2019%2B-red.svg)](https://www.microsoft.com/sql-server)
[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)

**Centralised, high‑performance version with Microsoft SQL Server backend.**  
Designed for multi‑station environments, improved security, and enterprise‑grade reliability.

> 🚨 **This is the actively developed version.**  
> The old SQLite‑based version is [archived and no longer supported](https://github.com/meytiii/visitor_management_edu).

---

## ✨ What's New in SQL Server Edition

- **Central database** – Multiple workstations can connect to the same SQL Server instance.
- **Better concurrency** – No more file‑locking issues; true client‑server architecture.
- **Enhanced security** – SQL Server authentication, encrypted connections (optional).
- **Higher performance** – Optimised indexes, stored procedures (coming soon).
- **Easier backups** – Use SQL Server native backup tools.
- **Migration tool included** – Convert your old SQLite data to SQL Server with one script.

---

## 📋 Requirements

- Windows 7/10/11 (or Windows Server)
- SQL Server 2019 or newer (Express edition works fine)
- SQL Server ODBC Driver – **ODBC Driver 18 for SQL Server** (or Native Client 11.0)
- Python 3.9+ (only if running from source)

---

## 🚀 Installation & Setup

### 1. Prepare SQL Server

Create a database (e.g., `VisitorSystem`) and a SQL login (e.g., `VisitorAppUser`) with `INSERT`, `SELECT`, `UPDATE`, `DELETE` permissions on the tables. The application will create the tables automatically on first run.

### 2. Configure the Application

Edit `config.py` and update the SQL connection parameters:

```python
SQL_SERVER = r"10.15.2.26\visitormanager"
SQL_DATABASE = "VisitorSystem"
SQL_USER = "VisitorAppUser"
SQL_PASSWORD = "Herasat1405@"
SQL_DRIVER = "{ODBC Driver 18 for SQL Server}"
```

### 3. Run from Source
```bash
git clone https://github.com/meytiii/visitor_management_sqlserver.git
cd visitor_management_sqlserver
pip install -r requirements.txt
python main.py
```

### 4. Build Standalone EXE
```bash
pyinstaller --noconsole --onefile --icon=assets/app_icon.ico --add-data "assets;assets" main.py
```

### 🔄 Migrate Old Data (from SQLite)

If you have been using the old SQLite‑based version, you can migrate all existing records (visitors, users, audit logs) to the new SQL Server database using the provided migration script.

Migration Script: migrate_old_DB.py

Place the script in a folder like migration_tool/ inside the repository.
You can download it directly from the repository at:

migrate_old_DB.py(https://github.com/meytiii/visitor_management_sqlserver/blob/main/migration_tool/migrate_old_DB.py)

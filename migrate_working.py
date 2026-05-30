import sqlite3
import pyodbc
import os
from datetime import datetime

# ========== CONFIGURATION ==========
SQLITE_DB_PATH = r"C:\ProgramData\VisitorSystem\visitor_log.db"

SQL_SERVER = r"10.15.2.26\visitormanager"
SQL_USER = "VisitorAppUser"
SQL_PASSWORD = "Herasat1405@"
SQL_DATABASE = "VisitorSystem"

CONN_STR = (
    f"DRIVER={{SQL Server Native Client 11.0}};"
    f"SERVER={SQL_SERVER};"
    f"DATABASE={SQL_DATABASE};"
    f"UID={SQL_USER};"
    f"PWD={SQL_PASSWORD};"
    "Trusted_Connection=no;"
)
# ===================================

def drop_and_create_tables(sql_cursor):
    tables = ['visitors', 'users', 'audit_log']
    for table in tables:
        sql_cursor.execute(f"IF OBJECT_ID('{table}', 'U') IS NOT NULL DROP TABLE {table}")
    sql_cursor.commit()
    print("Dropped existing tables.")

    # Create visitors table
    sql_cursor.execute("""
        CREATE TABLE visitors (
            id INT IDENTITY(1,1) PRIMARY KEY,
            visitor_name NVARCHAR(200) NOT NULL,
            national_id NVARCHAR(20) NOT NULL,
            employee_to_meet NVARCHAR(200) NOT NULL,
            department NVARCHAR(200) NOT NULL,
            entry_time DATETIME2 NOT NULL,
            shamsi_date NVARCHAR(20),
            exit_time NVARCHAR(10),
            created_by NVARCHAR(100)
        )
    """)
    
    # Create users table
    sql_cursor.execute("""
        CREATE TABLE users (
            id INT IDENTITY(1,1) PRIMARY KEY,
            username NVARCHAR(100) UNIQUE NOT NULL,
            password NVARCHAR(255) NOT NULL,
            role NVARCHAR(50) NOT NULL,
            full_name NVARCHAR(200)
        )
    """)
    
    # Create audit_log table
    sql_cursor.execute("""
        CREATE TABLE audit_log (
            id INT IDENTITY(1,1) PRIMARY KEY,
            shamsi_date NVARCHAR(20) NOT NULL,
            shamsi_time NVARCHAR(20) NOT NULL,
            event_type NVARCHAR(100) NOT NULL,
            user_name NVARCHAR(100),
            visitor_id INT,
            visitor_name NVARCHAR(200),
            national_id NVARCHAR(20),
            employee_to_meet NVARCHAR(200),
            department NVARCHAR(200),
            details NVARCHAR(MAX),
            created_at NVARCHAR(50)
        )
    """)
    sql_cursor.commit()
    print("Created tables with appropriate sizes.")

def migrate_visitors(sqlite_conn, sql_cursor):
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT visitor_name, national_id, employee_to_meet, department, entry_time, shamsi_date, exit_time, created_by FROM visitors")
    rows = sqlite_cursor.fetchall()
    if not rows:
        print("No visitors data.")
        return
    
    count = 0
    for row in rows:
        entry_time_str = row[4]
        dt = None
        if entry_time_str and isinstance(entry_time_str, str):
            try:
                if len(entry_time_str) >= 19:
                    entry_time_str = entry_time_str[:19]
                dt = datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        sql_cursor.execute("""
            INSERT INTO visitors (visitor_name, national_id, employee_to_meet, department, entry_time, shamsi_date, exit_time, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (row[0], row[1], row[2], row[3], dt, row[5], row[6], row[7]))
        count += 1
        if count % 1000 == 0:
            sql_cursor.commit()
            print(f"  Inserted {count} visitors...")
    sql_cursor.commit()
    print(f"✅ Migrated {count} rows to 'visitors'")

def migrate_users(sqlite_conn, sql_cursor):
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT username, password, role, full_name FROM users")
    rows = sqlite_cursor.fetchall()
    if not rows:
        print("No users data.")
        return
    
    count = 0
    skipped = 0
    for row in rows:
        username = row[0]
        if not username:
            skipped += 1
            continue
            
        sql_cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
        if sql_cursor.fetchone()[0] > 0:
            skipped += 1
            continue
            
        sql_cursor.execute("""
            INSERT INTO users (username, password, role, full_name)
            VALUES (?, ?, ?, ?)
        """, (username, row[1], row[2], row[3]))
        count += 1
    sql_cursor.commit()
    print(f"✅ Migrated {count} rows to 'users' (skipped {skipped} duplicates)")

def migrate_audit_log(sqlite_conn, sql_cursor):
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT shamsi_date, shamsi_time, event_type, user_name, visitor_id, visitor_name, national_id, employee_to_meet, department, details, created_at FROM audit_log")
    rows = sqlite_cursor.fetchall()
    if not rows:
        print("No audit_log data.")
        return
    
    count = 0
    for row in rows:
        sql_cursor.execute("""
            INSERT INTO audit_log (shamsi_date, shamsi_time, event_type, user_name, visitor_id, visitor_name, national_id, employee_to_meet, department, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)
        count += 1
        if count % 1000 == 0:
            sql_cursor.commit()
            print(f"  Inserted {count} audit_log...")
    sql_cursor.commit()
    print(f"✅ Migrated {count} rows to 'audit_log'")

def main():
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"❌ SQLite file not found: {SQLITE_DB_PATH}")
        return
    print(f"✅ SQLite file found: {SQLITE_DB_PATH}")
    
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    
    print("Connecting to SQL Server...")
    try:
        sql_conn = pyodbc.connect(CONN_STR, autocommit=False)
        sql_cursor = sql_conn.cursor()
        print("✅ Connected.")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    drop_and_create_tables(sql_cursor)
    
    print("\nMigrating visitors...")
    migrate_visitors(sqlite_conn, sql_cursor)
    
    print("\nMigrating users...")
    migrate_users(sqlite_conn, sql_cursor)
    
    print("\nMigrating audit_log...")
    migrate_audit_log(sqlite_conn, sql_cursor)
    
    sqlite_conn.close()
    sql_conn.close()
    print("\n🎉 Migration completed successfully!")

if __name__ == "__main__":
    main()
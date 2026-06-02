import os
import sys
import re
from datetime import datetime
from tkinter import messagebox, filedialog
import arabic_reshaper
from bidi.algorithm import get_display
import config
import sqlite3
import database

def validate_national_id(nid):
    if not nid:
        return False, "کد ملی نمی‌تواند خالی باشد"
    
    if not nid.isdigit():
        return False, "کد ملی باید فقط شامل اعداد باشد"
    
    if len(nid) != 10:
        return False, "کد ملی باید ۱۰ رقمی باشد"
    
    if len(set(nid)) == 1:
        return False, "کد ملی معتبر نیست (همه ارقام یکسان)"

    try:
        control_digit = int(nid[9])
        
        sum_val = 0
        for i in range(9):
            sum_val += int(nid[i]) * (10 - i)
        
        remainder = sum_val % 11
        
        if remainder < 2:
            valid = (remainder == control_digit)
        else:
            valid = ((11 - remainder) == control_digit)
        
        if not valid:
            return False, "کد ملی وارد شده معتبر نیست"
        
        return True, ""
        
    except Exception as e:
        return False, f"خطا در اعتبارسنجی کد ملی: {str(e)}"

def validate_persian_name(name):
    import re
    
    persian_pattern = re.compile(r'^[\u0600-\u06FF\uFB8A\u067E\u0686\u06AF\u200C\u200F\.\s]+$')
    
    english_pattern = re.compile(r'^[A-Za-z\s\.]+$')
    
    name = name.strip()
    
    if not name or len(name) < 2:
        return False, "نام باید حداقل ۲ کاراکتر باشد"
    
    has_letter = any(c.isalpha() for c in name)
    if not has_letter:
        return False, "نام باید شامل حروف باشد"
    if not (persian_pattern.match(name) or english_pattern.match(name)):
        return False, "نام باید فقط شامل حروف فارسی/عربی یا انگلیسی باشد"
    
    return True, ""

def validate_numeric(text):
    if text == "":
        return True
    
    if not text.isdigit():
        return False
    
    if len(text) > 10:
        return False
    
    return True

def make_farsi(text):
    try:
        import arabic_reshaper
        
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)
    except ImportError:
        return text

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# ----------------------------------------------------------------------
# BACKUP & RESTORE
# ----------------------------------------------------------------------

def do_backup(parent, current_username="admin"):
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    hour_str = now.strftime("%H%M%S")
    filename = f"VisitorSystemBackup_{date_str}-{hour_str}.db"
    app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    file_path = filedialog.asksaveasfilename(
        parent=parent,
        defaultextension=".db",
        filetypes=[("SQLite Database", "*.db")],
        title="ذخیره فایل پشتیبان",
        initialfile=filename,
        initialdir=app_dir
    )
    if not file_path:
        return
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        
        sqlite_conn = sqlite3.connect(file_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        sqlite_cursor.execute("""
            CREATE TABLE visitors (
                id INTEGER PRIMARY KEY, visitor_name TEXT NOT NULL,
                national_id TEXT NOT NULL, employee_to_meet TEXT NOT NULL,
                department TEXT NOT NULL, entry_time TEXT NOT NULL,
                shamsi_date TEXT, exit_time TEXT, created_by TEXT
            )
        """)
        sqlite_cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL, role TEXT NOT NULL, full_name TEXT
            )
        """)
        sqlite_cursor.execute("""
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY, shamsi_date TEXT NOT NULL,
                shamsi_time TEXT NOT NULL, event_type TEXT NOT NULL,
                user_name TEXT, visitor_id INTEGER, visitor_name TEXT,
                national_id TEXT, employee_to_meet TEXT, department TEXT,
                details TEXT, created_at TEXT
            )
        """)
        
        visitors = database.get_all_visitors_for_backup()
        for row in visitors:
            sqlite_cursor.execute("""
                INSERT INTO visitors VALUES (?,?,?,?,?,?,?,?,?)
            """, row)
        
        users = database.get_all_users_for_backup()
        for row in users:
            sqlite_cursor.execute("""
                INSERT INTO users VALUES (?,?,?,?,?)
            """, row)
        
        audit_logs = database.get_all_audit_logs_for_backup()
        for row in audit_logs:
            sqlite_cursor.execute("""
                INSERT INTO audit_log VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, row)
        
        sqlite_conn.commit()
        sqlite_conn.close()
        
        database.log_audit(
            "backup_created",
            user=current_username,
            details=f"Backup: {os.path.basename(file_path)} | V:{len(visitors)} U:{len(users)} A:{len(audit_logs)}"
        )
        
        total = len(visitors) + len(users) + len(audit_logs)
        messagebox.showinfo(
            "پشتیبان‌گیری موفق",
            f"✅ فایل پشتیبان ذخیره شد:\n\n📁 {file_path}\n\n"
            f"📊 آمار:\n   • مهمانان: {len(visitors)}\n"
            f"   • کاربران: {len(users)}\n   • لاگ‌ها: {len(audit_logs)}\n"
            f"   • جمع کل: {total}",
            parent=parent
        )
    except Exception as e:
        messagebox.showerror(
            "خطای پشتیبان‌گیری", f"❌ خطا:\n{str(e)}", parent=parent
        )


def do_restore(parent, current_username="admin"):
    file_path = filedialog.askopenfilename(
        parent=parent,
        filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
        title="انتخاب فایل پشتیبان"
    )
    if not file_path:
        return
    if not os.path.exists(file_path):
        messagebox.showerror("خطا", "فایل یافت نشد", parent=parent)
        return
    
    try:
        sqlite_conn = sqlite3.connect(file_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in sqlite_cursor.fetchall()]
        missing = [t for t in ['visitors','users','audit_log'] if t not in tables]
        if missing:
            messagebox.showerror(
                "فایل نامعتبر",
                f"❌ فایل نامعتبر. جداول یافت نشده: {', '.join(missing)}",
                parent=parent
            )
            sqlite_conn.close()
            return
        
        stats = {
            'visitors': {'new': 0, 'dup': 0, 'err': 0},
            'users': {'new': 0, 'dup': 0, 'err': 0},
            'audit_log': {'new': 0, 'dup': 0, 'err': 0}
        }
        
        # Restore visitors
        sqlite_cursor.execute("""
            SELECT visitor_name, national_id, employee_to_meet, department,
                   entry_time, shamsi_date, exit_time, created_by FROM visitors
        """)
        for row in sqlite_cursor.fetchall():
            try:
                if database.get_visitor_by_natid_employee_date(row[1], row[2], row[5], row[4]):
                    stats['visitors']['dup'] += 1
                    continue
                database.insert_visitor_from_backup(*row)
                stats['visitors']['new'] += 1
            except:
                stats['visitors']['err'] += 1
        
        # Restore users
        sqlite_cursor.execute("SELECT username, password, role, full_name FROM users")
        for row in sqlite_cursor.fetchall():
            try:
                if database.get_user_by_username(row[0]):
                    stats['users']['dup'] += 1
                    continue
                database.insert_user_from_backup(*row)
                stats['users']['new'] += 1
            except:
                stats['users']['err'] += 1
        
        # Restore audit logs
        sqlite_cursor.execute("""
            SELECT shamsi_date, shamsi_time, event_type, user_name,
                   visitor_id, visitor_name, national_id, employee_to_meet,
                   department, details, created_at FROM audit_log
        """)
        for row in sqlite_cursor.fetchall():
            try:
                if database.get_audit_log_duplicate(row[0], row[1], row[2], row[3], row[9]):
                    stats['audit_log']['dup'] += 1
                    continue
                database.insert_audit_log_from_backup(*row)
                stats['audit_log']['new'] += 1
            except:
                stats['audit_log']['err'] += 1
        
        sqlite_conn.close()
        
        total_new = stats['visitors']['new'] + stats['users']['new'] + stats['audit_log']['new']
        total_dup = stats['visitors']['dup'] + stats['users']['dup'] + stats['audit_log']['dup']
        
        database.log_audit(
            "backup_restored",
            user=current_username,
            details=f"Restored: {os.path.basename(file_path)} | New:{total_new} Dup:{total_dup}"
        )
        
        report = (
            f"✅ بازیابی موفق!\n\n📁 {os.path.basename(file_path)}\n\n"
            f"👥 کاربران:  جدید {stats['users']['new']} | تکراری {stats['users']['dup']} | خطا {stats['users']['err']}\n"
            f"🙋 مهمانان:  جدید {stats['visitors']['new']} | تکراری {stats['visitors']['dup']} | خطا {stats['visitors']['err']}\n"
            f"📋 لاگ‌ها:    جدید {stats['audit_log']['new']} | تکراری {stats['audit_log']['dup']} | خطا {stats['audit_log']['err']}\n\n"
            f"━━━━━━━━━━━━\n"
            f"📊 جمع:  جدید {total_new} | تکراری {total_dup} | خطا {sum(v['err'] for v in stats.values())}"
        )
        messagebox.showinfo("گزارش بازیابی", report, parent=parent)
        
    except Exception as e:
        messagebox.showerror("خطای بازیابی", f"❌ خطا:\n{str(e)}", parent=parent)
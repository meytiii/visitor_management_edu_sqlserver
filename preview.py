"""
==============================================================================
🎨 VISITOR MANAGEMENT SYSTEM - UI & STYLE PREVIEW STUDIO (Standalone / No DB)
==============================================================================
این فایل اختصاصاً برای توسعه، تست و شخصی‌سازی رابط کاربری (UI/UX) و استایل‌های
سامانه مدیریت ورود و خروج طراحی شده است.

ویژگی‌های کلیدی:
  1. کاملاً مستقل بدون نیاز به اتصال به SQL Server یا شبکه (Zero DB Dependency).
  2. دارای بانک اطلاعاتی درون‌حافظه‌ای کامل (In-Memory Mock Database) با ده‌ها رکورد
     واقعی، کدهای ملی معتبر، اسامی فارسی، تاریخ‌های شمسی و لاگ‌های حسابرسی.
  3. قابلیت باز کردن و تست تک‌تک پنجره‌ها، فرم‌ها و دیالوگ‌ها به صورت ایزوله با ۱ کلیک.
  4. تغییر تم زنده (Live Theme Switcher) برای بررسی ظاهر در تمام تم‌های مدرن و تیره/روشن.
  5. جعبه‌ابزار تعاملی تست ویجت‌ها و استایل‌ها (RoundedEntry, RoundedButton, AutocompleteEntry,
     Validation States, Success Overlay, Typography).
  6. شبیه‌ساز چاپگر حرارتی رسید (Thermal Receipt Visualizer) برای مشاهده رسید بدون نیاز به پرینتر فیزیکی.
  7. کاوشگر داده‌های موک (Mock Data Explorer) جهت بررسی و تغییر وضعیت داده‌های آزمایشی.

اجرا:
  python preview.py
==============================================================================
"""

import sys
import os
import random
import time
import uuid
import threading
from datetime import datetime, timedelta
import jdatetime

# Tkinter & ttkbootstrap
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk

# Data & Charts
import pandas as pd
import matplotlib
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Tahoma', 'Arial', 'DejaVu Sans']
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Local Modules
import config
import utils
import widgets

# ==============================================================================
# 1. GENERATOR FOR REALISTIC PERSIAN MOCK DATA
# ==============================================================================

PERSIAN_FIRST_NAMES = [
    "علی", "محمد", "حسین", "رضا", "مهدی", "امیرحسین", "علیرضا", "محمدرضا",
    "سجاد", "مصطفی", "مرتضی", "ابوالفضل", "احمد", "مهرداد", "فرهاد", "محسن",
    "زهرا", "فاطمه", "مریم", "نرگس", "زینب", "سارا", "الهام", "سمیه",
    "مهسا", "نازنین", "نیلوفر", "سپیده", "شیما", "مونا", "پریسا", "ریحانه"
]

PERSIAN_LAST_NAMES = [
    "محمدی", "حسینی", "رضایی", "مرادی", "احمدی", "کریمی", "موسوی", "جعفری",
    "قاسمی", "حیدری", "کاظمی", "رستمی", "صادقی", "فتحی", "عباسی", "صالحی",
    "باقری", "طاهری", "رحیمی", "ابراهیمی", "شریفی", "نجفی", "نوری", "فراهانی",
    "اکبری", "خسروی", "امانی", "سلیمانی", "هاشمی", "امیدی", "محمودی", "شجاعی"
]

EMPLOYEE_PREFIXES = ["دکتر", "مهندس", "آقای", "سرکار خانم", "استاد"]

def generate_valid_national_id():
    """Generates a mathematically valid 10-digit Iranian National ID."""
    while True:
        digits = [random.randint(0, 9) for _ in range(9)]
        if len(set(digits)) == 1:
            continue
        sum_val = sum(digits[i] * (10 - i) for i in range(9))
        rem = sum_val % 11
        control = rem if rem < 2 else 11 - rem
        nid = "".join(map(str, digits)) + str(control)
        if len(set(nid)) == 1:
            continue
        return nid

def generate_random_persian_name():
    return f"{random.choice(PERSIAN_FIRST_NAMES)} {random.choice(PERSIAN_LAST_NAMES)}"

def generate_random_employee():
    prefix = random.choice(EMPLOYEE_PREFIXES)
    return f"{prefix} {generate_random_persian_name()}"

# ==============================================================================
# 2. IN-MEMORY MOCK DATABASE ENGINE (ZERO SQL DEPENDENCY)
# ==============================================================================

class MockDatabaseEngine:
    """Complete in-memory replacement for database.py functionality."""
    
    def __init__(self):
        self.users = []
        self.visitors = []
        self.audit_logs = []
        self.hidden_employees = set()
        self.hidden_visitors = set()
        self.employee_department_map = {}
        self.print_history = []
        self.visitor_id_counter = 1000
        self.audit_id_counter = 5000
        self.seed_default_data()

    def seed_default_data(self):
        """Populates rich, diverse mock data for testing UI."""
        self.users.clear()
        self.visitors.clear()
        self.audit_logs.clear()
        self.hidden_employees.clear()
        self.hidden_visitors.clear()
        self.print_history.clear()
        
        # 1. Default Users
        self.users = [
            {"id": 1, "username": "admin", "password": "123", "role": "admin", "full_name": "مهندس سید مهدی حسینی (مدیر سیستم)"},
            {"id": 2, "username": "guard1", "password": "123", "role": "guard", "full_name": "علی مرادی (نگهبان شیفت صبح)"},
            {"id": 3, "username": "guard2", "password": "123", "role": "guard", "full_name": "حسین رضایی (نگهبان شیفت عصر)"},
            {"id": 4, "username": "supervisor", "password": "123", "role": "admin", "full_name": "دکتر صادقی (رئیس اداره حراست)"},
        ]

        # 2. Predefined Employees & Departments for autofill & suggestions
        known_employees = [
            ("دکتر علی رضایی", "حوزه مدیر کل"),
            ("مهندس سارا محمدی", "اداره فناوری اطلاعات"),
            ("آقای حسین کاظمی", "امور اداری"),
            ("خانم دکتر مریم کریمی", "معاونت آموزش ابتدایی"),
            ("آقای احمد رستمی", "اداره حراست"),
            ("مهندس رضا باقری", "اداره بودجه"),
            ("سرکار خانم فاطمه موسوی", "معاونت پرورشی"),
            ("آقای جعفر قاسم‌پور", "اداره امور مالی و حسابداری"),
            ("دکتر مصطفی فراهانی", "معاونت آموزش متوسطه"),
            ("مهندس فرهاد حیدری", "اداره بازرسی"),
            ("آقای مسعود عباسی", "اداره خدمات و پشتیبانی"),
            ("سرکار خانم شیما اکبری", "اداره استعداد های درخشان"),
        ]
        for emp, dept in known_employees:
            self.employee_department_map[emp] = dept

        # 3. Seed Mock Visitors (spanning today, yesterday, and recent days)
        now_dt = datetime.now()
        
        # Fixed returning visitor profiles for quick manual testing
        fixed_returning_profiles = [
            ("1271234567", "محمدرضا سلطانی", "دکتر علی رضایی", "حوزه مدیر کل"),
            ("0019876543", "سارا فیاضی", "مهندس سارا محمدی", "اداره فناوری اطلاعات"),
            ("3872233445", "علیرضا نجفی", "آقای حسین کاظمی", "امور اداری"),
            ("0451122334", "مریم سعیدی", "خانم دکتر مریم کریمی", "معاونت آموزش ابتدایی"),
        ]

        # Generate 45 realistic visitor records
        for i in range(45):
            self.visitor_id_counter += 1
            vid = self.visitor_id_counter
            
            # Mix fixed profiles and random ones
            if i < len(fixed_returning_profiles):
                nid, vname, emp, dept = fixed_returning_profiles[i]
            else:
                nid = generate_valid_national_id()
                vname = generate_random_persian_name()
                emp = random.choice(list(self.employee_department_map.keys()))
                dept = self.employee_department_map[emp]
            
            # Days offset: 0 (today), 1 (yesterday), 2-15 (past days)
            days_ago = 0 if i < 15 else (1 if i < 28 else random.randint(2, 20))
            record_date = now_dt - timedelta(days=days_ago)
            j_date = jdatetime.date.fromgregorian(date=record_date.date())
            shamsi_date_str = j_date.strftime("%Y/%m/%d")

            # Entry time between 07:30 and 14:15
            entry_hour = random.randint(7, 13)
            entry_min = random.choice([0, 10, 15, 20, 30, 40, 45, 50])
            entry_time_str = f"{entry_hour:02d}:{entry_min:02d}"
            
            # Exit time (some completed, some still pending)
            if days_ago > 0 or random.random() > 0.4:
                stay_mins = random.randint(15, 110)
                exit_dt = datetime(2026, 1, 1, entry_hour, entry_min) + timedelta(minutes=stay_mins)
                exit_time_str = exit_dt.strftime("%H:%M")
            else:
                exit_time_str = "" # Currently in building

            creator = random.choice(["admin", "guard1", "guard2"])

            self.visitors.append({
                "id": vid,
                "visitor_name": vname,
                "national_id": nid,
                "employee_to_meet": emp,
                "department": dept,
                "entry_time": entry_time_str,
                "shamsi_date": shamsi_date_str,
                "exit_time": exit_time_str,
                "created_by": creator
            })

        # 4. Seed Mock Audit Logs
        events = [
            ("login_success", "admin", "ورود موفق کاربر مدیر به سامانه"),
            ("visitor_added", "guard1", "ثبت ورود مهمان: محمدرضا سلطانی"),
            ("visitor_exit_recorded", "guard1", "ثبت ساعت خروج مهمان شماره 1001"),
            ("login_success", "guard1", "ورود نگهبان شیفت صبح"),
            ("backup_created", "admin", "تهیه فایل پشتیبان موفقیت‌آمیز"),
            ("data_exported", "admin", "خروجی اکسل گزارش سوابق مراجعین"),
            ("user_created", "admin", "ایجاد حساب کاربری جدید: guard2"),
            ("login_failed", "unknown", "تلاش ناموفق برای ورود به سیستم"),
        ]
        
        for i, (event_type, user, details) in enumerate(events):
            self.audit_id_counter += 1
            j_now = jdatetime.datetime.fromgregorian(datetime=now_dt - timedelta(minutes=i*45))
            self.audit_logs.append({
                "id": self.audit_id_counter,
                "shamsi_date": j_now.strftime("%Y/%m/%d"),
                "shamsi_time": j_now.strftime("%H:%M:%S"),
                "event_type": event_type,
                "user_name": user,
                "visitor_id": 1000 + i if "visitor" in event_type else None,
                "visitor_name": "مهمان نمونه" if "visitor" in event_type else None,
                "national_id": "0019876543" if "visitor" in event_type else None,
                "employee_to_meet": "دکتر رضایی" if "visitor" in event_type else None,
                "department": "اداره حراست" if "visitor" in event_type else None,
                "details": details,
                "created_at": (now_dt - timedelta(minutes=i*45)).strftime("%Y-%m-%d %H:%M:%S")
            })

    # --------------------------------------------------------------------------
    # Database.py Method Emulations
    # --------------------------------------------------------------------------

    def setup_database(self):
        return True

    def get_connection(self):
        return None

    def release_connection(self, conn=None):
        pass

    def pool_stats(self):
        return {"pool_size": 10, "available": 10, "active": 0, "max_size": 10}

    def shutdown_pool(self):
        pass

    def hash_password(self, password, salt=None):
        return f"mock_hash_{password}"

    def verify_password(self, stored_password, provided_password):
        if not stored_password or not provided_password:
            return False
        return (stored_password == provided_password or 
                stored_password == f"mock_hash_{provided_password}" or
                provided_password in ["123", "admin", "123456"])

    def authenticate_user(self, username, password):
        u_match = next((u for u in self.users if u["username"] == username), None)
        if not u_match:
            return False, None, None, "نام کاربری یا رمز عبور اشتباه است"
        if self.verify_password(u_match["password"], password):
            return True, u_match["role"], u_match["full_name"], ""
        return False, None, None, "نام کاربری یا رمز عبور اشتباه است"

    def get_all_users(self):
        return [(u["username"], u["role"], u["full_name"]) for u in self.users]

    def create_user(self, username, password, full_name, role):
        if any(u["username"] == username for u in self.users):
            return False, "این نام کاربری قبلاً ثبت شده است"
        self.users.append({
            "id": len(self.users) + 1,
            "username": username,
            "password": password,
            "role": role,
            "full_name": full_name
        })
        return True, ""

    def delete_user(self, username):
        initial_len = len(self.users)
        self.users = [u for u in self.users if u["username"] != username]
        if len(self.users) < initial_len:
            return True, ""
        return False, "کاربر یافت نشد"

    def update_user(self, username, new_full_name, new_role, new_password=None):
        for u in self.users:
            if u["username"] == username:
                u["full_name"] = new_full_name
                u["role"] = new_role
                if new_password:
                    u["password"] = new_password
                return True, ""
        return False, "کاربر یافت نشد"

    def change_user_password(self, username, new_password):
        for u in self.users:
            if u["username"] == username:
                u["password"] = new_password
                return True
        return False

    def get_employee_suggestions(self):
        emps = set(self.employee_department_map.keys())
        for v in self.visitors:
            if v["employee_to_meet"]:
                emps.add(v["employee_to_meet"])
        return sorted([e for e in emps if e not in self.hidden_employees])

    def get_last_department_for_employee(self, employee_name):
        if employee_name in self.employee_department_map:
            return self.employee_department_map[employee_name]
        for v in reversed(self.visitors):
            if v["employee_to_meet"] == employee_name:
                return v["department"]
        return None

    def get_visitor_name_by_nid(self, national_id):
        for v in reversed(self.visitors):
            if v["national_id"] == national_id:
                if (national_id, v["visitor_name"]) not in self.hidden_visitors:
                    return v["visitor_name"]
        return None

    def check_duplicate_entry(self, national_id, employee_to_meet, shamsi_date):
        for v in self.visitors:
            if (v["national_id"] == national_id and 
                v["employee_to_meet"] == employee_to_meet and 
                v["shamsi_date"] == shamsi_date):
                return True
        return False

    def add_visitor(self, visitor_name, national_id, employee_to_meet, department, entry_time, shamsi_date, registrar):
        self.visitor_id_counter += 1
        vid = self.visitor_id_counter
        self.visitors.insert(0, {
            "id": vid,
            "visitor_name": visitor_name,
            "national_id": national_id,
            "employee_to_meet": employee_to_meet,
            "department": department,
            "entry_time": entry_time.split(" ")[-1][:5] if " " in entry_time else entry_time[:5],
            "shamsi_date": shamsi_date,
            "exit_time": "",
            "created_by": registrar
        })
        self.employee_department_map[employee_to_meet] = department
        return vid

    def search_visitors(self, filters, page=1, items_per_page=50):
        res = list(self.visitors)
        if filters:
            name = filters.get("name", "").strip()
            if name:
                res = [r for r in res if name.lower() in r["visitor_name"].lower()]
            nid = filters.get("nid", "").strip()
            if nid:
                res = [r for r in res if nid in r["national_id"]]
            year = filters.get("year", "").strip()
            if year:
                res = [r for r in res if r["shamsi_date"].startswith(year)]
            m_name = filters.get("month_name", "").strip()
            if m_name in config.PERSIAN_MONTHS:
                m_num = str(config.PERSIAN_MONTHS.index(m_name) + 1).zfill(2)
                res = [r for r in res if len(r["shamsi_date"].split("/")) > 1 and r["shamsi_date"].split("/")[1] == m_num]
            day = filters.get("day", "").strip()
            if day:
                day_str = day.zfill(2)
                res = [r for r in res if len(r["shamsi_date"].split("/")) > 2 and r["shamsi_date"].split("/")[2] == day_str]
            dept = filters.get("dept", "").strip()
            if dept:
                res = [r for r in res if dept == r["department"]]

        total_records = len(res)
        start = (page - 1) * items_per_page
        end = start + items_per_page
        page_items = res[start:end]

        rows = [
            (
                r["id"],
                r["visitor_name"],
                r["national_id"],
                r["employee_to_meet"],
                r["department"],
                r["entry_time"],
                r["shamsi_date"],
                r["exit_time"],
                r["created_by"]
            )
            for r in page_items
        ]
        return total_records, rows

    def update_exit_time(self, visitor_id, exit_time_str, operator=None):
        for v in self.visitors:
            if str(v["id"]) == str(visitor_id):
                v["exit_time"] = exit_time_str
                return True
        return False

    def get_daily_stats(self, target_date_str):
        matches = [v for v in self.visitors if v["shamsi_date"] == target_date_str]
        total = len(matches)
        no_exit = sum(1 for v in matches if not v["exit_time"])
        return total, no_exit

    def get_hourly_stats(self, year=None, month_name=None, day=None, department=None):
        filtered = list(self.visitors)
        if year:
            filtered = [v for v in filtered if v["shamsi_date"].startswith(year)]
        if month_name in config.PERSIAN_MONTHS:
            m_num = str(config.PERSIAN_MONTHS.index(month_name) + 1).zfill(2)
            filtered = [v for v in filtered if len(v["shamsi_date"].split("/")) > 1 and v["shamsi_date"].split("/")[1] == m_num]
        if day:
            d_num = day.zfill(2)
            filtered = [v for v in filtered if len(v["shamsi_date"].split("/")) > 2 and v["shamsi_date"].split("/")[2] == d_num]
        if department:
            filtered = [v for v in filtered if v["department"] == department]

        hour_counts = {}
        for v in filtered:
            h = v["entry_time"].split(":")[0].zfill(2)
            hour_counts[h] = hour_counts.get(h, 0) + 1

        return sorted(hour_counts.items(), key=lambda x: x[0])

    def get_top_departments(self, year=None, month_name=None, day=None):
        filtered = list(self.visitors)
        if year:
            filtered = [v for v in filtered if v["shamsi_date"].startswith(year)]
        if month_name in config.PERSIAN_MONTHS:
            m_num = str(config.PERSIAN_MONTHS.index(month_name) + 1).zfill(2)
            filtered = [v for v in filtered if len(v["shamsi_date"].split("/")) > 1 and v["shamsi_date"].split("/")[1] == m_num]
        if day:
            d_num = day.zfill(2)
            filtered = [v for v in filtered if len(v["shamsi_date"].split("/")) > 2 and v["shamsi_date"].split("/")[2] == d_num]

        dept_counts = {}
        for v in filtered:
            d = v["department"]
            dept_counts[d] = dept_counts.get(d, 0) + 1

        sorted_depts = sorted(dept_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_depts[:3]

    def get_all_unique_employees(self):
        emp_counts = {}
        for v in self.visitors:
            e = v["employee_to_meet"]
            if e and e not in self.hidden_employees:
                emp_counts[e] = emp_counts.get(e, 0) + 1
        return sorted(emp_counts.items(), key=lambda x: x[1], reverse=True)

    def get_all_unique_visitors(self):
        vis_counts = {}
        for v in self.visitors:
            key = (v["national_id"], v["visitor_name"])
            if key not in self.hidden_visitors:
                vis_counts[key] = vis_counts.get(key, 0) + 1
        return [(nid, name, count) for (nid, name), count in sorted(vis_counts.items(), key=lambda x: x[1], reverse=True)]

    def fix_employee_typo(self, old_name, new_name):
        for v in self.visitors:
            if v["employee_to_meet"] == old_name:
                v["employee_to_meet"] = new_name
        if old_name in self.employee_department_map:
            self.employee_department_map[new_name] = self.employee_department_map.pop(old_name)

    def fix_visitor_typo(self, nid, old_name, new_name):
        for v in self.visitors:
            if v["national_id"] == nid and v["visitor_name"] == old_name:
                v["visitor_name"] = new_name

    def hide_employee_from_autofill(self, emp_name):
        self.hidden_employees.add(emp_name)

    def hide_visitor_from_autofill(self, nid, vis_name):
        self.hidden_visitors.add((nid, vis_name))

    def log_audit(self, action, user='سیستم', visitor_id=None, visitor_name=None, national_id=None,
                  employee_to_meet=None, department=None, entry_time=None, shamsi_date=None, details=None):
        self.audit_id_counter += 1
        now = datetime.now()
        j_now = jdatetime.datetime.fromgregorian(datetime=now)
        self.audit_logs.insert(0, {
            "id": self.audit_id_counter,
            "shamsi_date": shamsi_date or j_now.strftime("%Y/%m/%d"),
            "shamsi_time": j_now.strftime("%H:%M:%S"),
            "event_type": action,
            "user_name": user,
            "visitor_id": visitor_id,
            "visitor_name": visitor_name,
            "national_id": national_id,
            "employee_to_meet": employee_to_meet,
            "department": department,
            "details": details or f"Action: {action}",
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
        })

    def get_audit_logs(self, start_date=None, end_date=None):
        res = list(self.audit_logs)
        if start_date:
            res = [a for a in res if a["shamsi_date"] >= start_date]
        if end_date:
            res = [a for a in res if a["shamsi_date"] <= end_date]
        return [
            (
                a["shamsi_date"], a["shamsi_time"], a["event_type"], a["user_name"],
                a["visitor_id"], a["visitor_name"], a["national_id"],
                a["employee_to_meet"], a["department"], a["details"], a["created_at"]
            )
            for a in res
        ]

    def add_dummy_data(self):
        """Adds 50 random mock records on demand."""
        now_dt = datetime.now()
        for _ in range(50):
            self.visitor_id_counter += 1
            vid = self.visitor_id_counter
            nid = generate_valid_national_id()
            vname = generate_random_persian_name()
            emp = random.choice(list(self.employee_department_map.keys()))
            dept = self.employee_department_map[emp]
            days_ago = random.randint(0, 30)
            rec_date = now_dt - timedelta(days=days_ago)
            j_date = jdatetime.date.fromgregorian(date=rec_date.date())
            shamsi_date_str = j_date.strftime("%Y/%m/%d")
            entry_h = random.randint(7, 13)
            entry_m = random.choice([0, 15, 30, 45])
            entry_time_str = f"{entry_h:02d}:{entry_m:02d}"
            exit_time_str = f"{(entry_h + 1):02d}:{entry_m:02d}" if random.random() > 0.3 else ""
            
            self.visitors.insert(0, {
                "id": vid,
                "visitor_name": vname,
                "national_id": nid,
                "employee_to_meet": emp,
                "department": dept,
                "entry_time": entry_time_str,
                "shamsi_date": shamsi_date_str,
                "exit_time": exit_time_str,
                "created_by": random.choice(["admin", "guard1", "guard2"])
            })
        return True

    def delete_dev_records(self):
        return True

    def delete_all_records(self):
        self.visitors.clear()
        return True

    def get_all_visitors_for_backup(self):
        return [
            (v["id"], v["visitor_name"], v["national_id"], v["employee_to_meet"],
             v["department"], v["entry_time"], v["shamsi_date"], v["exit_time"], v["created_by"])
            for v in self.visitors
        ]

    def get_all_users_for_backup(self):
        return [(u["id"], u["username"], u["password"], u["role"], u["full_name"]) for u in self.users]

    def get_all_audit_logs_for_backup(self):
        return [
            (a["id"], a["shamsi_date"], a["shamsi_time"], a["event_type"], a["user_name"],
             a["visitor_id"], a["visitor_name"], a["national_id"], a["employee_to_meet"],
             a["department"], a["details"], a["created_at"])
            for a in self.audit_logs
        ]

    def insert_visitor_from_backup(self, *row):
        return True

    def insert_user_from_backup(self, *row):
        return True

    def insert_audit_log_from_backup(self, *row):
        return True

    def get_visitor_by_natid_employee_date(self, nid, emp, sdate, dept):
        return self.check_duplicate_entry(nid, emp, sdate)

    def get_user_by_username(self, username):
        return any(u["username"] == username for u in self.users)

    def get_audit_log_duplicate(self, sdate, stime, event, user, details):
        return False

# Instantiate Mock Engine
mock_db = MockDatabaseEngine()

# ==============================================================================
# 3. MONKEY-PATCHING PROJECT MODULES (SEAMLESS IN-MEMORY INTERCEPTION)
# ==============================================================================

import database
import printer

# Patch database module functions with mock engine methods
for attr in dir(mock_db):
    if not attr.startswith("__"):
        setattr(database, attr, getattr(mock_db, attr))

# Patch config test_connection so it always succeeds instantaneously
def mock_test_connection(settings_dict=None):
    return True, ""
config.test_connection = mock_test_connection

# Patch printer.print_receipt to record receipt and show preview
def mock_print_receipt(visitor_id, name, nid, emp, dept, entry_dt, shamsi_date):
    if entry_dt is None:
        entry_dt = datetime.now()
    elif isinstance(entry_dt, str):
        try:
            entry_dt = datetime.strptime(entry_dt, "%Y-%m-%d %H:%M:%S")
        except:
            entry_dt = datetime.now()

    receipt_item = {
        "id": visitor_id,
        "name": name,
        "nid": nid,
        "emp": emp,
        "dept": dept,
        "entry_dt": entry_dt,
        "shamsi_date": shamsi_date,
        "printed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    mock_db.print_history.insert(0, receipt_item)
    print(f"🖨️ [Mock Print] Receipt #{visitor_id:06d} for {name} ({dept}) queued successfully.")

printer.print_receipt = mock_print_receipt

# Import windows module after database and config are safely mocked
import windows

# Prevent os._exit from killing the preview suite when sub-windows close
_original_os_exit = os._exit
def safe_os_exit(code=0):
    print(f"ℹ️ [Preview Mode] Intercepted os._exit({code}) to keep Preview Studio running.")
os._exit = safe_os_exit

# ==============================================================================
# 4. THERMAL RECEIPT VISUALIZER COMPONENT
# ==============================================================================

def open_receipt_preview_dialog(parent, visitor_id=1024, name="محمدرضا سلطانی", 
                                nid="0019876543", emp="دکتر علی رضایی", 
                                dept="حوزه مدیر کل", entry_time="09:15", 
                                shamsi_date=None):
    """Renders a pixel-perfect simulated 80mm thermal receipt."""
    if not shamsi_date:
        shamsi_date = jdatetime.date.fromgregorian(date=datetime.now().date()).strftime("%Y/%m/%d")

    rec_win = tb.Toplevel(parent)
    rec_win.title(f"پیش‌نمایش رسید حرارتی - قبض شماره {visitor_id:06d}")
    rec_win.geometry("420x720")
    rec_win.resizable(False, False)

    # Receipt paper container with drop shadow aesthetic
    paper_frame = tk.Frame(rec_win, bg="#FFFDF0", bd=2, relief="groove")
    paper_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

    # Thermal Receipt Content
    tb.Label(paper_frame, text="«باسمه تعالی»", font=("Tahoma", 10, "bold"), background="#FFFDF0", foreground="#333333").pack(pady=(15, 2))
    tb.Label(paper_frame, text="اداره کل آموزش و پرورش استان همدان", font=("Tahoma", 11, "bold"), background="#FFFDF0", foreground="#111111").pack(pady=1)
    tb.Label(paper_frame, text="(اداره حراست)", font=("Tahoma", 10, "bold"), background="#FFFDF0", foreground="#222222").pack(pady=1)
    
    tb.Label(paper_frame, text="------------------------------------------------", font=("Courier", 10), background="#FFFDF0", foreground="#888888").pack(pady=4)

    # Receipt metadata grid
    meta_frame = tk.Frame(paper_frame, bg="#FFFDF0")
    meta_frame.pack(fill=tk.X, padx=15)

    def add_line(lbl, val):
        row = tk.Frame(meta_frame, bg="#FFFDF0")
        row.pack(fill=tk.X, pady=2)
        tk.Label(row, text=lbl, font=("Tahoma", 10, "bold"), bg="#FFFDF0", fg="#333333").pack(side=tk.RIGHT)
        tk.Label(row, text=val, font=("Tahoma", 10), bg="#FFFDF0", fg="#111111").pack(side=tk.RIGHT, padx=5)

    add_line("شماره قبض:", f"{int(visitor_id):06d}")
    add_line("تاریخ ورود:", shamsi_date)
    add_line("ساعت ورود:", entry_time)
    add_line("ساعت خروج:", "...............")
    
    tb.Label(paper_frame, text="------------------------------------------------", font=("Courier", 10), background="#FFFDF0", foreground="#888888").pack(pady=4)

    add_line("نام ملاقات کننده:", name)
    add_line("کد ملی:", nid)
    add_line("امور / واحد مربوطه:", dept)
    add_line("ملاقات شونده:", emp)

    tb.Label(paper_frame, text="------------------------------------------------", font=("Courier", 10), background="#FFFDF0", foreground="#888888").pack(pady=4)
    
    # Signature Box
    sig_frame = tk.Frame(paper_frame, bg="#FFFDF0", height=60)
    sig_frame.pack(fill=tk.X, padx=15, pady=5)
    tk.Label(sig_frame, text="امضاء و تایید ملاقات شونده:", font=("Tahoma", 9), bg="#FFFDF0", fg="#555555").pack(anchor="ne")

    # Barcode Simulation
    barcode_frame = tk.Frame(paper_frame, bg="#FFFDF0")
    barcode_frame.pack(pady=10)
    canvas = tk.Canvas(barcode_frame, width=240, height=45, bg="#FFFDF0", highlightthickness=0)
    canvas.pack()
    random.seed(visitor_id)
    x = 10
    while x < 230:
        w = random.choice([1, 2, 3, 4])
        canvas.create_rectangle(x, 5, x + w, 40, fill="#111111", outline="")
        x += w + random.choice([1, 2, 3])
    random.seed()

    tb.Label(paper_frame, text=f"* {int(visitor_id):06d} *", font=("Courier", 9, "bold"), background="#FFFDF0", foreground="#333333").pack()
    tb.Label(paper_frame, text="* حداکثر زمان مجاز حضور در اداره ۲ ساعت می‌باشد *", font=("Tahoma", 8), background="#FFFDF0", foreground="#777777").pack(pady=(6, 12))

    btn_close = tb.Button(rec_win, text="بستن پیش‌نمایش", command=rec_win.destroy, bootstyle=SECONDARY)
    btn_close.pack(pady=(0, 10))

# ==============================================================================
# 5. MAIN PREVIEW & STYLE STUDIO APPLICATION
# ==============================================================================

class UIPreviewStudio:
    def __init__(self):
        # Master ttkbootstrap window
        self.root = tb.Window(themename="lumen")
        self.root.title("🎨 سامانه مدیریت مراجعین | استودیوی پیش‌نمایش رابط کاربری و استایل (Standalone)")
        self.root.geometry("1180x820")
        self.root.minsize(980, 700)
        
        # Load app icon safely
        try:
            icon_path = utils.resource_path(os.path.join('assets', 'app_icon.ico'))
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

        self.current_role = tk.StringVar(value="admin")
        self.current_theme = tk.StringVar(value="lumen")
        self.active_subwindows = []
        
        self.setup_ui()

    def setup_ui(self):
        # ----------------- Top Header Banner -----------------
        header_frame = tb.Frame(self.root, bootstyle="primary", padding=15)
        header_frame.pack(fill=tk.X)

        # Title & Badges
        title_box = tb.Frame(header_frame, bootstyle="primary")
        title_box.pack(side=tk.RIGHT, fill=tk.Y)
        
        tb.Label(
            title_box, 
            text="🛡️ سامانه مدیریت مراجعین - استودیوی پیش‌نمایش رابط کاربری", 
            font=("Tahoma", 15, "bold"), 
            bootstyle="inverse-primary"
        ).pack(anchor="e")
        
        tb.Label(
            title_box, 
            text="محیط ایزوله تست استایل‌ها، کامپوننت‌ها و پنجره‌ها بدون نیاز به پایگاه داده (نسخه ۴.۲.۸)", 
            font=("Tahoma", 10), 
            bootstyle="inverse-primary"
        ).pack(anchor="e", pady=(2, 0))

        # Controls in Header (Left Side)
        ctrl_box = tb.Frame(header_frame, bootstyle="primary")
        ctrl_box.pack(side=tk.LEFT, fill=tk.Y)

        # Theme Selector Dropdown
        tb.Label(ctrl_box, text="تم ظاهری:", font=("Tahoma", 10, "bold"), bootstyle="inverse-primary").pack(side=tk.LEFT, padx=(5, 3))
        available_themes = [
            "lumen", "cosmo", "flatly", "journal", "litera", "minty", 
            "pulse", "sandstone", "united", "yeti", "morph", "simplex", 
            "cerculean", "darkly", "cyborg", "solar", "vapor", "superhero"
        ]
        self.theme_combo = tb.Combobox(
            ctrl_box, 
            textvariable=self.current_theme, 
            values=available_themes, 
            state="readonly", 
            width=11, 
            font=("Tahoma", 10)
        )
        self.theme_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.theme_combo.bind("<<ComboboxSelected>>", self.on_theme_change)

        # Role Selector
        tb.Label(ctrl_box, text="نقش فعال:", font=("Tahoma", 10, "bold"), bootstyle="inverse-primary").pack(side=tk.LEFT, padx=(5, 3))
        self.role_combo = tb.Combobox(
            ctrl_box, 
            textvariable=self.current_role, 
            values=["admin", "guard"], 
            state="readonly", 
            width=8, 
            font=("Tahoma", 10)
        )
        self.role_combo.pack(side=tk.LEFT, padx=(0, 10))

        # Reset Mock Data Button
        tb.Button(
            ctrl_box, 
            text="🔄 بازنشانی موک", 
            command=self.reset_mock_data, 
            bootstyle="warning", 
            width=12
        ).pack(side=tk.LEFT, padx=3)

        # Add 50 Records Button
        tb.Button(
            ctrl_box, 
            text="➕ ۵۰ رکورد آزمایشی", 
            command=self.add_50_mock_records, 
            bootstyle="success", 
            width=15
        ).pack(side=tk.LEFT, padx=3)

        # ----------------- Main Notebook Tabs -----------------
        self.notebook = tb.Notebook(self.root, bootstyle="primary", padding=10)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Tab 1: Window Launchers
        self.tab_launchers = tb.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_launchers, text="🪟 پنجره‌ها و صفحات برنامه")
        self.setup_tab_launchers()

        # Tab 2: Style & Component Sandbox
        self.tab_sandbox = tb.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_sandbox, text="🎨 جعبه‌ابزار استایل و کامپوننت‌ها")
        self.setup_tab_sandbox()

        # Tab 3: Mock Data Explorer
        self.tab_data = tb.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_data, text="📋 کاوشگر داده‌های موک (In-Memory DB)")
        self.setup_tab_data()

        # Tab 4: Thermal Receipt Simulator
        self.tab_receipt = tb.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_receipt, text="🧾 شبیه‌ساز چاپگر حرارتی رسید")
        self.setup_tab_receipt()

        # ----------------- Bottom Status Bar -----------------
        self.status_bar = tb.Label(
            self.root, 
            text="  🟢 سیستم در حالت پیش‌نمایش مستقل (Mock DB فعال است - بدون نیاز به SQL Server)", 
            anchor=tk.E, 
            font=("Tahoma", 10), 
            padding=4, 
            bootstyle="inverse-secondary"
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # --------------------------------------------------------------------------
    # TAB 1: WINDOW & SCREEN LAUNCHERS
    # --------------------------------------------------------------------------
    def setup_tab_launchers(self):
        # Quick Description Card
        info_card = tb.LabelFrame(self.tab_launchers, text="راهنمای راه‌اندازی سریع صفحات", padding=10, bootstyle="info")
        info_card.pack(fill=tk.X, pady=(0, 15))
        
        tb.Label(
            info_card, 
            text="از دکمه‌های زیر برای باز کردن هر صفحه یا دیالوگ به صورت جداگانه و مستقل استفاده کنید. تمام داده‌ها، جدول‌ها و عملیات‌ها بدون ایجاد اتصال به SQL Server در حافظه شبیه‌سازی می‌شوند.",
            font=("Tahoma", 10),
            justify="right"
        ).pack(anchor="e")

        # Scrollable area for cards
        canvas = tk.Canvas(self.tab_launchers, highlightthickness=0)
        v_scroll = tb.Scrollbar(self.tab_launchers, orient=tk.VERTICAL, command=canvas.yview)
        scroll_content = tb.Frame(canvas)

        scroll_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_content, anchor="nw", width=1100)
        canvas.configure(yscrollcommand=v_scroll.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Group 1: Core Screens
        g1 = tb.LabelFrame(scroll_content, text="📌 صفحات و فرم‌های اصلی", padding=15, bootstyle="primary")
        g1.pack(fill=tk.X, pady=8)

        self.create_launcher_card(
            g1, 
            title="🚪 صفحه ورود به سیستم (Login Screen)", 
            desc="فرم احراز هویت با انیمیشن پس‌زمینه، استاتوس بار سرور و ورود آزمایشی (نام کاربری: admin یا guard1 / رمز: 123)",
            btn_text="اجرای صفحه ورود", 
            btn_style="primary", 
            command=self.launch_login_screen
        )

        self.create_launcher_card(
            g1, 
            title="🖥️ داشبورد اصلی ثبت ورود و خروج (Main App Window)", 
            desc="کارت ثبت مراجعین با اعتبارسنجی زنده کد ملی، پیشنهادات تکمیل خودکار (Autocomplete)، ساعت دیجیتال و نوار احادیث",
            btn_text="اجرای داشبورد اصلی", 
            btn_style="success", 
            command=self.launch_main_dashboard
        )

        self.create_launcher_card(
            g1, 
            title="🔍 مشاهده و جستجوی سوابق مراجعین (Search & Records)", 
            desc="جدول کامل مراجعین با فیلتر نام، کد ملی، تاریخ و واحد، صفحه‌بندی هوشمند، ثبت خروج با دابل‌کلیک و خروجی اکسل",
            btn_text="اجرای جستجوی سوابق", 
            btn_style="info", 
            command=lambda: windows.open_search_window(self.root)
        )

        # Group 2: Management & Admin Panels
        g2 = tb.LabelFrame(scroll_content, text="🛠️ پنل‌ها و ابزارهای مدیریت", padding=15, bootstyle="primary")
        g2.pack(fill=tk.X, pady=8)

        self.create_launcher_card(
            g2, 
            title="👥 مدیریت کاربران (User Manager)", 
            desc="مشاهده لیست کاربران، افزودن کاربر جدید، ویرایش نقش‌ها (مدیر/نگهبان) و تغییر رمز با پس‌زمینه گرافیکی",
            btn_text="اجرای مدیریت کاربران", 
            btn_style="primary", 
            command=lambda: windows.open_user_manager(self.root, current_user="admin")
        )

        self.create_launcher_card(
            g2, 
            title="🧹 اصلاح و پاکسازی داده‌های Autofill (Data Cleanup)", 
            desc="رفع غلط‌های املایی اسامی مراجعین و پرسنل، ادغام سوابق تکراری و مخفی‌سازی اسامی از لیست پیشنهادات",
            btn_text="اجرای پاکسازی داده‌ها", 
            btn_style="warning", 
            command=lambda: windows.open_data_cleanup_window(self.root)
        )

        self.create_launcher_card(
            g2, 
            title="🛠️ پنل مدیریت راهبر (Developer Mode Panel)", 
            desc="دسترسی به ابزارهای مدیریتی شامل پشتیبان‌گیری، تحلیل آماری، خروجی اکسل لاگ حسابرسی و تست دیتابیس",
            btn_text="اجرای پنل مدیریت", 
            btn_style="dark", 
            command=lambda: windows.open_developer_mode(self.root)
        )

        self.create_launcher_card(
            g2, 
            title="⚙️ تنظیمات اتصال به سرور (SQL Server Settings)", 
            desc="فرم پیکربندی آدرس سرور، نام دیتابیس، درایور ODBC و تست آنی اتصال",
            btn_text="اجرای تنظیمات سرور", 
            btn_style="secondary", 
            command=lambda: windows.open_server_settings(self.root)
        )

        # Group 3: Analytics, Reports & Utilities
        g3 = tb.LabelFrame(scroll_content, text="📊 آمار، گزارش‌ها و ابزارهای جانبی", padding=15, bootstyle="primary")
        g3.pack(fill=tk.X, pady=8)

        self.create_launcher_card(
            g3, 
            title="📈 تحلیل آماری و نمودارهای تردد (Heatmap / Hourly Analytics)", 
            desc="نمودار میله‌ای توزیع ساعتی تردد با فیلترهای سال، ماه، روز و واحد مربوطه به همراه معرفی ۳ واحد پرتردد",
            btn_text="اجرای نمودارهای آماری", 
            btn_style="info", 
            command=lambda: windows.show_heatmap_analytics(self.root)
        )

        self.create_launcher_card(
            g3, 
            title="📊 آمار روزانه مراجعین (Daily Stats Popup)", 
            desc="محاسبه‌گر سریع تعداد کل مراجعین ثبت شده و افراد بدون ساعت خروج در هر تاریخ شمسی دلخواه",
            btn_text="اجرای آمار روزانه", 
            btn_style="secondary", 
            command=lambda: windows.show_daily_stats_ui(self.root)
        )

        self.create_launcher_card(
            g3, 
            title="📋 خروجی اکسل لاگ حسابرسی (Audit Log Export)", 
            desc="فرم انتخاب بازه زمانی تاریخ شمسی جهت استخراج اکسل تمام رویدادهای سیستمی و امنیتی",
            btn_text="اجرای خروجی لاگ اکسل", 
            btn_style="success", 
            command=lambda: windows.export_audit_log_excel(self.root)
        )

        self.create_launcher_card(
            g3, 
            title="🔑 تغییر رمز عبور کاربر (Change Password)", 
            desc="دیالوگ تغییر رمز عبور کاربر جاری با اعتبارسنجی رمز فعلی و تکرار رمز جدید",
            btn_text="اجرای تغییر رمز", 
            btn_style="warning", 
            command=lambda: windows.open_change_password_window(self.root, username="admin")
        )

        self.create_launcher_card(
            g3, 
            title="📑 راهنمای جامع سیستم (Help Guide Viewer)", 
            desc="نمایش راهنمای کاربری و مدیریتی تحت مرورگر به همراه گرافیک کامل و جداول راهنما",
            btn_text="مشاهده راهنمای HTML", 
            btn_style="secondary", 
            command=lambda: windows.show_help_popup(self.current_role.get())
        )

    def create_launcher_card(self, parent, title, desc, btn_text, btn_style, command):
        card = tb.Frame(parent, padding=8)
        card.pack(fill=tk.X, pady=4)
        
        left_box = tb.Frame(card)
        left_box.pack(side=tk.LEFT, padx=10)
        tb.Button(left_box, text=btn_text, command=command, bootstyle=btn_style, width=20).pack(ipady=4)

        right_box = tb.Frame(card)
        right_box.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        tb.Label(right_box, text=title, font=("Tahoma", 11, "bold"), anchor="e").pack(fill=tk.X)
        tb.Label(right_box, text=desc, font=("Tahoma", 9), foreground="#666666", anchor="e").pack(fill=tk.X)

        tb.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)

    # --------------------------------------------------------------------------
    # TAB 2: COMPONENT & STYLE SANDBOX
    # --------------------------------------------------------------------------
    def setup_tab_sandbox(self):
        container = tb.Frame(self.tab_sandbox)
        container.pack(fill=tk.BOTH, expand=True)

        left_col = tb.Frame(container)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        right_col = tb.Frame(container)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        # 1. Custom Widgets Test (widgets.py)
        box_widgets = tb.LabelFrame(right_col, text="🎨 ویجت‌های سفارشی (widgets.py)", padding=15, bootstyle="primary")
        box_widgets.pack(fill=tk.X, pady=5)

        tb.Label(box_widgets, text="AutocompleteEntry (پیشنهاد خودکار اسامی):", font=("Tahoma", 10, "bold"), anchor="e").pack(fill=tk.X, pady=(0, 2))
        mock_suggestions = mock_db.get_employee_suggestions()
        self.auto_entry = widgets.AutocompleteEntry(box_widgets, completevalues=mock_suggestions, justify="right", font=("Tahoma", 11))
        self.auto_entry.pack(fill=tk.X, pady=(0, 10))

        tb.Label(box_widgets, text="RoundedButton (دکمه منحنی):", font=("Tahoma", 10, "bold"), anchor="e").pack(fill=tk.X, pady=(5, 2))
        btn_wrapper = tk.Frame(box_widgets)
        btn_wrapper.pack(fill=tk.X, pady=5)
        
        def on_rounded_click():
            messagebox.showinfo("تست ویجت", "دکمه گرد (RoundedButton) با موفقیت فشرده شد!", parent=self.root)

        r_btn = widgets.RoundedButton(btn_wrapper, text="دکمه با گوشه‌های منحنی (Rounded)", command=on_rounded_click, width=280, height=40, bg="#198754", hover_bg="#146c43")
        r_btn.pack(pady=4)

        tb.Label(box_widgets, text="RoundedEntry (فیلد ورودی منحنی):", font=("Tahoma", 10, "bold"), anchor="e").pack(fill=tk.X, pady=(10, 2))
        r_ent = widgets.RoundedEntry(box_widgets, width=280, height=35, radius=12, justify="center")
        r_ent.pack(pady=4)

        # 2. Validation States Sandbox
        box_val = tb.LabelFrame(right_col, text="⚡ وضعیت‌های اعتبارسنجی (Validation Bootstyles)", padding=15, bootstyle="primary")
        box_val.pack(fill=tk.X, pady=10)

        tb.Label(box_val, text="تست حالت‌های رنگی فیلدهای ورودی:", font=("Tahoma", 10, "bold"), anchor="e").pack(fill=tk.X)
        val_grid = tb.Frame(box_val)
        val_grid.pack(fill=tk.X, pady=5)

        tb.Entry(val_grid, bootstyle=DEFAULT, justify="center").grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        tb.Label(val_grid, text="پیش‌فرض (DEFAULT)", font=("Tahoma", 9)).grid(row=0, column=1, sticky="e", padx=4)

        tb.Entry(val_grid, bootstyle=SUCCESS, justify="center").grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        tb.Label(val_grid, text="موفق / معتبر (SUCCESS)", font=("Tahoma", 9), foreground="#198754").grid(row=1, column=1, sticky="e", padx=4)

        tb.Entry(val_grid, bootstyle=WARNING, justify="center").grid(row=2, column=0, padx=4, pady=4, sticky="ew")
        tb.Label(val_grid, text="هشدار (WARNING)", font=("Tahoma", 9), foreground="#d97706").grid(row=2, column=1, sticky="e", padx=4)

        tb.Entry(val_grid, bootstyle=DANGER, justify="center").grid(row=3, column=0, padx=4, pady=4, sticky="ew")
        tb.Label(val_grid, text="خطا (DANGER)", font=("Tahoma", 9), foreground="#dc2626").grid(row=3, column=1, sticky="e", padx=4)
        val_grid.columnconfigure(0, weight=1)

        # 3. Interactive Animations & Overlays
        box_anim = tb.LabelFrame(left_col, text="✨ انیمیشن‌ها و افکت‌های بصری", padding=15, bootstyle="primary")
        box_anim.pack(fill=tk.X, pady=5)

        tb.Label(box_anim, text="انیمیشن تأیید ثبت اطلاعات (Success Overlay):", font=("Tahoma", 10, "bold"), anchor="e").pack(fill=tk.X)
        tb.Button(
            box_anim, 
            text="▶ نمایش انیمیشن تایید ثبت (سبز محو شونده)", 
            command=lambda: self.trigger_overlay_demo(box_anim), 
            bootstyle="success"
        ).pack(fill=tk.X, pady=8)

        # 4. Persian Font Showcase
        box_fonts = tb.LabelFrame(left_col, text="🔤 تست فونت‌های فارسی سیستم", padding=15, bootstyle="primary")
        box_fonts.pack(fill=tk.X, pady=10)

        available_system_fonts = font.families()
        tb.Label(box_fonts, text="پیش‌نمایش تایپوگرافی با فونت‌های مختلف:", font=("Tahoma", 10, "bold"), anchor="e").pack(fill=tk.X)
        
        sample_fonts = [
            ("B Titr", "سامانه مدیریت ورود و خروج مراجعین (B Titr)"),
            ("B Nazanin", "اداره کل آموزش و پرورش استان همدان - حراست (B Nazanin)"),
            ("B Roya", "تکریم ارباب رجوع، وظیفه شرعی و اخلاقی ماست (B Roya)"),
            ("Tahoma", "سامانه مدیریت مراجعین با فونت استاندارد سیستم (Tahoma)"),
            ("Segoe UI", "Visitor Management Security System (Segoe UI)"),
        ]

        for fname, sample_text in sample_fonts:
            status_tag = "✓ نصب است" if fname in available_system_fonts else "✗ پیش‌فرض"
            row = tb.Frame(box_fonts)
            row.pack(fill=tk.X, pady=3)
            tb.Label(row, text=sample_text, font=(fname if fname in available_system_fonts else "Tahoma", 11)).pack(side=tk.RIGHT)
            tb.Label(row, text=f"[{status_tag}]", font=("Tahoma", 8), foreground="#888888").pack(side=tk.LEFT)

    def trigger_overlay_demo(self, parent):
        """Displays the smooth success checkmark animation."""
        import main
        main.show_success_overlay(self.root)

    # --------------------------------------------------------------------------
    # TAB 3: MOCK DATA EXPLORER
    # --------------------------------------------------------------------------
    def setup_tab_data(self):
        # Controls Header
        top_bar = tb.Frame(self.tab_data)
        top_bar.pack(fill=tk.X, pady=(0, 10))

        tb.Label(top_bar, text="جستجو در داده‌ها:", font=("Tahoma", 10, "bold")).pack(side=tk.RIGHT, padx=5)
        self.data_search_ent = tb.Entry(top_bar, justify="right", font=("Tahoma", 10), width=25)
        self.data_search_ent.pack(side=tk.RIGHT, padx=5)
        self.data_search_ent.bind("<KeyRelease>", lambda e: self.refresh_data_table())

        tb.Button(top_bar, text="جستجو", command=self.refresh_data_table, bootstyle="primary").pack(side=tk.RIGHT, padx=5)
        tb.Button(top_bar, text="➕ افزودن مراجع جدید", command=self.quick_add_visitor_dialog, bootstyle="success").pack(side=tk.LEFT, padx=5)
        tb.Button(top_bar, text="🗑️ حذف انتخاب شده", command=self.delete_selected_mock_record, bootstyle="danger-outline").pack(side=tk.LEFT, padx=5)
        tb.Button(top_bar, text="🔄 به‌روزرسانی جدول", command=self.refresh_data_table, bootstyle="secondary").pack(side=tk.LEFT, padx=5)

        # Treeview
        tree_frame = tb.Frame(self.tab_data)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        v_scroll = tb.Scrollbar(tree_frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll = tb.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.mock_tree = tb.Treeview(
            tree_frame, 
            columns=("id", "name", "nid", "emp", "dept", "entry", "date", "exit", "by"), 
            show="headings", 
            bootstyle="primary", 
            yscrollcommand=v_scroll.set, 
            xscrollcommand=h_scroll.set
        )
        v_scroll.config(command=self.mock_tree.yview)
        h_scroll.config(command=self.mock_tree.xview)

        cols = [
            ("id", "شناسه", 70),
            ("name", "نام مهمان", 150),
            ("nid", "کد ملی", 110),
            ("emp", "ملاقات شونده", 140),
            ("dept", "واحد مربوطه", 180),
            ("entry", "ساعت ورود", 80),
            ("date", "تاریخ شمسی", 90),
            ("exit", "ساعت خروج", 80),
            ("by", "ثبت کننده", 110),
        ]
        for col_id, text, width in cols:
            self.mock_tree.heading(col_id, text=text)
            self.mock_tree.column(col_id, width=width, anchor=tk.CENTER)

        self.mock_tree.pack(fill=tk.BOTH, expand=True)
        self.mock_tree.bind("<Double-1>", self.on_mock_row_double_click)

        self.lbl_mock_stats = tb.Label(self.tab_data, text="", font=("Tahoma", 10), bootstyle="secondary")
        self.lbl_mock_stats.pack(anchor="e", pady=5)

        self.refresh_data_table()

    def refresh_data_table(self):
        for item in self.mock_tree.get_children():
            self.mock_tree.delete(item)

        q = self.data_search_ent.get().strip().lower()
        items = mock_db.visitors
        if q:
            items = [v for v in items if q in v["visitor_name"].lower() or q in v["national_id"] or q in v["department"].lower() or q in v["employee_to_meet"].lower()]

        for v in items:
            self.mock_tree.insert("", tk.END, values=(
                v["id"],
                v["visitor_name"],
                v["national_id"],
                v["employee_to_meet"],
                v["department"],
                v["entry_time"],
                v["shamsi_date"],
                v["exit_time"] or "در حال حضور",
                v["created_by"]
            ))

        self.lbl_mock_stats.config(text=f"تعداد کل رکوردهای بارگذاری شده در حافظه: {len(mock_db.visitors)} | رکوردهای نمایش داده شده: {len(items)}")

    def on_mock_row_double_click(self, event):
        sel = self.mock_tree.selection()
        if not sel:
            return
        vals = self.mock_tree.item(sel[0], "values")
        open_receipt_preview_dialog(
            self.root, 
            visitor_id=vals[0], 
            name=vals[1], 
            nid=vals[2], 
            emp=vals[3], 
            dept=vals[4], 
            entry_time=vals[5], 
            shamsi_date=vals[6]
        )

    def quick_add_visitor_dialog(self):
        dlg = tb.Toplevel(self.root)
        dlg.title("ثبت سریع مراجع آزمایشی")
        dlg.geometry("400x480")
        dlg.resizable(False, False)

        frm = tb.Frame(dlg, padding=20)
        frm.pack(fill=tk.BOTH, expand=True)

        tb.Label(frm, text="نام و نام خانوادگی:", font=("Tahoma", 10)).pack(anchor="e", pady=(5, 2))
        ent_name = tb.Entry(frm, justify="right")
        ent_name.insert(0, generate_random_persian_name())
        ent_name.pack(fill=tk.X, pady=(0, 8))

        tb.Label(frm, text="کد ملی (معتبر):", font=("Tahoma", 10)).pack(anchor="e", pady=(5, 2))
        ent_nid = tb.Entry(frm, justify="center")
        ent_nid.insert(0, generate_valid_national_id())
        ent_nid.pack(fill=tk.X, pady=(0, 8))

        tb.Label(frm, text="ملاقات شونده:", font=("Tahoma", 10)).pack(anchor="e", pady=(5, 2))
        ent_emp = tb.Entry(frm, justify="right")
        ent_emp.insert(0, generate_random_employee())
        ent_emp.pack(fill=tk.X, pady=(0, 8))

        tb.Label(frm, text="واحد مربوطه:", font=("Tahoma", 10)).pack(anchor="e", pady=(5, 2))
        cb_dept = tb.Combobox(frm, values=config.DEPARTMENT_LIST, justify="right", state="readonly")
        cb_dept.set(random.choice(config.DEPARTMENT_LIST))
        cb_dept.pack(fill=tk.X, pady=(0, 15))

        def save_quick():
            vname = ent_name.get().strip()
            nid = ent_nid.get().strip()
            emp = ent_emp.get().strip()
            dept = cb_dept.get().strip()
            now_dt = datetime.now()
            sdate = jdatetime.date.fromgregorian(date=now_dt.date()).strftime("%Y/%m/%d")
            etime = now_dt.strftime("%H:%M")
            mock_db.add_visitor(vname, nid, emp, dept, etime, sdate, self.current_role.get())
            self.refresh_data_table()
            dlg.destroy()
            messagebox.showinfo("موفق", f"مراجع با موفقیت در دیتابیس موک ثبت شد.", parent=self.root)

        tb.Button(frm, text="ثبت و ذخیره در موک", command=save_quick, bootstyle="success").pack(fill=tk.X, pady=10)

    def delete_selected_mock_record(self):
        sel = self.mock_tree.selection()
        if not sel:
            return messagebox.showwarning("انتخاب رکورد", "لطفاً یک رکورد را انتخاب کنید.", parent=self.root)
        vid = self.mock_tree.item(sel[0], "values")[0]
        mock_db.visitors = [v for v in mock_db.visitors if str(v["id"]) != str(vid)]
        self.refresh_data_table()

    # --------------------------------------------------------------------------
    # TAB 4: THERMAL RECEIPT SIMULATOR
    # --------------------------------------------------------------------------
    def setup_tab_receipt(self):
        split = tb.Frame(self.tab_receipt)
        split.pack(fill=tk.BOTH, expand=True)

        left_ctrl = tb.LabelFrame(split, text="تنظیمات اطلاعات قبض", padding=15, bootstyle="primary", width=380)
        left_ctrl.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)
        left_ctrl.pack_propagate(False)

        right_preview = tb.LabelFrame(split, text="پیش‌نمایش چاپ حرارتی (۸۰ میلی‌متری)", padding=15, bootstyle="primary")
        right_preview.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Form Controls on Left
        tb.Label(left_ctrl, text="شماره قبض:", font=("Tahoma", 9, "bold")).pack(anchor="e", pady=(5, 2))
        self.rec_ent_id = tb.Entry(left_ctrl, justify="center")
        self.rec_ent_id.insert(0, "001048")
        self.rec_ent_id.pack(fill=tk.X, pady=(0, 6))

        tb.Label(left_ctrl, text="نام مهمان:", font=("Tahoma", 9, "bold")).pack(anchor="e", pady=(5, 2))
        self.rec_ent_name = tb.Entry(left_ctrl, justify="right")
        self.rec_ent_name.insert(0, "محمدرضا سلطانی")
        self.rec_ent_name.pack(fill=tk.X, pady=(0, 6))

        tb.Label(left_ctrl, text="کد ملی:", font=("Tahoma", 9, "bold")).pack(anchor="e", pady=(5, 2))
        self.rec_ent_nid = tb.Entry(left_ctrl, justify="center")
        self.rec_ent_nid.insert(0, "0019876543")
        self.rec_ent_nid.pack(fill=tk.X, pady=(0, 6))

        tb.Label(left_ctrl, text="ملاقات شونده:", font=("Tahoma", 9, "bold")).pack(anchor="e", pady=(5, 2))
        self.rec_ent_emp = tb.Entry(left_ctrl, justify="right")
        self.rec_ent_emp.insert(0, "دکتر علی رضایی")
        self.rec_ent_emp.pack(fill=tk.X, pady=(0, 6))

        tb.Label(left_ctrl, text="واحد مربوطه:", font=("Tahoma", 9, "bold")).pack(anchor="e", pady=(5, 2))
        self.rec_combo_dept = tb.Combobox(left_ctrl, values=config.DEPARTMENT_LIST, justify="right", state="readonly")
        self.rec_combo_dept.set("حوزه مدیر کل")
        self.rec_combo_dept.pack(fill=tk.X, pady=(0, 6))

        tb.Button(left_ctrl, text="🔄 به‌روزرسانی پیش‌نمایش رسید", command=self.update_receipt_preview, bootstyle="primary").pack(fill=tk.X, pady=10)
        tb.Button(left_ctrl, text="🖨️ شبیه‌سازی دستور چاپ (Mock Print)", command=self.simulate_print_job, bootstyle="success").pack(fill=tk.X, pady=5)

        # Receipt Container on Right
        self.receipt_paper = tk.Frame(right_preview, bg="#FFFDF0", bd=2, relief="groove", width=340)
        self.receipt_paper.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)

        self.lbl_rec_header1 = tk.Label(self.receipt_paper, text="«باسمه تعالی»", font=("Tahoma", 10, "bold"), bg="#FFFDF0", fg="#333333")
        self.lbl_rec_header1.pack(pady=(12, 1))

        self.lbl_rec_header2 = tk.Label(self.receipt_paper, text="اداره کل آموزش و پرورش استان همدان", font=("Tahoma", 11, "bold"), bg="#FFFDF0", fg="#111111")
        self.lbl_rec_header2.pack(pady=1)

        self.lbl_rec_header3 = tk.Label(self.receipt_paper, text="(اداره حراست)", font=("Tahoma", 10, "bold"), bg="#FFFDF0", fg="#222222")
        self.lbl_rec_header3.pack(pady=1)

        tk.Label(self.receipt_paper, text="------------------------------------------------", font=("Courier", 10), bg="#FFFDF0", fg="#888888").pack(pady=3)

        self.rec_body_frame = tk.Frame(self.receipt_paper, bg="#FFFDF0")
        self.rec_body_frame.pack(fill=tk.X, padx=20)

        self.update_receipt_preview()

    def update_receipt_preview(self):
        for widget in self.rec_body_frame.winfo_children():
            widget.destroy()

        vid = self.rec_ent_id.get().strip()
        vname = self.rec_ent_name.get().strip()
        nid = self.rec_ent_nid.get().strip()
        emp = self.rec_ent_emp.get().strip()
        dept = self.rec_combo_dept.get().strip()
        now_dt = datetime.now()
        sdate = jdatetime.date.fromgregorian(date=now_dt.date()).strftime("%Y/%m/%d")
        etime = now_dt.strftime("%H:%M")

        def add_line(lbl, val):
            row = tk.Frame(self.rec_body_frame, bg="#FFFDF0")
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=lbl, font=("Tahoma", 10, "bold"), bg="#FFFDF0", fg="#333333").pack(side=tk.RIGHT)
            tk.Label(row, text=val, font=("Tahoma", 10), bg="#FFFDF0", fg="#111111").pack(side=tk.RIGHT, padx=5)

        add_line("شماره قبض:", f"{int(vid) if vid.isdigit() else 1001:06d}")
        add_line("تاریخ ورود:", sdate)
        add_line("ساعت ورود:", etime)
        add_line("ساعت خروج:", "...............")
        
        tk.Label(self.rec_body_frame, text="------------------------------------------------", font=("Courier", 10), bg="#FFFDF0", fg="#888888").pack(pady=3)

        add_line("ملاقات کننده:", vname)
        add_line("کد ملی:", nid)
        add_line("امور / واحد:", dept)
        add_line("ملاقات شونده:", emp)

        tk.Label(self.rec_body_frame, text="------------------------------------------------", font=("Courier", 10), bg="#FFFDF0", fg="#888888").pack(pady=3)

        sig_box = tk.Frame(self.rec_body_frame, bg="#FFFDF0")
        sig_box.pack(fill=tk.X, pady=5)
        tk.Label(sig_box, text="امضاء ملاقات شونده:", font=("Tahoma", 9), bg="#FFFDF0", fg="#666666").pack(anchor="ne")

        tk.Label(self.rec_body_frame, text=f"* {int(vid) if vid.isdigit() else 1001:06d} *", font=("Courier", 10, "bold"), bg="#FFFDF0", fg="#222222").pack(pady=(10, 2))
        tk.Label(self.rec_body_frame, text="* حداکثر زمان حضور در اداره ۲ ساعت می‌باشد *", font=("Tahoma", 8), bg="#FFFDF0", fg="#777777").pack(pady=(0, 10))

    def simulate_print_job(self):
        vid = int(self.rec_ent_id.get()) if self.rec_ent_id.get().isdigit() else 1001
        vname = self.rec_ent_name.get()
        nid = self.rec_ent_nid.get()
        emp = self.rec_ent_emp.get()
        dept = self.rec_combo_dept.get()
        sdate = jdatetime.date.fromgregorian(date=datetime.now().date()).strftime("%Y/%m/%d")
        
        printer.print_receipt(vid, vname, nid, emp, dept, datetime.now(), sdate)
        messagebox.showinfo("شبیه‌سازی پرینت", f"قبض شماره {vid:06d} با موفقیت به صف شبیه‌ساز پرینتر ارسال شد.", parent=self.root)

    # --------------------------------------------------------------------------
    # GLOBAL ACTIONS & EVENT HANDLERS
    # --------------------------------------------------------------------------
    def on_theme_change(self, event=None):
        theme = self.current_theme.get()
        try:
            self.root.style.theme_use(theme)
            self.status_bar.config(text=f"  🎨 تم فعال به '{theme}' تغییر یافت.")
        except Exception as e:
            print(f"Error changing theme: {e}")

    def reset_mock_data(self):
        if messagebox.askyesno("بازنشانی", "آیا از بازنشانی داده‌های موک به حالت اولیه اطمینان دارید؟", parent=self.root):
            mock_db.seed_default_data()
            self.auto_entry.set_completion_list(mock_db.get_employee_suggestions())
            self.refresh_data_table()
            messagebox.showinfo("موفق", "داده‌های موک با موفقیت بازنشانی شدند.", parent=self.root)

    def add_50_mock_records(self):
        mock_db.add_dummy_data()
        self.auto_entry.set_completion_list(mock_db.get_employee_suggestions())
        self.refresh_data_table()
        messagebox.showinfo("موفق", "۵۰ رکورد مراجع تصادفی جدید به حافظه اضافه شد.", parent=self.root)

    def launch_login_screen(self):
        def on_login_success(u, role, full_name):
            messagebox.showinfo(
                "ورود موفق", 
                f"✅ ورود موفقیت‌آمیز کاربر:\n\nنام کاربری: {u}\nنقش: {role}\nنام: {full_name}", 
                parent=self.root
            )
        windows.show_login_screen(self.root, on_login_success)

    def launch_main_dashboard(self):
        """Launches the primary registration dashboard window in preview mode."""
        import main
        main.app.is_logged_in = True
        main.app.current_user = "مهندس سید مهدی حسینی (مدیر سیستم)"
        main.app.current_username = "admin"
        main.app.current_role = self.current_role.get()
        
        main.setup_dashboard("admin", self.current_role.get(), "مهندس سید مهدی حسینی")
        main.app.deiconify()
        
        # Override close behavior so closing main app hides it without killing the preview studio
        main.app.protocol("WM_DELETE_WINDOW", lambda: main.app.withdraw())
        main.app.lift()

    def run(self):
        self.root.mainloop()

# ==============================================================================
# 6. ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    print("====================================================================")
    print("🚀 Running Visitor Management System UI Preview & Style Studio...")
    print("🟢 In-Memory Database Active (Zero SQL Server connection required)")
    print("====================================================================")
    
    app_studio = UIPreviewStudio()
    app_studio.run()

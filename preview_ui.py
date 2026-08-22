"""
Visitor Management System - Enterprise Cyber-Modern & Glassmorphic Dashboard
Run with: python preview_ui.py
Ultra-Modern Persian RTL Security & Visitor Operations Center
"""

import sys
import os
import random
import threading
import tkinter as tk
from tkinter import messagebox, filedialog, font
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from datetime import datetime
import jdatetime
import pandas as pd
from PIL import Image, ImageTk

import matplotlib
import matplotlib.font_manager as fm
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Local modules
import config
import database
import utils
import widgets
import windows
import printer

# --- Dynamic Font Loading ---
utils.load_bundled_fonts()
for f in ['Vazirmatn-Regular.ttf', 'Vazirmatn-Bold.ttf', 'Vazirmatn-Medium.ttf']:
    _fpath = os.path.join('assets', f)
    if os.path.exists(_fpath):
        try:
            fm.fontManager.addfont(_fpath)
        except Exception:
            pass

FONT_FAMILY = "Vazirmatn"
windows.ensure_fonts()

# --- Mock Data Store ---
mock_users = [
    ("admin", "admin", "مهندس حسینی (مدیر ارشد امنیت)"),
    ("guard1", "guard", "علی رضایی (سرپرست شیفت حراست)"),
    ("guard2", "guard", "محمد کریمی (مامور انتظامات ورودی)")
]

mock_employees = [
    ("مهندس رضایی", "امور مالی و حسابداری", 18),
    ("دکتر محمدی", "منابع انسانی و کارگزینی", 14),
    ("خانم مهندس حسینی", "فناوری اطلاعات و شبکه", 12),
    ("مهندس تقوی", "امور اداری و پشتیبانی", 8),
    ("آقای احمدی", "حراست و بازرسی", 6)
]

mock_visitors = [
    ("0012345678", "احمد کریمی", 4),
    ("0098765432", "مریم حسینی", 3),
    ("0054321098", "حسین صادقی", 2),
    ("0076543210", "زهرا کاظمی", 1),
    ("0034567890", "رضا محمدی", 3),
    ("0023456789", "سارا امینی", 2)
]

mock_records = [
    [1, "احمد کریمی", "0012345678", "مهندس رضایی", "امور مالی و حسابداری", "08:15:00", "1404/12/03", "10:30:00", "admin"],
    [2, "مریم حسینی", "0098765432", "دکتر محمدی", "منابع انسانی و کارگزینی", "08:45:00", "1404/12/03", "", "admin"],
    [3, "حسین صادقی", "0054321098", "خانم مهندس حسینی", "فناوری اطلاعات و شبکه", "09:20:00", "1404/12/03", "11:00:00", "guard1"],
    [4, "زهرا کاظمی", "0076543210", "مهندس تقوی", "امور اداری و پشتیبانی", "09:50:00", "1404/12/03", "", "guard1"],
    [5, "رضا محمدی", "0034567890", "دکتر محمدی", "مدیریت عاملی", "10:15:00", "1404/12/03", "12:10:00", "admin"],
    [6, "سارا امینی", "0023456789", "آقای احمدی", "حراست و بازرسی", "10:45:00", "1404/12/03", "", "guard2"],
    [7, "امید جعفری", "0067890123", "مهندس رضایی", "امور مالی و حسابداری", "11:10:00", "1404/12/03", "13:00:00", "admin"],
    [8, "نازنین باقری", "0089012345", "مهندس تقوی", "امور اداری و پشتیبانی", "11:35:00", "1404/12/03", "", "guard1"],
]

# --- Database & Config Mock ---
config.test_connection = lambda cfg: (True, "")
database.setup_database = lambda: None
database.shutdown_pool = lambda: None
database.log_audit = lambda event, **kwargs: print(f"[AUDIT LOG]: {event} -> {kwargs}")
database.authenticate_user = lambda u, p: (True, "admin", "مهندس حسینی (مدیر سیستم)", "")
database.get_all_users = lambda: list(mock_users)
database.create_user = lambda u, p, fname, r: (mock_users.append((u, r, fname)) or True, "")
database.delete_user = lambda u: (True, "")
database.update_user = lambda u, **kw: True
database.change_user_password = lambda u, p: True
database.get_daily_stats = lambda d: (len(mock_records), sum(1 for r in mock_records if not r[7]))
database.get_hourly_stats = lambda **kw: [
    ('08', 4), ('09', 8), ('10', 14), ('11', 10), ('12', 6), ('13', 3), ('14', 9), ('15', 5)
]
database.get_top_departments = lambda **kw: [
    ("امور مالی و حسابداری", 18),
    ("منابع انسانی و کارگزینی", 14),
    ("فناوری اطلاعات و شبکه", 9)
]

def mock_search_visitors(filters, page=1, items_per_page=50):
    name_q = (filters.get("name") or "").strip()
    nid_q = (filters.get("nid") or "").strip()
    dept_q = (filters.get("dept") or "").strip()
    status_q = (filters.get("status") or "").strip()
    filtered = []
    for r in mock_records:
        if name_q and name_q not in r[1]: continue
        if nid_q and nid_q not in r[2]: continue
        if dept_q and dept_q != r[4]: continue
        if status_q == "present" and r[7]: continue
        if status_q == "exited" and not r[7]: continue
        filtered.append(r)
    start = (page - 1) * items_per_page
    end = start + items_per_page
    return len(filtered), filtered[start:end]

database.search_visitors = mock_search_visitors

def mock_add_visitor(v_name, nid, emp, dept, entry_time, shamsi_date, created_by):
    new_id = len(mock_records) + 1
    mock_records.insert(0, [new_id, v_name, nid, emp, dept, datetime.now().strftime("%H:%M:%S"), shamsi_date, "", created_by])
    return new_id

database.add_visitor = mock_add_visitor

def mock_update_exit_time(visitor_id, exit_time_str, operator=None):
    for i, r in enumerate(mock_records):
        if r[0] == int(visitor_id):
            mock_records[i][7] = exit_time_str
            return True
    return True

database.update_exit_time = mock_update_exit_time
database.get_last_department_for_employee = lambda name: next((e[1] for e in mock_employees if e[0] in name), "امور مالی و حسابداری")
database.get_visitor_name_by_nid = lambda nid: next((v[1] for v in mock_visitors if v[0] == nid), None)
database.check_duplicate_entry = lambda *args: False
database.get_employee_suggestions = lambda: [e[0] for e in mock_employees]
database.get_all_unique_employees = lambda: [(e[0], e[2]) for e in mock_employees]
database.get_all_unique_visitors = lambda: list(mock_visitors)
database.get_audit_logs = lambda s, e: [
    (1, "1404/12/03", "08:15:00", "visitor_added", "admin", 1, "احمد کریمی", "0012345678", "مهندس رضایی", "امور مالی", "ثبت ورود", "2026-08-22 08:15:00"),
    (2, "1404/12/03", "10:30:00", "visitor_exit_recorded", "admin", 1, "احمد کریمی", "0012345678", "مهندس رضایی", "امور مالی", "ساعت خروج: 10:30", "2026-08-22 10:30:00")
]
printer.print_receipt = lambda *args: print(f"[PRINTER]: قبض ورود مراجع {args[1]} با موفقیت صادر گردید.")

# --- THEME DESIGN TOKENS ---
C_BG_MAIN = "#0B0F19"       # Deep Cosmic Black
C_BG_SIDEBAR = "#070B14"    # Sidebar Slate
C_BG_CARD = "#111827"       # Glass Surface
C_BG_CARD_HOVER = "#1E293B" # Card Hover State
C_BORDER = "#1E293B"        # Subtle Glass Border
C_BORDER_ACCENT = "#38BDF8" # Electric Cyan Glow

C_CYAN = "#06B6D4"          # Electric Cyan
C_BLUE = "#3B82F6"          # Royal Blue
C_PURPLE = "#A855F7"        # Neon Violet
C_EMERALD = "#10B981"       # Emerald Green
C_AMBER = "#F59E0B"         # Amber Glow
C_ROSE = "#F43F5E"          # Rose Coral

C_TEXT_TITLE = "#F8FAFC"     # White Heading
C_TEXT_BODY = "#E2E8F0"      # Slate 200
C_TEXT_MUTED = "#94A3B8"     # Slate 400
C_TEXT_DIM = "#64748B"       # Slate 500

# --- App Window Initialization ---
app = tb.Window(themename="darkly")
app.title(f"سامانه هوشمند تردد و امنیت مراجعین (اداره حراست) — نسخه ۴.۰")
app.geometry("1340x880")
app.minsize(1200, 780)
app.configure(bg=C_BG_MAIN)

try:
    icon_path = utils.resource_path(os.path.join('assets', 'app_icon.ico'))
    app.iconbitmap(icon_path)
    app.iconbitmap(default=icon_path)
except Exception:
    pass

# Treeview Styles
style = tb.Style()
style.configure('Treeview', 
                font=(FONT_FAMILY, 10), 
                rowheight=40, 
                background="#111827", 
                fieldbackground="#111827", 
                foreground="#F8FAFC")
style.configure('Treeview.Heading', 
                font=(FONT_FAMILY, 10, "bold"), 
                background="#1E293B", 
                foreground="#38BDF8", 
                relief="flat")
style.map('Treeview', 
          background=[('selected', '#0284C7')], 
          foreground=[('selected', '#FFFFFF')])

# ==============================================================================
# 🌟 MAIN MASTER-DETAIL LAYOUT (RIGHT SIDEBAR + MAIN STAGE)
# ==============================================================================
root_layout = tk.Frame(app, bg=C_BG_MAIN)
root_layout.pack(fill=tk.BOTH, expand=True)

# ------------------------------------------------------------------------------
# 📱 RIGHT SIDEBAR: BRANDING & NAVIGATION
# ------------------------------------------------------------------------------
sidebar = tk.Frame(root_layout, bg=C_BG_SIDEBAR, width=280, highlightthickness=1, highlightbackground=C_BORDER)
sidebar.pack(side=tk.RIGHT, fill=tk.Y)
sidebar.pack_propagate(False)

# App Brand Header
brand_container = tk.Frame(sidebar, bg=C_BG_SIDEBAR, padx=18, pady=20)
brand_container.pack(fill=tk.X)

logo_row = tk.Frame(brand_container, bg=C_BG_SIDEBAR)
logo_row.pack(fill=tk.X)

tk.Label(logo_row, text="🛡️", font=(FONT_FAMILY, 24), bg=C_BG_SIDEBAR).pack(side=tk.RIGHT, padx=(0, 10))

title_col = tk.Frame(logo_row, bg=C_BG_SIDEBAR)
title_col.pack(side=tk.RIGHT, fill=tk.X, expand=True)

tk.Label(title_col, text="سامانه هوشمند تردد", font=(FONT_FAMILY, 13, "bold"), bg=C_BG_SIDEBAR, fg=C_TEXT_TITLE, anchor="e").pack(fill=tk.X)
tk.Label(title_col, text="مرکز پایش و حفاظت فیزیکی", font=(FONT_FAMILY, 9), bg=C_BG_SIDEBAR, fg=C_CYAN, anchor="e").pack(fill=tk.X)

# User Profile Card in Sidebar
user_card = tk.Frame(sidebar, bg="#111827", highlightthickness=1, highlightbackground=C_BORDER, padx=14, pady=12)
user_card.pack(fill=tk.X, padx=16, pady=(0, 20))

u_row = tk.Frame(user_card, bg="#111827")
u_row.pack(fill=tk.X)

tk.Label(u_row, text="👤", font=(FONT_FAMILY, 20), bg="#111827", fg=C_PURPLE).pack(side=tk.RIGHT, padx=(0, 8))

u_info = tk.Frame(u_row, bg="#111827")
u_info.pack(side=tk.RIGHT, fill=tk.X, expand=True)

tk.Label(u_info, text="مهندس حسینی", font=(FONT_FAMILY, 10, "bold"), bg="#111827", fg=C_TEXT_TITLE, anchor="e").pack(fill=tk.X)
tk.Label(u_info, text="👑 مدیر ارشد امنیت • آنلاین", font=(FONT_FAMILY, 8), bg="#111827", fg=C_EMERALD, anchor="e").pack(fill=tk.X)

# Navigation Menu List
nav_menu_frame = tk.Frame(sidebar, bg=C_BG_SIDEBAR, padx=12)
nav_menu_frame.pack(fill=tk.BOTH, expand=True)

sidebar_buttons = []

def select_nav_view(index):
    for i, (btn, bar) in enumerate(sidebar_buttons):
        if i == index:
            btn.config(bg="#1E293B", fg="#FFFFFF", font=(FONT_FAMILY, 10, "bold"))
            bar.config(bg=C_CYAN)
        else:
            btn.config(bg=C_BG_SIDEBAR, fg=C_TEXT_MUTED, font=(FONT_FAMILY, 10))
            bar.config(bg=C_BG_SIDEBAR)
            
    for i, view in enumerate(page_views):
        if i == index:
            view.pack(fill=tk.BOTH, expand=True)
        else:
            view.pack_forget()

nav_items = [
    ("📊  پیشخوان و مانیتورینگ زنده", 0),
    ("📝  پذیرش و ثبت تردد سریع", 1),
    ("🔍  سوابق تردد و جستجوی پیشرفته", 2),
    ("📈  هوش سازمانی و نمودارهای تحلیلی", 3),
    ("👥  مدیریت کاربران و دسترسی‌ها", 4),
    ("⚙️  تنظیمات پایگاه داده و سرور", 5),
]

for label_text, idx in nav_items:
    item_row = tk.Frame(nav_menu_frame, bg=C_BG_SIDEBAR)
    item_row.pack(fill=tk.X, pady=4)
    
    # Active indicator vertical pill
    active_pill = tk.Frame(item_row, bg=C_BG_SIDEBAR, width=4)
    active_pill.pack(side=tk.RIGHT, fill=tk.Y)
    
    btn = tk.Button(
        item_row, 
        text=label_text, 
        font=(FONT_FAMILY, 10), 
        bg=C_BG_SIDEBAR, 
        fg=C_TEXT_MUTED, 
        activebackground="#1E293B", 
        activeforeground="#FFFFFF",
        bd=0, 
        anchor="e", 
        padx=14, 
        pady=8, 
        cursor="hand2",
        command=lambda i=idx: select_nav_view(i)
    )
    btn.pack(side=tk.RIGHT, fill=tk.X, expand=True)
    sidebar_buttons.append((btn, active_pill))

# Bottom Health Monitor Widget
system_health = tk.Frame(sidebar, bg="#0F172A", highlightthickness=1, highlightbackground=C_BORDER, padx=14, pady=12)
system_health.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=16)

tk.Label(system_health, text="⚡ وضعیت ارتباط و سرور:", font=(FONT_FAMILY, 9, "bold"), bg="#0F172A", fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X)
tk.Label(system_health, text="🟢 پایگاه داده متصل • پینگ: ۱۲ms", font=(FONT_FAMILY, 9), bg="#0F172A", fg=C_EMERALD, anchor="e").pack(fill=tk.X, pady=(2, 0))

# ------------------------------------------------------------------------------
# 💻 MAIN VIEW STAGE (LEFT 80% AREA)
# ------------------------------------------------------------------------------
main_stage = tk.Frame(root_layout, bg=C_BG_MAIN)
main_stage.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Top Bar (Live Clock + Global Search + Quick Actions)
top_app_bar = tk.Frame(main_stage, bg="#0E1424", height=68, highlightthickness=1, highlightbackground=C_BORDER, padx=20)
top_app_bar.pack(side=tk.TOP, fill=tk.X)
top_app_bar.pack_propagate(False)

# Left: Live Date & Real-time Clock Chip
clock_chip = tk.Frame(top_app_bar, bg="#1E293B", highlightthickness=1, highlightbackground="#334155", padx=14, pady=6)
clock_chip.pack(side=tk.LEFT, pady=16)

clock_text_lbl = tk.Label(clock_chip, text="", font=(FONT_FAMILY, 10, "bold"), bg="#1E293B", fg=C_CYAN)
clock_text_lbl.pack()

def update_live_timer():
    now = datetime.now()
    j_date = jdatetime.date.fromgregorian(date=now.date()).strftime("%Y/%m/%d")
    t_str = now.strftime("%H:%M:%S")
    clock_text_lbl.config(text=f"📅 {j_date}   |   🕒 {t_str}")
    app.after(1000, update_live_timer)

update_live_timer()

# Center Search Filter Input
search_chip = tk.Frame(top_app_bar, bg="#111827", highlightthickness=1, highlightbackground=C_BORDER, padx=10, pady=4)
search_chip.pack(side=tk.RIGHT, pady=16)

tk.Label(search_chip, text="🔍", font=(FONT_FAMILY, 11), bg="#111827", fg=C_CYAN).pack(side=tk.RIGHT, padx=(0, 4))
global_search_ent = tk.Entry(search_chip, justify='right', font=(FONT_FAMILY, 10), bg="#111827", fg="#F8FAFC", insertbackground=C_CYAN, bd=0, width=28)
global_search_ent.pack(side=tk.RIGHT, ipady=3)
global_search_ent.insert(0, "جستجوی مراجع، کدملی، واحد...")

def on_search_focus_in(e):
    if global_search_ent.get() == "جستجوی مراجع، کدملی، واحد...":
        global_search_ent.delete(0, tk.END)

def on_search_focus_out(e):
    if not global_search_ent.get().strip():
        global_search_ent.insert(0, "جستجوی مراجع، کدملی، واحد...")

global_search_ent.bind("<FocusIn>", on_search_focus_in)
global_search_ent.bind("<FocusOut>", on_search_focus_out)

# Main Stage Content Holder
page_views = []
content_area = tk.Frame(main_stage, bg=C_BG_MAIN, padx=20, pady=15)
content_area.pack(fill=tk.BOTH, expand=True)

# ==============================================================================
# 🌟 PAGE 0: DASHBOARD OVERVIEW & LIVE BENTO GRID
# ==============================================================================
page_dashboard = tk.Frame(content_area, bg=C_BG_MAIN)
page_views.append(page_dashboard)

# Top Bento Row: 4 Glowing KPI Metric Tiles
bento_kpi_row = tk.Frame(page_dashboard, bg=C_BG_MAIN)
bento_kpi_row.pack(side=tk.TOP, fill=tk.X, pady=(0, 15))

def create_bento_card(parent, title, value, icon, color, badge_text, progress_pct=0.75):
    card = tk.Frame(parent, bg=C_BG_CARD, highlightthickness=1, highlightbackground=C_BORDER, padx=16, pady=12)
    card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=6)
    
    # Top Accent Glow Line
    tk.Frame(card, bg=color, height=3).pack(fill=tk.X, pady=(0, 8))
    
    top_line = tk.Frame(card, bg=C_BG_CARD)
    top_line.pack(fill=tk.X)
    
    tk.Label(top_line, text=icon, font=(FONT_FAMILY, 16), bg=C_BG_CARD, fg=color).pack(side=tk.RIGHT)
    tk.Label(top_line, text=title, font=(FONT_FAMILY, 9), bg=C_BG_CARD, fg=C_TEXT_MUTED).pack(side=tk.RIGHT, padx=(0, 8))
    
    # Badge
    tk.Label(top_line, text=badge_text, font=(FONT_FAMILY, 8, "bold"), bg="#1F2937", fg=color, padx=6, pady=1).pack(side=tk.LEFT)
    
    v_lbl = tk.Label(card, text=value, font=(FONT_FAMILY, 16, "bold"), bg=C_BG_CARD, fg=C_TEXT_TITLE, anchor="e")
    v_lbl.pack(fill=tk.X, pady=(6, 8))
    
    # Mini Progress Bar
    prog_bg = tk.Frame(card, bg="#1F2937", height=4)
    prog_bg.pack(fill=tk.X)
    prog_fill = tk.Frame(prog_bg, bg=color, height=4)
    prog_fill.place(relx=1.0, rely=0, relwidth=progress_pct, relheight=1.0, anchor="ne")
    
    return v_lbl

bento_1 = create_bento_card(bento_kpi_row, "کل تردد ثبت‌شده امروز", f"{len(mock_records)} مراجع", "👥", C_CYAN, "📈 +۱۸٪ رشد", 0.85)
bento_2 = create_bento_card(bento_kpi_row, "مراجعین حاضر در سازمان", f"{sum(1 for r in mock_records if not r[7])} نفر", "🚪", C_AMBER, "⏳ در جریان", 0.40)
bento_3 = create_bento_card(bento_kpi_row, "پرترددترین واحد کاری", "امور مالی", "🏢", C_PURPLE, "🔥 رتبه ۱", 0.90)
bento_4 = create_bento_card(bento_kpi_row, "وضعیت پایگاه داده و سرور", "فعال و پایدار", "⚡", C_EMERALD, "✓ ۱۰۰٪ متصل", 1.00)

def refresh_bento_kpis():
    tot = len(mock_records)
    pres = sum(1 for r in mock_records if not r[7])
    bento_1.config(text=f"{tot} مراجع")
    bento_2.config(text=f"{pres} نفر")

# Middle Bento Row: Quick Registration Card (Left) + Live Activity Stream Table (Right)
bento_mid_row = tk.Frame(page_dashboard, bg=C_BG_MAIN)
bento_mid_row.pack(fill=tk.BOTH, expand=True)

# Right: Quick Entry Glass Card
quick_form = tk.Frame(bento_mid_row, bg=C_BG_CARD, highlightthickness=1, highlightbackground=C_BORDER, padx=18, pady=16)
quick_form.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
quick_form.config(width=400)
quick_form.pack_propagate(False)

tk.Label(quick_form, text="⚡ پذیرش و صدور مجوز تردد", font=(FONT_FAMILY, 12, "bold"), bg=C_BG_CARD, fg=C_CYAN, anchor="e").pack(fill=tk.X, pady=(0, 10))

tk.Label(quick_form, text="شماره کارت ملی:", font=(FONT_FAMILY, 9, "bold"), bg=C_BG_CARD, fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(4, 2))
dash_nid_ent = tk.Entry(quick_form, justify='right', font=(FONT_FAMILY, 10), bg="#1F2937", fg="#F8FAFC", insertbackground=C_CYAN, bd=0, highlightthickness=1, highlightbackground="#374151", highlightcolor=C_CYAN)
dash_nid_ent.pack(fill=tk.X, pady=(0, 4), ipady=4)

def dash_returning_check(e=None):
    nid = dash_nid_ent.get().strip()
    name = database.get_visitor_name_by_nid(nid)
    if name and not dash_name_ent.get():
        dash_name_ent.delete(0, tk.END)
        dash_name_ent.insert(0, name)

dash_nid_ent.bind("<FocusOut>", dash_returning_check)

tk.Label(quick_form, text="نام و نام خانوادگی:", font=(FONT_FAMILY, 9, "bold"), bg=C_BG_CARD, fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(4, 2))
dash_name_ent = tk.Entry(quick_form, justify='right', font=(FONT_FAMILY, 10), bg="#1F2937", fg="#F8FAFC", insertbackground=C_CYAN, bd=0, highlightthickness=1, highlightbackground="#374151", highlightcolor=C_CYAN)
dash_name_ent.pack(fill=tk.X, pady=(0, 4), ipady=4)

def dash_emp_fill(name):
    dept = database.get_last_department_for_employee(name)
    if dept:
        dash_dept_cb.set(dept)

tk.Label(quick_form, text="ملاقات‌شونده:", font=(FONT_FAMILY, 9, "bold"), bg=C_BG_CARD, fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(4, 2))
dash_emp_ent = widgets.AutocompleteEntry(quick_form, justify='right', font=(FONT_FAMILY, 10), selection_callback=dash_emp_fill)
dash_emp_ent.set_completion_list([e[0] for e in mock_employees])
dash_emp_ent.pack(fill=tk.X, pady=(0, 4))

tk.Label(quick_form, text="واحد سازمانی:", font=(FONT_FAMILY, 9, "bold"), bg=C_BG_CARD, fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(4, 2))
dash_dept_cb = tb.Combobox(quick_form, values=config.DEPARTMENT_LIST, justify='right', state='readonly', font=(FONT_FAMILY, 9))
dash_dept_cb.pack(fill=tk.X, pady=(0, 10))

def submit_dashboard_entry():
    name = dash_name_ent.get().strip()
    nid = dash_nid_ent.get().strip()
    emp = dash_emp_ent.get().strip()
    dept = dash_dept_cb.get().strip()
    if not (name and nid and emp and dept):
        messagebox.showwarning("اطلاعات ناقص", "لطفاً تمامی فیلدهای فرم را با دقت تکمیل فرمایید.", parent=app)
        return
        
    sh_date = jdatetime.date.fromgregorian(date=datetime.now().date()).strftime("%Y/%m/%d")
    v_id = database.add_visitor(name, nid, emp, dept, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sh_date, "admin")
    printer.print_receipt(v_id, name, nid, emp, dept, datetime.now(), sh_date)
    
    for w in [dash_name_ent, dash_nid_ent, dash_emp_ent]:
        w.delete(0, tk.END)
    dash_dept_cb.set("")
    
    refresh_dashboard_table()
    refresh_bento_kpis()
    show_toast(f"✓ پذیرش مراجع ({name}) با شماره قبض {v_id} با موفقیت ثبت شد.", C_EMERALD)

tk.Button(
    quick_form, 
    text="ثبت تردد و چاپ رسید 🖨️", 
    font=(FONT_FAMILY, 10, "bold"), 
    bg="#0284C7", 
    fg="#FFFFFF", 
    activebackground="#0369A1", 
    activeforeground="#FFFFFF",
    bd=0, 
    cursor="hand2", 
    command=submit_dashboard_entry,
    pady=6
).pack(fill=tk.X, pady=(8, 4))

# Left: Live Activity Feed Table
feed_panel = tk.Frame(bento_mid_row, bg=C_BG_CARD, highlightthickness=1, highlightbackground=C_BORDER, padx=16, pady=16)
feed_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

feed_hdr = tk.Frame(feed_panel, bg=C_BG_CARD)
feed_hdr.pack(fill=tk.X, pady=(0, 10))

tk.Label(feed_hdr, text="🕒 جریان زنده مراجعین امروز", font=(FONT_FAMILY, 12, "bold"), bg=C_BG_CARD, fg=C_TEXT_TITLE).pack(side=tk.RIGHT)
tk.Label(feed_hdr, text="💡 با دوبار کلیک بر روی هر سطر، ساعت خروج ثبت می‌شود", font=(FONT_FAMILY, 9), bg=C_BG_CARD, fg=C_CYAN).pack(side=tk.LEFT)

# Quick Filter Chips Row
chips_row = tk.Frame(feed_panel, bg=C_BG_CARD)
chips_row.pack(fill=tk.X, pady=(0, 8))

filter_status_var = "all"

def filter_feed(status):
    global filter_status_var
    filter_status_var = status
    refresh_dashboard_table()

tk.Button(chips_row, text="همه (۸)", font=(FONT_FAMILY, 8, "bold"), bg="#1E293B", fg="#F8FAFC", bd=0, padx=10, pady=2, cursor="hand2", command=lambda: filter_feed("all")).pack(side=tk.RIGHT, padx=3)
tk.Button(chips_row, text="🟢 حاضرین (۳)", font=(FONT_FAMILY, 8, "bold"), bg="#064E3B", fg="#34D399", bd=0, padx=10, pady=2, cursor="hand2", command=lambda: filter_feed("present")).pack(side=tk.RIGHT, padx=3)
tk.Button(chips_row, text="🚪 خارج‌شده (۵)", font=(FONT_FAMILY, 8, "bold"), bg="#312E81", fg="#A5B4FC", bd=0, padx=10, pady=2, cursor="hand2", command=lambda: filter_feed("exited")).pack(side=tk.RIGHT, padx=3)

dash_tree_container = tk.Frame(feed_panel, bg=C_BG_CARD)
dash_tree_container.pack(fill=tk.BOTH, expand=True)

dash_tree = tb.Treeview(
    dash_tree_container,
    columns=("id", "name", "nid", "emp", "dept", "entry", "exit"),
    show='headings'
)
dash_tree.tag_configure('evenrow', background='#0F172A')
dash_tree.tag_configure('oddrow', background='#131D31')

dash_cols = {
    "id": "قبض", "name": "نام مراجع", "nid": "کد ملی", "emp": "ملاقات‌شونده",
    "dept": "واحد مربوطه", "entry": "ساعت ورود", "exit": "وضعیت خروج"
}
for k, v in dash_cols.items():
    dash_tree.heading(k, text=v)
    
dash_tree.column("id", width=55, anchor=tk.CENTER)
dash_tree.column("name", width=140, anchor=tk.CENTER)
dash_tree.column("nid", width=110, anchor=tk.CENTER)
dash_tree.column("emp", width=130, anchor=tk.CENTER)
dash_tree.column("dept", width=160, anchor=tk.CENTER)
dash_tree.column("entry", width=85, anchor=tk.CENTER)
dash_tree.column("exit", width=100, anchor=tk.CENTER)

dash_tree.pack(fill=tk.BOTH, expand=True)

def refresh_dashboard_table():
    for item in dash_tree.get_children():
        dash_tree.delete(item)
        
    filtered = []
    for r in mock_records:
        if filter_status_var == "present" and r[7]: continue
        if filter_status_var == "exited" and not r[7]: continue
        filtered.append(r)
        
    for idx, r in enumerate(filtered):
        tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
        status_chip = f"✓ {r[7]}" if r[7] else "🟢 حاضر در سازمان"
        dash_tree.insert("", tk.END, values=(r[0], r[1], r[2], r[3], r[4], r[5], status_chip), tags=(tag,))

def on_dash_tree_dbl_click(e):
    sel = dash_tree.selection()
    if not sel: return
    vals = dash_tree.item(sel[0], "values")
    v_id, v_name, status = vals[0], vals[1], vals[6]
    if "✓" in status:
        messagebox.showinfo("اطلاع", f"خروج مراجع {v_name} قبلاً ثبت گردیده است.", parent=app)
        return
    now_t = datetime.now().strftime("%H:%M")
    if messagebox.askyesno("ثبت خروج", f"آیا ساعت خروج مراجع ({v_name}) در زمان جاری ({now_t}) ثبت گردد؟", parent=app):
        database.update_exit_time(v_id, now_t)
        refresh_dashboard_table()
        refresh_bento_kpis()
        show_toast(f"✓ خروج مراجع ({v_name}) در ساعت {now_t} ثبت شد.", C_CYAN)

dash_tree.bind("<Double-1>", on_dash_tree_dbl_click)
refresh_dashboard_table()

# ==============================================================================
# 🌟 PAGE 1: DEDICATED QUICK REGISTRATION FORM
# ==============================================================================
page_reg = tk.Frame(content_area, bg=C_BG_MAIN)
page_views.append(page_reg)

reg_center_card = tk.Frame(page_reg, bg=C_BG_CARD, highlightthickness=1, highlightbackground=C_BORDER, padx=30, pady=25)
reg_center_card.place(relx=0.5, rely=0.5, anchor="center", width=520)

tk.Label(reg_center_card, text="🛡️ سامانه پذیرش و ثبت تردد مراجعین", font=(FONT_FAMILY, 14, "bold"), bg=C_BG_CARD, fg=C_TEXT_TITLE).pack(pady=(0, 5))
tk.Label(reg_center_card, text="اطلاعات هویتی و واحد مقصد را با دقت وارد فرمایید", font=(FONT_FAMILY, 9), bg=C_BG_CARD, fg=C_TEXT_MUTED).pack(pady=(0, 20))

def make_reg_field(parent, label_text):
    tk.Label(parent, text=label_text, font=(FONT_FAMILY, 10, "bold"), bg=C_BG_CARD, fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(6, 2))
    ent = tk.Entry(parent, justify='right', font=(FONT_FAMILY, 11), bg="#1F2937", fg="#F8FAFC", insertbackground=C_CYAN, bd=0, highlightthickness=1, highlightbackground="#374151", highlightcolor=C_CYAN)
    ent.pack(fill=tk.X, pady=(0, 6), ipady=6)
    return ent

p1_nid = make_reg_field(reg_center_card, "شماره کارت ملی:")
p1_name = make_reg_field(reg_center_card, "نام و نام خانوادگی مراجع:")

tk.Label(reg_center_card, text="نام ملاقات‌شونده:", font=(FONT_FAMILY, 10, "bold"), bg=C_BG_CARD, fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(6, 2))
p1_emp = widgets.AutocompleteEntry(reg_center_card, justify='right', font=(FONT_FAMILY, 11))
p1_emp.set_completion_list([e[0] for e in mock_employees])
p1_emp.pack(fill=tk.X, pady=(0, 6))

tk.Label(reg_center_card, text="امور / واحد سازمانی:", font=(FONT_FAMILY, 10, "bold"), bg=C_BG_CARD, fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(6, 2))
p1_dept = tb.Combobox(reg_center_card, values=config.DEPARTMENT_LIST, justify='right', state='readonly', font=(FONT_FAMILY, 10))
p1_dept.pack(fill=tk.X, pady=(0, 20))

def submit_p1_reg():
    name = p1_name.get().strip()
    nid = p1_nid.get().strip()
    emp = p1_emp.get().strip()
    dept = p1_dept.get().strip()
    if not (name and nid and emp and dept):
        messagebox.showwarning("خطا", "لطفاً تمام موارد را تکمیل کنید.", parent=app)
        return
    sh_date = jdatetime.date.fromgregorian(date=datetime.now().date()).strftime("%Y/%m/%d")
    v_id = database.add_visitor(name, nid, emp, dept, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sh_date, "admin")
    printer.print_receipt(v_id, name, nid, emp, dept, datetime.now(), sh_date)
    for w in [p1_name, p1_nid, p1_emp]: w.delete(0, tk.END)
    p1_dept.set("")
    refresh_dashboard_table()
    refresh_bento_kpis()
    show_toast(f"✓ ورود مراجع ({name}) با شماره {v_id} ثبت شد.", C_EMERALD)
    select_nav_view(0)

tk.Button(
    reg_center_card, 
    text="ثبت و چاپ رسید 🖨️", 
    font=(FONT_FAMILY, 11, "bold"), 
    bg="#0284C7", 
    fg="#FFFFFF", 
    activebackground="#0369A1", 
    activeforeground="#FFFFFF",
    bd=0, 
    cursor="hand2", 
    command=submit_p1_reg,
    pady=8
).pack(fill=tk.X)

# ==============================================================================
# 🌟 PAGE 2: ADVANCED SEARCH & RECORDS TABLE
# ==============================================================================
page_search = tk.Frame(content_area, bg=C_BG_MAIN)
page_views.append(page_search)

search_card = tk.Frame(page_search, bg=C_BG_CARD, highlightthickness=1, highlightbackground=C_BORDER, padx=20, pady=15)
search_card.pack(fill=tk.BOTH, expand=True)

s_top = tk.Frame(search_card, bg=C_BG_CARD)
s_top.pack(fill=tk.X, pady=(0, 12))

tk.Label(s_top, text="🔍 جستجوی پیشرفته و استخراج سوابق تردد", font=(FONT_FAMILY, 13, "bold"), bg=C_BG_CARD, fg=C_TEXT_TITLE).pack(side=tk.RIGHT)

s_filter_row = tk.Frame(search_card, bg="#0E1424", highlightthickness=1, highlightbackground=C_BORDER, padx=14, pady=10)
s_filter_row.pack(fill=tk.X, pady=(0, 12))

tk.Label(s_filter_row, text="نام مراجع:", font=(FONT_FAMILY, 9, "bold"), bg="#0E1424", fg=C_TEXT_MUTED).pack(side=tk.RIGHT, padx=4)
p2_name_ent = tk.Entry(s_filter_row, justify='right', font=(FONT_FAMILY, 10), bg="#1F2937", fg="#F8FAFC", bd=0, width=16)
p2_name_ent.pack(side=tk.RIGHT, padx=4, ipady=3)

tk.Label(s_filter_row, text="کد ملی:", font=(FONT_FAMILY, 9, "bold"), bg="#0E1424", fg=C_TEXT_MUTED).pack(side=tk.RIGHT, padx=(12, 4))
p2_nid_ent = tk.Entry(s_filter_row, justify='right', font=(FONT_FAMILY, 10), bg="#1F2937", fg="#F8FAFC", bd=0, width=14)
p2_nid_ent.pack(side=tk.RIGHT, padx=4, ipady=3)

tk.Label(s_filter_row, text="واحد سازمانی:", font=(FONT_FAMILY, 9, "bold"), bg="#0E1424", fg=C_TEXT_MUTED).pack(side=tk.RIGHT, padx=(12, 4))
p2_dept_cb = tb.Combobox(s_filter_row, values=[""] + config.DEPARTMENT_LIST, state="readonly", width=18)
p2_dept_cb.pack(side=tk.RIGHT, padx=4)

def do_advanced_search():
    for item in p2_tree.get_children():
        p2_tree.delete(item)
    filters = {
        "name": p2_name_ent.get().strip(),
        "nid": p2_nid_ent.get().strip(),
        "dept": p2_dept_cb.get().strip()
    }
    _, rows = database.search_visitors(filters, 1, 100)
    for idx, r in enumerate(rows):
        tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
        p2_tree.insert("", tk.END, values=(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7] or "🟢 حاضر در سازمان", r[8]), tags=(tag,))

tk.Button(s_filter_row, text="اعمال فیلتر 🔍", font=(FONT_FAMILY, 9, "bold"), bg="#0284C7", fg="#FFFFFF", bd=0, padx=12, pady=4, cursor="hand2", command=do_advanced_search).pack(side=tk.LEFT, padx=4)
tk.Button(s_filter_row, text="خروجی اکسل 📊", font=(FONT_FAMILY, 9, "bold"), bg="#10B981", fg="#FFFFFF", bd=0, padx=12, pady=4, cursor="hand2", command=lambda: messagebox.showinfo("اکسل", "گزارش با ۸ رکورد استخراج شد.", parent=app)).pack(side=tk.LEFT, padx=4)

p2_tree_container = tk.Frame(search_card, bg=C_BG_CARD)
p2_tree_container.pack(fill=tk.BOTH, expand=True)

p2_tree = tb.Treeview(
    p2_tree_container,
    columns=("id", "name", "nid", "emp", "dept", "entry", "date", "exit", "user"),
    show='headings'
)
p2_tree.tag_configure('evenrow', background='#0F172A')
p2_tree.tag_configure('oddrow', background='#131D31')

all_cols = {
    "id": "شناسه", "name": "نام مراجع", "nid": "شماره ملی", "emp": "ملاقات‌شونده",
    "dept": "امور / واحد", "entry": "ساعت ورود", "date": "تاریخ", "exit": "ساعت خروج", "user": "ثبت‌کننده"
}
for k, v in all_cols.items():
    p2_tree.heading(k, text=v)
    p2_tree.column(k, anchor=tk.CENTER)

p2_tree.pack(fill=tk.BOTH, expand=True)
do_advanced_search()

# ==============================================================================
# 🌟 PAGE 3: ANALYTICS & INTELLIGENCE HUB
# ==============================================================================
page_analytics = tk.Frame(content_area, bg=C_BG_MAIN)
page_views.append(page_analytics)

analytics_container = tk.Frame(page_analytics, bg=C_BG_CARD, highlightthickness=1, highlightbackground=C_BORDER, padx=20, pady=18)
analytics_container.pack(fill=tk.BOTH, expand=True)

def render_master_chart():
    for w in analytics_container.winfo_children():
        w.destroy()
        
    top_r = tk.Frame(analytics_container, bg=C_BG_CARD)
    top_r.pack(fill=tk.X, pady=(0, 12))
    tk.Label(top_r, text="📊 تحلیل هوشمند ترافیک و توزیع زمانی مراجعین", font=(FONT_FAMILY, 13, "bold"), bg=C_BG_CARD, fg=C_TEXT_TITLE).pack(side=tk.RIGHT)
    tk.Button(top_r, text="🔄 به‌روزرسانی تحلیل", font=(FONT_FAMILY, 9), bg="#1E293B", fg=C_CYAN, bd=0, padx=12, pady=4, cursor="hand2", command=render_master_chart).pack(side=tk.LEFT)
    
    fig = Figure(figsize=(9, 4.8), dpi=100)
    fig.patch.set_facecolor('#111827')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#0B0F19')
    
    hours = [f"{h:02d}" for h in range(7, 18)]
    counts = [1, 5, 12, 18, 14, 6, 4, 11, 8, 3, 1]
    colors = ['#38BDF8' if c < 10 else ('#818CF8' if c < 15 else '#C084FC') for c in counts]
    
    bars = ax.bar(hours, counts, color=colors, edgecolor='#1E293B', width=0.55, zorder=3)
    ax.set_title(utils.make_farsi("نمودار پراکندگی تردد ساعتی مراجعین در طول روز"), fontname=FONT_FAMILY, fontsize=12, fontweight='bold', color='#F8FAFC', pad=12)
    ax.set_xlabel(utils.make_farsi("ساعت شبانه‌روز"), fontname=FONT_FAMILY, fontsize=10, color='#94A3B8')
    ax.set_ylabel(utils.make_farsi("تعداد مراجعین"), fontname=FONT_FAMILY, fontsize=10, color='#94A3B8')
    ax.tick_params(colors='#94A3B8')
    ax.grid(axis='y', linestyle='--', color='#1E293B', alpha=0.9, zorder=0)
    
    for bar in bars:
        h_val = bar.get_height()
        if h_val > 0:
            ax.text(bar.get_x() + bar.get_width()/2., h_val + 0.2, f'{int(h_val)}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold', color='#F8FAFC')
                    
    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=analytics_container)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

render_master_chart()

# ==============================================================================
# 🌟 PAGE 4: USER MANAGER & ACCESS CONTROL
# ==============================================================================
page_users = tk.Frame(content_area, bg=C_BG_MAIN)
page_views.append(page_users)

user_stage_card = tk.Frame(page_users, bg=C_BG_CARD, highlightthickness=1, highlightbackground=C_BORDER, padx=25, pady=20)
user_stage_card.pack(fill=tk.BOTH, expand=True)

tk.Label(user_stage_card, text="👥 مدیریت کاربران و سطوح دسترسی", font=(FONT_FAMILY, 14, "bold"), bg=C_BG_CARD, fg=C_TEXT_TITLE).pack(anchor="e", pady=(0, 15))

user_split = tk.Frame(user_stage_card, bg=C_BG_CARD)
user_split.pack(fill=tk.BOTH, expand=True)

# User List Box
u_left = tk.Frame(user_split, bg="#0E1424", highlightthickness=1, highlightbackground=C_BORDER, padx=14, pady=12)
u_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

tk.Label(u_left, text="لیست حساب‌های فعال در سامانه:", font=(FONT_FAMILY, 10, "bold"), bg="#0E1424", fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(0, 8))

u_listbox = tk.Listbox(u_left, font=(FONT_FAMILY, 10), bg="#111827", fg="#F8FAFC", selectbackground="#0284C7", selectforeground="#FFFFFF", bd=0, highlightthickness=1, highlightbackground="#1E293B")
u_listbox.pack(fill=tk.BOTH, expand=True)

for u, r, fname in mock_users:
    role_icon = "👑 مدیر ارشد" if r == "admin" else "🛡️ حراست"
    u_listbox.insert(tk.END, f"  {role_icon}  |  {fname}  ({u})")

# User Actions
u_right = tk.Frame(user_split, bg="#0E1424", highlightthickness=1, highlightbackground=C_BORDER, padx=18, pady=15)
u_right.pack(side=tk.RIGHT, fill=tk.Y)
u_right.config(width=340)
u_right.pack_propagate(False)

tk.Label(u_right, text="افزودن کاربر جدید", font=(FONT_FAMILY, 11, "bold"), bg="#0E1424", fg=C_CYAN, anchor="e").pack(fill=tk.X, pady=(0, 10))

tk.Label(u_right, text="نام و نام خانوادگی:", font=(FONT_FAMILY, 9), bg="#0E1424", fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(4, 2))
nu_name = tk.Entry(u_right, justify='right', font=(FONT_FAMILY, 10), bg="#1F2937", fg="#F8FAFC", bd=0)
nu_name.pack(fill=tk.X, ipady=3)

tk.Label(u_right, text="نام کاربری:", font=(FONT_FAMILY, 9), bg="#0E1424", fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(6, 2))
nu_user = tk.Entry(u_right, justify='right', font=(FONT_FAMILY, 10), bg="#1F2937", fg="#F8FAFC", bd=0)
nu_user.pack(fill=tk.X, ipady=3)

tk.Label(u_right, text="رمز عبور:", font=(FONT_FAMILY, 9), bg="#0E1424", fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(6, 2))
nu_pass = tk.Entry(u_right, show="●", justify='right', font=(FONT_FAMILY, 10), bg="#1F2937", fg="#F8FAFC", bd=0)
nu_pass.pack(fill=tk.X, ipady=3, pady=(0, 15))

def add_new_user_action():
    fn, un, pw = nu_name.get().strip(), nu_user.get().strip(), nu_pass.get().strip()
    if not (fn and un and pw):
        messagebox.showwarning("خطا", "تمام فیلدها را پر کنید.", parent=app)
        return
    mock_users.append((un, "guard", fn))
    u_listbox.insert(tk.END, f"  🛡️ حراست  |  {fn}  ({un})")
    for w in [nu_name, nu_user, nu_pass]: w.delete(0, tk.END)
    show_toast(f"✓ کاربر ({fn}) با موفقیت ایجاد شد.", C_EMERALD)

tk.Button(u_right, text="ثبت کاربر جدید ➕", font=(FONT_FAMILY, 10, "bold"), bg="#10B981", fg="#FFFFFF", bd=0, pady=6, cursor="hand2", command=add_new_user_action).pack(fill=tk.X)

# ==============================================================================
# 🌟 PAGE 5: SERVER SETTINGS & POPUP LAUNCHER
# ==============================================================================
page_settings = tk.Frame(content_area, bg=C_BG_MAIN)
page_views.append(page_settings)

settings_card = tk.Frame(page_settings, bg=C_BG_CARD, highlightthickness=1, highlightbackground=C_BORDER, padx=25, pady=20)
settings_card.pack(fill=tk.BOTH, expand=True)

tk.Label(settings_card, text="⚙️ تنظیمات سامانه و پرتابل ابزارهای مدیریتی", font=(FONT_FAMILY, 14, "bold"), bg=C_BG_CARD, fg=C_TEXT_TITLE).pack(anchor="e", pady=(0, 15))

tools_grid = tk.Frame(settings_card, bg=C_BG_CARD)
tools_grid.pack(fill=tk.BOTH, expand=True)

def create_action_tile(parent, r, c, title, desc, icon, color, cmd):
    tile = tk.Frame(parent, bg="#131B2E", highlightthickness=1, highlightbackground="#1E293B", padx=16, pady=14)
    tile.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
    tk.Frame(tile, bg=color, height=3).pack(fill=tk.X, pady=(0, 8))
    
    top = tk.Frame(tile, bg="#131B2E")
    top.pack(fill=tk.X)
    tk.Label(top, text=icon, font=(FONT_FAMILY, 16), bg="#131B2E", fg=color).pack(side=tk.RIGHT)
    tk.Label(top, text=title, font=(FONT_FAMILY, 11, "bold"), bg="#131B2E", fg="#F8FAFC").pack(side=tk.RIGHT, padx=(0, 8))
    
    tk.Label(tile, text=desc, font=(FONT_FAMILY, 9), bg="#131B2E", fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(6, 10))
    tk.Button(tile, text="باز کردن پنجره ➔", font=(FONT_FAMILY, 9, "bold"), bg=color, fg="#FFFFFF", bd=0, padx=12, pady=4, cursor="hand2", command=cmd).pack(anchor="w")

create_action_tile(tools_grid, 0, 0, "تنظیمات اتصال به سرور SQL", "پیکربندی هاست، نام دیتابیس و درایور ODBC", "⚙️", C_CYAN, lambda: windows.open_server_settings(app))
create_action_tile(tools_grid, 0, 1, "آمار تردد در تاریخ انتخابی", "محاسبه دقیق تردد و گزارش خروج‌های ثبت‌نشده", "📊", C_AMBER, lambda: windows.show_daily_stats_ui(app))
create_action_tile(tools_grid, 1, 0, "تحلیل آماری و نمودارهای تردد", "مشاهده نمودار تخصصی در پنجره جداگانه", "📈", C_PURPLE, lambda: windows.show_heatmap_analytics(app))
create_action_tile(tools_grid, 1, 1, "گزارش لاگ حسابرسی اکسل", "استخراج تمامی رویدادها در بازه زمانی", "📑", C_EMERALD, lambda: windows.export_audit_log_excel(app, app=app))
create_action_tile(tools_grid, 2, 0, "اصلاح داده‌های تکمیل خودکار", "پاکسازی و ادغام اسامی اشتباه پرسنل و مراجعین", "✏️", C_BLUE, lambda: windows.open_data_cleanup_window(app))
create_action_tile(tools_grid, 2, 1, "صفحه ورود به سیستم", "پیش‌نمایش فرم احراز هویت نگهبانان", "🚪", C_ROSE, lambda: windows.show_login_screen(app, lambda u, r, f: None))

tools_grid.columnconfigure(0, weight=1)
tools_grid.columnconfigure(1, weight=1)

# Default to Page 0
select_nav_view(0)

# ==============================================================================
# 🌟 BOTTOM NOTIFICATION TOAST & STATUS
# ==============================================================================
toast_bar = tk.Label(
    app, 
    text="  با سلام — به پیشخوان هوشمند مانیتورینگ تردد و امنیت مراجعین خوش آمدید.", 
    font=(FONT_FAMILY, 10), 
    bg="#070B14", 
    fg=C_CYAN, 
    anchor="e", 
    padx=20, 
    pady=8,
    highlightthickness=1,
    highlightbackground=C_BORDER
)
toast_bar.pack(side=tk.BOTTOM, fill=tk.X)

toast_timer = None
def show_toast(msg, color=C_EMERALD):
    global toast_timer
    if toast_timer:
        app.after_cancel(toast_timer)
    toast_bar.config(text=f"  {msg}", fg=color)
    toast_timer = app.after(6000, lambda: toast_bar.config(text="  سامانه هوشمند در وضعیت پایش آنلاین و ایمن قرار دارد.", fg=C_CYAN))

if __name__ == "__main__":
    print("==================================================================")
    print("🚀 Running Cyber-Modern & Glassmorphism Enterprise Master Dashboard")
    print("✨ Featuring: Master-Detail Layout, Bento KPIs, & Interactive Hub")
    print("==================================================================")
    app.mainloop()

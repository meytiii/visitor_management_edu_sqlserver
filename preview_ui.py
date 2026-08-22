"""
Visitor Management System - Next-Gen Glassmorphism & Cyber-Modern UI/UX
Run this script with: python preview_ui.py
Ultra-modern Glassmorphic Dark & Vibrant Persian RTL Enterprise Dashboard
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

# --- Ensure Fonts & Dynamic Registration ---
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

# --- In-Memory Mock Data Store ---
mock_users = [
    ("admin", "admin", "مهندس حسینی (مدیر سیستم)"),
    ("guard1", "guard", "علی رضایی (سرپرست انتظامات)"),
    ("guard2", "guard", "محمد کریمی (مامور حراست)")
]

mock_employees = [
    ("مهندس رضایی", "امور مالی", 15),
    ("دکتر محمدی", "منابع انسانی", 12),
    ("خانم حسینی", "فناوری اطلاعات", 9),
    ("مهندس تقوی", "امور اداری", 7),
    ("آقای احمدی", "حراست و انتظامات", 5)
]

mock_visitors = [
    ("0012345678", "احمد کریمی", 4),
    ("0098765432", "مریم حسینی", 3),
    ("0054321098", "حسین صادقی", 2),
    ("0076543210", "زهرا کاظمی", 1)
]

mock_records = [
    [1, "احمد کریمی", "0012345678", "مهندس رضایی", "امور مالی", "08:15:00", "1404/12/03", "10:30:00", "admin"],
    [2, "مریم حسینی", "0098765432", "دکتر محمدی", "منابع انسانی", "08:45:00", "1404/12/03", "", "admin"],
    [3, "حسین صادقی", "0054321098", "خانم حسینی", "فناوری اطلاعات", "09:20:00", "1404/12/03", "11:00:00", "guard1"],
    [4, "زهرا کاظمی", "0076543210", "مهندس تقوی", "امور اداری", "09:50:00", "1404/12/03", "", "guard1"],
    [5, "رضا محمدی", "0034567890", "دکتر محمدی", "مدیریت", "10:15:00", "1404/12/03", "12:10:00", "admin"],
    [6, "سارا امینی", "0023456789", "آقای احمدی", "حراست و انتظامات", "10:45:00", "1404/12/03", "", "guard2"],
    [7, "امید جعفری", "0067890123", "مهندس رضایی", "امور مالی", "11:10:00", "1404/12/03", "13:00:00", "admin"],
    [8, "نازنین باقری", "0089012345", "مهندس تقوی", "امور اداری", "11:35:00", "1404/12/03", "", "guard1"],
]

# --- Mock Database Engine ---
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
    ("منابع انسانی و رفاه", 14),
    ("فناوری اطلاعات و شبکه", 9)
]

def mock_search_visitors(filters, page=1, items_per_page=50):
    name_q = (filters.get("name") or "").strip()
    nid_q = (filters.get("nid") or "").strip()
    dept_q = (filters.get("dept") or "").strip()
    filtered = []
    for r in mock_records:
        if name_q and name_q not in r[1]: continue
        if nid_q and nid_q not in r[2]: continue
        if dept_q and dept_q != r[4]: continue
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
database.get_last_department_for_employee = lambda name: "امور مالی" if "رضایی" in name else "منابع انسانی"
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

# --- GLASSMORPHISM COLOR TOKENS ---
C_BG_DARK = "#090D16"         # Deep Space Black
C_BG_CARD = "#111827"         # Frosted Dark Glass Surface
C_BG_CARD_HOVER = "#1F2937"   # Hover Glass
C_BORDER = "#1E293B"          # Subtle Translucent Border
C_BORDER_GLOW = "#38BDF8"     # Electric Sky Active Glow

C_CYAN = "#06B6D4"            # Vibrant Cyan
C_BLUE = "#3B82F6"            # Royal Azure
C_PURPLE = "#8B5CF6"          # Neon Violet
C_EMERALD = "#10B981"         # Emerald Green
C_AMBER = "#F59E0B"           # Amber Coral
C_ROSE = "#F43F5E"            # Rose Glow

C_TEXT_MAIN = "#F8FAFC"       # Pure Crisp White
C_TEXT_MUTED = "#94A3B8"      # Slate 400
C_TEXT_DIM = "#64748B"        # Slate 500

# --- App Window Initialization ---
app = tb.Window(themename="darkly")
app.title(f"سامانه هوشمند مراجعین (اداره حراست) — رابط کاربری گلس‌مورفیک {config.APP_VERSION}")
app.geometry("1260x840")
app.minsize(1150, 750)
app.configure(bg=C_BG_DARK)

try:
    icon_path = utils.resource_path(os.path.join('assets', 'app_icon.ico'))
    app.iconbitmap(icon_path)
    app.iconbitmap(default=icon_path)
except Exception:
    pass

# Configure Dark Custom TTK Styles
style = tb.Style()
style.configure('Treeview', 
                font=(FONT_FAMILY, 10), 
                rowheight=38, 
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

# ==========================================
# 🌌 TOP GLASS NAVIGATION BAR
# ==========================================
nav_bar = tk.Frame(app, bg="#0D1322", height=72, highlightthickness=1, highlightbackground="#1E293B")
nav_bar.pack(side=tk.TOP, fill=tk.X)
nav_bar.pack_propagate(False)

# Left: Live Date & Clock Glass Badge
clock_badge = tk.Frame(nav_bar, bg="#131D31", highlightthickness=1, highlightbackground="#223354", padx=16, pady=6)
clock_badge.pack(side=tk.LEFT, padx=20, pady=16)

clock_lbl = tk.Label(
    clock_badge, 
    text="", 
    font=(FONT_FAMILY, 11, "bold"), 
    bg="#131D31", 
    fg="#38BDF8"
)
clock_lbl.pack()

def update_clock():
    now = datetime.now()
    j_date = jdatetime.date.fromgregorian(date=now.date()).strftime("%Y/%m/%d")
    t_str = now.strftime("%H:%M:%S")
    clock_lbl.config(text=f"📅 {j_date}   |   🕒 {t_str}")
    app.after(1000, update_clock)

update_clock()

# Right: Brand Identity
brand_box = tk.Frame(nav_bar, bg="#0D1322")
brand_box.pack(side=tk.RIGHT, padx=20, pady=10)

brand_title = tk.Label(
    brand_box, 
    text="سامانه هوشمند تردد و پایش مراجعین", 
    font=(FONT_FAMILY, 14, "bold"), 
    bg="#0D1322", 
    fg="#F8FAFC"
)
brand_title.pack(anchor="e")

brand_sub = tk.Label(
    brand_box, 
    text="مرکز مدیریت و حفاظت اطلاعات سازمانی • اداره حراست و انتظامات", 
    font=(FONT_FAMILY, 9), 
    bg="#0D1322", 
    fg="#38BDF8"
)
brand_sub.pack(anchor="e")

# User Badge Pill
user_pill = tk.Label(
    nav_bar,
    text="🛡️ مهندس حسینی  |  👑 مدیر ارشد سیستم",
    font=(FONT_FAMILY, 10, "bold"),
    bg="#1E1B4B",
    fg="#C084FC",
    padx=16,
    pady=6,
    highlightthickness=1,
    highlightbackground="#4338CA"
)
user_pill.pack(side=tk.RIGHT, padx=(0, 20), pady=18)

# ==========================================
# 💎 VIBRANT GLASS KPI CARDS
# ==========================================
kpi_container = tk.Frame(app, bg=C_BG_DARK, height=95)
kpi_container.pack(side=tk.TOP, fill=tk.X, padx=20, pady=(15, 8))

def create_glass_kpi(parent, title, val, icon, accent_color, badge_text):
    # Outer Glass Card with colored accent top border
    card = tk.Frame(parent, bg="#111827", highlightthickness=1, highlightbackground="#1E293B", padx=14, pady=10)
    card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=6)
    
    # Top Accent Glow Line
    accent_bar = tk.Frame(card, bg=accent_color, height=3)
    accent_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))
    
    content = tk.Frame(card, bg="#111827")
    content.pack(fill=tk.BOTH, expand=True)
    
    # Left: Icon with glowing circle background
    icon_box = tk.Label(
        content, 
        text=icon, 
        font=(FONT_FAMILY, 18), 
        bg="#111827", 
        fg=accent_color
    )
    icon_box.pack(side=tk.RIGHT, padx=(0, 10))
    
    info_box = tk.Frame(content, bg="#111827")
    info_box.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    t_lbl = tk.Label(info_box, text=title, font=(FONT_FAMILY, 9), bg="#111827", fg=C_TEXT_MUTED, anchor="e")
    t_lbl.pack(fill=tk.X)
    
    v_row = tk.Frame(info_box, bg="#111827")
    v_row.pack(fill=tk.X)
    
    v_lbl = tk.Label(v_row, text=val, font=(FONT_FAMILY, 14, "bold"), bg="#111827", fg=C_TEXT_MAIN, anchor="e")
    v_lbl.pack(side=tk.RIGHT)
    
    badge = tk.Label(v_row, text=badge_text, font=(FONT_FAMILY, 8, "bold"), bg="#1E293B", fg=accent_color, padx=6, pady=1)
    badge.pack(side=tk.LEFT)
    
    return v_lbl

kpi_1 = create_glass_kpi(kpi_container, "کل مراجعین امروز", f"{len(mock_records)} نفر", "👥", C_CYAN, "+۱۲٪ رشد")
kpi_2 = create_glass_kpi(kpi_container, "مراجعین حاضر در سازمان", f"{sum(1 for r in mock_records if not r[7])} نفر", "🚪", C_AMBER, "نیاز به خروج")
kpi_3 = create_glass_kpi(kpi_container, "پرترددترین واحد کاری", "امور مالی", "🏢", C_PURPLE, "۲۴ تردد")
kpi_4 = create_glass_kpi(kpi_container, "وضعیت امنیت و سرور", "فعال و ایمن", "⚡", C_EMERALD, "۱۰۰٪ متصل")

def update_kpis():
    tot = len(mock_records)
    pres = sum(1 for r in mock_records if not r[7])
    kpi_1.config(text=f"{tot} نفر")
    kpi_2.config(text=f"{pres} نفر")

# ==========================================
# 🔮 GLASS TAB SYSTEM
# ==========================================
tab_control_bar = tk.Frame(app, bg=C_BG_DARK)
tab_control_bar.pack(fill=tk.X, padx=20, pady=(5, 10))

tabs_frame = tk.Frame(tab_control_bar, bg="#0D1322", highlightthickness=1, highlightbackground="#1E293B", padx=6, pady=4)
tabs_frame.pack(side=tk.RIGHT)

tab_buttons = []
tab_views = []

view_container = tk.Frame(app, bg=C_BG_DARK)
view_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

def switch_tab(index):
    for i, btn in enumerate(tab_buttons):
        if i == index:
            btn.config(bg="#0284C7", fg="#FFFFFF", font=(FONT_FAMILY, 10, "bold"))
        else:
            btn.config(bg="#0D1322", fg=C_TEXT_MUTED, font=(FONT_FAMILY, 10))
    for i, view in enumerate(tab_views):
        if i == index:
            view.pack(fill=tk.BOTH, expand=True)
        else:
            view.pack_forget()

tab_names = [
    ("⚡ پذیرش و تردد سریع", 0),
    ("🔍 سوابق جامع و جستجو", 1),
    ("📊 مانیتورینگ و هوش آماری", 2),
    ("🛠️ مرکز کنترل و ابزارها", 3)
]

for name, idx in tab_names:
    b = tk.Button(
        tabs_frame, 
        text=name, 
        font=(FONT_FAMILY, 10),
        bg="#0D1322", 
        fg=C_TEXT_MUTED, 
        activebackground="#0284C7", 
        activeforeground="#FFFFFF",
        bd=0, 
        padx=18, 
        pady=6, 
        cursor="hand2",
        command=lambda i=idx: switch_tab(i)
    )
    b.pack(side=tk.RIGHT, padx=3)
    tab_buttons.append(b)

# ==========================================
# 🌟 VIEW 1: REGISTRATION & LIVE FEED
# ==========================================
view_reg = tk.Frame(view_container, bg=C_BG_DARK)
tab_views.append(view_reg)

# Left Glass Form Card
reg_card = tk.Frame(view_reg, bg="#111827", highlightthickness=1, highlightbackground="#1E293B", padx=22, pady=18)
reg_card.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
reg_card.config(width=430)
reg_card.pack_propagate(False)

tk.Label(
    reg_card, 
    text="📝 صدور مجوز ورود مراجع", 
    font=(FONT_FAMILY, 13, "bold"), 
    bg="#111827", 
    fg=C_CYAN, 
    anchor="e"
).pack(fill=tk.X, pady=(0, 15))

def create_glass_input(parent, label_text):
    tk.Label(parent, text=label_text, font=(FONT_FAMILY, 10, "bold"), bg="#111827", fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(6, 2))
    ent = tk.Entry(parent, justify='right', font=(FONT_FAMILY, 11), bg="#1F2937", fg="#F8FAFC", insertbackground="#38BDF8", bd=0, highlightthickness=1, highlightbackground="#374151", highlightcolor="#0284C7")
    ent.pack(fill=tk.X, pady=(0, 4), ipady=5)
    return ent

tk.Label(reg_card, text="شماره کارت ملی:", font=(FONT_FAMILY, 10, "bold"), bg="#111827", fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(6, 2))
reg_nid_ent = tk.Entry(reg_card, justify='right', font=(FONT_FAMILY, 11), bg="#1F2937", fg="#F8FAFC", insertbackground="#38BDF8", bd=0, highlightthickness=1, highlightbackground="#374151", highlightcolor="#0284C7")
reg_nid_ent.pack(fill=tk.X, pady=(0, 4), ipady=5)

def check_returning_user(e=None):
    nid = reg_nid_ent.get().strip()
    name = database.get_visitor_name_by_nid(nid)
    if name and not reg_name_ent.get():
        reg_name_ent.delete(0, tk.END)
        reg_name_ent.insert(0, name)

reg_nid_ent.bind("<FocusOut>", check_returning_user)

tk.Label(reg_card, text="نام و نام خانوادگی مراجع:", font=(FONT_FAMILY, 10, "bold"), bg="#111827", fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(6, 2))
reg_name_ent = tk.Entry(reg_card, justify='right', font=(FONT_FAMILY, 11), bg="#1F2937", fg="#F8FAFC", insertbackground="#38BDF8", bd=0, highlightthickness=1, highlightbackground="#374151", highlightcolor="#0284C7")
reg_name_ent.pack(fill=tk.X, pady=(0, 4), ipady=5)

def on_select_emp(emp_name):
    dept = database.get_last_department_for_employee(emp_name)
    if dept:
        reg_dept_cb.set(dept)

tk.Label(reg_card, text="ملاقات‌شونده (تکمیل خودکار):", font=(FONT_FAMILY, 10, "bold"), bg="#111827", fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(6, 2))
reg_emp_ent = widgets.AutocompleteEntry(reg_card, justify='right', font=(FONT_FAMILY, 11), selection_callback=on_select_emp)
reg_emp_ent.set_completion_list([e[0] for e in mock_employees])
reg_emp_ent.pack(fill=tk.X, pady=(0, 4))

tk.Label(reg_card, text="امور / واحد سازمانی:", font=(FONT_FAMILY, 10, "bold"), bg="#111827", fg=C_TEXT_MUTED, anchor="e").pack(fill=tk.X, pady=(6, 2))
reg_dept_cb = tb.Combobox(reg_card, values=config.DEPARTMENT_LIST, justify='right', state='readonly', font=(FONT_FAMILY, 10))
reg_dept_cb.pack(fill=tk.X, pady=(0, 15))

def submit_glass_visitor():
    name = reg_name_ent.get().strip()
    nid = reg_nid_ent.get().strip()
    emp = reg_emp_ent.get().strip()
    dept = reg_dept_cb.get().strip()
    
    if not (name and nid and emp and dept):
        messagebox.showwarning("خطای اعتبارسنجی", "لطفاً تمام فیلدهای فرم را با دقت تکمیل کنید.", parent=app)
        return
        
    sh_date = jdatetime.date.fromgregorian(date=datetime.now().date()).strftime("%Y/%m/%d")
    v_id = database.add_visitor(name, nid, emp, dept, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sh_date, "admin")
    printer.print_receipt(v_id, name, nid, emp, dept, datetime.now(), sh_date)
    
    for w in [reg_name_ent, reg_nid_ent, reg_emp_ent]:
        w.delete(0, tk.END)
    reg_dept_cb.set("")
    
    refresh_live_feed()
    refresh_search_view()
    update_kpis()
    show_toast(f"✓ تردد مراجع ({name}) با شماره قبض {v_id} ثبت شد.", C_EMERALD)

btn_submit = tk.Button(
    reg_card, 
    text="ثبت ورود و صدور برگه تردد 🖨️", 
    font=(FONT_FAMILY, 11, "bold"), 
    bg="#0284C7", 
    fg="#FFFFFF", 
    activebackground="#0369A1", 
    activeforeground="#FFFFFF",
    bd=0, 
    cursor="hand2", 
    command=submit_glass_visitor,
    pady=8
)
btn_submit.pack(fill=tk.X, pady=(10, 8))

# Right Column: Live Feed Glass Table
live_feed_box = tk.Frame(view_reg, bg="#111827", highlightthickness=1, highlightbackground="#1E293B", padx=16, pady=16)
live_feed_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

live_top_row = tk.Frame(live_feed_box, bg="#111827")
live_top_row.pack(fill=tk.X, pady=(0, 12))

tk.Label(live_top_row, text="⚡ پایش زنده تردد مراجعین در ساعات جاری", font=(FONT_FAMILY, 12, "bold"), bg="#111827", fg="#F8FAFC").pack(side=tk.RIGHT)
tk.Label(live_top_row, text="برای ثبت سریع خروج، روی هر ردیف ۲ بار کلیک کنید", font=(FONT_FAMILY, 9), bg="#111827", fg=C_CYAN).pack(side=tk.LEFT)

feed_tree_container = tk.Frame(live_feed_box, bg="#111827")
feed_tree_container.pack(fill=tk.BOTH, expand=True)

glass_feed_tree = tb.Treeview(
    feed_tree_container,
    columns=("id", "name", "nid", "emp", "dept", "entry", "exit"),
    show='headings'
)
glass_feed_tree.tag_configure('evenrow', background='#0F172A')
glass_feed_tree.tag_configure('oddrow', background='#131D31')

feed_cols = {
    "id": "قبض", "name": "نام مراجع", "nid": "کد ملی", "emp": "ملاقات‌شونده",
    "dept": "واحد مربوطه", "entry": "ساعت ورود", "exit": "وضعیت خروج"
}
for col_id, col_text in feed_cols.items():
    glass_feed_tree.heading(col_id, text=col_text)
    
glass_feed_tree.column("id", width=55, anchor=tk.CENTER)
glass_feed_tree.column("name", width=150, anchor=tk.CENTER)
glass_feed_tree.column("nid", width=110, anchor=tk.CENTER)
glass_feed_tree.column("emp", width=130, anchor=tk.CENTER)
glass_feed_tree.column("dept", width=160, anchor=tk.CENTER)
glass_feed_tree.column("entry", width=90, anchor=tk.CENTER)
glass_feed_tree.column("exit", width=100, anchor=tk.CENTER)

glass_feed_tree.pack(fill=tk.BOTH, expand=True)

def refresh_live_feed():
    for item in glass_feed_tree.get_children():
        glass_feed_tree.delete(item)
    for idx, r in enumerate(mock_records[:15]):
        tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
        status_str = f"✓ {r[7]}" if r[7] else "🟢 حاضر در سازمان"
        glass_feed_tree.insert("", tk.END, values=(r[0], r[1], r[2], r[3], r[4], r[5], status_str), tags=(tag,))

def on_double_click_feed(e):
    sel = glass_feed_tree.selection()
    if not sel: return
    vals = glass_feed_tree.item(sel[0], "values")
    v_id, v_name, status = vals[0], vals[1], vals[6]
    if "✓" in status:
        messagebox.showinfo("ثبت شده", f"ساعت خروج مراجع {v_name} قبلاً ثبت شده است.", parent=app)
        return
    now_t = datetime.now().strftime("%H:%M")
    if messagebox.askyesno("تأیید خروج", f"آیا ساعت خروج مراجع ({v_name}) در ساعت {now_t} ثبت شود؟", parent=app):
        database.update_exit_time(v_id, now_t)
        refresh_live_feed()
        refresh_search_view()
        update_kpis()
        show_toast(f"✓ خروج مراجع ({v_name}) ثبت گردید.", C_CYAN)

glass_feed_tree.bind("<Double-1>", on_double_click_feed)
refresh_live_feed()

# ==========================================
# 🌟 VIEW 2: SEARCH & FULL AUDIT HISTORY
# ==========================================
view_search = tk.Frame(view_container, bg=C_BG_DARK)
tab_views.append(view_search)

search_filter_bar = tk.Frame(view_search, bg="#111827", highlightthickness=1, highlightbackground="#1E293B", padx=16, pady=12)
search_filter_bar.pack(fill=tk.X, pady=(0, 10))

s_r = tk.Frame(search_filter_bar, bg="#111827")
s_r.pack(fill=tk.X)

tk.Label(s_r, text="نام مراجع:", font=(FONT_FAMILY, 10, "bold"), bg="#111827", fg=C_TEXT_MUTED).pack(side=tk.RIGHT, padx=5)
s_name_input = tk.Entry(s_r, justify='right', font=(FONT_FAMILY, 10), bg="#1F2937", fg="#F8FAFC", insertbackground="#38BDF8", bd=0, width=16)
s_name_input.pack(side=tk.RIGHT, padx=5, ipady=4)

tk.Label(s_r, text="کد ملی:", font=(FONT_FAMILY, 10, "bold"), bg="#111827", fg=C_TEXT_MUTED).pack(side=tk.RIGHT, padx=(15, 5))
s_nid_input = tk.Entry(s_r, justify='right', font=(FONT_FAMILY, 10), bg="#1F2937", fg="#F8FAFC", insertbackground="#38BDF8", bd=0, width=14)
s_nid_input.pack(side=tk.RIGHT, padx=5, ipady=4)

tk.Label(s_r, text="واحد سازمانی:", font=(FONT_FAMILY, 10, "bold"), bg="#111827", fg=C_TEXT_MUTED).pack(side=tk.RIGHT, padx=(15, 5))
s_dept_input = tb.Combobox(s_r, values=[""] + config.DEPARTMENT_LIST, state="readonly", width=18)
s_dept_input.pack(side=tk.RIGHT, padx=5)

def refresh_search_view():
    for item in full_search_tree.get_children():
        full_search_tree.delete(item)
    filters = {
        "name": s_name_input.get().strip(),
        "nid": s_nid_input.get().strip(),
        "dept": s_dept_input.get().strip()
    }
    _, rows = database.search_visitors(filters, 1, 100)
    for idx, r in enumerate(rows):
        tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
        full_search_tree.insert("", tk.END, values=(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7] or "🟢 حاضر", r[8]), tags=(tag,))

tk.Button(s_r, text="🔍 جستجو", font=(FONT_FAMILY, 10, "bold"), bg="#0284C7", fg="#FFFFFF", bd=0, padx=14, pady=4, cursor="hand2", command=refresh_search_view).pack(side=tk.LEFT, padx=4)
tk.Button(s_r, text="🔄 بازنشانی", font=(FONT_FAMILY, 10), bg="#1E293B", fg="#94A3B8", bd=0, padx=12, pady=4, cursor="hand2", command=lambda: (s_name_input.delete(0, tk.END), s_nid_input.delete(0, tk.END), s_dept_input.set(""), refresh_search_view())).pack(side=tk.LEFT, padx=4)

search_tree_box = tk.Frame(view_search, bg="#111827", highlightthickness=1, highlightbackground="#1E293B")
search_tree_box.pack(fill=tk.BOTH, expand=True)

full_search_tree = tb.Treeview(
    search_tree_box,
    columns=("id", "name", "nid", "emp", "dept", "entry", "date", "exit", "user"),
    show='headings'
)
full_search_tree.tag_configure('evenrow', background='#0F172A')
full_search_tree.tag_configure('oddrow', background='#131D31')

all_cols = {
    "id": "شناسه", "name": "نام مراجع", "nid": "شماره ملی", "emp": "ملاقات‌شونده",
    "dept": "امور / واحد", "entry": "ساعت ورود", "date": "تاریخ", "exit": "ساعت خروج", "user": "ثبت‌کننده"
}
for k, v in all_cols.items():
    full_search_tree.heading(k, text=v)
    full_search_tree.column(k, anchor=tk.CENTER)

full_search_tree.pack(fill=tk.BOTH, expand=True)
refresh_search_view()

# ==========================================
# 🌟 VIEW 3: LIVE ANALYTICS & CHARTS
# ==========================================
view_analytics = tk.Frame(view_container, bg=C_BG_DARK)
tab_views.append(view_analytics)

chart_glass_card = tk.Frame(view_analytics, bg="#111827", highlightthickness=1, highlightbackground="#1E293B", padx=16, pady=16)
chart_glass_card.pack(fill=tk.BOTH, expand=True)

def draw_glass_chart():
    for w in chart_glass_card.winfo_children():
        w.destroy()
        
    c_header = tk.Frame(chart_glass_card, bg="#111827")
    c_header.pack(fill=tk.X, pady=(0, 10))
    tk.Label(c_header, text="📈 توزیع ساعتی تردد و مراجعین در طول روز (تحلیل هوشمند)", font=(FONT_FAMILY, 12, "bold"), bg="#111827", fg="#F8FAFC").pack(side=tk.RIGHT)
    tk.Button(c_header, text="🔄 به‌روزرسانی زنده", font=(FONT_FAMILY, 9), bg="#1E293B", fg=C_CYAN, bd=0, padx=12, pady=4, cursor="hand2", command=draw_glass_chart).pack(side=tk.LEFT)
    
    fig = Figure(figsize=(9, 4.8), dpi=100)
    fig.patch.set_facecolor('#111827')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#0B0F19')
    
    hours = [f"{h:02d}" for h in range(7, 18)]
    counts = [1, 5, 12, 18, 14, 6, 4, 11, 8, 3, 1]
    
    colors = ['#38BDF8' if c < 10 else ('#818CF8' if c < 15 else '#C084FC') for c in counts]
    bars = ax.bar(hours, counts, color=colors, edgecolor='#1E293B', width=0.55, zorder=3)
    
    ax.set_title(utils.make_farsi("تحلیل هوشمند اوج ساعات تردد مراجعین"), fontname=FONT_FAMILY, fontsize=12, fontweight='bold', color='#F8FAFC', pad=12)
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
    canvas = FigureCanvasTkAgg(fig, master=chart_glass_card)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

draw_glass_chart()

# ==========================================
# 🌟 VIEW 4: SYSTEM & ADMIN CONTROL CENTER
# ==========================================
view_tools = tk.Frame(view_container, bg=C_BG_DARK)
tab_views.append(view_tools)

tools_card = tk.Frame(view_tools, bg="#111827", highlightthickness=1, highlightbackground="#1E293B", padx=25, pady=20)
tools_card.pack(fill=tk.BOTH, expand=True)

tk.Label(
    tools_card, 
    text="🛠️ مرکز ابزارها و پنل‌های اجرایی مدیریت سیستم", 
    font=(FONT_FAMILY, 14, "bold"), 
    bg="#111827", 
    fg="#F8FAFC"
).pack(pady=(0, 20))

glass_tools_grid = tk.Frame(tools_card, bg="#111827")
glass_tools_grid.pack(fill=tk.BOTH, expand=True)

def make_tile(parent, r, c, title, desc, icon, color, cmd):
    tile = tk.Frame(parent, bg="#1A2234", highlightthickness=1, highlightbackground="#2A3854", padx=16, pady=14, cursor="hand2")
    tile.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
    
    # Accent top border
    tk.Frame(tile, bg=color, height=3).pack(fill=tk.X, pady=(0, 8))
    
    top = tk.Frame(tile, bg="#1A2234")
    top.pack(fill=tk.X)
    
    tk.Label(top, text=icon, font=(FONT_FAMILY, 16), bg="#1A2234", fg=color).pack(side=tk.RIGHT)
    tk.Label(top, text=title, font=(FONT_FAMILY, 11, "bold"), bg="#1A2234", fg="#F8FAFC").pack(side=tk.RIGHT, padx=(0, 8))
    
    tk.Label(tile, text=desc, font=(FONT_FAMILY, 9), bg="#1A2234", fg="#94A3B8", anchor="e").pack(fill=tk.X, pady=(6, 10))
    
    tk.Button(tile, text="اجرا و مشاهده ➔", font=(FONT_FAMILY, 9, "bold"), bg=color, fg="#FFFFFF", bd=0, padx=12, pady=4, cursor="hand2", command=cmd).pack(anchor="w")

make_tile(glass_tools_grid, 0, 0, "مدیریت کاربران و دسترسی‌ها", "تعریف و ویرایش نقش‌های نگهبان و مدیران", "👥", C_BLUE, lambda: windows.open_user_manager(app, app=app, current_user="admin"))
make_tile(glass_tools_grid, 0, 1, "آمار تردد روزانه", "محاسبه دقیق تردد و گزارش مراجعین در تاریخ انتخابی", "📊", C_CYAN, lambda: windows.show_daily_stats_ui(app))
make_tile(glass_tools_grid, 1, 0, "نمودار تحلیل آماری تردد", "تحلیل پیشرفته ساعات اوج و پرترددترین واحدها", "📈", C_PURPLE, lambda: windows.show_heatmap_analytics(app))
make_tile(glass_tools_grid, 1, 1, "گزارش لاگ حسابرسی اکسل", "تولید فایل اکسل از کلیه فعالیت‌های ثبت‌شده در سامانه", "📑", C_EMERALD, lambda: windows.export_audit_log_excel(app, app=app))
make_tile(glass_tools_grid, 2, 0, "اصلاح داده‌های تکمیل خودکار", "پاکسازی و ادغام اسامی پرسنل و مراجعین", "✏️", C_AMBER, lambda: windows.open_data_cleanup_window(app))
make_tile(glass_tools_grid, 2, 1, "تنظیمات اتصال سرور SQL", "پیکربندی آدرس سرور، پایگاه داده و احراز هویت", "⚙️", C_ROSE, lambda: windows.open_server_settings(app))

glass_tools_grid.columnconfigure(0, weight=1)
glass_tools_grid.columnconfigure(1, weight=1)

# Default to Tab 0
switch_tab(0)

# ==========================================
# 🌟 BOTTOM NOTIFICATION TOAST & STATUS
# ==========================================
toast_bar = tk.Label(
    app, 
    text="  با سلام — به نسخه گلس‌مورفیک سامانه هوشمند تردد خوش آمدید.", 
    font=(FONT_FAMILY, 10), 
    bg="#0D1322", 
    fg="#38BDF8", 
    anchor="e", 
    padx=16, 
    pady=8,
    highlightthickness=1,
    highlightbackground="#1E293B"
)
toast_bar.pack(side=tk.BOTTOM, fill=tk.X)

toast_timer = None
def show_toast(msg, color=C_EMERALD):
    global toast_timer
    if toast_timer:
        app.after_cancel(toast_timer)
    toast_bar.config(text=f"  {msg}", fg=color)
    toast_timer = app.after(6000, lambda: toast_bar.config(text="  سامانه در حالت آماده به کار قرار دارد.", fg="#38BDF8"))

if __name__ == "__main__":
    print("==================================================================")
    print("💎 Running Next-Gen Glassmorphism & Cyber-Modern UI/UX Preview")
    print("✨ Featuring: Frosted Glass Cards, Neon Glow Accents, & Lively Charts")
    print("==================================================================")
    app.mainloop()

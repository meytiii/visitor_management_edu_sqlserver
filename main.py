import tkinter as tk
from tkinter import messagebox, font
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import random
import threading
from datetime import datetime
import jdatetime
from PIL import Image, ImageTk
import os

# Local modules
import config
import database
import utils
import widgets
import windows
import printer

# --- Main Application Setup ---
app = tb.Window(themename="lumen")
app.title(f"سامانه مدیریت ورود و خروج (اداره حراست) - نسخه {config.APP_VERSION}")
app.geometry("1050x600")
app.resizable(False, False)

# **FIX: Hide main window immediately after creation**
app.withdraw()

try:
    icon_path = utils.resource_path(os.path.join('assets', 'app_icon.ico'))
    app.iconbitmap(icon_path)
    app.iconbitmap(default=icon_path)
except Exception: 
    pass

# --- FONT SAFETY CHECK ---
available_fonts = font.families()
FONT_MAIN = "B Titr" if "B Titr" in available_fonts else "Tahoma"
FONT_TABLE = "B Nazanin" if "B Nazanin" in available_fonts else "Tahoma"

# --- BACKGROUND FUNCTION ---
def setup_background(window_root):
    bg_path = utils.resource_path(os.path.join('assets', 'background.png'))
    if not os.path.exists(bg_path): return
    try:
        window_root.original_img = Image.open(bg_path)
        bg_label = tk.Label(window_root)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        def resize_image(event):
            if event.widget == window_root:
                new_w, new_h = event.width, event.height
                if new_w < 50 or new_h < 50: return
                resized = window_root.original_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(resized)
                bg_label.config(image=photo)
                bg_label.image = photo 
                
        window_root.bind('<Configure>', resize_image)
        bg_label.lower()
    except Exception as e: print(f"Background Error: {e}")

setup_background(app)

# --- LIVE CLOCK & DATE DASHBOARD ---
def update_live_clock():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    j_date = jdatetime.date.fromgregorian(date=now.date())
    persian_date_str = j_date.strftime("%Y/%m/%d")
    
    live_clock_label.config(text=f"{persian_date_str}   -   {current_time}")
    live_clock_label.after(1000, update_live_clock)

live_clock_label = tb.Label(
    app, 
    text="", 
    font=(FONT_MAIN, 14, "bold"),
    bootstyle=PRIMARY       
)
live_clock_label.place(relx=1.0, y=20, anchor="ne", x=-30)
live_clock_label.lift()
update_live_clock()

# --- HELPER UI FUNCTIONS ---
def focus_next_widget(event):
    event.widget.tk_focusNext().focus()
    return("break")

def clear_fields():
    entry_visitor_name.delete(0, tk.END); entry_national_id.delete(0, tk.END)
    entry_employee_to_meet.delete(0, tk.END); combo_department.set("")
    entry_national_id.configure(bootstyle=DEFAULT) 
    entry_visitor_name.configure(bootstyle=DEFAULT)
    entry_national_id.focus()

def auto_fill_department(employee_name):
    dept = database.get_last_department_for_employee(employee_name)
    if dept:
        combo_department.set(dept)

def update_employee_suggestions():
    try:
        names = database.get_employee_suggestions() 
        entry_employee_to_meet.set_completion_list(names)
    except: pass

def check_returning_visitor(event):
    nid = entry_national_id.get().strip()
    if len(nid) < 5: return
    name = database.get_visitor_name_by_nid(nid)
    if name and not entry_visitor_name.get():
        entry_visitor_name.delete(0, tk.END)
        entry_visitor_name.insert(0, name)

# --- VALIDATION WRAPPERS ---
def validate_national_id_on_exit():
    nid = entry_national_id.get().strip()
    if nid and len(nid) == 10:
        is_valid, error_msg = utils.validate_national_id(nid)
        if not is_valid:
            entry_national_id.configure(bootstyle=WARNING)
            show_status(f"⚠️ {error_msg} (می‌توانید ادامه دهید)", "orange", duration=5000)
        else:
            entry_national_id.configure(bootstyle=SUCCESS)
            check_returning_visitor(None)
    elif nid:
        entry_national_id.configure(bootstyle=WARNING)
        show_status("⚠️ کد ملی باید ۱۰ رقمی باشد (می‌توانید ادامه دهید)", "orange", duration=5000)
    else:
        entry_national_id.configure(bootstyle=DEFAULT)

def validate_visitor_name_on_exit():
    name = entry_visitor_name.get().strip()
    if name and len(name) > 0:
        is_valid, error_msg = utils.validate_persian_name(name)
        if not is_valid and len(name) >= 2:
            entry_visitor_name.configure(bootstyle=DANGER)
            show_status(f"⚠️ {error_msg}", "red", duration=3000)
        else:
            entry_visitor_name.configure(bootstyle=DEFAULT)

def on_national_id_enter(event):
    nid = entry_national_id.get().strip()
    target_widget = entry_visitor_name
    
    if len(nid) >= 5:
        name = database.get_visitor_name_by_nid(nid)
        if name and not entry_visitor_name.get():
            entry_visitor_name.delete(0, tk.END)
            entry_visitor_name.insert(0, name)
            target_widget = entry_employee_to_meet
    target_widget.focus_set()
    return "break"

# --- SUBMISSION LOGIC ---
def submit_visitor():
    visitor_name = entry_visitor_name.get().strip()
    national_id = entry_national_id.get().strip()
    employee_to_meet = entry_employee_to_meet.get().strip()
    department = combo_department.get()
    if not all([visitor_name, national_id, employee_to_meet, department]):
        messagebox.showwarning("خطا", "لطفاً تمام اطلاعات را وارد کنید")
        entry_national_id.focus_set() if not national_id else entry_visitor_name.focus_set()
        return
    
    is_valid, error_msg = utils.validate_national_id(national_id)
    if not is_valid:
        response = messagebox.askyesno("هشدار کد ملی", f"{error_msg}\n\nآیا مطمئن هستید که می‌خواهید ادامه دهید؟")
        if not response:
            entry_national_id.focus_set()
            entry_national_id.select_range(0, tk.END)
            return
    
    if len(visitor_name) < 3:
        messagebox.showwarning("خطا", "نام باید حداقل ۳ کاراکتر باشد")
        return

    if len(employee_to_meet) < 3:
        messagebox.showwarning("خطا", "نام ملاقات شونده باید حداقل ۳ کاراکتر باشد")
        return

    current_shamsi_date = jdatetime.date.fromgregorian(date=datetime.now().date()).strftime("%Y/%m/%d")
    duplicate = database.check_duplicate_entry(national_id, employee_to_meet, current_shamsi_date)
    if duplicate:
        if not messagebox.askyesno("تکرار ورود", "امروز قبلاً ثبت شده است. آیا مطمئن هستید؟"):
            return

    now = datetime.now()
    entry_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    shamsi_date_str = jdatetime.date.fromgregorian(date=now.date()).strftime("%Y/%m/%d")
    registrar = getattr(app, 'current_user', 'سیستم')
    username = getattr(app, 'current_username', 'سیستم')
    
    try:
        visitor_id = database.add_visitor(
            visitor_name, national_id, employee_to_meet, department,
            entry_time_str, shamsi_date_str, registrar
        )
        
        database.log_audit(
            "visitor_added",
            user=username,
            visitor_id=visitor_id,
            visitor_name=visitor_name,
            national_id=national_id,
            employee_to_meet=employee_to_meet,
            department=department,
            entry_time=entry_time_str,
            shamsi_date=shamsi_date_str
        )
        
        threading.Thread(target=printer.print_receipt, args=(visitor_id, visitor_name, national_id, employee_to_meet, department, now, shamsi_date_str), daemon=True).start()
        show_success_overlay(card_frame)
        clear_fields()
        show_status(f"✓ ورود مهمان با شماره {visitor_id} با موفقیت ثبت شد", "green", duration=10000)
        update_employee_suggestions()
    except Exception as e:
        database.log_audit("visitor_entry_failed",
            visitor_name=visitor_name, 
            national_id=national_id, 
            error=str(e))
        messagebox.showerror("خطای پایگاه داده", f"خطا در ثبت اطلاعات: {e}")

# --- CENTRAL CARD CONTAINER ---
card_frame = tb.Frame(app, padding=15)
card_frame.place(relx=0.5, rely=0.46, anchor="center", width=420, height=480)

header_lbl = tb.Label(card_frame, text="🛡️(سامانه ثبت ورود و خروج (اداره حراست💻", font=(FONT_MAIN, 16, "bold"), anchor="center")
header_lbl.grid(row=0, column=0, columnspan=2, pady=(5, 15), sticky="ew")

labels = {": شماره کارت ملی 🆔": 1, ": نام ملاقات کننده 🙋": 2, ": نام ملاقات شونده 👔": 3, ": امور / واحد مربوطه 🏢": 4}
for text, row in labels.items():
    tb.Label(card_frame, text=text, font=(FONT_MAIN, 12)).grid(row=row, column=1, padx=(10, 20), pady=6, sticky="e")

vcmd = (app.register(utils.validate_numeric), '%P')

entry_national_id = tb.Entry(card_frame, justify='right', font=(FONT_MAIN, 12), validate='key', validatecommand=vcmd)
entry_national_id.bind("<FocusOut>", lambda e: (check_returning_visitor(e), validate_national_id_on_exit()))
entry_national_id.bind("<Return>", on_national_id_enter) 

entry_visitor_name = tb.Entry(card_frame, justify='right', font=(FONT_MAIN, 12))
entry_visitor_name.bind("<Return>", focus_next_widget)
entry_visitor_name.bind("<FocusOut>", lambda e: validate_visitor_name_on_exit())

entry_employee_to_meet = widgets.AutocompleteEntry(card_frame, justify='right', font=(FONT_MAIN, 12), selection_callback=auto_fill_department)
combo_department = tb.Combobox(card_frame, values=config.DEPARTMENT_LIST, justify='right', state='readonly', font=(FONT_MAIN, 12))
combo_department.bind("<Return>", focus_next_widget)

entry_national_id.grid(row=1, column=0, sticky="ew", padx=(10, 5), pady=6)
entry_visitor_name.grid(row=2, column=0, sticky="ew", padx=(10, 5), pady=6)
entry_employee_to_meet.grid(row=3, column=0, sticky="ew", padx=(10, 5), pady=6)
combo_department.grid(row=4, column=0, sticky="ew", padx=(10, 5), pady=6)
card_frame.grid_columnconfigure(0, weight=1)

btn_frame = tb.Frame(card_frame)
btn_frame.grid(row=5, column=0, columnspan=2, pady=(15, 10), sticky="ew")

tb.Button(btn_frame, text="ثبت و چاپ رسید✅", command=submit_visitor, bootstyle=SUCCESS).pack(pady=4, fill=tk.X)
tb.Button(btn_frame, text="مشاهده و جستجوی سوابق📚", command=lambda: windows.open_search_window(app), bootstyle=PRIMARY).pack(pady=4, fill=tk.X)
tb.Button(btn_frame, text="راهنما📑", command=lambda: windows.show_help_popup(getattr(app, 'current_role', 'guard')), bootstyle=SECONDARY).pack(pady=4, fill=tk.X)

# --- LOGIN & MENU SETUP ---
def rebuild_dashboard_menu():
    role = getattr(app, 'current_role', 'guard')
    full_name = getattr(app, 'current_user', '')
    username = getattr(app, 'current_username', '')
    
    menubar = tk.Menu(app)
    if role == 'admin':
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="پنل مدیریت (Admin)", command=lambda: windows.open_developer_mode(app, rebuild_dashboard_menu))
        menubar.add_cascade(label="تنظیمات سیستم", menu=tools_menu)
    
    user_menu = tk.Menu(menubar, tearoff=0)

    def change_password():
        windows.open_change_password_window(app, username)

    def logout():
        database.log_audit("logout", user=username)
        for child in app.winfo_children():
            if isinstance(child, tk.Toplevel):
                child.destroy()
        app.withdraw()
        windows.show_login_screen(app, setup_dashboard)

    user_menu.add_command(label="تغییر رمز عبور", command=change_password)
    user_menu.add_separator()
    user_menu.add_command(label="خروج از حساب", command=logout)
    menubar.add_cascade(label=f"حساب کاربری: {full_name}", menu=user_menu)
    app.config(menu=menubar)

def setup_dashboard(username, role, full_name):
    app.deiconify()
    app.current_user = full_name
    app.current_username = username
    app.current_role = role
    app.title(f"سامانه مدیریت ورود و خروج (اداره حراست)   |   کاربر: {full_name}")
    rebuild_dashboard_menu()

try:
    for widget in [entry_visitor_name, combo_department]:
        widget.bind("<Return>", focus_next_widget)
except NameError: pass

# --- STATUS BAR & QUOTE SYSTEM ---
status_bar = tb.Label(
    app, 
    text="  با سلام - به سامانه مدیریت مراجعین (اداره حراست) خوش آمدید", 
    anchor=tk.E, 
    font=(FONT_MAIN, 12), 
    padding=2,
    bootstyle="inverse-light"
)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

cycle_timer_id = None
def cycle_cultural_messages():
    global cycle_timer_id
    quote = random.choice(config.CULTURAL_MESSAGES)
    status_bar.config(text=f"  {quote}", foreground="#555555")
    cycle_timer_id = app.after(30000, cycle_cultural_messages)

def start_quote_cycle():
    global cycle_timer_id
    cycle_timer_id = app.after(30000, cycle_cultural_messages)

def show_status(message, color="#555555", duration=10000):
    global cycle_timer_id
    if cycle_timer_id:
        app.after_cancel(cycle_timer_id)
        cycle_timer_id = None
    status_bar.config(text=f"  {message}", foreground=color)
    def return_to_quotes(): cycle_cultural_messages()
    app.after(duration, return_to_quotes)

def show_success_overlay(parent):
    parent.update_idletasks()
    x = parent.winfo_rootx()
    y = parent.winfo_rooty()
    w = parent.winfo_width()
    h = parent.winfo_height()

    overlay = tk.Toplevel(parent)
    overlay.overrideredirect(True)
    overlay.geometry(f"{w}x{h}+{x}+{y}")
    overlay.wm_attributes("-alpha", 0.0)
    overlay.configure(bg="#198754")

    inner = tk.Frame(overlay, bg="#198754")
    inner.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(inner, text="✓", font=("Segoe UI", 52, "bold"),
             bg="#198754", fg="white").pack()
    tk.Label(inner, text="ثبت شد", font=("Segoe UI", 18, "bold"),
             bg="#198754", fg="white").pack(pady=(4, 0))

    def fade(alpha, direction):
        alpha = round(alpha + direction * 0.04, 2)
        if direction == 1 and alpha >= 0.88:
            overlay.wm_attributes("-alpha", 0.88)
            overlay.after(1000, lambda: fade(0.88, -1))
        elif direction == -1 and alpha <= 0.0:
            overlay.destroy()
        else:
            overlay.wm_attributes("-alpha", alpha)
            overlay.after(30, lambda: fade(alpha, direction))

    fade(0.0, 1)

def on_app_close():
    database.log_audit("logout", user=getattr(app, "current_username", None))
    database.log_audit("app_closed", user=getattr(app, "current_username", None))
    app.destroy()
app.protocol("WM_DELETE_WINDOW", on_app_close)

if __name__ == "__main__":
    try:
        database.setup_database()
        database.setup_audit_table()
    except Exception as e:
        print(f"Database setup error: {e}")
        def show_warning():
            messagebox.showwarning("اتصال به پایگاه داده",
                                   "امکان اتصال به سرور پیش‌فرض وجود ندارد.\n"
                                   "لطفاً از منوی 'ابزارها' -> 'تنظیمات سرور' اطلاعات صحیح را وارد کنید.",
                                   parent=app)
        app.after(500, show_warning)
    
    try:
        update_employee_suggestions()
    except:
        pass
        
    start_quote_cycle()
    windows.show_login_screen(app, setup_dashboard)
    app.mainloop()
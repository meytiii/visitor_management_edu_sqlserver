import tkinter as tk
from tkinter import messagebox, filedialog, font
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import pandas as pd
from datetime import datetime
import jdatetime
import os
import sys
from PIL import Image, ImageTk

import matplotlib
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Tahoma', 'Arial', 'DejaVu Sans']
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import config
import database
import utils

# --- Configuration & Styles ---
FONT_MAIN = "Tahoma"
FONT_TABLE = "Tahoma"
_fonts_checked = False

def ensure_fonts():
    global FONT_MAIN, FONT_TABLE, _fonts_checked
    if _fonts_checked: return
    try:
        available = font.families()
        if "B Titr" in available: FONT_MAIN = "B Titr"
        if "B Nazanin" in available: FONT_TABLE = "B Nazanin"
        elif "B Roya" in available: FONT_TABLE = "B Roya"
        
        style = tb.Style()
        style.configure('TButton', font=(FONT_MAIN, 12))
        
        style.configure('Treeview', font=(FONT_TABLE, 12, "bold"), rowheight=45) 
        style.configure('Treeview.Heading', font=(FONT_MAIN, 11, "bold"))
        
        style.configure('primary.Treeview', font=(FONT_TABLE, 12, "bold"), rowheight=45) 
        style.configure('primary.Treeview.Heading', font=(FONT_MAIN, 11, "bold"))
        
        _fonts_checked = True
    except: pass

def show_help_popup(role='guard'):
    import tempfile
    import webbrowser
    import base64

    if role == 'admin':
        html_file = "help_guide_admins.html"
    else:
        html_file = "help_guide.html"

    template_path = utils.resource_path(os.path.join("assets", html_file))
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_template = f.read()
    except Exception as e:
        messagebox.showerror("خطا", f"فایل راهنما یافت نشد:\n{e}")
        return

    bg_path = utils.resource_path(os.path.join('assets', 'background.png'))
    bg_base64 = ""
    if os.path.exists(bg_path):
        try:
            with open(bg_path, "rb") as img_file:
                bg_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        except:
            pass

    html_content = html_template.replace("{{BG_BASE64}}", bg_base64)
    html_content = html_content.replace("{{APP_VERSION}}", config.APP_VERSION)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_path = f.name

    webbrowser.open('file://' + temp_path)

    def cleanup():
        try:
            os.unlink(temp_path)
        except:
            pass
    import threading
    threading.Timer(10.0, cleanup).start()

def show_login_screen(app, on_success_callback):
    ensure_fonts()
    login_win = tb.Toplevel(app)
    login_win.title("ورود به سیستم")
    
    width, height = 400, 400
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    login_win.geometry(f"{width}x{height}+{x}+{y}")
    login_win.resizable(False, False)

    canvas = tk.Canvas(login_win, width=width, height=height, highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.configure(bg="#2E3B4E")
    
    bg_path = utils.resource_path(os.path.join('assets', 'login.png'))
    if os.path.exists(bg_path):
        try:
            pil_image = Image.open(bg_path)
            pil_image = pil_image.resize((width, height), Image.Resampling.LANCZOS)
            bg_image_obj = ImageTk.PhotoImage(pil_image)
            canvas.create_image(0, 0, image=bg_image_obj, anchor="nw")
            login_win.bg_image_obj = bg_image_obj 
        except Exception as e: pass

    try: login_win.iconbitmap(utils.resource_path(os.path.join('assets', 'app_icon.ico')))
    except: pass

    # --- CONNECTION STATUS BAR ---
    status_text = canvas.create_text(200, 355, text="", fill="", font=(FONT_MAIN, 10))

    def test_and_update_status():
        server_display = config.SQL_SERVER.split('\\')[0] if config.SQL_SERVER else 'نامشخص'
        canvas.itemconfig(status_text, 
            text=f'... {server_display} در حال اتصال به', 
            fill='#FF8C00')
        login_win.update_idletasks()
        
        ok, err_msg = config.test_connection({
            "sql_server": config.SQL_SERVER,
            "sql_database": config.SQL_DATABASE,
            "sql_user": config.SQL_USER,
            "sql_password": config.SQL_PASSWORD,
            "sql_driver": config.SQL_DRIVER
        })
        
        if ok:
            canvas.itemconfig(status_text,
                text=f'ارتباط با سرور پایگاه داده {server_display} برقرار شد.',
                fill='#4CAF50')
            try:
                database.setup_database()
            except Exception as e:
                print(f"Database setup error: {e}")
        else:
            canvas.itemconfig(status_text,
                text='برقراری اتصال ناموفق بود. تنظیمات سرور را بررسی کنید.',
                fill='#f44336')

    def on_settings_changed():
        test_and_update_status()

    # ---------- MENU BAR ----------
    menubar = tk.Menu(login_win)
    tools_menu = tk.Menu(menubar, tearoff=0)
    tools_menu.add_command(label="تنظیمات سرور", command=lambda: open_server_settings(login_win, on_settings_changed))
    menubar.add_cascade(label="ابزارها", menu=tools_menu)
    login_win.config(menu=menubar)
    # ----------------------------------

    canvas.create_text(200, 40, text="سامانه مدیریت مراجعین💻", fill="#d6f7fd", font=(FONT_MAIN, 16, "bold"))
    
    canvas.create_text(200, 90, text=":نام کاربری👤", fill="#fffbda", font=(FONT_MAIN, 12))
    ent_user = tb.Entry(login_win, justify='center', font=(FONT_MAIN, 12))
    canvas.create_window(200, 120, window=ent_user, width=200, height=35)
    
    canvas.create_text(200, 160, text=":رمز عبور🔑", fill="#fffbda", font=(FONT_MAIN, 12))
    ent_pass = tb.Entry(login_win, show="●", justify='center', font=(FONT_MAIN, 12))
    canvas.create_window(200, 190, window=ent_pass, width=200, height=35)
    
    def do_login():
        u = ent_user.get().strip()
        p = ent_pass.get().strip()
        success, role, full_name, err_msg = database.authenticate_user(u, p)
        if success:
            database.log_audit("login_success", user=u)
            login_win.destroy()
            on_success_callback(u, role, full_name)
        else:
            database.log_audit("login_failed", user=u)
            messagebox.showerror("خطا", err_msg, parent=login_win)
            ent_pass.delete(0, tk.END)

    btn_login = tb.Button(login_win, text="ورود🚪", command=do_login, bootstyle=SUCCESS)
    canvas.create_window(200, 260, window=btn_login, width=150, height=40)

    def on_login_window_close():
        database.log_audit("app_closed", user=getattr(app, "current_username", None))
        app.destroy()

    login_win.protocol("WM_DELETE_WINDOW", on_login_window_close)

    login_win.bind('<Return>', lambda e: do_login())
    ent_user.focus()

    login_win.after(100, test_and_update_status)

def open_server_settings(parent, on_settings_changed=None):
    import pyodbc
    ensure_fonts()

    settings_win = tb.Toplevel(parent)
    settings_win.title("Server Settings")
    settings_win.geometry("500x680")
    settings_win.resizable(False, False)
    try:
        settings_win.iconbitmap(utils.resource_path(os.path.join('assets', 'app_icon.ico')))
    except:
        pass

    # Background (developer.png)
    bg_path = utils.resource_path(os.path.join('assets', 'developer.png'))
    if os.path.exists(bg_path):
        try:
            original_img = Image.open(bg_path)
            resized_img = original_img.resize((500, 680), Image.Resampling.LANCZOS)
            bg_photo = ImageTk.PhotoImage(resized_img)
            bg_label = tk.Label(settings_win, image=bg_photo)
            bg_label.image = bg_photo
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            bg_label.lower()
        except Exception:
            pass

    #White card frame
    card_frame = tk.Frame(settings_win, bg="white", bd=0, highlightthickness=0)
    card_frame.place(relx=0.5, rely=0.5, anchor="center", width=460, height=650)

    main_frame = tk.Frame(card_frame, bg="white", padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    #Title
    tb.Label(main_frame, text="⚙️ SQL Server Connection Settings", font=(FONT_MAIN, 13, "bold"),
             bootstyle=PRIMARY, background="white").pack(pady=(0, 20))

    # --- Server ---
    lbl_server = tk.Label(main_frame, text="Server address:", font=(FONT_MAIN, 10),
                          bg="white", anchor="w")
    lbl_server.pack(anchor="w", pady=(5, 2))
    server_entry = tb.Entry(main_frame, font=(FONT_MAIN, 10))
    server_entry.insert(0, config.SQL_SERVER)
    server_entry.pack(fill=tk.X, pady=(0, 10))

    # --- Database ---
    lbl_db = tk.Label(main_frame, text="Database name:", font=(FONT_MAIN, 10),
                      bg="white", anchor="w")
    lbl_db.pack(anchor="w", pady=(5, 2))
    db_entry = tb.Entry(main_frame, font=(FONT_MAIN, 10))
    db_entry.insert(0, config.SQL_DATABASE)
    db_entry.pack(fill=tk.X, pady=(0, 10))

    # --- Username ---
    lbl_user = tk.Label(main_frame, text="Username:", font=(FONT_MAIN, 10),
                        bg="white", anchor="w")
    lbl_user.pack(anchor="w", pady=(5, 2))
    user_entry = tb.Entry(main_frame, font=(FONT_MAIN, 10))
    user_entry.insert(0, config.SQL_USER)
    user_entry.pack(fill=tk.X, pady=(0, 10))

    # --- Password ---
    lbl_pass = tk.Label(main_frame, text="Password:", font=(FONT_MAIN, 10),
                        bg="white", anchor="w")
    lbl_pass.pack(anchor="w", pady=(5, 2))
    pass_entry = tb.Entry(main_frame, font=(FONT_MAIN, 10), show="●")
    pass_entry.insert(0, config.SQL_PASSWORD)
    pass_entry.pack(fill=tk.X, pady=(0, 10))

    # --- Driver dropdown ---
    lbl_driver = tk.Label(main_frame, text="ODBC Driver:", font=(FONT_MAIN, 10),
                          bg="white", anchor="w")
    lbl_driver.pack(anchor="w", pady=(5, 2))
    available_drivers = pyodbc.drivers()
    driver_var = tk.StringVar(value=config.SQL_DRIVER)
    driver_combo = tb.Combobox(main_frame, textvariable=driver_var, values=available_drivers,
                               state='readonly', font=(FONT_MAIN, 10))
    driver_combo.pack(fill=tk.X, pady=(0, 30))

    top_btn_frame = tk.Frame(main_frame, bg="white")
    top_btn_frame.pack(pady=(5, 10))

    bottom_btn_frame = tk.Frame(main_frame, bg="white")
    bottom_btn_frame.pack(pady=(0, 10))

    def test_connection():
        new_settings = {
            "sql_server": server_entry.get().strip(),
            "sql_database": db_entry.get().strip(),
            "sql_user": user_entry.get().strip(),
            "sql_password": pass_entry.get().strip(),
            "sql_driver": driver_var.get().strip()
        }

        if not all([new_settings["sql_server"], new_settings["sql_database"],
                    new_settings["sql_user"], new_settings["sql_driver"]]):
            messagebox.showerror("Validation Error", "All fields must be filled.", parent=settings_win)
            return

        ok, err_msg = config.test_connection(new_settings)
        if ok:
            messagebox.showinfo("Connection Test", "✅ Connection successful!", parent=settings_win)
            if on_settings_changed:
                on_settings_changed()
        else:
            messagebox.showerror("Connection Failed", err_msg, parent=settings_win)
            if on_settings_changed:
                on_settings_changed()

    def save_settings():
        new_settings = {
            "sql_server": server_entry.get().strip(),
            "sql_database": db_entry.get().strip(),
            "sql_user": user_entry.get().strip(),
            "sql_password": pass_entry.get().strip(),
            "sql_driver": driver_var.get().strip()
        }

        if not all([new_settings["sql_server"], new_settings["sql_database"],
                    new_settings["sql_user"], new_settings["sql_driver"]]):
            messagebox.showerror("Validation Error", "All fields must be filled.", parent=settings_win)
            return

        ok, err_msg = config.test_connection(new_settings)
        if not ok:
            if not messagebox.askyesno("Connection Failed",
                                       f"Connection test failed:\n{err_msg}\n\nDo you still want to save these settings?",
                                       parent=settings_win):
                return

        if config.save_config(new_settings):
            messagebox.showinfo("Success", "Settings saved.\nThe application will now use these settings.", parent=settings_win)
            if on_settings_changed:
                on_settings_changed()
            settings_win.destroy()
        else:
            messagebox.showerror("Error", "Failed to save settings.\nCheck file permissions.", parent=settings_win)

    btn_test = tb.Button(top_btn_frame, text="Test Connection", command=test_connection,
                         bootstyle=(INFO, OUTLINE), width=18)
    btn_test.pack(side=tk.LEFT, padx=8, ipady=3)

    btn_save = tb.Button(top_btn_frame, text="Save Settings", command=save_settings,
                         bootstyle=SUCCESS, width=20)
    btn_save.pack(side=tk.LEFT, padx=8, ipady=3)

    btn_cancel = tb.Button(bottom_btn_frame, text="Cancel", command=settings_win.destroy,
                           bootstyle=(SECONDARY, OUTLINE), width=18)
    btn_cancel.pack(ipady=3)

    settings_win.bind('<Return>', lambda e: save_settings())

def open_user_manager(parent, app=None, current_user=None, on_self_role_change=None):
    ensure_fonts()
    self_role_callback = on_self_role_change
    um_win = tb.Toplevel(parent)
    um_win.title("مدیریت کاربران")
    um_win.geometry("750x550")
    um_win.resizable(False, False)
    try:
        um_win.iconbitmap(utils.resource_path('app_icon.ico'))
    except:
        pass

    bg_path = utils.resource_path(os.path.join('assets', 'user_management.png'))
    if os.path.exists(bg_path):
        try:
            original_img = Image.open(bg_path)
            resized_img = original_img.resize((750, 550), Image.Resampling.LANCZOS)
            bg_photo = ImageTk.PhotoImage(resized_img)
            bg_label = tk.Label(um_win, image=bg_photo)
            bg_label.image = bg_photo
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            bg_label.lower()
        except Exception:
            pass

    # --- Left side: user list ---
    list_frame = tk.Frame(um_win, width=300, bg="white", bd=1, relief="solid")
    list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=15)
    list_frame.pack_propagate(False)

    tb.Label(
        list_frame, text="لیست کاربران", font=(FONT_MAIN, 14, "bold"),
        bootstyle=PRIMARY, background="white"
    ).pack(anchor="e", pady=(10, 5), padx=10)

    user_list = tk.Listbox(list_frame, font=(FONT_TABLE, 12), bd=0, justify='right')
    user_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # --- Right side: actions ---
    action_frame = tk.Frame(um_win, width=350, bg="white", bd=1, relief="solid")
    action_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=15, pady=15)
    action_frame.pack_propagate(False)

    tb.Label(
        action_frame, text="افزودن کاربر جدید", font=(FONT_MAIN, 14, "bold"),
        background="white"
    ).pack(pady=(15, 10))

    def create_input(label_text, show=None):
        tb.Label(
            action_frame, text=label_text, font=(FONT_MAIN, 11),
            background="white"
        ).pack(anchor="e", pady=(5, 2), padx=20)
        entry = tb.Entry(
            action_frame, justify='center', font=(FONT_MAIN, 11), show=show
        )
        entry.pack(fill=tk.X, padx=20)
        return entry

    new_fullname_ent = create_input(":نام و نام خانوادگی")
    new_user_ent = create_input(":نام کاربری")
    new_pass_ent = create_input(":رمز عبور", show="●")

    tb.Label(
        action_frame, text=":نقش کاربری", font=(FONT_MAIN, 11),
        background="white"
    ).pack(anchor="e", pady=(10, 5), padx=20)
    role_var = tk.StringVar(value="guard")
    radio_frame = tk.Frame(action_frame, bg="white")
    radio_frame.pack(anchor="e", padx=20)
    tb.Radiobutton(
        radio_frame, text="نگهبان", variable=role_var, value="guard",
        bootstyle=PRIMARY
    ).pack(side=tk.RIGHT, padx=10)
    tb.Radiobutton(
        radio_frame, text="مدیر", variable=role_var, value="admin",
        bootstyle=PRIMARY
    ).pack(side=tk.RIGHT, padx=10)

    # --- Edit and Delete buttons frame ---
    edit_delete_frame = tk.Frame(action_frame, bg="white")
    edit_delete_frame.pack(fill=tk.X, pady=(10, 5), padx=20)

    edit_btn = tb.Button(
        edit_delete_frame, text="ویرایش کاربر", bootstyle=(INFO, OUTLINE),
        state=tk.DISABLED
    )
    edit_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(0, 5))

    delete_btn = tb.Button(
        edit_delete_frame, text="حذف کاربر", bootstyle=(DANGER, OUTLINE),
        state=tk.DISABLED
    )
    delete_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

    # --- Functions ---
    def refresh_list():
        user_list.delete(0, tk.END)
        for u, r, fname in database.get_all_users():
            role_fa = "مدیر" if r == 'admin' else "نگهبان"
            display_name = fname if fname else "---"
            user_list.insert(tk.END, f"[{role_fa}]  {display_name}  ({u})")

    def on_user_select(event=None):
        if user_list.curselection():
            edit_btn.config(state=tk.NORMAL)
            delete_btn.config(state=tk.NORMAL)
        else:
            edit_btn.config(state=tk.DISABLED)
            delete_btn.config(state=tk.DISABLED)

    user_list.bind('<<ListboxSelect>>', on_user_select)

    def add_user():
        fname = new_fullname_ent.get().strip()
        u = new_user_ent.get().strip()
        p = new_pass_ent.get().strip()
        r = role_var.get()

        if len(u) < 3 or len(p) < 3:
            messagebox.showwarning(
                "خطا", "نام کاربری و رمز عبور باید حداقل ۳ حرف باشند", parent=um_win
            )
            return
        if len(fname) < 2:
            messagebox.showwarning(
                "خطا", "لطفاً نام و نام خانوادگی را وارد کنید", parent=um_win
            )
            return

        ok, msg = database.create_user(u, p, fname, r)
        if ok:
            database.log_audit(
                "user_created",
                user=current_user,
                details=f"Created user: {u} ({fname}), role: {r}"
            )
            messagebox.showinfo("موفق", f"کاربر {fname} با موفقیت ایجاد شد", parent=um_win)
            for ent in [new_fullname_ent, new_user_ent, new_pass_ent]:
                ent.delete(0, tk.END)
            refresh_list()
            on_user_select()
        else:
            messagebox.showerror("خطا", msg, parent=um_win)

    def delete_selected():
        sel = user_list.curselection()
        if not sel:
            return
        item_text = user_list.get(sel[0])
        username = item_text.split("  (")[-1].replace(")", "").strip()

        if current_user and username == current_user:
            messagebox.showwarning(
                "خطا", ".نمی‌توانید حساب کاربری خود را حذف کنید", parent=um_win
            )
            return

        if messagebox.askyesno(
            "حذف", f"{username} آیا از حذف کاربر مطمئن هستید؟", parent=um_win
        ):
            ok, msg = database.delete_user(username)
            if ok:
                database.log_audit(
                    "user_deleted",
                    user=current_user,
                    details=f"Deleted user: {username}"
                )
                refresh_list()
                on_user_select()
                if app and current_user and username == current_user:
                    um_win.destroy()
                    parent.destroy()
                    app.current_user = None
                    from windows import show_login_screen
                    import main
                    show_login_screen(app, main.setup_dashboard)
            else:
                messagebox.showerror("خطا", msg, parent=um_win)

    def edit_selected():
        sel = user_list.curselection()
        if not sel:
            return
        item_text = user_list.get(sel[0])
        username = item_text.split("  (")[-1].replace(")", "").strip()

        users = database.get_all_users()
        user_data = None
        for u, r, fname in users:
            if u == username:
                user_data = (u, r, fname)
                break
        if not user_data:
            messagebox.showerror("خطا", "کاربر یافت نشد", parent=um_win)
            return

        edit_win = tb.Toplevel(um_win)
        edit_win.title(f"{username} : ویرایش کاربر")
        edit_win.geometry("400x800")
        edit_win.resizable(False, False)
        try:
            edit_win.iconbitmap(utils.resource_path('app_icon.ico'))
        except:
            pass

        canvas = tk.Canvas(edit_win, highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        bg_path_edit = utils.resource_path(os.path.join('assets', 'change_password_bg.png'))
        if os.path.exists(bg_path_edit):
            try:
                pil_img = Image.open(bg_path_edit)
                pil_img = pil_img.resize((400, 800), Image.Resampling.LANCZOS)
                bg_image = ImageTk.PhotoImage(pil_img)
                canvas.create_image(0, 0, image=bg_image, anchor="nw")
                canvas.bg_image = bg_image
            except Exception:
                pass

        card_x1, card_y1 = 30, 50
        card_x2, card_y2 = 370, 750
        points = [
            card_x1 + 20, card_y1,
            card_x2 - 20, card_y1,
            card_x2, card_y1,
            card_x2, card_y1 + 20,
            card_x2, card_y2 - 20,
            card_x2, card_y2,
            card_x2 - 20, card_y2,
            card_x1 + 20, card_y2,
            card_x1, card_y2,
            card_x1, card_y2 - 20,
            card_x1, card_y1 + 20,
            card_x1, card_y1,
        ]
        canvas.create_polygon(points, fill="white", stipple="gray50", outline="#cccccc", width=1, smooth=True)

        form_frame = tk.Frame(canvas, bg='', highlightthickness=0)
        canvas.create_window(200, 400, window=form_frame, width=320, height=620)

        tb.Label(
            form_frame, text=f"✏️ ویرایش کاربر", font=(FONT_MAIN, 16, "bold"),
            bootstyle=PRIMARY, anchor="center", background=''
        ).pack(pady=(10, 15))

        #Full name field
        tb.Label(form_frame, text=": نام و نام خانوادگی", font=(FONT_MAIN, 12), background='').pack(anchor="e", pady=(5, 2))
        fullname_entry = tb.Entry(form_frame, justify='center', font=(FONT_MAIN, 12))
        fullname_entry.insert(0, user_data[2] if user_data[2] else "")
        fullname_entry.pack(fill=tk.X, pady=(0, 10))

        #Username field
        tb.Label(form_frame, text=": نام کاربری", font=(FONT_MAIN, 12), background='').pack(anchor="e", pady=(5, 2))
        username_entry = tb.Entry(form_frame, justify='center', font=(FONT_MAIN, 12))
        username_entry.insert(0, username)
        username_entry.pack(fill=tk.X, pady=(0, 10))

        #Role selection
        tb.Label(form_frame, text=": نقش کاربری", font=(FONT_MAIN, 12), background='').pack(anchor="e", pady=(5, 2))
        role_var_edit = tk.StringVar(value=user_data[1])
        role_frame = tk.Frame(form_frame, bg='')
        role_frame.pack(fill=tk.X, pady=(0, 10))
        tb.Radiobutton(
            role_frame, text="نگهبان", variable=role_var_edit, value="guard",
            bootstyle=PRIMARY
        ).pack(side=tk.RIGHT, padx=10)
        tb.Radiobutton(
            role_frame, text="مدیر", variable=role_var_edit, value="admin",
            bootstyle=PRIMARY
        ).pack(side=tk.RIGHT, padx=10)

        #Password fields
        tb.Label(
            form_frame, text=": رمز عبور جدید (اختیاری)", font=(FONT_MAIN, 12),
            background=''
        ).pack(anchor="e", pady=(5, 2))
        new_pass_edit = tb.Entry(form_frame, show="●", justify='center', font=(FONT_MAIN, 12))
        new_pass_edit.pack(fill=tk.X, pady=(0, 5))

        tb.Label(
            form_frame, text=": تکرار رمز عبور جدید", font=(FONT_MAIN, 12),
            background=''
        ).pack(anchor="e", pady=(5, 2))
        confirm_pass_edit = tb.Entry(form_frame, show="●", justify='center', font=(FONT_MAIN, 12))
        confirm_pass_edit.pack(fill=tk.X, pady=(0, 10))

        status_label = tb.Label(
            form_frame, text="", font=(FONT_MAIN, 11), bootstyle=INFO,
            anchor="center", background=''
        )
        status_label.pack(pady=(0, 10))

        def save_changes():
            new_fullname = fullname_entry.get().strip()
            new_username = username_entry.get().strip()
            new_role = role_var_edit.get()
            new_pass = new_pass_edit.get().strip()
            confirm_pass = confirm_pass_edit.get().strip()

            if not new_fullname or len(new_fullname) < 2:
                status_label.config(text="❌ نام و نام خانوادگی الزامی است", bootstyle=DANGER)
                return
            if not new_username or len(new_username) < 3:
                status_label.config(text="❌ نام کاربری باید حداقل ۳ کاراکتر باشد", bootstyle=DANGER)
                return

            if new_pass or confirm_pass:
                if len(new_pass) < 3:
                    status_label.config(text="❌ رمز عبور باید حداقل ۳ کاراکتر باشد", bootstyle=DANGER)
                    return
                if new_pass != confirm_pass:
                    status_label.config(text="❌ تکرار رمز عبور مطابقت ندارد", bootstyle=DANGER)
                    return

            if new_username != username:
                existing_users = [u for u, _, _ in database.get_all_users()]
                if new_username in existing_users:
                    status_label.config(text="❌ نام کاربری تکراری است", bootstyle=DANGER)
                    return

            if (current_user and username == current_user and
                user_data[1] == 'admin' and new_role != 'admin'):
                users = database.get_all_users()
                admin_count = sum(1 for _, r, _ in users if r == 'admin')
                if admin_count <= 1:
                    status_label.config(
                        text="❌ نمی‌توانید نقش خود را تغییر دهید (آخرین مدیر سیستم)",
                        bootstyle=DANGER
                    )
                    return

            try:
                database.update_user(
                    username,
                    new_username=new_username if new_username != username else None,
                    new_fullname=new_fullname,
                    new_role=new_role,
                    new_password=new_pass if new_pass else None
                )
                database.log_audit(
                    "user_updated",
                    user=current_user,
                    details=f"Updated user {username} -> {new_username}"
                )
                messagebox.showinfo("موفقیت", "✅ اطلاعات کاربر با موفقیت به‌روزرسانی شد", parent=edit_win)
                edit_win.destroy()
                refresh_list()
                on_user_select()
                
                if app and current_user and username == current_user:
                    if new_username != username:
                        app.current_username = new_username
                    if new_fullname != app.current_user:
                        app.current_user = new_fullname
                        app.title(f"سامانه مدیریت ورود و خروج (اداره حراست)   |   کاربر: {new_fullname}")
                    if new_role != app.current_role:
                        app.current_role = new_role
                        for child in app.winfo_children():
                            if isinstance(child, tk.Toplevel):
                                if child.title() in ["پنل مدیریت", "مدیریت کاربران", "آمار تردد", "تحلیل آماری تردد", "خروجی اکسل لاگ حسابرسی"]:
                                    child.destroy()
                        if on_self_role_change:
                            on_self_role_change()
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در به‌روزرسانی: {str(e)}", parent=edit_win)

        btn_frame_edit = tb.Frame(form_frame)
        btn_frame_edit.pack(fill=tk.X, pady=(20, 0))

        tb.Button(
            btn_frame_edit, text="انصراف", command=edit_win.destroy,
            bootstyle=(SECONDARY, OUTLINE), width=12
        ).pack(side=tk.RIGHT, padx=5)

        tb.Button(
            btn_frame_edit, text="ذخیره تغییرات", command=save_changes,
            bootstyle=SUCCESS, width=12
        ).pack(side=tk.RIGHT, padx=5)

        edit_win.bind('<Return>', lambda e: save_changes())

    edit_btn.config(command=edit_selected)
    delete_btn.config(command=delete_selected)

    tb.Button(
        action_frame, text="ثبت کاربر", command=add_user, bootstyle=SUCCESS
    ).pack(fill=tk.X, pady=15, padx=20)

    refresh_list()
    on_user_select()

def show_daily_stats_ui(parent_win):
    ensure_fonts()
    stats_win = tb.Toplevel(parent_win)
    stats_win.title("آمار تردد")
    stats_win.geometry("420x420")
    stats_win.resizable(False,False)
    try: stats_win.iconbitmap(utils.resource_path(os.path.join('assets', 'app_icon.ico')))
    except: pass
    
    main_frame = tb.Frame(stats_win, padding=15)
    main_frame.pack(fill=tk.BOTH, expand=True)

    tb.Label(main_frame, text=":تاریخ مورد نظر را وارد کنید", font=(FONT_MAIN, 12, "bold")).pack(pady=(10, 15))
    
    date_frame = tb.Frame(main_frame)
    date_frame.pack()
    ent_day = tb.Entry(date_frame, justify='center', width=5, font=(FONT_MAIN, 11))
    ent_day.pack(side=tk.RIGHT, padx=2)
    tb.Label(date_frame, text="/", font=(FONT_MAIN, 11)).pack(side=tk.RIGHT)
    ent_month = tb.Entry(date_frame, justify='center', width=5, font=(FONT_MAIN, 11))
    ent_month.pack(side=tk.RIGHT, padx=2)
    tb.Label(date_frame, text="/", font=(FONT_MAIN, 11)).pack(side=tk.RIGHT)
    ent_year = tb.Entry(date_frame, justify='center', width=7, font=(FONT_MAIN, 11))
    ent_year.pack(side=tk.RIGHT, padx=2)
    
    result_lbl = tb.Label(main_frame, text="", font=(FONT_MAIN, 12), justify="center", bootstyle=INFO)
    result_lbl.pack(pady=15)

    def calculate(target_date_str=None):
        if not target_date_str:
            y, m, d = ent_year.get(), ent_month.get(), ent_day.get()
            if not (y and m and d):
                messagebox.showwarning("خطا", "لطفاً تاریخ را کامل وارد کنید", parent=stats_win)
                return
            target_date_str = f"{y}/{m.zfill(2)}/{d.zfill(2)}"
        try:
            total, no_exit = database.get_daily_stats(target_date_str)
            result_lbl.config(text=f"تاریخ: {target_date_str}\n\nتعداد کل ثبت شده: {total}\nبدون ساعت خروج: {no_exit}")
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=stats_win)

    def set_today():
        now_j = jdatetime.date.fromgregorian(date=datetime.now().date())
        ent_year.delete(0, tk.END)
        ent_year.insert(0, str(now_j.year))
        ent_month.delete(0, tk.END)
        ent_month.insert(0, str(now_j.month))
        ent_day.delete(0, tk.END)
        ent_day.insert(0, str(now_j.day))
        calculate(now_j.strftime("%Y/%m/%d"))

    btn_frame = tb.Frame(main_frame)
    btn_frame.pack(fill=tk.X, pady=(10, 0))
    tb.Button(btn_frame, text="امروز", command=set_today, bootstyle=WARNING).pack(side=tk.LEFT, expand=True, padx=5, fill=tk.X, ipady=4)
    tb.Button(btn_frame, text="محاسبه", command=lambda: calculate(), bootstyle=PRIMARY).pack(side=tk.LEFT, expand=True, padx=5, fill=tk.X, ipady=4)

def show_heatmap_analytics(app):
    ensure_fonts()
    analytics_win = tb.Toplevel(app)
    analytics_win.title("تحلیل آماری تردد")
    analytics_win.geometry("1000x800")
    analytics_win.resizable(False, False)
    try: analytics_win.iconbitmap(utils.resource_path('app_icon.ico'))
    except: pass
    
    # ---------- FILTER FRAME ----------
    filter_frame = tb.Frame(analytics_win, padding=10)
    filter_frame.pack(fill=tk.X)
    
    # Time filters row
    time_frame = tb.Frame(filter_frame)
    time_frame.pack(fill=tk.X)
    
    tb.Label(time_frame, text=":فیلتر زمانی", font=(FONT_MAIN, 12, "bold")).pack(side=tk.RIGHT, padx=10)
    cb_day = tb.Combobox(time_frame, values=[""] + [str(i) for i in range(1, 32)], width=3, state="readonly", justify='center')
    cb_day.pack(side=tk.RIGHT, padx=2)
    tb.Label(time_frame, text="روز").pack(side=tk.RIGHT)
    cb_month = tb.Combobox(time_frame, values=[""] + config.PERSIAN_MONTHS, width=10, state="readonly", justify='center')
    cb_month.pack(side=tk.RIGHT, padx=2)
    tb.Label(time_frame, text="ماه").pack(side=tk.RIGHT)
    cb_year = tb.Combobox(time_frame, values=[""] + [str(i) for i in range(1400, 1411)], width=5, state="readonly", justify='center')
    cb_year.pack(side=tk.RIGHT, padx=2)
    tb.Label(time_frame, text="سال").pack(side=tk.RIGHT)
    
    # Department + buttons row
    dept_frame = tb.Frame(filter_frame)
    dept_frame.pack(fill=tk.X, pady=(10, 0))
    
    tb.Label(dept_frame, text=":واحد مربوطه", font=(FONT_MAIN, 12, "bold")).pack(side=tk.RIGHT, padx=10)
    cb_dept = tb.Combobox(dept_frame, values=[""] + config.DEPARTMENT_LIST, width=25, state="readonly", justify='right')
    cb_dept.pack(side=tk.RIGHT, padx=2)
    
    tb.Button(dept_frame, text="نمایش نمودار", command=lambda: update_chart(), bootstyle=PRIMARY).pack(side=tk.LEFT, padx=5)
    tb.Button(dept_frame, text="حذف فیلترها", command=lambda: reset_filters(), bootstyle=(DANGER, OUTLINE)).pack(side=tk.LEFT, padx=5)
    
    # ---------- CHART CONTAINER ----------
    chart_container = tb.Frame(analytics_win, padding=10)
    chart_container.pack(fill=tk.BOTH, expand=True)
    
    # ---------- TOP 3 DEPARTMENTS ----------
    top3_frame = tb.Frame(analytics_win, padding=(10, 15))
    top3_frame.pack(fill=tk.X)
    
    def update_chart():
        for widget in chart_container.winfo_children():
            widget.destroy()
        for widget in top3_frame.winfo_children():
            widget.destroy()
            
        y = cb_year.get()
        m_name = cb_month.get()
        d = cb_day.get()
        dept = cb_dept.get()
        
        data = database.get_hourly_stats(
            year=y if y else None,
            month_name=m_name if m_name in config.PERSIAN_MONTHS else None,
            day=d if d else None,
            department=dept if dept else None
        )
        
        top3 = database.get_top_departments(
            year=y if y else None,
            month_name=m_name if m_name in config.PERSIAN_MONTHS else None,
            day=d if d else None
        )
        
        if not data:
            tb.Label(chart_container, text="اطلاعاتی با این فیلتر یافت نشد", font=(FONT_MAIN, 14), bootstyle=SECONDARY).pack(pady=50)
            if top3:
                tb.Label(top3_frame, text="🏆 ۳ واحد پرتردد:", font=(FONT_MAIN, 12, "bold"), bootstyle=PRIMARY).pack(side=tk.RIGHT, padx=10)
                for i, (dept_name, count) in enumerate(top3, 1):
                    tb.Label(top3_frame, text=f"{i}- {dept_name} ({count})", font=(FONT_TABLE, 10), bootstyle=INFO).pack(side=tk.RIGHT, padx=10)
            else:
                tb.Label(top3_frame, text="واحدی یافت نشد", font=(FONT_MAIN, 11), bootstyle=SECONDARY).pack(side=tk.RIGHT)
            return
        
        hours_found, counts_found = zip(*data) if data else ([], [])
        full_hours = [f"{h:02d}" for h in range(7, 20)]
        full_counts = []
        for h in full_hours:
            if h in hours_found:
                idx = hours_found.index(h)
                full_counts.append(counts_found[idx])
            else:
                full_counts.append(0)
        
        import matplotlib
        matplotlib.rcParams['font.family'] = 'Tahoma'
        
        fig = Figure(figsize=(8, 5), dpi=100)
        fig.patch.set_facecolor('#ffffff')
        ax = fig.add_subplot(111)
        bars = ax.bar(full_hours, full_counts, color='#2596be', width=0.6, zorder=3)
        title_context = "کل ادوار"
        if y:
            title_context = f"سال {y}"
        if m_name in config.PERSIAN_MONTHS:
            title_context += f" - {m_name}"
        if d:
            title_context += f" - روز {d}"
        if dept:
            title_context += f" - {dept}"
        ax.set_title(utils.make_farsi(f"تحلیل تردد - {title_context}"), fontsize=14, fontname='Tahoma')
        ax.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)
        
        for bar in bars:
            if bar.get_height() > 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{int(bar.get_height())}',
                        ha='center', va='bottom', fontsize=10)
        canvas = FigureCanvasTkAgg(fig, master=chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Top 3 display
        if top3:
            tb.Label(top3_frame, text="🏆 ۳ واحد پرتردد:", font=(FONT_MAIN, 12, "bold"), bootstyle=PRIMARY).pack(side=tk.RIGHT, padx=10)
            for i, (dept_name, count) in enumerate(top3, 1):
                rank_colors = {1: "#B8860B", 2: "#708090", 3: "#8B4513"}
                color = rank_colors.get(i, "#555555")
                tb.Label(top3_frame, text=f"{i}- {dept_name} ({count})", font=(FONT_TABLE, 10), foreground=color).pack(side=tk.RIGHT, padx=10)
        else:
            tb.Label(top3_frame, text="واحدی یافت نشد", font=(FONT_MAIN, 11), bootstyle=SECONDARY).pack(side=tk.RIGHT)
    
    def reset_filters():
        cb_year.set("")
        cb_month.set("")
        cb_day.set("")
        cb_dept.set("")
        update_chart()
    
    update_chart()

def open_search_window(app):
    ensure_fonts()
    search_win = tb.Toplevel(app)
    try: search_win.iconbitmap(utils.resource_path('app_icon.ico'))
    except: pass
    search_win.title("مشاهده و جستجوی سوابق")
    search_win.geometry("1300x800") 
    
    current_page = 1
    items_per_page = 50
    total_pages = 1
    current_filters = {} 
    
    search_frame = tb.LabelFrame(search_win, text="فیلترهای جستجو", padding=15, bootstyle=PRIMARY)
    search_frame.pack(fill=tk.X, padx=15, pady=10)
    
    tb.Label(search_frame, text=": نام مهمان").grid(row=0, column=5, sticky=tk.E, padx=(15, 5), pady=5)
    entry_search_name = tb.Entry(search_frame, justify='right')
    entry_search_name.grid(row=0, column=4, sticky=tk.EW, padx=5, pady=5)
    
    tb.Label(search_frame, text=": کد ملی").grid(row=0, column=3, sticky=tk.E, padx=(15, 5), pady=5)
    entry_search_nid = tb.Entry(search_frame, justify='right')
    entry_search_nid.grid(row=0, column=2, sticky=tk.EW, padx=5, pady=5)
    
    tb.Label(search_frame, text=": تاریخ").grid(row=1, column=5, sticky=tk.E, padx=(15, 5), pady=5)
    combo_day = tb.Combobox(search_frame, values=[""] + [str(i) for i in range(1, 32)], justify='center', width=3, state='readonly')
    combo_day.grid(row=1, column=4, sticky=tk.E, padx=(0, 5))
    combo_month = tb.Combobox(search_frame, values=[""] + config.PERSIAN_MONTHS, justify='center', width=10, state='readonly')
    combo_month.grid(row=1, column=4, sticky=tk.E, padx=(0, 55))
    combo_year = tb.Combobox(search_frame, values=[""] + [str(i) for i in range(1404, 1451)], justify='center', width=5, state='readonly')
    combo_year.grid(row=1, column=4, sticky=tk.W, padx=(0, 0))
    
    tb.Label(search_frame, text=": واحد").grid(row=1, column=3, sticky=tk.E, padx=(15, 5), pady=5)
    combo_search_dept = tb.Combobox(search_frame, values=[""] + config.DEPARTMENT_LIST, justify='right', state='readonly')
    combo_search_dept.grid(row=1, column=2, sticky=tk.EW, padx=5, pady=5)
    
    search_frame.columnconfigure(2, weight=1)
    search_frame.columnconfigure(4, weight=1)
    
    tree_frame = tb.Frame(search_win, padding=(15, 5))
    tree_frame.pack(expand=True, fill=tk.BOTH)
    
    tree = tb.Treeview(tree_frame, columns=("id", "visitor_name", "national_id", "employee_to_meet", "department", "entry_time", "shamsi_date", "exit_time", "created_by"), 
                        show='headings', selectmode="browse", bootstyle=PRIMARY)
    
    v_scroll = tb.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    h_scroll = tb.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
    h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
    tree.pack(expand=True, fill=tk.BOTH)
    
    headings = {"id": "شماره", "visitor_name": "نام مهمان", "national_id": "کد ملی", "employee_to_meet": "ملاقات شونده", 
                "department": "واحد", "entry_time": "ساعت ورود", "shamsi_date": "تاریخ ورود", "exit_time": "ساعت خروج", "created_by": "کاربر ثبت کننده"}
    for col, text in headings.items():
        tree.heading(col, text=text)
    
    tree.column("id", width=60, anchor=tk.CENTER)
    tree.column("visitor_name", width=160, anchor=tk.CENTER)
    tree.column("national_id", width=100, anchor=tk.CENTER)
    tree.column("employee_to_meet", width=140, anchor=tk.CENTER)
    tree.column("department", width=200, anchor=tk.CENTER)
    tree.column("entry_time", width=70, anchor=tk.CENTER)
    tree.column("shamsi_date", width=90, anchor=tk.CENTER)
    tree.column("exit_time", width=70, anchor=tk.CENTER)
    tree.column("created_by", width=130, anchor=tk.CENTER)

    pagination_frame = tb.Frame(search_win, padding=10)
    pagination_frame.pack(fill=tk.X)
    lbl_info = tb.Label(pagination_frame, text="", font=(FONT_MAIN, 11))
    lbl_info.pack(side=tk.RIGHT, padx=(10, 20))
    controls_frame = tb.Frame(pagination_frame)
    controls_frame.pack(side=tk.RIGHT, padx=10)
    lbl_page_num = tb.Label(controls_frame, text="1", font=(FONT_MAIN, 14, "bold"), width=4, anchor="center")
    
    def change_page(action):
        nonlocal current_page
        if action == 'first':
            current_page = 1
        elif action == 'prev' and current_page > 1:
            current_page -= 1
        elif action == 'next' and current_page < total_pages:
            current_page += 1
        elif action == 'last':
            current_page = total_pages
        fetch_and_display_records(current_filters)

    tb.Button(controls_frame, text="⏭", command=lambda: change_page('first'), bootstyle=(SECONDARY, OUTLINE)).pack(side=tk.RIGHT, padx=2)
    tb.Button(controls_frame, text="▶", command=lambda: change_page('prev'), bootstyle=(SECONDARY, OUTLINE)).pack(side=tk.RIGHT, padx=2)
    lbl_page_num.pack(side=tk.RIGHT, padx=10)
    tb.Button(controls_frame, text="◀", command=lambda: change_page('next'), bootstyle=(SECONDARY, OUTLINE)).pack(side=tk.RIGHT, padx=2)
    tb.Button(controls_frame, text="⏮", command=lambda: change_page('last'), bootstyle=(SECONDARY, OUTLINE)).pack(side=tk.RIGHT, padx=2)

    def fetch_and_display_records(filters=None):
        nonlocal current_page, total_pages
        if filters is None:
            filters = {}
        
        total_records, rows = database.search_visitors(filters, current_page, items_per_page)
        total_pages = max(1, (total_records + items_per_page - 1) // items_per_page)
        if current_page > total_pages:
            current_page = total_pages
            total_records, rows = database.search_visitors(filters, current_page, items_per_page)
        
        for i in tree.get_children():
            tree.delete(i)
        for r in rows:
            tree.insert("", tk.END, values=(r[0], r[1], r[2], r[3], r[4], r[5], r[6] or "", r[7] or "", r[8] or "---"))
        
        start_idx = (current_page - 1) * items_per_page + 1 if total_records > 0 else 0
        end_idx = min(current_page * items_per_page, total_records)
        lbl_info.config(text=f"نمایش {start_idx} تا {end_idx} از {total_records} رکورد")
        lbl_page_num.config(text=str(current_page))

    def search_action():
        nonlocal current_filters, current_page
        current_page = 1
        current_filters = {
            "name": entry_search_name.get(),
            "nid": entry_search_nid.get(),
            "year": combo_year.get(),
            "month_name": combo_month.get(),
            "day": combo_day.get(),
            "dept": combo_search_dept.get()
        }
        fetch_and_display_records(current_filters)

    def reset_action():
        for w in [entry_search_name, entry_search_nid]:
            w.delete(0, tk.END)
        for w in [combo_year, combo_month, combo_day, combo_search_dept]:
            w.set("")
        search_action()

    def export_to_excel():
        filters = current_filters
        total, all_rows = database.search_visitors(filters, page=1, items_per_page=1000000)
        if not all_rows:
            messagebox.showwarning("هشدار", "رکوردی برای خروجی گرفتن با این فیلترها وجود ندارد", parent=search_win)
            return
        
        columns_export = ["شناسه", "نام مهمان", "کد ملی", "ملاقات شونده", "واحد", "زمان ورود", "تاریخ شمسی", "ساعت خروج", "کاربر ثبت کننده"]
        df = pd.DataFrame(all_rows, columns=columns_export)
        
        file_path = filedialog.asksaveasfilename(
            parent=search_win,
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            title="ذخیره فایل اکسل"
        )
        if file_path:
            df.to_excel(file_path, index=False)
            username = getattr(app, 'current_username', 'سیستم') if app else 'سیستم'
            database.log_audit(
                "data_exported",
                user=username,
                details=f"Excel export: {os.path.basename(file_path)} | Records: {len(all_rows)}"
            )
            messagebox.showinfo("موفق", f"فایل اکسل با موفقیت ذخیره شد:\n{file_path}", parent=search_win)

    def on_tree_double_click(event):
        selected = tree.selection()
        if not selected:
            return
        vals = tree.item(selected[0], "values")
        visitor_id = vals[0]
        visitor_name = vals[1]
        entry_shamsi_date = vals[6]
        
        if vals[7].strip():
            messagebox.showerror("خطا", "ساعت خروج قبلاً ثبت شده است", parent=search_win)
            return
        
        popup = tb.Toplevel(search_win)
        popup.title("ثبت خروج")
        popup.geometry("500x500")
        try:
            popup.iconbitmap(utils.resource_path('app_icon.ico'))
        except:
            pass
        
        p_frame = tb.Frame(popup, padding=30)
        p_frame.pack(fill=tk.BOTH, expand=True)
        tb.Label(p_frame, text="ثبت خروج", font=(FONT_MAIN, 16, "bold"), bootstyle=SUCCESS).pack(pady=(0,5))
        tb.Label(p_frame, text=f": {visitor_name}", font=(FONT_MAIN, 13)).pack(pady=(0,15))
        
        current_shamsi = jdatetime.date.fromgregorian(date=datetime.now().date()).strftime("%Y/%m/%d")
        if entry_shamsi_date != current_shamsi:
            warn_lbl = tb.Label(p_frame, text=f"⚠️ تاریخ ورود: {entry_shamsi_date} (امروز نیست!)",
                                font=(FONT_MAIN, 11), bootstyle=(WARNING, INVERSE), padding=8, anchor="center")
            warn_lbl.pack(fill=tk.X, pady=(0, 15))
        
        tb.Label(p_frame, text=": ساعت خروج را انتخاب کنید", font=(FONT_MAIN, 12)).pack(anchor="e", pady=(0, 5))
        
        t_frame = tb.Frame(p_frame)
        t_frame.pack(pady=10)
        
        h_var = tk.StringVar(value=datetime.now().strftime("%H"))
        m_var = tk.StringVar(value=datetime.now().strftime("%M"))
        
        def set_current_time():
            now = datetime.now()
            h_var.set(now.strftime("%H"))
            m_var.set(now.strftime("%M"))
        
        tb.Button(t_frame, text="زمان فعلی", command=set_current_time, bootstyle=INFO).pack(side=tk.RIGHT, padx=(20, 0))
        tb.Combobox(t_frame, textvariable=m_var, values=[str(i).zfill(2) for i in range(0, 60, 5)], width=4, font=(FONT_MAIN, 12), justify='center', state='readonly').pack(side=tk.RIGHT, padx=5)
        tb.Label(t_frame, text=":", font=(FONT_MAIN, 14, "bold")).pack(side=tk.RIGHT)
        tb.Combobox(t_frame, textvariable=h_var, values=[str(i).zfill(2) for i in range(7, 21)], width=4, font=(FONT_MAIN, 12), justify='center', state='readonly').pack(side=tk.RIGHT, padx=5)
        
        try:
            entry_time_only = vals[5]
            info_lbl = tb.Label(p_frame, text=f"ساعت ورود: {entry_time_only}   |   تاریخ: {entry_shamsi_date}",
                                font=(FONT_MAIN, 11), bootstyle=(INFO, INVERSE), padding=10, anchor="center")
            info_lbl.pack(fill=tk.X, pady=(20, 10))
        except:
            pass
        
        def save_exit():
            hour = h_var.get()
            minute = m_var.get()
            if not hour or not minute:
                messagebox.showerror("خطا", "لطفاً ساعت و دقیقه را انتخاب کنید", parent=popup)
                return
            
            try:
                entry_time_str = vals[5]  # already HH:MM
                entry_h, entry_m = map(int, entry_time_str.split(':'))
                exit_h, exit_m = int(hour), int(minute)
                if (exit_h * 60 + exit_m) < (entry_h * 60 + entry_m):
                    if not messagebox.askyesno("هشدار", f"ساعت خروج قبل از ساعت ورود است.\n\nآیا مطمئن هستید؟", parent=popup):
                        return
            except:
                pass
            
            if entry_shamsi_date != current_shamsi:
                if not messagebox.askyesno("تأیید", "تاریخ ورود با امروز متفاوت است.\n\nآیا مطمئن هستید که می‌خواهید خروج ثبت کنید؟", parent=popup):
                    return
            
            exit_time_str = f"{hour}:{minute}"
            try:
                success = database.update_exit_time(visitor_id, exit_time_str, operator=getattr(app, 'current_username', None))
                if success:
                    database.log_audit(
                        "visitor_exit_recorded",
                        user=getattr(app, 'current_username', 'سیستم'),
                        visitor_id=visitor_id,
                        visitor_name=visitor_name,
                        details=f"Exit time: {exit_time_str} | Entry date: {entry_shamsi_date}"
                    )
                    popup.destroy()
                    fetch_and_display_records(current_filters)
                    messagebox.showinfo("موفق", f"خروج {visitor_name} ثبت شد", parent=search_win)
                else:
                    messagebox.showerror("خطا", "ثبت خروج انجام نشد", parent=popup)
            except Exception as e:
                messagebox.showerror("خطا", str(e), parent=popup)
        
        btn_frame = tb.Frame(p_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        tb.Button(btn_frame, text="انصراف", command=popup.destroy, bootstyle=(DANGER, OUTLINE)).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5, ipady=5)
        tb.Button(btn_frame, text="تایید خروج", command=save_exit, bootstyle=SUCCESS).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5, ipady=5)

    tree.bind("<Double-1>", on_tree_double_click)

    buttons_frame = tb.Frame(search_win, padding=15)
    buttons_frame.pack(fill=tk.X)
    tb.Button(buttons_frame, text="جستجو", command=search_action, bootstyle=PRIMARY, width=15).pack(side=tk.RIGHT, padx=5)
    tb.Button(buttons_frame, text="نمایش همه", command=reset_action, bootstyle=(SECONDARY, OUTLINE), width=15).pack(side=tk.RIGHT, padx=5)
    tb.Button(buttons_frame, text="خروجی اکسل", command=export_to_excel, bootstyle=SUCCESS, width=15).pack(side=tk.LEFT, padx=5)
    
    search_action()

def export_audit_log_excel(parent, app=None):
    ensure_fonts()

    popup = tb.Toplevel(parent)
    popup.title("خروجی اکسل لاگ حسابرسی")
    popup.geometry("480x340")
    popup.resizable(False, False)
    try:
        popup.iconbitmap(utils.resource_path('app_icon.ico'))
    except Exception:
        pass

    tb.Label(
        popup,
        text="بازه تاریخ را وارد کنید",
        font=(FONT_MAIN, 13, "bold"),
        bootstyle=PRIMARY,
        anchor="center",
    ).pack(pady=(24, 16))

    def _date_row(frm, label_text):
        row = tb.Frame(frm)
        row.pack(fill=tk.X, pady=6, padx=30)

        tb.Label(row, text=label_text, font=(FONT_MAIN, 11), width=10,
                 anchor="e").pack(side=tk.RIGHT)

        years  = [str(y) for y in range(1403, 1420)]
        months = config.PERSIAN_MONTHS
        days   = [str(d).zfill(2) for d in range(1, 32)]

        cb_day   = tb.Combobox(row, values=days,   width=4,  state="readonly",
                               font=(FONT_MAIN, 11))
        cb_month = tb.Combobox(row, values=months, width=8,  state="readonly",
                               font=(FONT_MAIN, 11))
        cb_year  = tb.Combobox(row, values=years,  width=7,  state="readonly",
                               font=(FONT_MAIN, 11))

        cb_day.pack(side=tk.LEFT, padx=3)
        cb_month.pack(side=tk.LEFT, padx=3)
        cb_year.pack(side=tk.LEFT, padx=3)

        today = jdatetime.date.today()
        cb_year.set(str(today.year))
        cb_month.set(config.PERSIAN_MONTHS[today.month - 1])
        cb_day.set(str(today.day).zfill(2))

        return cb_year, cb_month, cb_day

    date_frm = tb.Frame(popup)
    date_frm.pack(fill=tk.X)

    cy_start, cm_start, cd_start = _date_row(date_frm, ": از تاریخ")
    cy_end,   cm_end,   cd_end   = _date_row(date_frm, ": تا تاریخ")

    def _generate():
        def _month_num(name):
            if name in config.PERSIAN_MONTHS:
                return config.PERSIAN_MONTHS.index(name) + 1
            return 1

        start_str = (
            f"{cy_start.get()}/"
            f"{_month_num(cm_start.get()):02d}/"
            f"{cd_start.get()}"
        )
        end_str = (
            f"{cy_end.get()}/"
            f"{_month_num(cm_end.get()):02d}/"
            f"{cd_end.get()}"
        )

        if start_str > end_str:
            messagebox.showwarning(
                "خطای تاریخ",
                ".تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد",
                parent=popup,
            )
            return

        rows = database.get_audit_logs(start_str, end_str)

        rows = [tuple(row) for row in rows]

        if not rows:
            messagebox.showwarning(
                "نتیجه‌ای یافت نشد",
                f"هیچ لاگی در بازه\n{start_str}  تا  {end_str}\nوجود ندارد.",
                parent=popup,
            )
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            title="ذخیره لاگ حسابرسی",
            initialfile=f"audit_{start_str.replace('/', '-')}_to_{end_str.replace('/', '-')}.xlsx",
            parent=popup,
        )
        if not file_path:
            return

        username = getattr(app, 'current_username', 'سیستم') if app else 'سیستم'
        database.log_audit(
            "data_exported",
            user=username,
            details=f"Audit log Excel export: {os.path.basename(file_path)} | Records: {len(rows)}"
        )

        col_names = [
            "شناسه",
            "تاریخ (شمسی)",
            "ساعت",
            "نوع رویداد",
            "نام کاربر",
            "شناسه مهمان",
            "نام مهمان",
            "کد ملی",
            "ملاقات‌شونده",
            "واحد",
            "جزئیات",
            "تاریخ ایجاد"
        ]

        try:
            df = pd.DataFrame(rows, columns=col_names)
            df.to_excel(file_path, index=False)
            messagebox.showinfo(
                "موفقیت",
                f"فایل اکسل با {len(rows)} رکورد ذخیره شد.",
                parent=popup,
            )
            popup.destroy()
        except Exception as e:
            messagebox.showerror(
                "خطا",
                f"خطا در ایجاد فایل اکسل:\n{e}",
                parent=popup,
            )

    tb.Button(
        popup,
        text="📥  تولید و ذخیره اکسل",
        command=_generate,
        bootstyle=SUCCESS,
    ).pack(pady=20, ipadx=10, ipady=6)

def open_change_password_window(parent, username):
    ensure_fonts()
    cp_win = tb.Toplevel(parent)
    cp_win.title("تغییر رمز عبور")
    cp_win.geometry("400x700")
    cp_win.resizable(False, False)
    try:
        cp_win.iconbitmap(utils.resource_path(os.path.join('assets', 'app_icon.ico')))
    except:
        pass

    canvas = tk.Canvas(cp_win, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    bg_path = utils.resource_path(os.path.join('assets', 'change_password_bg.png'))
    bg_image = None
    if os.path.exists(bg_path):
        try:
            pil_img = Image.open(bg_path)
            pil_img = pil_img.resize((400, 700), Image.Resampling.LANCZOS)
            bg_image = ImageTk.PhotoImage(pil_img)
            canvas.create_image(0, 0, image=bg_image, anchor="nw")
            canvas.bg_image = bg_image
        except Exception as e:
            print(f"Background error: {e}")

    card_x1, card_y1 = 30, 50
    card_x2, card_y2 = 370, 650
    radius = 20

    points = [
        card_x1 + radius, card_y1,
        card_x2 - radius, card_y1,
        card_x2, card_y1,
        card_x2, card_y1 + radius,
        card_x2, card_y2 - radius,
        card_x2, card_y2,
        card_x2 - radius, card_y2,
        card_x1 + radius, card_y2,
        card_x1, card_y2,
        card_x1, card_y2 - radius,
        card_x1, card_y1 + radius,
        card_x1, card_y1,
    ]
    canvas.create_polygon(points, fill="white", stipple="gray50", outline="#cccccc", width=1, smooth=True)

    form_frame = tk.Frame(canvas, bg='', highlightthickness=0)
    canvas.create_window(200, 350, window=form_frame, width=320, height=520)

    tb.Label(
        form_frame,
        text="🔐 تغییر رمز عبور",
        font=(FONT_MAIN, 16, "bold"),
        bootstyle=PRIMARY,
        anchor="center",
        background=''
    ).pack(pady=(10, 15))

    tb.Label(
        form_frame,
        text=f"{username} : کاربر",
        font=(FONT_MAIN, 12),
        bootstyle=SECONDARY,
        anchor="center",
        background=''
    ).pack(pady=(0, 15))

    tb.Label(form_frame, text=": رمز عبور فعلی", font=(FONT_MAIN, 12), background='').pack(anchor="e", pady=(5, 2))
    current_pass_entry = tb.Entry(form_frame, show="●", justify="center", font=(FONT_MAIN, 12))
    current_pass_entry.pack(fill=tk.X, pady=(0, 10))
    current_pass_entry.focus()

    tb.Label(form_frame, text=": رمز عبور جدید", font=(FONT_MAIN, 12), background='').pack(anchor="e", pady=(5, 2))
    new_pass_entry = tb.Entry(form_frame, show="●", justify="center", font=(FONT_MAIN, 12))
    new_pass_entry.pack(fill=tk.X, pady=(0, 10))

    tb.Label(form_frame, text=": تکرار رمز عبور جدید", font=(FONT_MAIN, 12), background='').pack(anchor="e", pady=(5, 2))
    confirm_pass_entry = tb.Entry(form_frame, show="●", justify="center", font=(FONT_MAIN, 12))
    confirm_pass_entry.pack(fill=tk.X, pady=(0, 15))

    status_label = tb.Label(form_frame, text="", font=(FONT_MAIN, 11), bootstyle=INFO, anchor="center", background='')
    status_label.pack(pady=(0, 10))

    def do_change():
        current_pw = current_pass_entry.get().strip()
        new_pw = new_pass_entry.get().strip()
        confirm_pw = confirm_pass_entry.get().strip()

        if not current_pw:
            status_label.config(text="❌ لطفاً رمز عبور فعلی را وارد کنید", bootstyle=DANGER)
            return
        if len(new_pw) < 3:
            status_label.config(text="❌ رمز عبور جدید باید حداقل ۳ کاراکتر باشد", bootstyle=DANGER)
            return
        if new_pw != confirm_pw:
            status_label.config(text="❌ تکرار رمز عبور مطابقت ندارد", bootstyle=DANGER)
            return

        success, _, _ = database.authenticate_user(username, current_pw)
        if not success:
            status_label.config(text="❌ رمز عبور فعلی اشتباه است", bootstyle=DANGER)
            return

        if database.change_user_password(username, new_pw):
            database.log_audit("user_password_changed", user=username)
            messagebox.showinfo("موفقیت", "✅ رمز عبور با موفقیت تغییر یافت", parent=cp_win)
            cp_win.destroy()
        else:
            status_label.config(text="❌ خطا در به‌روزرسانی رمز عبور", bootstyle=DANGER)

    btn_frame = tb.Frame(form_frame)
    btn_frame.pack(fill=tk.X, pady=(10, 0))

    tb.Button(
        btn_frame,
        text="انصراف",
        command=cp_win.destroy,
        bootstyle=(SECONDARY, OUTLINE),
        width=12
    ).pack(side=tk.RIGHT, padx=5)

    tb.Button(
        btn_frame,
        text="تغییر رمز",
        command=do_change,
        bootstyle=SUCCESS,
        width=12
    ).pack(side=tk.RIGHT, padx=5)

    cp_win.bind('<Return>', lambda e: do_change())

def open_developer_mode(app, on_self_role_change=None):
    ensure_fonts()
    dev_win = tb.Toplevel(app)
    dev_win.title("پنل مدیریت")
    dev_win.geometry("400x700")
    dev_win.resizable(False,False)
    try: dev_win.iconbitmap(utils.resource_path('app_icon.ico'))
    except: pass

    bg_path = utils.resource_path(os.path.join('assets', 'developer.png'))
    if os.path.exists(bg_path):
        try:
            original_img = Image.open(bg_path)
            resized_img = original_img.resize((400, 700), Image.Resampling.LANCZOS)
            bg_photo = ImageTk.PhotoImage(resized_img)
            bg_label = tk.Label(dev_win, image=bg_photo)
            bg_label.image = bg_photo
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            bg_label.lower()
        except Exception: pass

    tb.Label(dev_win, text="ابزارهای مدیریت سیستم", font=(FONT_MAIN, 12, "bold"), bootstyle=PRIMARY).pack(pady=(40, 30))
    
    buttons = [
        ("مدیریت کاربران", lambda: open_user_manager(dev_win, app=app, current_user=app.current_username, on_self_role_change=on_self_role_change), PRIMARY),
        ("تعداد ورودی/خروجی های ثبت شده", lambda: show_daily_stats_ui(dev_win), INFO),
        ("نمودار تحلیل ترافیک", lambda: show_heatmap_analytics(app), WARNING),
        ("لاگ حسابرسی (خروجی اکسل)",lambda: export_audit_log_excel(dev_win, app),INFO),
        ("افزودن ۱۰۰ رکورد آزمایشی", database.add_dummy_data, (SUCCESS, OUTLINE)),
        ("پشتیبان‌گیری از دیتابیس", lambda: utils.do_backup(dev_win, getattr(app, 'current_username', 'admin')), SUCCESS),
        ("بازیابی از فایل پشتیبان", lambda: utils.do_restore(dev_win, getattr(app, 'current_username', 'admin')), (WARNING, OUTLINE)),
    ]
    
    for text, cmd, style in buttons:
        tb.Button(dev_win, text=text, command=cmd, bootstyle=style).pack(fill=tk.X, pady=8, padx=40, ipady=5)
    
    tb.Label(dev_win, text="⚠️ مخصوص راهبر سیستم و پشتیبانی", font=(FONT_MAIN, 10), bootstyle=SECONDARY).pack(side=tk.BOTTOM, pady=10)
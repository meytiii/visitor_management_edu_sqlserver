import os
from tkinter import messagebox
import sys
import json

APP_VERSION = "4.1.3"

APP_DATA_DIR = os.path.join(os.environ['PROGRAMDATA'], 'VisitorSystem')

if not os.path.exists(APP_DATA_DIR):
    try:
        os.makedirs(APP_DATA_DIR)
    except OSError as e:
        messagebox.showerror("Error", f"Could not create database folder:\n{e}")

# ----------------------------------------------------------------------
# DYNAMIC SERVER CONFIGURATION
# ----------------------------------------------------------------------
DEFAULT_SETTINGS = {
    "sql_server": r"10.15.2.26\visitormanager",
    "sql_database": "VisitorSystem",
    "sql_user": "VisitorAppUser",
    "sql_password": "Herasat1405@",
    "sql_driver": "{ODBC Driver 18 for SQL Server}"
}

CONFIG_FILE = os.path.join(APP_DATA_DIR, "server_config.json")

def _rebuild_connection_string():
    global SQL_CONNECTION_STRING, SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASSWORD, SQL_DRIVER
    SQL_CONNECTION_STRING = (
        f"DRIVER={SQL_DRIVER};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USER};"
        f"PWD={SQL_PASSWORD};"
        "Trusted_Connection=no;"
        "Encrypt=no;"
    )

def load_config():
    global SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASSWORD, SQL_DRIVER
    if not os.path.exists(CONFIG_FILE):
        SQL_SERVER = DEFAULT_SETTINGS["sql_server"]
        SQL_DATABASE = DEFAULT_SETTINGS["sql_database"]
        SQL_USER = DEFAULT_SETTINGS["sql_user"]
        SQL_PASSWORD = DEFAULT_SETTINGS["sql_password"]
        SQL_DRIVER = DEFAULT_SETTINGS["sql_driver"]
        _rebuild_connection_string()
        return

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        SQL_SERVER = saved.get("sql_server", DEFAULT_SETTINGS["sql_server"])
        SQL_DATABASE = saved.get("sql_database", DEFAULT_SETTINGS["sql_database"])
        SQL_USER = saved.get("sql_user", DEFAULT_SETTINGS["sql_user"])
        SQL_PASSWORD = saved.get("sql_password", DEFAULT_SETTINGS["sql_password"])
        SQL_DRIVER = saved.get("sql_driver", DEFAULT_SETTINGS["sql_driver"])
        _rebuild_connection_string()
    except Exception as e:
        print(f"Error loading server config: {e}")
        SQL_SERVER = DEFAULT_SETTINGS["sql_server"]
        SQL_DATABASE = DEFAULT_SETTINGS["sql_database"]
        SQL_USER = DEFAULT_SETTINGS["sql_user"]
        SQL_PASSWORD = DEFAULT_SETTINGS["sql_password"]
        SQL_DRIVER = DEFAULT_SETTINGS["sql_driver"]
        _rebuild_connection_string()

def save_config(settings_dict):
    global SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASSWORD, SQL_DRIVER
    SQL_SERVER = settings_dict["sql_server"]
    SQL_DATABASE = settings_dict["sql_database"]
    SQL_USER = settings_dict["sql_user"]
    SQL_PASSWORD = settings_dict["sql_password"]
    SQL_DRIVER = settings_dict["sql_driver"]
    _rebuild_connection_string()

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "sql_server": SQL_SERVER,
                "sql_database": SQL_DATABASE,
                "sql_user": SQL_USER,
                "sql_password": SQL_PASSWORD,
                "sql_driver": SQL_DRIVER
            }, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving server config: {e}")
        return False

def test_connection(settings_dict):
    try:
        conn_str = (
            f"DRIVER={settings_dict['sql_driver']};"
            f"SERVER={settings_dict['sql_server']};"
            f"DATABASE={settings_dict['sql_database']};"
            f"UID={settings_dict['sql_user']};"
            f"PWD={settings_dict['sql_password']};"
            "Trusted_Connection=no;"
            "Encrypt=no;"
        )
        import pyodbc
        conn = pyodbc.connect(conn_str, timeout=5)
        conn.close()
        return True, ""
    except pyodbc.OperationalError as e:
        return False, f"سرور یافت نشد یا در دسترس نیست:\n{e}"
    except pyodbc.ProgrammingError as e:
        return False, f"خطا در اعتبارسنجی یا نام پایگاه داده:\n{e}"
    except Exception as e:
        return False, f"خطای ناشناخته:\n{e}"

load_config()

DEPARTMENT_LIST = [
    "حوزه مدیر کل", "معاونت پرورشی", "معاونت تربیت بدنی",
    "معاونت نهضت سواد آموزی", "معاونت آموزش متوسطه", "معاونت آموزش ابتدایی",
    "اداره حراست", "اداره سنجش", "اداره خدمات و پشتیبانی",
    "امور اداری", "اداره فناوری اطلاعات", "اداره امور مالی و حسابداری",
    "اداره بودجه", "اداره تعاون و رفاه", "اداره استعداد های درخشان",
    "اداره امور شاهد", "اداره بازرسی", "اداره روابط عمومی",
    "اداره حقوقی", "اداره مشارکت ها", "اداره آموزش استثنائی",
    "کارپردازی", "معاونت پژوهش و برنامه ریزی", "هیأت تخلفات" , "دبیرخانه"
]

PERSIAN_MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
]

CULTURAL_MESSAGES = [
    # --- Quran & Hadith ---
    "«اللهم عجل لولیک الفرج»",
    "«الا بذکر الله تطمئن القلوب»",
    "پیامبر اکرم (ص): ز گهواره تا گور دانش بجوی",
    "پیامبر اکرم (ص): دو نعمت مجهولند: سلامت و امنیت",
    "امام علی (ع): هر کس کلمه‌ای به من بیاموزد، مرا بنده خود کرده است",
    "امام علی (ع): فرصت‌ها مانند ابر می‌گذرند، آن‌ها را دریابید",
    "امام صادق (ع): امانت‌داری و راستگویی، کلید رزق و روزی است",
    "امام حسین (ع): نیاز مردم به شما از نعمت‌های خدا بر شماست",
    "امام علی (ع): زینت علم، فروتنی است",
    "پیامبر اکرم (ص): معلمی شغل انبیاست",
    # --- Imam Khomeini (RA) ---
    "امام خمینی (ره): عالم محضر خداست، در محضر خدا معصیت نکنید",
    "امام خمینی (ره): معلم امانت‌داری است که انسان امانت اوست",
    "امام خمینی (ره): دبستان‌ها را دریابید که دانشگاه‌ها دیر است",
    "امام خمینی (ره): آموزش و پرورش کارخانه‌ی انسان‌سازی است",
    "امام خمینی (ره): انتظار فرج، انتظار قدرت اسلام است",
    # --- Supreme Leader (Ayatollah Khamenei) ---
    "مقام معظم رهبری: زنده نگه داشتن یاد شهدا کمتر از شهادت نیست",
    "مقام معظم رهبری: امنیت رکن اساسی پیشرفت کشور است",
    "مقام معظم رهبری: خدمت به مردم، بزرگترین مبارزه با آمریکاست",
    "مقام معظم رهبری: معلمان، افسران سپاه پیشرفت کشور هستند",
    "مقام معظم رهبری: آموزش و پرورش کانون خلق دنیای آینده است",
    "مقام معظم رهبری: هزینه کردن در آموزش و پرورش، سرمایه‌گذاری است",
    "مقام معظم رهبری: حراست، چشم بینا و گوش شنوای سازمان است",
    "مقام معظم رهبری: مدرسه، سلول بنیادی تحول در کشور است",
    # --- Martyr Morteza Motahhari (Education) ---
    "شهید مطهری: معلم باید نیروی فکری متعلم را پرورش دهد",
    "شهید مطهری: ستایشگر معلمی هستم که اندیشیدن را به من بیاموزد",
    # --- General Education & Security Values ---
    "«اداره کل آموزش و پرورش استان همدان - اداره حراست»",
    "تکریم ارباب رجوع، وظیفه شرعی و قانونی ماست",
    "حفظ اسرار و آبروی مومن، از واجبات است",
    "مدرسه قوی، ایران قوی",
    "هر دانش‌آموز، یک امید برای آینده ایران اسلامی",
    "رعایت حجاب و عفاف، ضامن سلامت جامعه است",
    "نظم و انضباط اداری، نشانه تعهد کاری است",
    "با لبخند پاسخگوی مراجعین محترم باشیم",
    "خوش آمدید - با آرزوی روزی پربار برای شما",
    "«سامانه مدیریت هوشمند مراجعین»",
    "شهید رجایی: معلمی شغل نیست، معلمی عشق است",
    "سردار دل‌ها حاج قاسم سلیمانی: ما ملت امام حسینیم",
    "حراست؛ مشاور امین و یاور مدیران",
    "صیانت از کرامت انسانی، رسالت اصلی حراست است",
    "فرزندان خود را به سلاح علم و ایمان مجهز کنید"
]

DEFAULT_DEV_PASSWORD = "herasat_edu@!" 
GREEN_COLOR = "#4CAF50"
GREEN_ACTIVE_COLOR = "#45a049"
BLUE_COLOR = "#008CBA"
BLUE_ACTIVE_COLOR = "#007ba7"
RED_COLOR = "#f44336"
RED_ACTIVE_COLOR = "#d32f2f"
DEFAULT_BG_COLOR = "#F0F0F0"
CARD_BG_COLOR = "#B1E666"

AUDIT_EVENT_TYPES = [
    "login_success",
    "login_failed",
    "logout",
    "app_closed",
    "visitor_added",
    "visitor_exit_recorded",
    "user_created",
    "user_deleted",
    "user_password_changed",
    "user_updated",
    "backup_created",
    "backup_restored",
    "data_exported",
    "developer_mode_enabled",
    "error"
]
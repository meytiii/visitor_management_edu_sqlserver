import os
from tkinter import messagebox
import sys
import json

APP_VERSION = "4.3.0"

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
    "sql_server": os.environ.get("VISITOR_DB_SERVER", r"10.15.2.26\visitormanager"),
    "sql_database": os.environ.get("VISITOR_DB_NAME", "VisitorSystem"),
    "sql_user": os.environ.get("VISITOR_DB_USER", "VisitorAppUser"),
    "sql_password": os.environ.get("VISITOR_DB_PASS", ""),
    "sql_driver": os.environ.get("VISITOR_DB_DRIVER", "{ODBC Driver 18 for SQL Server}"),
    "sql_encrypt": os.environ.get("VISITOR_DB_ENCRYPT", "no"),
    "sql_trust_cert": os.environ.get("VISITOR_DB_TRUST_CERT", "yes")
}

CONFIG_FILE = os.path.join(APP_DATA_DIR, "server_config.json")

def _escape_odbc_val(val):
    if not val:
        return ""
    val_str = str(val)
    if any(c in val_str for c in (';', '{', '}', ' ')):
        escaped = val_str.replace('}', '}}')
        return f"{{{escaped}}}"
    return val_str

def build_connection_string(settings):
    driver = settings.get("sql_driver", DEFAULT_SETTINGS["sql_driver"])
    server = settings.get("sql_server", DEFAULT_SETTINGS["sql_server"])
    database = settings.get("sql_database", DEFAULT_SETTINGS["sql_database"])
    user = settings.get("sql_user", DEFAULT_SETTINGS["sql_user"])
    password = settings.get("sql_password", DEFAULT_SETTINGS["sql_password"])
    encrypt = settings.get("sql_encrypt", DEFAULT_SETTINGS["sql_encrypt"])
    trust_cert = settings.get("sql_trust_cert", DEFAULT_SETTINGS["sql_trust_cert"])

    driver_esc = driver if driver.startswith("{") and driver.endswith("}") else _escape_odbc_val(driver)
    server_esc = _escape_odbc_val(server)
    db_esc = _escape_odbc_val(database)
    user_esc = _escape_odbc_val(user)
    pwd_esc = _escape_odbc_val(password)

    conn_str = (
        f"DRIVER={driver_esc};"
        f"SERVER={server_esc};"
        f"DATABASE={db_esc};"
        f"UID={user_esc};"
        f"PWD={pwd_esc};"
        "Trusted_Connection=no;"
    )

    if encrypt.lower() in ("yes", "true", "1"):
        conn_str += f"Encrypt=yes;TrustServerCertificate={trust_cert};"
    else:
        conn_str += "Encrypt=no;"

    return conn_str

def _rebuild_connection_string():
    global SQL_CONNECTION_STRING, SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASSWORD, SQL_DRIVER, SQL_ENCRYPT, SQL_TRUST_CERT
    SQL_CONNECTION_STRING = build_connection_string({
        "sql_driver": SQL_DRIVER,
        "sql_server": SQL_SERVER,
        "sql_database": SQL_DATABASE,
        "sql_user": SQL_USER,
        "sql_password": SQL_PASSWORD,
        "sql_encrypt": SQL_ENCRYPT,
        "sql_trust_cert": SQL_TRUST_CERT
    })

def load_config():
    global SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASSWORD, SQL_DRIVER, SQL_ENCRYPT, SQL_TRUST_CERT
    if not os.path.exists(CONFIG_FILE):
        SQL_SERVER = DEFAULT_SETTINGS["sql_server"]
        SQL_DATABASE = DEFAULT_SETTINGS["sql_database"]
        SQL_USER = DEFAULT_SETTINGS["sql_user"]
        SQL_PASSWORD = DEFAULT_SETTINGS["sql_password"]
        SQL_DRIVER = DEFAULT_SETTINGS["sql_driver"]
        SQL_ENCRYPT = DEFAULT_SETTINGS["sql_encrypt"]
        SQL_TRUST_CERT = DEFAULT_SETTINGS["sql_trust_cert"]
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
        SQL_ENCRYPT = saved.get("sql_encrypt", DEFAULT_SETTINGS["sql_encrypt"])
        SQL_TRUST_CERT = saved.get("sql_trust_cert", DEFAULT_SETTINGS["sql_trust_cert"])
        _rebuild_connection_string()
    except Exception as e:
        print(f"Error loading server config: {e}")
        SQL_SERVER = DEFAULT_SETTINGS["sql_server"]
        SQL_DATABASE = DEFAULT_SETTINGS["sql_database"]
        SQL_USER = DEFAULT_SETTINGS["sql_user"]
        SQL_PASSWORD = DEFAULT_SETTINGS["sql_password"]
        SQL_DRIVER = DEFAULT_SETTINGS["sql_driver"]
        SQL_ENCRYPT = DEFAULT_SETTINGS["sql_encrypt"]
        SQL_TRUST_CERT = DEFAULT_SETTINGS["sql_trust_cert"]
        _rebuild_connection_string()

def save_config(settings_dict):
    global SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASSWORD, SQL_DRIVER, SQL_ENCRYPT, SQL_TRUST_CERT
    SQL_SERVER = settings_dict["sql_server"]
    SQL_DATABASE = settings_dict["sql_database"]
    SQL_USER = settings_dict["sql_user"]
    SQL_PASSWORD = settings_dict["sql_password"]
    SQL_DRIVER = settings_dict["sql_driver"]
    SQL_ENCRYPT = settings_dict.get("sql_encrypt", "no")
    SQL_TRUST_CERT = settings_dict.get("sql_trust_cert", "yes")
    _rebuild_connection_string()

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "sql_server": SQL_SERVER,
                "sql_database": SQL_DATABASE,
                "sql_user": SQL_USER,
                "sql_password": SQL_PASSWORD,
                "sql_driver": SQL_DRIVER,
                "sql_encrypt": SQL_ENCRYPT,
                "sql_trust_cert": SQL_TRUST_CERT
            }, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving server config: {e}")
        return False

def test_connection(settings_dict):
    try:
        conn_str = build_connection_string(settings_dict)
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
    "visitor_entry_failed",
    "error"
]

# ----------------------------------------------------------------------
# CONNECTION POOL & RETRY CONFIGURATION
# ----------------------------------------------------------------------
POOL_MAX_SIZE = 10
POOL_TIMEOUT = 30
CONN_RETRY_MAX_ATTEMPTS = 5
CONN_RETRY_BASE_DELAY = 1.0
CONN_RETRY_MAX_DELAY = 30.0
CONN_RETRY_BACKOFF_MULTIPLIER = 2.0
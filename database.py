import pyodbc
import random
import hashlib
import binascii
import os
import time
import threading
from datetime import datetime
from queue import Queue, Empty
import jdatetime
from tkinter import messagebox
import config

DEPARTMENT_LIST = config.DEPARTMENT_LIST

# ----------------------------------------------------------------------
# CONNECTION POOL WITH EXPONENTIAL BACKOFF RETRY
# ----------------------------------------------------------------------
class ConnectionPool:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._pool = Queue(maxsize=config.POOL_MAX_SIZE)
        self._pool_lock = threading.Lock()
        self._active_count = 0
        self._max_size = config.POOL_MAX_SIZE
        self._timeout = config.POOL_TIMEOUT
        self._initialized = True
    
    def _create_connection(self):
        """Create a fresh database connection."""
        return pyodbc.connect(
            config.SQL_CONNECTION_STRING,
            autocommit=False,
            timeout=3
        )
    
    def _get_with_retry(self):
        """Get connection with exponential backoff retry."""
        max_attempts = config.CONN_RETRY_MAX_ATTEMPTS
        base_delay = config.CONN_RETRY_BASE_DELAY
        max_delay = config.CONN_RETRY_MAX_DELAY
        multiplier = config.CONN_RETRY_BACKOFF_MULTIPLIER
        
        last_exception = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                return self._create_connection()
            except Exception as e:
                last_exception = e
                if attempt == max_attempts:
                    break
                
                # Calculate delay with exponential backoff + jitter
                delay = min(base_delay * (multiplier ** (attempt - 1)), max_delay)
                jitter = random.uniform(0, delay * 0.3)  # 30% jitter
                sleep_time = delay + jitter
                
                print(f"[Connection Retry] Attempt {attempt}/{max_attempts} failed. "
                      f"Retrying in {sleep_time:.2f}s... Error: {e}")
                time.sleep(sleep_time)
        
        raise last_exception
    
    def get_connection(self):
        """Get connection from pool or create new one with retry logic."""
        # Try to get from pool first
        try:
            conn = self._pool.get(timeout=0.5)
            # Validate connection is still alive
            try:
                conn.execute("SELECT 1")
                return conn
            except:
                conn.close()
                with self._pool_lock:
                    self._active_count -= 1
                # Fall through to create new
        except Empty:
            pass
        
        # Create new connection with retry
        with self._pool_lock:
            if self._active_count < self._max_size:
                self._active_count += 1
            else:
                # Pool full, wait for available connection
                return self._pool.get(timeout=self._timeout)
        
        return self._get_with_retry()
    
    def return_connection(self, conn, is_healthy=True):
        """Return connection to pool or close it."""
        if not is_healthy:
            try:
                conn.close()
            except:
                pass
            with self._pool_lock:
                self._active_count -= 1
            return
        
        try:
            self._pool.put(conn, timeout=1.0)
        except:
            # Pool full or error, close connection
            try:
                conn.close()
            except:
                pass
            with self._pool_lock:
                self._active_count -= 1
    
    def stats(self):
        """Return current pool statistics."""
        return {
            "pool_size": self._pool.qsize(),
            "active_count": self._active_count,
            "max_size": self._max_size
        }


# Global pool instance
_pool_instance = ConnectionPool()


def get_connection():
    """Legacy wrapper — now uses pooled connections with retry."""
    return _pool_instance.get_connection()


def release_connection(conn, is_healthy=True):
    """Return connection to pool. Call this instead of conn.close()."""
    _pool_instance.return_connection(conn, is_healthy)


def pool_stats():
    """Get current connection pool statistics."""
    return _pool_instance.stats()


class DBConnection:
    def __enter__(self):
        self.conn = get_connection()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        is_healthy = exc_type is None
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()
        release_connection(self.conn, is_healthy)


# --- HASHING UTILS ---
def hash_password(password):
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password, provided_password):
    try:
        salt = stored_password[:64]
        stored_password = stored_password[64:]
        pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'), salt.encode('ascii'), 100000)
        pwdhash = binascii.hexlify(pwdhash).decode('ascii')
        return pwdhash == stored_password
    except:
        return False

# --- DATABASE SETUP ---
def setup_database():
    with DBConnection() as conn:
        cursor = conn.cursor()
        
        # Visitors table
        cursor.execute("""
            IF OBJECT_ID('visitors', 'U') IS NULL
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
        
        # Users table
        cursor.execute("""
            IF OBJECT_ID('users', 'U') IS NULL
            CREATE TABLE users (
                id INT IDENTITY(1,1) PRIMARY KEY,
                username NVARCHAR(100) UNIQUE NOT NULL,
                password NVARCHAR(255) NOT NULL,
                role NVARCHAR(50) NOT NULL,
                full_name NVARCHAR(200)
            )
        """)
        
        # Audit log table
        cursor.execute("""
            IF OBJECT_ID('audit_log', 'U') IS NULL
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
        
        try:
            cursor.execute("CREATE INDEX idx_national_id ON visitors (national_id)")
        except:
            pass
        try:
            cursor.execute("CREATE INDEX idx_shamsi_date ON visitors (shamsi_date)")
        except:
            pass
        try:
            cursor.execute("CREATE INDEX idx_visitor_name ON visitors (visitor_name)")
        except:
            pass
        try:
            cursor.execute("CREATE INDEX idx_employee ON visitors (employee_to_meet)")
        except:
            pass
        try:
            cursor.execute("CREATE INDEX idx_audit_date ON audit_log (shamsi_date)")
        except:
            pass
        
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            default_pass = hash_password("admin")
            cursor.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                ("admin", default_pass, "admin", "مدیر سیستم")
            )
            print("Default Admin created")

# --- CACHED DATA FETCHING ---
_cache = {
    "employees": {
        "data": [],
        "timestamp": 0
    }
}
CACHE_DURATION = 300

def get_employee_suggestions(force_refresh=False):
    global _cache
    now = time.time()
    
    if not force_refresh and (now - _cache["employees"]["timestamp"] < CACHE_DURATION):
        return _cache["employees"]["data"]

    try:
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT employee_to_meet, COUNT(*) as cnt 
                FROM visitors 
                WHERE employee_to_meet != '' 
                GROUP BY employee_to_meet 
                ORDER BY cnt DESC
            ''')
            names = [row[0] for row in cursor.fetchall()]
            
            _cache["employees"]["data"] = names
            _cache["employees"]["timestamp"] = now
            return names
    except:
        return []

# --- USER MANAGEMENT ---
def authenticate_user(username, password):
    try:
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password, role, full_name FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            
            if row:
                stored_hash, role, full_name_db = row
                full_name = full_name_db if full_name_db else username
                
                if verify_password(stored_hash, password):
                    return True, role, full_name, ""
                else:
                    return False, None, None, "رمز عبور اشتباه است"
            else:
                return False, None, None, "نام کاربری یافت نشد"
    except Exception as e:
        # Connection or other database error
        return False, None, None, f"خطا در اتصال به پایگاه داده:\n{str(e)}"

def create_user(username, password, full_name, role="guard"):
    try:
        hashed = hash_password(password)
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                (username, hashed, role, full_name)
            )
        return True, ""
    except pyodbc.IntegrityError:
        return False, "نام کاربری تکراری است"
    except Exception as e:
        return False, str(e)

def delete_user(username):
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username = ?", (username,))
        target_role = cursor.fetchone()
        
        if target_role and target_role[0] == 'admin':
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            if cursor.fetchone()[0] <= 1:
                return False, "نمی‌توان آخرین مدیر سیستم را حذف کرد"
                
        try:
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            return True, ""
        except Exception as e:
            return False, str(e)

def get_all_users():
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, role, full_name FROM users")
        return cursor.fetchall()

def change_user_password(username, new_password):
    try:
        hashed = hash_password(new_password)
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed, username))
        return True
    except:
        return False

# --- DATA GENERATION ---
def delete_all_records():
    if not messagebox.askyesno("Danger Zone", "آیا از حذف تمامی اطلاعات پایگاه داده اطمینان دارید؟\n\n!این غیرقابل بازگشت می‌باشد"):
        return
    try:
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM visitors")
            cursor.execute("DBCC CHECKIDENT ('visitors', RESEED, 0)")
        messagebox.showinfo("Developer Mode", ".تمامی اطلاعات پایگاه داده حذف شدند")
    except Exception as e:
        messagebox.showerror("Error", f"حذف اطلاعات با شکست مواجه شد {e}")

def add_dummy_data():
    try:
        first_names = ["علی", "محمد", "رضا", "حسین", "محسن", "احمد", "مهدی", "سارا", "مریم", "زهرا", "فاطمه", "نرگس", "نیما", "کاوه", "امید", "پیمان", "سعید", "بهرام", "نازنین"]
        last_names = ["محمدی", "حسینی", "رضایی", "کریمی", "احمدی", "موسوی", "جعفری", "صادقی", "رحیمی", "عباسی", "باقری", "زاهدی", "میرزایی", "غفاری", "تهرانی", "راد"]
        dummy_records = []
        for _ in range(100):
            visitor_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            employee_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            nid = str(random.randint(1000000000, 9999999999))
            year = random.choice([1403, 1404])
            month = random.randint(1, 12)
            if month <= 6: day = random.randint(1, 31)
            elif month <= 11: day = random.randint(1, 30)
            else: day = random.randint(1, 29)
            shamsi_date = f"{year}/{month:02d}/{day:02d}"
            hour = random.randint(7, 14)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            time_str = f"{hour:02d}:{minute:02d}:{second:02d}"
            try:
                g_date = jdatetime.date(year, month, day).togregorian()
                entry_time_gregorian = f"{g_date.year}-{g_date.month:02d}-{g_date.day:02d} {time_str}"
                entry_dt = datetime.strptime(entry_time_gregorian, "%Y-%m-%d %H:%M:%S")
            except: continue
            dept = random.choice(DEPARTMENT_LIST)
            dummy_records.append({
                "visitor_name": visitor_name, "national_id": nid, "employee_to_meet": employee_name,
                "department": dept, "entry_time": entry_dt, "shamsi_date": shamsi_date
            })
        dummy_records.sort(key=lambda x: x['entry_time'])
        
        with DBConnection() as conn:
            cursor = conn.cursor()
            for r in dummy_records:
                cursor.execute(
                    '''INSERT INTO visitors (visitor_name, national_id, employee_to_meet, department, entry_time, shamsi_date, created_by) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (r['visitor_name'], r['national_id'], r['employee_to_meet'], r['department'], r['entry_time'], r['shamsi_date'], 'dev_debug')
                )
        messagebox.showinfo("Developer Mode", "100 Random Records Added Successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate data: {e}")

def delete_dev_records():
    try:
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM visitors WHERE created_by = 'dev_debug'")
            deleted_count = cursor.rowcount
        messagebox.showinfo("Developer Mode", f"{deleted_count} : تعداد رکورد های آزمایشی حذف شده ")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete dev records: {e}")

# --- AUDIT LOG ---
def setup_audit_table():
    pass

def log_audit(event_type: str, user=None, **kwargs):
    if event_type not in config.AUDIT_EVENT_TYPES:
        print(f"[Audit Log Error] Invalid event type: {event_type}")
        return
    
    try:
        now_j = jdatetime.datetime.now()
        sh_date = now_j.strftime("%Y/%m/%d")
        sh_time = now_j.strftime("%H:%M:%S")
        created_at = datetime.now().isoformat(timespec="seconds")
        
        if user is None:
            user = "System"
        
        visitor_id = kwargs.get("visitor_id")
        visitor_name = kwargs.get("visitor_name")
        national_id = kwargs.get("national_id")
        employee_to_meet = kwargs.get("employee_to_meet")
        department = kwargs.get("department")
        details = kwargs.get("details") or kwargs.get("error") or "No details provided"
        
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO audit_log
                    (shamsi_date, shamsi_time, event_type, user_name,
                     visitor_id, visitor_name, national_id,
                     employee_to_meet, department, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sh_date, sh_time, event_type, user,
                visitor_id, visitor_name, national_id,
                employee_to_meet, department, details, created_at,
            ))
    except Exception as e:
        print(f"[Audit Log Error] {e}")

def get_audit_logs(start_date: str, end_date: str) -> list:
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, shamsi_date, shamsi_time, event_type,
                   user_name, visitor_id, visitor_name,
                   national_id, employee_to_meet, department, details, created_at
            FROM   audit_log
            WHERE  shamsi_date BETWEEN ? AND ?
            ORDER  BY shamsi_date, shamsi_time
        ''', (start_date, end_date))
        return cursor.fetchall()

# --- ADDITIONAL HELPERS FOR MAIN.PY ---
def get_last_department_for_employee(employee_name):
    try:
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 department FROM visitors
                WHERE employee_to_meet = ?
                ORDER BY id DESC
            """, (employee_name,))
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception:
        return None

def get_visitor_name_by_nid(national_id):
    try:
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 visitor_name FROM visitors
                WHERE national_id = ?
                ORDER BY id DESC
            """, (national_id,))
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception:
        return None

def check_duplicate_entry(national_id, employee_to_meet, shamsi_date):
    try:
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM visitors
                WHERE national_id = ? 
                  AND employee_to_meet = ? 
                  AND shamsi_date = ? 
                  AND (exit_time IS NULL OR exit_time = '')
            """, (national_id, employee_to_meet, shamsi_date))
            return cursor.fetchone() is not None
    except Exception:
        return False

def add_visitor(visitor_name, national_id, employee_to_meet, department, entry_time, shamsi_date, created_by):
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO visitors 
                (visitor_name, national_id, employee_to_meet, department, entry_time, shamsi_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (visitor_name, national_id, employee_to_meet, department, entry_time, shamsi_date, created_by))
        
        cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
        row = cursor.fetchone()
        new_id = row[0] if row and row[0] is not None else None
        
        if new_id is None:
            cursor.execute("SELECT CAST(IDENT_CURRENT('visitors') AS INT)")
            new_id = cursor.fetchone()[0]
        
        if new_id is None or new_id == 0:
            cursor.execute("SELECT MAX(id) FROM visitors")
            new_id = cursor.fetchone()[0]
        
        return int(new_id) if new_id is not None else 0


# ----------------------------------------------------------------------
# BACKUP & RESTORE FUNCTIONS
# ----------------------------------------------------------------------
def get_all_visitors_for_backup():
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, visitor_name, national_id, employee_to_meet, department,
                   entry_time, shamsi_date, exit_time, created_by
            FROM visitors
            ORDER BY id
        """)
        return cursor.fetchall()

def get_all_users_for_backup():
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, password, role, full_name
            FROM users
            ORDER BY id
        """)
        return cursor.fetchall()

def get_all_audit_logs_for_backup():
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, shamsi_date, shamsi_time, event_type, user_name,
                   visitor_id, visitor_name, national_id, employee_to_meet,
                   department, details, created_at
            FROM audit_log
            ORDER BY id
        """)
        return cursor.fetchall()

def get_visitor_by_natid_employee_date(national_id, employee_to_meet, shamsi_date, entry_time):
    try:
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM visitors
                WHERE national_id = ?
                  AND employee_to_meet = ?
                  AND shamsi_date = ?
                  AND entry_time = ?
            """, (national_id, employee_to_meet, shamsi_date, entry_time))
            return cursor.fetchone() is not None
    except:
        return False

def get_user_by_username(username):
    """Check if a user already exists."""
    try:
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            return cursor.fetchone() is not None
    except:
        return False

def get_audit_log_duplicate(shamsi_date, shamsi_time, event_type, user_name, details):
    """Check if an audit log entry already exists."""
    try:
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM audit_log
                WHERE shamsi_date = ?
                  AND shamsi_time = ?
                  AND event_type = ?
                  AND user_name = ?
                  AND details = ?
            """, (shamsi_date, shamsi_time, event_type, user_name, details))
            return cursor.fetchone() is not None
    except:
        return False

def insert_visitor_from_backup(visitor_name, national_id, employee_to_meet, department,
                                entry_time, shamsi_date, exit_time, created_by):
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO visitors 
                (visitor_name, national_id, employee_to_meet, department, entry_time, shamsi_date, exit_time, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (visitor_name, national_id, employee_to_meet, department, entry_time, shamsi_date, exit_time, created_by))

def insert_user_from_backup(username, password, role, full_name):
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, role, full_name)
            VALUES (?, ?, ?, ?)
        """, (username, password, role, full_name))

def insert_audit_log_from_backup(shamsi_date, shamsi_time, event_type, user_name,
                                  visitor_id, visitor_name, national_id,
                                  employee_to_meet, department, details, created_at):
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log
                (shamsi_date, shamsi_time, event_type, user_name,
                 visitor_id, visitor_name, national_id,
                 employee_to_meet, department, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (shamsi_date, shamsi_time, event_type, user_name,
              visitor_id, visitor_name, national_id,
              employee_to_meet, department, details, created_at))

# --- ADDITIONAL FUNCTIONS FOR WINDOWS.PY ---

def get_daily_stats(shamsi_date: str):
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM visitors WHERE shamsi_date = ?", (shamsi_date,))
        total = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COUNT(*) FROM visitors WHERE shamsi_date = ? AND (exit_time IS NULL OR exit_time = '')",
            (shamsi_date,)
        )
        no_exit = cursor.fetchone()[0]
        return total, no_exit

def get_hourly_stats(year=None, month_name=None, day=None):
    query = """
        SELECT 
            RIGHT('0' + CAST(DATEPART(hour, entry_time) AS VARCHAR(2)), 2) AS hour,
            COUNT(*) AS cnt
        FROM visitors
        WHERE 1=1
    """
    params = []
    
    if year:
        query += " AND shamsi_date LIKE ?"
        params.append(f"{year}%")
    if month_name and month_name in config.PERSIAN_MONTHS:
        month_num = config.PERSIAN_MONTHS.index(month_name) + 1
        query += " AND shamsi_date LIKE ?"
        params.append(f"%/{month_num:02d}/%")
    if day:
        query += " AND shamsi_date LIKE ?"
        params.append(f"%/{day.zfill(2)}")
    
    query += " GROUP BY DATEPART(hour, entry_time) ORDER BY hour"
    
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [(row[0], row[1]) for row in rows]

def search_visitors(filters: dict, page: int, items_per_page: int):
    """
    Filters can contain:
        'name' (str),
        'nid' (str),
        'year' (str),
        'month_name' (str, Persian month),
        'day' (str, day of month),
        'dept' (str, department name)
    Returns (total_count, list_of_rows) where each row is:
        (id, visitor_name, national_id, employee_to_meet, department,
         entry_time_formatted, shamsi_date, exit_time, created_by)
    entry_time_formatted is HH:MM (24h) as string.
    """
    base_query = """
        FROM visitors
        WHERE 1=1
    """
    params = []
    
    if filters.get("name"):
        base_query += " AND visitor_name LIKE ?"
        params.append(f"%{filters['name']}%")
    if filters.get("nid"):
        base_query += " AND national_id LIKE ?"
        params.append(f"%{filters['nid']}%")
    if filters.get("dept"):
        base_query += " AND department = ?"
        params.append(filters['dept'])
    
    y = filters.get("year")
    m_name = filters.get("month_name")
    d = filters.get("day")
    
    if y:
        base_query += " AND shamsi_date LIKE ?"
        params.append(f"{y}%")
    if m_name and m_name in config.PERSIAN_MONTHS:
        month_num = config.PERSIAN_MONTHS.index(m_name) + 1
        base_query += " AND shamsi_date LIKE ?"
        params.append(f"%/{month_num:02d}/%")
    if d:
        base_query += " AND shamsi_date LIKE ?"
        params.append(f"%/{d.zfill(2)}")
    
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*)" + base_query, params)
        total = cursor.fetchone()[0]
    
    select_query = """
        SELECT 
            id, visitor_name, national_id, employee_to_meet, department,
            FORMAT(entry_time, 'HH:mm') as entry_time_fmt,
            shamsi_date, exit_time, created_by
    """ + base_query + """
        ORDER BY id DESC
        OFFSET ? ROWS
        FETCH NEXT ? ROWS ONLY
    """
    params_page = params + [(page - 1) * items_per_page, items_per_page]
    
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute(select_query, params_page)
        rows = cursor.fetchall()
        return total, [tuple(row) for row in rows]

def update_exit_time(visitor_id: int, exit_time: str, operator: str = None):
    try:
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE visitors SET exit_time = ? WHERE id = ?",
                (exit_time, visitor_id)
            )
        return True
    except Exception:
        return False

def update_user(old_username: str, new_username: str = None, new_fullname: str = None,
                new_role: str = None, new_password: str = None):
    with DBConnection() as conn:
        cursor = conn.cursor()
        if new_fullname:
            cursor.execute(
                "UPDATE users SET full_name = ? WHERE username = ?",
                (new_fullname, old_username)
            )
        if new_role:
            cursor.execute(
                "UPDATE users SET role = ? WHERE username = ?",
                (new_role, old_username)
            )
        if new_password:
            hashed = hash_password(new_password)
            cursor.execute(
                "UPDATE users SET password = ? WHERE username = ?",
                (hashed, old_username)
            )
        if new_username and new_username != old_username:
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (new_username,))
            if cursor.fetchone()[0] > 0:
                raise Exception("نام کاربری تکراری است")
            cursor.execute(
                "UPDATE users SET username = ? WHERE username = ?",
                (new_username, old_username)
            )
    return True
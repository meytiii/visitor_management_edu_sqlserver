import os
import sys
import re
from datetime import datetime
from tkinter import messagebox, filedialog
import arabic_reshaper
from bidi.algorithm import get_display
import config

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
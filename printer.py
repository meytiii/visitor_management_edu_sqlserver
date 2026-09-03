import win32ui
import win32print
import win32con
from tkinter import messagebox
from datetime import datetime

def print_receipt(visitor_id, name, nid, emp, dept, entry_dt, shamsi_date, error_callback=None):
    try:
        if entry_dt is None:
            entry_dt = datetime.now()
        elif isinstance(entry_dt, str):
            try:
                entry_dt = datetime.strptime(entry_dt, "%Y-%m-%d %H:%M:%S")
            except Exception:
                entry_dt = datetime.now()

        try:
            printer_name = win32print.GetDefaultPrinter()
        except Exception as pe:
            err_msg = f"پرینتر پیش‌فرض در سیستم یافت نشد یا تنظیم نشده است:\n{pe}"
            if error_callback:
                error_callback(err_msg)
            else:
                print(f"[Printer Warning] {err_msg}")
            return False

        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)
        hDC.StartDoc("Visitor Receipt")
        hDC.StartPage()
        page_width = hDC.GetDeviceCaps(win32con.HORZRES)

        x_center = page_width // 2
        y = 0
        line_height = 45
        font_data = {"name": "B Roya", "height": 45, "weight": 700}
        f = win32ui.CreateFont(font_data)
        hDC.SelectObject(f)

        headers = [
            ".جامعه معلمان، سربازان گمنام نظام اسلامی هستند",
            "«حضرت آیت‌الله خامنه‌ای»",
            "********************************",
            "اداره کل آموزش و پرورش استان همدان",
            "(اداره حراست)",
            "********************************",
            f"شماره: {visitor_id:06d}",
            f"تاریخ: {shamsi_date}",
            f"ساعت ورود: {entry_dt.strftime('%H:%M')}",
            ":ساعت خروج ",
            "--------------------------------",
            f"ملاقات کننده: {name}",
            f"شماره ملی: {nid}",
            f"معاونت/اداره: {dept}",
            f"ملاقات شونده: {emp}",
            "امضاء ملاقات شونده",
            "",
            "* حداکثر زمان حضور 2 ساعت می باشد *",
            "********************************"
        ]

        hDC.SetTextAlign(win32con.TA_CENTER)
        for line in headers:
            hDC.TextOut(x_center, y, line)
            y += line_height

        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()
        return True
    except Exception as e:
        err_msg = f"خطا در ارتباط با پرینتر:\n{e}"
        if error_callback:
            error_callback(err_msg)
        else:
            print(f"[Printer Error] {err_msg}")
        return False
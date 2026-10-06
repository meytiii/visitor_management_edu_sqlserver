import sys
import io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

from datetime import datetime
import win32print
import printer

def main():
    try:
        current_printer = win32print.GetDefaultPrinter()
        print(f"[*] Default Printer: {current_printer}")
    except Exception as e:
        print(f"[!] Error detecting default printer: {e}")
        return

    try:
        import jdatetime
        shamsi_date = jdatetime.date.today().strftime("%Y/%m/%d")
    except Exception:
        shamsi_date = "۱۴۰۴/۰۷/۰۸"

    now = datetime.now()

    print("[*] Sending test receipt to printer...")
    success = printer.print_receipt(
        visitor_id=129,
        name="محمد مهدی خرّم آبادی",
        nid="3861191376",
        emp="مهدی باقری",
        dept="اداره حراست",
        entry_dt=now,
        shamsi_date=shamsi_date,
        error_callback=lambda err: print(f"[!] Error: {err}")
    )

    if success:
        print(f"[+] Receipt printed successfully on: {current_printer}")
    else:
        print(f"[-] Print failed. Please check printer connection.")

if __name__ == "__main__":
    main()

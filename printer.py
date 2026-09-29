# -*- coding: utf-8 -*-
"""
Thermal Receipt Printing Module
Designed for standard 80mm/58mm POS thermal printers (e.g. POS-80C).
Features:
- Extra bold, high-contrast pure monochrome rasterization (eliminates faint thermal dithering).
- Large, comfortable typography with Vazirmatn-Bold for optimal physical readability.
- Max horizontal width utilization with balanced margins.
- Official Herasat institutional crest and dual signature clearance blocks.
- Standards-compliant Code39 barcode.
"""

import os
import sys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageWin
import arabic_reshaper
from bidi.algorithm import get_display

import win32ui
import win32print
import win32con

from utils import resource_path

def to_persian_digits(text):
    """Convert Latin digits to Persian numerals for administrative authenticity."""
    if text is None:
        return ""
    persian_digits = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }
    return ''.join(persian_digits.get(c, c) for c in str(text))

def reshape_farsi(text):
    """Reshape and reorder bidirectional Persian text for PIL rendering."""
    if not text:
        return ""
    try:
        return get_display(arabic_reshaper.reshape(str(text).strip()))
    except Exception:
        return str(text)

def draw_code39_barcode(draw, text, x_center, y_top, bar_height=52, module_width=2):
    """Draw a clean, standards-compliant Code39 1D barcode on PIL canvas."""
    chars_code39 = {
        '0': '000110100', '1': '100100001', '2': '001100001', '3': '101100000',
        '4': '000110001', '5': '100110000', '6': '001110000', '7': '000100101',
        '8': '100100100', '9': '001100100', '-': '010000101', '*': '010010100'
    }
    cleaned = ''.join(c for c in str(text).upper() if c in chars_code39)
    if not cleaned:
        cleaned = "000000"
    pattern = '*' + cleaned + '*'
    
    elements = []
    for c in pattern:
        p = chars_code39.get(c, chars_code39['0'])
        for idx, bit in enumerate(p):
            is_bar = (idx % 2 == 0)
            w = module_width * 3 if bit == '1' else module_width
            elements.append((is_bar, w))
        elements.append((False, module_width * 2)) # Inter-character quiet gap
    
    total_w = sum(w for _, w in elements)
    curr_x = x_center - (total_w // 2)
    for is_bar, w in elements:
        if is_bar:
            draw.rectangle([curr_x, y_top, curr_x + w - 1, y_top + bar_height], fill=0)
        curr_x += w
    return total_w, bar_height

def generate_receipt_image(visitor_id, name, nid, emp, dept, entry_dt, shamsi_date, width=576, quote=None):
    """
    Renders an extra bold, high-contrast, large-type thermal receipt.
    Width: 576px (Standard 80mm thermal paper at 203 DPI, 72mm printable width).
    Returns an RGB PIL Image where all text is pure solid black (0, 0, 0) to guarantee
    dark, deep, crystal-clear physical printing on POS-80C without faint halftones.
    """
    if entry_dt is None:
        entry_dt = datetime.now()
    elif isinstance(entry_dt, str):
        try:
            entry_dt = datetime.strptime(entry_dt, "%Y-%m-%d %H:%M:%S")
        except Exception:
            try:
                entry_dt = datetime.strptime(entry_dt, "%Y-%m-%d %H:%M")
            except Exception:
                entry_dt = datetime.now()

    if not shamsi_date:
        try:
            import jdatetime
            shamsi_date = jdatetime.date.today().strftime("%Y/%m/%d")
        except Exception:
            shamsi_date = ""

    font_bold_path = resource_path(os.path.join('assets', 'Vazirmatn-Bold.ttf'))
    if not os.path.exists(font_bold_path):
        font_bold_path = resource_path(os.path.join('assets', 'B Roya Bold_0.ttf'))

    def load_font(size):
        try:
            return ImageFont.truetype(font_bold_path, size)
        except Exception:
            return ImageFont.load_default()

    # High-legibility large bold font hierarchy
    f_org_title = load_font(23)
    f_quote = load_font(16)
    f_quote_author = load_font(15)
    f_badge = load_font(21)
    f_meta_lbl = load_font(16)
    f_meta_val = load_font(18)
    f_card_val = load_font(18)
    f_sign_hdr = load_font(15)
    f_sign_sub = load_font(14)
    f_rules = load_font(14)
    f_serial = load_font(15)

    img_canvas_height = 1500
    img = Image.new('L', (width, img_canvas_height), 255)
    draw = ImageDraw.Draw(img)

    margin = 10
    usable_w = width - (2 * margin)
    x_center = width // 2
    x_right = width - margin
    x_left = margin

    def draw_text_center(y_pos, text, font):
        reshaped = reshape_farsi(text)
        bbox = draw.textbbox((0, 0), reshaped, font=font)
        w = bbox[2] - bbox[0]
        draw.text((x_center - (w // 2), y_pos), reshaped, font=font, fill=0)
        return y_pos + (bbox[3] - bbox[1])

    def draw_text_right(x_pos, y_pos, text, font):
        reshaped = reshape_farsi(text)
        bbox = draw.textbbox((0, 0), reshaped, font=font)
        w = bbox[2] - bbox[0]
        draw.text((x_pos - w, y_pos), reshaped, font=font, fill=0)
        return w, bbox[3] - bbox[1]

    def draw_text_left(x_pos, y_pos, text, font):
        reshaped = reshape_farsi(text)
        draw.text((x_pos, y_pos), reshaped, font=font, fill=0)
        bbox = draw.textbbox((0, 0), reshaped, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def draw_centered_card_row(y_pos, lbl_text, val_text):
        full_text = f"{lbl_text} {val_text}"
        reshaped = reshape_farsi(full_text)
        bbox = draw.textbbox((0, 0), reshaped, font=f_card_val)
        w = bbox[2] - bbox[0]
        draw.text((x_center - (w // 2), y_pos), reshaped, font=f_card_val, fill=0)

    # --- 1. OFFICIAL HERASAT LOGO (Prominent 120px) ---
    y = 15
    logo_path = resource_path(os.path.join('assets', 'logo khali.png'))
    if os.path.exists(logo_path):
        try:
            raw_logo = Image.open(logo_path).convert('RGBA')
            logo_dim = 120
            logo_resized = raw_logo.resize((logo_dim, logo_dim), Image.LANCZOS)
            img.paste(logo_resized.convert('L'), (x_center - (logo_dim // 2), y), mask=logo_resized.split()[3])
            y += logo_dim + 12
        except Exception:
            y += 6

    # --- 2. ORGANIZATION HEADERS (Both same size: 23pt bold) ---
    y = draw_text_center(y, "اداره کل آموزش و پرورش استان همدان", f_org_title) + 6
    y = draw_text_center(y, "اداره حراست", f_org_title) + 10

    # --- 3. SAYING WITH UPDATED ATTRIBUTION (16pt bold & 15pt bold) ---
    q_line1 = quote[0] if quote and len(quote) > 0 else "« جامعه معلمان، سربازان گمنام نظام اسلامی هستند »"
    q_line2 = quote[1] if quote and len(quote) > 1 else "قائد شهید (رضوان‌الله تعالی علیه)"
    y = draw_text_center(y, q_line1, f_quote) + 5
    y = draw_text_center(y, q_line2, f_quote_author) + 16

    # --- 4. DOUBLE RULE DIVIDER (Thick solid black rules) ---
    draw.line([x_left, y, x_right, y], fill=0, width=3)
    draw.line([x_left, y + 5, x_right, y + 5], fill=0, width=2)
    y += 18

    # --- 5. TITLE BADGE (Solid Black Pill with Inverted White Vazir) ---
    badge_h = 44
    badge_rect = [x_left + 25, y, x_right - 25, y + badge_h]
    draw.rounded_rectangle(badge_rect, radius=8, fill=0)
    badge_text = "« بـرگـه ورود مـراجـعـیـن »"
    reshaped_badge = reshape_farsi(badge_text)
    bbox_b = draw.textbbox((0, 0), reshaped_badge, font=f_badge)
    bw = bbox_b[2] - bbox_b[0]
    bh = bbox_b[3] - bbox_b[1]
    draw.text((x_center - (bw // 2), y + ((badge_h - bh) // 2) - 2), reshaped_badge, font=f_badge, fill=255)
    y += badge_h + 16

    # --- 6. METADATA SECTION (90px height, bold text) ---
    meta_box_h = 90
    draw.rounded_rectangle([x_left, y, x_right, y + meta_box_h], radius=7, outline=0, width=2)
    draw.line([x_left, y + (meta_box_h // 2), x_right, y + (meta_box_h // 2)], fill=0, width=2)
    draw.line([x_center, y, x_center, y + meta_box_h], fill=0, width=2)

    # Row 1 (y + 10)
    r1_y = y + 10
    # Top Right Cell: شماره برگه
    draw_text_right(x_right - 14, r1_y, "شماره برگه:", f_meta_lbl)
    draw_text_left(x_center + 16, r1_y, to_persian_digits(f"{visitor_id:06d}"), f_meta_val)

    # Top Left Cell: تاریخ
    draw_text_right(x_center - 14, r1_y, "تـاریـخ:", f_meta_lbl)
    draw_text_left(x_left + 16, r1_y, to_persian_digits(shamsi_date), f_meta_val)

    # Row 2 (y + 55)
    r2_y = y + (meta_box_h // 2) + 10
    # Bottom Right Cell: ساعت ورود
    time_str = entry_dt.strftime("%H:%M") if isinstance(entry_dt, datetime) else str(entry_dt)
    draw_text_right(x_right - 14, r2_y, "ساعت ورود:", f_meta_lbl)
    draw_text_left(x_center + 16, r2_y, to_persian_digits(time_str), f_meta_val)

    # Bottom Left Cell: ساعت خروج (Dedicated neat stamp box)
    draw_text_right(x_center - 14, r2_y, "ساعت خروج:", f_meta_lbl)
    exit_box_w = 80
    exit_box_h = 28
    exit_box_x = x_left + 16
    draw.rounded_rectangle([exit_box_x, r2_y - 2, exit_box_x + exit_box_w, r2_y - 2 + exit_box_h], radius=4, outline=0, width=1)
    colon_text = reshape_farsi(":")
    draw.text((exit_box_x + (exit_box_w // 2) - 3, r2_y), colon_text, font=f_meta_val, fill=80)

    y += meta_box_h + 16

    # --- 7. TITLE BADGE 2: مشخصات مراجع و مقصد (Identical solid black box & font as Badge 1) ---
    badge2_h = 44
    badge2_rect = [x_left + 25, y, x_right - 25, y + badge2_h]
    draw.rounded_rectangle(badge2_rect, radius=8, fill=0)
    badge2_text = "« مشخصات مراجع و مقصد »"
    reshaped_badge2 = reshape_farsi(badge2_text)
    bbox_b2 = draw.textbbox((0, 0), reshaped_badge2, font=f_badge)
    b2w = bbox_b2[2] - bbox_b2[0]
    b2h = bbox_b2[3] - bbox_b2[1]
    draw.text((x_center - (b2w // 2), y + ((badge2_h - b2h) // 2) - 2), reshaped_badge2, font=f_badge, fill=255)
    y += badge2_h + 12

    # Details Card Box (Centered layout, large bold text)
    card_h = 185
    draw.rounded_rectangle([x_left, y, x_right, y + card_h], radius=7, outline=0, width=2)

    card_y = y + 16
    # Row 1: مراجع محترم
    draw_centered_card_row(card_y, "مراجع محترم:", str(name))

    # Row 2: کد ملی
    card_y += 38
    draw_centered_card_row(card_y, "کد ملی:", to_persian_digits(nid))

    # Centered Inner separator hairline
    card_y += 32
    draw.line([x_left + 30, card_y, x_right - 30, card_y], fill=0, width=1)
    card_y += 12

    # Row 3: واحد مقصد
    draw_centered_card_row(card_y, "واحد مقصد:", str(dept))

    # Row 4: ملاقات‌شونده
    card_y += 38
    draw_centered_card_row(card_y, "ملاقات‌شونده:", str(emp))

    y += card_h + 16

    # --- 8. BARCODE & SERIAL NUMBER ---
    serial_str = f"{visitor_id:06d}"
    draw_code39_barcode(draw, serial_str, x_center, y, bar_height=52, module_width=2)
    y += 56
    draw_text_center(y, f"* {serial_str} *", f_serial)
    y += 24

    # --- 9. SIGNATURE & CLEARANCE BOXES (115px height) ---
    box_w = (usable_w - 12) // 2
    box_h = 115

    # Right Box: ملاقات‌شونده
    b_right_x1 = x_right - box_w
    b_right_x2 = x_right
    draw.rounded_rectangle([b_right_x1, y, b_right_x2, y + box_h], radius=6, outline=0, width=2)
    draw.rounded_rectangle([b_right_x1, y, b_right_x2, y + 28], radius=5, fill=0)
    draw.rectangle([b_right_x1, y + 18, b_right_x2, y + 28], fill=0)
    t_r = reshape_farsi("امضاء و نظر ملاقات‌شونده")
    tb_r = draw.textbbox((0, 0), t_r, font=f_sign_hdr)
    draw.text((b_right_x1 + (box_w - (tb_r[2] - tb_r[0])) // 2, y + 4), t_r, font=f_sign_hdr, fill=255)
    draw_text_left(b_right_x1 + 12, y + box_h - 24, "ساعت خاتمه: ______", f_sign_sub)

    # Left Box: انتظامات / خروج
    b_left_x1 = x_left
    b_left_x2 = x_left + box_w
    draw.rounded_rectangle([b_left_x1, y, b_left_x2, y + box_h], radius=6, outline=0, width=2)
    draw.rounded_rectangle([b_left_x1, y, b_left_x2, y + 28], radius=5, fill=0)
    draw.rectangle([b_left_x1, y + 18, b_left_x2, y + 28], fill=0)
    t_l = reshape_farsi("تایید و مهر انتظامات (خروج)")
    tb_l = draw.textbbox((0, 0), t_l, font=f_sign_hdr)
    draw.text((b_left_x1 + (box_w - (tb_l[2] - tb_l[0])) // 2, y + 4), t_l, font=f_sign_hdr, fill=255)
    draw_text_left(b_left_x1 + 12, y + box_h - 24, "امضاء انتظامات: ______", f_sign_sub)

    y += box_h + 16

    # --- 10. INSTRUCTIONS & POLICY RULES (14pt Bold) ---
    draw.line([x_left, y, x_right, y], fill=0, width=2)
    y += 10
    draw_text_right(x_right - 4, y, "• حداکثر مدت زمان مجاز حضور در اداره ۲ ساعت می‌باشد.", f_rules)
    y += 24
    draw_text_right(x_right - 4, y, "• همراه داشتن این برگه الزامی بوده و هنگام خروج تحویل انتظامات گردد.", f_rules)
    y += 30

    # --- 11. BOTTOM FOOTER & TEAR LINE ---
    draw_text_center(y, "سامانه هوشمند مدیریت مراجعین و تردد اداره حراست", f_rules)
    y += 22

    # Dashed tear line
    dash_w = 10
    gap_w = 8
    cx = x_left
    while cx < x_right:
        draw.line([cx, y, min(cx + dash_w, x_right), y], fill=0, width=2)
        cx += dash_w + gap_w
    
    # Extra paper feed margin (45px) for physical thermal cutter blade
    y += 45

    cropped = img.crop((0, 0, width, y))

    # Pure solid black thresholding:
    # A balanced threshold ensures anti-aliased black text on white remains solid and deep,
    # while white inverted text on solid black boxes (like "برگه ورود مراجعین" and "مشخصات مراجع و مقصد")
    # retains its full stroke thickness without erosion.
    thresholded = cropped.point(lambda p: 0 if p < 140 else 255, mode='1')
    return thresholded.convert('RGB')


def print_receipt(visitor_id, name, nid, emp, dept, entry_dt, shamsi_date, error_callback=None):
    """
    Sends the beautifully styled receipt to the default Windows thermal printer.
    Preserves backward compatibility with all existing callers.
    """
    try:
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

        # Standard thermal roll width is 576 dots (80mm) or 384 dots (58mm)
        target_w = page_width if 384 <= page_width <= 800 else 576

        receipt_img = generate_receipt_image(
            visitor_id=visitor_id,
            name=name,
            nid=nid,
            emp=emp,
            dept=dept,
            entry_dt=entry_dt,
            shamsi_date=shamsi_date,
            width=target_w
        )

        # Center horizontally if page_width > receipt_img.width (e.g. A4 or virtual printer)
        x_offset = max(0, (page_width - receipt_img.width) // 2) if page_width > receipt_img.width else 0

        dib = ImageWin.Dib(receipt_img)
        dib.draw(hDC.GetHandleOutput(), (x_offset, 0, x_offset + receipt_img.width, receipt_img.height))

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
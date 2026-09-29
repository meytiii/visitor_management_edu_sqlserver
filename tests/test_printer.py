# -*- coding: utf-8 -*-
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from PIL import Image

import printer

class TestPrinterReceipt(unittest.TestCase):
    def test_to_persian_digits(self):
        self.assertEqual(printer.to_persian_digits("0123456789"), "۰۱۲۳۴۵۶۷۸۹")
        self.assertEqual(printer.to_persian_digits("1403/07/08"), "۱۴۰۳/۰۷/۰۸")
        self.assertEqual(printer.to_persian_digits(None), "")

    def test_reshape_farsi(self):
        text = "اداره کل آموزش و پرورش"
        reshaped = printer.reshape_farsi(text)
        self.assertTrue(len(reshaped) > 0)
        self.assertEqual(printer.reshape_farsi(""), "")
        self.assertEqual(printer.reshape_farsi(None), "")

    def test_draw_code39_barcode(self):
        img = Image.new('RGB', (300, 100), (255, 255, 255))
        draw = MagicMock()
        total_w, bar_h = printer.draw_code39_barcode(draw, "000124", x_center=150, y_top=10, bar_height=40, module_width=2)
        self.assertTrue(total_w > 0)
        self.assertEqual(bar_h, 40)
        self.assertTrue(draw.rectangle.called)

    def test_generate_receipt_image_standard(self):
        now = datetime(2024, 9, 29, 9, 30)
        img = printer.generate_receipt_image(
            visitor_id=124,
            name="علی محمدی",
            nid="3871234567",
            emp="مهندس احمدی",
            dept="اداره فناوری اطلاعات",
            entry_dt=now,
            shamsi_date="۱۴۰۳/۰۷/۰۸",
            width=576
        )
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.width, 576)
        self.assertEqual(img.mode, 'RGB')
        # Receipt should have substantial content height
        self.assertGreater(img.height, 700)

    def test_generate_receipt_image_edge_cases(self):
        # Empty dates, string dates, None values
        img = printer.generate_receipt_image(
            visitor_id=0,
            name="",
            nid="",
            emp="",
            dept="",
            entry_dt=None,
            shamsi_date="",
            width=576
        )
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.width, 576)

    @patch('printer.win32print.GetDefaultPrinter', side_effect=Exception("No default printer"))
    def test_print_receipt_no_default_printer(self, mock_get_printer):
        errors = []
        result = printer.print_receipt(
            visitor_id=1,
            name="تست",
            nid="123",
            emp="تست",
            dept="تست",
            entry_dt=None,
            shamsi_date="",
            error_callback=lambda msg: errors.append(msg)
        )
        self.assertFalse(result)
        self.assertEqual(len(errors), 1)
        self.assertIn("پرینتر پیش‌فرض", errors[0])

    @patch('printer.win32print.GetDefaultPrinter', return_value="POS-80C")
    @patch('printer.win32ui.CreateDC')
    @patch('printer.ImageWin.Dib')
    def test_print_receipt_success(self, mock_dib_cls, mock_create_dc, mock_get_printer):
        mock_dc = MagicMock()
        mock_dc.GetDeviceCaps.return_value = 576
        mock_create_dc.return_value = mock_dc

        mock_dib = MagicMock()
        mock_dib_cls.return_value = mock_dib

        result = printer.print_receipt(
            visitor_id=124,
            name="رضا رضایی",
            nid="3871234567",
            emp="کارشناس",
            dept="امور اداری",
            entry_dt=datetime.now(),
            shamsi_date="۱۴۰۳/۰۷/۰۸"
        )
        self.assertTrue(result)
        mock_dc.StartDoc.assert_called_once_with("Visitor Receipt")
        mock_dc.StartPage.assert_called_once()
        mock_dib.draw.assert_called_once()
        mock_dc.EndPage.assert_called_once()
        mock_dc.EndDoc.assert_called_once()
        mock_dc.DeleteDC.assert_called_once()

if __name__ == '__main__':
    unittest.main()

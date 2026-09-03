import unittest
import tkinter as tk
import widgets

class TestWidgets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create hidden root window for tkinter widget testing
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def test_autocomplete_comparison_matching(self):
        names = ["علی محمدی", "محمد رضایی", "سارا کریمی", "مهدی رضایی", "احمد احمدی"]
        entry = widgets.AutocompleteEntry(self.root, completevalues=names)

        # Prefix match
        entry.var.set("علی")
        matches = entry.comparison()
        self.assertIn("علی محمدی", matches)

        # Substring / last name match (critical fix in P1-2)
        entry.var.set("رضایی")
        matches = entry.comparison()
        self.assertIn("محمد رضایی", matches)
        self.assertIn("مهدی رضایی", matches)

        # Empty match
        entry.var.set("")
        matches = entry.comparison()
        self.assertEqual(matches, [])

        # Non-matching
        entry.var.set("کامران")
        matches = entry.comparison()
        self.assertEqual(matches, [])

    def test_autocomplete_selection_when_closed_advances_focus(self):
        entry1 = widgets.AutocompleteEntry(self.root, completevalues=["تست"])
        entry2 = tk.Entry(self.root)
        entry1.pack()
        entry2.pack()

        # Create mock event for Return key when listbox is not up
        mock_event = tk.Event()
        mock_event.keysym = "Return"

        res = entry1.selection(mock_event)
        self.assertEqual(res, "break")

    def test_rounded_entry_get_delete(self):
        rentry = widgets.RoundedEntry(self.root)
        rentry.entry.insert(0, "TestValue")
        self.assertEqual(rentry.get(), "TestValue")
        rentry.delete(0, tk.END)
        self.assertEqual(rentry.get(), "")

if __name__ == "__main__":
    unittest.main()

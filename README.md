# Visitor Management System (Security Dept) | سیستم مدیریت ورود و خروج
![background image](background.png)
A lightweight, user-friendly Desktop Application designed for security guards at the **Education Department of Hamedan (اداره کل آموزش و پرورش استان همدان)** to track visitor entries and exits efficiently.

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 📋 Features

*   **Visitor Registration:** Quickly record visitor details (Name, National ID, Host, Department).
*   **Thermal Receipt Printing:** Automatically generates and prints a visitor pass/receipt to the default Windows printer immediately after registration.
*   **Jalali Calendar (Hijri Shamsi):** Full support for Persian dates using `jdatetime`.
*   **Database Storage:** Stores all records locally using SQLite.
*   **Search & History:**
    *   Advanced filtering by Name, National ID, Department, and Date.
    *   User-friendly Date Dropdowns (Year/Month/Day).
*   **Exit Management:** Simple double-click action to record the exit time for a visitor.
*   **Persian UI:** Fully localized Right-to-Left (RTL) interface optimized for Persian users.

## 🛠️ Tech Stack

*   **Language:** Python 3.x
*   **GUI Framework:** Tkinter (Standard Python GUI) & Ttk (Themed Tkinter)
*   **Database:** SQLite3
*   **Date Handling:** `jdatetime` (for Hijri Shamsi conversion)

## 🚀 Installation & Usage

### Prerequisites
Ensure you have [Python](https://www.python.org/) installed on your machine.

### 1. Clone the Repository
```bash
git clone https://github.com/meytiii/visitor_management_edu.git
cd visitor_management_edu

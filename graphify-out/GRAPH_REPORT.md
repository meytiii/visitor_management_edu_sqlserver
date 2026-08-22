# Graph Report - visitor_management_edu_sqlserver  (2026-08-22)

## Corpus Check
- 20 files · ~281,810 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 149 nodes · 287 edges · 15 communities (11 shown, 4 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 16 edges (avg confidence: 0.82)
- Token cost: 1,250 input · 850 output

## Community Hubs (Navigation)
- Application Core & Form Controller
- UI Assets & User Documentation
- Database Schema & CRUD Operations
- Custom UI Widgets & Autocomplete
- Database Connection Pooling & Concurrency
- Backup Restoration & Record Sync
- SQLite to SQL Server Migration
- System Configuration & Connection Management
- Autofill Suggestions & Privacy Controls
- Audit Logging & System Backup
- User Authentication & Credential Security
- Database Context Manager Acquisition
- Database Context Manager Release
- Visitor Search & Query Filtering

## God Nodes (most connected - your core abstractions)
1. `DBConnection` - 40 edges
2. `resource_path()` - 13 edges
3. `ensure_fonts()` - 11 edges
4. `open_developer_mode()` - 11 edges
5. `AutocompleteEntry` - 10 edges
6. `ConnectionPool` - 9 edges
7. `submit_visitor()` - 9 edges
8. `do_restore()` - 9 edges
9. `log_audit()` - 6 edges
10. `_ensure_hidden_table()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `open_server_settings()` --indirect_call--> `test_connection()`  [INFERRED]
  windows.py → config.py
- `setup_background()` --calls--> `resource_path()`  [EXTRACTED]
  main.py → utils.py
- `submit_visitor()` --calls--> `log_audit()`  [EXTRACTED]
  main.py → database.py
- `do_restore()` --calls--> `log_audit()`  [EXTRACTED]
  utils.py → database.py
- `auto_fill_department()` --calls--> `get_last_department_for_employee()`  [EXTRACTED]
  main.py → database.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **UI Visual & Branding Asset Suite** — assets_background_background, assets_change_password_bg_change_password_bg, assets_developer_developer, assets_icon_icon, assets_login_login [INFERRED 0.85]

## Communities (15 total, 4 thin omitted)

### Community 0 - "Application Core & Form Controller"
Cohesion: 0.10
Nodes (23): PyInstaller Packaging & Windows Build Instructions, test_connection(), get_visitor_name_by_nid(), auto_fill_department(), check_returning_visitor(), clear_fields(), cycle_cultural_messages(), force_disconnect() (+15 more)

### Community 1 - "UI Assets & User Documentation"
Cohesion: 0.21
Nodes (21): Main Application Background Banner, Password Change Dialog Graphic, Developer Avatar / About Graphic, Administrator & Supervisor Guide (??????? ??????), Operator User Guide (??????? ?????? ??? ???? ? ????), Application Window & Taskbar Icon, Login Window Illustration, UI Asset (user_management.png) (+13 more)

### Community 2 - "Database Schema & CRUD Operations"
Cohesion: 0.18
Nodes (18): add_dummy_data(), add_visitor(), authenticate_user(), check_duplicate_entry(), DBConnection, delete_all_records(), delete_dev_records(), delete_user() (+10 more)

### Community 3 - "Custom UI Widgets & Autocomplete"
Cohesion: 0.15
Nodes (3): AutocompleteEntry, RoundedButton, RoundedEntry

### Community 5 - "Backup Restoration & Record Sync"
Cohesion: 0.22
Nodes (9): get_audit_log_duplicate(), get_user_by_username(), get_visitor_by_natid_employee_date(), insert_audit_log_from_backup(), insert_user_from_backup(), insert_visitor_from_backup(), Check if a user already exists., Check if an audit log entry already exists. (+1 more)

### Community 6 - "SQLite to SQL Server Migration"
Cohesion: 0.48
Nodes (6): drop_and_create_tables(), main(), migrate_audit_log(), migrate_users(), migrate_visitors(), SQLite to SQL Server Migration Workflow

### Community 7 - "System Configuration & Connection Management"
Cohesion: 0.47
Nodes (5): load_config(), _rebuild_connection_string(), save_config(), Client-Server Architecture & SQL Server Backend, Visitor Management System (SQL Server Edition)

### Community 8 - "Autofill Suggestions & Privacy Controls"
Cohesion: 0.33
Nodes (6): _ensure_hidden_table(), get_all_unique_employees(), get_all_unique_visitors(), get_employee_suggestions(), hide_employee_from_autofill(), hide_visitor_from_autofill()

### Community 9 - "Audit Logging & System Backup"
Cohesion: 0.33
Nodes (6): get_all_audit_logs_for_backup(), get_all_users_for_backup(), get_all_visitors_for_backup(), _get_system_context(), log_audit(), do_backup()

### Community 10 - "User Authentication & Credential Security"
Cohesion: 0.40
Nodes (5): change_user_password(), create_user(), hash_password(), setup_database(), update_user()

## Knowledge Gaps
- **10 isolated node(s):** `SQLite to SQL Server Migration Workflow`, `Operator User Guide (??????? ?????? ??? ???? ? ????)`, `Administrator & Supervisor Guide (??????? ??????)`, `PyInstaller Packaging & Windows Build Instructions`, `Main Application Background Banner` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ConnectionPool` connect `Database Connection Pooling & Concurrency` to `Database Schema & CRUD Operations`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **What connects `SQLite to SQL Server Migration Workflow`, `Operator User Guide (??????? ?????? ??? ???? ? ????)`, `Administrator & Supervisor Guide (??????? ??????)` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Application Core & Form Controller` be split into smaller, more focused modules?**
  _Cohesion score 0.0967741935483871 - nodes in this community are weakly interconnected._
- **Should `Custom UI Widgets & Autocomplete` be split into smaller, more focused modules?**
  _Cohesion score 0.14619883040935672 - nodes in this community are weakly interconnected._
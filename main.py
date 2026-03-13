import tkinter as tk
from tkinter import ttk, messagebox, font
import mysql.connector
from datetime import datetime
import threading


# ─────────────────────────────────────────────
#  THEME CONSTANTS
# ─────────────────────────────────────────────
BG        = "#0f1117"
SURFACE   = "#1a1d27"
CARD      = "#21253a"
ACCENT    = "#4f8ef7"
ACCENT2   = "#7c3aed"
SUCCESS   = "#22c55e"
DANGER    = "#ef4444"
WARNING   = "#f59e0b"
TEXT      = "#e8eaf0"
MUTED     = "#6b7280"
BORDER    = "#2d3148"
FONT_MAIN = "Courier New"


# ─────────────────────────────────────────────
#  DATABASE LAYER  (improved original logic)
# ─────────────────────────────────────────────
class Database:
    def __init__(self, host, user, password, database):
        self.config = dict(host=host, user=user, password=password, database=database)
        self.conn   = None
        self.cursor = None

    def connect(self):
        self.conn   = mysql.connector.connect(**self.config)
        self.conn.autocommit = False
        self.cursor = self.conn.cursor()

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    @property
    def connected(self):
        return self.conn is not None and self.conn.is_connected()

    # ── queries ──────────────────────────────
    def get_table_columns(self, table):
        self.cursor.execute(f"DESCRIBE `{table}`;")
        return self.cursor.fetchall()

    def get_employees(self):
        self.cursor.execute(
            "SELECT ssn, fname, minit, lname, bdate, address, sex, salary, super_ssn, dno FROM employee;"
        )
        return self.cursor.fetchall()

    def get_dependents_report(self):
        self.cursor.execute("""
            SELECT e.fname, e.lname, e.ssn,
                   d.dependent_name, d.relationship, d.sex, d.bdate
            FROM   employee e
            JOIN   dependent d ON e.ssn = d.essn
            ORDER  BY e.ssn, d.dependent_name;
        """)
        return self.cursor.fetchall()

    def insert_employee(self, fields: dict):
        cols = ", ".join(f"`{k}`" for k in fields)
        placeholders = ", ".join(["%s"] * len(fields))
        self.cursor.execute(
            f"INSERT INTO employee ({cols}) VALUES ({placeholders});",
            list(fields.values())
        )

    def insert_works_on(self, essn, pno, hours):
        self.cursor.execute(
            "INSERT INTO works_on (essn, pno, hours) VALUES (%s, %s, %s);",
            (essn, pno, hours)
        )

    def commit(self):   self.conn.commit()
    def rollback(self): self.conn.rollback()


# ─────────────────────────────────────────────
#  WIDGET HELPERS
# ─────────────────────────────────────────────
def styled_label(parent, text, size=11, bold=False, color=TEXT, **kw):
    weight = "bold" if bold else "normal"
    return tk.Label(
        parent, text=text, font=(FONT_MAIN, size, weight),
        fg=color, bg=kw.pop("bg", SURFACE), **kw
    )

def styled_button(parent, text, command, color=ACCENT, width=18, **kw):
    btn = tk.Button(
        parent, text=text, command=command,
        font=(FONT_MAIN, 10, "bold"),
        bg=color, fg="white", activebackground=color,
        relief="flat", bd=0, cursor="hand2",
        padx=14, pady=8, width=width, **kw
    )
    # hover effect
    darker = _darken(color)
    btn.bind("<Enter>", lambda e: btn.config(bg=darker))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn

def styled_entry(parent, width=30, show=None):
    e = tk.Entry(
        parent, font=(FONT_MAIN, 10),
        bg=CARD, fg=TEXT, insertbackground=TEXT,
        relief="flat", bd=0, width=width,
        highlightthickness=1, highlightbackground=BORDER,
        highlightcolor=ACCENT, show=show or ""
    )
    return e

def _darken(hex_color, factor=0.85):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return "#{:02x}{:02x}{:02x}".format(
        int(r*factor), int(g*factor), int(b*factor)
    )

def separator(parent, color=BORDER):
    return tk.Frame(parent, bg=color, height=1)


# ─────────────────────────────────────────────
#  CONNECTION PANEL
# ─────────────────────────────────────────────
class ConnectionPanel(tk.Frame):
    def __init__(self, master, on_connect):
        super().__init__(master, bg=BG)
        self.on_connect = on_connect
        self._build()

    def _build(self):
        # centre card
        card = tk.Frame(self, bg=SURFACE, padx=40, pady=36,
                        highlightthickness=1, highlightbackground=BORDER)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="  COMPANY DB", font=(FONT_MAIN, 22, "bold"),
                 fg=ACCENT, bg=SURFACE).pack(pady=(0, 4))
        tk.Label(card, text="MySQL Management Console", font=(FONT_MAIN, 10),
                 fg=MUTED, bg=SURFACE).pack(pady=(0, 24))

        separator(card).pack(fill="x", pady=(0, 20))

        fields = [
            ("Host",     "localhost"),
            ("User",     "root"),
            ("Password", ""),
            ("Database", "companydb"),
        ]
        self.entries = {}
        for label, default in fields:
            row = tk.Frame(card, bg=SURFACE)
            row.pack(fill="x", pady=5)
            tk.Label(row, text=f"{label:<12}", font=(FONT_MAIN, 10),
                     fg=MUTED, bg=SURFACE, anchor="w").pack(side="left")
            show = "*" if label == "Password" else None
            e = styled_entry(row, width=24, show=show)
            e.insert(0, default)
            e.pack(side="left", padx=(8, 0))
            self.entries[label.lower()] = e

        separator(card).pack(fill="x", pady=20)

        self.status_lbl = tk.Label(card, text="", font=(FONT_MAIN, 9),
                                   fg=DANGER, bg=SURFACE)
        self.status_lbl.pack(pady=(0, 10))

        styled_button(card, "CONNECT  →", self._attempt_connect,
                      color=ACCENT, width=28).pack()

    def _attempt_connect(self):
        cfg = {k: e.get() for k, e in self.entries.items()}
        self.status_lbl.config(text="Connecting…", fg=WARNING)
        self.update()
        try:
            db = Database(cfg["host"], cfg["user"], cfg["password"], cfg["database"])
            db.connect()
            self.on_connect(db)
        except mysql.connector.Error as ex:
            self.status_lbl.config(text=f"✗  {ex.msg}", fg=DANGER)


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class App(tk.Frame):
    def __init__(self, master, db: Database):
        super().__init__(master, bg=BG)
        self.db = db
        self.pack(fill="both", expand=True)
        self._build()
        self._load_employees()

    # ── layout ───────────────────────────────
    def _build(self):
        # ── sidebar ──
        sidebar = tk.Frame(self, bg=SURFACE, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="  COMPANY DB", font=(FONT_MAIN, 13, "bold"),
                 fg=ACCENT, bg=SURFACE).pack(pady=(28, 4))
        tk.Label(sidebar, text="Management Console", font=(FONT_MAIN, 8),
                 fg=MUTED, bg=SURFACE).pack(pady=(0, 24))

        separator(sidebar).pack(fill="x", padx=20, pady=(0, 16))

        nav_items = [
            ("👥  Employees",        self._show_employees),
            ("➕  Insert Employee",  self._show_insert),
            ("📋  Dependents Report",self._show_dependents),
        ]
        self.nav_btns = []
        for label, cmd in nav_items:
            btn = tk.Button(
                sidebar, text=label, command=cmd,
                font=(FONT_MAIN, 10), fg=TEXT, bg=SURFACE,
                activebackground=CARD, activeforeground=ACCENT,
                relief="flat", bd=0, cursor="hand2",
                anchor="w", padx=24, pady=10, width=22
            )
            btn.pack(fill="x")
            self.nav_btns.append(btn)

        # push disconnect to bottom
        tk.Frame(sidebar, bg=SURFACE).pack(fill="y", expand=True)
        separator(sidebar).pack(fill="x", padx=20, pady=12)
        styled_button(sidebar, "Disconnect", self._disconnect,
                      color=DANGER, width=18).pack(pady=(0, 20))

        # ── main area ──
        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)

        # status bar
        self.statusbar = tk.Label(
            self, text=f"  ● Connected  |  {self.db.config['database']}@{self.db.config['host']}",
            font=(FONT_MAIN, 8), fg=SUCCESS, bg=CARD, anchor="w", padx=10
        )
        self.statusbar.pack(side="bottom", fill="x", ipady=4)

        # show default view
        self._show_employees()

    def _clear_main(self):
        for w in self.main.winfo_children():
            w.destroy()

    def _highlight_nav(self, index):
        for i, btn in enumerate(self.nav_btns):
            btn.config(bg=CARD if i == index else SURFACE,
                       fg=ACCENT if i == index else TEXT)

    # ── EMPLOYEE LIST ─────────────────────────
    def _show_employees(self):
        self._highlight_nav(0)
        self._clear_main()
        frame = tk.Frame(self.main, bg=BG)
        frame.pack(fill="both", expand=True, padx=28, pady=24)

        hdr = tk.Frame(frame, bg=BG)
        hdr.pack(fill="x", pady=(0, 16))
        styled_label(hdr, "Employee Directory", size=16, bold=True, bg=BG).pack(side="left")
        styled_button(hdr, "↻  Refresh", self._load_employees, color=ACCENT2, width=14).pack(side="right")

        # table
        cols = ("SSN", "First Name", "MI", "Last Name", "Birth Date",
                "Sex", "Salary", "Dept#")
        tree_frame = tk.Frame(frame, bg=BORDER, pady=1, padx=1)
        tree_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Treeview",
                        background=CARD, foreground=TEXT,
                        fieldbackground=CARD, rowheight=28,
                        font=(FONT_MAIN, 9))
        style.configure("Custom.Treeview.Heading",
                        background=SURFACE, foreground=ACCENT,
                        font=(FONT_MAIN, 9, "bold"), relief="flat")
        style.map("Custom.Treeview", background=[("selected", ACCENT2)])

        self.emp_tree = ttk.Treeview(tree_frame, columns=cols,
                                     show="headings", style="Custom.Treeview")
        widths = [100, 100, 40, 100, 100, 50, 90, 60]
        for col, w in zip(cols, widths):
            self.emp_tree.heading(col, text=col)
            self.emp_tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(tree_frame, orient="vertical",
                               command=self.emp_tree.yview)
        self.emp_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.emp_tree.pack(fill="both", expand=True)

        self._populate_employee_tree()

    def _load_employees(self):
        if hasattr(self, "emp_tree"):
            self._populate_employee_tree()

    def _populate_employee_tree(self):
        self.emp_tree.delete(*self.emp_tree.get_children())
        try:
            rows = self.db.get_employees()
            for row in rows:
                # SSN, fname, minit, lname, bdate, address, sex, salary, super_ssn, dno
                display = (row[0], row[1], row[2] or "", row[3],
                           str(row[4]) if row[4] else "",
                           row[6] or "", f"${row[7]:,.2f}" if row[7] else "", row[9] or "")
                self.emp_tree.insert("", "end", values=display)
        except mysql.connector.Error as ex:
            messagebox.showerror("DB Error", str(ex))

    # ── INSERT EMPLOYEE ───────────────────────
    def _show_insert(self):
        self._highlight_nav(1)
        self._clear_main()

        canvas = tk.Canvas(self.main, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.main, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG)
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)

        inner.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        # scroll with mousewheel
        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        frame = tk.Frame(inner, bg=BG)
        frame.pack(fill="both", expand=True, padx=28, pady=24)

        styled_label(frame, "Insert New Employee", size=16, bold=True, bg=BG).pack(anchor="w", pady=(0, 20))

        # ── Employee fields card ──
        emp_card = tk.Frame(frame, bg=SURFACE, padx=24, pady=20,
                            highlightthickness=1, highlightbackground=BORDER)
        emp_card.pack(fill="x", pady=(0, 16))

        styled_label(emp_card, "EMPLOYEE DETAILS", size=9, color=ACCENT, bg=SURFACE).pack(anchor="w", pady=(0, 14))

        emp_fields = [
            ("SSN",           "ssn",       "text",   False),
            ("First Name",    "fname",     "text",   True),
            ("Middle Init",   "minit",     "text",   True),
            ("Last Name",     "lname",     "text",   True),
            ("Birth Date",    "bdate",     "date",   True),
            ("Address",       "address",   "text",   True),
            ("Sex (M/F)",     "sex",       "text",   True),
            ("Salary",        "salary",    "number", True),
            ("Supervisor SSN","super_ssn", "text",   True),
            ("Dept Number",   "dno",       "number", True),
        ]

        self.emp_entries = {}
        grid = tk.Frame(emp_card, bg=SURFACE)
        grid.pack(fill="x")

        for i, (label, key, dtype, nullable) in enumerate(emp_fields):
            row_frame = tk.Frame(grid, bg=SURFACE)
            row_frame.pack(fill="x", pady=4)

            lbl_txt = label + ("" if not nullable else "  (opt)")
            tk.Label(row_frame, text=f"{lbl_txt:<22}", font=(FONT_MAIN, 9),
                     fg=MUTED if nullable else TEXT, bg=SURFACE, anchor="w",
                     width=22).pack(side="left")

            if dtype == "date":
                e = styled_entry(row_frame, width=20)
                e.insert(0, "YYYY-MM-DD")
                e.bind("<FocusIn>", lambda ev, en=e: (en.delete(0, "end") if en.get() == "YYYY-MM-DD" else None))
            else:
                e = styled_entry(row_frame, width=20)

            e.pack(side="left", padx=(8, 0))
            self.emp_entries[key] = (e, dtype, nullable)

        # ── Works On card ──
        wo_card = tk.Frame(frame, bg=SURFACE, padx=24, pady=20,
                           highlightthickness=1, highlightbackground=BORDER)
        wo_card.pack(fill="x", pady=(0, 16))

        styled_label(wo_card, "PROJECT ASSIGNMENT  (works_on)", size=9, color=ACCENT, bg=SURFACE).pack(anchor="w", pady=(0, 14))

        wo_fields = [("Project #", "pno"), ("Hours", "hours")]
        self.wo_entries = {}
        for label, key in wo_fields:
            row_frame = tk.Frame(wo_card, bg=SURFACE)
            row_frame.pack(fill="x", pady=4)
            tk.Label(row_frame, text=f"{label:<22}", font=(FONT_MAIN, 9),
                     fg=TEXT, bg=SURFACE, anchor="w", width=22).pack(side="left")
            e = styled_entry(row_frame, width=20)
            e.pack(side="left", padx=(8, 0))
            self.wo_entries[key] = e

        # ── buttons ──
        btn_row = tk.Frame(frame, bg=BG)
        btn_row.pack(fill="x", pady=16)
        styled_button(btn_row, "✓  Submit & Commit", self._submit_employee,
                      color=SUCCESS, width=22).pack(side="left", padx=(0, 12))
        styled_button(btn_row, "✗  Cancel", self._show_employees,
                      color=DANGER, width=14).pack(side="left")

        self.insert_status = tk.Label(frame, text="", font=(FONT_MAIN, 9),
                                      fg=TEXT, bg=BG)
        self.insert_status.pack(anchor="w")

    def _submit_employee(self):
        fields = {}
        for key, (entry, dtype, nullable) in self.emp_entries.items():
            val = entry.get().strip()
            if val in ("", "YYYY-MM-DD"):
                if not nullable:
                    messagebox.showwarning("Validation", f"'{key}' is required.")
                    return
                fields[key] = None
            elif dtype == "date":
                try:
                    datetime.strptime(val, "%Y-%m-%d")
                    fields[key] = val
                except ValueError:
                    messagebox.showwarning("Validation", f"'{key}' must be YYYY-MM-DD.")
                    return
            elif dtype == "number":
                try:
                    fields[key] = float(val)
                except ValueError:
                    messagebox.showwarning("Validation", f"'{key}' must be numeric.")
                    return
            else:
                fields[key] = val

        pno   = self.wo_entries["pno"].get().strip()
        hours = self.wo_entries["hours"].get().strip()

        if not pno or not hours:
            messagebox.showwarning("Validation", "Project # and Hours are required.")
            return

        try:
            hours_f = float(hours)
        except ValueError:
            messagebox.showwarning("Validation", "Hours must be a number.")
            return

        try:
            self.db.insert_employee(fields)
            self.db.insert_works_on(fields["ssn"], pno, hours_f)

            if hours_f > 0:
                self.db.commit()
                msg = "✓  Employee inserted and COMMITTED."
                messagebox.showinfo("Success", msg)
                self._show_employees()
            else:
                self.db.rollback()
                messagebox.showwarning("Rolled Back",
                    "Hours ≤ 0 — transaction ROLLED BACK. No data was saved.")
        except mysql.connector.Error as ex:
            self.db.rollback()
            messagebox.showerror("DB Error", f"Transaction ROLLED BACK.\n\n{ex}")

    # ── DEPENDENTS REPORT ─────────────────────
    def _show_dependents(self):
        self._highlight_nav(2)
        self._clear_main()
        frame = tk.Frame(self.main, bg=BG)
        frame.pack(fill="both", expand=True, padx=28, pady=24)

        styled_label(frame, "Dependents Report", size=16, bold=True, bg=BG).pack(anchor="w", pady=(0, 16))

        cols = ("Employee", "SSN", "Dependent", "Relationship", "Sex", "Birth Date")
        tree_frame = tk.Frame(frame, bg=BORDER, pady=1, padx=1)
        tree_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", style="Custom.Treeview")
        widths = [160, 110, 160, 120, 50, 100]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        try:
            rows = self.db.get_dependents_report()
            last_emp = None
            for row in rows:
                fname, lname, ssn, dep_name, rel, sex, bdate = row
                full = f"{fname} {lname}"
                emp_display = full if full != last_emp else ""
                ssn_display = ssn if full != last_emp else ""
                last_emp = full
                tree.insert("", "end", values=(
                    emp_display, ssn_display, dep_name,
                    rel, sex or "", str(bdate) if bdate else ""
                ))
        except mysql.connector.Error as ex:
            messagebox.showerror("DB Error", str(ex))

    # ── DISCONNECT ────────────────────────────
    def _disconnect(self):
        if messagebox.askyesno("Disconnect", "Disconnect from the database?"):
            self.db.disconnect()
            # restart connection screen
            for w in self.master.winfo_children():
                w.destroy()
            show_connection_screen(self.master)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
def show_connection_screen(root):
    panel = ConnectionPanel(root, lambda db: launch_app(root, db))
    panel.pack(fill="both", expand=True)

def launch_app(root, db):
    for w in root.winfo_children():
        w.destroy()
    App(root, db)

def main():
    root = tk.Tk()
    root.title("Company DB — Management Console")
    root.geometry("1100x680")
    root.minsize(860, 560)
    root.configure(bg=BG)

    # app icon (coloured square fallback)
    try:
        icon = tk.PhotoImage(width=1, height=1)
        icon.put(ACCENT, to=(0, 0))
        root.iconphoto(True, icon)
    except Exception:
        pass

    show_connection_screen(root)
    root.mainloop()

if __name__ == "__main__":
    main()

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry, Calendar
import csv
from datetime import datetime
import os
from fpdf import FPDF
import io
import matplotlib
matplotlib.use("Agg")  # use non-interactive backend for PDF-safe rendering
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# -----------------------
# Final: per-user CSV isolation + UI features
# -----------------------

expenses = []
current_user = None   # holds the logged-in username

# --------------------- Core functions ---------------------

def add_expense():
    try:
        amount = float(amount_entry.get())
        category = category_var.get()
        date = date_entry.get_date().strftime("%m/%d/%y")
        note = note_entry.get()
        expenses.append([date, category, float(amount), note])
        update_table()
        save_to_csv()
        update_monthly_total()
        clear_fields()
    except ValueError:
        messagebox.showerror("Invalid Input", "Amount must be a number")

def edit_expense():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select an expense to edit.")
        return

    index = tree.index(selected[0])
    try:
        amount = float(amount_entry.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Amount must be a number.")
        return

    category = category_var.get()
    date = date_entry.get_date().strftime("%m/%d/%y")
    note = note_entry.get()

    expenses[index] = [date, category, float(amount), note]
    update_table()
    save_to_csv()
    update_monthly_total()
    clear_fields()

def populate_fields_for_edit(event=None, index=None):
    if index is None:
        selected = tree.selection()
        if not selected:
            return
        values = tree.item(selected[0])["values"]
    else:
        values = expenses[index]
    # values might have formatted amount string; handle both
    date_entry.set_date(datetime.strptime(values[0], "%m/%d/%y"))
    category_var.set(values[1])
    amount_entry.delete(0, tk.END)
    amount_entry.insert(0, str(values[2]))
    note_entry.delete(0, tk.END)
    note_entry.insert(0, values[3])

def clear_fields():
    amount_entry.delete(0, tk.END)
    note_entry.delete(0, tk.END)

def save_to_csv():
    """
    Save expenses to the current user's CSV file.
    Falls back to 'expenses.csv' if current_user is None (safety).
    """
    filename = f"expenses_{current_user}.csv" if current_user else "expenses.csv"
    try:
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Category", "Amount", "Note"])
            writer.writerows(expenses)
    except Exception as e:
        messagebox.showerror("File Error", f"Could not save CSV: {e}")

def load_from_csv():
    """
    Load expenses from the current user's CSV file.
    Clears the global expenses list before loading.
    """
    global expenses
    expenses = []  # clear previous data to avoid mixing users
    filename = f"expenses_{current_user}.csv" if current_user else "expenses.csv"
    try:
        with open(filename, newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 4:
                    try:
                        row[2] = float(row[2])
                    except:
                        row[2] = 0.0
                    expenses.append(row)
    except FileNotFoundError:
        # No file yet: that's fine — user has empty list
        pass
    except Exception as e:
        messagebox.showerror("File Error", f"Could not load CSV: {e}")

def update_table(filtered=None):
    # Clear tree first
    for row in tree.get_children():
        tree.delete(row)
    data = filtered if filtered else expenses
    for row in data:
        tree.insert("", tk.END, values=(row[0], row[1], f"{row[2]:.2f}", row[3], "✏️  🗑️"))

def filter_expenses():
    keyword = filter_entry.get().lower()
    filtered = [row for row in expenses if keyword in row[1].lower() or keyword in row[3].lower()]
    update_table(filtered)

def export_to_csv():
    data = [tree.item(row)["values"] for row in tree.get_children()]
    if not data:
        messagebox.showwarning("No Data", "No data to export.")
        return
    file = filedialog.asksaveasfilename(defaultextension=".csv")
    if file:
        try:
            with open(file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Category", "Amount", "Note"])
                writer.writerows([[r[0], r[1], r[2], r[3]] for r in data])
            messagebox.showinfo("Exported", f"Data exported to {file}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not export CSV: {e}")

def update_monthly_total():
    current_month = datetime.now().month
    current_year = datetime.now().year
    total = 0.0
    for row_id in tree.get_children():
        values = tree.item(row_id)["values"]
        try:
            date = datetime.strptime(values[0], "%m/%d/%y")
            if date.month == current_month and date.year == current_year:
                total += float(values[2])
        except:
            pass
    monthly_total_label.config(text=f"This Month's Total: ₹ {total:.2f}")

def close_app():
    save_to_csv()
    root.destroy()

# --------------------- New features ---------------------

def export_to_pdf():
    data = [tree.item(row)["values"] for row in tree.get_children()]
    if not data:
        messagebox.showwarning("No Data", "No data to include in PDF.")
        return
    file = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
    if not file:
        return
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Expense Report", ln=True, align="C")
    pdf.ln(4)
    pdf.set_font("Arial", size=10)
    # Table header
    pdf.cell(40, 8, "Date", 1, 0, "C")
    pdf.cell(40, 8, "Category", 1, 0, "C")
    pdf.cell(40, 8, "Amount", 1, 0, "C")
    pdf.cell(70, 8, "Note", 1, 1, "C")
    for r in data:
        pdf.cell(40, 8, str(r[0]), 1, 0, "C")
        pdf.cell(40, 8, str(r[1]), 1, 0, "C")
        pdf.cell(40, 8, str(r[2]), 1, 0, "R")
        note_text = str(r[3])[:38]
        pdf.cell(70, 8, note_text, 1, 1, "L")
    try:
        pdf.output(file)
        messagebox.showinfo("PDF Generated", f"PDF saved to {file}")
    except Exception as e:
        messagebox.showerror("PDF Error", f"Could not save PDF: {e}")

def show_calendar_view():
    cal_win = tk.Toplevel(root)
    cal_win.title("Monthly Calendar View")
    cal_win.geometry("400x400")
    cal = Calendar(cal_win, selectmode="day", date_pattern="mm/dd/yy")
    cal.pack(fill="both", expand=True, padx=10, pady=10)

    def on_date_select():
        sel = cal.get_date()
        filtered = [row for row in expenses if row[0] == sel]
        update_table(filtered)
        cal_win.destroy()

    btn_frame = tk.Frame(cal_win)
    btn_frame.pack(pady=8)
    tk.Button(btn_frame, text="Filter by Date", command=on_date_select, bg="#6C5CE7", fg="white").pack(side="left", padx=6)
    tk.Button(btn_frame, text="Close", command=cal_win.destroy, bg="#636E72", fg="white").pack(side="left", padx=6)

def show_analytics():
    if not expenses:
        messagebox.showwarning("No Data", "No expenses to analyze.")
        return

    from collections import defaultdict
    cat_sum = defaultdict(float)
    month_sum = defaultdict(float)
    for r in expenses:
        try:
            amt = float(r[2])
        except:
            amt = 0.0
        cat_sum[r[1]] += amt
        dt = datetime.strptime(r[0], "%m/%d/%y")
        month_label = dt.strftime("%b %Y")
        month_sum[month_label] += amt

    months_sorted = sorted(month_sum.items(), key=lambda x: datetime.strptime(x[0], "%b %Y"))
    m_labels = [m for m, _ in months_sorted]
    m_values = [v for _, v in months_sorted]

    analytic_win = tk.Toplevel(root)
    analytic_win.title("Analytics")
    analytic_win.geometry("900x450")

    fig1 = plt.Figure(figsize=(4.5, 4), dpi=80)
    ax1 = fig1.add_subplot(111)
    cats = list(cat_sum.keys())
    vals = [cat_sum[c] for c in cats]
    if sum(vals) == 0:
        vals = [1 for _ in vals]
    ax1.pie(vals, labels=cats, autopct='%1.1f%%', startangle=140)
    ax1.set_title("Category Breakdown")
    canvas1 = FigureCanvasTkAgg(fig1, analytic_win)
    canvas1.get_tk_widget().pack(side="left", fill="both", expand=True, padx=10, pady=10)

    fig2 = plt.Figure(figsize=(4.5, 4), dpi=80)
    ax2 = fig2.add_subplot(111)
    ax2.bar(m_labels, m_values)
    ax2.set_title("Monthly Totals")
    ax2.set_ylabel("Amount (₹)")
    ax2.tick_params(axis='x', rotation=30)
    canvas2 = FigureCanvasTkAgg(fig2, analytic_win)
    canvas2.get_tk_widget().pack(side="left", fill="both", expand=True, padx=10, pady=10)

# --------------------- Table action handling ---------------------

def on_tree_click(event):
    region = tree.identify("region", event.x, event.y)
    if region != "cell":
        return
    col = tree.identify_column(event.x)
    rowid = tree.identify_row(event.y)
    if not rowid:
        return
    # Actions column is '#5'
    if col == "#5":
        x_offset = tree.column("#1", option="width") + tree.column("#2", option="width") + tree.column("#3", option="width") + tree.column("#4", option="width")
        actions_x = event.x - x_offset
        actions_width = tree.column("#5", option="width")
        if actions_x <= actions_width / 2:
            index = tree.index(rowid)
            populate_fields_for_edit(index=index)
        else:
            idx = tree.index(rowid)
            confirm = messagebox.askyesno("Delete", "Delete selected expense?")
            if confirm:
                try:
                    expenses.pop(idx)
                except:
                    pass
                update_table()
                save_to_csv()
                update_monthly_total()

# --------------------------- UI BUILD (dark theme + gradients) ---------------------------

def make_gradient_button(parent, text, command, width=120, height=34, start_color="#6C5CE7", end_color="#4D77FF"):
    canv = tk.Canvas(parent, width=width, height=height, highlightthickness=0, bd=0, bg=dark_bg)
    steps = 20
    try:
        def hex_to_rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        sc = hex_to_rgb(start_color)
        ec = hex_to_rgb(end_color)
        for i in range(steps):
            r = int(sc[0] + (ec[0]-sc[0]) * i / steps)
            g = int(sc[1] + (ec[1]-sc[1]) * i / steps)
            b = int(sc[2] + (ec[2]-sc[2]) * i / steps)
            color = f"#{r:02x}{g:02x}{b:02x}"
            x0 = int(i * (width / steps))
            x1 = int((i+1) * (width / steps))
            canv.create_rectangle(x0, 0, x1, height, outline=color, fill=color)
        canv.create_text(width//2, height//2, text=text, fill="white", font=("Segoe UI", 10, "bold"))
    except Exception:
        canv.create_rectangle(0,0,width,height, fill=start_color, outline=start_color)
        canv.create_text(width//2, height//2, text=text, fill="white", font=("Segoe UI", 10, "bold"))
    canv.bind("<Button-1>", lambda e: command())
    return canv

def open_main_app(username):
    global amount_entry, category_var, category_dropdown, date_entry, note_entry
    global tree, monthly_total_label, filter_entry, root, dark_bg, current_user

    # Set current user immediately
    current_user = username

    root = tk.Tk()
    root.title(f"Expense Tracker - {username}")
    root.geometry("1000x600")
    root.minsize(900, 520)

    # Dark color palette
    dark_bg = "#121214"
    panel_bg = "#1E1F29"
    accent = "#6C5CE7"
    text_fg = "#ECEFF4"
    subtle = "#2B2E3A"

    root.configure(bg=dark_bg)

    # Left sidebar
    sidebar = tk.Frame(root, bg=panel_bg, width=220)
    sidebar.pack(side="left", fill="y")

    logo = tk.Label(sidebar, text="Daily Based Expense", bg=panel_bg, fg=accent, font=("Segoe UI", 16, "bold"))
    logo.pack(pady=(18, 6))

    subtitle = tk.Label(sidebar, text="Expense Dashboard", bg=panel_bg, fg=text_fg, font=("Segoe UI", 10))
    subtitle.pack(pady=(0, 12))

    btn_frame = tk.Frame(sidebar, bg=panel_bg)
    btn_frame.pack(pady=6)

    make_gradient_button(btn_frame, "Add Expense", lambda: add_expense()).pack(pady=6)
    make_gradient_button(btn_frame, "Update Expense", lambda: edit_expense()).pack(pady=6)
    make_gradient_button(btn_frame, "Export CSV", lambda: export_to_csv()).pack(pady=6)
    make_gradient_button(btn_frame, "Export PDF", lambda: export_to_pdf(), start_color="#FF7F50", end_color="#FF6B6B").pack(pady=6)

    small_frame = tk.Frame(sidebar, bg=panel_bg)
    small_frame.pack(side="bottom", pady=18)
    btn_cal = tk.Button(small_frame, text="Calendar View", command=show_calendar_view, bg="#2D3436", fg=text_fg, relief="flat")
    btn_cal.pack(fill="x", padx=10, pady=4)
    btn_analytic = tk.Button(small_frame, text="Analytics", command=show_analytics, bg="#2D3436", fg=text_fg, relief="flat")
    btn_analytic.pack(fill="x", padx=10, pady=4)
    btn_exit = tk.Button(small_frame, text="Exit", command=close_app, bg="#b33939", fg="white", relief="flat")
    btn_exit.pack(fill="x", padx=10, pady=6)

    # Main content area
    main = tk.Frame(root, bg=dark_bg, padx=16, pady=12)
    main.pack(side="left", fill="both", expand=True)

    header = tk.Frame(main, bg=dark_bg)
    header.pack(fill="x")
    header_lbl = tk.Label(header, text=f"Welcome, {username}", bg=dark_bg, fg=text_fg, font=("Segoe UI", 14, "bold"))
    header_lbl.pack(side="left")
    month_label = tk.Label(header, text=datetime.now().strftime("%B %Y"), bg=dark_bg, fg="#A9B0C0", font=("Segoe UI", 10))
    month_label.pack(side="right")

    form_card = tk.Frame(main, bg=subtle, bd=0, relief="flat", padx=12, pady=12)
    form_card.pack(fill="x", pady=10)

    lbl_amount = tk.Label(form_card, text="Amount ₹", bg=subtle, fg=text_fg)
    lbl_amount.grid(row=0, column=0, sticky="w", padx=4, pady=6)
    amount_entry = tk.Entry(form_card, width=12, bg="#2A2B33", fg=text_fg, insertbackground=text_fg, relief="flat")
    amount_entry.grid(row=0, column=1, padx=6)

    lbl_cat = tk.Label(form_card, text="Category", bg=subtle, fg=text_fg)
    lbl_cat.grid(row=0, column=2, sticky="w", padx=4)
    category_var = tk.StringVar()
    category_dropdown = ttk.Combobox(form_card, textvariable=category_var,
                                     values=["Food", "Transport", " card-Bills", "Shopping","electricity-bills", "Other"],
                                     state="readonly", width=18)
    category_dropdown.set("Food")
    category_dropdown.grid(row=0, column=3, padx=6)

    lbl_date = tk.Label(form_card, text="Date", bg=subtle, fg=text_fg)
    lbl_date.grid(row=0, column=4, sticky="w", padx=4)
    date_entry = DateEntry(form_card, width=12, date_pattern="mm/dd/yy")
    date_entry.grid(row=0, column=5, padx=6)

    lbl_note = tk.Label(form_card, text="Note", bg=subtle, fg=text_fg)
    lbl_note.grid(row=1, column=0, sticky="nw", padx=4, pady=8)
    note_entry = tk.Entry(form_card, width=80, bg="#2A2B33", fg=text_fg, insertbackground=text_fg, relief="flat")
    note_entry.grid(row=1, column=1, columnspan=5, pady=6, padx=6, sticky="w")

    action_frame = tk.Frame(form_card, bg=subtle)
    action_frame.grid(row=2, column=0, columnspan=6, pady=(6,0))

    make_gradient_button(action_frame, "Add Expense", add_expense, start_color="#2ECC71", end_color="#2AB07F").pack(side="left", padx=6)
    make_gradient_button(action_frame, "Update Selected", edit_expense, start_color="#FF9F43", end_color="#FF6B6B").pack(side="left", padx=6)
    make_gradient_button(action_frame, "Export CSV", export_to_csv, start_color="#4D77FF", end_color="#6C5CE7").pack(side="left", padx=6)
    make_gradient_button(action_frame, "PDF Report", export_to_pdf, start_color="#D63031", end_color="#E66767").pack(side="left", padx=6)

    table_card = tk.Frame(main, bg=subtle, pady=8, padx=8)
    table_card.pack(fill="both", expand=True, pady=8)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview",
                    background="#1B1C22",
                    foreground=text_fg,
                    fieldbackground="#1B1C22",
                    rowheight=28,
                    borderwidth=0,
                    font=("Segoe UI", 10))
    style.map("Treeview", background=[("selected", "#3B3F6B")])

    columns = ("Date", "Category", "Amount", "Note", "Actions")
    tree = ttk.Treeview(table_card, columns=columns, show="headings")
    tree.pack(fill="both", expand=True, side="left")
    vsb = ttk.Scrollbar(table_card, orient="vertical", command=tree.yview)
    vsb.pack(side="right", fill="y")
    tree.configure(yscrollcommand=vsb.set)

    tree.heading("Date", text="Date")
    tree.heading("Category", text="Category")
    tree.heading("Amount", text="Amount")
    tree.heading("Note", text="Note")
    tree.heading("Actions", text="Actions")
    tree.column("Date", width=110, anchor="center")
    tree.column("Category", width=120, anchor="center")
    tree.column("Amount", width=90, anchor="center")
    tree.column("Note", width=420, anchor="w")
    tree.column("Actions", width=100, anchor="center")

    tree.bind("<ButtonRelease-1>", on_tree_click)
    tree.bind("<Double-1>", lambda e: populate_fields_for_edit(e))

    bottom_bar = tk.Frame(main, bg=dark_bg)
    bottom_bar.pack(fill="x", pady=(6,0))

    monthly_total_label = tk.Label(bottom_bar, text="This Month's Total: ₹ 0.00", bg=dark_bg, fg=text_fg, font=("Segoe UI", 11, "bold"))
    monthly_total_label.pack(side="left", padx=8)

    search_frame = tk.Frame(bottom_bar, bg=dark_bg)
    search_frame.pack(side="right", padx=8)
    tk.Label(search_frame, text="Search:", bg=dark_bg, fg="#A9B0C0").pack(side="left")
    filter_entry = tk.Entry(search_frame, width=18, bg="#2A2B33", fg=text_fg, insertbackground=text_fg, relief="flat")
    filter_entry.pack(side="left", padx=6)
    tk.Button(search_frame, text="Filter", command=filter_expenses, bg="#2D3436", fg=text_fg, relief="flat").pack(side="left", padx=4)
    tk.Button(search_frame, text="Clear Filter", command=lambda: (filter_entry.delete(0, tk.END), update_table(), update_monthly_total()), bg="#2D3436", fg=text_fg, relief="flat").pack(side="left", padx=4)

    # Load and populate for this user (ensure state is fresh)
    load_from_csv()
    update_table()
    update_monthly_total()

    root.mainloop()

# --------------------------- LOGIN SCREEN --------------------------- #

def login_screen():
    def login():
        username = user_entry.get().strip()
        password = pass_entry.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        if not os.path.exists("users.txt"):
            with open("users.txt", "w") as _:
                pass

        with open("users.txt", "r") as f:
            users = f.readlines()

        for u in users:
            parts = u.strip().split(":")
            if len(parts) < 2:
                continue
            stored_user, stored_pass = parts[0], parts[1]
            if stored_user == username and stored_pass == password:
                messagebox.showinfo("Success", f"Welcome back, {username}!")
                login_win.destroy()
                open_main_app(username)
                return

        messagebox.showerror("Login Failed", "Incorrect username or password.")

    def register():
        username = user_entry.get().strip()
        password = pass_entry.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        if not os.path.exists("users.txt"):
            with open("users.txt", "w") as _:
                pass

        with open("users.txt", "r") as f:
            users = [line.strip().split(":")[0] for line in f.readlines() if ":" in line]

        if username in users:
            messagebox.showerror("Error", "Username already exists.")
            return

        with open("users.txt", "a") as f:
            f.write(f"{username}:{password}\n")

        # Auto-create user's personal CSV file
        try:
            filename = f"expenses_{username}.csv"
            if not os.path.exists(filename):
                with open(filename, "w", newline="") as f_csv:
                    writer = csv.writer(f_csv)
                    writer.writerow(["Date", "Category", "Amount", "Note"])
        except Exception as e:
            messagebox.showwarning("Warning", f"User created but couldn't create CSV file: {e}")

        messagebox.showinfo("Registered", "Registration successful! You can now log in.")

    login_win = tk.Tk()
    login_win.title("Daily Expense Tracker")
    login_win.geometry("360x300")
    login_win.configure(bg="#121214")
    login_win.resizable(False, False)

    tk.Label(login_win, text="Login / Register",
             font=("Segoe UI", 14, "bold"),
             bg="#121214", fg="#ECEFF4").pack(pady=15)

    tk.Label(login_win, text="Username:", bg="#121214", fg="#A9B0C0").pack()
    user_entry = tk.Entry(login_win, width=30, bg="#2A2B33", fg="#ECEFF4", insertbackground="#ECEFF4", relief="flat")
    user_entry.pack()

    tk.Label(login_win, text="Password:", bg="#121214", fg="#A9B0C0").pack(pady=6)
    pass_entry = tk.Entry(login_win, show="*", width=30, bg="#2A2B33", fg="#ECEFF4", insertbackground="#ECEFF4", relief="flat")
    pass_entry.pack()

    button_frame = tk.Frame(login_win, bg="#121214")
    button_frame.pack(pady=18)

    tk.Button(button_frame, text="Login", command=login, bg="#6C5CE7", fg="white", width=12, relief="flat").pack(side="left", padx=8)
    tk.Button(button_frame, text="Register", command=register, bg="#2ECC71", fg="white", width=12, relief="flat").pack(side="left", padx=8)

    login_win.mainloop()

# --------------------------- START APP --------------------------- #

if __name__ == "__main__":
    if not os.path.exists("users.txt"):
        with open("users.txt", "w") as f:
            pass
    login_screen()

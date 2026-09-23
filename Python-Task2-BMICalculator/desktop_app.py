"""
BMI Insight - desktop application.

A Tkinter GUI over the same calculation, validation and database code
used by the Flask web app. Built as one file because the app is small
enough that splitting the UI across modules would just add navigation
overhead without any real benefit.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import COLORS, BMI_DISCLAIMER
from bmi_calculator import calculate_bmi, categorize_bmi, category_position
from validators import validate_weight, validate_height, validate_name
from database import (
    init_db, add_user, get_users, add_record, get_records,
    delete_record, get_stats, DatabaseError,
)

APP_NAME = "BMI Insight"
APP_SUBTITLE = "Personal Health & Fitness Analytics"


class BMIInsightApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("980x680")
        self.minsize(820, 560)

        self.theme = "light"
        self.colors = COLORS[self.theme]
        self.current_user_id = None
        self.current_user_name = None

        try:
            init_db()
        except DatabaseError as exc:
            messagebox.showerror("Database error", str(exc))

        self.style = ttk.Style(self)
        self._build_layout()
        self._apply_theme()
        self._refresh_user_list()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self):
        self.header = tk.Frame(self, height=78)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        title_box = tk.Frame(self.header)
        title_box.pack(side="left", padx=24, pady=10)
        self.title_label = tk.Label(
            title_box, text=APP_NAME, font=("Segoe UI", 18, "bold"), anchor="w"
        )
        self.title_label.pack(anchor="w")
        self.subtitle_label = tk.Label(
            title_box, text=APP_SUBTITLE, font=("Segoe UI", 10), anchor="w"
        )
        self.subtitle_label.pack(anchor="w")

        self.theme_button = tk.Button(
            self.header, text="Dark mode", relief="flat",
            command=self._toggle_theme, cursor="hand2", padx=12, pady=6
        )
        self.theme_button.pack(side="right", padx=24, pady=20)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.dashboard_tab = tk.Frame(self.notebook)
        self.history_tab = tk.Frame(self.notebook)
        self.analytics_tab = tk.Frame(self.notebook)

        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.history_tab, text="History")
        self.notebook.add(self.analytics_tab, text="Analytics")

        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self._on_tab_change())

        self._build_dashboard_tab()
        self._build_history_tab()
        self._build_analytics_tab()

    def _build_dashboard_tab(self):
        tab = self.dashboard_tab

        user_row = tk.Frame(tab)
        user_row.pack(fill="x", padx=20, pady=(20, 10))

        tk.Label(user_row, text="User", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.user_combo = ttk.Combobox(user_row, state="readonly", width=24)
        self.user_combo.pack(side="left", padx=(10, 10))
        self.user_combo.bind("<<ComboboxSelected>>", lambda e: self._on_user_selected())

        tk.Button(
            user_row, text="+ Add user", relief="flat", cursor="hand2",
            command=self._open_add_user_dialog, padx=10, pady=4
        ).pack(side="left")

        self.updated_label = tk.Label(user_row, text="", font=("Segoe UI", 9))
        self.updated_label.pack(side="right")

        body = tk.Frame(tab)
        body.pack(fill="both", expand=True, padx=20, pady=10)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        # Left: input card
        self.input_card = tk.Frame(body, bd=0, highlightthickness=1)
        self.input_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        form = tk.Frame(self.input_card)
        form.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(form, text="Weight (kg)", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        self.weight_entry = tk.Entry(form, font=("Segoe UI", 12), relief="flat")
        self.weight_entry.grid(row=1, column=0, sticky="ew", ipady=6, pady=(0, 16))

        tk.Label(form, text="Height (m)", font=("Segoe UI", 10)).grid(
            row=2, column=0, sticky="w", pady=(0, 4)
        )
        self.height_entry = tk.Entry(form, font=("Segoe UI", 12), relief="flat")
        self.height_entry.grid(row=3, column=0, sticky="ew", ipady=6, pady=(0, 16))

        form.columnconfigure(0, weight=1)

        self.error_label = tk.Label(
            form, text="", font=("Segoe UI", 9), wraplength=280, justify="left"
        )
        self.error_label.grid(row=4, column=0, sticky="w", pady=(0, 10))

        button_row = tk.Frame(form)
        button_row.grid(row=5, column=0, sticky="ew")

        self.calc_button = tk.Button(
            button_row, text="Calculate BMI", relief="flat", cursor="hand2",
            font=("Segoe UI", 10, "bold"), padx=16, pady=8,
            command=self._on_calculate
        )
        self.calc_button.pack(side="left")

        tk.Button(
            button_row, text="Reset", relief="flat", cursor="hand2",
            padx=16, pady=8, command=self._on_reset
        ).pack(side="left", padx=(10, 0))

        self.disclaimer_label = tk.Label(
            form, text=BMI_DISCLAIMER, font=("Segoe UI", 8), wraplength=280,
            justify="left"
        )
        self.disclaimer_label.grid(row=6, column=0, sticky="w", pady=(20, 0))

        # Right: result card
        self.result_card = tk.Frame(body, bd=0, highlightthickness=1)
        self.result_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        result_inner = tk.Frame(self.result_card)
        result_inner.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(result_inner, text="Your result", font=("Segoe UI", 10, "bold")).pack(
            anchor="w"
        )
        self.bmi_value_label = tk.Label(
            result_inner, text="--", font=("Segoe UI", 42, "bold")
        )
        self.bmi_value_label.pack(anchor="w", pady=(6, 0))

        self.category_badge = tk.Label(
            result_inner, text="Enter your details", font=("Segoe UI", 11, "bold"),
            padx=12, pady=5
        )
        self.category_badge.pack(anchor="w", pady=(4, 20))

        tk.Label(result_inner, text="BMI scale", font=("Segoe UI", 9, "bold")).pack(
            anchor="w"
        )
        self.scale_canvas = tk.Canvas(result_inner, height=28, highlightthickness=0)
        self.scale_canvas.pack(fill="x", pady=(6, 4))
        self.scale_canvas.bind("<Configure>", lambda e: self._draw_scale())

        legend = tk.Frame(result_inner)
        legend.pack(fill="x")
        for label in ("Underweight", "Normal", "Overweight", "Obese"):
            tk.Label(legend, text=label, font=("Segoe UI", 7)).pack(
                side="left", expand=True
            )

    def _build_history_tab(self):
        tab = self.history_tab

        toolbar = tk.Frame(tab)
        toolbar.pack(fill="x", padx=20, pady=(20, 10))

        tk.Button(
            toolbar, text="Refresh", relief="flat", cursor="hand2", padx=12, pady=5,
            command=self._refresh_history
        ).pack(side="left")

        tk.Button(
            toolbar, text="Delete selected", relief="flat", cursor="hand2",
            padx=12, pady=5, command=self._delete_selected_record
        ).pack(side="left", padx=(10, 0))

        columns = ("date", "weight", "height", "bmi", "category")
        self.history_tree = ttk.Treeview(
            tab, columns=columns, show="headings", height=16
        )
        headings = {
            "date": "Date", "weight": "Weight (kg)", "height": "Height (m)",
            "bmi": "BMI", "category": "Category",
        }
        for col in columns:
            self.history_tree.heading(col, text=headings[col])
            self.history_tree.column(col, anchor="center", width=140)

        self.history_tree.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.history_empty_label = tk.Label(
            tab, text="No records yet - calculate a BMI to start your history.",
            font=("Segoe UI", 10)
        )

    def _build_analytics_tab(self):
        tab = self.analytics_tab

        stats_row = tk.Frame(tab)
        stats_row.pack(fill="x", padx=20, pady=20)

        self.stat_labels = {}
        self.stat_cards = []
        for key, label in [
            ("latest", "Latest BMI"), ("previous", "Previous BMI"),
            ("highest", "Highest BMI"), ("lowest", "Lowest BMI"),
            ("count", "Records"),
        ]:
            card = tk.Frame(stats_row, bd=0, highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=6)
            tk.Label(card, text=label, font=("Segoe UI", 9)).pack(
                anchor="w", padx=14, pady=(12, 0)
            )
            value_label = tk.Label(card, text="--", font=("Segoe UI", 18, "bold"))
            value_label.pack(anchor="w", padx=14, pady=(0, 12))
            self.stat_labels[key] = value_label
            self.stat_cards.append(card)

        chart_area = tk.Frame(tab)
        chart_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.bmi_axis = self.figure.add_subplot(121)
        self.weight_axis = self.figure.add_subplot(122)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_area)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Theming
    # ------------------------------------------------------------------
    def _toggle_theme(self):
        self.theme = "dark" if self.theme == "light" else "light"
        self.colors = COLORS[self.theme]
        self._apply_theme()
        self._draw_scale()
        self._draw_charts()

    def _apply_theme(self):
        c = self.colors
        self.configure(bg=c["bg"])
        self.header.configure(bg=c["surface"])
        self.title_label.configure(bg=c["surface"], fg=c["text"])
        self.subtitle_label.configure(bg=c["surface"], fg=c["muted"])
        self.theme_button.configure(
            bg=c["surface"], fg=c["accent"], activebackground=c["bg"],
            text="Dark mode" if self.theme == "light" else "Light mode",
        )
        self.dashboard_tab.configure(bg=c["bg"])
        self.history_tab.configure(bg=c["bg"])
        self.analytics_tab.configure(bg=c["bg"])

        for card in (self.input_card, self.result_card):
            card.configure(bg=c["surface"], highlightbackground=c["border"],
                            highlightcolor=c["border"])
            for child in card.winfo_children():
                self._recolor_recursive(child, c)

        self.calc_button.configure(bg=c["accent"], fg="white",
                                    activebackground=c["accent_dark"])
        self.error_label.configure(bg=c["surface"], fg=c["obese"])
        self.disclaimer_label.configure(bg=c["surface"], fg=c["muted"])
        self._style_category_badge()
        self.updated_label.configure(bg=c["bg"], fg=c["muted"])

        self.history_empty_label.configure(bg=c["bg"], fg=c["muted"])

        for card in getattr(self, "stat_cards", []):
            card.configure(bg=c["surface"], highlightbackground=c["border"])
            for child in card.winfo_children():
                child.configure(bg=c["surface"], fg=c["text"])

        style = self.style
        style.theme_use("clam")
        style.configure("TNotebook", background=c["bg"], borderwidth=0)
        style.configure(
            "TNotebook.Tab", background=c["surface"], foreground=c["text"],
            padding=(16, 8), font=("Segoe UI", 10)
        )
        style.map("TNotebook.Tab", background=[("selected", c["accent"])],
                   foreground=[("selected", "white")])
        style.configure("Treeview", background=c["surface"], fieldbackground=c["surface"],
                         foreground=c["text"], rowheight=26)
        style.configure("Treeview.Heading", background=c["bg"], foreground=c["text"],
                         font=("Segoe UI", 9, "bold"))
        style.configure("TCombobox", fieldbackground=c["surface"], background=c["surface"])

        # Frames with no explicit colours yet (toolbars etc.)
        for frame in self.winfo_children():
            self._recolor_bare_frames(frame, c)

    def _recolor_bare_frames(self, widget, c):
        """Plain container frames (toolbars, rows) just need the page
        background - cards are handled separately and skipped here so
        their own (different) colouring doesn't get overwritten."""
        skip = (self.input_card, self.result_card, self.header) + tuple(
            getattr(self, "stat_cards", [])
        )
        if widget in skip:
            return
        if isinstance(widget, tk.Frame):
            try:
                widget.configure(bg=c["bg"])
            except tk.TclError:
                pass
        for child in widget.winfo_children():
            self._recolor_bare_frames(child, c)

    def _recolor_recursive(self, widget, c):
        try:
            if isinstance(widget, (tk.Frame,)):
                widget.configure(bg=c["surface"])
            elif isinstance(widget, tk.Label) and widget not in (
                self.category_badge,
            ):
                widget.configure(bg=c["surface"], fg=c["text"])
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=c["bg"], fg=c["text"], insertbackground=c["text"],
                                  highlightthickness=1, highlightbackground=c["border"])
            elif isinstance(widget, tk.Button):
                widget.configure(bg=c["surface"], fg=c["text"], activebackground=c["bg"])
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._recolor_recursive(child, c)

    def _style_category_badge(self):
        c = self.colors
        category = self.category_badge.cget("text")
        color_key = {
            "Underweight": "underweight", "Normal": "normal",
            "Overweight": "overweight", "Obese": "obese",
        }.get(category)
        bg = c[color_key] if color_key else c["border"]
        fg = "white" if color_key else c["muted"]
        self.category_badge.configure(bg=bg, fg=fg)
        self.bmi_value_label.configure(bg=c["surface"], fg=c["text"])

    # ------------------------------------------------------------------
    # User management
    # ------------------------------------------------------------------
    def _refresh_user_list(self):
        try:
            users = get_users()
        except DatabaseError as exc:
            messagebox.showerror("Database error", str(exc))
            users = []

        self._users = {row["name"]: row["id"] for row in users}
        self.user_combo["values"] = list(self._users.keys())

        if self._users:
            if self.current_user_name not in self._users:
                first_name = list(self._users.keys())[0]
                self.user_combo.set(first_name)
                self.current_user_name = first_name
                self.current_user_id = self._users[first_name]
            self._refresh_history()
            self._refresh_analytics()

    def _on_user_selected(self):
        name = self.user_combo.get()
        self.current_user_name = name
        self.current_user_id = self._users.get(name)
        self._refresh_history()
        self._refresh_analytics()

    def _open_add_user_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add user")
        dialog.geometry("300x140")
        dialog.configure(bg=self.colors["surface"])
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="Name", bg=self.colors["surface"],
                 fg=self.colors["text"]).pack(anchor="w", padx=20, pady=(20, 4))
        name_entry = tk.Entry(dialog, font=("Segoe UI", 11))
        name_entry.pack(fill="x", padx=20)
        name_entry.focus_set()

        def submit():
            ok, result = validate_name(name_entry.get())
            if not ok:
                messagebox.showerror("Invalid name", result, parent=dialog)
                return
            try:
                add_user(result)
            except DatabaseError as exc:
                messagebox.showerror("Database error", str(exc), parent=dialog)
                return
            dialog.destroy()
            self.current_user_name = result
            self._refresh_user_list()
            self.user_combo.set(result)
            self.current_user_id = self._users.get(result)
            self._refresh_history()
            self._refresh_analytics()

        tk.Button(dialog, text="Add", command=submit, relief="flat",
                  bg=self.colors["accent"], fg="white", padx=16, pady=6).pack(
            pady=16
        )
        dialog.bind("<Return>", lambda e: submit())

    # ------------------------------------------------------------------
    # Dashboard actions
    # ------------------------------------------------------------------
    def _on_calculate(self):
        self.error_label.configure(text="")

        if not self.current_user_id:
            self.error_label.configure(text="Add or select a user first")
            return

        weight_ok, weight_result = validate_weight(self.weight_entry.get())
        if not weight_ok:
            self.error_label.configure(text=weight_result)
            return

        height_ok, height_result = validate_height(self.height_entry.get())
        if not height_ok:
            self.error_label.configure(text=height_result)
            return

        bmi = calculate_bmi(weight_result, height_result)
        category = categorize_bmi(bmi)

        self.bmi_value_label.configure(text=f"{bmi:.2f}")
        self.category_badge.configure(text=category)
        self._style_category_badge()
        self._draw_scale(bmi)
        self.updated_label.configure(
            text=f"Last updated: {datetime.now().strftime('%d %b %Y, %H:%M')}"
        )

        try:
            add_record(self.current_user_id, weight_result, height_result, bmi, category)
        except DatabaseError as exc:
            messagebox.showerror("Database error", str(exc))
            return

        self._refresh_history()
        self._refresh_analytics()

    def _on_reset(self):
        self.weight_entry.delete(0, tk.END)
        self.height_entry.delete(0, tk.END)
        self.error_label.configure(text="")
        self.bmi_value_label.configure(text="--")
        self.category_badge.configure(text="Enter your details")
        self._style_category_badge()
        self._draw_scale()

    def _draw_scale(self, bmi=None):
        self.scale_canvas.delete("all")
        width = self.scale_canvas.winfo_width() or 280
        height = 28
        c = self.colors

        segments = [
            ("underweight", 0.0, 0.28),
            ("normal", 0.28, 0.52),
            ("overweight", 0.52, 0.72),
            ("obese", 0.72, 1.0),
        ]
        for key, start, end in segments:
            self.scale_canvas.create_rectangle(
                start * width, 4, end * width, height - 4,
                fill=c[key], outline=""
            )

        if bmi is not None:
            pos = category_position(bmi) * width
            self.scale_canvas.create_polygon(
                pos - 6, 0, pos + 6, 0, pos, 10, fill=c["text"], outline=""
            )

    # ------------------------------------------------------------------
    # History tab
    # ------------------------------------------------------------------
    def _refresh_history(self):
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)

        if not self.current_user_id:
            return

        try:
            records = get_records(self.current_user_id)
        except DatabaseError as exc:
            messagebox.showerror("Database error", str(exc))
            return

        if not records:
            self.history_tree.pack_forget()
            self.history_empty_label.pack(pady=40)
            return

        self.history_empty_label.pack_forget()
        self.history_tree.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        for row in records:
            self.history_tree.insert(
                "", "end", iid=str(row["id"]),
                values=(row["created_at"], row["weight"], row["height"],
                        f'{row["bmi"]:.2f}', row["category"])
            )

    def _delete_selected_record(self):
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showinfo("No selection", "Select a record to delete first")
            return

        if not messagebox.askyesno(
            "Delete record", "Delete the selected BMI record? This can't be undone."
        ):
            return

        try:
            delete_record(int(selection[0]))
        except DatabaseError as exc:
            messagebox.showerror("Database error", str(exc))
            return

        self._refresh_history()
        self._refresh_analytics()

    # ------------------------------------------------------------------
    # Analytics tab
    # ------------------------------------------------------------------
    def _on_tab_change(self):
        if self.notebook.index(self.notebook.select()) == 2:
            self._refresh_analytics()

    def _refresh_analytics(self):
        if not self.current_user_id:
            return
        try:
            stats = get_stats(self.current_user_id)
        except DatabaseError as exc:
            messagebox.showerror("Database error", str(exc))
            return

        for key in ("latest", "previous", "highest", "lowest"):
            value = stats[key]
            self.stat_labels[key].configure(text=f"{value:.2f}" if value is not None else "--")
        self.stat_labels["count"].configure(text=str(stats["count"]))

        self._draw_charts()

    def _draw_charts(self):
        if not self.current_user_id:
            return
        try:
            records = list(reversed(get_records(self.current_user_id)))
        except DatabaseError:
            records = []

        c = self.colors
        self.figure.set_facecolor(c["surface"])

        for axis, key, title, color in (
            (self.bmi_axis, "bmi", "BMI trend", c["accent"]),
            (self.weight_axis, "weight", "Weight trend", c["overweight"]),
        ):
            axis.clear()
            axis.set_facecolor(c["surface"])
            axis.set_title(title, color=c["text"], fontsize=10)
            axis.tick_params(colors=c["muted"], labelsize=8)
            for spine in axis.spines.values():
                spine.set_color(c["border"])

            if records:
                values = [row[key] for row in records]
                axis.plot(range(1, len(values) + 1), values, marker="o",
                          color=color, linewidth=2)
            else:
                axis.text(0.5, 0.5, "No data yet", ha="center", va="center",
                          color=c["muted"], transform=axis.transAxes)

        self.figure.tight_layout()
        self.canvas.draw()


if __name__ == "__main__":
    app = BMIInsightApp()
    app.mainloop()

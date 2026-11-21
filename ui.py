from decimal import Decimal
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk, ImageOps, ImageDraw, ImageFont, ImageFilter

from core import (
    ctk,
    ttk,
    messagebox,
    BG,
    SIDEBAR,
    CARD,
    BLUE,
    BLUE_HOVER,
    WHITE,
    MUTED
)

from bank import Bank


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.db = Bank()

        self.title("NG BANK | Secure Banking")
        self.geometry("1350x950")
        self.minsize(1050, 700)
        self.configure(fg_color=BG)

        self.show_login()

    # ============================================================
    # GENERAL UI HELPERS
    # ============================================================

    def ask_yes_no(self, title, message):
        result = {"confirmed": False}

        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("520x430")
        popup.minsize(520, 430)
        popup.resizable(False, False)
        popup.configure(fg_color="#17263F")

        popup.transient(self)
        popup.grab_set()

        popup.update_idletasks()

        x = self.winfo_rootx() + (
                self.winfo_width() - 520
        ) // 2

        y = self.winfo_rooty() + (
                self.winfo_height() - 430
        ) // 2

        popup.geometry(f"+{x}+{y}")

        message_label = ctk.CTkLabel(
            popup,
            text=message,
            font=("Arial", 12),
            text_color="#FFFFFF",
            wraplength=470,
            justify="center"
        )
        message_label.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(20, 10)
        )

        button_frame = ctk.CTkFrame(
            popup,
            fg_color="transparent"
        )
        button_frame.pack(
            side="bottom",
            pady=(10, 25)
        )

        def close_popup(confirmed):
            result["confirmed"] = confirmed
            popup.destroy()

        ctk.CTkButton(
            button_frame,
            text="Yes",
            width=110,
            height=36,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=lambda: close_popup(True)
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            button_frame,
            text="No",
            width=110,
            height=36,
            fg_color="#374151",
            hover_color="#4B5563",
            command=lambda: close_popup(False)
        ).pack(side="left", padx=8)

        popup.protocol(
            "WM_DELETE_WINDOW",
            lambda: close_popup(False)
        )

        popup.bind(
            "<Escape>",
            lambda event: close_popup(False)
        )

        popup.bind(
            "<Return>",
            lambda event: close_popup(True)
        )

        popup.after(100, popup.focus_force)
        self.wait_window(popup)

        return result["confirmed"]


    def show_ok(self, title, message):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("430x220")
        popup.resizable(False, False)
        popup.configure(fg_color="#17263F")

        popup.transient(self)
        popup.grab_set()
        popup.update_idletasks()

        x = self.winfo_rootx() + (
            self.winfo_width() - 430
        ) // 2

        y = self.winfo_rooty() + (
            self.winfo_height() - 220
        ) // 2

        popup.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            popup,
            text=message,
            font=("Arial", 12),
            text_color="#FFFFFF",
            wraplength=385,
            justify="center"
        ).pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(20, 10)
        )

        ctk.CTkButton(
            popup,
            text="OK",
            width=120,
            height=36,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=popup.destroy
        ).pack(pady=(0, 20))

        popup.protocol("WM_DELETE_WINDOW", popup.destroy)
        popup.bind("<Escape>", lambda event: popup.destroy())
        popup.bind("<Return>", lambda event: popup.destroy())

        popup.after(100, popup.focus_force)
        self.wait_window(popup)


    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def run(self, fn):
        try:
            return fn()
        except Exception as error:
            self.show_ok("Error", str(error))
            return None


    def button(self, parent, title, command, width=200):
        return ctk.CTkButton(
            parent,
            text=title,
            command=command,
            width=width,
            height=44,
            corner_radius=10,
            border_width=0,
            fg_color=BLUE,
            hover_color=BLUE_HOVER,
            font=("Arial", 13, "bold")
        )

    def entry(self, parent, placeholder, secret=False):
        widget = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            width=330,
            height=44,
            corner_radius=10,
            border_width=1,
            font=("Arial", 13),
            show="*" if secret else None
        )

        widget.pack(pady=6)
        return widget



    def auth_card(self, title, subtitle, height):
        self.clear()

        card = ctk.CTkFrame(
            self,
            width=460,
            height=height,
            fg_color=CARD,
            corner_radius=20
        )

        card.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        card.pack_propagate(False)

        ctk.CTkLabel(
            card,
            text="BANKING SYSTEM",
            font=("Arial", 14, "bold"),
            text_color="#60A5FA"
        ).pack(pady=(18, 8))

        ctk.CTkLabel(
            card,
            text=title,
            font=("Arial", 27, "bold"),
            text_color=WHITE
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            card,
            text=subtitle,
            font=("Arial", 13),
            text_color=MUTED
        ).pack(pady=(0, 14))

        return card



    def table(self, parent, columns, headings):
        holder = ctk.CTkFrame(
            parent,
            fg_color=CARD,
            corner_radius=12
        )
        holder.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=12
        )

        style = ttk.Style()
        style.configure(
            "Bank.Treeview",
            font=("Arial", 11),
            rowheight=32
        )
        style.configure(
            "Bank.Treeview.Heading",
            font=("Arial", 11, "bold"),
            padding=(10, 9)
        )

        table_frame = ctk.CTkFrame(
            holder,
            fg_color="transparent"
        )
        table_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Bank.Treeview"
        )

        for col, heading in zip(columns, headings):
            tree.heading(col, text=heading)
            tree.column(
                col,
                width=155,
                minwidth=95,
                anchor="center",
                stretch=True
            )

        yscroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=tree.yview
        )

        xscroll = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=tree.xview
        )

        tree.configure(
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set
        )

        yscroll.pack(
            side="right",
            fill="y"
        )

        xscroll.pack(
            side="bottom",
            fill="x"
        )

        tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        return tree


    def refresh_table(self, tree, function):
        rows = self.run(function)

        if rows is None:
            return

        tree.delete(*tree.get_children())

        for row in rows:
            tree.insert(
                "",
                "end",
                values=[
                    "" if item is None else str(item)
                    for item in row
                ]
            )

    # ============================================================
    # LOGIN SCREEN
    # ============================================================

    def show_login(self):
        self.clear()

        import tkinter as tk
        from pathlib import Path
        from PIL import (
            Image,
            ImageTk,
            ImageOps,
            ImageDraw,
            ImageFont,
            ImageFilter
        )

        image_path = (
            Path(__file__).resolve().parent
            / "ng_bank_landscape.png"
        )

        if image_path.exists():
            landscape = Image.open(image_path).convert("RGB")
        else:
            landscape = Image.new("RGB", (1600, 950), "#152C50")

        # ====================================================
        # COLORS
        # ====================================================

        INPUT_BG = "#F5F7FC"
        INPUT_TEXT = "#21385F"
        ICON_COLOR = "#304B78"
        WHITE_TEXT = "#FFFFFF"
        MUTED_TEXT = "#5F708D"
        LINK_TEXT = "#2463E9"

        # ====================================================
        # FONTS
        # ====================================================

        def image_font(size, bold=False):
            names = (
                ["arialbd.ttf", "segoeuib.ttf"]
                if bold else
                ["arial.ttf", "segoeui.ttf"]
            )

            for name in names:
                path = Path("C:/Windows/Fonts") / name
                if path.exists():
                    return ImageFont.truetype(
                        str(path),
                        max(10, int(size))
                    )

            return ImageFont.load_default()

        # ====================================================
        # CANVAS
        # ====================================================

        canvas = tk.Canvas(
            self,
            bg=BG,
            highlightthickness=0,
            bd=0
        )
        canvas.pack(fill="both", expand=True)

        background_ref = {"photo": None}
        resize_job = {"id": None}
        password_visible = {"value": False}

        # ====================================================
        # REAL TEXT INPUTS - NO CUSTOMTKINTER OVERLAYS
        # ====================================================

        email = tk.Entry(
            canvas,
            bg=INPUT_BG,
            fg=INPUT_TEXT,
            insertbackground=INPUT_TEXT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Arial", 14)
        )

        password = tk.Entry(
            canvas,
            bg=INPUT_BG,
            fg=INPUT_TEXT,
            insertbackground=INPUT_TEXT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Arial", 14),
            show="*"
        )

        placeholders = {
            email: "Gmail address",
            password: "Password"
        }

        def apply_placeholder(entry):
            if not entry.get():
                entry.configure(
                    fg="#667795",
                    show=""
                )
                entry.insert(0, placeholders[entry])

        def remove_placeholder(entry):
            if entry.get() == placeholders[entry]:
                entry.delete(0, "end")

            entry.configure(fg=INPUT_TEXT)

            if entry is password:
                entry.configure(
                    show=(
                        ""
                        if password_visible["value"]
                        else "*"
                    )
                )

        for entry in (email, password):
            entry.bind(
                "<FocusIn>",
                lambda event, e=entry: remove_placeholder(e)
            )
            entry.bind(
                "<FocusOut>",
                lambda event, e=entry: apply_placeholder(e)
            )
            apply_placeholder(entry)

        # ====================================================
        # LOGIN ACTION
        # ====================================================

        def submit():
            email_value = email.get().strip()
            password_value = password.get()

            if email_value == placeholders[email]:
                email_value = ""

            if password_value == placeholders[password]:
                password_value = ""

            def action():
                self.db.login(email_value, password_value)
                self.show_panel()

            self.run(action)

        # ====================================================
        # REGISTRATION ACTION
        # ====================================================

        def open_registration():
            # Wait until the mouse event has completely ended.
            canvas.after(
                80,
                self.show_register
            )

        # ====================================================
        # PASSWORD VISIBILITY
        # ====================================================

        def toggle_password():
            password_visible["value"] = (
                not password_visible["value"]
            )

            if password.get() != placeholders[password]:
                password.configure(
                    show=(
                        ""
                        if password_visible["value"]
                        else "*"
                    )
                )

            render()

        # ====================================================
        # DRAWING
        # ====================================================

        def render():
            if not canvas.winfo_exists():
                return

            width = canvas.winfo_width()
            height = canvas.winfo_height()

            if width < 2 or height < 2:
                return

            scale = min(width / 1600, height / 950)
            scale = max(0.7, min(scale, 1.15))

            def px(value):
                return max(1, round(value * scale))

            background = ImageOps.fit(
                landscape,
                (width, height),
                method=Image.Resampling.LANCZOS
            ).convert("RGBA")

            overlay = Image.new(
                "RGBA",
                (width, height),
                (5, 12, 30, 12)
            )
            background = Image.alpha_composite(
                background,
                overlay
            )

            center_x = width // 2

            card_w = min(px(590), width - 40)
            card_h = min(px(555), height - px(170))

            center_y = int(height * 0.57)

            left = center_x - card_w // 2
            right = center_x + card_w // 2
            top = center_y - card_h // 2
            bottom = center_y + card_h // 2

            # ====================================================
            # GLASS CARD
            # ====================================================

            # Soft drop shadow and frosted white glass panel.
            shadow_mask = Image.new("L", (width, height), 0)
            shadow_draw = ImageDraw.Draw(shadow_mask)

            shadow_draw.rounded_rectangle(
                (left, top + px(9), right, bottom + px(9)),
                radius=px(30),
                fill=115
            )

            shadow_mask = shadow_mask.filter(
                ImageFilter.GaussianBlur(px(22))
            )

            shadow = Image.new(
                "RGBA",
                (width, height),
                (15, 30, 60, 0)
            )
            shadow.putalpha(shadow_mask)

            background = Image.alpha_composite(background, shadow)

            blurred = background.filter(
                ImageFilter.GaussianBlur(px(17))
            )

            mask = Image.new("L", (width, height), 0)
            mask_draw = ImageDraw.Draw(mask)

            mask_draw.rounded_rectangle(
                (left, top, right, bottom),
                radius=px(30),
                fill=255
            )

            background.paste(blurred, (0, 0), mask)

            glass = Image.new(
                "RGBA",
                (width, height),
                (0, 0, 0, 0)
            )

            glass_draw = ImageDraw.Draw(glass)

            glass_draw.rounded_rectangle(
                (left, top, right, bottom),
                radius=px(30),
                fill=(246, 249, 255, 193),
                outline=(255, 255, 255, 235),
                width=max(1, px(2))
            )

            background = Image.alpha_composite(
                background,
                glass
            )

            draw = ImageDraw.Draw(background)

            # ====================================================
            # NG BANK LOGO
            # ====================================================

            logo_y = max(px(15), top - px(105))
            logo_x = center_x - px(200)

            draw.arc(
                (
                    logo_x,
                    logo_y,
                    logo_x + px(110),
                    logo_y + px(80)
                ),
                start=25,
                end=335,
                fill="#12B7FF",
                width=max(3, px(5))
            )

            draw.text(
                (logo_x + px(17), logo_y + px(7)),
                "NG",
                font=image_font(px(52), True),
                fill=WHITE_TEXT
            )

            divider_x = logo_x + px(125)

            draw.line(
                (
                    divider_x,
                    logo_y + px(12),
                    divider_x,
                    logo_y + px(66)
                ),
                fill="#DCEAFF",
                width=max(1, px(2))
            )

            draw.text(
                (
                    divider_x + px(22),
                    logo_y + px(9)
                ),
                "NG BANK",
                font=image_font(px(40), True),
                fill=WHITE_TEXT
            )

            # ====================================================
            # BANK ICON
            # ====================================================

            icon_size = px(76)
            icon_x = center_x - icon_size // 2
            icon_y = top + px(28)

            draw.rounded_rectangle(
                (
                    icon_x,
                    icon_y,
                    icon_x + icon_size,
                    icon_y + icon_size
                ),
                radius=px(19),
                fill="#365DA2"
            )

            roof_y = icon_y + px(19)

            draw.polygon(
                [
                    (center_x, roof_y),
                    (center_x - px(23), roof_y + px(15)),
                    (center_x + px(23), roof_y + px(15))
                ],
                fill=WHITE_TEXT
            )

            for offset in (-15, 0, 15):
                x = center_x + px(offset)

                draw.rectangle(
                    (
                        x - px(3),
                        roof_y + px(20),
                        x + px(3),
                        roof_y + px(42)
                    ),
                    fill=WHITE_TEXT
                )

            draw.rectangle(
                (
                    center_x - px(25),
                    roof_y + px(44),
                    center_x + px(25),
                    roof_y + px(48)
                ),
                fill=WHITE_TEXT
            )

            # ====================================================
            # WELCOME TEXT
            # ====================================================

            title_y = top + px(128)

            draw.text(
                (center_x, title_y),
                "Welcome Back",
                font=image_font(px(35), True),
                fill="#1B3560",
                anchor="mt"
            )

            draw.text(
                (center_x, title_y + px(56)),
                "Sign in to your account",
                font=image_font(px(16)),
                fill=MUTED_TEXT,
                anchor="mt"
            )

            # ====================================================
            # INPUT BOXES
            # ====================================================

            input_w = card_w - px(96)
            input_h = px(61)
            input_left = center_x - input_w // 2

            email_y = top + px(242)
            password_y = email_y + px(82)

            for y in (email_y, password_y):
                draw.rounded_rectangle(
                    (
                        input_left,
                        y,
                        input_left + input_w,
                        y + input_h
                    ),
                    radius=px(12),
                    fill=INPUT_BG,
                    outline="#E0E7F2",
                    width=max(1, px(1))
                )

            # Email icon
            mx = input_left + px(22)
            my = email_y + px(21)

            draw.rounded_rectangle(
                (mx, my, mx + px(26), my + px(19)),
                radius=px(3),
                outline=ICON_COLOR,
                width=max(1, px(2))
            )

            draw.line(
                [
                    (mx, my + px(2)),
                    (mx + px(13), my + px(11)),
                    (mx + px(26), my + px(2))
                ],
                fill=ICON_COLOR,
                width=max(1, px(2))
            )

            # Password icon
            lx = input_left + px(24)
            ly = password_y + px(28)

            draw.rounded_rectangle(
                (lx, ly, lx + px(23), ly + px(20)),
                radius=px(3),
                outline=ICON_COLOR,
                width=max(1, px(2))
            )

            draw.arc(
                (
                    lx + px(4),
                    ly - px(13),
                    lx + px(19),
                    ly + px(9)
                ),
                start=180,
                end=360,
                fill=ICON_COLOR,
                width=max(1, px(2))
            )

            # ====================================================
            # SIGN IN BUTTON
            # ====================================================

            button_y = password_y + px(88)
            button_h = px(62)

            draw.rounded_rectangle(
                (
                    input_left,
                    button_y,
                    input_left + input_w,
                    button_y + button_h
                ),
                radius=px(12),
                fill=BLUE
            )

            draw.text(
                (center_x, button_y + button_h // 2),
                "Sign In",
                font=image_font(px(17), True),
                fill=WHITE_TEXT,
                anchor="mm"
            )

            # ====================================================
            # REGISTER LINK
            # ====================================================

            register_y = button_y + button_h + px(38)

            draw.text(
                (center_x, register_y),
                "Create a new account",
                font=image_font(px(15)),
                fill="#516789",
                anchor="mm"
            )

            # ====================================================
            # PASSWORD SHOW/HIDE TEXT
            # ====================================================

            show_x = input_left + input_w - px(42)
            show_y = password_y + input_h // 2

            draw.text(
                (show_x, show_y),
                (
                    "Hide"
                    if password_visible["value"]
                    else "Show"
                ),
                font=image_font(px(12)),
                fill=LINK_TEXT,
                anchor="mm"
            )

            # ====================================================
            # UPDATE BACKGROUND
            # ====================================================

            photo = ImageTk.PhotoImage(
                background.convert("RGB")
            )

            background_ref["photo"] = photo

            canvas.delete("all")

            canvas.create_image(
                0,
                0,
                image=photo,
                anchor="nw"
            )

            # ====================================================
            # PLACE ENTRIES
            # ====================================================

            entry_x = input_left + px(65)

            email_window_width = input_w - px(90)
            password_window_width = input_w - px(165)

            canvas.create_window(
                entry_x,
                email_y + input_h // 2,
                window=email,
                width=email_window_width,
                height=px(30),
                anchor="w"
            )

            canvas.create_window(
                entry_x,
                password_y + input_h // 2,
                window=password,
                width=password_window_width,
                height=px(30),
                anchor="w"
            )

            # ====================================================
            # CLICKABLE CANVAS AREAS
            # ====================================================

            canvas.create_rectangle(
                input_left,
                button_y,
                input_left + input_w,
                button_y + button_h,
                fill="",
                outline="",
                tags="login_action"
            )

            canvas.create_rectangle(
                center_x - px(130),
                register_y - px(20),
                center_x + px(130),
                register_y + px(20),
                fill="",
                outline="",
                tags="register_action"
            )

            canvas.create_rectangle(
                show_x - px(35),
                show_y - px(20),
                show_x + px(35),
                show_y + px(20),
                fill="",
                outline="",
                tags="password_action"
            )

            canvas.tag_bind(
                "login_action",
                "<ButtonRelease-1>",
                lambda event: submit()
            )

            canvas.tag_bind(
                "register_action",
                "<ButtonRelease-1>",
                lambda event: open_registration()
            )

            canvas.tag_bind(
                "password_action",
                "<ButtonRelease-1>",
                lambda event: toggle_password()
            )

            for tag in (
                "login_action",
                "register_action",
                "password_action"
            ):
                canvas.tag_bind(
                    tag,
                    "<Enter>",
                    lambda event: canvas.configure(cursor="hand2")
                )
                canvas.tag_bind(
                    tag,
                    "<Leave>",
                    lambda event: canvas.configure(cursor="")
                )

        # ====================================================
        # RESIZE HANDLING
        # ====================================================

        def schedule_render(event=None):
            if resize_job["id"] is not None:
                canvas.after_cancel(resize_job["id"])

            resize_job["id"] = canvas.after(
                150,
                delayed_render
            )

        def delayed_render():
            resize_job["id"] = None
            render()

        canvas.bind("<Configure>", schedule_render)

        email.bind(
            "<Return>",
            lambda event: password.focus_set()
        )

        password.bind(
            "<Return>",
            lambda event: submit()
        )

        canvas.after(100, render)

    # ============================================================
    # REGISTRATION SCREEN
    # ============================================================

    def show_register(self):
        self.clear()

        image_path = (
                Path(__file__).resolve().parent
                / "ng_bank_landscape.png"
        )

        if image_path.exists():
            landscape = Image.open(image_path).convert("RGB")
        else:
            landscape = Image.new("RGB", (1600, 950), "#152C50")

        canvas = tk.Canvas(
            self,
            highlightthickness=0,
            bd=0
        )
        canvas.pack(fill="both", expand=True)

        background_ref = {"photo": None}
        resize_job = {"id": None}

        # ====================================================
        # REGISTRATION FIELDS
        # ====================================================

        field_specs = [
            ("First name", False),
            ("Last name", False),
            ("11-digit National ID", False),
            ("Phone number (11 digits)", False),
            ("Gmail address (@gmail.com)", False),
            ("City (İl)", False),
            ("District (İlçe)", False),
            ("Password (minimum 4 characters)", True),
            ("Confirm password", True)
        ]

        entries = []

        for placeholder, secret in field_specs:
            entry = ctk.CTkEntry(
                canvas,
                placeholder_text=placeholder,
                height=43,
                corner_radius=11,
                border_width=1,
                border_color="#DCE5F2",
                fg_color="#F5F7FC",
                text_color="#21385F",
                placeholder_text_color="#71819B",
                font=("Arial", 12),
                show="*" if secret else None
            )
            entries.append(entry)

        (
            first, last, national_id, phone, email,
            city, district, password, confirm
        ) = entries

        # ====================================================
        # REGISTRATION ACTION - ORIGINAL LOGIC
        # ====================================================

        def submit():
            def action():
                if password.get() != confirm.get():
                    raise ValueError(
                        "Passwords do not match."
                    )

                city_value = city.get().strip()
                district_value = district.get().strip()

                if not city_value or not district_value:
                    raise ValueError(
                        "City and District are required."
                    )

                address_value = (
                    f"{city_value} / {district_value}"
                )

                self.db.register(
                    first.get(),
                    last.get(),
                    national_id.get(),
                    phone.get(),
                    email.get(),
                    address_value,
                    password.get()
                )

                self.show_ok(
                    "Registration Successful",
                    "Registration Successful!"
                )

                self.show_login()

            self.run(action)

        register_button = ctk.CTkButton(
            canvas,
            text="Register",
            command=submit,
            height=46,
            corner_radius=11,
            fg_color="#2463E9",
            hover_color="#1D4ED8",
            text_color="#FFFFFF",
            font=("Arial", 13, "bold")
        )

        back_button = ctk.CTkButton(
            canvas,
            text="Back to Login",
            command=self.show_login,
            height=30,
            fg_color="transparent",
            hover_color="#E2E9F5",
            text_color="#304B78",
            font=("Arial", 12)
        )

        # ====================================================
        # FONT HELPER
        # ====================================================

        def image_font(size, bold=False):
            names = (
                ["arialbd.ttf", "segoeuib.ttf"]
                if bold else
                ["arial.ttf", "segoeui.ttf"]
            )

            for name in names:
                path = Path("C:/Windows/Fonts") / name
                if path.exists():
                    return ImageFont.truetype(
                        str(path),
                        max(10, int(size))
                    )

            return ImageFont.load_default()

        # ====================================================
        # BACKGROUND AND WHITE GLASS PANEL
        # ====================================================

        def render():
            if not canvas.winfo_exists():
                return

            width = canvas.winfo_width()
            height = canvas.winfo_height()

            if width < 2 or height < 2:
                return

            scale = min(width / 1600, height / 950)
            scale = max(0.70, min(scale, 1.10))

            def px(value):
                return max(1, round(value * scale))

            background = ImageOps.fit(
                landscape,
                (width, height),
                method=Image.Resampling.LANCZOS
            ).convert("RGBA")

            overlay = Image.new(
                "RGBA",
                (width, height),
                (5, 12, 30, 12)
            )
            background = Image.alpha_composite(
                background, overlay
            )

            center_x = width // 2
            center_y = height // 2

            card_w = min(px(540), width - 40)
            card_h = min(px(850), height - 25)

            left = center_x - card_w // 2
            right = center_x + card_w // 2
            top = center_y - card_h // 2
            bottom = center_y + card_h // 2

            # Soft shadow
            shadow_mask = Image.new(
                "L", (width, height), 0
            )
            shadow_draw = ImageDraw.Draw(shadow_mask)

            shadow_draw.rounded_rectangle(
                (
                    left,
                    top + px(7),
                    right,
                    bottom + px(7)
                ),
                radius=px(28),
                fill=100
            )

            shadow_mask = shadow_mask.filter(
                ImageFilter.GaussianBlur(px(20))
            )

            shadow = Image.new(
                "RGBA",
                (width, height),
                (15, 30, 60, 0)
            )
            shadow.putalpha(shadow_mask)

            background = Image.alpha_composite(
                background, shadow
            )

            # Blur only the panel background
            blurred = background.filter(
                ImageFilter.GaussianBlur(px(17))
            )

            mask = Image.new("L", (width, height), 0)
            mask_draw = ImageDraw.Draw(mask)

            mask_draw.rounded_rectangle(
                (left, top, right, bottom),
                radius=px(28),
                fill=255
            )

            background.paste(blurred, (0, 0), mask)

            # White translucent glass
            glass = Image.new(
                "RGBA",
                (width, height),
                (0, 0, 0, 0)
            )

            glass_draw = ImageDraw.Draw(glass)
            glass_draw.rounded_rectangle(
                (left, top, right, bottom),
                radius=px(28),
                fill=(246, 249, 255, 193),
                outline=(255, 255, 255, 235),
                width=max(1, px(2))
            )

            background = Image.alpha_composite(
                background, glass
            )

            draw = ImageDraw.Draw(background)

            # ====================================================
            # TITLE
            # ====================================================

            draw.text(
                (center_x, top + px(24)),
                "NG BANK",
                font=image_font(px(20), True),
                fill="#2463E9",
                anchor="mt"
            )

            draw.text(
                (center_x, top + px(62)),
                "Create Your Account",
                font=image_font(px(28), True),
                fill="#1B3560",
                anchor="mt"
            )

            draw.text(
                (center_x, top + px(109)),
                "All fields are required",
                font=image_font(px(14)),
                fill="#5F708D",
                anchor="mt"
            )

            # ====================================================
            # DRAW BACKGROUND
            # ====================================================

            photo = ImageTk.PhotoImage(
                background.convert("RGB")
            )

            background_ref["photo"] = photo

            canvas.delete("all")
            canvas.create_image(
                0, 0,
                image=photo,
                anchor="nw"
            )

            # ====================================================
            # PLACE FORM WIDGETS
            # ====================================================

            field_width = card_w - px(90)
            field_height = px(43)
            field_gap = px(10)
            first_y = top + px(155)

            for index, entry in enumerate(entries):
                y = first_y + index * (
                        field_height + field_gap
                )

                canvas.create_window(
                    center_x,
                    y,
                    window=entry,
                    width=field_width,
                    height=field_height,
                    anchor="n"
                )

            button_y = (
                    first_y
                    + len(entries) * (field_height + field_gap)
                    + px(6)
            )

            canvas.create_window(
                center_x,
                button_y,
                window=register_button,
                width=field_width,
                height=px(46),
                anchor="n"
            )

            canvas.create_window(
                center_x,
                button_y + px(55),
                window=back_button,
                width=px(180),
                height=px(30),
                anchor="n"
            )

        # ====================================================
        # RESIZE HANDLING
        # ====================================================

        def delayed_render():
            resize_job["id"] = None
            render()

        def schedule_render(event=None):
            if resize_job["id"] is not None:
                canvas.after_cancel(resize_job["id"])

            resize_job["id"] = canvas.after(
                150, delayed_render
            )

        canvas.bind("<Configure>", schedule_render)
        canvas.after(100, render)

    # ============================================================
    # MAIN PANEL AND SIDEBAR
    # ============================================================


    def show_panel(self):
        session = self.db.session

        if session is None:
            self.show_login()
            return

        self.clear()

        # Main sidebar
        self.sidebar = ctk.CTkFrame(
            self,
            width=252,
            fg_color=SIDEBAR,
            corner_radius=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Main content area
        self.main = ctk.CTkFrame(
            self,
            fg_color=BG,
            corner_radius=0
        )
        self.main.pack(
            side="right",
            fill="both",
            expand=True
        )

        # Branding
        brand = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )
        brand.pack(
            fill="x",
            padx=20,
            pady=(26, 16)
        )

        ctk.CTkLabel(
            brand,
            text="BANKING",
            font=("Arial", 25, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            brand,
            text="MANAGEMENT SYSTEM",
            font=("Arial", 10, "bold"),
            text_color=MUTED,
            anchor="w"
        ).pack(fill="x", pady=(3, 0))

        # User information
        user_info = ctk.CTkFrame(
            self.sidebar,
            fg_color=CARD,
            corner_radius=12
        )
        user_info.pack(
            fill="x",
            padx=14,
            pady=(0, 18)
        )

        ctk.CTkLabel(
            user_info,
            text=session["role"].upper(),
            font=("Arial", 12, "bold"),
            text_color="#60A5FA",
            anchor="w"
        ).pack(
            fill="x",
            padx=14,
            pady=(12, 3)
        )

        ctk.CTkLabel(
            user_info,
            text=session["email"],
            font=("Arial", 11),
            text_color=MUTED,
            anchor="w",
            wraplength=190
        ).pack(
            fill="x",
            padx=14,
            pady=(0, 12)
        )

        # Navigation
        if session["role"] == "Admin":
            navigation = [
                ("Dashboard", self.show_dashboard),
                ("Customers", self.show_customers),
                ("Accounts", self.show_accounts),
                ("Transactions", self.show_transactions),
                (
                    "Credit Card Applications",
                    self.show_admin_credit_card_applications
                ),
                ("Fraud Alerts", self.show_fraud),
                ("Fraud Rules", self.show_rules),
                ("Send Announcement", self.show_announcement),
                ("Audit Logs", self.show_logs)
            ]
        else:
            navigation = [
                ("Dashboard", self.show_dashboard),
                ("My Accounts", self.show_accounts),
                ("My Credit Cards", self.show_my_credit_cards),
                ("My Transactions", self.show_transactions),
                (
                    "My Fraud Reviews",
                    self.show_customer_fraud_reviews
                ),
                ("Notifications", self.show_notifications)
            ]

        ctk.CTkLabel(
            self.sidebar,
            text="NAVIGATION",
            font=("Arial", 11, "bold"),
            text_color=MUTED,
            anchor="w"
        ).pack(
            fill="x",
            padx=24,
            pady=(0, 9)
        )

        navigation_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            corner_radius=0
        )
        navigation_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 8)
        )

        for title, fn in navigation:
            ctk.CTkButton(
                navigation_frame,
                text=title,
                command=lambda f=fn: self.run(f),
                height=42,
                corner_radius=10,
                fg_color=BLUE,
                hover_color=BLUE_HOVER,
                font=("Arial", 12, "bold"),
                anchor="w"
            ).pack(
                fill="x",
                padx=5,
                pady=4
            )

        # Logout
        ctk.CTkButton(
            self.sidebar,
            text="Logout",
            command=self.logout,
            height=44,
            corner_radius=10,
            font=("Arial", 13, "bold"),
            fg_color="#991B1B",
            hover_color="#7F1D1D"
        ).pack(
            side="bottom",
            fill="x",
            padx=15,
            pady=(8, 20)
        )

        self.run(self.show_dashboard)


    def logout(self):
        self.db.logout()
        self.show_login()


    def page(self, title):
        for widget in self.main.winfo_children():
            widget.destroy()

        header = ctk.CTkFrame(
            self.main,
            fg_color="transparent"
        )
        header.pack(
            fill="x",
            padx=24,
            pady=(22, 14)
        )

        ctk.CTkLabel(
            header,
            text=title,
            font=("Arial", 26, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            header,
            text="Banking Management & Fraud Detection System",
            font=("Arial", 12),
            text_color=MUTED,
            anchor="w"
        ).pack(
            fill="x",
            pady=(5, 0)
        )

        return self.main



    # ============================================================
    # DASHBOARD - ADMIN / CUSTOMER MOBILE BANKING
    # ============================================================


    def show_dashboard(self):
        session = self.db.require_login()
        page = self.page("Dashboard")


        # ====================================================
        # ADMIN DASHBOARD
        # ====================================================

        if session["role"] == "Admin":
            data = self.db.dashboard()
            metrics = dict(data)

            scroll = ctk.CTkScrollableFrame(
                page,
                fg_color="transparent",
                corner_radius=0
            )
            scroll.pack(
                fill="both",
                expand=True,
                padx=20,
                pady=(0, 12)
            )

            # ====================================================
            # WELCOME HEADER
            # ====================================================

            welcome = ctk.CTkFrame(
                scroll,
                fg_color="transparent"
            )
            welcome.pack(
                fill="x",
                pady=(4, 18)
            )

            ctk.CTkLabel(
                welcome,
                text="Admin Overview",
                font=("Arial", 25, "bold"),
                text_color=WHITE,
                anchor="w"
            ).pack(
                fill="x",
                padx=5
            )

            ctk.CTkLabel(
                welcome,
                text="Welcome to your banking management dashboard.",
                font=("Arial", 13),
                text_color=MUTED,
                anchor="w"
            ).pack(
                fill="x",
                padx=5,
                pady=(5, 0)
            )

            # ====================================================
            # TOTAL SYSTEM BALANCE - FULL WIDTH
            # ====================================================

            balance_card = ctk.CTkFrame(
                scroll,
                fg_color="#2056C7",
                corner_radius=18
            )
            balance_card.pack(
                fill="x",
                pady=(0, 18)
            )

            ctk.CTkLabel(
                balance_card,
                text="TOTAL SYSTEM BALANCE",
                font=("Arial", 12, "bold"),
                text_color="#DCEAFF",
                anchor="w"
            ).pack(
                fill="x",
                padx=30,
                pady=(25, 12)
            )

            ctk.CTkLabel(
                balance_card,
                text=str(metrics.get("Total Balance", "0.00 TRY")),
                font=("Arial", 34, "bold"),
                text_color=WHITE,
                anchor="w"
            ).pack(
                fill="x",
                padx=30
            )

            ctk.CTkLabel(
                balance_card,
                text="Combined balance of all active bank accounts",
                font=("Arial", 13),
                text_color="#DCEAFF",
                anchor="w"
            ).pack(
                fill="x",
                padx=30,
                pady=(12, 27)
            )

            # ====================================================
            # SYSTEM STATISTICS
            # ====================================================

            ctk.CTkLabel(
                scroll,
                text="System Statistics",
                font=("Arial", 19, "bold"),
                text_color=WHITE,
                anchor="w"
            ).pack(
                fill="x",
                padx=5,
                pady=(4, 12)
            )

            statistics = ctk.CTkFrame(
                scroll,
                fg_color="transparent"
            )
            statistics.pack(
                fill="x",
                pady=(0, 12)
            )

            for column in range(2):
                statistics.grid_columnconfigure(
                    column,
                    weight=1,
                    uniform="admin_statistics"
                )

            statistic_items = [
                ("Customers", metrics.get("Customers", 0)),
                ("Accounts", metrics.get("Accounts", 0)),
                (
                    "Today's Transactions",
                    metrics.get("Today's Transactions", 0)
                ),
                (
                    "Pending Fraud Alerts",
                    metrics.get("Pending Fraud Alerts", 0)
                )
            ]

            for index, (title, value) in enumerate(statistic_items):
                card = ctk.CTkFrame(
                    statistics,
                    fg_color=CARD,
                    corner_radius=14
                )
                card.grid(
                    row=index // 2,
                    column=index % 2,
                    sticky="nsew",
                    padx=6,
                    pady=6
                )

                ctk.CTkLabel(
                    card,
                    text=title,
                    font=("Arial", 12),
                    text_color=MUTED,
                    anchor="w"
                ).pack(
                    fill="x",
                    padx=22,
                    pady=(20, 10)
                )

                value_color = (
                    "#FCA5A5"
                    if title == "Pending Fraud Alerts"
                    else WHITE
                )

                ctk.CTkLabel(
                    card,
                    text=str(value),
                    font=("Arial", 27, "bold"),
                    text_color=value_color,
                    anchor="w"
                ).pack(
                    fill="x",
                    padx=22,
                    pady=(0, 23)
                )

            # ====================================================
            # MANAGEMENT & SECURITY
            # ====================================================

            ctk.CTkLabel(
                scroll,
                text="Management & Security",
                font=("Arial", 19, "bold"),
                text_color=WHITE,
                anchor="w"
            ).pack(
                fill="x",
                padx=5,
                pady=(15, 12)
            )

            management = ctk.CTkFrame(
                scroll,
                fg_color="transparent"
            )
            management.pack(
                fill="x",
                pady=(0, 12)
            )

            for column in range(2):
                management.grid_columnconfigure(
                    column,
                    weight=1,
                    uniform="management_cards"
                )

            management_sections = [
                (
                    "Customer Management",
                    "View registered customers and their information.",
                    "View Customers",
                    self.show_customers
                ),
                (
                    "Banking Operations",
                    "Review accounts and banking transactions.",
                    "View Transactions",
                    self.show_transactions
                ),
                (
                    "Fraud Monitoring",
                    "Review fraud alerts and suspicious activities.",
                    "View Fraud Alerts",
                    self.show_fraud
                ),
                (
                    "System Audit",
                    "Review recorded system and banking activities.",
                    "View Audit Logs",
                    self.show_logs
                )
            ]

            for index, (
                title,
                description,
                button_title,
                command
            ) in enumerate(management_sections):

                card = ctk.CTkFrame(
                    management,
                    fg_color=CARD,
                    corner_radius=14
                )
                card.grid(
                    row=index // 2,
                    column=index % 2,
                    sticky="nsew",
                    padx=6,
                    pady=6
                )

                card.grid_columnconfigure(
                    0,
                    weight=1
                )

                text_frame = ctk.CTkFrame(
                    card,
                    fg_color="transparent"
                )
                text_frame.grid(
                    row=0,
                    column=0,
                    sticky="ew",
                    padx=(22, 10),
                    pady=19
                )

                ctk.CTkLabel(
                    text_frame,
                    text=title,
                    font=("Arial", 15, "bold"),
                    text_color=WHITE,
                    anchor="w"
                ).pack(
                    fill="x",
                    pady=(0, 7)
                )

                ctk.CTkLabel(
                    text_frame,
                    text=description,
                    font=("Arial", 11),
                    text_color=MUTED,
                    anchor="w",
                    justify="left",
                    wraplength=290
                ).pack(
                    fill="x"
                )

                ctk.CTkButton(
                    card,
                    text=button_title,
                    command=lambda fn=command: self.run(fn),
                    width=150,
                    height=38,
                    corner_radius=9,
                    fg_color=BLUE,
                    hover_color=BLUE_HOVER,
                    text_color=WHITE,
                    font=("Arial", 11, "bold")
                ).grid(
                    row=0,
                    column=1,
                    padx=(5, 18),
                    pady=18
                )

            # ====================================================
            # REFRESH DASHBOARD
            # ====================================================

            refresh_frame = ctk.CTkFrame(
                scroll,
                fg_color="transparent"
            )
            refresh_frame.pack(
                fill="x",
                pady=(12, 25)
            )

            self.button(
                refresh_frame,
                "Refresh Dashboard",
                lambda: self.run(self.show_dashboard),
                width=190
            ).pack(
                side="right"
            )

            return

        # ====================================================
        # CUSTOMER DASHBOARD
        # ====================================================

        data = self.db.customer_banking_overview()

        scroll = ctk.CTkScrollableFrame(
            page,
            fg_color="transparent"
        )
        scroll.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 15)
        )

        def money_text(value):
            return f"{value:,.2f} TRY"

        def section_title(parent, title):
            ctk.CTkLabel(
                parent,
                text=title,
                font=("Arial", 19, "bold"),
                text_color=WHITE,
                anchor="w"
            ).pack(
                fill="x",
                padx=5,
                pady=(23, 12)
            )

        def info_card(parent, title, value, color=WHITE):
            frame = ctk.CTkFrame(
                parent,
                fg_color=CARD,
                corner_radius=14
            )

            ctk.CTkLabel(
                frame,
                text=title,
                font=("Arial", 12),
                text_color=MUTED,
                anchor="w"
            ).pack(
                fill="x",
                padx=20,
                pady=(18, 8)
            )

            ctk.CTkLabel(
                frame,
                text=str(value),
                font=("Arial", 22, "bold"),
                text_color=color,
                anchor="w",
                wraplength=240
            ).pack(
                fill="x",
                padx=20,
                pady=(0, 19)
            )

            return frame

        # ====================================================
        # WELCOME
        # ====================================================

        welcome = ctk.CTkFrame(
            scroll,
            fg_color="transparent"
        )
        welcome.pack(
            fill="x",
            pady=(8, 16)
        )

        ctk.CTkLabel(
            welcome,
            text=f"Hello, {data['customer_name']}!",
            font=("Arial", 25, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(fill="x", padx=5)

        ctk.CTkLabel(
            welcome,
            text="Welcome to your personal banking overview.",
            font=("Arial", 13),
            text_color=MUTED,
            anchor="w"
        ).pack(
            fill="x",
            padx=5,
            pady=(6, 0)
        )

        # ====================================================
        # TOTAL ASSETS
        # ====================================================

        hero = ctk.CTkFrame(
            scroll,
            fg_color="#2056C7",
            corner_radius=18
        )
        hero.pack(
            fill="x",
            pady=(0, 14)
        )

        ctk.CTkLabel(
            hero,
            text="TOTAL ASSETS",
            font=("Arial", 12, "bold"),
            text_color="#DCEAFF",
            anchor="w"
        ).pack(
            fill="x",
            padx=28,
            pady=(24, 9)
        )

        ctk.CTkLabel(
            hero,
            text=money_text(data["total_assets"]),
            font=("Arial", 34, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(
            fill="x",
            padx=28
        )

        ctk.CTkLabel(
            hero,
            text=f"{data['account_count']} active bank accounts",
            font=("Arial", 13),
            text_color="#DCEAFF",
            anchor="w"
        ).pack(
            fill="x",
            padx=28,
            pady=(10, 25)
        )

        # ====================================================
        # FINANCIAL SUMMARY
        # ====================================================

        summary = ctk.CTkFrame(
            scroll,
            fg_color="transparent"
        )
        summary.pack(fill="x", pady=5)

        for column in range(2):
            summary.grid_columnconfigure(
                column,
                weight=1,
                uniform="summary"
            )

        financial_cards = [
            (
                "Total Money In",
                money_text(data["total_in"]),
                "#4ADE80"
            ),
            (
                "Total Money Out",
                money_text(data["total_out"]),
                "#FCA5A5"
            ),
            (
                "Available Balance",
                money_text(data["available_balance"]),
                WHITE
            ),
            (
                "Active Credit Cards",
                str(data["active_credit_card_count"]),
                "#93C5FD"
            )
        ]

        for index, (title, value, color) in enumerate(financial_cards):
            card = info_card(
                summary,
                title,
                value,
                color
            )
            card.grid(
                row=index // 2,
                column=index % 2,
                sticky="nsew",
                padx=6,
                pady=6
            )

        # ====================================================
        # QUICK ACTIONS
        # ====================================================

        section_title(scroll, "Quick Actions")

        actions = ctk.CTkFrame(
            scroll,
            fg_color="transparent"
        )
        actions.pack(fill="x", pady=(0, 8))

        for column in range(4):
            actions.grid_columnconfigure(
                column,
                weight=1,
                uniform="actions"
            )

        quick_actions = [
            ("Transfer", self.show_transactions),
            ("Deposit", self.show_transactions),
            ("Withdraw", self.show_transactions),
            ("My Accounts", self.show_accounts),
            ("Credit Cards", self.show_my_credit_cards),
            ("Transactions", self.show_transactions),
            ("Fraud Reviews", self.show_customer_fraud_reviews),
            ("Notifications", self.show_notifications)
        ]

        for index, (title, command) in enumerate(quick_actions):
            action_button = self.button(
                actions,
                title,
                lambda fn=command: self.run(fn),
                width=115
            )
            action_button.grid(
                row=index // 4,
                column=index % 4,
                sticky="ew",
                padx=6,
                pady=6
            )

        # ====================================================
        # MY BANK ACCOUNTS
        # ====================================================

        section_title(scroll, "My Bank Accounts")

        if not data["accounts"]:
            ctk.CTkLabel(
                scroll,
                text="You do not have an active bank account.",
                text_color=MUTED,
                anchor="w"
            ).pack(fill="x", padx=10, pady=8)

        for account in data["accounts"]:
            account_frame = ctk.CTkFrame(
                scroll,
                fg_color=CARD,
                corner_radius=14
            )
            account_frame.pack(
                fill="x",
                pady=6
            )

            header = ctk.CTkFrame(
                account_frame,
                fg_color="transparent"
            )
            header.pack(
                fill="x",
                padx=20,
                pady=(18, 9)
            )

            ctk.CTkLabel(
                header,
                text=f"{account['type']} Account",
                font=("Arial", 16, "bold"),
                text_color=WHITE
            ).pack(side="left")

            status = "Frozen" if account["frozen"] else "Active"

            ctk.CTkLabel(
                header,
                text=status,
                font=("Arial", 12, "bold"),
                text_color=(
                    "#FCA5A5"
                    if account["frozen"]
                    else "#4ADE80"
                )
            ).pack(side="right")

            ctk.CTkLabel(
                account_frame,
                text="Account Number",
                font=("Arial", 12),
                text_color=MUTED,
                anchor="w"
            ).pack(
                fill="x",
                padx=20
            )

            number_row = ctk.CTkFrame(
                account_frame,
                fg_color="transparent"
            )
            number_row.pack(
                fill="x",
                padx=20,
                pady=(5, 9)
            )

            ctk.CTkLabel(
                number_row,
                text=account["number"],
                font=("Arial", 14),
                text_color=WHITE
            ).pack(side="left")

            ctk.CTkButton(
                number_row,
                text="Copy",
                width=70,
                height=30,
                corner_radius=8,
                command=lambda n=account["number"]: (
                    self.clipboard_clear(),
                    self.clipboard_append(n),
                    self.update()
                )
            ).pack(side="right")

            ctk.CTkLabel(
                account_frame,
                text=money_text(account["balance"]),
                font=("Arial", 23, "bold"),
                text_color=WHITE,
                anchor="w"
            ).pack(
                fill="x",
                padx=20,
                pady=(2, 19)
            )

        # ====================================================
        # MY CREDIT CARDS
        # ====================================================

        section_title(scroll, "My Credit Cards")

        credit_summary = ctk.CTkFrame(
            scroll,
            fg_color="transparent"
        )
        credit_summary.pack(fill="x")

        for column in range(2):
            credit_summary.grid_columnconfigure(
                column,
                weight=1,
                uniform="credit"
            )

        info_card(
            credit_summary,
            "Total Credit Limit",
            money_text(data["total_credit_limit"])
        ).grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=6,
            pady=6
        )

        info_card(
            credit_summary,
            "Available Credit Limit",
            money_text(data["available_credit_limit"]),
            "#4ADE80"
        ).grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=6,
            pady=6
        )

        if data["pending_applications"]:
            pending_frame = ctk.CTkFrame(
                scroll,
                fg_color="#263956",
                corner_radius=12
            )
            pending_frame.pack(
                fill="x",
                pady=9
            )

            ctk.CTkLabel(
                pending_frame,
                text=(
                    f"{data['pending_applications']} "
                    "credit card application(s) "
                    "awaiting approval."
                ),
                text_color="#FDE68A",
                font=("Arial", 13),
                wraplength=650
            ).pack(
                padx=18,
                pady=15
            )

        if not data["credit_cards"]:
            ctk.CTkLabel(
                scroll,
                text="No credit cards issued yet.",
                text_color=MUTED,
                anchor="w"
            ).pack(fill="x", padx=10, pady=8)

        for card in data["credit_cards"]:
            card_frame = ctk.CTkFrame(
                scroll,
                fg_color="#1B3055",
                corner_radius=15
            )
            card_frame.pack(
                fill="x",
                pady=7
            )

            ctk.CTkLabel(
                card_frame,
                text=(
                    f"{card['type']} Credit Card"
                    f"  |  {card['status']}"
                ),
                font=("Arial", 17, "bold"),
                text_color=WHITE,
                anchor="w"
            ).pack(
                fill="x",
                padx=22,
                pady=(19, 10)
            )

            ctk.CTkLabel(
                card_frame,
                text=(
                    "**** **** **** "
                    f"{card['last_four']}"
                ),
                font=("Arial", 17),
                text_color="#BBD3FF",
                anchor="w"
            ).pack(
                fill="x",
                padx=22,
                pady=(0, 12)
            )

            ctk.CTkLabel(
                card_frame,
                text=(
                    "Credit Limit: "
                    f"{money_text(card['limit'])}"
                ),
                font=("Arial", 13),
                text_color=WHITE,
                anchor="w"
            ).pack(
                fill="x",
                padx=22,
                pady=3
            )

            ctk.CTkLabel(
                card_frame,
                text=(
                    "Available Limit: "
                    f"{money_text(card['available'])}"
                ),
                font=("Arial", 13, "bold"),
                text_color="#4ADE80",
                anchor="w"
            ).pack(
                fill="x",
                padx=22,
                pady=(3, 20)
            )

        self.button(
            scroll,
            "View All Credit Cards",
            lambda: self.run(self.show_my_credit_cards)
        ).pack(
            anchor="e",
            pady=(12, 6)
        )

        # ====================================================
        # RECENT TRANSACTIONS
        # ====================================================

        section_title(scroll, "Recent Transactions")

        if not data["recent_transactions"]:
            ctk.CTkLabel(
                scroll,
                text="No recent transactions.",
                text_color=MUTED,
                anchor="w"
            ).pack(fill="x", padx=10, pady=8)

        for transaction in data["recent_transactions"]:
            transaction_frame = ctk.CTkFrame(
                scroll,
                fg_color=CARD,
                corner_radius=12
            )
            transaction_frame.pack(
                fill="x",
                pady=5
            )

            direction = transaction["direction"]

            if direction == "Incoming":
                amount_color = "#4ADE80"
                prefix = "+"
            elif direction == "Outgoing":
                amount_color = "#FCA5A5"
                prefix = "-"
            else:
                amount_color = WHITE
                prefix = ""

            left = ctk.CTkFrame(
                transaction_frame,
                fg_color="transparent"
            )
            left.pack(
                side="left",
                fill="both",
                expand=True,
                padx=19,
                pady=15
            )

            ctk.CTkLabel(
                left,
                text=(
                    f"{transaction['type']} "
                    f"({direction})"
                ),
                font=("Arial", 14, "bold"),
                text_color=WHITE,
                anchor="w"
            ).pack(fill="x")

            ctk.CTkLabel(
                left,
                text=(
                    f"{str(transaction['date'])[:16]}"
                    f"  |  {transaction['status']}"
                ),
                font=("Arial", 12),
                text_color=MUTED,
                anchor="w"
            ).pack(
                fill="x",
                pady=(5, 0)
            )

            ctk.CTkLabel(
                transaction_frame,
                text=(
                    f"{prefix}"
                    f"{money_text(transaction['amount'])}"
                ),
                font=("Arial", 16, "bold"),
                text_color=amount_color
            ).pack(
                side="right",
                padx=19
            )

        self.button(
            scroll,
            "View All Transactions",
            lambda: self.run(self.show_transactions)
        ).pack(
            anchor="e",
            pady=(12, 8)
        )

        # ====================================================
        # REFRESH
        # ====================================================

        self.button(
            scroll,
            "Refresh Dashboard",
            lambda: self.run(self.show_dashboard)
        ).pack(
            anchor="e",
            pady=(14, 25)
        )


    # ============================================================
    # CUSTOMERS SCREEN
    # ============================================================
    def show_customers(self):
        # ====================================================
        # ADMIN CUSTOMER MANAGEMENT - PREMIUM DESIGN
        # ====================================================

        self.db.require_admin()
        page = self.page("Customer Management")

        colors = {
            "panel": "#17263F",
            "header": "#243A59",
            "border": "#2B4161",
            "text": "#F5F8FF",
            "muted": "#9EB2D0",
            "blue": "#3478F6",
            "green": "#4ADE80",
            "red": "#FCA5A5"
        }

        # ====================================================
        # LOAD CUSTOMERS
        # ====================================================

        rows = self.run(self.db.customers)

        if rows is None:
            rows = []

        # Original column order:
        # ID, First Name, Last Name, National ID,
        # Phone, Email, Address, Active

        def is_active(value):
            if isinstance(value, str):
                return value.strip().lower() in (
                    "true", "1", "yes"
                )
            return bool(value)

        total_customers = len(rows)
        active_customers = sum(
            1 for row in rows if is_active(row[7])
        )

        # ====================================================
        # OVERVIEW HEADER
        # ====================================================

        overview = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )
        overview.pack(
            fill="x",
            padx=27,
            pady=(5, 12)
        )

        ctk.CTkLabel(
            overview,
            text="Customer Overview",
            font=("Arial", 19, "bold"),
            text_color=colors["text"],
            anchor="w"
        ).pack(
            fill="x",
            pady=(0, 12)
        )

        # ====================================================
        # CUSTOMER STATISTICS
        # ====================================================

        metrics = ctk.CTkFrame(
            overview,
            fg_color="transparent"
        )
        metrics.pack(fill="x")

        for column in range(3):
            metrics.grid_columnconfigure(
                column,
                weight=1,
                uniform="customer_metrics"
            )

        metric_items = (
            (
                "TOTAL CUSTOMERS",
                str(total_customers),
                "#93C5FD"
            ),
            (
                "ACTIVE CUSTOMERS",
                str(active_customers),
                colors["green"]
            ),
            (
                "INACTIVE CUSTOMERS",
                str(total_customers - active_customers),
                colors["red"]
            )
        )

        metric_labels = []

        for index, (title, value, value_color) in enumerate(
            metric_items
        ):
            card = ctk.CTkFrame(
                metrics,
                fg_color=colors["panel"],
                corner_radius=16,
                border_width=1,
                border_color=colors["border"]
            )

            card.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=5
            )

            ctk.CTkLabel(
                card,
                text=title,
                font=("Arial", 11, "bold"),
                text_color=colors["muted"],
                anchor="w"
            ).pack(
                fill="x",
                padx=20,
                pady=(18, 7)
            )

            value_label = ctk.CTkLabel(
                card,
                text=value,
                font=("Arial", 27, "bold"),
                text_color=value_color,
                anchor="w"
            )
            value_label.pack(
                fill="x",
                padx=20,
                pady=(0, 18)
            )

            metric_labels.append(value_label)

        # ====================================================
        # CUSTOMER DIRECTORY TOOLBAR
        # ====================================================

        toolbar = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )
        toolbar.pack(
            fill="x",
            padx=32,
            pady=(8, 13)
        )

        title_area = ctk.CTkFrame(
            toolbar,
            fg_color="transparent"
        )
        title_area.pack(side="left")

        ctk.CTkLabel(
            title_area,
            text="Registered Customers",
            font=("Arial", 18, "bold"),
            text_color=colors["text"],
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_area,
            text="View Only  |  Customer Directory",
            font=("Arial", 11),
            text_color=colors["muted"],
            anchor="w"
        ).pack(
            anchor="w",
            pady=(5, 0)
        )

        # ====================================================
        # DARK CUSTOMER TABLE CONTAINER
        # ====================================================

        table_holder = ctk.CTkFrame(
            page,
            fg_color=colors["panel"],
            corner_radius=16,
            border_width=1,
            border_color=colors["border"]
        )
        table_holder.pack(
            fill="both",
            expand=True,
            padx=27,
            pady=(0, 16)
        )

        table_area = ctk.CTkFrame(
            table_holder,
            fg_color=colors["panel"]
        )
        table_area.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=12
        )

        # ====================================================
        # WINDOWS DARK TREEVIEW THEME
        # ====================================================

        style = ttk.Style()
        previous_theme = style.theme_use()

        # The clam theme supports custom Treeview colors
        # more reliably on Windows.
        if previous_theme != "clam":
            style.theme_use("clam")

        def restore_theme(event):
            if event.widget is table_holder:
                current_style = ttk.Style()

                if current_style.theme_use() != previous_theme:
                    current_style.theme_use(previous_theme)

        table_holder.bind(
            "<Destroy>",
            restore_theme,
            add="+"
        )

        # Dedicated style: does not modify Bank.Treeview.

        style.configure(
            "AdminCustomers.Treeview",
            background=colors["panel"],
            fieldbackground=colors["panel"],
            foreground=colors["text"],
            rowheight=43,
            font=("Arial", 11),
            borderwidth=0,
            relief="flat"
        )

        style.configure(
            "AdminCustomers.Treeview.Heading",
            background=colors["header"],
            foreground="#FFFFFF",
            font=("Arial", 11, "bold"),
            padding=(12, 13),
            borderwidth=0,
            relief="flat"
        )

        style.map(
            "AdminCustomers.Treeview",
            background=[
                ("selected", colors["blue"])
            ],
            foreground=[
                ("selected", "#FFFFFF")
            ]
        )

        style.map(
            "AdminCustomers.Treeview.Heading",
            background=[
                ("active", "#2D4669"),
                ("pressed", colors["header"])
            ],
            foreground=[
                ("active", "#FFFFFF")
            ]
        )

        # ====================================================
        # DARK SCROLLBARS
        # ====================================================

        style.configure(
            "AdminCustomers.Vertical.TScrollbar",
            background="#304B70",
            troughcolor="#111F35",
            arrowcolor="#FFFFFF",
            bordercolor="#17263F",
            lightcolor="#304B70",
            darkcolor="#304B70",
            gripcount=0,
            borderwidth=0,
            relief="flat",
            width=13
        )

        style.map(
            "AdminCustomers.Vertical.TScrollbar",
            background=[
                ("active", "#456B9B"),
                ("pressed", "#3478F6")
            ]
        )

        style.configure(
            "AdminCustomers.Horizontal.TScrollbar",
            background="#304B70",
            troughcolor="#111F35",
            arrowcolor="#FFFFFF",
            bordercolor="#17263F",
            lightcolor="#304B70",
            darkcolor="#304B70",
            gripcount=0,
            borderwidth=0,
            relief="flat",
            width=13
        )

        style.map(
            "AdminCustomers.Horizontal.TScrollbar",
            background=[
                ("active", "#456B9B"),
                ("pressed", "#3478F6")
            ]
        )

        # ====================================================
        # CUSTOMER TABLE - ALL ORIGINAL COLUMNS
        # ====================================================

        columns = (
            "id",
            "first",
            "last",
            "nid",
            "phone",
            "email",
            "address",
            "active"
        )

        tree = ttk.Treeview(
            table_area,
            columns=columns,
            show="headings",
            style="AdminCustomers.Treeview",
            selectmode="browse"
        )

        column_specs = (
            ("id", "ID", 65),
            ("first", "First Name", 140),
            ("last", "Last Name", 140),
            ("nid", "National ID", 155),
            ("phone", "Phone", 155),
            ("email", "Email", 240),
            ("address", "Address", 240),
            ("active", "Active", 110)
        )


        for key, heading, width in column_specs:
            tree.heading(
                key,
                text=heading
            )

            tree.column(
                key,
                width=width,
                minwidth=70,
                anchor=(
                    "w"
                    if key in (
                        "first", "last", "email", "address"
                    )
                    else "center"
                ),
                stretch=True
            )

        # ====================================================
        # SCROLLBARS
        # ====================================================

        yscroll = ttk.Scrollbar(
            table_area,
            orient="vertical",
            command=tree.yview,
            style="AdminCustomers.Vertical.TScrollbar"
        )

        xscroll = ttk.Scrollbar(
            table_area,
            orient="horizontal",
            command=tree.xview,
            style="AdminCustomers.Horizontal.TScrollbar"
        )

        tree.configure(
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set
        )

        yscroll.pack(
            side="right",
            fill="y"
        )

        xscroll.pack(
            side="bottom",
            fill="x"
        )

        tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        # ====================================================
        # CUSTOMER STATUS AND ROW COLORS
        # ====================================================

        tree.tag_configure(
            "active_even",
            background="#17263F",
            foreground="#F5F8FF"
        )

        tree.tag_configure(
            "active_odd",
            background="#1C2D48",
            foreground="#F5F8FF"
        )

        tree.tag_configure(
            "inactive_even",
            background="#17263F",
            foreground="#FCA5A5"
        )

        tree.tag_configure(
            "inactive_odd",
            background="#1C2D48",
            foreground="#FCA5A5"
        )

        # ====================================================
        # POPULATE CUSTOMER TABLE
        # ====================================================

        def populate_customers(customer_rows):
            tree.delete(*tree.get_children())

            for index, row in enumerate(customer_rows):
                active = is_active(row[7])

                status = "Active" if active else "Inactive"

                tag = (
                    ("active_" if active else "inactive_")
                    + ("even" if index % 2 == 0 else "odd")
                )

                tree.insert(
                    "",
                    "end",
                    values=(
                        "" if row[0] is None else str(row[0]),
                        "" if row[1] is None else str(row[1]),
                        "" if row[2] is None else str(row[2]),
                        "" if row[3] is None else str(row[3]),
                        "" if row[4] is None else str(row[4]),
                        "" if row[5] is None else str(row[5]),
                        "" if row[6] is None else str(row[6]),
                        status
                    ),
                    tags=(tag,)
                )

        populate_customers(rows)

        # ====================================================
        # EMPTY CUSTOMER STATE
        # ====================================================

        empty_state = ctk.CTkFrame(
            table_holder,
            width=420,
            height=180,
            fg_color=colors["panel"],
            corner_radius=14,
            border_width=1,
            border_color=colors["border"]
        )
        empty_state.pack_propagate(False)

        ctk.CTkLabel(
            empty_state,
            text="No customers found",
            font=("Arial", 21, "bold"),
            text_color=colors["text"]
        ).pack(
            pady=(48, 10)
        )

        ctk.CTkLabel(
            empty_state,
            text="Registered customers will appear here.",
            font=("Arial", 12),
            text_color=colors["muted"]
        ).pack()

        def update_empty_state(customer_rows):
            if customer_rows:
                empty_state.place_forget()
            else:
                empty_state.place(
                    relx=0.5,
                    rely=0.53,
                    anchor="center"
                )

        update_empty_state(rows)

        # ====================================================
        # REFRESH - ORIGINAL DATABASE FUNCTION PRESERVED
        # ====================================================

        def refresh_customers():
            updated_rows = self.run(self.db.customers)

            if updated_rows is None:
                return

            populate_customers(updated_rows)
            update_empty_state(updated_rows)

            updated_total = len(updated_rows)
            updated_active = sum(
                1 for row in updated_rows
                if is_active(row[7])
            )

            metric_labels[0].configure(
                text=str(updated_total)
            )

            metric_labels[1].configure(
                text=str(updated_active)
            )

            metric_labels[2].configure(
                text=str(updated_total - updated_active)
            )

        ctk.CTkButton(
            toolbar,
            text="Refresh",
            command=refresh_customers,
            width=130,
            height=43,
            corner_radius=11,
            fg_color=colors["blue"],
            hover_color=BLUE_HOVER,
            text_color="#FFFFFF",
            font=("Arial", 12, "bold")
        ).pack(
            side="right"
        )

    # ============================================================
    # ACCOUNT TYPE SELECTION
    # ============================================================

    def show_account_type_selection(self):
        session = self.db.require_login()

        if session["role"] != "Customer":
            raise PermissionError(
                "Only customers can create accounts."
            )

        page = self.page("Choose Account Type")

        ctk.CTkLabel(
            page,
            text="What would you like to open?",
            font=("Arial", 20, "bold"),
            text_color=WHITE
        ).pack(pady=(15, 8))

        ctk.CTkLabel(
            page,
            text="Select one of the available banking products.",
            text_color=MUTED
        ).pack(pady=(0, 25))

        options_frame = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )
        options_frame.pack(
            fill="x",
            padx=25,
            pady=15
        )

        # BANK ACCOUNT OPTION
        bank_frame = ctk.CTkFrame(
            options_frame,
            fg_color=CARD,
            corner_radius=15
        )
        bank_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=10
        )

        ctk.CTkLabel(
            bank_frame,
            text="BANK ACCOUNT",
            font=("Arial", 20, "bold"),
            text_color=WHITE
        ).pack(pady=(25, 10))

        ctk.CTkLabel(
            bank_frame,
            text=(
                "Create a checking account.\n"
                "Deposit and withdraw money.\n"
                "Send and receive transfers."
            ),
            text_color=MUTED,
            justify="center"
        ).pack(pady=10)

        self.button(
            bank_frame,
            "Select Bank Account",
            self.show_bank_account_creation
        ).pack(pady=(15, 25))

        # CREDIT CARD OPTION
        credit_frame = ctk.CTkFrame(
            options_frame,
            fg_color=CARD,
            corner_radius=15
        )
        credit_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=10
        )

        ctk.CTkLabel(
            credit_frame,
            text="CREDIT CARD",
            font=("Arial", 20, "bold"),
            text_color=WHITE
        ).pack(pady=(25, 10))

        ctk.CTkLabel(
            credit_frame,
            text=(
                "Apply for a credit card.\n"
                "Request a credit limit.\n"
                "Manage future card payments."
            ),
            text_color=MUTED,
            justify="center"
        ).pack(pady=10)

        self.button(
            credit_frame,
            "Select Credit Card",
            self.show_credit_card_application
        ).pack(pady=(15, 25))

        self.button(
            page,
            "Back to My Accounts",
            self.show_accounts
        ).pack(pady=20)

    # ============================================================
    # BANK ACCOUNT CREATION
    # ============================================================

    def show_bank_account_creation(self):
        session = self.db.require_login()

        if session["role"] != "Customer":
            raise PermissionError(
                "Only customers can create bank accounts."
            )

        page = self.page("Open Bank Account")

        form = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=15
        )
        form.pack(
            fill="x",
            padx=25,
            pady=15
        )

        ctk.CTkLabel(
            form,
            text="Bank Account Information",
            font=("Arial", 19, "bold"),
            text_color=WHITE
        ).pack(pady=(20, 15))

        ctk.CTkLabel(
            form,
            text="Account Type: Checking",
            text_color=WHITE
        ).pack(pady=6)

        ctk.CTkLabel(
            form,
            text="Currency: TRY",
            text_color=WHITE
        ).pack(pady=6)

        ctk.CTkLabel(
            form,
            text="Opening Balance: 0.00 TRY",
            text_color=WHITE
        ).pack(pady=6)

        ctk.CTkLabel(
            form,
            text="Your account number will be generated automatically.",
            text_color=MUTED
        ).pack(pady=(10, 20))

        def create_bank_account():
            def action():
                confirmed = self.ask_yes_no(
                    "Confirm Account Creation",
                    "Do you want to create a new bank account?"
                )

                if not confirmed:
                    return

                account_id = self.db.add_account(
                    session["customer_id"]
                )

                self.show_ok(
                    "Account Created",
                    (
                        "Your bank account was created successfully.\n"
                        f"Account ID: {account_id}\n"
                        "Opening Balance: 0.00 TRY"
                    )
                )

                self.show_accounts()

            self.run(action)

        self.button(
            form,
            "Create Bank Account",
            create_bank_account
        ).pack(pady=(0, 25))

        self.button(
            page,
            "Back",
            self.show_account_type_selection
        ).pack(pady=10)


    # ============================================================
    # CUSTOMER CREDIT CARD APPLICATION
    # ============================================================

    def show_credit_card_application(self):
        session = self.db.require_login()

        if session["role"] != "Customer":
            raise PermissionError(
                "Only customers can apply for credit cards."
            )

        page = self.page("Credit Card Application")

        form = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=15
        )

        form.pack(
            fill="x",
            padx=25,
            pady=15
        )

        ctk.CTkLabel(
            form,
            text="Credit Card Application",
            font=("Arial", 20, "bold"),
            text_color=WHITE
        ).pack(pady=(20, 15))

        ctk.CTkLabel(
            form,
            text="Card Type",
            text_color=WHITE
        ).pack(pady=(10, 5))

        card_type = ctk.CTkComboBox(
            form,
            values=["Standard", "Gold"],
            width=300,
            state="readonly"
        )

        card_type.pack(pady=5)
        card_type.set("Standard")

        ctk.CTkLabel(
            form,
            text="Requested Credit Limit",
            text_color=WHITE
        ).pack(pady=(15, 5))

        credit_limit = ctk.CTkComboBox(
            form,
            values=[
                "5000",
                "10000",
                "25000",
                "50000"
            ],
            width=300,
            state="readonly"
        )

        credit_limit.pack(pady=5)
        credit_limit.set("10000")

        ctk.CTkLabel(
            form,
            text="Currency: TRY",
            text_color=MUTED
        ).pack(pady=15)

        ctk.CTkLabel(
            form,
            text=(
                "Your application will be reviewed "
                "by an administrator.\n"
                "Submitting an application does not "
                "guarantee approval."
            ),
            text_color=MUTED,
            justify="center"
        ).pack(pady=15)

        def submit_application():

            def action():
                selected_type = card_type.get()
                selected_limit = credit_limit.get()

                confirmed = self.ask_yes_no(
                    "Confirm Application",
                    (
                        f"Card Type: {selected_type}\n"
                        f"Requested Limit: "
                        f"{selected_limit} TRY\n\n"
                        "Submit this application?"
                    )
                )

                if not confirmed:
                    return

                application_id = (
                    self.db.apply_for_credit_card(
                        selected_type,
                        selected_limit
                    )
                )

                self.show_ok(
                    "Application Submitted",
                    (
                        "Application submitted successfully.\n"
                        f"Application ID: {application_id}\n"
                        "Status: Pending"
                    )
                )

                self.show_my_credit_cards()

            self.run(action)

        self.button(
            form,
            "Submit Application",
            submit_application
        ).pack(pady=(5, 25))

        self.button(
            page,
            "Back",
            self.show_account_type_selection
        ).pack(pady=10)

    # ============================================================
    # ADMIN: CREDIT CARD APPLICATIONS
    # ============================================================


    def show_admin_credit_card_applications(self):
        session = self.db.require_login()

        if session["role"] != "Admin":
            raise PermissionError("Admin access required.")

        page = self.page("Credit Card Applications")

        ctk.CTkLabel(
            page,
            text="Credit Card Application Management",
            font=("Arial", 20, "bold"),
            text_color=WHITE
        ).pack(pady=(10, 5))

        rows = self.db.admin_credit_card_applications()

        columns = (
            "application_id",
            "customer_id",
            "card_type",
            "requested_limit",
            "status",
            "applied_at"
        )

        headings = (
            "Application ID",
            "Customer ID",
            "Card Type",
            "Requested Limit",
            "Status",
            "Applied At"
        )

        # ====================================================
        # DARK TABLE THEME
        # ====================================================

        style = ttk.Style()
        previous_theme = style.theme_use()

        if previous_theme != "clam":
            style.theme_use("clam")

        style.configure(
            "CreditApplications.Treeview",
            background="#17263F",
            fieldbackground="#17263F",
            foreground="#F5F8FF",
            rowheight=36,
            font=("Arial", 11),
            borderwidth=0,
            relief="flat"
        )

        style.configure(
            "CreditApplications.Treeview.Heading",
            background="#243A59",
            foreground="#FFFFFF",
            font=("Arial", 11, "bold"),
            padding=(10, 9),
            borderwidth=0,
            relief="flat"
        )

        style.map(
            "CreditApplications.Treeview",
            background=[
                ("selected", "#3478F6")
            ],
            foreground=[
                ("selected", "#FFFFFF")
            ]
        )

        style.map(
            "CreditApplications.Treeview.Heading",
            background=[
                ("active", "#304B70")
            ],
            foreground=[
                ("active", "#FFFFFF")
            ]
        )

        for orientation in ("Vertical", "Horizontal"):
            scrollbar_style = (
                f"CreditApplications.{orientation}.TScrollbar"
            )

            style.configure(
                scrollbar_style,
                background="#304B70",
                troughcolor="#111F35",
                arrowcolor="#FFFFFF",
                bordercolor="#17263F",
                lightcolor="#304B70",
                darkcolor="#304B70",
                borderwidth=0,
                relief="flat",
                width=13
            )

            style.map(
                scrollbar_style,
                background=[
                    ("active", "#456B9B"),
                    ("pressed", "#3478F6")
                ]
            )

        # ====================================================
        # APPLICATION TABLE
        # ====================================================

        tree = self.table(
            page,
            columns,
            headings
        )

        tree.configure(
            style="CreditApplications.Treeview"
        )

        # The shared table helper places both scrollbars
        # inside the same frame as the Treeview.
        table_frame = tree.master

        for widget in table_frame.winfo_children():
            if isinstance(widget, ttk.Scrollbar):
                orientation = str(widget.cget("orient"))

                widget.configure(
                    style=(
                        "CreditApplications.Vertical.TScrollbar"
                        if orientation == "vertical"
                        else "CreditApplications.Horizontal.TScrollbar"
                    )
                )

        # Restore the previous ttk theme when leaving
        # the Credit Card Applications page.
        # The shared page container is self.main, so use
        # the table widget's destruction as the trigger.

        def restore_credit_applications_theme(event):
            if event.widget is tree:
                current_style = ttk.Style()

                if current_style.theme_use() != previous_theme:
                    current_style.theme_use(previous_theme)

        tree.bind(
            "<Destroy>",
            restore_credit_applications_theme,
            add="+"
        )

        application_map = {}

        for row in rows:
            application_id = int(row[0])
            application_map[application_id] = row

            tree.insert(
                "",
                "end",
                iid=str(application_id),
                values=(
                    application_id,
                    row[1],
                    row[2],
                    f"{row[3]:.2f} TRY",
                    row[4],
                    str(row[5])[:19]
                )
            )

        # ====================================================
        # REVIEW FORM - ORIGINAL FUNCTIONALITY
        # ====================================================

        form = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=12
        )

        form.pack(
            fill="x",
            padx=18,
            pady=10
        )

        details = ctk.CTkLabel(
            form,
            text="Select an application from the table.",
            text_color=WHITE,
            justify="left"
        )

        details.pack(pady=(15, 10))

        ctk.CTkLabel(
            form,
            text="Linked Bank Account",
            text_color=WHITE
        ).pack(pady=(5, 5))

        account_combo = ctk.CTkComboBox(
            form,
            values=["Select an application"],
            width=350,
            state="readonly"
        )

        account_combo.pack(pady=5)
        account_combo.set("Select an application")
        account_combo.configure(state="disabled")

        ctk.CTkLabel(
            form,
            text="Rejection Reason",
            text_color=WHITE
        ).pack(pady=(10, 5))

        reason_entry = ctk.CTkEntry(
            form,
            width=350,
            placeholder_text="Required when rejecting"
        )

        reason_entry.pack(pady=5)
        reason_entry.configure(state="disabled")

        account_map = {}

        # ====================================================
        # GET SELECTED APPLICATION
        # ====================================================

        def get_selected():
            selection = tree.selection()

            if not selection:
                raise ValueError(
                    "Please select an application."
                )

            application_id = int(selection[0])

            return (
                application_id,
                application_map[application_id]
            )

        # ====================================================
        # UPDATE ACCOUNT COMBOBOX
        # ====================================================

        def set_account_options(values, enabled=False):
            account_combo.configure(state="normal")
            account_combo.configure(values=values)
            account_combo.set(values[0])

            account_combo.configure(
                state="readonly" if enabled else "disabled"
            )

        # ====================================================
        # SELECT APPLICATION
        # ====================================================

        def on_select(event=None):

            def action():
                nonlocal account_map

                account_map = {}

                approve_button.configure(state="disabled")
                reject_button.configure(state="disabled")

                reason_entry.configure(state="normal")
                reason_entry.delete(0, "end")
                reason_entry.configure(state="disabled")

                set_account_options(
                    ["Select an application"]
                )

                if not tree.selection():
                    details.configure(
                        text="Select an application from the table."
                    )
                    return

                application_id, row = get_selected()

                customer_id = int(row[1])
                status = str(row[4]).strip()

                details.configure(
                    text=(
                        f"Application ID: {application_id}\n"
                        f"Customer ID: {customer_id}\n"
                        f"Card Type: {row[2]}\n"
                        f"Requested Limit: {row[3]:.2f} TRY\n"
                        f"Status: {status}\n"
                        f"Review Note: {row[6] or '-'}"
                    )
                )

                # ============================================
                # PENDING APPLICATION
                # ============================================

                if status == "Pending":
                    accounts = (
                        self.db.admin_credit_card_accounts(
                            customer_id
                        )
                    )

                    for account in accounts:
                        account_id = int(account[0])

                        account_number = str(
                            account[1]
                        ).strip()

                        label = (
                            f"{account_number} "
                            f"(ID: {account_id})"
                        )

                        account_map[label] = account_id

                    labels = list(account_map.keys())

                    if labels:
                        set_account_options(
                            labels,
                            enabled=True
                        )

                        approve_button.configure(
                            state="normal"
                        )
                    else:
                        set_account_options(
                            ["No eligible bank accounts"]
                        )

                    reject_button.configure(
                        state="normal"
                    )

                    reason_entry.configure(
                        state="normal"
                    )

                # ============================================
                # APPROVED APPLICATION
                # ============================================

                elif status == "Approved":
                    account = (
                        self.db.admin_credit_card_linked_account(
                            application_id
                        )
                    )

                    if account is not None:
                        account_id = int(account[0])

                        account_number = str(
                            account[1]
                        ).strip()

                        is_active = bool(account[2])
                        is_frozen = bool(account[3])

                        if not is_active:
                            account_status = "Inactive"
                        elif is_frozen:
                            account_status = "Frozen"
                        else:
                            account_status = "Active"

                        label = (
                            f"{account_number} "
                            f"(ID: {account_id})"
                        )

                        set_account_options([label])

                        details.configure(
                            text=(
                                f"Application ID: {application_id}\n"
                                f"Customer ID: {customer_id}\n"
                                f"Card Type: {row[2]}\n"
                                f"Requested Limit: {row[3]:.2f} TRY\n"
                                f"Status: Approved\n"
                                f"Linked Account Status: "
                                f"{account_status}\n"
                                f"Review Note: {row[6] or '-'}"
                            )
                        )
                    else:
                        set_account_options(
                            ["Linked account not found"]
                        )

                # ============================================
                # REJECTED APPLICATION
                # ============================================

                elif status == "Rejected":
                    set_account_options(
                        ["Not applicable"]
                    )

                # ============================================
                # UNKNOWN APPLICATION STATUS
                # ============================================

                else:
                    set_account_options(
                        ["Unknown application status"]
                    )

            self.run(action)

        # ====================================================
        # APPROVE APPLICATION
        # ====================================================

        def approve():

            def action():
                application_id, row = get_selected()

                if str(row[4]).strip() != "Pending":
                    raise ValueError(
                        "Application already reviewed."
                    )

                selected_account = account_combo.get()

                if selected_account not in account_map:
                    raise ValueError(
                        "Select an eligible bank account."
                    )

                confirmed = self.ask_yes_no(
                    "Confirm Approval",
                    (
                        f"Application ID: {application_id}\n"
                        f"Customer ID: {row[1]}\n"
                        f"Card Type: {row[2]}\n"
                        f"Credit Limit: {row[3]:.2f} TRY\n"
                        f"Bank Account: {selected_account}\n\n"
                        "Approve this application?"
                    )
                )

                if not confirmed:
                    return

                credit_card_id = (
                    self.db.approve_credit_card_application(
                        application_id,
                        account_map[selected_account]
                    )
                )

                self.show_ok(
                    "Application Approved",
                    (
                        "Application approved successfully.\n"
                        f"Credit Card ID: {credit_card_id}"
                    )
                )

                self.show_admin_credit_card_applications()

            self.run(action)

        # ====================================================
        # REJECT APPLICATION
        # ====================================================

        def reject():

            def action():
                application_id, row = get_selected()

                if str(row[4]).strip() != "Pending":
                    raise ValueError(
                        "Application already reviewed."
                    )

                reason = reason_entry.get().strip()

                if not reason:
                    raise ValueError(
                        "Please enter a rejection reason."
                    )

                if len(reason) > 500:
                    raise ValueError(
                        "Rejection reason cannot exceed "
                        "500 characters."
                    )

                confirmed = self.ask_yes_no(
                    "Confirm Rejection",
                    (
                        f"Application ID: {application_id}\n\n"
                        "Reject this application?"
                    )
                )

                if not confirmed:
                    return

                self.db.reject_credit_card_application(
                    application_id,
                    reason
                )

                self.show_ok(
                    "Application Rejected",
                    "Application rejected successfully."
                )

                self.show_admin_credit_card_applications()

            self.run(action)

        # ====================================================
        # ACTION BUTTONS
        # ====================================================

        buttons = ctk.CTkFrame(
            form,
            fg_color="transparent"
        )

        buttons.pack(pady=(15, 20))

        approve_button = self.button(
            buttons,
            "Approve Application",
            approve,
            width=180
        )

        approve_button.pack(
            side="left",
            padx=8
        )

        approve_button.configure(
            state="disabled"
        )

        reject_button = self.button(
            buttons,
            "Reject Application",
            reject,
            width=180
        )

        reject_button.pack(
            side="left",
            padx=8
        )

        reject_button.configure(
            state="disabled"
        )

        # ====================================================
        # REFRESH APPLICATIONS
        # ====================================================

        self.button(
            page,
            "Refresh Applications",
            lambda: self.run(
                self.show_admin_credit_card_applications
            )
        ).pack(pady=10)

        # ====================================================
        # TABLE SELECTION EVENT
        # ====================================================

        tree.bind(
            "<<TreeviewSelect>>",
            on_select
        )


    # ============================================================
    # CUSTOMER: MY CREDIT CARDS
    # ============================================================

    def show_my_credit_cards(self):
        session = self.db.require_login()

        if session["role"] != "Customer":
            raise PermissionError(
                "Customer access required."
            )

        page = self.page("My Credit Cards")

        applications = (
            self.db.my_credit_card_applications()
        )

        cards = self.db.my_credit_cards()

        scroll = ctk.CTkScrollableFrame(
            page,
            fg_color="transparent",
            corner_radius=0
        )

        scroll.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 15)
        )

        # ====================================================
        # APPLICATIONS
        # ====================================================

        ctk.CTkLabel(
            scroll,
            text="My Credit Card Applications",
            font=("Arial", 18, "bold"),
            text_color=WHITE
        ).pack(pady=(10, 5))

        application_tree = self.table(
            scroll,
            (
                "id",
                "type",
                "limit",
                "status",
                "date",
                "note"
            ),
            (
                "Application ID",
                "Card Type",
                "Requested Limit",
                "Status",
                "Applied At",
                "Review Note"
            )
        )

        application_tree.configure(height=4)

        for row in applications:
            application_tree.insert(
                "",
                "end",
                values=(
                    row[0],
                    row[1],
                    f"{row[2]:.2f} TRY",
                    row[3],
                    str(row[4])[:19],
                    row[6] or "-"
                )
            )

        # ====================================================
        # APPLICATION ACTIONS
        # ====================================================

        application_actions = ctk.CTkFrame(
            scroll,
            fg_color="transparent"
        )

        application_actions.pack(
            fill="x",
            padx=20,
            pady=(5, 12)
        )

        self.button(
            application_actions,
            "Apply for Credit Card",
            self.show_credit_card_application,
            width=210
        ).pack(
            side="left",
            padx=(0, 10)
        )

        self.button(
            application_actions,
            "Refresh",
            lambda: self.run(
                self.show_my_credit_cards
            ),
            width=130
        ).pack(side="right")

        # ====================================================
        # CREDIT CARD SUMMARY
        # ====================================================

        total_limit = sum(
            (
                Decimal(str(row[2]))
                for row in cards
                if str(row[5]).strip() == "Active"
            ),
            Decimal("0.00")
        )

        total_outstanding = sum(
            (
                Decimal(str(row[3]))
                for row in cards
            ),
            Decimal("0.00")
        )

        total_available = sum(
            (
                Decimal(str(row[2]))
                - Decimal(str(row[3]))
                for row in cards
                if str(row[5]).strip() == "Active"
            ),
            Decimal("0.00")
        )

        summary = ctk.CTkFrame(
            scroll,
            fg_color="transparent"
        )

        summary.pack(
            fill="x",
            padx=20,
            pady=(10, 12)
        )

        for column in range(3):
            summary.grid_columnconfigure(
                column,
                weight=1,
                uniform="credit_summary"
            )

        summary_items = [
            (
                "Total Credit Limit",
                total_limit,
                WHITE
            ),
            (
                "Outstanding Debt",
                total_outstanding,
                "#FCA5A5"
            ),
            (
                "Available Credit Limit",
                total_available,
                "#4ADE80"
            )
        ]

        for index, (
            title,
            amount,
            color
        ) in enumerate(summary_items):

            summary_card = ctk.CTkFrame(
                summary,
                fg_color=CARD,
                corner_radius=14
            )

            summary_card.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=5,
                pady=5
            )

            ctk.CTkLabel(
                summary_card,
                text=title,
                font=("Arial", 12),
                text_color=MUTED,
                anchor="w"
            ).pack(
                fill="x",
                padx=18,
                pady=(18, 8)
            )

            ctk.CTkLabel(
                summary_card,
                text=f"{amount:,.2f} TRY",
                font=("Arial", 21, "bold"),
                text_color=color,
                anchor="w"
            ).pack(
                fill="x",
                padx=18,
                pady=(0, 18)
            )

        # ====================================================
        # APPROVED CREDIT CARDS
        # ====================================================

        ctk.CTkLabel(
            scroll,
            text="My Approved Credit Cards",
            font=("Arial", 18, "bold"),
            text_color=WHITE
        ).pack(pady=(12, 5))

        card_tree = self.table(
            scroll,
            (
                "id",
                "type",
                "number",
                "limit",
                "balance",
                "available",
                "status"
            ),
            (
                "Card ID",
                "Card Type",
                "Card Number",
                "Credit Limit",
                "Outstanding",
                "Available Limit",
                "Status"
            )
        )

        card_tree.configure(
            height=4,
            selectmode="browse"
        )

        card_map = {}

        for row in cards:
            card_id = int(row[0])

            card_map[card_id] = row

            credit_limit = Decimal(str(row[2]))
            outstanding = Decimal(str(row[3]))
            available = credit_limit - outstanding

            card_number = str(row[7]).strip()

            masked_number = (
                "**** **** **** " + card_number[-4:]
            )

            card_tree.insert(
                "",
                "end",
                iid=str(card_id),
                values=(
                    card_id,
                    row[1],
                    masked_number,
                    f"{credit_limit:,.2f} TRY",
                    f"{outstanding:,.2f} TRY",
                    f"{available:,.2f} TRY",
                    row[5]
                )
            )

        # ====================================================
        # CREDIT CARD OPERATIONS
        # ====================================================

        operation_frame = ctk.CTkFrame(
            scroll,
            fg_color=CARD,
            corner_radius=14
        )

        operation_frame.pack(
            fill="x",
            padx=20,
            pady=(10, 15)
        )

        ctk.CTkLabel(
            operation_frame,
            text="Credit Card Operations",
            font=("Arial", 18, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(
            fill="x",
            padx=22,
            pady=(18, 8)
        )

        selected_details = ctk.CTkLabel(
            operation_frame,
            text="Select a credit card from the table.",
            font=("Arial", 13),
            text_color=MUTED,
            justify="left",
            anchor="w"
        )

        selected_details.pack(
            fill="x",
            padx=22,
            pady=(0, 15)
        )

        # ====================================================
        # AMOUNT AND DESCRIPTION
        # ====================================================

        input_frame = ctk.CTkFrame(
            operation_frame,
            fg_color="transparent"
        )

        input_frame.pack(
            fill="x",
            padx=22,
            pady=8
        )

        input_frame.grid_columnconfigure(
            0,
            weight=1
        )

        input_frame.grid_columnconfigure(
            1,
            weight=2
        )

        ctk.CTkLabel(
            input_frame,
            text="Amount (TRY)",
            text_color=WHITE,
            anchor="w"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=5,
            pady=(0, 5)
        )

        ctk.CTkLabel(
            input_frame,
            text="Description",
            text_color=WHITE,
            anchor="w"
        ).grid(
            row=0,
            column=1,
            sticky="w",
            padx=5,
            pady=(0, 5)
        )

        amount_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter amount",
            height=42,
            corner_radius=9
        )

        amount_entry.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=5
        )

        description_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Optional description",
            height=42,
            corner_radius=9
        )

        description_entry.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=5
        )

        # ====================================================
        # GET SELECTED CREDIT CARD
        # ====================================================

        def get_selected_card():
            selection = card_tree.selection()

            if not selection:
                raise ValueError(
                    "Please select a credit card."
                )

            card_id = int(selection[0])

            return (
                card_id,
                card_map[card_id]
            )

        # ====================================================
        # EXECUTE CREDIT CARD TRANSACTION
        # ====================================================

        def execute_transaction(kind):

            def action():

                card_id, row = get_selected_card()

                status = str(row[5]).strip()

                if status != "Active":
                    raise ValueError(
                        "This credit card is not active."
                    )

                amount = (
                    self.db._validate_credit_card_amount(
                        amount_entry.get()
                    )
                )

                description = (
                    description_entry.get().strip()
                )

                if len(description) > 250:
                    raise ValueError(
                        "Description cannot exceed "
                        "250 characters."
                    )

                credit_limit = Decimal(str(row[2]))
                outstanding = Decimal(str(row[3]))
                available = credit_limit - outstanding

                card_number = str(row[7]).strip()

                masked_number = (
                    "**** **** **** "
                    + card_number[-4:]
                )

                # ============================================
                # PURCHASE
                # ============================================

                if kind == "Purchase":

                    if amount > available:
                        raise ValueError(
                            "Insufficient available "
                            "credit limit."
                        )

                    operation_title = "Credit Card Purchase"

                    operation_message = (
                        "This amount will be added "
                        "to your credit card debt."
                    )

                # ============================================
                # CASH ADVANCE
                # ============================================

                elif kind == "CashAdvance":

                    if amount > available:
                        raise ValueError(
                            "Insufficient available "
                            "credit limit."
                        )

                    operation_title = "Cash Advance"

                    operation_message = (
                        "This amount will be transferred "
                        "to your linked bank account and "
                        "added to your credit card debt."
                    )

                # ============================================
                # PAY CREDIT CARD DEBT
                # ============================================

                elif kind == "Payment":

                    if outstanding <= 0:
                        raise ValueError(
                            "This credit card has "
                            "no outstanding debt."
                        )

                    if amount > outstanding:
                        raise ValueError(
                            "Payment cannot exceed "
                            "the outstanding debt."
                        )

                    operation_title = (
                        "Pay Credit Card Debt"
                    )

                    operation_message = (
                        "This amount will be deducted "
                        "from your linked bank account "
                        "and reduce your credit card debt."
                    )

                else:
                    raise ValueError(
                        "Invalid credit card operation."
                    )

                # ============================================
                # CONFIRM TRANSACTION
                # ============================================

                confirmed = self.ask_yes_no(
                    "Confirm Transaction",
                    (
                        f"Operation: {operation_title}\n"
                        f"Card: {masked_number}\n"
                        f"Amount: {amount:,.2f} TRY\n\n"
                        f"{operation_message}\n\n"
                        "Do you want to continue?"
                    )
                )

                if not confirmed:
                    return

                # ============================================
                # CALL BACKEND
                # ============================================


                try:
                    transaction_id = (
                        self.db.credit_card_transact(
                            kind,
                            card_id,
                            amount,
                            description
                        )
                    )

                except Exception as error:
                    error_text = str(error).lower()

                    if (
                        kind == "Payment"
                        and (
                            "51118" in error_text
                            or "insufficient bank account balance"
                            in error_text
                        )
                    ):
                        self.show_ok(
                            "Insufficient Balance",
                            (
                                "Your linked bank account does not "
                                "have sufficient funds to complete "
                                "this credit card payment.\n\n"
                                "Please check your account balance "
                                "and try again."
                            )
                        )
                        return

                    raise


                self.show_ok(
                    "Transaction Successful",
                    (
                        f"{operation_title} completed "
                        "successfully.\n\n"
                        f"Transaction ID: {transaction_id}\n"
                        f"Amount: {amount:,.2f} TRY"
                    )
                )

                # ============================================
                # REFRESH CREDIT CARDS
                # ============================================

                self.show_my_credit_cards()

            self.run(action)

        # ====================================================
        # OPERATION BUTTONS
        # ====================================================

        buttons = ctk.CTkFrame(
            operation_frame,
            fg_color="transparent"
        )

        buttons.pack(
            fill="x",
            padx=22,
            pady=(12, 15)
        )

        for column in range(3):
            buttons.grid_columnconfigure(
                column,
                weight=1,
                uniform="card_operations"
            )

        purchase_button = self.button(
            buttons,
            "Purchase",
            lambda: execute_transaction(
                "Purchase"
            ),
            width=150
        )

        purchase_button.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=5,
            pady=5
        )

        cash_advance_button = self.button(
            buttons,
            "Cash Advance",
            lambda: execute_transaction(
                "CashAdvance"
            ),
            width=150
        )

        cash_advance_button.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=5,
            pady=5
        )

        payment_button = self.button(
            buttons,
            "Pay Credit Card Debt",
            lambda: execute_transaction(
                "Payment"
            ),
            width=190
        )

        payment_button.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=5,
            pady=5
        )

        operation_buttons = (
            purchase_button,
            cash_advance_button,
            payment_button
        )

        for button in operation_buttons:
            button.configure(state="disabled")

        # ====================================================
        # SECURITY INFORMATION
        # ====================================================

        ctk.CTkLabel(
            operation_frame,
            text=(
                "Cash advances and debt payments use "
                "your linked bank account. All operations "
                "are subject to account status, available "
                "balance and security restrictions."
            ),
            font=("Arial", 12),
            text_color=MUTED,
            justify="left",
            anchor="w",
            wraplength=700
        ).pack(
            fill="x",
            padx=22,
            pady=(0, 18)
        )

        # ====================================================
        # CREDIT CARD TRANSACTION HISTORY
        # ====================================================

        ctk.CTkLabel(
            scroll,
            text="Credit Card Transaction History",
            font=("Arial", 18, "bold"),
            text_color=WHITE
        ).pack(pady=(10, 5))

        history_filter = ctk.CTkFrame(
            scroll,
            fg_color="transparent"
        )

        history_filter.pack(
            fill="x",
            padx=20,
            pady=5
        )

        history_title = ctk.CTkLabel(
            history_filter,
            text="Showing transactions for all credit cards",
            font=("Arial", 12),
            text_color=MUTED
        )

        history_title.pack(side="left")

        history_tree = self.table(
            scroll,
            (
                "id",
                "card_id",
                "card_type",
                "card_number",
                "type",
                "amount",
                "description",
                "status",
                "date"
            ),
            (
                "Transaction ID",
                "Card ID",
                "Card Type",
                "Card Number",
                "Transaction Type",
                "Amount",
                "Description",
                "Status",
                "Date"
            )
        )

        history_tree.configure(height=7)

        # ====================================================
        # REFRESH TRANSACTION HISTORY
        # ====================================================

        def refresh_history(
            credit_card_id=None
        ):

            rows = (
                self.db.my_credit_card_transactions(
                    credit_card_id
                )
            )

            history_tree.delete(
                *history_tree.get_children()
            )

            type_labels = {
                "Purchase": "Purchase",
                "CashAdvance": "Cash Advance",
                "Payment": "Debt Payment",
                "Refund": "Refund"
            }

            for row in rows:

                transaction_type = str(
                    row[4]
                ).strip()

                display_type = type_labels.get(
                    transaction_type,
                    transaction_type
                )

                history_tree.insert(
                    "",
                    "end",
                    values=(
                        row[0],
                        row[1],
                        row[2],
                        "**** " + str(row[3])[-4:],
                        display_type,
                        f"{row[5]:,.2f} TRY",
                        row[6] or "-",
                        row[7],
                        str(row[8])[:19]
                    )
                )

            if credit_card_id is None:

                history_title.configure(
                    text=(
                        "Showing transactions "
                        "for all credit cards"
                    )
                )

            else:

                history_title.configure(
                    text=(
                        "Showing transactions "
                        f"for Card ID: {credit_card_id}"
                    )
                )

        self.button(
            history_filter,
            "Show All Transactions",
            lambda: self.run(refresh_history),
            width=190
        ).pack(side="right")

        # ====================================================
        # CREDIT CARD SELECTION EVENT
        # ====================================================

        def on_card_select(event=None):

            def action():

                for button in operation_buttons:
                    button.configure(
                        state="disabled"
                    )

                if not card_tree.selection():

                    selected_details.configure(
                        text=(
                            "Select a credit card "
                            "from the table."
                        )
                    )

                    refresh_history()

                    return

                card_id, row = get_selected_card()

                credit_limit = Decimal(
                    str(row[2])
                )

                outstanding = Decimal(
                    str(row[3])
                )

                available = (
                    credit_limit - outstanding
                )

                status = str(row[5]).strip()

                card_number = str(
                    row[7]
                ).strip()

                selected_details.configure(
                    text=(
                        f"Selected Card: {row[1]}  |  "
                        f"**** **** **** {card_number[-4:]}\n"
                        f"Status: {status}  |  "
                        f"Expires: {row[6]}\n"
                        f"Credit Limit: "
                        f"{credit_limit:,.2f} TRY\n"
                        f"Outstanding Debt: "
                        f"{outstanding:,.2f} TRY\n"
                        f"Available Limit: "
                        f"{available:,.2f} TRY"
                    )
                )

                amount_entry.delete(0, "end")
                description_entry.delete(0, "end")

                if status == "Active":

                    if available > 0:

                        purchase_button.configure(
                            state="normal"
                        )

                        cash_advance_button.configure(
                            state="normal"
                        )

                    if outstanding > 0:

                        payment_button.configure(
                            state="normal"
                        )

                refresh_history(card_id)

            self.run(action)

        card_tree.bind(
            "<<TreeviewSelect>>",
            on_card_select
        )

        # ====================================================
        # INITIAL TRANSACTION HISTORY
        # ====================================================

        refresh_history()

    # ============================================================
    # ACCOUNT MANAGEMENT - ADMIN / CUSTOMER
    # ============================================================

    def show_accounts(self):
        session = self.db.require_login()
        is_admin = session["role"] == "Admin"

        page = self.page(
            "Account Management" if is_admin else "My Accounts"
        )

        rows = self.db.accounts()

        def account_status(is_active, is_frozen):
            if not bool(is_active):
                return "Inactive"

            if bool(is_frozen):
                return "Frozen"

            return "Active"

        def configure_status_colors(tree):
            tree.tag_configure(
                "Frozen",
                foreground="#DC2626"
            )

            tree.tag_configure(
                "Active",
                foreground="#15803D"
            )

            tree.tag_configure(
                "Inactive",
                foreground="#64748B"
            )

        def require_account_admin():
            current_session = self.db.require_login()

            if current_session["role"] != "Admin":
                raise PermissionError(
                    "Only bank administrators can manage "
                    "account security restrictions."
                )

        # ====================================================
        # ADMIN ACCOUNT MANAGEMENT
        # ====================================================


        if is_admin:
            # ====================================================
            # ADMIN ACCOUNT MANAGEMENT - PREMIUM DARK DESIGN
            # ====================================================

            colors = {
                "panel": "#17263F",
                "header": "#243A59",
                "border": "#2B4161",
                "text": "#F5F8FF",
                "muted": "#9EB2D0",
                "blue": "#3478F6",
                "green": "#4ADE80",
                "red": "#FCA5A5",
                "amber": "#FBBF24"
            }

            # ====================================================
            # ACCOUNT OVERVIEW
            # ====================================================

            total_count = len(rows)
            active_count = sum(
                1 for row in rows
                if account_status(row[6], row[7]) == "Active"
            )
            frozen_count = sum(
                1 for row in rows
                if account_status(row[6], row[7]) == "Frozen"
            )

            overview = ctk.CTkFrame(
                page,
                fg_color="transparent"
            )
            overview.pack(
                fill="x",
                padx=27,
                pady=(4, 12)
            )

            ctk.CTkLabel(
                overview,
                text="Account Overview",
                font=("Arial", 19, "bold"),
                text_color=colors["text"],
                anchor="w"
            ).pack(
                fill="x",
                pady=(0, 12)
            )

            metrics = ctk.CTkFrame(
                overview,
                fg_color="transparent"
            )
            metrics.pack(fill="x")

            for column in range(3):
                metrics.grid_columnconfigure(
                    column,
                    weight=1,
                    uniform="admin_account_metrics"
                )

            metric_items = (
                (
                    "TOTAL ACCOUNTS",
                    total_count,
                    "#93C5FD"
                ),
                (
                    "ACTIVE ACCOUNTS",
                    active_count,
                    colors["green"]
                ),
                (
                    "FROZEN ACCOUNTS",
                    frozen_count,
                    colors["amber"]
                )
            )

            for index, (title, value, color) in enumerate(
                metric_items
            ):
                card = ctk.CTkFrame(
                    metrics,
                    fg_color=colors["panel"],
                    corner_radius=16,
                    border_width=1,
                    border_color=colors["border"]
                )
                card.grid(
                    row=0,
                    column=index,
                    sticky="nsew",
                    padx=5
                )

                ctk.CTkLabel(
                    card,
                    text=title,
                    font=("Arial", 11, "bold"),
                    text_color=colors["muted"],
                    anchor="w"
                ).pack(
                    fill="x",
                    padx=20,
                    pady=(17, 7)
                )

                ctk.CTkLabel(
                    card,
                    text=str(value),
                    font=("Arial", 27, "bold"),
                    text_color=color,
                    anchor="w"
                ).pack(
                    fill="x",
                    padx=20,
                    pady=(0, 18)
                )

            # ====================================================
            # ACCOUNT SEARCH
            # ====================================================

            search_frame = ctk.CTkFrame(
                page,
                fg_color=colors["panel"],
                corner_radius=15,
                border_width=1,
                border_color=colors["border"]
            )
            search_frame.pack(
                fill="x",
                padx=32,
                pady=(0, 13)
            )

            ctk.CTkLabel(
                search_frame,
                text="Account Search",
                font=("Arial", 16, "bold"),
                text_color=colors["text"],
                anchor="w"
            ).pack(
                fill="x",
                padx=20,
                pady=(15, 5)
            )

            ctk.CTkLabel(
                search_frame,
                text="Filter bank accounts by customer name",
                font=("Arial", 11),
                text_color=colors["muted"],
                anchor="w"
            ).pack(
                fill="x",
                padx=20,
                pady=(0, 10)
            )

            customer_names = sorted({
                str(row[2]).strip()
                for row in rows
            })

            customer_combo = ctk.CTkComboBox(
                search_frame,
                values=["All Customers"] + customer_names,
                width=370,
                height=39,
                corner_radius=9,
                font=("Arial", 12),
                state="readonly",
                fg_color=colors["header"],
                border_color=colors["border"],
                button_color="#304B70",
                button_hover_color="#456B9B",
                text_color=colors["text"],
                dropdown_fg_color=colors["header"],
                dropdown_text_color=colors["text"],
                dropdown_hover_color="#304B70"
            )
            customer_combo.pack(
                anchor="w",
                padx=20,
                pady=(0, 16)
            )
            customer_combo.set("All Customers")

            # ====================================================
            # TABLE TOOLBAR
            # ====================================================

            toolbar = ctk.CTkFrame(
                page,
                fg_color="transparent"
            )
            toolbar.pack(
                fill="x",
                padx=32,
                pady=(2, 10)
            )

            title_area = ctk.CTkFrame(
                toolbar,
                fg_color="transparent"
            )
            title_area.pack(side="left")

            ctk.CTkLabel(
                title_area,
                text="Registered Bank Accounts",
                font=("Arial", 17, "bold"),
                text_color=colors["text"],
                anchor="w"
            ).pack(anchor="w")

            ctk.CTkLabel(
                title_area,
                text="Select an account to manage security restrictions",
                font=("Arial", 11),
                text_color=colors["muted"],
                anchor="w"
            ).pack(
                anchor="w",
                pady=(4, 0)
            )

            ctk.CTkButton(
                toolbar,
                text="Refresh",
                command=lambda: self.run(self.show_accounts),
                width=125,
                height=40,
                corner_radius=10,
                fg_color=colors["blue"],
                hover_color=BLUE_HOVER,
                text_color="#FFFFFF",
                font=("Arial", 12, "bold")
            ).pack(side="right")

            # ====================================================
            # DARK TABLE CONTAINER
            # ====================================================
            # ====================================================
            # ACCOUNT ACTION BUTTONS - ABOVE TABLE
            # ====================================================

            action_frame = ctk.CTkFrame(
                page,
                fg_color="transparent"
            )
            action_frame.pack(
                fill="x",
                padx=32,
                pady=(0, 12)
            )
            table_holder = ctk.CTkFrame(
                page,
                fg_color=colors["panel"],
                corner_radius=15,
                border_width=1,
                border_color=colors["border"]
            )
            table_holder.pack(
                fill="both",
                expand=True,
                padx=27,
                pady=(0, 12)
            )

            table_area = ctk.CTkFrame(
                table_holder,
                fg_color=colors["panel"]
            )
            table_area.pack(
                fill="both",
                expand=True,
                padx=12,
                pady=12
            )

            # ====================================================
            # DARK TREEVIEW STYLE
            # ====================================================

            style = ttk.Style()
            previous_theme = style.theme_use()

            if previous_theme != "clam":
                style.theme_use("clam")

            def restore_theme(event):
                if event.widget is table_holder:
                    current_style = ttk.Style()

                    if current_style.theme_use() != previous_theme:
                        current_style.theme_use(previous_theme)

            table_holder.bind(
                "<Destroy>",
                restore_theme,
                add="+"
            )

            style.configure(
                "AdminAccounts.Treeview",
                background=colors["panel"],
                fieldbackground=colors["panel"],
                foreground=colors["text"],
                rowheight=39,
                font=("Arial", 11),
                borderwidth=0,
                relief="flat"
            )

            style.configure(
                "AdminAccounts.Treeview.Heading",
                background=colors["header"],
                foreground="#FFFFFF",
                font=("Arial", 11, "bold"),
                padding=(10, 12),
                borderwidth=0,
                relief="flat"
            )

            style.map(
                "AdminAccounts.Treeview",
                background=[
                    ("selected", colors["blue"])
                ],
                foreground=[
                    ("selected", "#FFFFFF")
                ]
            )

            style.map(
                "AdminAccounts.Treeview.Heading",
                background=[
                    ("active", "#304B70"),
                    ("pressed", colors["header"])
                ],
                foreground=[
                    ("active", "#FFFFFF")
                ]
            )

            # ====================================================
            # DARK SCROLLBARS
            # ====================================================

            for orientation in ("Vertical", "Horizontal"):
                scrollbar_style = (
                    f"AdminAccounts.{orientation}.TScrollbar"
                )

                style.configure(
                    scrollbar_style,
                    background="#304B70",
                    troughcolor="#111F35",
                    arrowcolor="#FFFFFF",
                    bordercolor=colors["panel"],
                    lightcolor="#304B70",
                    darkcolor="#304B70",
                    gripcount=0,
                    borderwidth=0,
                    relief="flat",
                    width=13
                )

                style.map(
                    scrollbar_style,
                    background=[
                        ("active", "#456B9B"),
                        ("pressed", colors["blue"])
                    ]
                )

            # ====================================================
            # ACCOUNT TABLE
            # ====================================================

            columns = (
                "id",
                "number",
                "customer",
                "balance",
                "currency",
                "status"
            )

            tree = ttk.Treeview(
                table_area,
                columns=columns,
                show="headings",
                style="AdminAccounts.Treeview",
                selectmode="browse"
            )

            column_specs = (
                ("id", "Account ID", 110),
                ("number", "Account Number", 250),
                ("customer", "Customer Name", 210),
                ("balance", "Balance", 150),
                ("currency", "Currency", 115),
                ("status", "Status", 140)
            )

            for key, heading, width in column_specs:
                tree.heading(
                    key,
                    text=heading
                )

                tree.column(
                    key,
                    width=width,
                    minwidth=90,
                    anchor=(
                        "w"
                        if key in ("number", "customer")
                        else "center"
                    ),
                    stretch=True
                )

            yscroll = ttk.Scrollbar(
                table_area,
                orient="vertical",
                command=tree.yview,
                style="AdminAccounts.Vertical.TScrollbar"
            )

            xscroll = ttk.Scrollbar(
                table_area,
                orient="horizontal",
                command=tree.xview,
                style="AdminAccounts.Horizontal.TScrollbar"
            )

            tree.configure(
                yscrollcommand=yscroll.set,
                xscrollcommand=xscroll.set
            )

            yscroll.pack(
                side="right",
                fill="y"
            )

            xscroll.pack(
                side="bottom",
                fill="x"
            )

            tree.pack(
                side="left",
                fill="both",
                expand=True
            )

            # ====================================================
            # ROW COLORS
            # ====================================================

            status_colors = {
                "Active": "#4ADE80",
                "Frozen": "#FBBF24",
                "Inactive": "#9EB2D0"
            }

            for status, foreground in status_colors.items():
                for parity, background in (
                    ("even", "#17263F"),
                    ("odd", "#1C2D48")
                ):
                    tree.tag_configure(
                        f"{status}_{parity}",
                        background=background,
                        foreground=foreground
                    )

            # ====================================================
            # ACCOUNT FILTER - ORIGINAL BEHAVIOR
            # ====================================================

            def refresh_accounts(*args):
                selected_customer = customer_combo.get()

                tree.delete(*tree.get_children())

                visible_index = 0

                for row in rows:
                    customer_name = str(row[2]).strip()

                    if (
                        selected_customer != "All Customers"
                        and customer_name != selected_customer
                    ):
                        continue

                    status = account_status(
                        row[6],
                        row[7]
                    )

                    parity = (
                        "even"
                        if visible_index % 2 == 0
                        else "odd"
                    )

                    tree.insert(
                        "",
                        "end",
                        values=(
                            row[0],
                            str(row[1]).strip(),
                            customer_name,
                            f"{row[4]:.2f}",
                            str(row[5]).strip(),
                            status
                        ),
                        tags=(f"{status}_{parity}",)
                    )

                    visible_index += 1

                update_admin_buttons()

            customer_combo.configure(
                command=refresh_accounts
            )

            # ====================================================
            # SELECT ADMIN ACCOUNT - ORIGINAL LOGIC
            # ====================================================

            def get_selected_account():
                selection = tree.selection()

                if not selection:
                    raise ValueError(
                        "Please select an account from the table."
                    )

                values = tree.item(
                    selection[0],
                    "values"
                )

                return {
                    "id": int(values[0]),
                    "number": values[1],
                    "customer": values[2],
                    "status": values[5]
                }

            # ====================================================
            # ADMIN - FREEZE ACCOUNT - ORIGINAL LOGIC
            # ====================================================

            def freeze_selected():
                def action():
                    require_account_admin()

                    account = get_selected_account()

                    if account["status"] != "Active":
                        raise ValueError(
                            "Only active, unfrozen accounts "
                            "can be frozen."
                        )

                    confirmed = self.ask_yes_no(
                        "Confirm Account Freeze",
                        (
                            f"Customer: {account['customer']}\n"
                            f"Account: {account['number']}\n\n"
                            "Freeze this account?\n\n"
                            "Deposits, withdrawals and transfers "
                            "will be restricted.\n\n"
                            "Only a bank administrator can "
                            "remove this restriction."
                        )
                    )

                    if not confirmed:
                        return

                    self.db.freeze_account(
                        account["id"]
                    )

                    self.show_ok(
                        "Account Frozen",
                        "The account has been frozen successfully."
                    )

                    self.show_accounts()

                self.run(action)

            # ====================================================
            # ADMIN - UNFREEZE ACCOUNT - ORIGINAL LOGIC
            # ====================================================

            def unfreeze_selected():
                def action():
                    require_account_admin()

                    account = get_selected_account()

                    if account["status"] != "Frozen":
                        raise ValueError(
                            "Only frozen accounts can be unfrozen."
                        )

                    confirmed = self.ask_yes_no(
                        "Confirm Account Unfreeze",
                        (
                            f"Customer: {account['customer']}\n"
                            f"Account: {account['number']}\n\n"
                            "Unfreeze this account?\n\n"
                            "Eligible banking operations will "
                            "be available again."
                        )
                    )

                    if not confirmed:
                        return

                    self.db.unfreeze_account(
                        account["id"]
                    )

                    self.show_ok(
                        "Account Unfrozen",
                        "The account has been unfrozen successfully."
                    )

                    self.show_accounts()

                self.run(action)

            # ====================================================
            # ACCOUNT ACTION BUTTONS
            # ====================================================


            freeze_button = ctk.CTkButton(
                action_frame,
                text="Freeze Selected Account",
                command=freeze_selected,
                width=215,
                height=43,
                corner_radius=10,
                fg_color="#A13B43",
                hover_color="#862D35",
                text_color="#FFFFFF",
                font=("Arial", 12, "bold")
            )
            freeze_button.pack(
                side="left",
                padx=(0, 12)
            )

            unfreeze_button = ctk.CTkButton(
                action_frame,
                text="Unfreeze Selected Account",
                command=unfreeze_selected,
                width=225,
                height=43,
                corner_radius=10,
                fg_color="#276A91",
                hover_color="#205674",
                text_color="#FFFFFF",
                font=("Arial", 12, "bold")
            )
            unfreeze_button.pack(side="left")

            # ====================================================
            # SELECTION STATE - ORIGINAL BEHAVIOR
            # ====================================================

            def update_admin_buttons(event=None):
                selection = tree.selection()

                if not selection:
                    freeze_button.configure(
                        state="disabled"
                    )
                    unfreeze_button.configure(
                        state="disabled"
                    )
                    return

                values = tree.item(
                    selection[0],
                    "values"
                )

                status = values[5]

                freeze_button.configure(
                    state=(
                        "normal"
                        if status == "Active"
                        else "disabled"
                    )
                )

                unfreeze_button.configure(
                    state=(
                        "normal"
                        if status == "Frozen"
                        else "disabled"
                    )
                )

            tree.bind(
                "<<TreeviewSelect>>",
                update_admin_buttons
            )

            refresh_accounts()

            return


        # ====================================================
        # CUSTOMER ACCOUNT OVERVIEW
        # ====================================================

        active_count = sum(
            1 for row in rows if bool(row[5])
        )

        frozen_count = sum(
            1 for row in rows
            if bool(row[5]) and bool(row[6])
        )

        palette = {
            "panel": "#17263F",
            "panel_alt": "#243A59",
            "border": "#2B4161",
            "text": "#F5F8FF",
            "muted": "#9EB2D0",
            "accent": "#3478F6",
            "green": "#4ADE80",
            "red": "#FCA5A5"
        }

        overview = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        overview.pack(
            fill="x",
            padx=22,
            pady=(8, 12)
        )

        ctk.CTkLabel(
            overview,
            text="Account Overview",
            font=("Arial", 19, "bold"),
            text_color=palette["text"],
            anchor="w"
        ).pack(
            fill="x",
            pady=(0, 12)
        )

        # ====================================================
        # ACCOUNT STATISTICS CARDS
        # ====================================================

        metrics = ctk.CTkFrame(
            overview,
            fg_color="transparent"
        )
        metrics.pack(fill="x")

        for column in range(3):
            metrics.grid_columnconfigure(
                column,
                weight=1,
                uniform="account_metrics"
            )

        metric_items = (
            ("TOTAL ACCOUNTS", str(len(rows)), "#93C5FD"),
            ("ACTIVE ACCOUNTS", f"{active_count} / 3", palette["green"]),
            ("FROZEN ACCOUNTS", str(frozen_count), palette["red"])
        )

        for index, (label, value, color) in enumerate(metric_items):
            metric = ctk.CTkFrame(
                metrics,
                fg_color=palette["panel"],
                corner_radius=16,
                border_width=1,
                border_color=palette["border"]
            )

            metric.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=5
            )

            ctk.CTkLabel(
                metric,
                text=label,
                font=("Arial", 11, "bold"),
                text_color=palette["muted"],
                anchor="w"
            ).pack(
                fill="x",
                padx=20,
                pady=(18, 7)
            )

            ctk.CTkLabel(
                metric,
                text=value,
                font=("Arial", 27, "bold"),
                text_color=color,
                anchor="w"
            ).pack(
                fill="x",
                padx=20,
                pady=(0, 18)
            )

        # ====================================================
        # CUSTOMER SECURITY WARNING
        # ====================================================

        if frozen_count > 0:
            warning_frame = ctk.CTkFrame(
                page,
                fg_color="#3B2029",
                corner_radius=12,
                border_width=1,
                border_color="#991B1B"
            )

            warning_frame.pack(
                fill="x",
                padx=27,
                pady=(0, 14)
            )

            ctk.CTkLabel(
                warning_frame,
                text="Account Frozen - Security Restriction",
                font=("Arial", 15, "bold"),
                text_color="#FCA5A5",
                anchor="w"
            ).pack(
                fill="x",
                padx=18,
                pady=(15, 6)
            )

            ctk.CTkLabel(
                warning_frame,
                text=(
                    "Your account has been frozen for security "
                    "reasons.\n\n"
                    "Your balance and transaction history remain "
                    "available. Deposits, withdrawals and transfers "
                    "are disabled for frozen accounts.\n\n"
                    "Only a bank administrator can unfreeze "
                    "your account. Please contact the bank."
                ),
                text_color="#FECACA",
                font=("Arial", 12),
                justify="left",
                anchor="w",
                wraplength=800
            ).pack(
                fill="x",
                padx=18,
                pady=(0, 16)
            )

        # ====================================================
        # CUSTOMER ACCOUNT TOOLBAR
        # ====================================================

        toolbar = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        toolbar.pack(
            fill="x",
            padx=27,
            pady=(4, 12)
        )

        ctk.CTkLabel(
            toolbar,
            text="Your Bank Accounts",
            font=("Arial", 18, "bold"),
            text_color=palette["text"],
            anchor="w"
        ).pack(side="left")

        ctk.CTkButton(
            toolbar,
            text="+ Create Account",
            command=self.show_account_type_selection,
            width=175,
            height=42,
            corner_radius=11,
            fg_color=palette["accent"],
            hover_color=BLUE_HOVER,
            text_color="#FFFFFF",
            font=("Arial", 12, "bold")
        ).pack(
            side="right",
            padx=(10, 0)
        )

        ctk.CTkButton(
            toolbar,
            text="Refresh",
            command=lambda: self.run(self.show_accounts),
            width=110,
            height=42,
            corner_radius=11,
            fg_color=palette["panel_alt"],
            hover_color=palette["border"],
            border_width=1,
            border_color=palette["border"],
            text_color=palette["text"],
            font=("Arial", 12, "bold")
        ).pack(side="right")

        # ====================================================
        # CUSTOMER ACCOUNTS TABLE - WINDOWS DARK FIX
        # ====================================================

        table_holder = ctk.CTkFrame(
            page,
            fg_color=palette["panel"],
            corner_radius=16,
            border_width=1,
            border_color=palette["border"]
        )

        table_holder.pack(
            fill="both",
            expand=True,
            padx=27,
            pady=(0, 12)
        )

        table_area = ctk.CTkFrame(
            table_holder,
            fg_color=palette["panel"]
        )

        table_area.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=12
        )

        # Windows ttk theme fix.
        # Preserve the original theme for other pages.

        style = ttk.Style()
        previous_theme = style.theme_use()

        if previous_theme != "clam":
            style.theme_use("clam")

        def restore_table_theme(event):
            if event.widget is table_holder:
                current_style = ttk.Style()

                if current_style.theme_use() != previous_theme:
                    current_style.theme_use(previous_theme)

        table_holder.bind(
            "<Destroy>",
            restore_table_theme,
            add="+"
        )

        # Separate My Accounts table style.

        style.configure(
            "MyAccounts.Treeview",
            background=palette["panel"],
            fieldbackground=palette["panel"],
            foreground=palette["text"],
            rowheight=43,
            font=("Arial", 11),
            borderwidth=0,
            relief="flat"
        )

        style.configure(
            "MyAccounts.Treeview.Heading",
            background=palette["panel_alt"],
            foreground="#FFFFFF",
            font=("Arial", 11, "bold"),
            padding=(12, 13),
            borderwidth=0,
            relief="flat"
        )

        style.map(
            "MyAccounts.Treeview",
            background=[
                ("selected", "#3478F6")
            ],
            foreground=[
                ("selected", "#FFFFFF")
            ]
        )

        style.map(
            "MyAccounts.Treeview.Heading",
            background=[
                ("active", "#2D4669"),
                ("pressed", palette["panel_alt"])
            ],
            foreground=[
                ("active", "#FFFFFF")
            ]
        )

        tree = ttk.Treeview(
            table_area,
            columns=(
                "id",
                "number",
                "balance",
                "currency",
                "status"
            ),
            show="headings",
            style="MyAccounts.Treeview"
        )

        column_specs = (
            ("id", "Account ID", 120),
            ("number", "Account Number", 230),
            ("balance", "Balance", 170),
            ("currency", "Currency", 120),
            ("status", "Status", 140)
        )

        for key, heading, width in column_specs:
            tree.heading(
                key,
                text=heading
            )

            tree.column(
                key,
                width=width,
                minwidth=90,
                anchor="center",
                stretch=True
            )

        # Dark scrollbars.

        style.configure(
            "MyAccounts.Vertical.TScrollbar",
            background="#243A59",
            troughcolor="#17263F",
            arrowcolor="#FFFFFF",
            borderwidth=0
        )

        style.configure(
            "MyAccounts.Horizontal.TScrollbar",
            background="#243A59",
            troughcolor="#17263F",
            arrowcolor="#FFFFFF",
            borderwidth=0
        )

        yscroll = ttk.Scrollbar(
            table_area,
            orient="vertical",
            command=tree.yview,
            style="MyAccounts.Vertical.TScrollbar"
        )

        xscroll = ttk.Scrollbar(
            table_area,
            orient="horizontal",
            command=tree.xview,
            style="MyAccounts.Horizontal.TScrollbar"
        )

        tree.configure(
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set
        )

        yscroll.pack(
            side="right",
            fill="y"
        )

        xscroll.pack(
            side="bottom",
            fill="x"
        )

        tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        # ====================================================
        # ACCOUNT STATUS COLORS
        # ====================================================

        tree.tag_configure(
            "Active",
            foreground=palette["green"]
        )

        tree.tag_configure(
            "Frozen",
            foreground=palette["red"]
        )

        tree.tag_configure(
            "Inactive",
            foreground="#A5B4CC"
        )

        # ====================================================
        # POPULATE CUSTOMER ACCOUNTS
        # ====================================================

        for row in rows:
            status = account_status(
                row[5],
                row[6]
            )

            tree.insert(
                "",
                "end",
                values=(
                    row[0],
                    str(row[1]).strip(),
                    f"{row[3]:.2f}",
                    str(row[4]).strip(),
                    status
                ),
                tags=(status,)
            )

        # ====================================================
        # EMPTY ACCOUNTS STATE - CENTERED DESIGN
        # ====================================================

        if not rows:
            empty_state = ctk.CTkFrame(
                table_holder,
                width=440,
                height=230,
                fg_color=palette["panel"],
                corner_radius=16,
                border_width=1,
                border_color=palette["border"]
            )

            empty_state.place(
                relx=0.5,
                rely=0.54,
                anchor="center"
            )

            empty_state.pack_propagate(False)

            ctk.CTkLabel(
                empty_state,
                text="No accounts yet",
                font=("Arial", 22, "bold"),
                text_color="#FFFFFF"
            ).pack(
                pady=(40, 10)
            )

            ctk.CTkLabel(
                empty_state,
                text="Create your first bank account to get started.",
                font=("Arial", 13),
                text_color=palette["muted"]
            ).pack(
                pady=(0, 22)
            )

            ctk.CTkButton(
                empty_state,
                text="+ Create Account",
                command=self.show_account_type_selection,
                width=190,
                height=43,
                corner_radius=11,
                fg_color=palette["accent"],
                hover_color=BLUE_HOVER,
                text_color="#FFFFFF",
                font=("Arial", 12, "bold")
            ).pack()

        # ====================================================
        # CUSTOMER - CLOSE ACCOUNT
        # ORIGINAL BUSINESS LOGIC PRESERVED
        # ====================================================

        def close_selected_account():
            def action():
                current_session = self.db.require_login()

                if current_session["role"] != "Customer":
                    raise PermissionError(
                        "Only customers can close their own accounts."
                    )

                selected = tree.selection()

                if not selected:
                    self.show_ok(
                        "Select Account",
                        "Please select an account first."
                    )
                    return

                values = tree.item(
                    selected[0],
                    "values"
                )

                account_id = int(values[0])
                account_number = values[1]
                balance = Decimal(str(values[2]))
                status = values[4]

                if status == "Frozen":
                    raise PermissionError(
                        "This account is frozen and cannot be "
                        "closed. Only a bank administrator "
                        "can remove this restriction."
                    )

                if status != "Active":
                    raise ValueError(
                        "This account is already inactive."
                    )

                if balance != 0:
                    raise ValueError(
                        "Only accounts with 0 TRY balance "
                        "can be closed."
                    )

                confirmed = self.ask_yes_no(
                    "Confirm Account Closure",
                    (
                        "Close this bank account?\n\n"
                        f"Account: {account_number}\n"
                        f"Balance: {balance:.2f} TRY\n\n"
                        "Your transaction history will be preserved."
                    )
                )

                if not confirmed:
                    return

                self.db.delete_account(account_id)

                self.show_ok(
                    "Success",
                    "Your bank account has been closed successfully."
                )

                self.show_accounts()

            self.run(action)

        # ====================================================
        # CUSTOMER ACCOUNT ACTIONS
        # ====================================================

        action_frame = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        action_frame.pack(
            fill="x",
            padx=27,
            pady=(8, 18)
        )

        close_button = ctk.CTkButton(
            action_frame,
            text="Close Selected Account",
            command=close_selected_account,
            width=220,
            height=43,
            corner_radius=11,
            fg_color="#263A58",
            hover_color="#334E74",
            border_width=1,
            border_color="#456184",
            text_color="#F5F8FF",
            font=("Arial", 12, "bold")
        )

        close_button.pack(side="left")

        # ====================================================
        # UPDATE CLOSE BUTTON STATE
        # ORIGINAL BUSINESS LOGIC PRESERVED
        # ====================================================

        def update_customer_buttons(event=None):
            selection = tree.selection()

            if not selection:
                close_button.configure(
                    state="disabled"
                )
                return

            values = tree.item(
                selection[0],
                "values"
            )

            balance = Decimal(str(values[2]))
            status = values[4]

            can_close = (
                status == "Active"
                and balance == 0
            )

            close_button.configure(
                state=(
                    "normal"
                    if can_close
                    else "disabled"
                )
            )

        tree.bind(
            "<<TreeviewSelect>>",
            update_customer_buttons
        )

        update_customer_buttons()

    # ============================================================
    # TRANSACTIONS SCREEN
    # ============================================================

    def show_transactions(self):
        session = self.db.require_login()
        is_admin = session["role"] == "Admin"

        page = self.page(
            "Transactions" if is_admin else "My Transactions"
        )

        account_rows = self.db.accounts()
        account_map = {}
        card_map = {}

        # ====================================================
        # AVAILABLE BANK ACCOUNTS
        # ====================================================

        for row in account_rows:

            active = bool(
                row[6] if is_admin else row[5]
            )

            frozen = bool(
                row[7] if is_admin else row[6]
            )

            if not active or frozen:
                continue

            account_id = int(row[0])
            account_number = str(row[1]).strip()

            balance = (
                row[4] if is_admin else row[3]
            )

            label = (
                f"{account_number} | "
                f"{balance:.2f} TRY"
            )

            account_map[label] = {
                "id": account_id,
                "number": account_number
            }

        account_labels = list(account_map)

        # ====================================================
        # AVAILABLE CREDIT CARDS
        # ====================================================

        if not is_admin:

            for row in self.db.my_credit_cards():

                if str(row[5]).strip() != "Active":
                    continue

                card_id = int(row[0])

                credit_limit = Decimal(
                    str(row[2])
                )

                outstanding = Decimal(
                    str(row[3])
                )

                available = (
                    credit_limit - outstanding
                )

                card_number = str(row[7]).strip()

                label = (
                    f"{row[1]} | "
                    f"**** {card_number[-4:]} | "
                    f"ID: {card_id}"
                )

                card_map[label] = {
                    "id": card_id,
                    "type": row[1],
                    "number": card_number[-4:],
                    "limit": credit_limit,
                    "outstanding": outstanding,
                    "available": available
                }

        # ====================================================
        # TRANSACTION TYPES
        # ====================================================

        card_transaction_types = {
            "Credit Card Purchase": "Purchase",
            "Cash Advance": "CashAdvance",
            "Pay Credit Card Debt": "Payment"
        }

        transaction_types = [
            "Deposit",
            "Withdrawal",
            "Transfer"
        ]

        if not is_admin:

            transaction_types.extend(
                card_transaction_types.keys()
            )

        # ====================================================
        # TRANSACTION FORM
        # ====================================================

        form = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=14
        )

        form.pack(
            fill="x",
            padx=22,
            pady=(8, 12)
        )

        ctk.CTkLabel(
            form,
            text="New Transaction",
            font=("Arial", 19, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(
            fill="x",
            padx=22,
            pady=(20, 5)
        )

        ctk.CTkLabel(
            form,
            text="Enter the transaction details below.",
            font=("Arial", 12),
            text_color=MUTED,
            anchor="w"
        ).pack(
            fill="x",
            padx=22,
            pady=(0, 16)
        )

        fields = ctk.CTkFrame(
            form,
            fg_color="transparent"
        )

        fields.pack(
            fill="x",
            padx=16,
            pady=(0, 8)
        )

        fields.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="transaction_fields"
        )

        def field_label(title, row, column):

            label = ctk.CTkLabel(
                fields,
                text=title,
                font=("Arial", 12, "bold"),
                text_color=WHITE,
                anchor="w"
            )

            label.grid(
                row=row,
                column=column,
                sticky="ew",
                padx=8,
                pady=(8, 5)
            )

            return label

        # ====================================================
        # TRANSACTION TYPE AND SOURCE
        # ====================================================

        field_label(
            "Transaction Type",
            0,
            0
        )

        source_label = field_label(
            "From / My Account",
            0,
            1
        )

        kind = ctk.CTkComboBox(
            fields,
            values=transaction_types,
            height=40,
            corner_radius=9,
            state="readonly"
        )

        kind.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=8,
            pady=(0, 9)
        )

        source = ctk.CTkComboBox(
            fields,
            values=(
                account_labels
                or ["No available accounts"]
            ),
            height=40,
            corner_radius=9,
            state="readonly"
        )

        source.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=8,
            pady=(0, 9)
        )

        # ====================================================
        # AMOUNT AND DESCRIPTION
        # ====================================================

        field_label(
            "Amount (TRY)",
            2,
            0
        )

        field_label(
            "Description",
            2,
            1
        )

        amount = ctk.CTkEntry(
            fields,
            placeholder_text="Amount",
            height=40,
            corner_radius=9
        )

        amount.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=8,
            pady=(0, 9)
        )

        description = ctk.CTkEntry(
            fields,
            placeholder_text="Optional",
            height=40,
            corner_radius=9
        )

        description.grid(
            row=3,
            column=1,
            sticky="ew",
            padx=8,
            pady=(0, 9)
        )

        # ====================================================
        # TRANSFER DESTINATION
        # ====================================================

        transfer_mode_label = field_label(
            "Transfer To",
            4,
            0
        )

        transfer_mode = ctk.CTkComboBox(
            fields,
            values=[
                "My Own Accounts",
                "Another Customer"
            ],
            height=40,
            corner_radius=9,
            state="readonly"
        )

        transfer_mode.grid(
            row=5,
            column=0,
            sticky="ew",
            padx=8,
            pady=(0, 9)
        )

        own_destination_label = field_label(
            "To My Account",
            4,
            1
        )

        own_destination = ctk.CTkComboBox(
            fields,
            values=(
                account_labels
                or ["No available accounts"]
            ),
            height=40,
            corner_radius=9,
            state="readonly"
        )

        own_destination.grid(
            row=5,
            column=1,
            sticky="ew",
            padx=8,
            pady=(0, 9)
        )

        external_destination_label = field_label(
            "Recipient Account Number",
            4,
            1
        )

        external_destination = ctk.CTkEntry(
            fields,
            placeholder_text="TR + 16 digits",
            height=40,
            corner_radius=9
        )

        external_destination.grid(
            row=5,
            column=1,
            sticky="ew",
            padx=8,
            pady=(0, 9)
        )

        # ====================================================
        # CREDIT CARD INFORMATION
        # ====================================================

        card_info = ctk.CTkLabel(
            fields,
            text="",
            font=("Arial", 12),
            text_color=MUTED,
            justify="left",
            anchor="w",
            wraplength=800
        )

        card_info.grid(
            row=6,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=8,
            pady=(5, 10)
        )

        card_info.grid_remove()

        # ====================================================
        # SECURITY AND AVAILABILITY INFORMATION
        # ====================================================

        warning_label = ctk.CTkLabel(
            page,
            text="",
            text_color="#FBBF24",
            font=("Arial", 12),
            wraplength=800
        )

        def show_warning(text):

            warning_label.configure(text=text)

            if text:

                warning_label.pack(
                    padx=22,
                    pady=(0, 10),
                    before=history_header
                )

            else:

                warning_label.pack_forget()

        # ====================================================
        # UPDATE CARD INFORMATION
        # ====================================================

        def update_card_info(*args):

            selected_kind = kind.get()

            if selected_kind not in card_transaction_types:

                card_info.grid_remove()
                return

            selected_card = source.get()

            if selected_card not in card_map:

                card_info.configure(
                    text="No eligible credit cards available."
                )

                card_info.grid()

                return

            card = card_map[selected_card]

            operation_help = {
                "Credit Card Purchase": (
                    "The purchase amount will be added "
                    "to your credit card debt."
                ),

                "Cash Advance": (
                    "The amount will be transferred "
                    "to your linked bank account."
                ),

                "Pay Credit Card Debt": (
                    "The amount will be deducted "
                    "from your linked bank account."
                )
            }

            card_info.configure(
                text=(
                    f"Credit Limit: "
                    f"{card['limit']:,.2f} TRY"
                    f"    |    Outstanding Debt: "
                    f"{card['outstanding']:,.2f} TRY\n"
                    f"Available Limit: "
                    f"{card['available']:,.2f} TRY\n"
                    f"{operation_help[selected_kind]}\n"
                    "Subject to account status and "
                    "security restrictions."
                )
            )

            card_info.grid()

        # ====================================================
        # UPDATE TRANSACTION FIELDS
        # ====================================================

        def update_destination_fields(*args):

            selected_kind = kind.get()

            previous_source = source.get()

            transfer_mode_label.grid_remove()
            transfer_mode.grid_remove()

            own_destination_label.grid_remove()
            own_destination.grid_remove()

            external_destination_label.grid_remove()
            external_destination.grid_remove()

            card_info.grid_remove()

            # ================================================
            # CREDIT CARD OPERATIONS
            # ================================================

            if selected_kind in card_transaction_types:

                source_label.configure(
                    text="Select Credit Card"
                )

                eligible_cards = []

                for label, card in card_map.items():

                    if selected_kind == "Pay Credit Card Debt":

                        if card["outstanding"] > 0:

                            eligible_cards.append(
                                label
                            )

                    else:

                        if card["available"] > 0:

                            eligible_cards.append(
                                label
                            )

                source.configure(
                    state="normal"
                )

                source.configure(
                    values=(
                        eligible_cards
                        or ["No eligible credit cards"]
                    )
                )

                if eligible_cards:

                    source.set(
                        previous_source
                        if previous_source in eligible_cards
                        else eligible_cards[0]
                    )

                    source.configure(
                        state="readonly"
                    )

                    execute_button.configure(
                        state="normal"
                    )

                    show_warning("")

                else:

                    source.set(
                        "No eligible credit cards"
                    )

                    source.configure(
                        state="disabled"
                    )

                    execute_button.configure(
                        state="disabled"
                    )

                    show_warning(
                        "No eligible credit cards are "
                        "available for this operation."
                    )

                update_card_info()

                return

            # ================================================
            # BANK ACCOUNT OPERATIONS
            # ================================================

            source_label.configure(
                text="From / My Account"
            )

            source.configure(
                state="normal"
            )

            source.configure(
                values=(
                    account_labels
                    or ["No available accounts"]
                )
            )

            if account_labels:

                source.set(
                    previous_source
                    if previous_source in account_labels
                    else account_labels[0]
                )

                source.configure(
                    state="readonly"
                )

                execute_button.configure(
                    state="normal"
                )

                show_warning("")

            else:

                source.set(
                    "No available accounts"
                )

                source.configure(
                    state="disabled"
                )

                execute_button.configure(
                    state="disabled"
                )

                show_warning(
                    "No active, unfrozen accounts are "
                    "available for new transactions. "
                    "Existing transaction history "
                    "remains accessible."
                )

            # ================================================
            # TRANSFER DESTINATION
            # ================================================

            if selected_kind != "Transfer":

                return

            transfer_mode_label.grid()
            transfer_mode.grid()

            if transfer_mode.get() == "My Own Accounts":

                own_destination_label.grid()
                own_destination.grid()

            else:

                external_destination_label.grid()
                external_destination.grid()

        # ====================================================
        # EXECUTE CREDIT CARD TRANSACTION
        # ====================================================

        def execute_card_transaction():

            selected_kind = kind.get()
            selected_card = source.get()

            if is_admin:

                raise PermissionError(
                    "Customer access required."
                )

            if selected_card not in card_map:

                raise ValueError(
                    "Please select an eligible credit card."
                )

            card = card_map[selected_card]

            transaction_kind = (
                card_transaction_types[selected_kind]
            )

            transaction_amount = (
                self.db._validate_credit_card_amount(
                    amount.get()
                )
            )

            transaction_description = (
                description.get().strip()
            )

            if len(transaction_description) > 250:

                raise ValueError(
                    "Description cannot exceed "
                    "250 characters."
                )

            # ================================================
            # VALIDATE LIMIT OR OUTSTANDING DEBT
            # ================================================

            if transaction_kind == "Payment":

                if (
                    transaction_amount
                    > card["outstanding"]
                ):

                    raise ValueError(
                        "Payment cannot exceed "
                        "the outstanding debt."
                    )

                operation_message = (
                    "The amount will be deducted "
                    "from your linked bank account."
                )

            else:

                if (
                    transaction_amount
                    > card["available"]
                ):

                    raise ValueError(
                        "Insufficient available "
                        "credit card limit."
                    )

                if transaction_kind == "CashAdvance":

                    operation_message = (
                        "The amount will be added to "
                        "your linked bank account and "
                        "your credit card debt."
                    )

                else:

                    operation_message = (
                        "The amount will be added "
                        "to your credit card debt."
                    )

            # ================================================
            # CONFIRM CREDIT CARD TRANSACTION
            # ================================================

            confirmed = self.ask_yes_no(
                "Confirm Transaction",
                (
                    f"Operation: {selected_kind}\n"
                    f"Card: **** {card['number']}\n"
                    f"Amount: "
                    f"{transaction_amount:,.2f} TRY\n\n"
                    f"{operation_message}\n\n"
                    "Do you want to continue?"
                )
            )

            if not confirmed:

                return

            # ================================================
            # CALL CREDIT CARD BACKEND
            # ================================================

            tx_id = self.db.credit_card_transact(
                transaction_kind,
                card["id"],
                transaction_amount,
                transaction_description
            )

            self.show_ok(
                "Transaction Completed",
                (
                    f"{selected_kind} completed "
                    "successfully.\n\n"
                    f"Card Transaction ID: {tx_id}"
                )
            )

            self.show_transactions()

        # ====================================================
        # EXECUTE BANK TRANSACTION
        # ====================================================

        def execute():

            def action():

                selected_kind = kind.get()

                # ============================================
                # CREDIT CARD TRANSACTION
                # ============================================

                if selected_kind in card_transaction_types:

                    execute_card_transaction()

                    return

                # ============================================
                # BANK TRANSACTION
                # ============================================

                selected_source = source.get()

                if selected_source not in account_map:

                    raise ValueError(
                        "Please select an active, "
                        "unfrozen source account."
                    )

                source_id = (
                    account_map[selected_source]["id"]
                )

                destination_number = ""

                # ============================================
                # TRANSFER TO MY OWN ACCOUNT
                # ============================================

                if selected_kind == "Transfer":

                    if (
                        transfer_mode.get()
                        == "My Own Accounts"
                    ):

                        selected_destination = (
                            own_destination.get()
                        )

                        if (
                            selected_destination
                            not in account_map
                        ):

                            raise ValueError(
                                "Please select an active, "
                                "unfrozen destination account."
                            )

                        destination_number = account_map[
                            selected_destination
                        ]["number"]

                    # ========================================
                    # TRANSFER TO ANOTHER CUSTOMER
                    # ========================================

                    else:

                        destination_number = (
                            external_destination
                            .get()
                            .strip()
                            .upper()
                        )

                    if (
                        destination_number
                        == account_map[
                            selected_source
                        ]["number"]
                    ):

                        raise ValueError(
                            "Source and destination "
                            "accounts must differ."
                        )

                # ============================================
                # CALL EXISTING BANK BACKEND
                # ============================================

                tx_id = self.db.transact(
                    selected_kind,
                    source_id,
                    destination_number,
                    amount.get(),
                    description.get()
                )

                self.show_ok(
                    "Transaction Completed",
                    f"Transaction ID: {tx_id}"
                )

                self.show_transactions()

            self.run(action)

        # ====================================================
        # TRANSACTION ACTION BUTTONS
        # ====================================================

        action_frame = ctk.CTkFrame(
            form,
            fg_color="transparent"
        )

        action_frame.pack(
            fill="x",
            padx=24,
            pady=(5, 20)
        )

        execute_button = self.button(
            action_frame,
            "Execute Transaction",
            execute,
            width=220
        )

        execute_button.pack(
            side="right"
        )

        if not is_admin:

            self.button(
                action_frame,
                "My Credit Cards",
                lambda: self.run(
                    self.show_my_credit_cards
                ),
                width=170
            ).pack(
                side="left"
            )

        # ====================================================
        # TRANSACTION HISTORY HEADER
        # ====================================================

        history_header = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        history_header.pack(
            fill="x",
            padx=24,
            pady=(10, 2)
        )

        ctk.CTkLabel(
            history_header,
            text="Transaction History",
            font=("Arial", 19, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(
            side="left"
        )

        self.button(
            history_header,
            "Refresh",
            lambda: self.run(
                self.show_transactions
            ),
            width=110
        ).pack(
            side="right"
        )

        # ====================================================
        # HISTORY TYPE SELECTOR
        # ====================================================

        history_filter = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        history_filter.pack(
            fill="x",
            padx=24,
            pady=(5, 8)
        )

        history_mode = ctk.CTkComboBox(
            history_filter,
            values=[
                "Bank Transactions",
                "Credit Card Transactions"
            ],
            width=240,
            height=36,
            corner_radius=9,
            state="readonly"
        )

        history_mode.pack(
            side="left"
        )

        history_mode.set(
            "Bank Transactions"
        )

        # ====================================================
        # TRANSACTION HISTORY - DARK TABLE STYLE
        # ====================================================

        transaction_style = ttk.Style()
        previous_theme = transaction_style.theme_use()

        if previous_theme != "clam":
            transaction_style.theme_use("clam")

        transaction_style.configure(
            "TransactionsDark.Treeview",
            background="#17263F",
            fieldbackground="#17263F",
            foreground="#F5F8FF",
            rowheight=34,
            font=("Arial", 11),
            borderwidth=0,
            relief="flat"
        )

        transaction_style.configure(
            "TransactionsDark.Treeview.Heading",
            background="#243A59",
            foreground="#FFFFFF",
            font=("Arial", 11, "bold"),
            padding=(10, 9),
            borderwidth=0,
            relief="flat"
        )

        transaction_style.map(
            "TransactionsDark.Treeview",
            background=[
                ("selected", "#3478F6")
            ],
            foreground=[
                ("selected", "#FFFFFF")
            ]
        )

        transaction_style.map(
            "TransactionsDark.Treeview.Heading",
            background=[
                ("active", "#304B70")
            ],
            foreground=[
                ("active", "#FFFFFF")
            ]
        )

        for orientation in ("Vertical", "Horizontal"):
            scrollbar_style = (
                f"TransactionsDark.{orientation}.TScrollbar"
            )

            transaction_style.configure(
                scrollbar_style,
                background="#304B70",
                troughcolor="#111F35",
                arrowcolor="#FFFFFF",
                bordercolor="#17263F",
                lightcolor="#304B70",
                darkcolor="#304B70",
                borderwidth=0,
                relief="flat",
                width=13
            )

            transaction_style.map(
                scrollbar_style,
                background=[
                    ("active", "#456B9B"),
                    ("pressed", "#3478F6")
                ]
            )

        # ====================================================
        # HISTORY TABLE CONTAINER
        # ====================================================


        history_container = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        history_container.pack(
            fill="both",
            expand=True
        )

        # Restore the previous ttk theme when leaving this page.
        def restore_transaction_theme(event):
            if event.widget is history_container:
                current_style = ttk.Style()

                if current_style.theme_use() != previous_theme:
                    current_style.theme_use(previous_theme)

        history_container.bind(
            "<Destroy>",
            restore_transaction_theme,
            add="+"
        )


        # ====================================================
        # BANK TRANSACTION HISTORY
        # ====================================================

        def show_bank_history():

            if is_admin:

                columns = (
                    "id",
                    "type",
                    "sender_customer",
                    "receiver_customer",
                    "from",
                    "to",
                    "amount",
                    "description",
                    "date",
                    "status",
                    "fraud_status"
                )

                headings = (
                    "ID",
                    "Type",
                    "Sender Customer",
                    "Receiver Customer",
                    "From Account",
                    "To Account",
                    "Amount",
                    "Description",
                    "Date",
                    "Status",
                    "Fraud Status"
                )

            else:

                columns = (
                    "id",
                    "type",
                    "from",
                    "to",
                    "amount",
                    "description",
                    "date",
                    "status",
                    "fraud_status"
                )

                headings = (
                    "ID",
                    "Type",
                    "From Account",
                    "To Account",
                    "Amount",
                    "Description",
                    "Date",
                    "Status",
                    "Fraud Status"
                )

            rows = self.db.transactions()

            tree = self.table(
                history_container,
                columns,
                headings
            )


            # Dark style for bank transaction history
            tree.configure(
                style="TransactionsDark.Treeview"
            )


            # Apply dark styles to existing table scrollbars.
            # Search recursively because self.table() may
            # create scrollbars inside a nested frame.

            def apply_dark_scrollbars(widget):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Scrollbar):
                        orientation = str(
                            child.cget("orient")
                        )

                        if orientation == "vertical":
                            child.configure(
                                style="TransactionsDark.Vertical.TScrollbar"
                            )
                        else:
                            child.configure(
                                style="TransactionsDark.Horizontal.TScrollbar"
                            )

                    apply_dark_scrollbars(child)

            apply_dark_scrollbars(history_container)


            for row in rows:

                fraud_status = (
                    row[10] or "Not Flagged"
                )

                if is_admin:

                    values = (
                        row[0],
                        row[1],
                        row[8] or "-",
                        row[9] or "-",
                        row[2] or "-",
                        row[3] or "-",
                        f"{row[4]:.2f}",
                        row[5] or "-",
                        str(row[6])[:19],
                        row[7],
                        fraud_status
                    )

                else:

                    values = (
                        row[0],
                        row[1],
                        row[2] or "-",
                        row[3] or "-",
                        f"{row[4]:.2f}",
                        row[5] or "-",
                        str(row[6])[:19],
                        row[7],
                        fraud_status
                    )

                tree.insert(
                    "",
                    "end",
                    values=values
                )

        # ====================================================
        # CREDIT CARD TRANSACTION HISTORY
        # ====================================================

        def show_card_history():

            if is_admin:

                columns = (
                    "id",
                    "card_id",
                    "customer_id",
                    "card_type",
                    "card_number",
                    "type",
                    "amount",
                    "description",
                    "status",
                    "date"
                )

                headings = (
                    "Transaction ID",
                    "Card ID",
                    "Customer ID",
                    "Card Type",
                    "Card Number",
                    "Transaction Type",
                    "Amount (TRY)",
                    "Description",
                    "Status",
                    "Date"
                )

                rows = (
                    self.db.admin_credit_card_transactions()
                )

            else:

                columns = (
                    "id",
                    "card_id",
                    "card_type",
                    "card_number",
                    "type",
                    "amount",
                    "description",
                    "status",
                    "date"
                )

                headings = (
                    "Transaction ID",
                    "Card ID",
                    "Card Type",
                    "Card Number",
                    "Transaction Type",
                    "Amount (TRY)",
                    "Description",
                    "Status",
                    "Date"
                )

                rows = (
                    self.db.my_credit_card_transactions()
                )

            tree = self.table(
                history_container,
                columns,
                headings
            )


            # Dark style for credit card transaction history
            tree.configure(
                style="TransactionsDark.Treeview"
            )


            # Apply dark styles to existing table scrollbars.
            # Search recursively because self.table() may
            # create scrollbars inside a nested frame.

            def apply_dark_scrollbars(widget):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Scrollbar):
                        orientation = str(
                            child.cget("orient")
                        )

                        if orientation == "vertical":
                            child.configure(
                                style="TransactionsDark.Vertical.TScrollbar"
                            )
                        else:
                            child.configure(
                                style="TransactionsDark.Horizontal.TScrollbar"
                            )

                    apply_dark_scrollbars(child)

            apply_dark_scrollbars(history_container)


            type_labels = {
                "Purchase": "Purchase",
                "CashAdvance": "Cash Advance",
                "Payment": "Debt Payment",
                "Refund": "Refund"
            }

            for row in rows:

                if is_admin:

                    transaction_type = str(
                        row[5]
                    ).strip()

                    values = (
                        row[0],
                        row[1],
                        row[2],
                        row[3],
                        "**** " + str(row[4])[-4:],
                        type_labels.get(
                            transaction_type,
                            transaction_type
                        ),
                        f"{row[6]:.2f}",
                        row[7] or "-",
                        row[8],
                        str(row[9])[:19]
                    )

                else:

                    transaction_type = str(
                        row[4]
                    ).strip()

                    values = (
                        row[0],
                        row[1],
                        row[2],
                        "**** " + str(row[3])[-4:],
                        type_labels.get(
                            transaction_type,
                            transaction_type
                        ),
                        f"{row[5]:.2f}",
                        row[6] or "-",
                        row[7],
                        str(row[8])[:19]
                    )

                tree.insert(
                    "",
                    "end",
                    values=values
                )

        # ====================================================
        # SWITCH TRANSACTION HISTORY
        # ====================================================

        def refresh_transactions(*args):

            def action():

                for widget in (
                    history_container.winfo_children()
                ):

                    widget.destroy()

                if (
                    history_mode.get()
                    == "Credit Card Transactions"
                ):

                    show_card_history()

                else:

                    show_bank_history()

            self.run(action)

        # ====================================================
        # INITIALIZE TRANSACTION FORM
        # ====================================================

        kind.configure(
            command=update_destination_fields
        )

        transfer_mode.configure(
            command=update_destination_fields
        )

        source.configure(
            command=update_card_info
        )

        history_mode.configure(
            command=refresh_transactions
        )

        kind.set("Deposit")

        transfer_mode.set(
            "My Own Accounts"
        )

        if account_labels:

            source.set(
                account_labels[0]
            )

            own_destination.set(
                account_labels[0]
            )

        else:

            source.set(
                "No available accounts"
            )

            own_destination.set(
                "No available accounts"
            )

        update_destination_fields()

        refresh_transactions()


    # ============================================================
    # FRAUD DETECTION SCREEN
    # ============================================================

    def show_fraud(self):
        self.db.require_admin()

        page = self.page("Fraud Detection & Alerts")

        rows = self.db.alerts()

        # ====================================================
        # FRAUD MONITORING PANEL
        # ====================================================

        actions = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=14
        )

        actions.pack(
            fill="x",
            padx=20,
            pady=(8, 8)
        )

        ctk.CTkLabel(
            actions,
            text="Fraud Monitoring",
            font=("Arial", 19, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(14, 3)
        )

        ctk.CTkLabel(
            actions,
            text=(
                "Scan bank and credit card transactions "
                "and review suspicious activity."
            ),
            font=("Arial", 12),
            text_color=MUTED,
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        # ====================================================
        # RUN FRAUD DETECTION
        # ====================================================

        def scan():

            def action():

                count = self.db.scan_fraud()

                self.show_ok(
                    "Fraud Detection",
                    (
                        "Fraud detection completed.\n\n"
                        f"{count} new fraud alerts created."
                    )
                )

                self.show_fraud()

            self.run(action)

        # ====================================================
        # MONITORING ACTION BUTTONS
        # ====================================================

        action_buttons = ctk.CTkFrame(
            actions,
            fg_color="transparent"
        )

        action_buttons.pack(
            fill="x",
            padx=14,
            pady=(0, 14)
        )

        self.button(
            action_buttons,
            "Run Fraud Detection",
            scan,
            width=200
        ).pack(
            side="left",
            padx=6
        )

        self.button(
            action_buttons,
            "Refresh",
            lambda: self.run(
                self.show_fraud
            ),
            width=110
        ).pack(
            side="left",
            padx=6
        )

        # ====================================================
        # TRANSACTION SOURCE FILTER
        # ====================================================

        source_filter = ctk.CTkComboBox(
            action_buttons,
            values=[
                "All Transactions",
                "Bank Transactions",
                "Credit Card Transactions"
            ],
            width=215,
            height=36,
            corner_radius=9,
            state="readonly"
        )

        source_filter.pack(
            side="right",
            padx=6
        )

        source_filter.set(
            "All Transactions"
        )

        ctk.CTkLabel(
            action_buttons,
            text="Transaction Source:",
            font=("Arial", 12),
            text_color=MUTED
        ).pack(
            side="right",
            padx=6
        )

        # ====================================================
        # REVIEW ACTIONS - ALWAYS VISIBLE
        # ====================================================

        review_actions = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=14
        )

        review_actions.pack(
            fill="x",
            padx=20,
            pady=(0, 8)
        )

        review_header = ctk.CTkFrame(
            review_actions,
            fg_color="transparent"
        )

        review_header.pack(
            fill="x",
            padx=18,
            pady=(12, 7)
        )

        ctk.CTkLabel(
            review_header,
            text="Fraud Review Actions",
            font=("Arial", 15, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            review_header,
            text=(
                "Select a pending alert "
                "to make a decision."
            ),
            font=("Arial", 12),
            text_color=MUTED,
            anchor="w"
        ).pack(
            fill="x",
            pady=(3, 0)
        )

        decision_row = ctk.CTkFrame(
            review_actions,
            fg_color="transparent"
        )

        decision_row.pack(
            fill="x",
            padx=12,
            pady=(0, 12)
        )

        # ====================================================
        # ALERT TABLE COLUMNS
        # ====================================================

        columns = (
            "alert",
            "transaction",
            "source",
            "rule",
            "type",
            "sender",
            "sender_account",
            "receiver",
            "receiver_account",
            "amount",
            "transaction_description",
            "risk",
            "status",
            "created",
            "review_note"
        )

        headings = (
            "Alert ID",
            "Transaction ID",
            "Source",
            "Fraud Rule",
            "Type",
            "Sender Customer",
            "Sender Account",
            "Receiver Customer",
            "Receiver Account",
            "Amount (TRY)",
            "Transaction Description",
            "Risk",
            "Status",
            "Created",
            "Admin Review Note"
        )

        # ====================================================
        # LOWER SECTION
        # ====================================================

        lower_section = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        lower_section.pack(
            side="bottom",
            fill="x",
            padx=20,
            pady=(0, 8)
        )

        # ====================================================
        # SELECTED ALERT DETAILS
        # ====================================================

        info = ctk.CTkFrame(
            lower_section,
            fg_color=CARD,
            corner_radius=14
        )

        info.pack(
            fill="x",
            pady=(0, 7)
        )

        ctk.CTkLabel(
            info,
            text="Selected Alert Details",
            font=("Arial", 15, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(
            fill="x",
            padx=18,
            pady=(11, 5)
        )

        detail_label = ctk.CTkLabel(
            info,
            text=(
                "Select an alert from the table "
                "to view its details."
            ),
            text_color=WHITE,
            font=("Arial", 12),
            justify="left",
            anchor="w",
            wraplength=1100
        )

        detail_label.pack(
            fill="x",
            padx=18,
            pady=(0, 11)
        )

        # ====================================================
        # ADMIN REVIEW NOTE
        # ====================================================

        review_frame = ctk.CTkFrame(
            lower_section,
            fg_color=CARD,
            corner_radius=14
        )

        review_frame.pack(
            fill="x"
        )

        note_header = ctk.CTkFrame(
            review_frame,
            fg_color="transparent"
        )

        note_header.pack(
            fill="x",
            padx=18,
            pady=(10, 5)
        )

        ctk.CTkLabel(
            note_header,
            text="Admin Review Note",
            text_color=WHITE,
            font=("Arial", 15, "bold"),
            anchor="w"
        ).pack(
            side="left"
        )

        ctk.CTkLabel(
            note_header,
            text=(
                "Optional - maximum 500 characters"
            ),
            text_color=MUTED,
            font=("Arial", 11)
        ).pack(
            side="right"
        )

        review_note = ctk.CTkTextbox(
            review_frame,
            height=60,
            fg_color=SIDEBAR,
            text_color=WHITE,
            corner_radius=10,
            font=("Arial", 12)
        )

        review_note.pack(
            fill="x",
            padx=18,
            pady=(0, 12)
        )

        review_note.configure(
            state="disabled"
        )

        # ====================================================
        # ALERT TABLE
        # ====================================================

        fraud_style = ttk.Style()
        previous_fraud_theme = fraud_style.theme_use()

        # Windows native themes may ignore Treeview colors.
        if previous_fraud_theme != "clam":
            fraud_style.theme_use("clam")

        fraud_style.configure(
            "FraudAlerts.Treeview",
            background="#17263F",
            fieldbackground="#17263F",
            foreground="#F5F8FF",
            rowheight=36,
            font=("Arial", 11),
            borderwidth=0,
            relief="flat"
        )

        fraud_style.configure(
            "FraudAlerts.Treeview.Heading",
            background="#243A59",
            foreground="#FFFFFF",
            font=("Arial", 11, "bold"),
            padding=(10, 9),
            borderwidth=0,
            relief="flat"
        )

        fraud_style.map(
            "FraudAlerts.Treeview",
            background=[
                ("selected", "#3478F6")
            ],
            foreground=[
                ("selected", "#FFFFFF")
            ]
        )

        fraud_style.map(
            "FraudAlerts.Treeview.Heading",
            background=[
                ("active", "#304B70")
            ],
            foreground=[
                ("active", "#FFFFFF")
            ]
        )

        # ====================================================
        # DARK SCROLLBARS
        # ====================================================

        for orientation in ("Vertical", "Horizontal"):
            scrollbar_style = (
                f"FraudAlerts.{orientation}.TScrollbar"
            )

            fraud_style.configure(
                scrollbar_style,
                background="#304B70",
                troughcolor="#111F35",
                arrowcolor="#FFFFFF",
                bordercolor="#17263F",
                lightcolor="#304B70",
                darkcolor="#304B70",
                borderwidth=0,
                relief="flat",
                width=13
            )

            fraud_style.map(
                scrollbar_style,
                background=[
                    ("active", "#456B9B"),
                    ("pressed", "#3478F6")
                ]
            )

        # ====================================================
        # CREATE TABLE - ORIGINAL COLUMNS
        # ====================================================

        tree = self.table(
            page,
            columns,
            headings
        )

        tree.configure(
            style="FraudAlerts.Treeview",
            selectmode="browse"
        )

        # ====================================================
        # APPLY DARK SCROLLBARS
        # ====================================================

        table_frame = tree.master

        for widget in table_frame.winfo_children():
            if isinstance(widget, ttk.Scrollbar):
                orientation = str(widget.cget("orient"))

                widget.configure(
                    style=(
                        "FraudAlerts.Vertical.TScrollbar"
                        if orientation == "vertical"
                        else "FraudAlerts.Horizontal.TScrollbar"
                    )
                )

        # ====================================================
        # RESTORE PREVIOUS THEME ON PAGE CHANGE
        # ====================================================

        def restore_fraud_theme(event):
            if event.widget is tree:
                current_style = ttk.Style()

                if current_style.theme_use() != previous_fraud_theme:
                    current_style.theme_use(previous_fraud_theme)

        tree.bind(
            "<Destroy>",
            restore_fraud_theme,
            add="+"
        )

        # ====================================================
        # ORIGINAL COLUMN SETTINGS
        # ====================================================

        tree.column(
            "source",
            width=110,
            minwidth=90
        )

        tree.column(
            "transaction_description",
            width=230,
            minwidth=150,
            anchor="w"
        )

        tree.column(
            "review_note",
            width=280,
            minwidth=150,
            anchor="w"
        )

        # ====================================================
        # FRAUD ALERT ROW STRUCTURE
        # ====================================================

        # Existing fraud.py row indexes:
        #
        # 0  AlertID
        # 1  Transaction Reference / ID
        # 2  RuleName
        # 3  TransactionType
        # 4  SenderCustomerID
        # 5  SenderCustomer
        # 6  SenderAccountNumber
        # 7  ReceiverCustomerID
        # 8  ReceiverCustomer
        # 9  ReceiverAccountNumber
        # 10 Amount
        # 11 AlertDescription
        # 12 RiskLevel
        # 13 ReviewStatus
        # 14 CreatedAt
        # 15 ReviewedAt
        # 16 ReviewNote
        # 17 TransactionDescription

        alert_details = {}

        # ====================================================
        # SAFE TEXT FORMATTING
        # ====================================================

        def safe_text(value):

            if value is None:

                return "-"

            text = str(value).strip()

            return text or "-"

        # ====================================================
        # DETERMINE TRANSACTION SOURCE
        # ====================================================

        def get_transaction_source(row):

            transaction_type = safe_text(
                row[3]
            )

            reference = safe_text(
                row[1]
            ).upper()

            card_types = (
                "Purchase",
                "Credit Card Purchase",
                "CreditCardPurchase",
                "CashAdvance",
                "Cash Advance",
                "CardPayment",
                "Payment",
                "Debt Payment",
                "Pay Credit Card Debt",
                "Refund"
            )

            if (
                transaction_type in card_types
                or reference.startswith("CC-")
            ):

                return "Credit Card"

            return "Bank"

        # ====================================================
        # DISPLAY TRANSACTION REFERENCE
        # ====================================================

        def get_transaction_reference(row):

            reference = safe_text(
                row[1]
            )

            transaction_type = safe_text(
                row[3]
            )

            if reference == "-":

                return reference

            if reference.upper().startswith("CC-"):

                return reference

            # Purchases use independent card transaction IDs.
            # Cash advances and payments use bank transaction IDs
            # when fraud alerts originate from the bank scan.

            if transaction_type in (
                "Purchase",
                "Credit Card Purchase",
                "CreditCardPurchase"
            ):

                return f"CC-{reference}"

            return reference

        # ====================================================
        # DISPLAY TRANSACTION TYPE
        # ====================================================

        def get_transaction_type(row):

            transaction_type = safe_text(
                row[3]
            )

            type_labels = {
                "Purchase": "Credit Card Purchase",
                "CreditCardPurchase": "Credit Card Purchase",
                "CashAdvance": "Cash Advance",
                "CardPayment": "Debt Payment",
                "Payment": "Debt Payment",
                "Refund": "Credit Card Refund"
            }

            return type_labels.get(
                transaction_type,
                transaction_type
            )

        # ====================================================
        # RESET SELECTED ALERT DETAILS
        # ====================================================

        def clear_selection_details():

            detail_label.configure(
                text=(
                    "Select an alert from the table "
                    "to view its details."
                )
            )

            review_note.configure(
                state="normal"
            )

            review_note.delete(
                "1.0",
                "end"
            )

            review_note.configure(
                state="disabled"
            )

            for button in decision_buttons:

                button.configure(
                    state="disabled"
                )

        # ====================================================
        # LOAD FRAUD ALERTS
        # ====================================================

        def load_alerts(*args):

            tree.delete(
                *tree.get_children()
            )

            alert_details.clear()

            clear_selection_details()

            selected_filter = (
                source_filter.get()
            )

            for row in rows:

                alert_id = int(
                    row[0]
                )

                transaction_source = (
                    get_transaction_source(row)
                )

                # ============================================
                # APPLY TRANSACTION SOURCE FILTER
                # ============================================

                if (
                    selected_filter == "Bank Transactions"
                    and transaction_source != "Bank"
                ):

                    continue

                if (
                    selected_filter
                    == "Credit Card Transactions"
                    and transaction_source != "Credit Card"
                ):

                    continue

                alert_details[alert_id] = row

                transaction_reference = (
                    get_transaction_reference(row)
                )

                transaction_type = (
                    get_transaction_type(row)
                )

                sender = safe_text(
                    row[5]
                )

                receiver = safe_text(
                    row[8]
                )

                sender_account = safe_text(
                    row[6]
                )

                receiver_account = safe_text(
                    row[9]
                )

                transaction_description = (
                    safe_text(row[17])
                )

                admin_review_note = (
                    safe_text(row[16])
                )

                tree.insert(
                    "",
                    "end",
                    iid=str(alert_id),
                    values=(
                        alert_id,
                        transaction_reference,
                        transaction_source,
                        row[2],
                        transaction_type,
                        sender,
                        sender_account,
                        receiver,
                        receiver_account,
                        f"{row[10]:.2f}",
                        transaction_description,
                        row[12],
                        row[13],
                        str(row[14])[:19],
                        admin_review_note
                    )
                )

        # ====================================================
        # GET SELECTED ALERT
        # ====================================================

        def get_selected_alert():

            selected = tree.selection()

            if not selected:

                raise ValueError(
                    "Please select an alert from the table."
                )

            alert_id = int(
                selected[0]
            )

            if alert_id not in alert_details:

                raise ValueError(
                    "Selected alert is no longer available."
                )

            return (
                alert_id,
                alert_details[alert_id]
            )

        # ====================================================
        # SHOW SELECTED ALERT DETAILS
        # ====================================================

        def show_details(event=None):

            selected = tree.selection()

            if not selected:

                clear_selection_details()

                return

            alert_id = int(
                selected[0]
            )

            if alert_id not in alert_details:

                clear_selection_details()

                return

            row = alert_details[alert_id]

            transaction_source = (
                get_transaction_source(row)
            )

            transaction_reference = (
                get_transaction_reference(row)
            )

            transaction_type = (
                get_transaction_type(row)
            )

            transaction_description = (
                safe_text(row[17])
            )

            saved_review_note = (
                str(row[16])
                if row[16] is not None
                else ""
            )

            # ================================================
            # CREDIT CARD FRAUD DETAILS
            # ================================================

            if transaction_source == "Credit Card":

                customer_name = (
                    row[5]
                    or row[8]
                    or "-"
                )

                linked_account = (
                    row[6]
                    or row[9]
                    or "-"
                )

                participant_details = (
                    f"Customer: {customer_name}\n"
                    f"Account: "
                    f"{str(linked_account).strip()}"
                )

            # ================================================
            # BANK TRANSACTION FRAUD DETAILS
            # ================================================

            else:

                participant_details = (
                    f"Sender: {safe_text(row[5])}    "
                    f"Receiver: {safe_text(row[8])}\n"
                    f"From Account: "
                    f"{safe_text(row[6])}    "
                    f"To Account: "
                    f"{safe_text(row[9])}"
                )

            detail_label.configure(
                text=(
                    f"Alert ID: {row[0]}    "
                    f"Transaction ID: "
                    f"{transaction_reference}\n"

                    f"Source: {transaction_source}    "
                    f"Type: {transaction_type}\n"

                    f"Rule: {row[2]}\n"

                    f"{participant_details}\n"

                    f"Amount: {row[10]:.2f} TRY    "
                    f"Risk: {row[12]}\n"

                    f"Transaction Description: "
                    f"{transaction_description}\n"

                    f"Status: {row[13]}\n"

                    f"Reason: {row[11]}"
                )
            )

            # ================================================
            # UPDATE ADMIN REVIEW NOTE
            # ================================================

            review_note.configure(
                state="normal"
            )

            review_note.delete(
                "1.0",
                "end"
            )

            is_pending = (
                row[13] == "Pending"
            )

            if saved_review_note:

                review_note.insert(
                    "1.0",
                    saved_review_note
                )

            review_note.configure(
                state=(
                    "normal"
                    if is_pending
                    else "disabled"
                )
            )

            # ================================================
            # UPDATE DECISION BUTTON STATES
            # ================================================

            for button in decision_buttons:

                button.configure(
                    state=(
                        "normal"
                        if is_pending
                        else "disabled"
                    )
                )

        # ====================================================
        # CHANGE FRAUD REVIEW STATUS
        # ====================================================

        def change_status(status):

            def action():

                alert_id, row = (
                    get_selected_alert()
                )

                allowed_statuses = (
                    "Reviewed",
                    "FalsePositive",
                    "ConfirmedFraud"
                )

                if status not in allowed_statuses:

                    raise ValueError(
                        "Invalid fraud review status."
                    )

                if row[13] != "Pending":

                    raise ValueError(
                        "This alert has already been reviewed."
                    )

                note = review_note.get(
                    "1.0",
                    "end-1c"
                ).strip()

                if len(note) > 500:

                    raise ValueError(
                        "Review note cannot exceed "
                        "500 characters."
                    )

                transaction_source = (
                    get_transaction_source(row)
                )

                transaction_reference = (
                    get_transaction_reference(row)
                )

                transaction_type = (
                    get_transaction_type(row)
                )

                warning = ""

                # ============================================
                # CONFIRMED CREDIT CARD FRAUD
                # ============================================

                if status == "ConfirmedFraud":

                    if transaction_source == "Credit Card":

                        warning = (
                            "\nSECURITY ACTION:\n"
                            "The linked bank account "
                            "will be frozen.\n"
                            "New credit card purchases, "
                            "cash advances and debt payments "
                            "using this account will be "
                            "restricted.\n"
                            "Deposits, withdrawals and "
                            "transfers involving the affected "
                            "account will also be disabled.\n"
                            "Existing balances, card debt "
                            "and transaction history will "
                            "be preserved.\n"
                            "The customer will receive "
                            "a notification.\n"
                        )

                    # ========================================
                    # CONFIRMED BANK FRAUD
                    # ========================================

                    else:

                        warning = (
                            "\nSECURITY ACTION:\n"
                            "The affected bank account "
                            "will be frozen.\n"
                            "Deposits, withdrawals and "
                            "transfers will be disabled.\n"
                            "Credit card operations linked "
                            "to this account will also "
                            "be restricted.\n"
                            "The existing balance and "
                            "transaction history will "
                            "be preserved.\n"
                            "The customer will receive "
                            "a notification.\n"
                        )

                # ============================================
                # CONFIRM ADMIN DECISION
                # ============================================

                confirmed = self.ask_yes_no(
                    "Confirm Decision",
                    (
                        f"Alert ID: {alert_id}\n"

                        f"Transaction ID: "
                        f"{transaction_reference}\n"

                        f"Source: "
                        f"{transaction_source}\n"

                        f"Type: "
                        f"{transaction_type}\n"

                        f"New Status: {status}\n"

                        f"Review Note: "
                        f"{note or '(empty)'}\n"

                        f"{warning}\n"

                        "Do you want to continue?"
                    )
                )

                if not confirmed:

                    return

                # ============================================
                # EXECUTE EXISTING FRAUD REVIEW BACKEND
                # ============================================

                self.db.review(
                    alert_id,
                    status,
                    note
                )

                # ============================================
                # SUCCESS MESSAGE
                # ============================================

                success_message = (
                    f"Alert marked as {status}.\n"
                    "Review information saved."
                )

                if status == "ConfirmedFraud":

                    success_message += (
                        "\n\n"
                        "The affected bank account "
                        "has been restricted."
                    )

                self.show_ok(
                    "Success",
                    success_message
                )

                self.show_fraud()

            self.run(action)

        # ====================================================
        # MARK REVIEWED BUTTON
        # ====================================================

        reviewed_button = self.button(
            decision_row,
            "Mark Reviewed",
            lambda: change_status(
                "Reviewed"
            ),
            width=170
        )

        reviewed_button.pack(
            side="left",
            padx=6
        )

        # ====================================================
        # FALSE POSITIVE BUTTON
        # ====================================================

        false_positive_button = self.button(
            decision_row,
            "False Positive",
            lambda: change_status(
                "FalsePositive"
            ),
            width=170
        )

        false_positive_button.pack(
            side="left",
            padx=6
        )

        # ====================================================
        # CONFIRM FRAUD BUTTON
        # ====================================================

        confirm_fraud_button = self.button(
            decision_row,
            "Confirm Fraud",
            lambda: change_status(
                "ConfirmedFraud"
            ),
            width=170
        )

        confirm_fraud_button.pack(
            side="left",
            padx=6
        )

        # ====================================================
        # BUTTON STATE MANAGEMENT
        # ====================================================

        decision_buttons = (
            reviewed_button,
            false_positive_button,
            confirm_fraud_button
        )

        for button in decision_buttons:

            button.configure(
                state="disabled"
            )

        # ====================================================
        # TRANSACTION SOURCE FILTER EVENT
        # ====================================================

        source_filter.configure(
            command=lambda value: self.run(
                load_alerts
            )
        )

        # ====================================================
        # TABLE SELECTION EVENT
        # ====================================================

        tree.bind(
            "<<TreeviewSelect>>",
            show_details
        )

        # ====================================================
        # INITIAL FRAUD ALERTS
        # ====================================================

        self.run(load_alerts)

    # ============================================================
    # FRAUD RULES SCREEN
    # ============================================================

    def show_rules(self):
        self.db.require_admin()

        page = self.page("Fraud Rules")

        # ====================================================
        # FRAUD RULES - COLOR PALETTE
        # ====================================================

        panel_color = "#17263F"
        header_color = "#243A59"
        border_color = "#2B4161"
        text_color = "#F5F8FF"
        muted_color = "#9EB2D0"

        # ====================================================
        # FRAUD DETECTION RULES BANNER
        # ====================================================

        overview = ctk.CTkFrame(
            page,
            fg_color=panel_color,
            corner_radius=15,
            border_width=1,
            border_color=border_color
        )
        overview.pack(
            fill="x",
            padx=22,
            pady=(8, 16)
        )

        banner_content = ctk.CTkFrame(
            overview,
            fg_color="transparent"
        )
        banner_content.pack(
            fill="x",
            padx=22,
            pady=20
        )

        icon_box = ctk.CTkFrame(
            banner_content,
            width=62,
            height=62,
            fg_color="#214575",
            corner_radius=13
        )
        icon_box.pack(side="left", padx=(0, 18))
        icon_box.pack_propagate(False)

        ctk.CTkLabel(
            icon_box,
            text="✓",
            font=("Arial", 30, "bold"),
            text_color="#93C5FD"
        ).pack(expand=True)

        banner_text = ctk.CTkFrame(
            banner_content,
            fg_color="transparent"
        )
        banner_text.pack(
            side="left",
            fill="both",
            expand=True
        )

        ctk.CTkLabel(
            banner_text,
            text="Fraud Detection Rules",
            font=("Arial", 20, "bold"),
            text_color=text_color,
            anchor="w"
        ).pack(
            fill="x",
            pady=(3, 7)
        )

        ctk.CTkLabel(
            banner_text,
            text=(
                "Review the configured fraud detection rules, "
                "thresholds, monitoring windows and activation status."
            ),
            font=("Arial", 12),
            text_color=muted_color,
            anchor="w",
            justify="left",
            wraplength=900
        ).pack(fill="x")

        # ====================================================
        # CONFIGURED RULES HEADER
        # ====================================================

        section = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )
        section.pack(
            fill="x",
            padx=22,
            pady=(6, 14)
        )

        ctk.CTkLabel(
            section,
            text="☷  Configured Rules",
            font=("Arial", 19, "bold"),
            text_color=text_color,
            anchor="w"
        ).pack(side="left")

        # ====================================================
        # DARK RULES TABLE CONTAINER
        # ====================================================

        table_holder = ctk.CTkFrame(
            page,
            fg_color=panel_color,
            corner_radius=14,
            border_width=1,
            border_color=border_color
        )
        table_holder.pack(
            fill="both",
            expand=True,
            padx=22,
            pady=(0, 18)
        )

        table_area = ctk.CTkFrame(
            table_holder,
            fg_color=panel_color
        )
        table_area.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=12
        )

        # ====================================================
        # DARK TREEVIEW THEME
        # ====================================================

        style = ttk.Style()
        previous_theme = style.theme_use()

        if previous_theme != "clam":
            style.theme_use("clam")

        style.configure(
            "FraudRules.Treeview",
            background=panel_color,
            fieldbackground=panel_color,
            foreground=text_color,
            rowheight=44,
            font=("Arial", 11),
            borderwidth=0,
            relief="flat"
        )

        style.configure(
            "FraudRules.Treeview.Heading",
            background=header_color,
            foreground="#FFFFFF",
            font=("Arial", 11, "bold"),
            padding=(10, 12),
            borderwidth=0,
            relief="flat"
        )

        style.map(
            "FraudRules.Treeview",
            background=[
                ("selected", "#3478F6")
            ],
            foreground=[
                ("selected", "#FFFFFF")
            ]
        )

        style.map(
            "FraudRules.Treeview.Heading",
            background=[
                ("active", "#304B70"),
                ("pressed", header_color)
            ],
            foreground=[
                ("active", "#FFFFFF")
            ]
        )

        # ====================================================
        # DARK SCROLLBAR STYLES
        # ====================================================

        for orientation in ("Vertical", "Horizontal"):
            scrollbar_style = (
                f"FraudRules.{orientation}.TScrollbar"
            )

            style.configure(
                scrollbar_style,
                background="#304B70",
                troughcolor="#111F35",
                arrowcolor="#FFFFFF",
                bordercolor=panel_color,
                lightcolor="#304B70",
                darkcolor="#304B70",
                borderwidth=0,
                relief="flat",
                width=13
            )

            style.map(
                scrollbar_style,
                background=[
                    ("active", "#456B9B"),
                    ("pressed", "#3478F6")
                ]
            )

        # ====================================================
        # FRAUD RULES TABLE
        # ====================================================

        columns = (
            "id",
            "name",
            "type",
            "threshold",
            "window",
            "active"
        )

        headings = (
            "ID",
            "Rule Name",
            "Rule Type",
            "Threshold",
            "Window (min)",
            "Active"
        )

        tree = ttk.Treeview(
            table_area,
            columns=columns,
            show="headings",
            style="FraudRules.Treeview",
            selectmode="browse"
        )

        column_specs = (
            ("id", "ID", 80, "center"),
            ("name", "Rule Name", 260, "w"),
            ("type", "Rule Type", 190, "center"),
            ("threshold", "Threshold", 160, "center"),
            ("window", "Window (min)", 150, "center"),
            ("active", "Active", 120, "center")
        )

        for key, title, width, anchor in column_specs:
            tree.heading(
                key,
                text=title
            )

            tree.column(
                key,
                width=width,
                minwidth=70,
                anchor=anchor,
                stretch=True
            )

        # ====================================================
        # DARK SCROLLBARS
        # ====================================================

        yscroll = ttk.Scrollbar(
            table_area,
            orient="vertical",
            command=tree.yview,
            style="FraudRules.Vertical.TScrollbar"
        )

        xscroll = ttk.Scrollbar(
            table_area,
            orient="horizontal",
            command=tree.xview,
            style="FraudRules.Horizontal.TScrollbar"
        )

        tree.configure(
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set
        )

        yscroll.pack(
            side="right",
            fill="y"
        )

        xscroll.pack(
            side="bottom",
            fill="x"
        )

        tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        # ====================================================
        # ALTERNATING ROW COLORS
        # ====================================================

        tree.tag_configure(
            "even",
            background="#17263F",
            foreground="#F5F8FF"
        )

        tree.tag_configure(
            "odd",
            background="#1C2D48",
            foreground="#F5F8FF"
        )

        # ====================================================
        # LOAD FRAUD RULES FROM DATABASE
        # ====================================================

        rules = self.db.fraud_rules()

        for index, rule in enumerate(rules):
            parity = "even" if index % 2 == 0 else "odd"

            tree.insert(
                "",
                "end",
                values=(
                    rule[0],
                    rule[1],
                    rule[2],
                    rule[3],
                    rule[4],
                    rule[5]
                ),
                tags=(parity,)
            )

        # ====================================================
        # RESTORE PREVIOUS THEME WHEN LEAVING PAGE
        # ====================================================

        def restore_rules_theme(event):
            if event.widget is table_holder:
                current_style = ttk.Style()

                if current_style.theme_use() != previous_theme:
                    current_style.theme_use(previous_theme)

        table_holder.bind(
            "<Destroy>",
            restore_rules_theme,
            add="+"
        )

        # No Refresh Rules button.
        # Rules are loaded when the page is opened.

    # ============================================================
    # CUSTOMER FRAUD REVIEWS SCREEN
    # ============================================================

    def show_customer_fraud_reviews(self):
        session = self.db.require_login()

        if session["role"] != "Customer":

            raise PermissionError(
                "This page is for customers only."
            )

        page = self.page("My Fraud Reviews")

        # ====================================================
        # PAGE DESCRIPTION
        # ====================================================

        ctk.CTkLabel(
            page,
            text=(
                "Admin reviews related to your bank "
                "and credit card transactions."
            ),
            text_color=MUTED,
            font=("Arial", 15)
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 12)
        )

        # ====================================================
        # FRAUD REVIEW SUMMARY
        # ====================================================

        summary = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        summary.pack(
            fill="x",
            padx=20,
            pady=(0, 12)
        )

        for column in range(4):

            summary.grid_columnconfigure(
                column,
                weight=1,
                uniform="fraud_summary"
            )

        summary_labels = {}

        summary_items = [
            (
                "total",
                "Total Reviews",
                WHITE
            ),
            (
                "reviewed",
                "Reviewed",
                "#60A5FA"
            ),
            (
                "false_positive",
                "False Positive",
                "#4ADE80"
            ),
            (
                "confirmed",
                "Confirmed Fraud",
                "#F87171"
            )
        ]

        for index, (
            key,
            title,
            color
        ) in enumerate(summary_items):

            summary_card = ctk.CTkFrame(
                summary,
                fg_color=CARD,
                corner_radius=14
            )

            summary_card.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=5,
                pady=5
            )

            ctk.CTkLabel(
                summary_card,
                text=title,
                font=("Arial", 12),
                text_color=MUTED,
                anchor="w"
            ).pack(
                fill="x",
                padx=16,
                pady=(14, 4)
            )

            value_label = ctk.CTkLabel(
                summary_card,
                text="0",
                font=("Arial", 26, "bold"),
                text_color=color,
                anchor="w"
            )

            value_label.pack(
                fill="x",
                padx=16,
                pady=(0, 14)
            )

            summary_labels[key] = value_label

        # ====================================================
        # REVIEW FILTER PANEL
        # ====================================================

        filters = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=14
        )

        filters.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        filter_row = ctk.CTkFrame(
            filters,
            fg_color="transparent"
        )

        filter_row.pack(
            fill="x",
            padx=16,
            pady=14
        )

        ctk.CTkLabel(
            filter_row,
            text="Transaction Source:",
            font=("Arial", 12, "bold"),
            text_color=WHITE
        ).pack(
            side="left",
            padx=(0, 8)
        )

        source_filter = ctk.CTkComboBox(
            filter_row,
            values=[
                "All Transactions",
                "Bank Transactions",
                "Credit Card Transactions"
            ],
            width=210,
            height=36,
            corner_radius=9,
            state="readonly"
        )

        source_filter.pack(
            side="left",
            padx=(0, 15)
        )

        source_filter.set(
            "All Transactions"
        )

        # ====================================================
        # REVIEW STATUS FILTER
        # ====================================================

        ctk.CTkLabel(
            filter_row,
            text="Review Status:",
            font=("Arial", 12, "bold"),
            text_color=WHITE
        ).pack(
            side="left",
            padx=(0, 8)
        )

        status_filter = ctk.CTkComboBox(
            filter_row,
            values=[
                "All Statuses",
                "Reviewed",
                "False Positive",
                "Confirmed Fraud"
            ],
            width=165,
            height=36,
            corner_radius=9,
            state="readonly"
        )

        status_filter.pack(
            side="left",
            padx=(0, 10)
        )

        status_filter.set(
            "All Statuses"
        )

        # ====================================================
        # TABLE COLUMNS
        # ====================================================

        columns = (
            "alert",
            "transaction",
            "source",
            "type",
            "amount",
            "transaction_description",
            "rule",
            "risk",
            "status",
            "note",
            "reviewed"
        )

        headings = (
            "Alert ID",
            "Transaction ID",
            "Source",
            "Transaction Type",
            "Amount (TRY)",
            "Transaction Description",
            "Fraud Rule",
            "Risk",
            "Review Status",
            "Admin Review Note",
            "Reviewed At"
        )

        # ====================================================
        # LOWER SECTION
        # ====================================================

        lower_section = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        lower_section.pack(
            side="bottom",
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        # ====================================================
        # SELECTED REVIEW DETAILS
        # ====================================================

        details_frame = ctk.CTkFrame(
            lower_section,
            fg_color=CARD,
            corner_radius=14
        )

        details_frame.pack(
            fill="x",
            pady=(0, 8)
        )

        ctk.CTkLabel(
            details_frame,
            text="Selected Review Details",
            font=("Arial", 16, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(
            fill="x",
            padx=18,
            pady=(12, 5)
        )

        detail_label = ctk.CTkLabel(
            details_frame,
            text=(
                "Select a review from the table "
                "to view its details."
            ),
            font=("Arial", 12),
            text_color=WHITE,
            justify="left",
            anchor="w",
            wraplength=1000
        )

        detail_label.pack(
            fill="x",
            padx=18,
            pady=(0, 10)
        )

        # ====================================================
        # SECURITY INFORMATION
        # ====================================================

        security_label = ctk.CTkLabel(
            details_frame,
            text="",
            font=("Arial", 12),
            text_color="#FBBF24",
            justify="left",
            anchor="w",
            wraplength=1000
        )

        # Initially hidden.
        # Display only when a reviewed alert is selected.

        # ====================================================
        # REVIEW RESULT INFORMATION
        # ====================================================

        result_label = ctk.CTkLabel(
            lower_section,
            text="",
            font=("Arial", 12),
            text_color=MUTED,
            anchor="w"
        )

        result_label.pack(
            fill="x",
            padx=5,
            pady=(2, 0)
        )

        # ====================================================
        # REVIEWS TABLE
        # ====================================================

        tree = self.table(
            page,
            columns,
            headings
        )

        tree.configure(
            selectmode="browse"
        )

        tree.column(
            "source",
            width=110,
            minwidth=90
        )

        tree.column(
            "transaction_description",
            width=230,
            minwidth=150,
            anchor="w"
        )

        tree.column(
            "note",
            width=350,
            minwidth=150,
            anchor="w"
        )

        # ====================================================
        # CUSTOMER FRAUD REVIEW ROW STRUCTURE
        # ====================================================

        # Row indexes from fraud.py:
        #
        # 0 AlertID
        # 1 TransactionReference / TransactionID
        # 2 TransactionType
        # 3 Amount
        # 4 RuleName
        # 5 RiskLevel
        # 6 ReviewStatus
        # 7 ReviewNote
        # 8 ReviewedAt
        # 9 TransactionDescription

        review_details = {}

        all_reviews = []

        # ====================================================
        # SAFE TEXT FORMATTING
        # ====================================================

        def safe_text(value):

            if value is None:

                return "-"

            text = str(value).strip()

            return text or "-"

        # ====================================================
        # TRANSACTION SOURCE
        # ====================================================

        def get_transaction_source(row):

            transaction_type = safe_text(
                row[2]
            )

            reference = safe_text(
                row[1]
            ).upper()

            card_types = (
                "Purchase",
                "Credit Card Purchase",
                "CreditCardPurchase",
                "CashAdvance",
                "Cash Advance",
                "CardPayment",
                "Payment",
                "Debt Payment",
                "Pay Credit Card Debt",
                "Refund"
            )

            if (
                transaction_type in card_types
                or reference.startswith("CC-")
            ):

                return "Credit Card"

            return "Bank"

        # ====================================================
        # TRANSACTION REFERENCE
        # ====================================================

        def get_transaction_reference(row):

            reference = safe_text(
                row[1]
            )

            transaction_type = safe_text(
                row[2]
            )

            if reference == "-":

                return reference

            if reference.upper().startswith("CC-"):

                return reference

            if transaction_type in (
                "Purchase",
                "Credit Card Purchase",
                "CreditCardPurchase"
            ):

                return f"CC-{reference}"

            return reference

        # ====================================================
        # TRANSACTION TYPE DISPLAY
        # ====================================================

        def get_transaction_type(row):

            transaction_type = safe_text(
                row[2]
            )

            type_labels = {
                "Purchase": "Credit Card Purchase",
                "CreditCardPurchase": "Credit Card Purchase",
                "CashAdvance": "Cash Advance",
                "CardPayment": "Debt Payment",
                "Payment": "Debt Payment",
                "Refund": "Credit Card Refund"
            }

            return type_labels.get(
                transaction_type,
                transaction_type
            )

        # ====================================================
        # REVIEW STATUS DISPLAY
        # ====================================================

        def get_review_status(status):

            status_labels = {
                "Reviewed": "Reviewed",
                "FalsePositive": "False Positive",
                "ConfirmedFraud": "Confirmed Fraud",
                "Pending": "Pending"
            }

            return status_labels.get(
                status,
                status
            )

        # ====================================================
        # UPDATE REVIEW SUMMARY
        # ====================================================

        def update_summary():

            total = len(all_reviews)

            reviewed = sum(
                1
                for row in all_reviews
                if row[6] == "Reviewed"
            )

            false_positive = sum(
                1
                for row in all_reviews
                if row[6] == "FalsePositive"
            )

            confirmed = sum(
                1
                for row in all_reviews
                if row[6] == "ConfirmedFraud"
            )

            summary_labels["total"].configure(
                text=str(total)
            )

            summary_labels["reviewed"].configure(
                text=str(reviewed)
            )

            summary_labels["false_positive"].configure(
                text=str(false_positive)
            )

            summary_labels["confirmed"].configure(
                text=str(confirmed)
            )

        # ====================================================
        # CLEAR SELECTED REVIEW
        # ====================================================

        def clear_details():

            detail_label.configure(
                text=(
                    "Select a review from the table "
                    "to view its details."
                )
            )

            security_label.configure(
                text=""
            )

            security_label.pack_forget()

        # ====================================================
        # APPLY REVIEW FILTERS
        # ====================================================

        def apply_filters(*args):

            tree.delete(
                *tree.get_children()
            )

            review_details.clear()

            clear_details()

            selected_source = source_filter.get()

            selected_status = status_filter.get()

            status_map = {
                "Reviewed": "Reviewed",
                "False Positive": "FalsePositive",
                "Confirmed Fraud": "ConfirmedFraud"
            }

            visible_count = 0

            for row in all_reviews:

                alert_id = int(
                    row[0]
                )

                transaction_source = (
                    get_transaction_source(row)
                )

                # ============================================
                # TRANSACTION SOURCE FILTER
                # ============================================

                if (
                    selected_source == "Bank Transactions"
                    and transaction_source != "Bank"
                ):

                    continue

                if (
                    selected_source
                    == "Credit Card Transactions"
                    and transaction_source != "Credit Card"
                ):

                    continue

                # ============================================
                # REVIEW STATUS FILTER
                # ============================================

                if selected_status != "All Statuses":

                    if row[6] != status_map.get(
                        selected_status
                    ):

                        continue

                # ============================================
                # STORE REVIEW DETAILS
                # ============================================

                review_details[alert_id] = row

                transaction_reference = (
                    get_transaction_reference(row)
                )

                transaction_type = (
                    get_transaction_type(row)
                )

                review_status = (
                    get_review_status(row[6])
                )

                transaction_description = (
                    safe_text(row[9])
                )

                admin_note = safe_text(
                    row[7]
                )

                reviewed_at = (
                    str(row[8])[:19]
                    if row[8] is not None
                    else "-"
                )

                # ============================================
                # INSERT REVIEW INTO TABLE
                # ============================================

                tree.insert(
                    "",
                    "end",
                    iid=str(alert_id),
                    values=(
                        alert_id,
                        transaction_reference,
                        transaction_source,
                        transaction_type,
                        f"{row[3]:.2f}",
                        transaction_description,
                        row[4],
                        row[5],
                        review_status,
                        admin_note,
                        reviewed_at
                    )
                )

                visible_count += 1

            # ================================================
            # UPDATE FILTER RESULT
            # ================================================

            result_label.configure(
                text=(
                    f"Showing {visible_count} "
                    f"of {len(all_reviews)} reviews."
                )
            )

            if not all_reviews:

                detail_label.configure(
                    text=(
                        "No completed fraud reviews "
                        "are available for your transactions."
                    )
                )

            elif visible_count == 0:

                detail_label.configure(
                    text=(
                        "No fraud reviews match "
                        "the selected filters."
                    )
                )

        # ====================================================
        # SHOW SELECTED REVIEW DETAILS
        # ====================================================

        def show_details(event=None):

            selection = tree.selection()

            if not selection:

                clear_details()

                return

            alert_id = int(
                selection[0]
            )

            if alert_id not in review_details:

                clear_details()

                return

            row = review_details[alert_id]

            transaction_reference = (
                get_transaction_reference(row)
            )

            transaction_source = (
                get_transaction_source(row)
            )

            transaction_type = (
                get_transaction_type(row)
            )

            review_status = (
                get_review_status(row[6])
            )

            reviewed_at = (
                str(row[8])[:19]
                if row[8] is not None
                else "-"
            )

            # ================================================
            # DISPLAY REVIEW INFORMATION
            # ================================================

            detail_label.configure(
                text=(
                    f"Alert ID: {alert_id}    "
                    f"Transaction ID: "
                    f"{transaction_reference}\n"

                    f"Source: {transaction_source}    "
                    f"Type: {transaction_type}\n"

                    f"Amount: {row[3]:,.2f} TRY    "
                    f"Risk: {safe_text(row[5])}\n"

                    f"Fraud Rule: {safe_text(row[4])}\n"

                    f"Transaction Description: "
                    f"{safe_text(row[9])}\n"

                    f"Review Status: {review_status}\n"

                    f"Admin Review Note: "
                    f"{safe_text(row[7])}\n"

                    f"Reviewed At: {reviewed_at}"
                )
            )

            # ================================================
            # CONFIRMED FRAUD INFORMATION
            # ================================================

            if row[6] == "ConfirmedFraud":

                security_label.configure(
                    text=(
                        "SECURITY NOTICE\n"
                        "This transaction was marked as "
                        "confirmed fraud by the administrator.\n"
                        "The affected account was restricted "
                        "following the original review. "
                        "Linked credit card operations may "
                        "also be unavailable while the "
                        "restriction remains active.\n"
                        "Your existing balance, credit card "
                        "debt and transaction history remain "
                        "available.\n"
                        "Please contact the bank administrator "
                        "for assistance."
                    ),
                    text_color="#FBBF24"
                )

            # ================================================
            # FALSE POSITIVE INFORMATION
            # ================================================

            elif row[6] == "FalsePositive":

                security_label.configure(
                    text=(
                        "REVIEW RESULT\n"
                        "The administrator classified this "
                        "alert as a false positive.\n"
                        "No account restriction was applied "
                        "as a result of this review."
                    ),
                    text_color="#4ADE80"
                )

            # ================================================
            # REVIEWED INFORMATION
            # ================================================

            elif row[6] == "Reviewed":

                security_label.configure(
                    text=(
                        "REVIEW RESULT\n"
                        "This alert has been reviewed "
                        "by the bank administrator."
                    ),
                    text_color="#60A5FA"
                )

            else:

                security_label.pack_forget()

                return

            security_label.pack(
                fill="x",
                padx=18,
                pady=(0, 14)
            )

        # ====================================================
        # REFRESH REVIEWS
        # ====================================================

        def refresh_reviews():

            rows = self.db.customer_fraud_reviews()

            all_reviews.clear()

            all_reviews.extend(rows)

            update_summary()

            apply_filters()

        # ====================================================
        # REFRESH REVIEWS BUTTON
        # ====================================================

        self.button(
            filter_row,
            "Refresh Reviews",
            lambda: self.run(
                refresh_reviews
            ),
            width=150
        ).pack(
            side="right",
            padx=(5, 0)
        )

        # ====================================================
        # FILTER EVENTS
        # ====================================================

        source_filter.configure(
            command=lambda value: self.run(
                apply_filters
            )
        )

        status_filter.configure(
            command=lambda value: self.run(
                apply_filters
            )
        )

        # ====================================================
        # REVIEW SELECTION EVENT
        # ====================================================

        tree.bind(
            "<<TreeviewSelect>>",
            show_details
        )

        # ====================================================
        # INITIAL REVIEW DATA
        # ====================================================

        self.run(refresh_reviews)

    # ============================================================
    # ADMIN - ADVANCED AUDIT LOGS
    # ============================================================


    def show_logs(self):
        self.db.require_admin()

        import csv
        from tkinter import filedialog

        page = self.page("Audit Logs")

        current_page = [1]
        current_result = [None]

        # ====================================================
        # HEADER
        # ====================================================

        header = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )
        header.pack(
            fill="x",
            padx=22,
            pady=(8, 14)
        )

        ctk.CTkLabel(
            header,
            text="Audit & Activity Logs",
            font=("Arial", 21, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            header,
            text="Search, filter and review banking activities.",
            font=("Arial", 12),
            text_color=MUTED,
            anchor="w"
        ).pack(
            fill="x",
            pady=(5, 0)
        )

        # ====================================================
        # AUDIT OVERVIEW CARDS
        # ====================================================

        audit_colors = {
            "panel": "#17263F",
            "header": "#243A59",
            "border": "#2B4161",
            "text": "#F5F8FF",
            "muted": "#9EB2D0",
            "blue": "#93C5FD"
        }

        overview_frame = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )
        overview_frame.pack(
            fill="x",
            padx=20,
            pady=(0, 12)
        )

        for index in range(3):
            overview_frame.grid_columnconfigure(
                index,
                weight=1,
                uniform="audit_overview"
            )

        def create_audit_card(column, title, color):
            card = ctk.CTkFrame(
                overview_frame,
                fg_color=audit_colors["panel"],
                corner_radius=14,
                border_width=1,
                border_color=audit_colors["border"]
            )
            card.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=5
            )

            ctk.CTkLabel(
                card,
                text=title,
                font=("Arial", 11, "bold"),
                text_color=audit_colors["muted"],
                anchor="w"
            ).pack(
                fill="x",
                padx=18,
                pady=(14, 6)
            )

            value_label = ctk.CTkLabel(
                card,
                text="—",
                font=("Arial", 25, "bold"),
                text_color=color,
                anchor="w"
            )
            value_label.pack(
                fill="x",
                padx=18,
                pady=(0, 14)
            )

            return value_label

        total_value = create_audit_card(
            0,
            "TOTAL RECORDS",
            "#93C5FD"
        )

        page_value = create_audit_card(
            1,
            "CURRENT PAGE",
            "#F5F8FF"
        )

        showing_value = create_audit_card(
            2,
            "SHOWING",
            "#4ADE80"
        )

        # ====================================================
        # FILTER PANEL
        # ====================================================

        filters = ctk.CTkFrame(
            page,
            fg_color="#17263F",
            corner_radius=14,
            border_width=1,
            border_color="#2B4161"
        )
        filters.pack(
            fill="x",
            padx=20,
            pady=(0, 12)
        )

        ctk.CTkLabel(
            filters,
            text="Filter Audit Records",
            font=("Arial", 17, "bold"),
            text_color=WHITE,
            anchor="w"
        ).grid(
            row=0,
            column=0,
            columnspan=4,
            sticky="ew",
            padx=18,
            pady=(18, 10)
        )

        for column in range(4):
            filters.grid_columnconfigure(
                column,
                weight=1,
                uniform="audit_filters"
            )

        def make_label(title, row, column):
            ctk.CTkLabel(
                filters,
                text=title,
                font=("Arial", 12, "bold"),
                text_color=WHITE,
                anchor="w"
            ).grid(
                row=row,
                column=column,
                sticky="ew",
                padx=10,
                pady=(8, 5)
            )

        def make_combo(values, row, column):
            combo = ctk.CTkComboBox(
                filters,
                values=values,
                state="readonly",
                height=40,
                corner_radius=9,
                font=("Arial", 12)
            )
            combo.grid(
                row=row,
                column=column,
                sticky="ew",
                padx=10,
                pady=(0, 10)
            )
            combo.set(values[0])
            return combo

        make_label("Category", 1, 0)
        make_label("Action Type", 1, 1)
        make_label("Date Range", 1, 2)
        make_label("Sort Order", 1, 3)

        category_combo = make_combo(
            [
                "All Categories",
                "Transactions",
                "Accounts",
                "Credit Cards",
                "Security",
                "Customers",
                "Authentication"
            ],
            2,
            0
        )

        actions = [
            "All Actions"
        ] + self.db.audit_log_actions()

        action_combo = make_combo(
            actions,
            2,
            1
        )

        date_combo = make_combo(
            [
                "All Time",
                "Today",
                "Last 7 Days",
                "Last 30 Days"
            ],
            2,
            2
        )

        sort_combo = make_combo(
            [
                "Newest First",
                "Oldest First"
            ],
            2,
            3
        )

        make_label("User ID", 3, 0)
        make_label("Keyword Search", 3, 1)
        make_label("Page Size", 3, 2)

        user_entry = ctk.CTkEntry(
            filters,
            placeholder_text="e.g. 12",
            height=40,
            corner_radius=9,
            font=("Arial", 12)
        )
        user_entry.grid(
            row=4,
            column=0,
            sticky="ew",
            padx=10,
            pady=(0, 18)
        )

        keyword_entry = ctk.CTkEntry(
            filters,
            placeholder_text="Action, entity, description...",
            height=40,
            corner_radius=9,
            font=("Arial", 12)
        )
        keyword_entry.grid(
            row=4,
            column=1,
            sticky="ew",
            padx=10,
            pady=(0, 18)
        )

        page_size_combo = make_combo(
            ["25", "50", "100"],
            4,
            2
        )

        # ====================================================
        # RESULTS HEADER
        # ====================================================

        results_header = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )
        results_header.pack(
            fill="x",
            padx=24,
            pady=(4, 2)
        )

        ctk.CTkLabel(
            results_header,
            text="Activity Records",
            font=("Arial", 18, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(side="left")

        summary = ctk.CTkLabel(
            results_header,
            text="Loading audit records...",
            font=("Arial", 12),
            text_color=MUTED
        )
        summary.pack(side="right")

        # ====================================================
        # AUDIT LOGS - DARK TABLE STYLE
        # ====================================================

        audit_style = ttk.Style()
        previous_audit_theme = audit_style.theme_use()

        if previous_audit_theme != "clam":
            audit_style.theme_use("clam")

        audit_style.configure(
            "AuditLogs.Treeview",
            background="#17263F",
            fieldbackground="#17263F",
            foreground="#F5F8FF",
            rowheight=35,
            font=("Arial", 11),
            borderwidth=0,
            relief="flat"
        )

        audit_style.configure(
            "AuditLogs.Treeview.Heading",
            background="#243A59",
            foreground="#FFFFFF",
            font=("Arial", 11, "bold"),
            padding=(10, 10),
            borderwidth=0,
            relief="flat"
        )

        audit_style.map(
            "AuditLogs.Treeview",
            background=[
                ("selected", "#3478F6")
            ],
            foreground=[
                ("selected", "#FFFFFF")
            ]
        )

        audit_style.map(
            "AuditLogs.Treeview.Heading",
            background=[
                ("active", "#304B70")
            ],
            foreground=[
                ("active", "#FFFFFF")
            ]
        )

        # Dark scrollbars
        for orientation in ("Vertical", "Horizontal"):
            scrollbar_style = (
                f"AuditLogs.{orientation}.TScrollbar"
            )

            audit_style.configure(
                scrollbar_style,
                background="#304B70",
                troughcolor="#111F35",
                arrowcolor="#FFFFFF",
                bordercolor="#17263F",
                lightcolor="#304B70",
                darkcolor="#304B70",
                borderwidth=0,
                relief="flat",
                width=13
            )

            audit_style.map(
                scrollbar_style,
                background=[
                    ("active", "#456B9B"),
                    ("pressed", "#3478F6")
                ]
            )

        # ====================================================
        # AUDIT LOG TABLE
        # ====================================================

        tree = self.table(
            page,
            (
                "id",
                "action",
                "entity",
                "entity_id",
                "description",
                "created"
            ),
            (
                "ID",
                "Action",
                "Entity",
                "Entity ID",
                "Description",
                "Created"
            )
        )


        # ====================================================
        # AUDIT LOGS - TABLE HEIGHT FIX
        # Keep action buttons visible below the table.
        # ====================================================

        audit_table_holder = tree.master.master

        audit_table_holder.pack_configure(
            fill="both",
            expand=False,
            padx=20,
            pady=(8, 8)
        )

        audit_table_holder.configure(
            height=255
        )

        audit_table_holder.pack_propagate(False)



        # Apply the dark style only to Audit Logs.
        tree.configure(
            style="AuditLogs.Treeview"
        )

        # Apply dark scrollbar styles to this table.
        for widget in tree.master.winfo_children():
            if isinstance(widget, ttk.Scrollbar):
                orientation = str(widget.cget("orient"))

                widget.configure(
                    style=(
                        "AuditLogs.Vertical.TScrollbar"
                        if orientation == "vertical"
                        else "AuditLogs.Horizontal.TScrollbar"
                    )
                )

        # Alternating row backgrounds.
        tree.tag_configure(
            "audit_even",
            background="#17263F",
            foreground="#F5F8FF"
        )

        tree.tag_configure(
            "audit_odd",
            background="#1C2D48",
            foreground="#F5F8FF"
        )

        # Restore the previous theme when this table is destroyed.
        def restore_audit_theme(event):
            if event.widget is tree:
                current_style = ttk.Style()

                if current_style.theme_use() != previous_audit_theme:
                    current_style.theme_use(previous_audit_theme)

        tree.bind(
            "<Destroy>",
            restore_audit_theme,
            add="+"
        )


        tree.column(
            "id",
            width=75,
            minwidth=60
        )
        tree.column(
            "action",
            width=170,
            minwidth=110
        )
        tree.column(
            "entity",
            width=130,
            minwidth=100
        )
        tree.column(
            "entity_id",
            width=100,
            minwidth=80
        )
        tree.column(
            "description",
            width=340,
            minwidth=180,
            anchor="w"
        )
        tree.column(
            "created",
            width=165,
            minwidth=130
        )

        # ====================================================
        # FILTER VALUES
        # ====================================================

        def get_filters():
            return {
                "category": category_combo.get(),
                "action": action_combo.get(),
                "date_range": date_combo.get(),
                "user_id": user_entry.get().strip(),
                "keyword": keyword_entry.get().strip(),
                "sort": sort_combo.get(),
                "page_size": int(page_size_combo.get())
            }

        # ====================================================
        # LOAD RECORDS
        # ====================================================

        def load_records():
            result = self.db.logs(
                **get_filters(),
                page=current_page[0]
            )

            current_result[0] = result

            for item in tree.get_children():
                tree.delete(item)


            for index, row in enumerate(result["rows"]):
                row_tag = (
                    "audit_even"
                    if index % 2 == 0
                    else "audit_odd"
                )

                tree.insert(
                    "",
                    "end",
                    values=(
                        row[0],
                        row[1],
                        row[2],
                        row[3],
                        str(row[4] or ""),
                        str(row[5])[:19]
                    ),
                    tags=(row_tag,)
                )


            summary.configure(
                text=(
                    f"Total Records: {result['total']}   |   "
                    f"Page: {result['page']} / "
                    f"{result['total_pages']}   |   "
                    f"Showing: {len(result['rows'])}"
                )
            )

            total_value.configure(text=str(result["total"]))
            page_value.configure(
                text=f"{result['page']} / {result['total_pages']}"
            )
            showing_value.configure(text=str(len(result["rows"])))

            previous_button.configure(
                state=(
                    "normal"
                    if current_page[0] > 1
                    else "disabled"
                )
            )

            next_button.configure(
                state=(
                    "normal"
                    if current_page[0] < result["total_pages"]
                    else "disabled"
                )
            )

        def apply_filters():
            current_page[0] = 1
            self.run(load_records)

        def reset_filters():
            category_combo.set("All Categories")
            action_combo.set("All Actions")
            date_combo.set("All Time")
            sort_combo.set("Newest First")
            page_size_combo.set("25")

            user_entry.delete(0, "end")
            keyword_entry.delete(0, "end")

            current_page[0] = 1
            self.run(load_records)

        # ====================================================
        # PAGINATION
        # ====================================================

        def previous_page():
            if current_page[0] > 1:
                current_page[0] -= 1
                self.run(load_records)

        def next_page():
            result = current_result[0]

            if (
                result is not None
                and current_page[0] < result["total_pages"]
            ):
                current_page[0] += 1
                self.run(load_records)

        # ====================================================
        # CSV EXPORT
        # ====================================================

        def export_csv():
            def action():
                selected_filters = get_filters()

                filename = filedialog.asksaveasfilename(
                    title="Export Audit Logs",
                    defaultextension=".csv",
                    filetypes=[
                        ("CSV Files", "*.csv")
                    ],
                    initialfile="audit_logs.csv"
                )

                if not filename:
                    return

                first = self.db.logs(
                    **selected_filters,
                    page=1
                )

                total_pages = first["total_pages"]

                with open(
                    filename,
                    "w",
                    newline="",
                    encoding="utf-8-sig"
                ) as file:
                    writer = csv.writer(file)

                    writer.writerow(
                        [
                            "Audit ID",
                            "Action",
                            "Entity",
                            "Entity ID",
                            "Description",
                            "Created At"
                        ]
                    )

                    def write_rows(rows):
                        for row in rows:
                            writer.writerow(
                                [
                                    row[0],
                                    row[1],
                                    row[2],
                                    row[3],
                                    row[4],
                                    row[5]
                                ]
                            )

                    write_rows(first["rows"])

                    for page_number in range(
                        2,
                        total_pages + 1
                    ):
                        result = self.db.logs(
                            **selected_filters,
                            page=page_number
                        )
                        write_rows(result["rows"])

                self.show_ok(
                    "Export Complete",
                    (
                        "Filtered audit logs exported "
                        "successfully."
                    )
                )

            self.run(action)

        # ====================================================
        # FILTER ACTION BUTTONS
        # ====================================================

        filter_buttons = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )
        filter_buttons.pack(
            fill="x",
            padx=22,
            pady=(8, 8)
        )

        self.button(
            filter_buttons,
            "Apply Filters",
            apply_filters,
            width=150
        ).pack(
            side="left",
            padx=(0, 8)
        )

        self.button(
            filter_buttons,
            "Reset Filters",
            reset_filters,
            width=150
        ).pack(
            side="left",
            padx=8
        )

        self.button(
            filter_buttons,
            "Refresh",
            lambda: self.run(load_records),
            width=120
        ).pack(
            side="left",
            padx=8
        )

        self.button(
            filter_buttons,
            "Export CSV",
            export_csv,
            width=130
        ).pack(
            side="right"
        )

        # ====================================================
        # PAGE NAVIGATION
        # ====================================================

        navigation = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )
        navigation.pack(
            fill="x",
            padx=22,
            pady=(4, 16)
        )

        previous_button = self.button(
            navigation,
            "Previous",
            previous_page,
            width=130
        )
        previous_button.pack(
            side="left",
            padx=(0, 8)
        )

        next_button = self.button(
            navigation,
            "Next",
            next_page,
            width=130
        )
        next_button.pack(
            side="left",
            padx=8
        )

        previous_button.configure(state="disabled")
        next_button.configure(state="disabled")

        # ====================================================
        # INITIAL LOAD
        # ====================================================

        self.run(load_records)

    # ============================================================
    # CUSTOMER NOTIFICATIONS
    # ============================================================


    def show_notifications(self):
        session = self.db.require_login()

        if session["role"] != "Customer":
            raise PermissionError(
                "Only customers can view notifications."
            )

        page = self.page("My Notifications")

        rows = self.db.notifications()
        unread_count = self.db.unread_notification_count()

        # ====================================================
        # NOTIFICATION SUMMARY CARD
        # ====================================================

        summary = ctk.CTkFrame(
            page,
            fg_color="#142641",
            corner_radius=14,
            border_width=1,
            border_color="#294568",
            height=102
        )
        summary.pack(
            fill="x",
            padx=20,
            pady=(5, 10)
        )
        summary.pack_propagate(False)

        summary_left = ctk.CTkFrame(
            summary,
            fg_color="transparent"
        )
        summary_left.pack(
            side="left",
            fill="y",
            padx=(18, 12),
            pady=15
        )

        icon_box = ctk.CTkFrame(
            summary_left,
            width=64,
            height=64,
            corner_radius=12,
            fg_color="#23466F"
        )
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)

        ctk.CTkLabel(
            icon_box,
            text="●",
            font=("Arial", 30, "bold"),
            text_color="#3B82F6"
        ).place(relx=0.5, rely=0.5, anchor="center")

        count_frame = ctk.CTkFrame(
            summary_left,
            fg_color="transparent"
        )
        count_frame.pack(
            side="left",
            padx=(18, 25)
        )

        ctk.CTkLabel(
            count_frame,
            text="Unread Notifications",
            font=("Arial", 15, "bold"),
            text_color="#FFFFFF",
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            count_frame,
            text=str(unread_count),
            font=("Arial", 30, "bold"),
            text_color="#93C5FD",
            anchor="w"
        ).pack(anchor="w", pady=(2, 0))

        separator = ctk.CTkFrame(
            summary,
            width=1,
            fg_color="#345477"
        )
        separator.pack(
            side="left",
            fill="y",
            pady=20
        )

        ctk.CTkLabel(
            summary,
            text=(
                "Stay informed about your account, "
                "credit cards and important updates."
            ),
            font=("Arial", 13),
            text_color="#A9C1E3",
            anchor="w",
            justify="left",
            wraplength=520
        ).pack(
            side="left",
            fill="both",
            expand=True,
            padx=28
        )

        # ====================================================
        # NOTIFICATIONS TABLE - DARK NAVY
        # ====================================================

        notification_style = ttk.Style()
        previous_theme = notification_style.theme_use()

        # Windows native themes may ignore Treeview colors.
        if previous_theme != "clam":
            notification_style.theme_use("clam")

        notification_style.configure(
            "Notifications.Treeview",
            background="#10213B",
            fieldbackground="#10213B",
            foreground="#F4F8FF",
            rowheight=39,
            font=("Arial", 11),
            borderwidth=0,
            relief="flat"
        )

        notification_style.configure(
            "Notifications.Treeview.Heading",
            background="#234266",
            foreground="#FFFFFF",
            font=("Arial", 11, "bold"),
            padding=(12, 11),
            borderwidth=0,
            relief="flat"
        )

        notification_style.map(
            "Notifications.Treeview",
            background=[
                ("selected", "#2563EB")
            ],
            foreground=[
                ("selected", "#FFFFFF")
            ]
        )

        notification_style.map(
            "Notifications.Treeview.Heading",
            background=[
                ("active", "#30577F")
            ],
            foreground=[
                ("active", "#FFFFFF")
            ]
        )

        for orientation in ("Vertical", "Horizontal"):
            scrollbar_style = (
                f"Notifications.{orientation}.TScrollbar"
            )

            notification_style.configure(
                scrollbar_style,
                background="#29496D",
                troughcolor="#10213B",
                arrowcolor="#DCEAFF",
                bordercolor="#10213B",
                lightcolor="#29496D",
                darkcolor="#29496D",
                borderwidth=0,
                relief="flat",
                width=12
            )

            notification_style.map(
                scrollbar_style,
                background=[
                    ("active", "#3A6594"),
                    ("pressed", "#2563EB")
                ]
            )

        tree = self.table(
            page,
            (
                "id",
                "title",
                "message",
                "type",
                "status",
                "created"
            ),
            (
                "ID",
                "Title",
                "Message",
                "Type",
                "Status",
                "Created At"
            )
        )

        tree.configure(
            style="Notifications.Treeview",
            selectmode="browse"
        )

        # ====================================================
        # TABLE COLUMNS
        # ====================================================

        tree.column(
            "id",
            width=75,
            minwidth=65,
            anchor="center",
            stretch=False
        )

        tree.column(
            "title",
            width=245,
            minwidth=170,
            anchor="w"
        )

        tree.column(
            "message",
            width=430,
            minwidth=250,
            anchor="w"
        )

        tree.column(
            "type",
            width=150,
            minwidth=120,
            anchor="center"
        )

        tree.column(
            "status",
            width=115,
            minwidth=90,
            anchor="center",
            stretch=False
        )

        tree.column(
            "created",
            width=180,
            minwidth=155,
            anchor="center",
            stretch=False
        )

        # ====================================================
        # DARK SCROLLBARS - THIS TABLE ONLY
        # ====================================================

        table_frame = tree.master

        for widget in table_frame.winfo_children():
            if isinstance(widget, ttk.Scrollbar):
                orientation = str(widget.cget("orient"))

                widget.configure(
                    style=(
                        "Notifications.Vertical.TScrollbar"
                        if orientation == "vertical"
                        else "Notifications.Horizontal.TScrollbar"
                    )
                )

        # Restore the previous theme when leaving this page.
        def restore_notification_theme(event):
            if event.widget is tree:
                current_style = ttk.Style()

                if current_style.theme_use() != previous_theme:
                    current_style.theme_use(previous_theme)

        tree.bind(
            "<Destroy>",
            restore_notification_theme,
            add="+"
        )

        # ====================================================
        # NOTIFICATION ROWS
        # ====================================================

        tree.tag_configure(
            "even_row",
            background="#10213B",
            foreground="#F4F8FF"
        )

        tree.tag_configure(
            "odd_row",
            background="#1A304E",
            foreground="#F4F8FF"
        )

        for index, row in enumerate(rows):
            row_tag = (
                "even_row"
                if index % 2 == 0
                else "odd_row"
            )

            tree.insert(
                "",
                "end",
                values=(
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    "Read" if bool(row[4]) else "Unread",
                    str(row[5])[:19]
                ),
                tags=(row_tag,)
            )

        # ====================================================
        # ACTION BUTTONS
        # ====================================================

        actions = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )
        actions.pack(
            fill="x",
            padx=20,
            pady=(8, 18)
        )

        button_group = ctk.CTkFrame(
            actions,
            fg_color="transparent"
        )
        button_group.pack(anchor="center")

        # ====================================================
        # ORIGINAL MARK SELECTED FUNCTION
        # ====================================================

        def mark_selected():
            def action():
                selected = tree.selection()

                if not selected:
                    self.show_ok(
                        "Select Notification",
                        "Please select a notification."
                    )
                    return

                values = tree.item(
                    selected[0],
                    "values"
                )

                notification_id = int(values[0])

                self.db.mark_notification_read(
                    notification_id
                )

                self.show_notifications()

            self.run(action)

        # ====================================================
        # ORIGINAL MARK ALL FUNCTION
        # ====================================================

        def mark_all():
            def action():
                self.db.mark_all_notifications_read()
                self.show_notifications()

            self.run(action)

        # ====================================================
        # BUTTON DESIGN
        # ====================================================

        ctk.CTkButton(
            button_group,
            text="✓  Mark Selected as Read",
            command=mark_selected,
            width=245,
            height=46,
            corner_radius=10,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            text_color="#FFFFFF",
            font=("Arial", 12, "bold")
        ).pack(
            side="left",
            padx=8
        )

        ctk.CTkButton(
            button_group,
            text="✓  Mark All as Read",
            command=mark_all,
            width=220,
            height=46,
            corner_radius=10,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            text_color="#FFFFFF",
            font=("Arial", 12, "bold")
        ).pack(
            side="left",
            padx=8
        )

    # ============================================================
    # ADMIN SEND ANNOUNCEMENT
    # ============================================================


    def show_announcement(self):
        import customtkinter as ctk
        from tkinter import messagebox

        self.db.require_admin()
        page = self.page("Send Announcement")

        selected_customer = {"id": None, "phone": None}
        pagination = {"page": 1, "total_pages": 1}
        search_job = {"id": None}

        # ====================================================
        # SCROLLABLE CONTENT
        # ====================================================

        content = ctk.CTkScrollableFrame(
            page,
            fg_color="transparent",
            corner_radius=0
        )
        content.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 15)
        )

        # ====================================================
        # PAGE INTRODUCTION
        # ====================================================

        intro = ctk.CTkFrame(
            content,
            fg_color=CARD,
            corner_radius=14
        )
        intro.pack(fill="x", pady=(8, 14))

        ctk.CTkLabel(
            intro,
            text="Customer Announcements",
            font=("Arial", 19, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(
            fill="x",
            padx=22,
            pady=(20, 6)
        )

        ctk.CTkLabel(
            intro,
            text=(
                "Search for a specific customer or send "
                "an announcement to all active customers."
            ),
            font=("Arial", 12),
            text_color=MUTED,
            anchor="w",
            wraplength=800
        ).pack(
            fill="x",
            padx=22,
            pady=(0, 20)
        )

        # ====================================================
        # RECIPIENT SELECTION
        # ====================================================

        mode_frame = ctk.CTkFrame(
            content,
            fg_color=CARD,
            corner_radius=14
        )
        mode_frame.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            mode_frame,
            text="Recipients",
            font=("Arial", 17, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(18, 12)
        )

        recipient_mode = ctk.StringVar(
            value="Specific Customer"
        )

        mode_buttons = ctk.CTkSegmentedButton(
            mode_frame,
            values=[
                "Specific Customer",
                "All Customers"
            ],
            variable=recipient_mode
        )
        mode_buttons.pack(
            fill="x",
            padx=20,
            pady=(0, 20)
        )

        # ====================================================
        # CUSTOMER SEARCH
        # ====================================================

        search_frame = ctk.CTkFrame(
            content,
            fg_color=CARD,
            corner_radius=14
        )
        search_frame.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            search_frame,
            text="Find Customer",
            font=("Arial", 17, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(18, 5)
        )

        ctk.CTkLabel(
            search_frame,
            text="Search by phone number",
            font=("Arial", 12),
            text_color=MUTED,
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(0, 12)
        )

        search_row = ctk.CTkFrame(
            search_frame,
            fg_color="transparent"
        )
        search_row.pack(
            fill="x",
            padx=20,
            pady=(0, 14)
        )

        phone_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Enter phone number...",
            height=42,
            corner_radius=10,
            font=("Arial", 12)
        )
        phone_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10)
        )

        ctk.CTkLabel(
            search_frame,
            text="Search Results",
            font=("Arial", 14, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(0, 8)
        )

        table_frame = ctk.CTkScrollableFrame(
            search_frame,
            height=180,
            fg_color="transparent",
            corner_radius=10
        )
        table_frame.pack(
            fill="x",
            padx=20,
            pady=(0, 12)
        )

        # ====================================================
        # PAGINATION
        # ====================================================

        pagination_frame = ctk.CTkFrame(
            search_frame,
            fg_color="transparent"
        )
        pagination_frame.pack(
            fill="x",
            padx=20,
            pady=(0, 18)
        )

        page_label = ctk.CTkLabel(
            pagination_frame,
            text="Page 1",
            font=("Arial", 12),
            text_color=MUTED
        )
        page_label.pack(side="left", padx=(0, 10))

        # ====================================================
        # SELECTED RECIPIENT
        # ====================================================

        selected_label = ctk.CTkLabel(
            content,
            text="Selected Customer: None",
            font=("Arial", 13, "bold"),
            text_color=WHITE,
            anchor="w"
        )
        selected_label.pack(
            fill="x",
            padx=5,
            pady=(0, 12)
        )

        all_customers_label = ctk.CTkLabel(
            content,
            text="",
            font=("Arial", 13, "bold"),
            text_color="#F59E0B",
            anchor="w"
        )
        all_customers_label.pack(
            fill="x",
            padx=5,
            pady=(0, 12)
        )

        # ====================================================
        # CUSTOMER SEARCH FUNCTIONS
        # ====================================================

        def select_customer(customer_id, phone):
            selected_customer["id"] = customer_id
            selected_customer["phone"] = phone

            selected_label.configure(
                text=f"Selected Customer: {phone}"
            )

        def load_customers():
            if recipient_mode.get() == "All Customers":
                return

            try:
                result = self.db.search_announcement_customers(
                    phone=phone_entry.get().strip(),
                    page=pagination["page"],
                    page_size=25
                )

                pagination["total_pages"] = result[
                    "total_pages"
                ]

                for widget in table_frame.winfo_children():
                    widget.destroy()

                rows = result["rows"]

                if not rows:
                    ctk.CTkLabel(
                        table_frame,
                        text="No customers found.",
                        text_color=MUTED
                    ).pack(pady=15)

                for row in rows:
                    customer_id = int(row[0])
                    first_name = str(row[1] or "")
                    last_name = str(row[2] or "")
                    phone = str(row[3] or "")

                    customer_row = ctk.CTkFrame(
                        table_frame,
                        fg_color=SIDEBAR,
                        corner_radius=9
                    )
                    customer_row.pack(
                        fill="x",
                        pady=4
                    )

                    ctk.CTkLabel(
                        customer_row,
                        text=phone,
                        width=150,
                        font=("Arial", 12),
                        text_color=WHITE,
                        anchor="w"
                    ).pack(
                        side="left",
                        padx=12,
                        pady=10
                    )

                    ctk.CTkLabel(
                        customer_row,
                        text=f"{first_name} {last_name}",
                        font=("Arial", 12),
                        text_color=WHITE,
                        anchor="w"
                    ).pack(
                        side="left",
                        fill="x",
                        expand=True,
                        padx=10
                    )

                    ctk.CTkButton(
                        customer_row,
                        text="Select",
                        width=85,
                        height=34,
                        corner_radius=8,
                        fg_color=BLUE,
                        hover_color=BLUE_HOVER,
                        command=lambda cid=customer_id, p=phone:
                            select_customer(cid, p)
                    ).pack(
                        side="right",
                        padx=10,
                        pady=7
                    )

                page_label.configure(
                    text=(
                        f"Page {pagination['page']} "
                        f"of {pagination['total_pages']} "
                        f"• {result['total']} customers"
                    )
                )

            except Exception as exc:
                self.show_ok(
                    "Customer Search Error",
                    str(exc)
                )

        def change_page(direction):
            new_page = pagination["page"] + direction

            if 1 <= new_page <= pagination["total_pages"]:
                pagination["page"] = new_page
                load_customers()

        def schedule_search(*args):
            if search_job["id"] is not None:
                self.after_cancel(search_job["id"])

            def run_search():
                search_job["id"] = None
                pagination["page"] = 1

                selected_customer["id"] = None
                selected_customer["phone"] = None

                selected_label.configure(
                    text="Selected Customer: None"
                )

                load_customers()

            search_job["id"] = self.after(
                350,
                run_search
            )

        phone_entry.bind(
            "<KeyRelease>",
            schedule_search
        )

        self.button(
            search_row,
            "Search",
            schedule_search,
            width=110
        ).pack(side="right")

        self.button(
            pagination_frame,
            "Next",
            lambda: change_page(1),
            width=95
        ).pack(
            side="right",
            padx=(5, 0)
        )

        self.button(
            pagination_frame,
            "Previous",
            lambda: change_page(-1),
            width=95
        ).pack(
            side="right",
            padx=5
        )

        # ====================================================
        # RECIPIENT MODE
        # ====================================================

        def update_recipient_mode(value=None):
            if recipient_mode.get() == "All Customers":
                search_frame.pack_forget()
                selected_label.pack_forget()

                try:
                    count = (
                        self.db.announcement_customer_count()
                    )

                    all_customers_label.configure(
                        text=(
                            f"All Customers selected: "
                            f"{count} active customers."
                        )
                    )

                except Exception as exc:
                    all_customers_label.configure(
                        text=f"Unable to load count: {exc}"
                    )

            else:
                all_customers_label.configure(text="")

                search_frame.pack(
                    fill="x",
                    pady=(0, 12),
                    before=all_customers_label
                )

                selected_label.pack(
                    fill="x",
                    padx=5,
                    pady=(0, 12),
                    before=all_customers_label
                )

                load_customers()

        mode_buttons.configure(
            command=update_recipient_mode
        )

        # ====================================================
        # ANNOUNCEMENT FORM
        # ====================================================

        form_frame = ctk.CTkFrame(
            content,
            fg_color=CARD,
            corner_radius=14
        )
        form_frame.pack(
            fill="x",
            pady=(0, 15)
        )

        ctk.CTkLabel(
            form_frame,
            text="Announcement Details",
            font=("Arial", 18, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(
            fill="x",
            padx=22,
            pady=(20, 5)
        )

        ctk.CTkLabel(
            form_frame,
            text="Write the title and message for your recipients.",
            font=("Arial", 12),
            text_color=MUTED,
            anchor="w"
        ).pack(
            fill="x",
            padx=22,
            pady=(0, 18)
        )

        ctk.CTkLabel(
            form_frame,
            text="Announcement Title",
            font=("Arial", 13, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(
            fill="x",
            padx=22,
            pady=(0, 7)
        )

        title_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter announcement title...",
            height=42,
            corner_radius=10,
            font=("Arial", 12)
        )
        title_entry.pack(
            fill="x",
            padx=22,
            pady=(0, 17)
        )

        ctk.CTkLabel(
            form_frame,
            text="Message",
            font=("Arial", 13, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(
            fill="x",
            padx=22,
            pady=(0, 7)
        )

        message_text = ctk.CTkTextbox(
            form_frame,
            height=135,
            corner_radius=10,
            font=("Arial", 12)
        )
        message_text.pack(
            fill="x",
            padx=22,
            pady=(0, 20)
        )

        # ====================================================
        # SEND ANNOUNCEMENT
        # ====================================================

        def send_announcement():
            title = title_entry.get().strip()

            message = message_text.get(
                "1.0",
                "end"
            ).strip()

            if not title or not message:
                self.show_ok(
                    "Missing Information",
                    "Please enter a title and message."
                )
                return

            if len(title) > 150:
                self.show_ok(
                    "Invalid Title",
                    "Title cannot exceed 150 characters."
                )
                return

            if len(message) > 1000:
                self.show_ok(
                    "Invalid Message",
                    "Message cannot exceed 1000 characters."
                )
                return

            if recipient_mode.get() == "All Customers":
                customer_id = None
                recipient_text = "ALL ACTIVE CUSTOMERS"

            else:
                customer_id = selected_customer["id"]

                if customer_id is None:
                    self.show_ok(
                        "Select Customer",
                        "Please select a customer from search results."
                    )
                    return

                recipient_text = (
                    selected_customer["phone"]
                )

            confirmed = self.ask_yes_no(
                "Confirm Announcement",
                (
                    f"Recipient: {recipient_text}\n\n"
                    f"Title: {title}\n\n"
                    "Do you want to send this announcement?"
                )
            )

            if not confirmed:
                return

            try:
                count = self.db.send_announcement(
                    title=title,
                    message=message,
                    customer_id=customer_id
                )

                self.show_ok(
                    "Announcement Sent",
                    (
                        "Announcement sent successfully.\n"
                        f"Recipients: {count}"
                    )
                )

                title_entry.delete(0, "end")
                message_text.delete("1.0", "end")

            except Exception as exc:
                self.show_ok(
                    "Announcement Error",
                    str(exc)
                )

        self.button(
            form_frame,
            "Send Announcement",
            send_announcement
        ).pack(
            fill="x",
            padx=22,
            pady=(0, 22)
        )

        # Initial search
        load_customers()

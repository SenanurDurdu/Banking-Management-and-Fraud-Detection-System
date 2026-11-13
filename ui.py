
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

        self.title("Banking Management & Fraud Detection System")
        self.geometry("1350x850")
        self.minsize(1050, 700)
        self.configure(fg_color=BG)

        self.show_login()

    # ============================================================
    # GENERAL UI HELPERS
    # ============================================================

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def run(self, fn):
        try:
            return fn()
        except Exception as error:
            messagebox.showerror("Error", str(error))
            return None

    def button(self, parent, title, command, width=200):
        return ctk.CTkButton(
            parent,
            text=title,
            command=command,
            width=width,
            height=40,
            fg_color=BLUE,
            hover_color=BLUE_HOVER
        )

    def entry(self, parent, placeholder, secret=False):
        widget = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            width=330,
            height=42,
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
            corner_radius=18
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
            font=("Arial", 17, "bold"),
            text_color="#60A5FA"
        ).pack(pady=(16, 6))

        ctk.CTkLabel(
            card,
            text=title,
            font=("Arial", 28, "bold"),
            text_color=WHITE
        ).pack(pady=4)

        ctk.CTkLabel(
            card,
            text=subtitle,
            text_color=MUTED
        ).pack(pady=(0, 8))

        return card

    def table(self, parent, columns, headings):
        holder = ctk.CTkFrame(
            parent,
            fg_color=CARD
        )

        holder.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=12
        )

        tree = ttk.Treeview(
            holder,
            columns=columns,
            show="headings"
        )

        for col, heading in zip(columns, headings):
            tree.heading(col, text=heading)
            tree.column(
                col,
                width=155,
                minwidth=95,
                anchor="center"
            )

        yscroll = ttk.Scrollbar(
            holder,
            orient="vertical",
            command=tree.yview
        )

        xscroll = ttk.Scrollbar(
            holder,
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
        card = self.auth_card(
            "Welcome Back",
            "Sign in to your account",
            400
        )

        email = self.entry(
            card,
            "Gmail address"
        )

        password = self.entry(
            card,
            "Password",
            secret=True
        )

        def submit():
            def action():
                self.db.login(
                    email.get(),
                    password.get()
                )

                self.show_panel()

            self.run(action)

        self.button(
            card,
            "Sign In",
            submit,
            330
        ).pack(pady=(16, 8))

        ctk.CTkButton(
            card,
            text="Create a new account",
            command=self.show_register,
            fg_color="transparent",
            text_color="#93C5FD"
        ).pack(pady=6)

    # ============================================================
    # REGISTRATION SCREEN
    # ============================================================

    def show_register(self):
        card = self.auth_card(
            "Create Account",
            "All fields are required",
            750
        )

        first = self.entry(
            card,
            "First name"
        )

        last = self.entry(
            card,
            "Last name"
        )

        national_id = self.entry(
            card,
            "11-digit National ID"
        )

        phone = self.entry(
            card,
            "Phone number (11 digits)"
        )

        email = self.entry(
            card,
            "Gmail address (@gmail.com)"
        )

        address = self.entry(
            card,
            "Address"
        )

        password = self.entry(
            card,
            "Password (minimum 4 characters)",
            secret=True
        )

        confirm = self.entry(
            card,
            "Confirm password",
            secret=True
        )

        def submit():
            def action():
                if password.get() != confirm.get():
                    raise ValueError(
                        "Passwords do not match."
                    )

                cid = self.db.register(
                    first.get(),
                    last.get(),
                    national_id.get(),
                    phone.get(),
                    email.get(),
                    address.get(),
                    password.get()
                )

                messagebox.showinfo(
                    "Registration Successful",
                    f"Customer ID: {cid}"
                )

                self.show_login()

            self.run(action)

        self.button(
            card,
            "Register",
            submit,
            330
        ).pack(pady=(8, 4))

        ctk.CTkButton(
            card,
            text="Back to Login",
            command=self.show_login,
            fg_color="transparent",
            text_color="#93C5FD"
        ).pack(pady=3)

    # ============================================================
    # MAIN PANEL AND SIDEBAR
    # ============================================================

    def show_panel(self):
        session = self.db.session

        if session is None:
            self.show_login()
            return

        self.clear()

        self.sidebar = ctk.CTkFrame(
            self,
            width=240,
            fg_color=SIDEBAR,
            corner_radius=0
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        self.sidebar.pack_propagate(False)

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

        ctk.CTkLabel(
            self.sidebar,
            text="BANKING",
            font=("Arial", 26, "bold"),
            text_color=WHITE
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            self.sidebar,
            text=session["role"].upper(),
            text_color="#60A5FA"
        ).pack(pady=5)

        ctk.CTkLabel(
            self.sidebar,
            text=session["email"],
            text_color=MUTED
        ).pack(pady=(5, 25))

        if session["role"] == "Admin":
            navigation = [
                ("Dashboard", self.show_dashboard),
                ("Customers", self.show_customers),
                ("Accounts", self.show_accounts),
                ("Transactions", self.show_transactions),
                ("Fraud Alerts", self.show_fraud),
                ("Fraud Rules", self.show_rules),
                ("Audit Logs", self.show_logs)
            ]
        else:
            navigation = [
                ("Dashboard", self.show_dashboard),
                ("My Accounts", self.show_accounts),
                ("My Transactions", self.show_transactions)
            ]

        for title, fn in navigation:
            self.button(
                self.sidebar,
                title,
                lambda f=fn: self.run(f),
                200
            ).pack(pady=6)

        ctk.CTkButton(
            self.sidebar,
            text="Logout",
            command=self.logout,
            fg_color="#991B1B",
            hover_color="#7F1D1D"
        ).pack(
            side="bottom",
            fill="x",
            padx=16,
            pady=25
        )

        self.run(self.show_dashboard)

    def logout(self):
        self.db.logout()
        self.show_login()

    def page(self, title):
        for widget in self.main.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.main,
            text=title,
            font=("Arial", 26, "bold"),
            text_color=WHITE
        ).pack(
            anchor="w",
            padx=22,
            pady=20
        )

        return self.main

    # ============================================================
    # DASHBOARD SCREEN
    # ============================================================

    def show_dashboard(self):
        data = self.db.dashboard()

        page = self.page(
            "Dashboard"
        )

        row = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        row.pack(
            fill="x",
            padx=15,
            pady=15
        )

        for title, value in data:
            card = ctk.CTkFrame(
                row,
                fg_color=CARD,
                corner_radius=14
            )

            card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=5
            )

            ctk.CTkLabel(
                card,
                text=title,
                text_color=MUTED,
                wraplength=145
            ).pack(pady=(20, 10))

            ctk.CTkLabel(
                card,
                text=str(value),
                font=("Arial", 18, "bold"),
                text_color=WHITE
            ).pack(pady=(0, 20))

        self.button(
            page,
            "Refresh Dashboard",
            lambda: self.run(self.show_dashboard)
        ).pack(pady=20)

    # ============================================================
    # CUSTOMERS SCREEN
    # ============================================================

    def show_customers(self):
        self.db.require_admin()

        page = self.page(
            "Customer Management"
        )

        ctk.CTkLabel(
            page,
            text="Registered Customers (View Only)",
            font=("Arial", 17, "bold"),
            text_color=WHITE
        ).pack(
            anchor="w",
            padx=20,
            pady=(5, 10)
        )

        tree = self.table(
            page,
            (
                "id",
                "first",
                "last",
                "nid",
                "phone",
                "email",
                "address",
                "active"
            ),
            (
                "ID",
                "First Name",
                "Last Name",
                "National ID",
                "Phone",
                "Email",
                "Address",
                "Active"
            )
        )

        self.refresh_table(
            tree,
            self.db.customers
        )

        self.button(
            page,
            "Refresh",
            lambda: self.refresh_table(
                tree,
                self.db.customers
            )
        ).pack(pady=8)

    # ============================================================
    # ACCOUNTS SCREEN
    # ============================================================

    def show_accounts(self):
        session = self.db.require_login()

        is_admin = session["role"] == "Admin"

        page = self.page(
            "Account Management"
            if is_admin
            else "My Accounts"
        )

        form = ctk.CTkFrame(
            page,
            fg_color=CARD
        )

        form.pack(
            fill="x",
            padx=18,
            pady=8
        )

        customer_map = {}
        customer_combo = None

        if is_admin:
            customers = self.db.customer_choices()

            customer_map = {
                f"{c.CustomerID} - {c.FirstName} {c.LastName}":
                    int(c.CustomerID)
                for c in customers
            }

            customer_combo = ctk.CTkComboBox(
                form,
                values=list(customer_map) or ["No customers"],
                width=270,
                state="readonly"
            )

            customer_combo.pack(
                side="left",
                padx=8,
                pady=14
            )

        account_type = ctk.CTkComboBox(
            form,
            values=[
                "Checking",
                "Savings"
            ],
            width=145,
            state="readonly"
        )

        account_type.pack(
            side="left",
            padx=8,
            pady=14
        )

        opening = None

        if is_admin:
            opening = ctk.CTkEntry(
                form,
                placeholder_text="Opening balance",
                width=155
            )

            opening.pack(
                side="left",
                padx=8
            )

        def create_account():
            def action():
                if is_admin:
                    selected = customer_combo.get()

                    if selected not in customer_map:
                        raise ValueError(
                            "Please select a customer."
                        )

                    customer_id = customer_map[selected]
                    balance = opening.get()

                else:
                    customer_id = session["customer_id"]
                    balance = "0"

                account_id = self.db.add_account(
                    customer_id,
                    account_type.get(),
                    balance
                )

                messagebox.showinfo(
                    "Created",
                    f"Account ID: {account_id}"
                )

                self.show_accounts()

            self.run(action)

        self.button(
            form,
            "Create Account",
            create_account,
            150
        ).pack(
            side="left",
            padx=8
        )

        if is_admin:
            cols = (
                "id",
                "number",
                "customer",
                "type",
                "balance",
                "currency",
                "active"
            )

            heads = (
                "ID",
                "Account Number",
                "Customer",
                "Type",
                "Balance",
                "Currency",
                "Active"
            )

        else:
            cols = (
                "id",
                "number",
                "type",
                "balance",
                "currency",
                "active"
            )

            heads = (
                "ID",
                "Account Number",
                "Type",
                "Balance",
                "Currency",
                "Active"
            )

        tree = self.table(
            page,
            cols,
            heads
        )

        self.refresh_table(
            tree,
            self.db.accounts
        )

        self.button(
            page,
            "Refresh",
            lambda: self.refresh_table(
                tree,
                self.db.accounts
            )
        ).pack(pady=8)

    # ============================================================
    # TRANSACTIONS SCREEN
    # ============================================================

    def show_transactions(self):
        session = self.db.require_login()

        is_admin = session["role"] == "Admin"

        page = self.page(
            "Transactions"
            if is_admin
            else "My Transactions"
        )

        form = ctk.CTkFrame(
            page,
            fg_color=CARD
        )

        form.pack(
            fill="x",
            padx=18,
            pady=8
        )

        kinds = (
            [
                "Deposit",
                "Withdrawal",
                "Transfer"
            ]
            if is_admin
            else [
                "Withdrawal",
                "Transfer"
            ]
        )

        kind = ctk.CTkComboBox(
            form,
            values=kinds,
            width=140,
            state="readonly"
        )

        kind.pack(
            side="left",
            padx=5,
            pady=14
        )

        source = ctk.CTkEntry(
            form,
            placeholder_text="Source Account ID",
            width=145
        )

        source.pack(
            side="left",
            padx=5
        )

        destination = ctk.CTkEntry(
            form,
            placeholder_text="Destination Account ID",
            width=175
        )

        destination.pack(
            side="left",
            padx=5
        )

        amount = ctk.CTkEntry(
            form,
            placeholder_text="Amount",
            width=115
        )

        amount.pack(
            side="left",
            padx=5
        )

        description = ctk.CTkEntry(
            form,
            placeholder_text="Description",
            width=145
        )

        description.pack(
            side="left",
            padx=5
        )

        def execute():
            def action():
                tx_id = self.db.transact(
                    kind.get(),
                    source.get(),
                    destination.get(),
                    amount.get(),
                    description.get()
                )

                messagebox.showinfo(
                    "Completed",
                    f"Transaction ID: {tx_id}"
                )

                self.show_transactions()

            self.run(action)

        self.button(
            page,
            "Execute Transaction",
            execute
        ).pack(pady=8)

        tree = self.table(
            page,
            (
                "id",
                "type",
                "from",
                "to",
                "amount",
                "description",
                "date",
                "status"
            ),
            (
                "ID",
                "Type",
                "From",
                "To",
                "Amount",
                "Description",
                "Date",
                "Status"
            )
        )

        self.refresh_table(
            tree,
            self.db.transactions
        )

        self.button(
            page,
            "Refresh",
            lambda: self.refresh_table(
                tree,
                self.db.transactions
            )
        ).pack(pady=8)

    # ============================================================
    # FRAUD DETECTION SCREEN
    # ============================================================

    def show_fraud(self):
        self.db.require_admin()

        page = self.page(
            "Fraud Detection & Alerts"
        )

        controls = ctk.CTkFrame(
            page,
            fg_color=CARD
        )

        controls.pack(
            fill="x",
            padx=18,
            pady=8
        )

        def scan():
            count = self.run(
                self.db.scan_fraud
            )

            if count is not None:
                messagebox.showinfo(
                    "Fraud Scan",
                    f"{count} new alert(s) created."
                )

                self.show_fraud()

        self.button(
            controls,
            "Run Fraud Detection",
            scan,
            190
        ).pack(
            side="left",
            padx=8,
            pady=12
        )

        alert_id = ctk.CTkEntry(
            controls,
            placeholder_text="Alert ID",
            width=110
        )

        alert_id.pack(
            side="left",
            padx=8
        )

        def review(status):
            def action():
                if not alert_id.get().isdigit():
                    raise ValueError(
                        "Enter a valid Alert ID."
                    )

                self.db.review(
                    int(alert_id.get()),
                    status
                )

                self.show_fraud()

            self.run(action)

        self.button(
            controls,
            "Mark Reviewed",
            lambda: review("Reviewed"),
            140
        ).pack(
            side="left",
            padx=5
        )

        self.button(
            controls,
            "False Positive",
            lambda: review("FalsePositive"),
            140
        ).pack(
            side="left",
            padx=5
        )

        tree = self.table(
            page,
            (
                "id",
                "tx",
                "rule",
                "description",
                "risk",
                "status",
                "created"
            ),
            (
                "Alert ID",
                "Transaction",
                "Rule",
                "Description",
                "Risk",
                "Status",
                "Created"
            )
        )

        self.refresh_table(
            tree,
            self.db.alerts
        )

    # ============================================================
    # FRAUD RULES SCREEN
    # ============================================================

    def show_rules(self):
        self.db.require_admin()

        page = self.page(
            "Fraud Rules"
        )

        tree = self.table(
            page,
            (
                "id",
                "name",
                "type",
                "threshold",
                "window",
                "active"
            ),
            (
                "ID",
                "Rule Name",
                "Rule Type",
                "Threshold",
                "Window (min)",
                "Active"
            )
        )

        self.refresh_table(
            tree,
            self.db.fraud_rules
        )

        self.button(
            page,
            "Refresh",
            lambda: self.refresh_table(
                tree,
                self.db.fraud_rules
            )
        ).pack(pady=8)

    # ============================================================
    # AUDIT LOGS SCREEN
    # ============================================================

    def show_logs(self):
        self.db.require_admin()

        page = self.page(
            "Audit Logs"
        )

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

        self.refresh_table(
            tree,
            self.db.logs
        )

        self.button(
            page,
            "Refresh",
            lambda: self.refresh_table(
                tree,
                self.db.logs
            )
        ).pack(pady=8)

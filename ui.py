
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
            "Account Management" if is_admin
            else "My Accounts"
        )

        rows = self.db.accounts()

        # ==========================================
        # ADMIN: SEARCH + DELETE ZERO-BALANCE ACCOUNT
        # ==========================================
        if is_admin:

            search_frame = ctk.CTkFrame(
                page,
                fg_color=CARD,
                corner_radius=12
            )
            search_frame.pack(
                fill="x",
                padx=18,
                pady=10
            )

            ctk.CTkLabel(
                search_frame,
                text="Search Accounts by Customer Name",
                text_color=WHITE
            ).pack(
                anchor="w",
                padx=12,
                pady=(12, 5)
            )

            search_entry = ctk.CTkEntry(
                search_frame,
                placeholder_text="Enter customer name...",
                width=350
            )
            search_entry.pack(
                anchor="w",
                padx=12,
                pady=(0, 12)
            )

            tree = self.table(
                page,
                (
                    "id",
                    "number",
                    "customer",
                    "balance",
                    "currency",
                    "status"
                ),
                (
                    "Account ID",
                    "Account Number",
                    "Customer Name",
                    "Balance",
                    "Currency",
                    "Status"
                )
            )

            def refresh_accounts(*args):
                search_text = (
                    search_entry.get()
                    .strip()
                    .casefold()
                )

                # Remove existing rows.
                for item in tree.get_children():
                    tree.delete(item)

                # Admin row format:
                # 0 AccountID
                # 1 AccountNumber
                # 2 CustomerName
                # 3 AccountType
                # 4 Balance
                # 5 Currency
                # 6 IsActive

                for row in rows:
                    customer_name = str(row[2])

                    if (
                        search_text
                        and search_text
                        not in customer_name.casefold()
                    ):
                        continue

                    status = (
                        "Active"
                        if bool(row[6])
                        else "Inactive"
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
                        )
                    )

            # Search while typing.
            search_entry.bind(
                "<KeyRelease>",
                refresh_accounts
            )

            refresh_accounts()

            def delete_selected():
                def action():
                    selected = tree.selection()

                    if not selected:
                        messagebox.showwarning(
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
                    customer_name = values[2]
                    balance = money(
                        values[3],
                        allow_zero=True
                    )
                    status = values[5]

                    if status != "Active":
                        raise ValueError(
                            "This account is already inactive."
                        )

                    if balance != 0:
                        raise ValueError(
                            "Only accounts with 0 TRY balance "
                            "can be deleted."
                        )

                    confirmed = messagebox.askyesno(
                        "Confirm Account Deletion",
                        (
                            "Deactivate this bank account?\n\n"
                            f"Customer: {customer_name}\n"
                            f"Account: {account_number}\n"
                            f"Balance: {balance:.2f} TRY\n\n"
                            "Transaction history will be preserved."
                        )
                    )

                    if not confirmed:
                        return

                    self.db.delete_account(
                        account_id
                    )

                    messagebox.showinfo(
                        "Success",
                        "Account deactivated successfully."
                    )

                    self.show_accounts()

                self.run(action)

            self.button(
                page,
                "Delete Selected Account",
                delete_selected
            ).pack(
                pady=(12, 5)
            )

            self.button(
                page,
                "Refresh Accounts",
                lambda: self.run(
                    self.show_accounts
                )
            ).pack(
                pady=(0, 12)
            )

            return

        # ==========================================
        # CUSTOMER: VIEW + CREATE OWN ACCOUNTS
        # ==========================================

        active_count = sum(
            1
            for row in rows
            if bool(row[5])
        )

        info_frame = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=12
        )
        info_frame.pack(
            fill="x",
            padx=18,
            pady=10
        )

        ctk.CTkLabel(
            info_frame,
            text=(
                f"Active Accounts: "
                f"{active_count} / 3"
            ),
            text_color=WHITE,
            font=("Arial", 16, "bold")
        ).pack(
            anchor="w",
            padx=12,
            pady=12
        )

        def create_account():
            def action():
                customer_id = session["customer_id"]

                account_id = self.db.add_account(
                    customer_id
                )

                messagebox.showinfo(
                    "Account Created",
                    (
                        "Your bank account was created.\n"
                        f"Account ID: {account_id}\n"
                        "Opening balance: 0 TRY"
                    )
                )

                self.show_accounts()

            self.run(action)

        create_button = self.button(
            page,
            "Create Account",
            create_account
        )
        create_button.pack(
            pady=(5, 12)
        )

        if active_count >= 3:
            create_button.configure(
                state="disabled"
            )

        tree = self.table(
            page,
            (
                "id",
                "number",
                "balance",
                "currency",
                "status"
            ),
            (
                "Account ID",
                "Account Number",
                "Balance",
                "Currency",
                "Status"
            )
        )

        # Customer row format:
        # 0 AccountID
        # 1 AccountNumber
        # 2 AccountType
        # 3 Balance
        # 4 Currency
        # 5 IsActive

        for row in rows:
            tree.insert(
                "",
                "end",
                values=(
                    row[0],
                    str(row[1]).strip(),
                    f"{row[3]:.2f}",
                    str(row[4]).strip(),
                    (
                        "Active"
                        if bool(row[5])
                        else "Inactive"
                    )
                )
            )

        self.button(
            page,
            "Refresh Accounts",
            lambda: self.run(
                self.show_accounts
            )
        ).pack(
            pady=12
        )

    # ============================================================
    # TRANSACTIONS SCREEN
    # ============================================================

    def show_transactions(self):
        session = self.db.require_login()
        is_admin = session["role"] == "Admin"

        page = self.page(
            "Transactions" if is_admin
            else "My Transactions"
        )

        account_rows = self.db.accounts()
        account_map = {}

        for row in account_rows:
            active = bool(
                row[6] if is_admin else row[5]
            )

            if not active:
                continue

            account_id = int(row[0])
            account_number = str(row[1]).strip()
            balance = row[4] if is_admin else row[3]

            label = (
                f"{account_number} | "
                f"{balance} TRY"
            )

            account_map[label] = {
                "id": account_id,
                "number": account_number
            }

        account_labels = list(account_map)

        form = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=12
        )
        form.pack(
            fill="x",
            padx=18,
            pady=8
        )

        # Transaction type
        ctk.CTkLabel(
            form,
            text="Transaction Type",
            text_color=WHITE
        ).grid(
            row=0, column=0,
            padx=10, pady=(12, 5),
            sticky="w"
        )

        kind = ctk.CTkComboBox(
            form,
            values=[
                "Deposit",
                "Withdrawal",
                "Transfer"
            ],
            width=165,
            state="readonly"
        )
        kind.grid(
            row=1, column=0,
            padx=10, pady=5,
            sticky="w"
        )

        # Source account
        ctk.CTkLabel(
            form,
            text="From / My Account",
            text_color=WHITE
        ).grid(
            row=0, column=1,
            padx=10, pady=(12, 5),
            sticky="w"
        )

        source = ctk.CTkComboBox(
            form,
            values=account_labels or [
                "No active accounts"
            ],
            width=290,
            state="readonly"
        )
        source.grid(
            row=1, column=1,
            padx=10, pady=5,
            sticky="w"
        )

        # Transfer destination mode
        transfer_mode_label = ctk.CTkLabel(
            form,
            text="Transfer To",
            text_color=WHITE
        )
        transfer_mode_label.grid(
            row=2, column=0,
            padx=10, pady=(12, 5),
            sticky="w"
        )

        transfer_mode = ctk.CTkComboBox(
            form,
            values=[
                "My Own Accounts",
                "Another Customer"
            ],
            width=180,
            state="readonly"
        )
        transfer_mode.grid(
            row=3, column=0,
            padx=10, pady=5,
            sticky="w"
        )

        # Own-account destination
        own_destination_label = ctk.CTkLabel(
            form,
            text="To My Account",
            text_color=WHITE
        )
        own_destination_label.grid(
            row=2, column=1,
            padx=10, pady=(12, 5),
            sticky="w"
        )

        own_destination = ctk.CTkComboBox(
            form,
            values=account_labels or [
                "No active accounts"
            ],
            width=290,
            state="readonly"
        )
        own_destination.grid(
            row=3, column=1,
            padx=10, pady=5,
            sticky="w"
        )

        # External recipient
        external_destination_label = ctk.CTkLabel(
            form,
            text="Recipient Account Number",
            text_color=WHITE
        )
        external_destination_label.grid(
            row=2, column=1,
            padx=10, pady=(12, 5),
            sticky="w"
        )

        external_destination = ctk.CTkEntry(
            form,
            placeholder_text="TR + 16 digits",
            width=290
        )
        external_destination.grid(
            row=3, column=1,
            padx=10, pady=5,
            sticky="w"
        )

        # Amount
        ctk.CTkLabel(
            form,
            text="Amount (TRY)",
            text_color=WHITE
        ).grid(
            row=0, column=2,
            padx=10, pady=(12, 5),
            sticky="w"
        )

        amount = ctk.CTkEntry(
            form,
            placeholder_text="Amount",
            width=150
        )
        amount.grid(
            row=1, column=2,
            padx=10, pady=5,
            sticky="w"
        )

        # Description
        ctk.CTkLabel(
            form,
            text="Description",
            text_color=WHITE
        ).grid(
            row=0, column=3,
            padx=10, pady=(12, 5),
            sticky="w"
        )

        description = ctk.CTkEntry(
            form,
            placeholder_text="Optional",
            width=190
        )
        description.grid(
            row=1, column=3,
            padx=10, pady=5,
            sticky="w"
        )

        def update_destination_fields(*args):
            selected_kind = kind.get()

            transfer_mode_label.grid_remove()
            transfer_mode.grid_remove()
            own_destination_label.grid_remove()
            own_destination.grid_remove()
            external_destination_label.grid_remove()
            external_destination.grid_remove()

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

        kind.configure(
            command=update_destination_fields
        )
        transfer_mode.configure(
            command=update_destination_fields
        )

        kind.set("Deposit")
        transfer_mode.set("My Own Accounts")

        if account_labels:
            source.set(account_labels[0])
            own_destination.set(account_labels[0])

        update_destination_fields()

        def execute():
            def action():
                selected_source = source.get()

                if selected_source not in account_map:
                    raise ValueError(
                        "Please select an active source account."
                    )

                source_id = account_map[
                    selected_source
                ]["id"]

                selected_kind = kind.get()
                destination_number = ""

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
                                "Please select a destination account."
                            )

                        destination_number = account_map[
                            selected_destination
                        ]["number"]

                    else:
                        destination_number = (
                            external_destination.get()
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

                tx_id = self.db.transact(
                    selected_kind,
                    source_id,
                    destination_number,
                    amount.get(),
                    description.get()
                )

                messagebox.showinfo(
                    "Transaction Completed",
                    f"Transaction ID: {tx_id}"
                )

                self.show_transactions()

            self.run(action)

        self.button(
            page,
            "Execute Transaction",
            execute
        ).pack(pady=10)

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
                "From Account",
                "To Account",
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
            lambda: self.run(
                self.show_transactions
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

from decimal import Decimal


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
        self.geometry("1350x950")
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
            "Registration",
            "All fields are required",
            820
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

        # City and district are entered manually.
        city = self.entry(
            card,
            "City (İl)"
        )

        district = self.entry(
            card,
            "District (İlçe)"
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

                messagebox.showinfo(
                    "Registration Successful",
                    "Registration Successful!"
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
                ("Send Announcement", self.show_send_announcement),
                ("Audit Logs", self.show_logs)
            ]
        else:
            navigation = [
                ("Dashboard", self.show_dashboard),
                ("My Accounts", self.show_accounts),
                ("My Transactions", self.show_transactions),
                ("My Fraud Reviews", self.show_customer_fraud_reviews),
                ("Notifications", self.show_notifications)
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

        # ========================================================
        # ADMIN: VIEW AND SEARCH ACCOUNTS
        # ========================================================

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

            customer_names = sorted(
                {
                    str(row[2]).strip()
                    for row in rows
                }
            )

            customer_options = (
                ["All Customers"] + customer_names
            )

            customer_combo = ctk.CTkComboBox(
                search_frame,
                values=customer_options,
                width=350,
                state="readonly"
            )
            customer_combo.pack(
                anchor="w",
                padx=12,
                pady=(0, 12)
            )
            customer_combo.set("All Customers")

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
                selected_customer = customer_combo.get()

                tree.delete(*tree.get_children())

                for row in rows:
                    customer_name = str(row[2]).strip()

                    if (
                        selected_customer != "All Customers"
                        and customer_name != selected_customer
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

            customer_combo.configure(
                command=refresh_accounts
            )

            refresh_accounts()

            return

        # ========================================================
        # CUSTOMER: VIEW AND CREATE OWN ACCOUNTS
        # ========================================================

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

        # ========================================================
        # CUSTOMER ACCOUNTS TABLE
        # ========================================================

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

        # ========================================================
        # CUSTOMER: CLOSE SELECTED ZERO-BALANCE ACCOUNT
        # ========================================================

        def close_selected_account():
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
                balance = Decimal(str(values[2]))
                status = values[4]

                if status != "Active":
                    raise ValueError(
                        "This account is already inactive."
                    )

                if balance != 0:
                    raise ValueError(
                        "Only accounts with 0 TRY balance "
                        "can be closed."
                    )

                confirmed = messagebox.askyesno(
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

                messagebox.showinfo(
                    "Success",
                    "Your bank account has been closed successfully."
                )

                self.show_accounts()

            self.run(action)

        self.button(
            page,
            "Close Selected Account",
            close_selected_account
        ).pack(
            pady=(12, 5)
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

        tree = self.table(
            page,
            columns,
            headings
        )

        def refresh_transactions():
            rows = self.db.transactions()

            tree.delete(*tree.get_children())

            for row in rows:
                fraud_status = row[10] or "Not Flagged"

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

        self.run(refresh_transactions)

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



    # ============================================================
    # FRAUD DETECTION SCREEN
    # ============================================================


    def show_fraud(self):
        self.db.require_admin()

        page = self.page("Fraud Detection & Alerts")
        rows = self.db.alerts()

        # ========================================================
        # ACTION PANEL
        # ========================================================

        actions = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=10
        )
        actions.pack(
            fill="x",
            padx=18,
            pady=(10, 8)
        )

        def scan():
            def action():
                count = self.db.scan_fraud()

                messagebox.showinfo(
                    "Fraud Detection",
                    f"{count} new fraud alerts created."
                )

                self.show_fraud()

            self.run(action)

        self.button(
            actions,
            "Run Fraud Detection",
            scan,
            width=180
        ).pack(
            side="left",
            padx=8,
            pady=12
        )

        self.button(
            actions,
            "Refresh",
            lambda: self.run(self.show_fraud),
            width=110
        ).pack(
            side="left",
            padx=8,
            pady=12
        )

        # ========================================================
        # FRAUD ALERTS TABLE
        # ========================================================

        columns = (
            "alert",
            "transaction",
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

        tree = self.table(
            page,
            columns,
            headings
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

        # ========================================================
        # LOAD FRAUD ALERTS
        # ========================================================

        # Expected row indexes from fraud.py:
        #
        # 0  AlertID
        # 1  TransactionID
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

        for row in rows:
            alert_id = int(row[0])

            alert_details[alert_id] = row

            sender = (
                str(row[5])
                if row[5] is not None
                else "-"
            )

            receiver = (
                str(row[8])
                if row[8] is not None
                else "-"
            )

            sender_account = (
                str(row[6]).strip()
                if row[6] is not None
                else "-"
            )

            receiver_account = (
                str(row[9]).strip()
                if row[9] is not None
                else "-"
            )

            transaction_description = (
                str(row[17])
                if row[17] is not None and str(row[17]).strip()
                else "-"
            )

            admin_review_note = (
                str(row[16])
                if row[16] is not None and str(row[16]).strip()
                else "-"
            )

            tree.insert(
                "",
                "end",
                iid=str(alert_id),
                values=(
                    alert_id,
                    row[1],
                    row[2],
                    row[3],
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

        # ========================================================
        # SELECTED ALERT DETAILS
        # ========================================================

        info = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=10
        )
        info.pack(
            fill="x",
            padx=18,
            pady=(5, 5)
        )

        detail_label = ctk.CTkLabel(
            info,
            text="Select an alert to view details.",
            text_color=WHITE,
            justify="left",
            anchor="w",
            wraplength=850
        )
        detail_label.pack(
            fill="x",
            padx=12,
            pady=10
        )

        # ========================================================
        # ADMIN REVIEW NOTE
        # ========================================================

        review_frame = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=10
        )
        review_frame.pack(
            fill="x",
            padx=18,
            pady=(5, 5)
        )

        ctk.CTkLabel(
            review_frame,
            text="Admin Review Note (Optional, max 500 characters)",
            text_color=WHITE,
            font=("Arial", 14, "bold")
        ).pack(
            anchor="w",
            padx=12,
            pady=(10, 4)
        )

        review_note = ctk.CTkTextbox(
            review_frame,
            height=75,
            fg_color=SIDEBAR,
            text_color=WHITE,
            corner_radius=8
        )
        review_note.pack(
            fill="x",
            padx=12,
            pady=(0, 10)
        )

        # ========================================================
        # REVIEW BUTTONS FRAME
        # ========================================================

        review_actions = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )
        review_actions.pack(
            fill="x",
            padx=18,
            pady=(5, 10)
        )

        def get_selected_alert():
            selected = tree.selection()

            if not selected:
                raise ValueError(
                    "Please select an alert from the table."
                )

            alert_id = int(selected[0])

            return alert_id, alert_details[alert_id]

        # ========================================================
        # SHOW SELECTED ALERT DETAILS
        # ========================================================

        def show_details(event=None):
            selected = tree.selection()

            if not selected:
                return

            alert_id = int(selected[0])
            row = alert_details[alert_id]

            transaction_description = (
                str(row[17])
                if row[17] is not None and str(row[17]).strip()
                else "-"
            )

            saved_review_note = (
                str(row[16])
                if row[16] is not None
                else ""
            )

            detail_label.configure(
                text=(
                    f"Alert ID: {row[0]}    "
                    f"Transaction ID: {row[1]}\n"
                    f"Rule: {row[2]}\n"
                    f"Sender: {row[5] or '-'}    "
                    f"Receiver: {row[8] or '-'}\n"
                    f"Amount: {row[10]:.2f} TRY    "
                    f"Risk: {row[12]}\n"
                    f"Transaction Description: "
                    f"{transaction_description}\n"
                    f"Status: {row[13]}\n"
                    f"Reason: {row[11]}"
                )
            )

            # Enable temporarily to update textbox content.
            review_note.configure(state="normal")
            review_note.delete("1.0", "end")

            is_pending = row[13] == "Pending"

            if not is_pending and saved_review_note:
                review_note.insert(
                    "1.0",
                    saved_review_note
                )

            # Pending alerts can be reviewed.
            # Already reviewed alerts are read-only.
            review_note.configure(
                state=(
                    "normal"
                    if is_pending
                    else "disabled"
                )
            )

            for button in decision_buttons:
                button.configure(
                    state=(
                        "normal"
                        if is_pending
                        else "disabled"
                    )
                )

        tree.bind(
            "<<TreeviewSelect>>",
            show_details
        )

        # ========================================================
        # CHANGE FRAUD REVIEW STATUS
        # ========================================================

        def change_status(status):
            def action():
                alert_id, row = get_selected_alert()

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
                        "Review note cannot exceed 500 characters."
                    )

                confirmed = messagebox.askyesno(
                    "Confirm Decision",
                    (
                        f"Alert ID: {alert_id}\n"
                        f"New Status: {status}\n"
                        f"Review Note: {note or '(empty)'}\n\n"
                        "Do you want to continue?"
                    )
                )

                if not confirmed:
                    return

                self.db.review(
                    alert_id,
                    status,
                    note
                )

                messagebox.showinfo(
                    "Success",
                    (
                        f"Alert marked as {status}.\n"
                        "Review information saved."
                    )
                )

                self.show_fraud()

            self.run(action)

        # ========================================================
        # MARK REVIEWED BUTTON
        # ========================================================

        reviewed_button = self.button(
            review_actions,
            "Mark Reviewed",
            lambda: change_status("Reviewed"),
            width=160
        )
        reviewed_button.pack(
            side="left",
            padx=8,
            pady=5
        )

        # ========================================================
        # FALSE POSITIVE BUTTON
        # ========================================================

        false_positive_button = self.button(
            review_actions,
            "False Positive",
            lambda: change_status("FalsePositive"),
            width=160
        )
        false_positive_button.pack(
            side="left",
            padx=8,
            pady=5
        )

        # ========================================================
        # CONFIRM FRAUD BUTTON
        # ========================================================

        confirm_fraud_button = self.button(
            review_actions,
            "Confirm Fraud",
            lambda: change_status("ConfirmedFraud"),
            width=160
        )
        confirm_fraud_button.pack(
            side="left",
            padx=8,
            pady=5
        )

        decision_buttons = (
            reviewed_button,
            false_positive_button,
            confirm_fraud_button
        )

        # Disable buttons until an alert is selected.
        for button in decision_buttons:
            button.configure(state="disabled")


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
    # CUSTOMER FRAUD REVIEWS SCREEN
    # ============================================================


    def show_customer_fraud_reviews(self):
        session = self.db.require_login()

        if session["role"] != "Customer":
            raise PermissionError(
                "This page is for customers only."
            )

        page = self.page("My Fraud Reviews")

        ctk.CTkLabel(
            page,
            text="Admin reviews related to your transactions",
            text_color=MUTED,
            font=("Arial", 15)
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 12)
        )

        # ========================================================
        # TABLE COLUMNS
        # ========================================================

        columns = (
            "alert",
            "transaction",
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
            "Transaction Type",
            "Amount (TRY)",
            "Transaction Description",
            "Fraud Rule",
            "Risk",
            "Review Status",
            "Admin Review Note",
            "Reviewed At"
        )

        tree = self.table(
            page,
            columns,
            headings
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
            anchor="w"
        )

        # ========================================================
        # REFRESH REVIEWS
        # ========================================================

        def refresh_reviews():
            rows = self.db.customer_fraud_reviews()

            tree.delete(*tree.get_children())

            for row in rows:
                transaction_description = (
                    str(row[9])
                    if row[9] is not None and str(row[9]).strip()
                    else "-"
                )

                tree.insert(
                    "",
                    "end",
                    values=(
                        row[0],
                        row[1],
                        row[2],
                        f"{row[3]:.2f}",
                        transaction_description,
                        row[4],
                        row[5],
                        row[6],
                        row[7] if row[7] else "-",
                        (
                            str(row[8])[:19]
                            if row[8] is not None
                            else "-"
                        )
                    )
                )

        self.button(
            page,
            "Refresh Reviews",
            lambda: self.run(refresh_reviews)
        ).pack(pady=12)

        self.run(refresh_reviews)

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

        info = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=12
        )
        info.pack(
            fill="x",
            padx=18,
            pady=(5, 10)
        )

        ctk.CTkLabel(
            info,
            text=f"Unread Notifications: {unread_count}",
            font=("Arial", 17, "bold"),
            text_color=WHITE
        ).pack(
            anchor="w",
            padx=15,
            pady=15
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

        tree.column(
            "title",
            width=200,
            anchor="w"
        )

        tree.column(
            "message",
            width=450,
            minwidth=220,
            anchor="w"
        )

        for row in rows:
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
                )
            )

        actions = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )
        actions.pack(pady=12)

        def mark_selected():
            def action():
                selected = tree.selection()

                if not selected:
                    messagebox.showwarning(
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

        def mark_all():
            def action():
                self.db.mark_all_notifications_read()
                self.show_notifications()

            self.run(action)

        self.button(
            actions,
            "Mark Selected as Read",
            mark_selected,
            width=200
        ).pack(
            side="left",
            padx=8
        )

        self.button(
            actions,
            "Mark All as Read",
            mark_all,
            width=180
        ).pack(
            side="left",
            padx=8
        )

    # ============================================================
    # ADMIN SEND ANNOUNCEMENT
    # ============================================================

    def show_send_announcement(self):
        self.db.require_admin()

        page = self.page("Send Announcement")

        form = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=12
        )
        form.pack(
            fill="x",
            padx=18,
            pady=12
        )

        ctk.CTkLabel(
            form,
            text="Send Announcement to Customers",
            font=("Arial", 18, "bold"),
            text_color=WHITE
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 12)
        )

        # Recipient selection
        ctk.CTkLabel(
            form,
            text="Recipient",
            text_color=WHITE
        ).pack(
            anchor="w",
            padx=20
        )

        customers = self.db.customers()

        customer_map = {}

        for row in customers:
            customer_id = int(row[0])

            # Only active customers.
            if not bool(row[7]):
                continue

            customer_name = (
                f"{row[1]} {row[2]}"
            ).strip()

            label = (
                f"{customer_name} "
                f"(ID: {customer_id})"
            )

            customer_map[label] = customer_id

        recipient_options = (
            ["All Active Customers"]
            + sorted(customer_map.keys())
        )

        recipient = ctk.CTkComboBox(
            form,
            values=recipient_options,
            width=400,
            state="readonly"
        )
        recipient.pack(
            anchor="w",
            padx=20,
            pady=(5, 15)
        )
        recipient.set("All Active Customers")

        # Announcement title
        ctk.CTkLabel(
            form,
            text="Announcement Title",
            text_color=WHITE
        ).pack(
            anchor="w",
            padx=20
        )

        title_entry = ctk.CTkEntry(
            form,
            placeholder_text="Enter announcement title",
            width=500,
            height=42
        )
        title_entry.pack(
            anchor="w",
            padx=20,
            pady=(5, 15)
        )

        # Announcement message
        ctk.CTkLabel(
            form,
            text="Announcement Message",
            text_color=WHITE
        ).pack(
            anchor="w",
            padx=20
        )

        message_entry = ctk.CTkTextbox(
            form,
            width=650,
            height=180,
            fg_color=SIDEBAR,
            text_color=WHITE,
            corner_radius=8
        )
        message_entry.pack(
            anchor="w",
            padx=20,
            pady=(5, 15)
        )

        def send():
            def action():
                title = title_entry.get().strip()

                message = message_entry.get(
                    "1.0",
                    "end-1c"
                ).strip()

                if not title or not message:
                    raise ValueError(
                        "Title and message are required."
                    )

                selected = recipient.get()

                if selected == "All Active Customers":
                    customer_id = None
                    recipient_text = "all active customers"
                else:
                    if selected not in customer_map:
                        raise ValueError(
                            "Please select a valid customer."
                        )

                    customer_id = customer_map[selected]
                    recipient_text = selected

                confirmed = messagebox.askyesno(
                    "Confirm Announcement",
                    (
                        f"Recipient: {recipient_text}\n\n"
                        f"Title: {title}\n\n"
                        "Do you want to send this announcement?"
                    )
                )

                if not confirmed:
                    return

                sent_count = self.db.send_announcement(
                    title,
                    message,
                    customer_id
                )

                messagebox.showinfo(
                    "Announcement Sent",
                    (
                        "Announcement sent successfully.\n"
                        f"Recipients: {sent_count}"
                    )
                )

                self.show_send_announcement()

            self.run(action)

        self.button(
            form,
            "Send Announcement",
            send,
            width=220
        ).pack(
            anchor="w",
            padx=20,
            pady=(5, 25)
        )

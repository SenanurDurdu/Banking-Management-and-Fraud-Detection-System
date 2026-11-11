import os
import secrets
import string

from decimal import Decimal, InvalidOperation

import customtkinter as ctk

from tkinter import ttk, messagebox

import pyodbc


# =========================================================
# DATABASE CONFIGURATIONpython app.py
# =========================================================

DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_NAME = os.getenv("DB_NAME", "BankingFraudDB")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
DB_TRUSTED = os.getenv("DB_TRUSTED", "no")
DB_USERNAME = os.getenv("DB_USERNAME", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


# =========================================================
# DATABASE CONNECTION
# =========================================================

def connect():

    auth = (
        "Trusted_Connection=yes;"
        if DB_TRUSTED.lower() == "yes"
        else f"UID={DB_USERNAME};PWD={DB_PASSWORD};"
    )

    connection = pyodbc.connect(

        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"{auth}"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;",

        timeout=5
    )

    return connection
# =========================================================
# VALIDATION
# =========================================================

def amount(value):

    try:

        value = Decimal(
            str(value).replace(",", ".")
        )

    except (InvalidOperation, ValueError):

        raise ValueError(
            "Enter a valid amount."
        )

    if value <= 0:

        raise ValueError(
            "Amount must be greater than zero."
        )

    return value.quantize(
        Decimal("0.01")
    )


# =========================================================
# AUDIT LOG
# =========================================================

def audit(
    cursor,
    action,
    entity,
    entity_id,
    description
):

    cursor.execute(

        """
        INSERT INTO AuditLogs
        (
            ActionType,
            EntityName,
            EntityID,
            Description
        )

        VALUES (?, ?, ?, ?)
        """,

        action,
        entity,
        entity_id,
        description
    )


# =========================================================
# BANKING SERVICE
# =========================================================

class Bank:

    # DATABASE TEST

    def test(self):

        with connect() as connection:

            cursor = connection.cursor()

            result = cursor.execute(
                "SELECT DB_NAME()"
            ).fetchone()

            return result[0]


    # -----------------------------------------------------
    # CUSTOMER OPERATIONS
    # -----------------------------------------------------

    def customers(self):

        with connect() as connection:

            cursor = connection.cursor()

            return cursor.execute(

                """
                SELECT
                    CustomerID,
                    FirstName,
                    LastName,
                    NationalID,
                    Phone,
                    Email,
                    IsActive

                FROM Customers

                ORDER BY CustomerID DESC
                """

            ).fetchall()


    def add_customer(
        self,
        first,
        last,
        nid,
        phone,
        email,
        address
    ):

        if not first.strip() or not last.strip():

            raise ValueError(
                "First and last name are required."
            )

        if not nid.isdigit() or len(nid) != 11:

            raise ValueError(
                "National ID must be 11 digits."
            )

        with connect() as connection:

            cursor = connection.cursor()

            cursor.execute(

                """
                INSERT INTO Customers
                (
                    FirstName,
                    LastName,
                    NationalID,
                    Phone,
                    Email,
                    Address
                )

                VALUES (?, ?, ?, ?, ?, ?)
                """,

                first.strip(),
                last.strip(),
                nid,
                phone,
                email,
                address
            )

            customer_id = cursor.execute(
                "SELECT SCOPE_IDENTITY()"
            ).fetchone()[0]

            audit(
                cursor,
                "CREATE",
                "Customer",
                customer_id,
                "Customer created"
            )

            connection.commit()

            return customer_id


    def customer_choices(self):

        with connect() as connection:

            cursor = connection.cursor()

            return cursor.execute(

                """
                SELECT
                    CustomerID,
                    FirstName,
                    LastName

                FROM Customers

                WHERE IsActive = 1

                ORDER BY FirstName
                """

            ).fetchall()


    # -----------------------------------------------------
    # ACCOUNT OPERATIONS
    # -----------------------------------------------------

    def accounts(self):

        with connect() as connection:

            cursor = connection.cursor()

            return cursor.execute(

                """
                SELECT
                    AccountID,
                    AccountNumber,
                    FirstName + ' ' + LastName,
                    AccountType,
                    Balance,
                    Currency,
                    IsActive

                FROM vw_AccountSummary

                ORDER BY AccountID DESC
                """

            ).fetchall()


    def add_account(
        self,
        customer_id,
        account_type,
        opening_balance
    ):

        opening_balance = (

            Decimal("0")

            if not opening_balance.strip()

            else amount(opening_balance)

        )

        account_number = (

            "TR"

            + "".join(
                secrets.choice(string.digits)
                for _ in range(16)
            )

        )

        with connect() as connection:

            cursor = connection.cursor()

            cursor.execute(

                """
                INSERT INTO Accounts
                (
                    CustomerID,
                    AccountNumber,
                    AccountType,
                    Balance
                )

                VALUES (?, ?, ?, ?)
                """,

                customer_id,
                account_number,
                account_type,
                opening_balance
            )

            account_id = cursor.execute(
                "SELECT SCOPE_IDENTITY()"
            ).fetchone()[0]

            audit(
                cursor,
                "CREATE",
                "Account",
                account_id,
                "Account created"
            )

            connection.commit()

            return account_id


    # -----------------------------------------------------
    # TRANSACTION OPERATIONS
    # -----------------------------------------------------

    def account_locked(
        self,
        cursor,
        account_id
    ):

        row = cursor.execute(

            """
            SELECT
                AccountID,
                Balance,
                Currency,
                IsActive

            FROM Accounts WITH (UPDLOCK, ROWLOCK)

            WHERE AccountID = ?
            """,

            account_id

        ).fetchone()

        if not row or not row.IsActive:

            raise ValueError(
                f"Account {account_id} not found or inactive."
            )

        return row


    def insert_tx(
        self,
        cursor,
        transaction_type,
        source,
        destination,
        value,
        description
    ):

        cursor.execute(

            """
            INSERT INTO Transactions
            (
                FromAccountID,
                ToAccountID,
                TransactionType,
                Amount,
                Description
            )

            VALUES (?, ?, ?, ?, ?)
            """,

            source,
            destination,
            transaction_type,
            value,
            description
        )

        return cursor.execute(
            "SELECT SCOPE_IDENTITY()"
        ).fetchone()[0]


    def transact(
        self,
        transaction_type,
        source,
        destination,
        value,
        description
    ):

        value = amount(value)

        with connect() as connection:

            cursor = connection.cursor()

            # DEPOSIT

            if transaction_type == "Deposit":

                self.account_locked(
                    cursor,
                    source
                )

                cursor.execute(

                    """
                    UPDATE Accounts

                    SET Balance = Balance + ?

                    WHERE AccountID = ?
                    """,

                    value,
                    source
                )

                transaction_id = self.insert_tx(

                    cursor,
                    "Deposit",
                    None,
                    source,
                    value,
                    description
                )


            # WITHDRAWAL

            elif transaction_type == "Withdrawal":

                account = self.account_locked(
                    cursor,
                    source
                )

                if account.Balance < value:

                    raise ValueError(
                        "Insufficient balance."
                    )

                cursor.execute(

                    """
                    UPDATE Accounts

                    SET Balance = Balance - ?

                    WHERE AccountID = ?
                    """,

                    value,
                    source
                )

                transaction_id = self.insert_tx(

                    cursor,
                    "Withdrawal",
                    source,
                    None,
                    value,
                    description
                )


            # TRANSFER

            else:

                if source == destination:

                    raise ValueError(
                        "Source and destination must differ."
                    )

                accounts = {}

                for account_id in sorted(
                    (source, destination)
                ):

                    accounts[account_id] = self.account_locked(
                        cursor,
                        account_id
                    )

                source_account = accounts[source]

                destination_account = accounts[destination]

                if source_account.Currency != destination_account.Currency:

                    raise ValueError(
                        "Different currencies cannot be transferred."
                    )

                if source_account.Balance < value:

                    raise ValueError(
                        "Insufficient balance."
                    )

                cursor.execute(

                    """
                    UPDATE Accounts

                    SET Balance = Balance - ?

                    WHERE AccountID = ?
                    """,

                    value,
                    source
                )

                cursor.execute(

                    """
                    UPDATE Accounts

                    SET Balance = Balance + ?

                    WHERE AccountID = ?
                    """,

                    value,
                    destination
                )

                transaction_id = self.insert_tx(

                    cursor,
                    "Transfer",
                    source,
                    destination,
                    value,
                    description
                )


            audit(
                cursor,
                transaction_type,
                "Transaction",
                transaction_id,
                f"{transaction_type} transaction; amount={value}"
            )

            connection.commit()

            return transaction_id


    def transactions(self):

        with connect() as connection:

            cursor = connection.cursor()

            return cursor.execute(

                """
                SELECT
                    t.TransactionID,
                    t.TransactionType,
                    f.AccountNumber,
                    d.AccountNumber,
                    t.Amount,
                    t.Description,
                    t.TransactionDate,
                    t.Status

                FROM Transactions t

                LEFT JOIN Accounts f
                    ON f.AccountID = t.FromAccountID

                LEFT JOIN Accounts d
                    ON d.AccountID = t.ToAccountID

                ORDER BY t.TransactionID DESC
                """

            ).fetchall()


    # -----------------------------------------------------
    # FRAUD DETECTION
    # -----------------------------------------------------

    def alerts(self):

        with connect() as connection:

            cursor = connection.cursor()

            return cursor.execute(

                """
                SELECT
                    a.AlertID,
                    a.TransactionID,
                    r.RuleName,
                    a.AlertDescription,
                    a.RiskLevel,
                    a.ReviewStatus,
                    a.CreatedAt

                FROM FraudAlerts a

                JOIN FraudRules r
                    ON r.RuleID = a.RuleID

                ORDER BY a.AlertID DESC
                """

            ).fetchall()


    def scan_fraud(self):

        new_alerts = 0

        with connect() as connection:

            cursor = connection.cursor()

            rules = cursor.execute(

                """
                SELECT
                    RuleID,
                    RuleName,
                    RuleType,
                    ThresholdValue,
                    TimeWindowMinutes

                FROM FraudRules

                WHERE IsActive = 1
                """

            ).fetchall()


            transactions = cursor.execute(

                """
                SELECT
                    TransactionID,
                    FromAccountID,
                    ToAccountID,
                    Amount,
                    TransactionDate

                FROM Transactions

                WHERE Status = 'Completed'
                """

            ).fetchall()


            for transaction in transactions:

                account_id = (
                    transaction.FromAccountID
                    or transaction.ToAccountID
                )

                for rule in rules:

                    suspicious = False

                    description = ""

                    risk = "Medium"


                    # HIGH AMOUNT

                    if (

                        rule.RuleType == "HighAmount"

                        and transaction.Amount >= rule.ThresholdValue

                    ):

                        suspicious = True

                        risk = "High"

                        description = (

                            f"Amount {transaction.Amount} reached "

                            f"high-value threshold {rule.ThresholdValue}."

                        )


                    # FREQUENT OR REPEATED TRANSACTIONS

                    elif (

                        rule.RuleType in (
                            "Frequent",
                            "RepeatedAmount"
                        )

                        and account_id

                    ):

                        if rule.RuleType == "Frequent":

                            count = cursor.execute(

                                """
                                SELECT COUNT(*)

                                FROM Transactions

                                WHERE TransactionDate BETWEEN
                                    DATEADD(MINUTE, -?, ?)
                                    AND ?

                                AND (
                                    FromAccountID = ?
                                    OR ToAccountID = ?
                                )

                                AND Status = 'Completed'
                                """,

                                rule.TimeWindowMinutes,
                                transaction.TransactionDate,
                                transaction.TransactionDate,
                                account_id,
                                account_id

                            ).fetchone()[0]


                            if count >= int(rule.ThresholdValue):

                                suspicious = True

                                description = (

                                    f"{count} transactions in "

                                    f"{rule.TimeWindowMinutes} minutes."

                                )

                                if count >= int(rule.ThresholdValue) + 3:

                                    risk = "High"


                        else:

                            count = cursor.execute(

                                """
                                SELECT COUNT(*)

                                FROM Transactions

                                WHERE Amount = ?

                                AND TransactionDate BETWEEN
                                    DATEADD(MINUTE, -?, ?)
                                    AND ?

                                AND (
                                    FromAccountID = ?
                                    OR ToAccountID = ?
                                )

                                AND Status = 'Completed'
                                """,

                                transaction.Amount,
                                rule.TimeWindowMinutes,
                                transaction.TransactionDate,
                                transaction.TransactionDate,
                                account_id,
                                account_id

                            ).fetchone()[0]


                            if count >= int(rule.ThresholdValue):

                                suspicious = True

                                description = (

                                    f"Same amount {transaction.Amount} "

                                    f"repeated {count} times in "

                                    f"{rule.TimeWindowMinutes} minutes."

                                )


                    # CREATE FRAUD ALERT

                    if suspicious:

                        cursor.execute(

                            """
                            IF NOT EXISTS
                            (
                                SELECT 1

                                FROM FraudAlerts

                                WHERE TransactionID = ?
                                AND RuleID = ?
                            )

                            INSERT INTO FraudAlerts
                            (
                                TransactionID,
                                RuleID,
                                AlertDescription,
                                RiskLevel
                            )

                            VALUES (?, ?, ?, ?)
                            """,

                            transaction.TransactionID,
                            rule.RuleID,

                            transaction.TransactionID,
                            rule.RuleID,
                            description,
                            risk

                        )

                        if cursor.rowcount > 0:

                            new_alerts += 1


            audit(
                cursor,
                "FRAUD_SCAN",
                "FraudAlert",
                None,
                f"{new_alerts} new alerts created"
            )

            connection.commit()

        return new_alerts


    def review(
        self,
        alert_id,
        status
    ):

        with connect() as connection:

            cursor = connection.cursor()

            cursor.execute(

                """
                UPDATE FraudAlerts

                SET
                    ReviewStatus = ?,
                    ReviewedAt = SYSDATETIME()

                WHERE AlertID = ?

                AND ReviewStatus = 'Pending'
                """,

                status,
                alert_id
            )

            if cursor.rowcount == 0:

                raise ValueError(
                    "Alert not found or already reviewed."
                )

            audit(
                cursor,
                "REVIEW",
                "FraudAlert",
                alert_id,
                status
            )

            connection.commit()


    # -----------------------------------------------------
    # DASHBOARD
    # -----------------------------------------------------

    def dashboard(self):

        with connect() as connection:

            cursor = connection.cursor()

            customers = cursor.execute(

                """
                SELECT COUNT(*)

                FROM Customers

                WHERE IsActive = 1
                """

            ).fetchone()[0]


            accounts = cursor.execute(

                """
                SELECT COUNT(*)

                FROM Accounts

                WHERE IsActive = 1
                """

            ).fetchone()[0]


            today_transactions = cursor.execute(

                """
                SELECT COUNT(*)

                FROM Transactions

                WHERE CAST(TransactionDate AS DATE)
                    = CAST(GETDATE() AS DATE)
                """

            ).fetchone()[0]


            pending_alerts = cursor.execute(

                """
                SELECT COUNT(*)

                FROM FraudAlerts

                WHERE ReviewStatus = 'Pending'
                """

            ).fetchone()[0]


            total_balance = cursor.execute(

                """
                SELECT COALESCE(SUM(Balance), 0)

                FROM Accounts

                WHERE IsActive = 1
                """

            ).fetchone()[0]


            return (
                customers,
                accounts,
                today_transactions,
                pending_alerts,
                total_balance
            )


    # -----------------------------------------------------
    # AUDIT LOGS
    # -----------------------------------------------------

    def logs(self):

        with connect() as connection:

            cursor = connection.cursor()

            return cursor.execute(

                """
                SELECT TOP 250

                    AuditID,
                    ActionType,
                    EntityName,
                    EntityID,
                    Description,
                    CreatedAt

                FROM AuditLogs

                ORDER BY AuditID DESC
                """

            ).fetchall()


# =========================================================
# CUSTOMTKINTER GUI
# =========================================================

class App(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.db = Bank()

        self.title(
            "Banking Management & Fraud Detection"
        )

        self.geometry("1250x800")


        # SIDEBAR

        self.sidebar = ctk.CTkFrame(
            self,
            width=190
        )

        self.sidebar.pack(
            side="left",
            fill="y",
            padx=8,
            pady=8
        )


        # MAIN CONTENT

        self.main = ctk.CTkFrame(self)

        self.main.pack(
            side="right",
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )


        ctk.CTkLabel(

            self.sidebar,

            text="BANKING SYSTEM",

            font=("Arial", 22, "bold")

        ).pack(pady=25)


        self.pages = {}


        self.build_dashboard()

        self.build_customers()

        self.build_accounts()

        self.build_transactions()

        self.build_fraud()

        self.build_logs()


        # NAVIGATION

        buttons = [

            ("Dashboard", "dash"),

            ("Customers", "customers"),

            ("Accounts", "accounts"),

            ("Transactions", "tx"),

            ("Fraud Alerts", "fraud"),

            ("Audit Logs", "logs")

        ]


        for label, key in buttons:

            ctk.CTkButton(

                self.sidebar,

                text=label,

                command=lambda k=key: self.show(k)

            ).pack(
                fill="x",
                padx=12,
                pady=6
            )


        ctk.CTkButton(

            self.sidebar,

            text="Test Database",

            fg_color="green",

            command=self.test_db

        ).pack(
            side="bottom",
            padx=12,
            pady=20,
            fill="x"
        )


        self.show("dash")

        self.refresh_all()


    # -----------------------------------------------------
    # COMMON GUI METHODS
    # -----------------------------------------------------

    def page(self, key, title):

        frame = ctk.CTkFrame(self.main)

        self.pages[key] = frame

        ctk.CTkLabel(

            frame,

            text=title,

            font=("Arial", 25, "bold")

        ).pack(
            anchor="w",
            padx=12,
            pady=12
        )

        return frame


    def show(self, key):

        for frame in self.pages.values():

            frame.pack_forget()

        self.pages[key].pack(
            fill="both",
            expand=True
        )


    def field(
        self,
        parent,
        hint,
        width=170
    ):

        entry = ctk.CTkEntry(

            parent,

            placeholder_text=hint,

            width=width

        )

        entry.pack(
            side="left",
            padx=4,
            pady=8
        )

        return entry


    def table(
        self,
        parent,
        columns,
        headings
    ):

        box = ctk.CTkFrame(parent)

        box.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

        tree = ttk.Treeview(

            box,

            columns=columns,

            show="headings"

        )


        for column, heading in zip(
            columns,
            headings
        ):

            tree.heading(
                column,
                text=heading
            )

            tree.column(
                column,
                width=130,
                anchor="center"
            )


        scrollbar = ttk.Scrollbar(

            box,

            orient="vertical",

            command=tree.yview

        )

        tree.configure(
            yscrollcommand=scrollbar.set
        )


        tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        return tree


    def fill(
        self,
        tree,
        rows
    ):

        tree.delete(
            *tree.get_children()
        )

        for row in rows:

            tree.insert(

                "",

                "end",

                values=tuple(
                    "" if value is None else str(value)
                    for value in row
                )

            )


    def run(self, function):

        try:

            return function()

        except Exception as error:

            messagebox.showerror(
                "Error",
                str(error)
            )

            return None


    # -----------------------------------------------------
    # DASHBOARD
    # -----------------------------------------------------

    def build_dashboard(self):

        page = self.page(
            "dash",
            "Dashboard"
        )

        self.stats = {}

        row = ctk.CTkFrame(page)

        row.pack(
            fill="x",
            padx=8,
            pady=8
        )


        cards = [

            ("c", "Customers"),

            ("a", "Accounts"),

            ("t", "Today's transactions"),

            ("f", "Pending fraud alerts"),

            ("b", "Total balance")

        ]


        for key, title in cards:

            card = ctk.CTkFrame(row)

            card.pack(
                side="left",
                expand=True,
                fill="x",
                padx=4,
                pady=4
            )


            ctk.CTkLabel(
                card,
                text=title
            ).pack(pady=8)


            self.stats[key] = ctk.CTkLabel(

                card,

                text="—",

                font=("Arial", 22, "bold")

            )

            self.stats[key].pack(pady=8)


        ctk.CTkButton(

            page,

            text="Refresh",

            command=self.refresh_dash

        ).pack(
            anchor="e",
            padx=10
        )


    # -----------------------------------------------------
    # CUSTOMERS PAGE
    # -----------------------------------------------------

    def build_customers(self):

        page = self.page(
            "customers",
            "Customer Management"
        )

        row = ctk.CTkFrame(page)

        row.pack(
            fill="x",
            padx=8
        )


        self.cf = [

            self.field(row, "First name", 130),

            self.field(row, "Last name", 130),

            self.field(row, "11-digit National ID", 160),

            self.field(row, "Phone", 130),

            self.field(row, "Email", 180),

            self.field(row, "Address", 200)

        ]


        ctk.CTkButton(

            page,

            text="Add Customer",

            command=self.add_customer

        ).pack(
            anchor="e",
            padx=10
        )


        self.ct = self.table(

            page,

            (
                "id",
                "first",
                "last",
                "nid",
                "phone",
                "email",
                "active"
            ),

            (
                "ID",
                "First",
                "Last",
                "National ID",
                "Phone",
                "Email",
                "Active"
            )

        )


    # -----------------------------------------------------
    # ACCOUNTS PAGE
    # -----------------------------------------------------

    def build_accounts(self):

        page = self.page(
            "accounts",
            "Account Management"
        )

        row = ctk.CTkFrame(page)

        row.pack(
            fill="x",
            padx=8
        )


        self.customer_combo = ctk.CTkComboBox(

            row,

            values=["No customers"],

            width=260

        )

        self.customer_combo.pack(
            side="left",
            padx=5,
            pady=8
        )


        self.account_type = ctk.CTkComboBox(

            row,

            values=["Checking", "Savings"],

            width=150

        )

        self.account_type.pack(
            side="left",
            padx=5
        )


        self.opening = self.field(

            row,

            "Opening balance (optional)",

            200

        )


        ctk.CTkButton(

            page,

            text="Create Account",

            command=self.add_account

        ).pack(
            anchor="e",
            padx=10
        )


        self.at = self.table(

            page,

            (
                "id",
                "number",
                "customer",
                "type",
                "balance",
                "currency",
                "active"
            ),

            (
                "ID",
                "Account number",
                "Customer",
                "Type",
                "Balance",
                "Currency",
                "Active"
            )

        )


    # -----------------------------------------------------
    # TRANSACTIONS PAGE
    # -----------------------------------------------------

    def build_transactions(self):

        page = self.page(
            "tx",
            "Transactions"
        )

        row = ctk.CTkFrame(page)

        row.pack(
            fill="x",
            padx=8
        )


        self.tx_type = ctk.CTkComboBox(

            row,

            values=[
                "Deposit",
                "Withdrawal",
                "Transfer"
            ],

            width=140

        )

        self.tx_type.pack(
            side="left",
            padx=4,
            pady=8
        )


        self.src = self.field(
            row,
            "Source account ID",
            150
        )

        self.dst = self.field(
            row,
            "Destination account ID",
            170
        )

        self.val = self.field(
            row,
            "Amount",
            130
        )

        self.desc = self.field(
            row,
            "Description",
            220
        )


        ctk.CTkButton(

            page,

            text="Execute Transaction",

            command=self.do_tx

        ).pack(
            anchor="e",
            padx=10
        )


        self.tt = self.table(

            page,

            (
                "id",
                "type",
                "from",
                "to",
                "amount",
                "desc",
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


    # -----------------------------------------------------
    # FRAUD DETECTION PAGE
    # -----------------------------------------------------

    def build_fraud(self):

        page = self.page(
            "fraud",
            "Fraud Detection & Alerts"
        )

        row = ctk.CTkFrame(page)

        row.pack(
            fill="x",
            padx=8
        )


        ctk.CTkButton(

            row,

            text="Run Fraud Detection",

            command=self.scan

        ).pack(
            side="left",
            padx=5,
            pady=8
        )


        self.alertid = self.field(
            row,
            "Alert ID",
            120
        )


        ctk.CTkButton(

            row,

            text="Mark Reviewed",

            command=lambda: self.review("Reviewed")

        ).pack(
            side="left",
            padx=5
        )


        ctk.CTkButton(

            row,

            text="False Positive",

            command=lambda: self.review("FalsePositive")

        ).pack(
            side="left",
            padx=5
        )


        self.ft = self.table(

            page,

            (
                "id",
                "tx",
                "rule",
                "desc",
                "risk",
                "status",
                "date"
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


    # -----------------------------------------------------
    # AUDIT LOG PAGE
    # -----------------------------------------------------

    def build_logs(self):

        page = self.page(
            "logs",
            "Audit Logs"
        )

        ctk.CTkButton(

            page,

            text="Refresh",

            command=self.refresh_logs

        ).pack(
            anchor="e",
            padx=10
        )


        self.lt = self.table(

            page,

            (
                "id",
                "action",
                "entity",
                "entityid",
                "desc",
                "date"
            ),

            (
                "ID",
                "Action",
                "Entity",
                "Entity ID",
                "Description",
                "Date"
            )

        )


    # -----------------------------------------------------
    # BUTTON FUNCTIONS
    # -----------------------------------------------------

    def test_db(self):

        name = self.run(
            self.db.test
        )

        if name:

            messagebox.showinfo(
                "Database",
                "Connected to " + name
            )


    def add_customer(self):

        def action():

            customer_id = self.db.add_customer(

                *[
                    field.get()
                    for field in self.cf
                ]

            )

            self.refresh_all()

            messagebox.showinfo(
                "Created",
                f"Customer ID: {customer_id}"
            )

        self.run(action)


    def add_account(self):

        def action():

            key = self.customer_combo.get()

            if key not in self.customer_map:

                raise ValueError(
                    "Select a customer first."
                )

            account_id = self.db.add_account(

                self.customer_map[key],

                self.account_type.get(),

                self.opening.get()

            )

            self.refresh_all()

            messagebox.showinfo(
                "Created",
                f"Account ID: {account_id}"
            )

        self.run(action)


    def do_tx(self):

        def action():

            transaction_type = self.tx_type.get()

            if not self.src.get().isdigit():

                raise ValueError(
                    "Enter source Account ID."
                )

            source = int(self.src.get())

            destination = (

                int(self.dst.get())

                if self.dst.get().isdigit()

                else None

            )

            if transaction_type == "Transfer" and destination is None:

                raise ValueError(
                    "Enter destination Account ID."
                )

            transaction_id = self.db.transact(

                transaction_type,

                source,

                destination,

                self.val.get(),

                self.desc.get() or transaction_type

            )

            self.refresh_all()

            messagebox.showinfo(

                "Completed",

                f"Transaction ID: {transaction_id}"

            )

        self.run(action)


    def scan(self):

        result = self.run(
            self.db.scan_fraud
        )

        if result is not None:

            self.refresh_all()

            messagebox.showinfo(

                "Fraud scan",

                f"{result} new alert(s) created."

            )


    def review(self, status):

        def action():

            if not self.alertid.get().isdigit():

                raise ValueError(
                    "Enter Alert ID."
                )

            self.db.review(

                int(self.alertid.get()),

                status

            )

            self.refresh_all()

        self.run(action)


    # -----------------------------------------------------
    # REFRESH FUNCTIONS
    # -----------------------------------------------------

    def refresh_dash(self):

        result = self.run(
            self.db.dashboard
        )

        if result:

            for key, value in zip(
                ("c", "a", "t", "f", "b"),
                result
            ):

                if key == "b":

                    text = f"{value:,.2f} TRY"

                else:

                    text = str(value)

                self.stats[key].configure(
                    text=text
                )


    def refresh_customers(self):

        result = self.run(
            self.db.customers
        )

        if result is not None:

            self.fill(
                self.ct,
                result
            )


        choices = self.run(
            self.db.customer_choices
        )

        if choices is not None:

            self.customer_map = {

                f"{row.CustomerID} - {row.FirstName} {row.LastName}":
                row.CustomerID

                for row in choices

            }

            values = (
                list(self.customer_map)
                or ["No customers"]
            )

            self.customer_combo.configure(
                values=values
            )

            self.customer_combo.set(
                values[0]
            )


    def refresh_accounts(self):

        result = self.run(
            self.db.accounts
        )

        if result is not None:

            self.fill(
                self.at,
                result
            )


    def refresh_tx(self):

        result = self.run(
            self.db.transactions
        )

        if result is not None:

            self.fill(
                self.tt,
                result
            )


    def refresh_fraud(self):

        result = self.run(
            self.db.alerts
        )

        if result is not None:

            self.fill(
                self.ft,
                result
            )


    def refresh_logs(self):

        result = self.run(
            self.db.logs
        )

        if result is not None:

            self.fill(
                self.lt,
                result
            )


    def refresh_all(self):

        self.refresh_dash()

        self.refresh_customers()

        self.refresh_accounts()

        self.refresh_tx()

        self.refresh_fraud()

        self.refresh_logs()


# =========================================================
# APPLICATION START
# =========================================================

if __name__ == "__main__":

    ctk.set_appearance_mode("light")

    ctk.set_default_color_theme("blue")

    app = App()

    app.mainloop()
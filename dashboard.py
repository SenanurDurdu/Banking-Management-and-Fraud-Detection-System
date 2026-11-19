
from decimal import Decimal

from core import connect


class DashboardMixin:

    # ========================================================
    # DASHBOARD - ADMIN / CUSTOMER
    # ========================================================

    def dashboard(self):
        session = self.require_login()
        con = connect()

        try:
            cur = con.cursor()

            if session["role"] == "Admin":
                customers = cur.execute("""
                    SELECT COUNT(*)
                    FROM dbo.Customers
                    WHERE IsActive = 1
                """).fetchone()[0]

                accounts = cur.execute("""
                    SELECT COUNT(*)
                    FROM dbo.Accounts
                    WHERE IsActive = 1
                """).fetchone()[0]

                today = cur.execute("""
                    SELECT COUNT(*)
                    FROM dbo.Transactions
                    WHERE CAST(TransactionDate AS DATE)
                        = CAST(GETDATE() AS DATE)
                """).fetchone()[0]

                pending = cur.execute("""
                    SELECT COUNT(*)
                    FROM dbo.FraudAlerts
                    WHERE ReviewStatus = 'Pending'
                """).fetchone()[0]

                balance = cur.execute("""
                    SELECT COALESCE(SUM(Balance), 0)
                    FROM dbo.Accounts
                    WHERE IsActive = 1
                """).fetchone()[0]

                return [
                    ("Customers", customers),
                    ("Accounts", accounts),
                    ("Today's Transactions", today),
                    ("Pending Fraud Alerts", pending),
                    ("Total Balance", f"{balance:,.2f} TRY")
                ]

            cid = session["customer_id"]

            accounts = cur.execute("""
                SELECT COUNT(*)
                FROM dbo.Accounts
                WHERE CustomerID = ?
                  AND IsActive = 1
            """, cid).fetchone()[0]

            balance = cur.execute("""
                SELECT COALESCE(SUM(Balance), 0)
                FROM dbo.Accounts
                WHERE CustomerID = ?
                  AND IsActive = 1
            """, cid).fetchone()[0]

            transactions = cur.execute("""
                SELECT COUNT(*)
                FROM dbo.Transactions t
                LEFT JOIN dbo.Accounts f
                    ON f.AccountID = t.FromAccountID
                LEFT JOIN dbo.Accounts d
                    ON d.AccountID = t.ToAccountID
                WHERE f.CustomerID = ?
                   OR d.CustomerID = ?
            """, cid, cid).fetchone()[0]

            return [
                ("My Accounts", accounts),
                ("My Transactions", transactions),
                ("My Balance", f"{balance:,.2f} TRY")
            ]

        finally:
            con.close()

    # ========================================================
    # CUSTOMER MOBILE BANKING OVERVIEW
    # ========================================================

    def customer_banking_overview(self):
        session = self.require_login()

        if session["role"] != "Customer":
            raise PermissionError(
                "Customer access required."
            )

        customer_id = int(session["customer_id"])
        con = connect()

        try:
            cur = con.cursor()

            # CUSTOMER NAME
            cur.execute("""
                SELECT FirstName, LastName
                FROM dbo.Customers
                WHERE CustomerID = ?
            """, customer_id)

            customer = cur.fetchone()

            customer_name = (
                f"{customer[0]} {customer[1]}".strip()
                if customer
                else "Customer"
            )

            # BANK ACCOUNTS
            cur.execute("""
                SELECT
                    AccountID,
                    AccountNumber,
                    AccountType,
                    Balance,
                    Currency,
                    IsActive,
                    IsFrozen
                FROM dbo.Accounts
                WHERE CustomerID = ?
                  AND IsActive = 1
                ORDER BY AccountID DESC
            """, customer_id)

            accounts = []
            total_assets = Decimal("0")
            available_balance = Decimal("0")

            for row in cur.fetchall():
                balance = Decimal(str(row[3]))
                frozen = bool(row[6])

                total_assets += balance

                if not frozen:
                    available_balance += balance

                accounts.append({
                    "id": int(row[0]),
                    "number": str(row[1]),
                    "type": str(row[2]),
                    "balance": balance,
                    "currency": str(row[4]),
                    "active": bool(row[5]),
                    "frozen": frozen
                })

            # TOTAL MONEY IN / OUT
            # Exclude transfers between the customer's own
            # accounts and count only completed transactions.

            cur.execute("""
                SELECT
                    COALESCE(SUM(
                        CASE
                            WHEN d.CustomerID = ?
                             AND (
                                 f.CustomerID IS NULL
                                 OR f.CustomerID <> ?
                             )
                            THEN t.Amount
                            ELSE 0
                        END
                    ), 0) AS TotalIn,

                    COALESCE(SUM(
                        CASE
                            WHEN f.CustomerID = ?
                             AND (
                                 d.CustomerID IS NULL
                                 OR d.CustomerID <> ?
                             )
                            THEN t.Amount
                            ELSE 0
                        END
                    ), 0) AS TotalOut

                FROM dbo.Transactions t

                LEFT JOIN dbo.Accounts f
                    ON f.AccountID = t.FromAccountID

                LEFT JOIN dbo.Accounts d
                    ON d.AccountID = t.ToAccountID

                WHERE t.Status = 'Completed'
                  AND (
                      f.CustomerID = ?
                      OR d.CustomerID = ?
                  )
            """,
                customer_id,
                customer_id,
                customer_id,
                customer_id,
                customer_id,
                customer_id
            )

            money_row = cur.fetchone()

            total_in = Decimal(str(money_row[0]))
            total_out = Decimal(str(money_row[1]))

            # RECENT TRANSACTIONS
            cur.execute("""
                SELECT TOP (5)
                    t.TransactionID,
                    t.TransactionType,
                    t.Amount,
                    t.TransactionDate,
                    t.Status,
                    t.Description,
                    f.AccountNumber,
                    d.AccountNumber,

                    CASE
                        WHEN f.CustomerID = ?
                         AND d.CustomerID = ?
                        THEN 'Internal'

                        WHEN d.CustomerID = ?
                        THEN 'Incoming'

                        WHEN f.CustomerID = ?
                        THEN 'Outgoing'

                        ELSE 'Other'
                    END AS Direction

                FROM dbo.Transactions t

                LEFT JOIN dbo.Accounts f
                    ON f.AccountID = t.FromAccountID

                LEFT JOIN dbo.Accounts d
                    ON d.AccountID = t.ToAccountID

                WHERE f.CustomerID = ?
                   OR d.CustomerID = ?

                ORDER BY
                    t.TransactionDate DESC,
                    t.TransactionID DESC
            """,
                customer_id,
                customer_id,
                customer_id,
                customer_id,
                customer_id,
                customer_id
            )

            recent_transactions = []

            for row in cur.fetchall():
                recent_transactions.append({
                    "id": int(row[0]),
                    "type": str(row[1]),
                    "amount": Decimal(str(row[2])),
                    "date": row[3],
                    "status": str(row[4]),
                    "description": str(row[5] or ""),
                    "from_account": str(row[6] or ""),
                    "to_account": str(row[7] or ""),
                    "direction": str(row[8])
                })

            # CREDIT CARDS
            cur.execute("""
                SELECT
                    CreditCardID,
                    CardType,
                    CardNumber,
                    CreditLimit,
                    OutstandingBalance,
                    Currency,
                    CardStatus,
                    ExpiresAt
                FROM dbo.CreditCards
                WHERE CustomerID = ?
                ORDER BY CreditCardID DESC
            """, customer_id)

            credit_cards = []
            total_credit_limit = Decimal("0")
            available_credit_limit = Decimal("0")
            active_card_count = 0

            for row in cur.fetchall():
                credit_limit = Decimal(str(row[3]))
                outstanding = Decimal(str(row[4]))
                status = str(row[6])

                available = max(
                    credit_limit - outstanding,
                    Decimal("0")
                )

                if status == "Active":
                    active_card_count += 1
                    total_credit_limit += credit_limit
                    available_credit_limit += available

                credit_cards.append({
                    "id": int(row[0]),
                    "type": str(row[1]),
                    "last_four": str(row[2])[-4:],
                    "limit": credit_limit,
                    "outstanding": outstanding,
                    "available": available,
                    "currency": str(row[5]),
                    "status": status,
                    "expires_at": row[7]
                })

            # PENDING CREDIT CARD APPLICATIONS
            cur.execute("""
                SELECT COUNT(*)
                FROM dbo.CreditCardApplications
                WHERE CustomerID = ?
                  AND ApplicationStatus = 'Pending'
            """, customer_id)

            pending_applications = int(
                cur.fetchone()[0]
            )

            return {
                "customer_name": customer_name,
                "total_assets": total_assets,
                "available_balance": available_balance,
                "total_in": total_in,
                "total_out": total_out,
                "account_count": len(accounts),
                "accounts": accounts,
                "credit_card_count": len(credit_cards),
                "active_credit_card_count": active_card_count,
                "credit_cards": credit_cards,
                "total_credit_limit": total_credit_limit,
                "available_credit_limit": available_credit_limit,
                "pending_applications": pending_applications,
                "recent_transactions": recent_transactions
            }

        finally:
            con.close()

    # ========================================================
    # ADMIN - ADVANCED AUDIT LOGS
    # ========================================================

    def logs(
        self,
        category="All Categories",
        action="All Actions",
        date_range="All Time",
        user_id="",
        keyword="",
        sort="Newest First",
        page=1,
        page_size=25
    ):
        self.require_admin()

        page = int(page)
        page_size = int(page_size)

        if page < 1:
            raise ValueError("Page must be positive.")

        if page_size not in (25, 50, 100):
            raise ValueError("Invalid page size.")

        if date_range not in (
            "All Time",
            "Today",
            "Last 7 Days",
            "Last 30 Days"
        ):
            raise ValueError("Invalid date range.")

        if sort not in (
            "Newest First",
            "Oldest First"
        ):
            raise ValueError("Invalid sort order.")

        category_entities = {
            "Transactions": (
                "Transaction",
                "Transactions"
            ),
            "Accounts": (
                "Account",
                "Accounts"
            ),
            "Credit Cards": (
                "CreditCard",
                "CreditCards",
                "CreditCardApplication",
                "CreditCardApplications"
            ),
            "Security": (
                "FraudAlert",
                "FraudAlerts",
                "FraudRule",
                "FraudRules"
            ),
            "Customers": (
                "Customer",
                "Customers"
            ),
            "Authentication": (
                "User",
                "Users"
            )
        }

        if (
            category != "All Categories"
            and category not in category_entities
        ):
            raise ValueError("Invalid category.")

        conditions = []
        params = []

        # CATEGORY
        if category != "All Categories":
            entities = category_entities[category]
            placeholders = ", ".join(
                "?" for _ in entities
            )

            conditions.append(
                f"EntityName IN ({placeholders})"
            )
            params.extend(entities)

        # ACTION
        if action != "All Actions":
            conditions.append("ActionType = ?")
            params.append(action)

        # USER
        if str(user_id).strip():
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                raise ValueError(
                    "User ID must be a number."
                )

            if user_id <= 0:
                raise ValueError(
                    "User ID must be positive."
                )

            conditions.append("UserID = ?")
            params.append(user_id)

        # KEYWORD
        keyword = str(keyword or "").strip()

        if keyword:
            if len(keyword) > 200:
                raise ValueError(
                    "Search text is too long."
                )

            conditions.append("""
                (
                    Description LIKE ?
                    OR ActionType LIKE ?
                    OR EntityName LIKE ?
                    OR CONVERT(
                        VARCHAR(30), EntityID
                    ) LIKE ?
                )
            """)

            escaped = (
                keyword
                .replace("[", "[[]")
                .replace("%", "[%]")
                .replace("_", "[_]")
            )

            pattern = f"%{escaped}%"
            params.extend([pattern] * 4)

        # DATE
        if date_range == "Today":
            conditions.append("""
                CreatedAt >= CAST(GETDATE() AS DATE)
            """)
            conditions.append("""
                CreatedAt < DATEADD(
                    DAY, 1, CAST(GETDATE() AS DATE)
                )
            """)

        elif date_range == "Last 7 Days":
            conditions.append("""
                CreatedAt >= DATEADD(DAY, -7, GETDATE())
            """)

        elif date_range == "Last 30 Days":
            conditions.append("""
                CreatedAt >= DATEADD(DAY, -30, GETDATE())
            """)

        where_clause = (
            "WHERE " + " AND ".join(conditions)
            if conditions
            else ""
        )

        order = (
            "DESC"
            if sort == "Newest First"
            else "ASC"
        )

        offset = (page - 1) * page_size

        con = connect()

        try:
            cur = con.cursor()

            # COUNT
            count_sql = f"""
                SELECT COUNT(*)
                FROM BankingFraudDB.dbo.AuditLogs
                {where_clause}
            """

            cur.execute(count_sql, *params)
            total = int(cur.fetchone()[0])

            # PAGINATED RESULTS
            data_sql = f"""
                SELECT
                    AuditID,
                    ActionType,
                    EntityName,
                    EntityID,
                    Description,
                    CreatedAt
                FROM BankingFraudDB.dbo.AuditLogs
                {where_clause}
                ORDER BY AuditID {order}
                OFFSET ? ROWS
                FETCH NEXT ? ROWS ONLY
            """

            cur.execute(
                data_sql,
                *(params + [offset, page_size])
            )

            rows = cur.fetchall()

            return {
                "rows": rows,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": max(
                    1,
                    (total + page_size - 1) // page_size
                )
            }

        finally:
            con.close()

    # ========================================================
    # ADMIN - AUDIT LOG ACTION TYPES
    # ========================================================

    def audit_log_actions(self):
        self.require_admin()

        con = connect()

        try:
            cur = con.cursor()

            cur.execute("""
                SELECT DISTINCT
                    a.ActionType
                FROM BankingFraudDB.dbo.AuditLogs AS a
                WHERE a.ActionType IS NOT NULL
                ORDER BY a.ActionType
            """)

            return [
                str(row[0])
                for row in cur.fetchall()
            ]

        finally:
            con.close()

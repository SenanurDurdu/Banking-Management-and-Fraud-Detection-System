
from core import *


class DashboardMixin:
    def dashboard(self):
        session = self.require_login()
        con = connect()

        try:
            cur = con.cursor()

            if session["role"] == "Admin":
                customers = cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM Customers
                    WHERE IsActive = 1
                    """
                ).fetchone()[0]

                accounts = cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM Accounts
                    WHERE IsActive = 1
                    """
                ).fetchone()[0]

                today = cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM Transactions
                    WHERE CAST(TransactionDate AS DATE)
                        = CAST(GETDATE() AS DATE)
                    """
                ).fetchone()[0]

                pending = cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM FraudAlerts
                    WHERE ReviewStatus = 'Pending'
                    """
                ).fetchone()[0]

                balance = cur.execute(
                    """
                    SELECT COALESCE(SUM(Balance), 0)
                    FROM Accounts
                    WHERE IsActive = 1
                    """
                ).fetchone()[0]

                return [
                    ("Customers", customers),
                    ("Accounts", accounts),
                    ("Today's Transactions", today),
                    ("Pending Fraud Alerts", pending),
                    ("Total Balance", f"{balance:,.2f} TRY")
                ]

            cid = session["customer_id"]

            accounts = cur.execute(
                """
                SELECT COUNT(*)
                FROM Accounts
                WHERE CustomerID = ?
                  AND IsActive = 1
                """,
                cid
            ).fetchone()[0]

            balance = cur.execute(
                """
                SELECT COALESCE(SUM(Balance), 0)
                FROM Accounts
                WHERE CustomerID = ?
                  AND IsActive = 1
                """,
                cid
            ).fetchone()[0]

            transactions = cur.execute(
                """
                SELECT COUNT(*)
                FROM Transactions t
                LEFT JOIN Accounts f
                    ON f.AccountID = t.FromAccountID
                LEFT JOIN Accounts d
                    ON d.AccountID = t.ToAccountID
                WHERE f.CustomerID = ?
                   OR d.CustomerID = ?
                """,
                cid,
                cid
            ).fetchone()[0]

            return [
                ("My Accounts", accounts),
                ("My Transactions", transactions),
                ("My Balance", f"{balance:,.2f} TRY")
            ]

        finally:
            con.close()

    def logs(self):
        self.require_admin()
        con = connect()

        try:
            return con.cursor().execute(
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

        finally:
            con.close()

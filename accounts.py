
from core import *


class AccountsMixin:
    def accounts(self):
        session = self.require_login()
        con = connect()

        try:
            cur = con.cursor()

            if session["role"] == "Admin":
                return cur.execute(
                    """
                    SELECT
                        a.AccountID,
                        a.AccountNumber,
                        c.FirstName + ' ' + c.LastName,
                        a.AccountType,
                        a.Balance,
                        a.Currency,
                        a.IsActive
                    FROM Accounts a
                    JOIN Customers c
                        ON c.CustomerID = a.CustomerID
                    ORDER BY a.AccountID DESC
                    """
                ).fetchall()

            return cur.execute(
                """
                SELECT
                    AccountID,
                    AccountNumber,
                    AccountType,
                    Balance,
                    Currency,
                    IsActive
                FROM Accounts
                WHERE CustomerID = ?
                ORDER BY AccountID DESC
                """,
                session["customer_id"]
            ).fetchall()

        finally:
            con.close()

    def add_account(
        self,
        customer_id,
        account_type,
        opening_balance
    ):
        session = self.require_login()
        customer_id = int(customer_id)

        if account_type not in ("Checking", "Savings"):
            raise ValueError(
                "Invalid account type."
            )

        balance = money(
            opening_balance
            if str(opening_balance).strip()
            else "0",
            allow_zero=True
        )

        if session["role"] == "Customer":
            if customer_id != session["customer_id"]:
                raise PermissionError(
                    "You can only create your own account."
                )

            if balance != 0:
                raise PermissionError(
                    "Customer opening balance must be zero."
                )

        account_number = "TR" + "".join(
            secrets.choice(string.digits)
            for _ in range(16)
        )

        con = connect()

        try:
            cur = con.cursor()

            customer = cur.execute(
                """
                SELECT CustomerID
                FROM Customers
                WHERE CustomerID = ?
                  AND IsActive = 1
                """,
                customer_id
            ).fetchone()

            if not customer:
                raise ValueError(
                    "Customer not found or inactive."
                )

            cur.execute(
                """
                INSERT INTO Accounts
                    (
                        CustomerID,
                        AccountNumber,
                        AccountType,
                        Balance
                    )
                OUTPUT INSERTED.AccountID
                VALUES (?, ?, ?, ?)
                """,
                customer_id,
                account_number,
                account_type,
                balance
            )

            account_id = int(cur.fetchone()[0])

            audit(
                cur,
                "CREATE",
                "Account",
                account_id,
                "Bank account created"
            )

            con.commit()
            return account_id

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

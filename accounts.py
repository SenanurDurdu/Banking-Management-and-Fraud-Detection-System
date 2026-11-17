
from core import *


class AccountsMixin:

    MAX_ACTIVE_ACCOUNTS = 3

    # ========================================================
    # ACCOUNTS - ADMIN / CUSTOMER
    # ========================================================

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

    # ========================================================
    # CREATE ACCOUNT - CUSTOMER
    # ========================================================

    def add_account(
        self,
        customer_id,
        account_type=None,
        opening_balance="0"
    ):
        session = self.require_login()

        if session["role"] != "Customer":
            raise PermissionError(
                "Only customers can create bank accounts."
            )

        try:
            customer_id = int(customer_id)

            if customer_id <= 0:
                raise ValueError()

        except (ValueError, TypeError):
            raise ValueError(
                "Invalid Customer ID."
            )

        if customer_id != int(session["customer_id"]):
            raise PermissionError(
                "You can only create your own account."
            )

        balance = money(
            opening_balance
            if str(opening_balance).strip()
            else "0",
            allow_zero=True
        )

        if balance != 0:
            raise ValueError(
                "New accounts must start with 0 TRY."
            )

        con = connect()

        try:
            cur = con.cursor()

            customer = cur.execute(
                """
                SELECT CustomerID
                FROM Customers WITH (UPDLOCK, HOLDLOCK)
                WHERE CustomerID = ?
                  AND IsActive = 1
                """,
                customer_id
            ).fetchone()

            if not customer:
                raise ValueError(
                    "Customer not found or inactive."
                )

            count_row = cur.execute(
                """
                SELECT COUNT(*)
                FROM Accounts
                WHERE CustomerID = ?
                  AND IsActive = 1
                """,
                customer_id
            ).fetchone()

            active_count = int(count_row[0])

            if active_count >= self.MAX_ACTIVE_ACCOUNTS:
                raise ValueError(
                    "A customer can have at most "
                    "3 active bank accounts."
                )

            account_number = None

            for _ in range(10):
                candidate = "TR" + "".join(
                    secrets.choice(string.digits)
                    for _ in range(16)
                )

                exists = cur.execute(
                    """
                    SELECT AccountID
                    FROM Accounts
                    WHERE AccountNumber = ?
                    """,
                    candidate
                ).fetchone()

                if not exists:
                    account_number = candidate
                    break

            if account_number is None:
                raise RuntimeError(
                    "Could not generate an account number."
                )

            # Compatible with the existing SQL schema.
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
                "Checking",
                balance
            )

            account_id = int(cur.fetchone()[0])

            audit(
                cur,
                "CREATE",
                "Account",
                account_id,
                "Customer created a bank account."
            )

            con.commit()
            return account_id

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

    # ========================================================
    # CLOSE ACCOUNT - CUSTOMER ONLY
    # ========================================================

    def delete_account(self, account_id):
        session = self.require_login()

        # Only customers can close their own accounts.
        if session["role"] != "Customer":
            raise PermissionError(
                "Only customers can close their own bank accounts."
            )

        customer_id = session["customer_id"]

        if customer_id is None:
            raise PermissionError(
                "Customer account not found."
            )

        customer_id = int(customer_id)

        try:
            account_id = int(account_id)

            if account_id <= 0:
                raise ValueError()

        except (ValueError, TypeError):
            raise ValueError(
                "Invalid Account ID."
            )

        con = connect()

        try:
            cur = con.cursor()

            # Lock the account while checking ownership and balance.
            account = cur.execute(
                """
                SELECT
                    AccountID,
                    CustomerID,
                    Balance,
                    IsActive
                FROM dbo.Accounts WITH (UPDLOCK, HOLDLOCK)
                WHERE AccountID = ?
                  AND CustomerID = ?
                """,
                account_id,
                customer_id
            ).fetchone()

            if not account:
                raise ValueError(
                    "Bank account not found or does not belong to you."
                )

            if not bool(account.IsActive):
                raise ValueError(
                    "This account is already inactive."
                )

            if account.Balance != 0:
                raise ValueError(
                    "Only accounts with 0 TRY balance can be closed."
                )

            # Soft delete: preserve transactions and fraud history.
            cur.execute(
                """
                UPDATE dbo.Accounts
                SET IsActive = 0
                WHERE AccountID = ?
                  AND CustomerID = ?
                  AND IsActive = 1
                  AND Balance = 0
                """,
                account_id,
                customer_id
            )

            if cur.rowcount != 1:
                raise ValueError(
                    "Account could not be closed."
                )

            audit(
                cur,
                "DELETE",
                "Account",
                account_id,
                "Customer closed their own zero-balance bank account."
            )

            con.commit()
            return True

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()


from core import *


class AccountsMixin:

    MAX_ACTIVE_ACCOUNTS = 3

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

            # Temporary compatibility with existing SQL schema.
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

    def delete_account(self, account_id):
        session = self.require_login()

        if session["role"] != "Admin":
            raise PermissionError(
                "Only admins can delete bank accounts."
            )

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

            # Lock the account while checking its balance.
            account = cur.execute(
                """
                SELECT
                    AccountID,
                    CustomerID,
                    Balance,
                    IsActive
                FROM Accounts WITH (UPDLOCK, HOLDLOCK)
                WHERE AccountID = ?
                """,
                account_id
            ).fetchone()

            if not account:
                raise ValueError(
                    "Bank account not found."
                )

            if not bool(account.IsActive):
                raise ValueError(
                    "This account is already inactive."
                )

            if account.Balance != 0:
                raise ValueError(
                    "Only accounts with 0 TRY balance "
                    "can be deleted."
                )

            # Soft delete: keep transactions and history.
            cur.execute(
                """
                UPDATE Accounts
                SET IsActive = 0
                WHERE AccountID = ?
                  AND IsActive = 1
                  AND Balance = 0
                """,
                account_id
            )

            if cur.rowcount != 1:
                raise ValueError(
                    "Account could not be deactivated."
                )

            audit(
                cur,
                "DELETE",
                "Account",
                account_id,
                (
                    "Admin deactivated a zero-balance "
                    "bank account."
                )
            )

            con.commit()
            return True

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

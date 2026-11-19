
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
                        a.IsActive,
                        a.IsFrozen
                    FROM dbo.Accounts a
                    JOIN dbo.Customers c
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
                    IsActive,
                    IsFrozen
                FROM dbo.Accounts
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
                FROM dbo.Customers WITH (UPDLOCK, HOLDLOCK)
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
                FROM dbo.Accounts
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
                    FROM dbo.Accounts
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

            cur.execute(
                """
                INSERT INTO dbo.Accounts
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

            account = cur.execute(
                """
                SELECT
                    AccountID,
                    CustomerID,
                    Balance,
                    IsActive,
                    IsFrozen
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

            if bool(account.IsFrozen):
                raise ValueError(
                    "This account is frozen and cannot be closed. "
                    "Please contact the bank administrator."
                )

            if account.Balance != 0:
                raise ValueError(
                    "Only accounts with 0 TRY balance can be closed."
                )

            cur.execute(
                """
                UPDATE dbo.Accounts
                SET IsActive = 0
                WHERE AccountID = ?
                  AND CustomerID = ?
                  AND IsActive = 1
                  AND IsFrozen = 0
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

    # ========================================================
    # ADMIN - FREEZE ACCOUNT
    # ========================================================

    def freeze_account(self, account_id):
        session = self.require_login()

        if session["role"] != "Admin":
            raise PermissionError(
                "Only admins can freeze bank accounts."
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

            account = cur.execute(
                """
                SELECT
                    AccountID,
                    IsActive,
                    IsFrozen
                FROM dbo.Accounts WITH (UPDLOCK, HOLDLOCK)
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
                    "Inactive accounts cannot be frozen."
                )

            if bool(account.IsFrozen):
                raise ValueError(
                    "This account is already frozen."
                )

            cur.execute(
                """
                UPDATE dbo.Accounts
                SET IsFrozen = 1
                WHERE AccountID = ?
                  AND IsActive = 1
                  AND IsFrozen = 0
                """,
                account_id
            )

            if cur.rowcount != 1:
                raise ValueError(
                    "Account could not be frozen."
                )

            audit(
                cur,
                "FREEZE",
                "Account",
                account_id,
                "Administrator froze the bank account."
            )

            con.commit()
            return True

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

    # ========================================================
    # ADMIN ONLY - UNFREEZE ACCOUNT
    # ========================================================


def unfreeze_account(self, account_id):
    session = self.require_login()

    # Validate session authorization.

    if session.get("role") != "Admin":
        raise PermissionError(
            "Only bank administrators can unfreeze accounts."
        )

    # Validate administrator UserID.

    try:
        admin_user_id = int(session.get("user_id"))

        if admin_user_id <= 0:
            raise ValueError()

    except (ValueError, TypeError, OverflowError):
        raise PermissionError(
            "Invalid administrator session."
        )

    # Validate bank account ID.

    try:
        account_id = int(account_id)

        if account_id <= 0:
            raise ValueError()

    except (ValueError, TypeError, OverflowError):
        raise ValueError(
            "Invalid Account ID."
        )

    con = connect()

    try:
        con.autocommit = False

        cur = con.cursor()

        cur.execute("""
               SET XACT_ABORT ON;
           """)

        # Verify administrator directly in the database.

        admin = cur.execute(
            """
            SELECT UserID
            FROM dbo.Users WITH (UPDLOCK, HOLDLOCK)
            WHERE UserID = ?
              AND Role = 'Admin'
              AND IsActive = 1
            """,
            admin_user_id
        ).fetchone()

        if admin is None:
            raise PermissionError(
                "Active administrator access is required."
            )

        # Lock and validate the selected account.

        account = cur.execute(
            """
            SELECT
                AccountID,
                CustomerID,
                IsActive,
                IsFrozen
            FROM dbo.Accounts WITH (UPDLOCK, HOLDLOCK)
            WHERE AccountID = ?
            """,
            account_id
        ).fetchone()

        if account is None:
            raise ValueError(
                "Bank account not found."
            )

        if not bool(account.IsActive):
            raise ValueError(
                "Inactive accounts cannot be unfrozen."
            )

        if not bool(account.IsFrozen):
            raise ValueError(
                "This account is not frozen."
            )

        customer_id = int(account.CustomerID)

        # Unfreeze the account only when admin access
        # remains valid.

        cur.execute(
            """
            UPDATE dbo.Accounts
            SET IsFrozen = 0
            WHERE AccountID = ?
              AND IsActive = 1
              AND IsFrozen = 1
              AND EXISTS
              (
                  SELECT 1
                  FROM dbo.Users
                  WHERE UserID = ?
                    AND Role = 'Admin'
                    AND IsActive = 1
              )
            """,
            account_id,
            admin_user_id
        )

        if cur.rowcount != 1:
            raise RuntimeError(
                "Account could not be unfrozen."
            )

        # Record administrator action.

        cur.execute(
            """
            INSERT INTO dbo.AuditLogs
            (
                ActionType,
                EntityName,
                EntityID,
                Description,
                UserID
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            "UNFREEZE",
            "Account",
            account_id,
            "Administrator unfroze the bank account.",
            admin_user_id
        )

        # Notify the account owner.

        cur.execute(
            """
            INSERT INTO dbo.Notifications
            (
                CustomerID,
                Title,
                Message,
                NotificationType,
                IsRead
            )
            VALUES (?, ?, ?, ?, 0)
            """,
            customer_id,
            "Bank Account Unfrozen",
            (
                "Your bank account has been unfrozen "
                "by a bank administrator. "
                "You can resume eligible banking operations."
            ),
            "Security"
        )

        con.commit()

        return True

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()
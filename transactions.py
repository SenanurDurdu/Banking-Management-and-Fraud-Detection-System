
from core import *


class TransactionsMixin:

    def transact(
        self,
        kind,
        source,
        destination,
        value,
        description=""
    ):
        session = self.require_login()

        if kind not in (
            "Deposit",
            "Withdrawal",
            "Transfer"
        ):
            raise ValueError(
                "Invalid transaction type."
            )

        try:
            source = int(source)
            if source <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError(
                "Valid source account is required."
            )

        amount = money(value)

        description = (
            "" if description is None
            else str(description).strip()
        )

        if len(description) > 250:
            raise ValueError(
                "Description cannot exceed 250 characters."
            )

        destination_number = None

        if kind == "Transfer":
            destination_number = str(
                destination or ""
            ).strip().upper()

            if (
                len(destination_number) != 18
                or not destination_number.startswith("TR")
                or not destination_number[2:].isdigit()
            ):
                raise ValueError(
                    "Enter a valid 18-character "
                    "recipient account number."
                )

        con = connect()

        try:
            cur = con.cursor()

            destination_id = None

            if kind == "Transfer":
                # Resolve the recipient's public account
                # number to the internal AccountID.
                #
                # The lock is retained until commit,
                # so the account cannot be changed
                # concurrently during this transaction.
                recipient = cur.execute(
                    """
                    SELECT AccountID
                    FROM Accounts WITH (UPDLOCK, HOLDLOCK)
                    WHERE AccountNumber = ?
                    """,
                    destination_number
                ).fetchone()

                if not recipient:
                    raise ValueError(
                        "Recipient account not found."
                    )

                destination_id = int(
                    recipient.AccountID
                )

                if source == destination_id:
                    raise ValueError(
                        "You cannot transfer money "
                        "to the same account."
                    )

            # Acquire account locks.
            # Accounts are locked for the transaction.
            locked = {}

            ids = sorted(
                {source, destination_id} - {None}
            )

            for account_id in ids:
                row = cur.execute(
                    """
                    SELECT
                        AccountID,
                        CustomerID,
                        Balance,
                        Currency,
                        IsActive
                    FROM Accounts WITH (UPDLOCK, HOLDLOCK)
                    WHERE AccountID = ?
                    """,
                    account_id
                ).fetchone()

                if not row or not row.IsActive:
                    raise ValueError(
                        f"Account {account_id} "
                        "is unavailable."
                    )

                locked[account_id] = row

            src = locked[source]

            # Customers may only initiate transactions
            # from their own bank accounts.
            if session["role"] == "Customer":
                if (
                    int(src.CustomerID)
                    != int(session["customer_id"])
                ):
                    raise PermissionError(
                        "You can only use your own account."
                    )

            if kind == "Deposit":
                cur.execute(
                    """
                    UPDATE Accounts
                    SET Balance = Balance + ?
                    WHERE AccountID = ?
                    """,
                    amount,
                    source
                )

                from_id = None
                to_id = source

            elif kind == "Withdrawal":
                if src.Balance < amount:
                    raise ValueError(
                        "Insufficient balance."
                    )

                cur.execute(
                    """
                    UPDATE Accounts
                    SET Balance = Balance - ?
                    WHERE AccountID = ?
                    """,
                    amount,
                    source
                )

                from_id = source
                to_id = None

            else:
                dst = locked[destination_id]

                if src.Currency != dst.Currency:
                    raise ValueError(
                        "Transfers between different "
                        "currencies are not supported."
                    )

                if src.Balance < amount:
                    raise ValueError(
                        "Insufficient balance."
                    )

                cur.execute(
                    """
                    UPDATE Accounts
                    SET Balance = Balance - ?
                    WHERE AccountID = ?
                    """,
                    amount,
                    source
                )

                cur.execute(
                    """
                    UPDATE Accounts
                    SET Balance = Balance + ?
                    WHERE AccountID = ?
                    """,
                    amount,
                    destination_id
                )

                from_id = source
                to_id = destination_id

            cur.execute(
                """
                INSERT INTO Transactions
                (
                    FromAccountID,
                    ToAccountID,
                    TransactionType,
                    Amount,
                    Description
                )
                OUTPUT INSERTED.TransactionID
                VALUES (?, ?, ?, ?, ?)
                """,
                from_id,
                to_id,
                kind,
                amount,
                description
            )

            transaction_id = int(
                cur.fetchone()[0]
            )

            audit(
                cur,
                kind.upper(),
                "Transaction",
                transaction_id,
                f"{kind}: {amount}"
            )

            con.commit()
            return transaction_id

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

    def transactions(self):
        session = self.require_login()
        con = connect()

        try:
            cur = con.cursor()

            base = """
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
            """

            if session["role"] == "Admin":
                return cur.execute(
                    base + """
                    ORDER BY t.TransactionID DESC
                    """
                ).fetchall()

            return cur.execute(
                base + """
                WHERE
                    f.CustomerID = ?
                    OR d.CustomerID = ?
                ORDER BY t.TransactionID DESC
                """,
                session["customer_id"],
                session["customer_id"]
            ).fetchall()

        finally:
            con.close()

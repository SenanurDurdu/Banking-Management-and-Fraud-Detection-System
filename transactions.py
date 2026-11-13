
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

        if (
            session["role"] == "Customer"
            and kind == "Deposit"
        ):
            raise PermissionError(
                "Deposits require Admin verification."
            )

        try:
            source = int(source)
        except (ValueError, TypeError):
            raise ValueError(
                "Valid source Account ID is required."
            )

        amount = money(value)

        if kind == "Transfer":
            try:
                destination = int(destination)
            except (ValueError, TypeError):
                raise ValueError(
                    "Valid destination Account ID is required."
                )

            if source == destination:
                raise ValueError(
                    "Source and destination accounts must differ."
                )
        else:
            destination = None

        con = connect()

        try:
            cur = con.cursor()

            ids = sorted(
                {source, destination} - {None}
            )

            locked = {}

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
                        f"Account {account_id} is unavailable."
                    )

                locked[account_id] = row

            src = locked[source]

            if (
                session["role"] == "Customer"
                and src.CustomerID != session["customer_id"]
            ):
                raise PermissionError(
                    "You cannot use another customer's source account."
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

                from_id, to_id = None, source

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

                from_id, to_id = source, None

            else:
                dst = locked[destination]

                if src.Currency != dst.Currency:
                    raise ValueError(
                        "Transfers between different currencies "
                        "are not supported."
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
                    destination
                )

                from_id, to_id = source, destination

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
                description.strip()
            )

            transaction_id = int(cur.fetchone()[0])

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
                    base + " ORDER BY t.TransactionID DESC"
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


from core import *


class TransactionsMixin:

    # ========================================================
    # EXECUTE BANK TRANSACTION
    # ========================================================

    def transact(
        self,
        kind,
        source,
        destination,
        value,
        description=""
    ):
        session = self.require_login()

        # ----------------------------------------------------
        # VALIDATE TRANSACTION TYPE
        # ----------------------------------------------------

        if kind not in (
            "Deposit",
            "Withdrawal",
            "Transfer"
        ):
            raise ValueError(
                "Invalid transaction type."
            )

        # ----------------------------------------------------
        # VALIDATE SOURCE ACCOUNT
        # ----------------------------------------------------

        try:
            source = int(source)

            if source <= 0:
                raise ValueError()

        except (ValueError, TypeError):
            raise ValueError(
                "Valid source account is required."
            )

        # ----------------------------------------------------
        # VALIDATE AMOUNT
        # ----------------------------------------------------

        amount = money(value)

        # ----------------------------------------------------
        # VALIDATE DESCRIPTION
        # ----------------------------------------------------

        description = (
            ""
            if description is None
            else str(description).strip()
        )

        if len(description) > 250:
            raise ValueError(
                "Description cannot exceed 250 characters."
            )

        # ----------------------------------------------------
        # VALIDATE DESTINATION ACCOUNT
        # ----------------------------------------------------

        destination_number = None

        if kind == "Transfer":

            destination_number = str(
                destination or ""
            ).strip().upper()

            if (
                len(destination_number) != 18
                or not destination_number.startswith("TR")
                or not destination_number[2:].isascii()
                or not destination_number[2:].isdigit()
            ):
                raise ValueError(
                    "Enter a valid 18-character "
                    "recipient account number."
                )

        # ----------------------------------------------------
        # DEPOSIT PERMISSION
        # ----------------------------------------------------

        # Customers can deposit into their own accounts.
        # SQL Server checks account ownership and status.
        # No Admin-only restriction is applied here.

        # ----------------------------------------------------
        # CALL SQL SERVER STORED PROCEDURE
        # ----------------------------------------------------

        con = connect()

        try:
            cur = con.cursor()

            if kind == "Deposit":

                cur.execute(
                    """
                    EXEC dbo.sp_Deposit
                        @UserID = ?,
                        @SourceAccountID = ?,
                        @Amount = ?,
                        @Description = ?
                    """,
                    session["user_id"],
                    source,
                    amount,
                    description
                )

            elif kind == "Withdrawal":

                cur.execute(
                    """
                    EXEC dbo.sp_Withdraw
                        @UserID = ?,
                        @SourceAccountID = ?,
                        @Amount = ?,
                        @Description = ?
                    """,
                    session["user_id"],
                    source,
                    amount,
                    description
                )

            else:

                cur.execute(
                    """
                    EXEC dbo.sp_Transfer
                        @UserID = ?,
                        @SourceAccountID = ?,
                        @DestinationAccountNumber = ?,
                        @Amount = ?,
                        @Description = ?
                    """,
                    session["user_id"],
                    source,
                    destination_number,
                    amount,
                    description
                )

            # ------------------------------------------------
            # READ TRANSACTION ID
            # ------------------------------------------------

            result = cur.fetchone()

            if result is None:
                raise RuntimeError(
                    "Stored procedure did not return "
                    "a TransactionID."
                )

            transaction_id = int(result[0])

            if description:
                cur.execute(
                    """
                    INSERT INTO dbo.TransactionNotes
                    (
                        TransactionID,
                        CreatedByUserID,
                        NoteText
                    )
                    VALUES (?, ?, ?)
                    """,
                    transaction_id,
                    session["user_id"],
                    description
                )

                # Save transfer recipient automatically
                if kind == "Transfer":
                    cur.execute(
                        """
                        INSERT INTO dbo.Beneficiaries
                        (
                            CustomerID,
                            DisplayName,
                            AccountNumber,
                            IsActive
                        )
                        SELECT
                            sender.CustomerID,
                            LEFT(
                                CONCAT(c.FirstName, ' ', c.LastName),
                                120
                            ),
                            receiver.AccountNumber,
                            1
                        FROM dbo.Accounts sender
                        JOIN dbo.Accounts receiver
                            ON receiver.AccountNumber = ?
                        JOIN dbo.Customers c
                            ON c.CustomerID = receiver.CustomerID
                        WHERE sender.AccountID = ?
                          AND sender.CustomerID <> receiver.CustomerID
                          AND NOT EXISTS
                          (
                              SELECT 1
                              FROM dbo.Beneficiaries b
                                  WITH (UPDLOCK, HOLDLOCK)
                              WHERE b.CustomerID = sender.CustomerID
                                AND b.AccountNumber = receiver.AccountNumber
                          )
                        """,
                        destination_number,
                        source
                    )

            con.commit()

            return transaction_id

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

    # ========================================================
    # TRANSACTION HISTORY
    # ========================================================


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
                    t.Status,

                    CONCAT(
                        fc.FirstName, ' ', fc.LastName
                    ) AS SenderCustomer,

                    CONCAT(
                        dc.FirstName, ' ', dc.LastName
                    ) AS ReceiverCustomer,

                    CASE
                        WHEN NOT EXISTS (
                            SELECT 1
                            FROM dbo.FraudAlerts fa
                            WHERE fa.TransactionID = t.TransactionID
                        )
                        THEN 'Not Flagged'

                        WHEN EXISTS (
                            SELECT 1
                            FROM dbo.FraudAlerts fa
                            WHERE fa.TransactionID = t.TransactionID
                              AND fa.ReviewStatus = 'ConfirmedFraud'
                        )
                        THEN 'Confirmed Fraud'

                        WHEN EXISTS (
                            SELECT 1
                            FROM dbo.FraudAlerts fa
                            WHERE fa.TransactionID = t.TransactionID
                              AND (
                                  fa.ReviewStatus IS NULL
                                  OR fa.ReviewStatus = 'Pending'
                              )
                        )
                        THEN 'Pending Review'

                        WHEN EXISTS (
                            SELECT 1
                            FROM dbo.FraudAlerts fa
                            WHERE fa.TransactionID = t.TransactionID
                              AND fa.ReviewStatus = 'Reviewed'
                        )
                        THEN 'Reviewed'

                        ELSE 'False Positive'
                    END AS FraudStatus

                FROM dbo.Transactions AS t

                LEFT JOIN dbo.Accounts AS f
                    ON f.AccountID = t.FromAccountID

                LEFT JOIN dbo.Customers AS fc
                    ON fc.CustomerID = f.CustomerID

                LEFT JOIN dbo.Accounts AS d
                    ON d.AccountID = t.ToAccountID

                LEFT JOIN dbo.Customers AS dc
                    ON dc.CustomerID = d.CustomerID
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

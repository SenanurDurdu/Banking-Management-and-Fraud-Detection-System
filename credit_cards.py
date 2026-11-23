
import secrets

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from core import connect, audit


class CreditCardsMixin:

    # ============================================================
    # HELPERS
    # ============================================================

    def _credit_customer(self):
        session = self.require_login()

        if session["role"] != "Customer":
            raise PermissionError(
                "Customer access required."
            )

        customer_id = session.get("customer_id")

        if customer_id is None:
            raise PermissionError(
                "Customer session is invalid."
            )

        return session, int(customer_id)

    def _credit_admin(self):
        session = self.require_login()

        if session["role"] != "Admin":
            raise PermissionError(
                "Admin access required."
            )

        return session

    @staticmethod
    def _generate_card_number():
        # Demo identifier only.
        # Not a payment-network-issued card number.

        return "9" + "".join(
            str(secrets.randbelow(10))
            for _ in range(15)
        )

    @staticmethod
    def _validate_credit_card_amount(amount):

        try:
            amount = Decimal(str(amount).strip())

        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(
                "Invalid transaction amount."
            )

        if not amount.is_finite():
            raise ValueError(
                "Invalid transaction amount."
            )

        if amount <= 0:
            raise ValueError(
                "Transaction amount must be greater than zero."
            )

        if amount > Decimal("9999999999999999.99"):
            raise ValueError(
                "Transaction amount is too large."
            )

        if amount != amount.quantize(Decimal("0.01")):
            raise ValueError(
                "Amount cannot have more than two decimal places."
            )

        return amount.quantize(Decimal("0.01"))

    # ============================================================
    # CUSTOMER: APPLY FOR CREDIT CARD
    # ============================================================

    def apply_for_credit_card(
        self,
        card_type,
        requested_limit
    ):
        session, customer_id = self._credit_customer()

        card_type = str(card_type).strip()

        if card_type not in ("Standard", "Gold"):
            raise ValueError(
                "Invalid credit card type."
            )

        try:
            requested_limit = Decimal(
                str(requested_limit)
            )

        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(
                "Invalid requested credit limit."
            )

        if not requested_limit.is_finite():
            raise ValueError(
                "Invalid requested credit limit."
            )

        allowed_limits = (
            Decimal("5000"),
            Decimal("10000"),
            Decimal("25000"),
            Decimal("50000")
        )

        if requested_limit not in allowed_limits:
            raise ValueError(
                "Invalid requested credit limit."
            )

        con = connect()

        try:
            con.autocommit = False

            cur = con.cursor()

            cur.execute(
                """
                SELECT ApplicationID
                FROM dbo.CreditCardApplications
                    WITH (UPDLOCK, HOLDLOCK)
                WHERE CustomerID = ?
                  AND ApplicationStatus = 'Pending'
                """,
                customer_id
            )

            if cur.fetchone() is not None:
                raise ValueError(
                    "You already have a pending "
                    "credit card application."
                )

            cur.execute(
                """
                INSERT INTO dbo.CreditCardApplications
                (
                    CustomerID,
                    CardType,
                    RequestedLimit,
                    Currency,
                    ApplicationStatus
                )
                OUTPUT INSERTED.ApplicationID
                VALUES (?, ?, ?, 'TRY', 'Pending')
                """,
                customer_id,
                card_type,
                requested_limit
            )

            application_id = int(
                cur.fetchone()[0]
            )

            audit(
                cur,
                "CREDIT_CARD_APPLICATION",
                "CreditCardApplications",
                application_id,
                (
                    f"Credit card application submitted. "
                    f"Type={card_type}, "
                    f"Limit={requested_limit} TRY"
                ),
                user_id=session["user_id"]
            )

            con.commit()

            return application_id

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

    # ============================================================
    # CUSTOMER: MY APPLICATIONS
    # ============================================================

    def my_credit_card_applications(self):

        _, customer_id = self._credit_customer()

        con = connect()

        try:
            cur = con.cursor()

            cur.execute(
                """
                SELECT
                    ApplicationID,
                    CardType,
                    RequestedLimit,
                    ApplicationStatus,
                    AppliedAt,
                    ReviewedAt,
                    ReviewNote
                FROM dbo.CreditCardApplications
                WHERE CustomerID = ?
                ORDER BY ApplicationID DESC
                """,
                customer_id
            )

            return cur.fetchall()

        finally:
            con.close()

    # ============================================================
    # CUSTOMER: MY CREDIT CARDS
    # ============================================================

    def my_credit_cards(self):

        _, customer_id = self._credit_customer()

        con = connect()

        try:
            cur = con.cursor()

            cur.execute(
                """
                SELECT
                    CreditCardID,
                    CardType,
                    CreditLimit,
                    OutstandingBalance,
                    Currency,
                    CardStatus,
                    ExpiresAt,
                    CardNumber
                FROM dbo.CreditCards
                WHERE CustomerID = ?
                ORDER BY CreditCardID DESC
                """,
                customer_id
            )

            return cur.fetchall()

        finally:
            con.close()

    # ============================================================
    # ADMIN: LIST APPLICATIONS
    # ============================================================

    def admin_credit_card_applications(self):

        self._credit_admin()

        con = connect()

        try:
            cur = con.cursor()

            cur.execute(
                """
                SELECT
                    ApplicationID,
                    CustomerID,
                    CardType,
                    RequestedLimit,
                    ApplicationStatus,
                    AppliedAt,
                    ReviewNote
                FROM dbo.CreditCardApplications
                ORDER BY
                    CASE
                        WHEN ApplicationStatus = 'Pending'
                        THEN 0
                        ELSE 1
                    END,
                    ApplicationID DESC
                """
            )

            return cur.fetchall()

        finally:
            con.close()

    # ============================================================
    # ADMIN: CUSTOMER BANK ACCOUNTS
    # ============================================================

    def admin_credit_card_accounts(
        self,
        customer_id
    ):
        self._credit_admin()

        customer_id = int(customer_id)

        con = connect()

        try:
            cur = con.cursor()

            cur.execute(
                """
                SELECT
                    AccountID,
                    AccountNumber
                FROM dbo.Accounts
                WHERE CustomerID = ?
                  AND IsActive = 1
                  AND IsFrozen = 0
                  AND Currency = 'TRY'
                ORDER BY AccountID
                """,
                customer_id
            )

            return cur.fetchall()

        finally:
            con.close()

    # ============================================================
    # ADMIN: GET LINKED BANK ACCOUNT
    # ============================================================

    def admin_credit_card_linked_account(
        self,
        application_id
    ):
        self._credit_admin()

        application_id = int(application_id)

        if application_id <= 0:
            raise ValueError(
                "Invalid application ID."
            )

        con = connect()

        try:
            cur = con.cursor()

            cur.execute(
                """
                SELECT
                    a.AccountID,
                    a.AccountNumber,
                    a.IsActive,
                    a.IsFrozen
                FROM dbo.CreditCards AS cc
                INNER JOIN dbo.Accounts AS a
                    ON a.AccountID = cc.LinkedAccountID
                   AND a.CustomerID = cc.CustomerID
                WHERE cc.ApplicationID = ?
                """,
                application_id
            )

            return cur.fetchone()

        finally:
            con.close()

    # ============================================================
    # ADMIN: APPROVE APPLICATION
    # ============================================================

    def approve_credit_card_application(
        self,
        application_id,
        linked_account_id
    ):
        session = self._credit_admin()

        application_id = int(application_id)
        linked_account_id = int(linked_account_id)

        if application_id <= 0:
            raise ValueError(
                "Invalid application ID."
            )

        if linked_account_id <= 0:
            raise ValueError(
                "Invalid bank account ID."
            )

        con = connect()

        try:
            con.autocommit = False

            cur = con.cursor()

            # Lock application until transaction finishes.

            cur.execute(
                """
                SELECT
                    CustomerID,
                    CardType,
                    RequestedLimit,
                    ApplicationStatus
                FROM dbo.CreditCardApplications
                    WITH (UPDLOCK, HOLDLOCK)
                WHERE ApplicationID = ?
                """,
                application_id
            )

            application = cur.fetchone()

            if application is None:
                raise ValueError(
                    "Application not found."
                )

            customer_id = int(application[0])
            card_type = str(application[1])

            credit_limit = Decimal(
                str(application[2])
            )

            status = str(application[3])

            if status != "Pending":
                raise ValueError(
                    "Only pending applications "
                    "can be approved."
                )

            # Verify linked account ownership and status.

            cur.execute(
                """
                SELECT AccountID
                FROM dbo.Accounts
                    WITH (UPDLOCK, HOLDLOCK)
                WHERE AccountID = ?
                  AND CustomerID = ?
                  AND IsActive = 1
                  AND IsFrozen = 0
                  AND Currency = 'TRY'
                """,
                linked_account_id,
                customer_id
            )

            if cur.fetchone() is None:
                raise ValueError(
                    "The customer must have an active, "
                    "unfrozen TRY bank account."
                )

            # Check for an existing card.

            cur.execute(
                """
                SELECT CreditCardID
                FROM dbo.CreditCards
                WHERE ApplicationID = ?
                """,
                application_id
            )

            if cur.fetchone() is not None:
                raise ValueError(
                    "A credit card already exists "
                    "for this application."
                )

            # Demo expiry: approximately four years.

            expires_at = (
                date.today() + timedelta(days=1460)
            )

            # Generate a unique demo card identifier.

            for _ in range(10):

                card_number = self._generate_card_number()

                cur.execute(
                    """
                    SELECT 1
                    FROM dbo.CreditCards
                    WHERE CardNumber = ?
                    """,
                    card_number
                )

                if cur.fetchone() is None:
                    break

            else:
                raise RuntimeError(
                    "Could not generate a unique "
                    "card identifier."
                )

            # Create the credit card.

            # Create the credit card.

            cur.execute(
                """
                SET NOCOUNT ON;

                DECLARE @NewCard TABLE
                (
                    CreditCardID INT
                );

                INSERT INTO dbo.CreditCards
                (
                    ApplicationID,
                    CustomerID,
                    LinkedAccountID,
                    CardNumber,
                    CardType,
                    CreditLimit,
                    OutstandingBalance,
                    Currency,
                    CardStatus,
                    ExpiresAt
                )
                OUTPUT INSERTED.CreditCardID
                    INTO @NewCard(CreditCardID)
                VALUES
                (
                    ?, ?, ?, ?, ?, ?, 0, 'TRY', 'Active', ?
                );

                SELECT CreditCardID
                FROM @NewCard;
                """,
                application_id,
                customer_id,
                linked_account_id,
                card_number,
                card_type,
                credit_limit,
                expires_at
            )

            credit_card_id = int(cur.fetchone()[0])
            # Create default billing settings if not already created
            cur.execute(
                """
                INSERT INTO dbo.CreditCardBillingSettings
                (
                    CreditCardID,
                    ClosingDay,
                    DueDaysAfterClosing
                )
                SELECT ?, 20, 10
                WHERE NOT EXISTS
                (
                    SELECT 1
                    FROM dbo.CreditCardBillingSettings WITH (UPDLOCK, HOLDLOCK)
                    WHERE CreditCardID = ?
                )
                """,
                credit_card_id,
                credit_card_id
            )

            # Update application status.

            cur.execute(
                """
                UPDATE dbo.CreditCardApplications
                SET
                    ApplicationStatus = 'Approved',
                    ReviewedByUserID = ?,
                    ReviewedAt = SYSDATETIME(),
                    ReviewNote = ?
                WHERE ApplicationID = ?
                  AND ApplicationStatus = 'Pending'
                """,
                session["user_id"],
                "Approved by administrator.",
                application_id
            )

            if cur.rowcount != 1:
                raise RuntimeError(
                    "Application update failed."
                )

            # Create audit record.

            audit(
                cur,
                "CREDIT_CARD_APPROVED",
                "CreditCardApplications",
                application_id,
                (
                    f"Approved. CardID={credit_card_id}, "
                    f"Limit={credit_limit} TRY"
                ),
                user_id=session["user_id"]
            )

            con.commit()

            return credit_card_id

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

    # ============================================================
    # ADMIN: REJECT APPLICATION
    # ============================================================

    def reject_credit_card_application(
        self,
        application_id,
        reason
    ):
        session = self._credit_admin()

        application_id = int(application_id)
        reason = str(reason or "").strip()

        if application_id <= 0:
            raise ValueError(
                "Invalid application ID."
            )

        if not reason:
            raise ValueError(
                "Rejection reason is required."
            )

        if len(reason) > 500:
            raise ValueError(
                "Rejection reason cannot exceed "
                "500 characters."
            )

        con = connect()

        try:
            con.autocommit = False

            cur = con.cursor()

            cur.execute(
                """
                SELECT ApplicationStatus
                FROM dbo.CreditCardApplications
                    WITH (UPDLOCK, HOLDLOCK)
                WHERE ApplicationID = ?
                """,
                application_id
            )

            application = cur.fetchone()

            if application is None:
                raise ValueError(
                    "Application not found."
                )

            if str(application[0]) != "Pending":
                raise ValueError(
                    "Only pending applications "
                    "can be rejected."
                )

            cur.execute(
                """
                UPDATE dbo.CreditCardApplications
                SET
                    ApplicationStatus = 'Rejected',
                    ReviewedByUserID = ?,
                    ReviewedAt = SYSDATETIME(),
                    ReviewNote = ?
                WHERE ApplicationID = ?
                  AND ApplicationStatus = 'Pending'
                """,
                session["user_id"],
                reason,
                application_id
            )

            if cur.rowcount != 1:
                raise RuntimeError(
                    "Application update failed."
                )

            audit(
                cur,
                "CREDIT_CARD_REJECTED",
                "CreditCardApplications",
                application_id,
                f"Rejected. Reason: {reason}",
                user_id=session["user_id"]
            )

            con.commit()

            return True

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

    # ============================================================
    # CREDIT CARD TRANSACTION EXECUTION
    # ============================================================

    def _execute_credit_card_transaction(
        self,
        kind,
        credit_card_id,
        amount,
        description=""
    ):
        session, _ = self._credit_customer()

        # Only predefined stored procedures are allowed.

        procedures = {
            "Purchase": "dbo.sp_CreditCardPurchase",
            "CashAdvance": "dbo.sp_CreditCardCashAdvance",
            "Payment": "dbo.sp_CreditCardPayment"
        }

        if kind not in procedures:
            raise ValueError(
                "Invalid credit card transaction type."
            )

        # Validate credit card ID.

        try:
            credit_card_id = int(credit_card_id)

            if credit_card_id <= 0:
                raise ValueError()

        except (ValueError, TypeError, OverflowError):
            raise ValueError(
                "Valid credit card is required."
            )

        # Validate amount.

        amount = self._validate_credit_card_amount(
            amount
        )

        # Validate transaction description.

        description = str(
            description or ""
        ).strip()

        if len(description) > 250:
            raise ValueError(
                "Description cannot exceed 250 characters."
            )

        # Default transaction descriptions.

        default_descriptions = {
            "Purchase": "Credit card purchase",
            "CashAdvance": "Credit card cash advance",
            "Payment": "Credit card debt payment"
        }

        if not description:
            description = default_descriptions[kind]

        procedure = procedures[kind]

        con = connect()

        try:
            con.autocommit = False

            cur = con.cursor()

            # Required SQL Server session options.
            # These settings support filtered indexes.

            cur.execute(
                """
                SET XACT_ABORT ON;
                SET NOCOUNT ON;
                SET ANSI_NULLS ON;
                SET ANSI_PADDING ON;
                SET ANSI_WARNINGS ON;
                SET QUOTED_IDENTIFIER ON;
                SET CONCAT_NULL_YIELDS_NULL ON;
                SET ARITHABORT ON;
                SET NUMERIC_ROUNDABORT OFF;
                """
            )

            # Execute the selected stored procedure.
            #
            # SQL Server handles:
            # - Customer ownership validation
            # - Account status validation
            # - Credit card status validation
            # - Available limit validation
            # - Bank balance validation
            # - Outstanding debt updates
            # - Bank balance updates
            # - Bank transaction records
            # - Credit card transaction records
            # - Audit logging
            # - Atomic transaction execution

            cur.execute(
                f"""
                EXEC {procedure}
                    @UserID = ?,
                    @CreditCardID = ?,
                    @Amount = ?,
                    @Description = ?
                """,
                int(session["user_id"]),
                credit_card_id,
                amount,
                description
            )

            # Locate the transaction result set.

            transaction_id = None

            while True:

                if cur.description is not None:

                    column_names = [
                        str(column[0]).lower()
                        for column in cur.description
                    ]

                    if "cardtransactionid" in column_names:

                        result = cur.fetchone()

                        if result is not None:

                            result_index = column_names.index(
                                "cardtransactionid"
                            )

                            transaction_id = int(
                                result[result_index]
                            )

                if not cur.nextset():
                    break

            if transaction_id is None:
                raise RuntimeError(
                    "Credit card transaction result "
                    "was not returned."
                )

            if transaction_id <= 0:
                raise RuntimeError(
                    "Invalid card transaction ID returned."
                )

            con.commit()

            return transaction_id

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

    # ============================================================
    # CUSTOMER: CREDIT CARD PURCHASE
    # ============================================================

    def credit_card_purchase(
        self,
        credit_card_id,
        amount,
        description=""
    ):
        """
        Execute a credit card purchase.

        Bank balance remains unchanged.
        Outstanding credit card debt increases.
        Available credit limit decreases.
        """

        return self._execute_credit_card_transaction(
            "Purchase",
            credit_card_id,
            amount,
            description
        )

    # ============================================================
    # CUSTOMER: CREDIT CARD CASH ADVANCE
    # ============================================================

    def credit_card_cash_advance(
        self,
        credit_card_id,
        amount,
        description=""
    ):
        """
        Transfer credit card funds to the linked bank account.

        Bank balance increases.
        Outstanding credit card debt increases.
        Available credit limit decreases.
        """

        return self._execute_credit_card_transaction(
            "CashAdvance",
            credit_card_id,
            amount,
            description
        )

    # ============================================================
    # CUSTOMER: CREDIT CARD DEBT PAYMENT
    # ============================================================

    def credit_card_payment(
        self,
        credit_card_id,
        amount,
        description=""
    ):
        """
        Pay credit card debt using the linked bank account.

        Bank balance decreases.
        Outstanding credit card debt decreases.
        Available credit limit increases.
        """

        return self._execute_credit_card_transaction(
            "Payment",
            credit_card_id,
            amount,
            description
        )

    # ============================================================
    # CUSTOMER: CREDIT CARD TRANSACTION HISTORY
    # ============================================================

    def my_credit_card_transactions(
        self,
        credit_card_id=None
    ):
        _, customer_id = self._credit_customer()

        con = connect()

        try:
            cur = con.cursor()

            sql = """
                SELECT
                    ct.CardTransactionID,
                    ct.CreditCardID,
                    cc.CardType,
                    RIGHT(cc.CardNumber, 4),
                    ct.TransactionType,
                    ct.Amount,
                    ct.Description,
                    ct.TransactionStatus,
                    ct.CreatedAt
                FROM dbo.CreditCardTransactions AS ct
                INNER JOIN dbo.CreditCards AS cc
                    ON cc.CreditCardID = ct.CreditCardID
                WHERE cc.CustomerID = ?
            """

            params = [customer_id]

            if credit_card_id is not None:

                credit_card_id = int(credit_card_id)

                if credit_card_id <= 0:
                    raise ValueError(
                        "Invalid credit card ID."
                    )

                sql += """
                    AND cc.CreditCardID = ?
                """

                params.append(credit_card_id)

            sql += """
                ORDER BY ct.CardTransactionID DESC
            """

            cur.execute(sql, *params)

            return cur.fetchall()

        finally:
            con.close()

    # ============================================================
    # ADMIN: CREDIT CARD TRANSACTION HISTORY
    # ============================================================

    def admin_credit_card_transactions(self):

        self._credit_admin()

        con = connect()

        try:
            cur = con.cursor()

            cur.execute(
                """
                SELECT
                    ct.CardTransactionID,
                    cc.CreditCardID,
                    cc.CustomerID,
                    cc.CardType,
                    RIGHT(cc.CardNumber, 4),
                    ct.TransactionType,
                    ct.Amount,
                    ct.Description,
                    ct.TransactionStatus,
                    ct.CreatedAt
                FROM dbo.CreditCardTransactions AS ct
                INNER JOIN dbo.CreditCards AS cc
                    ON cc.CreditCardID = ct.CreditCardID
                ORDER BY ct.CardTransactionID DESC
                """
            )

            return cur.fetchall()

        finally:
            con.close()

    # ============================================================
    # CUSTOMER: CREDIT CARD TRANSACTION DISPATCHER
    # ============================================================

    def credit_card_transact(
        self,
        kind,
        credit_card_id,
        value,
        description=""
    ):
        self._credit_customer()

        if kind not in (
            "Purchase",
            "CashAdvance",
            "Payment"
        ):
            raise ValueError(
                "Invalid credit card transaction type."
            )

        try:
            credit_card_id = int(credit_card_id)

            if credit_card_id <= 0:
                raise ValueError()

        except (ValueError, TypeError, OverflowError):
            raise ValueError(
                "Valid credit card is required."
            )

        amount = self._validate_credit_card_amount(
            value
        )

        description = str(
            description or ""
        ).strip()

        if len(description) > 250:
            raise ValueError(
                "Description cannot exceed 250 characters."
            )

        # ========================================================
        # PURCHASE
        # ========================================================

        if kind == "Purchase":

            return self.credit_card_purchase(
                credit_card_id,
                amount,
                description
            )

        # ========================================================
        # CASH ADVANCE
        # ========================================================

        elif kind == "CashAdvance":

            return self.credit_card_cash_advance(
                credit_card_id,
                amount,
                description
            )

        # ========================================================
        # CREDIT CARD DEBT PAYMENT
        # ========================================================

        elif kind == "Payment":

            return self.credit_card_payment(
                credit_card_id,
                amount,
                description
            )

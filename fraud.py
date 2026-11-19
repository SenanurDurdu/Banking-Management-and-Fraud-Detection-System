
from core import *


class FraudMixin:

    # ========================================================
    # FRAUD RULES - ADMIN
    # ========================================================

    def fraud_rules(self):

        self.require_admin()

        con = connect()

        try:

            return con.cursor().execute(
                """
                SELECT
                    RuleID,
                    RuleName,
                    RuleType,
                    ThresholdValue,
                    TimeWindowMinutes,
                    IsActive
                FROM dbo.FraudRules
                ORDER BY RuleID
                """
            ).fetchall()

        finally:
            con.close()


    # ========================================================
    # FRAUD ALERTS - ADMIN
    # ========================================================

    def alerts(self):

        self.require_admin()

        con = connect()

        try:

            return con.cursor().execute(
                """
                SELECT
                    v.AlertID,

                    v.TransactionReference
                        AS TransactionID,

                    v.RuleName,
                    v.TransactionType,

                    v.SenderCustomerID,
                    v.SenderCustomer,
                    v.SenderAccountNumber,

                    v.ReceiverCustomerID,
                    v.ReceiverCustomer,
                    v.ReceiverAccountNumber,

                    v.Amount,
                    v.AlertDescription,
                    v.RiskLevel,
                    v.ReviewStatus,
                    v.CreatedAt,
                    v.ReviewedAt,

                    fa.ReviewNote,

                    v.TransactionDescription

                FROM dbo.vw_FraudAlertDetails AS v

                INNER JOIN dbo.FraudAlerts AS fa
                    ON fa.AlertID = v.AlertID

                ORDER BY v.AlertID DESC
                """
            ).fetchall()

        finally:
            con.close()


    # ========================================================
    # FRAUD SCAN - ADMIN
    # ========================================================

    def scan_fraud(self):

        session = self.require_admin()

        admin_user_id = int(
            session["user_id"]
        )

        con = connect()

        try:

            con.autocommit = False

            cur = con.cursor()

            cur.execute("SET XACT_ABORT ON;")

            # Required settings for filtered indexes.

            cur.execute(
                """
                SET ANSI_NULLS ON;
                SET QUOTED_IDENTIFIER ON;
                SET ANSI_PADDING ON;
                SET ANSI_WARNINGS ON;
                SET CONCAT_NULL_YIELDS_NULL ON;
                SET ARITHABORT ON;
                SET NUMERIC_ROUNDABORT OFF;
                """
            )

            # Keep both scans in the same transaction.

            cur.execute("BEGIN TRANSACTION;")


            # ------------------------------------------------
            # BANK TRANSACTION FRAUD SCAN
            # ------------------------------------------------

            cur.execute(
                """
                EXEC dbo.sp_ScanFraud
                    @UserID = ?
                """,
                admin_user_id
            )

            bank_result = cur.fetchone()

            if bank_result is None:

                raise RuntimeError(
                    "Bank fraud scan procedure "
                    "did not return a result."
                )

            bank_alerts = int(
                bank_result[0]
            )


            # ------------------------------------------------
            # CREDIT CARD FRAUD SCAN
            # ------------------------------------------------

            cur.execute(
                """
                EXEC dbo.sp_ScanCreditCardFraud
                    @UserID = ?
                """,
                admin_user_id
            )

            card_result = cur.fetchone()

            if card_result is None:

                raise RuntimeError(
                    "Credit card fraud scan procedure "
                    "did not return a result."
                )

            card_alerts = int(
                card_result[0]
            )


            # ------------------------------------------------
            # RETURN TOTAL NEW ALERTS
            # ------------------------------------------------

            new_alerts = (
                bank_alerts + card_alerts
            )

            cur.execute("COMMIT TRANSACTION;")

            con.commit()

            return new_alerts

        except Exception:

            con.rollback()

            raise

        finally:

            con.close()


    # ========================================================
    # REVIEW FRAUD ALERT - ADMIN
    # ========================================================

    def review(
        self,
        alert_id,
        status,
        review_note=""
    ):

        session = self.require_admin()

        admin_user_id = int(
            session["user_id"]
        )


        # ----------------------------------------------------
        # VALIDATE REVIEW STATUS
        # ----------------------------------------------------

        allowed_statuses = (
            "Reviewed",
            "FalsePositive",
            "ConfirmedFraud"
        )

        if status not in allowed_statuses:

            raise ValueError(
                "Invalid review status."
            )


        # ----------------------------------------------------
        # VALIDATE ALERT ID
        # ----------------------------------------------------

        try:

            alert_id = int(alert_id)

            if alert_id <= 0:
                raise ValueError()

        except (ValueError, TypeError):

            raise ValueError(
                "Invalid Alert ID."
            )


        # ----------------------------------------------------
        # VALIDATE REVIEW NOTE
        # ----------------------------------------------------

        if review_note is None:
            review_note = ""

        if not isinstance(review_note, str):

            raise ValueError(
                "Review note must be text."
            )

        review_note = review_note.strip()

        if len(review_note) > 500:

            raise ValueError(
                "Review note cannot exceed "
                "500 characters."
            )

        review_note_db = review_note or None


        # ----------------------------------------------------
        # OPEN DATABASE CONNECTION
        # ----------------------------------------------------

        con = connect()

        try:

            con.autocommit = False

            cur = con.cursor()

            cur.execute("SET XACT_ABORT ON;")

            cur.execute(
                """
                SET ANSI_NULLS ON;
                SET QUOTED_IDENTIFIER ON;
                SET ANSI_PADDING ON;
                SET ANSI_WARNINGS ON;
                SET CONCAT_NULL_YIELDS_NULL ON;
                SET ARITHABORT ON;
                SET NUMERIC_ROUNDABORT OFF;
                """
            )


            # ------------------------------------------------
            # VALIDATE ACTIVE ADMIN
            # ------------------------------------------------

            admin = cur.execute(
                """
                SELECT UserID

                FROM dbo.Users
                    WITH (UPDLOCK, HOLDLOCK)

                WHERE UserID = ?
                  AND Role = 'Admin'
                  AND IsActive = 1
                """,
                admin_user_id
            ).fetchone()

            if admin is None:

                raise PermissionError(
                    "Active admin access required."
                )


            # ------------------------------------------------
            # LOCK FRAUD ALERT
            # ------------------------------------------------

            alert = cur.execute(
                """
                SELECT
                    AlertID,
                    ReviewStatus,
                    TransactionID,
                    CardTransactionID

                FROM dbo.FraudAlerts
                    WITH (UPDLOCK, HOLDLOCK)

                WHERE AlertID = ?
                """,
                alert_id
            ).fetchone()

            if alert is None:

                raise ValueError(
                    "Alert not found."
                )

            if alert.ReviewStatus != "Pending":

                raise ValueError(
                    "Alert already reviewed."
                )


            # ------------------------------------------------
            # IDENTIFY RELATED TRANSACTION
            # ------------------------------------------------

            bank_transaction_id = (
                alert.TransactionID
            )

            card_transaction_id = (
                alert.CardTransactionID
            )

            credit_card_id = None

            is_card_alert = False


            # ------------------------------------------------
            # CREDIT CARD PURCHASE ALERT
            # ------------------------------------------------

            if card_transaction_id is not None:

                transaction = cur.execute(
                    """
                    SELECT
                        cc.CreditCardID,
                        cc.LinkedAccountID
                            AS AffectedAccountID

                    FROM dbo.CreditCardTransactions AS ct

                    INNER JOIN dbo.CreditCards AS cc
                        ON cc.CreditCardID =
                           ct.CreditCardID

                    WHERE ct.CardTransactionID = ?
                    """,
                    card_transaction_id
                ).fetchone()

                if transaction is None:

                    raise ValueError(
                        "Credit card transaction not found."
                    )

                affected_account_id = (
                    transaction.AffectedAccountID
                )

                credit_card_id = int(
                    transaction.CreditCardID
                )

                is_card_alert = True


            # ------------------------------------------------
            # BANK TRANSACTION ALERT
            # ------------------------------------------------

            elif bank_transaction_id is not None:

                transaction = cur.execute(
                    """
                    SELECT

                        CASE

                            WHEN t.TransactionType = 'Deposit'
                            THEN t.ToAccountID

                            ELSE t.FromAccountID

                        END AS AffectedAccountID,

                        ct.CreditCardID

                    FROM dbo.Transactions AS t

                    LEFT JOIN dbo.CreditCardTransactions AS ct

                        ON ct.BankTransactionID =
                           t.TransactionID

                    WHERE t.TransactionID = ?
                    """,
                    bank_transaction_id
                ).fetchone()

                if transaction is None:

                    raise ValueError(
                        "Bank transaction not found."
                    )

                affected_account_id = (
                    transaction.AffectedAccountID
                )

                if transaction.CreditCardID is not None:

                    credit_card_id = int(
                        transaction.CreditCardID
                    )

                    is_card_alert = True

            else:

                raise ValueError(
                    "No transaction associated "
                    "with this alert."
                )


            if affected_account_id is None:

                raise ValueError(
                    "No account associated "
                    "with this alert."
                )


            # ------------------------------------------------
            # LOCK AFFECTED BANK ACCOUNT
            # ------------------------------------------------

            account = cur.execute(
                """
                SELECT
                    AccountID,
                    CustomerID,
                    AccountNumber,
                    IsFrozen

                FROM dbo.Accounts
                    WITH (UPDLOCK, HOLDLOCK)

                WHERE AccountID = ?
                """,
                affected_account_id
            ).fetchone()

            if account is None:

                raise ValueError(
                    "Affected account not found."
                )


            # ------------------------------------------------
            # LOCK RELATED CREDIT CARD
            # ------------------------------------------------

            card = None

            if is_card_alert:

                card = cur.execute(
                    """
                    SELECT
                        CreditCardID,
                        CustomerID,
                        LinkedAccountID,
                        CardStatus,

                        RIGHT(CardNumber, 4)
                            AS LastFourDigits

                    FROM dbo.CreditCards
                        WITH (UPDLOCK, HOLDLOCK)

                    WHERE CreditCardID = ?
                      AND CustomerID = ?
                      AND LinkedAccountID = ?
                    """,
                    credit_card_id,
                    int(account.CustomerID),
                    int(affected_account_id)
                ).fetchone()

                if card is None:

                    raise ValueError(
                        "Affected credit card not found."
                    )


            # ------------------------------------------------
            # SAVE REVIEW DECISION
            # ------------------------------------------------

            cur.execute(
                """
                UPDATE dbo.FraudAlerts

                SET
                    ReviewStatus = ?,
                    ReviewedAt = SYSDATETIME(),
                    ReviewedByUserID = ?,
                    ReviewNote = ?

                WHERE AlertID = ?
                  AND ReviewStatus = 'Pending'
                """,
                status,
                admin_user_id,
                review_note_db,
                alert_id
            )

            if cur.rowcount != 1:

                raise ValueError(
                    "Alert not found or already reviewed."
                )


            # ------------------------------------------------
            # REVIEW AUDIT LOG
            # ------------------------------------------------

            description = (
                f"Alert marked as {status}"
            )

            if review_note:

                description += (
                    f". Note: {review_note}"
                )

            audit(
                cur,
                "REVIEW",
                "FraudAlert",
                alert_id,
                description[:500],
                user_id=admin_user_id
            )


            # ------------------------------------------------
            # CONFIRMED FRAUD
            # ------------------------------------------------

            if status == "ConfirmedFraud":


                # --------------------------------------------
                # FREEZE AFFECTED BANK ACCOUNT
                # --------------------------------------------

                cur.execute(
                    """
                    UPDATE dbo.Accounts

                    SET IsFrozen = 1

                    WHERE AccountID = ?
                      AND IsFrozen = 0
                    """,
                    affected_account_id
                )

                if cur.rowcount == 1:

                    audit(
                        cur,
                        "ACCOUNT_FREEZE",
                        "Account",
                        int(affected_account_id),
                        (
                            f"Account frozen due to "
                            f"confirmed fraud alert "
                            f"{alert_id}."
                        ),
                        user_id=admin_user_id
                    )


                # --------------------------------------------
                # FREEZE RELATED CREDIT CARD
                # --------------------------------------------

                if is_card_alert:

                    cur.execute(
                        """
                        UPDATE dbo.CreditCards

                        SET CardStatus = 'Frozen'

                        WHERE CreditCardID = ?
                          AND CardStatus = 'Active'
                        """,
                        credit_card_id
                    )

                    if cur.rowcount == 1:

                        audit(
                            cur,
                            "CREDIT_CARD_FREEZE",
                            "CreditCards",
                            credit_card_id,
                            (
                                f"Credit card frozen due "
                                f"to confirmed fraud "
                                f"alert {alert_id}."
                            ),
                            user_id=admin_user_id
                        )


                # --------------------------------------------
                # BUILD CUSTOMER SECURITY NOTIFICATION
                # --------------------------------------------

                account_number = str(
                    account.AccountNumber
                ).strip()

                if is_card_alert:

                    card_digits = str(
                        card.LastFourDigits
                    ).strip()

                    notification_title = (
                        "Credit Card Security Restriction"
                    )

                    notification_message = (
                        f"A security restriction has been "
                        f"applied to your credit card "
                        f"ending in {card_digits} and "
                        f"linked account {account_number} "
                        f"following a fraud review. "
                        f"Purchases, cash advances, deposits, "
                        f"withdrawals and transfers are "
                        f"restricted. "
                        f"Your balance, credit card debt "
                        f"and transaction history "
                        f"remain available. "
                        f"Reference: Fraud Alert "
                        f"#{alert_id}. "
                        f"Please contact the bank "
                        f"administrator."
                    )

                else:

                    notification_title = (
                        "Account Security Restriction"
                    )

                    notification_message = (
                        f"Your account {account_number} "
                        f"has been restricted following "
                        f"a security review. Deposits, "
                        f"withdrawals and transfers are "
                        f"temporarily disabled. "
                        f"Credit card operations linked "
                        f"to this account are also blocked. "
                        f"Your balance and transaction "
                        f"history remain available. "
                        f"Reference: Fraud Alert "
                        f"#{alert_id}. "
                        f"Please contact the bank "
                        f"administrator."
                    )


                # --------------------------------------------
                # SEND CUSTOMER NOTIFICATION
                # --------------------------------------------

                cur.execute(
                    """
                    INSERT INTO dbo.Notifications
                    (
                        CustomerID,
                        Title,
                        Message,
                        NotificationType
                    )

                    VALUES (?, ?, ?, ?)
                    """,
                    int(account.CustomerID),
                    notification_title,
                    notification_message,
                    "Security"
                )


            # ------------------------------------------------
            # COMMIT REVIEW
            # ------------------------------------------------

            con.commit()

            return True

        except Exception:

            con.rollback()

            raise

        finally:

            con.close()


    # ========================================================
    # CUSTOMER FRAUD REVIEWS
    # ========================================================

    def customer_fraud_reviews(self):

        session = self.require_login()

        if session["role"] != "Customer":

            raise PermissionError(
                "Customer access required."
            )

        customer_id = session["customer_id"]

        if customer_id is None:

            raise PermissionError(
                "Customer account not found."
            )

        con = connect()

        try:

            cur = con.cursor()

            return cur.execute(
                """
                SELECT

                    v.AlertID,

                    v.TransactionReference
                        AS TransactionID,

                    v.TransactionType,
                    v.Amount,
                    v.RuleName,
                    v.RiskLevel,
                    v.ReviewStatus,
                    v.ReviewNote,
                    v.ReviewedAt,

                    v.TransactionDescription

                FROM dbo.vw_CustomerFraudReviews AS v

                WHERE EXISTS
                (
                    SELECT 1

                    FROM dbo.Accounts AS a

                    WHERE a.CustomerID = ?

                      AND
                      (
                          a.AccountID = v.FromAccountID

                          OR

                          a.AccountID = v.ToAccountID
                      )
                )

                ORDER BY
                    v.ReviewedAt DESC,
                    v.AlertID DESC
                """,
                customer_id
            ).fetchall()

        finally:

            con.close()

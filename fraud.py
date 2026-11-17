
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
                    v.TransactionID,
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
                    t.Description AS TransactionDescription

                FROM dbo.vw_FraudAlertDetails AS v

                INNER JOIN dbo.FraudAlerts AS fa
                    ON fa.AlertID = v.AlertID

                INNER JOIN dbo.Transactions AS t
                    ON t.TransactionID = v.TransactionID

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
        admin_user_id = int(session["user_id"])

        con = connect()

        try:
            cur = con.cursor()

            cur.execute(
                """
                EXEC dbo.sp_ScanFraud
                    @UserID = ?
                """,
                admin_user_id
            )

            result = cur.fetchone()

            if result is None:
                raise RuntimeError(
                    "Fraud scan procedure did not "
                    "return a result."
                )

            new_alerts = int(result[0])

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
        admin_user_id = int(session["user_id"])

        allowed_statuses = (
            "Reviewed",
            "FalsePositive",
            "ConfirmedFraud"
        )

        if status not in allowed_statuses:
            raise ValueError(
                "Invalid review status."
            )

        try:
            alert_id = int(alert_id)

            if alert_id <= 0:
                raise ValueError()

        except (ValueError, TypeError):
            raise ValueError(
                "Invalid Alert ID."
            )

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

        review_note_db = (
            review_note if review_note else None
        )

        con = connect()

        try:
            cur = con.cursor()

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
                    "Alert not found or "
                    "already reviewed."
                )

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
                    v.TransactionID,
                    v.TransactionType,
                    v.Amount,
                    v.RuleName,
                    v.RiskLevel,
                    v.ReviewStatus,
                    v.ReviewNote,
                    v.ReviewedAt,
                    t.Description AS TransactionDescription

                FROM dbo.vw_CustomerFraudReviews AS v

                INNER JOIN dbo.Transactions AS t
                    ON t.TransactionID = v.TransactionID

                WHERE EXISTS
                (
                    SELECT 1
                    FROM dbo.Accounts AS a
                    WHERE a.CustomerID = ?
                      AND
                      (
                          a.AccountID = v.FromAccountID
                          OR a.AccountID = v.ToAccountID
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

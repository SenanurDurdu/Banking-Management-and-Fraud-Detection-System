
from core import *


class FraudMixin:
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
                FROM FraudRules
                ORDER BY RuleID
                """
            ).fetchall()

        finally:
            con.close()

    def alerts(self):
        self.require_admin()
        con = connect()

        try:
            return con.cursor().execute(
                """
                SELECT
                    AlertID,
                    TransactionID,
                    RuleName,
                    TransactionType,
                    SenderCustomerID,
                    SenderCustomer,
                    SenderAccountNumber,
                    ReceiverCustomerID,
                    ReceiverCustomer,
                    ReceiverAccountNumber,
                    Amount,
                    AlertDescription,
                    RiskLevel,
                    ReviewStatus,
                    CreatedAt,
                    ReviewedAt
                FROM dbo.vw_FraudAlertDetails
                ORDER BY AlertID DESC
                """
            ).fetchall()

        finally:
            con.close()

    def scan_fraud(self):
        self.require_admin()
        con = connect()
        new_alerts = 0

        try:
            cur = con.cursor()

            rules = cur.execute(
                """
                SELECT
                    RuleID,
                    RuleName,
                    RuleType,
                    ThresholdValue,
                    TimeWindowMinutes
                FROM FraudRules
                WHERE IsActive = 1
                """
            ).fetchall()

            transactions = cur.execute(
                """
                SELECT
                    TransactionID,
                    FromAccountID,
                    ToAccountID,
                    Amount,
                    TransactionDate
                FROM Transactions
                WHERE Status = 'Completed'
                ORDER BY TransactionDate, TransactionID
                """
            ).fetchall()

            for tx in transactions:
                account_id = (
                    tx.FromAccountID
                    if tx.FromAccountID is not None
                    else tx.ToAccountID
                )

                for rule in rules:
                    suspicious = False
                    risk = "Medium"
                    description = ""

                    if rule.RuleType == "HighAmount":
                        if tx.Amount >= rule.ThresholdValue:
                            suspicious = True
                            risk = "High"

                            description = (
                                f"Amount {tx.Amount} reached "
                                f"threshold {rule.ThresholdValue}."
                            )

                    elif (
                        account_id is not None
                        and rule.RuleType in (
                            "Frequent",
                            "RepeatedAmount"
                        )
                    ):
                        query = """
                            SELECT COUNT(*)
                            FROM Transactions
                            WHERE TransactionDate >=
                                  DATEADD(MINUTE, -?, ?)
                              AND (
                                  TransactionDate < ?
                                  OR (
                                      TransactionDate = ?
                                      AND TransactionID <= ?
                                  )
                              )
                              AND Status = 'Completed'
                              AND (
                                  FromAccountID = ?
                                  OR ToAccountID = ?
                              )
                        """

                        params = [
                            int(rule.TimeWindowMinutes),
                            tx.TransactionDate,
                            tx.TransactionDate,
                            tx.TransactionDate,
                            tx.TransactionID,
                            account_id,
                            account_id
                        ]

                        if rule.RuleType == "RepeatedAmount":
                            query += " AND Amount = ?"
                            params.append(tx.Amount)

                        count = cur.execute(
                            query,
                            *params
                        ).fetchone()[0]

                        if count >= int(rule.ThresholdValue):
                            suspicious = True

                            description = (
                                f"{count} matching transactions "
                                f"in {rule.TimeWindowMinutes} minutes."
                            )

                            if count >= int(rule.ThresholdValue) + 3:
                                risk = "High"

                    if not suspicious:
                        continue

                    exists = cur.execute(
                        """
                        SELECT 1
                        FROM FraudAlerts
                        WHERE TransactionID = ?
                          AND RuleID = ?
                        """,
                        tx.TransactionID,
                        rule.RuleID
                    ).fetchone()

                    if exists:
                        continue

                    # Yeni fraud alarmını oluştur ve AlertID değerini al.
                    new_alert_id = cur.execute(
                        """
                        INSERT INTO FraudAlerts
                            (
                                TransactionID,
                                RuleID,
                                AlertDescription,
                                RiskLevel
                            )
                        OUTPUT INSERTED.AlertID
                        VALUES (?, ?, ?, ?)
                        """,
                        tx.TransactionID,
                        rule.RuleID,
                        description,
                        risk
                    ).fetchone()[0]

                    # Oluşturulan alarm için ayrı AuditLogs kaydı.
                    audit(
                        cur,
                        "FRAUD_ALERT",
                        "FraudAlert",
                        new_alert_id,
                        (
                            f"Alert created for TransactionID "
                            f"{tx.TransactionID}, "
                            f"Rule: {rule.RuleName}, "
                            f"Risk: {risk}"
                        )
                    )

                    new_alerts += 1

            audit(
                cur,
                "FRAUD_SCAN",
                "FraudAlert",
                None,
                f"{new_alerts} new alerts created"
            )

            con.commit()
            return new_alerts

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()


    def review(self, alert_id, status):
        self.require_admin()

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

        con = connect()

        try:
            cur = con.cursor()

            cur.execute(
                """
                UPDATE FraudAlerts
                SET
                    ReviewStatus = ?,
                    ReviewedAt = SYSDATETIME()
                WHERE AlertID = ?
                  AND ReviewStatus = 'Pending'
                """,
                status,
                alert_id
            )

            if cur.rowcount != 1:
                raise ValueError(
                    "Alert not found or already reviewed."
                )

            audit(
                cur,
                "REVIEW",
                "FraudAlert",
                alert_id,
                f"Alert marked as {status}"
            )

            con.commit()
            return True

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

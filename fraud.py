
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
                    a.AlertID,
                    a.TransactionID,
                    r.RuleName,
                    a.AlertDescription,
                    a.RiskLevel,
                    a.ReviewStatus,
                    a.CreatedAt
                FROM FraudAlerts a
                JOIN FraudRules r
                    ON r.RuleID = a.RuleID
                ORDER BY a.AlertID DESC
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

                    cur.execute(
                        """
                        INSERT INTO FraudAlerts
                            (
                                TransactionID,
                                RuleID,
                                AlertDescription,
                                RiskLevel
                            )
                        VALUES (?, ?, ?, ?)
                        """,
                        tx.TransactionID,
                        rule.RuleID,
                        description,
                        risk
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

        if status not in (
            "Reviewed",
            "FalsePositive"
        ):
            raise ValueError(
                "Invalid review status."
            )

        con = connect()

        try:
            cur = con.cursor()

            cur.execute(
                """
                UPDATE FraudAlerts
                SET ReviewStatus = ?,
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
                status
            )

            con.commit()

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()


-- ============================================================
-- BANKING MANAGEMENT & FRAUD DETECTION SYSTEM
-- FILE: 06_fraud_procedures.sql
-- PURPOSE: Fraud detection stored procedure
--
-- RUN AFTER:
--   01_schema.sql
--   02_constraints_indexes.sql
--   03_seed_fraud_rules.sql
--   04_views.sql
--   05_transaction_procedures.sql
--
-- IMPORTANT:
--   Only active Admin users can run the scan.
--   Existing alerts are preserved.
--   Duplicate alerts are prevented.
--   No customer or transaction records are deleted.
-- ============================================================

USE BankingFraudDB;
GO


-- ============================================================
-- 1. FRAUD SCANNING PROCEDURE
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_ScanFraud
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @NewAlerts INT = 0;
    DECLARE @LockResult INT;

    DECLARE @CreatedAlerts TABLE
    (
        AlertID BIGINT,
        TransactionID BIGINT,
        RuleID INT,
        RiskLevel VARCHAR(10)
    );

    -- ========================================================
    -- VALIDATE USER
    -- ========================================================

    IF @UserID IS NULL OR @UserID <= 0
        THROW 51030, 'Invalid UserID.', 1;

    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.Users
        WHERE UserID = @UserID
          AND Role = 'Admin'
          AND IsActive = 1
    )
        THROW 51031, 'Admin access required.', 1;

    BEGIN TRY

        BEGIN TRANSACTION;

        -- ====================================================
        -- PREVENT CONCURRENT FRAUD SCANS
        -- ====================================================

        EXEC @LockResult = sys.sp_getapplock
            @Resource = 'BankingFraudDB_FraudScan',
            @LockMode = 'Exclusive',
            @LockOwner = 'Transaction',
            @LockTimeout = 10000;

        IF @LockResult < 0
            THROW 51032,
                  'Could not acquire fraud scan lock.',
                  1;

        -- ====================================================
        -- FIND TRANSACTIONS MATCHING ACTIVE FRAUD RULES
        -- ====================================================

        ;WITH TransactionCandidates AS
        (
            SELECT
                t.TransactionID,
                t.FromAccountID,
                t.ToAccountID,
                t.Amount,
                t.TransactionDate,

                COALESCE(
                    t.FromAccountID,
                    t.ToAccountID
                ) AS EvaluatedAccountID

            FROM dbo.Transactions AS t

            WHERE t.Status = 'Completed'
        ),

        RuleMatches AS
        (
            SELECT
                t.TransactionID,
                r.RuleID,
                r.RuleName,
                r.RuleType,
                r.ThresholdValue,
                r.TimeWindowMinutes,
                t.Amount,
                counts.MatchCount,

                CASE
                    WHEN r.RuleType = 'HighAmount'
                         AND t.Amount >= r.ThresholdValue
                    THEN 1

                    WHEN r.RuleType IN
                         (
                             'Frequent',
                             'RepeatedAmount'
                         )
                         AND t.EvaluatedAccountID IS NOT NULL
                         AND r.TimeWindowMinutes > 0
                         AND counts.MatchCount >= r.ThresholdValue
                    THEN 1

                    ELSE 0
                END AS IsSuspicious

            FROM TransactionCandidates AS t

            CROSS JOIN dbo.FraudRules AS r

            OUTER APPLY
            (
                SELECT
                    COUNT_BIG(*) AS MatchCount

                FROM dbo.Transactions AS p

                WHERE r.RuleType IN
                      (
                          'Frequent',
                          'RepeatedAmount'
                      )

                  AND r.TimeWindowMinutes > 0

                  AND t.EvaluatedAccountID IS NOT NULL

                  AND p.Status = 'Completed'

                  AND p.TransactionDate >= DATEADD(
                      MINUTE,
                      -r.TimeWindowMinutes,
                      t.TransactionDate
                  )

                  AND
                  (
                      p.TransactionDate < t.TransactionDate

                      OR
                      (
                          p.TransactionDate = t.TransactionDate
                          AND p.TransactionID <= t.TransactionID
                      )
                  )

                  AND
                  (
                      p.FromAccountID = t.EvaluatedAccountID
                      OR p.ToAccountID = t.EvaluatedAccountID
                  )

                  AND
                  (
                      r.RuleType = 'Frequent'

                      OR
                      (
                          r.RuleType = 'RepeatedAmount'
                          AND p.Amount = t.Amount
                      )
                  )

            ) AS counts

            WHERE r.IsActive = 1

              AND r.RuleType IN
              (
                  'HighAmount',
                  'Frequent',
                  'RepeatedAmount'
              )
        ),

        SuspiciousTransactions AS
        (
            SELECT
                m.TransactionID,
                m.RuleID,

                CASE
                    WHEN m.RuleType = 'HighAmount'
                    THEN 'High'

                    WHEN m.MatchCount >= m.ThresholdValue + 3
                    THEN 'High'

                    ELSE 'Medium'
                END AS RiskLevel,

                CAST
                (
                    CASE
                        WHEN m.RuleType = 'HighAmount'
                        THEN CONCAT(
                            'Amount ',
                            CONVERT(VARCHAR(40), m.Amount),
                            ' reached threshold ',
                            CONVERT(VARCHAR(40), m.ThresholdValue),
                            '.'
                        )

                        ELSE CONCAT(
                            m.MatchCount,
                            ' matching transactions in ',
                            m.TimeWindowMinutes,
                            ' minutes.'
                        )
                    END
                    AS NVARCHAR(500)
                ) AS AlertDescription

            FROM RuleMatches AS m

            WHERE m.IsSuspicious = 1
        )

        -- ====================================================
        -- INSERT NEW FRAUD ALERTS
        -- ====================================================

        INSERT INTO dbo.FraudAlerts
        (
            TransactionID,
            RuleID,
            AlertDescription,
            RiskLevel
        )

        OUTPUT
            INSERTED.AlertID,
            INSERTED.TransactionID,
            INSERTED.RuleID,
            INSERTED.RiskLevel

        INTO @CreatedAlerts
        (
            AlertID,
            TransactionID,
            RuleID,
            RiskLevel
        )

        SELECT
            s.TransactionID,
            s.RuleID,
            s.AlertDescription,
            s.RiskLevel

        FROM SuspiciousTransactions AS s

        WHERE NOT EXISTS
        (
            SELECT 1
            FROM dbo.FraudAlerts AS fa
                WITH (UPDLOCK, HOLDLOCK)

            WHERE fa.TransactionID = s.TransactionID
              AND fa.RuleID = s.RuleID
        );

        -- ====================================================
        -- COUNT NEW ALERTS
        -- ====================================================

        SELECT
            @NewAlerts = COUNT(*)
        FROM @CreatedAlerts;

        -- ====================================================
        -- AUDIT EACH NEW FRAUD ALERT
        -- ====================================================

        INSERT INTO dbo.AuditLogs
        (
            ActionType,
            EntityName,
            EntityID,
            Description,
            UserID
        )

        SELECT
            'FRAUD_ALERT',
            'FraudAlert',
            ca.AlertID,

            CONCAT(
                'Alert created for TransactionID ',
                ca.TransactionID,
                ', Rule: ',
                r.RuleName,
                ', Risk: ',
                ca.RiskLevel
            ),

            @UserID

        FROM @CreatedAlerts AS ca

        INNER JOIN dbo.FraudRules AS r
            ON r.RuleID = ca.RuleID;

        -- ====================================================
        -- AUDIT THE FRAUD SCAN
        -- ====================================================

        INSERT INTO dbo.AuditLogs
        (
            ActionType,
            EntityName,
            EntityID,
            Description,
            UserID
        )

        VALUES
        (
            'FRAUD_SCAN',
            'FraudAlert',
            NULL,

            CONCAT(
                @NewAlerts,
                ' new alerts created'
            ),

            @UserID
        );

        -- ====================================================
        -- COMMIT
        -- ====================================================

        COMMIT TRANSACTION;

        SELECT
            @NewAlerts AS NewAlerts;

    END TRY

    BEGIN CATCH

        IF XACT_STATE() <> 0
            ROLLBACK TRANSACTION;

        THROW;

    END CATCH;

END;
GO


-- ============================================================
-- 2. VERIFY PROCEDURE
-- ============================================================

SELECT
    p.name AS ProcedureName,
    p.create_date AS CreatedAt,
    p.modify_date AS LastModified

FROM sys.procedures AS p

WHERE p.object_id =
    OBJECT_ID(N'dbo.sp_ScanFraud');
GO


-- ============================================================
-- 3. VERIFY PROCEDURE PARAMETERS
-- ============================================================

SELECT
    OBJECT_NAME(p.object_id) AS ProcedureName,
    p.parameter_id AS ParameterOrder,
    p.name AS ParameterName,
    TYPE_NAME(p.user_type_id) AS DataType

FROM sys.parameters AS p

WHERE p.object_id =
    OBJECT_ID(N'dbo.sp_ScanFraud')

ORDER BY p.parameter_id;
GO


-- ============================================================
-- 4. FINISH
-- ============================================================

PRINT '============================================';
PRINT '06_fraud_procedures.sql completed.';
PRINT 'sp_ScanFraud procedure checked.';
PRINT 'No fraud scan was executed.';
PRINT 'Existing records were preserved.';
PRINT '============================================';
GO

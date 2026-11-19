
USE BankingFraudDB;
GO

-- ============================================================
-- BANKING MANAGEMENT & FRAUD DETECTION SYSTEM
-- FILE: 10_credit_card_fraud.sql
-- PURPOSE: Credit card fraud detection integration
-- ============================================================

SET NOCOUNT ON;
SET XACT_ABORT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET ARITHABORT ON;
SET NUMERIC_ROUNDABORT OFF;
GO


-- ============================================================
-- 1. ADD CREDIT CARD TRANSACTION REFERENCE
-- ============================================================

IF COL_LENGTH(
    'dbo.FraudAlerts',
    'CardTransactionID'
) IS NULL
BEGIN

    ALTER TABLE dbo.FraudAlerts
    ADD CardTransactionID BIGINT NULL;

END;
GO


-- ============================================================
-- 2. UPDATE FRAUD ALERT CONSTRAINTS
-- ============================================================

BEGIN TRANSACTION;

IF EXISTS
(
    SELECT 1
    FROM sys.key_constraints
    WHERE name = 'UQ_Alert'
      AND parent_object_id =
          OBJECT_ID('dbo.FraudAlerts')
)
BEGIN

    ALTER TABLE dbo.FraudAlerts
    DROP CONSTRAINT UQ_Alert;

END;


IF EXISTS
(
    SELECT 1
    FROM sys.columns
    WHERE object_id =
          OBJECT_ID('dbo.FraudAlerts')
      AND name = 'TransactionID'
      AND is_nullable = 0
)
BEGIN

    IF EXISTS
    (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'IX_FraudAlerts_TransactionID'
          AND object_id =
              OBJECT_ID('dbo.FraudAlerts')
    )
    BEGIN

        DROP INDEX IX_FraudAlerts_TransactionID
        ON dbo.FraudAlerts;

    END;

    ALTER TABLE dbo.FraudAlerts
    ALTER COLUMN TransactionID BIGINT NULL;

END;


-- ============================================================
-- 3. CREDIT CARD FOREIGN KEY
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.foreign_keys
    WHERE name = 'FK_FraudAlerts_CardTransactions'
      AND parent_object_id =
          OBJECT_ID('dbo.FraudAlerts')
)
BEGIN

    ALTER TABLE dbo.FraudAlerts

    WITH CHECK ADD CONSTRAINT
        FK_FraudAlerts_CardTransactions

    FOREIGN KEY (CardTransactionID)

    REFERENCES dbo.CreditCardTransactions
    (
        CardTransactionID
    );

END;


-- ============================================================
-- 4. TRANSACTION REFERENCE VALIDATION
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.check_constraints
    WHERE name = 'CK_FraudAlerts_TransactionReference'
      AND parent_object_id =
          OBJECT_ID('dbo.FraudAlerts')
)
BEGIN

    ALTER TABLE dbo.FraudAlerts

    WITH CHECK ADD CONSTRAINT
        CK_FraudAlerts_TransactionReference

    CHECK
    (
        (
            TransactionID IS NOT NULL
            AND CardTransactionID IS NULL
        )

        OR

        (
            TransactionID IS NULL
            AND CardTransactionID IS NOT NULL
        )
    );

END;


-- ============================================================
-- 5. FRAUD ALERT INDEXES
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_FraudAlerts_TransactionID'
      AND object_id =
          OBJECT_ID('dbo.FraudAlerts')
)
BEGIN

    CREATE INDEX IX_FraudAlerts_TransactionID

    ON dbo.FraudAlerts
    (
        TransactionID
    );

END;


IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = 'UX_FraudAlerts_BankRule'
      AND object_id =
          OBJECT_ID('dbo.FraudAlerts')
)
BEGIN

    CREATE UNIQUE INDEX UX_FraudAlerts_BankRule

    ON dbo.FraudAlerts
    (
        TransactionID,
        RuleID
    )

    WHERE TransactionID IS NOT NULL;

END;


IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = 'UX_FraudAlerts_CardRule'
      AND object_id =
          OBJECT_ID('dbo.FraudAlerts')
)
BEGIN

    CREATE UNIQUE INDEX UX_FraudAlerts_CardRule

    ON dbo.FraudAlerts
    (
        CardTransactionID,
        RuleID
    )

    WHERE CardTransactionID IS NOT NULL;

END;

COMMIT TRANSACTION;
GO


-- ============================================================
-- 6. UNIFIED FRAUD TRANSACTION VIEW
-- ============================================================

CREATE OR ALTER VIEW dbo.vw_FraudTransactions
AS

SELECT

    CAST('Bank' AS VARCHAR(20))
        AS TransactionSource,

    t.TransactionID,

    CAST(NULL AS BIGINT)
        AS CardTransactionID,

    ct.CreditCardID,

    CASE

        WHEN ct.TransactionType = 'CashAdvance'
        THEN 'CashAdvance'

        WHEN ct.TransactionType = 'Payment'
        THEN 'CardPayment'

        ELSE t.TransactionType

    END AS TransactionType,

    t.FromAccountID,
    t.ToAccountID,

    COALESCE(
        t.FromAccountID,
        t.ToAccountID
    ) AS AffectedAccountID,

    t.Amount,
    t.TransactionDate,

    CAST(
        t.Description AS NVARCHAR(500)
    ) AS TransactionDescription,

    t.Status AS TransactionStatus

FROM dbo.Transactions AS t

LEFT JOIN dbo.CreditCardTransactions AS ct

    ON ct.BankTransactionID =
       t.TransactionID


UNION ALL


SELECT

    CAST('CreditCard' AS VARCHAR(20)),

    CAST(NULL AS BIGINT),

    ct.CardTransactionID,

    cc.CreditCardID,

    ct.TransactionType,

    cc.LinkedAccountID,

    CAST(NULL AS INT),

    cc.LinkedAccountID,

    ct.Amount,

    ct.CreatedAt,

    ct.Description,

    ct.TransactionStatus

FROM dbo.CreditCardTransactions AS ct

INNER JOIN dbo.CreditCards AS cc

    ON cc.CreditCardID =
       ct.CreditCardID

WHERE ct.BankTransactionID IS NULL

  AND ct.TransactionType = 'Purchase';
GO


-- ============================================================
-- 7. CREDIT CARD FRAUD SCANNING PROCEDURE
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_ScanCreditCardFraud

    @UserID INT

AS
BEGIN

    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    SET ANSI_PADDING ON;
    SET ANSI_WARNINGS ON;
    SET CONCAT_NULL_YIELDS_NULL ON;
    SET ARITHABORT ON;
    SET NUMERIC_ROUNDABORT OFF;


    DECLARE @NewAlerts INT = 0;
    DECLARE @LockResult INT;

    DECLARE @CreatedAlerts TABLE
    (
        AlertID BIGINT,
        CardTransactionID BIGINT,
        RuleID INT,
        RiskLevel VARCHAR(10)
    );


    -- ========================================================
    -- VALIDATE ADMIN USER
    -- ========================================================

    IF @UserID IS NULL OR @UserID <= 0
    BEGIN

        RAISERROR(
            'Invalid UserID.',
            16,
            1
        );

        RETURN;

    END;


    IF NOT EXISTS
    (
        SELECT 1

        FROM dbo.Users

        WHERE UserID = @UserID
          AND Role = 'Admin'
          AND IsActive = 1
    )
    BEGIN

        RAISERROR(
            'Admin access required.',
            16,
            1
        );

        RETURN;

    END;


    BEGIN TRANSACTION;


    -- ========================================================
    -- PREVENT CONCURRENT FRAUD SCANS
    -- ========================================================

    EXEC @LockResult = sys.sp_getapplock

        @Resource =
            'BankingFraudDB_CreditCardFraudScan',

        @LockMode = 'Exclusive',

        @LockOwner = 'Transaction',

        @LockTimeout = 10000;


    IF @LockResult < 0
    BEGIN

        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        RAISERROR(
            'Could not acquire fraud scan lock.',
            16,
            1
        );

        RETURN;

    END;


    -- ========================================================
    -- FIND COMPLETED CREDIT CARD PURCHASES
    -- ========================================================

    ;WITH CardCandidates AS
    (
        SELECT

            CardTransactionID,
            CreditCardID,
            Amount,
            CreatedAt

        FROM dbo.CreditCardTransactions

        WHERE TransactionStatus = 'Completed'
          AND TransactionType = 'Purchase'
          AND BankTransactionID IS NULL
    ),


    -- ========================================================
    -- MATCH ACTIVE FRAUD RULES
    -- ========================================================

    RuleMatches AS
    (
        SELECT

            t.CardTransactionID,

            r.RuleID,
            r.RuleName,
            r.RuleType,
            r.ThresholdValue,
            r.TimeWindowMinutes,

            t.Amount,

            counts.MatchCount,

            CASE

                WHEN r.RuleType = 'HighAmount'

                     AND t.Amount >=
                         r.ThresholdValue

                THEN 1


                WHEN r.RuleType IN
                (
                    'Frequent',
                    'RepeatedAmount'
                )

                AND r.TimeWindowMinutes > 0

                AND counts.MatchCount >=
                    r.ThresholdValue

                THEN 1


                ELSE 0

            END AS IsSuspicious

        FROM CardCandidates AS t

        CROSS JOIN dbo.FraudRules AS r

        OUTER APPLY
        (
            SELECT

                COUNT_BIG(*) AS MatchCount

            FROM CardCandidates AS p

            WHERE r.RuleType IN
            (
                'Frequent',
                'RepeatedAmount'
            )

              AND r.TimeWindowMinutes > 0

              AND p.CreditCardID =
                  t.CreditCardID

              AND p.CreatedAt >= DATEADD
              (
                  MINUTE,
                  -r.TimeWindowMinutes,
                  t.CreatedAt
              )

              AND
              (
                  p.CreatedAt < t.CreatedAt

                  OR

                  (
                      p.CreatedAt = t.CreatedAt

                      AND p.CardTransactionID <=
                          t.CardTransactionID
                  )
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


    -- ========================================================
    -- DETERMINE RISK LEVEL
    -- ========================================================

    SuspiciousTransactions AS
    (
        SELECT

            CardTransactionID,
            RuleID,

            CASE

                WHEN RuleType = 'HighAmount'
                THEN 'High'

                WHEN MatchCount >=
                     ThresholdValue + 3
                THEN 'High'

                ELSE 'Medium'

            END AS RiskLevel,


            CAST
            (
                CASE

                    WHEN RuleType = 'HighAmount'

                    THEN CONCAT
                    (
                        'Credit card purchase amount ',
                        Amount,
                        ' reached threshold ',
                        ThresholdValue,
                        '.'
                    )

                    ELSE CONCAT
                    (
                        MatchCount,
                        ' matching credit card purchases in ',
                        TimeWindowMinutes,
                        ' minutes.'
                    )

                END

                AS NVARCHAR(500)

            ) AS AlertDescription

        FROM RuleMatches

        WHERE IsSuspicious = 1
    )


    -- ========================================================
    -- INSERT FRAUD ALERTS
    -- ========================================================

    INSERT INTO dbo.FraudAlerts
    (
        TransactionID,
        CardTransactionID,
        RuleID,
        AlertDescription,
        RiskLevel
    )

    OUTPUT

        INSERTED.AlertID,
        INSERTED.CardTransactionID,
        INSERTED.RuleID,
        INSERTED.RiskLevel

    INTO @CreatedAlerts
    (
        AlertID,
        CardTransactionID,
        RuleID,
        RiskLevel
    )

    SELECT

        NULL,
        s.CardTransactionID,
        s.RuleID,
        s.AlertDescription,
        s.RiskLevel

    FROM SuspiciousTransactions AS s

    WHERE NOT EXISTS
    (
        SELECT 1

        FROM dbo.FraudAlerts AS fa
            WITH (UPDLOCK, HOLDLOCK)

        WHERE fa.CardTransactionID =
              s.CardTransactionID

          AND fa.RuleID = s.RuleID
    );


    -- ========================================================
    -- COUNT NEW FRAUD ALERTS
    -- ========================================================

    SELECT

        @NewAlerts = COUNT(*)

    FROM @CreatedAlerts;


    -- ========================================================
    -- AUDIT NEW FRAUD ALERTS
    -- ========================================================

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

        CONCAT
        (
            'Credit card fraud alert. ',
            'CardTransactionID=',
            ca.CardTransactionID,
            ', Rule=',
            r.RuleName,
            ', Risk=',
            ca.RiskLevel
        ),

        @UserID

    FROM @CreatedAlerts AS ca

    INNER JOIN dbo.FraudRules AS r

        ON r.RuleID = ca.RuleID;


    -- ========================================================
    -- AUDIT FRAUD SCAN
    -- ========================================================

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
        'CREDIT_CARD_FRAUD_SCAN',

        'FraudAlert',

        NULL,

        CONCAT
        (
            @NewAlerts,
            ' new credit card fraud alerts created.'
        ),

        @UserID
    );


    -- ========================================================
    -- COMPLETE FRAUD SCAN
    -- ========================================================

    COMMIT TRANSACTION;


    SELECT

        @NewAlerts AS NewAlerts;

END;
GO


-- ============================================================
-- 8. FRAUD ALERT DETAILS VIEW
-- ============================================================

CREATE OR ALTER VIEW dbo.vw_FraudAlertDetails
AS

SELECT

    fa.AlertID,

    fa.TransactionID,

    fr.RuleName,

    fr.RuleType,

    t.TransactionType,


    sender.CustomerID AS SenderCustomerID,

    CASE

        WHEN sender.CustomerID IS NOT NULL

        THEN sender.FirstName + N' ' +
             sender.LastName

        ELSE NULL

    END AS SenderCustomer,

    source.AccountNumber
        AS SenderAccountNumber,


    receiver.CustomerID AS ReceiverCustomerID,

    CASE

        WHEN receiver.CustomerID IS NOT NULL

        THEN receiver.FirstName + N' ' +
             receiver.LastName

        ELSE NULL

    END AS ReceiverCustomer,

    target.AccountNumber
        AS ReceiverAccountNumber,


    t.Amount,

    t.TransactionDate,

    fa.AlertDescription,

    fa.RiskLevel,

    fa.ReviewStatus,

    fa.CreatedAt,

    fa.ReviewedAt,


    fa.CardTransactionID,

    t.CreditCardID,

    t.TransactionSource,

    t.TransactionDescription,

    t.AffectedAccountID,


    CASE

        WHEN fa.CardTransactionID IS NOT NULL

        THEN CONCAT
        (
            'CC-',
            fa.CardTransactionID
        )

        ELSE CONVERT
        (
            VARCHAR(30),
            fa.TransactionID
        )

    END AS TransactionReference


FROM dbo.FraudAlerts AS fa


INNER JOIN dbo.FraudRules AS fr

    ON fr.RuleID = fa.RuleID


INNER JOIN dbo.vw_FraudTransactions AS t

    ON
    (
        fa.TransactionID IS NOT NULL

        AND t.TransactionID =
            fa.TransactionID
    )

    OR

    (
        fa.CardTransactionID IS NOT NULL

        AND t.CardTransactionID =
            fa.CardTransactionID
    )


LEFT JOIN dbo.Accounts AS source

    ON source.AccountID =
       t.FromAccountID


LEFT JOIN dbo.Customers AS sender

    ON sender.CustomerID =
       source.CustomerID


LEFT JOIN dbo.Accounts AS target

    ON target.AccountID =
       t.ToAccountID


LEFT JOIN dbo.Customers AS receiver

    ON receiver.CustomerID =
       target.CustomerID;
GO


-- ============================================================
-- 9. SUSPICIOUS TRANSACTIONS VIEW
-- ============================================================

CREATE OR ALTER VIEW dbo.vw_SuspiciousTransactions
AS

SELECT

    v.AlertID,

    v.TransactionID,

    v.RuleName,

    v.RuleType,

    v.TransactionType,

    v.Amount,

    v.TransactionDate,

    v.RiskLevel,

    v.ReviewStatus,

    v.CreatedAt,

    v.ReviewedAt,

    fa.ReviewedByUserID,

    fa.ReviewNote,

    v.CardTransactionID,

    v.TransactionSource,

    v.TransactionReference


FROM dbo.vw_FraudAlertDetails AS v


INNER JOIN dbo.FraudAlerts AS fa

    ON fa.AlertID = v.AlertID;
GO


-- ============================================================
-- 10. CUSTOMER RISK SUMMARY VIEW
-- ============================================================

CREATE OR ALTER VIEW dbo.vw_CustomerRiskSummary
AS

WITH LinkedCustomers AS
(
    SELECT

        AlertID,
        SenderCustomerID AS CustomerID,
        RiskLevel,
        ReviewStatus

    FROM dbo.vw_FraudAlertDetails

    WHERE SenderCustomerID IS NOT NULL


    UNION


    SELECT

        AlertID,
        ReceiverCustomerID,
        RiskLevel,
        ReviewStatus

    FROM dbo.vw_FraudAlertDetails

    WHERE ReceiverCustomerID IS NOT NULL
)


SELECT

    c.CustomerID,

    c.FirstName,

    c.LastName,


    COUNT(lc.AlertID)
        AS AlertCount,


    SUM
    (
        CASE

            WHEN lc.RiskLevel = 'High'
            THEN 1

            ELSE 0

        END

    ) AS HighRiskAlerts,


    SUM
    (
        CASE

            WHEN lc.ReviewStatus = 'Pending'
            THEN 1

            ELSE 0

        END

    ) AS PendingAlerts


FROM dbo.Customers AS c


LEFT JOIN LinkedCustomers AS lc

    ON lc.CustomerID = c.CustomerID


GROUP BY

    c.CustomerID,

    c.FirstName,

    c.LastName;
GO


-- ============================================================
-- 11. CUSTOMER FRAUD REVIEWS VIEW
-- ============================================================

CREATE OR ALTER VIEW dbo.vw_CustomerFraudReviews
AS

SELECT

    fa.AlertID,

    fa.TransactionID,

    t.TransactionType,

    t.Amount,

    fr.RuleName,

    fa.RiskLevel,

    fa.ReviewStatus,

    fa.ReviewNote,

    fa.ReviewedAt,

    fa.ReviewedByUserID,

    t.FromAccountID,

    t.ToAccountID,

    fa.CardTransactionID,

    t.TransactionSource,

    t.TransactionDescription,


    CASE

        WHEN fa.CardTransactionID IS NOT NULL

        THEN CONCAT
        (
            'CC-',
            fa.CardTransactionID
        )

        ELSE CONVERT
        (
            VARCHAR(30),
            fa.TransactionID
        )

    END AS TransactionReference


FROM dbo.FraudAlerts AS fa


INNER JOIN dbo.FraudRules AS fr

    ON fr.RuleID = fa.RuleID


INNER JOIN dbo.vw_FraudTransactions AS t

    ON
    (
        fa.TransactionID IS NOT NULL

        AND t.TransactionID =
            fa.TransactionID
    )

    OR

    (
        fa.CardTransactionID IS NOT NULL

        AND t.CardTransactionID =
            fa.CardTransactionID
    )


WHERE fa.ReviewStatus <> 'Pending';
GO


-- ============================================================
-- 12. VERIFY FRAUD ALERT COLUMNS
-- ============================================================

SELECT

    COLUMN_NAME,

    DATA_TYPE,

    IS_NULLABLE

FROM INFORMATION_SCHEMA.COLUMNS

WHERE TABLE_SCHEMA = 'dbo'

  AND TABLE_NAME = 'FraudAlerts'

  AND COLUMN_NAME IN
  (
      'TransactionID',
      'CardTransactionID'
  )

ORDER BY COLUMN_NAME;
GO


-- ============================================================
-- 13. VERIFY FRAUD PROCEDURES
-- ============================================================

SELECT

    name AS ProcedureName,

    create_date AS CreatedAt,

    modify_date AS LastModified

FROM sys.procedures

WHERE schema_id = SCHEMA_ID('dbo')

  AND name IN
  (
      'sp_ScanFraud',
      'sp_ScanCreditCardFraud'
  )

ORDER BY name;
GO


-- ============================================================
-- 14. VERIFY FRAUD VIEWS
-- ============================================================

SELECT

    name AS ViewName

FROM sys.views

WHERE schema_id = SCHEMA_ID('dbo')

  AND name IN
  (
      'vw_FraudTransactions',
      'vw_FraudAlertDetails',
      'vw_SuspiciousTransactions',
      'vw_CustomerRiskSummary',
      'vw_CustomerFraudReviews'
  )

ORDER BY name;
GO


-- ============================================================
-- 15. VERIFY FRAUD ALERTS
-- ============================================================

SELECT

    AlertID,

    TransactionID,

    CardTransactionID,

    RuleID,

    RiskLevel,

    ReviewStatus

FROM dbo.FraudAlerts

ORDER BY AlertID DESC;
GO


-- ============================================================
-- 16. VERIFY CREDIT CARD TRANSACTIONS
-- ============================================================

SELECT TOP (20)

    TransactionSource,

    TransactionID,

    CardTransactionID,

    CreditCardID,

    TransactionType,

    Amount,

    TransactionStatus

FROM dbo.vw_FraudTransactions

ORDER BY TransactionDate DESC;
GO


-- ============================================================
-- 17. FINISH
-- ============================================================

PRINT '============================================';
PRINT '10_credit_card_fraud.sql execution finished.';
PRINT 'Review verification results and error messages.';
PRINT 'No fraud scan was executed.';
PRINT '============================================';
GO

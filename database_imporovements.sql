
-- ============================================================
-- BANKING MANAGEMENT AND FRAUD DETECTION SYSTEM
-- DATABASE IMPROVEMENTS - M1
--
-- TARGET DATABASE: BankingFraudDB
--
-- Existing customer, account and transaction records
-- are not deleted or reset.
-- ============================================================

USE BankingFraudDB;
GO

SELECT DB_NAME() AS TargetDatabase;
GO


-- ============================================================
-- 1. AUDIT LOGS - USER ID
-- ============================================================

-- Record which user performed an action.
-- NULL is allowed for historical/system-generated records.

IF COL_LENGTH(N'dbo.AuditLogs', N'UserID') IS NULL
BEGIN
    ALTER TABLE dbo.AuditLogs
    ADD UserID INT NULL;
END;
GO

-- Foreign Key: AuditLogs -> Users

IF NOT EXISTS
(
    SELECT 1
    FROM sys.foreign_keys
    WHERE name = N'FK_AuditLogs_Users'
      AND parent_object_id = OBJECT_ID(N'dbo.AuditLogs')
)
BEGIN
    ALTER TABLE dbo.AuditLogs
    WITH CHECK ADD CONSTRAINT FK_AuditLogs_Users
    FOREIGN KEY (UserID)
    REFERENCES dbo.Users(UserID);
END;
GO


-- ============================================================
-- 2. FRAUD ALERTS - REVIEW INFORMATION
-- ============================================================

-- Admin who reviewed the alert.

IF COL_LENGTH(
    N'dbo.FraudAlerts',
    N'ReviewedByUserID'
) IS NULL
BEGIN
    ALTER TABLE dbo.FraudAlerts
    ADD ReviewedByUserID INT NULL;
END;
GO

-- Optional review note.

IF COL_LENGTH(
    N'dbo.FraudAlerts',
    N'ReviewNote'
) IS NULL
BEGIN
    ALTER TABLE dbo.FraudAlerts
    ADD ReviewNote NVARCHAR(500) NULL;
END;
GO

-- Foreign Key: FraudAlerts -> Users

IF NOT EXISTS
(
    SELECT 1
    FROM sys.foreign_keys
    WHERE name = N'FK_FraudAlerts_ReviewedBy'
      AND parent_object_id = OBJECT_ID(N'dbo.FraudAlerts')
)
BEGIN
    ALTER TABLE dbo.FraudAlerts
    WITH CHECK ADD CONSTRAINT FK_FraudAlerts_ReviewedBy
    FOREIGN KEY (ReviewedByUserID)
    REFERENCES dbo.Users(UserID);
END;
GO


-- ============================================================
-- 3. DATA QUALITY CHECKS
-- ============================================================

-- These queries display records that do not comply
-- with the proposed new constraints.
-- No data is modified.

-- Invalid transaction account relationships.

SELECT
    TransactionID,
    TransactionType,
    FromAccountID,
    ToAccountID
FROM dbo.Transactions
WHERE NOT
(
    (
        TransactionType = 'Deposit'
        AND FromAccountID IS NULL
        AND ToAccountID IS NOT NULL
    )
    OR
    (
        TransactionType = 'Withdrawal'
        AND FromAccountID IS NOT NULL
        AND ToAccountID IS NULL
    )
    OR
    (
        TransactionType = 'Transfer'
        AND FromAccountID IS NOT NULL
        AND ToAccountID IS NOT NULL
        AND FromAccountID <> ToAccountID
    )
);
GO

-- Invalid transaction statuses.

SELECT DISTINCT
    Status AS UnexpectedStatus
FROM dbo.Transactions
WHERE Status NOT IN
(
    'Completed',
    'Pending',
    'Blocked',
    'Failed'
);
GO

-- Invalid fraud risk levels.

SELECT DISTINCT
    RiskLevel AS UnexpectedRisk
FROM dbo.FraudAlerts
WHERE RiskLevel NOT IN
(
    'Medium',
    'High'
);
GO

-- Invalid fraud review statuses.

SELECT DISTINCT
    ReviewStatus AS UnexpectedReviewStatus
FROM dbo.FraudAlerts
WHERE ReviewStatus NOT IN
(
    'Pending',
    'Reviewed',
    'FalsePositive',
    'ConfirmedFraud'
);
GO


-- ============================================================
-- 4. TRANSACTIONS - ACCOUNT RELATIONSHIP CHECK
-- ============================================================

-- Deposit:
--   FromAccountID = NULL
--   ToAccountID   = NOT NULL
--
-- Withdrawal:
--   FromAccountID = NOT NULL
--   ToAccountID   = NULL
--
-- Transfer:
--   Both accounts must exist.
--   Source and destination must be different.
--
-- If existing records violate this rule,
-- the constraint is skipped instead of deleting data.

IF NOT EXISTS
(
    SELECT 1
    FROM sys.check_constraints
    WHERE name = N'CK_Transactions_Shape'
      AND parent_object_id =
          OBJECT_ID(N'dbo.Transactions')
)
BEGIN
    IF EXISTS
    (
        SELECT 1
        FROM dbo.Transactions
        WHERE NOT
        (
            (
                TransactionType = 'Deposit'
                AND FromAccountID IS NULL
                AND ToAccountID IS NOT NULL
            )
            OR
            (
                TransactionType = 'Withdrawal'
                AND FromAccountID IS NOT NULL
                AND ToAccountID IS NULL
            )
            OR
            (
                TransactionType = 'Transfer'
                AND FromAccountID IS NOT NULL
                AND ToAccountID IS NOT NULL
                AND FromAccountID <> ToAccountID
            )
        )
    )
    BEGIN
        PRINT 'WARNING: CK_Transactions_Shape skipped.';
        PRINT 'Existing transactions violate the rule.';
    END
    ELSE
    BEGIN
        ALTER TABLE dbo.Transactions
        WITH CHECK ADD CONSTRAINT CK_Transactions_Shape
        CHECK
        (
            (
                TransactionType = 'Deposit'
                AND FromAccountID IS NULL
                AND ToAccountID IS NOT NULL
            )
            OR
            (
                TransactionType = 'Withdrawal'
                AND FromAccountID IS NOT NULL
                AND ToAccountID IS NULL
            )
            OR
            (
                TransactionType = 'Transfer'
                AND FromAccountID IS NOT NULL
                AND ToAccountID IS NOT NULL
                AND FromAccountID <> ToAccountID
            )
        );

        PRINT 'CK_Transactions_Shape created.';
    END;
END;
GO


-- ============================================================
-- 5. TRANSACTIONS - STATUS CHECK
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.check_constraints
    WHERE name = N'CK_Transactions_Status'
      AND parent_object_id =
          OBJECT_ID(N'dbo.Transactions')
)
BEGIN
    IF EXISTS
    (
        SELECT 1
        FROM dbo.Transactions
        WHERE Status NOT IN
        (
            'Completed',
            'Pending',
            'Blocked',
            'Failed'
        )
    )
    BEGIN
        PRINT 'WARNING: CK_Transactions_Status skipped.';
    END
    ELSE
    BEGIN
        ALTER TABLE dbo.Transactions
        WITH CHECK ADD CONSTRAINT CK_Transactions_Status
        CHECK
        (
            Status IN
            (
                'Completed',
                'Pending',
                'Blocked',
                'Failed'
            )
        );

        PRINT 'CK_Transactions_Status created.';
    END;
END;
GO


-- ============================================================
-- 6. FRAUD ALERTS - RISK LEVEL CHECK
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.check_constraints
    WHERE name = N'CK_FraudAlerts_RiskLevel'
      AND parent_object_id =
          OBJECT_ID(N'dbo.FraudAlerts')
)
BEGIN
    IF EXISTS
    (
        SELECT 1
        FROM dbo.FraudAlerts
        WHERE RiskLevel NOT IN
        (
            'Medium',
            'High'
        )
    )
    BEGIN
        PRINT 'WARNING: CK_FraudAlerts_RiskLevel skipped.';
    END
    ELSE
    BEGIN
        ALTER TABLE dbo.FraudAlerts
        WITH CHECK ADD CONSTRAINT CK_FraudAlerts_RiskLevel
        CHECK
        (
            RiskLevel IN
            (
                'Medium',
                'High'
            )
        );

        PRINT 'CK_FraudAlerts_RiskLevel created.';
    END;
END;
GO


-- ============================================================
-- 7. VERIFY EXISTING REVIEW STATUS CHECK
-- ============================================================

-- The original schema.sql already defines a
-- ReviewStatus CHECK constraint.
-- Do not create an unnecessary duplicate.

SELECT
    name AS ConstraintName,
    definition AS ConstraintDefinition
FROM sys.check_constraints
WHERE parent_object_id =
      OBJECT_ID(N'dbo.FraudAlerts')
  AND definition LIKE '%ReviewStatus%';
GO


-- ============================================================
-- 8. VIEW - DAILY TRANSACTION STATISTICS
-- ============================================================

CREATE OR ALTER VIEW dbo.vw_DailyTransactionStats
AS
SELECT
    CONVERT(DATE, TransactionDate) AS TransactionDay,
    TransactionType,
    Status,
    COUNT_BIG(*) AS TransactionCount,
    SUM(Amount) AS TotalAmount
FROM dbo.Transactions
GROUP BY
    CONVERT(DATE, TransactionDate),
    TransactionType,
    Status;
GO


-- ============================================================
-- 9. VIEW - SUSPICIOUS TRANSACTIONS
-- ============================================================

CREATE OR ALTER VIEW dbo.vw_SuspiciousTransactions
AS
SELECT
    fa.AlertID,
    fa.TransactionID,

    fr.RuleName,
    fr.RuleType,

    t.TransactionType,
    t.Amount,
    t.TransactionDate,

    fa.RiskLevel,
    fa.ReviewStatus,
    fa.CreatedAt,

    fa.ReviewedAt,
    fa.ReviewedByUserID,
    fa.ReviewNote

FROM dbo.FraudAlerts AS fa

INNER JOIN dbo.Transactions AS t
    ON t.TransactionID = fa.TransactionID

INNER JOIN dbo.FraudRules AS fr
    ON fr.RuleID = fa.RuleID;
GO


-- ============================================================
-- 10. VIEW - CUSTOMER RISK SUMMARY
-- ============================================================

CREATE OR ALTER VIEW dbo.vw_CustomerRiskSummary
AS

WITH LinkedCustomers AS
(
    SELECT DISTINCT
        fa.AlertID,
        a.CustomerID,
        fa.RiskLevel,
        fa.ReviewStatus

    FROM dbo.FraudAlerts AS fa

    INNER JOIN dbo.Transactions AS t
        ON t.TransactionID = fa.TransactionID

    INNER JOIN dbo.Accounts AS a
        ON a.AccountID = t.FromAccountID
        OR a.AccountID = t.ToAccountID
)

SELECT
    c.CustomerID,
    c.FirstName,
    c.LastName,

    COUNT(lc.AlertID) AS AlertCount,

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
-- 11. VERIFY NEW COLUMNS
-- ============================================================

SELECT
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE
    (
        TABLE_NAME = 'AuditLogs'
        AND COLUMN_NAME = 'UserID'
    )
    OR
    (
        TABLE_NAME = 'FraudAlerts'
        AND COLUMN_NAME IN
        (
            'ReviewedByUserID',
            'ReviewNote'
        )
    )
ORDER BY
    TABLE_NAME,
    COLUMN_NAME;
GO


-- ============================================================
-- 12. VERIFY CHECK CONSTRAINTS
-- ============================================================

SELECT
    OBJECT_NAME(parent_object_id) AS TableName,
    name AS ConstraintName,
    definition AS ConstraintDefinition,
    is_disabled AS IsDisabled,
    is_not_trusted AS IsNotTrusted
FROM sys.check_constraints
WHERE parent_object_id IN
(
    OBJECT_ID(N'dbo.Transactions'),
    OBJECT_ID(N'dbo.FraudAlerts')
)
ORDER BY
    TableName,
    ConstraintName;
GO


-- ============================================================
-- 13. VERIFY REPORTING VIEWS
-- ============================================================

SELECT TOP (10)
    *
FROM dbo.vw_DailyTransactionStats
ORDER BY TransactionDay DESC;
GO

SELECT TOP (10)
    *
FROM dbo.vw_SuspiciousTransactions
ORDER BY AlertID DESC;
GO

SELECT TOP (10)
    *
FROM dbo.vw_CustomerRiskSummary
ORDER BY AlertCount DESC;
GO


-- ============================================================
-- 14. VERIFY EXISTING DATA COUNTS
-- ============================================================

SELECT 'Customers' AS TableName, COUNT(*) AS RecordCount
FROM dbo.Customers

UNION ALL

SELECT 'Users', COUNT(*)
FROM dbo.Users

UNION ALL

SELECT 'Accounts', COUNT(*)
FROM dbo.Accounts

UNION ALL

SELECT 'Transactions', COUNT(*)
FROM dbo.Transactions

UNION ALL

SELECT 'FraudRules', COUNT(*)
FROM dbo.FraudRules

UNION ALL

SELECT 'FraudAlerts', COUNT(*)
FROM dbo.FraudAlerts

UNION ALL

SELECT 'AuditLogs', COUNT(*)
FROM dbo.AuditLogs;
GO


-- ============================================================
-- 15. FINISH
-- ============================================================

PRINT '==========================================';
PRINT 'BankingFraudDB M1 improvements completed.';
PRINT 'Existing records were not deleted.';
PRINT 'Review any warning messages above.';
PRINT '==========================================';
GO


-- ============================================================
-- NG BANK
-- FILE: 06_verify.sql
-- PURPOSE: Verify a fresh database installation
-- SOURCE: current_database_schema.sql
-- TARGET: BankingFraudDB
--
-- RUN AFTER:
-- 01_schema.sql
-- 02_constraints_indexes.sql
-- 03_seed_data.sql
-- 04_views.sql
-- 05_procedures.sql
--
-- READ-ONLY VERIFICATION
-- No application tables or records are modified.
-- ============================================================

USE [BankingFraudDB];
GO

SET NOCOUNT ON;
GO

-- ============================================================
-- 1. PREPARE VERIFICATION RESULTS
-- ============================================================

IF OBJECT_ID('tempdb..#VerificationResults') IS NOT NULL
    DROP TABLE #VerificationResults;

CREATE TABLE #VerificationResults
(
    CheckName NVARCHAR(100) NOT NULL,
    ExpectedCount INT NOT NULL,
    ActualCount INT NOT NULL,
    Result VARCHAR(10) NOT NULL
);

-- ============================================================
-- 2. VERIFY ALL 11 TABLES
-- ============================================================

;WITH ExpectedTables AS
(
    SELECT TableName
    FROM (VALUES
        (N'Customers'),
        (N'Users'),
        (N'Accounts'),
        (N'Transactions'),
        (N'FraudRules'),
        (N'FraudAlerts'),
        (N'AuditLogs'),
        (N'Notifications'),
        (N'CreditCardApplications'),
        (N'CreditCards'),
        (N'CreditCardTransactions')
    ) AS t(TableName)
)
SELECT
    e.TableName AS MissingTable
FROM ExpectedTables AS e
WHERE OBJECT_ID(
    N'dbo.' + e.TableName,
    N'U'
) IS NULL;

INSERT INTO #VerificationResults
SELECT
    N'Tables',
    11,
    COUNT(*),
    CASE WHEN COUNT(*) = 11
         THEN 'PASS' ELSE 'FAIL' END
FROM sys.tables
WHERE schema_id = SCHEMA_ID(N'dbo');

-- ============================================================
-- 3. VERIFY ALL 7 VIEWS
-- ============================================================

;WITH ExpectedViews AS
(
    SELECT ViewName
    FROM (VALUES
        (N'vw_AccountSummary'),
        (N'vw_DailyTransactionStats'),
        (N'vw_FraudTransactions'),
        (N'vw_FraudAlertDetails'),
        (N'vw_SuspiciousTransactions'),
        (N'vw_CustomerRiskSummary'),
        (N'vw_CustomerFraudReviews')
    ) AS v(ViewName)
)
SELECT
    e.ViewName AS MissingView
FROM ExpectedViews AS e
WHERE OBJECT_ID(
    N'dbo.' + e.ViewName,
    N'V'
) IS NULL;

INSERT INTO #VerificationResults
SELECT
    N'Views',
    7,
    COUNT(*),
    CASE WHEN COUNT(*) = 7
         THEN 'PASS' ELSE 'FAIL' END
FROM sys.views
WHERE schema_id = SCHEMA_ID(N'dbo');

-- ============================================================
-- 4. VERIFY ALL 10 STORED PROCEDURES
-- ============================================================

;WITH ExpectedProcedures AS
(
    SELECT ProcedureName
    FROM (VALUES
        (N'sp_ExecuteBankTransaction'),
        (N'sp_Deposit'),
        (N'sp_Withdraw'),
        (N'sp_Transfer'),
        (N'sp_ExecuteCreditCardTransaction'),
        (N'sp_CreditCardPurchase'),
        (N'sp_CreditCardCashAdvance'),
        (N'sp_CreditCardPayment'),
        (N'sp_ScanFraud'),
        (N'sp_ScanCreditCardFraud')
    ) AS p(ProcedureName)
)
SELECT
    e.ProcedureName AS MissingProcedure
FROM ExpectedProcedures AS e
WHERE OBJECT_ID(
    N'dbo.' + e.ProcedureName,
    N'P'
) IS NULL;

INSERT INTO #VerificationResults
SELECT
    N'Stored Procedures',
    10,
    COUNT(*),
    CASE WHEN COUNT(*) = 10
         THEN 'PASS' ELSE 'FAIL' END
FROM sys.procedures
WHERE schema_id = SCHEMA_ID(N'dbo');

-- ============================================================
-- 5. VERIFY FOREIGN KEYS
-- ============================================================

SELECT
    fk.name AS ForeignKeyName,
    OBJECT_SCHEMA_NAME(fk.parent_object_id)
        AS SourceSchema,
    OBJECT_NAME(fk.parent_object_id)
        AS SourceTable,
    OBJECT_NAME(fk.referenced_object_id)
        AS TargetTable,
    fk.is_disabled AS IsDisabled,
    fk.is_not_trusted AS IsNotTrusted
FROM sys.foreign_keys AS fk
WHERE OBJECT_SCHEMA_NAME(fk.parent_object_id) = N'dbo'
ORDER BY SourceTable, ForeignKeyName;

INSERT INTO #VerificationResults
SELECT
    N'Foreign Keys',
    17,
    COUNT(*),
    CASE WHEN COUNT(*) = 17
         THEN 'PASS' ELSE 'FAIL' END
FROM sys.foreign_keys AS fk
WHERE OBJECT_SCHEMA_NAME(fk.parent_object_id) = N'dbo';

-- ============================================================
-- 6. VERIFY THE 17 EXPLICIT INDEXES
--
-- Exclude indexes automatically created by
-- PRIMARY KEY and UNIQUE constraints.
-- ============================================================

;WITH ExpectedIndexes AS
(
    SELECT
        TableName,
        IndexName
    FROM (VALUES
        (N'Accounts', N'IX_Accounts_CustomerID'),
        (N'AuditLogs', N'IX_AuditLogs_UserID'),

        (N'CreditCardApplications',
         N'IX_CreditCardApplications_Customer'),

        (N'CreditCards',
         N'IX_CreditCards_Customer'),

        (N'CreditCardTransactions',
         N'IX_CreditCardTransactions_Card'),

        (N'CreditCardTransactions',
         N'UX_CreditCardTransactions_BankTransaction'),

        (N'Customers', N'UX_Customers_Phone'),

        (N'FraudAlerts',
         N'IX_FraudAlerts_ReviewStatus'),

        (N'FraudAlerts',
         N'IX_FraudAlerts_TransactionID'),

        (N'FraudAlerts',
         N'UX_FraudAlerts_BankRule'),

        (N'FraudAlerts',
         N'UX_FraudAlerts_CardRule'),

        (N'Notifications',
         N'IX_Notifications_Customer'),

        (N'Transactions',
         N'IX_Transactions_Date'),

        (N'Transactions',
         N'IX_Transactions_FromAccount'),

        (N'Transactions',
         N'IX_Transactions_ToAccount'),

        (N'Users',
         N'UX_Users_CustomerID'),

        (N'Users',
         N'UX_Users_Email')
    ) AS x(TableName, IndexName)
)
SELECT
    e.TableName,
    e.IndexName AS MissingIndex
FROM ExpectedIndexes AS e
WHERE NOT EXISTS
(
    SELECT 1
    FROM sys.indexes AS i
    WHERE i.object_id =
        OBJECT_ID(N'dbo.' + e.TableName)
      AND i.name = e.IndexName
      AND i.is_disabled = 0
);

INSERT INTO #VerificationResults
SELECT
    N'Explicit Indexes',
    17,
    COUNT(*),
    CASE WHEN COUNT(*) = 17
         THEN 'PASS' ELSE 'FAIL' END
FROM sys.indexes AS i
INNER JOIN sys.tables AS t
    ON t.object_id = i.object_id
WHERE t.schema_id = SCHEMA_ID(N'dbo')
  AND i.index_id > 0
  AND i.is_primary_key = 0
  AND i.is_unique_constraint = 0;

-- ============================================================
-- 7. VERIFY REQUIRED FRAUD RULES
-- ============================================================

;WITH ExpectedRules AS
(
    SELECT RuleType
    FROM (VALUES
        ('HighAmount'),
        ('Frequent'),
        ('RepeatedAmount')
    ) AS r(RuleType)
)
SELECT
    e.RuleType AS MissingRule
FROM ExpectedRules AS e
WHERE NOT EXISTS
(
    SELECT 1
    FROM dbo.FraudRules AS f
    WHERE f.RuleType = e.RuleType
);

INSERT INTO #VerificationResults
SELECT
    N'Fraud Rule Types',
    3,
    COUNT(DISTINCT RuleType),
    CASE WHEN COUNT(DISTINCT RuleType) = 3
         THEN 'PASS' ELSE 'FAIL' END
FROM dbo.FraudRules
WHERE RuleType IN
(
    'HighAmount',
    'Frequent',
    'RepeatedAmount'
);

-- ============================================================
-- 8. VERIFY IMPORTANT COLUMNS
-- ============================================================

;WITH RequiredColumns AS
(
    SELECT TableName, ColumnName
    FROM (VALUES
        (N'Accounts', N'IsFrozen'),
        (N'Accounts', N'Balance'),
        (N'Accounts', N'CustomerID'),

        (N'FraudAlerts', N'TransactionID'),
        (N'FraudAlerts', N'CardTransactionID'),
        (N'FraudAlerts', N'ReviewStatus'),
        (N'FraudAlerts', N'ReviewedByUserID'),

        (N'CreditCards', N'LinkedAccountID'),
        (N'CreditCards', N'OutstandingBalance'),
        (N'CreditCards', N'CardStatus'),

        (N'CreditCardTransactions',
         N'BankTransactionID'),

        (N'CreditCardTransactions',
         N'TransactionStatus')
    ) AS c(TableName, ColumnName)
)
SELECT
    r.TableName,
    r.ColumnName AS MissingColumn
FROM RequiredColumns AS r
WHERE NOT EXISTS
(
    SELECT 1
    FROM sys.columns AS c
    WHERE c.object_id =
        OBJECT_ID(N'dbo.' + r.TableName)
      AND c.name = r.ColumnName
);

-- ============================================================
-- 9. VERIFY IMPORTANT NULLABILITY RULES
-- ============================================================

SELECT
    t.name AS TableName,
    c.name AS ColumnName,
    c.is_nullable AS IsNullable
FROM sys.columns AS c
INNER JOIN sys.tables AS t
    ON t.object_id = c.object_id
WHERE
    (
        t.name = N'FraudAlerts'
        AND c.name IN
        (
            N'TransactionID',
            N'CardTransactionID',
            N'ReviewedByUserID'
        )
    )
    OR
    (
        t.name = N'CreditCardTransactions'
        AND c.name = N'BankTransactionID'
    )
ORDER BY t.name, c.name;

-- ============================================================
-- 10. CHECK DISABLED OR UNTRUSTED CONSTRAINTS
-- ============================================================

SELECT
    N'Foreign Key' AS ConstraintType,
    fk.name AS ConstraintName,
    OBJECT_NAME(fk.parent_object_id) AS TableName,
    fk.is_disabled AS IsDisabled,
    fk.is_not_trusted AS IsNotTrusted
FROM sys.foreign_keys AS fk
WHERE fk.is_disabled = 1
   OR fk.is_not_trusted = 1

UNION ALL

SELECT
    N'Check Constraint',
    cc.name,
    OBJECT_NAME(cc.parent_object_id),
    cc.is_disabled,
    cc.is_not_trusted
FROM sys.check_constraints AS cc
WHERE cc.is_disabled = 1
   OR cc.is_not_trusted = 1;

-- ============================================================
-- 11. VERIFY TRIGGER COUNT
-- ============================================================

INSERT INTO #VerificationResults
SELECT
    N'Triggers',
    0,
    COUNT(*),
    CASE WHEN COUNT(*) = 0
         THEN 'PASS' ELSE 'FAIL' END
FROM sys.triggers AS tr
INNER JOIN sys.objects AS o
    ON o.object_id = tr.parent_id
WHERE OBJECT_SCHEMA_NAME(o.object_id) = N'dbo';

-- ============================================================
-- 12. FINAL VERIFICATION SUMMARY
-- ============================================================

SELECT
    CheckName,
    ExpectedCount,
    ActualCount,
    Result
FROM #VerificationResults
ORDER BY CheckName;

-- ============================================================
-- 13. FINAL STATUS
-- ============================================================

IF EXISTS
(
    SELECT 1
    FROM #VerificationResults
    WHERE Result = 'FAIL'
)
BEGIN
    PRINT 'NG BANK VERIFICATION FAILED.';
    PRINT 'Review missing objects and counts.';
END
ELSE
BEGIN
    PRINT 'NG BANK BASIC VERIFICATION PASSED.';
    PRINT 'All expected object counts were found.';
END;
GO


/******************************************************/

SELECT * FROM FraudRules;
SELECT * FROM Users;
SELECT * FROM Accounts;
SELECT * FROM Transactions;
SELECT * FROM FraudAlerts;
SELECT * FROM AuditLogs;
SELECT * FROM Customers;
SELECT * FROM Notifications;
SELECT * FROM CreditCardApplications;
SELECT * FROM CreditCards;
SELECT * FROM CreditCardTransactions;


SELECT 'Customers' AS TableName, COUNT(*) AS RecordCount FROM dbo.Customers
UNION ALL
SELECT 'Users', COUNT(*) FROM dbo.Users
UNION ALL
SELECT 'Accounts', COUNT(*) FROM dbo.Accounts
UNION ALL
SELECT 'Transactions', COUNT(*) FROM dbo.Transactions
UNION ALL
SELECT 'FraudRules', COUNT(*) FROM dbo.FraudRules
UNION ALL
SELECT 'FraudAlerts', COUNT(*) FROM dbo.FraudAlerts
UNION ALL
SELECT 'AuditLogs', COUNT(*) FROM dbo.AuditLogs
UNION ALL
SELECT 'Notifications', COUNT(*) FROM dbo.Notifications
UNION ALL 
SELECT 'CreditCards', COUNT(*) FROM dbo.CreditCards
UNION ALL
SELECT 'CreditCardsApplications', COUNT(*) FROM dbo.CreditCardApplications
UNION ALL
SELECT 'CreditCardTransactions', COUNT(*) FROM dbo.CreditCardTransactions;


/* USE BankingFraudDB;
GO

SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    -- Delete dependent records first
    DELETE FROM dbo.Notifications;
    DELETE FROM dbo.FraudAlerts;
    DELETE FROM dbo.AuditLogs;

    -- Credit card tables
    DELETE FROM dbo.CreditCardTransactions;
    DELETE FROM dbo.CreditCards;
    DELETE FROM dbo.CreditCardApplications;

    DELETE FROM dbo.Transactions;
    DELETE FROM dbo.Users;
    DELETE FROM dbo.Accounts;
    DELETE FROM dbo.Customers;

    -- Reset identity counters
    DBCC CHECKIDENT ('dbo.Notifications', RESEED, 0);
    DBCC CHECKIDENT ('dbo.FraudAlerts', RESEED, 0);
    DBCC CHECKIDENT ('dbo.AuditLogs', RESEED, 0);

    DBCC CHECKIDENT ('dbo.CreditCardTransactions', RESEED, 0);
    DBCC CHECKIDENT ('dbo.CreditCards', RESEED, 0);
    DBCC CHECKIDENT ('dbo.CreditCardApplications', RESEED, 0);

    DBCC CHECKIDENT ('dbo.Transactions', RESEED, 0);
    DBCC CHECKIDENT ('dbo.Users', RESEED, 0);
    DBCC CHECKIDENT ('dbo.Accounts', RESEED, 0);
    DBCC CHECKIDENT ('dbo.Customers', RESEED, 0);

    -- FraudRules are preserved

    COMMIT TRANSACTION;

    PRINT 'Test data deleted and identity counters reset.';

END TRY
BEGIN CATCH

    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    PRINT ERROR_MESSAGE();

END CATCH;
GO */
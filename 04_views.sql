
-- ============================================================
-- BANKING MANAGEMENT & FRAUD DETECTION SYSTEM
-- FILE: 04_views.sql
-- PURPOSE: Database views and reporting
--
-- RUN AFTER:
--   01_schema.sql
--   02_constraints_indexes.sql
--   03_seed_fraud_rules.sql
--
-- IMPORTANT:
--   Existing records are not deleted.
--   Existing views are updated when necessary.
--   Column names are preserved for application compatibility.
-- ============================================================

USE BankingFraudDB;
GO

SET NOCOUNT ON;
GO


-- ============================================================
-- 1. ACCOUNT SUMMARY VIEW
-- ============================================================

CREATE OR ALTER VIEW dbo.vw_AccountSummary
AS
SELECT
    a.AccountID,
    a.AccountNumber,
    a.AccountType,
    a.Balance,
    a.Currency,
    a.IsActive,

    c.CustomerID,
    c.FirstName,
    c.LastName,
    c.NationalID

FROM dbo.Accounts AS a

INNER JOIN dbo.Customers AS c
    ON c.CustomerID = a.CustomerID;
GO


-- ============================================================
-- 2. FRAUD ALERT DETAILS VIEW
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
        THEN sender.FirstName + N' ' + sender.LastName
        ELSE NULL
    END AS SenderCustomer,

    source.AccountNumber AS SenderAccountNumber,

    receiver.CustomerID AS ReceiverCustomerID,

    CASE
        WHEN receiver.CustomerID IS NOT NULL
        THEN receiver.FirstName + N' ' + receiver.LastName
        ELSE NULL
    END AS ReceiverCustomer,

    target.AccountNumber AS ReceiverAccountNumber,

    t.Amount,
    t.TransactionDate,

    fa.AlertDescription,
    fa.RiskLevel,
    fa.ReviewStatus,
    fa.CreatedAt,
    fa.ReviewedAt

FROM dbo.FraudAlerts AS fa

INNER JOIN dbo.FraudRules AS fr
    ON fr.RuleID = fa.RuleID

INNER JOIN dbo.Transactions AS t
    ON t.TransactionID = fa.TransactionID

LEFT JOIN dbo.Accounts AS source
    ON source.AccountID = t.FromAccountID

LEFT JOIN dbo.Customers AS sender
    ON sender.CustomerID = source.CustomerID

LEFT JOIN dbo.Accounts AS target
    ON target.AccountID = t.ToAccountID

LEFT JOIN dbo.Customers AS receiver
    ON receiver.CustomerID = target.CustomerID;
GO


-- ============================================================
-- 3. DAILY TRANSACTION STATISTICS VIEW
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
-- 4. SUSPICIOUS TRANSACTIONS VIEW
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
-- 5. CUSTOMER RISK SUMMARY VIEW
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
-- 6. CUSTOMER FRAUD REVIEWS VIEW
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
    t.ToAccountID

FROM dbo.FraudAlerts AS fa

INNER JOIN dbo.Transactions AS t
    ON t.TransactionID = fa.TransactionID

INNER JOIN dbo.FraudRules AS fr
    ON fr.RuleID = fa.RuleID

WHERE fa.ReviewStatus <> 'Pending';
GO


-- ============================================================
-- 7. VERIFY CREATED VIEWS
-- ============================================================

SELECT
    v.name AS ViewName,
    v.create_date AS CreatedAt,
    v.modify_date AS LastModified

FROM sys.views AS v

WHERE v.schema_id = SCHEMA_ID(N'dbo')
  AND v.name IN
  (
      N'vw_AccountSummary',
      N'vw_FraudAlertDetails',
      N'vw_DailyTransactionStats',
      N'vw_SuspiciousTransactions',
      N'vw_CustomerRiskSummary',
      N'vw_CustomerFraudReviews'
  )

ORDER BY v.name;
GO


-- ============================================================
-- 8. VERIFY ACCOUNT SUMMARY
-- ============================================================

SELECT TOP (10)
    *
FROM dbo.vw_AccountSummary
ORDER BY AccountID;
GO


-- ============================================================
-- 9. VERIFY FRAUD ALERT DETAILS
-- ============================================================

SELECT TOP (10)
    *
FROM dbo.vw_FraudAlertDetails
ORDER BY AlertID DESC;
GO


-- ============================================================
-- 10. VERIFY DAILY TRANSACTION STATISTICS
-- ============================================================

SELECT TOP (10)
    *
FROM dbo.vw_DailyTransactionStats
ORDER BY TransactionDay DESC;
GO


-- ============================================================
-- 11. VERIFY SUSPICIOUS TRANSACTIONS
-- ============================================================

SELECT TOP (10)
    *
FROM dbo.vw_SuspiciousTransactions
ORDER BY AlertID DESC;
GO


-- ============================================================
-- 12. VERIFY CUSTOMER RISK SUMMARY
-- ============================================================

SELECT TOP (10)
    *
FROM dbo.vw_CustomerRiskSummary
ORDER BY AlertCount DESC;
GO


-- ============================================================
-- 13. VERIFY CUSTOMER FRAUD REVIEWS
-- ============================================================

SELECT TOP (10)
    *
FROM dbo.vw_CustomerFraudReviews
ORDER BY AlertID DESC;
GO


-- ============================================================
-- 14. FINISH
-- ============================================================

PRINT '============================================';
PRINT '04_views.sql completed.';
PRINT '6 database views checked and updated.';
PRINT 'Existing records were not deleted.';
PRINT '============================================';
GO

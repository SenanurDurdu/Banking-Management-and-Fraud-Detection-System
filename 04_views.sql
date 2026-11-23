-- ============================================================
-- NG BANK
-- FILE: 04_views.sql
-- PURPOSE: Database views for banking and fraud analysis
-- DATABASE: BankingFraudDB
-- RUN AFTER: 01, 02 and 03
-- TOTAL PROJECT VIEWS: 9
-- ============================================================

USE BankingFraudDB_Test;
GO

-- ============================================================
-- 1. ACCOUNT SUMMARY
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
-- 2. DAILY TRANSACTION STATISTICS
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
-- 3. UNIFIED BANK AND CREDIT CARD TRANSACTIONS
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

    CAST(t.Description AS NVARCHAR(500))
        AS TransactionDescription,

    t.Status AS TransactionStatus

FROM dbo.Transactions AS t

LEFT JOIN dbo.CreditCardTransactions AS ct
    ON ct.BankTransactionID = t.TransactionID

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
    ON cc.CreditCardID = ct.CreditCardID

WHERE ct.BankTransactionID IS NULL
  AND ct.TransactionType = 'Purchase';
GO

-- ============================================================
-- 4. FRAUD ALERT DETAILS
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
    fa.ReviewedAt,
    fa.CardTransactionID,
    t.CreditCardID,
    t.TransactionSource,
    t.TransactionDescription,
    t.AffectedAccountID,

    CASE
        WHEN fa.CardTransactionID IS NOT NULL
            THEN CONCAT('CC-', fa.CardTransactionID)
        ELSE CONVERT(VARCHAR(30), fa.TransactionID)
    END AS TransactionReference

FROM dbo.FraudAlerts AS fa

INNER JOIN dbo.FraudRules AS fr
    ON fr.RuleID = fa.RuleID

INNER JOIN dbo.vw_FraudTransactions AS t
    ON (
        fa.TransactionID IS NOT NULL
        AND t.TransactionID = fa.TransactionID
    )
    OR (
        fa.CardTransactionID IS NOT NULL
        AND t.CardTransactionID = fa.CardTransactionID
    )

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
-- 5. SUSPICIOUS TRANSACTIONS
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
-- 6. CUSTOMER RISK SUMMARY
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

    COUNT(lc.AlertID) AS AlertCount,

    SUM(
        CASE
            WHEN lc.RiskLevel = 'High' THEN 1
            ELSE 0
        END
    ) AS HighRiskAlerts,

    SUM(
        CASE
            WHEN lc.ReviewStatus = 'Pending' THEN 1
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
-- 7. CUSTOMER FRAUD REVIEWS
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
            THEN CONCAT('CC-', fa.CardTransactionID)
        ELSE CONVERT(VARCHAR(30), fa.TransactionID)
    END AS TransactionReference

FROM dbo.FraudAlerts AS fa

INNER JOIN dbo.FraudRules AS fr
    ON fr.RuleID = fa.RuleID

INNER JOIN dbo.vw_FraudTransactions AS t
    ON (
        fa.TransactionID IS NOT NULL
        AND t.TransactionID = fa.TransactionID
    )
    OR (
        fa.CardTransactionID IS NOT NULL
        AND t.CardTransactionID = fa.CardTransactionID
    )

WHERE fa.ReviewStatus <> 'Pending';
GO

-- ============================================================
-- 8. ACCOUNT DAILY BALANCE DETAILS
-- NEW VIEW
-- ============================================================

CREATE OR ALTER VIEW dbo.vw_AccountDailyBalanceDetails
AS
SELECT
    adb.BalanceID,
    adb.AccountID,
    a.AccountNumber,
    a.AccountType,
    a.Currency,
    a.CustomerID,
    c.FirstName,
    c.LastName,
    adb.BalanceDate,
    adb.ClosingBalance,
    adb.RecordedAt

FROM dbo.AccountDailyBalances AS adb

INNER JOIN dbo.Accounts AS a
    ON a.AccountID = adb.AccountID

INNER JOIN dbo.Customers AS c
    ON c.CustomerID = a.CustomerID;
GO

-- ============================================================
-- 9. FRAUD RISK ASSESSMENT DETAILS
-- NEW VIEW
-- ============================================================

CREATE OR ALTER VIEW dbo.vw_FraudRiskAssessmentDetails
AS
SELECT
    fra.AssessmentID,
    fra.AlertID,
    fa.TransactionID,
    fa.CardTransactionID,
    fr.RuleName,
    fr.RuleType,
    fra.RiskLevel,
    fra.ReviewStatus,
    fa.AlertDescription,
    fa.CreatedAt AS AlertCreatedAt,
    fra.AssessedAt

FROM dbo.FraudRiskAssessments AS fra

INNER JOIN dbo.FraudAlerts AS fa
    ON fa.AlertID = fra.AlertID

INNER JOIN dbo.FraudRules AS fr
    ON fr.RuleID = fa.RuleID;
GO

-- ============================================================
-- 10. VERIFY ALL NINE VIEWS
-- ============================================================

SELECT
    name AS ViewName,
    create_date AS CreatedAt,
    modify_date AS ModifiedAt
FROM sys.views
WHERE schema_id = SCHEMA_ID(N'dbo')
  AND name IN
  (
      N'vw_AccountSummary',
      N'vw_DailyTransactionStats',
      N'vw_FraudTransactions',
      N'vw_FraudAlertDetails',
      N'vw_SuspiciousTransactions',
      N'vw_CustomerRiskSummary',
      N'vw_CustomerFraudReviews',
      N'vw_AccountDailyBalanceDetails',
      N'vw_FraudRiskAssessmentDetails'
  )
ORDER BY name;
GO

-- ============================================================
-- 11. CHECK VIEW COUNT
-- ============================================================

DECLARE @ViewCount INT;

SELECT @ViewCount = COUNT(*)
FROM sys.views
WHERE schema_id = SCHEMA_ID(N'dbo')
  AND name IN
  (
      N'vw_AccountSummary',
      N'vw_DailyTransactionStats',
      N'vw_FraudTransactions',
      N'vw_FraudAlertDetails',
      N'vw_SuspiciousTransactions',
      N'vw_CustomerRiskSummary',
      N'vw_CustomerFraudReviews',
      N'vw_AccountDailyBalanceDetails',
      N'vw_FraudRiskAssessmentDetails'
  );

IF @ViewCount = 9
BEGIN
    PRINT 'NG BANK: All nine required views exist.';
END
ELSE
BEGIN
    PRINT 'NG BANK WARNING: Expected 9 views, found '
          + CAST(@ViewCount AS VARCHAR(10)) + '.';
END;

SELECT
    @ViewCount AS TotalViews,
    CASE
        WHEN @ViewCount = 9 THEN 'PASS'
        ELSE 'FAIL'
    END AS VerificationStatus;
GO

-- ============================================================
-- 12. VERIFY DATABASE TABLE COUNT
-- ============================================================

DECLARE @TableCount INT;

SELECT @TableCount = COUNT(*)
FROM sys.tables
WHERE schema_id = SCHEMA_ID(N'dbo')
  AND is_ms_shipped = 0;

IF @TableCount = 20
BEGIN
    PRINT 'NG BANK: Exactly 20 tables confirmed.';
END
ELSE
BEGIN
    PRINT 'NG BANK WARNING: Expected 20 tables, found '
          + CAST(@TableCount AS VARCHAR(10)) + '.';
END;

SELECT
    @TableCount AS TotalTables,
    CASE
        WHEN @TableCount = 20 THEN 'PASS'
        ELSE 'FAIL'
    END AS VerificationStatus;
GO

-- ============================================================
-- 13. TEST NEW VIEWS
-- ============================================================

SELECT TOP (10) *
FROM dbo.vw_AccountDailyBalanceDetails
ORDER BY BalanceDate DESC, AccountID;
GO

SELECT TOP (10) *
FROM dbo.vw_FraudRiskAssessmentDetails
ORDER BY AssessedAt DESC, AlertID;
GO

PRINT '04_views.sql completed successfully.';
GO
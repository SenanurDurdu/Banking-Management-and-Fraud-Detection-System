
-- ============================================================
-- BANKING MANAGEMENT AND FRAUD DETECTION SYSTEM
-- COMPLETE SQL SERVER DATABASE SETUP
-- ============================================================
--
-- DATABASE: BankingFraudDB
--
-- TABLES:
--   1. Customers
--   2. Users
--   3. Accounts
--   4. Transactions
--   5. FraudRules
--   6. FraudAlerts
--   7. AuditLogs
--
-- VIEWS:
--   1. vw_AccountSummary
--   2. vw_FraudAlertDetails
--
-- FRAUD RULES:
--   HighAmount
--   Frequent
--   RepeatedAmount
--
-- REVIEW STATUSES:
--   Pending
--   Reviewed
--   FalsePositive
--   ConfirmedFraud
--
-- IMPORTANT:
--   Does not delete existing customer or transaction data.
--   Does not reset identity counters.
--   Does not create demo customers or fake transactions.
-- ============================================================


-- ============================================================
-- 1. CREATE DATABASE
-- ============================================================

IF DB_ID(N'BankingFraudDB') IS NULL
BEGIN
    CREATE DATABASE BankingFraudDB;
END;
GO

USE BankingFraudDB;
GO


-- ============================================================
-- 2. CUSTOMERS
-- ============================================================

IF OBJECT_ID(N'dbo.Customers', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Customers
    (
        CustomerID INT IDENTITY(1,1)
            CONSTRAINT PK_Customers PRIMARY KEY,

        FirstName NVARCHAR(60) NOT NULL,

        LastName NVARCHAR(60) NOT NULL,

        NationalID CHAR(11) NOT NULL,

        Phone NVARCHAR(20) NULL,

        Email NVARCHAR(120) NULL,

        Address NVARCHAR(255) NULL,

        CreatedAt DATETIME2 NOT NULL
            CONSTRAINT DF_Customers_CreatedAt
            DEFAULT SYSDATETIME(),

        IsActive BIT NOT NULL
            CONSTRAINT DF_Customers_IsActive
            DEFAULT 1,

        CONSTRAINT UQ_Customers_NationalID
            UNIQUE (NationalID),

        CONSTRAINT UQ_Customers_Email
            UNIQUE (Email)
    );
END;
GO


-- ============================================================
-- 3. CUSTOMER SCHEMA COMPATIBILITY
-- ============================================================

IF COL_LENGTH(N'dbo.Customers', N'Phone') IS NULL
BEGIN
    ALTER TABLE dbo.Customers
    ADD Phone NVARCHAR(20) NULL;
END;
GO

IF COL_LENGTH(N'dbo.Customers', N'Email') IS NULL
BEGIN
    ALTER TABLE dbo.Customers
    ADD Email NVARCHAR(120) NULL;
END;
GO

IF COL_LENGTH(N'dbo.Customers', N'Address') IS NULL
BEGIN
    ALTER TABLE dbo.Customers
    ADD Address NVARCHAR(255) NULL;
END;
GO

-- Upgrade the original NVARCHAR(250) Address column.

IF EXISTS
(
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID(N'dbo.Customers')
      AND name = N'Address'
      AND system_type_id = TYPE_ID(N'nvarchar')
      AND max_length = 500
)
BEGIN
    ALTER TABLE dbo.Customers
    ALTER COLUMN Address NVARCHAR(255) NULL;
END;
GO


-- ============================================================
-- 4. UNIQUE CUSTOMER EMAIL
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Customers')
      AND name = N'UQ_Customers_Email'
)
AND NOT EXISTS
(
    SELECT 1
    FROM dbo.Customers
    WHERE Email IS NOT NULL
    GROUP BY Email
    HAVING COUNT(*) > 1
)
BEGIN
    -- Only create if there is no existing equivalent
    -- single-column unique index on Email.

    IF NOT EXISTS
    (
        SELECT 1
        FROM sys.indexes i
        JOIN sys.index_columns ic
          ON ic.object_id = i.object_id
         AND ic.index_id = i.index_id
        JOIN sys.columns c
          ON c.object_id = ic.object_id
         AND c.column_id = ic.column_id
        WHERE i.object_id = OBJECT_ID(N'dbo.Customers')
          AND i.is_unique = 1
          AND i.has_filter = 0
          AND ic.key_ordinal = 1
          AND c.name = N'Email'
          AND NOT EXISTS
          (
              SELECT 1
              FROM sys.index_columns ic2
              WHERE ic2.object_id = i.object_id
                AND ic2.index_id = i.index_id
                AND ic2.key_ordinal > 1
          )
    )
    BEGIN
        CREATE UNIQUE INDEX UX_Customers_Email
        ON dbo.Customers(Email);
    END;
END;
GO


-- ============================================================
-- 5. UNIQUE CUSTOMER PHONE
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Customers')
      AND name = N'UX_Customers_Phone'
)
BEGIN
    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.Customers
        WHERE Phone IS NOT NULL
          AND Phone <> N''
        GROUP BY Phone
        HAVING COUNT(*) > 1
    )
    BEGIN
        CREATE UNIQUE INDEX UX_Customers_Phone
        ON dbo.Customers(Phone)
        WHERE Phone IS NOT NULL
          AND Phone <> N'';
    END
    ELSE
    BEGIN
        PRINT 'WARNING: Duplicate phone numbers found.';
        PRINT 'UX_Customers_Phone was not created.';
    END;
END;
GO


-- ============================================================
-- 6. USERS - AUTHENTICATION AND ROLES
-- ============================================================

IF OBJECT_ID(N'dbo.Users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Users
    (
        UserID INT IDENTITY(1,1)
            CONSTRAINT PK_Users PRIMARY KEY,

        CustomerID INT NULL,

        Email NVARCHAR(120) NOT NULL,

        PasswordHash NVARCHAR(255) NOT NULL,

        Role VARCHAR(20) NOT NULL,

        IsActive BIT NOT NULL
            CONSTRAINT DF_Users_IsActive
            DEFAULT 1,

        CreatedAt DATETIME2 NOT NULL
            CONSTRAINT DF_Users_CreatedAt
            DEFAULT SYSDATETIME(),

        LastLoginAt DATETIME2 NULL,

        CONSTRAINT FK_Users_Customers
            FOREIGN KEY (CustomerID)
            REFERENCES dbo.Customers(CustomerID),

        CONSTRAINT CK_Users_Role
            CHECK (Role IN ('Admin', 'Customer')),

        CONSTRAINT CK_Users_RoleCustomer
            CHECK
            (
                (Role = 'Admin' AND CustomerID IS NULL)
                OR
                (Role = 'Customer' AND CustomerID IS NOT NULL)
            )
    );
END;
GO


-- ============================================================
-- 7. UNIQUE USER EMAIL
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Users')
      AND name = N'UX_Users_Email'
)
BEGIN
    CREATE UNIQUE INDEX UX_Users_Email
    ON dbo.Users(Email);
END;
GO


-- ============================================================
-- 8. ONE LOGIN ACCOUNT PER CUSTOMER
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Users')
      AND name = N'UX_Users_CustomerID'
)
BEGIN
    CREATE UNIQUE INDEX UX_Users_CustomerID
    ON dbo.Users(CustomerID)
    WHERE CustomerID IS NOT NULL;
END;
GO


-- ============================================================
-- 9. ACCOUNTS
-- ============================================================

IF OBJECT_ID(N'dbo.Accounts', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Accounts
    (
        AccountID INT IDENTITY(1,1)
            CONSTRAINT PK_Accounts PRIMARY KEY,

        CustomerID INT NOT NULL,

        AccountNumber CHAR(18) NOT NULL,

        AccountType VARCHAR(20) NOT NULL,

        Balance DECIMAL(18,2) NOT NULL
            CONSTRAINT DF_Accounts_Balance
            DEFAULT 0,

        Currency CHAR(3) NOT NULL
            CONSTRAINT DF_Accounts_Currency
            DEFAULT 'TRY',

        CreatedAt DATETIME2 NOT NULL
            CONSTRAINT DF_Accounts_CreatedAt
            DEFAULT SYSDATETIME(),

        IsActive BIT NOT NULL
            CONSTRAINT DF_Accounts_IsActive
            DEFAULT 1,

        CONSTRAINT FK_Accounts_Customers
            FOREIGN KEY (CustomerID)
            REFERENCES dbo.Customers(CustomerID),

        CONSTRAINT UQ_Accounts_AccountNumber
            UNIQUE (AccountNumber),

        CONSTRAINT CK_Accounts_AccountType
            CHECK (AccountType IN ('Checking', 'Savings')),

        CONSTRAINT CK_Accounts_Balance
            CHECK (Balance >= 0)
    );
END;
GO


-- ============================================================
-- 10. TRANSACTIONS
-- ============================================================

IF OBJECT_ID(N'dbo.Transactions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Transactions
    (
        TransactionID BIGINT IDENTITY(1,1)
            CONSTRAINT PK_Transactions PRIMARY KEY,

        FromAccountID INT NULL,

        ToAccountID INT NULL,

        TransactionType VARCHAR(20) NOT NULL,

        Amount DECIMAL(18,2) NOT NULL,

        Description NVARCHAR(250) NULL,

        TransactionDate DATETIME2 NOT NULL
            CONSTRAINT DF_Transactions_Date
            DEFAULT SYSDATETIME(),

        Status VARCHAR(20) NOT NULL
            CONSTRAINT DF_Transactions_Status
            DEFAULT 'Completed',

        CONSTRAINT FK_Transactions_FromAccount
            FOREIGN KEY (FromAccountID)
            REFERENCES dbo.Accounts(AccountID),

        CONSTRAINT FK_Transactions_ToAccount
            FOREIGN KEY (ToAccountID)
            REFERENCES dbo.Accounts(AccountID),

        CONSTRAINT CK_Transactions_Type
            CHECK
            (
                TransactionType IN
                (
                    'Deposit',
                    'Withdrawal',
                    'Transfer'
                )
            ),

        CONSTRAINT CK_Transactions_Amount
            CHECK (Amount > 0)
    );
END;
GO


-- ============================================================
-- 11. FRAUD RULES
-- ============================================================

IF OBJECT_ID(N'dbo.FraudRules', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FraudRules
    (
        RuleID INT IDENTITY(1,1)
            CONSTRAINT PK_FraudRules PRIMARY KEY,

        RuleName NVARCHAR(100) NOT NULL,

        RuleType VARCHAR(30) NOT NULL,

        ThresholdValue DECIMAL(18,2) NOT NULL,

        TimeWindowMinutes INT NOT NULL
            CONSTRAINT DF_FraudRules_TimeWindow
            DEFAULT 60,

        IsActive BIT NOT NULL
            CONSTRAINT DF_FraudRules_IsActive
            DEFAULT 1,

        CONSTRAINT UQ_FraudRules_Name
            UNIQUE (RuleName),

        CONSTRAINT CK_FraudRules_Type
            CHECK
            (
                RuleType IN
                (
                    'HighAmount',
                    'Frequent',
                    'RepeatedAmount'
                )
            )
    );
END;
GO


-- ============================================================
-- 12. FRAUD ALERTS
-- ============================================================

IF OBJECT_ID(N'dbo.FraudAlerts', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FraudAlerts
    (
        AlertID BIGINT IDENTITY(1,1)
            CONSTRAINT PK_FraudAlerts PRIMARY KEY,

        TransactionID BIGINT NOT NULL,

        RuleID INT NOT NULL,

        AlertDescription NVARCHAR(500) NOT NULL,

        RiskLevel VARCHAR(10) NOT NULL
            CONSTRAINT DF_FraudAlerts_Risk
            DEFAULT 'Medium',

        ReviewStatus VARCHAR(20) NOT NULL
            CONSTRAINT DF_FraudAlerts_ReviewStatus
            DEFAULT 'Pending',

        CreatedAt DATETIME2 NOT NULL
            CONSTRAINT DF_FraudAlerts_CreatedAt
            DEFAULT SYSDATETIME(),

        ReviewedAt DATETIME2 NULL,

        CONSTRAINT FK_FraudAlerts_Transactions
            FOREIGN KEY (TransactionID)
            REFERENCES dbo.Transactions(TransactionID),

        CONSTRAINT FK_FraudAlerts_Rules
            FOREIGN KEY (RuleID)
            REFERENCES dbo.FraudRules(RuleID),

        CONSTRAINT UQ_Alert
            UNIQUE (TransactionID, RuleID),

        CONSTRAINT CK_FraudAlerts_ReviewStatus
            CHECK
            (
                ReviewStatus IN
                (
                    'Pending',
                    'Reviewed',
                    'FalsePositive',
                    'ConfirmedFraud'
                )
            )
    );
END;
GO


-- ============================================================
-- 13. EXISTING FRAUD ALERTS COMPATIBILITY
-- ============================================================

-- If an existing database does not yet have a
-- ReviewStatus CHECK constraint, add it.
-- Existing invalid statuses are not changed automatically.

IF NOT EXISTS
(
    SELECT 1
    FROM sys.check_constraints
    WHERE parent_object_id =
          OBJECT_ID(N'dbo.FraudAlerts')
      AND definition LIKE '%ReviewStatus%'
)
BEGIN
    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.FraudAlerts
        WHERE ReviewStatus NOT IN
        (
            'Pending',
            'Reviewed',
            'FalsePositive',
            'ConfirmedFraud'
        )
    )
    BEGIN
        ALTER TABLE dbo.FraudAlerts
        ADD CONSTRAINT CK_FraudAlerts_ReviewStatus
        CHECK
        (
            ReviewStatus IN
            (
                'Pending',
                'Reviewed',
                'FalsePositive',
                'ConfirmedFraud'
            )
        );
    END
    ELSE
    BEGIN
        PRINT 'WARNING: Invalid existing review statuses.';
        PRINT 'ReviewStatus CHECK was not added.';
    END;
END;
GO


-- ============================================================
-- 14. AUDIT LOGS
-- ============================================================

IF OBJECT_ID(N'dbo.AuditLogs', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.AuditLogs
    (
        AuditID BIGINT IDENTITY(1,1)
            CONSTRAINT PK_AuditLogs PRIMARY KEY,

        ActionType VARCHAR(40) NULL,

        EntityName VARCHAR(40) NULL,

        EntityID BIGINT NULL,

        Description NVARCHAR(500) NULL,

        CreatedAt DATETIME2 NOT NULL
            CONSTRAINT DF_AuditLogs_CreatedAt
            DEFAULT SYSDATETIME()
    );
END;
GO


-- ============================================================
-- 15. DEFAULT FRAUD RULE - HIGH AMOUNT
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM dbo.FraudRules
    WHERE RuleType = 'HighAmount'
)
BEGIN
    INSERT INTO dbo.FraudRules
    (
        RuleName,
        RuleType,
        ThresholdValue,
        TimeWindowMinutes
    )
    VALUES
    (
        'High Value Transaction',
        'HighAmount',
        50000,
        60
    );
END;
GO


-- ============================================================
-- 16. DEFAULT FRAUD RULE - FREQUENT
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM dbo.FraudRules
    WHERE RuleType = 'Frequent'
)
BEGIN
    INSERT INTO dbo.FraudRules
    (
        RuleName,
        RuleType,
        ThresholdValue,
        TimeWindowMinutes
    )
    VALUES
    (
        'Frequent Transactions',
        'Frequent',
        5,
        10
    );
END;
GO


-- ============================================================
-- 17. DEFAULT FRAUD RULE - REPEATED AMOUNT
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM dbo.FraudRules
    WHERE RuleType = 'RepeatedAmount'
)
BEGIN
    INSERT INTO dbo.FraudRules
    (
        RuleName,
        RuleType,
        ThresholdValue,
        TimeWindowMinutes
    )
    VALUES
    (
        'Repeated Same Amount',
        'RepeatedAmount',
        3,
        60
    );
END;
GO


-- ============================================================
-- 18. ACCOUNT SUMMARY VIEW
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
-- 19. FRAUD ALERT DETAILS VIEW
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
-- 20. PERFORMANCE INDEXES
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Accounts')
      AND name = N'IX_Accounts_CustomerID'
)
BEGIN
    CREATE INDEX IX_Accounts_CustomerID
    ON dbo.Accounts(CustomerID);
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Transactions')
      AND name = N'IX_Transactions_Date'
)
BEGIN
    CREATE INDEX IX_Transactions_Date
    ON dbo.Transactions(TransactionDate);
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Transactions')
      AND name = N'IX_Transactions_FromAccount'
)
BEGIN
    CREATE INDEX IX_Transactions_FromAccount
    ON dbo.Transactions
    (
        FromAccountID,
        TransactionDate
    );
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Transactions')
      AND name = N'IX_Transactions_ToAccount'
)
BEGIN
    CREATE INDEX IX_Transactions_ToAccount
    ON dbo.Transactions
    (
        ToAccountID,
        TransactionDate
    );
END;
GO


-- ============================================================
-- 21. VERIFY TABLES AND RECORD COUNTS
-- ============================================================

SELECT
    'Customers' AS TableName,
    COUNT(*) AS RecordCount
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
-- 22. VERIFY FRAUD RULES
-- ============================================================

SELECT
    RuleID,
    RuleName,
    RuleType,
    ThresholdValue,
    TimeWindowMinutes,
    IsActive
FROM dbo.FraudRules
ORDER BY RuleID;
GO


-- ============================================================
-- 23. VERIFY FRAUD REVIEW STATUSES
-- ============================================================

SELECT
    ReviewStatus,
    COUNT(*) AS AlertCount
FROM dbo.FraudAlerts
GROUP BY ReviewStatus
ORDER BY ReviewStatus;
GO


-- ============================================================
-- 24. VERIFY FRAUD ALERT DETAILS VIEW
-- ============================================================

SELECT
    AlertID,
    TransactionID,
    RuleName,
    TransactionType,
    SenderCustomer,
    SenderAccountNumber,
    ReceiverCustomer,
    ReceiverAccountNumber,
    Amount,
    RiskLevel,
    ReviewStatus
FROM dbo.vw_FraudAlertDetails
ORDER BY AlertID DESC;
GO


-- ============================================================
-- 25. VERIFY USERS
-- ============================================================

SELECT
    UserID,
    CustomerID,
    Email,
    Role,
    IsActive,
    CreatedAt,
    LastLoginAt
FROM dbo.Users
ORDER BY UserID;
GO


-- ============================================================
-- 26. VERIFY CUSTOMERS
-- ============================================================

SELECT
    CustomerID,
    FirstName,
    LastName,
    NationalID,
    Phone,
    Email,
    Address,
    IsActive
FROM dbo.Customers
ORDER BY CustomerID;
GO


-- ============================================================
-- 27. VERIFY ACCOUNTS
-- ============================================================

SELECT
    AccountID,
    CustomerID,
    AccountNumber,
    AccountType,
    Balance,
    Currency,
    IsActive
FROM dbo.Accounts
ORDER BY AccountID;
GO


-- ============================================================
-- 28. VERIFY TRANSACTIONS
-- ============================================================

SELECT
    TransactionID,
    FromAccountID,
    ToAccountID,
    TransactionType,
    Amount,
    Description,
    TransactionDate,
    Status
FROM dbo.Transactions
ORDER BY TransactionID DESC;
GO


-- ============================================================
-- 29. VERIFY INDEXES
-- ============================================================

SELECT
    OBJECT_NAME(i.object_id) AS TableName,
    i.name AS IndexName,
    i.is_unique AS IsUnique,
    i.has_filter AS HasFilter,
    i.filter_definition AS FilterDefinition
FROM sys.indexes AS i
WHERE i.object_id IN
(
    OBJECT_ID(N'dbo.Customers'),
    OBJECT_ID(N'dbo.Users'),
    OBJECT_ID(N'dbo.Accounts'),
    OBJECT_ID(N'dbo.Transactions')
)
AND i.name IS NOT NULL
ORDER BY TableName, IndexName;
GO


-- ============================================================
-- 30. ADMIN DASHBOARD - SUMMARY
-- ============================================================

SELECT
    (
        SELECT COUNT(*)
        FROM dbo.Customers
        WHERE IsActive = 1
    ) AS ActiveCustomers,

    (
        SELECT COUNT(*)
        FROM dbo.Accounts
        WHERE IsActive = 1
    ) AS ActiveAccounts,

    (
        SELECT COUNT(*)
        FROM dbo.Transactions
        WHERE TransactionDate >=
              CONVERT(DATE, GETDATE())
          AND TransactionDate <
              DATEADD(
                  DAY,
                  1,
                  CONVERT(DATE, GETDATE())
              )
    ) AS TodayTransactions,

    (
        SELECT COUNT(*)
        FROM dbo.FraudAlerts
        WHERE ReviewStatus = 'Pending'
    ) AS PendingFraudAlerts;
GO


-- ============================================================
-- 31. ADMIN DASHBOARD - TOTAL BALANCE
-- ============================================================

SELECT
    COALESCE(SUM(Balance), 0) AS TotalBalance
FROM dbo.Accounts
WHERE IsActive = 1;
GO


-- ============================================================
-- 32. CUSTOMER DASHBOARD EXAMPLE
-- ============================================================

DECLARE @CustomerID INT = 1;

SELECT
    (
        SELECT COUNT(*)
        FROM dbo.Accounts
        WHERE CustomerID = @CustomerID
          AND IsActive = 1
    ) AS MyAccounts,

    (
        SELECT COALESCE(SUM(Balance), 0)
        FROM dbo.Accounts
        WHERE CustomerID = @CustomerID
          AND IsActive = 1
    ) AS MyBalance,

    (
        SELECT COUNT(*)
        FROM dbo.Transactions AS t

        LEFT JOIN dbo.Accounts AS f
          ON f.AccountID = t.FromAccountID

        LEFT JOIN dbo.Accounts AS d
          ON d.AccountID = t.ToAccountID

        WHERE f.CustomerID = @CustomerID
           OR d.CustomerID = @CustomerID
    ) AS MyTransactions;
GO


-- ============================================================
-- 33. SETUP COMPLETE
-- ============================================================

PRINT '============================================';
PRINT 'BankingFraudDB setup completed.';
PRINT '7 tables and 2 views are defined.';
PRINT 'Fraud rules and review statuses configured.';
PRINT 'Existing records have not been deleted.';
PRINT '============================================';
GO

-- ============================================================
-- 34. ALL TABLE DATA
-- ============================================================

SELECT * FROM FraudRules;
SELECT * FROM Users;
SELECT * FROM Accounts;
SELECT * FROM Transactions;
SELECT * FROM FraudAlerts;
SELECT * FROM AuditLogs;
SELECT * FROM Customers;

-- ============================================================
-- 35. SHOW THE NUMBERS
-- ============================================================

SELECT 'Customers' AS TableName, COUNT(*) AS RecordCount FROM Customers
UNION ALL
SELECT 'Accounts', COUNT(*) FROM Accounts
UNION ALL
SELECT 'Transactions', COUNT(*) FROM Transactions
UNION ALL
SELECT 'FraudAlerts', COUNT(*) FROM FraudAlerts
UNION ALL
SELECT 'AuditLogs', COUNT(*) FROM AuditLogs
UNION ALL
SELECT 'FraudRules', COUNT(*) FROM FraudRules
UNION ALL
SELECT 'Users', COUNT(*) FROM Users;
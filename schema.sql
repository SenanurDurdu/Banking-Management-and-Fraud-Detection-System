
-- ============================================================
-- BANKING MANAGEMENT AND FRAUD DETECTION SYSTEM
-- DATABASE SCHEMA - MICROSOFT SQL SERVER
-- ============================================================
--
-- Tables:
-- 1. Customers
-- 2. Users
-- 3. Accounts
-- 4. Transactions
-- 5. FraudRules
-- 6. FraudAlerts
-- 7. AuditLogs
--
-- Features:
-- - Admin and Customer authentication
-- - Unique National ID
-- - Unique customer phone number
-- - Unique email address
-- - One login account per customer
-- - Bank account management
-- - Deposit, Withdrawal and Transfer
-- - Fraud detection rules
-- - Fraud alerts and audit logs
-- - Account summary view
-- - Database verification queries
--
-- This script does not delete existing customer data.
-- Admin credentials are initialized by app.py.
-- ============================================================


-- ============================================================
-- 1. CREATE DATABASE
-- ============================================================

IF DB_ID('BankingFraudDB') IS NULL
BEGIN
    CREATE DATABASE BankingFraudDB;
END;
GO

USE BankingFraudDB;
GO


-- ============================================================
-- 2. CUSTOMERS TABLE
-- ============================================================

IF OBJECT_ID('dbo.Customers', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Customers
    (
        CustomerID INT IDENTITY(1,1) PRIMARY KEY,

        FirstName NVARCHAR(60) NOT NULL,

        LastName NVARCHAR(60) NOT NULL,

        NationalID CHAR(11) NOT NULL UNIQUE,

        Phone NVARCHAR(20) NULL,

        Email NVARCHAR(120) NULL,

        Address NVARCHAR(255) NULL,

        CreatedAt DATETIME2
            DEFAULT SYSDATETIME(),

        IsActive BIT
            DEFAULT 1,

        CONSTRAINT UQ_Customers_Email
            UNIQUE (Email)
    );
END;
GO


-- ============================================================
-- 3. CUSTOMER TABLE UPDATES
-- Compatibility with the original schema
-- ============================================================

IF COL_LENGTH('dbo.Customers', 'Phone') IS NULL
BEGIN
    ALTER TABLE dbo.Customers
    ADD Phone NVARCHAR(20) NULL;
END;
GO

IF COL_LENGTH('dbo.Customers', 'Address') IS NULL
BEGIN
    ALTER TABLE dbo.Customers
    ADD Address NVARCHAR(255) NULL;
END;
GO

-- Original Address column was NVARCHAR(250).
-- The current application supports up to 255 characters.

IF EXISTS
(
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.Customers')
      AND name = 'Address'
      AND max_length = 500
)
BEGIN
    ALTER TABLE dbo.Customers
    ALTER COLUMN Address NVARCHAR(255) NULL;
END;
GO


-- ============================================================
-- 4. UNIQUE CUSTOMER PHONE NUMBER
-- ============================================================
-- Same phone number cannot be registered twice.
-- NULL and empty legacy values are excluded.
-- ============================================================


USE BankingFraudDB;
GO

-- ============================================================
-- UNIQUE CUSTOMER PHONE NUMBER
-- ============================================================

-- Check whether duplicate phone numbers exist
IF EXISTS
(
    SELECT Phone
    FROM dbo.Customers
    WHERE Phone IS NOT NULL
      AND Phone <> ''
    GROUP BY Phone
    HAVING COUNT(*) > 1
)
BEGIN
    PRINT 'ERROR: Duplicate phone numbers exist.';
    PRINT 'Please correct duplicate phone numbers first.';
END
ELSE
BEGIN
    -- Create unique index only if it does not exist
    IF NOT EXISTS
    (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'UX_Customers_Phone'
          AND object_id = OBJECT_ID('dbo.Customers')
    )
    BEGIN
        CREATE UNIQUE INDEX UX_Customers_Phone
        ON dbo.Customers(Phone)
        WHERE Phone IS NOT NULL
          AND Phone <> '';

        PRINT 'Unique phone index created successfully.';
    END
    ELSE
    BEGIN
        PRINT 'Unique phone index already exists.';
    END
END;
GO



-- ============================================================
-- 5. USERS TABLE
-- AUTHENTICATION AND ROLE MANAGEMENT
-- ============================================================
-- Admin users have CustomerID = NULL.
-- Customer users must have a CustomerID.
-- PasswordHash stores the Argon2 hash created by app.py.
-- ============================================================

IF OBJECT_ID('dbo.Users', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Users
    (
        UserID INT IDENTITY(1,1) PRIMARY KEY,

        CustomerID INT NULL
            REFERENCES dbo.Customers(CustomerID),

        Email NVARCHAR(120) NOT NULL,

        PasswordHash NVARCHAR(255) NOT NULL,

        Role VARCHAR(20) NOT NULL
            CONSTRAINT CK_Users_Role
            CHECK (Role IN ('Admin', 'Customer')),

        IsActive BIT NOT NULL
            CONSTRAINT DF_Users_IsActive
            DEFAULT 1,

        CreatedAt DATETIME2 NOT NULL
            CONSTRAINT DF_Users_CreatedAt
            DEFAULT SYSDATETIME(),

        LastLoginAt DATETIME2 NULL,

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
-- 6. UNIQUE USER EMAIL
-- ============================================================
-- Prevents multiple login accounts with the same email.
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = 'UX_Users_Email'
      AND object_id = OBJECT_ID('dbo.Users')
)
BEGIN
    CREATE UNIQUE INDEX UX_Users_Email
    ON dbo.Users(Email);
END;
GO


-- ============================================================
-- 7. ONE USER ACCOUNT PER CUSTOMER
-- ============================================================
-- Each customer can have only one login account.
-- Multiple Admin users are allowed.
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = 'UX_Users_CustomerID'
      AND object_id = OBJECT_ID('dbo.Users')
)
BEGIN
    CREATE UNIQUE INDEX UX_Users_CustomerID
    ON dbo.Users(CustomerID)
    WHERE CustomerID IS NOT NULL;
END;
GO


-- ============================================================
-- 8. ACCOUNTS TABLE
-- ============================================================

IF OBJECT_ID('dbo.Accounts', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Accounts
    (
        AccountID INT IDENTITY(1,1) PRIMARY KEY,

        CustomerID INT NOT NULL
            REFERENCES dbo.Customers(CustomerID),

        AccountNumber CHAR(18) NOT NULL UNIQUE,

        AccountType VARCHAR(20) NOT NULL
            CHECK
            (
                AccountType IN ('Checking', 'Savings')
            ),

        Balance DECIMAL(18,2) NOT NULL
            DEFAULT 0
            CHECK (Balance >= 0),

        Currency CHAR(3) NOT NULL
            DEFAULT 'TRY',

        CreatedAt DATETIME2
            DEFAULT SYSDATETIME(),

        IsActive BIT
            DEFAULT 1
    );
END;
GO


-- ============================================================
-- 9. TRANSACTIONS TABLE
-- ============================================================

IF OBJECT_ID('dbo.Transactions', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Transactions
    (
        TransactionID BIGINT IDENTITY(1,1) PRIMARY KEY,

        FromAccountID INT NULL
            REFERENCES dbo.Accounts(AccountID),

        ToAccountID INT NULL
            REFERENCES dbo.Accounts(AccountID),

        TransactionType VARCHAR(20) NOT NULL
            CHECK
            (
                TransactionType IN
                (
                    'Deposit',
                    'Withdrawal',
                    'Transfer'
                )
            ),

        Amount DECIMAL(18,2) NOT NULL
            CHECK (Amount > 0),

        Description NVARCHAR(250) NULL,

        TransactionDate DATETIME2
            DEFAULT SYSDATETIME(),

        Status VARCHAR(20) NOT NULL
            DEFAULT 'Completed'
    );
END;
GO


-- ============================================================
-- 10. FRAUD RULES TABLE
-- ============================================================

IF OBJECT_ID('dbo.FraudRules', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.FraudRules
    (
        RuleID INT IDENTITY(1,1) PRIMARY KEY,

        RuleName NVARCHAR(100) NOT NULL UNIQUE,

        RuleType VARCHAR(30) NOT NULL
            CHECK
            (
                RuleType IN
                (
                    'HighAmount',
                    'Frequent',
                    'RepeatedAmount'
                )
            ),

        ThresholdValue DECIMAL(18,2) NOT NULL,

        TimeWindowMinutes INT NOT NULL
            DEFAULT 60,

        IsActive BIT
            DEFAULT 1
    );
END;
GO


-- ============================================================
-- 11. FRAUD ALERTS TABLE
-- ============================================================

IF OBJECT_ID('dbo.FraudAlerts', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.FraudAlerts
    (
        AlertID BIGINT IDENTITY(1,1) PRIMARY KEY,

        TransactionID BIGINT NOT NULL
            REFERENCES dbo.Transactions(TransactionID),

        RuleID INT NOT NULL
            REFERENCES dbo.FraudRules(RuleID),

        AlertDescription NVARCHAR(500) NOT NULL,

        RiskLevel VARCHAR(10) NOT NULL
            DEFAULT 'Medium',

        ReviewStatus VARCHAR(20) NOT NULL
            DEFAULT 'Pending',

        CreatedAt DATETIME2
            DEFAULT SYSDATETIME(),

        ReviewedAt DATETIME2 NULL,

        CONSTRAINT UQ_Alert
            UNIQUE (TransactionID, RuleID)
    );
END;
GO


-- ============================================================
-- 12. AUDIT LOGS TABLE
-- ============================================================

IF OBJECT_ID('dbo.AuditLogs', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.AuditLogs
    (
        AuditID BIGINT IDENTITY(1,1) PRIMARY KEY,

        ActionType VARCHAR(40) NULL,

        EntityName VARCHAR(40) NULL,

        EntityID BIGINT NULL,

        Description NVARCHAR(500) NULL,

        CreatedAt DATETIME2
            DEFAULT SYSDATETIME()
    );
END;
GO


-- ============================================================
-- 13. DEFAULT FRAUD DETECTION RULES
-- ============================================================
-- Existing rules are preserved.
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
-- 14. ACCOUNT SUMMARY VIEW
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

FROM dbo.Accounts a
JOIN dbo.Customers c
    ON a.CustomerID = c.CustomerID;
GO


-- ============================================================
-- 15. PERFORMANCE INDEXES
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_Accounts_CustomerID'
      AND object_id = OBJECT_ID('dbo.Accounts')
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
    WHERE name = 'IX_Transactions_Date'
      AND object_id = OBJECT_ID('dbo.Transactions')
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
    WHERE name = 'IX_Transactions_FromAccount'
      AND object_id = OBJECT_ID('dbo.Transactions')
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
    WHERE name = 'IX_Transactions_ToAccount'
      AND object_id = OBJECT_ID('dbo.Transactions')
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
-- 16. VERIFY DATABASE TABLES
-- ============================================================

SELECT
    'Customers' AS TableName,
    COUNT(*) AS RecordCount
FROM dbo.Customers

UNION ALL

SELECT
    'Users',
    COUNT(*)
FROM dbo.Users

UNION ALL

SELECT
    'Accounts',
    COUNT(*)
FROM dbo.Accounts

UNION ALL

SELECT
    'Transactions',
    COUNT(*)
FROM dbo.Transactions

UNION ALL

SELECT
    'FraudRules',
    COUNT(*)
FROM dbo.FraudRules

UNION ALL

SELECT
    'FraudAlerts',
    COUNT(*)
FROM dbo.FraudAlerts

UNION ALL

SELECT
    'AuditLogs',
    COUNT(*)
FROM dbo.AuditLogs;
GO


-- ============================================================
-- 17. VERIFY USERS
-- ============================================================
-- Password hashes are intentionally excluded.
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
-- 18. VERIFY CUSTOMERS
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
-- 19. VERIFY UNIQUE PHONE NUMBERS
-- ============================================================
-- No rows means there are no duplicate non-empty phones.
-- ============================================================

SELECT
    Phone,
    COUNT(*) AS Total
FROM dbo.Customers
WHERE Phone IS NOT NULL
  AND Phone <> ''
GROUP BY Phone
HAVING COUNT(*) > 1;
GO


-- ============================================================
-- 20. VERIFY USER INDEXES
-- ============================================================

SELECT
    i.name AS IndexName,
    i.is_unique AS IsUnique,
    i.has_filter AS HasFilter,
    i.filter_definition AS FilterDefinition
FROM sys.indexes i
WHERE i.object_id = OBJECT_ID('dbo.Users')
  AND i.name IS NOT NULL;
GO


-- ============================================================
-- 21. VERIFY CUSTOMER PHONE INDEX
-- ============================================================

SELECT
    i.name AS IndexName,
    i.is_unique AS IsUnique,
    i.has_filter AS HasFilter,
    i.filter_definition AS FilterDefinition
FROM sys.indexes i
WHERE i.object_id = OBJECT_ID('dbo.Customers')
  AND i.name = 'UX_Customers_Phone';
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
-- 23. VERIFY CUSTOMER LOGIN ACCOUNTS
-- ============================================================

SELECT
    c.CustomerID,
    c.FirstName,
    c.LastName,
    c.Email,

    CASE
        WHEN u.UserID IS NULL
            THEN 'NO LOGIN ACCOUNT'
        ELSE 'LOGIN ACCOUNT EXISTS'
    END AS LoginStatus

FROM dbo.Customers c

LEFT JOIN dbo.Users u
    ON c.CustomerID = u.CustomerID
   AND u.Role = 'Customer'

ORDER BY c.CustomerID;
GO


-- ============================================================
-- SCHEMA SETUP COMPLETED
-- ============================================================

PRINT 'BankingFraudDB schema setup completed.';
GO

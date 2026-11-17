
-- ============================================================
-- BANKING MANAGEMENT & FRAUD DETECTION SYSTEM
-- FILE: 01_schema.sql
-- PURPOSE: Database and core tables
-- ============================================================
-- Run this file first.
-- Existing tables and records are preserved.
-- SQL Server 2016 SP1 or later is recommended.
-- ============================================================

IF DB_ID(N'BankingFraudDB') IS NULL
BEGIN
    CREATE DATABASE BankingFraudDB;
END;
GO

USE BankingFraudDB;
GO


-- ============================================================
-- 1. CUSTOMERS
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
-- 2. USERS
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
-- 3. ACCOUNTS
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
-- 4. TRANSACTIONS
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
-- 5. FRAUD RULES
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
-- 6. FRAUD ALERTS
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
        ReviewedByUserID INT NULL,
        ReviewNote NVARCHAR(500) NULL,

        CONSTRAINT FK_FraudAlerts_Transactions
            FOREIGN KEY (TransactionID)
            REFERENCES dbo.Transactions(TransactionID),

        CONSTRAINT FK_FraudAlerts_Rules
            FOREIGN KEY (RuleID)
            REFERENCES dbo.FraudRules(RuleID),

        CONSTRAINT FK_FraudAlerts_ReviewedBy
            FOREIGN KEY (ReviewedByUserID)
            REFERENCES dbo.Users(UserID),

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
-- 7. AUDIT LOGS
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
        UserID INT NULL,

        CreatedAt DATETIME2 NOT NULL
            CONSTRAINT DF_AuditLogs_CreatedAt
            DEFAULT SYSDATETIME(),

        CONSTRAINT FK_AuditLogs_Users
            FOREIGN KEY (UserID)
            REFERENCES dbo.Users(UserID)
    );
END;
GO


-- ============================================================
-- 8. NOTIFICATIONS
-- ============================================================

IF OBJECT_ID(N'dbo.Notifications', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Notifications
    (
        NotificationID INT IDENTITY(1,1)
            CONSTRAINT PK_Notifications PRIMARY KEY,

        CustomerID INT NOT NULL,
        Title NVARCHAR(150) NOT NULL,
        Message NVARCHAR(1000) NOT NULL,

        NotificationType NVARCHAR(30) NOT NULL
            CONSTRAINT DF_Notifications_Type
            DEFAULT 'System',

        IsRead BIT NOT NULL
            CONSTRAINT DF_Notifications_IsRead
            DEFAULT 0,

        CreatedAt DATETIME2 NOT NULL
            CONSTRAINT DF_Notifications_CreatedAt
            DEFAULT SYSDATETIME(),

        CONSTRAINT FK_Notifications_Customers
            FOREIGN KEY (CustomerID)
            REFERENCES dbo.Customers(CustomerID)
    );
END;
GO


-- ============================================================
-- VERIFICATION
-- ============================================================

SELECT
    t.name AS TableName
FROM sys.tables AS t
WHERE t.schema_id = SCHEMA_ID(N'dbo')
  AND t.name IN
  (
      N'Customers',
      N'Users',
      N'Accounts',
      N'Transactions',
      N'FraudRules',
      N'FraudAlerts',
      N'AuditLogs',
      N'Notifications'
  )
ORDER BY t.name;
GO

PRINT '01_schema.sql completed.';
GO

IF DB_ID('BankingFraudDB') IS NULL
    CREATE DATABASE BankingFraudDB;
GO

USE BankingFraudDB;
GO

-- 1. CUSTOMERS TABLE
CREATE TABLE Customers(
    CustomerID INT IDENTITY PRIMARY KEY,
    FirstName NVARCHAR(60) NOT NULL,
    LastName NVARCHAR(60) NOT NULL,
    NationalID CHAR(11) NOT NULL UNIQUE,
    Phone NVARCHAR(20),
    Email NVARCHAR(120),
    Address NVARCHAR(250),
    CreatedAt DATETIME2 DEFAULT SYSDATETIME(),
    IsActive BIT DEFAULT 1
);
GO

-- 2. ACCOUNTS TABLE
CREATE TABLE Accounts(
    AccountID INT IDENTITY PRIMARY KEY,
    CustomerID INT NOT NULL
        REFERENCES Customers(CustomerID),

    AccountNumber CHAR(18) NOT NULL UNIQUE,

    AccountType VARCHAR(20) NOT NULL
        CHECK(AccountType IN ('Checking','Savings')),

    Balance DECIMAL(18,2) NOT NULL DEFAULT 0
        CHECK(Balance >= 0),

    Currency CHAR(3) NOT NULL DEFAULT 'TRY',

    CreatedAt DATETIME2 DEFAULT SYSDATETIME(),
    IsActive BIT DEFAULT 1
);
GO

-- 3. TRANSACTIONS TABLE
CREATE TABLE Transactions(
    TransactionID BIGINT IDENTITY PRIMARY KEY,

    FromAccountID INT NULL
        REFERENCES Accounts(AccountID),

    ToAccountID INT NULL
        REFERENCES Accounts(AccountID),

    TransactionType VARCHAR(20) NOT NULL
        CHECK(TransactionType IN ('Deposit','Withdrawal','Transfer')),

    Amount DECIMAL(18,2) NOT NULL
        CHECK(Amount > 0),

    Description NVARCHAR(250),

    TransactionDate DATETIME2 DEFAULT SYSDATETIME(),

    Status VARCHAR(20) NOT NULL DEFAULT 'Completed'
);
GO

-- 4. FRAUD RULES TABLE
CREATE TABLE FraudRules(
    RuleID INT IDENTITY PRIMARY KEY,

    RuleName NVARCHAR(100) NOT NULL UNIQUE,

    RuleType VARCHAR(30) NOT NULL
        CHECK(RuleType IN ('HighAmount','Frequent','RepeatedAmount')),

    ThresholdValue DECIMAL(18,2) NOT NULL,

    TimeWindowMinutes INT NOT NULL DEFAULT 60,

    IsActive BIT DEFAULT 1
);
GO

-- 5. FRAUD ALERTS TABLE
CREATE TABLE FraudAlerts(
    AlertID BIGINT IDENTITY PRIMARY KEY,

    TransactionID BIGINT NOT NULL
        REFERENCES Transactions(TransactionID),

    RuleID INT NOT NULL
        REFERENCES FraudRules(RuleID),

    AlertDescription NVARCHAR(500) NOT NULL,

    RiskLevel VARCHAR(10) NOT NULL DEFAULT 'Medium',

    ReviewStatus VARCHAR(20) NOT NULL DEFAULT 'Pending',

    CreatedAt DATETIME2 DEFAULT SYSDATETIME(),

    ReviewedAt DATETIME2 NULL,

    CONSTRAINT UQ_Alert UNIQUE(TransactionID, RuleID)
);
GO

-- 6. AUDIT LOGS TABLE
CREATE TABLE AuditLogs(
    AuditID BIGINT IDENTITY PRIMARY KEY,

    ActionType VARCHAR(40),

    EntityName VARCHAR(40),

    EntityID BIGINT NULL,

    Description NVARCHAR(500),

    CreatedAt DATETIME2 DEFAULT SYSDATETIME()
);
GO

-- DEFAULT FRAUD RULES

INSERT INTO FraudRules
(RuleName, RuleType, ThresholdValue, TimeWindowMinutes)

VALUES
('High Value Transaction', 'HighAmount', 50000, 60),

('Frequent Transactions', 'Frequent', 5, 10),

('Repeated Same Amount', 'RepeatedAmount', 3, 60);
GO

-- ACCOUNT SUMMARY VIEW

CREATE VIEW vw_AccountSummary AS

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

FROM Accounts a

JOIN Customers c
ON a.CustomerID = c.CustomerID;
GO
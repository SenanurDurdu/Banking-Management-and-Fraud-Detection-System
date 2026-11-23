-- ============================================================
-- NG BANK
-- FILE: 01_schema.sql
-- DATABASE: BankingFraudDB
-- PURPOSE: Create all 20 application tables from the start
-- TARGET: Microsoft SQL Server
-- NOTE: Run on a new, empty test database
-- ============================================================

IF DB_ID(N'BankingFraudDB_Test') IS NULL
BEGIN
    CREATE DATABASE BankingFraudDB_Test;
END;
GO

USE BankingFraudDB_Test;
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

        IsFrozen BIT NOT NULL
            CONSTRAINT DF_Accounts_IsFrozen
            DEFAULT 0,

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

        TransactionID BIGINT NULL,
        CardTransactionID BIGINT NULL,
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

        CONSTRAINT CK_FraudAlerts_TransactionReference
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
            ),

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
-- 9. CREDIT CARD APPLICATIONS
-- ============================================================

IF OBJECT_ID(N'dbo.CreditCardApplications', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.CreditCardApplications
    (
        ApplicationID BIGINT IDENTITY(1,1)
            CONSTRAINT PK_CreditCardApplications PRIMARY KEY,

        CustomerID INT NOT NULL,
        CardType VARCHAR(20) NOT NULL,
        RequestedLimit DECIMAL(18,2) NOT NULL,

        Currency CHAR(3) NOT NULL
            CONSTRAINT DF_CreditCardApplications_Currency
            DEFAULT 'TRY',

        ApplicationStatus VARCHAR(20) NOT NULL
            CONSTRAINT DF_CreditCardApplications_Status
            DEFAULT 'Pending',

        AppliedAt DATETIME2 NOT NULL
            CONSTRAINT DF_CreditCardApplications_AppliedAt
            DEFAULT SYSDATETIME(),

        ReviewedByUserID INT NULL,
        ReviewedAt DATETIME2 NULL,
        ReviewNote NVARCHAR(500) NULL,

        CONSTRAINT FK_CreditCardApplications_Customers
            FOREIGN KEY (CustomerID)
            REFERENCES dbo.Customers(CustomerID),

        CONSTRAINT FK_CreditCardApplications_Users
            FOREIGN KEY (ReviewedByUserID)
            REFERENCES dbo.Users(UserID),

        CONSTRAINT CK_CreditCardApplications_CardType
            CHECK (CardType IN ('Standard', 'Gold')),

        CONSTRAINT CK_CreditCardApplications_Limit
            CHECK
            (
                RequestedLimit IN
                (5000, 10000, 25000, 50000)
            ),

        CONSTRAINT CK_CreditCardApplications_Currency
            CHECK (Currency = 'TRY'),

        CONSTRAINT CK_CreditCardApplications_Status
            CHECK
            (
                ApplicationStatus IN
                ('Pending', 'Approved', 'Rejected')
            )
    );
END;
GO

-- ============================================================
-- 10. CREDIT CARDS
-- ============================================================

IF OBJECT_ID(N'dbo.CreditCards', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.CreditCards
    (
        CreditCardID BIGINT IDENTITY(1,1)
            CONSTRAINT PK_CreditCards PRIMARY KEY,

        ApplicationID BIGINT NOT NULL,
        CustomerID INT NOT NULL,
        LinkedAccountID INT NOT NULL,
        CardNumber VARCHAR(19) NOT NULL,
        CardType VARCHAR(20) NOT NULL,
        CreditLimit DECIMAL(18,2) NOT NULL,

        OutstandingBalance DECIMAL(18,2) NOT NULL
            CONSTRAINT DF_CreditCards_OutstandingBalance
            DEFAULT 0,

        Currency CHAR(3) NOT NULL
            CONSTRAINT DF_CreditCards_Currency
            DEFAULT 'TRY',

        CardStatus VARCHAR(20) NOT NULL
            CONSTRAINT DF_CreditCards_Status
            DEFAULT 'Active',

        IssuedAt DATETIME2 NOT NULL
            CONSTRAINT DF_CreditCards_IssuedAt
            DEFAULT SYSDATETIME(),

        ExpiresAt DATE NOT NULL,

        CONSTRAINT FK_CreditCards_Applications
            FOREIGN KEY (ApplicationID)
            REFERENCES dbo.CreditCardApplications(ApplicationID),

        CONSTRAINT FK_CreditCards_Customers
            FOREIGN KEY (CustomerID)
            REFERENCES dbo.Customers(CustomerID),

        CONSTRAINT FK_CreditCards_Accounts
            FOREIGN KEY (LinkedAccountID)
            REFERENCES dbo.Accounts(AccountID),

        CONSTRAINT UQ_CreditCards_Application
            UNIQUE (ApplicationID),

        CONSTRAINT UQ_CreditCards_Number
            UNIQUE (CardNumber),

        CONSTRAINT CK_CreditCards_Type
            CHECK (CardType IN ('Standard', 'Gold')),

        CONSTRAINT CK_CreditCards_Limit
            CHECK (CreditLimit > 0),

        CONSTRAINT CK_CreditCards_Balance
            CHECK
            (
                OutstandingBalance >= 0
                AND OutstandingBalance <= CreditLimit
            ),

        CONSTRAINT CK_CreditCards_Currency
            CHECK (Currency = 'TRY'),

        CONSTRAINT CK_CreditCards_Status
            CHECK
            (
                CardStatus IN
                ('Active', 'Frozen', 'Closed')
            )
    );
END;
GO

-- ============================================================
-- 11. CREDIT CARD TRANSACTIONS
-- ============================================================

IF OBJECT_ID(N'dbo.CreditCardTransactions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.CreditCardTransactions
    (
        CardTransactionID BIGINT IDENTITY(1,1)
            CONSTRAINT PK_CreditCardTransactions PRIMARY KEY,

        CreditCardID BIGINT NOT NULL,
        BankTransactionID BIGINT NULL,
        TransactionType VARCHAR(20) NOT NULL,
        Amount DECIMAL(18,2) NOT NULL,
        Description NVARCHAR(500) NULL,

        TransactionStatus VARCHAR(20) NOT NULL
            CONSTRAINT DF_CreditCardTransactions_Status
            DEFAULT 'Completed',

        CreatedAt DATETIME2 NOT NULL
            CONSTRAINT DF_CreditCardTransactions_CreatedAt
            DEFAULT SYSDATETIME(),

        CONSTRAINT FK_CreditCardTransactions_Cards
            FOREIGN KEY (CreditCardID)
            REFERENCES dbo.CreditCards(CreditCardID),

        CONSTRAINT FK_CreditCardTransactions_BankTransaction
            FOREIGN KEY (BankTransactionID)
            REFERENCES dbo.Transactions(TransactionID),

        CONSTRAINT CK_CreditCardTransactions_Type
            CHECK
            (
                TransactionType IN
                (
                    'Purchase',
                    'Payment',
                    'Refund',
                    'CashAdvance'
                )
            ),

        CONSTRAINT CK_CreditCardTransactions_Amount
            CHECK (Amount > 0),

        CONSTRAINT CK_CreditCardTransactions_Status
            CHECK
            (
                TransactionStatus IN
                (
                    'Completed',
                    'Declined',
                    'Reversed'
                )
            )
    );
END;
GO

-- ============================================================
-- 12. CUSTOMER ADDRESSES
-- ============================================================

IF OBJECT_ID(N'dbo.CustomerAddresses', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.CustomerAddresses
    (
        AddressID BIGINT IDENTITY(1,1)
            CONSTRAINT PK_CustomerAddresses PRIMARY KEY,

        CustomerID INT NOT NULL,

        AddressType VARCHAR(20) NOT NULL
            CONSTRAINT DF_CustomerAddresses_Type
            DEFAULT 'Other',

        AddressLine NVARCHAR(255) NOT NULL,
        City NVARCHAR(100) NULL,
        PostalCode NVARCHAR(20) NULL,

        IsPrimary BIT NOT NULL
            CONSTRAINT DF_CustomerAddresses_Primary
            DEFAULT 0,

        CreatedAt DATETIME2 NOT NULL
            CONSTRAINT DF_CustomerAddresses_Created
            DEFAULT SYSDATETIME(),

        CONSTRAINT FK_CustomerAddresses_Customers
            FOREIGN KEY (CustomerID)
            REFERENCES dbo.Customers(CustomerID),

        CONSTRAINT CK_CustomerAddresses_Type
            CHECK
            (
                AddressType IN ('Home', 'Work', 'Other')
            )
    );
END;
GO

-- ============================================================
-- 13. CUSTOMER CONTACTS
-- ============================================================

IF OBJECT_ID(N'dbo.CustomerContacts', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.CustomerContacts
    (
        ContactID BIGINT IDENTITY(1,1)
            CONSTRAINT PK_CustomerContacts PRIMARY KEY,

        CustomerID INT NOT NULL,
        ContactType VARCHAR(20) NOT NULL,
        ContactValue NVARCHAR(150) NOT NULL,

        IsPrimary BIT NOT NULL
            CONSTRAINT DF_CustomerContacts_Primary
            DEFAULT 0,

        CreatedAt DATETIME2 NOT NULL
            CONSTRAINT DF_CustomerContacts_Created
            DEFAULT SYSDATETIME(),

        CONSTRAINT FK_CustomerContacts_Customers
            FOREIGN KEY (CustomerID)
            REFERENCES dbo.Customers(CustomerID),

        CONSTRAINT CK_CustomerContacts_Type
            CHECK
            (
                ContactType IN ('Email', 'Phone', 'Other')
            )
    );
END;
GO

-- ============================================================
-- 14. BENEFICIARIES
-- ============================================================

IF OBJECT_ID(N'dbo.Beneficiaries', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Beneficiaries
    (
        BeneficiaryID BIGINT IDENTITY(1,1)
            CONSTRAINT PK_Beneficiaries PRIMARY KEY,

        CustomerID INT NOT NULL,
        DisplayName NVARCHAR(120) NOT NULL,
        AccountNumber VARCHAR(34) NOT NULL,

        IsActive BIT NOT NULL
            CONSTRAINT DF_Beneficiaries_Active
            DEFAULT 1,

        CreatedAt DATETIME2 NOT NULL
            CONSTRAINT DF_Beneficiaries_Created
            DEFAULT SYSDATETIME(),

        CONSTRAINT FK_Beneficiaries_Customers
            FOREIGN KEY (CustomerID)
            REFERENCES dbo.Customers(CustomerID),

        CONSTRAINT UQ_Beneficiaries_Customer_Account
            UNIQUE (CustomerID, AccountNumber)
    );
END;
GO

-- ============================================================
-- 15. ACCOUNT STATUS HISTORY
-- ============================================================

IF OBJECT_ID(N'dbo.AccountStatusHistory', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.AccountStatusHistory
    (
        StatusHistoryID BIGINT IDENTITY(1,1)
            CONSTRAINT PK_AccountStatusHistory PRIMARY KEY,

        AccountID INT NOT NULL,
        ChangedByUserID INT NULL,

        OldIsActive BIT NULL,
        NewIsActive BIT NULL,

        OldIsFrozen BIT NULL,
        NewIsFrozen BIT NULL,

        ChangeReason NVARCHAR(500) NULL,

        ChangedAt DATETIME2 NOT NULL
            CONSTRAINT DF_AccountStatusHistory_Changed
            DEFAULT SYSDATETIME(),

        CONSTRAINT FK_AccountStatusHistory_Accounts
            FOREIGN KEY (AccountID)
            REFERENCES dbo.Accounts(AccountID),

        CONSTRAINT FK_AccountStatusHistory_Users
            FOREIGN KEY (ChangedByUserID)
            REFERENCES dbo.Users(UserID)
    );
END;
GO

-- ============================================================
-- 16. TRANSACTION NOTES
-- ============================================================

IF OBJECT_ID(N'dbo.TransactionNotes', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.TransactionNotes
    (
        NoteID BIGINT IDENTITY(1,1)
            CONSTRAINT PK_TransactionNotes PRIMARY KEY,

        TransactionID BIGINT NOT NULL,
        CreatedByUserID INT NULL,
        NoteText NVARCHAR(1000) NOT NULL,

        CreatedAt DATETIME2 NOT NULL
            CONSTRAINT DF_TransactionNotes_Created
            DEFAULT SYSDATETIME(),

        CONSTRAINT FK_TransactionNotes_Transactions
            FOREIGN KEY (TransactionID)
            REFERENCES dbo.Transactions(TransactionID),

        CONSTRAINT FK_TransactionNotes_Users
            FOREIGN KEY (CreatedByUserID)
            REFERENCES dbo.Users(UserID)
    );
END;
GO

-- ============================================================
-- 17. FRAUD ALERT REVIEW HISTORY
-- ============================================================

IF OBJECT_ID(N'dbo.FraudAlertReviewHistory', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FraudAlertReviewHistory
    (
        ReviewHistoryID BIGINT IDENTITY(1,1)
            CONSTRAINT PK_FraudAlertReviewHistory PRIMARY KEY,

        AlertID BIGINT NOT NULL,
        ReviewedByUserID INT NULL,

        OldReviewStatus VARCHAR(20) NULL,
        NewReviewStatus VARCHAR(20) NOT NULL,

        ReviewNote NVARCHAR(500) NULL,

        ReviewedAt DATETIME2 NOT NULL
            CONSTRAINT DF_FraudAlertReviewHistory_Reviewed
            DEFAULT SYSDATETIME(),

        CONSTRAINT FK_FraudAlertReviewHistory_Alerts
            FOREIGN KEY (AlertID)
            REFERENCES dbo.FraudAlerts(AlertID),

        CONSTRAINT FK_FraudAlertReviewHistory_Users
            FOREIGN KEY (ReviewedByUserID)
            REFERENCES dbo.Users(UserID),

        CONSTRAINT CK_FraudAlertReviewHistory_Status
            CHECK
            (
                NewReviewStatus IN
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
-- 18. CREDIT CARD BILLING SETTINGS
-- ============================================================

IF OBJECT_ID(N'dbo.CreditCardBillingSettings', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.CreditCardBillingSettings
    (
        BillingSettingID BIGINT IDENTITY(1,1)
            CONSTRAINT PK_CreditCardBillingSettings PRIMARY KEY,

        CreditCardID BIGINT NOT NULL,

        ClosingDay TINYINT NOT NULL,
        DueDaysAfterClosing TINYINT NOT NULL,

        EffectiveFrom DATE NOT NULL
            CONSTRAINT DF_CreditCardBillingSettings_Effective
            DEFAULT CONVERT(DATE, SYSDATETIME()),

        UpdatedAt DATETIME2 NOT NULL
            CONSTRAINT DF_CreditCardBillingSettings_Updated
            DEFAULT SYSDATETIME(),

        CONSTRAINT FK_CreditCardBillingSettings_Cards
            FOREIGN KEY (CreditCardID)
            REFERENCES dbo.CreditCards(CreditCardID),

        CONSTRAINT UQ_CreditCardBillingSettings_Card
            UNIQUE (CreditCardID),

        CONSTRAINT CK_CreditCardBillingSettings_Closing
            CHECK (ClosingDay BETWEEN 1 AND 28),

        CONSTRAINT CK_CreditCardBillingSettings_Due
            CHECK (DueDaysAfterClosing BETWEEN 1 AND 28)
    );
END;
GO

-- ============================================================
-- 19. ACCOUNT DAILY BALANCES
-- ============================================================

IF OBJECT_ID(N'dbo.AccountDailyBalances', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.AccountDailyBalances
    (
        BalanceID BIGINT IDENTITY(1,1)
            CONSTRAINT PK_AccountDailyBalances
            PRIMARY KEY,

        AccountID INT NOT NULL,

        BalanceDate DATE NOT NULL,

        ClosingBalance DECIMAL(18,2) NOT NULL,

        RecordedAt DATETIME2 NOT NULL
            CONSTRAINT DF_AccountDailyBalances_RecordedAt
            DEFAULT SYSDATETIME(),

        CONSTRAINT FK_AccountDailyBalances_Accounts
            FOREIGN KEY (AccountID)
            REFERENCES dbo.Accounts(AccountID),

        CONSTRAINT UQ_AccountDailyBalances_AccountDate
            UNIQUE (AccountID, BalanceDate)
    );
END;
GO

-- ============================================================
-- 20. FRAUD RISK ASSESSMENTS
-- ============================================================

IF OBJECT_ID(N'dbo.FraudRiskAssessments', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FraudRiskAssessments
    (
        AssessmentID BIGINT IDENTITY(1,1)
            CONSTRAINT PK_FraudRiskAssessments
            PRIMARY KEY,

        AlertID BIGINT NOT NULL,

        RiskLevel VARCHAR(10) NOT NULL,

        ReviewStatus VARCHAR(20) NOT NULL,

        AssessedAt DATETIME2 NOT NULL
            CONSTRAINT DF_FraudRiskAssessments_AssessedAt
            DEFAULT SYSDATETIME(),

        CONSTRAINT FK_FraudRiskAssessments_Alerts
            FOREIGN KEY (AlertID)
            REFERENCES dbo.FraudAlerts(AlertID),

        CONSTRAINT UQ_FraudRiskAssessments_Alert
            UNIQUE (AlertID),

        CONSTRAINT CK_FraudRiskAssessments_Risk
            CHECK
            (
                RiskLevel IN
                (
                    'Low',
                    'Medium',
                    'High',
                    'Critical'
                )
            ),

        CONSTRAINT CK_FraudRiskAssessments_Status
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
-- 21. DEFERRED FOREIGN KEY
-- FraudAlerts references CreditCardTransactions.
-- Both tables must exist before this relationship is added.
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.foreign_keys
    WHERE name = N'FK_FraudAlerts_CardTransactions'
      AND parent_object_id = OBJECT_ID(N'dbo.FraudAlerts')
)
BEGIN
    ALTER TABLE dbo.FraudAlerts
    WITH CHECK
    ADD CONSTRAINT FK_FraudAlerts_CardTransactions
        FOREIGN KEY (CardTransactionID)
        REFERENCES dbo.CreditCardTransactions(CardTransactionID);
END;
GO

-- ============================================================
-- 22. FRAUD ALERT UNIQUE INDEXES
-- Prevent duplicate alerts for the same rule and transaction.
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_FraudAlerts_Transaction_Rule'
      AND object_id = OBJECT_ID(N'dbo.FraudAlerts')
)
BEGIN
    CREATE UNIQUE INDEX UX_FraudAlerts_Transaction_Rule
    ON dbo.FraudAlerts(TransactionID, RuleID)
    WHERE TransactionID IS NOT NULL;
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_FraudAlerts_CardTransaction_Rule'
      AND object_id = OBJECT_ID(N'dbo.FraudAlerts')
)
BEGIN
    CREATE UNIQUE INDEX UX_FraudAlerts_CardTransaction_Rule
    ON dbo.FraudAlerts(CardTransactionID, RuleID)
    WHERE CardTransactionID IS NOT NULL;
END;
GO

-- ============================================================
-- 23. INITIAL SCHEMA VERIFICATION
-- ============================================================

DECLARE @TableCount INT;

SELECT @TableCount = COUNT(*)
FROM sys.tables
WHERE schema_id = SCHEMA_ID(N'dbo')
  AND is_ms_shipped = 0;

SELECT @TableCount AS TotalApplicationTables;

IF @TableCount = 20
BEGIN
    PRINT 'NG BANK: All 20 application tables are present.';
END
ELSE
BEGIN
    PRINT 'NG BANK WARNING: Expected 20 tables, found '
          + CAST(@TableCount AS VARCHAR(10)) + '.';
END;
GO

-- ============================================================
-- 24. LIST ALL TABLES
-- ============================================================

SELECT
    ROW_NUMBER() OVER (ORDER BY t.name) AS RowNumber,
    t.name AS TableName
FROM sys.tables AS t
WHERE t.schema_id = SCHEMA_ID(N'dbo')
  AND t.is_ms_shipped = 0
ORDER BY t.name;
GO

-- ============================================================
-- 25. LIST FOREIGN KEY RELATIONSHIPS
-- ============================================================

SELECT
    fk.name AS ForeignKeyName,
    OBJECT_NAME(fk.parent_object_id) AS ChildTable,
    pc.name AS ChildColumn,
    OBJECT_NAME(fk.referenced_object_id) AS ParentTable,
    rc.name AS ParentColumn
FROM sys.foreign_keys AS fk
INNER JOIN sys.foreign_key_columns AS fkc
    ON fkc.constraint_object_id = fk.object_id
INNER JOIN sys.columns AS pc
    ON pc.object_id = fkc.parent_object_id
   AND pc.column_id = fkc.parent_column_id
INNER JOIN sys.columns AS rc
    ON rc.object_id = fkc.referenced_object_id
   AND rc.column_id = fkc.referenced_column_id
ORDER BY
    ChildTable,
    ForeignKeyName;
GO

PRINT '01_schema.sql completed.';
GO
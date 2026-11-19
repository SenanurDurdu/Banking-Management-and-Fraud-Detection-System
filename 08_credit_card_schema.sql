
USE BankingFraudDB;
GO

-- ============================================================
-- 08_credit_card_schema.sql
-- CREDIT CARD DATABASE SCHEMA
-- ============================================================

-- ============================================================
-- 1. CREDIT CARD APPLICATIONS
-- ============================================================

IF OBJECT_ID('dbo.CreditCardApplications', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.CreditCardApplications
    (
        ApplicationID BIGINT IDENTITY(1,1) NOT NULL
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
            CHECK (RequestedLimit IN
                (5000, 10000, 25000, 50000)),

        CONSTRAINT CK_CreditCardApplications_Currency
            CHECK (Currency = 'TRY'),

        CONSTRAINT CK_CreditCardApplications_Status
            CHECK (ApplicationStatus IN
                ('Pending', 'Approved', 'Rejected'))
    );
END;
GO

-- ============================================================
-- 2. CREDIT CARDS
-- ============================================================

IF OBJECT_ID('dbo.CreditCards', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.CreditCards
    (
        CreditCardID BIGINT IDENTITY(1,1) NOT NULL
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
            CHECK (
                OutstandingBalance >= 0
                AND OutstandingBalance <= CreditLimit
            ),

        CONSTRAINT CK_CreditCards_Currency
            CHECK (Currency = 'TRY'),

        CONSTRAINT CK_CreditCards_Status
            CHECK (CardStatus IN
                ('Active', 'Frozen', 'Closed'))
    );
END;
GO

-- ============================================================
-- 3. CREDIT CARD TRANSACTIONS
-- ============================================================

IF OBJECT_ID('dbo.CreditCardTransactions', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.CreditCardTransactions
    (
        CardTransactionID BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_CreditCardTransactions PRIMARY KEY,

        CreditCardID BIGINT NOT NULL,

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

        CONSTRAINT CK_CreditCardTransactions_Type
            CHECK (TransactionType IN
                ('Purchase', 'Payment', 'Refund')),

        CONSTRAINT CK_CreditCardTransactions_Amount
            CHECK (Amount > 0),

        CONSTRAINT CK_CreditCardTransactions_Status
            CHECK (TransactionStatus IN
                ('Completed', 'Declined', 'Reversed'))
    );
END;
GO

-- ============================================================
-- 4. INDEXES
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_CreditCardApplications_Customer'
      AND object_id = OBJECT_ID('dbo.CreditCardApplications')
)
BEGIN
    CREATE INDEX IX_CreditCardApplications_Customer
    ON dbo.CreditCardApplications
    (
        CustomerID,
        ApplicationStatus,
        AppliedAt
    );
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_CreditCards_Customer'
      AND object_id = OBJECT_ID('dbo.CreditCards')
)
BEGIN
    CREATE INDEX IX_CreditCards_Customer
    ON dbo.CreditCards
    (
        CustomerID,
        CardStatus
    );
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_CreditCardTransactions_Card'
      AND object_id = OBJECT_ID('dbo.CreditCardTransactions')
)
BEGIN
    CREATE INDEX IX_CreditCardTransactions_Card
    ON dbo.CreditCardTransactions
    (
        CreditCardID,
        CreatedAt
    );
END;
GO

-- ============================================================
-- 5. VERIFICATION
-- ============================================================

SELECT
    name AS TableName
FROM sys.tables
WHERE name IN
(
    'CreditCardApplications',
    'CreditCards',
    'CreditCardTransactions'
)
ORDER BY name;
GO

SELECT
    'CreditCardApplications' AS TableName,
    COUNT(*) AS RecordCount
FROM dbo.CreditCardApplications

UNION ALL

SELECT
    'CreditCards',
    COUNT(*)
FROM dbo.CreditCards

UNION ALL

SELECT
    'CreditCardTransactions',
    COUNT(*)
FROM dbo.CreditCardTransactions;
GO

USE BankingFraudDB;
GO

SELECT
    ApplicationID,
    CustomerID,
    CardType,
    RequestedLimit,
    Currency,
    ApplicationStatus,
    AppliedAt
FROM dbo.CreditCardApplications
ORDER BY ApplicationID DESC;
GO

-- ============================================================
-- 6. CREDIT CARD TRANSACTION TYPE UPDATE
-- ============================================================

SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF EXISTS
    (
        SELECT 1
        FROM sys.check_constraints
        WHERE name = 'CK_CreditCardTransactions_Type'
          AND parent_object_id =
              OBJECT_ID('dbo.CreditCardTransactions')
    )
    BEGIN
        ALTER TABLE dbo.CreditCardTransactions
        DROP CONSTRAINT CK_CreditCardTransactions_Type;
    END;

    ALTER TABLE dbo.CreditCardTransactions
    WITH CHECK ADD CONSTRAINT CK_CreditCardTransactions_Type
    CHECK
    (
        TransactionType IN
        (
            'Purchase',
            'Payment',
            'Refund',
            'CashAdvance'
        )
    );

    COMMIT TRANSACTION;

    PRINT 'Credit card transaction types updated successfully.';

END TRY
BEGIN CATCH

    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    PRINT ERROR_MESSAGE();

END CATCH;
GO

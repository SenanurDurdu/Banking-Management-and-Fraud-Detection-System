
-- ============================================================
-- NG BANK
-- FILE: 02_constraints_indexes.sql
-- PURPOSE: Final integrity constraints and indexes
-- SOURCE: Exported live database schema
-- STATUS: DRAFT - SQL SERVER TEST PENDING
-- RUN AFTER: 01_schema.sql
-- ============================================================

USE BankingFraudDB;
GO

SET NOCOUNT ON;
GO

-- ============================================================
-- 1. TRANSACTION SHAPE
-- ============================================================

IF NOT EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE parent_object_id = OBJECT_ID(N'dbo.Transactions')
      AND name = N'CK_Transactions_Shape'
)
BEGIN
    ALTER TABLE dbo.Transactions
    WITH CHECK ADD CONSTRAINT CK_Transactions_Shape
    CHECK (
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
END;
GO

-- ============================================================
-- 2. TRANSACTION STATUS
-- ============================================================

IF NOT EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE parent_object_id = OBJECT_ID(N'dbo.Transactions')
      AND name = N'CK_Transactions_Status'
)
BEGIN
    ALTER TABLE dbo.Transactions
    WITH CHECK ADD CONSTRAINT CK_Transactions_Status
    CHECK (
        Status IN (
            'Completed',
            'Failed',
            'Pending',
            'Blocked'
        )
    );
END;
GO

-- ============================================================
-- 3. FRAUD RISK LEVEL
-- ============================================================

IF NOT EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE parent_object_id = OBJECT_ID(N'dbo.FraudAlerts')
      AND name = N'CK_FraudAlerts_RiskLevel'
)
BEGIN
    ALTER TABLE dbo.FraudAlerts
    WITH CHECK ADD CONSTRAINT CK_FraudAlerts_RiskLevel
    CHECK (RiskLevel IN ('Medium', 'High'));
END;
GO

-- ============================================================
-- 4. CUSTOMER AND USER UNIQUE INDEXES
-- ============================================================

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Customers')
      AND name = N'UX_Customers_Phone'
)
BEGIN
    CREATE UNIQUE INDEX UX_Customers_Phone
    ON dbo.Customers(Phone)
    WHERE Phone IS NOT NULL AND Phone <> N'';
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Users')
      AND name = N'UX_Users_Email'
)
BEGIN
    CREATE UNIQUE INDEX UX_Users_Email
    ON dbo.Users(Email);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
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
-- 5. ACCOUNT INDEX
-- ============================================================

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Accounts')
      AND name = N'IX_Accounts_CustomerID'
)
BEGIN
    CREATE INDEX IX_Accounts_CustomerID
    ON dbo.Accounts(CustomerID);
END;
GO

-- ============================================================
-- 6. BANK TRANSACTION INDEXES
-- ============================================================

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Transactions')
      AND name = N'IX_Transactions_Date'
)
BEGIN
    CREATE INDEX IX_Transactions_Date
    ON dbo.Transactions(TransactionDate ASC);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Transactions')
      AND name = N'IX_Transactions_FromAccount'
)
BEGIN
    CREATE INDEX IX_Transactions_FromAccount
    ON dbo.Transactions(
        FromAccountID ASC,
        TransactionDate ASC
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Transactions')
      AND name = N'IX_Transactions_ToAccount'
)
BEGIN
    CREATE INDEX IX_Transactions_ToAccount
    ON dbo.Transactions(
        ToAccountID ASC,
        TransactionDate ASC
    );
END;
GO

-- ============================================================
-- 7. FRAUD ALERT INDEXES
-- ============================================================

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.FraudAlerts')
      AND name = N'IX_FraudAlerts_TransactionID'
)
BEGIN
    CREATE INDEX IX_FraudAlerts_TransactionID
    ON dbo.FraudAlerts(TransactionID);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.FraudAlerts')
      AND name = N'IX_FraudAlerts_ReviewStatus'
)
BEGIN
    CREATE INDEX IX_FraudAlerts_ReviewStatus
    ON dbo.FraudAlerts(
        ReviewStatus ASC,
        CreatedAt DESC
    );
END;
GO

-- ============================================================
-- 8. AUDIT LOG INDEX
-- ============================================================

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.AuditLogs')
      AND name = N'IX_AuditLogs_UserID'
)
BEGIN
    CREATE INDEX IX_AuditLogs_UserID
    ON dbo.AuditLogs(
        UserID ASC,
        CreatedAt DESC
    );
END;
GO

-- ============================================================
-- 9. NOTIFICATION INDEX
-- ============================================================

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Notifications')
      AND name = N'IX_Notifications_Customer'
)
BEGIN
    CREATE INDEX IX_Notifications_Customer
    ON dbo.Notifications(
        CustomerID ASC,
        IsRead ASC,
        CreatedAt DESC
    );
END;
GO

-- ============================================================
-- 10. CREDIT CARD APPLICATION INDEX
-- ============================================================

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.CreditCardApplications')
      AND name = N'IX_CreditCardApplications_Customer'
)
BEGIN
    CREATE INDEX IX_CreditCardApplications_Customer
    ON dbo.CreditCardApplications(
        CustomerID ASC,
        ApplicationStatus ASC,
        AppliedAt ASC
    );
END;
GO

-- ============================================================
-- 11. CREDIT CARD INDEX
-- ============================================================

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.CreditCards')
      AND name = N'IX_CreditCards_Customer'
)
BEGIN
    CREATE INDEX IX_CreditCards_Customer
    ON dbo.CreditCards(
        CustomerID ASC,
        CardStatus ASC
    );
END;
GO

-- ============================================================
-- 12. CREDIT CARD TRANSACTION INDEXES
-- ============================================================

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.CreditCardTransactions')
      AND name = N'IX_CreditCardTransactions_Card'
)
BEGIN
    CREATE INDEX IX_CreditCardTransactions_Card
    ON dbo.CreditCardTransactions(
        CreditCardID ASC,
        CreatedAt ASC
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.CreditCardTransactions')
      AND name = N'UX_CreditCardTransactions_BankTransaction'
)
BEGIN
    CREATE UNIQUE INDEX
        UX_CreditCardTransactions_BankTransaction
    ON dbo.CreditCardTransactions(BankTransactionID)
    WHERE BankTransactionID IS NOT NULL;
END;
GO

-- ============================================================
-- 13. VERIFY CONSTRAINTS
-- ============================================================

SELECT
    OBJECT_NAME(parent_object_id) AS TableName,
    name AS ConstraintName,
    is_disabled AS IsDisabled,
    is_not_trusted AS IsNotTrusted
FROM sys.check_constraints
ORDER BY TableName, ConstraintName;
GO

-- ============================================================
-- 14. VERIFY INDEXES
-- ============================================================

SELECT
    OBJECT_NAME(object_id) AS TableName,
    name AS IndexName,
    is_unique AS IsUnique,
    has_filter AS HasFilter
FROM sys.indexes
WHERE object_id IN (
    SELECT object_id
    FROM sys.tables
    WHERE schema_id = SCHEMA_ID(N'dbo')
)
AND name IS NOT NULL
ORDER BY TableName, IndexName;
GO

PRINT 'NG BANK constraints and indexes draft completed.';
GO

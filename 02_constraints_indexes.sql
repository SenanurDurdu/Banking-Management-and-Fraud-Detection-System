
-- ============================================================
-- NG BANK
-- FILE: 02_constraints_indexes.sql
-- PURPOSE: Constraints and indexes for 20-table database
-- DATABASE: BankingFraudDB
-- RUN AFTER: 01_schema.sql
-- ============================================================

USE BankingFraudDB_Test;
GO

SET NOCOUNT ON;
GO

-- ============================================================
-- 1. TRANSACTION SHAPE
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.check_constraints
    WHERE parent_object_id = OBJECT_ID(N'dbo.Transactions')
      AND name = N'CK_Transactions_Shape'
)
BEGIN
    ALTER TABLE dbo.Transactions
    WITH CHECK
    ADD CONSTRAINT CK_Transactions_Shape
    CHECK
    (
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

IF NOT EXISTS
(
    SELECT 1
    FROM sys.check_constraints
    WHERE parent_object_id = OBJECT_ID(N'dbo.Transactions')
      AND name = N'CK_Transactions_Status'
)
BEGIN
    ALTER TABLE dbo.Transactions
    WITH CHECK
    ADD CONSTRAINT CK_Transactions_Status
    CHECK
    (
        Status IN
        (
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

IF NOT EXISTS
(
    SELECT 1
    FROM sys.check_constraints
    WHERE parent_object_id = OBJECT_ID(N'dbo.FraudAlerts')
      AND name = N'CK_FraudAlerts_RiskLevel'
)
BEGIN
    ALTER TABLE dbo.FraudAlerts
    WITH CHECK
    ADD CONSTRAINT CK_FraudAlerts_RiskLevel
    CHECK (RiskLevel IN ('Medium', 'High'));
END;
GO

-- ============================================================
-- 4. CUSTOMER AND USER UNIQUE INDEXES
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Customers')
      AND name = N'UX_Customers_Phone'
)
BEGIN
    CREATE UNIQUE INDEX UX_Customers_Phone
    ON dbo.Customers(Phone)
    WHERE Phone IS NOT NULL
      AND Phone <> N'';
END;
GO

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
-- 5. ACCOUNT INDEX
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

-- ============================================================
-- 6. BANK TRANSACTION INDEXES
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Transactions')
      AND name = N'IX_Transactions_Date'
)
BEGIN
    CREATE INDEX IX_Transactions_Date
    ON dbo.Transactions(TransactionDate ASC);
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
        FromAccountID ASC,
        TransactionDate ASC
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
        ToAccountID ASC,
        TransactionDate ASC
    );
END;
GO

-- ============================================================
-- 7. FRAUD ALERT INDEXES
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.FraudAlerts')
      AND name = N'IX_FraudAlerts_TransactionID'
)
BEGIN
    CREATE INDEX IX_FraudAlerts_TransactionID
    ON dbo.FraudAlerts(TransactionID);
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.FraudAlerts')
      AND name = N'IX_FraudAlerts_ReviewStatus'
)
BEGIN
    CREATE INDEX IX_FraudAlerts_ReviewStatus
    ON dbo.FraudAlerts
    (
        ReviewStatus ASC,
        CreatedAt DESC
    );
END;
GO

-- ============================================================
-- 8. AUDIT LOG INDEX
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.AuditLogs')
      AND name = N'IX_AuditLogs_UserID'
)
BEGIN
    CREATE INDEX IX_AuditLogs_UserID
    ON dbo.AuditLogs
    (
        UserID ASC,
        CreatedAt DESC
    );
END;
GO

-- ============================================================
-- 9. NOTIFICATION INDEX
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Notifications')
      AND name = N'IX_Notifications_Customer'
)
BEGIN
    CREATE INDEX IX_Notifications_Customer
    ON dbo.Notifications
    (
        CustomerID ASC,
        IsRead ASC,
        CreatedAt DESC
    );
END;
GO

-- ============================================================
-- 10. CREDIT CARD APPLICATION INDEX
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.CreditCardApplications')
      AND name = N'IX_CreditCardApplications_Customer'
)
BEGIN
    CREATE INDEX IX_CreditCardApplications_Customer
    ON dbo.CreditCardApplications
    (
        CustomerID ASC,
        ApplicationStatus ASC,
        AppliedAt ASC
    );
END;
GO

-- ============================================================
-- 11. CREDIT CARD INDEX
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.CreditCards')
      AND name = N'IX_CreditCards_Customer'
)
BEGIN
    CREATE INDEX IX_CreditCards_Customer
    ON dbo.CreditCards
    (
        CustomerID ASC,
        CardStatus ASC
    );
END;
GO

-- ============================================================
-- 12. CREDIT CARD TRANSACTION INDEXES
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.CreditCardTransactions')
      AND name = N'IX_CreditCardTransactions_Card'
)
BEGIN
    CREATE INDEX IX_CreditCardTransactions_Card
    ON dbo.CreditCardTransactions
    (
        CreditCardID ASC,
        CreatedAt ASC
    );
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
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
-- 13. CUSTOMER ADDRESSES INDEXES
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.CustomerAddresses')
      AND name = N'IX_CustomerAddresses_Customer'
)
BEGIN
    CREATE INDEX IX_CustomerAddresses_Customer
    ON dbo.CustomerAddresses
    (
        CustomerID,
        AddressType
    );
END;
GO

-- Only one primary address per customer
IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.CustomerAddresses')
      AND name = N'UX_CustomerAddresses_Primary'
)
BEGIN
    CREATE UNIQUE INDEX UX_CustomerAddresses_Primary
    ON dbo.CustomerAddresses(CustomerID)
    WHERE IsPrimary = 1;
END;
GO

-- ============================================================
-- 14. CUSTOMER CONTACTS INDEXES
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.CustomerContacts')
      AND name = N'IX_CustomerContacts_Customer'
)
BEGIN
    CREATE INDEX IX_CustomerContacts_Customer
    ON dbo.CustomerContacts
    (
        CustomerID,
        ContactType
    );
END;
GO

-- One primary contact for each contact type
IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.CustomerContacts')
      AND name = N'UX_CustomerContacts_Primary'
)
BEGIN
    CREATE UNIQUE INDEX UX_CustomerContacts_Primary
    ON dbo.CustomerContacts
    (
        CustomerID,
        ContactType
    )
    WHERE IsPrimary = 1;
END;
GO

-- Prevent duplicate contact entries for one customer
IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.CustomerContacts')
      AND name = N'UX_CustomerContacts_Value'
)
BEGIN
    CREATE UNIQUE INDEX UX_CustomerContacts_Value
    ON dbo.CustomerContacts
    (
        CustomerID,
        ContactType,
        ContactValue
    );
END;
GO

-- ============================================================
-- 15. BENEFICIARIES INDEXES
-- ============================================================

-- The schema already defines a UNIQUE constraint on
-- (CustomerID, AccountNumber).
-- This index supports listing active beneficiaries.

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Beneficiaries')
      AND name = N'IX_Beneficiaries_Customer_Active'
)
BEGIN
    CREATE INDEX IX_Beneficiaries_Customer_Active
    ON dbo.Beneficiaries
    (
        CustomerID,
        IsActive,
        DisplayName
    );
END;
GO

-- ============================================================
-- 16. ACCOUNT STATUS HISTORY INDEXES
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.AccountStatusHistory')
      AND name = N'IX_AccountStatusHistory_Account'
)
BEGIN
    CREATE INDEX IX_AccountStatusHistory_Account
    ON dbo.AccountStatusHistory
    (
        AccountID,
        ChangedAt DESC
    );
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.AccountStatusHistory')
      AND name = N'IX_AccountStatusHistory_User'
)
BEGIN
    CREATE INDEX IX_AccountStatusHistory_User
    ON dbo.AccountStatusHistory(ChangedByUserID)
    WHERE ChangedByUserID IS NOT NULL;
END;
GO

-- ============================================================
-- 17. TRANSACTION NOTES INDEXES
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.TransactionNotes')
      AND name = N'IX_TransactionNotes_Transaction'
)
BEGIN
    CREATE INDEX IX_TransactionNotes_Transaction
    ON dbo.TransactionNotes
    (
        TransactionID,
        CreatedAt DESC
    );
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.TransactionNotes')
      AND name = N'IX_TransactionNotes_User'
)
BEGIN
    CREATE INDEX IX_TransactionNotes_User
    ON dbo.TransactionNotes(CreatedByUserID)
    WHERE CreatedByUserID IS NOT NULL;
END;
GO

-- ============================================================
-- 18. FRAUD ALERT REVIEW HISTORY INDEXES
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.FraudAlertReviewHistory')
      AND name = N'IX_FraudReviewHistory_Alert'
)
BEGIN
    CREATE INDEX IX_FraudReviewHistory_Alert
    ON dbo.FraudAlertReviewHistory
    (
        AlertID,
        ReviewedAt DESC
    );
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.FraudAlertReviewHistory')
      AND name = N'IX_FraudReviewHistory_User'
)
BEGIN
    CREATE INDEX IX_FraudReviewHistory_User
    ON dbo.FraudAlertReviewHistory(ReviewedByUserID)
    WHERE ReviewedByUserID IS NOT NULL;
END;
GO

-- ============================================================
-- 19. CREDIT CARD BILLING SETTINGS
-- ============================================================

-- CreditCardID already has a UNIQUE constraint in 01_schema.
-- No duplicate index is required for that column.

-- ============================================================
-- 20. ACCOUNT DAILY BALANCES INDEXES
-- ============================================================

-- AccountID + BalanceDate already has a UNIQUE constraint
-- defined in 01_schema.sql.

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.AccountDailyBalances')
      AND name = N'IX_AccountDailyBalances_Date'
)
BEGIN
    CREATE INDEX IX_AccountDailyBalances_Date
    ON dbo.AccountDailyBalances
    (
        BalanceDate DESC,
        AccountID
    )
    INCLUDE
    (
        ClosingBalance,
        RecordedAt
    );
END;
GO

-- ============================================================
-- 21. FRAUD RISK ASSESSMENTS INDEXES
-- ============================================================

-- AlertID already has a UNIQUE constraint
-- defined in 01_schema.sql.

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.FraudRiskAssessments')
      AND name = N'IX_FraudRiskAssessments_Level'
)
BEGIN
    CREATE INDEX IX_FraudRiskAssessments_Level
    ON dbo.FraudRiskAssessments
    (
        RiskLevel,
        ReviewStatus,
        AssessedAt DESC
    )
    INCLUDE
    (
        AlertID
    );
END;
GO

-- ============================================================
-- 22. VERIFY CHECK CONSTRAINTS
-- ============================================================

SELECT
    OBJECT_NAME(parent_object_id) AS TableName,
    name AS ConstraintName,
    is_disabled AS IsDisabled,
    is_not_trusted AS IsNotTrusted
FROM sys.check_constraints
WHERE parent_object_id IN
(
    SELECT object_id
    FROM sys.tables
    WHERE schema_id = SCHEMA_ID(N'dbo')
)
ORDER BY
    TableName,
    ConstraintName;
GO

-- ============================================================
-- 23. VERIFY FOREIGN KEYS
-- ============================================================

SELECT
    OBJECT_NAME(parent_object_id) AS ChildTable,
    name AS ForeignKeyName,
    OBJECT_NAME(referenced_object_id) AS ParentTable,
    is_disabled AS IsDisabled,
    is_not_trusted AS IsNotTrusted
FROM sys.foreign_keys
WHERE parent_object_id IN
(
    SELECT object_id
    FROM sys.tables
    WHERE schema_id = SCHEMA_ID(N'dbo')
)
ORDER BY
    ChildTable,
    ForeignKeyName;
GO

-- ============================================================
-- 24. VERIFY INDEXES
-- ============================================================

SELECT
    OBJECT_NAME(object_id) AS TableName,
    name AS IndexName,
    is_unique AS IsUnique,
    has_filter AS HasFilter
FROM sys.indexes
WHERE object_id IN
(
    SELECT object_id
    FROM sys.tables
    WHERE schema_id = SCHEMA_ID(N'dbo')
)
AND name IS NOT NULL
ORDER BY
    TableName,
    IndexName;
GO

-- ============================================================
-- 25. VERIFY TABLE COUNT
-- ============================================================

DECLARE @TableCount INT;

SELECT @TableCount = COUNT(*)
FROM sys.tables
WHERE schema_id = SCHEMA_ID(N'dbo')
  AND is_ms_shipped = 0;

SELECT @TableCount AS TotalApplicationTables;

IF @TableCount = 20
BEGIN
    PRINT 'NG BANK: 20 tables confirmed.';
END
ELSE
BEGIN
    PRINT 'NG BANK WARNING: Expected exactly 20 tables, found '
          + CAST(@TableCount AS VARCHAR(10)) + '.';
END;
GO

PRINT '02_constraints_indexes.sql completed.';
GO
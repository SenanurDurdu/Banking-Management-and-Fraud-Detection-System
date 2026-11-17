
-- ============================================================
-- BANKING MANAGEMENT & FRAUD DETECTION SYSTEM
-- FILE: 02_constraints_indexes.sql
-- PURPOSE:
--   1. Schema compatibility
--   2. Data integrity constraints
--   3. Foreign keys
--   4. Unique indexes
--   5. Performance indexes
--
-- RUN AFTER: 01_schema.sql
--
-- IMPORTANT:
--   Existing records are not deleted.
--   Identity counters are not reset.
--   Existing invalid data is not automatically modified.
--   Constraints with incompatible existing data are skipped.
-- ============================================================

USE BankingFraudDB;
GO

SET NOCOUNT ON;
GO


-- ============================================================
-- 1. CUSTOMER SCHEMA COMPATIBILITY
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
-- NVARCHAR(250) has max_length = 500 bytes.

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
-- 2. AUDIT LOGS - USER INFORMATION
-- ============================================================

IF COL_LENGTH(N'dbo.AuditLogs', N'UserID') IS NULL
BEGIN
    ALTER TABLE dbo.AuditLogs
    ADD UserID INT NULL;
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.foreign_keys
    WHERE name = N'FK_AuditLogs_Users'
      AND parent_object_id = OBJECT_ID(N'dbo.AuditLogs')
)
BEGIN
    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.AuditLogs AS a
        WHERE a.UserID IS NOT NULL
          AND NOT EXISTS
          (
              SELECT 1
              FROM dbo.Users AS u
              WHERE u.UserID = a.UserID
          )
    )
    BEGIN
        ALTER TABLE dbo.AuditLogs
        WITH CHECK ADD CONSTRAINT FK_AuditLogs_Users
        FOREIGN KEY (UserID)
        REFERENCES dbo.Users(UserID);
    END
    ELSE
    BEGIN
        PRINT 'WARNING: FK_AuditLogs_Users skipped.';
        PRINT 'Some audit records reference missing users.';
    END;
END;
GO


-- ============================================================
-- 3. FRAUD ALERTS - REVIEW INFORMATION
-- ============================================================

IF COL_LENGTH(N'dbo.FraudAlerts', N'ReviewedByUserID') IS NULL
BEGIN
    ALTER TABLE dbo.FraudAlerts
    ADD ReviewedByUserID INT NULL;
END;
GO

IF COL_LENGTH(N'dbo.FraudAlerts', N'ReviewNote') IS NULL
BEGIN
    ALTER TABLE dbo.FraudAlerts
    ADD ReviewNote NVARCHAR(500) NULL;
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.foreign_keys
    WHERE name = N'FK_FraudAlerts_ReviewedBy'
      AND parent_object_id = OBJECT_ID(N'dbo.FraudAlerts')
)
BEGIN
    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.FraudAlerts AS fa
        WHERE fa.ReviewedByUserID IS NOT NULL
          AND NOT EXISTS
          (
              SELECT 1
              FROM dbo.Users AS u
              WHERE u.UserID = fa.ReviewedByUserID
          )
    )
    BEGIN
        ALTER TABLE dbo.FraudAlerts
        WITH CHECK ADD CONSTRAINT FK_FraudAlerts_ReviewedBy
        FOREIGN KEY (ReviewedByUserID)
        REFERENCES dbo.Users(UserID);
    END
    ELSE
    BEGIN
        PRINT 'WARNING: FK_FraudAlerts_ReviewedBy skipped.';
        PRINT 'Some fraud reviews reference missing users.';
    END;
END;
GO


-- ============================================================
-- 4. CUSTOMER EMAIL - UNIQUE INDEX
-- ============================================================

-- Avoid creating a duplicate unique index when an
-- equivalent single-column unique index already exists.

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes AS i
    INNER JOIN sys.index_columns AS ic
        ON ic.object_id = i.object_id
       AND ic.index_id = i.index_id
    INNER JOIN sys.columns AS c
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
          FROM sys.index_columns AS ic2
          WHERE ic2.object_id = i.object_id
            AND ic2.index_id = i.index_id
            AND ic2.key_ordinal > 1
      )
)
BEGIN
    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.Customers
        WHERE Email IS NOT NULL
        GROUP BY Email
        HAVING COUNT(*) > 1
    )
    AND
    (
        SELECT COUNT(*)
        FROM dbo.Customers
        WHERE Email IS NULL
    ) <= 1
    BEGIN
        CREATE UNIQUE INDEX UX_Customers_Email
        ON dbo.Customers(Email);
    END
    ELSE
    BEGIN
        PRINT 'WARNING: UX_Customers_Email skipped.';
        PRINT 'Duplicate or multiple NULL email values found.';
    END;
END;
GO


-- ============================================================
-- 5. CUSTOMER PHONE - UNIQUE FILTERED INDEX
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
        PRINT 'WARNING: UX_Customers_Phone skipped.';
        PRINT 'Duplicate phone numbers found.';
    END;
END;
GO


-- ============================================================
-- 6. USERS - UNIQUE EMAIL
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Users')
      AND name = N'UX_Users_Email'
)
BEGIN
    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.Users
        GROUP BY Email
        HAVING COUNT(*) > 1
    )
    BEGIN
        CREATE UNIQUE INDEX UX_Users_Email
        ON dbo.Users(Email);
    END
    ELSE
    BEGIN
        PRINT 'WARNING: UX_Users_Email skipped.';
        PRINT 'Duplicate user email addresses found.';
    END;
END;
GO


-- ============================================================
-- 7. USERS - ONE LOGIN PER CUSTOMER
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.Users')
      AND name = N'UX_Users_CustomerID'
)
BEGIN
    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.Users
        WHERE CustomerID IS NOT NULL
        GROUP BY CustomerID
        HAVING COUNT(*) > 1
    )
    BEGIN
        CREATE UNIQUE INDEX UX_Users_CustomerID
        ON dbo.Users(CustomerID)
        WHERE CustomerID IS NOT NULL;
    END
    ELSE
    BEGIN
        PRINT 'WARNING: UX_Users_CustomerID skipped.';
        PRINT 'Some customers have multiple login records.';
    END;
END;
GO


-- ============================================================
-- 8. TRANSACTIONS - ACCOUNT RELATIONSHIP CHECK
-- ============================================================

-- Deposit:
--   FromAccountID = NULL
--   ToAccountID   = NOT NULL
--
-- Withdrawal:
--   FromAccountID = NOT NULL
--   ToAccountID   = NULL
--
-- Transfer:
--   Both account IDs must exist and differ.

IF NOT EXISTS
(
    SELECT 1
    FROM sys.check_constraints
    WHERE name = N'CK_Transactions_Shape'
      AND parent_object_id =
          OBJECT_ID(N'dbo.Transactions')
)
BEGIN
    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.Transactions
        WHERE NOT
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
        )
    )
    BEGIN
        ALTER TABLE dbo.Transactions
        WITH CHECK ADD CONSTRAINT CK_Transactions_Shape
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

        PRINT 'CK_Transactions_Shape created.';
    END
    ELSE
    BEGIN
        PRINT 'WARNING: CK_Transactions_Shape skipped.';
        PRINT 'Existing transactions violate the relationship rule.';
    END;
END;
GO


-- ============================================================
-- 9. TRANSACTIONS - STATUS CHECK
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.check_constraints
    WHERE name = N'CK_Transactions_Status'
      AND parent_object_id =
          OBJECT_ID(N'dbo.Transactions')
)
BEGIN
    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.Transactions
        WHERE Status NOT IN
        (
            'Completed',
            'Pending',
            'Blocked',
            'Failed'
        )
    )
    BEGIN
        ALTER TABLE dbo.Transactions
        WITH CHECK ADD CONSTRAINT CK_Transactions_Status
        CHECK
        (
            Status IN
            (
                'Completed',
                'Pending',
                'Blocked',
                'Failed'
            )
        );

        PRINT 'CK_Transactions_Status created.';
    END
    ELSE
    BEGIN
        PRINT 'WARNING: CK_Transactions_Status skipped.';
        PRINT 'Unexpected transaction statuses found.';
    END;
END;
GO


-- ============================================================
-- 10. FRAUD ALERTS - RISK LEVEL CHECK
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.check_constraints
    WHERE name = N'CK_FraudAlerts_RiskLevel'
      AND parent_object_id =
          OBJECT_ID(N'dbo.FraudAlerts')
)
BEGIN
    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.FraudAlerts
        WHERE RiskLevel NOT IN
        (
            'Medium',
            'High'
        )
    )
    BEGIN
        ALTER TABLE dbo.FraudAlerts
        WITH CHECK ADD CONSTRAINT CK_FraudAlerts_RiskLevel
        CHECK
        (
            RiskLevel IN
            (
                'Medium',
                'High'
            )
        );

        PRINT 'CK_FraudAlerts_RiskLevel created.';
    END
    ELSE
    BEGIN
        PRINT 'WARNING: CK_FraudAlerts_RiskLevel skipped.';
        PRINT 'Unexpected fraud risk levels found.';
    END;
END;
GO


-- ============================================================
-- 11. FRAUD ALERTS - REVIEW STATUS CHECK
-- ============================================================

IF NOT EXISTS
(
    SELECT 1
    FROM sys.check_constraints
    WHERE name = N'CK_FraudAlerts_ReviewStatus'
      AND parent_object_id =
          OBJECT_ID(N'dbo.FraudAlerts')
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
        WITH CHECK ADD CONSTRAINT CK_FraudAlerts_ReviewStatus
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
        PRINT 'WARNING: CK_FraudAlerts_ReviewStatus skipped.';
        PRINT 'Unexpected review statuses found.';
    END;
END;
GO


-- ============================================================
-- 12. ACCOUNTS - CUSTOMER INDEX
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
-- 13. TRANSACTIONS - DATE INDEX
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
    ON dbo.Transactions(TransactionDate);
END;
GO


-- ============================================================
-- 14. TRANSACTIONS - SOURCE ACCOUNT INDEX
-- ============================================================

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


-- ============================================================
-- 15. TRANSACTIONS - DESTINATION ACCOUNT INDEX
-- ============================================================

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
-- 16. FRAUD ALERTS - TRANSACTION INDEX
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


-- ============================================================
-- 17. FRAUD ALERTS - REVIEW STATUS INDEX
-- ============================================================

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
        ReviewStatus,
        CreatedAt DESC
    );
END;
GO


-- ============================================================
-- 18. NOTIFICATIONS - CUSTOMER INDEX
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
        CustomerID,
        IsRead,
        CreatedAt DESC
    );
END;
GO


-- ============================================================
-- 19. AUDIT LOGS - USER INDEX
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
        UserID,
        CreatedAt DESC
    );
END;
GO


-- ============================================================
-- 20. VERIFY SCHEMA IMPROVEMENTS
-- ============================================================

SELECT
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE
    (
        TABLE_NAME = 'AuditLogs'
        AND COLUMN_NAME = 'UserID'
    )
    OR
    (
        TABLE_NAME = 'FraudAlerts'
        AND COLUMN_NAME IN
        (
            'ReviewedByUserID',
            'ReviewNote'
        )
    )
ORDER BY
    TABLE_NAME,
    COLUMN_NAME;
GO


-- ============================================================
-- 21. VERIFY CHECK CONSTRAINTS
-- ============================================================

SELECT
    OBJECT_NAME(parent_object_id) AS TableName,
    name AS ConstraintName,
    definition AS ConstraintDefinition,
    is_disabled AS IsDisabled,
    is_not_trusted AS IsNotTrusted
FROM sys.check_constraints
WHERE parent_object_id IN
(
    OBJECT_ID(N'dbo.Transactions'),
    OBJECT_ID(N'dbo.FraudAlerts')
)
ORDER BY
    TableName,
    ConstraintName;
GO


-- ============================================================
-- 22. VERIFY FOREIGN KEYS
-- ============================================================

SELECT
    OBJECT_NAME(parent_object_id) AS TableName,
    name AS ForeignKeyName,
    OBJECT_NAME(referenced_object_id) AS ReferencedTable,
    is_disabled AS IsDisabled,
    is_not_trusted AS IsNotTrusted
FROM sys.foreign_keys
WHERE parent_object_id IN
(
    OBJECT_ID(N'dbo.AuditLogs'),
    OBJECT_ID(N'dbo.FraudAlerts'),
    OBJECT_ID(N'dbo.Notifications')
)
ORDER BY
    TableName,
    ForeignKeyName;
GO


-- ============================================================
-- 23. VERIFY INDEXES
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
    OBJECT_ID(N'dbo.Transactions'),
    OBJECT_ID(N'dbo.FraudAlerts'),
    OBJECT_ID(N'dbo.AuditLogs'),
    OBJECT_ID(N'dbo.Notifications')
)
AND i.name IS NOT NULL
ORDER BY
    TableName,
    IndexName;
GO


-- ============================================================
-- 24. VERIFY EXISTING DATA COUNTS
-- ============================================================

SELECT 'Customers' AS TableName, COUNT(*) AS RecordCount
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
FROM dbo.AuditLogs

UNION ALL

SELECT 'Notifications', COUNT(*)
FROM dbo.Notifications;
GO


-- ============================================================
-- 25. FINISH
-- ============================================================

PRINT '============================================';
PRINT '02_constraints_indexes.sql completed.';
PRINT 'Schema compatibility checks completed.';
PRINT 'Constraints and indexes checked.';
PRINT 'Existing records were not deleted.';
PRINT 'Review any WARNING messages above.';
PRINT '============================================';
GO

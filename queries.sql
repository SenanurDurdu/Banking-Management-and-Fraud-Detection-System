USE BankingFraudDB;
GO

-- 1. VIEW CUSTOMERS
SELECT * FROM Customers;
GO

-- 2. VIEW ACCOUNTS
SELECT * FROM Accounts;
GO

-- 3. ACCOUNT DETAILS
SELECT AccountID, AccountNumber, Balance
FROM Accounts;
GO

-- 4. RECENT TRANSACTIONS
SELECT *
FROM Transactions
ORDER BY TransactionDate DESC;
GO

-- 5. FRAUD ALERTS
SELECT *
FROM FraudAlerts;
GO

-- 6. FRAUD ALERT COLUMN INFORMATION
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'FraudAlerts';
GO

-- 7. CHECK DUPLICATE EMAILS
SELECT Email, COUNT(*) AS EmailCount
FROM Customers
WHERE Email IS NOT NULL
GROUP BY Email
HAVING COUNT(*) > 1;
GO

-- 8. FOREIGN KEY INFORMATION
SELECT
    fk.name AS ForeignKeyName,
    tp.name AS ParentTable,
    cp.name AS ParentColumn,
    tr.name AS ReferencedTable,
    cr.name AS ReferencedColumn
FROM sys.foreign_keys fk
INNER JOIN sys.foreign_key_columns fkc
    ON fk.object_id = fkc.constraint_object_id
INNER JOIN sys.tables tp
    ON fkc.parent_object_id = tp.object_id
INNER JOIN sys.columns cp
    ON fkc.parent_object_id = cp.object_id
    AND fkc.parent_column_id = cp.column_id
INNER JOIN sys.tables tr
    ON fkc.referenced_object_id = tr.object_id
INNER JOIN sys.columns cr
    ON fkc.referenced_object_id = cr.object_id
    AND fkc.referenced_column_id = cr.column_id;
GO

-- 9. TABLE CONSTRAINTS
SELECT
    tc.TABLE_NAME,
    kcu.COLUMN_NAME,
    tc.CONSTRAINT_NAME,
    tc.CONSTRAINT_TYPE
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc
LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS kcu
    ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
    AND tc.TABLE_NAME = kcu.TABLE_NAME
ORDER BY
    tc.TABLE_NAME,
    tc.CONSTRAINT_TYPE;
GO

-- 10. CHECK CONSTRAINTS
SELECT
    OBJECT_NAME(parent_object_id) AS TableName,
    name AS ConstraintName,
    definition AS CheckCondition
FROM sys.check_constraints;
GO

-- 11. UNIQUE CONSTRAINTS
SELECT
    TABLE_NAME,
    CONSTRAINT_NAME,
    CONSTRAINT_TYPE
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
WHERE CONSTRAINT_TYPE = 'UNIQUE'
ORDER BY TABLE_NAME;
GO

-- ============================================================
-- BANKING MANAGEMENT & FRAUD DETECTION SYSTEM
-- FILE: 07_verify.sql
-- PURPOSE: Read-only database verification
--
-- RUN AFTER:
--   01_schema.sql
--   02_constraints_indexes.sql
--   03_seed_fraud_rules.sql
--   04_views.sql
--   05_transaction_procedures.sql
--   06_fraud_procedures.sql
--
-- IMPORTANT:
--   Select BankingFraudDB in SSMS before execution.
--   This script contains SELECT statements only.
--   No records or database objects are modified.
-- ============================================================


-- ============================================================
-- 1. VERIFY SELECTED DATABASE
-- ============================================================

SELECT
    DB_NAME() AS CurrentDatabase,
    CASE
        WHEN DB_NAME() = N'BankingFraudDB'
        THEN 'PASS'
        ELSE 'FAIL - Select BankingFraudDB'
    END AS VerificationStatus;


-- ============================================================
-- 2. VERIFY REQUIRED TABLES
-- ============================================================

SELECT
    expected.TableName,

    CASE
        WHEN t.object_id IS NOT NULL
        THEN 'PASS'
        ELSE 'MISSING'
    END AS VerificationStatus

FROM
(
    VALUES
        (N'Customers'),
        (N'Users'),
        (N'Accounts'),
        (N'Transactions'),
        (N'FraudRules'),
        (N'FraudAlerts'),
        (N'AuditLogs'),
        (N'Notifications')
) AS expected(TableName)

LEFT JOIN sys.tables AS t
    ON t.name = expected.TableName
   AND t.schema_id = SCHEMA_ID(N'dbo')

ORDER BY expected.TableName;


-- ============================================================
-- 3. VERIFY REQUIRED VIEWS
-- ============================================================

SELECT
    expected.ViewName,

    CASE
        WHEN v.object_id IS NOT NULL
        THEN 'PASS'
        ELSE 'MISSING'
    END AS VerificationStatus

FROM
(
    VALUES
        (N'vw_AccountSummary'),
        (N'vw_FraudAlertDetails'),
        (N'vw_DailyTransactionStats'),
        (N'vw_SuspiciousTransactions'),
        (N'vw_CustomerRiskSummary'),
        (N'vw_CustomerFraudReviews')
) AS expected(ViewName)

LEFT JOIN sys.views AS v
    ON v.name = expected.ViewName
   AND v.schema_id = SCHEMA_ID(N'dbo')

ORDER BY expected.ViewName;


-- ============================================================
-- 4. VERIFY REQUIRED STORED PROCEDURES
-- ============================================================

SELECT
    expected.ProcedureName,

    CASE
        WHEN p.object_id IS NOT NULL
        THEN 'PASS'
        ELSE 'MISSING'
    END AS VerificationStatus

FROM
(
    VALUES
        (N'sp_ExecuteBankTransaction'),
        (N'sp_Deposit'),
        (N'sp_Withdraw'),
        (N'sp_Transfer'),
        (N'sp_ScanFraud')
) AS expected(ProcedureName)

LEFT JOIN sys.procedures AS p
    ON p.name = expected.ProcedureName
   AND p.schema_id = SCHEMA_ID(N'dbo')

ORDER BY expected.ProcedureName;


-- ============================================================
-- 5. VERIFY REQUIRED APPLICATION COLUMNS
-- ============================================================

SELECT
    expected.TableName,
    expected.ColumnName,

    CASE
        WHEN c.column_id IS NOT NULL
        THEN 'PASS'
        ELSE 'MISSING'
    END AS VerificationStatus,

    TYPE_NAME(c.user_type_id) AS ActualDataType,
    c.max_length AS ActualMaxLength,
    c.is_nullable AS IsNullable

FROM
(
    VALUES
        (N'Customers', N'CustomerID'),
        (N'Customers', N'FirstName'),
        (N'Customers', N'LastName'),
        (N'Customers', N'NationalID'),
        (N'Customers', N'Phone'),
        (N'Customers', N'Email'),
        (N'Customers', N'Address'),
        (N'Customers', N'IsActive'),

        (N'Users', N'UserID'),
        (N'Users', N'CustomerID'),
        (N'Users', N'Email'),
        (N'Users', N'PasswordHash'),
        (N'Users', N'Role'),
        (N'Users', N'IsActive'),

        (N'Accounts', N'AccountID'),
        (N'Accounts', N'CustomerID'),
        (N'Accounts', N'AccountNumber'),
        (N'Accounts', N'AccountType'),
        (N'Accounts', N'Balance'),
        (N'Accounts', N'Currency'),
        (N'Accounts', N'IsActive'),

        (N'Transactions', N'TransactionID'),
        (N'Transactions', N'FromAccountID'),
        (N'Transactions', N'ToAccountID'),
        (N'Transactions', N'TransactionType'),
        (N'Transactions', N'Amount'),
        (N'Transactions', N'Description'),
        (N'Transactions', N'TransactionDate'),
        (N'Transactions', N'Status'),

        (N'FraudRules', N'RuleID'),
        (N'FraudRules', N'RuleName'),
        (N'FraudRules', N'RuleType'),
        (N'FraudRules', N'ThresholdValue'),
        (N'FraudRules', N'TimeWindowMinutes'),
        (N'FraudRules', N'IsActive'),

        (N'FraudAlerts', N'AlertID'),
        (N'FraudAlerts', N'TransactionID'),
        (N'FraudAlerts', N'RuleID'),
        (N'FraudAlerts', N'RiskLevel'),
        (N'FraudAlerts', N'ReviewStatus'),
        (N'FraudAlerts', N'ReviewedAt'),
        (N'FraudAlerts', N'ReviewedByUserID'),
        (N'FraudAlerts', N'ReviewNote'),

        (N'AuditLogs', N'AuditID'),
        (N'AuditLogs', N'ActionType'),
        (N'AuditLogs', N'EntityName'),
        (N'AuditLogs', N'EntityID'),
        (N'AuditLogs', N'Description'),
        (N'AuditLogs', N'UserID'),

        (N'Notifications', N'NotificationID'),
        (N'Notifications', N'CustomerID'),
        (N'Notifications', N'Title'),
        (N'Notifications', N'Message'),
        (N'Notifications', N'NotificationType'),
        (N'Notifications', N'IsRead'),
        (N'Notifications', N'CreatedAt')
) AS expected(TableName, ColumnName)

LEFT JOIN sys.tables AS t
    ON t.name = expected.TableName
   AND t.schema_id = SCHEMA_ID(N'dbo')

LEFT JOIN sys.columns AS c
    ON c.object_id = t.object_id
   AND c.name = expected.ColumnName

ORDER BY
    expected.TableName,
    expected.ColumnName;


-- ============================================================
-- 6. VERIFY PROCEDURE PARAMETERS
-- ============================================================

SELECT
    expected.ProcedureName,
    expected.ParameterName,

    CASE
        WHEN prm.parameter_id IS NOT NULL
        THEN 'PASS'
        ELSE 'MISSING'
    END AS VerificationStatus,

    TYPE_NAME(prm.user_type_id) AS ActualDataType,
    prm.parameter_id AS ParameterOrder

FROM
(
    VALUES
        (N'sp_ExecuteBankTransaction', N'@Kind'),
        (N'sp_ExecuteBankTransaction', N'@UserID'),
        (N'sp_ExecuteBankTransaction', N'@SourceAccountID'),
        (N'sp_ExecuteBankTransaction', N'@DestinationAccountNumber'),
        (N'sp_ExecuteBankTransaction', N'@Amount'),
        (N'sp_ExecuteBankTransaction', N'@Description'),

        (N'sp_Deposit', N'@UserID'),
        (N'sp_Deposit', N'@SourceAccountID'),
        (N'sp_Deposit', N'@Amount'),
        (N'sp_Deposit', N'@Description'),

        (N'sp_Withdraw', N'@UserID'),
        (N'sp_Withdraw', N'@SourceAccountID'),
        (N'sp_Withdraw', N'@Amount'),
        (N'sp_Withdraw', N'@Description'),

        (N'sp_Transfer', N'@UserID'),
        (N'sp_Transfer', N'@SourceAccountID'),
        (N'sp_Transfer', N'@DestinationAccountNumber'),
        (N'sp_Transfer', N'@Amount'),
        (N'sp_Transfer', N'@Description'),

        (N'sp_ScanFraud', N'@UserID')
) AS expected(ProcedureName, ParameterName)

LEFT JOIN sys.procedures AS p
    ON p.name = expected.ProcedureName
   AND p.schema_id = SCHEMA_ID(N'dbo')

LEFT JOIN sys.parameters AS prm
    ON prm.object_id = p.object_id
   AND prm.name = expected.ParameterName

ORDER BY
    expected.ProcedureName,
    expected.ParameterName;


-- ============================================================
-- 7. VERIFY REQUIRED CHECK CONSTRAINTS
-- ============================================================

SELECT
    expected.TableName,
    expected.ConstraintName,

    CASE
        WHEN cc.object_id IS NULL
        THEN 'MISSING'

        WHEN cc.is_disabled = 1
        THEN 'DISABLED'

        WHEN cc.is_not_trusted = 1
        THEN 'NOT TRUSTED'

        ELSE 'PASS'
    END AS VerificationStatus

FROM
(
    VALUES
        (N'Users', N'CK_Users_Role'),
        (N'Users', N'CK_Users_RoleCustomer'),

        (N'Accounts', N'CK_Accounts_AccountType'),
        (N'Accounts', N'CK_Accounts_Balance'),

        (N'Transactions', N'CK_Transactions_Type'),
        (N'Transactions', N'CK_Transactions_Amount'),
        (N'Transactions', N'CK_Transactions_Shape'),
        (N'Transactions', N'CK_Transactions_Status'),

        (N'FraudRules', N'CK_FraudRules_Type'),

        (N'FraudAlerts', N'CK_FraudAlerts_ReviewStatus'),
        (N'FraudAlerts', N'CK_FraudAlerts_RiskLevel')
) AS expected(TableName, ConstraintName)

LEFT JOIN sys.tables AS t
    ON t.name = expected.TableName
   AND t.schema_id = SCHEMA_ID(N'dbo')

LEFT JOIN sys.check_constraints AS cc
    ON cc.parent_object_id = t.object_id
   AND cc.name = expected.ConstraintName

ORDER BY
    expected.TableName,
    expected.ConstraintName;


-- ============================================================
-- 8. VERIFY REQUIRED FOREIGN KEYS
-- ============================================================

SELECT
    expected.TableName,
    expected.ForeignKeyName,

    CASE
        WHEN fk.object_id IS NULL
        THEN 'MISSING'

        WHEN fk.is_disabled = 1
        THEN 'DISABLED'

        WHEN fk.is_not_trusted = 1
        THEN 'NOT TRUSTED'

        ELSE 'PASS'
    END AS VerificationStatus

FROM
(
    VALUES
        (N'Users', N'FK_Users_Customers'),
        (N'Accounts', N'FK_Accounts_Customers'),

        (N'Transactions', N'FK_Transactions_FromAccount'),
        (N'Transactions', N'FK_Transactions_ToAccount'),

        (N'FraudAlerts', N'FK_FraudAlerts_Transactions'),
        (N'FraudAlerts', N'FK_FraudAlerts_Rules'),
        (N'FraudAlerts', N'FK_FraudAlerts_ReviewedBy'),

        (N'AuditLogs', N'FK_AuditLogs_Users'),
        (N'Notifications', N'FK_Notifications_Customers')
) AS expected(TableName, ForeignKeyName)

LEFT JOIN sys.tables AS t
    ON t.name = expected.TableName
   AND t.schema_id = SCHEMA_ID(N'dbo')

LEFT JOIN sys.foreign_keys AS fk
    ON fk.parent_object_id = t.object_id
   AND fk.name = expected.ForeignKeyName

ORDER BY
    expected.TableName,
    expected.ForeignKeyName;


-- ============================================================
-- 9. VERIFY REQUIRED INDEXES
-- ============================================================

SELECT
    expected.TableName,
    expected.IndexName,

    CASE
        WHEN i.index_id IS NULL
        THEN 'MISSING'
        WHEN i.is_disabled = 1
        THEN 'DISABLED'
        ELSE 'PASS'
    END AS VerificationStatus,

    i.is_unique AS IsUnique,
    i.has_filter AS HasFilter

FROM
(
    VALUES
        (N'Customers', N'UX_Customers_Phone'),
        (N'Users', N'UX_Users_Email'),
        (N'Users', N'UX_Users_CustomerID'),

        (N'Accounts', N'IX_Accounts_CustomerID'),

        (N'Transactions', N'IX_Transactions_Date'),
        (N'Transactions', N'IX_Transactions_FromAccount'),
        (N'Transactions', N'IX_Transactions_ToAccount'),

        (N'FraudAlerts', N'IX_FraudAlerts_TransactionID'),
        (N'FraudAlerts', N'IX_FraudAlerts_ReviewStatus'),

        (N'AuditLogs', N'IX_AuditLogs_UserID'),

        (N'Notifications', N'IX_Notifications_Customer')
) AS expected(TableName, IndexName)

LEFT JOIN sys.tables AS t
    ON t.name = expected.TableName
   AND t.schema_id = SCHEMA_ID(N'dbo')

LEFT JOIN sys.indexes AS i
    ON i.object_id = t.object_id
   AND i.name = expected.IndexName

ORDER BY
    expected.TableName,
    expected.IndexName;


-- ============================================================
-- 10. VERIFY CUSTOMER EMAIL UNIQUENESS
-- ============================================================

SELECT
    Email,
    COUNT(*) AS DuplicateCount

FROM dbo.Customers

WHERE Email IS NOT NULL

GROUP BY Email

HAVING COUNT(*) > 1;


-- ============================================================
-- 11. VERIFY CUSTOMER PHONE UNIQUENESS
-- ============================================================

SELECT
    Phone,
    COUNT(*) AS DuplicateCount

FROM dbo.Customers

WHERE Phone IS NOT NULL
  AND Phone <> N''

GROUP BY Phone

HAVING COUNT(*) > 1;


-- ============================================================
-- 12. VERIFY NATIONAL ID UNIQUENESS
-- ============================================================

SELECT
    NationalID,
    COUNT(*) AS DuplicateCount

FROM dbo.Customers

GROUP BY NationalID

HAVING COUNT(*) > 1;


-- ============================================================
-- 13. VERIFY USER EMAIL UNIQUENESS
-- ============================================================

SELECT
    Email,
    COUNT(*) AS DuplicateCount

FROM dbo.Users

GROUP BY Email

HAVING COUNT(*) > 1;


-- ============================================================
-- 14. VERIFY ONE LOGIN PER CUSTOMER
-- ============================================================

SELECT
    CustomerID,
    COUNT(*) AS LoginCount

FROM dbo.Users

WHERE CustomerID IS NOT NULL

GROUP BY CustomerID

HAVING COUNT(*) > 1;


-- ============================================================
-- 15. VERIFY USER ROLE AND CUSTOMER RELATIONSHIP
-- ============================================================

SELECT
    UserID,
    CustomerID,
    Email,
    Role

FROM dbo.Users

WHERE Role NOT IN ('Admin', 'Customer')
   OR Role IS NULL
   OR
   (
       Role = 'Admin'
       AND CustomerID IS NOT NULL
   )
   OR
   (
       Role = 'Customer'
       AND CustomerID IS NULL
   );


-- ============================================================
-- 16. VERIFY USERS REFERENCING MISSING CUSTOMERS
-- ============================================================

SELECT
    u.UserID,
    u.CustomerID,
    u.Email

FROM dbo.Users AS u

LEFT JOIN dbo.Customers AS c
    ON c.CustomerID = u.CustomerID

WHERE u.CustomerID IS NOT NULL
  AND c.CustomerID IS NULL;


-- ============================================================
-- 17. VERIFY INVALID ACCOUNT BALANCES
-- ============================================================

SELECT
    AccountID,
    CustomerID,
    AccountNumber,
    Balance

FROM dbo.Accounts

WHERE Balance < 0
   OR Balance IS NULL;


-- ============================================================
-- 18. VERIFY DUPLICATE ACCOUNT NUMBERS
-- ============================================================

SELECT
    AccountNumber,
    COUNT(*) AS DuplicateCount

FROM dbo.Accounts

GROUP BY AccountNumber

HAVING COUNT(*) > 1;


-- ============================================================
-- 19. VERIFY ACCOUNTS REFERENCING MISSING CUSTOMERS
-- ============================================================

SELECT
    a.AccountID,
    a.CustomerID,
    a.AccountNumber

FROM dbo.Accounts AS a

LEFT JOIN dbo.Customers AS c
    ON c.CustomerID = a.CustomerID

WHERE c.CustomerID IS NULL;


-- ============================================================
-- 20. VERIFY ACTIVE ACCOUNT LIMIT
-- ============================================================

-- Application rule: Maximum 3 active accounts
-- per customer.

SELECT
    CustomerID,
    COUNT(*) AS ActiveAccountCount

FROM dbo.Accounts

WHERE IsActive = 1

GROUP BY CustomerID

HAVING COUNT(*) > 3;


-- ============================================================
-- 21. VERIFY TRANSACTION AMOUNTS
-- ============================================================

SELECT
    TransactionID,
    TransactionType,
    Amount

FROM dbo.Transactions

WHERE Amount <= 0
   OR Amount IS NULL;


-- ============================================================
-- 22. VERIFY TRANSACTION TYPES
-- ============================================================

SELECT
    TransactionID,
    TransactionType

FROM dbo.Transactions

WHERE TransactionType NOT IN
(
    'Deposit',
    'Withdrawal',
    'Transfer'
)
OR TransactionType IS NULL;


-- ============================================================
-- 23. VERIFY TRANSACTION STATUSES
-- ============================================================

SELECT
    TransactionID,
    Status

FROM dbo.Transactions

WHERE Status NOT IN
(
    'Completed',
    'Pending',
    'Blocked',
    'Failed'
)
OR Status IS NULL;


-- ============================================================
-- 24. VERIFY TRANSACTION ACCOUNT RELATIONSHIPS
-- ============================================================

SELECT
    TransactionID,
    TransactionType,
    FromAccountID,
    ToAccountID

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
);


-- ============================================================
-- 25. VERIFY MISSING TRANSACTION ACCOUNTS
-- ============================================================

SELECT
    t.TransactionID,
    t.FromAccountID,
    t.ToAccountID,

    CASE
        WHEN t.FromAccountID IS NOT NULL
             AND src.AccountID IS NULL
        THEN 'Missing source account'

        WHEN t.ToAccountID IS NOT NULL
             AND dst.AccountID IS NULL
        THEN 'Missing destination account'

        ELSE 'Unknown'
    END AS IntegrityProblem

FROM dbo.Transactions AS t

LEFT JOIN dbo.Accounts AS src
    ON src.AccountID = t.FromAccountID

LEFT JOIN dbo.Accounts AS dst
    ON dst.AccountID = t.ToAccountID

WHERE
    (
        t.FromAccountID IS NOT NULL
        AND src.AccountID IS NULL
    )
    OR
    (
        t.ToAccountID IS NOT NULL
        AND dst.AccountID IS NULL
    );


-- ============================================================
-- 26. VERIFY REQUIRED FRAUD RULE TYPES
-- ============================================================

SELECT
    expected.RuleType,

    COUNT(fr.RuleID) AS ExistingRuleCount,

    SUM
    (
        CASE
            WHEN fr.IsActive = 1 THEN 1
            ELSE 0
        END
    ) AS ActiveRuleCount,

    CASE
        WHEN COUNT(fr.RuleID) = 0
        THEN 'MISSING'
        ELSE 'PASS'
    END AS VerificationStatus

FROM
(
    VALUES
        ('HighAmount'),
        ('Frequent'),
        ('RepeatedAmount')
) AS expected(RuleType)

LEFT JOIN dbo.FraudRules AS fr
    ON fr.RuleType = expected.RuleType

GROUP BY expected.RuleType;


-- ============================================================
-- 27. VERIFY INVALID FRAUD RULE SETTINGS
-- ============================================================

SELECT
    RuleID,
    RuleName,
    RuleType,
    ThresholdValue,
    TimeWindowMinutes

FROM dbo.FraudRules

WHERE ThresholdValue <= 0
   OR ThresholdValue IS NULL
   OR TimeWindowMinutes <= 0
   OR TimeWindowMinutes IS NULL
   OR RuleType NOT IN
   (
       'HighAmount',
       'Frequent',
       'RepeatedAmount'
   )
   OR RuleType IS NULL;


-- ============================================================
-- 28. VERIFY DUPLICATE FRAUD ALERTS
-- ============================================================

SELECT
    TransactionID,
    RuleID,
    COUNT(*) AS DuplicateCount

FROM dbo.FraudAlerts

GROUP BY
    TransactionID,
    RuleID

HAVING COUNT(*) > 1;


-- ============================================================
-- 29. VERIFY FRAUD ALERT RISK LEVELS
-- ============================================================

SELECT
    AlertID,
    TransactionID,
    RiskLevel

FROM dbo.FraudAlerts

WHERE RiskLevel NOT IN ('Medium', 'High')
   OR RiskLevel IS NULL;


-- ============================================================
-- 30. VERIFY FRAUD REVIEW STATUSES
-- ============================================================

SELECT
    AlertID,
    TransactionID,
    ReviewStatus

FROM dbo.FraudAlerts

WHERE ReviewStatus NOT IN
(
    'Pending',
    'Reviewed',
    'FalsePositive',
    'ConfirmedFraud'
)
OR ReviewStatus IS NULL;


-- ============================================================
-- 31. VERIFY FRAUD ALERT REFERENCES
-- ============================================================

SELECT
    fa.AlertID,
    fa.TransactionID,
    fa.RuleID,

    CASE
        WHEN t.TransactionID IS NULL
        THEN 'Missing transaction'

        WHEN r.RuleID IS NULL
        THEN 'Missing fraud rule'

        ELSE 'Unknown'
    END AS IntegrityProblem

FROM dbo.FraudAlerts AS fa

LEFT JOIN dbo.Transactions AS t
    ON t.TransactionID = fa.TransactionID

LEFT JOIN dbo.FraudRules AS r
    ON r.RuleID = fa.RuleID

WHERE t.TransactionID IS NULL
   OR r.RuleID IS NULL;


-- ============================================================
-- 32. VERIFY FRAUD REVIEW USER REFERENCES
-- ============================================================

SELECT
    fa.AlertID,
    fa.ReviewedByUserID

FROM dbo.FraudAlerts AS fa

LEFT JOIN dbo.Users AS u
    ON u.UserID = fa.ReviewedByUserID

WHERE fa.ReviewedByUserID IS NOT NULL
  AND u.UserID IS NULL;


-- ============================================================
-- 33. VERIFY FRAUD REVIEW INFORMATION
-- ============================================================

-- Reports completed reviews with missing reviewer
-- or review timestamp.
-- Existing records are not changed.

SELECT
    AlertID,
    TransactionID,
    ReviewStatus,
    ReviewedAt,
    ReviewedByUserID,
    ReviewNote

FROM dbo.FraudAlerts

WHERE ReviewStatus IN
(
    'Reviewed',
    'FalsePositive',
    'ConfirmedFraud'
)
AND
(
    ReviewedAt IS NULL
    OR ReviewedByUserID IS NULL
);


-- ============================================================
-- 34. VERIFY AUDIT LOG USER REFERENCES
-- ============================================================

SELECT
    a.AuditID,
    a.UserID,
    a.ActionType,
    a.EntityName

FROM dbo.AuditLogs AS a

LEFT JOIN dbo.Users AS u
    ON u.UserID = a.UserID

WHERE a.UserID IS NOT NULL
  AND u.UserID IS NULL;


-- ============================================================
-- 35. VERIFY NOTIFICATION CUSTOMER REFERENCES
-- ============================================================

SELECT
    n.NotificationID,
    n.CustomerID,
    n.Title

FROM dbo.Notifications AS n

LEFT JOIN dbo.Customers AS c
    ON c.CustomerID = n.CustomerID

WHERE c.CustomerID IS NULL;


-- ============================================================
-- 36. VERIFY NOTIFICATION READ STATUS
-- ============================================================

SELECT
    NotificationID,
    CustomerID,
    IsRead

FROM dbo.Notifications

WHERE IsRead IS NULL;


-- ============================================================
-- 37. VERIFY EXISTING RECORD COUNTS
-- ============================================================

SELECT 'Customers' AS TableName, COUNT(*) AS RecordCount FROM dbo.Customers
UNION ALL
SELECT 'Users', COUNT(*) FROM dbo.Users
UNION ALL
SELECT 'Accounts', COUNT(*) FROM dbo.Accounts
UNION ALL
SELECT 'Transactions', COUNT(*) FROM dbo.Transactions
UNION ALL
SELECT 'FraudRules', COUNT(*) FROM dbo.FraudRules
UNION ALL
SELECT 'FraudAlerts', COUNT(*) FROM dbo.FraudAlerts
UNION ALL
SELECT 'AuditLogs', COUNT(*) FROM dbo.AuditLogs
UNION ALL
SELECT 'Notifications', COUNT(*) FROM dbo.Notifications;

-- ============================================================
-- 38. VERIFY TRANSACTION SUMMARY
-- ============================================================

SELECT
    TransactionType,
    Status,
    COUNT_BIG(*) AS TransactionCount,
    SUM(Amount) AS TotalAmount

FROM dbo.Transactions

GROUP BY
    TransactionType,
    Status

ORDER BY
    TransactionType,
    Status;


-- ============================================================
-- 39. VERIFY FRAUD ALERT SUMMARY
-- ============================================================

SELECT
    RiskLevel,
    ReviewStatus,
    COUNT_BIG(*) AS AlertCount

FROM dbo.FraudAlerts

GROUP BY
    RiskLevel,
    ReviewStatus

ORDER BY
    RiskLevel,
    ReviewStatus;


-- ============================================================
-- 40. VERIFY NOTIFICATION SUMMARY
-- ============================================================

SELECT
    NotificationType,
    IsRead,
    COUNT_BIG(*) AS NotificationCount

FROM dbo.Notifications

GROUP BY
    NotificationType,
    IsRead

ORDER BY
    NotificationType,
    IsRead;


-- ============================================================
-- 41. VERIFY OVERALL OBJECT COUNTS
-- ============================================================

SELECT
    'Tables' AS ObjectType,
    COUNT(*) AS ExistingCount,
    8 AS ExpectedCount

FROM sys.tables

WHERE schema_id = SCHEMA_ID(N'dbo')
  AND name IN
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

UNION ALL

SELECT
    'Views',
    COUNT(*),
    6

FROM sys.views

WHERE schema_id = SCHEMA_ID(N'dbo')
  AND name IN
  (
      N'vw_AccountSummary',
      N'vw_FraudAlertDetails',
      N'vw_DailyTransactionStats',
      N'vw_SuspiciousTransactions',
      N'vw_CustomerRiskSummary',
      N'vw_CustomerFraudReviews'
  )

UNION ALL

SELECT
    'Stored Procedures',
    COUNT(*),
    5

FROM sys.procedures

WHERE schema_id = SCHEMA_ID(N'dbo')
  AND name IN
  (
      N'sp_ExecuteBankTransaction',
      N'sp_Deposit',
      N'sp_Withdraw',
      N'sp_Transfer',
      N'sp_ScanFraud'
  );


-- ============================================================
-- 42. VERIFY EXPECTED OBJECTS - FINAL SUMMARY
-- ============================================================

SELECT
    DB_NAME() AS DatabaseName,

    (
        SELECT COUNT(*)
        FROM sys.tables
        WHERE schema_id = SCHEMA_ID(N'dbo')
          AND name IN
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
    ) AS TableCount,

    (
        SELECT COUNT(*)
        FROM sys.views
        WHERE schema_id = SCHEMA_ID(N'dbo')
          AND name IN
          (
              N'vw_AccountSummary',
              N'vw_FraudAlertDetails',
              N'vw_DailyTransactionStats',
              N'vw_SuspiciousTransactions',
              N'vw_CustomerRiskSummary',
              N'vw_CustomerFraudReviews'
          )
    ) AS ViewCount,

    (
        SELECT COUNT(*)
        FROM sys.procedures
        WHERE schema_id = SCHEMA_ID(N'dbo')
          AND name IN
          (
              N'sp_ExecuteBankTransaction',
              N'sp_Deposit',
              N'sp_Withdraw',
              N'sp_Transfer',
              N'sp_ScanFraud'
          )
    ) AS ProcedureCount;


-- ============================================================
-- END OF 07_verify.sql
-- ============================================================

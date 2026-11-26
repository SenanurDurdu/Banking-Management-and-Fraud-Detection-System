-- ============================================================
-- NG BANK
-- FILE: 06_verify.sql
-- DATABASE: BankingFraudDB_Test
-- READ-ONLY VERIFICATION
-- EXPECTED: 20 TABLES, 9 VIEWS,
--           10 PROCEDURES, 5 TRIGGERS
-- ============================================================

USE BankingFraudDB_Test;
GO

SET NOCOUNT ON; --Etkilenen satır sayısını yazdırmaz.
GO

-- ============================================================
-- 1. EXPECTED DATABASE OBJECTS
-- ============================================================

DECLARE @ExpectedTables TABLE --Tablo değişkenini oluşturur.
(
    TableName SYSNAME PRIMARY KEY
);

INSERT INTO @ExpectedTables --Beklenen 20 tablo adını tablo değişkenine ekler.
VALUES
(N'Customers'),
(N'Users'),
(N'Accounts'),
(N'Transactions'),
(N'FraudRules'),
(N'FraudAlerts'),
(N'AuditLogs'),
(N'Notifications'),
(N'CreditCardApplications'),
(N'CreditCards'),
(N'CreditCardTransactions'),
(N'CustomerAddresses'),
(N'CustomerContacts'),
(N'Beneficiaries'),
(N'AccountStatusHistory'),
(N'TransactionNotes'),
(N'FraudAlertReviewHistory'),
(N'CreditCardBillingSettings'),
(N'AccountDailyBalances'),
(N'FraudRiskAssessments');

DECLARE @ExpectedViews TABLE --Tablo değişkenini oluşturur.
(
    ViewName SYSNAME PRIMARY KEY
);

INSERT INTO @ExpectedViews --Beklenen 9 views adını tablo değişkenine ekler.
VALUES
(N'vw_AccountSummary'),
(N'vw_DailyTransactionStats'),
(N'vw_FraudTransactions'),
(N'vw_FraudAlertDetails'),
(N'vw_SuspiciousTransactions'),
(N'vw_CustomerRiskSummary'),
(N'vw_CustomerFraudReviews'),
(N'vw_AccountDailyBalanceDetails'),
(N'vw_FraudRiskAssessmentDetails');

DECLARE @ExpectedProcedures TABLE --Tablo değişkenini oluşturur.
(
    ProcedureName SYSNAME PRIMARY KEY
);

INSERT INTO @ExpectedProcedures --Beklenen 10 prosedürü tablo değişkenine ekler.
VALUES
(N'sp_ExecuteBankTransaction'),
(N'sp_Deposit'),
(N'sp_Withdraw'),
(N'sp_Transfer'),
(N'sp_ExecuteCreditCardTransaction'),
(N'sp_CreditCardPurchase'),
(N'sp_CreditCardCashAdvance'),
(N'sp_CreditCardPayment'),
(N'sp_ScanFraud'),
(N'sp_ScanCreditCardFraud');

DECLARE @ExpectedTriggers TABLE --Tablo değişkenini oluşturur.
(
    TriggerName SYSNAME PRIMARY KEY,
    ParentTable SYSNAME NOT NULL
);

INSERT INTO @ExpectedTriggers --Beklenen 5 trigger'ı tablo değişkenine ekler.
VALUES
(N'trg_Accounts_StatusHistory',N'Accounts'),
(N'trg_FraudAlerts_ReviewHistory',N'FraudAlerts'),
(N'trg_CreditCards_BillingSettings',N'CreditCards'),
(N'trg_Accounts_DailyBalances',N'Accounts'),
(N'trg_FraudAlerts_RiskAssessments',N'FraudAlerts');

DECLARE @Results TABLE --Sonuç rapor tablosu hazırlanır ver her ana kontrol buraya bir satır  ekler.
(
    CheckName NVARCHAR(150),
    ExpectedCount INT,
    ActualCount INT,
    Result VARCHAR(10)
);

-- ============================================================
-- 2. TABLE COUNT
-- ============================================================

DECLARE @TableCount INT;  --20 tablo oluştu mu kontrol eder ve pass yazdırır.

SELECT @TableCount = COUNT(*)
FROM sys.tables
WHERE schema_id = SCHEMA_ID(N'dbo')
  AND is_ms_shipped = 0;

INSERT INTO @Results --Sonuç tablosuna satır eklenir.
VALUES
(
    N'Total dbo Tables',
    20,
    @TableCount,
    CASE WHEN @TableCount = 20
         THEN 'PASS' ELSE 'FAIL' END
);

-- ============================================================
-- 3. REQUIRED TABLES
-- ============================================================
--Gerekli tablolar sayılır,bulunamayanlar missing olarak işratlenir.
SELECT
    e.TableName AS MissingTable
FROM @ExpectedTables AS e
WHERE OBJECT_ID(N'dbo.' + e.TableName,N'U') IS NULL;

DECLARE @RequiredTableCount INT;

SELECT @RequiredTableCount = COUNT(*)
FROM @ExpectedTables AS e
WHERE OBJECT_ID(N'dbo.' + e.TableName,N'U') IS NOT NULL;

INSERT INTO @Results
VALUES
(
    N'Required Tables',
    20,
    @RequiredTableCount,
    CASE WHEN @RequiredTableCount = 20
         THEN 'PASS' ELSE 'FAIL' END
);

-- ============================================================
-- 4. REQUIRED VIEWS
-- ============================================================
--Gerekli views'lar sayılır,bulunamayanlar missing olarak işratlenir.
SELECT
    e.ViewName AS MissingView
FROM @ExpectedViews AS e
WHERE OBJECT_ID(N'dbo.' + e.ViewName,N'V') IS NULL;

DECLARE @ViewCount INT;

SELECT @ViewCount = COUNT(*)
FROM @ExpectedViews AS e
WHERE OBJECT_ID(N'dbo.' + e.ViewName,N'V') IS NOT NULL;

INSERT INTO @Results
VALUES
(
    N'Required Views',
    9,
    @ViewCount,
    CASE WHEN @ViewCount = 9
         THEN 'PASS' ELSE 'FAIL' END
);

-- ============================================================
-- 5. REQUIRED PROCEDURES
-- ============================================================
--Gerekli procedure'ler sayılır,bulunamayanlar missing olarak işratlenir.
SELECT
    e.ProcedureName AS MissingProcedure
FROM @ExpectedProcedures AS e
WHERE OBJECT_ID(N'dbo.' + e.ProcedureName,N'P') IS NULL;

DECLARE @ProcedureCount INT;

SELECT @ProcedureCount = COUNT(*)
FROM @ExpectedProcedures AS e
WHERE OBJECT_ID(N'dbo.' + e.ProcedureName,N'P') IS NOT NULL;

INSERT INTO @Results
VALUES
(
    N'Required Procedures',
    10,
    @ProcedureCount,
    CASE WHEN @ProcedureCount = 10
         THEN 'PASS' ELSE 'FAIL' END
);

-- ============================================================
-- 6. REQUIRED ENABLED TRIGGERS
-- ============================================================
--Gerekli trigger'lar sayılır doğru tabloda etkin mi bakılır,bulunamayanlar missing olarak işratlenir.
SELECT
    e.TriggerName,
    e.ParentTable,
    CASE
        WHEN t.object_id IS NULL THEN 'MISSING'
        WHEN t.is_disabled = 1 THEN 'DISABLED'
        ELSE 'ENABLED'
    END AS TriggerStatus
FROM @ExpectedTriggers AS e
LEFT JOIN sys.triggers AS t
    ON t.name = e.TriggerName
   AND t.parent_id = OBJECT_ID(N'dbo.' + e.ParentTable);

DECLARE @TriggerCount INT;

SELECT @TriggerCount = COUNT(*)
FROM @ExpectedTriggers AS e
INNER JOIN sys.triggers AS t
    ON t.name = e.TriggerName
   AND t.parent_id = OBJECT_ID(N'dbo.' + e.ParentTable)
   AND t.is_disabled = 0;

INSERT INTO @Results
VALUES
(
    N'Required Enabled Triggers',
    5,
    @TriggerCount,
    CASE WHEN @TriggerCount = 5
         THEN 'PASS' ELSE 'FAIL' END
);

-- ============================================================
-- 7. NEW TABLE FOREIGN KEYS
-- ============================================================
--Eklenen 2 tablonun froeign keyleri kontrol edilir.
DECLARE @NewFKCount INT;

SELECT @NewFKCount = COUNT(*)
FROM sys.foreign_keys
WHERE
    (
        parent_object_id =
            OBJECT_ID(N'dbo.AccountDailyBalances')
        AND referenced_object_id =
            OBJECT_ID(N'dbo.Accounts')
    )
    OR
    (
        parent_object_id =
            OBJECT_ID(N'dbo.FraudRiskAssessments')
        AND referenced_object_id =
            OBJECT_ID(N'dbo.FraudAlerts')
    );

INSERT INTO @Results
VALUES
(
    N'New Table Foreign Keys',
    2,
    @NewFKCount,
    CASE WHEN @NewFKCount = 2
         THEN 'PASS' ELSE 'FAIL' END
);

-- ============================================================
-- 8. REQUIRED NEW INDEXES
-- ============================================================
--Gerekli iki yeni index var mı ve etkin mi kontrol edilir.
DECLARE @NewIndexCount INT;

SELECT @NewIndexCount = COUNT(*)
FROM sys.indexes
WHERE
    (
        object_id = OBJECT_ID(N'dbo.AccountDailyBalances')
        AND name = N'IX_AccountDailyBalances_Date'
        AND is_disabled = 0
    )
    OR
    (
        object_id = OBJECT_ID(N'dbo.FraudRiskAssessments')
        AND name = N'IX_FraudRiskAssessments_Level'
        AND is_disabled = 0
    );

INSERT INTO @Results
VALUES
(
    N'New Table Indexes',
    2,
    @NewIndexCount,
    CASE WHEN @NewIndexCount = 2
         THEN 'PASS' ELSE 'FAIL' END
);

-- ============================================================
-- 9. ACTIVE FRAUD RULES
-- ============================================================
--3 Fraud kuralı da etkin mi kontrol edilir.
DECLARE @FraudRuleCount INT;

SELECT @FraudRuleCount = COUNT(DISTINCT RuleType)
FROM dbo.FraudRules
WHERE IsActive = 1
  AND RuleType IN
  (
      'HighAmount',
      'Frequent',
      'RepeatedAmount'
  );

INSERT INTO @Results
VALUES
(
    N'Active Fraud Rule Types',
    3,
    @FraudRuleCount,
    CASE WHEN @FraudRuleCount = 3
         THEN 'PASS' ELSE 'FAIL' END
);

-- ============================================================
-- 10. ACCOUNT BALANCE COVERAGE
-- ============================================================
--Günlük bakiye doğru mu kontrol ediliyor.
DECLARE @MissingDailyBalances INT = NULL;

IF OBJECT_ID(N'dbo.AccountDailyBalances',N'U') IS NOT NULL
BEGIN
    EXEC sys.sp_executesql --Eksik hesap ayıklanıyor.
        N'
        SELECT @Missing = COUNT(*)
        FROM dbo.Accounts AS a
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM dbo.AccountDailyBalances AS adb
            WHERE adb.AccountID = a.AccountID
              AND adb.BalanceDate =
                  CONVERT(DATE,SYSDATETIME())
        );
        ',
        N'@Missing INT OUTPUT',
        @Missing = @MissingDailyBalances OUTPUT;
END;

INSERT INTO @Results
VALUES
(
    N'Accounts Missing Today Balance',
    0,
    ISNULL(@MissingDailyBalances,-1),
    CASE WHEN @MissingDailyBalances = 0
         THEN 'PASS' ELSE 'FAIL' END
);

-- ============================================================
-- 11. FRAUD ASSESSMENT COVERAGE
-- ============================================================
--Risk değerlendirmesinde eksik var mı kontrol edilir.
DECLARE @MissingAssessments INT = NULL;

IF OBJECT_ID(N'dbo.FraudRiskAssessments',N'U') IS NOT NULL
BEGIN
    EXEC sys.sp_executesql
        N'
        SELECT @Missing = COUNT(*)
        FROM dbo.FraudAlerts AS fa
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM dbo.FraudRiskAssessments AS fra
            WHERE fra.AlertID = fa.AlertID
        );
        ',
        N'@Missing INT OUTPUT',
        @Missing = @MissingAssessments OUTPUT;
END;

INSERT INTO @Results
VALUES
(
    N'Fraud Alerts Missing Assessment',
    0,
    ISNULL(@MissingAssessments,-1),
    CASE WHEN @MissingAssessments = 0
         THEN 'PASS' ELSE 'FAIL' END
);

-- ============================================================
-- 12. DISABLED OR UNTRUSTED CONSTRAINTS
-- ============================================================
--Devre dışı veya doğrulanmamış kısıtlamalar var mı kotrol edilir.
DECLARE @BadConstraintCount INT;

SELECT @BadConstraintCount = --Değişken açılır.
(
    SELECT COUNT(*)
    FROM sys.foreign_keys
    WHERE OBJECT_SCHEMA_NAME(parent_object_id) = N'dbo'
      AND (is_disabled = 1 OR is_not_trusted = 1)
)
+
(
    SELECT COUNT(*)
    FROM sys.check_constraints
    WHERE OBJECT_SCHEMA_NAME(parent_object_id) = N'dbo'
      AND (is_disabled = 1 OR is_not_trusted = 1)
);

INSERT INTO @Results
VALUES
(
    N'Disabled Or Untrusted Constraints',
    0,
    @BadConstraintCount,
    CASE WHEN @BadConstraintCount = 0
         THEN 'PASS' ELSE 'FAIL' END
);

-- ============================================================
-- 13. ALL TABLE RECORD COUNTS
-- Uses metadata so missing tables do not break verification.
-- ============================================================
--Her tabloda kaç kayıt var kontrol edilir.
IF OBJECT_ID('tempdb..#TableCounts') IS NOT NULL
    DROP TABLE #TableCounts;

SELECT
    t.name AS TableName,
    CONVERT(BIGINT,ISNULL(SUM(ps.row_count),0))
        AS RecordCount
INTO #TableCounts
FROM sys.tables AS t
LEFT JOIN sys.dm_db_partition_stats AS ps
    ON ps.object_id = t.object_id
   AND ps.index_id IN (0,1)
WHERE t.schema_id = SCHEMA_ID(N'dbo')
  AND t.is_ms_shipped = 0
GROUP BY t.name;

SELECT
    e.TableName,
    ISNULL(tc.RecordCount,0) AS RecordCount,
    CASE
        WHEN tc.TableName IS NULL THEN 'MISSING'
        WHEN tc.RecordCount = 0 THEN 'EMPTY'
        ELSE 'HAS DATA'
    END AS DataStatus
FROM @ExpectedTables AS e
LEFT JOIN #TableCounts AS tc
    ON tc.TableName = e.TableName
ORDER BY e.TableName;

-- ============================================================
-- 14. EMPTY TABLES
-- ============================================================
--Boş tablolar kontrol edilir.
SELECT
    e.TableName AS EmptyOrMissingTable,
    ISNULL(tc.RecordCount,0) AS RecordCount
FROM @ExpectedTables AS e
LEFT JOIN #TableCounts AS tc
    ON tc.TableName = e.TableName
WHERE ISNULL(tc.RecordCount,0) = 0
ORDER BY e.TableName;

DECLARE @NonEmptyTableCount INT;

SELECT @NonEmptyTableCount = COUNT(*)
FROM @ExpectedTables AS e
INNER JOIN #TableCounts AS tc
    ON tc.TableName = e.TableName
WHERE tc.RecordCount > 0;

INSERT INTO @Results
VALUES
(
    N'Tables Containing Data',
    20,
    @NonEmptyTableCount,
    CASE WHEN @NonEmptyTableCount = 20
         THEN 'PASS' ELSE 'FAIL' END
);

-- ============================================================
-- 15. INVALID ACCOUNT BALANCES
-- ============================================================
--Geçersiz hesap bakiyesi var mı kontrol edilir.
DECLARE @NegativeAccountCount INT;

SELECT @NegativeAccountCount = COUNT(*)
FROM dbo.Accounts
WHERE Balance < 0;

INSERT INTO @Results
VALUES
(
    N'Negative Account Balances',
    0,
    @NegativeAccountCount,
    CASE WHEN @NegativeAccountCount = 0
         THEN 'PASS' ELSE 'FAIL' END
);

-- ============================================================
-- 16. INVALID CREDIT CARD BALANCES
-- ============================================================
--Geçersiz kart bakiyesi var mı kontrol edilir.
DECLARE @InvalidCardCount INT;

SELECT @InvalidCardCount = COUNT(*)
FROM dbo.CreditCards
WHERE OutstandingBalance < 0
   OR OutstandingBalance > CreditLimit;

INSERT INTO @Results
VALUES
(
    N'Invalid Credit Card Balances',
    0,
    @InvalidCardCount,
    CASE WHEN @InvalidCardCount = 0
         THEN 'PASS' ELSE 'FAIL' END
);

-- ============================================================
-- 17. INVALID FRAUD ALERT REFERENCES
-- ============================================================
--Yanlış alarm referansı var mı kontrol edilir.
DECLARE @InvalidAlertCount INT;

SELECT @InvalidAlertCount = COUNT(*)
FROM dbo.FraudAlerts
WHERE
    (
        TransactionID IS NULL
        AND CardTransactionID IS NULL
    )
    OR
    (
        TransactionID IS NOT NULL
        AND CardTransactionID IS NOT NULL
    );

INSERT INTO @Results --Sonuç tablosuna satır olarak eklenir.
VALUES
(
    N'Invalid Fraud Alert References',
    0,
    @InvalidAlertCount,
    CASE WHEN @InvalidAlertCount = 0
         THEN 'PASS' ELSE 'FAIL' END
);

-- ============================================================
-- 18. FINAL VERIFICATION REPORT
-- ============================================================
--Başarılı kontroller listelenir.
SELECT
    CheckName,
    ExpectedCount,
    ActualCount,
    Result
FROM @Results
ORDER BY
    CASE WHEN Result = 'FAIL' THEN 0 ELSE 1 END,
    CheckName;

-- ============================================================
-- 19. FINAL STATUS
-- ============================================================
--Final durumu listelenir.
DECLARE @PassedChecks INT;
DECLARE @FailedChecks INT;

SELECT
    @PassedChecks =
        SUM(CASE WHEN Result = 'PASS' THEN 1 ELSE 0 END),
    @FailedChecks =
        SUM(CASE WHEN Result = 'FAIL' THEN 1 ELSE 0 END)
FROM @Results;

SELECT
    @PassedChecks AS PassedChecks,
    @FailedChecks AS FailedChecks,
    CASE
        WHEN @FailedChecks = 0
            THEN 'NG BANK VERIFICATION PASSED'
        ELSE 'NG BANK VERIFICATION FAILED'
    END AS FinalStatus;

-- ============================================================
-- 20. ALL APPLICATION TABLES
-- ============================================================
--Tüm tablolar
SELECT
    name AS TableName
FROM sys.tables
WHERE schema_id = SCHEMA_ID(N'dbo')
  AND is_ms_shipped = 0
ORDER BY name;

-- ============================================================
-- 21. ALL PROJECT VIEWS
-- ============================================================
--Tğm views'lar
SELECT
    name AS ViewName
FROM sys.views
WHERE schema_id = SCHEMA_ID(N'dbo')
ORDER BY name;

-- ============================================================
-- 22. ALL PROJECT PROCEDURES
-- ============================================================
--Tüm procedure'ler
SELECT
    name AS ProcedureName
FROM sys.procedures
WHERE schema_id = SCHEMA_ID(N'dbo')
ORDER BY name;

-- ============================================================
-- 23. ALL PROJECT TRIGGERS
-- ============================================================
--Tüm trigger'lar
SELECT
    t.name AS TriggerName,
    OBJECT_NAME(t.parent_id) AS ParentTable,
    t.is_disabled AS IsDisabled
FROM sys.triggers AS t
WHERE t.parent_class = 1
ORDER BY t.name;

PRINT '06_verify.sql completed.';
GO

-- ============================================================
-- VERIFY ACCOUNT TRIGGERS
-- ============================================================
--Hesap triggerları
SELECT
    t.name AS TriggerName,
    t.is_disabled AS IsDisabled
FROM sys.triggers AS t
WHERE t.parent_id = OBJECT_ID(N'dbo.Accounts')
ORDER BY t.name;
GO

/* ============================================================
   ALL DATA VIEWS - CURRENT 20 TABLES
   ============================================================ */
--Tüm tablo içerikleri
SELECT * FROM dbo.FraudRules;
SELECT * FROM dbo.Users;
SELECT * FROM dbo.Accounts;
SELECT * FROM dbo.Transactions;
SELECT * FROM dbo.FraudAlerts;
SELECT * FROM dbo.AuditLogs;
SELECT * FROM dbo.Customers;
SELECT * FROM dbo.Notifications;
SELECT * FROM dbo.CreditCardApplications;
SELECT * FROM dbo.CreditCards;
SELECT * FROM dbo.CreditCardTransactions;
SELECT * FROM dbo.CustomerAddresses;
SELECT * FROM dbo.CustomerContacts;
SELECT * FROM dbo.Beneficiaries;
SELECT * FROM dbo.AccountStatusHistory;
SELECT * FROM dbo.TransactionNotes;
SELECT * FROM dbo.FraudAlertReviewHistory;
SELECT * FROM dbo.CreditCardBillingSettings;
SELECT * FROM dbo.AccountDailyBalances;
SELECT * FROM dbo.FraudRiskAssessments;
GO


/* ============================================================
   DATA COUNT IN TABLES - CURRENT 20 TABLES
   ============================================================ */
--Tğm tabloların içindeki veri sayısı
SELECT 'Customers' AS TableName, COUNT(*) AS RecordCount
FROM dbo.Customers
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
SELECT 'Notifications', COUNT(*) FROM dbo.Notifications
UNION ALL
SELECT 'CreditCards', COUNT(*) FROM dbo.CreditCards
UNION ALL
SELECT 'CreditCardApplications', COUNT(*) FROM dbo.CreditCardApplications
UNION ALL
SELECT 'CreditCardTransactions', COUNT(*) FROM dbo.CreditCardTransactions
UNION ALL
SELECT 'CustomerAddresses', COUNT(*) FROM dbo.CustomerAddresses
UNION ALL
SELECT 'CustomerContacts', COUNT(*) FROM dbo.CustomerContacts
UNION ALL
SELECT 'Beneficiaries', COUNT(*) FROM dbo.Beneficiaries
UNION ALL
SELECT 'AccountStatusHistory', COUNT(*) FROM dbo.AccountStatusHistory
UNION ALL
SELECT 'TransactionNotes', COUNT(*) FROM dbo.TransactionNotes
UNION ALL
SELECT 'FraudAlertReviewHistory', COUNT(*) FROM dbo.FraudAlertReviewHistory
UNION ALL
SELECT 'CreditCardBillingSettings', COUNT(*) FROM dbo.CreditCardBillingSettings
UNION ALL
SELECT 'AccountDailyBalances', COUNT(*) FROM dbo.AccountDailyBalances
UNION ALL
SELECT 'FraudRiskAssessments', COUNT(*) FROM dbo.FraudRiskAssessments;
GO

/* ============================================================
   OPTIONAL: DELETE TEST DATA AND RESET IDENTITY COUNTERS

   WARNING:
   This section is COMMENTED OUT.
   Do not activate it unless you intentionally want
   to delete application data.

   FraudRules are preserved.

   CURRENT 20-TABLE STRUCTURE
   ============================================================

USE BankingFraudDB_Test;
GO

SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    -- Delete dependent records first
    DELETE FROM dbo.Notifications;
    DELETE FROM dbo.FraudAlertReviewHistory;

    -- New fraud assessment table
    DELETE FROM dbo.FraudRiskAssessments;

    DELETE FROM dbo.FraudAlerts;
    DELETE FROM dbo.AuditLogs;

    -- Credit card tables
    DELETE FROM dbo.CreditCardTransactions;
    DELETE FROM dbo.CreditCardBillingSettings;
    DELETE FROM dbo.CreditCards;
    DELETE FROM dbo.CreditCardApplications;

    -- Transaction tables
    DELETE FROM dbo.TransactionNotes;
    DELETE FROM dbo.Transactions;

    -- New daily balance table
    DELETE FROM dbo.AccountDailyBalances;

    -- Account tables
    DELETE FROM dbo.AccountStatusHistory;
    DELETE FROM dbo.Accounts;

    -- Customer tables
    DELETE FROM dbo.Beneficiaries;
    DELETE FROM dbo.CustomerAddresses;
    DELETE FROM dbo.CustomerContacts;
    DELETE FROM dbo.Users;
    DELETE FROM dbo.Customers;

    -- Reset identity counters

    DBCC CHECKIDENT ('dbo.Notifications', RESEED, 0);
    DBCC CHECKIDENT ('dbo.FraudAlertReviewHistory', RESEED, 0);

    -- New fraud assessment table
    DBCC CHECKIDENT ('dbo.FraudRiskAssessments', RESEED, 0);

    DBCC CHECKIDENT ('dbo.FraudAlerts', RESEED, 0);
    DBCC CHECKIDENT ('dbo.AuditLogs', RESEED, 0);

    -- Credit card tables
    DBCC CHECKIDENT ('dbo.CreditCardTransactions', RESEED, 0);
    DBCC CHECKIDENT ('dbo.CreditCardBillingSettings', RESEED, 0);
    DBCC CHECKIDENT ('dbo.CreditCards', RESEED, 0);
    DBCC CHECKIDENT ('dbo.CreditCardApplications', RESEED, 0);

    -- Transaction tables
    DBCC CHECKIDENT ('dbo.TransactionNotes', RESEED, 0);
    DBCC CHECKIDENT ('dbo.Transactions', RESEED, 0);

    -- New daily balance table
    DBCC CHECKIDENT ('dbo.AccountDailyBalances', RESEED, 0);

    -- Account tables
    DBCC CHECKIDENT ('dbo.AccountStatusHistory', RESEED, 0);
    DBCC CHECKIDENT ('dbo.Accounts', RESEED, 0);

    -- Customer tables
    DBCC CHECKIDENT ('dbo.Beneficiaries', RESEED, 0);
    DBCC CHECKIDENT ('dbo.CustomerAddresses', RESEED, 0);
    DBCC CHECKIDENT ('dbo.CustomerContacts', RESEED, 0);
    DBCC CHECKIDENT ('dbo.Users', RESEED, 0);
    DBCC CHECKIDENT ('dbo.Customers', RESEED, 0);

    -- FraudRules are preserved

    COMMIT TRANSACTION;

    PRINT 'Test data deleted and identity counters reset.';

END TRY
BEGIN CATCH

    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    PRINT ERROR_MESSAGE();

END CATCH;

============================================================ */


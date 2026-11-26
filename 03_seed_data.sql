-- ============================================================
-- NG BANK
-- FILE: 03_seed_data.sql
-- PURPOSE:
--   1. Create default fraud detection rules
--   2. Backfill daily account balances
--   3. Backfill fraud risk assessments
--
-- RUN AFTER:
--   01_schema.sql
--   02_constraints_indexes.sql
--
-- SAFE TO RERUN:
--   Existing customers, accounts, transactions and alerts
--   are not deleted.
-- ============================================================

USE BankingFraudDB_Test;
GO

SET NOCOUNT ON; --"1 row affected " gibi satır sayısı mesajlarını kapatır.
SET XACT_ABORT ON; --Çalışma zamanı hatası olduğunda o an açık olan sql işlemini geri alır.
GO

-- ============================================================
-- 1. HIGH AMOUNT RULE
-- ============================================================

IF NOT EXISTS  --60 dakika içerisinde 50000 den fazla tutarda işlem yapılırsa uyarı kuralıdır.
(
    SELECT 1
    FROM dbo.FraudRules
    WHERE RuleType = 'HighAmount'
)
BEGIN
    INSERT INTO dbo.FraudRules  --Fraud rules tablosuna eklenir
    (
        RuleName,
        RuleType,
        ThresholdValue,
        TimeWindowMinutes,
        IsActive
    )
    VALUES
    (
        N'High Value Transaction',
        'HighAmount',
        50000,
        60,
        1
    );
END;
GO

-- ============================================================
-- 2. FREQUENT TRANSACTIONS RULE
-- ============================================================

IF NOT EXISTS -- 10 dakika içerisinde 5 ve daha fazla işlem yapılırsa uyarı kuralıdır.
(
    SELECT 1
    FROM dbo.FraudRules
    WHERE RuleType = 'Frequent'
)
BEGIN
    INSERT INTO dbo.FraudRules  --Fraud rules tablosuna eklenir
    (
        RuleName,
        RuleType,
        ThresholdValue,
        TimeWindowMinutes,
        IsActive
    )
    VALUES
    (
        N'Frequent Transactions',
        'Frequent',
        5,
        10,
        1
    );
END;
GO

-- ============================================================
-- 3. REPEATED AMOUNT RULE
-- ============================================================

IF NOT EXISTS -- 60 dakika içerisinde 3 kere aynı tutarda işlem yapılırsa uyarı kuralıdır.
(
    SELECT 1
    FROM dbo.FraudRules
    WHERE RuleType = 'RepeatedAmount'
)
BEGIN
    INSERT INTO dbo.FraudRules --Fraud rules tablosuna eklenir
    (
        RuleName,
        RuleType,
        ThresholdValue,
        TimeWindowMinutes,
        IsActive
    )
    VALUES
    (
        N'Repeated Same Amount',
        'RepeatedAmount',
        3,
        60,
        1
    );
END;
GO

-- ============================================================
-- 4. ACCOUNT DAILY BALANCES BACKFILL
--
-- Only today's known account balance is recorded.
-- Historical balances are not invented.
-- ============================================================

DECLARE @Today DATE = CONVERT(DATE, SYSDATETIME());

INSERT INTO dbo.AccountDailyBalances
(
    AccountID,
    BalanceDate,
    ClosingBalance
)
SELECT --Hesabın kimliği,bugünün tarihi ve o an ki bakiye seçilir accounts tablosundan.
    a.AccountID,
    @Today,
    a.Balance
FROM dbo.Accounts AS a
WHERE NOT EXISTS --Aynı hesap ve tarih zaten varsa eklemez.
(
    SELECT 1
    FROM dbo.AccountDailyBalances AS adb
    WHERE adb.AccountID = a.AccountID
      AND adb.BalanceDate = @Today
);

PRINT 'AccountDailyBalances backfill completed.';
GO

-- ============================================================
-- 5. FRAUD RISK ASSESSMENTS BACKFILL
--
-- RiskLevel is copied from existing fraud alerts.
-- ReviewStatus is copied from existing fraud alerts.
--
-- This table has one assessment per alert.
-- ============================================================

INSERT INTO dbo.FraudRiskAssessments --Alarm id ve risk level ve incileme durumuna göre tablo doldurulur.
(
    AlertID,
    RiskLevel,
    ReviewStatus
)
SELECT
    fa.AlertID,
    fa.RiskLevel,
    fa.ReviewStatus
FROM dbo.FraudAlerts AS fa
WHERE fa.RiskLevel IN
(
    'Low',
    'Medium',
    'High',
    'Critical'
)
AND NOT EXISTS --Zaten içerilenler tekrar eklenmez.
(
    SELECT 1
    FROM dbo.FraudRiskAssessments AS fra
    WHERE fra.AlertID = fa.AlertID
);

PRINT 'FraudRiskAssessments backfill completed.';
GO

-- ============================================================
-- 6. VERIFY FRAUD RULES
-- ============================================================

SELECT       --Faud ruleslar id ye göre tabloda gösterilir.
    RuleID,
    RuleName,
    RuleType,
    ThresholdValue,
    TimeWindowMinutes,
    IsActive
FROM dbo.FraudRules
ORDER BY RuleID;
GO

-- ============================================================
-- 7. VERIFY DAILY BALANCES
-- ============================================================

SELECT          --Günlük harcamalar tabloda gösterilir.
    adb.BalanceID,
    adb.AccountID,
    a.AccountNumber,
    adb.BalanceDate,
    adb.ClosingBalance,
    adb.RecordedAt
FROM dbo.AccountDailyBalances AS adb
INNER JOIN dbo.Accounts AS a
    ON a.AccountID = adb.AccountID
ORDER BY
    adb.BalanceDate DESC,
    adb.AccountID;
GO

-- ============================================================
-- 8. VERIFY FRAUD RISK ASSESSMENTS
-- ============================================================

SELECT  --Risk değerlendirmeleri tabloda gösterilir.
    fra.AssessmentID,
    fra.AlertID,
    fa.TransactionID,
    fa.CardTransactionID,
    fra.RiskLevel,
    fra.ReviewStatus,
    fra.AssessedAt
FROM dbo.FraudRiskAssessments AS fra
INNER JOIN dbo.FraudAlerts AS fa
    ON fa.AlertID = fra.AlertID
ORDER BY fra.AssessmentID;
GO

-- ============================================================
-- 9. VERIFY TABLE COUNTS
-- ============================================================

SELECT --Tablo sayıları hesaplanır ve gösterilir.
    t.name AS TableName,
    p.RecordCount
FROM sys.tables AS t
CROSS APPLY
(
    SELECT SUM(ps.row_count) AS RecordCount
    FROM sys.dm_db_partition_stats AS ps
    WHERE ps.object_id = t.object_id
      AND ps.index_id IN (0, 1)
) AS p
WHERE t.schema_id = SCHEMA_ID(N'dbo')
  AND t.is_ms_shipped = 0
ORDER BY t.name;
GO

-- ============================================================
-- 10. VERIFY EXACTLY 20 TABLES
-- ============================================================
--20 tablo olduğu doğrulanır.
SELECT
    COUNT(*) AS TotalTables
FROM sys.tables
WHERE schema_id = SCHEMA_ID(N'dbo')
  AND is_ms_shipped = 0;
GO

PRINT '03_seed_data.sql completed.';
GO
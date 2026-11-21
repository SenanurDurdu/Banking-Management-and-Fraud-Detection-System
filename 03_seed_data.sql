
-- ============================================================
-- NG BANK
-- FILE: 03_seed_data.sql
-- PURPOSE: Insert default fraud detection rules
-- RUN AFTER: 01_schema.sql and 02_constraints_indexes.sql
-- STATUS: DRAFT - SQL SERVER TEST PENDING
--
-- Existing rules and thresholds are preserved.
-- No existing records are deleted.
-- ============================================================

USE BankingFraudDB;
GO

SET NOCOUNT ON;
GO

-- ============================================================
-- 1. HIGH AMOUNT RULE
-- Detect transactions of 50,000 TRY or more.
-- ============================================================

IF NOT EXISTS (
    SELECT 1
    FROM dbo.FraudRules
    WHERE RuleType = 'HighAmount'
)
BEGIN
    INSERT INTO dbo.FraudRules
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

    PRINT 'HighAmount rule created.';
END
ELSE
BEGIN
    PRINT 'HighAmount rule already exists. Skipped.';
END;
GO

-- ============================================================
-- 2. FREQUENT TRANSACTIONS RULE
-- Detect 5 or more transactions within 10 minutes.
-- ============================================================

IF NOT EXISTS (
    SELECT 1
    FROM dbo.FraudRules
    WHERE RuleType = 'Frequent'
)
BEGIN
    INSERT INTO dbo.FraudRules
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

    PRINT 'Frequent rule created.';
END
ELSE
BEGIN
    PRINT 'Frequent rule already exists. Skipped.';
END;
GO

-- ============================================================
-- 3. REPEATED AMOUNT RULE
-- Detect 3 same-amount transactions within 60 minutes.
-- ============================================================

IF NOT EXISTS (
    SELECT 1
    FROM dbo.FraudRules
    WHERE RuleType = 'RepeatedAmount'
)
BEGIN
    INSERT INTO dbo.FraudRules
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

    PRINT 'RepeatedAmount rule created.';
END
ELSE
BEGIN
    PRINT 'RepeatedAmount rule already exists. Skipped.';
END;
GO

-- ============================================================
-- 4. VERIFY INSERTED RULES
-- ============================================================

SELECT
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
-- 5. VERIFY REQUIRED RULE TYPES
-- ============================================================

SELECT
    Expected.RuleType,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM dbo.FraudRules AS fr
            WHERE fr.RuleType = Expected.RuleType
        )
        THEN 'EXISTS'
        ELSE 'MISSING'
    END AS RuleStatus
FROM (
    VALUES
        ('HighAmount'),
        ('Frequent'),
        ('RepeatedAmount')
) AS Expected(RuleType);
GO

PRINT 'NG BANK default fraud rules checked.';
GO

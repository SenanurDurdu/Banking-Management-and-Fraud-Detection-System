
-- ============================================================
-- BANKING MANAGEMENT & FRAUD DETECTION SYSTEM
-- FILE: 03_seed_fraud_rules.sql
-- PURPOSE: Default fraud detection rules
--
-- RUN AFTER:
--   01_schema.sql
--   02_constraints_indexes.sql
--
-- IMPORTANT:
--   Existing fraud rules are preserved.
--   Existing thresholds are not overwritten.
--   Existing records are not deleted.
-- ============================================================

USE BankingFraudDB;
GO

SET NOCOUNT ON;
GO


-- ============================================================
-- 1. HIGH AMOUNT RULE
-- ============================================================

-- Detect transactions with an amount of 50,000 or more.
--
-- RuleType: HighAmount
-- ThresholdValue: 50000
-- TimeWindowMinutes: 60
--
-- The fraud scanner uses the amount threshold directly.

IF NOT EXISTS
(
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
-- ============================================================

-- Detect frequent transactions involving the same account.
--
-- RuleType: Frequent
-- ThresholdValue: 5
-- TimeWindowMinutes: 10
--
-- Five or more matching completed transactions
-- within 10 minutes trigger the rule.

IF NOT EXISTS
(
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
-- ============================================================

-- Detect repeated transactions with the same amount.
--
-- RuleType: RepeatedAmount
-- ThresholdValue: 3
-- TimeWindowMinutes: 60
--
-- Three or more matching completed transactions
-- with the same amount within 60 minutes
-- trigger the rule.

IF NOT EXISTS
(
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
-- 4. VERIFY FRAUD RULES
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
-- 5. VERIFY RULE COUNTS
-- ============================================================

SELECT
    RuleType,
    COUNT(*) AS RuleCount,
    SUM
    (
        CASE
            WHEN IsActive = 1 THEN 1
            ELSE 0
        END
    ) AS ActiveRuleCount
FROM dbo.FraudRules
GROUP BY RuleType
ORDER BY RuleType;
GO


-- ============================================================
-- 6. VERIFY EXPECTED RULE TYPES
-- ============================================================

SELECT
    Expected.RuleType,
    CASE
        WHEN EXISTS
        (
            SELECT 1
            FROM dbo.FraudRules AS fr
            WHERE fr.RuleType = Expected.RuleType
        )
        THEN 'EXISTS'
        ELSE 'MISSING'
    END AS RuleStatus
FROM
(
    VALUES
        ('HighAmount'),
        ('Frequent'),
        ('RepeatedAmount')
) AS Expected(RuleType);
GO


-- ============================================================
-- 7. FINISH
-- ============================================================

PRINT '============================================';
PRINT '03_seed_fraud_rules.sql completed.';
PRINT 'Default fraud rules checked.';
PRINT 'Existing rule settings were preserved.';
PRINT 'No existing records were deleted.';
PRINT '============================================';
GO

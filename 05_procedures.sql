
-- ============================================================
-- NG BANK | 05_procedures.sql
-- CONSOLIDATED VERSION - 20 TABLE DATABASE
--
-- 10 original application-facing procedures
--  1 additional statement procedure
--  4 triggers
--  Billing settings backfill
--  Final verification
--
-- RUN AFTER:
-- 01_schema.sql
-- 02_constraints_indexes.sql
-- 03_seed_data.sql
-- 04_views.sql
--
-- SQL SERVER EXECUTION TEST: NOT YET PERFORMED
-- ============================================================

USE [BankingFraudDB_Test];
GO

SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

-- ============================================================
-- 01. MAIN BANK TRANSACTION ENGINE
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_ExecuteBankTransaction
    @Kind VARCHAR(20),
    @UserID INT,
    @SourceAccountID INT,
    @DestinationAccountNumber CHAR(18) = NULL,
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N''
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE
        @Role VARCHAR(20),
        @CustomerID INT,
        @SourceCustomerID INT,
        @SourceBalance DECIMAL(18,2),
        @SourceCurrency CHAR(3),
        @SourceActive BIT,
        @SourceFrozen BIT,
        @DestinationAccountID INT,
        @DestinationBalance DECIMAL(18,2),
        @DestinationCurrency CHAR(3),
        @DestinationActive BIT,
        @DestinationFrozen BIT,
        @FromID INT,
        @ToID INT,
        @TransactionID BIGINT,
        @FirstID INT,
        @SecondID INT,
        @LockedAccountID INT;

    DECLARE @Created TABLE
    (
        TransactionID BIGINT
    );

    IF @Kind IS NULL
       OR @Kind NOT IN ('Deposit','Withdrawal','Transfer')
        THROW 51001, 'Invalid transaction type.', 1;

    IF @UserID IS NULL OR @UserID <= 0
       OR @SourceAccountID IS NULL OR @SourceAccountID <= 0
        THROW 51002, 'Invalid user or account.', 1;

    IF @Amount IS NULL OR @Amount <= 0
        THROW 51003, 'Amount must be positive.', 1;

    IF @Kind = 'Transfer'
       AND
       (
           @DestinationAccountNumber IS NULL
           OR LEN(RTRIM(@DestinationAccountNumber)) <> 18
           OR LEFT(@DestinationAccountNumber, 2) <> 'TR'
           OR SUBSTRING(
               @DestinationAccountNumber,3,16
           ) LIKE '%[^0-9]%'
       )
        THROW 51005, 'Invalid destination account number.', 1;

    BEGIN TRY
        BEGIN TRANSACTION;

        SELECT
            @Role = u.Role,
            @CustomerID = u.CustomerID
        FROM dbo.Users AS u WITH (UPDLOCK,HOLDLOCK)
        LEFT JOIN dbo.Customers AS c
            ON c.CustomerID = u.CustomerID
        WHERE u.UserID = @UserID
          AND u.IsActive = 1
          AND
          (
              u.Role = 'Admin'
              OR
              (
                  u.Role = 'Customer'
                  AND c.IsActive = 1
              )
          );

        IF @Role IS NULL
            THROW 51006, 'User is not authorized.', 1;

        IF @Kind = 'Transfer'
        BEGIN
            SELECT
                @DestinationAccountID = AccountID
            FROM dbo.Accounts
            WHERE AccountNumber = @DestinationAccountNumber;

            IF @DestinationAccountID IS NULL
                THROW 51008, 'Destination account not found.', 1;

            IF @DestinationAccountID = @SourceAccountID
                THROW 51009, 'Cannot transfer to the same account.', 1;
        END;

        -- Lock accounts in deterministic order.

        SET @FirstID =
            CASE
                WHEN @DestinationAccountID IS NOT NULL
                 AND @DestinationAccountID < @SourceAccountID
                THEN @DestinationAccountID
                ELSE @SourceAccountID
            END;

        SET @SecondID =
            CASE
                WHEN @DestinationAccountID IS NULL THEN NULL
                WHEN @DestinationAccountID > @SourceAccountID
                THEN @DestinationAccountID
                ELSE @SourceAccountID
            END;

        SELECT @LockedAccountID = AccountID
        FROM dbo.Accounts WITH (UPDLOCK,HOLDLOCK)
        WHERE AccountID = @FirstID;

        IF @LockedAccountID IS NULL
            THROW 51010, 'Account not found.', 1;

        IF @SecondID IS NOT NULL
        BEGIN
            SET @LockedAccountID = NULL;

            SELECT @LockedAccountID = AccountID
            FROM dbo.Accounts WITH (UPDLOCK,HOLDLOCK)
            WHERE AccountID = @SecondID;

            IF @LockedAccountID IS NULL
                THROW 51010, 'Account not found.', 1;
        END;

        SELECT
            @SourceCustomerID = CustomerID,
            @SourceBalance = Balance,
            @SourceCurrency = Currency,
            @SourceActive = IsActive,
            @SourceFrozen = IsFrozen
        FROM dbo.Accounts
        WHERE AccountID = @SourceAccountID;

        IF @SourceActive IS NULL OR @SourceActive <> 1
            THROW 51011, 'Source account is unavailable.', 1;

        IF @SourceFrozen = 1
            THROW 51017, 'Source account is frozen.', 1;

        IF @Role = 'Customer'
           AND
           (
               @CustomerID IS NULL
               OR @SourceCustomerID <> @CustomerID
           )
            THROW 51012, 'Account ownership check failed.', 1;

        IF @Kind = 'Transfer'
        BEGIN
            SELECT
                @DestinationBalance = Balance,
                @DestinationCurrency = Currency,
                @DestinationActive = IsActive,
                @DestinationFrozen = IsFrozen
            FROM dbo.Accounts
            WHERE AccountID = @DestinationAccountID;

            IF @DestinationActive IS NULL
               OR @DestinationActive <> 1
                THROW 51013, 'Destination account is unavailable.', 1;

            IF @DestinationFrozen = 1
                THROW 51018, 'Destination account is frozen.', 1;

            IF @SourceCurrency <> @DestinationCurrency
                THROW 51014, 'Currency mismatch.', 1;
        END;

        IF @Kind IN ('Withdrawal','Transfer')
           AND @SourceBalance < @Amount
            THROW 51015, 'Insufficient balance.', 1;

        IF @Kind = 'Deposit'
           AND @SourceBalance >
               9999999999999999.99 - @Amount
            THROW 51016, 'Balance limit exceeded.', 1;

        IF @Kind = 'Transfer'
           AND @DestinationBalance >
               9999999999999999.99 - @Amount
            THROW 51016, 'Destination balance limit exceeded.', 1;

        SET @FromID = NULL;
        SET @ToID = NULL;

        IF @Kind = 'Deposit'
        BEGIN
            UPDATE dbo.Accounts
            SET Balance = Balance + @Amount
            WHERE AccountID = @SourceAccountID;

            SET @ToID = @SourceAccountID;
        END
        ELSE IF @Kind = 'Withdrawal'
        BEGIN
            UPDATE dbo.Accounts
            SET Balance = Balance - @Amount
            WHERE AccountID = @SourceAccountID;

            SET @FromID = @SourceAccountID;
        END
        ELSE
        BEGIN
            UPDATE dbo.Accounts
            SET Balance = Balance - @Amount
            WHERE AccountID = @SourceAccountID;

            UPDATE dbo.Accounts
            SET Balance = Balance + @Amount
            WHERE AccountID = @DestinationAccountID;

            SET @FromID = @SourceAccountID;
            SET @ToID = @DestinationAccountID;
        END;

        INSERT INTO dbo.Transactions
        (
            FromAccountID,
            ToAccountID,
            TransactionType,
            Amount,
            Description
        )
        OUTPUT INSERTED.TransactionID
        INTO @Created(TransactionID)
        VALUES
        (
            @FromID,
            @ToID,
            @Kind,
            @Amount,
            COALESCE(@Description,N'')
        );

        SELECT @TransactionID = TransactionID
        FROM @Created;

        INSERT INTO dbo.AuditLogs
        (
            ActionType,
            EntityName,
            EntityID,
            Description,
            UserID
        )
        VALUES
        (
            UPPER(@Kind),
            'Transaction',
            @TransactionID,
            CONCAT(@Kind, ': ', @Amount),
            @UserID
        );

        COMMIT TRANSACTION;

        SELECT @TransactionID AS TransactionID;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- ============================================================
-- 02. DEPOSIT
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_Deposit
    @UserID INT,
    @SourceAccountID INT,
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N''
AS
BEGIN
    SET NOCOUNT ON;

    EXEC dbo.sp_ExecuteBankTransaction
        @Kind = 'Deposit',
        @UserID = @UserID,
        @SourceAccountID = @SourceAccountID,
        @Amount = @Amount,
        @Description = @Description;
END;
GO

-- ============================================================
-- 03. WITHDRAW
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_Withdraw
    @UserID INT,
    @SourceAccountID INT,
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N''
AS
BEGIN
    SET NOCOUNT ON;

    EXEC dbo.sp_ExecuteBankTransaction
        @Kind = 'Withdrawal',
        @UserID = @UserID,
        @SourceAccountID = @SourceAccountID,
        @Amount = @Amount,
        @Description = @Description;
END;
GO

-- ============================================================
-- 04. TRANSFER
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_Transfer
    @UserID INT,
    @SourceAccountID INT,
    @DestinationAccountNumber CHAR(18),
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N''
AS
BEGIN
    SET NOCOUNT ON;

    EXEC dbo.sp_ExecuteBankTransaction
        @Kind = 'Transfer',
        @UserID = @UserID,
        @SourceAccountID = @SourceAccountID,
        @DestinationAccountNumber = @DestinationAccountNumber,
        @Amount = @Amount,
        @Description = @Description;
END;
GO

-- ============================================================
-- 05. CREDIT CARD TRANSACTION ENGINE
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_ExecuteCreditCardTransaction
    @Kind VARCHAR(20),
    @UserID INT,
    @CreditCardID BIGINT,
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N''
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE
        @CustomerID INT,
        @LinkedAccountID INT,
        @CardCustomerID INT,
        @CardStatus VARCHAR(20),
        @CardCurrency CHAR(3),
        @CreditLimit DECIMAL(18,2),
        @OutstandingBalance DECIMAL(18,2),
        @ExpiresAt DATE,
        @AccountBalance DECIMAL(18,2),
        @AccountActive BIT,
        @AccountFrozen BIT,
        @AccountCurrency CHAR(3),
        @BankTransactionID BIGINT,
        @CardTransactionID BIGINT,
        @BankDescription NVARCHAR(250);

    DECLARE @CreatedBank TABLE
    (
        TransactionID BIGINT
    );

    DECLARE @CreatedCard TABLE
    (
        CardTransactionID BIGINT
    );

    IF @Kind IS NULL
       OR @Kind NOT IN ('Purchase','CashAdvance','Payment')
        THROW 51101, 'Invalid card transaction type.', 1;

    IF @UserID IS NULL OR @UserID <= 0
        THROW 51102, 'Invalid user.', 1;

    IF @CreditCardID IS NULL OR @CreditCardID <= 0
        THROW 51103, 'Invalid credit card.', 1;

    IF @Amount IS NULL OR @Amount <= 0
        THROW 51104, 'Amount must be positive.', 1;

    SET @Description = COALESCE(@Description,N'');

    BEGIN TRY
        BEGIN TRANSACTION;

        SELECT @CustomerID = u.CustomerID
        FROM dbo.Users AS u WITH (UPDLOCK,HOLDLOCK)
        INNER JOIN dbo.Customers AS c
            ON c.CustomerID = u.CustomerID
        WHERE u.UserID = @UserID
          AND u.Role = 'Customer'
          AND u.IsActive = 1
          AND c.IsActive = 1;

        IF @CustomerID IS NULL
            THROW 51105, 'Active customer required.', 1;

        SELECT @LinkedAccountID = LinkedAccountID
        FROM dbo.CreditCards
        WHERE CreditCardID = @CreditCardID
          AND CustomerID = @CustomerID;

        IF @LinkedAccountID IS NULL
            THROW 51106, 'Credit card not found.', 1;

        SELECT
            @AccountBalance = Balance,
            @AccountActive = IsActive,
            @AccountFrozen = IsFrozen,
            @AccountCurrency = Currency
        FROM dbo.Accounts WITH (UPDLOCK,HOLDLOCK)
        WHERE AccountID = @LinkedAccountID
          AND CustomerID = @CustomerID;

        IF @AccountActive IS NULL OR @AccountActive <> 1
            THROW 51107, 'Linked account unavailable.', 1;

        IF @AccountFrozen = 1
            THROW 51108, 'Linked account frozen.', 1;

        IF @AccountCurrency <> 'TRY'
            THROW 51109, 'Only TRY supported.', 1;

        SELECT
            @CardCustomerID = CustomerID,
            @CardStatus = CardStatus,
            @CardCurrency = Currency,
            @CreditLimit = CreditLimit,
            @OutstandingBalance = OutstandingBalance,
            @ExpiresAt = ExpiresAt
        FROM dbo.CreditCards WITH (UPDLOCK,HOLDLOCK)
        WHERE CreditCardID = @CreditCardID
          AND CustomerID = @CustomerID
          AND LinkedAccountID = @LinkedAccountID;

        IF @CardCustomerID IS NULL
            THROW 51110, 'Credit card unavailable.', 1;

        IF @CardCurrency <> 'TRY'
            THROW 51111, 'Card currency not supported.', 1;

        IF @Kind IN ('Purchase','CashAdvance')
        BEGIN
            IF @CardStatus <> 'Active'
                THROW 51112, 'Card is not active.', 1;

            IF @ExpiresAt < CONVERT(DATE,SYSDATETIME())
                THROW 51113, 'Card has expired.', 1;

            IF @Amount > @CreditLimit - @OutstandingBalance
                THROW 51114, 'Insufficient card limit.', 1;
        END;

        IF @Kind = 'CashAdvance'
           AND @AccountBalance >
               9999999999999999.99 - @Amount
            THROW 51115, 'Account balance limit exceeded.', 1;

        IF @Kind = 'Payment'
        BEGIN
            IF @OutstandingBalance <= 0
                THROW 51116, 'No card debt.', 1;

            IF @Amount > @OutstandingBalance
                THROW 51117, 'Payment exceeds card debt.', 1;

            IF @Amount > @AccountBalance
                THROW 51118, 'Insufficient bank balance.', 1;
        END;

        IF @Kind = 'Purchase'
        BEGIN
            UPDATE dbo.CreditCards
            SET OutstandingBalance = OutstandingBalance + @Amount
            WHERE CreditCardID = @CreditCardID;
        END
        ELSE IF @Kind = 'CashAdvance'
        BEGIN
            UPDATE dbo.CreditCards
            SET OutstandingBalance = OutstandingBalance + @Amount
            WHERE CreditCardID = @CreditCardID;

            UPDATE dbo.Accounts
            SET Balance = Balance + @Amount
            WHERE AccountID = @LinkedAccountID;

            SET @BankDescription = LEFT(
                CONCAT(
                    'Credit card cash advance. CardID=',
                    @CreditCardID,
                    '. ',
                    @Description
                ),250
            );

            INSERT INTO dbo.Transactions
            (
                FromAccountID,
                ToAccountID,
                TransactionType,
                Amount,
                Description
            )
            OUTPUT INSERTED.TransactionID
            INTO @CreatedBank(TransactionID)
            VALUES
            (
                NULL,
                @LinkedAccountID,
                'Deposit',
                @Amount,
                @BankDescription
            );
        END
        ELSE
        BEGIN
            UPDATE dbo.Accounts
            SET Balance = Balance - @Amount
            WHERE AccountID = @LinkedAccountID;

            UPDATE dbo.CreditCards
            SET OutstandingBalance = OutstandingBalance - @Amount
            WHERE CreditCardID = @CreditCardID;

            SET @BankDescription = LEFT(
                CONCAT(
                    'Credit card debt payment. CardID=',
                    @CreditCardID,
                    '. ',
                    @Description
                ),250
            );

            INSERT INTO dbo.Transactions
            (
                FromAccountID,
                ToAccountID,
                TransactionType,
                Amount,
                Description
            )
            OUTPUT INSERTED.TransactionID
            INTO @CreatedBank(TransactionID)
            VALUES
            (
                @LinkedAccountID,
                NULL,
                'Withdrawal',
                @Amount,
                @BankDescription
            );
        END;

        SELECT @BankTransactionID = TransactionID
        FROM @CreatedBank;

        INSERT INTO dbo.CreditCardTransactions
        (
            CreditCardID,
            BankTransactionID,
            TransactionType,
            Amount,
            Description,
            TransactionStatus
        )
        OUTPUT INSERTED.CardTransactionID
        INTO @CreatedCard(CardTransactionID)
        VALUES
        (
            @CreditCardID,
            @BankTransactionID,
            @Kind,
            @Amount,
            CASE
                WHEN LEN(@Description) > 0 THEN @Description
                WHEN @Kind = 'Purchase' THEN N'Card purchase'
                WHEN @Kind = 'CashAdvance' THEN N'Cash advance'
                ELSE N'Card payment'
            END,
            'Completed'
        );

        SELECT @CardTransactionID = CardTransactionID
        FROM @CreatedCard;

        IF @BankTransactionID IS NOT NULL
        BEGIN
            INSERT INTO dbo.AuditLogs
            (
                ActionType,
                EntityName,
                EntityID,
                Description,
                UserID
            )
            VALUES
            (
                CASE
                    WHEN @Kind = 'CashAdvance'
                    THEN 'DEPOSIT'
                    ELSE 'WITHDRAWAL'
                END,
                'Transaction',
                @BankTransactionID,
                @BankDescription,
                @UserID
            );
        END;

        INSERT INTO dbo.AuditLogs
        (
            ActionType,
            EntityName,
            EntityID,
            Description,
            UserID
        )
        VALUES
        (
            CASE
                WHEN @Kind = 'Purchase'
                    THEN 'CREDIT_CARD_PURCHASE'
                WHEN @Kind = 'CashAdvance'
                    THEN 'CREDIT_CARD_CASH_ADVANCE'
                ELSE 'CREDIT_CARD_PAYMENT'
            END,
            'CreditCardTransactions',
            @CardTransactionID,
            CONCAT(
                'CardID=',@CreditCardID,
                ', Amount=',@Amount
            ),
            @UserID
        );

        COMMIT TRANSACTION;

        SELECT
            @CardTransactionID AS CardTransactionID,
            @BankTransactionID AS BankTransactionID;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- ============================================================
-- 06. CREDIT CARD PURCHASE
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_CreditCardPurchase
    @UserID INT,
    @CreditCardID BIGINT,
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N''
AS
BEGIN
    SET NOCOUNT ON;

    EXEC dbo.sp_ExecuteCreditCardTransaction
        @Kind = 'Purchase',
        @UserID = @UserID,
        @CreditCardID = @CreditCardID,
        @Amount = @Amount,
        @Description = @Description;
END;
GO

-- ============================================================
-- 07. CREDIT CARD CASH ADVANCE
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_CreditCardCashAdvance
    @UserID INT,
    @CreditCardID BIGINT,
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N''
AS
BEGIN
    SET NOCOUNT ON;

    EXEC dbo.sp_ExecuteCreditCardTransaction
        @Kind = 'CashAdvance',
        @UserID = @UserID,
        @CreditCardID = @CreditCardID,
        @Amount = @Amount,
        @Description = @Description;
END;
GO

-- ============================================================
-- 08. CREDIT CARD PAYMENT
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_CreditCardPayment
    @UserID INT,
    @CreditCardID BIGINT,
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N''
AS
BEGIN
    SET NOCOUNT ON;

    EXEC dbo.sp_ExecuteCreditCardTransaction
        @Kind = 'Payment',
        @UserID = @UserID,
        @CreditCardID = @CreditCardID,
        @Amount = @Amount,
        @Description = @Description;
END;
GO

-- ============================================================
-- 09. BANK FRAUD SCAN
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_ScanFraud
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE
        @NewAlerts INT = 0,
        @LockResult INT;

    DECLARE @Created TABLE
    (
        AlertID BIGINT,
        TransactionID BIGINT,
        RuleID INT,
        RiskLevel VARCHAR(10)
    );

    IF @UserID IS NULL OR @UserID <= 0
        THROW 51030, 'Invalid UserID.', 1;

    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.Users
        WHERE UserID = @UserID
          AND Role = 'Admin'
          AND IsActive = 1
    )
        THROW 51031, 'Admin access required.', 1;

    BEGIN TRY
        BEGIN TRANSACTION;

        EXEC @LockResult = sys.sp_getapplock
            @Resource = 'BankingFraudDB_FraudScan',
            @LockMode = 'Exclusive',
            @LockOwner = 'Transaction',
            @LockTimeout = 10000;

        IF @LockResult < 0
            THROW 51032, 'Fraud scan lock failed.', 1;

        ;WITH Candidates AS
        (
            SELECT
                t.TransactionID,
                t.Amount,
                t.TransactionDate,
                COALESCE(
                    t.FromAccountID,
                    t.ToAccountID
                ) AS AccountID
            FROM dbo.Transactions AS t
            WHERE t.Status = 'Completed'
        ),
        Matches AS
        (
            SELECT
                t.TransactionID,
                t.Amount,
                r.RuleID,
                r.RuleType,
                r.ThresholdValue,
                r.TimeWindowMinutes,
                x.MatchCount
            FROM Candidates AS t
            CROSS JOIN dbo.FraudRules AS r
            OUTER APPLY
            (
                SELECT COUNT_BIG(*) AS MatchCount
                FROM dbo.Transactions AS p
                WHERE r.RuleType IN
                (
                    'Frequent',
                    'RepeatedAmount'
                )
                  AND r.TimeWindowMinutes > 0
                  AND t.AccountID IS NOT NULL
                  AND p.Status = 'Completed'
                  AND p.TransactionDate >= DATEADD(
                      MINUTE,
                      -r.TimeWindowMinutes,
                      t.TransactionDate
                  )
                  AND
                  (
                      p.TransactionDate < t.TransactionDate
                      OR
                      (
                          p.TransactionDate = t.TransactionDate
                          AND p.TransactionID <= t.TransactionID
                      )
                  )
                  AND
                  (
                      p.FromAccountID = t.AccountID
                      OR p.ToAccountID = t.AccountID
                  )
                  AND
                  (
                      r.RuleType = 'Frequent'
                      OR p.Amount = t.Amount
                  )
            ) AS x
            WHERE r.IsActive = 1
              AND r.RuleType IN
              (
                  'HighAmount',
                  'Frequent',
                  'RepeatedAmount'
              )
        ),
        Suspicious AS
        (
            SELECT
                TransactionID,
                RuleID,
                CASE
                    WHEN RuleType = 'HighAmount'
                    THEN 'High'
                    WHEN MatchCount >= ThresholdValue + 3
                    THEN 'High'
                    ELSE 'Medium'
                END AS RiskLevel,
                CAST(
                    CASE
                        WHEN RuleType = 'HighAmount'
                        THEN CONCAT(
                            'High amount: ',
                            Amount,
                            ', threshold: ',
                            ThresholdValue
                        )
                        ELSE CONCAT(
                            MatchCount,
                            ' matching transactions in ',
                            TimeWindowMinutes,
                            ' minutes'
                        )
                    END
                    AS NVARCHAR(500)
                ) AS AlertDescription
            FROM Matches
            WHERE
                (
                    RuleType = 'HighAmount'
                    AND Amount >= ThresholdValue
                )
                OR
                (
                    RuleType IN
                    (
                        'Frequent',
                        'RepeatedAmount'
                    )
                    AND TimeWindowMinutes > 0
                    AND MatchCount >= ThresholdValue
                )
        )
        INSERT INTO dbo.FraudAlerts
        (
            TransactionID,
            RuleID,
            AlertDescription,
            RiskLevel
        )
        OUTPUT
            INSERTED.AlertID,
            INSERTED.TransactionID,
            INSERTED.RuleID,
            INSERTED.RiskLevel
        INTO @Created
        (
            AlertID,
            TransactionID,
            RuleID,
            RiskLevel
        )
        SELECT
            s.TransactionID,
            s.RuleID,
            s.AlertDescription,
            s.RiskLevel
        FROM Suspicious AS s
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM dbo.FraudAlerts AS fa
                WITH (UPDLOCK,HOLDLOCK)
            WHERE fa.TransactionID = s.TransactionID
              AND fa.RuleID = s.RuleID
        );

        SELECT @NewAlerts = COUNT(*)
        FROM @Created;

        INSERT INTO dbo.AuditLogs
        (
            ActionType,
            EntityName,
            EntityID,
            Description,
            UserID
        )
        SELECT
            'FRAUD_ALERT',
            'FraudAlert',
            c.AlertID,
            CONCAT(
                'TransactionID=',c.TransactionID,
                ', RuleID=',c.RuleID,
                ', Risk=',c.RiskLevel
            ),
            @UserID
        FROM @Created AS c;

        INSERT INTO dbo.AuditLogs
        (
            ActionType,
            EntityName,
            EntityID,
            Description,
            UserID
        )
        VALUES
        (
            'FRAUD_SCAN',
            'FraudAlert',
            NULL,
            CONCAT(@NewAlerts,' new bank fraud alerts'),
            @UserID
        );

        COMMIT TRANSACTION;

        SELECT @NewAlerts AS NewAlerts;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- ============================================================
-- 10. CREDIT CARD FRAUD SCAN
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_ScanCreditCardFraud
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE
        @NewAlerts INT = 0,
        @LockResult INT;

    DECLARE @Created TABLE
    (
        AlertID BIGINT,
        CardTransactionID BIGINT,
        RuleID INT,
        RiskLevel VARCHAR(10)
    );

    IF @UserID IS NULL OR @UserID <= 0
        THROW 51040, 'Invalid UserID.', 1;

    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.Users
        WHERE UserID = @UserID
          AND Role = 'Admin'
          AND IsActive = 1
    )
        THROW 51041, 'Admin access required.', 1;

    BEGIN TRY
        BEGIN TRANSACTION;

        EXEC @LockResult = sys.sp_getapplock
            @Resource =
                'BankingFraudDB_CreditCardFraudScan',
            @LockMode = 'Exclusive',
            @LockOwner = 'Transaction',
            @LockTimeout = 10000;

        IF @LockResult < 0
            THROW 51042, 'Card fraud scan lock failed.', 1;

        ;WITH Candidates AS
        (
            SELECT
                ct.CardTransactionID,
                ct.CreditCardID,
                ct.Amount,
                ct.CreatedAt
            FROM dbo.CreditCardTransactions AS ct
            WHERE ct.TransactionStatus = 'Completed'
              AND ct.TransactionType = 'Purchase'
              AND ct.BankTransactionID IS NULL
        ),
        Matches AS
        (
            SELECT
                t.CardTransactionID,
                t.Amount,
                r.RuleID,
                r.RuleType,
                r.ThresholdValue,
                r.TimeWindowMinutes,
                x.MatchCount
            FROM Candidates AS t
            CROSS JOIN dbo.FraudRules AS r
            OUTER APPLY
            (
                SELECT COUNT_BIG(*) AS MatchCount
                FROM dbo.CreditCardTransactions AS p
                WHERE r.RuleType IN
                (
                    'Frequent',
                    'RepeatedAmount'
                )
                  AND r.TimeWindowMinutes > 0
                  AND p.CreditCardID = t.CreditCardID
                  AND p.TransactionStatus = 'Completed'
                  AND p.TransactionType = 'Purchase'
                  AND p.BankTransactionID IS NULL
                  AND p.CreatedAt >= DATEADD(
                      MINUTE,
                      -r.TimeWindowMinutes,
                      t.CreatedAt
                  )
                  AND
                  (
                      p.CreatedAt < t.CreatedAt
                      OR
                      (
                          p.CreatedAt = t.CreatedAt
                          AND p.CardTransactionID <=
                              t.CardTransactionID
                      )
                  )
                  AND
                  (
                      r.RuleType = 'Frequent'
                      OR p.Amount = t.Amount
                  )
            ) AS x
            WHERE r.IsActive = 1
              AND r.RuleType IN
              (
                  'HighAmount',
                  'Frequent',
                  'RepeatedAmount'
              )
        ),
        Suspicious AS
        (
            SELECT
                CardTransactionID,
                RuleID,
                CASE
                    WHEN RuleType = 'HighAmount'
                    THEN 'High'
                    WHEN MatchCount >= ThresholdValue + 3
                    THEN 'High'
                    ELSE 'Medium'
                END AS RiskLevel,
                CAST(
                    CASE
                        WHEN RuleType = 'HighAmount'
                        THEN CONCAT(
                            'High card purchase: ',
                            Amount,
                            ', threshold: ',
                            ThresholdValue
                        )
                        ELSE CONCAT(
                            MatchCount,
                            ' matching card purchases in ',
                            TimeWindowMinutes,
                            ' minutes'
                        )
                    END
                    AS NVARCHAR(500)
                ) AS AlertDescription
            FROM Matches
            WHERE
                (
                    RuleType = 'HighAmount'
                    AND Amount >= ThresholdValue
                )
                OR
                (
                    RuleType IN
                    (
                        'Frequent',
                        'RepeatedAmount'
                    )
                    AND TimeWindowMinutes > 0
                    AND MatchCount >= ThresholdValue
                )
        )
        INSERT INTO dbo.FraudAlerts
        (
            TransactionID,
            CardTransactionID,
            RuleID,
            AlertDescription,
            RiskLevel
        )
        OUTPUT
            INSERTED.AlertID,
            INSERTED.CardTransactionID,
            INSERTED.RuleID,
            INSERTED.RiskLevel
        INTO @Created
        (
            AlertID,
            CardTransactionID,
            RuleID,
            RiskLevel
        )
        SELECT
            NULL,
            s.CardTransactionID,
            s.RuleID,
            s.AlertDescription,
            s.RiskLevel
        FROM Suspicious AS s
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM dbo.FraudAlerts AS fa
                WITH (UPDLOCK,HOLDLOCK)
            WHERE fa.CardTransactionID = s.CardTransactionID
              AND fa.RuleID = s.RuleID
        );

        SELECT @NewAlerts = COUNT(*)
        FROM @Created;

        INSERT INTO dbo.AuditLogs
        (
            ActionType,
            EntityName,
            EntityID,
            Description,
            UserID
        )
        SELECT
            'FRAUD_ALERT',
            'FraudAlert',
            c.AlertID,
            CONCAT(
                'CardTransactionID=',c.CardTransactionID,
                ', RuleID=',c.RuleID,
                ', Risk=',c.RiskLevel
            ),
            @UserID
        FROM @Created AS c;

        INSERT INTO dbo.AuditLogs
        (
            ActionType,
            EntityName,
            EntityID,
            Description,
            UserID
        )
        VALUES
        (
            'CREDIT_CARD_FRAUD_SCAN',
            'FraudAlert',
            NULL,
            CONCAT(@NewAlerts,' new card fraud alerts'),
            @UserID
        );

        COMMIT TRANSACTION;

        SELECT @NewAlerts AS NewAlerts;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- ============================================================
-- 11. ACCOUNT STATUS HISTORY TRIGGER
-- ============================================================

CREATE OR ALTER TRIGGER dbo.trg_Accounts_StatusHistory
ON dbo.Accounts
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF NOT (UPDATE(IsActive) OR UPDATE(IsFrozen))
        RETURN;

    INSERT INTO dbo.AccountStatusHistory
    (
        AccountID,
        ChangedByUserID,
        OldIsActive,
        NewIsActive,
        OldIsFrozen,
        NewIsFrozen,
        ChangeReason,
        ChangedAt
    )
    SELECT
        i.AccountID,
        NULL,
        d.IsActive,
        i.IsActive,
        d.IsFrozen,
        i.IsFrozen,
        N'Account status changed',
        SYSDATETIME()
    FROM inserted AS i
    INNER JOIN deleted AS d
        ON d.AccountID = i.AccountID
    WHERE i.IsActive <> d.IsActive
       OR i.IsFrozen <> d.IsFrozen;
END;
GO

-- ============================================================
-- 12. FRAUD ALERT REVIEW HISTORY TRIGGER
-- ============================================================

CREATE OR ALTER TRIGGER dbo.trg_FraudAlerts_ReviewHistory
ON dbo.FraudAlerts
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF NOT
    (
        UPDATE(ReviewStatus)
        OR UPDATE(ReviewNote)
        OR UPDATE(ReviewedByUserID)
    )
        RETURN;

    INSERT INTO dbo.FraudAlertReviewHistory
    (
        AlertID,
        ReviewedByUserID,
        OldReviewStatus,
        NewReviewStatus,
        ReviewNote,
        ReviewedAt
    )
    SELECT
        i.AlertID,
        i.ReviewedByUserID,
        d.ReviewStatus,
        i.ReviewStatus,
        i.ReviewNote,
        COALESCE(i.ReviewedAt, SYSDATETIME())
    FROM inserted AS i
    INNER JOIN deleted AS d
        ON d.AlertID = i.AlertID
    WHERE i.ReviewStatus <> d.ReviewStatus
       OR ISNULL(i.ReviewNote, N'')
          <> ISNULL(d.ReviewNote, N'')
       OR ISNULL(i.ReviewedByUserID, -1)
          <> ISNULL(d.ReviewedByUserID, -1);
END;
GO

-- ============================================================
-- 13. DEFAULT BILLING SETTINGS TRIGGER
-- ============================================================

CREATE OR ALTER TRIGGER dbo.trg_CreditCards_BillingSettings
ON dbo.CreditCards
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.CreditCardBillingSettings
    (
        CreditCardID,
        ClosingDay,
        DueDaysAfterClosing,
        EffectiveFrom,
        UpdatedAt
    )
    SELECT
        i.CreditCardID,
        20,
        10,
        CONVERT(DATE, SYSDATETIME()),
        SYSDATETIME()
    FROM inserted AS i
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.CreditCardBillingSettings AS bs
        WHERE bs.CreditCardID = i.CreditCardID
    );
END;
GO

-- ============================================================
-- 14. BACKFILL BILLING SETTINGS
-- ============================================================

INSERT INTO dbo.CreditCardBillingSettings
(
    CreditCardID,
    ClosingDay,
    DueDaysAfterClosing,
    EffectiveFrom,
    UpdatedAt
)
SELECT
    cc.CreditCardID,
    20,
    10,
    CONVERT(DATE, SYSDATETIME()),
    SYSDATETIME()
FROM dbo.CreditCards AS cc
WHERE NOT EXISTS
(
    SELECT 1
    FROM dbo.CreditCardBillingSettings AS bs
    WHERE bs.CreditCardID = cc.CreditCardID
);
GO

-- ============================================================
-- 15. ACCOUNT DAILY BALANCES TRIGGER
--
-- When an account is created or its balance changes,
-- today's recorded balance is updated automatically.
-- ============================================================

CREATE OR ALTER TRIGGER dbo.trg_Accounts_DailyBalances
ON dbo.Accounts
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF NOT UPDATE(Balance)
        RETURN;

    DECLARE @Today DATE = CONVERT(DATE, SYSDATETIME());

    -- Update existing daily balance records.

    UPDATE adb
    SET
        adb.ClosingBalance = i.Balance,
        adb.RecordedAt = SYSDATETIME()
    FROM dbo.AccountDailyBalances AS adb
    INNER JOIN inserted AS i
        ON i.AccountID = adb.AccountID
    WHERE adb.BalanceDate = @Today
      AND
      (
          adb.ClosingBalance <> i.Balance
      );

    -- Insert today's record for accounts without one.

    INSERT INTO dbo.AccountDailyBalances
    (
        AccountID,
        BalanceDate,
        ClosingBalance,
        RecordedAt
    )
    SELECT
        i.AccountID,
        @Today,
        i.Balance,
        SYSDATETIME()
    FROM inserted AS i
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.AccountDailyBalances AS adb
            WITH (UPDLOCK, HOLDLOCK)
        WHERE adb.AccountID = i.AccountID
          AND adb.BalanceDate = @Today
    );
END;
GO

-- ============================================================
-- 16. FRAUD RISK ASSESSMENTS TRIGGER
--
-- Automatically creates or updates one assessment
-- for every fraud alert.
-- ============================================================

CREATE OR ALTER TRIGGER dbo.trg_FraudAlerts_RiskAssessments
ON dbo.FraudAlerts
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Update assessments for changed alerts.

    UPDATE fra
    SET
        fra.RiskLevel = i.RiskLevel,
        fra.ReviewStatus = i.ReviewStatus,
        fra.AssessedAt = SYSDATETIME()
    FROM dbo.FraudRiskAssessments AS fra
    INNER JOIN inserted AS i
        ON i.AlertID = fra.AlertID
    WHERE fra.RiskLevel <> i.RiskLevel
       OR fra.ReviewStatus <> i.ReviewStatus;

    -- Create assessments for new alerts.

    INSERT INTO dbo.FraudRiskAssessments
    (
        AlertID,
        RiskLevel,
        ReviewStatus,
        AssessedAt
    )
    SELECT
        i.AlertID,
        i.RiskLevel,
        i.ReviewStatus,
        SYSDATETIME()
    FROM inserted AS i
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.FraudRiskAssessments AS fra
            WITH (UPDLOCK, HOLDLOCK)
        WHERE fra.AlertID = i.AlertID
    );
END;
GO

-- ============================================================
-- 17. BACKFILL DAILY BALANCES
--
-- Existing account balances are recorded for today.
-- ============================================================

DECLARE @Today DATE = CONVERT(DATE, SYSDATETIME());

UPDATE adb
SET
    adb.ClosingBalance = a.Balance,
    adb.RecordedAt = SYSDATETIME()
FROM dbo.AccountDailyBalances AS adb
INNER JOIN dbo.Accounts AS a
    ON a.AccountID = adb.AccountID
WHERE adb.BalanceDate = @Today
  AND adb.ClosingBalance <> a.Balance;

INSERT INTO dbo.AccountDailyBalances
(
    AccountID,
    BalanceDate,
    ClosingBalance
)
SELECT
    a.AccountID,
    @Today,
    a.Balance
FROM dbo.Accounts AS a
WHERE NOT EXISTS
(
    SELECT 1
    FROM dbo.AccountDailyBalances AS adb
    WHERE adb.AccountID = a.AccountID
      AND adb.BalanceDate = @Today
);
GO

-- ============================================================
-- 18. BACKFILL FRAUD RISK ASSESSMENTS
-- ============================================================

UPDATE fra
SET
    fra.RiskLevel = fa.RiskLevel,
    fra.ReviewStatus = fa.ReviewStatus,
    fra.AssessedAt = SYSDATETIME()
FROM dbo.FraudRiskAssessments AS fra
INNER JOIN dbo.FraudAlerts AS fa
    ON fa.AlertID = fra.AlertID
WHERE fra.RiskLevel <> fa.RiskLevel
   OR fra.ReviewStatus <> fa.ReviewStatus;

INSERT INTO dbo.FraudRiskAssessments
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
WHERE NOT EXISTS
(
    SELECT 1
    FROM dbo.FraudRiskAssessments AS fra
    WHERE fra.AlertID = fa.AlertID
);
GO

-- ============================================================
-- 19. REMOVE OLD STATEMENT PROCEDURE AND TRIGGER
--
-- These objects belong to the two removed tables.
-- ============================================================

IF OBJECT_ID(
    N'dbo.sp_GenerateCreditCardStatement',
    N'P'
) IS NOT NULL
BEGIN
    DROP PROCEDURE dbo.sp_GenerateCreditCardStatement;
END;
GO

IF OBJECT_ID(
    N'dbo.trg_StatementItems_ValidateCard',
    N'TR'
) IS NOT NULL
BEGIN
    DROP TRIGGER dbo.trg_StatementItems_ValidateCard;
END;
GO

-- ============================================================
-- 20. VERIFY APPLICATION PROCEDURES
-- ============================================================

SELECT
    name AS ProcedureName,
    create_date AS CreatedAt,
    modify_date AS ModifiedAt
FROM sys.procedures
WHERE schema_id = SCHEMA_ID(N'dbo')
  AND name IN
  (
      N'sp_ExecuteBankTransaction',
      N'sp_Deposit',
      N'sp_Withdraw',
      N'sp_Transfer',
      N'sp_ExecuteCreditCardTransaction',
      N'sp_CreditCardPurchase',
      N'sp_CreditCardCashAdvance',
      N'sp_CreditCardPayment',
      N'sp_ScanFraud',
      N'sp_ScanCreditCardFraud'
  )
ORDER BY name;
GO

-- ============================================================
-- 21. VERIFY TRIGGERS
-- ============================================================

SELECT
    t.name AS TriggerName,
    OBJECT_NAME(t.parent_id) AS TableName,
    t.is_disabled AS IsDisabled
FROM sys.triggers AS t
WHERE t.parent_class = 1
  AND t.name IN
  (
      N'trg_Accounts_StatusHistory',
      N'trg_FraudAlerts_ReviewHistory',
      N'trg_CreditCards_BillingSettings',
      N'trg_Accounts_DailyBalances',
      N'trg_FraudAlerts_RiskAssessments'
  )
ORDER BY t.name;
GO

-- ============================================================
-- 22. VERIFY DAILY BALANCE RECORDS
-- ============================================================

SELECT
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
-- 23. VERIFY FRAUD RISK ASSESSMENTS
-- ============================================================

SELECT
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
-- 24. VERIFY EXACTLY 20 TABLES
-- ============================================================

DECLARE @TableCount INT;

SELECT @TableCount = COUNT(*)
FROM sys.tables
WHERE schema_id = SCHEMA_ID(N'dbo')
  AND is_ms_shipped = 0;

SELECT @TableCount AS TotalTables;

IF @TableCount = 20
BEGIN
    PRINT 'NG BANK: Exactly 20 tables confirmed.';
END
ELSE
BEGIN
    PRINT 'NG BANK WARNING: Expected 20 tables, found '
          + CAST(@TableCount AS VARCHAR(10)) + '.';
END;
GO

-- ============================================================
-- 25. FINAL SUMMARY
-- ============================================================

SELECT
    (SELECT COUNT(*)
     FROM sys.tables
     WHERE schema_id = SCHEMA_ID(N'dbo')
       AND is_ms_shipped = 0) AS TotalTables,

    (SELECT COUNT(*)
     FROM sys.views
     WHERE schema_id = SCHEMA_ID(N'dbo')) AS TotalViews,

    (SELECT COUNT(*)
     FROM dbo.AccountDailyBalances) AS DailyBalanceRecords,

    (SELECT COUNT(*)
     FROM dbo.FraudRiskAssessments) AS FraudRiskRecords;
GO

PRINT '05_procedures.sql completed successfully.';
GO
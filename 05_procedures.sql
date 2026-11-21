
-- ============================================================
-- NG BANK - 05_procedures.sql
-- PART 1/5: BANK TRANSACTION ENGINE
--
-- Creates the sp_ExecuteBankTransaction procedure.
-- Target database: BankingFraudDB
-- ============================================================

USE [BankingFraudDB];
GO
SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

-- sp_ExecuteBankTransaction
CREATE OR ALTER PROCEDURE [dbo].[sp_ExecuteBankTransaction]
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
        @DestinationAccountID INT = NULL,
        @SourceCustomerID INT,
        @SourceBalance DECIMAL(18,2),
        @SourceCurrency CHAR(3),
        @SourceActive BIT,
        @SourceFrozen BIT,
        @DestinationBalance DECIMAL(18,2),
        @DestinationCurrency CHAR(3),
        @DestinationActive BIT,
        @DestinationFrozen BIT,
        @FromID INT = NULL,
        @ToID INT = NULL,
        @TransactionID BIGINT,
        @FirstID INT,
        @SecondID INT,
        @LockedAccountID INT;

    DECLARE @Created TABLE
    (
        TransactionID BIGINT NOT NULL
    );

    -- ================================================
    -- VALIDATE INPUTS
    -- ================================================

    IF @Kind IS NULL
       OR @Kind NOT IN ('Deposit', 'Withdrawal', 'Transfer')
        THROW 51001, 'Invalid transaction type.', 1;

    IF @UserID IS NULL
       OR @UserID <= 0
       OR @SourceAccountID IS NULL
       OR @SourceAccountID <= 0
        THROW 51002, 'Invalid user or account.', 1;

    IF @Amount IS NULL OR @Amount <= 0
        THROW 51003, 'Amount must be greater than zero.', 1;

    IF @Kind = 'Transfer'
       AND
       (
           @DestinationAccountNumber IS NULL
           OR LEN(RTRIM(@DestinationAccountNumber)) <> 18
           OR LEFT(@DestinationAccountNumber, 2) <> 'TR'
           OR SUBSTRING(
               @DestinationAccountNumber, 3, 16
           ) LIKE '%[^0-9]%'
       )
        THROW 51005, 'Invalid recipient account number.', 1;

    BEGIN TRY

        BEGIN TRANSACTION;

        -- ============================================
        -- AUTHORIZE USER
        -- ============================================

        SELECT
            @Role = u.Role,
            @CustomerID = u.CustomerID
        FROM dbo.Users AS u WITH (UPDLOCK, HOLDLOCK)
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

        -- Customers are allowed to deposit into
        -- their own accounts.
        -- No Admin-only Deposit restriction.

        -- ============================================
        -- FIND TRANSFER DESTINATION
        -- ============================================

        IF @Kind = 'Transfer'
        BEGIN

            SELECT
                @DestinationAccountID = AccountID
            FROM dbo.Accounts
            WHERE AccountNumber = @DestinationAccountNumber;

            IF @DestinationAccountID IS NULL
                THROW 51008, 'Recipient account not found.', 1;

            IF @DestinationAccountID = @SourceAccountID
                THROW 51009, 'Source and destination must differ.', 1;

        END;

        -- ============================================
        -- LOCK ACCOUNTS IN FIXED ORDER
        -- ============================================

        SET @FirstID =
            CASE
                WHEN @DestinationAccountID IS NOT NULL
                     AND @DestinationAccountID < @SourceAccountID
                THEN @DestinationAccountID
                ELSE @SourceAccountID
            END;

        SET @SecondID =
            CASE
                WHEN @DestinationAccountID IS NULL
                THEN NULL

                WHEN @DestinationAccountID > @SourceAccountID
                THEN @DestinationAccountID

                ELSE @SourceAccountID
            END;

        SELECT
            @LockedAccountID = AccountID
        FROM dbo.Accounts WITH (UPDLOCK, HOLDLOCK)
        WHERE AccountID = @FirstID;

        IF @LockedAccountID IS NULL
            THROW 51010, 'Account not found.', 1;

        IF @SecondID IS NOT NULL
        BEGIN

            SET @LockedAccountID = NULL;

            SELECT
                @LockedAccountID = AccountID
            FROM dbo.Accounts WITH (UPDLOCK, HOLDLOCK)
            WHERE AccountID = @SecondID;

            IF @LockedAccountID IS NULL
                THROW 51010, 'Account not found.', 1;

        END;

        -- ============================================
        -- CHECK SOURCE ACCOUNT
        -- ============================================

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
            THROW 51012, 'You can only use your own account.', 1;

        -- ============================================
        -- CHECK DESTINATION ACCOUNT
        -- ============================================

        IF @Kind = 'Transfer'
        BEGIN

            SELECT
                @DestinationBalance = Balance,
                @DestinationCurrency = Currency,
                @DestinationActive = IsActive,
                @DestinationFrozen = IsFrozen
            FROM dbo.Accounts
            WHERE AccountID = @DestinationAccountID
              AND AccountNumber = @DestinationAccountNumber;

            IF @DestinationActive IS NULL
               OR @DestinationActive <> 1
                THROW 51013, 'Recipient account is unavailable.', 1;

            IF @DestinationFrozen = 1
                THROW 51018, 'Recipient account is frozen.', 1;

            IF @SourceCurrency <> @DestinationCurrency
                THROW 51014, 'Different currencies are not supported.', 1;

        END;

        -- ============================================
        -- CHECK AVAILABLE BALANCE
        -- ============================================

        IF @Kind IN ('Withdrawal', 'Transfer')
           AND @SourceBalance < @Amount
            THROW 51015, 'Insufficient balance.', 1;

        -- Prevent DECIMAL(18,2) balance overflow.
        IF @Kind = 'Deposit'
           AND @SourceBalance >
               9999999999999999.99 - @Amount
            THROW 51016, 'Account balance limit exceeded.', 1;

        IF @Kind = 'Transfer'
           AND @DestinationBalance >
               9999999999999999.99 - @Amount
            THROW 51016, 'Recipient balance limit exceeded.', 1;

        -- ============================================
        -- EXECUTE DEPOSIT
        -- ============================================

        IF @Kind = 'Deposit'
        BEGIN

            UPDATE dbo.Accounts
            SET Balance = Balance + @Amount
            WHERE AccountID = @SourceAccountID;

            SET @ToID = @SourceAccountID;

        END

        -- ============================================
        -- EXECUTE WITHDRAWAL
        -- ============================================

        ELSE IF @Kind = 'Withdrawal'
        BEGIN

            UPDATE dbo.Accounts
            SET Balance = Balance - @Amount
            WHERE AccountID = @SourceAccountID;

            SET @FromID = @SourceAccountID;

        END

        -- ============================================
        -- EXECUTE TRANSFER
        -- ============================================

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

        -- ============================================
        -- INSERT TRANSACTION RECORD
        -- ============================================

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
            COALESCE(@Description, N'')
        );

        SELECT
            @TransactionID = TransactionID
        FROM @Created;

        -- ============================================
        -- INSERT AUDIT LOG
        -- ============================================

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
            CONCAT(
                @Kind,
                ': ',
                CONVERT(VARCHAR(40), @Amount)
            ),
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
-- NG BANK - 05_procedures.sql
-- PART 2/5: BANK TRANSACTION WRAPPERS
--
-- Run after sp_ExecuteBankTransaction is created.
-- Target database: BankingFraudDB
-- ============================================================

USE [BankingFraudDB];
GO

-- ============================================================
-- 1. DEPOSIT
-- ============================================================

CREATE OR ALTER PROCEDURE [dbo].[sp_Deposit]
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
-- 2. WITHDRAW
-- ============================================================

CREATE OR ALTER PROCEDURE [dbo].[sp_Withdraw]
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
-- 3. TRANSFER
-- ============================================================

CREATE OR ALTER PROCEDURE [dbo].[sp_Transfer]
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
-- NG BANK - 05_procedures.sql
-- PART 3/5: CREDIT CARD TRANSACTION ENGINE
-- TARGET: BankingFraudDB
-- ============================================================

USE [BankingFraudDB];
GO

CREATE OR ALTER PROCEDURE [dbo].[sp_ExecuteCreditCardTransaction]
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
        @AvailableLimit DECIMAL(18,2),
        @ExpiresAt DATE,
        @AccountBalance DECIMAL(18,2),
        @AccountActive BIT,
        @AccountFrozen BIT,
        @AccountCurrency CHAR(3),
        @BankTransactionID BIGINT = NULL,
        @CardTransactionID BIGINT,
        @BankDescription NVARCHAR(250);

    DECLARE @CreatedCardTransaction TABLE
    (
        CardTransactionID BIGINT
    );

    DECLARE @CreatedBankTransaction TABLE
    (
        TransactionID BIGINT
    );

    -- ========================================================
    -- VALIDATE INPUTS
    -- ========================================================

    IF @Kind IS NULL
       OR @Kind NOT IN ('Purchase', 'CashAdvance', 'Payment')
        THROW 51101, 'Invalid credit card transaction type.', 1;

    IF @UserID IS NULL OR @UserID <= 0
        THROW 51102, 'Invalid user ID.', 1;

    IF @CreditCardID IS NULL OR @CreditCardID <= 0
        THROW 51103, 'Invalid credit card ID.', 1;

    IF @Amount IS NULL OR @Amount <= 0
        THROW 51104, 'Amount must be greater than zero.', 1;

    SET @Description = COALESCE(@Description, N'');

    BEGIN TRY
        BEGIN TRANSACTION;

        -- ====================================================
        -- AUTHORIZE CUSTOMER
        -- ====================================================

        SELECT
            @CustomerID = u.CustomerID
        FROM dbo.Users AS u WITH (UPDLOCK, HOLDLOCK)
        INNER JOIN dbo.Customers AS c
            ON c.CustomerID = u.CustomerID
        WHERE u.UserID = @UserID
          AND u.Role = 'Customer'
          AND u.IsActive = 1
          AND c.IsActive = 1;

        IF @CustomerID IS NULL
            THROW 51105, 'Active customer access required.', 1;

        -- ====================================================
        -- IDENTIFY LINKED BANK ACCOUNT
        -- ====================================================

        SELECT
            @LinkedAccountID = LinkedAccountID
        FROM dbo.CreditCards
        WHERE CreditCardID = @CreditCardID
          AND CustomerID = @CustomerID;

        IF @LinkedAccountID IS NULL
            THROW 51106, 'Credit card not found.', 1;

        -- ====================================================
        -- LOCK AND VALIDATE LINKED BANK ACCOUNT
        -- ====================================================

        SELECT
            @AccountBalance = Balance,
            @AccountActive = IsActive,
            @AccountFrozen = IsFrozen,
            @AccountCurrency = Currency
        FROM dbo.Accounts WITH (UPDLOCK, HOLDLOCK)
        WHERE AccountID = @LinkedAccountID
          AND CustomerID = @CustomerID;

        IF @AccountActive IS NULL OR @AccountActive <> 1
            THROW 51107, 'Linked bank account is unavailable.', 1;

        IF @AccountFrozen = 1
            THROW 51108, 'Linked bank account is frozen.', 1;

        IF @AccountCurrency IS NULL OR @AccountCurrency <> 'TRY'
            THROW 51109, 'Only TRY accounts are supported.', 1;

        -- ====================================================
        -- LOCK AND VALIDATE CREDIT CARD
        -- ====================================================

        SELECT
            @CardCustomerID = CustomerID,
            @CardStatus = CardStatus,
            @CardCurrency = Currency,
            @CreditLimit = CreditLimit,
            @OutstandingBalance = OutstandingBalance,
            @ExpiresAt = ExpiresAt
        FROM dbo.CreditCards WITH (UPDLOCK, HOLDLOCK)
        WHERE CreditCardID = @CreditCardID
          AND CustomerID = @CustomerID
          AND LinkedAccountID = @LinkedAccountID;

        IF @CardCustomerID IS NULL
            THROW 51110, 'Credit card is unavailable.', 1;

        IF @CardCurrency <> 'TRY'
            THROW 51111, 'Only TRY credit cards are supported.', 1;

        -- Spending requires an active, unexpired card.
        -- Payments remain available for frozen, expired
        -- or closed cards when the linked account is usable.

        IF @Kind IN ('Purchase', 'CashAdvance')
        BEGIN
            IF @CardStatus <> 'Active'
                THROW 51112, 'This credit card is not active.', 1;

            IF @ExpiresAt < CAST(SYSDATETIME() AS DATE)
                THROW 51113, 'This credit card has expired.', 1;
        END;

        -- ====================================================
        -- CREDIT LIMIT AND BALANCE VALIDATION
        -- ====================================================

        SET @AvailableLimit = @CreditLimit - @OutstandingBalance;

        IF @Kind IN ('Purchase', 'CashAdvance')
           AND @Amount > @AvailableLimit
            THROW 51114, 'Insufficient available credit limit.', 1;

        IF @Kind = 'CashAdvance'
           AND @AccountBalance > 9999999999999999.99 - @Amount
            THROW 51115, 'Bank account balance limit exceeded.', 1;

        IF @Kind = 'Payment'
        BEGIN
            IF @OutstandingBalance <= 0
                THROW 51116, 'There is no outstanding credit card debt.', 1;

            IF @Amount > @OutstandingBalance
                THROW 51117, 'Payment cannot exceed outstanding debt.', 1;

            IF @Amount > @AccountBalance
                THROW 51118, 'Insufficient bank account balance.', 1;
        END;

        -- ====================================================
        -- PURCHASE
        -- ====================================================

        IF @Kind = 'Purchase'
        BEGIN
            UPDATE dbo.CreditCards
            SET OutstandingBalance = OutstandingBalance + @Amount
            WHERE CreditCardID = @CreditCardID;

            IF @@ROWCOUNT <> 1
                THROW 51119, 'Credit card update failed.', 1;
        END

        -- ====================================================
        -- CASH ADVANCE
        -- ====================================================

        ELSE IF @Kind = 'CashAdvance'
        BEGIN
            UPDATE dbo.CreditCards
            SET OutstandingBalance = OutstandingBalance + @Amount
            WHERE CreditCardID = @CreditCardID;

            IF @@ROWCOUNT <> 1
                THROW 51119, 'Credit card update failed.', 1;

            UPDATE dbo.Accounts
            SET Balance = Balance + @Amount
            WHERE AccountID = @LinkedAccountID;

            IF @@ROWCOUNT <> 1
                THROW 51120, 'Bank account update failed.', 1;

            SET @BankDescription = LEFT(
                CONCAT(
                    'Credit card cash advance. CardID=',
                    @CreditCardID,
                    '. ',
                    @Description
                ),
                250
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
                INTO @CreatedBankTransaction(TransactionID)
            VALUES
            (
                NULL,
                @LinkedAccountID,
                'Deposit',
                @Amount,
                @BankDescription
            );
        END

        -- ====================================================
        -- CREDIT CARD PAYMENT
        -- ====================================================

        ELSE IF @Kind = 'Payment'
        BEGIN
            UPDATE dbo.Accounts
            SET Balance = Balance - @Amount
            WHERE AccountID = @LinkedAccountID;

            IF @@ROWCOUNT <> 1
                THROW 51120, 'Bank account update failed.', 1;

            UPDATE dbo.CreditCards
            SET OutstandingBalance = OutstandingBalance - @Amount
            WHERE CreditCardID = @CreditCardID;

            IF @@ROWCOUNT <> 1
                THROW 51119, 'Credit card update failed.', 1;

            SET @BankDescription = LEFT(
                CONCAT(
                    'Credit card debt payment. CardID=',
                    @CreditCardID,
                    '. ',
                    @Description
                ),
                250
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
                INTO @CreatedBankTransaction(TransactionID)
            VALUES
            (
                @LinkedAccountID,
                NULL,
                'Withdrawal',
                @Amount,
                @BankDescription
            );
        END;

        -- ====================================================
        -- GET BANK TRANSACTION ID
        -- ====================================================

        SELECT @BankTransactionID = TransactionID
        FROM @CreatedBankTransaction;

        -- ====================================================
        -- INSERT CREDIT CARD TRANSACTION
        -- ====================================================

        INSERT INTO dbo.CreditCardTransactions
        (
            CreditCardID,
            TransactionType,
            Amount,
            Description,
            TransactionStatus,
            BankTransactionID
        )
        OUTPUT INSERTED.CardTransactionID
            INTO @CreatedCardTransaction(CardTransactionID)
        VALUES
        (
            @CreditCardID,
            @Kind,
            @Amount,
            CASE
                WHEN LEN(@Description) > 0
                    THEN @Description
                WHEN @Kind = 'Purchase'
                    THEN N'Credit card purchase'
                WHEN @Kind = 'CashAdvance'
                    THEN N'Credit card cash advance'
                ELSE N'Credit card debt payment'
            END,
            'Completed',
            @BankTransactionID
        );

        SELECT @CardTransactionID = CardTransactionID
        FROM @CreatedCardTransaction;

        -- ====================================================
        -- BANK TRANSACTION AUDIT LOG
        -- ====================================================

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

        -- ====================================================
        -- CREDIT CARD AUDIT LOG
        -- ====================================================

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
                'CardID=',
                @CreditCardID,
                ', Type=',
                @Kind,
                ', Amount=',
                CONVERT(VARCHAR(40), @Amount),
                ' TRY'
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
-- NG BANK
-- FILE: 05_procedures.sql
-- PART 4/5: CREDIT CARD TRANSACTION WRAPPERS
--
-- Run after sp_ExecuteCreditCardTransaction.
-- Target database: BankingFraudDB
-- ============================================================

USE [BankingFraudDB];
GO

-- ============================================================
-- 1. CREDIT CARD PURCHASE
-- ============================================================

CREATE OR ALTER PROCEDURE
    [dbo].[sp_CreditCardPurchase]

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
-- 2. CREDIT CARD CASH ADVANCE
-- ============================================================

CREATE OR ALTER PROCEDURE
    [dbo].[sp_CreditCardCashAdvance]

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
-- 3. CREDIT CARD PAYMENT
-- ============================================================

CREATE OR ALTER PROCEDURE
    [dbo].[sp_CreditCardPayment]

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
-- NG BANK - 05_procedures.sql
-- PART 5/5: FRAUD DETECTION PROCEDURES
--
-- Creates sp_ScanFraud and sp_ScanCreditCardFraud.
-- Target database: BankingFraudDB
-- ============================================================

USE [BankingFraudDB];
GO

CREATE OR ALTER PROCEDURE [dbo].[sp_ScanFraud]
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @NewAlerts INT = 0;
    DECLARE @LockResult INT;

    DECLARE @CreatedAlerts TABLE
    (
        AlertID BIGINT,
        TransactionID BIGINT,
        RuleID INT,
        RiskLevel VARCHAR(10)
    );

    -- VALIDATE USER

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

        -- PREVENT CONCURRENT FRAUD SCANS

        EXEC @LockResult = sys.sp_getapplock
            @Resource = 'BankingFraudDB_FraudScan',
            @LockMode = 'Exclusive',
            @LockOwner = 'Transaction',
            @LockTimeout = 10000;

        IF @LockResult < 0
            THROW 51032,
                  'Could not acquire fraud scan lock.',
                  1;

        -- FIND TRANSACTIONS MATCHING ACTIVE RULES

        ;WITH TransactionCandidates AS
        (
            SELECT
                t.TransactionID,
                t.FromAccountID,
                t.ToAccountID,
                t.Amount,
                t.TransactionDate,
                COALESCE(
                    t.FromAccountID,
                    t.ToAccountID
                ) AS EvaluatedAccountID
            FROM dbo.Transactions AS t
            WHERE t.Status = 'Completed'
        ),

        RuleMatches AS
        (
            SELECT
                t.TransactionID,
                r.RuleID,
                r.RuleName,
                r.RuleType,
                r.ThresholdValue,
                r.TimeWindowMinutes,
                t.Amount,
                counts.MatchCount,

                CASE
                    WHEN r.RuleType = 'HighAmount'
                         AND t.Amount >= r.ThresholdValue
                    THEN 1

                    WHEN r.RuleType IN
                         ('Frequent', 'RepeatedAmount')
                         AND t.EvaluatedAccountID IS NOT NULL
                         AND r.TimeWindowMinutes > 0
                         AND counts.MatchCount >= r.ThresholdValue
                    THEN 1

                    ELSE 0
                END AS IsSuspicious

            FROM TransactionCandidates AS t
            CROSS JOIN dbo.FraudRules AS r

            OUTER APPLY
            (
                SELECT COUNT_BIG(*) AS MatchCount
                FROM dbo.Transactions AS p

                WHERE r.RuleType IN
                      ('Frequent', 'RepeatedAmount')

                  AND r.TimeWindowMinutes > 0
                  AND t.EvaluatedAccountID IS NOT NULL
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
                      p.FromAccountID = t.EvaluatedAccountID
                      OR p.ToAccountID = t.EvaluatedAccountID
                  )

                  AND
                  (
                      r.RuleType = 'Frequent'
                      OR
                      (
                          r.RuleType = 'RepeatedAmount'
                          AND p.Amount = t.Amount
                      )
                  )
            ) AS counts

            WHERE r.IsActive = 1
              AND r.RuleType IN
              (
                  'HighAmount',
                  'Frequent',
                  'RepeatedAmount'
              )
        ),

        SuspiciousTransactions AS
        (
            SELECT
                m.TransactionID,
                m.RuleID,

                CASE
                    WHEN m.RuleType = 'HighAmount'
                    THEN 'High'

                    WHEN m.MatchCount >= m.ThresholdValue + 3
                    THEN 'High'

                    ELSE 'Medium'
                END AS RiskLevel,

                CAST
                (
                    CASE
                        WHEN m.RuleType = 'HighAmount'
                        THEN CONCAT(
                            'Amount ',
                            CONVERT(VARCHAR(40), m.Amount),
                            ' reached threshold ',
                            CONVERT(VARCHAR(40), m.ThresholdValue),
                            '.'
                        )

                        ELSE CONCAT(
                            m.MatchCount,
                            ' matching transactions in ',
                            m.TimeWindowMinutes,
                            ' minutes.'
                        )
                    END
                    AS NVARCHAR(500)
                ) AS AlertDescription

            FROM RuleMatches AS m
            WHERE m.IsSuspicious = 1
        )

        -- INSERT NEW FRAUD ALERTS

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

        INTO @CreatedAlerts
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

        FROM SuspiciousTransactions AS s

        WHERE NOT EXISTS
        (
            SELECT 1
            FROM dbo.FraudAlerts AS fa
                WITH (UPDLOCK, HOLDLOCK)
            WHERE fa.TransactionID = s.TransactionID
              AND fa.RuleID = s.RuleID
        );

        -- COUNT NEW ALERTS

        SELECT @NewAlerts = COUNT(*)
        FROM @CreatedAlerts;

        -- AUDIT EACH NEW FRAUD ALERT

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
            ca.AlertID,

            CONCAT(
                'Alert created for TransactionID ',
                ca.TransactionID,
                ', Rule: ',
                r.RuleName,
                ', Risk: ',
                ca.RiskLevel
            ),

            @UserID

        FROM @CreatedAlerts AS ca
        INNER JOIN dbo.FraudRules AS r
            ON r.RuleID = ca.RuleID;

        -- AUDIT THE FRAUD SCAN

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
            CONCAT(@NewAlerts, ' new alerts created'),
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


USE [BankingFraudDB];
GO

CREATE OR ALTER PROCEDURE [dbo].[sp_ScanCreditCardFraud]
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    SET ANSI_PADDING ON;
    SET ANSI_WARNINGS ON;
    SET CONCAT_NULL_YIELDS_NULL ON;
    SET ARITHABORT ON;
    SET NUMERIC_ROUNDABORT OFF;

    DECLARE @NewAlerts INT = 0;
    DECLARE @LockResult INT;

    DECLARE @CreatedAlerts TABLE
    (
        AlertID BIGINT,
        CardTransactionID BIGINT,
        RuleID INT,
        RiskLevel VARCHAR(10)
    );

    -- VALIDATE ADMIN USER

    IF @UserID IS NULL OR @UserID <= 0
    BEGIN
        RAISERROR('Invalid UserID.', 16, 1);
        RETURN;
    END;

    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.Users
        WHERE UserID = @UserID
          AND Role = 'Admin'
          AND IsActive = 1
    )
    BEGIN
        RAISERROR('Admin access required.', 16, 1);
        RETURN;
    END;

    BEGIN TRY
    BEGIN TRANSACTION;

    -- PREVENT CONCURRENT FRAUD SCANS

    EXEC @LockResult = sys.sp_getapplock
        @Resource = 'BankingFraudDB_CreditCardFraudScan',
        @LockMode = 'Exclusive',
        @LockOwner = 'Transaction',
        @LockTimeout = 10000;

    IF @LockResult < 0
    BEGIN
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        RAISERROR(
            'Could not acquire fraud scan lock.',
            16,
            1
        );

        RETURN;
    END;

    -- FIND COMPLETED CREDIT CARD PURCHASES

    ;WITH CardCandidates AS
    (
        SELECT
            CardTransactionID,
            CreditCardID,
            Amount,
            CreatedAt
        FROM dbo.CreditCardTransactions
        WHERE TransactionStatus = 'Completed'
          AND TransactionType = 'Purchase'
          AND BankTransactionID IS NULL
    ),

    -- MATCH ACTIVE FRAUD RULES

    RuleMatches AS
    (
        SELECT
            t.CardTransactionID,
            r.RuleID,
            r.RuleName,
            r.RuleType,
            r.ThresholdValue,
            r.TimeWindowMinutes,
            t.Amount,
            counts.MatchCount,

            CASE
                WHEN r.RuleType = 'HighAmount'
                     AND t.Amount >= r.ThresholdValue
                THEN 1

                WHEN r.RuleType IN
                (
                    'Frequent',
                    'RepeatedAmount'
                )
                AND r.TimeWindowMinutes > 0
                AND counts.MatchCount >= r.ThresholdValue
                THEN 1

                ELSE 0
            END AS IsSuspicious

        FROM CardCandidates AS t
        CROSS JOIN dbo.FraudRules AS r

        OUTER APPLY
        (
            SELECT COUNT_BIG(*) AS MatchCount
            FROM CardCandidates AS p

            WHERE r.RuleType IN
            (
                'Frequent',
                'RepeatedAmount'
            )

              AND r.TimeWindowMinutes > 0
              AND p.CreditCardID = t.CreditCardID

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
                  OR
                  (
                      r.RuleType = 'RepeatedAmount'
                      AND p.Amount = t.Amount
                  )
              )
        ) AS counts

        WHERE r.IsActive = 1
          AND r.RuleType IN
          (
              'HighAmount',
              'Frequent',
              'RepeatedAmount'
          )
    ),

    -- DETERMINE RISK LEVEL

    SuspiciousTransactions AS
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

            CAST
            (
                CASE
                    WHEN RuleType = 'HighAmount'
                    THEN CONCAT(
                        'Credit card purchase amount ',
                        Amount,
                        ' reached threshold ',
                        ThresholdValue,
                        '.'
                    )

                    ELSE CONCAT(
                        MatchCount,
                        ' matching credit card purchases in ',
                        TimeWindowMinutes,
                        ' minutes.'
                    )
                END
                AS NVARCHAR(500)
            ) AS AlertDescription

        FROM RuleMatches
        WHERE IsSuspicious = 1
    )

    -- INSERT FRAUD ALERTS

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

    INTO @CreatedAlerts
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

    FROM SuspiciousTransactions AS s

    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.FraudAlerts AS fa
            WITH (UPDLOCK, HOLDLOCK)

        WHERE fa.CardTransactionID = s.CardTransactionID
          AND fa.RuleID = s.RuleID
    );

    -- COUNT NEW FRAUD ALERTS

    SELECT @NewAlerts = COUNT(*)
    FROM @CreatedAlerts;

    -- AUDIT NEW FRAUD ALERTS

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
        ca.AlertID,

        CONCAT(
            'Credit card fraud alert. ',
            'CardTransactionID=',
            ca.CardTransactionID,
            ', Rule=',
            r.RuleName,
            ', Risk=',
            ca.RiskLevel
        ),

        @UserID

    FROM @CreatedAlerts AS ca
    INNER JOIN dbo.FraudRules AS r
        ON r.RuleID = ca.RuleID;

    -- AUDIT FRAUD SCAN

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
        CONCAT(
            @NewAlerts,
            ' new credit card fraud alerts created.'
        ),
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



USE BankingFraudDB;
GO

SELECT
    name AS ProcedureName
FROM sys.procedures
WHERE schema_id = SCHEMA_ID('dbo')
ORDER BY name;
GO
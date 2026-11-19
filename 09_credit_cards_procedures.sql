
USE BankingFraudDB;
GO

-- ============================================================
-- BANKING MANAGEMENT & FRAUD DETECTION SYSTEM
-- FILE: 09_credit_card_procedures.sql
-- PURPOSE: Credit card transaction procedures
--
-- RUN AFTER:
--   05_transaction_procedures.sql
--   08_credit_card_schema.sql
--
-- IMPORTANT:
--   Existing records are preserved.
--   No transaction is executed by this setup script.
-- ============================================================


-- ============================================================
-- 1. LINK CREDIT CARD AND BANK TRANSACTIONS
-- ============================================================

IF COL_LENGTH(
    'dbo.CreditCardTransactions',
    'BankTransactionID'
) IS NULL
BEGIN

    ALTER TABLE dbo.CreditCardTransactions
    ADD BankTransactionID BIGINT NULL
        CONSTRAINT FK_CreditCardTransactions_BankTransaction
        REFERENCES dbo.Transactions(TransactionID);

END;
GO


IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = 'UX_CreditCardTransactions_BankTransaction'
      AND object_id =
          OBJECT_ID('dbo.CreditCardTransactions')
)
BEGIN

    CREATE UNIQUE INDEX
        UX_CreditCardTransactions_BankTransaction
    ON dbo.CreditCardTransactions
    (
        BankTransactionID
    )
    WHERE BankTransactionID IS NOT NULL;

END;
GO


-- ============================================================
-- 2. MAIN CREDIT CARD TRANSACTION PROCEDURE
-- ============================================================

CREATE OR ALTER PROCEDURE
    dbo.sp_ExecuteCreditCardTransaction

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
       OR @Kind NOT IN
       (
           'Purchase',
           'CashAdvance',
           'Payment'
       )
        THROW 51101,
              'Invalid credit card transaction type.',
              1;

    IF @UserID IS NULL OR @UserID <= 0
        THROW 51102,
              'Invalid user ID.',
              1;

    IF @CreditCardID IS NULL
       OR @CreditCardID <= 0
        THROW 51103,
              'Invalid credit card ID.',
              1;

    IF @Amount IS NULL OR @Amount <= 0
        THROW 51104,
              'Amount must be greater than zero.',
              1;

    SET @Description =
        COALESCE(@Description, N'');


    BEGIN TRY

        BEGIN TRANSACTION;


        -- ====================================================
        -- AUTHORIZE CUSTOMER
        -- ====================================================

        SELECT
            @CustomerID = u.CustomerID

        FROM dbo.Users AS u
            WITH (UPDLOCK, HOLDLOCK)

        INNER JOIN dbo.Customers AS c
            ON c.CustomerID = u.CustomerID

        WHERE u.UserID = @UserID
          AND u.Role = 'Customer'
          AND u.IsActive = 1
          AND c.IsActive = 1;

        IF @CustomerID IS NULL
            THROW 51105,
                  'Active customer access required.',
                  1;


        -- ====================================================
        -- IDENTIFY LINKED BANK ACCOUNT
        -- ====================================================

        SELECT
            @LinkedAccountID = LinkedAccountID

        FROM dbo.CreditCards

        WHERE CreditCardID = @CreditCardID
          AND CustomerID = @CustomerID;

        IF @LinkedAccountID IS NULL
            THROW 51106,
                  'Credit card not found.',
                  1;


        -- ====================================================
        -- LOCK AND VALIDATE LINKED BANK ACCOUNT
        -- ====================================================

        SELECT
            @AccountBalance = Balance,
            @AccountActive = IsActive,
            @AccountFrozen = IsFrozen,
            @AccountCurrency = Currency

        FROM dbo.Accounts
            WITH (UPDLOCK, HOLDLOCK)

        WHERE AccountID = @LinkedAccountID
          AND CustomerID = @CustomerID;

        IF @AccountActive IS NULL
           OR @AccountActive <> 1
            THROW 51107,
                  'Linked bank account is unavailable.',
                  1;

        IF @AccountFrozen = 1
            THROW 51108,
                  'Linked bank account is frozen.',
                  1;

        IF @AccountCurrency IS NULL
           OR @AccountCurrency <> 'TRY'
            THROW 51109,
                  'Only TRY accounts are supported.',
                  1;


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

        FROM dbo.CreditCards
            WITH (UPDLOCK, HOLDLOCK)

        WHERE CreditCardID = @CreditCardID
          AND CustomerID = @CustomerID
          AND LinkedAccountID = @LinkedAccountID;

        IF @CardCustomerID IS NULL
            THROW 51110,
                  'Credit card is unavailable.',
                  1;

        IF @CardCurrency <> 'TRY'
            THROW 51111,
                  'Only TRY credit cards are supported.',
                  1;


        -- ====================================================
        -- CHECK CARD STATUS
        -- ====================================================

        -- Spending requires an active, unexpired card.
        -- Debt payments remain available for frozen,
        -- expired or closed cards if the linked account
        -- is active and unfrozen.

        IF @Kind IN ('Purchase', 'CashAdvance')
        BEGIN

            IF @CardStatus <> 'Active'
                THROW 51112,
                      'This credit card is not active.',
                      1;

            IF @ExpiresAt < CAST(SYSDATETIME() AS DATE)
                THROW 51113,
                      'This credit card has expired.',
                      1;

        END;


        -- ====================================================
        -- CALCULATE AVAILABLE CREDIT LIMIT
        -- ====================================================

        SET @AvailableLimit =
            @CreditLimit - @OutstandingBalance;


        -- ====================================================
        -- VALIDATE PURCHASE AND CASH ADVANCE
        -- ====================================================

        IF @Kind IN ('Purchase', 'CashAdvance')
           AND @Amount > @AvailableLimit

            THROW 51114,
                  'Insufficient available credit limit.',
                  1;


        -- ====================================================
        -- VALIDATE CASH ADVANCE ACCOUNT BALANCE
        -- ====================================================

        IF @Kind = 'CashAdvance'
           AND @AccountBalance >
               9999999999999999.99 - @Amount

            THROW 51115,
                  'Bank account balance limit exceeded.',
                  1;


        -- ====================================================
        -- VALIDATE CREDIT CARD PAYMENT
        -- ====================================================

        IF @Kind = 'Payment'
        BEGIN

            IF @OutstandingBalance <= 0
                THROW 51116,
                      'There is no outstanding credit card debt.',
                      1;

            IF @Amount > @OutstandingBalance
                THROW 51117,
                      'Payment cannot exceed outstanding debt.',
                      1;

            IF @Amount > @AccountBalance
                THROW 51118,
                      'Insufficient bank account balance.',
                      1;

        END;


        -- ====================================================
        -- EXECUTE CREDIT CARD PURCHASE
        -- ====================================================

        IF @Kind = 'Purchase'
        BEGIN

            UPDATE dbo.CreditCards

            SET OutstandingBalance =
                OutstandingBalance + @Amount

            WHERE CreditCardID = @CreditCardID;

            IF @@ROWCOUNT <> 1
                THROW 51119,
                      'Credit card update failed.',
                      1;

        END;


        -- ====================================================
        -- EXECUTE CASH ADVANCE
        -- ====================================================

        ELSE IF @Kind = 'CashAdvance'
        BEGIN

            -- Increase credit card debt.

            UPDATE dbo.CreditCards

            SET OutstandingBalance =
                OutstandingBalance + @Amount

            WHERE CreditCardID = @CreditCardID;

            IF @@ROWCOUNT <> 1
                THROW 51119,
                      'Credit card update failed.',
                      1;


            -- Credit the linked bank account.

            UPDATE dbo.Accounts

            SET Balance = Balance + @Amount

            WHERE AccountID = @LinkedAccountID;

            IF @@ROWCOUNT <> 1
                THROW 51120,
                      'Bank account update failed.',
                      1;


            -- Record the bank-side movement.

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

        END;


        -- ====================================================
        -- EXECUTE CREDIT CARD PAYMENT
        -- ====================================================

        ELSE IF @Kind = 'Payment'
        BEGIN

            -- Deduct payment from the linked bank account.

            UPDATE dbo.Accounts

            SET Balance = Balance - @Amount

            WHERE AccountID = @LinkedAccountID;

            IF @@ROWCOUNT <> 1
                THROW 51120,
                      'Bank account update failed.',
                      1;


            -- Reduce outstanding credit card debt.

            UPDATE dbo.CreditCards

            SET OutstandingBalance =
                OutstandingBalance - @Amount

            WHERE CreditCardID = @CreditCardID;

            IF @@ROWCOUNT <> 1
                THROW 51119,
                      'Credit card update failed.',
                      1;


            -- Record the bank-side movement.

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

        SELECT
            @BankTransactionID = TransactionID

        FROM @CreatedBankTransaction;


        -- ====================================================
        -- INSERT CREDIT CARD TRANSACTION RECORD
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

        INTO @CreatedCardTransaction
        (
            CardTransactionID
        )

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


        SELECT
            @CardTransactionID = CardTransactionID

        FROM @CreatedCardTransaction;


        -- ====================================================
        -- CREATE BANK TRANSACTION AUDIT LOG
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
        -- CREATE CREDIT CARD AUDIT LOG
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


        -- ====================================================
        -- COMMIT TRANSACTION
        -- ====================================================

        COMMIT TRANSACTION;


        -- ====================================================
        -- RETURN CREATED TRANSACTION ID
        -- ====================================================

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
-- 3. CREDIT CARD PURCHASE PROCEDURE
-- ============================================================

CREATE OR ALTER PROCEDURE
    dbo.sp_CreditCardPurchase

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
-- 4. CREDIT CARD CASH ADVANCE PROCEDURE
-- ============================================================

CREATE OR ALTER PROCEDURE
    dbo.sp_CreditCardCashAdvance

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
-- 5. CREDIT CARD PAYMENT PROCEDURE
-- ============================================================

CREATE OR ALTER PROCEDURE
    dbo.sp_CreditCardPayment

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
-- 6. VERIFY CREATED PROCEDURES
-- ============================================================

SELECT

    p.name AS ProcedureName,
    p.create_date AS CreatedAt,
    p.modify_date AS LastModified

FROM sys.procedures AS p

WHERE p.schema_id = SCHEMA_ID(N'dbo')

  AND p.name IN
  (
      N'sp_ExecuteCreditCardTransaction',
      N'sp_CreditCardPurchase',
      N'sp_CreditCardCashAdvance',
      N'sp_CreditCardPayment'
  )

ORDER BY p.name;
GO


-- ============================================================
-- 7. VERIFY CREDIT CARD BALANCES
-- ============================================================

SELECT

    CreditCardID,
    CustomerID,
    LinkedAccountID,
    CardType,

    RIGHT(CardNumber, 4) AS LastFourDigits,

    CreditLimit,
    OutstandingBalance,

    CreditLimit - OutstandingBalance
        AS AvailableCreditLimit,

    CardStatus,
    ExpiresAt

FROM dbo.CreditCards

ORDER BY CreditCardID DESC;
GO


-- ============================================================
-- 8. VERIFY CREDIT CARD TRANSACTIONS
-- ============================================================

SELECT

    CardTransactionID,
    CreditCardID,
    BankTransactionID,
    TransactionType,
    Amount,
    Description,
    TransactionStatus,
    CreatedAt

FROM dbo.CreditCardTransactions

ORDER BY CardTransactionID DESC;
GO


-- ============================================================
-- 9. FINISH
-- ============================================================

PRINT '============================================';
PRINT '09_credit_card_procedures.sql completed.';
PRINT '4 credit card procedures checked.';
PRINT 'Credit card transaction support added.';
PRINT 'No financial transaction was executed.';
PRINT 'Existing records were preserved.';
PRINT '============================================';
GO

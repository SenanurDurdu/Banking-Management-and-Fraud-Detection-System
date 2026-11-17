
-- ============================================================
-- BANKING MANAGEMENT & FRAUD DETECTION SYSTEM
-- FILE: 05_transaction_procedures.sql
-- PURPOSE: Banking transaction stored procedures
--
-- SOURCE:
--   Improved sp_ExecuteBankTransaction
--   Original deposit, withdrawal and transfer wrappers
--
-- RUN AFTER:
--   01_schema.sql
--   02_constraints_indexes.sql
--   03_seed_fraud_rules.sql
--   04_views.sql
--
-- IMPORTANT:
--   No transaction is executed by this setup script.
--   Existing records are not deleted or modified.
-- ============================================================

USE BankingFraudDB;
GO


-- ============================================================
-- 1. MAIN BANK TRANSACTION PROCEDURE
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
        @DestinationAccountID INT = NULL,
        @SourceCustomerID INT,
        @SourceBalance DECIMAL(18,2),
        @SourceCurrency CHAR(3),
        @SourceActive BIT,
        @DestinationBalance DECIMAL(18,2),
        @DestinationCurrency CHAR(3),
        @DestinationActive BIT,
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
            @SourceActive = IsActive
        FROM dbo.Accounts
        WHERE AccountID = @SourceAccountID;

        IF @SourceActive IS NULL OR @SourceActive <> 1
            THROW 51011, 'Source account is unavailable.', 1;

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
                @DestinationActive = IsActive
            FROM dbo.Accounts
            WHERE AccountID = @DestinationAccountID
              AND AccountNumber = @DestinationAccountNumber;

            IF @DestinationActive IS NULL
               OR @DestinationActive <> 1
                THROW 51013, 'Recipient account is unavailable.', 1;

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
-- 2. DEPOSIT PROCEDURE
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
-- 3. WITHDRAWAL PROCEDURE
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
-- 4. TRANSFER PROCEDURE
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
-- 5. VERIFY CREATED PROCEDURES
-- ============================================================

-- Read-only verification.
-- No deposit, withdrawal or transfer is executed.

SELECT
    p.name AS ProcedureName,
    p.create_date AS CreatedAt,
    p.modify_date AS LastModified
FROM sys.procedures AS p
WHERE p.schema_id = SCHEMA_ID(N'dbo')
  AND p.name IN
  (
      N'sp_ExecuteBankTransaction',
      N'sp_Deposit',
      N'sp_Withdraw',
      N'sp_Transfer'
  )
ORDER BY p.name;
GO


-- ============================================================
-- 6. VERIFY PROCEDURE PARAMETERS
-- ============================================================

SELECT
    OBJECT_NAME(p.object_id) AS ProcedureName,
    p.parameter_id AS ParameterOrder,
    p.name AS ParameterName,
    TYPE_NAME(p.user_type_id) AS DataType,
    p.max_length AS MaxLength,
    p.precision AS NumericPrecision,
    p.scale AS NumericScale
FROM sys.parameters AS p
WHERE p.object_id IN
(
    OBJECT_ID(N'dbo.sp_ExecuteBankTransaction'),
    OBJECT_ID(N'dbo.sp_Deposit'),
    OBJECT_ID(N'dbo.sp_Withdraw'),
    OBJECT_ID(N'dbo.sp_Transfer')
)
ORDER BY
    ProcedureName,
    ParameterOrder;
GO


-- ============================================================
-- 7. FINISH
-- ============================================================

PRINT '============================================';
PRINT '05_transaction_procedures.sql completed.';
PRINT '4 transaction procedures checked.';
PRINT 'No banking transaction was executed.';
PRINT 'Existing records were preserved.';
PRINT '============================================';
GO

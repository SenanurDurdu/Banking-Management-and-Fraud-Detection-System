
-- ============================================================
-- NG BANK | 05_procedures.sql
-- CONSOLIDATED VERSION - 20 TABLE DATABASE
--
-- 10 original application-facing procedures
--  1 additional statement procedure
--  5 triggers
--  Billing settings backfill
--  Final verification
--
-- RUN AFTER:
-- 01_schema.sql
-- 02_constraints_indexes.sql
-- 03_seed_data.sql
-- 04_views.sql
-- ============================================================

USE [BankingFraudDB_Test];
GO

SET ANSI_NULLS ON; --IS NULL VE IS NOT NULL kontrolleri sağlanır.
GO
SET QUOTED_IDENTIFIER ON; -- "" ın nesne adı için yorumlanmasını sağlar.Metinler de '' içinde saklanır.
GO

-- ============================================================
-- 01. MAIN BANK TRANSACTION ENGINE
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_ExecuteBankTransaction --Para yatırma,çekme ve transferi aynı prosedürü yürütür.
    @Kind VARCHAR(20),--Hangi dalın çalışacağını belirler.(İşlem türü)
    @UserID INT,
    @SourceAccountID INT,
    @DestinationAccountNumber CHAR(18) = NULL,
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N'' --İsteğe bağlı doldurulur.
AS
BEGIN
    SET NOCOUNT ON; --Etkilenen satır sayısını yazdırmaz.
    SET XACT_ABORT ON; --Hata çıkması durumunda geri alabiliriz.

    DECLARE --Değişkenler açılır.
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

    DECLARE @Created TABLE --Tek sütunlu tablo değişkeni; yeni banka transaction ı sonrası TransactionID buraya yazılacak.
    (
        TransactionID BIGINT
    );

    IF @Kind IS NULL
       OR @Kind NOT IN ('Deposit','Withdrawal','Transfer') --Bu liste dışındaysa parametre reddedilir.
        THROW 51001, 'Invalid transaction type.', 1;

    IF @UserID IS NULL OR @UserID <= 0 -- Kullanıcı kimlği boşsa  parametre reddedilir.
       OR @SourceAccountID IS NULL OR @SourceAccountID <= 0
        THROW 51002, 'Invalid user or account.', 1;

    IF @Amount IS NULL OR @Amount <= 0 --Tutar sıfır ve sıfırdan küçük ve nullsa  parametre reddedilir.
        THROW 51003, 'Amount must be positive.', 1;

    IF @Kind = 'Transfer' --Transfer için hedef hesap numarası 18 rakamdan oluşmalı ve TR bulunmalı yoksa  parametre reddedilir.
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

    BEGIN TRY  --Hata yakalama kapsamı başlatılır.
        BEGIN TRANSACTION; --Tutarlı biçimde tamamlanacak SQL işlemini başlatır.

        SELECT
            @Role = u.Role,
            @CustomerID = u.CustomerID
        FROM dbo.Users AS u WITH (UPDLOCK,HOLDLOCK) --UPDLOCK okunan hesapta güncelleme amacıyla kilit ister,HOLDLOCK sql transactiın sonuna kadar tutulmasını ister.
        LEFT JOIN dbo.Customers AS c
            ON c.CustomerID = u.CustomerID
        WHERE u.UserID = @UserID
          AND u.IsActive = 1
          AND
          (
              u.Role = 'Admin' --Kullanıcı admin ise aktif müşteri profiline ihtiyaç yoktur.
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

            IF @DestinationAccountID IS NULL --Hedef hesap null olamaz.
                THROW 51008, 'Destination account not found.', 1;

            IF @DestinationAccountID = @SourceAccountID  --Hedef ve kaynak hesap aynı olamaz.
                THROW 51009, 'Cannot transfer to the same account.', 1;
        END;

        -- Lock accounts in deterministic order.

        SET @FirstID = --İki hesap varsa küçük olan seçilir.
            CASE
                WHEN @DestinationAccountID IS NOT NULL
                 AND @DestinationAccountID < @SourceAccountID
                THEN @DestinationAccountID
                ELSE @SourceAccountID
            END;

        SET @SecondID = --İki hesap varsa büyük olan seçilir.
            CASE
                WHEN @DestinationAccountID IS NULL THEN NULL
                WHEN @DestinationAccountID > @SourceAccountID
                THEN @DestinationAccountID
                ELSE @SourceAccountID
            END;

        SELECT @LockedAccountID = AccountID --İlk hesap kilit ipuçlarıyla okunur yoksa error verilir.
        FROM dbo.Accounts WITH (UPDLOCK,HOLDLOCK)
        WHERE AccountID = @FirstID;

        IF @LockedAccountID IS NULL
            THROW 51010, 'Account not found.', 1;

        IF @SecondID IS NOT NULL  --İkinci hesap kilit ipuçlarıyla okunur yoksa error verilir.
        BEGIN
            SET @LockedAccountID = NULL;

            SELECT @LockedAccountID = AccountID
            FROM dbo.Accounts WITH (UPDLOCK,HOLDLOCK)
            WHERE AccountID = @SecondID;

            IF @LockedAccountID IS NULL
                THROW 51010, 'Account not found.', 1;
        END;

        SELECT --Kilitleme sonrası seçilen hesabın bilgileri okunur.
            @SourceCustomerID = CustomerID,
            @SourceBalance = Balance,
            @SourceCurrency = Currency,
            @SourceActive = IsActive,
            @SourceFrozen = IsFrozen
        FROM dbo.Accounts
        WHERE AccountID = @SourceAccountID;

        IF @SourceActive IS NULL OR @SourceActive <> 1  --Aktif hesap 0 veya null olamaz.
            THROW 51011, 'Source account is unavailable.', 1;

        IF @SourceFrozen = 1
            THROW 51017, 'Source account is frozen.', 1;

        IF @Role = 'Customer' --Müşteri gönderici değilse parametre reddedilir.
           AND
           (
               @CustomerID IS NULL
               OR @SourceCustomerID <> @CustomerID
           )
            THROW 51012, 'Account ownership check failed.', 1;

        IF @Kind = 'Transfer' --Hedef hesap bilgileri okunur.
        BEGIN
            SELECT
                @DestinationBalance = Balance,
                @DestinationCurrency = Currency,
                @DestinationActive = IsActive,
                @DestinationFrozen = IsFrozen
            FROM dbo.Accounts
            WHERE AccountID = @DestinationAccountID;

            IF @DestinationActive IS NULL --Aktif değilse parametre reddedilir.
               OR @DestinationActive <> 1
                THROW 51013, 'Destination account is unavailable.', 1;

            IF @DestinationFrozen = 1 -- Frozen ise parametre reddedilir.
                THROW 51018, 'Destination account is frozen.', 1;

            IF @SourceCurrency <> @DestinationCurrency --Kaynak ve hedef para birimi farklıysa parametre reddedilir.
                THROW 51014, 'Currency mismatch.', 1;
        END;

        IF @Kind IN ('Withdrawal','Transfer') --Transferve para çekimi güncel bakiyeden  büyükse parametre reddedilir.
           AND @SourceBalance < @Amount
            THROW 51015, 'Insufficient balance.', 1;

        IF @Kind = 'Deposit' --Decimal sınırını geçmemeli yoksa parametre reddedilir.
           AND @SourceBalance >
               9999999999999999.99 - @Amount
            THROW 51016, 'Balance limit exceeded.', 1;

        IF @Kind = 'Transfer'--Decimal sınırını geçmemeli yoksa parametre reddedilir.
           AND @DestinationBalance >
               9999999999999999.99 - @Amount
            THROW 51016, 'Destination balance limit exceeded.', 1;

        SET @FromID = NULL; --İşlem geçmişinde kullanılacakları için başlangıçta null yapılır.
        SET @ToID = NULL;

        IF @Kind = 'Deposit'--Para yatırma
        BEGIN
            UPDATE dbo.Accounts
            SET Balance = Balance + @Amount  -- Mevcut bakiyeye yatırılacak tutar eklenir.
            WHERE AccountID = @SourceAccountID;--Hedef hesaba ait tutar üzerinde bu işlem yapılır.

            SET @ToID = @SourceAccountID;
        END
        ELSE IF @Kind = 'Withdrawal'--Para çekme
        BEGIN
            UPDATE dbo.Accounts
            SET Balance = Balance - @Amount --Mevcut bakiyeden çekilecek olan tutar çıkarılır.
            WHERE AccountID = @SourceAccountID;--Hedef hesaba ait tutar üzerinde bu işlem yapılır.

            SET @FromID = @SourceAccountID;
        END
        ELSE
        BEGIN
            UPDATE dbo.Accounts --Önce kaynak hesaptan düşülür.
            SET Balance = Balance - @Amount
            WHERE AccountID = @SourceAccountID;

            UPDATE dbo.Accounts --Sonra hedef hesaba eklenir.
            SET Balance = Balance + @Amount
            WHERE AccountID = @DestinationAccountID;

            SET @FromID = @SourceAccountID;
            SET @ToID = @DestinationAccountID;
        END;

        INSERT INTO dbo.Transactions --Yapılan işlemler Transaction tablosuna yazılır.
        (
            FromAccountID,
            ToAccountID,
            TransactionType,
            Amount,
            Description
        )
        OUTPUT INSERTED.TransactionID --Yeni transaction ın otomatik kimliğini yakalr ve tablo değişkenine koyar.
        INTO @Created(TransactionID)
        VALUES
        (
            @FromID,
            @ToID,
            @Kind,
            @Amount,
            COALESCE(@Description,N'')--Değerler yazılır, açıklama null geldiyse boş metin kullanılır.
        );

        SELECT @TransactionID = TransactionID
        FROM @Created;

        INSERT INTO dbo.AuditLogs --Bu tabloya da eylem eklenir.
        (
            ActionType,
            EntityName,
            EntityID,
            Description,
            UserID
        )
        VALUES
        (
            UPPER(@Kind),--Transfer değerini transfer yapar.
            'Transaction',
            @TransactionID,
            CONCAT(@Kind, ': ', @Amount),--Birleştirilir.
            @UserID
        );

        COMMIT TRANSACTION;--İşlem transaction seviyesini tamamlar.

        SELECT @TransactionID AS TransactionID;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0  --Hata olursa rollback ile işlemler geri alınır.
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- ============================================================
-- 02. DEPOSIT
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_Deposit --Kullanıcının gerekli bilgilerini alır.
    @UserID INT,
    @SourceAccountID INT,
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N''
AS
BEGIN
    SET NOCOUNT ON;

    EXEC dbo.sp_ExecuteBankTransaction --Deposit'e göre diğer parametreler aynen iletilir.
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

CREATE OR ALTER PROCEDURE dbo.sp_Withdraw  --Kullanıcının gerekli bilgilerini alır.
    @UserID INT,
    @SourceAccountID INT,
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N''
AS
BEGIN
    SET NOCOUNT ON;

    EXEC dbo.sp_ExecuteBankTransaction --Withdrawal'a göre diğer parametreler aynen iletilir.
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

CREATE OR ALTER PROCEDURE dbo.sp_Transfer --Kullanıcının gerekli bilgilerini alır.
    @UserID INT,
    @SourceAccountID INT,
    @DestinationAccountNumber CHAR(18),
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N''
AS
BEGIN
    SET NOCOUNT ON;

    EXEC dbo.sp_ExecuteBankTransaction  --Transfer'e göre diğer parametreler aynen iletilir.
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

CREATE OR ALTER PROCEDURE dbo.sp_ExecuteCreditCardTransaction --Kredi kartı işlemleri yürütülür.
    @Kind VARCHAR(20),
    @UserID INT,
    @CreditCardID BIGINT,
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N''
AS
BEGIN
    SET NOCOUNT ON;  --Etkilenen satır sayısını yazdırmaz.
    SET XACT_ABORT ON; --Hata çıkması durumunda geri alabiliriz.

    DECLARE --Değişkenler açılır.
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

    DECLARE @CreatedBank TABLE --Yeni banka hareket kimliğini yakalamak için açılır.
    (
        TransactionID BIGINT
    );

    DECLARE @CreatedCard TABLE ---Yeni  kart hareket kimliğini yakalamak için açılır.
    (
        CardTransactionID BIGINT
    );

    IF @Kind IS NULL --Bu liste dışındaysa parametre reddedilir.
       OR @Kind NOT IN ('Purchase','CashAdvance','Payment')
        THROW 51101, 'Invalid card transaction type.', 1;

    IF @UserID IS NULL OR @UserID <= 0 --ID negatif veya sıfırsa parametre reddedilir.
        THROW 51102, 'Invalid user.', 1;

    IF @CreditCardID IS NULL OR @CreditCardID <= 0 --ID negatif veya sıfırsa parametre reddedilir.
        THROW 51103, 'Invalid credit card.', 1;

    IF @Amount IS NULL OR @Amount <= 0 --Miktar negatif veya sıfırsa parametre reddedilir.
        THROW 51104, 'Amount must be positive.', 1;

    SET @Description = COALESCE(@Description,N''); --Değerler yazılır, açıklama null geldiyse boş metin kullanılır.

    BEGIN TRY --Hata yakalama kapsamı başlatılır.
        BEGIN TRANSACTION; --Tutarlı biçimde tamamlanacak SQL işlemini başlatır.

        SELECT @CustomerID = u.CustomerID
        FROM dbo.Users AS u WITH (UPDLOCK,HOLDLOCK) --UPDLOCK okunan hesapta güncelleme amacıyla kilit ister,HOLDLOCK sql transactiın sonuna kadar tutulmasını ister.
        INNER JOIN dbo.Customers AS c
            ON c.CustomerID = u.CustomerID
        WHERE u.UserID = @UserID
          AND u.Role = 'Customer' --Kullanıcının hem users hem de customers tablosunda aktif olması gerekir.
          AND u.IsActive = 1
          AND c.IsActive = 1;

        IF @CustomerID IS NULL --ID nullsa parametre reddedilir.
            THROW 51105, 'Active customer required.', 1;

        SELECT @LinkedAccountID = LinkedAccountID
        FROM dbo.CreditCards  --Kart id'si müşteri id'si ile aranır.
        WHERE CreditCardID = @CreditCardID
          AND CustomerID = @CustomerID;

        IF @LinkedAccountID IS NULL --ID nullsa parametre reddedilir.
            THROW 51106, 'Credit card not found.', 1;

        SELECT
            @AccountBalance = Balance,
            @AccountActive = IsActive,
            @AccountFrozen = IsFrozen,
            @AccountCurrency = Currency
        FROM dbo.Accounts WITH (UPDLOCK,HOLDLOCK) --UPDLOCK okunan hesapta güncelleme amacıyla kilit ister,HOLDLOCK sql transactiın sonuna kadar tutulmasını sağlar.
        WHERE AccountID = @LinkedAccountID
          AND CustomerID = @CustomerID;

        IF @AccountActive IS NULL OR @AccountActive <> 1 -- Hesap aktif olmaıdır.
            THROW 51107, 'Linked account unavailable.', 1;

        IF @AccountFrozen = 1
            THROW 51108, 'Linked account frozen.', 1; --Hesap donmuş olmamalıdır.

        IF @AccountCurrency <> 'TRY' --Hesap para birimi TRY olmalıdır.
            THROW 51109, 'Only TRY supported.', 1;

        SELECT
            @CardCustomerID = CustomerID,
            @CardStatus = CardStatus,
            @CardCurrency = Currency,
            @CreditLimit = CreditLimit,
            @OutstandingBalance = OutstandingBalance,
            @ExpiresAt = ExpiresAt
        FROM dbo.CreditCards WITH (UPDLOCK,HOLDLOCK) --UPDLOCK okunan hesapta güncelleme amacıyla kilit ister,HOLDLOCK sql transactiın sonuna kadar tutulmasını sağlar.
        WHERE CreditCardID = @CreditCardID --Kart id'si , müşteri id,2si ve bağlı hesaplar bir kere daha eşleştirilir.
          AND CustomerID = @CustomerID
          AND LinkedAccountID = @LinkedAccountID;

        IF @CardCustomerID IS NULL --ID nullsa parametre reddedilir.
            THROW 51110, 'Credit card unavailable.', 1;

        IF @CardCurrency <> 'TRY' --Para birimi farklıysa parametre reddedilir.
            THROW 51111, 'Card currency not supported.', 1;

        IF @Kind IN ('Purchase','CashAdvance')
        BEGIN
            IF @CardStatus <> 'Active' --Kart aktif olmalıdır.
                THROW 51112, 'Card is not active.', 1;

            IF @ExpiresAt < CONVERT(DATE,SYSDATETIME()) --Süresi geçmemiş olmalıdır.
                THROW 51113, 'Card has expired.', 1;

            IF @Amount > @CreditLimit - @OutstandingBalance --Kullanılabilir limit , istenilen limit ve bporç farkından düşük olmalıdır.
                THROW 51114, 'Insufficient card limit.', 1;
        END;

        IF @Kind = 'CashAdvance' --Üst sınırı aşmamalıdır.
           AND @AccountBalance >
               9999999999999999.99 - @Amount
            THROW 51115, 'Account balance limit exceeded.', 1;

        IF @Kind = 'Payment' -- Ödeme tutarı kart borcundan fazla olamaz.
        BEGIN
            IF @OutstandingBalance <= 0
                THROW 51116, 'No card debt.', 1;

            IF @Amount > @OutstandingBalance -- Ödeme tutarı kart borcundan fazla olamaz.
                THROW 51117, 'Payment exceeds card debt.', 1;

            IF @Amount > @AccountBalance -- Mikyat hesap bakiyesinden fazla olmalıdır.
                THROW 51118, 'Insufficient bank balance.', 1;
        END;

        IF @Kind = 'Purchase' --Para çekme
        BEGIN
            UPDATE dbo.CreditCards
            SET OutstandingBalance = OutstandingBalance + @Amount --Miktar kadar borca eklenir.
            WHERE CreditCardID = @CreditCardID;
        END
        ELSE IF @Kind = 'CashAdvance' -- Nakit avans
        BEGIN
            UPDATE dbo.CreditCards
            SET OutstandingBalance = OutstandingBalance + @Amount --Miktar kadar borca eklenir.
            WHERE CreditCardID = @CreditCardID;

            UPDATE dbo.Accounts
            SET Balance = Balance + @Amount  --Miktar kadar hesabın bakiyesine eklenir.
            WHERE AccountID = @LinkedAccountID;

            SET @BankDescription = LEFT( --Banka hareketi açıklamaası hazırlanır.
                CONCAT( --Birleştirilir
                    'Credit card cash advance. CardID=',
                    @CreditCardID,
                    '. ',
                    @Description
                ),250
            );

            INSERT INTO dbo.Transactions --Transactions tablosuna veriler girilir.
            (
                FromAccountID,
                ToAccountID,
                TransactionType,
                Amount,
                Description
            )
            OUTPUT INSERTED.TransactionID --Yeni transaction ın otomatik kimliğini yakalar ve tablo değişkenine koyar.
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
        ELSE --Payment (Borç ödeme için)
        BEGIN
            UPDATE dbo.Accounts
            SET Balance = Balance - @Amount --Banka hesabından miktar düşülür.
            WHERE AccountID = @LinkedAccountID;

            UPDATE dbo.CreditCards
            SET OutstandingBalance = OutstandingBalance - @Amount --Borçtan yatırılan miktar düşülür.
            WHERE CreditCardID = @CreditCardID;

            SET @BankDescription = LEFT( --Açıklama oluşturulur.
                CONCAT( --Birleştirilir
                    'Credit card debt payment. CardID=', --Metin 250 ile sınırlandırılır.
                    @CreditCardID,
                    '. ',
                    @Description
                ),250
            );

            INSERT INTO dbo.Transactions --Transactions tablosuna veriler eklenir.
            (
                FromAccountID,
                ToAccountID,
                TransactionType,
                Amount,
                Description
            )
            OUTPUT INSERTED.TransactionID --Yeni transaction ın otomatik kimliğini yakalar ve tablo değişkenine koyar.
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

        INSERT INTO dbo.CreditCardTransactions --CreditCardTransactions tablosuna veriler eklenir.
        (
            CreditCardID,
            BankTransactionID,
            TransactionType,
            Amount,
            Description,
            TransactionStatus
        )
        OUTPUT INSERTED.CardTransactionID --Yeni transaction ın otomatik kimliğini yakalar ve tablo değişkenine koyar.
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
            INSERT INTO dbo.AuditLogs --AuditLogs tablosuna da veriler eklenir.
            (
                ActionType,
                EntityName,
                EntityID,
                Description,
                UserID
            )
            VALUES
            (
                CASE --Banka hareketleri için audit yazılır.
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

        INSERT INTO dbo.AuditLogs --AuditLogs tablosuna da veriler eklenir.
        (
            ActionType,
            EntityName,
            EntityID,
            Description,
            UserID
        )
        VALUES
        (
            CASE  --Her başarılı kart hareketi için ayrı audit yazılır.
                WHEN @Kind = 'Purchase'
                    THEN 'CREDIT_CARD_PURCHASE'
                WHEN @Kind = 'CashAdvance'
                    THEN 'CREDIT_CARD_CASH_ADVANCE'
                ELSE 'CREDIT_CARD_PAYMENT'
            END,
            'CreditCardTransactions',
            @CardTransactionID,
            CONCAT( --Birleştirilir
                'CardID=',@CreditCardID,
                ', Amount=',@Amount
            ),
            @UserID
        );

        COMMIT TRANSACTION;--Transaction sonuna kadar kaydedilir.

        SELECT --Çağırana iki sütun döner.
            @CardTransactionID AS CardTransactionID,
            @BankTransactionID AS BankTransactionID;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0  --Hata olursa rollback ile işlemler geri alınır.
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- ============================================================
-- 06. CREDIT CARD PURCHASE
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_CreditCardPurchase  --Kullanıcının gerekli bilgilerini alır.
    @UserID INT,
    @CreditCardID BIGINT,
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N''
AS
BEGIN
    SET NOCOUNT ON;

    EXEC dbo.sp_ExecuteCreditCardTransaction --Purchase'e göre diğer parametreler aynen iletilir.
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

CREATE OR ALTER PROCEDURE dbo.sp_CreditCardCashAdvance --Kullanıcının gerekli bilgilerini alır.
    @UserID INT,
    @CreditCardID BIGINT,
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N''
AS
BEGIN
    SET NOCOUNT ON;

    EXEC dbo.sp_ExecuteCreditCardTransaction --CashAdvance'e göre diğer parametreler aynen iletilir.
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

CREATE OR ALTER PROCEDURE dbo.sp_CreditCardPayment --Kullanıcının gerekli bilgilerini alır.
    @UserID INT,
    @CreditCardID BIGINT,
    @Amount DECIMAL(18,2),
    @Description NVARCHAR(250) = N''
AS
BEGIN
    SET NOCOUNT ON;

    EXEC dbo.sp_ExecuteCreditCardTransaction --Payment'e göre diğer parametreler aynen iletilir.
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

CREATE OR ALTER PROCEDURE dbo.sp_ScanFraud --Tamamlanmış banka hareketlerini aktif fraud kurallarıyla karşılaştırıyor.
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON; --Etkilenen satır sayısını yazdırmaz.
    SET XACT_ABORT ON;--Hata çıkması durumunda geri alabiliriz.

    DECLARE --Değişkenler açılır.
        @NewAlerts INT = 0,
        @LockResult INT;

    DECLARE @Created TABLE  --Yeni tabloda uyarı bilgileri banka hareket id'si ve risk saklanır.
    (
        AlertID BIGINT,
        TransactionID BIGINT,
        RuleID INT,
        RiskLevel VARCHAR(10)
    );

    IF @UserID IS NULL OR @UserID <= 0 --ID null veya negatif olursa parametre reddedilir.
        THROW 51030, 'Invalid UserID.', 1;

    IF NOT EXISTS
    (
        SELECT 1
        FROM dbo.Users
        WHERE UserID = @UserID
          AND Role = 'Admin'
          AND IsActive = 1 --Aktif admin aranır yoksa parametre reddedilir.
    )
        THROW 51031, 'Admin access required.', 1;

    BEGIN TRY --Hata yakalama kapsamı başlatılır.
        BEGIN TRANSACTION; --Tutarlı biçimde tamamlanacak SQL işlemini başlatır.

        EXEC @LockResult = sys.sp_getapplock --Tarama kili alma denenir.
            @Resource = 'BankingFraudDB_FraudScan',
            @LockMode = 'Exclusive',--Aynı kaynak adına sahip başka banka taramasının eşzamanlı girilmesi engellenir.
            @LockOwner = 'Transaction',--Kilidi transaction!a bağlar.
            @LockTimeout = 10000;--10000 milisaniye (10 saniye) ile sınırlıdır.

        IF @LockResult < 0 --Kilit sonu negatifse tarama hata verir catch yoluna girer.
            THROW 51032, 'Fraud scan lock failed.', 1;

        ;WITH Candidates AS
        (
            SELECT   --Her adayın banka transaction id'si tutarı ve işlem tarihi alınır.
                t.TransactionID,
                t.Amount,
                t.TransactionDate,
                COALESCE( --ilk dolu değer alınır.
                    t.FromAccountID,
                    t.ToAccountID
                ) AS AccountID
            FROM dbo.Transactions AS t --Sadece completed olan hareketler alınır.
            WHERE t.Status = 'Completed'
        ),
        Matches AS --Amaç:Her aday her aktif kuralla nasıl karşılaştırılıyor?
        (
            SELECT --Aday işlem ve kural bilgileri alınır.
                t.TransactionID,
                t.Amount,
                r.RuleID,
                r.RuleType,
                r.ThresholdValue,
                r.TimeWindowMinutes,
                x.MatchCount
            FROM Candidates AS t --Adaylarl kuralları eşleştirilir.
            CROSS JOIN dbo.FraudRules AS r
            OUTER APPLY
            (
                SELECT COUNT_BIG(*) AS MatchCount --Her aday çifti için eşleşen hareketleri sayan sayaç çalıştırılır.
                FROM dbo.Transactions AS p
                WHERE r.RuleType IN
                (
                    'Frequent', --Sık kullnılan işlemler için
                    'RepeatedAmount' --Aynı tutard yapılan işlemler için
                )
                  AND r.TimeWindowMinutes > 0
                  AND t.AccountID IS NOT NULL
                  AND p.Status = 'Completed'
                  AND p.TransactionDate >= DATEADD(--Pencerenin başlangıcı bulunur.
                      MINUTE,
                      -r.TimeWindowMinutes,
                      t.TransactionDate
                  )
                  AND
                  (
                      p.TransactionDate < t.TransactionDate --Aday hareketin sonrasındaki olaylar sayılmaz.
                      OR
                      (
                          p.TransactionDate = t.TransactionDate --Daha eski ve aynı olabilir.
                          AND p.TransactionID <= t.TransactionID
                      )
                  )
                  AND
                  (
                      p.FromAccountID = t.AccountID --Transaction'ın kaynak veya hedef hesabı, aday olaraak seçilen hespla aynı olmalıdır.
                      OR p.ToAccountID = t.AccountID
                  )
                  AND
                  (
                      r.RuleType = 'Frequent' --Tutarlar farklı olabilir.
                      OR p.Amount = t.Amount --Ama repeated için aynı olmaları gee
                  )
            ) AS x   --Alt sayım x ile kapanır.
            WHERE r.IsActive = 1
              AND r.RuleType IN
              (
                  'HighAmount',  --Dış sorgu bu kuralları kullanır.
                  'Frequent',
                  'RepeatedAmount'
              )
        ),
        Suspicious AS --Amaç: Hangi eşleşme uyarıya dönüşüyor?
        (
            SELECT
                TransactionID,
                RuleID,
                CASE
                    WHEN RuleType = 'HighAmount' --Yüksek miktar direkt 'high' amount olarak belirleniyor.
                    THEN 'High'
                    WHEN MatchCount >= ThresholdValue + 3 --Geride kalan kurallardan 3 ve daha fazla tekrar edilirse 'high' oluyor.
                    THEN 'High'
                    ELSE 'Medium'
                END AS RiskLevel,
                CAST(  --Description hazırlanır.
                    CASE
                        WHEN RuleType = 'HighAmount'
                        THEN CONCAT( --Birleştirilir
                            'High amount: ',
                            Amount,
                            ', threshold: ',
                            ThresholdValue
                        )
                        ELSE CONCAT( --Birleştirilir
                            MatchCount,
                            ' matching transactions in ',
                            TimeWindowMinutes,
                            ' minutes'
                        )
                    END
                    AS NVARCHAR(500)
                ) AS AlertDescription --Eşleşen kurallar için yazılır.
            FROM Matches
            WHERE
                (
                    RuleType = 'HighAmount'  --Eşik değere'e (50000) eşit veya daha yüksek olmalıdır.
                    AND Amount >= ThresholdValue
                )
                OR
                (
                    RuleType IN --Süre pozitif ve eşleme sayısı eşik değer'e (3) eşit veya daha yüksek olmalıdır.
                    (
                        'Frequent',
                        'RepeatedAmount'
                    )
                    AND TimeWindowMinutes > 0
                    AND MatchCount >= ThresholdValue
                )
        )
        INSERT INTO dbo.FraudAlerts --FraudAlert tablosuna satır eklenir.
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
        INTO @Created --Eklenen satır OUTPUT ile @Created tablosuna aktarılır.
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
        FROM Suspicious AS s --Eklenen satırların kaynağıdır.
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM dbo.FraudAlerts AS fa
                WITH (UPDLOCK,HOLDLOCK) --UPDLOCK okunan hesapta güncelleme amacıyla kilit ister,HOLDLOCK sql transactiın sonuna kadar tutulmasını sağlar.
            WHERE fa.TransactionID = s.TransactionID
              AND fa.RuleID = s.RuleID
        );

        SELECT @NewAlerts = COUNT(*) --Yalnızca bu çağrıda eklenen uyarıları sayar.
        FROM @Created;

        INSERT INTO dbo.AuditLogs --AuditLogs tablosuna Fraud_alert kaydı eklenir.
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
            CONCAT( --Birleştirilir
                'TransactionID=',c.TransactionID,
                ', RuleID=',c.RuleID,
                ', Risk=',c.RiskLevel
            ),
            @UserID
        FROM @Created AS c;

        INSERT INTO dbo.AuditLogs --Bütün tarama için ayrıca Fraud_scan kaydı açılır.
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
            CONCAT(@NewAlerts,' new bank fraud alerts'), --Birleştirilir
            @UserID
        );

        COMMIT TRANSACTION; --Transaction sonuna kadar kaydedilir.

        SELECT @NewAlerts AS NewAlerts;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0  --Hata olursa rollback ile işlemler geri alınır.
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- ============================================================
-- 10. CREDIT CARD FRAUD SCAN
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.sp_ScanCreditCardFraud --Tamamlanmış kart hareketlerini aktif fraud kurallarıyla karşılaştırıyor.
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON; --Etkilenen satır sayısını yazdırmaz.
    SET XACT_ABORT ON; --Hata çıkması durumunda geri alabiliriz.

    DECLARE --Değişkenler açılr.
        @NewAlerts INT = 0,
        @LockResult INT;

    DECLARE @Created TABLE --Tek sütunlu tablo değişkeni; yeni kart transaction ı sonrası TransactionID buraya yazılacak.
    (
        AlertID BIGINT,
        CardTransactionID BIGINT,
        RuleID INT,
        RiskLevel VARCHAR(10)
    );

    IF @UserID IS NULL OR @UserID <= 0 --ID negatif olursa parametre reddedilir.
        THROW 51040, 'Invalid UserID.', 1;

    IF NOT EXISTS  --Users tablosunda aktif admin aranıt yoksa parametre reddedilir.
    (
        SELECT 1
        FROM dbo.Users
        WHERE UserID = @UserID
          AND Role = 'Admin'
          AND IsActive = 1
    )
        THROW 51041, 'Admin access required.', 1;

    BEGIN TRY  --Hata yakalama kapsamı başlatılır.
        BEGIN TRANSACTION; --Tutarlı biçimde tamamlanacak SQL işlemini başlatır.

        EXEC @LockResult = sys.sp_getapplock --Özel kilit alınır 10 saniyelik sınırı vardır.
            @Resource =
                'BankingFraudDB_CreditCardFraudScan',
            @LockMode = 'Exclusive',
            @LockOwner = 'Transaction',
            @LockTimeout = 10000;

        IF @LockResult < 0 -- sonuç negatifse hata alınır.
            THROW 51042, 'Card fraud scan lock failed.', 1;

        ;WITH Candidates AS --Tamamlanmış ve alışveriş işlemine filtrelerle adaylar alınır..
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
        Matches AS --Her aday aktif kural seçenekleriyle eşleştirilir.
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
            OUTER APPLY --Uygun alışverişler sayılacak.
            (
                SELECT COUNT_BIG(*) AS MatchCount
                FROM dbo.CreditCardTransactions AS p
                WHERE r.RuleType IN
                (
                    'Frequent',
                    'RepeatedAmount'
                )
                  AND r.TimeWindowMinutes > 0
                  AND p.CreditCardID = t.CreditCardID --Aday kart id ile kart işlemlerindeki kart id aynı olmalıdır.
                  AND p.TransactionStatus = 'Completed'
                  AND p.TransactionType = 'Purchase'
                  AND p.BankTransactionID IS NULL
                  AND p.CreatedAt >= DATEADD( --Zamandan dakika penceresi çıkarılır.
                      MINUTE,
                      -r.TimeWindowMinutes,
                      t.CreatedAt
                  )
                  AND
                  (
                      p.CreatedAt < t.CreatedAt --Önceki hareketler ve
                      OR
                      (
                          p.CreatedAt = t.CreatedAt --Aynı anda ID'si adaydan büyük olmayan hareketler sayılır.
                          AND p.CardTransactionID <=
                              t.CardTransactionID
                      )
                  )
                  AND
                  (
                      r.RuleType = 'Frequent' --Her tutar
                      OR p.Amount = t.Amount --Eşit tutarlar
                  )
            ) AS x --Alt sayım x ile kapanır.
            WHERE r.IsActive = 1 --Aktif olan için bu kurallardan alınır.
              AND r.RuleType IN
              (
                  'HighAmount',
                  'Frequent',
                  'RepeatedAmount'
              )
        ),
        Suspicious AS  --Amaç: Hangi eşleşme uyarıya dönüşüyor?
        (
            SELECT
                CardTransactionID,
                RuleID,
                CASE
                    WHEN RuleType = 'HighAmount' --Yüksek miktar direkt 'high' amount olarak belirleniyor.
                    THEN 'High'
                    WHEN MatchCount >= ThresholdValue + 3 --Geride kalan kurallardan 3 ve daha fazla tekrar edilirse 'high' oluyor.
                    THEN 'High'
                    ELSE 'Medium'
                END AS RiskLevel, --Risk level hazırlanır.
                CAST(
                    CASE
                        WHEN RuleType = 'HighAmount'
                        THEN CONCAT(--Birleştirilir
                            'High card purchase: ',
                            Amount,
                            ', threshold: ',
                            ThresholdValue
                        )
                        ELSE CONCAT(--Birleştirilir
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
                    RuleType = 'HighAmount' --Eşik değere'e (50000) eşit veya daha yüksek olmalıdır.
                    AND Amount >= ThresholdValue
                )
                OR
                (
                    RuleType IN --Süre pozitif ve eşleme sayısı eşik değer'e (3) eşit veya daha yüksek olmalıdır.
                    (
                        'Frequent',
                        'RepeatedAmount'
                    )
                    AND TimeWindowMinutes > 0
                    AND MatchCount >= ThresholdValue
                )
        )
        INSERT INTO dbo.FraudAlerts  --FraudAlert tablosuna satır eklenir.
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
        INTO @Created --Eklenen satır OUTPUT ile @Created tablosuna aktarılır.
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
        FROM Suspicious AS s --Eklenen satırların kaynağıdır.
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM dbo.FraudAlerts AS fa
                WITH (UPDLOCK,HOLDLOCK)  --UPDLOCK okunan hesapta güncelleme amacıyla kilit ister,HOLDLOCK sql transactiın sonuna kadar tutulmasını sağlar.
            WHERE fa.CardTransactionID = s.CardTransactionID
              AND fa.RuleID = s.RuleID
        );

        SELECT @NewAlerts = COUNT(*)  --Yalnızca bu çağrıda eklenen uyarıları sayar.
        FROM @Created;

        INSERT INTO dbo.AuditLogs --AuditLogs tablosuna Fraud_alert kaydı eklenir.
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
            CONCAT( --Birleştirilir
                'CardTransactionID=',c.CardTransactionID,
                ', RuleID=',c.RuleID,
                ', Risk=',c.RiskLevel
            ),
            @UserID
        FROM @Created AS c;

        INSERT INTO dbo.AuditLogs --Bütün tarama için ayrıca Fraud_scan kaydı açılır.
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
            CONCAT(@NewAlerts,' new card fraud alerts'), --Birleştirilir
            @UserID
        );

        COMMIT TRANSACTION; --Transaction sonuna kadar kaydedilir.

        SELECT @NewAlerts AS NewAlerts;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0  --Hata olursa rollback ile işlemler geri alınır.
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
AFTER UPDATE --Hesap güncellemesinden sonra çalışır.
AS
BEGIN
    SET NOCOUNT ON;  --Etkilenen satır sayısını yazdırmaz.

    IF NOT (UPDATE(IsActive) OR UPDATE(IsFrozen)) --Hesap aktif değilse veya frozen ise devam edilmez.
        RETURN;

    INSERT INTO dbo.AccountStatusHistory --Hesap durumu geçmişi tablosuna yazılacak bilgiler.
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
        i.AccountID, --Yeni satır kimliğidir.
        NULL,
        d.IsActive, --Geçmiş hesap aktifliğidir.
        i.IsActive,
        d.IsFrozen,
        i.IsFrozen,
        N'Account status changed',
        SYSDATETIME()
    FROM inserted AS i --Eklenen yeni satırlar.(SQL Server sağlar bu satır kümelerini)
    INNER JOIN deleted AS d --Silinen eski satırlar.(SQL Server sağlar bu satır kümelerini)
        ON d.AccountID = i.AccountID
    WHERE i.IsActive <> d.IsActive  --Aktiflik ve donma durumunda değişiklik varsa geçmişe eklenir.
       OR i.IsFrozen <> d.IsFrozen;
END;
GO

-- ============================================================
-- 12. FRAUD ALERT REVIEW HISTORY TRIGGER
-- ============================================================

CREATE OR ALTER TRIGGER dbo.trg_FraudAlerts_ReviewHistory
ON dbo.FraudAlerts
AFTER UPDATE --Uyarı güncellemesinden sonra çalışır.
AS
BEGIN
    SET NOCOUNT ON;  --Etkilenen satır sayısını yazdırmaz.

    IF NOT  --İnceleme durumu , notu ve inceleyen kişi durumda güncelleme yoksa devam edilmez.
    (
        UPDATE(ReviewStatus)
        OR UPDATE(ReviewNote)
        OR UPDATE(ReviewedByUserID)
    )
        RETURN;

    INSERT INTO dbo.FraudAlertReviewHistory --Uyarı inceleme geçmişi tablosuna yazılacak bilgiler.
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
        COALESCE(i.ReviewedAt, SYSDATETIME()) --Sistem tarihine göre yeni eklenenleri kullanır.
    FROM inserted AS i --Eklenen yeni satırlar.(SQL Server sağlar bu satır kümelerini)
    INNER JOIN deleted AS d --Silinen eski satırlar.(SQL Server sağlar bu satır kümelerini)
        ON d.AlertID = i.AlertID
    WHERE i.ReviewStatus <> d.ReviewStatus --Inceleme durumunda değişiklik varsa ve null değillerse geçmişe eklenir.
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
AFTER INSERT --Yeni kart satırı eklenince çalışır.
AS
BEGIN
    SET NOCOUNT ON; --Etkilenen satır sayısını yazdırmaz.

    INSERT INTO dbo.CreditCardBillingSettings --Tablyo bilgiler yazılır.
    (
        CreditCardID,
        ClosingDay,
        DueDaysAfterClosing,
        EffectiveFrom,
        UpdatedAt
    )
    SELECT
        i.CreditCardID,
        20, --Varsayılan kesim günü
        10, --Varsayılan ödeme için geçecek gün sayısı
        CONVERT(DATE, SYSDATETIME()), --Bugünün tarihi
        SYSDATETIME() -- O anın tarihi ve saati
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
SELECT  --Mevcut kartların ayarlarını tanımlar.
    cc.CreditCardID,
    20,--Varsayılan kesim günü
    10, --Varsayılan ödeme için geçecek gün sayısı
    CONVERT(DATE, SYSDATETIME()), --Bugünün tarihi
    SYSDATETIME()  -- O anın tarihi ve saati
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
AFTER INSERT, UPDATE --Yeni hesap ekleme ve veya güncelleme sonrası çalışır.
AS
BEGIN
    SET NOCOUNT ON; --Etkilenen satır sayısını yazdırmaz.

    IF NOT UPDATE(Balance) --Eğer güncelleme yoksa devam etmez.
        RETURN;

    DECLARE @Today DATE = CONVERT(DATE, SYSDATETIME());--Sadece bugünün tarihini alır.

    -- Update existing daily balance records.

    UPDATE adb --Bugün için bulunan AccountDailyBalances satırı güncellenir.
    SET
        adb.ClosingBalance = i.Balance,
        adb.RecordedAt = SYSDATETIME()
    FROM dbo.AccountDailyBalances AS adb
    INNER JOIN inserted AS i
        ON i.AccountID = adb.AccountID
    WHERE adb.BalanceDate = @Today
      AND
      (
          adb.ClosingBalance <> i.Balance --Bakiyenin gerçekten farklı olması gerekir.
      );

    -- Insert today's record for accounts without one.

    INSERT INTO dbo.AccountDailyBalances --Tabloya gerekli bilgiler eklenir.
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
            WITH (UPDLOCK, HOLDLOCK) --UPDLOCK okunan hesapta güncelleme amacıyla kilit ister,HOLDLOCK sql transactiın sonuna kadar tutulmasını sağlar.
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
AFTER INSERT, UPDATE --Yeni uyarı ekleme veya güncelleme sonrası çalışır.
AS
BEGIN
    SET NOCOUNT ON; --Etkilenen satır sayısını yazdırmaz.

    -- Update assessments for changed alerts.

    UPDATE fra --Mecvut satırı alertId ile bulur ve risk veya inceleme durumu farklıysa AssessedAt güncellenir.
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

    INSERT INTO dbo.FraudRiskAssessments --Oluşan yeni aler için tabloya yeni bir satır girilir.
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
    WHERE NOT EXISTS --Değerlendirme zaten varsa ikinci satır açılmaz.
    (
        SELECT 1
        FROM dbo.FraudRiskAssessments AS fra
            WITH (UPDLOCK, HOLDLOCK) --UPDLOCK okunan hesapta güncelleme amacıyla kilit ister,HOLDLOCK sql transactiın sonuna kadar tutulmasını sağlar.
        WHERE fra.AlertID = i.AlertID
    );
END;
GO

-- ============================================================
-- 17. BACKFILL DAILY BALANCES
--
-- Existing account balances are recorded for today.
-- ============================================================

DECLARE @Today DATE = CONVERT(DATE, SYSDATETIME()); --Sdece bugünün tarihi alınır.

UPDATE adb --Bugün ki satırda kayıtlı bakiye güncel hesaptakinden farkıysa güncellenir.
SET
    adb.ClosingBalance = a.Balance,
    adb.RecordedAt = SYSDATETIME()
FROM dbo.AccountDailyBalances AS adb
INNER JOIN dbo.Accounts AS a
    ON a.AccountID = adb.AccountID
WHERE adb.BalanceDate = @Today
  AND adb.ClosingBalance <> a.Balance;

INSERT INTO dbo.AccountDailyBalances --Tüm hesaplar için varsayılandan veriler gelir.
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
    SELECT 1 --Bugün ve o hesap için satır varsa eklenmez.
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
FROM dbo.FraudAlerts AS fa --Tabloya varsayılandan veri gelir.
WHERE NOT EXISTS
(
    SELECT 1
    FROM dbo.FraudRiskAssessments AS fra
    WHERE fra.AlertID = fa.AlertID
);
GO


-- ============================================================
-- 19. VERIFY APPLICATION PROCEDURES
-- ============================================================

SELECT  --Tüm procedure ler gösterilir.
    name AS ProcedureName,
    create_date AS CreatedAt,
    modify_date AS ModifiedAt
FROM sys.procedures
WHERE schema_id = SCHEMA_ID(N'dbo')
  AND name IN
  (  --10 beklenen ismi filtreler.
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
ORDER BY name; --Isme göre sıralar.
GO

-- ============================================================
-- 20. VERIFY TRIGGERS
-- ============================================================
--Tüm triggerlar listelenir.
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
ORDER BY t.name; --İsme göre sıralanır.
GO

-- ============================================================
-- 21. VERIFY DAILY BALANCE RECORDS
-- ============================================================
--Günlük bakiye kayıtları gösterilir (AccountDailyBalance ve accounts üzerinden birleştirilir.)
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
-- 22. VERIFY FRAUD RISK ASSESSMENTS
-- ============================================================
--Risk değerlendirmeleri gösterilir.(RdaudRiskAssessments ve FraudAlerts üzerinden ilişkilendirilir.)
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
-- 23. VERIFY EXACTLY 20 TABLES
-- ============================================================

DECLARE @TableCount INT; --Tüm tablolar başarılı oluşturulduysa kontrol edilir.

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
-- 24. FINAL SUMMARY
-- ============================================================
--Tablo sayısı kontrolleri yapılır.
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
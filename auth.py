
from core import *


class AuthMixin:
    def __init__(self):
        self.session = None

    # ========================================================
    # REGISTER
    # ========================================================

    def register(
        self,
        first,
        last,
        national_id,
        phone,
        email,
        address,
        password
    ):
        first, last = validate_name(first, last)
        national_id = validate_national_id(national_id)
        phone = validate_phone(phone)
        email = validate_email(email)
        address = validate_address(address)
        validate_password(password)

        con = connect()

        try:
            cur = con.cursor()

            check_duplicates(
                cur,
                email,
                national_id,
                phone
            )

            # Create customer
            cur.execute(
                """
                INSERT INTO dbo.Customers
                (
                    FirstName,
                    LastName,
                    NationalID,
                    Phone,
                    Email,
                    Address
                )
                OUTPUT INSERTED.CustomerID
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                first,
                last,
                national_id,
                phone,
                email,
                address
            )

            customer_id = int(cur.fetchone()[0])

            # Create login user and retrieve UserID
            cur.execute(
                """
                INSERT INTO dbo.Users
                (
                    CustomerID,
                    Email,
                    PasswordHash,
                    Role
                )
                OUTPUT INSERTED.UserID
                VALUES (?, ?, ?, 'Customer')
                """,
                customer_id,
                email,
                HASHER.hash(password)
            )

            user_id = int(cur.fetchone()[0])

            # Audit with the newly created UserID
            audit(
                cur,
                "REGISTER",
                "Customer",
                customer_id,
                "Customer registered",
                user_id=user_id
            )

            con.commit()
            return customer_id

        except pyodbc.IntegrityError as error:
            con.rollback()
            raise duplicate_error(error) from error

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

    # ========================================================
    # LOGIN
    # ========================================================

    def login(self, email, password):
        email = email.strip().lower()
        con = connect()

        try:
            cur = con.cursor()

            user = cur.execute(
                """
                SELECT
                    u.UserID,
                    u.CustomerID,
                    u.Email,
                    u.PasswordHash,
                    u.Role
                FROM dbo.Users AS u
                LEFT JOIN dbo.Customers AS c
                    ON c.CustomerID = u.CustomerID
                WHERE u.Email = ?
                  AND u.IsActive = 1
                  AND
                  (
                      u.Role = 'Admin'
                      OR
                      (
                          u.Role = 'Customer'
                          AND c.IsActive = 1
                      )
                  )
                """,
                email
            ).fetchone()

            if user is None:
                raise ValueError(
                    "Invalid email or password."
                )

            try:
                HASHER.verify(
                    user.PasswordHash,
                    password
                )

            except (
                VerifyMismatchError,
                VerificationError,
                InvalidHashError,
                ValueError,
                TypeError
            ):
                raise ValueError(
                    "Invalid email or password."
                )

            # Update successful login timestamp
            cur.execute(
                """
                UPDATE dbo.Users
                SET LastLoginAt = SYSDATETIME()
                WHERE UserID = ?
                """,
                user.UserID
            )

            # Record successful login
            audit(
                cur,
                "LOGIN",
                "Users",
                int(user.UserID),
                "User signed in successfully",
                user_id=int(user.UserID)
            )

            con.commit()

            self.session = {
                "user_id": int(user.UserID),
                "customer_id": (
                    int(user.CustomerID)
                    if user.CustomerID is not None
                    else None
                ),
                "email": user.Email,
                "role": user.Role
            }

            return self.session.copy()

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

    # ========================================================
    # LOGOUT
    # ========================================================

    def logout(self):
        session = self.session

        if session is None:
            return

        # Clear the local session immediately.
        self.session = None

        # Record explicit logout.
        # A database error should not restore the session.
        con = connect()

        try:
            cur = con.cursor()

            audit(
                cur,
                "LOGOUT",
                "Users",
                session["user_id"],
                "User signed out",
                user_id=session["user_id"]
            )

            con.commit()

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

    # ========================================================
    # REQUIRE LOGIN
    # ========================================================

    def require_login(self):
        if not self.session:
            raise PermissionError(
                "Please sign in first."
            )

        con = connect()

        try:
            row = con.cursor().execute(
                """
                SELECT
                    u.CustomerID,
                    u.Role
                FROM dbo.Users AS u
                LEFT JOIN dbo.Customers AS c
                    ON c.CustomerID = u.CustomerID
                WHERE u.UserID = ?
                  AND u.IsActive = 1
                  AND
                  (
                      u.Role = 'Admin'
                      OR
                      (
                          u.Role = 'Customer'
                          AND c.IsActive = 1
                      )
                  )
                """,
                self.session["user_id"]
            ).fetchone()

            if (
                row is None
                or row.Role != self.session["role"]
                or row.CustomerID != self.session["customer_id"]
            ):
                # Clear invalid session without requiring
                # another database connection.
                self.session = None

                raise PermissionError(
                    "Session is no longer valid."
                )

            return self.session

        finally:
            con.close()

    # ========================================================
    # REQUIRE ADMIN
    # ========================================================

    def require_admin(self):
        session = self.require_login()

        if session["role"] != "Admin":
            raise PermissionError(
                "Admin access required."
            )

        return session

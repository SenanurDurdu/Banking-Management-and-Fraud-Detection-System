
import os
import re
import secrets
import string
from decimal import Decimal, InvalidOperation
from tkinter import ttk, messagebox

import customtkinter as ctk
import pyodbc

from argon2 import PasswordHasher
from argon2.exceptions import (
    VerifyMismatchError,
    VerificationError,
    InvalidHashError
)

# ============================================================
# SETTINGS
# ============================================================

DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_NAME = os.getenv("DB_NAME", "BankingFraudDB_Test")
DB_DRIVER = os.getenv(
    "DB_DRIVER",
    "ODBC Driver 18 for SQL Server"
)

DB_TRUSTED = os.getenv(
    "DB_TRUSTED",
    "no"
).strip().lower()

DB_USERNAME = os.getenv("DB_USERNAME", "sa")

# Database password must be supplied externally.
DB_PASSWORD = os.getenv("DB_PASSWORD", "Sd-135798834")

ADMIN_EMAIL = os.getenv(
    "ADMIN_EMAIL",
    "admin@gmail.com"
).strip().lower()

# Used only when creating the initial administrator.
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin-123")

# Never reset the existing administrator password
# automatically on application startup.
RESET_DEMO_ADMIN_PASSWORD = False

HASHER = PasswordHasher()


# ============================================================
# UI COLORS
# ============================================================

BG = "#0B1220"
SIDEBAR = "#111C30"
CARD = "#17243B"
BLUE = "#2563EB"
BLUE_HOVER = "#1D4ED8"
WHITE = "#F8FAFC"
MUTED = "#94A3B8"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def connect():
    if DB_TRUSTED in ("yes", "true", "1"):
        auth = "Trusted_Connection=yes;"

    else:
        if not DB_PASSWORD:
            raise RuntimeError(
                "DB_PASSWORD environment variable is missing. "
                "Set DB_PASSWORD in your environment or use "
                "DB_TRUSTED=yes for Windows Authentication."
            )

        auth = (
            f"UID={DB_USERNAME};"
            f"PWD={DB_PASSWORD};"
        )

    connection_string = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"{auth}"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(
        connection_string,
        timeout=5,
        autocommit=False
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_email(value):
    email = value.strip().lower()

    if len(email) > 120 or not re.fullmatch(
        r"[a-z0-9](?:[a-z0-9._+]*[a-z0-9])?@gmail\.com",
        email
    ):
        raise ValueError(
            "Only valid Gmail addresses (@gmail.com) "
            "are allowed."
        )

    if ".." in email:
        raise ValueError(
            "Please enter a valid Gmail address."
        )

    return email


def validate_national_id(value):
    value = value.strip()

    if not (
        len(value) == 11
        and value.isascii()
        and value.isdigit()
    ):
        raise ValueError(
            "National ID must contain exactly 11 digits."
        )

    return value


def validate_phone(value):
    value = value.strip()

    if not (
        len(value) == 11
        and value.isascii()
        and value.isdigit()
    ):
        raise ValueError(
            "Phone number must contain exactly 11 digits."
        )

    return value


def validate_name(first, last):
    first = first.strip()
    last = last.strip()

    if not first or not last:
        raise ValueError(
            "First name and last name are required."
        )

    if len(first) > 60 or len(last) > 60:
        raise ValueError(
            "First name or last name is too long."
        )

    return first, last


def validate_address(value):
    address = value.strip()

    if not address:
        raise ValueError(
            "Address is required."
        )

    if len(address) > 255:
        raise ValueError(
            "Address is too long."
        )

    return address


def validate_password(value):
    if not isinstance(value, str):
        raise ValueError(
            "Password must be a string."
        )

    if len(value) < 8:
        raise ValueError(
            "Password must contain at least 8 characters."
        )

    if not re.search(r"[A-Z]", value):
        raise ValueError(
            "Password must contain an uppercase letter."
        )

    if not re.search(r"[a-z]", value):
        raise ValueError(
            "Password must contain a lowercase letter."
        )

    if not re.search(r"[0-9]", value):
        raise ValueError(
            "Password must contain a number."
        )

    return True


# ============================================================
# MONEY VALIDATION
# ============================================================

def money(value, allow_zero=False):
    try:
        amount = Decimal(
            str(value).strip().replace(",", ".")
        )

    except (InvalidOperation, ValueError):
        raise ValueError(
            "Please enter a valid amount."
        )

    if not amount.is_finite():
        raise ValueError(
            "Please enter a valid amount."
        )

    if amount < 0 or (
        amount == 0 and not allow_zero
    ):
        if allow_zero:
            raise ValueError(
                "Amount cannot be negative."
            )

        raise ValueError(
            "Amount must be greater than zero."
        )

    if amount.as_tuple().exponent < -2:
        raise ValueError(
            "Maximum two decimal places are allowed."
        )

    if amount >= Decimal("10000000000000000"):
        raise ValueError(
            "Amount is too large."
        )

    return amount.quantize(
        Decimal("0.01")
    )


# ============================================================
# AUDIT LOGS
# ============================================================

def audit(
    cursor,
    action,
    entity,
    entity_id,
    description,
    user_id=None
):
    """
    Writes an audit record using the current DB transaction.

    user_id:
        ID of the user who performed the action.

        None is permitted for system-generated events
        and older calls that do not pass a user ID.

    Requires AuditLogs.UserID to exist in the database.
    """

    if user_id is not None:
        try:
            user_id = int(user_id)

        except (ValueError, TypeError):
            raise ValueError(
                "Invalid audit UserID."
            )

        if user_id <= 0:
            raise ValueError(
                "Invalid audit UserID."
            )

    cursor.execute(
        """
        INSERT INTO dbo.AuditLogs
        (
            ActionType,
            EntityName,
            EntityID,
            Description,
            UserID
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        action,
        entity,
        entity_id,
        description,
        user_id
    )


# ============================================================
# DUPLICATE CHECK
# ============================================================

def check_duplicates(
    cursor,
    email,
    national_id,
    phone
):
    if cursor.execute(
        """
        SELECT TOP 1 1
        FROM
        (
            SELECT Email
            FROM dbo.Customers

            UNION ALL

            SELECT Email
            FROM dbo.Users
        ) AS E
        WHERE Email = ?
        """,
        email
    ).fetchone():

        raise ValueError(
            "This email address is already registered. "
            "Please use a different email address."
        )

    if cursor.execute(
        """
        SELECT 1
        FROM dbo.Customers
        WHERE NationalID = ?
        """,
        national_id
    ).fetchone():

        raise ValueError(
            "This National ID is already registered. "
            "Please use a different National ID."
        )

    if cursor.execute(
        """
        SELECT 1
        FROM dbo.Customers
        WHERE Phone = ?
        """,
        phone
    ).fetchone():

        raise ValueError(
            "This phone number is already registered. "
            "Please use a different phone number."
        )


# ============================================================
# DUPLICATE ERROR HANDLING
# ============================================================

def duplicate_error(error):
    text = str(error).lower()

    if (
        "phone" in text
        or "ux_customers_phone" in text
    ):
        return ValueError(
            "This phone number is already registered. "
            "Please use a different phone number."
        )

    if "nationalid" in text:
        return ValueError(
            "This National ID is already registered. "
            "Please use a different National ID."
        )

    if "email" in text:
        return ValueError(
            "This email address is already registered. "
            "Please use a different email address."
        )

    return ValueError(
        "Registration details already exist. "
        "Check your email, National ID "
        "and phone number."
    )


# ============================================================
# INITIAL ADMIN SETUP
# ============================================================

def create_initial_admin():
    """
    Creates the initial Admin account if needed.

    Existing Admin:
        Password is not reset.
        Account is not automatically reactivated.

    New Admin:
        ADMIN_PASSWORD environment variable is required.
        Password must satisfy validate_password().

    This function does not delete existing records.
    """

    con = connect()

    try:
        cur = con.cursor()

        # ----------------------------------------------------
        # 1. CHECK EXISTING ADMIN EMAIL
        # ----------------------------------------------------

        existing = cur.execute(
            """
            SELECT
                UserID,
                Role
            FROM dbo.Users
            WHERE Email = ?
            """,
            ADMIN_EMAIL
        ).fetchone()

        if existing:
            if existing.Role != "Admin":
                raise RuntimeError(
                    "The configured Admin email is "
                    "already used by a customer."
                )

            # Do not reset passwords on startup.
            # Do not reactivate a disabled Admin.
            return

        # ----------------------------------------------------
        # 2. CHECK LEGACY ADMIN
        # ----------------------------------------------------

        old = cur.execute(
            """
            SELECT UserID
            FROM dbo.Users
            WHERE Email = ?
              AND Role = 'Admin'
            """,
            "admin@banking.com"
        ).fetchone()

        # ----------------------------------------------------
        # 3. VALIDATE INITIAL ADMIN PASSWORD
        # ----------------------------------------------------

        if not ADMIN_PASSWORD:
            raise RuntimeError(
                "ADMIN_PASSWORD environment variable "
                "is required to configure the initial Admin."
            )

        validate_password(ADMIN_PASSWORD)

        password_hash = HASHER.hash(
            ADMIN_PASSWORD
        )

        # ----------------------------------------------------
        # 4. MIGRATE LEGACY ADMIN OR CREATE NEW ADMIN
        # ----------------------------------------------------

        if old:
            cur.execute(
                """
                UPDATE dbo.Users
                SET
                    Email = ?,
                    PasswordHash = ?
                WHERE UserID = ?
                  AND Role = 'Admin'
                """,
                ADMIN_EMAIL,
                password_hash,
                old.UserID
            )

            admin_id = int(
                old.UserID
            )

            description = (
                "Legacy administrator email "
                "and password configured"
            )

        else:
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
                VALUES
                (
                    NULL,
                    ?,
                    ?,
                    'Admin'
                )
                """,
                ADMIN_EMAIL,
                password_hash
            )

            admin_id = int(
                cur.fetchone()[0]
            )

            description = (
                "Initial administrator created"
            )

        # ----------------------------------------------------
        # 5. AUDIT
        # ----------------------------------------------------

        audit(
            cur,
            "ADMIN_SETUP",
            "Users",
            admin_id,
            description,
            user_id=admin_id
        )

        con.commit()

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()

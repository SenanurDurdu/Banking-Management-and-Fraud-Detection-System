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
DB_NAME = os.getenv("DB_NAME", "BankingFraudDB")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
DB_TRUSTED = os.getenv("DB_TRUSTED", "no").lower()
DB_USERNAME = os.getenv("DB_USERNAME", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "SİZ KENDİ ŞİFRENİZİ GİRİN")

ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "Admin_password"

RESET_DEMO_ADMIN_PASSWORD = True

HASHER = PasswordHasher()

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
    if DB_TRUSTED == "yes":
        auth = "Trusted_Connection=yes;"
    else:
        if not DB_PASSWORD:
            raise RuntimeError(
                "DB_PASSWORD environment variable is missing. "
                "Set it in PyCharm or use DB_TRUSTED=yes "
                "for Windows Authentication."
            )

        auth = f"UID={DB_USERNAME};PWD={DB_PASSWORD};"

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
            "Only valid Gmail addresses (@gmail.com) are allowed."
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
    first, last = first.strip(), last.strip()

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
        raise ValueError("Address is required.")

    if len(address) > 255:
        raise ValueError("Address is too long.")

    return address


def validate_password(value):
    if len(value) < 4:
        raise ValueError(
            "Password must contain at least 4 characters."
        )


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

    if amount < 0 or (amount == 0 and not allow_zero):
        raise ValueError(
            "Amount cannot be negative."
            if allow_zero
            else "Amount must be greater than zero."
        )

    if amount.as_tuple().exponent < -2:
        raise ValueError(
            "Maximum two decimal places are allowed."
        )

    if amount >= Decimal("10000000000000000"):
        raise ValueError(
            "Amount is too large."
        )

    return amount.quantize(Decimal("0.01"))


# ============================================================
# AUDIT LOGS
# ============================================================

def audit(cursor, action, entity, entity_id, description):
    cursor.execute(
        """
        INSERT INTO AuditLogs
            (ActionType, EntityName, EntityID, Description)
        VALUES (?, ?, ?, ?)
        """,
        action,
        entity,
        entity_id,
        description
    )


# ============================================================
# DUPLICATE CHECK
# ============================================================

def check_duplicates(cursor, email, national_id, phone):
    if cursor.execute(
        """
        SELECT TOP 1 1
        FROM (
            SELECT Email FROM Customers
            UNION ALL
            SELECT Email FROM Users
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
        "SELECT 1 FROM Customers WHERE NationalID = ?",
        national_id
    ).fetchone():
        raise ValueError(
            "This National ID is already registered. "
            "Please use a different National ID."
        )

    if cursor.execute(
        "SELECT 1 FROM Customers WHERE Phone = ?",
        phone
    ).fetchone():
        raise ValueError(
            "This phone number is already registered. "
            "Please use a different phone number."
        )


def duplicate_error(error):
    text = str(error).lower()

    if "phone" in text or "ux_customers_phone" in text:
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
        "Check your email, National ID and phone number."
    )


# ============================================================
# ADMIN SETUP
# ============================================================

def create_initial_admin():
    con = connect()

    try:
        cur = con.cursor()

        existing = cur.execute(
            "SELECT UserID, Role FROM Users WHERE Email = ?",
            ADMIN_EMAIL
        ).fetchone()

        if existing:
            if existing.Role != "Admin":
                raise RuntimeError(
                    "admin@gmail.com is already used by a customer."
                )

            if RESET_DEMO_ADMIN_PASSWORD:
                cur.execute(
                    """
                    UPDATE Users
                    SET PasswordHash = ?, IsActive = 1
                    WHERE UserID = ? AND Role = 'Admin'
                    """,
                    HASHER.hash(ADMIN_PASSWORD),
                    existing.UserID
                )

                con.commit()

            return

        old = cur.execute(
            """
            SELECT UserID
            FROM Users
            WHERE Email = 'admin@banking.com'
              AND Role = 'Admin'
            """
        ).fetchone()

        password_hash = HASHER.hash(ADMIN_PASSWORD)

        if old:
            cur.execute(
                """
                UPDATE Users
                SET Email = ?, PasswordHash = ?, IsActive = 1
                WHERE UserID = ?
                """,
                ADMIN_EMAIL,
                password_hash,
                old.UserID
            )

            admin_id = int(old.UserID)

        else:
            cur.execute(
                """
                INSERT INTO Users
                    (CustomerID, Email, PasswordHash, Role)
                OUTPUT INSERTED.UserID
                VALUES (NULL, ?, ?, 'Admin')
                """,
                ADMIN_EMAIL,
                password_hash
            )

            admin_id = int(cur.fetchone()[0])

        audit(
            cur,
            "ADMIN_SETUP",
            "Users",
            admin_id,
            "Demo administrator configured"
        )

        con.commit()

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()
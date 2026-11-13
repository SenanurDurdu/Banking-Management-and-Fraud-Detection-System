
from core import *


class CustomersMixin:
    def customers(self):
        self.require_admin()
        con = connect()

        try:
            return con.cursor().execute(
                """
                SELECT CustomerID, FirstName, LastName,
                       NationalID, Phone, Email,
                       Address, IsActive
                FROM Customers
                ORDER BY CustomerID DESC
                """
            ).fetchall()

        finally:
            con.close()

    def customer_choices(self):
        self.require_admin()
        con = connect()

        try:
            return con.cursor().execute(
                """
                SELECT CustomerID, FirstName, LastName
                FROM Customers
                WHERE IsActive = 1
                ORDER BY CustomerID
                """
            ).fetchall()

        finally:
            con.close()

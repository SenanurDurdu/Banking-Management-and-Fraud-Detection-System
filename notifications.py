
from core import connect, audit


class NotificationsMixin:

    # ========================================================
    # CUSTOMER - VIEW NOTIFICATIONS
    # ========================================================

    def notifications(self):
        session = self.require_login()

        if session["role"] != "Customer":
            raise PermissionError(
                "Only customers can view notifications."
            )

        con = connect()

        try:
            cur = con.cursor()

            return cur.execute(
                """
                SELECT
                    NotificationID,
                    Title,
                    Message,
                    NotificationType,
                    IsRead,
                    CreatedAt
                FROM dbo.Notifications
                WHERE CustomerID = ?
                ORDER BY
                    CreatedAt DESC,
                    NotificationID DESC
                """,
                session["customer_id"]
            ).fetchall()

        finally:
            con.close()

    # ========================================================
    # CUSTOMER - UNREAD NOTIFICATION COUNT
    # ========================================================

    def unread_notification_count(self):
        session = self.require_login()

        if session["role"] != "Customer":
            raise PermissionError(
                "Only customers can view notifications."
            )

        con = connect()

        try:
            cur = con.cursor()

            row = cur.execute(
                """
                SELECT COUNT(*)
                FROM dbo.Notifications
                WHERE CustomerID = ?
                  AND IsRead = 0
                """,
                session["customer_id"]
            ).fetchone()

            return int(row[0])

        finally:
            con.close()

    # ========================================================
    # CUSTOMER - MARK ONE NOTIFICATION AS READ
    # ========================================================

    def mark_notification_read(self, notification_id):
        session = self.require_login()

        if session["role"] != "Customer":
            raise PermissionError(
                "Only customers can update notifications."
            )

        try:
            notification_id = int(notification_id)

            if notification_id <= 0:
                raise ValueError()

        except (ValueError, TypeError):
            raise ValueError(
                "Invalid notification ID."
            )

        con = connect()

        try:
            cur = con.cursor()

            cur.execute(
                """
                UPDATE dbo.Notifications
                SET IsRead = 1
                WHERE NotificationID = ?
                  AND CustomerID = ?
                """,
                notification_id,
                session["customer_id"]
            )

            if cur.rowcount != 1:
                raise ValueError(
                    "Notification not found."
                )

            con.commit()
            return True

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

    # ========================================================
    # CUSTOMER - MARK ALL NOTIFICATIONS AS READ
    # ========================================================

    def mark_all_notifications_read(self):
        session = self.require_login()

        if session["role"] != "Customer":
            raise PermissionError(
                "Only customers can update notifications."
            )

        con = connect()

        try:
            cur = con.cursor()

            cur.execute(
                """
                UPDATE dbo.Notifications
                SET IsRead = 1
                WHERE CustomerID = ?
                  AND IsRead = 0
                """,
                session["customer_id"]
            )

            updated_count = cur.rowcount
            con.commit()

            return updated_count

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

    # ========================================================
    # INTERNAL - FIND CUSTOMER PHONE COLUMN
    # ========================================================

    def _announcement_phone_column(self, cur):
        cur.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo'
              AND TABLE_NAME = 'Customers'
            """
        )

        columns = {
            str(row[0]).lower(): str(row[0])
            for row in cur.fetchall()
        }

        candidates = (
            "Phone",
            "PhoneNumber",
            "MobilePhone",
            "PhoneNo",
            "MobileNumber",
            "Telephone"
        )

        for candidate in candidates:
            found = columns.get(candidate.lower())

            if found:
                return "[" + found.replace("]", "]]") + "]"

        raise RuntimeError(
            "No supported phone column was found in "
            "dbo.Customers. Check the Customers table schema."
        )

    # ========================================================
    # ADMIN - SEARCH CUSTOMERS BY PHONE
    # ========================================================

    def search_announcement_customers(
        self,
        phone="",
        page=1,
        page_size=25
    ):
        self.require_admin()

        phone = str(phone or "").strip()

        try:
            page = int(page)
            page_size = int(page_size)

        except (ValueError, TypeError):
            raise ValueError(
                "Invalid pagination parameters."
            )

        if page < 1:
            raise ValueError(
                "Page must be positive."
            )

        if page_size not in (10, 25, 50):
            raise ValueError(
                "Page size must be 10, 25 or 50."
            )

        if len(phone) > 30:
            raise ValueError(
                "Phone search cannot exceed 30 characters."
            )

        # Escape special LIKE characters.
        escaped = (
            phone
            .replace("[", "[[]")
            .replace("%", "[%]")
            .replace("_", "[_]")
        )

        pattern = escaped + "%"
        offset = (page - 1) * page_size

        con = connect()

        try:
            cur = con.cursor()

            phone_column = self._announcement_phone_column(
                cur
            )

            count_sql = f"""
                SELECT COUNT(*)
                FROM dbo.Customers
                WHERE IsActive = 1
                  AND (
                      ? = ''
                      OR {phone_column} LIKE ?
                  )
            """

            cur.execute(
                count_sql,
                phone,
                pattern
            )

            total = int(cur.fetchone()[0])

            data_sql = f"""
                SELECT
                    CustomerID,
                    FirstName,
                    LastName,
                    {phone_column} AS PhoneNumber
                FROM dbo.Customers
                WHERE IsActive = 1
                  AND (
                      ? = ''
                      OR {phone_column} LIKE ?
                  )
                ORDER BY CustomerID DESC
                OFFSET ? ROWS
                FETCH NEXT ? ROWS ONLY
            """

            cur.execute(
                data_sql,
                phone,
                pattern,
                offset,
                page_size
            )

            rows = cur.fetchall()

            total_pages = max(
                1,
                (total + page_size - 1) // page_size
            )

            return {
                "rows": rows,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }

        finally:
            con.close()

    # ========================================================
    # ADMIN - COUNT ACTIVE CUSTOMERS
    # ========================================================

    def announcement_customer_count(self):
        self.require_admin()

        con = connect()

        try:
            cur = con.cursor()

            cur.execute(
                """
                SELECT COUNT(*)
                FROM dbo.Customers
                WHERE IsActive = 1
                """
            )

            return int(cur.fetchone()[0])

        finally:
            con.close()

    # ========================================================
    # ADMIN - SEND ANNOUNCEMENT
    # ========================================================

    def send_announcement(
        self,
        title,
        message,
        customer_id=None
    ):
        session = self.require_login()

        if session["role"] != "Admin":
            raise PermissionError(
                "Only admins can send announcements."
            )

        title = str(title or "").strip()
        message = str(message or "").strip()

        if not title or not message:
            raise ValueError(
                "Title and message are required."
            )

        if len(title) > 150:
            raise ValueError(
                "Title cannot exceed 150 characters."
            )

        if len(message) > 1000:
            raise ValueError(
                "Message cannot exceed 1000 characters."
            )

        if customer_id is not None:
            try:
                customer_id = int(customer_id)

                if customer_id <= 0:
                    raise ValueError()

            except (ValueError, TypeError):
                raise ValueError(
                    "Invalid Customer ID."
                )

        con = connect()

        try:
            cur = con.cursor()

            if customer_id is None:

                # --------------------------------------------
                # SEND TO ALL ACTIVE CUSTOMERS
                # --------------------------------------------

                cur.execute(
                    """
                    INSERT INTO dbo.Notifications
                    (
                        CustomerID,
                        Title,
                        Message,
                        NotificationType
                    )
                    SELECT
                        CustomerID,
                        ?,
                        ?,
                        'Announcement'
                    FROM dbo.Customers
                    WHERE IsActive = 1
                    """,
                    title,
                    message
                )

                sent_count = cur.rowcount

            else:

                # --------------------------------------------
                # SEND TO ONE ACTIVE CUSTOMER
                # --------------------------------------------

                customer = cur.execute(
                    """
                    SELECT CustomerID
                    FROM dbo.Customers
                    WHERE CustomerID = ?
                      AND IsActive = 1
                    """,
                    customer_id
                ).fetchone()

                if not customer:
                    raise ValueError(
                        "Customer not found or inactive."
                    )

                cur.execute(
                    """
                    INSERT INTO dbo.Notifications
                    (
                        CustomerID,
                        Title,
                        Message,
                        NotificationType
                    )
                    VALUES (?, ?, ?, 'Announcement')
                    """,
                    customer_id,
                    title,
                    message
                )

                sent_count = cur.rowcount

            con.commit()
            return sent_count

        except Exception:
            con.rollback()
            raise

        finally:
            con.close()

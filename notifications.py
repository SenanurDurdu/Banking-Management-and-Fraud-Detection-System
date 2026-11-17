
from core import *


class NotificationsMixin:

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
                ORDER BY CreatedAt DESC, NotificationID DESC
                """,
                session["customer_id"]
            ).fetchall()

        finally:
            con.close()

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

    def mark_notification_read(self, notification_id):
        session = self.require_login()

        if session["role"] != "Customer":
            raise PermissionError(
                "Only customers can update notifications."
            )

        notification_id = int(notification_id)

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

        title = str(title).strip()
        message = str(message).strip()

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

        con = connect()

        try:
            cur = con.cursor()

            if customer_id is None:
                # Send to all active customers.
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

            else:
                customer_id = int(customer_id)

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

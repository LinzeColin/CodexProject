from __future__ import annotations

import unittest

from arxiv_daily_push.notifications import EmailNotification
from arxiv_daily_push.smtp_delivery import deliver_notification


class SmtpDeliveryIdentityTests(unittest.TestCase):
    def test_delivery_id_is_stable_for_same_revision_and_changes_for_content_revision(self) -> None:
        notification = EmailNotification(
            recipient="linzezhang35@gmail.com",
            subject="20260702 -- arXiv Daily Push -- B1 -- Test",
            body="same body",
            html_body="<p>same body</p>",
        )
        first = deliver_notification(notification, generated_at="2026-07-02T06:00:00+10:00")
        retry = deliver_notification(notification, generated_at="2026-07-02T06:00:00+10:00")
        revised = deliver_notification(
            EmailNotification(
                recipient=notification.recipient,
                subject=notification.subject,
                body="changed body",
                html_body=notification.html_body,
            ),
            generated_at="2026-07-02T06:00:00+10:00",
        )

        self.assertEqual(first["delivery_id"], retry["delivery_id"])
        self.assertNotEqual(first["delivery_id"], revised["delivery_id"])

    def test_real_message_includes_standard_message_id_when_mocked_send_is_allowed(self) -> None:
        messages = []

        class FakeSmtp:
            def __init__(self, *_args, **_kwargs) -> None:
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_args) -> None:
                return None

            def starttls(self) -> None:
                return None

            def login(self, _username: str, _password: str) -> None:
                return None

            def send_message(self, message):
                messages.append(message)
                return {}

        notification = EmailNotification(
            recipient="linzezhang35@gmail.com",
            subject="20260702 -- arXiv Daily Push -- B1 -- Test",
            body="body",
            html_body="",
        )
        report = deliver_notification(
            notification,
            generated_at="2026-07-02T06:00:00+10:00",
            allow_send=True,
            smtp_factory=FakeSmtp,
            env={
                "ADP_SMTP_HOST": "smtp.example.com",
                "ADP_SMTP_PORT": "587",
                "ADP_SMTP_USERNAME": "sender@example.com",
                "ADP_SMTP_PASSWORD": "secret",
            },
        )

        self.assertEqual(report["status"], "sent")
        self.assertEqual(messages[0]["X-ADP-Delivery-ID"], report["delivery_id"])
        self.assertEqual(messages[0]["Message-ID"], f"<{report['delivery_id'].replace(':', '-')}@arxiv-daily-push.local>")


if __name__ == "__main__":
    unittest.main()

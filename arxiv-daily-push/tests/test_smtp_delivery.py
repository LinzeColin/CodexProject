from __future__ import annotations

import unittest

from arxiv_daily_push.notifications import EmailNotification
from arxiv_daily_push.smtp_delivery import deliver_notification, validate_smtp_delivery_report


class SmtpDeliveryIdentityTests(unittest.TestCase):
    def test_delivery_id_is_stable_for_same_revision_and_changes_for_content_revision(self) -> None:
        notification = EmailNotification(
            recipient="linzezhang35@gmail.com",
            subject="20260702 -- arXiv Daily Push -- B1 -- Test",
            body="same body",
            html_body="<p>same body</p>",
        )
        first = deliver_notification(
            notification,
            generated_at="2026-07-02T06:00:00+10:00",
            cycle_id="2026-07-02",
            product_id="M1",
        )
        retry = deliver_notification(
            notification,
            generated_at="2026-07-02T06:00:00+10:00",
            cycle_id="2026-07-02",
            product_id="M1",
        )
        revised = deliver_notification(
            EmailNotification(
                recipient=notification.recipient,
                subject=notification.subject,
                body="changed body",
                html_body=notification.html_body,
            ),
            generated_at="2026-07-02T06:00:00+10:00",
            cycle_id="2026-07-02",
            product_id="M1",
        )

        self.assertEqual(first["mail_key"], retry["mail_key"])
        self.assertEqual(first["content_revision_id"], retry["content_revision_id"])
        self.assertEqual(first["message_id"], retry["message_id"])
        self.assertEqual(first["delivery_id"], retry["delivery_id"])
        self.assertEqual(first["mail_key"], revised["mail_key"])
        self.assertNotEqual(first["content_revision_id"], revised["content_revision_id"])
        self.assertNotEqual(first["message_id"], revised["message_id"])
        self.assertNotEqual(first["delivery_id"], revised["delivery_id"])
        self.assertEqual(first["message"]["mail_key_components"], {
            "cycle_id": "2026-07-02",
            "product_id": "M1",
            "recipient": "linzezhang35@gmail.com",
        })
        self.assertIn("supersede_or_resend", first["message"]["resend_policy"])
        self.assertFalse(validate_smtp_delivery_report(first))

    def test_mail_key_changes_by_product_but_content_revision_stays_immutable(self) -> None:
        notification = EmailNotification(
            recipient="linzezhang35@gmail.com",
            subject="20260702 -- arXiv Daily Push -- B1 -- Test",
            body="same body",
            html_body="<p>same body</p>",
        )
        m1 = deliver_notification(notification, generated_at="2026-07-02T06:00:00+10:00", cycle_id="2026-07-02", product_id="M1")
        m2 = deliver_notification(notification, generated_at="2026-07-02T06:00:00+10:00", cycle_id="2026-07-02", product_id="M2")

        self.assertNotEqual(m1["mail_key"], m2["mail_key"])
        self.assertEqual(m1["content_revision_id"], m2["content_revision_id"])
        self.assertNotEqual(m1["message_id"], m2["message_id"])

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
            cycle_id="2026-07-02",
            product_id="M1",
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
        self.assertEqual(messages[0]["X-ADP-Mail-Key"], report["mail_key"])
        self.assertEqual(messages[0]["X-ADP-Content-Revision-ID"], report["content_revision_id"])
        self.assertEqual(messages[0]["Message-ID"], report["message_id"])
        self.assertRegex(messages[0]["Message-ID"], r"^<adp-[a-f0-9]{24}@arxiv-daily-push\.local>$")
        self.assertFalse(validate_smtp_delivery_report(report))


if __name__ == "__main__":
    unittest.main()

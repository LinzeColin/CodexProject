import unittest
from email.message import EmailMessage

from arxiv_daily_push.notifications import render_email
from arxiv_daily_push.smtp_delivery import deliver_notification, validate_smtp_delivery_report


class NotificationTests(unittest.TestCase):
    def test_render_email_uses_configured_recipient_and_no_secret(self):
        email = render_email("success", "run-001", "Daily status", date="2026-06-21")
        self.assertEqual(email.recipient, "linzezhang35@gmail.com")
        self.assertIn("[arXiv Daily Push][SUCCESS][2026-06-21]", email.subject)
        self.assertIn("claim_gate:", email.body)
        self.assertNotIn("password", email.body.lower())
        self.assertNotIn("token", email.body.lower())

    def test_smtp_delivery_dry_run_does_not_require_secrets(self):
        email = render_email("success", "run-001", "Daily status", date="2026-06-21")
        report = deliver_notification(email, generated_at="2026-06-21T05:00:00+10:00", env={})

        self.assertEqual(report["status"], "dry_run")
        self.assertFalse(report["real_smtp_send_enabled"])
        self.assertFalse(report["smtp_config"]["secret_values_logged"])
        self.assertFalse(report["message"]["body_logged"])
        self.assertEqual(validate_smtp_delivery_report(report), [])

    def test_smtp_delivery_blocks_real_send_without_env(self):
        email = render_email("failure", "run-001", "Daily failed", date="2026-06-21")
        report = deliver_notification(email, generated_at="2026-06-21T05:00:00+10:00", allow_send=True, env={})

        self.assertEqual(report["status"], "blocked")
        self.assertIn("ADP_SMTP_PASSWORD", " ".join(report["blocking_reasons"]))
        self.assertEqual(validate_smtp_delivery_report(report), [])

    def test_smtp_delivery_blocks_invalid_timeout_before_smtp(self):
        email = render_email("failure", "run-001", "Daily failed", date="2026-06-21")
        env = {
            "ADP_SMTP_HOST": "smtp.example.invalid",
            "ADP_SMTP_PORT": "587",
            "ADP_SMTP_USERNAME": "sender@example.invalid",
            "ADP_SMTP_PASSWORD": "super-secret-password",
        }
        report = deliver_notification(
            email,
            generated_at="2026-06-21T05:00:00+10:00",
            allow_send=True,
            env=env,
            timeout_seconds=0,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("timeout_seconds", " ".join(report["blocking_reasons"]))
        self.assertEqual(validate_smtp_delivery_report(report), [])

    def test_smtp_delivery_sends_with_mock_smtp_without_logging_secret_values(self):
        class FakeSMTP:
            sent_messages: list[EmailMessage] = []
            logged_in = False
            tls_started = False

            def __init__(self, host, port, timeout):
                self.host = host
                self.port = port
                self.timeout = timeout

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def starttls(self):
                FakeSMTP.tls_started = True

            def login(self, username, password):
                FakeSMTP.logged_in = bool(username and password)

            def send_message(self, message):
                FakeSMTP.sent_messages.append(message)
                return {}

        env = {
            "ADP_SMTP_HOST": "smtp.example.invalid",
            "ADP_SMTP_PORT": "587",
            "ADP_SMTP_USERNAME": "sender@example.invalid",
            "ADP_SMTP_PASSWORD": "super-secret-password",
        }
        email = render_email("success", "run-001", "Daily status", date="2026-06-21")
        report = deliver_notification(
            email,
            generated_at="2026-06-21T05:00:00+10:00",
            allow_send=True,
            env=env,
            smtp_factory=FakeSMTP,
        )

        self.assertEqual(report["status"], "sent")
        self.assertTrue(FakeSMTP.tls_started)
        self.assertTrue(FakeSMTP.logged_in)
        self.assertEqual(FakeSMTP.sent_messages[0]["To"], "linzezhang35@gmail.com")
        self.assertNotIn("super-secret-password", str(report))
        self.assertEqual(validate_smtp_delivery_report(report), [])


if __name__ == "__main__":
    unittest.main()

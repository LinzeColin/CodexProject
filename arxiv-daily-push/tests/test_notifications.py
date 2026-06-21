import unittest

from arxiv_daily_push.notifications import render_email


class NotificationTests(unittest.TestCase):
    def test_render_email_uses_configured_recipient_and_no_secret(self):
        email = render_email("success", "run-001", "Daily status", date="2026-06-21")
        self.assertEqual(email.recipient, "linzezhang35@gmail.com")
        self.assertIn("[arXiv Daily Push][SUCCESS][2026-06-21]", email.subject)
        self.assertIn("claim_gate:", email.body)
        self.assertNotIn("password", email.body.lower())
        self.assertNotIn("token", email.body.lower())


if __name__ == "__main__":
    unittest.main()


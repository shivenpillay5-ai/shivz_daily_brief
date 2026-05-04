from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from daily_brief.config import EmailConfig
from daily_brief.tools.alerts import read_failure_log, send_failure_alert


class FailureAlertTests(unittest.TestCase):
    @patch("daily_brief.tools.alerts.send_email")
    def test_send_failure_alert_uses_email_configuration(self, send_email_mock) -> None:
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_use_tls=True,
            smtp_username="sender@example.com",
            smtp_password="secret",
            email_from="sender@example.com",
            email_to=["reader@example.com"],
            subject_prefix="Shivz Daily Brief",
        )

        send_failure_alert(
            config,
            brief_date=datetime(2026, 5, 4),
            log_text="attempt 1 failed\nattempt 2 failed\nattempt 3 failed",
            run_url="https://github.com/example/actions/runs/1",
        )

        send_email_mock.assert_called_once()
        args, kwargs = send_email_mock.call_args
        self.assertEqual(args[0], config)
        self.assertIn("Shivz Daily Brief failed", kwargs["subject"])
        self.assertIn("attempt 3 failed", kwargs["text_body"])
        self.assertIn("https://github.com/example/actions/runs/1", kwargs["html_body"])

    @patch("daily_brief.tools.alerts.send_email")
    def test_send_failure_alert_can_use_custom_alert_name(self, send_email_mock) -> None:
        send_failure_alert(
            _email_config(),
            brief_date=datetime(2026, 5, 4),
            log_text="failed",
            alert_name="Daily Motivation and Bible Verse",
        )

        _, kwargs = send_email_mock.call_args
        self.assertIn("Daily Motivation and Bible Verse failed", kwargs["subject"])

    def test_read_failure_log_handles_missing_path(self) -> None:
        self.assertIn("not found", read_failure_log(Path("does-not-exist.log")))

    def test_read_failure_log_reads_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            log_path = Path(folder) / "failure.log"
            log_path.write_text("failed here", encoding="utf-8")

            self.assertEqual(read_failure_log(log_path), "failed here")

def _email_config() -> EmailConfig:
    return EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_use_tls=True,
        smtp_username="sender@example.com",
        smtp_password="secret",
        email_from="sender@example.com",
        email_to=["reader@example.com"],
        subject_prefix="Shivz Daily Brief",
    )


if __name__ == "__main__":
    unittest.main()

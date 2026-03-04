"""Tests for notifications/email.py — Gmail SMTP digest sender.

All SMTP interactions are mocked. No real emails are sent in CI.
"""

import smtplib
from unittest.mock import MagicMock, patch

import pytest


SUBJECT = "Job Digest 2026-03-04 — 3 matches"
HTML_BODY = "<html><body><h1>Jobs</h1></body></html>"


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Patch settings so no real env vars are required."""
    monkeypatch.setattr("config.settings.GMAIL_ADDRESS", "sender@gmail.com")
    monkeypatch.setattr("config.settings.GMAIL_APP_PASSWORD", "app-password-16ch")
    monkeypatch.setattr("config.settings.DIGEST_EMAIL", "recipient@example.com")


class TestSendDigest:
    def _call(self, mock_smtp_ssl):
        """Helper: invoke send_digest with the standard test subject/body."""
        from notifications.email import send_digest

        send_digest(SUBJECT, HTML_BODY)
        return mock_smtp_ssl

    def test_connects_to_gmail_ssl(self):
        """send_digest connects to smtp.gmail.com on port 465 via SMTP_SSL."""
        with patch("smtplib.SMTP_SSL") as mock_ssl:
            mock_ssl.return_value.__enter__ = MagicMock(return_value=mock_ssl.return_value)
            mock_ssl.return_value.__exit__ = MagicMock(return_value=False)

            from notifications.email import send_digest
            send_digest(SUBJECT, HTML_BODY)

        mock_ssl.assert_called_once_with("smtp.gmail.com", 465)

    def test_authenticates_with_credentials(self):
        """send_digest calls server.login() with GMAIL_ADDRESS and GMAIL_APP_PASSWORD."""
        with patch("smtplib.SMTP_SSL") as mock_ssl:
            mock_server = MagicMock()
            mock_ssl.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_ssl.return_value.__exit__ = MagicMock(return_value=False)

            from notifications.email import send_digest
            send_digest(SUBJECT, HTML_BODY)

        mock_server.login.assert_called_once_with("sender@gmail.com", "app-password-16ch")

    def test_sends_to_digest_email(self):
        """send_digest calls sendmail() with DIGEST_EMAIL as the recipient."""
        with patch("smtplib.SMTP_SSL") as mock_ssl:
            mock_server = MagicMock()
            mock_ssl.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_ssl.return_value.__exit__ = MagicMock(return_value=False)

            from notifications.email import send_digest
            send_digest(SUBJECT, HTML_BODY)

        args = mock_server.sendmail.call_args[0]
        assert args[0] == "sender@gmail.com"   # from_addr
        assert args[1] == "recipient@example.com"  # to_addr

    def test_message_contains_subject_and_html(self):
        """The raw message passed to sendmail contains the subject header and HTML body."""
        with patch("smtplib.SMTP_SSL") as mock_ssl:
            mock_server = MagicMock()
            mock_ssl.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_ssl.return_value.__exit__ = MagicMock(return_value=False)

            from notifications.email import send_digest
            send_digest(SUBJECT, HTML_BODY)

        raw_message: str = mock_server.sendmail.call_args[0][2]
        # Subject may be RFC-2047 encoded; check for the "Subject:" header presence
        assert "Subject:" in raw_message
        assert "<h1>Jobs</h1>" in raw_message

    def test_smtp_exception_propagates(self):
        """SMTPException raised by the server propagates out of send_digest."""
        with patch("smtplib.SMTP_SSL") as mock_ssl:
            mock_ssl.return_value.__enter__ = MagicMock(
                side_effect=smtplib.SMTPException("auth failed")
            )
            mock_ssl.return_value.__exit__ = MagicMock(return_value=False)

            from notifications.email import send_digest

            with pytest.raises(smtplib.SMTPException):
                send_digest(SUBJECT, HTML_BODY)

"""Gmail SMTP sender for the daily job digest email.

Uses Python's built-in smtplib with SMTP_SSL to send HTML email via Gmail.
Credentials are loaded from settings (never hardcoded). No third-party
email library is required.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_digest(subject: str, html_body: str) -> None:
    """Send the HTML digest email via Gmail SMTP.

    Connects to smtp.gmail.com:465 using SSL, authenticates with
    settings.GMAIL_ADDRESS and settings.GMAIL_APP_PASSWORD, and sends
    the email to settings.DIGEST_EMAIL.

    Args:
        subject: Email subject line. Typically includes the run date and
                 count of matching jobs (e.g. "Job Digest 2026-03-03 — 5 matches").
        html_body: Full HTML string for the email body, as produced by
                   the format_report node.

    Raises:
        smtplib.SMTPException: On authentication or send failure.
        OSError: On network connectivity issues.
    """
    pass

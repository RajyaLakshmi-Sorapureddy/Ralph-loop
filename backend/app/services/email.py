import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str) -> None:
    """Send a plaintext email via SMTP using settings from the environment.

    Raises on failure; callers that must not block on email errors should catch
    and log rather than letting this propagate.
    """
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)


def send_new_request_notification(
    requester_name: str, amount: str, currency: str, category: str, request_id: int
) -> None:
    """Notify the finance team of a newly submitted request.

    Failures are logged and swallowed so they never block request creation.
    """
    subject = f"New reimbursement request #{request_id} from {requester_name}"
    body = (
        f"{requester_name} submitted a new reimbursement request.\n\n"
        f"Amount: {amount} {currency}\n"
        f"Category: {category}\n"
        f"Request reference: #{request_id}\n"
    )
    try:
        send_email(settings.finance_notification_email, subject, body)
    except Exception:
        logger.exception("Failed to send new-request notification email for request %s", request_id)


def send_status_change_notification(
    requester_email: str, request_id: int, new_status: str, reason: str | None
) -> None:
    """Notify the requester that finance changed their request's status.

    Failures are logged and swallowed so they never block the review action.
    """
    subject = f"Your reimbursement request #{request_id} was {new_status}"
    body = f"Your reimbursement request #{request_id} status is now: {new_status}\n"
    if reason:
        body += f"\nReason/comment: {reason}\n"
    try:
        send_email(requester_email, subject, body)
    except Exception:
        logger.exception("Failed to send status-change notification email for request %s", request_id)

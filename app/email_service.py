# app/email_service.py
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "no-reply@cloud-sentiment.com")
APP_BASE_URL = os.getenv(
    "APP_BASE_URL",
    "https://sentimentdockerapp.azurewebsites.net"  # change if needed
)


def send_verification_email(to_email: str, token: str):
    verify_url = f"{APP_BASE_URL}/auth/verify-email?token={token}"

    # Fallback for local/dev without SendGrid
    if not SENDGRID_API_KEY:
        print("⚠ SENDGRID_API_KEY not set. Verification link:")
        print(verify_url)
        return

    subject = "Verify your Cloud Sentiment account"
    html_content = f"""
    <p>Hi,</p>
    <p>Thank you for registering in <b>Cloud Sentiment API</b>.</p>
    <p>Please verify your email by clicking the link below:</p>
    <p><a href="{verify_url}">Verify Email</a></p>
    <p>If you did not request this, you can ignore this email.</p>
    """

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        print(f"✅ Verification email sent to {to_email}")
    except Exception as e:
        print(f"❌ Error sending verification email: {e}")
        print("Verification link:", verify_url)

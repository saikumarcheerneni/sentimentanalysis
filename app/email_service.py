# from azure.communication.email import EmailClient
# import os

# conn_str = os.getenv("AZURE_COMM_EMAIL_CONNECTION_STRING")
# sender = os.getenv("AZURE_COMM_SENDER_ADDRESS")

# client = EmailClient.from_connection_string(conn_str)


# def send_azure_email(to_email: str, subject: str, body: str):
#     message = {
#         "senderAddress": sender,
#         "recipients": {
#             "to": [{"address": to_email}]
#         },
#         "content": {
#             "subject": subject,
#             "plainText": body
#         }
#     }

#     try:
#         poller = client.begin_send(message)
#         result = poller.result()

#         message_id = result.get("id") or result.get("messageId")

#         return {
#             "status": "sent",
#             "messageId": message_id
#         }

#     except Exception as e:
#         print("Email send failed:", e)
#         return {"status": "failed", "error": str(e)}


# def send_verification_email(to_email: str, token: str):
#     subject = "Verify Your Email Address"

#     body = f"""
# Hello,

# Your verification code is:

#     {token}

# Enter this code in the app to verify your email.

# Thank you!
# Sentiment Analysis Cloud Platform
# """

#     return send_azure_email(
#         to_email=to_email,
#         subject=subject,
#         body=body
#     )
from azure.communication.email import EmailClient
import os
from urllib.parse import quote

conn_str = os.getenv("AZURE_COMM_EMAIL_CONNECTION_STRING")
sender = os.getenv("AZURE_COMM_SENDER_ADDRESS")
APP_BASE_URL = os.getenv("APP_BASE_URL")

client = EmailClient.from_connection_string(conn_str)

def send_azure_email(to_email: str, subject: str, body: str):
    message = {
        "senderAddress": sender,
        "recipients": {"to": [{"address": to_email}]},
        "content": {
            "subject": subject,
            "plainText": body
        }
    }

    try:
        poller = client.begin_send(message)
        result = poller.result()
        message_id = result.get("id") or result.get("messageId")
        return {"status": "sent", "messageId": message_id}

    except Exception as e:
        print("Email send failed:", e)
        return {"status": "failed", "error": str(e)}


def send_verification_email(to_email: str, token: str):
    subject = "Verify Your Email Address"
    token_encoded = quote(token)

    # ⬅️ Correct verification route
    verify_url = f"{APP_BASE_URL}/auth/verify-email?token={token_encoded}"

    body = f"""
Hello 👋,

Please verify your email address by clicking the link below:

🔗 Verify Email:
{verify_url}

If the link doesn't work, you can manually enter your verification code:

Verification Code:
{token}

Thank you for registering!
Sentiment Analysis Cloud Platform
"""

    return send_azure_email(
        to_email=to_email,
        subject=subject,
        body=body
    )

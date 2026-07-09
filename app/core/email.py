from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import NameEmail
from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
)

mail = FastMail(conf)


async def send_verification_email(email: str, token: str) -> None:
    verify_url = f"{settings.CLIENT_URL}/verify-token?token={token}"

    message = MessageSchema(
        subject="Verify your email — Resolution Engine",
        recipients=[NameEmail(name=email, email=email)],
        body=f"""
        <html>
          <body style="font-family: Inter, sans-serif; background: #0A0D12; color: #F9FAFB; padding: 40px;">
            <div style="max-width: 480px; margin: 0 auto; background: #111827; border: 1px solid #1F2937; border-radius: 12px; padding: 32px;">
              <h2 style="color: #F9FAFB; margin-bottom: 8px;">Verify your email</h2>
              <p style="color: #6B7280; margin-bottom: 24px;">
                Click the button below to verify your email address and activate your account.
              </p>
              <a href="{verify_url}"
                 style="display: inline-block; background: #6366F1; color: white; padding: 12px 24px;
                        border-radius: 8px; text-decoration: none; font-weight: 500;">
                Verify email
              </a>
              <p style="color: #4B5563; font-size: 12px; margin-top: 24px; font-family: monospace;">
                If you didn't create an account, ignore this email.
              </p>
            </div>
          </body>
        </html>
        """,
        subtype=MessageType.html,
    )
    try:
        await mail.send_message(message)
    except Exception:
        import traceback

        traceback.print_exc()

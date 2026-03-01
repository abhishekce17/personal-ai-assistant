import os
import logging
import asyncio
from email.message import EmailMessage
import aiosmtplib

logger = logging.getLogger(__name__)

# Strong references to pending background tasks to avoid garbage collection midway
_background_tasks = set()

class EmailService:
    @classmethod
    async def send_email_async(cls, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """
        Connects to the SMTP server and sends the email asynchronously.
        Does not block the main thread waiting for network I/O.
        """
        host = os.getenv("SMTP_HOST")
        port = os.getenv("SMTP_PORT")
        user = os.getenv("SMTP_USER")
        password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("SMTP_FROM_EMAIL", user)

        if not all([host, port, user, password]):
            logger.error("Email configuration is missing. Check SMTP variables in .env")
            return False

        message = EmailMessage()
        message["From"] = from_email
        message["To"] = to_email
        message["Subject"] = subject
        
        if is_html:
            message.add_alternative(body, subtype='html')
        else:
            message.set_content(body)

        try:
            # Assuming port 465 is SSL/TLS and 587 is STARTTLS based on common configurations
            port_num = int(port)
            await aiosmtplib.send(
                message,
                hostname=host,
                port=port_num,
                username=user,
                password=password,
                start_tls=port_num == 587,
                use_tls=port_num == 465,
            )
            logger.info(f"📧 Async email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send async email to {to_email}: {e}")
            return False

    @classmethod
    def send_email_background(cls, to_email: str, subject: str, body: str, is_html: bool = False):
        """
        Fire-and-forget wrapper. 
        Creates a background task in the current event loop to send the email.
        Returns immediately, imposing virtually no CPU load.
        """
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(cls.send_email_async(to_email, subject, body, is_html))
            
            # Keep a strong reference to prevent garbage collection before task finishes
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)
            
            logger.debug(f"📬 Scheduled background email task for {to_email}")
        except RuntimeError:
            logger.error("Cannot schedule background email: no running event loop found.")

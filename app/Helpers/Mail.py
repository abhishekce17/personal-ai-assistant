from email.header import decode_header
from dotenv import load_dotenv
from datetime import datetime, timedelta
import imaplib
import email
import os

load_dotenv()
imap_server = "imap.gmail.com"


class Mail:
    def __init__(self):
        self.__mail = imaplib.IMAP4_SSL(imap_server)
        self.__mail.login(os.getenv("EMAIL"), os.getenv("PASSWORD"))
        self.__mail.select("INBOX")

    def get_mails_by_date_range(self, since_date=None, before_date=None):
        try:
            if since_date is None and before_date is None:
                since_date = datetime.now()
                before_date = since_date + timedelta(days=1)

            elif (
                (since_date and not before_date)
                or (before_date and not since_date)
                or since_date == before_date
            ):
                if not since_date:
                    since_date = before_date
                if not before_date:
                    before_date = since_date
                before_date = before_date + timedelta(days=1)  # to include full day

            # Case 3: Both given but different → validate range
            elif since_date and before_date and since_date < before_date:
                before_date = before_date + timedelta(days=1)  # inclusive range

            else:
                return {
                    "error": "Invalid date range: 'since_date' must be less than or equal to 'before_date'"
                }

            # Format dates for IMAP
            since_str = since_date.strftime("%d-%b-%Y")
            before_str = before_date.strftime("%d-%b-%Y")

            # Perform IMAP search
            status, messages = self.__mail.search(
                None, f"SINCE {since_str} BEFORE {before_str}"
            )
            email_ids = messages[0].split()

            if not email_ids:
                return []

            headers_list = []

            for email_id in email_ids:
                status, msg_data = self.__mail.fetch(
                    email_id, "(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT)])"
                )
                if status != "OK":
                    continue

                msg = email.message_from_bytes(msg_data[0][1])
                headers_list.append(
                    {
                        "email_id": email_id.decode(),
                        "from": self.__decode_maybe(msg.get("From")),
                        "to": self.__decode_maybe(msg.get("To")),
                        "subject": self.__decode_maybe(msg.get("Subject")),
                    }
                )

            return headers_list
        except Exception as e:
            return {"error": str(e)}

    def get_full_email_by_id(self, email_id):
        try:
            status, msg_data = self.__mail.fetch(
                email_id.encode(), "(RFC822)"
            )  # encode str to bytes
            if status != "OK":
                return None

            msg = email.message_from_bytes(msg_data[0][1])

            # Extract headers
            from_email = self.__decode_maybe(msg.get("From"))
            to_email = self.__decode_maybe(msg.get("To"))
            subject = self.__decode_maybe(msg.get("Subject"))
            date = self.__decode_maybe(msg.get("Date"))

            # Extract body (text/plain or text/html)
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if (
                        content_type == "text/plain"
                        and "attachment" not in content_disposition
                    ):
                        payload = part.get_payload(decode=True)
                        if payload:
                            body += payload.decode(errors="ignore")
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body += payload.decode(errors="ignore")

            return {
                "email_id": email_id,
                "from": from_email,
                "to": to_email,
                "subject": subject,
                "date": date,
                "body": body.strip(),
            }

        except Exception as e:
            return e

    def __decode_maybe(self, header):
        if header:
            decoded, charset = decode_header(header)[0]
            if isinstance(decoded, bytes):
                return decoded.decode(charset or "utf-8", errors="ignore")
            return decoded
        return ""

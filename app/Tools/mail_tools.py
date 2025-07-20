from langchain_core.tools import tool
from datetime import datetime
from Helpers.Mail import Mail
import json

mail = Mail()


@tool
def get_todays_mail() -> str:
    """
    Fetches today's emails.

    Returns:
        A JSON list of emails with email_id, from, to, subject.
    """
    try:
        results = mail.get_mails_by_date_range()
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_mail_by_date(date_str: str) -> str:
    """
    Fetches emails from a specific date.

    Args:
        date_str: A date string in 'YYYY-MM-DD' format.

    Returns:
        A JSON list of emails with email_id, from, to, subject.
    """
    try:
        date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        results = mail.get_mails_by_date_range(since_date=date)
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_mail_by_date_range(since: str, before: str) -> str:
    """
    Fetches emails between a date range.

    Args:
        since: Start date in 'YYYY-MM-DD' format.
        before: End date in 'YYYY-MM-DD' format.

    Returns:
        A JSON list of emails with email_id, from, to, subject.
    """
    try:
        since_date = datetime.strptime(since.strip(), "%Y-%m-%d")
        before_date = datetime.strptime(before.strip(), "%Y-%m-%d")

        if since_date > before_date:
            return "Error: 'since' date must be before or equal to 'before' date."

        results = mail.get_mails_by_date_range(
            since_date=since_date, before_date=before_date
        )
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def read_mail_by_id(email_id: str) -> str:
    """
    Reads the full content of an email by its ID.

    Args:
        email_id: The IMAP email ID (as a string).

    Returns:
        A JSON object with from, to, subject, date, and body.
    """
    try:
        result = mail.get_full_email_by_id(email_id.strip())
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

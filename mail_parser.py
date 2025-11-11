import base64
from mail_reply import mail_reply
from helpers import categorize_email

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import KEYWORDS
from logger import get_logger

logger = get_logger(__name__)

def mail_parser(creds):
    """
       Checks unread messages. If there are keywords in subject of unread messages - calls mail_reply() function

       Args:
           creds: Credentials object
       """
    logger.info('Parsing unread mails')
    replied_mails = []
    ignored_mails = []
    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        results = (
            service.users().messages().list(userId="me", labelIds=["UNREAD","CATEGORY_PERSONAL"]).execute()
        )
        messages = results.get("messages", [])

        if not messages:
            logger.info('No unread messages')
            return [], []

        logger.info('Messages found: ')
        for message in messages:
            msg = (
                service.users().messages().get(userId="me", id=message["id"], format='full').execute()
            )
            message_content = msg.get("payload", {}).get("headers")
            thread_id = message["threadId"]

            # Get mail body
            if msg['payload']['mimeType'] == 'text/plain':
                body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')
            else:
                parts = msg['payload'].get('parts', [])
                body = ""
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break

            receiver = None
            references = None
            subject = None
            sender = None
            date = None

            for name in message_content:
                if name.get("name") == "From":
                    sender = name.get("value")
                if name.get("name") == "To":
                    receiver = name.get("value")
                if name.get("name") == "Message-ID":
                    references = name.get("value")
                if name.get("name") == "Subject":
                    subject = name.get("value")
                if name.get("name") == "Date":
                    date = name.get("value")
            
            category = categorize_email(subject)

            if subject and any(keyword in subject.lower() for keyword in KEYWORDS):
                if receiver:
                    logger.info(f'Mails with keywords found: {subject}')
                    reply_content = mail_reply(message["id"], receiver, references, subject, service, thread_id, body)
                    replied_mails.append({"to": receiver, "subject": subject, "reply": reply_content, "date": date, "category": category})
                    service.users().messages().modify(
                        userId='me',
                        id=thread_id,
                        body={'removeLabelIds': ['UNREAD']}
                    ).execute()
                else:
                    logger.warning(f"Could not find receiver for message with subject: {subject}. Skipping reply.")
                    ignored_mails.append({"from": sender, "subject": subject, "date": date, "category": category})
            else:
                ignored_mails.append({"from": sender, "subject": subject, "date": date, "category": category})


    except HttpError as error:
        logger.warning(f"An error occurred during parsing mails: {error}")
    
    return replied_mails, ignored_mails
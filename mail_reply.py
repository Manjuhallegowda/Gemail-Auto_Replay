import base64
from email.mime.text import MIMEText
from ai_reply import generate_ai_reply
from logger import get_logger
from googleapiclient.errors import HttpError
import config

logger = get_logger(__name__)

def mail_reply(message_id, receiver, references, subject, service, thread_id, body):
    """
       Mail reply according to given details

       Args:
           message_id: The id of the message
           receiver: Receiver email
           subject: Subject of the mail
           service: Authorized Gmail API service object
           thread_id: Thread ID
           body: Body of the mail
       """
    if config.USE_AI:
        reply_content = generate_ai_reply(body)
        if not reply_content:
            reply_content = config.MAILTEMPLATE
    else:
        reply_content = config.MAILTEMPLATE

    message = MIMEText(reply_content)
    if not subject.lower().startswith('re:'):
        message['Subject'] = f"Re: {subject}"
    else:
        message['Subject'] = subject
    message['To'] = receiver
    message['From'] = "me"

    message['In-Reply-To'] = message_id
    if references:
        message['References'] = references

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message_request = {
        'raw': encoded_message,
        'threadId': thread_id
    }
    try:
        service.users().messages().send(
            userId='me',
            body=create_message_request
        ).execute()
        logger.info(f'The automated reply was sent to: {receiver}, in a mail thread: {thread_id}')
        return reply_content

    except HttpError as error:
        logger.warning(f"An error occurred during sending reply: {error}")
        return None

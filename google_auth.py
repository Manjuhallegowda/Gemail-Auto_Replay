import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from config import SCOPES
from logger import get_logger

logger = get_logger(__name__)

def google_auth():
    """
    Authenticate with Google and return credentials.
    """
    creds = None
    
    # Check for credentials in environment variable first
    creds_json_str = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if creds_json_str:
        logger.info('Loading credentials from environment variable.')
        creds_info = json.loads(creds_json_str)
        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)

    # If not in env var, check for token.json
    elif os.path.exists("token.json"):
        logger.info('Loading credentials from token.json.')
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info('Refreshing expired credentials.')
            creds.refresh(Request())
        else:
            logger.info('No valid credentials found, starting authentication flow.')
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
            logger.info('Credentials saved to token.json.')

    return creds
import time
from googleapiclient.errors import HttpError
from google_auth import google_auth
from logger import get_logger
from mail_parser import mail_parser

logger = get_logger(__name__)

def main():
    logger.info('Script started')
    creds = google_auth()
    while True:
        try:
            mail_parser(creds)
            logger.info('Script successfully finished one cycle, waiting for 60 seconds...')
        except HttpError as error:
            logger.error(f"An HTTP error occurred: {error}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
        time.sleep(60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Script stopped by user.")
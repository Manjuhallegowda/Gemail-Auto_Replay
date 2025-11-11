import time
import json
import os
from googleapiclient.errors import HttpError
from google_auth import google_auth
from logger import get_logger
from mail_parser import mail_parser

logger = get_logger(__name__)

DATA_FILE = "data.json"
STATUS_FILE = "status.json"

def update_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump({"status": status}, f)

def main():
    logger.info('Script started')
    update_status("running")
    creds = google_auth()
    while True:
        try:
            replied_mails, ignored_mails = mail_parser(creds)

            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
            else:
                data = {"replied_mails": [], "ignored_mails": []}

            data["replied_mails"].extend(replied_mails)
            data["ignored_mails"].extend(ignored_mails)

            with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)

            logger.info('Script successfully finished one cycle, waiting for 60 seconds...')
        except HttpError as error:
            logger.error(f"An HTTP error occurred: {error}")
            update_status("stopped")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            update_status("stopped")
        time.sleep(60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Script stopped by user.")
        update_status("stopped")
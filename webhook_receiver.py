from flask import Flask,request, jsonify
from google_auth import google_auth
from logger import get_logger
from mail_parser import mail_parser
from config import SECRET_TOKEN

logger = get_logger(__name__)
app = Flask(__name__)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook_listener():
    """
    Receives webhook from Google Apps Script and starts mail auto reply.
    """
    logger.info("="*60)
    logger.info("Webhook has been received. Starting script....")
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != f"Bearer {SECRET_TOKEN}":
        logger.warning("Unauthorized webhook attempt.")
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    try:
        logger.info('Script started via webhook')
        creds = google_auth()
        mail_parser(creds)
        logger.info('Script successfully finished')
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

def main():
    """
    Server start function
    """
    logger.info("Webhook service starting....")
    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
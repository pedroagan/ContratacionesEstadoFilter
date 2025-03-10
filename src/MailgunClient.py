import logging

import requests
import traceback

_logger = logging.getLogger("alertmanager")

def send_email(config, attachment, text_email):
    text_subject = config['EMAIL_MSG']['EMAIL_SUBJECT']
    to_email = config['EMAIL_CONF']['EMAIL_TO']
    mailgun_url = config['MAILGUN_CONF']['MAILGUN_URL']
    mailgun_api_key = config['MAILGUN_CONF']['MAILGUN_API_KEY']
    mailgun_from = config['MAILGUN_CONF']['MAILGUN_FROM']
    # Send email
    try:
        result = requests.post(
            mailgun_url,
            auth=("api", mailgun_api_key),
            files=[("attachment", (attachment, open(attachment, "rb")))],
            data={"from": mailgun_from,
                "to": to_email,
                "subject": text_subject,
                "text": text_email})
        
        if result.status_code != 200:
            _logger.error("Error sending email: " + result.text)
            _logger.debug(traceback.format_exc())
        else:
            _logger.info(f"Email sent successfully to {to_email}")
        
    except Exception as e:
        _logger.error("Error sending email: " + str(e))
        _logger.debug(traceback.format_exc())
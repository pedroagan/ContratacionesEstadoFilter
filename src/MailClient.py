import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import re
import time
import os

_logger = logging.getLogger("contrataciones_estado")

def check_email(email):
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,4})+$'
    if(re.search(regex,email)):
        return True
    else:
        return False

def send_email(config, attachment, text_email):
    email_server = config['EMAIL_CONF']['EMAIL_SERVER']
    email_port = int(config['EMAIL_CONF']['EMAIL_PORT'])
    email_from = config['EMAIL_CONF']['EMAIL_FROM']
    email_password = config['EMAIL_CONF']['EMAIL_PASSWD']
    email_to = config['EMAIL_CONF']['EMAIL_TO']

    email_subject = config['EMAIL_MSG']['EMAIL_SUBJECT']

    _logger.info("Send email to '%s'" % (email_to))

    email_sent = False
    email_sent_attempts = 0

    if(check_email(email_to)):
        while(not email_sent and email_sent_attempts < 5):
            try:
                _logger.info("Connect to '%s:%d'" % (email_server, email_port))

                s = smtplib.SMTP(email_server, email_port)
                s.ehlo('mylowercasehost')
                s.starttls()
                s.ehlo('mylowercasehost')

                s.login(email_from, email_password)

                msg = MIMEMultipart()
                msg['From'] = email_from
                msg['To'] = email_to
                msg['Subject'] = email_subject

                # Add body to email
                msg.attach(MIMEText(text_email, "plain"))

                # Add attachment to message and convert message to string
                part = adjuntar_archivo_xlsx(attachment)
                if(part):
                    msg.attach(part)
        
                s.sendmail(email_from, email_to, msg.as_string().encode('utf-8'))
                _logger.info("Email enviado a '%s'" % (email_to))

            except Exception as ex:
                _logger.error("ERROR! Email cannot be sent : " + str(ex))
            
            time.sleep(5)
            email_sent_attempts += 1

    else:
        _logger.error("ERROR! Email invalido '%s'" % (email_to))


def adjuntar_archivo_xlsx(attachment_filename):
    part = None

    if(len(attachment_filename) > 0):
        # Open PDF file in binary mode
        #with open(attachment, "rb") as attachment:
        #    # Add file as application/octet-stream
        #    # Email client can usually download this automatically as attachment
        #    part = MIMEBase("application", "octet-stream")
        #    part.set_payload(attachment.read())

        # Open PDF file in binary mode
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(attachment_filename, "rb").read())
        encoders.encode_base64(part)
        # Add header as key/value pair to attachment part
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {os.path.basename(attachment_filename)}",
        )

    return part


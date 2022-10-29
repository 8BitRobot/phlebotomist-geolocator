import smtplib, ssl
from email.mime.text import MIMEText

SENDER      = "premgiridhar11@gmail.com"
RECIPIENTS  = "premgiridhar11+alerts@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
PORT        = 465
SSL_CONTEXT = ssl.create_default_context()
MAILER_OBJ  = smtplib.SMTP_SSL(SMTP_SERVER, PORT, context=SSL_CONTEXT)

ERROR_MESSAGE = lambda id_str : f"There was an API error while attempting to fetch location data for clinician {id_str}."
LOST_MESSAGE  = lambda id_str : f"Clinician {id_str} has exited their bounding box. Please contact them ASAP to ensure their safety."
CRIT_MESSAGE  = lambda id_str : f"Clinician {id_str} has been outside the bounding box for over 3 minutes. Consider initiating the appropriate safety processes."
SAFE_MESSAGE  = lambda id_str : f"Clinician {id_str} has returned to within the bounding box."

VALID_IDS   = ["1", "2", "3", "4", "5", "6", "7"]

if __name__ == "__main__":
    pass

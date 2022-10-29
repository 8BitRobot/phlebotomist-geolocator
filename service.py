# Global constants and login information
from config import config, secrets

# Other libraries
from datetime import datetime, timedelta  # to run the task over an interval of time
import time
import requests                           # to make requests to the API
import smtplib                            # to send emails
from email.mime.text import MIMEText      # to easily add metadata to email
from shapely.geometry import shape, Point # to parse GeoJSON polygons


'''
Poll the API for the location data of a given phlebotomist.

Params:
    id_str - a string containing the ID number of the phlebotomist

Returns the raw JSON data produced by the request.
'''
def poll_sh_api(id_str):
    results = requests.get(f"https://3qbqr98twd.execute-api.us-west-2.amazonaws.com/test/clinicianstatus/{id_str}")
    return results.json()


'''
Wrap email functions in a try/except to handle SMTP connection timeouts.
'''
def attempt_email(email_type, id_str):
    repeat = True
    while repeat:
        repeat = False
        try:
            if email_type == "error":
                send_error_email(id_str)
            elif email_type == "lost":
                send_lost_email(id_str)
            elif email_type == "critical":
                send_critical_email(id_str)
            elif email_type == "safe":
                send_safe_email(id_str)
        except smtplib.SMTPSenderRefused:
            config.MAILER_OBJ  = smtplib.SMTP_SSL(config.SMTP_SERVER, config.PORT, context=config.SSL_CONTEXT)
            config.MAILER_OBJ.login(secrets.EMAIL_ADDR, secrets.PASSWORD)
            # repeat = True


'''
Send an email alert indicating that an error occurred while attempting to find the status of a given phlebotomist.

Params:
    id_str - a string containing the ID number of the phlebotomist

Doesn't return anything.
'''
def send_error_email(id_str):
    msg = MIMEText(config.ERROR_MESSAGE(id_str), "plain")
    msg["From"] = config.SENDER
    msg["To"] = config.RECIPIENTS
    msg["Subject"] = f"[ALERT] API Error for ID {id_str}"
    config.MAILER_OBJ.sendmail(config.SENDER, config.RECIPIENTS, msg.as_string())


'''
Send an email alert indicating that a phlebotomist has exited their bounding zone.

Params:
    id_str - a string containing the ID number of the phlebotomist

Doesn't return anything.
'''
def send_lost_email(id_str):
    msg = MIMEText(config.LOST_MESSAGE(id_str), "plain")
    msg["From"] = config.SENDER
    msg["To"] = config.RECIPIENTS
    msg["Subject"] = f"[ALERT] Out of Bounds Clinician ID {id_str}"
    config.MAILER_OBJ.sendmail(config.SENDER, config.RECIPIENTS, msg.as_string())


'''
Send an email alert indicating that a phlebotomist has been outside the bounding zone
for an extended period of time.

Params:
    id_str - a string containing the ID number of the phlebotomist

Doesn't return anything.
'''
def send_critical_email(id_str):
    msg = MIMEText(config.CRIT_MESSAGE(id_str), "plain")
    msg["From"] = config.SENDER
    msg["To"] = config.RECIPIENTS
    msg["Subject"] = f"[ALERT] Excessive Out of Bounds Clinician ID {id_str}"
    config.MAILER_OBJ.sendmail(config.SENDER, config.RECIPIENTS, msg.as_string())



'''
Send an email alert indicating that a phlebotomist has returned to within their bounding zone.

Params:
    id_str - a string containing the ID number of the phlebotomist

Doesn't return anything.
'''
def send_safe_email(id_str):
    msg = MIMEText(config.SAFE_MESSAGE(id_str), "plain")
    msg["From"] = config.SENDER
    msg["To"] = config.RECIPIENTS
    msg["Subject"] = f"[ALERT] Returned to Bounds Clinician ID {id_str}"
    config.MAILER_OBJ.sendmail(config.SENDER, config.RECIPIENTS, msg.as_string())


'''
Determine whether an API response is an error or actual GeoJSON data.
If it's an error, send an error email.
If it's actual data, process that data to determine the phlebotomist's location.

Params:
    id_str - a string containing the ID number of the phlebotomist

Returns True if the phlebotomist is safe, and False otherwise.
'''
def is_phlebotomist_safe(id_str):
    res = poll_sh_api(id_str)
    if "error" in res:
        # if the "error" key exists in the response, an error has occurred;
        # try to make the api call again, up to 5 times
        counts = 5
        while "error" in res and counts > 0:
            time.sleep(5)
            res = poll_sh_api(id_str)
            counts -= 1
        # if the API is still erroring, stop trying and move onto the next clinician
        if "error" in res:
            return "error"
    else:
        if not determine_valid_location(res["features"][0]["geometry"], res["features"][1:]):
            return "unsafe"
    return "safe"

'''
Determine whether the phlebotomist at location `point` is within the boundaries indicated by `bounds`.

Params:
    point  - the current location of the phlebotomist
    bounds - the bounding box that the phlebotomist needs to be inside

Returns True if the phlebotomist is in-bounds, and False otherwise.
'''
def determine_valid_location(point, bounds):
    # convert the `point` to a `shapely` shape object
    loc = shape(point)
    safe = False
    for box in bounds:
        # ditto for the bounding box
        polygon = shape(box["geometry"])
        # if the clinician is in ANY of the bounding boxes in the list, they're safe
        if polygon.contains(loc) or polygon.touches(loc):
            safe = True
            break
    return safe


if __name__ == "__main__":
    print(f"starting at {datetime.now()}")

    # log into the mailer
    config.MAILER_OBJ.login(secrets.EMAIL_ADDR, secrets.PASSWORD)
    
    # calculate the time that the program should quit
    endtime = datetime.now() + timedelta(minutes=60)

    # initialize dict of IDs and statuses
    statuses = {}
    for id_str in config.VALID_IDS:
        statuses[id_str] = "safe"

    while datetime.now() < endtime:
        for id_str in config.VALID_IDS:
            result = is_phlebotomist_safe(id_str)
            # if they're lost (and weren't already lost), send alert
            if result == "unsafe" and statuses[id_str] == "safe":
                statuses[id_str] = "lost"
                attempt_email("lost", id_str)
            # if they've been lost for over 4 minutes, send alert
            elif result == "unsafe" and statuses[id_str] == "lost":
                statuses[id_str] = "critical"
                attempt_email("critical", id_str)
            # if they're safe (and weren't already safe), send alert
            elif result == "safe" and statuses[id_str] != "safe":
                statuses[id_str] = "safe"
                attempt_email("safe", id_str)
            # do nothing if they're safe and were already safe
            # if there was an error, send alert
            elif result == "error":
                attempt_email("error", id_str)
        time.sleep(240)

    config.MAILER_OBJ.quit()
    print(f"finished at {datetime.now()}")

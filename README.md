# Phlebotomist Geolocation Service

## Summary

This application is a service that monitors the location of remote health techs for safety reporting. When clinicians are sent to customers' houses, it's imperative that we have a system in place to alert us if they stray too far from the expected region; this could indicate any number of issues regarding incorrect location info or clinician safety. Essentially, the service checks each clinician's location every 4 minutes to ensure that they're safely in the expected boundaries.

## How it works

The service works by polling an API that reports the current location and expected region(s) in GeoJSON format. Then, it compares each expected region to the current location; if the current location isn't within or touching any of the expected regions, we send an email alert indicating as such.

If there's an error with the API, the service attempts to re-request the data up to 5 times. If all requests fail, we then send an email alert indicating that the clinician's location data could not be accessed and try again after the monitoring interval.

If a clinician has been lost for more than one monitoring period (4 minutes each), we send another email alert indicating that that clinician has been lost for an extended period of time. In order to not flood the alerts inbox with alerts that a clinician has been lost, subsequent alerts after this final "critical" alert are suppressed until the clinician is safe again.

If a clinician that was previously lost has returned to within the bounding box, we send an email alert indicating that they're safe again.

Lastly, if a clinician wasn't lost to begin with, we don't send any alerts if they continue to be within the bounding box.

The polling interval I chose is 4 minutes. This value was chosen to meet the task specification that an alert should be sent within 5 minutes. Having an extra 1 minute buffer allows for:
- network delays when sending emails
- time to re-request API data when an error occurs

More specifically, each monitoring interval for ONE clinician is comprised of:
- An attempt to request information from the API
- (optional) up to five 5-second delays to re-request data from the API when an error occurs (25 seconds)
- Comparing the GeoJSON data
- Attempting to send the email
- (optional) if the SMTP connection has timed out, attempt to reconnect and log in again (<5 seconds)
- Downtime in the monitoring interval (4 minutes)

This process ensures that, even with significant network delays (>5 seconds), the alert will be sent within 5 minutes and clinicians can be tracked with close to real-time updates.

![image](https://user-images.githubusercontent.com/32723225/198849429-73cf27e6-3af3-46d2-a168-c71d8a2c4357.png)

## Libraries used

- `datetime` to run the service for an extended period of time (in this case, 1 hour)
- `time` to run the API polling over an interval (in this case, 4 minutes)
- `requests` to make API requests
- `smtplib` and `email` to send email alerts
- `shapely` to easily work with GeoJSON data

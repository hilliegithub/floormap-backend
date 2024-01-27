import smtplib, os, logging, json, ssl
from email.message import EmailMessage

logging.basicConfig(level=logging.DEBUG)

def notify(filepath,imageDownloadUrl, recipient):
    try:
        sender_address = os.environ.get("GMAIL_ADDRESS")
        sender_password = os.environ.get("GMAIL_PASSWORD")
        recipient_address = recipient

        msg = EmailMessage()
        msg.set_content(f"Hello, thank you for using floor mapping. You could download the image floormap from here {imageDownloadUrl}. We have attached the seat configuration in a file as an attachment.")
        msg["Subject"] = "Floor mapping"
        msg["From"] = sender_address
        msg["To"] = recipient_address

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(sender_address, sender_password)
            smtp.sendmail(sender_address, recipient_address, msg.as_string())

        print(f"Email message sent to {recipient_address}")

    except Exception as err:
        logging.debug("Email:" + err)
        return err
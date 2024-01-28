import smtplib, os, logging, json, ssl
from email.message import EmailMessage

logging.basicConfig(level=logging.DEBUG)

def notify(filepath,imageDownloadUrl, recipient):
    try:
        sender_address = os.environ.get("GMAIL_ADDRESS")
        sender_password = os.environ.get("GMAIL_PASSWORD")
        recipient_address = recipient
        smtp_port = 587

        msg = EmailMessage()
        msg.set_content(f"Hello, thank you for using floor mapping. You could download the image floormap from here {imageDownloadUrl}. We have attached the seat configuration in a file as an attachment.")
        msg["Subject"] = "RE: Floor mapping"
        msg["From"] = sender_address
        msg["To"] = recipient_address
        with open(filepath, 'rb') as f:
            file_data = f.read()
        file_name_split = filepath.rsplit('/',1)[-1]
        print("file_name(split - Email) " + file_name_split)
        msg.add_attachment(file_data, maintype='text', subtype='plain', filename=file_name_split)

        context = ssl.create_default_context()

        with smtplib.SMTP('smtp.gmail.com', smtp_port) as server:
            server.starttls()
            server.login(sender_address,sender_password)
            server.send_message(msg)

        # with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        #     smtp.login(sender_address, sender_password)
        #     smtp.sendmail(sender_address, recipient_address, msg.as_string())

        print(f"Email message sent to {recipient_address}")

    except Exception as err:
        logging.debug("Email:" + str(err))
        return err
    except SSLCertVerificationError as err:
        logging.debug("Email.notify(SSLCertVerificationError): " + str(err))
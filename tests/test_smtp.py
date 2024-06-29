import smtplib
from config import Config

def test_smtp_connection():
    try:
        server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT)
        server.starttls()
        server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
        print("Connected successfully!")
        server.quit()
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_smtp_connection()
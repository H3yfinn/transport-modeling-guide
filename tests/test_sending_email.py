from flask import Flask
from flask_mail import Mail, Message
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Print configuration to debug
print("MAIL_SERVER:", app.config.get('MAIL_SERVER'))
print("MAIL_PORT:", app.config.get('MAIL_PORT'))
print("MAIL_USE_TLS:", app.config.get('MAIL_USE_TLS'))
print("MAIL_USE_SSL:", app.config.get('MAIL_USE_SSL'))
print("MAIL_USERNAME:", app.config.get('MAIL_USERNAME'))
print("MAIL_PASSWORD:", app.config.get('MAIL_PASSWORD'))

# Initialize Flask-Mail
mail = Mail(app)

def test_sending_email():
    with app.app_context():
        try:
            email = ''  # Replace with your email to test
            password = 'a'
            msg = Message('Your Login Password', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Your password is: {password}'
            mail.send(msg)
            print("Email sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {e}")

if __name__ == "__main__":
    test_sending_email()

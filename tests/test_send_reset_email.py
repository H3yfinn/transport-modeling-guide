import os
import backend
from config import Config
from itsdangerous import URLSafeTimedSerializer

def generate_reset_token(email, secret_key, salt='password-reset-salt'):
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(email, salt=salt)

def test_send_reset_email():
    email = Config.PERSONAL_EMAIL
    secret_key = Config.SECRET_KEY  # Replace with your actual secret key
    token = generate_reset_token(email, secret_key)
    reset_link = f"https://transport-energy-modelling.com/reset_password/{token}"
    from_email = Config.MAIL_USERNAME
    
    new_values_dict = {'reset_link': reset_link}
    
    backend.setup_and_send_email(
        email=email,
        from_email=from_email,
        new_values_dict=new_values_dict,
        email_template='templates/reset_password_email_template.html',
        subject_title='Password Reset Request'
    )

if __name__ == "__main__":
    test_send_reset_email()

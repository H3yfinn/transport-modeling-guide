from cryptography.fernet import Fernet
import secrets
import os

def load_encryption_key():
    key = os.getenv('ENCRYPTION_KEY')
    if key is None:
        raise ValueError("ENCRYPTION_KEY is not set in the environment.")
    return key.encode()

def load_secret_key():
    key = os.getenv('SECRET_KEY')
    if key is None:
        raise ValueError("SECRET_KEY is not set in the environment.")
    return key.encode()

def encrypt_password(password):
    key = load_encryption_key()
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    key = load_encryption_key()
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(encrypted_password.encode()).decode()

def generate_keys(filepath=".env"):
    encryption_key = Fernet.generate_key().decode()
    secret_key = secrets.token_urlsafe(32)
    
    # Read the existing content and filter out old keys
    if os.path.exists(filepath):
        with open(filepath, "r") as key_file:
            lines = key_file.readlines()
        lines = [line for line in lines if not line.startswith('ENCRYPTION_KEY=') and not line.startswith('SECRET_KEY=')]
    else:
        lines = []
    
    # Append new keys
    lines.append(f'ENCRYPTION_KEY="{encryption_key}"\n')
    lines.append(f'SECRET_KEY="{secret_key}"\n')
    
    # Write everything back
    with open(filepath, "w") as key_file:
        key_file.writelines(lines)
    
    print("Keys generated and saved to secret.key file.")
# Example usage
# generate_keys()
# load_keys_from_file()
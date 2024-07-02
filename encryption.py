from cryptography.fernet import Fernet
import secrets
import os 

def load_keys_from_file(filepath="secret.key"):
    with open(filepath, "r") as key_file:
        for line in key_file:
            key, value = line.strip().split('=', 1)
            os.environ[key] = value
            
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

def generate_keys():
    encryption_key = Fernet.generate_key().decode()
    secret_key = secrets.token_urlsafe(32)
    
    with open("secret.key", "w") as key_file:
        key_file.write(f'ENCRYPTION_KEY={encryption_key}\n')
        key_file.write(f'SECRET_KEY={secret_key}\n')
    
    print("Keys generated and saved to secret.key file.")

# generate_keys()

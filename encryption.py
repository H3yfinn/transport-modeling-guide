# encryption.py
from cryptography.fernet import Fernet

# Generate a key for encryption
def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

# Load the previously generated key
def load_key():
    return open("secret.key", "rb").read()

# Encrypt a password
def encrypt_password(password):
    key = load_key()
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(password.encode())

# Decrypt a password
def decrypt_password(encrypted_password):
    key = load_key()
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(encrypted_password).decode()

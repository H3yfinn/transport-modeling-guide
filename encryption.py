import boto3
import base64
import logging
from dotenv import load_dotenv
import os
from flask import current_app
from cryptography.fernet import Fernet
import secrets

load_dotenv()

# Enable logging
from shared import global_logger, error_logger

def decrypt_data(encrypted_data):
    kms_client = boto3.client('kms', region_name='ap-northeast-1')
    if current_app.config.AWS_CONNECTION_AVAILABLE:#for some reason this doesnt actually stop the function from running if the connection is not available *hence why i put try except in the function
        return decrypt_data_with_kms(encrypted_data, kms_client)
    else:
        return encrypted_data#decrypt_data_without_kms(encrypted_data)

def encrypt_data(data):
    kms_client = boto3.client('kms', region_name='ap-northeast-1')
    if current_app.config.AWS_CONNECTION_AVAILABLE:#for some reason this doesnt actually stop the function from running if the connection is not available*hence why i put try except in the function
        return encrypt_data_with_kms(data, kms_client)
    else:
        return data#encrypt_data_without_kms(data)

def encrypt_data_with_kms(data, kms_client):
    try:
        response =  kms_client.encrypt(
            KeyId=os.getenv('KMS_KEY_ID'),
            Plaintext=data
        )
        ciphertext_blob = response['CiphertextBlob']
        encrypted_data = base64.b64encode(ciphertext_blob).decode('utf-8')
        # global_logger.debug(f"Encrypted data: {encrypted_data}")
        return encrypted_data
    except Exception as e:
        global_logger.error(f"Error during encryption: {e}", exc_info=True)
        error_logger.error(f"Error during encryption: {e}", exc_info=True)
        return data

def decrypt_data_with_kms(encrypted_data,kms_client):
    try:
        # if current_app.config.LOGGING:
        #     global_logger.debug(f"Original encrypted data: {encrypted_data}")

        # Add padding if necessary
        missing_padding = len(encrypted_data) % 4
        if missing_padding:
            new_encrypted_data += '=' * (4 - missing_padding)
        # if current_app.config.LOGGING:
        #     global_logger.debug(f"Padded encrypted data: {new_encrypted_data}")

        decoded_encrypted_data = base64.b64decode(new_encrypted_data)
        # if current_app.config.LOGGING:
        #     global_logger.debug(f"Decoded encrypted data.")

        response = kms_client.decrypt(
            CiphertextBlob=decoded_encrypted_data
        )
        decrypted_data = response['Plaintext'].decode('utf-8')

        return decrypted_data
    except Exception as e:
        global_logger.error(f"Error during decryption: {e}", exc_info=True)
        error_logger.error(f"Error during decryption: {e}", exc_info=True)
        return encrypted_data

##########Non KMS encryption and decryption functions##########

def load_encryption_key():
    key = os.getenv('NON_KMS_ENCRYPTION_KEY')
    if key is None:
        raise ValueError("ENCRYPTION_KEY is not set in the environment.")
    return key.encode()

def load_secret_key():
    key = os.getenv('SECRET_KEY')
    if key is None:
        raise ValueError("SECRET_KEY is not set in the environment.")
    return key.encode()

def encrypt_data_without_kms(data):
    key = load_encryption_key()
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data_without_kms(encrypted_data):
    key = load_encryption_key()
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

def generate_keys(filepath=".env", REPLACE_EXISTING=False):
    encryption_key = Fernet.generate_key().decode()
    secret_key = secrets.token_urlsafe(32)
    
    # Read the existing content and filter out old keys
    if os.path.exists(filepath):
        with open(filepath, "r") as key_file:
            lines = key_file.readlines()
        lines = [line for line in lines if not line.startswith('NON_KMS_ENCRYPTION_KEY=') and not line.startswith('SECRET_KEY=')]
    else:
        lines = []
    
    if not REPLACE_EXISTING:
        # Check if keys already exist
        if any(line.startswith('NON_KMS_ENCRYPTION_KEY=') for line in lines) or any(line.startswith('SECRET_KEY=') for line in lines):
            print("Keys already exist in the file. Use REPLACE_EXISTING=True to overwrite them.")
            return
        
    # Append new keys
    lines.append(f'NON_KMS_ENCRYPTION_KEY={encryption_key}\n')
    lines.append(f'SECRET_KEY={secret_key}\n')
    
    # Write everything back
    with open(filepath, "w") as key_file:
        key_file.writelines(lines)
    
    print("Keys generated and saved to secret.key file.")

# generate_keys(REPLACE_EXISTING=True)
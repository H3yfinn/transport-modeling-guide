import boto3
import base64
import logging
from dotenv import load_dotenv
import os
from config import Config
load_dotenv()

# Enable logging
from shared import global_logger
# Initialize the KMS client using the IAM role credentials
kms_client = boto3.client('kms', region_name='ap-northeast-1')

# def encrypt_data_with_kms(data):
#     response = kms_client.encrypt(
#         KeyId=os.getenv('KMS_KEY_ID'),
#         Plaintext=data.encode('utf-8')
#     )
#     return base64.b64encode(response['CiphertextBlob']).decode('utf-8')

# def decrypt_data_with_kms(encrypted_data):
#     decoded_encrypted_data = base64.b64decode(encrypted_data)
#     response = kms_client.decrypt(
#         CiphertextBlob=decoded_encrypted_data
#     )
#     return response['Plaintext'].decode('utf-8')

def encrypt_data_with_kms(data):
    try:
        response = kms_client.encrypt(
            KeyId=os.getenv('KMS_KEY_ID'),
            Plaintext=data
        )
        ciphertext_blob = response['CiphertextBlob']
        encrypted_data = base64.b64encode(ciphertext_blob).decode('utf-8')
        global_logger.debug(f"Encrypted data: {encrypted_data}")
        return encrypted_data
    except Exception as e:
        global_logger.error("Error during encryption:", exc_info=True)
        raise e

def decrypt_data_with_kms(encrypted_data):
    try:
        if Config.LOGGING:
            global_logger.debug(f"Original encrypted data: {encrypted_data}")
        
        # Add padding if necessary
        missing_padding = len(encrypted_data) % 4
        if missing_padding:
            encrypted_data += '=' * (4 - missing_padding)
        if Config.LOGGING:
            global_logger.debug(f"Padded encrypted data: {encrypted_data}")
        
        decoded_encrypted_data = base64.b64decode(encrypted_data)
        if Config.LOGGING:
            global_logger.debug(f"Decoded encrypted data: {decoded_encrypted_data}")

        response = kms_client.decrypt(
            CiphertextBlob=decoded_encrypted_data
        )
        decrypted_data = response['Plaintext'].decode('utf-8')
        if Config.LOGGING:
            global_logger.debug(f"Decrypted data: {decrypted_data}")
        
        return decrypted_data
    except Exception as e:
        global_logger.error("Error during decryption:", exc_info=True)
        raise e
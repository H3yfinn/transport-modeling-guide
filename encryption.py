import boto3
import base64
import logging

# Enable logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# Initialize the KMS client using the IAM role credentials
kms_client = boto3.client('kms', region_name='ap-northeast-1')

# Specify the KMS key ID (ARN of the KMS key)
KMS_KEY_ID = 'arn:aws:kms:ap-northeast-1:192888286458:key/05c2dfcf-5163-4c2a-83e9-8df291a08d34'

def encrypt_data_with_kms(data):
    response = kms_client.encrypt(
        KeyId=KMS_KEY_ID,
        Plaintext=data.encode('utf-8')
    )
    return base64.b64encode(response['CiphertextBlob']).decode('utf-8')

def decrypt_data_with_kms(encrypted_data):
    decoded_encrypted_data = base64.b64decode(encrypted_data)
    response = kms_client.decrypt(
        CiphertextBlob=decoded_encrypted_data
    )
    return response['Plaintext'].decode('utf-8')

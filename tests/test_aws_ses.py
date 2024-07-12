import boto3
import logging

# Enable logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# Initialize the SES client using the IAM role credentials
ses_client = boto3.client('ses', region_name='ap-northeast-1')

# Print the current configuration to verify
logger.debug("Current configuration:")
logger.debug("AWS_ACCESS_KEY_ID: %s", ses_client._request_signer._credentials.access_key)
logger.debug("AWS_SECRET_ACCESS_KEY: %s", ses_client._request_signer._credentials.secret_key)
logger.debug("Region: %s", ses_client.meta.region_name)

# Get sending statistics
try:
    response = ses_client.get_send_statistics()
    for data_point in response['SendDataPoints']:
        print(f"Timestamp: {data_point['Timestamp']}")
        print(f"Delivery Attempts: {data_point['DeliveryAttempts']}")
        print(f"Bounces: {data_point['Bounces']}")
        print(f"Complaints: {data_point['Complaints']}")
        print(f"Rejects: {data_point['Rejects']}")
        print()
except Exception as e:
    logger.error("Error occurred: %s", e)

import boto3
import os
# Initialize the SES client
ses_client = boto3.client('ses', region_name='ap-northeast-1')

# Get sending statistics
response = ses_client.get_send_statistics()

# Print the sending statistics
for data_point in response['SendDataPoints']:
    print(f"Timestamp: {data_point['Timestamp']}")
    print(f"Delivery Attempts: {data_point['DeliveryAttempts']}")
    print(f"Bounces: {data_point['Bounces']}")
    print(f"Complaints: {data_point['Complaints']}")
    print(f"Rejects: {data_point['Rejects']}")
    print()
    
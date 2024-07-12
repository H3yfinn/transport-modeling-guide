import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

class Config:
    LOGGING = True
    AWS_REGION = 'ap-northeast-1'  # or your actual AWS region

def encrypt_data_with_kms(data):
    # Placeholder for your actual KMS encryption function
    return data

def setup_and_send_email(email, from_email, new_values_dict, email_template, subject_title):
    """Send an email with the generated password. e.g. 
        backend.setup_and_send_email(email, new_values_dict, email_template='reset_password_email_template.html', subject_title='Password Reset Request')"""
    if Config.LOGGING:
        print(f'Sending email to {encrypt_data_with_kms(email)}')

    # Read HTML content from file
    with open(email_template, 'r') as file:
        html_content = file.read()

    # Replace placeholders with actual values
    for key, value in new_values_dict.items():
        html_content = html_content.replace('{{{}}}'.format(key), value)

    # AWS SES client setup
    ses_client = boto3.client('ses', region_name='ap-northeast-1')

    try:
        # Send email using AWS SES
        response = ses_client.send_email(
            Source=from_email,
            Destination={
                'ToAddresses': [email]
            },
            Message={
                'Subject': {
                    'Data': subject_title,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': html_content,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        if Config.LOGGING:
            print('Email sent successfully')
            print("Email sent! Message ID:", response['MessageId'])
    except NoCredentialsError:
        print("Credentials not available.")
    except PartialCredentialsError:
        print("Incomplete credentials provided.")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    # Test parameters
    test_email = 'recipient@example.com'
    from_email = 'your-email@example.com'
    new_values_dict = {'username': 'John Doe', 'password': '123456'}
    email_template = 'email_template.html'
    subject_title = 'Test Email'

    setup_and_send_email(test_email, from_email, new_values_dict, email_template, subject_title)

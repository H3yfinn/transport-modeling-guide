# Project Purpose

This project aims to communicate how the APERC 9th Edition Transport Model works. It was initiated after realizing that the model had become too complicated to explain easily to others who needed to interpret the results in detail. The best way to achieve this is to:

1. **Interactive Model**: Allow users to interact with the model directly to get a feel for how it works.
2. **Secondary Guide**: Provide a detailed guide to explain key parts of the model using the interactive model as a reference. The guide leverages web technologies to offer a more interactive experience than a static document, including GIFs, interactive charts, and code snippets.

This project aims to be useful in APERC activities such as workshops, training, and presentations, as well as for internal use by the APERC research team.

## Problems Addressed

- **Lack of Understanding by APERC Researchers**: Helps researchers interpret and explain the results to others.
- **Lack of Understanding by External Stakeholders**: Assists stakeholders in comprehending the results.
- **Training for New Researchers**: Aids new researchers in learning how to use the model.
- **Understanding of Transport Modelling Concepts**: Enhances understanding of both basic and advanced transport modelling and analysis concepts.
- **Improved Documentation**: Addresses disdain for the current 100+ page PDF documentation, making it easier to navigate and understand.
- **Model Simplification Pressure**: Reduces pressure to simplify the model for explanation purposes, thus maintaining its accuracy and usefulness.
- **Communication of Key Indicators and Results**: Improves the communication of key indicators and results to stakeholders, supporting the 9th APERC Outlook Report.


# Application Overview

The application enables users to upload input files, select an economy, run a model, and view or download the results. Each user session is uniquely identified and isolated, ensuring users do not interfere with each other's data.

## Application code

1. **Upload Input Data**: Users upload the required input files for running the model.
2. **Select Economy and Run Model**: Users select an economy and execute the model.
3. **View Results**: Users can view the results in a new tab and download key result/input CSV files.
4. **Reset Session**: Users can reset their session to start anew.

## Key Components

1. **Session Management**: Each user session is assigned a unique ID and a session-specific directory for storing input and output files.
2. **File Handling**: Uploaded files are saved in the session-specific directory. The entire model library is duplicated to this directory to ensure data isolation.
3. **Running the Model**: The model is executed for the selected economy using the provided input files.
4. **Results Display**: Results are shown in a new tab, and users can download key result/input CSV files.

# Standard update procedure

```bash
ssh -i "~/.ssh/transport-model-web-app.pem"  ec2-user@ec2-3-113-59-243.ap-northeast-1.compute.amazonaws.com 
cd /var/www/transport-modeling-guide && git pull --recurse-submodules && git submodule update --remote --merge
source venv/bin/activate && pip3 install --ignore-installed -r /var/www/transport-modeling-guide/requirements.txt
sudo systemctl daemon-reload &&  sudo systemctl restart gunicorn-transport-energy-modelling && sudo systemctl restart gunicorn-aws && sudo systemctl restart nginx  && sudo certbot renew && sudo systemctl status gunicorn-transport-energy-modelling
```
All together (except ssh and requirements update):
```bash
ssh -i "~/.ssh/transport-model-web-app.pem"  ec2-user@ec2-3-113-59-243.ap-northeast-1.compute.amazonaws.com 
cd /var/www/transport-modeling-guide && git pull --recurse-submodules && git submodule update --remote --merge && source venv/bin/activate && sudo systemctl daemon-reload && sudo systemctl restart gunicorn-transport-energy-modelling && sudo systemctl restart gunicorn-aws && sudo systemctl restart nginx  && sudo certbot renew && sudo systemctl status gunicorn-transport-energy-modelling
```
Might also need to use git lfs if its still being used for data:
```bash
git lfs install
git lfs pull
```
# Guide for getting website up and running
Using Amazon EC2 to deploy the website.
First set up the requirements.txt file.
```bash
pip freeze > requirements.txt   
```
There were also some windows related libraries i had to remove manually.

# Local installation
```bash
python3.9 -m venv transport-modeling-guide-venv
transport-modeling-guide-venv\Scripts\activate #activate the virtual environment
pip install -r requirements.txt
```
All done (hopefully...)

# Submodule integration
since this uses the transport model 9th edition repo, it seems clean to initialise it as a submodule. This is done with the following command:
```bash
git submodule add https://github.com/H3yfinn/transport_model_9th_edition.git transport_model_9th_edition
```
However you will also need to run the following command to get the submodule when you git clone:
```bash
git submodule update --init --recursive
```
And to update the submodel use (which will also update the main repo -  i think the second one is the only one you need to use though):
```bash
git pull --recurse-submodules && git submodule update --remote --merge
```

# .env files:
We manage the secret keys using generate_key,py and the .env file. The .env file is not uploaded to the git repo. It is used to store the secret keys and other sensitive information. The .env file should look like this:
```bash
LOGGING=
DEBUG=
MAIL_USERNAME=
PERSONAL_EMAIL=
MASTER_USER_EMAIL=
MASTER_USER_PASSWORD=
```
You will need to copy/paste the values for everything except the keys, as the keys are generated using the generate_key.py file.

Also i found alt-shift-s to be useful for softwrapping things in nano. good for user_data.json viewin
# New EC2 instance
I'm going to try to set up a new EC2 instance instaed of using elastic beanstalk. Maybe it will be easier to manage.

Using pem file this time. ssh into the ec2 instance using the following commands:
```bash
nano ~/.ssh/transport-model-web-app.pem
chmod 400 ~/.ssh/transport-model-web-app.pem
```
Then ssh into the ec2 instance using the following command:
```bash
ssh -i "~/.ssh/transport-model-web-app.pem"  ec2-user@ec2-3-113-59-243.ap-northeast-1.compute.amazonaws.com 
```
# NGINX gunicorn setup:
Instead of using Apache with mod_wsgi, you can use gunicorn as the WSGI server and Nginx as a reverse proxy. Some of this can be fund in this chat: https://chatgpt.com/share/7caf780a-5746-4194-923f-729c5720b871

Steps to Set Up gunicorn with Nginx
Update and Install Dependencies:

```bash
sudo yum update -y
sudo yum install -y python3-pip nginx
sudo pip3 install virtualenv
```
Set Up Your Flask Application:

```bash
virtualenv venv
mkdir -p /var/www/
sudo git clone https://github.com/H3yfinn/transport-modeling-guide.git
git submodule update --init --recursive #make sure to get the submodule
cd /var/www/transport-modeling-guide
source venv/bin/activate #this means ur virtual environment is activated and is called venv
pip install flask gunicorn

sudo pip3 install --ignore-installed -r /var/www/transport-modeling-guide/requirements.txt #might as well install the requirements now
```
Create a Simple Flask App:

```python
# /var/www/transport-modeling-guide/app.py
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"

if __name__ == "__main__":
    app.run()
```
Create a Gunicorn Systemd Service:

```bash
sudo nano /etc/systemd/system/gunicorn-transport-energy-modelling.service
sudo nano /etc/systemd/system/gunicorn-aws.service
```
Add the following content:
```ini
[Unit]
Description=gunicorn daemon for transport-energy-modelling.com
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/var/www/transport-modeling-guide
ExecStart=/var/www/transport-modeling-guide/venv/bin/gunicorn --workers 3 --bind unix:transport-modeling-guide.sock -m 007 wsgi:app
Umask=007

[Install]
WantedBy=multi-user.target
#and paste the below for the aws one
[Unit]
Description=gunicorn daemon for ec2-3-112-219-75.ap-northeast-1.compute.amazonaws.com
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/var/www/transport-modeling-guide
ExecStart=/var/www/transport-modeling-guide/venv/bin/gunicorn --workers 3 --bind unix:transport-modeling-guide.sock -m 007 wsgi:app
Umask=007

[Install]
WantedBy=multi-user.target
```

Create a WSGI Entry Point: 

```python
# /var/www/transport-modeling-guide/wsgi.py
from app import app

if __name__ == "__main__":
    app.run()
```
Set Permissions (some of this might not be necessary):
```bash
sudo chown -R ec2-user:ec2-user /var/www/transport-modeling-guide
sudo chmod -R 755 /var/www/transport-modeling-guide
```
Start and Enable the Gunicorn Service:

```bash
sudo systemctl start gunicorn-transport-energy-modelling && sudo systemctl enable gunicorn-transport-energy-modelling && sudo systemctl start gunicorn-aws && sudo systemctl enable gunicorn-aws
```
Configure Nginx:

```bash
sudo nano /etc/nginx/conf.d/transport-modeling-guide.conf
```

Add the following content:
```bash
server {
    listen 80;
    server_name transport-energy-modelling.com www.transport-energy-modelling.com;

    location / {
        proxy_pass http://unix:/var/www/transport-modeling-guide/transport-modeling-guide.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name ec2-3-112-219-75.ap-northeast-1.compute.amazonaws.com;

    location / {
        proxy_pass http://unix:/var/www/transport-modeling-guide/transport-modeling-guide.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

```
Start and Enable Nginx:

```bash
sudo systemctl start nginx && sudo systemctl enable nginx
```

Verify Gunicorn Service

```bash
sudo systemctl status gunicorn-transport-energy-modelling && sudo systemctl status gunicorn-aws
```
You should see output indicating that Gunicorn is active and running.

Verify Nginx Configuration

```bash
sudo nginx -t
```
You should see a message indicating that the configuration is successful.

Restart Nginx

```bash
sudo systemctl restart nginx
```

# Setting up DNS:
Had some issues getting certbot to work but doing thsi it worked:
```bash
#make sure you are in the virtual environment: source venv/bin/activate 
sudo yum install python3-six -y
sudo yum remove certbot python3-certbot-nginx -y
sudo pip3 install certbot-nginx
sudo certbot --nginx -d transport-energy-modelling.com -d www.transport-energy-modelling.com #e.g. ec2-3-112-219-75.ap-northeast-1.compute.amazonaws.com < but this wont work, it cant be the aws domain, it has to be a proper domain name - also you will have needed to add the domain to the aws route 53 thing
```

# Setting up AWS SES:
this is the email service that will be used to send emails. You will need to verify the email address you want to send from in the SES console. ?Then you can use the following command to get the smtp credentials:?
```bash
pip install awscli boto3 jmespath
aws configure 
```
For aws configure you need to have a user set up in the aws IAM console with the correct permissions. You can then input the access key and secret key for that user. You can then use the following command to get the smtp credentials:
```bash
aws sts get-caller-identity
aws ses verify-email-identity --email-address #not sure, suggested by github copilot
```

# Error handling
Quick note, whenever you change most settings you will probably want to restart the daemon, gunicorn and nginx services. This can be done with the following commands:
```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

Check Gunicorn Service Status:

```bash
sudo systemctl status gunicorn
```
You should see output indicating that Gunicorn is active and running. If there are any issues, this output will provide clues.

# Check Gunicorn Logs (usually what you want to check):
After changes to the app (and not configurations),you normally only need to run *sudo systemctl restart gunicorn* to make sure the changes are applied. If there are any issues, you should first check the Gunicorn logs with the following command:
```bash
sudo journalctl -u gunicorn -e
```
This command shows the logs for the Gunicorn service, which can help diagnose any issues.
Then if you cant find the issue there, you can check the nginx logs with the following commands:

Verify Nginx Configuration
```bash
sudo nginx -t
```
You should see a message indicating that the configuration is successful.

Check Nginx Service Status:
```bash
sudo systemctl status nginx
```
This command shows whether Nginx is running correctly.

Check Nginx Logs:
```bash
sudo tail -f /var/log/nginx/access.log
```
Error log:
```bash
sudo tail -f /var/log/nginx/error.log
```
Verify SSL Configuration:
```bash
https://ec2-3-112-219-75.ap-northeast-1.compute.amazonaws.com
https://www.ec2-3-112-219-75.ap-northeast-1.compute.amazonaws.com
```
You should see the "Hello, World!" message from your Flask application. The browser should indicate a secure connection (usually a padlock icon in the address bar).

Check Certbot Certificate:

```bash
sudo certbot certificates
```
This command shows the details of the SSL certificates managed by Certbot.



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
And to update the submodel use (which will also update the main repo):
```bash
git pull --recurse-submodules
git submodule update --remote --merge
```

# New EC2 instance
I'm going to try to set up a new EC2 instance instaed of using elastic beanstalk. Maybe it will be easier to manage.

Using pem file this time. ssh into the ec2 instance using the following commands:
```bash
nano ~/.ssh/transport-model-web-app.pem
chmod 400 ~/.ssh/transport-model-web-app.pem
```
Then ssh into the ec2 instance using the following command:
```bash
ssh -i "~/.ssh/transport-model-web-app.pem" ec2-user@ec2-3-112-219-75.ap-northeast-1.compute.amazonaws.com
```

# NGINX gunicorn setup:
Instead of using Apache with mod_wsgi, you can use gunicorn as the WSGI server and Nginx as a reverse proxy. This setup is often simpler and widely used in the Python community.

Steps to Set Up gunicorn with Nginx
Update and Install Dependencies:

```bash
sudo yum update -y
sudo yum install -y python3-pip nginx
sudo pip3 install virtualenv
```
Set Up Your Flask Application:

```bash
mkdir -p /var/www/
sudo git clone https://github.com/H3yfinn/transport-modeling-guide.git
git submodule update --init --recursive #make sure to get the submodule
cd /var/www/transport-modeling-guide
virtualenv venv
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
sudo nano /etc/systemd/system/gunicorn.service
```
Add the following content:
```ini
[Unit]
Description=gunicorn daemon
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
Start and Enable the Gunicorn Service:

```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```
Configure Nginx:

```bash
sudo nano /etc/nginx/conf.d/transport-modeling-guide.conf
```
Add the following content:
```bash
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
sudo systemctl start nginx
sudo systemctl enable nginx
```

Verify Gunicorn Service

```bash
sudo systemctl status gunicorn
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
sudo yum install python3-six -y
sudo yum remove certbot python3-certbot-nginx -y
sudo pip3 install certbot-nginx
sudo certbot --nginx -d DOMAIN.com -d www.DOMAIN.com #e.g. ec2-3-112-219-75.ap-northeast-1.compute.amazonaws.com < but this wont work, it cant be the aws domain, it has to be a proper domain name
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








<!-- Then set permissions for the ec2-user:
```bash
sudo chown -R ec2-user:ec2-user /var/www/html/transport-modeling-guide
```
Then install the required packages:
```bash
sudo yum install python3
sudo yum install python3-pip
sudo pip3 install -r /var/www/html/transport-modeling-guide/requirements.txt
```
Then you can set up the virtual host configuration file for apache and the wsgi file for the website. Then restart the apache server:
```bash
sudo systemctl restart httpd  # For Amazon Linux
```
Then setup the virtual host configuration file for apache and the wsgi file for the website. Then restart the apache server:
```bash
sudo nano /etc/httpd/conf.d/transport-modeling-guide.conf 
```
Fill it with the following:
```bash
<VirtualHost *:80>
    ServerAdmin webmaster@yourdomain.com
    DocumentRoot /var/www/html/transport-modeling-guide
    ServerName ec2-3-112-219-75.ap-northeast-1.compute.amazonaws.com
    ServerAlias www.ec2-3-112-219-75.ap-northeast-1.compute.amazonaws.com

    WSGIDaemonProcess transport-modeling-guide user=ec2-user group=ec2-user threads=5
    WSGIScriptAlias / /var/www/html/transport-modeling-guide/transport-modeling-guide.wsgi

    <Directory /var/www/html/transport-modeling-guide>
        Require all granted
    </Directory>

    Alias /static /var/www/html/transport-modeling-guide/static
    <Directory /var/www/html/transport-modeling-guide/static/>
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/transport-modeling-guide_error.log
    CustomLog ${APACHE_LOG_DIR}/transport-modeling-guide_access.log combined
</VirtualHost>
```
Then restart the apache server:
```bash
sudo systemctl restart httpd  # For Amazon Linux
```
Then create the wsgi file:
```bash
sudo nano /var/www/html/transport-modeling-guide/transport-modeling-guide.wsgi
```
Fill it with the following:
```bash
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/var/www/html/transport-modeling-guide")

from transport-modeling-guide import app as application
application.secret_key = '' # put the secret key from the generate_key.py file here
```
Then restart the apache server:
```bash
sudo systemctl restart httpd  # For Amazon Linux
```
Then you can access the website from the browser using the public DNS of the EC2 instance. -->

<!-- ```bash
git clone https://github.com/H3yfinn/transport-modeling-guide.git
python generate_key.py
```
At this point you will need to organise your config files. I couldnt find how to do this more easily so i created 01_create_env.config and put the MAIL_USERNAME, MAIL_PASSWORD, ENCRYPTION_KEY and SECRET_KEY (and any others) in the aws systems-manager/parameters thing.
```bash
pip install awsebcli --upgrade
eb init -p python-3.9 transport-modeling-guide
eb create env-transport-model-app
eb deploy
```
If that doesnt work, theres a slight chance you'll have to run this because the transport_model_9th_edition repo is in my git as a submodule (trying to delete it):
```bash
git submodule deinit -f transport_model_9th_edition
rm -rf .git/modules/transport_model_9th_edition
git rm -f transport_model_9th_edition
git commit -m "Removed submodule transport_model_9th_edition"
```
And when you want to update the git you can just do regular git pull and so on. and then run the following commmand to update that all on the website:
```bash
eb deploy
```

If you need to install new packages you will need to update the requirements.txt and/or conda-requirements.txt file. Then when you use the eb deploy command it will install the new packages for you.

If you make a mistake you can remove the environment with the following command:
```bash
eb terminate env-transport-model-app
```
You can also use *eb logs* to see the logs of the website and see what went wrong if it crashes.
If you need to ssh into the thing to check the files you can use the following command (assuming you put the .ppk file in the ~/.ssh directory, put the key pair in aws's EC2 keypairs menu and activated the key pair within the elastic beanstalk environment configuration menu -  also get the domain from EC2>Instances>Public DNS (IPv4)):
```bash
chmod 400 ~/.ssh/transport-model-web-app.ppk # to adjust the permissions of the key file
ssh -i ~/.ssh/transport-model-web-app.ppk ec2-54-202-194-218.us-west-2.compute.amazonaws.com
``` -->
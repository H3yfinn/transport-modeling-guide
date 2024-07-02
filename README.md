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
Using Amazon elastic beanstalk to deploy the website.
```bash

pip install awsebcli --upgrade
conda list --export > conda-requirements.txt  
pip freeze > requirements.txt   
mkdir .ebextensions
mv conda-requirements.txt .ebextensions
mv requirements.txt .ebextensions
```
Create a file called 01_conda_setup.config in the .ebextensions folder:
```bash

commands:
  01_install_conda:
    command: |
      mkdir -p /opt/miniconda3
      wget -nv https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
      bash /tmp/miniconda.sh -b -f -p /opt/miniconda3
      /opt/miniconda3/bin/conda init
  02_create_conda_env:
    command: |
      /opt/miniconda3/bin/conda create -n env_transport_model_web_app --file conda-requirements.txt -y
      echo 'source /opt/miniconda3/bin/activate env_transport_model_web_app' >> ~/.bashrc
  03_install_requirements:
    command: |
      source /opt/miniconda3/bin/activate env_transport_model_web_app
      pip install -r requirements.txt
```
Then use the following commands to deploy the website:
```bash
eb init -p python-3.9 transport-modeling-guide
eb create env_transport_model_web_app_aws
eb deploy
```


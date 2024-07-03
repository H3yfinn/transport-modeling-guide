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
pip freeze > requirements.txt   
mkdir .ebextensions
mv requirements.txt .ebextensions
```
I actually then went into Claude.ai and moved all the conda files to pip bnecause it seemed conda wasnt working well with the elastic beanstalk. So I had to change the conda-requirements.txt to requirements.txt.

Now update your git with all these cahnges because you're going to clone it within the amazon Cloudshell (just a terminal in the cloud) and then deploy it from there.

Get in there and clone the git! and use the following commands to deploy the website:
```bash
git clone https://github.com/H3yfinn/transport-modeling-guide.git
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


# local installation
```bash
python3.9 -m venv transport-modeling-guide-venv
transport-modeling-guide-venv\Scripts\activate #activate the virtual environment
pip install -r requirements.txt
```
All done (hopefully...)
#want to remove the spaces from file names saved in this directory and then update their names in the readme too.
#this is a script to do that
#%%
#first find what files we have and rename their filenames to replace spaces with underscores
from asyncore import write
import os
import re

#%%
folder_names = ['transport-model-9th-edition', 'Kyoto-transport-lecture-2022']
file_name_list = []
for folder_name in folder_names:
    for file_name in os.listdir(folder_name):
        if ' ' in file_name:
            old_file_name = file_name
            file_name = file_name.replace(' ', '_')
            os.rename(os.path.join(folder_name, old_file_name), os.path.join(folder_name, file_name))

        #add file nae to list so we can print it in the readme. note that if the file is already in the readme or has no space anywa, it will still be added to the readme as we will add the files to the readme all over again.
        #creat fulll file name form folder name as well
        file_name_full = os.path.join(folder_name, file_name)
        file_name_list.append(file_name_full)
    
#%%
#now we need to update the readme with links to the files
with open('README.md', 'w') as f:
    f.write("##Repo for hosting graphs so that i can share them with others easily. Especially useful for html Plotly graphs which cannot be shared easily. \n\n")
    for file_name in file_name_list:
        #replace backslashes with forward slashes
        file_name = file_name.replace('\\', '/')
        line = "https://h3yfinn.github.io/APERC-graphs/" + file_name + "\n\n"
        f.write(line)

#done
# %%

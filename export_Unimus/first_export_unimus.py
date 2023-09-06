import requests
import base64
from datetime import datetime
from time import sleep
from urllib.parse import urljoin
import warnings
warnings.filterwarnings("ignore")
import os
import shutil


url = 
token = 
ids=[]
descriptions=[]
configs=[]
vendors=[]

pathback = "./export_Unimus/backup"
pathtemp = "./export_Unimus/temp"


isExistback = os.path.exists(pathback)
isExisttemp = os.path.exists(pathtemp)

if isExistback == True:
    shutil.rmtree(pathback)
    os.makedirs(pathback)

else: os.makedirs(pathback)

if isExisttemp == True:
    shutil.rmtree(pathtemp)
    os.makedirs(pathtemp)
else: os.makedirs(pathtemp)

def get_totalpages(uri, headers):
    try:
        response = requests.get(uri, headers=headers, verify=False) # To disable SSL verification, pass this parameter: verify=False
    except requests.exceptions.ConnectionError:
        print('Connection Error! Can you ping the URL? Also, please make sure there is only 1 line in each file url.txt and token.txt with no EOL marker.')
        exit()
    devices = response.json()
    totalpages = devices['paginator']['totalPages']
    return totalpages


def get_ids_and_descriptions():
    page=0
    device=0
    uri = (url + "/api/v2/devices?page=0&size=50")
    headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
    totalpages = get_totalpages(uri, headers) #finds the total number of pages using a 50 size limit (50 is the maximum Unimus will allow)
    
    addresses = open('./export_Unimus/temp/addresses', 'w')
    addresses.truncate(0)
    filenames = open('./export_Unimus/temp/filenames', 'w')
    filenames.truncate(0)
    
    while page <= totalpages: #loads all of the ids into the ids array + all the descriptions into the descriptions array + writes files with the addresses and descriptions (substituting spaces with hyphens) so we can easily lookup the address of the device using the filename
        uri = (url + "/api/v2/devices?page=" + str(page) + "&size=50")
        response = requests.get(uri, headers=headers, verify=False) # To disable SSL verification, pass this parameter: verify=False
        devices = response.json()
        for device in range(len(devices['data'])):
            ids.append(devices['data'][device]['id'])
            description = devices['data'][device]['description']
            descriptions.append(description)
            vendor = devices['data'][device]['vendor']
            vendors.append(vendor)
            #print(vendor)
        page += 1

def get_configs(): #decrypts the base64 config (the "bytes" value) and writes it to a file in the configs folder. Skips devices that dont have a config.
    i = 0
    de = 1

    headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
    for device in ids:
        uri = (url + "/api/v2/devices/" + str(device) + "/backups/latest")
        response = requests.get(uri, headers=headers, verify=False) # To disable SSL verification, pass this parameter: verify=False
        devicedata = response.json()
        #print(i)
        #print(b)
        if vendors[i] == None:
            vendors[i] = 'Inconnu'
        if vendors[i] == 'HP' or vendors[i] == 'Aruba':
            if descriptions[i] == None or descriptions[i] == '':
                descriptions[i] = 'Inconnu_' + str(de)
                de = de+1
            print(descriptions[i])
            print(vendors[i])
            print("\n")
            config = devicedata['data']['bytes']
            device = open('./export_Unimus/backup/' + str(descriptions[i]) + '.txt', 'w')
            base64_message = config
            base64_bytes = base64_message.encode('utf-8')
            message_bytes = base64.b64decode(base64_bytes)
            message = message_bytes.decode('utf-8')
            #print(message)
            device.write(message)
            device.close()
        i = i + 1


get_ids_and_descriptions()
get_configs()
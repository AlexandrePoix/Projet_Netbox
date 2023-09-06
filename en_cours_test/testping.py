import xml.etree.ElementTree as ET
from os import listdir, path
import json
import re
import requests
import pynetbox
import json
import logging
import os
import re
import sys
import time
import xml.dom.minidom
from collections import OrderedDict
import urllib3
from pyzabbix import ZabbixAPI
from pkg_resources import parse_version
urllib3.disable_warnings()

mypath = './hosts'                                         # chemin vers les fichiers exporter de zabbix

files=[path.join(mypath, f) for f in listdir(mypath) if f.endswith('.xml')]
FPasIP = open('./test_ip/pasip.txt', 'w')
FPing = open ('./test_ip/pingfail.txt', 'w')
def check_ping(ipv4):
    pingstatus = os.system("ping -n 1 " + ipv4)
    return pingstatus



try:
    for file in files:                                      # On regarde les fichiers exportés de zabbix
        tree = ET.parse(file)
        root = tree.getroot()
        for name in root.findall('./hosts/host/name'):      # On trouve le noms du host
            devname = name.text

            for name in root.findall('./hosts/host/groups/group/name'): # On trouve les groupes
                if "Switchs" in name.text:                  # On verifie que le host exporter de zabbix est un switch
                    sep = "/"
                    names = name
                    names = (names.text.split(sep, 1)[0])   # On récupere le nom du groupe d'hote de l'hote
                    
                    for ip in root.iter('ip'):                                  # Les IP serviront a la connexion sur les switchs pour les informations supplémentaires                
                            ipv4 = ip.text
                            print(ipv4)
                            result = check_ping(ipv4)
                            print(result)
                            print(devname)
                            if result == 1:
                                FPing.write(devname + ': ' + ipv4 + '\n')
except: FPasIP.write(devname + '\n')
FPing.close()
FPasIP.close()

"""
FPing = open ('./resultest/ping.txt', 'w')
mypath = './hosts'                                          # chemin vers les fichiers exporter de zabbix

files=[path.join(mypath, f) for f in listdir(mypath) if f.endswith('.xml')]

for file in files:                                      # On regarde les fichiers exportés de zabbix

    devname = ''
    newos = ''
    tenid = ''
    siteid = ''
    modid = ''
    serial = ''
    ipv4 = ''
    tree = ET.parse(file)
    root = tree.getroot()
    for ip in root.iter('ip'):                                  # Les IP serviront a la connexion sur les switchs pour les informations supplémentaires
        ipv4 = ip.text
        if ipv4 != '':
            pingstatus = check_ping(ipv4)
        if pingstatus != 0:

        else : FPing.write((ipv4) + "\n")
FPing.close()
"""
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

nb = pynetbox.apitoken = 
nb.http_session.verify = False          
files=[path.join(mypath, f) for f in listdir(mypath) if f.endswith('.xml')]
oldname = ''


devices=list(nb.dcim.devices.all())
ldevice=' '.join([str(item) for item in devices])

if ' in ldevice:
    print('ahoy')

with open('./res/ips.txt', 'r') as f:
    for line in f:
        name = line.split(' : ' [1])
        name = name[1].strip(' ')
        name2 = name
        if name2 not in ldevice:
            with open('./res/doublons.txt', 'a') as w:
                w.write(name2)
        else: print('non')


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
nb = pynetbox.apitoken = 

nb.http_session.verify = False                              # désactive la connexion avec certificat pour netbox

urllib3.disable_warnings()

def creaint(decid, maxint):
    inta = 1
    url = 
    while inta <= int(maxint):
        payload = json.dumps({
        "device": decid,
        "name": inta,
        "type": "1000base-t",
        "enabled": 0
        })
        headers = {
        'accept': 'application/json',
        'Authorization': 
        'Content-Type': 'application/json'
        }

        requests.request("POST", url, headers=headers, data=payload, verify=False)
        inta = inta + 1



def patchintuntagged(vlanid, listuntagged, decid):
    t = 0
    intid = 0
    ten = 1512
    print(vlanid)
    vlanid = nb.ipam.vlans.get(vid = vlanid, tenant_id = ten).id

    while t < len(listuntagged):
        inti = nb.dcim.interfaces.get(name=listuntagged[t], device_id=decid)
        intid = inti.id

        url = + str(intid) + '/'
        payload = json.dumps({
        "device": decid,
        "name": str(listuntagged[t]),
        "enabled": 1,
        "mode": "access",
        "untagged_vlan": vlanid
        })

        headers = {
        'accept': 
        'Authorization': 'Token 
        'Content-Type': 'application/json'
        }

        response = requests.request("PATCH", url, headers=headers, data=payload, verify=False)
        t = t+1
        print(response)




filne = "
checker = 0
interface = 1
"""
with open(filne, 'r') as f:

    for line in f:
        if line.startswith('interface'):
            maxint = line.strip('interface ')
            devname = 'Switch_Test_Int'
            dec = nb.dcim.devices.get(name=devname)
            decid = dec.id
    #creaint(decid, maxint)
"""
devname = 
dec = nb.dcim.devices.get(name=devname)
decid = dec.id

with open(filne, 'r') as f:
    for line in f:
        a = 0
        b = 0
        i = 0
        if line.startswith('vlan'):
            vlanid = line.strip('vlan ')

        if 'exit' not in line:
            if 'spanning-tree' in line:
                checker = 1
                break

        if 'no untagged' in line:
                nline = line.strip('no untagged ')
                listnountagged = nline.strip('\n').split(',')
                i = 0
                if len(listnountagged) == 1:
                    if '-' in listnountagged[i]:
                        a = listnountagged[i].split('-')[0]
                        b = listnountagged[i].split('-')[1]
                        del listnountagged[i]
                        while int(a) <= int(b):
                            listnountagged.append(str(a))
                            a = int(a) + 1
                        i = i-1

                    i = i + 1
                    print('les ports no untagged du vlan ' + vlanid + 'sont : ' + str(listnountagged))

                else:
                    while i < len(listnountagged):
                        if '-' in listnountagged[i]:
                            a = listnountagged[i].split('-')[0]
                            b = listnountagged[i].split('-')[1]
                            del listnountagged[i]
                            while int(a) <= int(b):
                                listnountagged.append(str(a))
                                a = int(a) + 1
                            i = i-1

                        i = i + 1
                    print('les ports no untagged du vlan ' + vlanid + 'sont : ' + str(listnountagged))


        if 'untagged' in line and 'no untagged' not in line:
                nline = line.strip('untagged ')
                listuntagged = nline.strip('\n').split(',')
                i = 0
                if len(listuntagged) == 1:

                    if '-' in listuntagged[i]:
                        a = listuntagged[i].split('-')[0]
                        b = listuntagged[i].split('-')[1]
                        del listuntagged[i]
                        while int(a) <= int(b):
                            listuntagged.append(str(a))
                            a = int(a) + 1
                    print('les ports untagged du vlan ' + vlanid + 'sont : ' + str(listuntagged) + '\n')

                    patchintuntagged(vlanid, listuntagged, decid)

                else:
                    while i < len(listuntagged):
                        if '-' in listuntagged[i]:
                            a = listuntagged[i].split('-')[0]
                            b = listuntagged[i].split('-')[1]
                            del listuntagged[i]
                            while int(a) <= int(b):
                                listuntagged.append(str(a))
                                a = int(a) + 1
                            i = i-1
                        i = i + 1

                    print('les ports untagged du vlan ' + vlanid + 'sont : ' + str(listuntagged) + '\n')
                    patchintuntagged(vlanid, listuntagged, decid)

        if ' tagged ' in line:
                nline = line.strip('tagged ')
                listtagged = nline.strip('\n').split(',')
                i = 0
                if len(listtagged) == 1:
                    if '-' in listtagged[i]:
                        a = listtagged[i].split('-')[0]
                        b = listtagged[i].split('-')[1]
                        del listtagged[i]
                        while int(a) <= int(b):
                            listtagged.append(str(a))
                            a = int(a) + 1
                        i = i-1

                    i = i + 1
                    print('les ports tagged du vlan ' + vlanid + 'sont : ' + str(listtagged) + '\n')

                else:
                    while i < len(listtagged):
                        if '-' in listtagged[i]:
                            a = listtagged[i].split('-')[0]
                            b = listtagged[i].split('-')[1]
                            del listtagged[i]
                            while int(a) <= int(b):
                                listtagged.append(str(a))
                                a = int(a) + 1
                            i = i-1
                        i = i + 1
                    print('les ports tagged du vlan ' + vlanid + 'sont : ' + str(listtagged) + '\n')

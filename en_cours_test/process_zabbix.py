import xml.etree.ElementTree as ET
from os import listdir, path
import json
import string
import re
import requests
import pynetbox
import warnings

warnings.filterwarnings("ignore")

nb = pynetbox.api('url', token = 'token')
nb.http_session.verify = False                              # désactive la connexion avec certificat pour netbox


mypath = './hosts'                                          # chemin vers les fichiers exporter de zabbix

files=[path.join(mypath, f) for f in listdir(mypath) if f.endswith('.xml')]

def postdevice(devname, se, tenid, siteid, modid, serial):    #   création d'une fonction permettant l'ajout d'un device sur netbox
    url = ""           #   url de netbox (à changer en cas de migration) suivi de /api/dcim/devices/ pour pointer vers l'url
                                                            #   des devices
    payload = json.dumps({
    "name": devname,
    "device_type": modid,
    "device_role": "1",
    "tenant": tenid,
    "site": siteid,
    "custom_fields":{
    "OS": se,
    "Numero_de_serie": serial
    }
    })
    headers = {
    'accept': 'application/json',
    'Authorization': 'Token 
    'Content-Type': 'application/json'
    }

    requests.request("POST", url, headers=headers, data=payload, verify=False)


def compten(slug):
    x = nb.tenancy.tenants.get(slug = slug)                 # utilisation de netboxapi pour trouver le tenant correspondant à celui exporter de zabbix
    tenid = x.id                                            # pour récuperer son ID de tenant 
    return tenid

def compsite(slug):                                         # utilisation de netboxapi pour trouver le site correspondant à celui exporter de zabbix
    s = nb.dcim.sites.get(slug = slug)                      # pour récuperer son ID de site
    siteid = s.id
    return siteid
"""
def comptype(modele):
    typeslug = ''.join(modele.split()).lower()              # utilisation de netboxapi pour trouver le modèle correspondant à celui exporter de zabbix
    typeslug = typeslug.translate(str.maketrans('','', '"!#$%&()*+_,./:;<=>?@[\]^`{|}~'))   # pour récuperer son ID de modèle (device-type)
    t = nb.dcim.device_types.get(slug = typeslug)
    modid = t.id
    return modid
"""

def comptype(modele):
    #typeslug = nb.dcim.device_types.get(model = modele)
    t = nb.dcim.device_types.get(model = modele)
    modid = t.id
    return modid

def compvend(vendor):
    vendslug = ''.join(vendor.split()).lower()               # utilisation de netboxapi pour trouver le vendeur correspondant à celui exporter de zabbix
    vendslug = vendslug.translate(str.maketrans('','', '"!#$%&()*+_,./:;<=>?@[\]^`{|}~'))   # pour récuperer son ID de vendeur (manufacturer)
    v = nb.dcim.manufacturers.get(slug = vendslug)
    vendid = v.id
    return vendid

def createnant(names):                                       # fonction de création de vendeur (manufacturer)    
    
    tenslug = ''.join(names.split()).lower()
    tenslug = tenslug.translate(str.maketrans('','', '"!#$%&()*+_,./:;<=>?@[\]^`{|}~'))

    url = 

    payload = json.dumps({
    "name": names,
    "slug": tenslug
    })
    headers = {
    'accept': 'application/json',
    'Authorization': 'Token 
    'Content-Type': 'application/json'
    }

    requests.request("POST", url, headers=headers, data=payload, verify=False)

    x = nb.tenancy.tenants.get(slug = tenslug)                 # utilisation de netboxapi pour trouver le tenant correspondant à celui exporter de zabbix
    tenid = x.id

    url = 

    payload = json.dumps({
    "name": names,
    "slug": tenslug,
    "tenant": tenid
    })
    headers = {
    'accept': 'application/json',
    'Authorization': 'Token 
    'Content-Type': 'application/json'
    }

    requests.request("POST", url, headers=headers, data=payload, verify=False)


def creavend(vendor):                                       # fonction de création de vendeur (manufacturer)    
    vendslug = ''.join(vendor.split()).lower()
    vendslug = vendslug.translate(str.maketrans('','', '"!#$%&()*+_,./:;<=>?@[\]^`{|}~'))

    url = 

    payload = json.dumps({
    "name": vendor,
    "slug": vendslug
    })
    headers = {
    'accept': 'application/json',
    'Authorization': 'Token 
    'Content-Type': 'application/json'
    }

    requests.request("POST", url, headers=headers, data=payload, verify=False)


def creatype(modele, vendid):                                # fonction de création de modèle (device-type) au travers de l'API de netbox

    typeslug = ''.join(modele.split()).lower()
    typeslug = typeslug.translate(str.maketrans('','', '"!#$%&()*+_,./:;<=>?@[\]^`{|}~'))

    url = 

    payload = json.dumps({
    "manufacturer": vendid,
    "model": modele,
    "slug": typeslug
    })
    headers = {
    'accept': 'application/json',
    'Authorization': 'Token 
    'Content-Type': 'application/json'
    }
    requests.request("POST", url, headers=headers, data=payload, verify= False)

devices=list(nb.dcim.devices.all())
ldevice=' '.join([str(item) for item in devices])

for file in files:                                      # On regarde les fichiers exportés de zabbix
    tree = ET.parse(file)
    root = tree.getroot()
    for name in root.findall('./hosts/host/name'):      # On trouve le noms du host
        devname = name.text

        if devname in ldevice:          # On le compare a notre export netbox pour voir
            print("Device deja existant")
            break                                       # il n'existe pas déjà

        for name in root.findall('./hosts/host/groups/group/name'): # On trouve les groupes
            if "Switchs" in name.text:                  # On verifie que le host exporter de zabbix est un switch
                sep = "/"
                names = name
                names = (names.text.split(sep, 1)[0])   # On récupere le nom du groupe d'hote de l'hote

                tenants=list(nb.tenancy.tenants.all())
                ltenant=' '.join([str(item) for item in tenants])

                if names not in ltenant:                       # Si il est dans le fichier de tenant exporter depuis netbo
                    createnant(names)
                
                slug = nb.tenancy.tenants.get(name=names)
                tenid = ""
                tenid = (compten(slug))              # on appelle la fonction de récuperation de tenant id
                siteid = ""
                siteid = (compsite(slug))            # on appelle la fonction de récuperation de site id

                vendors=list(nb.dcim.manufacturers.all())
                #lvendor=' '.join([str(item) for item in vendors])
                a = 0
                for vendor in root.iter('vendor'):              # On récupere le vendeur dans le fichier d'hote zabbix
        
                    vendeur = vendor.text
                    if vendeur == 'Hewlett-Packard' or vendeur == 'Hewlett Packard':
                       vendeur = 'HP'

                    if vendeur in vendors:                      # on regarde si il est déjà dans netbox
                        vendid = (compvend(vendeur))             # si oui on récupere son manufacturer ID
                        a = 1
                                
                    else:
                        creavend(vendeur)                        # sinon on le créer
                        vendid = (compvend(vendeur))
                        a = 1

                if a == 0:
                    vendeur = 'Inconnu'
                    if vendeur in vendors:                      # on regarde si il est déjà dans netbox
                        vendid = (compvend(vendeur))             # si oui on récupere son manufacturer ID
                    else: 
                        creavend(vendeur)                        # sinon on le créer
                        vendid = (compvend(vendeur))

                for type_full in root.iter('type_full'):        # on récupere le modèle du switch dans le fichier d'hote zabbix

                    ldevtype=list(nb.dcim.device_types.all())

                    modele = type_full.text
                    print(modele)
                    if vendeur == 'Inconnu':
                        modele = 'Inconnu'

                    if modele in ldevtype:                      # si il est deja dans netbox on récupere son ID
                        modid = (comptype(modele))
                    else:                                       # sinon on le créer
                        creatype(modele, vendid)
                        modid = (comptype(modele))
                if 'serialno_a' in root.iter('serialno_a'):
                    for serial in root.iter('serialno_a'):
                        serial = serial.text
                else : serial = 'inconnu'

                if 'os' in root.iter('os'):
                    for se in root.iter('os'):                                  # On récupere l'os dans le fichier d'hote zabbix
                        se = se.text
                else: se = 'Inconnu'
                
                for ip in root.iter('ip'):                                  # Les IP serviront a la connexion sur les switchs pour les informations supplémentaires
                    ipv4 = ip.text                                   
                postdevice(devname, se, tenid, siteid, modid, serial)         # appelle de la fonction de création de device

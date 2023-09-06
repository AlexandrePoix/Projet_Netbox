
import xml.etree.ElementTree as ET
from os import listdir, path
import json
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

start_time = time.time()

print("\n" + "DEBUT DE L'EXPORT ZABBIX")
def remove_none(obj):
    """
    Retire les valeurs None 
    Comme expliqué sur : https://stackoverflow.com/a/20558778/6753144
    """
    if isinstance(obj, (list, tuple, set)):
        return type(obj)(remove_none(x) for x in obj if x is not None)
    elif isinstance(obj, dict):
        return type(obj)(
            (remove_none(k), remove_none(v))
            for k, v in obj.items()
            if k is not None and v is not None
        )
    else:
        return obj


def get_zabbix_connection():
    """
    Retourne l'object zbx_pyzabbix, puis on essaie de ce connecter à l'API de zabbix
    """
    # pyzabbix library, with user\password in login method. It's GOOD library
    logging.debug("Try connect to Zabbix by pyzabbix...")
    try:
        zbx_pyzabbix = ZabbixAPI("https://203zabbix.agrom.mousquetaires.com/")
        zbx_pyzabbix.session.verify = False
        zbx_pyzabbix.login(api_token="e508e29b0c3395fc89bd5a8d812caf45")
        return zbx_pyzabbix
    except Exception as e:
        logging.exception(e)

    # py-zabbix library, with user\password in ZabbixAPI

    raise Exception("Some error in pyzabbix or py_zabbix module, see logs")


def order_data(data):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = order_data(value)
        return OrderedDict(sorted(data.items()))
    elif isinstance(data, list):
        data.sort(key=lambda x: str(x))
        return [order_data(x) for x in data]
    else:
        return data


def dumps_json(object, data, directory, key="name", save_yaml=False, drop_keys=[]):
    """
    Create JSON or yaml file in folder
    """
    subfolder = os.path.join(directory, object.lower())
    if not os.path.exists(subfolder):
        os.makedirs(subfolder)

    data = order_data(data)


    for item in data:

        if isinstance(key, tuple):
            logging.debug("Processing {}...".format(item[key[0]]))
        else:
            logging.debug("Processing {}...".format(item[key]))
        if drop_keys:
            for drop_key in drop_keys:
                if drop_key in item:
                    item.pop(drop_key, None)
        txt = json.dumps(item, indent=4)

        # Remove bad characters from name
        if isinstance(key, tuple):
            name = "_".join(map(lambda x: item[x], key))
        else:
            name = item[key]
        name = re.sub(r'[\\/:"*?<>|]+', " ", name)
        filename = "{}/{}.{}".format(subfolder, name, "yaml" if save_yaml else "json")
        filename = os.path.abspath(filename)

        logging.debug("Write to file '{}'".format(filename))

        with open(filename, mode="w", encoding="utf-8", newline="\n") as file:
            file.write(txt)
    



def dump_xml(object, txt, name, directory, save_yaml=False):
    """
    Create XML or YAML in folder
    """
    folder = os.path.join(directory, object.lower())
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Remove bad characters from name
    name = re.sub(r'[\\/:"*?<>|]+', " ", name)
    filename = "{}/{}.{}".format(folder, name, "yaml" if save_yaml else "xml")
    filename = os.path.abspath(filename)

    # Remove bad lines from content
    # date
    txt = re.sub(r"<date>.*<\/date>", "", txt)
    # zabbix.version
    # txt = re.sub(r'<version>.*<\/version>', '', txt)

    # ppretty xml
    xml_ = xml.dom.minidom.parseString(
        txt
    )  # or xml.dom.minidom.parseString(xml_string)
    txt = xml_.toprettyxml(indent="  ", encoding="UTF-8")
    txt = txt.decode()

    # replace xml quot to normal readable "
    txt = txt.replace("&quot;", '"')

    logging.debug("Write to file '{}'".format(filename))
    
    with open(filename, mode="w", encoding="utf-8", newline="\n") as file:
        file.write(txt)
    print('-', end="", flush=True)


def main(zabbix_, save_yaml, directory, only="all"):
    # XML
    # Standart zabbix xml export via API
    def export(zabbix_api, type, itemid, name):
        """
        Export one type: hosts, template, screen or other
        https://www.zabbix.com/documentation/4.0/manual/api/reference/configuration/export
        """
        logging.info("Export {}".format(type))
        items = zabbix_api.get()
        for item in items:
            logging.debug("Processing {}...".format(item[name]))
            try:
                txt = zabbix_.configuration.export(
                    format="xml", options={type: [item[itemid]]}
                )
                dump_xml(
                    object=type,
                    txt=txt,
                    name=item[name],
                    save_yaml=save_yaml,
                    directory=directory,
                )
            except Exception as e:
                logging.error(
                    "Exception during export of template: {}".format(item[name])
                )
                logging.error(e)

    api_version = parse_version(zabbix_.apiinfo.version())
    logging.debug("Source Zabbix server version: {}".format(api_version))
    
    export(zabbix_.host, "hosts", "hostid", "name")

    # JSON
    # not support `export` method
    # Read more in https://www.zabbix.com/documentation/4.0/manual/api/reference/configuration/export
    logging.info("Start export JSON part...")



    # logging.info("Processing services...")
    # services = zabbix_.service.get(selectParent=['name'], selectTimes='extend')
    # dumps_json(object='services', data=services, key=('name', 'serviceid'), save_yaml=save_yaml, directory=directory, drop_keys=["status"])


def environ_or_required(key):
    "Argparse environment vars helper"
    if os.environ.get(key):
        return {"default": os.environ.get(key)}
    else:
        return {"required": True}


def init_logging(level):
    logger_format_string = "%(asctime)s %(levelname)-8s %(message)s"
    logging.basicConfig(level=level, format=logger_format_string, stream=sys.stdout)


if __name__ == "__main__":
    args = "hosts"

    zabbix_ = get_zabbix_connection(
    )

    #logging.info("All files will be save in {}".format(os.path.abspath(args.directory)))
    main(
        zabbix_=zabbix_,
        save_yaml=False,
        directory="./",
        only="hosts"
    )

print("\n" + "FIN DE L'EXPORT")

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
FIN DE L'EXPORT ZABBIX DÉBUT DU L'IMPORT DANS NETBOX
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

print("\nIMPORT EN COURS SUR 
nb = pynetbox.apitoken = threading=True)
nb.http_session.verify = False                              # désactive la connexion avec certificat pour netbox


mypath = './hosts'                                          # chemin vers les fichiers exporter de zabbix

files=[path.join(mypath, f) for f in listdir(mypath) if f.endswith('.xml')]

def postdevice(devname, newos, tenid, siteid, modid, serial):    #   création d'une fonction permettant l'ajout d'un device sur netbox
    url = " 							#   url de netbox (à changer en cas de migration) suivi de /api/dcim/devices/ pour pointer vers l'url
                                                            #   des devices
    payload = json.dumps({
    "name": devname,
    "device_type": modid,
    "device_role": "1",
    "tenant": tenid,
    "site": siteid,
    "custom_fields":{
    "OS": newos,
    "Numero_de_serie": serial
    }
    })
    headers = {
    'accept': 'application/json',
    'Authorization': 'Token ',
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

def comptype(modele):
    #typeslug = nb.dcim.device_types.get(model = modele)
    t = nb.dcim.device_types.get(model = modele)
    modid = t.id
    return modid

def compvend(vendor):
    v = nb.dcim.manufacturers.get(name = vendor)
    vendid = v.id
    print(vendid)
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
    'Authorization': '',
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

    url = types/"

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
    requests.request("POST", url, headers=headers, data=payload, verify=False)

def upos(newos, decid):                                       # fonction de création de vendeur (manufacturer)    
   
    url = 

    payload = json.dumps({
    
   "custom_fields": {
        "OS": newos
    }
    })
    headers = {
    'accept': 'application/json',
    'Authorization': 'Token 
    'Content-Type': 'application/json'
    }
    request = requests.request("PATCH", url, headers=headers, data=payload, verify=False)
    print(request)


devices=list(nb.dcim.devices.all())
ldevice=' '.join([str(item) for item in devices])

tenants=list(nb.tenancy.tenants.all())
ltenant=' '.join([str(item) for item in tenants])

vendors=list(nb.dcim.manufacturers.all())

ldevtype=list(nb.dcim.device_types.all())

for file in files:                                      # On regarde les fichiers exportés de zabbix
    devname = ''
    newos = ''
    tenid = ''
    siteid = ''
    modid = ''
    serial = ''
    oldserial = ''
    
    tree = ET.parse(file)
    root = tree.getroot()
    for name in root.findall('./hosts/host/name'):      # On trouve le noms du host
        devname = name.text

        if devname in ldevice:          # On le compare a notre export netbox pour voir
            print("Device deja existant")
            dec = nb.dcim.devices.get(name=devname)
            decid = dec.id
            for newos in root.iter('os'):                                  # On récupere l'os dans le fichier d'hote zabbix
                newos = newos.text
                print(newos)
            if dec.custom_fields.get('OS') == newos:
                print("pas de changements")
                break
            else: 
                upos(newos, decid)
                break                                     # il n'existe pas déjà

        else:
            for name in root.findall('./hosts/host/groups/group/name'): # On trouve les groupes
                if "Switchs" in name.text:                  # On verifie que le host exporter de zabbix est un switch
                    sep = "/"
                    names = name
                    names = (names.text.split(sep, 1)[0])   # On récupere le nom du groupe d'hote de l'hote

                    if names not in ltenant:                       # Si il est dans le fichier de tenant exporter depuis netbo
                        tenants=list(nb.tenancy.tenants.all())
                        ltenant=' '.join([str(item) for item in tenants])
                        if names not in ltenant:                       # Si il est dans le fichier de tenant exporter depuis netbo    
                            createnant(names)
                    
                    slug = nb.tenancy.tenants.get(name=names)
                    tenid = ""
                    tenid = (compten(slug))              # on appelle la fonction de récuperation de tenant id
                    siteid = ""
                    siteid = (compsite(slug))            # on appelle la fonction de récuperation de site id


                    checker = 0
                    for vendor in root.iter('vendor'):              # On récupere le vendeur dans le fichier d'hote zabbix
            
                        vendeur = vendor.text
                        if vendeur == 'Hewlett-Packard' or vendeur == 'Hewlett Packard':
                            vendeur = 'HP'

                        if vendeur in vendors:                      # on regarde si il est déjà dans netbox
                            vendid = (compvend(vendeur))             # si oui on récupere son manufacturer ID
                            checker = 1
                                    
                        else:
                            vendors=list(nb.dcim.manufacturers.all())
                            if vendeur in vendors:
                                vendid = (compvend(vendeur))             # si oui on récupere son manufacturer ID
                                checker = 1
                            else:
                                creavend(vendeur)                        # sinon on le créer
                                vendid = (compvend(vendeur))
                                checker = 1

                    if checker == 0:
                        vendeur = 'Inconnu'
                        if vendeur in vendors:                      # on regarde si il est déjà dans netbox
                            vendid = (compvend(vendeur))             # si oui on récupere son manufacturer ID
                        else: 
                            creavend(vendeur)                        # sinon on le créer
                            vendid = (compvend(vendeur))

                    for type_full in root.iter('type_full'):        # on récupere le modèle du switch dans le fichier d'hote zabbix

                        modele = type_full.text
                        print(devname)
                        if vendeur == 'Inconnu':
                            modele = 'Inconnu'

                        if modele in ldevtype:                      # si il est deja dans netbox on récupere son ID
                            modid = (comptype(modele))
                        else:                                       # sinon on le créer
                            ldevtype=list(nb.dcim.device_types.all())
                            if modele in ldevtype:                      # si il est deja dans netbox on récupere son ID
                                modid = (comptype(modele))
                            else:
                                creatype(modele, vendid)
                                modid = (comptype(modele))

                    for newos in root.iter('os'):                                  # On récupere l'os dans le fichier d'hote zabbix
                        newos = newos.text

                    for serial in root.iter('serialno_a'):
                        serial = serial.text
                        if oldserial == serial:
                            serial = ""
                        oldserial = serial
                    
                    for ip in root.iter('ip'):                                  # Les IP serviront a la connexion sur les switchs pour les informations supplémentaires
                        ipv4 = ip.text

                    postdevice(devname, newos, tenid, siteid, modid, serial)         # appelle de la fonction de création de device

print("--- %s secondes ---" % (time.time() - start_time))

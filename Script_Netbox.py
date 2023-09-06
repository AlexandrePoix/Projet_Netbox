
import asyncio
import xml.etree.ElementTree as ET
from os import listdir, path
import json
import requests
import pynetbox
import json
from multiprocessing.dummy import Pool
from netaddr import IPAddress
import logging
import os
import filecmp
import re
import sys
import shutil
import time
from netmiko import ConnectHandler 
import threading 
import xml.dom.minidom
from collections import OrderedDict
import urllib3
from pyzabbix import ZabbixAPI
from pkg_resources import parse_version

urllib3.disable_warnings()
start_time = time.time()

"""
Variables
"""
type_de_log = 'debug' # defaut = 'info', en cas de problème changez en "debug" et executez à nouveau (faire le ménage dans le fichier de log après)

token_netbox = ''
url_netbox = 'url' # bien mettre le / a la fin

url_zabbix = 'url'
token_zabbix = 'token'

username = 'compte admin'
password = 'mdp admin'

"""
"""

if type_de_log == 'info':
    logging.basicConfig(filename='./log/netbox_log.log', encoding='utf-8', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    logging.getLogger("paramiko").setLevel(logging.INFO)
else:
    logging.basicConfig(filename='./log/netbox_log.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
    logging.getLogger("paramiko").setLevel(logging.WARNING)


#print("\n" + "DEBUT DE L'EXPORT ZABBIX")
'''
try:
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
            zbx_pyzabbix = ZabbixAPI(url_zabbix)
            zbx_pyzabbix.session.verify = False
            zbx_pyzabbix.login(api_token=token_zabbix)
            return zbx_pyzabbix
        except Exception as e:
            logging.exception(e)

        # py-zabbix library, with user\password in ZabbixAPI

        raise Exception("Some error in pyzabbix or py_zabbix module, see logs")

    """
    Organise les fichiers exportés
    """
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

        
        with open(filename, mode="w", encoding="utf-8", newline="\n") as file:
            file.write(txt)
        #print('-', end="", flush=True)
        


    def main(zabbix_, save_yaml, directory, only="all"):
        # XML
        # Standart zabbix xml export via API
        def export(zabbix_api, type, itemid, name):
            """
            Export one type: hosts, template, screen or other
            https://www.zabbix.com/documentation/4.0/manual/api/reference/configuration/export
            """
            logging.info("Debut de l'export")
            items = zabbix_api.get()
            logging.debug("Processing...")
            for item in items:
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

        #logging.debug("Source Zabbix server version")
        
        export(zabbix_.host, "hosts", "hostid", "name")

        # JSON
        # not support `export` method
        # Read more in https://www.zabbix.com/documentation/4.0/manual/api/reference/configuration/export
        #logging.info("Start export JSON part...")



        # logging.info("Processing services...")
        # services = zabbix_.service.get(selectParent=['name'], selectTimes='extend')
        # dumps_json(object='services', data=services, key=('name', 'serviceid'), save_yaml=save_yaml, directory=directory, drop_keys=["status"])


    def environ_or_required(key):
        "Argparse environment vars helper"
        if os.environ.get(key):
            return {"default": os.environ.get(key)}
        else:
            return {"required": True}



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
    

    logging.info("Execution de l'export terminée")
except:
  logging.error("Erreur critique pendant l'exportation Zabbix, verifiez le token et l'url du serveur Zabbix", exc_info=True)

#print("\n" + "FIN DE L'EXPORT")

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
FIN DE L'EXPORT ZABBIX DÉBUT DU L'IMPORT DANS NETBOX
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
'''
#print("\nIMPORT EN COURS SUR NETBOX")
logging.info("Debut de l'importation sur Netbox")
nb = pynetbox.api(url_netbox, token = token_netbox, threading=True)
nb.http_session.verify = False                              # désactive la verification du certificat pour netbox

try:
    nb.status() # verification du fonctionnement de la connexion
except: 
    logging.critical('Connexion impossible au serveur Netbox')

mypath = './hosts'                                          # chemin vers les fichiers exporter de zabbix

files=[path.join(mypath, f) for f in listdir(mypath) if f.endswith('.xml')] # récupération des fichiers dans le chemin 'mypath'

def postdevice(devname, newos, tenid, siteid, modid, serial, ip):    #   création d'une fonction permettant l'ajout d'un device sur netbox
    try :
        url = url_netbox + "api/dcim/devices/"           #   url de netbox (à changer en cas de migration) suivi de api/dcim/devices/
        payload = json.dumps({
        "name": devname,
        "device_type": modid,
        "device_role": "1",
        "tenant": tenid,
        "serial": serial,
        "site": siteid,
        "custom_fields":{
        "OS": newos
        }
        })
        headers = {
        'accept': 'application/json',
        'Authorization': 'Token ' + token_netbox,
        'Content-Type': 'application/json'
        }
        
        requests.request("POST", url, headers=headers, data=payload, verify=False)
        decid = nb.dcim.devices.get(name=devname)
        decid = decid.id
        ips.append(ip + ',' + str(decid))
        logging.info(devname + " ajouté")
    except: logging.warning("Échec de la création de " + devname)

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
    return vendid

def createnant(names):                                       # fonction de création de vendeur (manufacturer)    
    
    tenslug = ''.join(names.split()).lower()
    tenslug = tenslug.translate(str.maketrans('','', '"!#$%&()*+_,./:;<=>?@[\]^`{|}~'))

    url = url_netbox + "api/tenancy/tenants/"

    payload = json.dumps({
    "name": names,
    "slug": tenslug
    })
    headers = {
    'accept': 'application/json',
    'Authorization': 'Token ' + token_netbox,
    'Content-Type': 'application/json'
    }

    requests.request("POST", url, headers=headers, data=payload, verify=False)

    x = nb.tenancy.tenants.get(slug = tenslug)                 # utilisation de netboxapi pour trouver le tenant correspondant à celui exporter de zabbix
    tenid = x.id

    url = url_netbox + "api/dcim/sites/"

    payload = json.dumps({
    "name": names,
    "slug": tenslug,
    "tenant": tenid
    })
    headers = {
    'accept': 'application/json',
    'Authorization': 'Token ' + token_netbox,
    'Content-Type': 'application/json'
    }

    requests.request("POST", url, headers=headers, data=payload, verify=False)


def creavend(vendor):                                       # fonction de création de vendeur (manufacturer)    
    vendslug = ''.join(vendor.split()).lower()
    vendslug = vendslug.translate(str.maketrans('','', '"!#$%&()*+_,./:;<=>?@[\]^`{|}~'))

    url = url_netbox + "api/dcim/manufacturers/"

    payload = json.dumps({
    "name": vendor,
    "slug": vendslug
    })
    headers = {
    'accept': 'application/json',
    'Authorization': 'Token  ' + token_netbox,
    'Content-Type': 'application/json'
    }

    requests.request("POST", url, headers=headers, data=payload, verify=False)


def creatype(modele, vendid):                                # fonction de création de modèle (device-type) au travers de l'API de netbox

    typeslug = ''.join(modele.split()).lower()
    typeslug = typeslug.translate(str.maketrans('','', '"!#$%&()*+_,./:;<=>?@[\]^`{|}~'))

    url = url_netbox + "api/dcim/device-types/"

    payload = json.dumps({
    "manufacturer": vendid,
    "model": modele,
    "slug": typeslug
    })
    headers = {
    'accept': 'application/json',
    'Authorization': 'Token  ' + token_netbox,
    'Content-Type': 'application/json'
    }
    requests.request("POST", url, headers=headers, data=payload, verify=False)

def upos(newos, decid):                                       # fonction de création de vendeur (manufacturer)    
   
    url = url_netbox + "api/dcim/devices/"+str(decid)+"/"
    payload = json.dumps({
    
   "custom_fields": {
        "OS": newos
    }
    })
    headers = {
    'accept': 'application/json',
    'Authorization': 'Token  ' + token_netbox,
    'Content-Type': 'application/json'
    }
    requests.request("PATCH", url, headers=headers, data=payload, verify=False)

devices=list(nb.dcim.devices.all())
ldevice=' '.join([str(item) for item in devices])
tenants=list(nb.tenancy.tenants.all())
ltenant=' '.join([str(item) for item in tenants])
vendors=list(nb.dcim.manufacturers.all())
ldevtype=list(nb.dcim.device_types.all())
ips= []
for file in files:                                      # On regarde les fichiers exportés de zabbix
    devname = ''
    newos = ''
    tenid = ''
    siteid = ''
    modid = ''
    serial = ''
    oldserial = ''
    checker = 0
    tree = ET.parse(file)
    root = tree.getroot()
    with open(file, 'r') as f:
        try:
            if 'Switchs' not in f.read():
                continue
            for name in root.findall('./hosts/host/name'):      # On trouve le noms du host
                devname = name.text
                for ip in root.iter('ip'):                                  # Les IP serviront a la connexion sur les switchs pour les informations supplémentaires
                    if ip != '':
                        ip = ip.text
                    else:
                        continue
                        
                if devname in ldevice:          # On le compare a notre export netbox pour voir
                    dec = nb.dcim.devices.get(name=devname)
                    decid = dec.id
                    for ip in root.iter('ip'):                                  # Les IP serviront a la connexion sur les switchs pour les informations supplémentaires
                        ip = ip.text
                        ips.append(ip + ',' + str(decid))
                        logging.debug(devname + " deja dans Netbox : " + ip)
                        break

                    for newos in root.iter('os'):                                  # On récupere l'os dans le fichier d'hote zabbix
                        newos = newos.text
                    if dec.custom_fields.get('OS') == newos:
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
                            if names not in ltenant:                       # Si il est dans le fichier de tenant exporter depuis netbox
                                tenants=list(nb.tenancy.tenants.all())
                                ltenant=' '.join([str(item) for item in tenants])
                                if names not in ltenant:                       # Si il est dans le fichier de tenant exporter depuis netbox
                                    createnant(names)
                            
                            slug = nb.tenancy.tenants.get(name=names)
                            tenid = ""
                            tenid = (compten(slug))              # on appelle la fonction de récuperation de tenant id
                            siteid = ""
                            siteid = (compsite(slug))            # on appelle la fonction de récuperation de site id
                            for type_full in root.iter('type_full'):        # on récupere le modèle du switch dans le fichier d'hote zabbix
                                modele = type_full.text
                            for vendor in root.iter('vendor'):              # On récupere le vendeur dans le fichier d'hote zabbix
                    
                                vendeur = vendor.text
                                checker = 1
                                if vendeur == 'Hewlett-Packard' or vendeur == 'Hewlett Packard' or modele.startswith('HP ') or modele.startswith('Aruba JL'):
                                    vendeur = 'HP'
                                if vendeur in vendors:                      # on regarde si il est déjà dans netbox
                                    vendid = (compvend(vendeur))             # si oui on récupere son manufacturer ID
                                                                            
                                else:
                                    vendors=list(nb.dcim.manufacturers.all())
                                    if vendeur in vendors:
                                        vendid = (compvend(vendeur))             # si oui on récupere son manufacturer ID
                                    else:
                                        creavend(vendeur)                        # sinon on le créer
                                        vendid = (compvend(vendeur))
                            if checker == 0:
                                break
                            for type_full in root.iter('type_full'):        # on récupere le modèle du switch dans le fichier d'hote zabbix
                                modele = type_full.text
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
                                break
                            for ip in root.iter('ip'):                                  # Les IP serviront a la connexion sur les switchs pour les informations supplémentaires
                                ip = ip.text
                            postdevice(devname, newos, tenid, siteid, modid, serial,ip)         # appelle de la fonction de création de device
        except: logging.warning('Traitement du fichier ' + devname + ' impossible.')
#shutil.rmtree('./hosts')


class procurve:

    def sshvlan(ssh, expect_string, tenid, siteid):
        lvlan=[] #création d'une liste pour les vlans
        commande = "show vlan"
        output = ssh.send_command(commande, expect_string=expect_string) #envoie de la commande show vlan
        with open('./res/vlan.txt', 'w') as v:
            v.write(output)
            v.close
        with open('./res/vlan.txt', 'r') as r:
            for line in r: #pour chaque ligne dans le fichier 
                vlan = line.split('   ')[0].replace(' ', '')
                l = line.split(' ')
                while '' in l: l.remove('')
                try:
                    int(l[0])
                    vlaname = l[1] # si l est un nombre (vlan id) on l'ajoute a la variable
                except:continue
                if nb.ipam.vlans.get(vid=vlan, tenant_id= tenid) == None: #si le vlan n'existe pas on le créer
                    nb.ipam.vlans.create(name=vlaname, vid=vlan, status='active', tenant=tenid, site=siteid)
                lvlan.append(vlan) # on l'ajoute a la liste
                r.close
        procurve.sshint(lvlan, ssh, expect_string, decid, tenid)

    
    def sshint(lvlan, ssh, expect_string, decid, tenid):
        commande = "show ip"
        print(commande)
        output = ssh.send_command(commande, expect_string=expect_string)
        with open('./res/ip.txt', 'w') as i:
            i.write(output)
        with open('./res/ip.txt') as r:
            i = 0
            for line in r:
                if "--------" in line:
                    i = 1
                    continue
                if i == 1:
                    try: 
                        x = line.split(' ')
                        x = list(filter(None, x))
                        ip = x[3]
                        submask = x [4]
                    except: continue
                    try:
                        intid = nb.dcim.interfaces.create(device=decid, name='management', type='virtual').id # si l'interface vlan303 existe pas on la créer
                    except:
                        intid = nb.dcim.interfaces.get(device_id=decid, name='management', type='virtual').id # sinon on l'a créer
                    maskcidr=IPAddress(submask).netmask_bits() # conversion du format x.x.x.x en CIDR
                    ip = ip+'/'+str(maskcidr) # on ajoute le masque a l'IP
                    if nb.ipam.ip_addresses.get(address=ip,tenant_id=tenid) == None: # si l'ip n'est pas dans netbox
                        ipid = nb.ipam.ip_addresses.create(address=ip, tenant=tenid, assigned_object_type='dcim.interface' ,assigned_object_id=intid).id # on créer l'ip
                    else:ipid = nb.ipam.ip_addresses.get(address=ip, tenant_id=tenid).id # sinon on l'a récupere
                    dec = nb.dcim.devices.get(id=decid) # on récupere l'objet
                    dec.primary_ip4 = ipid # on ajoute l'ip a l'objet
                    dec.save() # on met a jour l'objet dans netbox
                    r.close
        lint=[] # creation d'une liste pour les interfaces
        commande = "show interface brief" # on fait des show vlans pour tout les vlans
        output = ssh.send_command(commande, expect_string=expect_string)
        with open('./res/int.txt', 'w') as v:
            v.write(output)
            v.close
        i = 0
        with open('./res/int.txt', 'r') as r:
            for line in r: # pour chaque ligne dans le show vlan x
                if  '--------' in line: # tries dans les lignes pour ne récuperer que les interfaces
                    i = 1
                    continue
                if i==0 or line == '': continue
                line = line.split(' ')
                line = list(filter(None, line))
                inte = line[0]
                print('inte = ' + inte)
                if inte == '\n': continue
                try:
                    if inte not in lint: # si l'interface n'est pas encore dans la liste des vlans
                        lint.append(inte) # on l'ajoute
                    if 'Up' in line: status = 1 # si l'interface est up on change la valeur de status
                    else: status = 0
                    typ='1000base-t' # a changer, par défaut les interfaces sont en 1Ge
                    try:
                        nb.dcim.interfaces.create(device=decid, name=str(inte), type=typ, enabled=status) # on créer l'interface
                        logging.debug('Interface ' +  inte + ' sur le device ' + decid + ' créé')
                    except: pass
                except: pass
                #else: print('non')
                r.close
                print(lint)

                try:
                    print('interface : ' + inte)
                    inter=nb.dcim.interfaces.get(name=str(inte), device_id=decid) # on récupere l'objet netbox de l'interface
                    commande = 'show vlan ports ' + str(inte) + ' detail' 
                    print(commande)
                    output = ssh.send_command(commande, expect_string=expect_string)
                    with open('./res/tempint.txt', 'w') as t: 
                        t.write(output)
                    with open('./res/tempint.txt', 'r') as t:
                        taggvlan=[]
                        for line in t: # pour chaque ligne dans le fichier
                            if line == '\n': continue # on skip les lignes vide
                            vlanid = line.split('   ')[0].replace(' ', '') 
                            try: 
                                int(vlanid) # on verife que le vid est bien un numero
                                tem=nb.ipam.vlans.get(vid=vlanid,tenant_id=tenid).id
                                if 'Tagged' in line: # si tagged dans la ligne, l'interface est taggé
                                    vlanid2=nb.ipam.vlans.get(vid=vlanid, tenant_id=tenid).id # on récupere les vlans déjà sur l'interface
                                    if vlanid2 not in taggvlan: # si l'interface n'est pas encore dans la liste des vlans tag
                                        taggvlan.append(vlanid2) # on l'ajoute
                                elif 'Untagged' in line: # si untagged dans la ligne
                                    untagid=nb.ipam.vlans.get(vid=vlanid,tenant_id=tenid).id # on récupere l'objet vlan dans netbox
                                    inter.update({"untagged_vlan" : untagid}) # on update l'interface avec les vlans untagged
                                else: continue
                                tint=nb.dcim.interfaces.get(device_id=decid, name=str(inte))
                            except: 
                                continue
                        if taggvlan==[]:
                            inter.update({"mode" : "access", "untagged_vlan" : untagid}) # si il n'y a pas d'interface tagged, on ajoute le tag 'untagged' sur l'interface
                        else:
                            inter.update({"mode" : "tagged", "tagged_vlans" : taggvlan}) # sinon on ajoute les vlans tag
                except:
                        logging.error("L'interface " + inte + "n'a pas pu être récuperé")
                        continue
            r.close


class aruba:
    def sshvlan(ssh, expect_string, tenid, siteid):
        try:
            lvlan=[]
            commande = "show vlan"
            output = ssh.send_command(commande, expect_string=expect_string)
            with open('./res/vlan.txt', 'w') as v:
                v.write(output)
                v.close
            with open('./res/vlan.txt', 'r') as r:
                i = 0
                for line in r:
                    if i != 2: # on attend d'avoir vu les deux lignes -------- dans le fichier 
                        if '---------------------------------------------------------------------------------------------------' in line:
                            i = i+1
                            continue
                        else: continue
                    spl = line.split(' ') # on split la ligne
                    spl = list(filter(None, spl))
                    vid = spl[0] # on récupere le vlan id
                    try: spl[1]
                    except: continue
                    vlaname = spl[1] # le nom du vlan
                    try:
                        int(vid) # on verifie que le vid est l'id d'un vlan
                    except: continue
                    if nb.ipam.vlans.get(vid=vid, tenant_id= tenid) == None: # si le vlan n'existe pas dans netbox
                        try:
                            nb.ipam.vlans.create(name=vlaname, vid=vid, status='active', tenant=tenid, site=siteid) # on le créer
                        except: logging.error('Création du vlan ' + vid + 'dans ' + tenid)
                    lvlan.append(vid) # on l'ajoute a la liste de vlan
                    r.close
                return(lvlan)
            
        except: 
            r.close
            logging.error('Erreur pendant aruba.sshvlan')

    def sshint(lvlan, ssh, expect_string, decid, tenid):
        try:
            lint=[]
            commande = "show interface brief"
            output = ssh.send_command(commande, expect_string=expect_string)
            with open('./res/int.txt', 'w') as v:
                v.write(output)
                v.close
            with open('./res/int.txt', 'r') as r:
                i = 0
                for line in r: 
                    if i != 2: # on attend d'avoir vu les deux lignes -------- dans le fichier 
                        if '------------------------------------------------------------' in line:
                            i = i+1
                            continue
                        else: continue
                    spl = line.split(' ') # on split la ligne
                    spl = list(filter(None, spl)) # on retire les elements vide de la liste
                    inte = spl[0] # on récupere l'interface
                    print('int' + str(inte))
                    if 'up' in line: status = 1 # si elle est up on la tag up
                    else: status = 0 # sinon elle est down
                    try:
                        if inte not in lint: # si l'interface est pas dans la liste des interfaces
                            lint.append(inte)  # on l'ajoute a la liste
                        if 'up' in line: status = 1 # si elle est up on la tag up
                        else: status = 0 # sinon elle est down
                        if spl[1] == '--' and spl[2]: # si il y a -- c'est une interface virtuelle
                            continue
                        else: typ='1000base-t' # a changer, par défaut les interfaces sont en 1Ge
                        try:
                            nb.dcim.interfaces.create(device=decid, name=str(inte), type=typ, enabled=status) # on essaie de créer l'interface
                        except: pass
                    except: continue
                        #else: print('non')
                    r.close

                    print('interface : ' + inte)
                    inter=nb.dcim.interfaces.get(name=str(inte), device_id=decid) # on récupere l'objet 
                    commande = 'show vlan port ' + str(inte)
                    try:
                        output = ssh.send_command(commande, expect_string=expect_string)
                    except:
                        continue
                    #print(output)
                    with open('./res/intconf.txt', 'w') as v:
                        v.write(output)
                        v.close
                    with open('./res/intconf.txt', 'r') as r:
                        taggvlan=[]
                        i = 0
                        for line in r:
                            if i != 2: # on attend d'avoir vu les deux lignes -------- dans le fichier 
                                if '------------------------------------------------' in line:
                                    i = i+1
                                    continue
                                else: continue   
                            vlanid = line.split(' ')[0]
                            if 'trunk' in line: # si trunk dans la ligne, l'interface est trunk
                                vlanid2=nb.ipam.vlans.get(vid=vlanid, tenant_id=tenid).id
                                if vlanid2 not in taggvlan:
                                    taggvlan.append(vlanid2) # si pas dans la liste on ajoute
                            elif 'access' in line: # si access interface access
                                untagid=nb.ipam.vlans.get(vid=vlanid,tenant_id=tenid).id
                                inter.update({"untagged_vlan" : untagid}) # on met a jour l'interface
                            elif 'native-untagged' in line: # si native untagged
                                untagid=nb.ipam.vlans.get(vid=vlanid,tenant_id=tenid).id
                                inter.update({"untagged_vlan" : untagid}) # on met a jour l'interface
                            else: continue
                            if taggvlan==[]:
                                inter.update({"mode" : "access", "untagged_vlan" : untagid}) # si il n'y a pas d'interface tagged, on ajoute le tag 'untagged' sur l'interface
                            else:
                                inter.update({"mode" : "tagged", "tagged_vlans" : taggvlan}) # sinon on ajoute les vlans tag
                            r.close
                aruba.sship(ip,decid,tenid)
        except:logging.error('Erreur pendant aruba.sshint')

    def sship(ip,decid,tenid):
        try:
            commande = "show ip interface brief"
            output = ssh.send_command(commande, expect_string=expect_string)
            with open('./res/ip.txt', 'w') as i:
                i.write(output)
            with open('./res/ip.txt', 'r') as r:
                for line in r:
                    if 'Address' in line:
                        continue
                    else:
                        if '.' in line:
                            try:
                                intid = nb.dcim.interfaces.create(device=decid, name='management', type='virtual').id
                            except:
                                intid = nb.dcim.interfaces.get(device_id=decid, name='management', type='virtual').id
                            lip = line.split(' ')
                            lip = list(filter(None, lip))
                            ip = lip[1]
                            if nb.ipam.ip_addresses.get(address=ip,tenant_id=tenid) == None:
                                ipid = nb.ipam.ip_addresses.create(address=ip, tenant=tenid, assigned_object_type='dcim.interface' ,assigned_object_id=intid).id
                            else:ipid = nb.ipam.ip_addresses.get(address=ip, tenant_id=tenid).id
                            dec = nb.dcim.devices.get(id=decid)
                            dec.primary_ip4 = ipid
                            dec.save()
                            r.close
        except: logging.error('Erreur pendant aruba.sship')

#ips = ['172.30.205.136,49645','172.30.205.140,49843']
for item in ips:
    try:
        ip = item.split(',', 1)[0]
        decid=item.split(',', 1)[1]
        print(ip)
        print(decid)
        dec = nb.dcim.devices.get(id=decid)
        tenid=dec.tenant.id
        siteid=dec.site.id
        if decid == None:
            continue
        
        if dec.device_type.manufacturer == nb.dcim.manufacturers.get(name='HP'):
            try:
                ssh = ConnectHandler(device_type='hp_procurve', ip=ip, username=username, password=password) 
            except:
                logging.error('Connexion a ' + ip + ' impossible.')
            expect_string = ssh.find_prompt()
            ssh.send_command("terminal length 500", expect_string=expect_string)
            commande="show run"
            output = ssh.send_command(commande, expect_string=expect_string)
            with open('./run/'+decid+'.txt', 'w') as newid:
                newid.write(output)
            with open('./run/'+decid+'.txt', 'r') as newid:
                try:
                    with open('./old/'+decid+'.txt', 'r') as oldid:
                        if filecmp.cmp('./old/'+decid+'.txt', './run/'+decid+'.txt') == True:
                            continue

                    with open('./old/'+decid+'.txt', 'w') as newid:
                        newid.write(output)
                    
                except:
                    with open('./old/'+decid+'.txt', 'w') as newid:
                        newid.write(output)

                logging.info('Modification du device : '  + str(dec))
                lvlan = procurve.sshvlan(ssh, expect_string, tenid, siteid)
                
        

        if dec.device_type.manufacturer == nb.dcim.manufacturers.get(name='Aruba'):
            try:
                ssh = ConnectHandler(device_type='aruba_os', ip=ip, username=username, password=password) 
                expect_string = ssh.find_prompt()
                ssh.send_command("no page", expect_string=expect_string)
                commande="show run"
                output = ssh.send_command(commande, expect_string=expect_string)
            except:
                logging.error('Connexion sur ' + ip + ' impossible.')

            with open('./run/'+decid+'.txt', 'w') as newid:
                newid.write(output)
            with open('./run/'+decid+'.txt', 'r') as newid:
                try:
                    with open('./old/'+decid+'.txt', 'r') as oldid:
                        if filecmp.cmp('./old/'+decid+'.txt', './run/'+decid+'.txt') == True:
                            print("yup")
                            continue
                        else: pass
                    with open('./old/'+decid+'.txt', 'w') as newid:
                        newid.write(output)
                except:
                    with open('./old/'+decid+'.txt', 'w') as newid:
                        newid.write(output)
                logging.info('Modification du device : '  + str(dec))
                lvlan = aruba.sshvlan(ssh, expect_string, tenid, siteid)
                aruba.sshint(lvlan, ssh, expect_string, decid, tenid)
        #else: print("faux")
    except:
        logging.error('Erreur pendant le traitement de ' + item)
        continue
logging.info('Mise a jour de Netbox terminé \n')


print("\n" + "--- %s secondes ---" % (time.time() - start_time))

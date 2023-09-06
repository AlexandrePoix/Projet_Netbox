
import xml.etree.ElementTree as ET
from os import listdir, path
from netaddr import IPAddress
import json
import requests
import pynetbox
import json
import logging
import filecmp
import os
from netmiko import ConnectHandler 
import re
import sys
import time
import xml.dom.minidom
from collections import OrderedDict
import urllib3
from pyzabbix import ZabbixAPI
from pkg_resources import parse_version
import shutil
urllib3.disable_warnings()
start_time = time.time()
nb = pynetbox.api('url netbox', token = 'token netbox')
nb.http_session.verify = False


logging.basicConfig(filename='./log/netbox_log.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')


username = ''
password = ''

ips = ['']

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
                    print(spl)
                    vid = spl[0] # on récupere le vlan id
                    if len(vid) > 5:
                        continue
                    print('vlanid au dessus')
                    vlaname = spl[1] # le nom du vlan
                    try:
                        int(vid) # on verifie que le vid est l'id d'un vlan
                    except: continue
                    if nb.ipam.vlans.get(vid=vid, tenant_id= tenid) == None: # si le vlan n'existe pas dans netbox
                        try:
                            nb.ipam.vlans.create(name=vlaname, vid=vid, status='active', tenant=tenid, site=siteid) # on le créer
                        except: logging.error('Création du vlan ' + vid + 'dans ' + tenid)
                    lvlan.append(vid) # on l'ajoute a la liste de vlan
                return(lvlan)
        except: logging.error('Erreur pendant aruba.sshvlan')

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
                        if '--------------------------------------------------------------------------------------' in line:
                            i = i+1
                            continue
                        else: continue
                    spl = line.split(' ') # on split la ligne
                    spl = list(filter(None, spl)) # on retire les elements vide de la liste
                    inte = spl[0] # on récupere l'interface
                    if 'Up' in line: status = 1 # si elle est up on la tag up
                    else: status = 0 # sinon elle est down
                    try:
                        if inte not in lint: # si l'interface est pas dans la liste des interfaces
                            lint.append(inte)  # on l'ajoute a la liste
                        if 'up' in line: status = 1 # si elle est up on la tag up
                        else: status = 0 # sinon elle est down
                        if spl[1] == '--': # si il y a -- c'est une interface virtuelle
                            continue
                        else: typ='1000base-t' # a changer, par défaut les interfaces sont en 1Ge
                        try:
                            nb.dcim.interfaces.create(device=decid, name=str(inte), type=typ, enabled=status) # on essaie de créer l'interface
                        except: pass
                    except: pass
                        #else: print('non')

            for x in lint: # pour chaque interface dans la liste 

                inter=nb.dcim.interfaces.get(name=str(x), device_id=decid) # on récupere l'objet 
                commande = 'show vlan port ' + str(x)
                output = ssh.send_command(commande, expect_string=expect_string)
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
        except: logging.error('Erreur pendant aruba.sship')


for item in ips:
    try:
        ip = item.split(',', 1)[0]
        decid=item.split(',', 1)[1]
        print(ip)
        print(decid)
        dec = nb.dcim.devices.get(id=decid)
        tenid=dec.tenant.id
        siteid=dec.site.id
        print(decid)
        if decid == None:
            continue
        '''
        if dec.device_type.manufacturer == nb.dcim.manufacturers.get(name='HP') and tenid == 1512:
            try:
                ssh = ConnectHandler(device_type='hp_procurve', ip=ip, username=username, password=password) 
            except:
                logging.error('Connexion sur ' + ip + ' impossible.')
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
                            print("yup")
                            continue
                        else: pass
                    with open('./old/'+decid+'.txt', 'w') as newid:
                        newid.write(output)
                    
                except:
                    with open('./old/'+decid+'.txt', 'w') as newid:
                        newid.write(output)

                logging.info('Modification du device : '  + str(dec))
                lvlan = procurve.sshvlan(ssh, expect_string, tenid, siteid)
                procurve.sshint(lvlan, ssh, expect_string, decid, tenid)
        '''

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

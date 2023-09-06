
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
nb = pynetbox.apitoken = 
nb.http_session.verify = False


username = 
password = '


class aruba:
    def sshvlan(ssh, expect_string, tenid, siteid):
        lvlan=[]
        commande = "show vlan"
        output = ssh.send_command(commande, expect_string=expect_string)
        with open('./res/vlan.txt', 'w') as v:
            v.write(output)
            v.close
        with open('./res/vlan.txt', 'r') as r:
            i = 0
            for line in r:
                if i != 2:
                    if '---------------------------------------------------------------------------------------------------' in line:
                        i = i+1
                        continue
                    else: continue
                spl = line.split(' ')
                spl = list(filter(None, spl))
                vid = spl[0]
                print(vid)
                vlaname = spl[1]
                print(vlaname)
                interfaces = spl[5]
                print(interfaces)
                try:
                    int(vid)
                except: continue
                if nb.ipam.vlans.get(vid=vid, tenant_id= tenid) == None:
                    nb.ipam.vlans.create(name=vlaname, vid=vid, status='active', tenant=tenid, site=siteid)
                lvlan.append(vid)
            print(lvlan)
            print('\n \n \n VLAN au dessus \n \n \n')
            return(lvlan)
        

    def sshint(lvlan, ssh, expect_string, decid, tenid):
        lint=[]
        commande = "show interface brief"
        output = ssh.send_command(commande, expect_string=expect_string)
        with open('./res/int.txt', 'w') as v:
            v.write(output)
            v.close
        with open('./res/int.txt', 'r') as r:
            i = 0
            for line in r:
                if i != 2:
                    if '---------------------------------------------------------------------------------------------------' in line:
                        i = i+1
                        continue
                    else: continue
                spl = line.split(' ')
                spl = list(filter(None, spl))
                inte = spl[0]
                if 'Up' in line: status = 1
                else: status = 0
                typ='1000base-t'
                try:
                    if inte not in lint:
                        lint.append(inte)
                    if 'up' in line: status = 1
                    else: status = 0
                    if spl[1] == '--':
                        typ='virtual'
                    else: typ='1000base-t'
                    try:
                        nb.dcim.interfaces.create(device=decid, name=str(inte), type=typ, enabled=status)
                    except: pass
                except: pass
                    #else: print('non')
        print(lint)
        for x in lint:
            print(x)
            inter=nb.dcim.interfaces.get(name=str(x), device_id=decid)
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
                    if i != 2:
                        if '------------------------------------------------------------' in line:
                            i = i+1
                            continue
                        else: continue   
                    vlanid = line.split(' ')[0]
                    print(vlanid)
                    if 'trunk' in line:
                        vlanid2=nb.ipam.vlans.get(vid=vlanid, tenant_id=tenid).id
                        print('oui')
                        if vlanid2 not in taggvlan:
                            taggvlan.append(vlanid2)
                    elif 'access' in line:
                        untagid=nb.ipam.vlans.get(vid=vlanid,tenant_id=tenid).id
                        inter.update({"untagged_vlan" : untagid})
                    elif 'native-untagged' in line:
                        untagid=nb.ipam.vlans.get(vid=vlanid,tenant_id=tenid).id
                        inter.update({"untagged_vlan" : untagid})
                    else: continue
                    tint=nb.dcim.interfaces.get(device_id=decid, name=str(x))
                    if taggvlan==[]:
                        inter.update({"mode" : "access", "untagged_vlan" : untagid})
                    else:
                        inter.update({"mode" : "tagged", "tagged_vlans" : taggvlan})
                r.close
        aruba.sship(ip,decid)

    def sship(ip,decid):

        commande = "show ip int br"
        output = ssh.send_command(commande, expect_string=expect_string)
        with open('./res/ip.txt', 'w') as i:
            i.write(output)
        with open('./res/ip.txt', 'r') as r:
            for line in r:
                if line.startswith('vlan303'):
                    try:
                        intid = nb.dcim.interfaces.create(device=decid, name='vlan303', type='virtual').id
                    except:
                        intid = nb.dcim.interfaces.get(device_id=decid, name='vlan303', type='virtual').id
                    lip = line.split(' ')
                    lip = list(filter(None, lip))
                    ip = lip[1]
                    print(ip)
                    if nb.ipam.ip_addresses.get(address=ip,tenant_id=1512) == None:
                        ipid = nb.ipam.ip_addresses.create(address=ip, tenant=1512, assigned_object_type='dcim.interface' ,assigned_object_id=intid).id
                    else:ipid = nb.ipam.ip_addresses.get(address=ip, tenant_id=1512).id
                    dec = nb.dcim.devices.get(id=decid)
                    dec.primary_ip4 = ipid
                    dec.save()

ips = 

for item in ips:
    ip = item.split(',', 1)[0]
    decid=item.split(',', 1)[1]
    dec = nb.dcim.devices.get(id=decid)
    tenid=dec.tenant.id
    siteid=dec.site.id
    print(decid)
    if decid == None:
        continue
    if dec.device_type.manufacturer == nb.dcim.manufacturers.get(name='Aruba'):
        ssh = ConnectHandler(device_type='aruba_os', ip=ip, username=username, password=password) 
        expect_string = ssh.find_prompt()
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

            lvlan = aruba.sshvlan(ssh, expect_string, tenid, siteid)
            aruba.sshint(lvlan, ssh, expect_string, decid, tenid)
    else: print("faux")

print("\n" + "--- %s secondes ---" % (time.time() - start_time))

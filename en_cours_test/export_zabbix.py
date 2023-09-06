"""
Ca marche et honnetement je sais pas exactement comment mais pour tout comprendre
il faudrait que j'apprenne a utiliser pyzabbix et d'autres library pour pas grand chose
du coup pas trop envie :)
"""
import argparse
import json
import logging
import os
import re
import sys
import xml.dom.minidom
from collections import OrderedDict

import anymarkup
import urllib3
import yaml
from pyzabbix import ZabbixAPI

from pkg_resources import parse_version

urllib3.disable_warnings()


def remove_none(obj):
    """
    Remove None value from any object
    As is from https://stackoverflow.com/a/20558778/6753144
    :param obj:
    :return:
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
    Sometimes pyzabbix and py-zabbix library can replace each other.
    This is a wrapper, we don't care about what pip-module we install.
    Return ZabbixAPI object
    """
    # pyzabbix library, with user\password in login method. It's GOOD library
    logging.debug("Try connect to Zabbix by pyzabbix...")
    try:
        zbx_pyzabbix = ZabbixAPI("https://203zabbix.agrom.mousquetaires.com/")
        zbx_pyzabbix.session.verify = False
        zbx_pyzabbix.login(api_token="0a51dbc75c0de297eaae1120cf0abab7")
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
        only="hosts",
    )

import os
import re
import json
import time
import logging

from ncclient import manager, transport, operations

import xmltodict
import requests

log = logging.getLogger("wifininja.commsLib")

DASHBOARD_API_KEY = os.environ["DASHBOARD_API_KEY"]
INFLUX_API_KEY = os.environ["INFLUX_API_KEY"]
WLC_USER = os.environ["WLC_USER"]
WLC_PASS = os.environ["WLC_PASS"]


def send_to_influx(env, data, precision="s"):

    influx_api = f'http://{env["INFLUX_IP"]}:{env["INFLUX_PORT"]}/api/v2/write'
    headers = {
        "Content-Type" : "text/plain; charset=utf-8",
        "Accept" : "application/json",
        "Authorization": f'Token {INFLUX_API_KEY}'
    }
    params = {
        "org" : env["INFLUX_ORG"],
        "bucket" : env["INFLUX_BUCKET"],
        "precision" : precision
    }
    try:
        requests.post(
            influx_api,
            headers=headers,
            params=params,
            data=data,
            timeout=3
        )
    except requests.exceptions.ReadTimeout:
        log.error(f"Influx connection timeout")
    except requests.exceptions.ConnectionError:
        log.error(f"Influx connection error") 


def send_to_dashboard(env, api, data):

    dashboard_api = f'http://{env["DASHBOARD_IP"]}:{env["DASHBOARD_PORT"]}/Post{api}Data'
    headers = {"Api-Key" : DASHBOARD_API_KEY}
    try:
        requests.post(
            dashboard_api,
            headers=headers,
            data=json.dumps(data),
            verify=False,
            timeout=3
        )
    except requests.exceptions.ConnectTimeout:
        log.error(f"Dashboard connection timeout")
    except requests.exceptions.ConnectionError:
        log.error(f"Dashboard connection error")


def netconf_get(env, filter): #Using xmltodict

    try:
        start = time.time()
        with manager.connect(host=env["WLC_HOST"],
                             port=830,
                             username=WLC_USER,
                             password=WLC_PASS,
                             device_params={"name":"iosxe"},
                             hostkey_verify=False) as ncc:
            netconf_output = xmltodict.parse(ncc.get(filter=("subtree", filter)).data_xml)
        end = time.time()

    except (transport.errors.SSHError, operations.errors.TimeoutExpiredError, transport.errors.SessionError, transport.errors.AuthenticationError):
        netconf_output = {}
        log.error(f"NETCONF error")
    else:
        log.info(f"Netconf query took {round(end - start, 1)}s")

    return netconf_output


def netconf_get_x(env, filter): #Using XPath

    try:
        start = time.time()
        with manager.connect(host=env["WLC_HOST"],
                             port=830,
                             username=WLC_USER,
                             password=WLC_PASS,
                             device_params={"name":"iosxe"},
                             hostkey_verify=False) as ncc:
            netconf_output = ncc.get(filter=("subtree", filter)).data_xml
            netconf_output = re.sub('xmlns="[^"]+"', "", netconf_output)
        end = time.time()

    except (transport.errors.SSHError, operations.errors.TimeoutExpiredError, transport.errors.SessionError, transport.errors.AuthenticationError):
        netconf_output = ""
        log.error(f"NETCONF error")
    else:
        log.info(f"Netconf query took {round(end - start, 1)}s")

    return netconf_output


def netconf_get_config(env, filter): #Using xmltodict

    try:
        start = time.time()
        with manager.connect(host=env["WLC_HOST"],
                             port=830,
                             username=WLC_USER,
                             password=WLC_PASS,
                             device_params={"name":"iosxe"},
                             hostkey_verify=False) as ncc:
            netconf_output = xmltodict.parse(ncc.get_config(source="running", filter=("subtree", filter)).data_xml)
        end = time.time()

    except (transport.errors.SSHError, operations.errors.TimeoutExpiredError, transport.errors.SessionError, transport.errors.AuthenticationError):
        netconf_output = {}
        log.error(f"NETCONF error")
    else:
        log.info(f"Netconf query took {round(end - start, 1)}s")

    return netconf_output
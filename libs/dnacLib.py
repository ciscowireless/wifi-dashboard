import os
import re
import sys
import time
import json
import base64
import logging
import subprocess

from datetime import datetime

import libs.influxLib as influxLib
import libs.envLib as envLib

import requests

requests.packages.urllib3.disable_warnings()

log = logging.getLogger("wifininja.dnacLib")
env = envLib.read_config_file()


class Dna():

    def __init__(self):

        self.dnac_lastrun = datetime.now()
        self.dnac_firstrun = True
        try:
            self.wlc_host = env["WLC_IP"]
            self.dnac_ip = env["DNAC_IP"]
            #self.dnac_user = os.environ['DNAC_USER']
            #self.dnac_pass = os.environ['DNAC_PASS']
            self.dnac_user = os.environ['LAB_DNAC_USER']
            self.dnac_pass = os.environ['LAB_DNAC_PASS']
        
        except KeyError as missing_key:
            log.error(f"Missing environment variable: {missing_key}")
            subprocess.run(["echo", "DNAC collector : Stopped"])
            sys.exit()

        self.authz = base64.b64encode(f"{self.dnac_user}:{self.dnac_pass}".encode("UTF-8")).decode("ASCII")
        self.auth_api = "/dna/system/api/v1/auth/token"
        self.net_device_api = "/dna/intent/api/v1/network-device"
        self.cli_read_api = "/dna/intent/api/v1/network-device-poller/cli/read-request"
        self.get_taskid_api = "/dna/intent/api/v1/task"
        self.get_fileid_api = "/dna/intent/api/v1/file"


    def get_dnac_token(self):

        api = f"https://{self.dnac_ip}{self.auth_api}"
        headers = {"Content-Type" : "application/json", "Authorization" : f'Basic {self.authz}'}
        try:
            start = time.time()
            self.dnac_token = requests.post(api,
                                            headers=headers,
                                            verify=False,
                                            timeout=5
                                            ).json()["Token"]
            end = time.time()
            log.info(f"DNAC query took {round(end - start, 1)}s - {self.auth_api}")
        except requests.exceptions.ConnectionError:
            log.error(f"DNAC connection error")
            self.dnac_token = ""


    def get_network_device(self):

        api = f"https://{self.dnac_ip}{self.net_device_api}?managementIpAddress={self.wlc_host}"
        headers = {"Content-Type" : "application/json", "x-auth-token" : self.dnac_token}
        try:
            start = time.time()
            self.network_device = requests.get(api,
                                               headers=headers,
                                               verify=False,
                                               timeout=5
                                               ).json()["response"][0]["instanceUuid"]
            end = time.time()
            log.info(f"DNAC query took {round(end - start, 1)}s - {self.net_device_api}")
        except requests.exceptions.ConnectionError:
            log.error(f"DNAC connection error")
            self.network_device = ""


    def cli_read(self):

        self.wncd_cli = "show processes cpu platform | i wncd"
        
        data = json.dumps({
            "commands": [self.wncd_cli],
            "deviceUuids": [self.network_device]
            })
        api = f"https://{self.dnac_ip}{self.cli_read_api}"
        headers = {"Content-Type" : "application/json", "x-auth-token" : self.dnac_token}
        try:
            start = time.time()
            self.taskid = requests.post(api,
                                        headers=headers,
                                        data=data,
                                        verify=False,
                                        timeout=5
                                        ).json()["response"]["taskId"]
            end = time.time()
            log.info(f"DNAC query took {round(end - start, 1)}s - {self.cli_read_api}")
        except requests.exceptions.ConnectionError:
            log.error(f"DNAC connection error")
            self.taskid = ""


    def get_task(self):

        api = f"https://{self.dnac_ip}{self.get_taskid_api}/{self.taskid}"
        headers = {"Content-Type" : "application/json", "x-auth-token" : self.dnac_token}
        try:
            start = time.time()
            task = requests.get(api,
                                headers=headers,
                                verify=False,
                                timeout=5
                                ).json()["response"]
            self.task_progress = task["progress"]
            end = time.time()
            log.info(f"DNAC query took {round(end - start, 1)}s - {self.get_taskid_api}")
        except requests.exceptions.ConnectionError:
            log.error(f"DNAC connection error")
            self.task_progress = ""
    

    def wait_task(self):

        retry_time = 3 #sec
        wait_timer = 0
        fileid = ""
        while wait_timer < 9:
            self.get_task()
            if self.task_progress == "CLI Runner request creation":
                wait_timer += retry_time
                time.sleep(retry_time)
                continue
            else:
                try:
                    fileid = json.loads(self.task_progress)["fileId"]
                except json.decoder.JSONDecodeError:
                    pass
                break
        return fileid


    def get_file(self):

        api = f"https://{self.dnac_ip}{self.get_fileid_api}/{self.wait_task()}"
        headers = {"Content-Type" : "application/json", "x-auth-token" : self.dnac_token}
        try:
            start = time.time()
            self.wncd_output = requests.get(api, 
                                            headers=headers, 
                                            verify=False,
                                            timeout=5
                                            ).json()[0]["commandResponses"]["SUCCESS"][self.wncd_cli]
            end = time.time()
            log.info(f"DNAC query took {round(end - start, 1)}s - {self.get_fileid_api}")
        except requests.exceptions.ConnectionError:
            log.error(f"DNAC connection error")
            self.wncd_output = ""
    

    def parse_wncd(self):

        wncd_load = []
        for line in self.wncd_output.split("\n"):
            wncd_status = re.match("\s+\d+\s+\d+\s+(\d+)%\s+(\d+)%\s+(\d+)%\s+\S+\s+\d+\s+(\S+)",line)
            try:
                wncd_load.append((wncd_status.group(3), wncd_status.group(4)))
            except AttributeError:
                pass
        return {"wncd_load" : wncd_load}


run = Dna()

def dnac_loop():

    idle_period = datetime.now() - run.dnac_lastrun
    if run.dnac_firstrun or idle_period.seconds >= int(env["DNAC_CYCLE"]):

        run.dnac_firstrun = False
        run.dnac_lastrun = datetime.now()
                
        run.get_dnac_token()
        run.get_network_device()
        run.cli_read()
        run.get_file()

        if run.wncd_output != "":
            influxLib.send_to_influx_wncd(env, run.parse_wncd())

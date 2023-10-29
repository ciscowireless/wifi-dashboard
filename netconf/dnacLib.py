import os
import re
import time
import json
import base64
import requests

requests.packages.urllib3.disable_warnings() 


class Dna():

    def __init__(self, env):

        self.wlc_host = env["WLC_IP"]
        self.dnac_ip = env["DNAC_IP"]
        self.dnac_user = os.environ['DNAC_USER']
        self.dnac_pass = os.environ['DNAC_PASS']
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
            self.dnac_token = requests.post(api,
                                            headers=headers,
                                            verify=False
                                            ).json()["Token"]
        except requests.exceptions.ConnectionError:
            self.dnac_token = ""


    def get_network_device(self):

        api = f"https://{self.dnac_ip}{self.net_device_api}?managementIpAddress={self.wlc_host}"
        headers = {"Content-Type" : "application/json", "x-auth-token" : self.dnac_token}
        try:
            self.network_device = requests.get(api,
                                               headers=headers,
                                               verify=False
                                               ).json()["response"][0]["instanceUuid"]
        except requests.exceptions.ConnectionError:
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
            self.taskid = requests.post(api,
                                        headers=headers,
                                        data=data,
                                        verify=False
                                        ).json()["response"]["taskId"]
        except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError):
            self.taskid = ""


    def get_task(self):

        api = f"https://{self.dnac_ip}{self.get_taskid_api}/{self.taskid}"
        headers = {"Content-Type" : "application/json", "x-auth-token" : self.dnac_token}
        try:
            task = requests.get(api,
                                headers=headers,
                                verify=False
                                ).json()["response"]
            self.task_progress = task["progress"]
        except requests.exceptions.ConnectionError:
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
            self.wncd_output = requests.get(api, 
                                            headers=headers, 
                                            verify=False
                                            ).json()[0]["commandResponses"]["SUCCESS"][self.wncd_cli]
        except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError):
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


if __name__ == "__main__":

    run = Dna()
    run.get_dnac_token()
    run.get_network_device()
    run.cli_read()
    run.get_file()
    run.parse_wncd()
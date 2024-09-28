import sys
import subprocess
import os
import time
import re
import requests

from datetime import datetime

from radkit_client.sync import Client

INFLUX_ORG = "wifininja"
INFLUX_BUCKET = "telemetry"
INFLUX_HOST = "localhost"
INFLUX_PORT = "8086"
POLL_CYCLE = 30


class wncd_poller():


    def __init__(self):

        self.command = "show processes cpu platform sorted | i wncd"    
        
        self.radkit_user = os.environ["RADKIT_USER"]
        self.radkit_pass = os.environ["RADKIT_PASS"]
        self.influx_api_key = os.environ["INFLUX_API_KEY"]
        self.lastrun = datetime.now()
        self.firstrun = True
        self.run()


    def run(self):

        subprocess.run(["clear"])
        subprocess.run(["echo", "RADKit poller : Running"])
        try:
            with Client.create() as client:
                self.radkit = client.service_direct(
                            username=os.environ["RADKIT_USER"], 
                            password=os.environ["RADKIT_PASS"], 
                            host='localhost', 
                            port=8181
                            )
                self.radkit.update_inventory().wait()
                while True:
                    self.wncd_loop()
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            subprocess.run(["clear"])
            subprocess.run(["echo", "RADKit poller : Stopped"])
            sys.exit()


    def wncd_loop(self):

        idle_period = datetime.now() - self.lastrun
        if self.firstrun or idle_period.seconds >= POLL_CYCLE:

            self.firstrun = False
            self.lastrun = datetime.now()

            for device in self.radkit.inventory:
                
                target = self.radkit.inventory[device]
                self.command_output = target.exec(self.command).wait()
                print(f"Device: [{device}] RADKit status: {self.command_output.result.status}")
                measurement = self.parse_wncd()
                print(measurement)
                self.send_to_influx(device, measurement)

    
    def parse_wncd(self):

        wncd_load = ""
        for line in self.command_output.result.data.split("\n"):

            wncd_status = re.match("\s+\d+\s+\d+\s+(\d+)%\s+(\d+)%\s+(\d+)%\s+\S+\s+\d+\s+(\S+)",line)
            try:
                wncd_load += f"{wncd_status.group(4)}={wncd_status.group(3)},"
            except AttributeError:
                pass

        return wncd_load[:-1]
    

    def send_to_influx(self, device, measurement, precision="s"):

        line_protocol = f'wncd,wlcName={device} {measurement}\n'

        influx_api = f'http://{INFLUX_HOST}:{INFLUX_PORT}/api/v2/write'
        headers = {
            "Content-Type" : "text/plain; charset=utf-8",
            "Accept" : "application/json",
            "Authorization": f'Token {self.influx_api_key}'
        }
        params = {
            "org" : {INFLUX_ORG},
            "bucket" : {INFLUX_BUCKET},
            "precision" : precision
        }
        try:
            result = requests.post(influx_api, headers=headers, params=params, data=line_protocol, timeout=3)
            print(f"Influx [{result.status_code}]")
        except requests.exceptions.ReadTimeout:
            print(f"Influx connection timeout")
        except requests.exceptions.ConnectionError:
            print(f"Influx connection error") 


if __name__ == '__main__':

    wncd_poller()

import logging
import os
import sys
import time
import json
import subprocess

from datetime import datetime

from libs.netconf import Netconf
from libs.mysql import MySql
from libs.influx import Influx


log = logging.getLogger("wifininja")
log.setLevel(logging.DEBUG)
log_format = logging.Formatter(
    fmt="%(asctime)s (%(name)s) %(levelname)s:%(message)s",
    datefmt="%m/%d/%Y %H:%M:%S"
)
log_console = logging.StreamHandler()
log_console.setLevel(logging.DEBUG)
log_console.setFormatter(log_format)

log.addHandler(log_console)


class Dashboard():

    def __init__(self):

        self.config_file_json = "config.json"
        self.read_config_json()
        self.iosxe_user = os.environ["IOSXE_USER"]
        self.iosxe_pass = os.environ["IOSXE_PASS"]
        self.mysql_user = os.environ["MYSQL_USER"]
        self.mysql_pass = os.environ["MYSQL_PASS"]
        self.influx_api_key = os.environ["INFLUX_API_KEY"]       
        self.lastrun = datetime.now()
        self.firstrun = True

        self.netconf = Netconf(self)
        self.mysql = MySql(self)
        self.influx = Influx(self)

        self.run()


    def run(self):

        subprocess.run(["clear"])
        subprocess.run(["echo", "Dashboard : Running"])
        try:
            while True:
                self.dashboard_loop()
                time.sleep(1)
                    
        except KeyboardInterrupt:
            subprocess.run(["clear"])
            subprocess.run(["echo", "Dashboard : Stopped"])
            sys.exit()


    def dashboard_loop(self):

        idle_period = datetime.now() - self.lastrun

        if self.firstrun or idle_period.seconds >= int(self.config["general"]["netconf_cycle"]):

            self.firstrun = False
            self.lastrun = datetime.now()

            for wlc in self.config["wlc"]:

                self.netconf.wlc_ip = wlc["ip"]
                self.netconf.wlc_name = wlc["name"]
                self.netconf.wlc_interface = wlc["interface"]
                
                self.netconf.get_wireless_client_global_oper()
                self.mysql.put_wireless_client_global_oper(self.netconf)
                self.influx.put_wireless_client_global_oper()

                # get_netconf_interfaces_oper()
                # get_netconf_wireless_client_global_oper()
                # get_netconf_wireless_client_oper()
                # get_netconf_wireless_access_point_oper()
                # get_netconf_wireless_rrm_oper()

            log.info(f"Waiting for next NETCONF cycle")       


    def read_config_json(self):

        try:
            with open(self.config_file_json, "r") as j:
                self.config = json.load(j)

        except FileNotFoundError:
            log.critical(f"Error opening config file")
            sys.exit()


if __name__ == "__main__":

    Dashboard()
import logging
import os
import sys
import time
import json
import subprocess

from datetime import datetime

import mysql.connector

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
        self.mysql_user = os.environ["MYSQL_USER"]
        self.mysql_pass = os.environ["MYSQL_PASS"]
        self.influx_api_key = os.environ["INFLUX_API_KEY"]
        self.open_mysql_session()

        self.mysql = MySql(self)
        self.influx = Influx(self)
        self.netconf = Netconf(self)

        self.lastrun = datetime.now()
        self.firstrun = True
        self.run()


    def run(self):

        subprocess.run(["clear"])
        subprocess.run(["echo", "Dashboard: Running"])
        try:
            while True:
                self.dashboard_loop()
                time.sleep(1)
                    
        except KeyboardInterrupt:
            subprocess.run(["clear"])
            subprocess.run(["echo", "Dashboard: Stopped"])
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
                self.netconf.wlc_user = os.environ[wlc["user_env"]]
                self.netconf.wlc_pass = os.environ[wlc["pass_env"]]
                
                subprocess.run(["echo", f"WLC: {self.netconf.wlc_ip} ({self.netconf.wlc_name})"])

                self.netconf.get_wireless_client_global_oper()
                self.mysql.sql_wireless_client_global_oper_client(self.netconf)
                self.mysql.sql_wireless_client_global_oper_wlan(self.netconf)
                self.influx.post_wireless_client_global_oper_client()
                self.influx.post_wireless_client_global_oper_wlan()

                self.netconf.get_wireless_access_point_oper()
                self.mysql.sql_wireless_access_point_oper(self.netconf)
                self.netconf.get_wireless_rrm_oper()
                self.mysql.sql_wireless_rrm_oper(self.netconf)
                self.influx.post_wireless_oper()
                self.influx.post_ap_inventory()

                self.netconf.get_wireless_client_oper()
                self.mysql.sql_wireless_client_oper(self.netconf)
                self.influx.post_wireless_client_oper()

                self.netconf.get_wireless_ap_global_oper()
                self.mysql.sql_wireless_ap_global_oper(self.netconf)
                self.netconf.get_interfaces_oper()
                self.mysql.sql_interfaces_oper(self.netconf)
                self.influx.post_wlc_oper()

                self.netconf.get_device_hardware_oper()
                self.netconf.get_native()
                self.netconf.get_install_oper()
                self.mysql.sql_wlc_detail(self.netconf)
                self.influx.post_wlc_inventory()

            log.info(f"Waiting for next NETCONF cycle\n")
    

    def open_mysql_session(self):

        self.mysql_session = mysql.connector.connect(
                                                    host=self.config["general"]["mysql_host"],
                                                    database=self.config["general"]["mysql_db"],
                                                    user=self.mysql_user,
                                                    password=self.mysql_pass
                                                    )

    def read_config_json(self):

        try:
            with open(self.config_file_json, "r") as j:
                self.config = json.load(j)

        except FileNotFoundError:
            log.critical(f"Error opening config file")
            sys.exit()


if __name__ == "__main__":

    Dashboard()
import logging

import xml.etree.ElementTree as ET

import mysql.connector

log = logging.getLogger("wifininja.mysql")


class MySql():


    def __init__(self, init):

        self.mysql_db = init.config["general"]["mysql_db"]
        self.mysql_host = init.config["general"]["mysql_host"]
        self.mysql_user = init.mysql_user
        self.mysql_pass = init.mysql_pass

        self.open_mysql_session()


    def open_mysql_session(self):

        self.mysql_session = mysql.connector.connect(
                                                host=self.mysql_host,
                                                user=self.mysql_user,
                                                password=self.mysql_pass,
                                                database=self.mysql_db
                                                )


    def write_mysql(self, query):

        cursor = self.mysql_session.cursor()
        cursor.execute(query)       
        self.mysql_session.commit() 
        cursor.close()
        log.info("Write to MySql")


    def put_wireless_client_global_oper(self, netconf_data):

        try:
            data = ET.fromstring(netconf_data.wireless_client_global_oper).find(".//client-live-stats")

        except ET.ParseError:
            log.warning(f"No Client Live Stats data")
        else:
            try:
                auth = int(data.find("auth-state-clients").text)
                mobility = int(data.find("mobility-state-clients").text)
                iplearn = int(data.find("iplearn-state-clients").text)
                webauth = int(data.find("webauth-state-clients").text)
                run = int(data.find("run-state-clients").text)
                delete = int(data.find("delete-state-clients").text)
                random_mac = int(data.find("random-mac-clients").text)

            except AttributeError:
                log.warning(f"Bad Client Live Stats data")
            else:
                self.write_mysql(f"REPLACE INTO ClientLiveStats VALUES "\
                               f"('{netconf_data.wlc_ip}', '{netconf_data.wlc_name}', '{auth}', '{mobility}', '{iplearn}', '{webauth}', '{run}', '{delete}', '{random_mac}')"
                               )
                
                

import logging

import xml.etree.ElementTree as ET

log = logging.getLogger("wifininja.mysql")


class MySql():


    def __init__(self, init):

        self.mysql_db = init.config["general"]["mysql_db"]
        self.mysql_host = init.config["general"]["mysql_host"]
        self.mysql_user = init.mysql_user
        self.mysql_pass = init.mysql_pass

        self.mysql_session = init.mysql_session


    def write_mysql(self, query):

        cursor = self.mysql_session.cursor()
        cursor.execute(query)       
        self.mysql_session.commit() 
        cursor.close()
        log.info("Write to MySQL")


    def put_wireless_client_global_oper(self, netconf_data):

        try:
            live_stats = ET.fromstring(netconf_data.wireless_client_global_oper).find(".//client-live-stats")
            dot11_stats = ET.fromstring(netconf_data.wireless_client_global_oper).find(".//client-dot11-stats")

        except ET.ParseError:
            log.warning(f"No Client Live Stats data")
        else:
            try:
                auth = int(live_stats.find("auth-state-clients").text)
                mobility = int(live_stats.find("mobility-state-clients").text)
                iplearn = int(live_stats.find("iplearn-state-clients").text)
                webauth = int(live_stats.find("webauth-state-clients").text)
                run = int(live_stats.find("run-state-clients").text)
                delete = int(live_stats.find("delete-state-clients").text)
                random_mac = int(live_stats.find("random-mac-clients").text)

                clients24ghz = int(dot11_stats.find("num-clients-on-24ghz-radio").text)
                clients5ghz = int(dot11_stats.find("num-clients-on-5ghz-radio").text)
                clients6ghz = int(dot11_stats.find("num-6ghz-clients").text)
                
            except AttributeError:
                log.warning(f"Bad Client Live Stats data")
            else:
                self.write_mysql(f"REPLACE INTO ClientLiveStats VALUES "\
                                 f"('{netconf_data.wlc_ip}', '{netconf_data.wlc_name}', "\
                                 f"'{auth}', '{mobility}', '{iplearn}', '{webauth}', '{run}', '{delete}', '{random_mac}', "\
                                 f"'{clients24ghz}', '{clients5ghz}', '{clients6ghz}')"
                                )

                

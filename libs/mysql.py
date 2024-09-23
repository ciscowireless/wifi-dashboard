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
        #log.info("Write to MySQL")


    def sql_wireless_client_global_oper_client(self, netconf_data):

        try:
            client_live_stats = ET.fromstring(netconf_data.wireless_client_global_oper).find(".//client-live-stats")
            client_dot11_stats = ET.fromstring(netconf_data.wireless_client_global_oper).find(".//client-dot11-stats")

        except ET.ParseError:
            log.warning(f"XML parse error: wireless_client_global_oper (client)")
        else:
            try:
                auth = client_live_stats.find("auth-state-clients").text
                mobility = client_live_stats.find("mobility-state-clients").text
                iplearn = client_live_stats.find("iplearn-state-clients").text
                webauth = client_live_stats.find("webauth-state-clients").text
                run = client_live_stats.find("run-state-clients").text
                delete = client_live_stats.find("delete-state-clients").text
                random_mac = client_live_stats.find("random-mac-clients").text

                clients24ghz = client_dot11_stats.find("num-clients-on-24ghz-radio").text
                clients5ghz = client_dot11_stats.find("num-clients-on-5ghz-radio").text
                clients6ghz = client_dot11_stats.find("num-6ghz-clients").text
      
            except AttributeError:
                log.warning(f"Data validation error: wireless_client_global_oper (client)")
            else:
                self.write_mysql(
                                f"REPLACE INTO Client "
                                f"(wlcIp, wlcName, authClients, mobilityClients, ipLearnClients, webAuthClients, runClients, deleteClients, randomMacClients, "
                                f"clients24ghz, clients5ghz, clients6ghz) "
                                f"VALUES "\
                                f"('{netconf_data.wlc_ip}', '{netconf_data.wlc_name}', '{auth}', '{mobility}', '{iplearn}', '{webauth}', '{run}', '{delete}', '{random_mac}', "
                                f"'{clients24ghz}', '{clients5ghz}', '{clients6ghz}')"
                                )
    

    def sql_wireless_client_global_oper_wlan(self, netconf_data):

        try:
            wlan_stats = ET.fromstring(netconf_data.wireless_client_global_oper).find(".//sort-wlan")

        except ET.ParseError:
            log.warning(f"XML parse error: wireless_client_global_oper (wlan)")
        else:
            try:
                wlan_data = []
                for item in wlan_stats.findall(".//wlan-list"):
                    wlan_id = item.find("wlan-id").text
                    wlan_name = item.find("wlan-profile-name").text
                    wlan_users = item.find("num-client").text
                    wlan_data_usage = item.find("data-usage").text
                    wlan_data.append([wlan_id, wlan_name, wlan_users, wlan_data_usage])

            except AttributeError:
                log.warning(f"Data validation error: wireless_client_global_oper (wlan)")
            else:
                query_string = ""
                for wlan in wlan_data:
                    query_string += f"('{netconf_data.wlc_ip}', '{netconf_data.wlc_name}', '{wlan[0]}','{wlan[1]}','{wlan[2]}','{wlan[3]}'),"
                
                self.write_mysql(f"REPLACE INTO Wlan (wlcIp, wlcName, wlanId, wlanProfileName, wlanUsers, wlanDataUsage) VALUES {query_string[:-1]};")


    def sql_wireless_access_point_oper(self, netconf_data):

        try:
            access_point_oper_data = ET.fromstring(netconf_data.wireless_client_global_oper).find(".//access-point-oper-data")

        except ET.ParseError:
            log.warning(f"XML parse error: wireless_access_point_oper")
        else:
            try:
                ap_data = {}
                for item in access_point_oper_data.findall(".//ap-name-mac-map"):
                    ap_radio_mac = item.find("wtp-mac").text
                    ap_data[ap_radio_mac] = {}
                    ap_data[ap_radio_mac]["ap-name"] = item.find("wtp-name").text
                    ap_data[ap_radio_mac]["ap-eth-mac"] = item.find("eth-mac").text

                for item in access_point_oper_data.findall(".//capwap-data"):
                    ap_radio_mac = item.find("wtp-mac").text
                    ap_data[ap_radio_mac]["rf-tag"] = item.find("tag-info/rf-tag/rf-tag-name").text
                    ap_data[ap_radio_mac]["site-tag"] = item.find("tag-info/site-tag/site-tag-name").text

                slot_data = []
                for item in access_point_oper_data.findall(".//radio-oper-data"):
                    ap_radio_mac = item.find("wtp-mac").text
                    slot = item.find("radio-slot-id").text
                    oper_state = item.find("oper-state").text
                    radio_mode = item.find("radio-mode").text
                    band = item.find("current-active-band").text
                    channel = item.find("phy-ht-cfg/cfg-data/curr-freq").text
                    power = item.find("radio-band-info/phy-tx-pwr-cfg/cfg-data/current-tx-power-level").text
                    slot_data.append([ap_radio_mac, slot, oper_state, radio_mode, band, channel, power])
                
            except AttributeError:
                log.warning(f"Data validation error: wireless_access_point_oper")
            else:
                self.write_mysql(f"DELETE FROM Ap;")

                query_string = ""
                for radio_mac, ap_info in ap_data.items():
                    ap_name, eth_mac, rf_tag, site_tag = ap_info["ap-name"], ap_info["ap-eth-mac"], ap_info["rf-tag"], ap_info["site-tag"]
                    query_string += f"('{radio_mac}', '{ap_name}', '{eth_mac}', '{rf_tag}', '{site_tag}'),"

                self.write_mysql(f"REPLACE INTO Ap VALUES {query_string[:-1]};")
                
                query_string = ""
                for slot in slot_data:
                    query_string += f"('{slot[0]}','{slot[1]}','{slot[2]}','{slot[3]}','{slot[4]}','{slot[5]}','{slot[6]}'),"
                
                self.write_mysql(f"REPLACE INTO Slot (apRadioMac, slot, operState, radioMode, band, channel, power) VALUES {query_string[:-1]};")


    def sql_wireless_rrm_oper(self, netconf_data):

        try:
            wireless_rrm_oper_data = ET.fromstring(netconf_data.wireless_rrm_oper).find(".//rrm-oper-data")

        except ET.ParseError:
            log.warning(f"XML parse error: wireless_rrm_oper")
        else:
            try:
                rrm_data = []
                for item in wireless_rrm_oper_data.findall(".//rrm-measurement"):
                    ap_radio_mac = item.find("wtp-mac").text
                    slot = item.find("radio-slot-id").text
                    stations = item.find("load/stations").text
                    cca = item.find("load/cca-util-percentage").text
                    rrm_data.append([ap_radio_mac, slot, stations, cca])

            except AttributeError:
                log.warning(f"Data validation error: wireless_rrm_oper")
            else:
                for measurement in rrm_data:
                    self.write_mysql(f"UPDATE Slot SET stations = '{measurement[2]}', cca = '{measurement[3]}' WHERE apRadioMac = '{measurement[0]}' AND slot = '{measurement[1]}';")


    def sql_wireless_ap_global_oper(self, netconf_data):

        try:
            wireless_ap_global_oper_data = ET.fromstring(netconf_data.wireless_ap_global_oper).find(".//ap-global-oper-data")

        except ET.ParseError:
            log.warning(f"XML parse error: wireless_ap_global_oper")
        else:
            try:
                joined_aps = wireless_ap_global_oper_data.find("emltd-join-count-stat/joined-aps-count").text
                
            except AttributeError:
                log.warning(f"Data validation error: wireless_ap_global_oper")
            else:
                self.write_mysql(
                                f"REPLACE INTO Wlc (wlcIp, wlcName, joinedAps) VALUES "\
                                f"('{netconf_data.wlc_ip}', '{netconf_data.wlc_name}', '{joined_aps}');"
                                )


    def sql_wireless_client_oper(self, netconf_data):

        try:
            wireless_client_oper = ET.fromstring(netconf_data.wireless_ap_global_oper).find(".//client-oper-data")

        except ET.ParseError:
            log.warning(f"XML parse error: wireless_client_oper")
        else:
            try:
                wifi_4, wifi_5, wifi_6, wifi_other = 0, 0, 0, 0
                for item in wireless_client_oper.findall(".//common-oper-data"):
                    match item.find("ms-radio-type").text:
                        case "client-dot11ax-6ghz-prot": wifi_6 += 1
                        case "client-dot11ax-5ghz-prot": wifi_6 += 1
                        case "client-dot11ax-24ghz-prot": wifi_6 += 1
                        case "client-dot11ac-prot": wifi_5 += 1
                        case "client-dot11n-5-ghz-prot": wifi_4 += 1
                        case "client-dot11n-24-ghz-prot": wifi_4 += 1
                        case "client-dot11g-prot": wifi_other += 1
                        case "client-dot11a-prot": wifi_other += 1
                        case "client-dot11b-prot": wifi_other += 1
                        case _: wifi_other += 1
            
            except AttributeError:
                log.warning(f"Data validation error: wireless_ap_global_oper")
            else:
                self.write_mysql(f"UPDATE Client SET wifi4 = '{wifi_4}', wifi5 = '{wifi_5}', wifi6 = '{wifi_6}', wifiOther = '{wifi_other}' WHERE wlcIp = '{netconf_data.wlc_ip}';")


    def sql_interfaces_oper(self, netconf_data):

        try:
            interfaces_oper = ET.fromstring(netconf_data.interfaces_oper).find(".//interface")

        except ET.ParseError:
            log.warning(f"XML parse error: interfaces_oper")
        else:
            try:
                interface_name = interfaces_oper.find("name").text
                rx = interfaces_oper.find("statistics/rx-kbps").text
                tx = interfaces_oper.find("statistics/tx-kbps").text

            except AttributeError:
                log.warning(f"Data validation error: interfaces_oper")
            else:
                self.write_mysql(f"UPDATE Wlc SET interfaceName = '{interface_name}', Rx = '{rx}', Tx = '{tx}' WHERE wlcIp = '{netconf_data.wlc_ip}';")

                    
        






                

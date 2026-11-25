'''
Copyright (c) 2026 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.

'''
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
        self.clear_mysql()

    def clear_mysql(self):

        self.write_mysql(f"DELETE FROM Ap;")
        self.write_mysql(f"DELETE FROM Slot;")
        self.write_mysql(f"DELETE FROM SlotMetrics;")


    def write_mysql(self, query):

        cursor = self.mysql_session.cursor()
        cursor.execute(query)       
        self.mysql_session.commit() 
        cursor.close()
        #log.info("Write to MySQL")


    def sql_wireless_access_point_oper(self, netconf_data):

        try:
            access_point_oper_data = ET.fromstring(netconf_data.wireless_client_global_oper).find(".//access-point-oper-data")

        except ET.ParseError:
            log.warning(f"XML parse error [wireless_access_point_oper]")
        else:
            if access_point_oper_data: #Skip if empty result.
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
                        ap_data[ap_radio_mac]["model"] = item.find("device-detail/static-info/ap-models/model").text

                    slot_data = []
                    for item in access_point_oper_data.findall(".//radio-oper-data"):
                        ap_radio_mac = item.find("wtp-mac").text
                        slot = item.find("radio-slot-id").text
                        try:
                            oper_state = item.find("oper-state").text
                        except AttributeError:
                            oper_state = "NULL"
                            #log.warning(f"[wireless_access_point_oper] Radio MAC {ap_radio_mac}, Slot {slot}, no operational state")
                        try:
                            radio_mode = item.find("radio-mode").text
                            #log.warning(f"[wireless_access_point_oper] Radio MAC {ap_radio_mac}, Slot {slot}, no radio mode")
                        except AttributeError:
                            radio_mode = "NULL"
                        try:
                            band = item.find("current-active-band").text
                        except AttributeError:
                            band = "NULL"
                            #log.warning(f"[wireless_access_point_oper] Radio MAC {ap_radio_mac}, Slot {slot}, no band information")
                        try:
                            channel = item.find("phy-ht-cfg/cfg-data/curr-freq").text
                        except AttributeError:
                            channel = 0
                            #log.warning(f"[wireless_access_point_oper] Radio MAC {ap_radio_mac}, Slot {slot}, no channel information")
                        try:
                            power = item.find("radio-band-info/phy-tx-pwr-cfg/cfg-data/current-tx-power-level").text
                        except AttributeError:
                            power = 0
                            #log.warning(f"[wireless_access_point_oper] Radio MAC {ap_radio_mac}, Slot {slot}, no power information")

                        slot_data.append([ap_radio_mac, slot, oper_state, radio_mode, band, channel, power])

                except KeyboardInterrupt:
                    log.warning(f"Data validation error [wireless_access_point_oper]")
                else:
                    self.write_mysql(f"DELETE FROM Ap;")

                    query_string = ""
                    for radio_mac, ap_info in ap_data.items():
                        ap_name = ap_info["ap-name"]
                        eth_mac = ap_info["ap-eth-mac"]
                        rf_tag = ap_info["rf-tag"]
                        site_tag = ap_info["site-tag"]
                        model = ap_info["model"]
                        query_string += f"('{netconf_data.wlc_name}', '{radio_mac}', '{ap_name}', '{eth_mac}', '{rf_tag}', '{site_tag}', '{model}'),"

                    self.write_mysql(f"REPLACE INTO Ap (wlcName, apRadioMac, apName, apEthMac, rfTag, siteTag, model) VALUES {query_string[:-1]};")

                    query_string = ""
                    for slot in slot_data:
                        query_string += f"('{slot[0]}','{slot[1]}','{slot[2]}','{slot[3]}','{slot[4]}','{slot[5]}','{slot[6]}'),"

                    self.write_mysql(f"REPLACE INTO Slot (apRadioMac, slot, operState, radioMode, band, channel, power) VALUES {query_string[:-1]};")


    def sql_wireless_rrm_oper(self, netconf_data):

        try:
            wireless_rrm_oper_data = ET.fromstring(netconf_data.wireless_rrm_oper).find(".//rrm-oper-data")

        except ET.ParseError:
            log.warning(f"XML parse error [wireless_rrm_oper]")
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
                log.warning(f"Data validation error [wireless_rrm_oper]")
            else:
                self.write_mysql(f"DELETE FROM SlotMetrics;")

                query_string = ""
                for measurement in rrm_data:
                    #self.write_mysql(f"UPDATE Slot SET stations = '{measurement[2]}', cca = '{measurement[3]}' WHERE apRadioMac = '{measurement[0]}' AND slot = '{measurement[1]}';")
                    query_string += f"('{measurement[0]}','{measurement[1]}','{measurement[2]}','{measurement[3]}'),"
                
                self.write_mysql(f"REPLACE INTO SlotMetrics (apRadioMac, slot, stations, cca) VALUES {query_string[:-1]};")

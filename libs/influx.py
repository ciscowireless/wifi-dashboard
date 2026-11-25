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
import re
import logging
import requests

import xml.etree.ElementTree as ET

log = logging.getLogger("wifininja.influx")


class Influx():


    def __init__(self, init):

        self.influx_ip = init.config["general"]["influx_ip"]
        self.influx_port = init.config["general"]["influx_port"]
        self.influx_org = init.config["general"]["influx_org"]
        self.influx_bucket = init.config["general"]["influx_bucket"]
        self.influx_api_key = init.influx_api_key
        self.mysql_session = init.mysql_session


    def read_mysql(self, query):

        cursor = self.mysql_session.cursor()
        cursor.execute(query)
        mysql_result = cursor.fetchall()
        cursor.close()
        #log.info("Read from MySQL")

        return mysql_result
    

    def write_influx(self, data, precision="s"):

        influx_api = f'http://{self.influx_ip}:{self.influx_port}/api/v2/write'
        headers = {
            "Content-Type" : "text/plain; charset=utf-8",
            "Accept" : "application/json",
            "Authorization": f'Token {self.influx_api_key}'
        }
        params = {
            "org" : self.influx_org,
            "bucket" : self.influx_bucket,
            "precision" : precision
        }
        try:
            result = requests.post(influx_api, headers=headers, params=params, data=data, timeout=3)
            if not str(result.status_code).startswith("2"): #Skip 2xx HTTP status
                log.info(f"POST Influx [{result.status_code}]{result.text}")

        except requests.exceptions.ReadTimeout:
            log.error(f"Influx connection timeout")
        except requests.exceptions.ConnectionError:
            log.error(f"Influx connection error") 


    def post_wireless_client_global_oper_client(self, netconf_data):

        try:
            client_live_stats = ET.fromstring(netconf_data.wireless_client_global_oper).find(".//client-live-stats")
            client_dot11_stats = ET.fromstring(netconf_data.wireless_client_global_oper).find(".//client-dot11-stats")

        except ET.ParseError:
            log.warning(f"XML parse error: wireless_client_global_oper (client)")
        else:
            try:
                random_mac_clients = int(client_live_stats.find("random-mac-clients").text)
                mobility_clients = int(client_live_stats.find("mobility-state-clients").text)
                iplearn_clients = int(client_live_stats.find("iplearn-state-clients").text)
                webauth_clients = int(client_live_stats.find("webauth-state-clients").text)
                delete_clients = int(client_live_stats.find("delete-state-clients").text)
                auth_clients = int(client_live_stats.find("auth-state-clients").text)
                run_clients = int(client_live_stats.find("run-state-clients").text)

                client_count = auth_clients + mobility_clients + iplearn_clients + webauth_clients + run_clients + delete_clients
                
                clients_24ghz = client_dot11_stats.find("num-clients-on-24ghz-radio").text
                clients_5ghz = client_dot11_stats.find("num-clients-on-5ghz-radio").text
                clients_6ghz = client_dot11_stats.find("num-6ghz-clients").text
      
            except AttributeError:
                log.warning(f"Data validation error: wireless_client_global_oper (client)")
            else:
                line_protocol = (
                                f'clientSummary,wlcName={netconf_data.wlc_name} '
                                f'totalClients={client_count},'
                                f'authClients={auth_clients},'
                                f'mobilityClients={mobility_clients},'
                                f'ipLearnClients={iplearn_clients},'
                                f'webAuthClients={webauth_clients},'
                                f'runClients={run_clients},'
                                f'deleteClients={delete_clients},'
                                f'randomMacClients={random_mac_clients},'
                                f'24ghzClients={clients_24ghz},'
                                f'5ghzClients={clients_5ghz},'
                                f'6ghzClients={clients_6ghz}'
                                f'\n'
                                )        
                self.write_influx(line_protocol)


    def post_wireless_client_global_oper_wlan(self, netconf_data):

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

                if len(wlan_data) == 0:
                    raise ValueError("No WLAN data")

            except AttributeError:
                log.warning(f"Data validation error: wireless_client_global_oper (wlan)")
            except ValueError:
                log.warning("No WLAN data, possible zero clients connected to WLC")
            else:
                line_protocol = ""
                for wlan in wlan_data:
                    line_protocol += (
                                     f'wlanSummary,wlcName={netconf_data.wlc_name},'
                                     f'wlanId={wlan[0]},'
                                     f'wlanProfileName={wlan[1]}'
                                     f' wlanUsers={wlan[2]},'
                                     f'wlanData={wlan[3]}'
                                     f'\n'
                                     ) 
                self.write_influx(line_protocol)


    def post_wireless_oper(self):

        query = (
            f"SELECT wlcName, Ap.apRadioMac, apName, rfTag, siteTag, Slot.slot, operState, radioMode, band, channel, power, stations, cca FROM Ap "
            f"JOIN Slot ON Ap.apRadioMac = Slot.apRadioMac "
            f"JOIN SlotMetrics ON Slot.apRadioMac = SlotMetrics.apRadioMac AND Slot.slot = SlotMetrics.slot "
            f"WHERE radioMode = 'radio-mode-local' AND operState = 'radio-up';"
            )
        
        result = self.read_mysql(query)
        influx_data = ""
        count_2, count_5, count_6 = 0, 0, 0

        for item in result:
            wlc_name = item[0]
            ap_radio_mac = item[1]
            ap_name = item[2]
            rf_tag = item[3]
            site_tag = item[4]
            slot = item[5]
            oper_state = item[6]
            radio_mode = item[7]
            band = item[8]
            channel = item[9]
            power = item[10]
            stations = item[11]
            cca = item[12]

            line_protocol = (
                            f'rfData,wlcName={wlc_name},'
                            f'apName={ap_name},'
                            f'apRadioMac={ap_radio_mac},'
                            f'slot={slot},'
                            f'band={band},'
                            f'rfTag={rf_tag},'
                            f'siteTag={site_tag},'
                            f'operState={oper_state},'
                            f'radioMode={radio_mode}'
                            f' channel={channel},'
                            f'power={power},'
                            f'stations={stations},'
                            f'cca={cca}'
                            f'\n'
                            )

            influx_data += line_protocol

            match band:
                case "dot11-2-dot-4-ghz-band": count_2 += 1
                case "dot11-5-ghz-band": count_5 += 1
                case "dot11-6-ghz-band": count_6 += 1

        if influx_data != "":
            self.write_influx(influx_data)
            log.info(f"2.4GHz slots: {count_2}, 5GHz slots: {count_5}, 6GHz slots: {count_6}")


    def post_wireless_oper_tag_summary(self):
        
        query = (
            f"SELECT wlcName, apName, rfTag, siteTag, Slot.slot, operState, radioMode, stations FROM Ap "
            f"JOIN Slot ON Ap.apRadioMac = Slot.apRadioMac "
            f"JOIN SlotMetrics ON Slot.apRadioMac = SlotMetrics.apRadioMac AND Slot.slot = SlotMetrics.slot "
            f"WHERE radioMode = 'radio-mode-local' AND operState = 'radio-up';"
            )
        
        result = self.read_mysql(query)
        influx_data = ""
        tag_summary = {}
        for item in result:
            wlc_name, rf_tag, site_tag, stations = item[0], item[2], item[3], int(item[7])

            if wlc_name not in tag_summary.keys():
                tag_summary[wlc_name] = {}
                tag_summary[wlc_name]["rf_tags"] = {}
                tag_summary[wlc_name]["site_tags"] = {}

            if rf_tag not in tag_summary[wlc_name]["rf_tags"].keys():
                tag_summary[wlc_name]["rf_tags"][rf_tag] = stations
            else:
                tag_summary[wlc_name]["rf_tags"][rf_tag] += stations

            if site_tag not in tag_summary[wlc_name]["site_tags"].keys():
                tag_summary[wlc_name]["site_tags"][site_tag] = stations
            else:
                tag_summary[wlc_name]["site_tags"][site_tag] += stations

        for wlc, summary in tag_summary.items():
            for tags in summary.keys():
                if tags == "rf_tags":
                    for tag in tag_summary[wlc]["rf_tags"]:
                        line_protocol = f'tagSummary,wlcName={wlc_name},tags=rfTags,tag={tag} '
                        line_protocol += f'clients={tag_summary[wlc]["rf_tags"][tag]}\n'
                        influx_data += line_protocol
                
                if tags == "site_tags":         
                    for tag in tag_summary[wlc]["site_tags"]:
                        line_protocol = f'tagSummary,wlcName={wlc_name},tags=siteTags,tag={tag} '
                        line_protocol += f'clients={tag_summary[wlc]["site_tags"][tag]}\n'
                        influx_data += line_protocol
        
        if influx_data != "":
            self.write_influx(influx_data)


    def post_interfaces_oper(self, netconf_data):

        try:
            interfaces_oper = ET.fromstring(netconf_data.interfaces_oper).find(".//interfaces")

        except ET.ParseError:
            log.warning(f"XML parse error [interfaces_oper]")
        else:
            intf_data = []
            try:
                for item in interfaces_oper.findall(".//interface"):
                    interface_name = item.find("name").text
                    interface_status = item.find("oper-status").text
                    tx = item.find("statistics/tx-kbps").text
                    rx = item.find("statistics/rx-kbps").text
                    in_errors = item.find("statistics/in-errors").text
                    out_errors = item.find("statistics/out-errors").text
                    in_discards = item.find("statistics/in-discards").text
                    out_discards = item.find("statistics/out-discards").text

                    intf_data.append([interface_name, interface_status, rx, tx, in_errors, out_errors, in_discards, out_discards])

            except AttributeError:
                log.warning(f"Data validation error [interfaces_oper]")
            else:
                line_protocol = ""
                for intf in intf_data:
                    line_protocol += (
                                     f'wlcInterfaces,wlcName={netconf_data.wlc_name},intName={intf[0]},intStatus={intf[1]}'
                                     f' rx={intf[2]},' 
                                     f'tx={intf[3]},'
                                     f'inErrors={intf[4]},'
                                     f'outErrors={intf[5]},'
                                     f'inDiscards={intf[6]},'
                                     f'outDiscards={intf[7]}'
                                     f'\n'
                                     )
                self.write_influx(line_protocol)

    
    def post_wireless_client_oper(self, netconf_data):

        try:
            wireless_client_oper = ET.fromstring(netconf_data.wireless_client_global_oper).find(".//client-oper-data")

        except ET.ParseError:
            log.warning(f"XML parse error [wireless_client_oper]")
        else:
            line_protocol = ""
            try:
                wifi_4, wifi_5, wifi_6, wifi_7, wifi_other = 0, 0, 0, 0, 0
                for item in wireless_client_oper.findall(".//common-oper-data"):
                    match item.find("ms-radio-type").text:
                        case "client-dot11be-6ghz-prot": wifi_7 += 1
                        case "client-dot11be-5ghz-prot": wifi_7 += 1
                        case "client-dot11be-24ghz-prot": wifi_7 += 1
                        case "client-dot11ax-6ghz-prot": wifi_6 += 1
                        case "client-dot11ax-5ghz-prot": wifi_6 += 1
                        case "client-dot11ax-24ghz-prot": wifi_6 += 1
                        case "client-dot11ac": wifi_5 += 1
                        case "client-dot11n-5-ghz-prot": wifi_4 += 1
                        case "client-dot11n-24-ghz-prot": wifi_4 += 1
                        case "client-dot11g-prot": wifi_other += 1
                        case "client-dot11a-prot": wifi_other += 1
                        case "client-dot11b-prot": wifi_other += 1
                        case _: wifi_other += 1
            
            except AttributeError:
                log.warning(f"Data validation error [wireless_client_oper]")
            else:
                line_protocol += (
                                 f'clientGenerations,wlcName={netconf_data.wlc_name}'
                                 f' wifi4={wifi_4},'
                                 f'wifi5={wifi_5},'
                                 f'wifi6={wifi_6},'
                                 f'wifi7={wifi_7},'
                                 f'wifiOther={wifi_other}'
                                 f'\n'
                                 )
                self.write_influx(line_protocol)


    def post_wlc_detail(self, netconf_data):

        try:
            wireless_ap_global_oper_data = ET.fromstring(netconf_data.wireless_ap_global_oper).find(".//ap-global-oper-data")
            device_hardware_oper = ET.fromstring(netconf_data.device_hardware_oper).find(".//device-hardware-data")
            install_oper = ET.fromstring(netconf_data.install_oper).find(".//install-oper-data")
            native = ET.fromstring(netconf_data.native).find(".//native")
            
        except ET.ParseError:
            log.warning(f"XML parse error: wlc_detail")
        else:
            try:
                software_version = device_hardware_oper.find("device-hardware/device-system-data/software-version").text
                joined_aps_count = wireless_ap_global_oper_data.find("emltd-join-count-stat/joined-aps-count").text
                part_number = device_hardware_oper.find("device-hardware/device-inventory/part-number").text
                sso_state = install_oper.find("install-location-information/oper-state/sso-state").text
                hostname = native.find("hostname").text

                software = re.search("Version [0-9.]+", software_version).group(0)[8:]

            except AttributeError:
                log.warning(f"Data validation error [wlc_detail]")
            else:
                match sso_state:
                    case "true":
                        sso_state = "Up"
                    case "false":
                        sso_state = "Down"
                
                line_protocol = (
                             f'wlcInventory,wlcName={netconf_data.wlc_name}'
                             f' wlcHostName=\"{hostname}\",'
                             f'model=\"{part_number}\",'
                             f'software=\"{software}\",'
                             f'sso=\"{sso_state}\",'
                             f'aps={joined_aps_count}'
                             f'\n'
                             )
                self.write_influx(line_protocol)


    def post_ap_inventory(self):

        query = (f"SELECT wlcName, apRadioMac, apName, rfTag, siteTag, model FROM Ap;")
        result = self.read_mysql(query)

        if len(result) > 0:

            ap_models = {}
            for item in result:
                wlc_name = item[0]
                ap_radio_mac = item[1]
                ap_name = item[2]
                rf_tag = item[3]
                site_tag = item[4]
                model = item[5]

                if model not in ap_models.keys():
                    ap_models[model] = 1
                else:
                    ap_models[model] += 1

            line_protocol = (f'apInventory,wlcName={wlc_name} ')

            for ap_model, count in ap_models.items():
                line_protocol += f'{ap_model}={count},'

            line_protocol = line_protocol[:-1] + f'\n'
            self.write_influx(line_protocol)


    def post_rogue_oper(self, netconf_data):

        try:
            rogue_oper_data = ET.fromstring(netconf_data.rogue_oper).find(".//rogue-oper-data")
        
        except ET.ParseError:
            log.warning(f"XML parse error [rogue_oper]")
        else:
            line_protocol = ""
            try:
                for rogue in rogue_oper_data.findall(".//rogue-data"):
                    address = rogue.find("rogue-address").text
                    ssid = rogue.find("last-heard-ssid").text
                    ssid = ">>HIDDEN<<" if not ssid else ssid.replace(" ", "\\ ")
                    last_seen_day = rogue.find("rogue-last-timestamp").text.split("T")[0]
                    last_seen_time = rogue.find("rogue-last-timestamp").text.split("T")[1][:-13]
                    last_seen = f"{last_seen_day} @ " + f"{last_seen_time:0<8}"[:-3]
                    channel = rogue.find("last-channel").text
                    clients = rogue.find("n-clients").text
                    max_rssi = rogue.find("max-detected-rssi").text
                    detecting_ap = rogue.find("ap-name-max-rssi").text
                    radio_type = rogue.find("rogue-radio-type-max-rssi").text[:-11].lstrip("802-")
                    width_2 = int(rogue.find("./band-data-2dot4g/chan-width").text)
                    width_5 = int(rogue.find("./band-data-5g/chan-width").text)
                    width_6 = int(rogue.find("./band-data-6g/chan-width").text)
                    width = max(width_2, width_5, width_6) #Only one has a non-zero value
                    line_protocol += (
                                     f'rogueAP,address={address},ssid={ssid}'
                                     f' radio=\"{radio_type}\",'
                                     f'channel=\"{channel}\",'
                                     f'lastSeen=\"{last_seen}\",'
                                     f'detectingAP=\"{detecting_ap}\",'
                                     f'maxRssi={max_rssi},'
                                     f'channelWidth=\"{width} MHz\",'
                                     f'clients=\"{clients}\"'
                                     f'\n'
                                     )

            except AttributeError:
                log.warning(f"Data validation error: wireless_rogue_oper")
            else:
                self.write_influx(line_protocol)
                
            






import logging
import requests
import time

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
            #log.info(f"POST Influx [{result.status_code}]{result.text}")

        except requests.exceptions.ReadTimeout:
            log.error(f"Influx connection timeout")
        except requests.exceptions.ConnectionError:
            log.error(f"Influx connection error") 


    def post_wireless_client_global_oper_client(self):

        query = ("SELECT * from Client")
        result = self.read_mysql(query)
        influx_data = ""

        for item in result:
            #wlc_ip = item[0]
            wlc_name = item[1]
            auth_clients = item[2]
            mobility_clients = item[3]
            iplearn_clients = item[4]
            webauth_clients = item[5]
            run_clients = item[6]
            delete_clients = item[7]
            random_mac_clients = item[8]
            clients_24ghz = item[9]
            clients_5ghz = item[10]
            clients_6ghz = item[11]
            
            line_protocol = (
                            f'clientSummary,wlcName={wlc_name} '
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
            
            influx_data += line_protocol
        
        if influx_data != "":
            self.write_influx(influx_data)


    def post_wireless_client_global_oper_wlan(self):

        query = ("SELECT wlcName, wlanId, wlanProfileName, wlanUsers, wlanDataUsage from Wlan")
        result = self.read_mysql(query)
        influx_data = ""

        for item in result:
            wlc_name = item[0]
            wlan_id = item[1]
            wlan_name = item[2]
            wlan_users = item[3]
            wlan_data = item[4]
            
            line_protocol = (
                            f'wlanSummary,wlcName={wlc_name},'
                            f'wlanId={wlan_id},'
                            f'wlanProfileName={wlan_name}'
                            f' wlanUsers={wlan_users},'
                            f'wlanData={wlan_data}'
                            f'\n'
                            )
            
            influx_data += line_protocol
        
        if influx_data != "":
            self.write_influx(influx_data)


    def post_wireless_oper(self):

        query = ("SELECT * FROM Ap JOIN Slot ON Ap.apRadioMac = Slot.apRadioMac WHERE radioMode = 'radio-mode-local' AND operState = 'radio-up'")
        result = self.read_mysql(query)
        influx_data = ""
        count_2, count_5, count_6 = 0, 0, 0

        for item in result:
            ap_radio_mac = item[0]
            ap_name = item[1]
            #ap_eth_mac = item[2]
            rf_tag = item[3]
            site_tag = item[4]
            #ap_radio_mac = item[5] #SQL JOIN *
            slot = item[6]
            oper_state = item[7]
            radio_mode = item[8]
            band = item[9]
            channel = item[10]
            power = item[11]
            stations = item[12]
            cca = item[13]

            line_protocol = (
                            f'rfData,wlcName=Yay,'
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


    def post_wlc_oper(self):

        query = ("SELECT wlcName, joinedAps, Tx, Rx, interfaceName from Wlc")
        result = self.read_mysql(query)
        influx_data = ""

        for item in result:
            wlc_name = item[0]
            joined_aps = item[1]
            rx = item[2]
            tx = item[3]
            interface_name = item[4]
            
            line_protocol = f'wlcSummary,wlcName={wlc_name},intName={interface_name} joinedAps={joined_aps},tx={tx},rx={rx}\n'
            
            influx_data += line_protocol
        
        if influx_data != "":
            self.write_influx(influx_data)


    def post_wireless_client_oper(self):

        query = ("SELECT wlcName, wifi4, wifi5, wifi6, wifiOther from Client")
        result = self.read_mysql(query)
        influx_data = ""
        
        for item in result:
            wlc_name = item[0]
            wifi_4 = item[1]
            wifi_5 = item[2]
            wifi_6 = item[3]
            wifi_other = item[4]

            line_protocol = (
                            f'clientProtocols,wlcName={wlc_name}'
                            f' wifi4={wifi_4},'
                            f'wifi5={wifi_5},'
                            f'wifi6={wifi_6},'
                            f'wifiOther={wifi_other}'
                            f'\n'
                            )
            
            influx_data += line_protocol

            if influx_data != "":
                self.write_influx(influx_data)

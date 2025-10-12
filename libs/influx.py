import logging
import requests

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


    def post_wlc_oper(self):

        query = ("SELECT Wlc.wlcName, interfaceName, interfaceOperStatus, rxKbps, txKbps, inErrors, outErrors, inDiscards, outDiscards FROM Wlc JOIN WlcInterfaces")

        result = self.read_mysql(query)
        influx_data = ""

        for item in result:
            wlc_name = item[0]
            interface_name = item[1]
            interface_status = item[2]
            rx = item[3]
            tx = item[4]
            in_errors = item[5]
            out_errors = item[6]
            in_discards = item[7]
            out_discards = item[8]
            
            line_protocol = (
                            f'wlcInterfaces,wlcName={wlc_name},intName={interface_name},intStatus={interface_status}'
                            f' rx={rx},' 
                            f'tx={tx},'
                            f'inErrors={in_errors},'
                            f'outErrors={out_errors},'
                            f'inDiscards={in_discards},'
                            f'outDiscards={out_discards}'
                            f'\n'
                            )
            
            influx_data += line_protocol
        
        if influx_data != "":
            self.write_influx(influx_data)


    def post_wireless_client_oper(self):

        query = (
            f"SELECT wlcName, wifi4, wifi5, wifi6, wifi7, wifiOther from Client "
            f"WHERE wifi4 IS NOT NULL "
            f"AND wifi5 IS NOT NULL "
            f"AND wifi6 IS NOT NULL "
            f"AND wifi7 IS NOT NULL "
            f"AND wifiOther IS NOT NULL;"
            )
        result = self.read_mysql(query)
        influx_data = ""
        
        for item in result:
            wlc_name = item[0]
            wifi_4 = item[1]
            wifi_5 = item[2]
            wifi_6 = item[3]
            wifi_7 = item[4]
            wifi_other = item[5]

            line_protocol = (
                            f'clientGenerations,wlcName={wlc_name}'
                            f' wifi4={wifi_4},'
                            f'wifi5={wifi_5},'
                            f'wifi6={wifi_6},'
                            f'wifi7={wifi_7},'
                            f'wifiOther={wifi_other}'
                            f'\n'
                            )
            
            influx_data += line_protocol

            if influx_data != "":
                self.write_influx(influx_data)
    

    def post_wlc_inventory(self):

        query = (
            f"SELECT WlcDetail.wlcName, hostName, model, software, ssoState, joinedAps, "
            f"authClients, mobilityClients, ipLearnClients, webAuthClients, runClients, deleteClients FROM WlcDetail "
            f"JOIN Wlc ON WlcDetail.wlcIp = Wlc.wlcIp "
            f"JOIN Client ON WlcDetail.wlcIp = Client.wlcIp;"
            )
        result = self.read_mysql(query)

        if len(result) > 0:

            influx_data = ""
            wlc_name = result[0][0]
            hostname = result[0][1]
            model = result[0][2]
            software = result[0][3]
            sso = result[0][4]
            match sso:
                case "true":
                    sso_state = "Up"
                case "false":
                    sso_state = "Down"

            ap_count = result[0][5]
            client_count = result[0][6] + result[0][7] + result[0][8] + result[0][9] + result[0][10] + result[0][11]
            
            line_protocol = (
                            f'wlcInventory,wlcName={wlc_name}'
                            f' wlcHostName=\"{hostname}\",'
                            f'model=\"{model}\",'
                            f'software=\"{software}\",'
                            f'sso=\"{sso_state}\",'
                            f'aps={ap_count},'
                            f'clients={client_count}'
                            f'\n'
                            )
            
            influx_data += line_protocol

            if influx_data != "":
                    self.write_influx(influx_data)


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

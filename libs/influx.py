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
        log.info("Read from MySQL")

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
            log.info(f"Post to Influx ({result.status_code})")

        except requests.exceptions.ReadTimeout:
            log.error(f"Influx connection timeout")
        except requests.exceptions.ConnectionError:
            log.error(f"Influx connection error") 


    def put_wireless_client_global_oper(self):

        query = ("SELECT * from ClientLiveStats")
        result = self.read_mysql(query)
        
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

            line_protocol = f"wlcData,wlcName={wlc_name} "\
                            f"authClients={auth_clients},"\
                            f"mobilityClients={mobility_clients},"\
                            f"ipLearnClients={iplearn_clients},"\
                            f"webAuthClients={webauth_clients},"\
                            f"runClients={run_clients},"\
                            f"deleteClients={delete_clients},"\
                            f"randomMacClients={random_mac_clients},"\
                            f"24ghzClients={clients_24ghz},"\
                            f"5ghzClients={clients_5ghz},"\
                            f"6ghzClients={clients_6ghz} "
            
            self.write_influx(line_protocol)



'''
This is a testing script, it is not part of the dashboard code
'''
import time
import os
import re

from ncclient import manager, transport, operations
import xml.etree.ElementTree as ET

WLC_IP = "192.168.2.8"

TEST_FILTER = '''
    <client-global-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-client-global-oper">
        <client-live-stats/>
        <client-stats>
            <co-client-del-reason/>
        </client-stats>
        <client-dot11-stats>
            <num-clients-on-24ghz-radio/>
            <num-clients-on-5ghz-radio/>
            <num-6ghz-clients/>
        </client-dot11-stats>
        <sort-wlan>
            <mapping>wlan-top-by-clients</mapping>
        </sort-wlan>
    </client-global-oper-data>
'''

def netconf_rpc(filter, timeout = 60):

        try:
            netconf_output = ""
            start = time.time()
            with manager.connect(host=WLC_IP,
                                 port=830,
                                 username=os.environ["IOSXE_USER"],
                                 password=os.environ["IOSXE_PASS"],
                                 device_params={"name":"iosxe"},
                                 timeout=timeout,
                                 hostkey_verify=False) as ncc:
                netconf_output = ncc.get(filter=("subtree", filter)).data_xml
                netconf_output = re.sub('xmlns="[^"]+"', "", netconf_output)
            end = time.time()
            query_duration = round(end - start, 1)

        except transport.errors.AuthenticationError:
            print(f"NETCONF Authentication Error")       
        except operations.errors.TimeoutExpiredError:
            print(f"NETCONF Timeout ({timeout}sec)")
        except (transport.errors.SSHError, transport.errors.SessionError):
            print(f"NETCONF Error")
        else:
            print(f"Netconf query took {query_duration}s")

        return netconf_output


def parse(netconf_data):

        try:
            co_client_del_reason = ET.fromstring(netconf_data).find(".//co-client-del-reason")
        
        except ET.ParseError:
            print(f"XML parse error")
        else:
            try:
                delete_reasons = dict({element.tag: int(element.text) for element in co_client_del_reason.iter() if element is not co_client_del_reason}) #Parse all possible reasons, excluding root
                delete_reasons_sorted = {k: v for k, v in sorted(delete_reasons.items(), key=lambda item: item[1], reverse=True)}

                line_protocol = f'deleteReasons,wlcIP={WLC_IP} '
                for reason, counter in delete_reasons_sorted.items():
                    line_protocol += (
                        f'{reason}={counter}i,'
                    )
                line_protocol = line_protocol[:-1] + "\n"

                print(line_protocol)
            except AttributeError:
                print(f"Data validation error")
     

if __name__ == "__main__":

    data = netconf_rpc(TEST_FILTER)
    parse(data)

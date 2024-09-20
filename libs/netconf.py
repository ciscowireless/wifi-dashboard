import logging
import time
import re

from ncclient import manager, transport, operations

log = logging.getLogger("wifininja.netconf")


class Netconf():


    def __init__(self, init):

        self.iosxe_user = init.iosxe_user
        self.iosxe_pass = init.iosxe_pass


    def netconf_rpc(self, filter):

        try:
            start = time.time()
            with manager.connect(host=self.wlc_ip,
                                 port=830,
                                 username=self.iosxe_user,
                                 password=self.iosxe_pass,
                                 device_params={"name":"iosxe"},
                                 hostkey_verify=False) as ncc:
                netconf_output = ncc.get(filter=("subtree", filter)).data_xml
                netconf_output = re.sub('xmlns="[^"]+"', "", netconf_output)
            end = time.time()

        except (transport.errors.SSHError, operations.errors.TimeoutExpiredError, transport.errors.SessionError, transport.errors.AuthenticationError):
            netconf_output = ""
            log.error(f"NETCONF error")
        else:
            log.info(f"Netconf query took {round(end - start, 1)}s")

        return netconf_output
    

    def get_wireless_client_global_oper(self):

        filter = '''
            <client-global-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-client-global-oper">
                <client-live-stats/>
                <client-dot11-stats>
                    <num-clients-on-24ghz-radio/>
                    <num-clients-on-5ghz-radio/>
                    <num-6ghz-clients/>
                </client-dot11-stats>
            </client-global-oper-data>
        '''

        self.wireless_client_global_oper = self.netconf_rpc(filter)

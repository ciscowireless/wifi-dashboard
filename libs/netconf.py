import logging
import time
import re

from ncclient import manager, transport, operations

from libs.influx import Influx

log = logging.getLogger("wifininja.netconf")


class Netconf():


    def __init__(self, init):

        self.influx = Influx(init)


    def netconf_rpc(self, filter, query = "", timeout = 30):

        try:
            netconf_output = ""
            start = time.time()
            with manager.connect(host=self.wlc_ip,
                                 port=830,
                                 username=self.wlc_user,
                                 password=self.wlc_pass,
                                 device_params={"name":"iosxe"},
                                 timeout=timeout,
                                 hostkey_verify=False) as ncc:
                netconf_output = ncc.get(filter=("subtree", filter)).data_xml
                netconf_output = re.sub('xmlns="[^"]+"', "", netconf_output)
            end = time.time()
            query_duration = round(end - start, 1)

        except (transport.errors.SSHError, transport.errors.SessionError, transport.errors.AuthenticationError):
            log.error(f"NETCONF Error")
        except operations.errors.TimeoutExpiredError:
            log.error(f"NETCONF Timeout")
        else:
            log.info(f"Netconf query took {query_duration}s [{query}]")
            self.influx.write_influx(f'dashboardStats,wlcIp={self.wlc_ip} {query}={query_duration}\n')

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
                <sort-wlan>
                    <mapping>wlan-top-by-clients</mapping>
                </sort-wlan>
            </client-global-oper-data>
        '''
        self.wireless_client_global_oper = self.netconf_rpc(filter, "wireless-client-global-oper")
    

    def get_wireless_access_point_oper(self):

        filter = '''
            <access-point-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-access-point-oper">
                <ap-name-mac-map/>
                <radio-oper-data>
                    <wtp-mac/>
                    <radio-slot-id/>
                    <oper-state/>
                    <radio-mode/>
                    <current-active-band/>
                    <phy-ht-cfg>
                        <cfg-data>
                            <curr-freq/>
                        </cfg-data>
                    </phy-ht-cfg>
                    <radio-band-info>
                        <phy-tx-pwr-cfg>
                            <cfg-data>
                                <current-tx-power-level/>
                            </cfg-data>
                        </phy-tx-pwr-cfg>
                    </radio-band-info>
                </radio-oper-data>
                <capwap-data>
                    <wtp-mac/>
                    <device-detail>
                        <static-info>
                            <ap-models>
                                <model/>
                            </ap-models>
                        </static-info>
                    </device-detail>
                    <tag-info>
                        <site-tag>
                            <site-tag-name/>
                        </site-tag>
                        <rf-tag>
                            <rf-tag-name/>
                        </rf-tag>
                    </tag-info>

                </capwap-data>
            </access-point-oper-data>
        '''
        self.wireless_client_global_oper = self.netconf_rpc(filter, "wireless-access-point-oper")
    

    def get_wireless_rrm_oper(self):
        
        filter = '''
            <rrm-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-rrm-oper">
                <rrm-measurement>
                    <wtp-mac/>
                    <radio-slot-id/>
                    <load>
                        <cca-util-percentage/>
                        <stations/>
                    </load>
                </rrm-measurement>
            </rrm-oper-data>
        '''
        self.wireless_rrm_oper = self.netconf_rpc(filter, "wireless-rrm-oper")


    def get_wireless_ap_global_oper(self):
        
        filter = '''
            <ap-global-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-ap-global-oper">
                <emltd-join-count-stat>
                    <joined-aps-count/>
                </emltd-join-count-stat>
            </ap-global-oper-data>
        '''
        self.wireless_ap_global_oper = self.netconf_rpc(filter, "wireless-ap-global-oper")


    def get_wireless_client_oper(self):

        filter = '''
            <client-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-client-oper">
                <common-oper-data>
                    <ms-radio-type/>
                </common-oper-data>
            </client-oper-data>
        '''
        self.wireless_client_global_oper = self.netconf_rpc(filter, "wireless-client-oper")


    def get_interfaces_oper(self):

        filter = f'''
            <interfaces xmlns='http://cisco.com/ns/yang/Cisco-IOS-XE-interfaces-oper'>
                <interface>
                    <name>{self.wlc_interface}</name>
                    <statistics>
                        <rx-kbps/>
                        <tx-kbps/>
                    </statistics>
                </interface>
            </interfaces>
        '''
        self.interfaces_oper = self.netconf_rpc(filter, "interfaces-oper")


    def get_device_hardware_oper(self):

        filter = f'''
            <device-hardware-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-device-hardware-oper">
                <device-hardware>
                <device-inventory>
                    <hw-type>hw-type-chassis</hw-type>
                    <part-number/>
                </device-inventory>
                <device-system-data>
                    <software-version/>
                </device-system-data>
                </device-hardware>
            </device-hardware-data>
        '''
        self.device_hardware_oper = self.netconf_rpc(filter, "device-hardware-oper")


    def get_native(self):
       
        filter = f'''
            <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
                <hostname/>
            </native>
        '''
        self.native = self.netconf_rpc(filter, "native")


    def get_install_oper(self):

        filter = f'''
            <install-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-install-oper">
                <install-location-information>
                <oper-state>
                    <sso-state/>
                </oper-state>
                </install-location-information>
            </install-oper-data>
        '''
        self.install_oper = self.netconf_rpc(filter, "install-oper")
import logging
import xml.etree.ElementTree as ET

from collections import Counter, OrderedDict

log = logging.getLogger("wifininja.parseLib")


def parse_wireless_clients(netconf_dict):

    phy_data = {}
    total_clients = 0
    try:
        client_phy = netconf_dict["data"]["client-oper-data"]["dot11-oper-data"]
    except KeyError:
        log.warning(f"No client PHY data")
    else:
        if type(client_phy) in (dict, OrderedDict): #Change to list if only single client on WLC
            client_phy = [client_phy]

        for client in client_phy:
            total_clients += 1
            phy = rename_phy(client["ewlc-ms-phy-type"])
            if phy in phy_data.keys():
                phy_data[phy] += 1
            else:
                phy_data[phy] = 1
        
        phy_data = {"per-phy" : dict(sorted(phy_data.items(), reverse=True))}

    finally:
        phy_data = {**phy_data, "all-clients" : total_clients}

    return phy_data


def parse_wireless_devices(netconf_dict):

    os_type_data = {}
    try:
        client_types = netconf_dict["data"]["client-oper-data"]["dc-info"]
    except KeyError:
        log.warning(f"No client device data")
    else:
        if type(client_types) in (dict, OrderedDict): #Change to list if only a single client on WLC
            client_types = [client_types]

        os_data = []
        for client_type in client_types:
            try:
                os_data.append(client_type["device-os"])
            except KeyError:
                pass
                #log.info(f"Client OS not available")
        
        top_os = Counter(os_data)
        top_os_total = sum(top_os.values())
        
        for tup in top_os.most_common():
            os_type_data[tup[0]] = f"{int(int(tup[1])/top_os_total*100)} %"
        
        os_type_data = {"top-os" : os_type_data}

    return os_type_data


def parse_interfaces_oper(netconf_tree, interface):

    try:
        interface_data = ET.fromstring(netconf_tree).find(".//interface")
    except (KeyError, ET.ParseError):
        log.warning(f"No WLC interface data")
        return {}
    else:
        try:
            in_octets = interface_data.find("statistics/in-octets").text
            out_octets = interface_data.find("statistics/out-octets-64").text
            in_octets_units = change_units(in_octets)
            out_octets_units = change_units(out_octets)

            in_discards = int(interface_data.find("statistics/in-discards").text)
            in_discards_64 = int(interface_data.find("statistics/in-discards-64").text)
            in_unknown_protos = int(interface_data.find("statistics/in-unknown-protos").text)
            in_unknown_protos_64 = int(interface_data.find("statistics/in-unknown-protos-64").text)
            in_drops = in_discards + in_discards_64 + in_unknown_protos + in_unknown_protos_64
        
            out_discards = int(interface_data.find("statistics/out-discards").text)
            out_drops = out_discards
        except AttributeError:
            log.warning(f"Bad WLC interface data")
            return {}
        else:
            return {
                "lan-interface" : interface,
                "in-bytes" : in_octets,
                "out-bytes" : out_octets,
                "in-bytes-units" : in_octets_units,
                "out-bytes-units" : out_octets_units,
                "in-drops" : in_drops,
                "out-drops" : out_drops,
                "out-discards" : out_drops,
                "in-discards" : in_discards,
                "in-discards-64" : in_discards_64,
                "in-unknown-protos" : in_unknown_protos,
                "in-unknown-protos-64" : in_unknown_protos_64
            }


def parse_wireless_client_states(netconf_dict):

    try:
        client_state_data = netconf_dict["data"]["client-global-oper-data"]["client-live-stats"]
    except KeyError:
        log.warning(f"No client state data")
        return {}
    else:
        return {
            "client-states" : {
                "auth" : client_state_data["auth-state-clients"],
                "mobility" : client_state_data["mobility-state-clients"],
                "iplearn" : client_state_data["iplearn-state-clients"],
                "webauth" : client_state_data["webauth-state-clients"],
                "run" : client_state_data["run-state-clients"],
                "delete" : client_state_data["delete-state-clients"],
                "random-mac" : client_state_data["random-mac-clients"]
            }
        }


def parse_ap_name(netconf_dict):

    ap_data = {}
    try:
        ap_name_data = netconf_dict["data"]["access-point-oper-data"]["ap-name-mac-map"]
    except KeyError:
        log.warning(f"No AP name data")
    else:
        if type(ap_name_data) in (dict, OrderedDict): #Change to list if only a single AP on WLC
            ap_name_data = [ap_name_data]

        for ap in ap_name_data:
            ap_name = ap["wtp-name"]
            ap_mac_lan = ap["eth-mac"]
            ap_mac_wifi = ap["wtp-mac"]
            ap_data[ap_mac_wifi] =  {"ap_name" : ap_name, "eth_mac" : ap_mac_lan, "slot-count": 0}
    
    return ap_data


def parse_ap_ops_radio(netconf_dict, ap_data):

    try:
        ap_ops_data = netconf_dict["data"]["access-point-oper-data"]["radio-oper-data"]
    except KeyError:
        log.warning(f"No AP operational radio data")
    else:
        for radio in ap_ops_data:
            try:
                ap_data[radio["wtp-mac"]]["slot-count"] += 1
                ap_data[radio["wtp-mac"]][radio["radio-slot-id"]] = {}
                ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["state"] = radio["oper-state"]
                ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["band"] = radio["current-active-band"]
                ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["mode"] = radio ["radio-mode"]

                if radio ["radio-mode"] == "radio-mode-local":
                    ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["channel"] = radio["phy-ht-cfg"]["cfg-data"]["curr-freq"]
                    ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["width"] = radio["phy-ht-cfg"]["cfg-data"]["chan-width"]
                else:
                    ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["channel"] = ""
                    ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["width"] = ""
            except KeyError:
                continue #Script crashed at 05:15 on PSV WLC on line 158
    
    return ap_data


def parse_ap_ops_capwap(netconf_dict, ap_data):

    try:
        ap_ops_data = netconf_dict["data"]["access-point-oper-data"]["capwap-data"]
    except KeyError:
        log.warning(f"No AP operational capwap data")
    else:
        for ap in ap_ops_data:            
            ap_data[ap["wtp-mac"]]["site-tag"] = ap["tag-info"]["site-tag"]["site-tag-name"]
            ap_data[ap["wtp-mac"]]["rf-tag"] = ap["tag-info"]["rf-tag"]["rf-tag-name"]

    return ap_data


def parse_ap_cfg(netconf_dict, ap_data):

    try:
        ap_cfg_data = netconf_dict["data"]["ap-cfg-data"]["ap-tags"]["ap-tag"]
    except KeyError:
        log.warning(f"No AP configuration data")
    else:
        for ap in ap_cfg_data:
            for radio_mac in ap_data.keys():
                if ap_data[radio_mac]["eth_mac"] == ap["ap-mac"]:
                    try:
                        ap_data[radio_mac]["site-tag"] = ap["site-tag"]
                    except KeyError:
                        log.warning(f"AP {ap['ap-mac']} no site-tag value")
                        ap_data[radio_mac]["site-tag"] = "null"
                    try:
                        ap_data[radio_mac]["rf-tag"] = ap["rf-tag"]
                    except KeyError:
                        log.warning(f"AP {ap['ap-mac']} no rf-tag value")
                        ap_data[radio_mac]["rf-tag"] = "null"
    
    return ap_data


def parse_ap_rrm(netconf_dict, ap_data):

    try:
        ap_rrm_data = netconf_dict["data"]["rrm-oper-data"]["rrm-measurement"]
        ap_radio_slot_data = netconf_dict["data"]["rrm-oper-data"]["radio-slot"]
    except KeyError:
        log.warning(f"No AP RRM/Radio data")
    else:
        for radio in ap_rrm_data:
            try:
                ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["stations"] = radio["load"]["stations"]
            except KeyError:
                #ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["stations"] = "0"
                log.info("No client count for AP")
                continue
            try:
                ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["ch_util"] = radio["load"]["rx-noise-channel-utilization"]
            except KeyError:
                #ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["ch_util"] = "0"
                log.info("No channel utilization for AP")
                continue
        for slot in ap_radio_slot_data:
            try:
                ap_data[slot["wtp-mac"]][slot["radio-slot-id"]]["ch_changes"] = slot["radio-data"]["dca-stats"]["chan-changes"]
            except KeyError:
                #ap_data[slot["wtp-mac"]][slot["radio-slot-id"]]["ch_changes"] = "0"
                log.info("No channel changes for AP")
                continue

    return ap_data


def rename_phy(phy):

    phy = phy.lstrip("client-").rstrip("-prot")
    if phy == "dot11ax-6ghz": phy = "Wi-Fi_6_(6GHz)"
    if phy == "dot11ax-5ghz": phy = "Wi-Fi_6_(5GHz)"
    if phy == "dot11ax-24ghz": phy = "Wi-Fi_6_(2.4GHz)"
    if phy == "dot11ac": phy = "Wi-Fi_5"
    if phy == "dot11n-5-ghz": phy = "Wi-Fi_4_(5GHz)"
    if phy == "dot11n-24-ghz": phy = "Wi-Fi_4_(2.4GHz)"
    if phy == "dot11g": phy = "Wi-Fi_3"
    if phy == "dot11a": phy = "Wi-Fi_2"
    if phy == "dot11b": phy = "Wi-Fi_1"

    return phy


def change_units(bytes):

    if len(bytes) > 15:
        throughput = str(round(int(bytes) / 1000000000000000, 1)) + " PB"
    elif len(bytes) > 12:
        throughput = str(round(int(bytes) / 1000000000000, 1)) + " TB"
    elif len(bytes) > 9:
        throughput = str(round(int(bytes) / 1000000000, 1)) + " GB"
    elif len(bytes) > 6:
        throughput = str(round(int(bytes) / 1000000, 1)) + " MB"
    else:
        throughput = str(round(int(bytes) / 1000, 1)) + " KB"
    
    return throughput

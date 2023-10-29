import logging

import commsLib

log = logging.getLogger("wifininja.dashboardLib")


def send_to_dashboard_wlc(env, wlc_data):

    commsLib.send_to_dashboard(env, "WLC", wlc_data)


def send_to_dashboard_ap(env, ap_data):

    commsLib.send_to_dashboard(env, "AP", summarize_rrm_data(env, ap_data))


def summarize_rrm_data(env, ap_data):

    ap_data_summary = {}

    top_sta_2, top_util_2, top_change_2 = [], [], []
    top_sta_5, top_util_5, top_change_5 = [], [], []
    top_sta_6, top_util_6, top_change_6 = [], [], []

    for ap in ap_data.keys():
        for slot in range(0, ap_data[ap]["slot-count"]):
            try:
                if ap_data[ap][str(slot)]["state"] == "radio-up":

                    ap_name = ap_data[ap]["ap_name"]
                    ap_slot = slot
                    ap_ch = ap_data[ap][str(slot)]["channel"]
                    ap_sta = int(ap_data[ap][str(slot)]["stations"])
                    ap_util = int(ap_data[ap][str(slot)]["ch_util"])
                    ap_change = int(ap_data[ap][str(slot)]["ch_changes"])
                    ap_change_colour = "grey"

                    ap_sta_colour = "orange"
                    if ap_sta < int(env["AP_CLIENTS_LOW"]):
                        ap_sta_colour = "green"
                    if ap_sta >= int(env["AP_CLIENTS_HIGH"]):
                        ap_sta_colour = "red"

                    ap_util_colour = "orange"
                    if ap_util < int(env["AP_UTIL_LOW"]):
                        ap_util_colour = "green"
                    if ap_util >= int(env["AP_UTIL_HIGH"]):
                        ap_util_colour = "red"
                
                    if ap_data[ap][str(slot)]["band"] == "dot11-2-dot-4-ghz-band":    
                        top_sta_2.append((ap_name, ap_slot, ap_ch, ap_sta_colour, ap_sta))
                        top_util_2.append((ap_name, ap_slot, ap_ch, ap_util_colour, ap_util))
                        top_change_2.append((ap_name, ap_slot, ap_ch, ap_change_colour, ap_change))

                    if ap_data[ap][str(slot)]["band"] == "dot11-5-ghz-band":    
                        top_sta_5.append((ap_name, ap_slot, ap_ch, ap_sta_colour, ap_sta))
                        top_util_5.append((ap_name, ap_slot, ap_ch, ap_util_colour, ap_util))
                        top_change_5.append((ap_name, ap_slot, ap_ch, ap_change_colour, ap_change))

                    if ap_data[ap][str(slot)]["band"] == "dot11-6-ghz-band":
                        top_sta_6.append((ap_name, ap_slot, ap_ch, ap_sta_colour, ap_sta))
                        top_util_6.append((ap_name, ap_slot, ap_ch, ap_util_colour, ap_util))
                        top_change_6.append((ap_name, ap_slot, ap_ch, ap_change_colour, ap_change))

            except KeyError:
                log.info(f"No data for {ap} slot {slot}")

    ap_data_summary["ch_util_2"] = sorted(top_util_2, key=lambda tup: tup[4], reverse=True)[0:int(env["SEND_TOP"])]
    ap_data_summary["ch_util_5"] = sorted(top_util_5, key=lambda tup: tup[4], reverse=True)[0:int(env["SEND_TOP"])]
    ap_data_summary["ch_util_6"] = sorted(top_util_6, key=lambda tup: tup[4], reverse=True)[0:int(env["SEND_TOP"])]
    ap_data_summary["stations_2"] = sorted(top_sta_2, key=lambda tup: tup[4], reverse=True)[0:int(env["SEND_TOP"])]
    ap_data_summary["stations_5"] = sorted(top_sta_5, key=lambda tup: tup[4], reverse=True)[0:int(env["SEND_TOP"])]
    ap_data_summary["stations_6"] = sorted(top_sta_6, key=lambda tup: tup[4], reverse=True)[0:int(env["SEND_TOP"])]
    ap_data_summary["ch_changes_2"] = sorted(top_change_2, key=lambda tup: tup[4], reverse=True)[0:int(env["SEND_TOP"])]
    ap_data_summary["ch_changes_5"] = sorted(top_change_5, key=lambda tup: tup[4], reverse=True)[0:int(env["SEND_TOP"])]
    ap_data_summary["ch_changes_6"] = sorted(top_change_6, key=lambda tup: tup[4], reverse=True)[0:int(env["SEND_TOP"])]

    return ap_data_summary
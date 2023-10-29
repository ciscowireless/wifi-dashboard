import time
import json
import logging

import commsLib
import envLib

env = envLib.read_config_file()
log = logging.getLogger("wifininja.influxLib")


def send_to_influx_wlc(env, wlc_data):

    try:
        load_data = f"wlcData,wlcName=WLC9800 "
        for wncd in wlc_data["wncd_load"]:
            load_data += f"{wncd[1]}={wncd[0]},"
        
        load_data = load_data.rstrip(",") + " "

        commsLib.send_to_influx(env, load_data)

    except KeyError:
        log.warning("Data error sending to Influx (WNCD load)")

    try:
        commsLib.send_to_influx(env,
            f"wlcData,wlcName=WLC9800 "\
            f"inBytes={wlc_data['in-bytes']},"\
            f"outBytes={wlc_data['out-bytes']},"\
            f"inDrops={wlc_data['in-drops']},"\
            f"outDrops={wlc_data['out-drops']} "
        )
    except KeyError:
        log.warning("Data error sending to Influx (WLC Interface stats)")

    try:
        commsLib.send_to_influx(env,
            f"wlcData,wlcName=WLC9800 "\
            f"connectedClients={wlc_data['all-clients']},"\
            f"authClients={wlc_data['client-states']['auth']},"\
            f"ipLearnClients={wlc_data['client-states']['iplearn']},"\
            f"webAuthClients={wlc_data['client-states']['webauth']},"\
            f"mobilityClients={wlc_data['client-states']['mobility']},"\
            f"deleteClients={wlc_data['client-states']['delete']},"\
            f"runClients={wlc_data['client-states']['run']},"\
            f"randomMacClients={wlc_data['client-states']['random-mac']} "
        )
    except KeyError:
        log.warning("Data error sending to Influx (Client states)")

    phy_list = [
        "Wi-Fi_6_(6GHz)",
        "Wi-Fi_6_(5GHz)",
        "Wi-Fi_6_(2.4GHz)",
        "Wi-Fi_5",
        "Wi-Fi_4_(5GHz)",
        "Wi-Fi_4_(2.4GHz)",
        "Wi-Fi_3",
        "Wi-Fi_2",
        "Wi-Fi_1"
    ]
    line_protocol = f"wlcData,wlcName=WLC9800 "
    for phy in phy_list:
        try:
            line_protocol += f"{phy}={wlc_data['per-phy'][phy]},"
        except KeyError:
            line_protocol += f"{phy}=0,"
    line_protocol = line_protocol.rstrip(",") + " "
    commsLib.send_to_influx(env, line_protocol)


def send_to_influx_ap(env, ap_data):

    all_rf_data_2ghz = ""
    all_rf_data_5ghz = ""
    all_rf_data_6ghz = ""
    count_rf_data_24, count_rf_data_5, count_rf_data_6 = 0, 0, 0
    for ap in ap_data.keys():
        for slot in range(0, ap_data[ap]["slot-count"]):
            slot = str(slot)
            try:
                if ap_data[ap][slot]["band"] == "dot11-2-dot-4-ghz-band":
                    rf_data_2ghz = (
                        #tags
                        f"rf2ghz,"\
                        f"apName={ap_data[ap]['ap_name']},"\
                        f"radioMode={ap_data[ap][slot]['mode']},"\
                        f"radioSlot={slot},"\
                        f"radioState={ap_data[ap][slot]['state']},"\
                        f"rfTag={ap_data[ap]['rf-tag']},"\
                        f"siteTag={ap_data[ap]['site-tag']} "\
                        #fields
                        f"radioStas={ap_data[ap][slot]['stations']},"\
                        f"radioUtil={ap_data[ap][slot]['ch_util']},"\
                        f"radioChanges={ap_data[ap][slot]['ch_changes']} "\
                        #timestamp
                        #f" {str(time.time()).replace('.', '')}"
                        f"\n"
                    )
                    all_rf_data_2ghz += rf_data_2ghz
                    count_rf_data_24 += 1

                elif ap_data[ap][slot]["band"] == "dot11-5-ghz-band":
                    rf_data_5ghz = (
                        #tags
                        f"rf5ghz,"\
                        f"apName={ap_data[ap]['ap_name']},"\
                        f"radioMode={ap_data[ap][slot]['mode']},"\
                        f"radioSlot={slot},"\
                        f"radioState={ap_data[ap][slot]['state']},"\
                        f"rfTag={ap_data[ap]['rf-tag']},"\
                        f"siteTag={ap_data[ap]['site-tag']} "\
                        #fields
                        f"radioStas={ap_data[ap][slot]['stations']},"\
                        f"radioUtil={ap_data[ap][slot]['ch_util']},"\
                        f"radioChanges={ap_data[ap][slot]['ch_changes']} "\
                        #timestamp
                        #f" {str(time.time()).replace('.', '')}"
                        f"\n"
                    )
                    all_rf_data_5ghz += rf_data_5ghz
                    count_rf_data_5 += 1

                elif ap_data[ap][slot]["band"] == "dot11-6-ghz-band":
                    rf_data_6ghz = (
                        #tags
                        f"rf6ghz,"\
                        f"apName={ap_data[ap]['ap_name']},"\
                        f"radioMode={ap_data[ap][slot]['mode']},"\
                        f"radioSlot={slot},"\
                        f"radioState={ap_data[ap][slot]['state']},"\
                        f"rfTag={ap_data[ap]['rf-tag']},"\
                        f"siteTag={ap_data[ap]['site-tag']} "\
                        #fields
                        f"radioStas={ap_data[ap][slot]['stations']},"\
                        f"radioUtil={ap_data[ap][slot]['ch_util']},"\
                        f"radioChanges={ap_data[ap][slot]['ch_changes']} "\
                        #timestamp
                        #f" {str(time.time()).replace('.', '')}"
                        f"\n"
                    )
                    all_rf_data_6ghz += rf_data_6ghz
                    count_rf_data_6 += 1

            except KeyError:
                continue
            
    commsLib.send_to_influx(env, all_rf_data_2ghz)
    commsLib.send_to_influx(env, all_rf_data_5ghz)
    commsLib.send_to_influx(env, all_rf_data_6ghz)

    log.info(f"2.4GHz slots: {count_rf_data_24}, 5GHz slots: {count_rf_data_5}, 6GHz slots: {count_rf_data_6}")

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(ap_data, f, indent=4) #Save JSON containing last data sent to Influx

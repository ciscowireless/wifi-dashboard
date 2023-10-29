import sys
import logging

log = logging.getLogger("wifininja.envLib")


def read_config_file(config_file="../config.ini"):

    config_data = {}
    try:
        with open(config_file, 'r') as cf:
            for line in cf.readlines():
                if line[0] in ("#", "\n", " "):
                    continue
                else:
                    try:
                        config = line.split("=")
                        config_data[config[0]] = config[1].rstrip("\n")
                    except IndexError:
                        log.critical(f"Error parsing config file")
                        sys.exit()
                        
    except FileNotFoundError:
        log.critical(f"Error opening config file")
        sys.exit()

    return config_data

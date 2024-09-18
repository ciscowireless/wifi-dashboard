import logging
import time
import re

from datetime import datetime


log = logging.getLogger("wifininja.database")


class MySql():


    def __init__(self, init):

        self.iosxe_user = init.iosxe_user
        self.iosxe_pass = init.iosxe_pass


    def put_wireless_client_global_oper(self, netconf_data):

        print(netconf_data.wireless_client_global_oper)
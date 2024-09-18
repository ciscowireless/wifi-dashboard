import logging
import time
import re

from datetime import datetime


log = logging.getLogger("wifininja.database")


class Influx():


    def __init__(self, init):

        self.iosxe_user = init.iosxe_user
        self.iosxe_pass = init.iosxe_pass
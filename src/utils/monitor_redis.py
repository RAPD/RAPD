"""
Monitor script for redis.

Idea from http://stackoverflow.com/questions/10458146/how-can-i-mimic-the-redis-monitor-command-in-a-python-script-using-redis-py
"""

"""
This file is part of RAPD

Copyright (C) 2017, Cornell University
All rights reserved.

RAPD is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3.

RAPD is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__created__ = "2017-02-14"
_maintainer__ = "Your name"
__email__ = "Your email"
__status__ = "Development"

# Standard imports
import argparse
# import datetime
# import glob
# import json
# import logging
# import multiprocessing
# import os
# import pprint
# import pymongo
# import re
import redis
# import shutil
# import subprocess
# import sys
# import time
# import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils

class Monitor():
    """Run monitor on a redis instance"""
    def __init__(self, connection_pool):
        self.connection_pool = connection_pool
        self.connection = None

    def __del__(self):
        try:
            self.reset()
        except:
            pass

    def reset(self):
        if self.connection:
            self.connection_pool.release(self.connection)
            self.connection = None

    def monitor(self):
        if self.connection is None:
            self.connection = self.connection_pool.get_connection("monitor", None)
        self.connection.send_command("monitor")
        return self.listen()

    def parse_response(self):
        return self.connection.read_response()

    def listen(self):
        while True:
            yield self.parse_response()

def main(args):
    """
    Coordinate monitoring from the commandline
    """

    pool = redis.ConnectionPool(host=args.host, port=args.port, db=args.db)
    monitor = Monitor(pool)
    commands = monitor.monitor()

    for c in commands:
        if args.ignore:
            if not "\" \"OW:" in c:
                print c
        else:
            print c

def get_commandline():
    """
    Grabs the commandline
    """

    # Parse the commandline arguments
    commandline_description = "Monitor redis instrance activity"
    parser = argparse.ArgumentParser(description=commandline_description)

    # Ignore overwatch traffic
    parser.add_argument("-i", "--ignore",
                        action="store_true",
                        dest="ignore",
                        help="Ignore overwatch ")

    # Host
    parser.add_argument("-o", "--host",
                        action="store",
                        dest="host",
                        default="localhost",
                        help="Host of redis to be monitored")

    # Port
    parser.add_argument("-p", "--port",
                        action="store",
                        dest="port",
                        default=6379,
                        type=int,
                        help="Port of redis to be monitored")

    # Database
    parser.add_argument("-d", "--db",
                        action="store",
                        dest="db",
                        default=0,
                        type=int,
                        help="DB to be monitored")

    return parser.parse_args()

if __name__ == "__main__":

    commandline_args = get_commandline()

    main(args=commandline_args)

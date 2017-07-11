"""
Simple echo RAPD launcher adapter

For use in testing setup
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

__created__ = "2017-07-11"
__maintainer__ = "Your name"
__email__ = "Your email"
__status__ = "Development"

# Standard imports
# import argparse
# import from collections import OrderedDict
# import datetime
# import glob
import json
import logging
# import multiprocessing
# import os
from pprint import pprint
# import pymongo
# import re
import redis
# import shutil
# import subprocess
# import sys
# import time
# import unittest
# import urllib2
# import uuid
# from distutils.spawn import find_executable

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
# import utils.credits as credits
from utils import exceptions
import utils.launch_tools as launch_tools

class LauncherAdapter(object):
    """
    RAPD adapter for launcher process

    Doesn't launch the job, but merely echoes it back
    """

    redis = None

    def __init__(self, site, message, settings):
        """
        Initialize the plugin

        Keyword arguments
        site -- imported site definition module
        message -- command from the control process, encoded as JSON
        settings --
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.debug("__init__")

        # Store passed-in variables
        self.site = site
        self.message = message
        self.settings = settings

        print "site"
        pprint(site)
        print "message"
        pprint(message)
        print "settings"
        pprint(settings)

        self.run()

    def run(self):
        """Orchestrate the adapter's actions"""

        self.preprocess()
        self.process()
        self.postprocess()

    def preprocess(self):
        """Adjust the command passed in in install-specific ways"""

        # Connect to redis
        pool = redis.ConnectionPool(host=self.site.CONTROL_REDIS_HOST,
                                    port=self.site.CONTROL_REDIS_PORT,
                                    db=self.site.CONTROL_REDIS_DB)

        self.redis = redis.Redis(connection_pool=pool)

    def process(self):
        """The main action of the adapter"""

        # Set status on message to done
        self.message["process"]["status"] = 100

    def postprocess(self):
        """Clean up after adapter functions"""

        # Encode in JSON
        json_message = json.dumps(self.message)

        # Pass back result
        self.redis.publish("RAPD_RESULTS", json_message)
        self.redis.lpush("RAPD_RESULTS", json_message)

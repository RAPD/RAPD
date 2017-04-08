"""analysis RAPD plugin"""

"""
This file is part of RAPD

Copyright (C) 2011-2017, Cornell University
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

__created__ = "2011-02-02"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Development"

# This is an active RAPD plugin
RAPD_PLUGIN = True

# This plugin's type
PLUGIN_TYPE = "ANALYSIS"
PLUGIN_SUBTYPE = "EXPERIMENTAL"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "f06818cf1b0f11e79232ac87a3333966"
VERSION = "1.0.0"

# Standard imports
# import argparse
# import from collections import OrderedDict
# import datetime
import glob
import json
import logging
import multiprocessing
import os
from pprint import pprint
# import pymongo
# import re
# import redis
import shutil
import subprocess
import sys
import time
# import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
import utils.xutils as xutils
import info

# Software dependencies
VERSIONS = {
    "gnuplot": (
        "gnuplot 4.2",
        "gnuplot 5.0",
    )
}

class RapdPlugin(multiprocessing.Process):
    """
    RAPD plugin class

    Command format:
    {
       "command":"analysis",
       "directories":
           {
               "work": ""                          # Where to perform the work
           },
       "site_parameters": {}                       # Site data
       "preferences": {}                           # Settings for calculations
       "return_address":("127.0.0.1", 50000)       # Location of control process
    }
    """

    input_sg = None
    cell = None
    cell2 = None
    sample_type = "protein"
    solvent_content = 0.55
    stats_timer = 180
    test = True
    volume = None

    def __init__(self, command, tprint=False, logger=False):
        """Initialize the plugin"""

        # Keep track of start time
        self.start_time = time.time()

        # If the logging instance is passed in...
        if logger:
            self.logger = logger
        else:
            # Otherwise get the logger Instance
            self.logger = logging.getLogger("RAPDLogger")
            self.logger.debug("__init__")

        # Store tprint for use throughout
        if tprint:
            self.tprint = tprint
        # Dead end if no tprint passed
        else:
            def func(arg=False, level=False, verbosity=False, color=False):
                pass
            self.tprint = func

        # Some logging
        self.logger.info(command)
        pprint(command)

        # Store passed-in variables
        self.command = command

        # Start up processing
        multiprocessing.Process.__init__(self, name="analysis")
        self.start()

    def run(self):
        """Execution path of the plugin"""

        self.preprocess()
        sys.exit()
        self.process()
        self.postprocess()

    def preprocess(self):
        """Set up for plugin action"""

        self.tprint("preprocess")
        self.logger.debug("preprocess")

        # Handle sample type from commandline
        if not self.command["preferences"]["sample_type"] == "default":
            self.sample_type = self.command["preferences"]["sample_type"]

        # Make the work_dir if it does not exist.
        if os.path.exists(self.command["directories"]["work"]) == False:
            os.makedirs(self.command["directories"]["work"])

        # Change directory to the one specified in the incoming dict
        os.chdir(self.command["directories"]["work"])

        # Get information from the data file
        self.input_sg, self.cell, self.volume = \
            xutils.get_mtz_info(
                datafile=self.command["input_data"]["datafile"])

        self.tprint("  Spacegroup: %s" % self.input_sg, level=20)
        self.tprint("  Cell: %s" % str(self.cell), level=20)
        self.tprint("  Volume: %f" % self.volume, level=20)

        # Handle ribosome sample types
        if (self.command["preferences"]["sample_type"] != "default" and \
            self.volume > 25000000.0) or \
            self.command["preferences"]["sample_type"] == "ribosome": #For 30S
            self.sample_type = "ribosome"
            self.solvent_content = 0.64
            self.stats_timer = 300

        sys.exit()
        if self.test:
            self.logger.debug("TEST IS SET \"ON\"")

    def process(self):
        """Run plugin action"""

        self.tprint("process")

    def postprocess(self):
        """Clean up after plugin action"""

        self.tprint("postprocess")

        # Print out recognition of the program being used
        self.print_info()

def get_commandline():
    """Grabs the commandline"""

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Test analysis plugin"
    my_parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    my_parser.add_argument("-q", "--quiet",
                           action="store_false",
                           dest="verbose",
                           help="Reduce output")

    args = my_parser.parse_args()

    # Insert logic to check or modify args here

    return args

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    if args.verbose:
        verbosity = 2
    else:
        verbosity = 1

    unittest.main(verbosity=verbosity)

    if __name__ == "__main__":

        commandline_args = get_commandline()

        main(args=commandline_args)

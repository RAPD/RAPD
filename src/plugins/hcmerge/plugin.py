"""Hierarchical clustering and merging of data for RAPD plugin"""

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

__created__ = "2012-08-09"
__maintainer__ = "Kay Perry"
__email__ = "kperry@anl.gov"
__status__ = "Development"

# This is an active RAPD plugin
RAPD_PLUGIN = True

# This plugin's type
PLUGIN_TYPE = "HCMERGE"
PLUGIN_SUBTYPE = "EXPERIMENTAL"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "4cba470534f911e7bd89985aeb8c1e24"
VERSION = "1.0.0"

# Standard imports
# import argparse
import from collections import OrderedDict
# import datetime
import glob
import json
import logging, logging.handlers
import multiprocessing
import os
# import pprint
# import pymongo
# import re
# import redis
import shutil
import subprocess
import sys
import time
# import unittest
# import urllib2
import uuid

from multiprocessing import Process, cpu_count
import matplotlib
# Force matplotlib to not use any Xwindows backend.  Must be called before any other matplotlib/pylab import.
matplotlib.use('Agg')
import hashlib
from itertools import combinations
from iotbx import reflection_file_reader
from cctbx import miller
from cctbx.array_family import flex
from cctbx.sgtbx import space_group_symbols
from hcluster import linkage,dendrogram

import cPickle as pickle # For storing dicts as pickle files for later use

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
# import utils.credits as credits
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
       "command":"hcmerge",
       "directories":
           {
               "work": ""                          # Where to perform the work
           },
       "site_parameters": {}                       # Site data
       "preferences": {}                           # Settings for calculations
       "return_address":("127.0.0.1", 50000)       # Location of control process
    }
    """

    results = {}

    def __init__(self, command, tprint=False, logger=False):
        """Initialize the plugin"""

        # If the logging instance is passed in...
        if logger:
            self.logger = logger
        else:
            # Otherwise get the logger Instance
            self.logger = logging.getLogger("RAPDLogger")
            self.logger.debug("__init__")

        # Keep track of start time
        self.start_time = time.time()
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

        # Store passed-in variables
        self.command = command
        multiprocessing.Process.__init__(self, name="hcmerge")
        self.start()

    def run(self):
        """Execution path of the plugin"""

        self.preprocess()
        self.process()
        self.postprocess()
        self.print_credits()

    def preprocess(self):
        """Set up for plugin action"""

        self.tprint("preprocess")

    def process(self):
        """Run plugin action"""

        self.tprint("process")

    def postprocess(self):
        """Events after plugin action"""

        self.tprint("postprocess")

        # Clean up mess
        self.clean_up()

        # Send back results
        self.handle_return()

    def clean_up(self):
        """Clean up after plugin action"""

        self.tprint("clean_up")

    def handle_return(self):
        """Output data to consumer - still under construction"""

        self.tprint("handle_return")

        run_mode = self.command["preferences"]["run_mode"]

        # Print results to the terminal
        if run_mode == "interactive":
            self.print_results()
        # Prints JSON of results to the terminal
        elif run_mode == "json":
            self.print_json()
        # Traditional mode as at the beamline
        elif run_mode == "server":
            pass
        # Run and return results to launcher
        elif run_mode == "subprocess":
            return self.results
        # A subprocess with terminal printing
        elif run_mode == "subprocess-interactive":
            self.print_results()
            return self.results

    def print_credits(self):
        """Print credits for programs utilized by this plugin"""

        self.tprint("print_credits")

        self.tprint(credits.HEADER, level=99, color="blue")

        programs = ["CCTBX"]
        info_string = credits.get_credits_text(programs, "    ")
        self.tprint(info_string, level=99, color="white")

def get_commandline():
    """Grabs the commandline"""

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Test hcmerge plugin"
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

        main()

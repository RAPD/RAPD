"""pdbquery RAPD plugin"""

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

__created__ = "2017-04-20"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# This is an active RAPD plugin
RAPD_PLUGIN = True

# This plugin's type
PLUGIN_TYPE = "PDBQUERY"
PLUGIN_SUBTYPE = "EXPERIMENTAL"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "9a2e422625e811e79866ac87a3333966"
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
# import pprint
# import pymongo
# import re
# import redis
import shutil
import subprocess
import sys
import time
# import unittest
import uuid

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
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
       "command":"pdbquery",
       "directories":
           {
               "work": ""                          # Where to perform the work
           },
       "site_parameters": {}                       # Site data
       "preferences": {}                           # Settings for calculations
       "return_address":("127.0.0.1", 50000)       # Location of control process
    }
    """

    # Settings
    # Place that structure files may be stored
    cif_cache = "/tmp/rapd_cache/cif_files"
    # Calc ADF for each solution (creates a lot of big map files).
    adf = False
    percent = 0.01
    # Run rigid-body refinement after MR.
    rigid = False
    # Search for common contaminants.
    search_common = True

    sample_type = "protein"
    solvent_content = 0

    # Parameters
    cell = None
    cell_output = False
    cell_summary = False
    est_res_number = 0
    tooltips = False
    pdb_summary = False

    large_cell = False
    input_sg = False
    input_sg_num = 0
    laue = False
    dres = 0.0
    common = False
    volume = 0
    phaser_results = {}
    jobs = {}
    pids = {}
    pdbquery_timer = 30

    phaser_timer = 2000 #was 600 but too short for mackinnon (144,144,288,90,90,90)

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

        # Params
        self.working_dir = self.command["directories"].get("work", os.getcwd())
        self.test = self.command["preferences"].get("test", False)
        self.sample_type = self.command["preferences"].get("type", "protein")
        self.solvent_content = self.command["preferences"].get("solvent_content", 0.55)
        self.cluster_use = self.command["preferences"].get("cluster", False)
        self.clean = self.command["preferences"].get("clean", True)
        self.gui = self.command["preferences"].get("gui", True)
        self.verbose = self.command["preferences"].get("verbose", False)
        self.datafile = xutils.convert_unicode(self.command["input_data"].get("datafile"))

        multiprocessing.Process.__init__(self, name="pdbquery")
        self.start()

    def run(self):
        """Execution path of the plugin"""

        self.preprocess()
        self.process()
        self.postprocess()

    def preprocess(self):
        """Set up for plugin action"""

        self.tprint("preprocess")

    def process(self):
        """Run plugin action"""

        self.tprint("process")

    def postprocess(self):
        """Clean up after plugin action"""

        self.tprint("postprocess")

def get_commandline():
    """Grabs the commandline"""

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Test pdbquery plugin"
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

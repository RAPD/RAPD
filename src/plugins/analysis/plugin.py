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
from multiprocessing import Process, Queue
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
import utils.modules as modules
import utils.xutils as xutils
import info
# from subcontractors.pdb_query import PDBQuery
import plugins.pdbquery.commandline


# Software dependencies
VERSIONS = {
    "gnuplot": (
        "gnuplot 4.2",
        "gnuplot 5.0",
    )
}

class RapdPlugin(Process):
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
    cell_output = Queue()
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
        Process.__init__(self, name="analysis")
        self.start()

    def run(self):
        """Execution path of the plugin"""

        self.preprocess()
        self.process()
        sys.exit()
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

        self.tprint("  Spacegroup: %s" % self.input_sg, level=20, color="white")
        self.tprint("  Cell: %s" % str(self.cell), level=20, color="white")
        self.tprint("  Volume: %f" % self.volume, level=20, color="white")

        # Handle ribosome sample types
        if (self.command["preferences"]["sample_type"] != "default" and \
            self.volume > 25000000.0) or \
            self.command["preferences"]["sample_type"] == "ribosome": #For 30S
            self.sample_type = "ribosome"
            self.solvent_content = 0.64
            self.stats_timer = 300

        self.tprint("  Sample type: %s" % self.sample_type, level=20, color="white")
        self.tprint("  Solvent content: %s" % self.solvent_content, level=20, color="white")

        # Get some data back into the command
        self.command["preferences"]["sample_type"] = self.sample_type
        self.command["preferences"]["solvent_content"] = self.solvent_content

        if self.test:
            self.logger.debug("TEST IS SET \"ON\"")

    def process(self):
        """Run plugin action"""

        self.tprint("process")

        self.process_pdb_query()

    def postprocess(self):
        """Clean up after plugin action"""

        self.tprint("postprocess")

        # Print out recognition of the program being used
        self.print_info()

    def process_pdb_query(self):
        """Prepare and run PDBQuery"""
        self.logger.debug("process_pdb_query")

        # Construct the pdbquery plugin command
        class pdbquery_args(object):
            clean = True
            contaminants = True
            datafile = self.command["input_data"]["datafile"]
            json = False
            no_color = False
            nproc = 1
            pdbs = False
            run_mode = "subprocess"
            search = True
            test = False
            verbose = True

        pdbquery_command = plugins.pdbquery.commandline.construct_command(pdbquery_args)

        print pdbquery_command

        # Load the plugin
        plugin = modules.load_module(seek_module="plugin",
                                     directories=["plugins.pdbquery"],
                                     logger=self.logger)

        # Print out plugin info
        self.tprint(arg="\nPlugin information", level=10, color="blue")
        self.tprint(arg="  Plugin type:    %s" % plugin.PLUGIN_TYPE, level=10, color="white")
        self.tprint(arg="  Plugin subtype: %s" % plugin.PLUGIN_SUBTYPE, level=10, color="white")
        self.tprint(arg="  Plugin version: %s" % plugin.VERSION, level=10, color="white")
        self.tprint(arg="  Plugin id:      %s" % plugin.ID, level=10, color="white")

        # Run the plugin
        pdbquery_result = plugin.RapdPlugin(pdbquery_command,
                                            self.tprint,
                                            self.logger)

        sys.exit()

        # Move some information
        # self.command["preferences"]["sample_type"] = self.sample_type
        #
        # Process(target=PDBQuery, args=(self.command,
        #                                self.cell_output,
        #                                self.tprint,
        #                                self.logger)).start()

        # except:
        #     self.logger.exception("**Error in AutoStats.process_pdb_query**")

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

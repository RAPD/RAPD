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
from pprint import pprint
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
import utils.xutils as xutils
import info

# NE-CAT REST PDB server
PDBQ_SERVER = "remote.nec.aps.anl.gov:3030"

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
                """Dummy function"""
                pass
            self.tprint = func

        # Some logging
        self.logger.info(command)

        # Store passed-in variables
        self.command = command

        pprint(command)

        # Params
        self.working_dir = self.command["directories"].get("work", os.getcwd())
        self.test = self.command["preferences"].get("test", False)
        self.sample_type = self.command["preferences"].get("type", "protein")
        self.solvent_content = self.command["preferences"].get("solvent_content", 0.55)
        self.cluster_use = self.command["preferences"].get("cluster", False)
        self.clean = self.command["preferences"].get("clean", True)
        # self.gui = self.command["preferences"].get("gui", True)
        # self.verbose = self.command["preferences"].get("verbose", False)
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

        # Check the local pdb cache Location
        if self.cif_cache:
            if not os.path.exists(self.cif_cache):
                os.makedirs(self.cif_cache)

        # Glean some information on the input file
        self.input_sg, self.cell, self.volume = xutils.get_mtz_info(self.datafile)
        self.dres = xutils.get_res(self.datafile)
        self.input_sg_num = int(xutils.convert_spacegroup(self.input_sg))
        self.laue = xutils.get_sub_groups(self.input_sg_num, "simple")

        # Throw some information into the terminal
        self.tprint("\nDataset information", color="blue", level=10)
        self.tprint("  Data file: %s" % self.datafile, level=10, color="white")
        self.tprint("  Spacegroup: %s  (%d)" % (self.input_sg, self.input_sg_num),
                    level=10,
                    color="white")
        self.tprint("  Cell: %f %f %f %f %f %f" % tuple(self.cell), level=10, color="white")
        self.tprint("  Volume: %f" % self.volume, level=10, color="white")
        self.tprint("  Resolution: %f" % self.dres, level=10, color="white")
        self.tprint("  Subgroups: %s" % self.laue, level=10, color="white")

        # Set by number of residues in AU. Ribosome (70s) is 24k.
        self.est_res_number = xutils.calc_res_number(self.input_sg,
                                                     se=False,
                                                     volume=self.volume,
                                                     sample_type=self.sample_type,
                                                     solvent_content=self.solvent_content)
        if self.est_res_number > 5000:
            self.large_cell = True
            self.phaser_timer = 3000

    def process(self):
        """Run plugin action"""

        self.tprint("process")

        self.query_pdbq()
        # self.add_common_pdb()
        # phaser_results_raw = self.process_phaser()
        # self.postprocess_phaser(phaser_results_raw)
        # pprint(self.phaser_results)

    def query_pdbq(self):
        """
        Check if cell is found in PDBQ

        Places relevant pdbs into self.cell_output
        """

        self.logger.debug("query_pdbq")
        self.tprint("Searching for similar unit cells in the PDB", level=10, color="blue")

        def connect_pdbq(inp):
            """Function to query the PDBQ server"""

            _d0_ = inp
            l1 = ["a", "b", "c", "alpha", "beta", "gamma"]
            for y in range(end):
                _d_ = {}
                for x in range(len(l1)):
                    _d_[l1[x]] = [self.cell[l2[y][x]] - self.cell[l2[y][x]] * self.percent/2,
                                  self.cell[l2[y][x]] + self.cell[l2[y][x]] *self.percent/2]
                # Query server
                response = urllib2.urlopen(urllib2.Request("http://%s/pdb/rest/search/" % \
                           PDBQ_SERVER, data=json.dumps(_d_))).read()
                j = json.loads(response)
                for k in j.keys():
                    j[k]["Name"] = j[k].pop("struct.pdbx_descriptor")
                _d0_.update(j)
            return _d0_

        def limitOut(inp):
            """Filter repeates out of query"""
            l = inp.keys()[:i+1]
            for p in inp.keys():
                if l.count(p) == 0:
                    del inp[p]
            return inp

        permute = False
        end = 1
        l2 = [(0, 1, 2, 3, 4, 5), (1, 2, 0, 4, 5, 3), (2, 0, 1, 5, 3, 4)]

        # Check for orthorhombic
        if self.laue == "16":
            permute = True

        # Check monoclinic when Beta is near 90.
        if self.laue in ("3", "5"):
            if 89.0 < self.cell[4] < 91.0:
                permute = True

        if permute:
            end = len(l2)

        # Limit the minimum number of results
        no_limit = False
        if self.cluster_use:
            if self.large_cell:
                i = 10
            elif permute:
                i = 60
            else:
                no_limit = True
                i = 40
        else:
            i = 8
        counter = 0

        # Limit the unit cell difference to 25%. Also stops it if errors are received.
        pdbq_results = {}
        while counter < 25:
            self.tprint("  Querying server at %s" % PDBQ_SERVER,
                        level=20,
                        color="white")

            # Connect to and query the PDBQ server
            pdbq_results = connect_pdbq(pdbq_results)

            # Handle results
            if pdbq_results:
                for line in pdbq_results.keys():
                    # remove anything bigger than 4 letters
                    if len(line) > 4:
                        del pdbq_results[line]

                # Do not limit number of results if many models come out really close in cell
                # dimensions.
                if counter in (0, 1):
                    #Limit output
                    if no_limit == False:
                        pdbq_results = limitOut(pdbq_results)
                else:
                    pdbq_results = limitOut(pdbq_results)

            # Not enough results
            if len(pdbq_results.keys()) < i:
                counter += 1
                self.percent += 0.01
                self.logger.debug("Not enough PDB results. Going for more...")
            else:
                break

        # There will be results!
        if pdbq_results:
            self.cell_output = pdbq_results
            self.tprint("  %d relevant PDB files found on the PDBQ server" % len(pdbq_results.keys()),
                        level=50,
                        color="white")
        else:
            self.cell_output = {}
            self.logger.debug("Failed to find pdb with similar cell.")
            self.tprint("No relevant PDB files found on the PDBQ server",
                        level=50,
                        color="red")


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

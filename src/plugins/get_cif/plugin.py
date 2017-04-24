"""get_cif RAPD plugin"""

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

__created__ = "2017-04-24"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# This is an active RAPD plugin
RAPD_PLUGIN = True

# This plugin's type
PLUGIN_TYPE = "GET_CIF"
PLUGIN_SUBTYPE = "EXPERIMENTAL"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "e5b33482291111e780c3ac87a3333966"
VERSION = "1.0.0"

# Standard imports
import argparse
# import from collections import OrderedDict
# import datetime
# import glob
import json
import logging
import multiprocessing
import os
# import pprint
# import pymongo
# import re
# import redis
import shutil
import subprocess32
# import sys
import time
# import unittest
import urllib2
# import uuid

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
import utils.credits as rcredits
import utils.globals as rglobals
# import info

# Cache of CIF files
CIF_CACHE = rglobals.CIF_CACHE

# NE-CAT REST PDB server
PDBQ_SERVER = rglobals.PDBQ_SERVER

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
    """

    pdbq_entries = {}
    pdbs_to_download = []

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
        # self.reply_address = self.command["return_address"]
        multiprocessing.Process.__init__(self, name="get_cif")
        self.start()

    def run(self):
        """Execution path of the plugin"""

        self.preprocess()
        self.process()
        self.postprocess()
        self.print_credits()

    def preprocess(self):
        """Set up for plugin action"""

        # self.tprint("preprocess")

        # Check for existence of pdb codes in the PDBQ database
        self.check_in_pdbq()

        # Check to make sure we are not going to overwrite any files in the local directory
        self.check_path()

    def process(self):
        """Run plugin action"""

        # self.tprint("process")

        self.get_cif_files()

    def postprocess(self):
        """Clean up after plugin action"""

        # self.tprint("postprocess")

    def check_in_pdbq(self):
        """Check if input PDB codes are in the PDBQ database"""

        self.tprint("\nChecking that requested codes are in the PDBQ database",
                    level=30,
                    color="blue")

        for pdb_code in self.command["input_data"]["pdb_codes"]:

            # Query pdbq server
            response = urllib2.urlopen(urllib2.Request("http://%s/entry/%s" % \
                       (PDBQ_SERVER, pdb_code))).read()

            # Decode search result
            entry = json.loads(response)

            # No entry
            if entry["message"] == None:

                # Print info to console
                self.tprint("  %s not in PDBQ database" % pdb_code,
                            level=50,
                            color="red")

            # Have an entry in PDBQ
            else:

                # Save the entry
                self.pdbq_entries[pdb_code] = entry["message"]

                # Put code on the good list
                self.pdbs_to_download.append(pdb_code)

                # Grab the description
                description = entry["message"]["_entity-pdbx_description"][0]

                # Print info to console
                self.tprint("  %s - %s" % (pdb_code, description),
                            level=10,
                            color="white")

    def check_path(self):
        """Make sure that the file does not exist already"""

        for pdb_code in self.pdbs_to_download:

            if self.command["preferences"]["pdb"]:
                target_file = pdb_code.lower() + ".pdb"
            else:
                target_file = pdb_code.lower() + ".cif"

            if os.path.exists(target_file):
                if not self.command["preferences"]["force"]:
                    raise Exception("%s already exists. Erase or run with -f flag.")

    def get_cif_files(self):
        """Retrieve/check for/uncompress/convert structure file"""

        self.tprint("\nRetrieving files from PDBQ server",
                    level=30,
                    color="blue")

        for pdb_code in self.pdbs_to_download:

            # self.tprint("    %s" % pdb_code,
            #             level=30,
            #             color="white")

            # The cif file name
            cif_file = pdb_code.lower() + ".cif"
            # print "cif_file", cif_file
            gzip_file = cif_file+".gz"
            # print "gzip_file", gzip_file
            cached_file = False

            # There is a local cache
            if CIF_CACHE:
                cached_file = os.path.join(CIF_CACHE, gzip_file)
                # print "cached_file", cached_file

                # Using the cache and have cached version of the file
                if self.command["preferences"]["cached"] and os.path.exists(cached_file):
                    self.tprint("      Have cached cif file %s" % gzip_file,
                                level=10,
                                color="white")

                # DO NOT have cached version of file or not using the cached file
                else:
                    # Get the gzipped cif file from the PDBQ server
                    self.tprint("    Fetching %s" % cif_file, level=10, color="white")
                    try:
                        response = urllib2.urlopen(urllib2.Request(\
                                   "http://%s/pdbq/entry/get_cif/%s" % \
                                   (PDBQ_SERVER, cif_file.replace(".cif", "")))\
                                   , timeout=60).read()
                    except urllib2.HTTPError as http_error:
                        self.tprint("      %s when fetching %s" % (http_error, cif_file),
                                    level=50,
                                    color="red")
                        return False

                    # Write the  gzip file
                    with open(cached_file, "wb") as outfile:
                        outfile.write(response)

                # Copy the gzip file to the cwd
                shutil.copy(cached_file, os.path.join(os.getcwd(), gzip_file))

            # No local CIF file cache
            else:
                # Get the gzipped cif file from the PDBQ server
                self.tprint("      Fetching %s" % cif_file, level=10, color="white")
                try:
                    response = urllib2.urlopen(urllib2.Request(\
                               "http://%s/pdbq/entry/get_cif/%s" % \
                               (PDBQ_SERVER, cif_file.replace(".cif", ""))), \
                               timeout=60).read()
                except urllib2.HTTPError as http_error:
                    self.tprint("      %s when fetching %s" % (http_error, cif_file),
                                level=50,
                                color="red")
                    return False

                # Write the  gzip file
                with open(gzip_file, "wb") as outfile:
                    outfile.write(response)

            # Uncompress the gzipped file
            unzip_proc = subprocess32.Popen(["gunzip", gzip_file])
            unzip_proc.wait()

            # Convert from cif to pdb
            if self.command["preferences"]["pdb"]:
                # Convert
                conversion_proc = subprocess32.Popen(["phenix.cif_as_pdb", cif_file],
                                                     stdout=subprocess32.PIPE,
                                                     stderr=subprocess32.PIPE)
                conversion_proc.wait()
                # pdb_file = cif_file.replace(".cif", ".pdb")

                # Remove the CIF file
                os.unlink(cif_file)

    def print_credits(self):
        """Print credits for programs utilized by this plugin"""

        # self.tprint("print_credits")

        self.tprint(rcredits.HEADER, level=99, color="blue")

        programs = ["CCTBX"]
        info_string = rcredits.get_credits_text(programs, "    ")
        self.tprint(info_string, level=99, color="white")

def get_commandline():
    """Grabs the commandline"""

    # print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Retrieve CIF or PDB files from PDBQ server"
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

    if __name__ == "__main__":

        main()

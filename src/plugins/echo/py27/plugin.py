"""echo RAPD plugin"""

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
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# This is an active RAPD plugin
RAPD_PLUGIN = True

# This plugin's type
PLUGIN_TYPE = "ECHO"
PLUGIN_SUBTYPE = "EXPERIMENTAL"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "9c70d6ab667f11e79b75c82a1400d5bc"
VERSION = "1.0.0"

# Standard imports
# import argparse
# import from collections import OrderedDict
# import datetime
# import glob
import hashlib
import importlib
import logging
import multiprocessing
import os
from pprint import pprint
# import pymongo
# import re
# import redis
# import shutil
# import subprocess
# import sys
import tempfile
import time
# import unittest
# import urllib2
import uuid
# from distutils.spawn import find_executable

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
import utils.credits as rcredits
# import info
# from utils import exceptions
from utils.text import json
from bson.objectid import ObjectId

# Constants
DATA_REQUEST_TIMEOUT = 120

# Software dependencies
VERSIONS = {}

class RapdPlugin(multiprocessing.Process):
    """
    RAPD plugin class

    Command format:
    {
       "command":"echo",
       "directories":
           {
               "work": ""                          # Where to perform the work
           },
       "site_parameters": {}                       # Site data
       "preferences": {}                           # Settings for calculations
       "return_address":("127.0.0.1", 50000)       # Location of control process
    }
    """

    # Holders for passed-in info
    command = None
    preferences = None

    # Instance variables
    redis = None

    # Holders for results
    results = {}

    def __init__(self, site, command, tprint=False, logger=False):
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
            def func(*args, **kwargs):
                """Dummy function"""
                pass
            self.tprint = func

        # Some logging
        self.logger.info(command)

        # Store passed-in variables
        self.site = site
        self.command = command
        self.preferences = self.command.get("preferences", {})

        # Set up the results with command
        self.results["command"] = command

        # Update process with a starting status of 1
        if self.results.get("process"):
            self.results["process"]["status"] = 1

        # Create a process section of results with the id and a starting status of 1
        else:
            self.results["process"] = {
                "process_id": self.command.get("process_id"),
                "status": 1}

        multiprocessing.Process.__init__(self, name="echo")
        # self.start()

    def run(self):
        """Execution path of the plugin"""

        self.logger.debug("run")

        self.preprocess()
        self.process()
        self.postprocess()
        self.print_credits()

    def preprocess(self):
        """Set up for plugin action"""

        self.logger.debug("preprocess")

        self.tprint(arg=0, level="progress")
        self.tprint("preprocess")

        # Check for dependency problems
        self.check_dependencies()

        # Connect to redis
        if self.preferences.get("run_mode") == "server":
            self.connect_to_redis()

    def process(self):
        """Run plugin action"""

        self.logger.debug("process")

        self.tprint("process")

    def postprocess(self):
        """Events after plugin action"""

        self.logger.debug("postprocess")

        self.tprint("postprocess")

        self.tprint(arg=99, level="progress")

        # If command["site"] is there, make it a string representation, not a module
        if self.command.get("site"):
            self.results["command"]["site"] = self.command.get("site").SITE

        # Set status to done
        self.results["process"]["status"] = 100

        # Clean up mess
        self.clean_up()

        # Send back results
        self.handle_return()

    def check_dependencies(self):
        """Make sure dependencies are all available"""

        self.logger.debug("check_dependencies")

        # A couple examples from index plugin
        # Can avoid using best in the plugin b        # If no best, switch to mosflm for strategy
        # if self.strategy == "best":
        #     if not find_executable("best"):
        #         self.tprint("Executable for best is not present, using Mosflm for strategy",
        #                     level=30,
        #                     color="red")
        #         self.strategy = "mosflm"

        # If no gnuplot turn off printing
        # if self.preferences.get("show_plots", True) and (not self.preferences.get("json", False)):
        #     if not find_executable("gnuplot"):
        #         self.tprint("\nExecutable for gnuplot is not present, turning off plotting",
        #                     level=30,
        #                     color="red")
        #         self.preferences["show_plots"] = False

        # If no labelit.index, dead in the water
        # if not find_executable("labelit.index"):
        #     self.tprint("Executable for labelit.index is not present, exiting",
        #                 level=30,
        #                 color="red")
        #     self.results["process"]["status"] = -1
        #     self.results["error"] = "Executable for labelit.index is not present"
        #     self.write_json(self.results)
        #     raise exceptions.MissingExecutableException("labelit.index")

        # If no raddose, should be OK
        # if not find_executable("raddose"):
        #     self.tprint("\nExecutable for raddose is not present - will continue",
        #                 level=30,
        #                 color="red")

    def connect_to_redis_old(self):
        """Connect to the redis instance"""

        self.logger.debug("connect_to_redis_old")

        print "Connecting to Redis at %s" % self.command["site"].CONTROL_REDIS_HOST

        # Create a pool connection
        pool = redis.ConnectionPool(host=self.command["site"].CONTROL_REDIS_HOST,
                                    port=self.command["site"].CONTROL_REDIS_PORT,
                                    db=self.command["site"].CONTROL_REDIS_DB)

        # The connection
        self.redis = redis.Redis(connection_pool=pool)

    def connect_to_redis(self):
        """Connect to the redis instance"""

        self.logger.debug("connect_to_redis")

        redis_database = importlib.import_module('database.redis_adapter')
        self.redis = redis_database.Database(settings=self.command["site"].REQUEST_MONITOR_SETTINGS)


    def fetch_data(self, request_type="DATA_PRODUCED", result_id=False, description=False, request_hash=False, output_dir="./", output_file=False):
        """
        Fetch data for processing from control process. Need (result_id and description) or hash
        
        request_type - currently only DATA_PRODUCED is supported
        result_id - _id in the results collection, equal to process.result_id
        description - currently available: xdsascii_hkl, unmerged_mtz, rfree_mtz
        hash - can be used to get file
        """
        
        self.logger.debug("fetch_data")

        # Make sure we have enough to go on
        if not ((result_id and description) or request_hash):
            raise Exception("Unable to fetch data - need (result_id and description) or hash")

        # Form request
        request_id = str(uuid.uuid1())
        request = {
            "description": description,
            "hash": request_hash,
            "request_id": request_id,
            "request_type": request_type,
            "result_id": result_id,
        }
        
        # Push request into redis
        self.redis.lpush("RAPD2_REQUESTS", json.dumps(request))

        # Wait for reply
        counter = 0
        return_key = "RAPD2_DATA_REPLY_"+request_id
        while (counter) < DATA_REQUEST_TIMEOUT:
            counter += 1
            reply = self.redis.get(return_key)
            
            # Have a reply
            if reply:
                raw_metadata, raw_file = reply.split("://:")
                metadata = json.loads(raw_metadata)
                
                # Check for integrity
                my_hash = hashlib.sha1(raw_file).hexdigest()
                if metadata.get("hash") == my_hash:

                    # Write the file - data_produced files are NOT compressed
                    if output_dir:
                        if not os.path.exists(output_dir):
                            os.mkdir(output_dir)
                    if output_file:
                        if output_dir:
                            created_file = os.path.join(output_dir, output_file)
                        else:
                            created_file = output_file
                        fullpath_created_file = os.path.abspath(created_file)
                    elif output_dir:
                        __, fullpath_created_file = tempfile.mkstemp(suffix="."+metadata.get("description").split("_")[-1], dir=output_dir)
                    else:
                        __, fullpath_created_file = tempfile.mkstemp(suffix="."+metadata.get("description").split("_")[-1])

                    with open(fullpath_created_file, "w") as filehandle:
                        filehandle.write(raw_file)

                    return fullpath_created_file

                # Integrity is NOT confirmed
                else:
                    raise Exception("Data stream corrupted - hashes do not match")

            # Wait 1 second brefore re-querying    
            time.sleep(1)
        
        # Reply never comes
        else:
            return False

    def clean_up(self):
        """Clean up after plugin action"""

        self.logger.debug("clean_up")

        self.tprint("clean_up")

    def handle_return(self):
        """Output data to consumer - still under construction"""

        self.logger.debug("handle_return")

        self.tprint("handle_return")

        run_mode = self.preferences.get("run_mode")
        print "run_mode", run_mode

        # Print results to the terminal
        if run_mode == "interactive":
            self.print_results()

        # Traditional mode as at the beamline
        elif run_mode == "server":
            json_results = json.dumps(self.results)
            self.redis.lpush("RAPD_RESULTS", json_results)
            self.redis.publish("RAPD_RESULTS", json_results)

        # Run and return results to launcher
        elif run_mode == "subprocess":
            return self.results
        # A subprocess with terminal printing
        elif run_mode == "subprocess-interactive":
            self.print_results()
            return self.results

    def print_credits(self):
        """Print credits for programs utilized by this plugin"""

        self.logger.debug("print_credits")

        self.tprint("print_credits")

        self.tprint(rcredits.HEADER, level=99, color="blue")

        programs = ["CCTBX"]
        info_string = rcredits.get_credits_text(programs, "    ")
        self.tprint(info_string, level=99, color="white")

def get_commandline():
    """Grabs the commandline"""

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Test echo plugin"
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

def test_fetch():
    """Test fetch_data function"""

    print "Testing fetch_data plugin function"

    # Create an object to spoof site
    import types
    site = types.ModuleType('site', 'The site module')
    site.ID = "TEST"
    site.REQUEST_MONITOR_SETTINGS = {
        "REDIS_CONNECTION":     "direct",
        "REDIS_MASTER_NAME" :   None,
        "REDIS_HOST":           "127.0.0.1",
        "REDIS_PORT":           6379,
        "REDIS_DB":             0
    }
    # site.CONTROL_DATABASE = "mongodb"
    # site.CONTROL_DATABASE_SETTINGS = {"DATABASE_STRING": "mongodb://127.0.0.1:27017/rapd"}

    command = {"site":site}

    P = RapdPlugin(site=site, command=command)
    P.connect_to_redis()

    # Test no dir no filename
    filename = P.fetch_data(result_id="test", description="xdsascii_hkl")
    if filename:
        print "Successful fetch to file %s" % filename
    else:
        print "FAILURE"

    # Test no filename
    filename = P.fetch_data(result_id="test", description="xdsascii_hkl", output_dir="foo")
    if filename:
        print "Successful fetch to file %s" % filename
    else:
        print "FAILURE"

    print "Now we should get an error"
    filename = P.fetch_data(description="xdsascii_hkl", output_dir="foo")

    # Test no filename
    filename = P.fetch_data(result_id="test", description="xdsascii_hkl", output_dir="foo", output_file="bar.hkl")
    if filename:
        print "Successful fetch to file %s" % filename
    else:
        print "FAILURE"

if __name__ == "__main__":

    # main()

    test_fetch()

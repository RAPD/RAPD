"""This is a docstring for this file"""

"""
This file is part of RAPD

Copyright (C) 2018, Cornell University
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

__created__ = "2018-05-02"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
import from collections import OrderedDict
# import datetime
# import glob
import json
# import logging
# import math
# import multiprocessing
import os
# import pprint
# import pymongo
import re
# import redis
import shutil
# import subprocess
# import sys
import time
# import unittest
# import urllib2
import uuid

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
# import utils.credits as rcredits
from database.redis_adapter import Database
import utils.commandline
from utils.text import json

class Gatherer(object):
    """
    Watches the beamline and signals images and runs over redis
    """
    # For keeping track of file change times
    run_time = 0
    image_time = 0

    # Host computer detail
    ip_address = None

    def __init__(self, site, overwatch_id=None):
        """
        Setup and start the Gatherer
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")

        # Passed-in variables
        self.site = site
        self.overwatch_id = overwatch_id

        self.logger.info("Gatherer.__init__")

        # Get our bearings
        self.set_host()

        # Connect to redis
        self.connect()

        # Running conditions
        self.go = True

        # Now run
        self.run()

    def run(self):
        """
        The while loop for watching the files
        """
        self.logger.info("Gatherer.run")

        # Set up overwatcher
        self.ow_registrar = Registrar(site=self.site,
                                      ow_type="gatherer",
                                      ow_id=self.overwatch_id)
        self.ow_registrar.register({"site_id":self.site.ID})

        # A RUN ONLY EXAMPLE
        # Some logging
        self.logger.debug("  Will publish new datasets on run_data:%s" % self.tag)
        self.logger.debug("  Will push new datasets onto runs_data:%s" % self.tag)

        try:
            counter = 0
            while self.go:

                # NECAT uses a beamline Redis database to communicate
                #----------------------------------------------------

                # Check if the run info changed in beamline Redis DB.
                current_run_raw = self.redis_beamline.get("RUN_INFO_SV")

                # New run information
                if current_run_raw not in (None, ""):
                    # Blank out the Redis entry
                    self.redis_beamline.set("RUN_INFO_SV", "")
                    # Handle the run information
                    self.handle_run(run_raw=current_run_raw)

                # Have Registrar update status
                if counter % 5 == 0:
                    self.ow_registrar.update({"site_id":self.site.ID})
                    counter = 0
                else:
                    # Increment counter
                    counter += 1

                # Pause
                time.sleep(1)

        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """
        Stop the loop
        """
        self.logger.debug("Gatherer.stop")

        self.go = False
        self.redis_database.stop()
        self.bl_database.stop()

    def set_host(self):
        """
        Use os.uname to set files to watch
        """
        self.logger.debug("Gatherer.set_host")

        # Figure out which host we are on
        self.ip_address = socket.gethostbyaddr(socket.gethostname())[-1][0]
        self.logger.debug("IP Address:",self.ip_address)

        # Now grab the file locations, beamline from settings
        if self.site.GATHERERS.has_key(self.ip_address):
            self.tag = self.site.GATHERERS[self.ip_address]
            # Make sure we enforce uppercase for tag
            self.tag = self.tag.upper()
        else:
            print "ERROR - no settings for this host"
            self.tag = "test"

    def connect(self):
        """
        Connect to redis host
        """

        self.logger.debug("Gatherer.connect")

        # Connect to RAPD Redis
        self.redis_rapd = Database(settings=self.site.CONTROL_DATABASE_SETTINGS)

        # NECAT uses Redis to communicate with the beamline
        # Connect to beamline Redis to monitor if run is launched
        self.redis_beamline = Database(settings=self.site.SITE_ADAPTER_SETTINGS[self.tag])

        # NECAT uses Redis to communicate with the remote system
        # Connect to remote system Redis to monitor if run is launched
        self.redis_remote = Database(settings=self.site.REMOTE_ADAPTER_SETTINGS)

    def handle_run(self, run_raw):
        """
        Handle the raw run information
        """

        # Run information is encoded in JSON format
        # run_data = json.loads(current_run_raw)

        # Get extra run information and pack it up
        run_data = self.get_run_data(run_raw)

        # Determine if the run should be ignored
        if self.ignored(run_data["directory"]):
            self.logger.debug("Directory %s is marked to be ignored - skipping", run_data["directory"])
            return False

        # Put into exchangable format
        run_data_json = json.dumps(run_data)

        # RAPD
        self.redis_rapd.publish("run_data:%s" % self.tag, run_data_json)
        self.redis_rapd.lpush("runs_data:%s" % self.tag, run_data_json)

        # Remote
        self.redis_remote.hmset("current_run_C", run_data)
        self.redis_remote.publish("current_run_C", run_data_json)

    def ignored(self, dir):
        """
        Check if folder is supposed to be ignored
        """
        for d in self.site.IMAGE_IGNORE_DIRECTORIES:
            if dir.startswith(d):
                return True
        return False

    def get_run_data(self, run_info):
        """
        Put together info from run and pass it back
        """
        # Split it
        cur_run = run_info.split("_") #runnumber,first#,total#,dist,energy,transmission,omega_start,deltaomega,time,timestamp
        #1_1_23_400.00_12661.90_30.00_45.12_0.20_0.50_
        
        # Get some more information from beamline redis
        det_directory = self.redis_beamline.get("ADX_DIRECTORY_SV")
        run_prefix = self.redis_beamline.get("RUN_PREFIX_SV")
        
        # extend path with the '0_0' to path for Pilatus
        run_directory = os.path.join(det_directory, "0_0")

        # Standardize the run information
        run_data = {
            "anomalous":          None,
            "beamline":           self.tag,                                # Non-standard
            "directory":          run_directory,
            "distance":           float(cur_run[3]),
            "energy":             float(cur_run[4]),
            "image_prefix":       run_prefix,
            "kappa":              None,
            "number_images":      int(cur_run[2]),
            "omega":              None,
            "osc_axis":           "phi",
            "osc_start":          float(cur_run[6]),
            "osc_width":          float(cur_run[7]),
            "phi":                0.0,
            "run_number":         int(cur_run[0]),
            "site_tag":           self.tag,
            "start_image_number": int(cur_run[1]),
            "time":               float(cur_run[8]),
            "transmission":       float(cur_run[5]),
            "twotheta":           None
        }

        return run_data

def get_commandline():
    """
    Get the commandline variables and handle them
    """

    # Parse the commandline arguments
    commandline_description = "Data gatherer"
    parser = argparse.ArgumentParser(parents=[utils.commandline.base_parser],
                                     description=commandline_description) 

    return parser.parse_args()

def main(): 
    """ 
    The main process 
    Setup logging and instantiate the gatherer 
    """
 
    # Get the commandline args 
    commandline_args = get_commandline() 

    # Get the environmental variables 
    environmental_vars = utils.site.get_environmental_variables() 
    site = commandline_args.site 

    # If no commandline site, look to environmental args 
    if site == None: 
        if environmental_vars["RAPD_SITE"]: 
            site = environmental_vars["RAPD_SITE"] 

    # Determine the site 
    site_file = utils.site.determine_site(site_arg=site) 

    # Handle no site file 
    if site_file == False: 
        print text.error+"Could not determine a site file. Exiting."+text.stop
        sys.exit(9) 

    # Import the site settings 
    SITE = importlib.import_module(site_file) 

    # Single process lock? 
    utils.lock.file_lock(SITE.GATHERER_LOCK_FILE) 

    # Set up logging 
    if commandline_args.verbose: 
        log_level = 10 
    else: 
        log_level = SITE.LOG_LEVEL 
    logger = utils.log.get_logger(logfile_dir=SITE.LOGFILE_DIR, 
                                  logfile_id="rapd_gatherer", 
                                  level=log_level 
                                 ) 
    logger.debug("Commandline arguments:") 
    for pair in commandline_args._get_kwargs(): 
        logger.debug("  arg:%s  val:%s" % pair) 

    # Instantiate the Gatherer 
    GATHERER = Gatherer(site=SITE, 
                        overwatch_id=commandline_args.overwatch_id) 
if __name__ == "__main__":

    # Execute code
    main()

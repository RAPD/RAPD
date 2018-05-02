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
from database.redis_adapter import Database as RedisDB
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

                # Increment counter
                counter += 1

                # Pause
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

        # A RUN & IMAGES EXAMPLE
        # Some logging
        self.logger.debug("  Will publish new images on filecreate:%s" % self.tag)
        self.logger.debug("  Will push new images onto images_collected:%s" % self.tag)
        self.logger.debug("  Will publish new datasets on run_data:%s" % self.tag)
        self.logger.debug("  Will push new datasets onto runs_data:%s" % self.tag)

            while self.go:

                # 5 rounds of checking
                for ___ in range(5):
                    # An example of file-based signalling
                    # Check if the run info has changed on the disk
                    if self.check_for_run_info():
                        run_data = self.get_run_data()
                        if run_data:
                        # Handle the run information
                        self.handle_run(run_raw=current_run_raw)

                        # 20 image checks
                        for __ in range(20):
                            # Check if the image file has changed
                            if self.check_for_image_collected():
                                image_name = self.get_image_data()
                                if image_name:
                                    self.handle_image(image_name)
                                break
                            else:
                                time.sleep(0.05)
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
        self.redis_rapd = RedisDB(settings=self.site.CONTROL_DATABASE_SETTINGS)

        # NECAT uses Redis to communicate with the beamline
        # Connect to beamline Redis to monitor if run is launched
        # self.redis_beamline = RedisDB(settings=self.site.SITE_ADAPTER_SETTINGS[self.tag])

        # NECAT uses Redis to communicate with the remote system
        # Connect to remote system Redis to monitor if run is launched
        # self.redis_beamline = RedisDB(settings=self.site.REMOTE_ADAPTER_SETTINGS)

    handle_run(self, run_raw):
        """
        Handle the raw run information
        """

        # Run information is encoded in JSON format
        run_data = json.loads(current_run_raw)

        # Determine if the run should be ignored

        # If you need to manipulate the run information or add to it, here's the place

        # Put into exchangable format
        run_data_json = json.dumps(run_data)

        # Publish to Redis
        self.redis.publish("run_data:%s" % self.tag, run_data_json)

        # Push onto redis list in case no one is currently listening
        self.redis.lpush("runs_data:%s" % self.tag, run_data_json)

    handle_image(self, image_name):
        """
        Handle a new image
        """

        self.logger.debug("image_collected:%s %s",
                          self.tag,
                          image_name)

        # Publish to Redis
        red.publish("image_collected:%s" % self.tag, image_name)

        # Push onto redis list in case no one is currently listening
        red.lpush("images_collected:%s" % self.tag, image_name)

    # Used for file-based run information checking example
    def check_for_run_info(self):
        """
        Returns True if run_data_file has been changed, False if not
        """

        # Make sure we have a file to check
        if self.run_data_file:
            tries = 0
            while tries < 5:
                try:
                    statinfo = os.stat(self.run_data_file)
                    break
                except AttributeError:
                    if tries == 4:
                        return False
                    time.sleep(0.01)
                    tries += 1

            # The modification time has not changed
            if self.run_time == statinfo.st_ctime:
                return False

            # The file has changed
            else:
                self.run_time = statinfo.st_ctime
                return True
        else:
            return False

    # Used for file-based run information example
    def get_run_data(self):
        """
        Return contents of run data file
        """

        if self.run_data_file:

            # Copy the file to prevent conflicts with other programs
            # Use the ramdisk if it is available
            if os.path.exists("/dev/shm"):
                tmp_dir = "/dev/shm/"
            else:
                tmp_dir = "/tmp/"

            tmp_file = tmp_dir+uuid.uuid4().hex
            shutil.copyfile(self.run_data_file, tmp_file)

            # Read in the pickled file
            f = open(tmp_file, "rb")
            raw_run_data = pickle.load(f)
            f.close()
            self.logger.debug(raw_run_data)

            # Remove the temporary file
            os.unlink(tmp_file)

            # Standardize the run information
            """
            The necessary fields are:
                directory,
                image_prefix,
                run_number,
                start_image_number,
                number_images,
                distance,
                phi,
                kappa,
                omega,
                osc_axis,
                osc_start,
                osc_width,
                time,
                transmission,
                energy,
                anomalous
            """
            run_data = {
                "anomalous":None,
                "beamline":raw_run_data.get("beamline", None),              # Non-standard
                "beam_size_x":float(raw_run_data.get("beamsize", 0.0)),     # Non-standard
                "beam_size_y":float(raw_run_data.get("beamsize", 0.0)),     # Non-standard
                "directory":raw_run_data.get("directory", None),
                "distance":float(raw_run_data.get("dist", 0.0)),
                "energy":float(raw_run_data.get("energy", 0.0)),
                "file_ctime":datetime.datetime.fromtimestamp(self.run_time).isoformat(),
                "image_prefix":raw_run_data.get("image_prefix", None),
                "kappa":None,
                "number_images":int(float(raw_run_data.get("Nframes", 0))),
                "omega":None,
                "osc_axis":"phi",
                "osc_start":float(raw_run_data.get("start", 0.0)),
                "osc_width":float(raw_run_data.get("width", 0.0)),
                "phi":float(raw_run_data.get("start", 0.0)),
                "run_number":None,
                "site_tag":self.tag,
                "start_image_number":int(float(raw_run_data.get("first_image", 0))),
                "time":float(raw_run_data.get("time", 0.0)),
                "transmission":float(raw_run_data.get("trans", 0.0)),
                "twotheta":None
            }

        else:
            run_data = False

        return run_data

    # Used for file-based image example
    def check_for_image_collected(self):
        """
        Returns True if image information file has new timestamp, False if not
        """

        tries = 0
        while tries < 5:
            try:
                statinfo = os.stat(self.image_data_file)
                break
            except:
                if tries == 4:
                    return False
                time.sleep(0.01)
                tries += 1

        # The modification time has not changed
        if self.image_time == statinfo.st_mtime:
            return False
        # The file has changed
        else:
            self.image_time = statinfo.st_mtime
            return True

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

#!/usr/bin/env python

"""
This file is part of RAPD

Copyright (C) 2009-2018, Cornell University
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

__created__ = "2009-07-08"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

"""
rapd_adscserver provides an xmlrpclib  server that watches xf_status and
marcollect on an adsc data collection computer to provide information back
to rapd_server via to rapd_adsc

This server is used at 24ID-E with an ADSC Q315 detector

If you are adapting rapd to your locality, you will need to check this
carefully.
"""
# Standard imports
import argparse
import datetime
import importlib
import logging
import logging.handlers
import os
#import pickle
#import shutil
import socket
import sys
import time
import uuid
import redis

# RAPD imports
import utils.commandline
import utils.lock
import utils.log
from utils.overwatch import Registrar
import utils.site
import utils.text as text
from utils.text import json
from bson.objectid import ObjectId

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
        Setup and start the NecatGatherer
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")

        # Passed-in variables
        self.site = site
        self.overwatch_id = overwatch_id

        self.logger.info("NecatGatherer.__init__")

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
        self.logger.info("NecatGatherer.run")

        # Set up overwatcher
        self.ow_registrar = Registrar(site=self.site,
                                      ow_type="gatherer",
                                      ow_id=self.overwatch_id)
        self.ow_registrar.register({"site_id":self.site.ID})

        #self.logger.debug("  Will publish new images on filecreate:%s" % self.tag)
        #self.logger.debug("  Will push new images onto images_collected:%s" % self.tag)
        self.logger.debug("  Will publish new datasets on run_data:%s" % self.tag)
        self.logger.debug("  Will push new datasets onto run_data:%s" % self.tag)
        
        # path prefix for RDMA folder location with Eiger
        if self.tag == 'NECAT_E':
            path_prefix = '/epu2/rdma'
        else:
            path_prefix = ''

        try:
            while self.go:
                # Check if the run info changed in beamline Redis DB.
                #current_run = self.pipe.get("RUN_INFO_SV").set("RUN_INFO_SV", "").execute()
                # get run info passed from RAPD
                #current_run = self.redis.rpop('run_info_T')
                current_run = self.redis.rpop('run_info_%s'%self.tag[-1])
                if current_run not in (None, ""):
                    # get the additional beamline params and put into nice dict.
                    run_data = self.get_run_data(current_run)
                    if self.ignored(run_data['directory']):
                        self.logger.debug("Directory %s is marked to be ignored - skipping", run_data['directory'])
                    else:
                        #run_data['directory'] = dir
                        self.logger.debug("run_data:%s %s", self.tag, run_data)
                        # Put into exchangable format
                        run_data_json = json.dumps(run_data)
                        # Publish to Redis
                        self.redis.publish("run_data:%s" % self.tag, run_data_json)
                        # Push onto redis list in case no one is currently listening
                        self.redis.lpush("runs_data:%s" % self.tag, run_data_json)
                        """
                        ## This loop is for testing##
                        for i in range(2):
                            if i == 1:
                                dir = dir.replace('/epu/', '/epu2/')
                            run_data['directory'] = dir
                            self.logger.debug("run_data:%s %s", self.tag, run_data)
                            # Put into exchangable format
                            run_data_json = json.dumps(run_data)
                            # Publish to Redis
                            self.redis.publish("run_data:%s" % self.tag, run_data_json)
                            # Push onto redis list in case no one is currently listening
                            self.redis.lpush("run_data:%s" % self.tag, run_data_json)
                        """
                time.sleep(0.2)
                # Have Registrar update status
                self.ow_registrar.update({"site_id":self.site.ID})
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """
        Stop the loop
        """
        self.logger.debug("NecatGatherer.stop")

        self.go = False
        self.redis_database.stop()
        self.bl_database.stop()

    def connect(self):
        """Connect to redis host"""
        # Connect to control redis for publishing run data info
        redis_database = importlib.import_module('database.redis_adapter')

        self.redis_database = redis_database.Database(settings=self.site.CONTROL_DATABASE_SETTINGS)
        self.redis = self.redis_database.connect_to_redis()

        # Connect to beamline Redis to monitor if run is launched
        self.bl_database = redis_database.Database(settings=self.site.SITE_ADAPTER_SETTINGS[self.tag])
        self.bl_redis = self.bl_database.connect_redis_pool()
        #self.pipe = self.bl_redis.pipeline()

    def set_host(self):
        """
        Use os.uname to set files to watch
        """
        self.logger.debug("NecatGatherer.set_host")

        # Figure out which host we are on
        self.ip_address = socket.gethostbyaddr(socket.gethostname())[-1][0]
        self.logger.debug(self.ip_address)

        # Now grab the file locations, beamline from settings
        if self.site.GATHERERS.has_key(self.ip_address):
            self.tag = self.site.GATHERERS[self.ip_address]
            # Make sure we enforce uppercase for tag
            self.tag = self.tag.upper()
        else:
            print "ERROR - no settings for this host"
            self.tag = "test"
            # sys.exit(9)

    def ignored(self, dir):
        """Check if folder is supposed to be ignored."""
        for d in self.site.IMAGE_IGNORE_DIRECTORIES:
            if dir.startswith(d):
                return True
        return False

    def get_run_data(self, run_info):
        """Put together info from run and pass it back."""
        # Split it
        cur_run = run_info.split("_") #runnumber,first#,total#,dist,energy,transmission,omega_start,deltaomega,time,timestamp
        #1_1_23_400.00_12661.90_30.00_45.12_0.20_0.50_
        pipe = self.bl_redis.pipeline()
        #pipe.get("DETECTOR_SV")
        if self.tag == 'NECAT_C':
            pipe.get("ADX_DIRECTORY_SV")
        else:
            pipe.get("EIGER_DIRECTORY_SV")
        pipe.get("RUN_PREFIX_SV")
        #pipe.get("DET_THETA_SV")        #two theta
        #pipe.get("MD2_ALL_AXES_SV")     #for kappa and phi
        return_array = pipe.execute()
        # extend path with the '0_0' to path for Pilatus
        if self.tag == 'NECAT_C':
            #dir = os.path.join(return_array[0], "0_0")
            dir = '%s%s'%(return_array[0], "0_0")
        else:
            dir = return_array[0]
        # Get rid of trailing slash from beamline Redis.
        if dir[-1] == '/':
            dir = dir[:-1]
        # Standardize the run information
        run_data = {
            "anomalous":None,
            "beamline":self.tag,                                # Non-standard
            #"beam_size_x":float(raw_run_data.get("beamsize", 0.0)),     # Non-standard
            #"beam_size_y":float(raw_run_data.get("beamsize", 0.0)),     # Non-standard
            #"directory":return_array[0],
            "directory":dir,
            "distance":float(cur_run[3]),
            "energy":float(cur_run[4]),
            #"file_ctime":datetime.datetime.fromtimestamp(self.run_time).isoformat(),
            "image_prefix":return_array[1],
            "kappa":None,
            "number_images":int(cur_run[2]),
            "omega":None,
            "osc_axis":"phi",
            "osc_start":float(cur_run[6]),
            "osc_width":float(cur_run[7]),
            "phi": 0.0,
            "run_number":int(cur_run[0]),
            "site_tag":self.tag,
            "start_image_number":int(cur_run[1]),
            "time":float(cur_run[8]),
            "transmission":float(cur_run[5]),
            "twotheta":None,
        }

        return run_data

def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """Data gatherer for NECAT T beamline"""
    parser = argparse.ArgumentParser(parents=[utils.commandline.base_parser],
                                     description=commandline_description)

    return parser.parse_args()

def main():
    """ The main process
    Setup logging and instantiate the gatherer"""

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
                                  #level=log_level
                                  )

    logger.debug("Commandline arguments:")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s" % pair)

    # Instantiate the Gatherer
    GATHERER = Gatherer(site=SITE,
                        overwatch_id=commandline_args.overwatch_id)

if __name__ == '__main__':

    main()

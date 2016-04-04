"""
Watches files for information on images and runs on a MAR data collection
computer to provide information back to RAPD system via redis
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2009-2016, Cornell University
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
gatherer_sercat_id.py watches files for information on images and runs
on a MAR data collection computer to provide information back
to rapd_server via to redis

This server is used at SERCAT with MAR detectors

If you are adapting rapd to your locality, you will need to check this
carefully.

This server needs Python version 2.5 or greater (due to use of uuid module)
"""

# Standard imports
import argparse
import importlib
import json
import logging
import logging.handlers
import os
import pickle
import shutil
import socket
import time
import uuid

import redis

# RAPD imports
import utils.commandline
import utils.lock
import utils.log
from utils.overwatch import Registrar
import utils.site

class SercatGatherer(object):
    """
    Watches the beamline and signals images and runs over redis
    """

    # For keeping track of file change times
    run_time = 0
    image_time = 0

    # Host computer detail
    ip_address = None

    def __init__(self, site, overwatcher_id=None):
        """
        Setup and start the SercatGatherer
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")

        # Passed-in variables
        self.site = site
        self.overwatcher_id = overwatcher_id

        self.logger.info("SercatGatherer.__init__")

        # Connect to redis
        self.connect()

        # Get our bearings
        self.set_host()

        # Running conditions
        self.go = True

        # Now run
        self.run()

    def run(self):
        """
        The while loop for watching the files
        """
        self.logger.info("SercatGatherer.run")

        # Set up overwatcher
        if self.overwatcher_id:
            self.ow_registrar = Registrar(site=self.site,
                                          ow_type="gatherer",
                                          ow_id=self.overwatcher_id)
            self.ow_registrar.register({"site_id":self.site.ID})

        # Get redis connection
        red = redis.Redis(connection_pool=self.redis_pool)

        self.logger.debug("  Will publish new images on filecreate:%s" % self.tag)
        self.logger.debug("  Will push new images onto images_collected:%s" % self.tag)

        while self.go:

            # 5 rounds of checking
            for ___ in range(5):

                # Check if the run info has changed on the disk
                if self.check_for_run_info():
                    run_data = self.get_run_data()
                    if run_data:
                        run_data_json = json.dumps(run_data)
                        # Publish to Redis
                        red.publish("run_data:%s" % self.tag, run_data_json)
                        # Push onto redis list in case no one is currently listening
                        red.rpush("run_data:%s" % self.tag, run_data_json)

                # 20 image checks
                for __ in range(20):
                    # Check if the image file has changed
                    if self.check_for_image_collected():
                        image_name = self.get_image_data()
                        if image_name:
                            self.logger.debug("filecreate:%s %s",
                                              self.tag,
                                              image_name)
                            # Publish to Redis
                            red.publish("filecreate:%s" % self.tag, image_name)
                            # Push onto redis list in case no one is currently listening
                            red.rpush("images_collected:%s" % self.tag, image_name)
                        break
                    else:
                        time.sleep(0.05)

            # Have Registrar update status
            self.ow_registrar.update({"site_id":self.site.ID})

    def stop(self):
        """
        Stop the loop
        """
        self.logger.debug("SercatGatherer.stop")

        self.go = False

    def connect(self):
        """Connect to redis host"""

        # Connect to redis
        self.redis_pool = redis.ConnectionPool(host=self.site.IMAGE_MONITOR_REDIS_HOST)

    def set_host(self):
        """
        Use os.uname to set files to watch
        """
        self.logger.debug("SercatGatherer.set_host")

        # Figure out which host we are on
        self.ip_address = socket.gethostbyaddr(socket.gethostname())[-1][0]

        # Now grab the file locations, beamline from settings
        if self.site.GATHERERS.has_key(self.ip_address):
            self.image_data_file, self.run_data_file, self.tag = self.site.GATHERERS[self.ip_address]

            # Make sure we enforce lowercase for tag
            self.tag = self.tag.lower()
        else:
            print "ERROR - no settings for this host"
            self.tag = "test"
            # sys.exit(9)

    """
    Collected Image Information
    """
    def get_image_data(self):
        """
        Coordinates the retrieval of image data
        Called if image information file modification time is newer than the time in memory
        """

        # Get the image data line(s)
        image_lines = self.get_image_line()

        # Parse the lines
        image_data = self.parse_image_line(image_lines)

        # Return the parsed data
        return image_data

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

    def get_image_line(self):
        """
        return contents of xf_status
        """
        # Copy the file to prevent conflicts with other programs
        # HACK
        tmp_file = "/tmp/"+uuid.uuid4().hex
        shutil.copyfile(self.image_data_file, tmp_file)

        # Read in the lines of the file
        in_lines = open(tmp_file, "r").readlines()

        # Remove the temporary file
        os.unlink(tmp_file)

        return in_lines

    def parse_image_line(self, lines):
        """
        Parse the lines from the image information file and return a dict that
        is somewhat intelligible. Expect the file to look something like:
        8288 /data/BM_Emory_jrhorto.raw/xdc5/x13/x13_015/XDC-5_Pn13_r1_1.0400
        """

        try:
            for i in range(len(lines)):
                sline = lines[i].split()
                if len(sline) == 2:
                    if sline[1].strip() == "<none>":
                        self.logger.debug("image_data_file empty")
                        image_name = False
                        break
                    else:
                        image_name = os.path.realpath(sline[1])
                        break

            self.logger.debug("SercatGatherer.parse_image_line - %s", image_name)
            return image_name
        except:
            self.logger.exception("Failure to parse image data file - error in format?")
            return False

    """
    Run information methods
    """
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
                except:
                    if tries == 4:
                        return False
                    time.sleep(0.01)
                    tries += 1

            #the modification time has not changed
            if self.run_time == statinfo.st_mtime:
                return False

            #the file has changed
            else:
                self.run_time = statinfo.st_mtime
                return True
        else:
            return False

    def get_run_data(self):
        """
        Return contents of run data file
        """

        if self.run_data_file:
            # Copy the file to prevent conflicts with other programs
            tmp_file = "/dev/shm/"+uuid.uuid4().hex
            shutil.copyfile(self.run_data_file, tmp_file)

            # Read in the pickled file
            f = open(tmp_file, "rb")
            raw_run_data = pickle.load(f)
            f.close()

            # Remove the temporary file
            os.unlink(tmp_file)

            # Standardize the run information
            run_data = {
                "distance":float(raw_run_data.get("dist", 0.0)),
                "energy":float(raw_run_data.get("energy", 0.0)),
                "image_prefix":raw_run_data.get("image_prefix", ""),
                "number_images":int(raw_run_data.get("Nframes", 0)),
                "osc_range":float(raw_run_data.get("width", 0.0)),
                "osc_start":float(raw_run_data.get("start", 0.0)),
                "start_image_number":0,
                "time":float(raw_run_data.get("time", 0.0)),
                "transmission":float(raw_run_data.get("trans", 0.0)),
                "wavelength": 12400 / float(raw_run_data.get("energy", 0.0))
            }
            """
            X {'Nframes': '720.00',
            I 'beamline': '22ID',
            'beamsize': '50',
            I 'date': '2016_4_4',
            X 'dist': '400.00',
            X 'energy': '12398.42',
            I 'helical': 'No',
            X 'image_prefix': 'aC82to906_PIP2cocrys_D03292016_D3a',
            X 'start': '360.00',
            X 'time': '1.00',
            X 'trans': u'9.070',
            X 'width': '1.00'}
            """


        else:
            run_data = False

        return run_data

def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """Data gatherer for SERCAT ID beamline"""
    parser = argparse.ArgumentParser(parents=[utils.commandline.base_parser],
                                     description=commandline_description)

    return parser.parse_args()

def main():
    """ The main process
    Setup logging and instantiate the gatherer"""

    # Get the commandline args
    commandline_args = get_commandline()

    # Determine the site
    site_file = utils.site.determine_site(site_arg=commandline_args.site)

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
                                  logfile_id="gatherer_"+SITE.ID,
                                  level=log_level)

    logger.debug("Commandline arguments:")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s" % pair)

    # Instantiate the Gatherer
    GATHERER = SercatGatherer(site=SITE,
                              overwatcher_id=commandline_args.overwatcher_id)

if __name__ == '__main__':

    main()

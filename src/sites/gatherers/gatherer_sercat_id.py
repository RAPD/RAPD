#!/usr/bin/env python

"""
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

import argparse
import atexit
import importlib
import json
import logging, logging.handlers
import os
import pickle
import redis
import shutil
import socket
import sys
# import threading
import time
import uuid

# RAPD imports
import utils.commandline
import utils.lock
import utils.log
import utils.site_tools

GATHERERS = {
    "idc24.ser.aps.anl.gov" : (None, "/var/sergui/adxvframe")
}

# For testing
# HACK
GATHERERS = {
    "kona.nec.aps.anl.gov" : (None, "/tmp/adxvframe")
}

class SercatGatherer():
    """
    Watches the beamline and signals images and runs over redis
    """

    # For keeping track of file change times
    run_time = 0
    image_time = 0

    def __init__(self, site):
        """Setup and start the SercatGatherer"""

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")

        # Passed-in variable
        self.site = site

        self.logger.info("SercatGatherer.__init__")

        # Assign some to instance
        self.ip_address = socket.gethostbyaddr(socket.gethostname())[-1][0]

        #Connect to redis
        self.redis_pool = redis.ConnectionPool(host=self.site.IMAGE_MONITOR_REDIS_HOST)

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

        # Get redis connection
        red = redis.Redis(connection_pool=self.redis_pool)

        while self.go:
            # Check if the run info has changed on the disk
            if self.check_for_run_info():
                run_data = self.get_run_data()
                if run_data:
                    run_data_json = json.dumps(run_data)
                    # Publish to Redis
                    red.publish("run_data:%s" % self.site, run_data_json)
                    # Push onto redis list in case no one is currently listening
                    red.rpush("run_data:%s" % self.site, run_data_json)

            # 1 run check for every 20 image checks
            for __ in range(20):
                # Check if the image file has changed
                if self.check_for_image_collected():
                    image_name = self.get_image_data()
                    if image_name:
                        self.logger.debug("filecreate:%s %s",
                                          self.site,
                                          image_name)
                        # Publish to Redis
                        red.publish("filecreate:%s" % self.site, image_name)
                        # Push onto redis list in case no one is currently listening
                        red.rpush("filecreate:%s" % self.site, image_name)
                    break
                else:
                    time.sleep(0.05)

    def stop(self):
        """
        Stop the loop
        """
        self.logger.debug("SercatGatherer.stop")

        self.go = False

    def set_host(self):
        """
        Use os.uname to set files to watch
        """
        self.logger.debug("SercatGatherer.set_host")

        # Figure out which host we are on
        host = os.uname()[1]

        # Now grab the file locations, beamline from settings
        if GATHERERS.has_key(host):
            self.run_data_file, self.image_data_file = GATHERERS[host]
        else:
            print "ERROR - no settings for this host"
            sys.exit(9)

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
                        out_dict = False
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

        #copy the file to prevent conflicts with other programs
        tmp_file = "/dev/shm/"+uuid.uuid4().hex
        shutil.copyfile(self.run_data_file, tmp_file)

        #read in the pickled file
        run_data = pickle.load(tmp_file)

        #remove the temporary file
        os.unlink(tmp_file)

        return run_data

    # def ParseMarcollect(self, lines):
    #     """
    #     Parse the lines from the file marcollect and return a dict that
    #     is somewhat intelligible
    #     NB - only used with one line run-containing marcollect so far
    #     """
    #     self.logger.debug("RAPD_ADSC_Server::ParseMarcollect")
    #     #self.logger.debug(lines)
    #
    #     try:
    #         out_dict = {"Runs" : {}}
    #         for i in range(len(lines)):
    #             sline = lines[i].split(":")
    #             if sline[0] == "Directory":
    #                 if sline[1].strip().endswith('/'):
    #                     out_dict['Directory'] = sline[1].strip()[:-1]
    #                 else:
    #                     out_dict['Directory'] = sline[1].strip()
    #             elif sline[0] == 'Image_Prefix':
    #                 if sline[1].strip().endswith('_'):
    #                     out_dict['Image_Prefix'] = sline[1].strip()[:-1]
    #                 else:
    #                     out_dict['Image_Prefix'] = sline[1].strip()
    #             elif sline[0] == 'Mode':
    #                 out_dict['Mode'] = sline[1].strip()
    #             elif sline[0] == 'ADC':
    #                 out_dict['ADC'] = sline[1].strip()
    #             elif sline[0] == 'Anomalous':
    #                 out_dict['Anomalous'] = sline[1].strip()
    #             elif sline[0] == 'Anom_Wedge':
    #                 out_dict['Anom_Wedge'] = sline[1].strip()
    #             elif sline[0] == 'Compression':
    #                 out_dict['Compression'] = sline[1].strip()
    #             elif sline[0] == 'Binning':
    #                 out_dict['Binning'] = sline[1].strip()
    #             elif sline[0] == 'Comment':
    #                 out_dict['Comment'] = sline[1].strip()
    #             elif sline[0] == 'Beam_Center':
    #                 out_dict['Beam_Center'] = sline[1].strip()
    #             elif sline[0] == 'MAD':
    #                 out_dict['MAD'] = sline[1].strip()
    #             elif sline[0] == 'Energy to Use':
    #                 pass
    #
    #             #handle the run lines
    #             elif sline[0] == 'Run(s)':
    #                 run_num = 0
    #                 for j in range(i+1,len(lines)):
    #                     my_sline = lines[j].split()
    #                     if len(my_sline) > 0:
    #                         out_dict['Runs'][str(run_num)] = {
    #                             'file_source' : 'adsc',
    #                             'Run' : my_sline[0],
    #                             'Start' : my_sline[1],
    #                             'Total' : my_sline[2],
    #                             'Distance'     : my_sline[3],
    #                             '2-Theta'      : my_sline[4],
    #                             'Phi'          : my_sline[5],
    #                             'Kappa'        : my_sline[6],
    #                             'Omega'        : my_sline[7],
    #                             'Axis'         : my_sline[8],
    #                             'Width'        : my_sline[9],
    #                             'Time'         : my_sline[10],
    #                             'De-Zngr'      : my_sline[11],
    #                             'Directory'    : out_dict['Directory'],
    #                             'Image_Prefix' : out_dict['Image_Prefix'],
    #                             'Anomalous'    : 'No'}
    #                         run_num += 1
    #                         if 'Yes' in out_dict['Anomalous']:
    #                             out_dict['Runs'][str(run_num-1)]['Anomalous'] = 'Yes'
    #                             out_dict['Runs'][str(run_num)] = {'file_source' : 'adsc',
    #                                                          'Run'          : str(100+int(my_sline[0])),
    #                                                          'Start'        : my_sline[1],
    #                                                          'Total'        : my_sline[2],
    #                                                          'Distance'     : my_sline[3],
    #                                                          '2-Theta'      : my_sline[4],
    #                                                          'Phi'          : my_sline[5],
    #                                                          'Kappa'        : my_sline[6],
    #                                                          'Omega'        : my_sline[7],
    #                                                          'Axis'         : my_sline[8],
    #                                                          'Width'        : my_sline[9],
    #                                                          'Time'         : my_sline[10],
    #                                                          'De-Zngr'      : my_sline[11],
    #                                                          'Directory'    : out_dict['Directory'],
    #                                                          'Image_Prefix' : out_dict['Image_Prefix'],
    #                                                          'Anomalous'    : 'Yes'}
    #                             run_num += 1
    #         if not out_dict['MAD']:
    #             out_dict['MAD'] = 'No'
    #
    #         self.logger.debug("Resulting dict")
    #         self.logger.debug(out_dict)
    #
    #         return(out_dict)
    #
    #     except:
    #         self.logger.exception('Failure to parse marcollect - error in format?')
    #         return(False)

# def file_is_locked(file_path):
#     """Method to make sure only one instance is running on this machine"""
#     global file_handle
#
# 	# Create the directory for file_path if it does not exist
#     if not os.path.exists(os.path.dirname(file_path)):
#         os.makedirs(os.path.dirname(file_path))
#
#     file_handle = open(file_path, "w")
#     try:
#         fcntl.lockf(file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
#         return False
#     except IOError:
#         return True

def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """The core rapd process for coordination of a
    site install"""
    parser = argparse.ArgumentParser(parents=[utils.commandline.base_parser],
                                     description=commandline_description)

    return parser.parse_args()

def main(site_in=None):
    """ The main process
    Setup logging and instantiate the gatherer"""

    # Get the commandline args
    commandline_args = get_commandline()

    # Determine the site
    site_file = utils.site_tools.determine_site(site_arg=commandline_args.site)

    # Import the site settings
    SITE = importlib.import_module(site_file)

	# Single process lock?
    if SITE.GATHERER_LOCK_FILE:
        if utils.lock.file_is_locked(SITE.GATHERER_LOCK_FILE):
            raise Exception("%s is already locked, unable to run" % SITE.GATHERER_LOCK_FILE)

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
    GATHERER = SercatGatherer(site=SITE)

if __name__ == '__main__':

    main()

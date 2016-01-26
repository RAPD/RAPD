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
rapd_gatherer_sercat.py watches files for information on images and runs
on a MAR data collection computer to provide information back
to rapd_server via to redis

This server is used at SERCAT with MAR detectors

If you are adapting rapd to your locality, you will need to check this
carefully.

This server needs Python version 2.5 or greater (due to use of uuid module)
"""

import atexit
import json
import logging, logging.handlers
import os
import pickle
import redis
import shutil
import socket
import sys
import threading
import time
import uuid

# Import secret data
import sercat_secrets as secrets
GATHERERS = secrets.GATHERERS
REDISHOST = secrets.REDISHOST

class SercatGatherer(threading.Thread):
    """
    Watches the beamline and signals images and runs over redis
    """
    def __init__(self, one_run=False):
        """Setup and start the SercatGatherer"""

        #set up logging
        log_filename = "/tmp/rapd_gatherer_sercat.log"
        # Set up a specific logger with our desired output level
        logger = logging.getLogger("RAPDLogger")
        logger.setLevel(logging.DEBUG)
        # Add the log message handler to the logger
        handler = logging.handlers.RotatingFileHandler(log_filename, maxBytes=100000, backupCount=5)
        #add a formatter
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.info("SercatGatherer.__init__")

        #init the thread
        threading.Thread.__init__(self)

        # Assign some to instance
        self.logger = logger
        self.ip_address = socket.gethostbyaddr(socket.gethostname())[-1][0]

        #passed in
        self.one_run = one_run

        #for keeping track of file change times
        self.run_time = 0
        self.image_time = 0

        #Connect to redis
        self.redis_pool = redis.ConnectionPool(host=REDISHOST)

        #get our bearings
        self.set_host()

        #running conditions
        self.go = True
        atexit.register(self.stop)

        #now run
        self.start()

    def run(self):
        """
        The while loop for watching the files
        """
        self.logger.info("SercatGatherer.run")

        # Get redis connection
        red = redis.Redis(connection_pool=self.redis_pool)

        while self.go:
            # # Check if the run info has changed on the disk
            if self.check_for_run_info():
                run_data = self.get_run_data()
                if run_data:
                    run_data_json = json.dumps(run_data)
                    # Publish to Redis
                    red.publish("run_data:%s" % self.site, run_data_json)
                    # Push onto redis list in case no one is currently listening
                    red.rpush("run_data:%s" % self.site, run_data_json)

            # 1 run check for every 5 image checks
            for __ in range(5):
                # Check if the image file has changed
                if self.check_for_image_collected():
                    image_data = self.get_image_data()
                    if image_data:
                        # Publish to Redis
                        red.publish("filecreate:%s" % self.site, image_data.get("image_name", ""))
                        # Push onto redis list in case no one is currently listening
                        red.rpush("filecreate:%s" % self.site, image_data.get("image_name", ""))
                    break
                else:
                    time.sleep(0.1)
            if self.one_run:
                break

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

        #figure out which host we are on
        host = os.uname()[1]

        #now grab the file locations, beamline from settings
        if SETTINGS.has_key(host):
            self.run_data_file, self.image_data_file, self.site = secrets.GATHERERS[host]
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

        #get the image data line(s)
        image_lines = self.get_image_lines()

        #parse the lines
        image_data = self.parse_image_lines(image_lines)

        # return the parsed data
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

        #the modification time has not changed
        if self.image_time == statinfo.st_mtime:
            return False
        #the file has changed
        else:
            self.image_time = statinfo.st_mtime
            return True

    def get_image_lines(self):
        """
        return contents of xf_status
        """
        #copy the file to prevent conflicts with other programs
        tmp_file = "/dev/shm/"+uuid.uuid4().hex
        shutil.copyfile(self.image_data_file, tmp_file)

        #read in the lines of the file
        in_lines = open(tmp_file, "r").readlines()

        #remove the temporary file
        os.unlink(tmp_file)

        return in_lines

    def parse_image_lines(self, lines):
        """
        Parse the lines from the image information file and return a dict that
        is somewhat intelligible. Expect the file to look something like:
        8288 /data/BM_Emory_jrhorto.raw/xdc5/x13/x13_015/XDC-5_Pn13_r1_1.0400
        """

        out_dict = {"adsc_number"  : "",
                    "image_name"   : "",
                    "directory"    : "",
                    "image_prefix" : "",
                    "run_number"   : "",
                    "image_number" : "",
                    "status"       : "None"}
        try:
            for i in range(len(lines)):
                sline = lines[i].split()
                if len(sline) == 2:
                    if sline[1].strip() == "<none>":
                        self.logger.debug("image_data_file empty")
                        out_dict = False
                        break
                    else:
                        try:
                            # Commented-out entries remain for future possible use
                            # out_dict["adsc_number"] = int(sline[0])
                            out_dict["image_name"] = sline[1]
                            # out_dict["directory"] = os.path.dirname(sline[1])
                            # out_dict["image_prefix"] = "_".join(
                                # os.path.basename(sline[1]).split("_")[:-1])
                            # out_dict["run_number"] = int(os.path.basename(
                                # sline[1]).split("_")[-1].split(".")[0])
                            # out_dict["image_number"] = int(sline[1].split(".")[-1])
                            out_dict["status"] = "SUCCESS"
                            break
                        except:
                            self.logger.exception(
                                "Exception in SercatGatherer.parse_image_lines %s", lines[i])
                            out_dict = False
                            break
            self.logger.debug("SercatGatherer.parse_image_lines - %s", out_dict["image_name"])
            return out_dict
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


if __name__ == '__main__':

    #create the watcher instance
    WATCHER = SercatGatherer()

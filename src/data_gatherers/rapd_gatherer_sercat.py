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
"""

import atexit
from collections import deque
import logging, logging.handlers
import os
import redis
import socket
import sys
import threading
import time
import uuid

# Site-specific setup
REDISHOST = "164.54.208.142"
SETTINGS = {"idc24.ser.aps.anl.gov": ("/var/sergui/adxvframe", "", "22ID"),
            "bmc83.ser.aps.anl.gov": ("/var/sergui/adxvframe", "", "22BM")}

class SercatGatherer(threading.Thread):
    """
    Watches the beamline and signals images and runs over redis
    """
    def __init__(self, one_run=False):
        """Setup and start the SercatGatherer"""

        #set up logging
        log_filename = "/tmp/rapd_gatherer_sercat.log"
        # Set up a specific logger with our desired output level
        logger = logging.getLogger('RAPDLogger')
        logger.setLevel(logging.DEBUG)
        # Add the log message handler to the logger
        handler = logging.handlers.RotatingFileHandler(log_filename, maxBytes=100000, backupCount=5)
        #add a formatter
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.info('SercatGatherer.__init__')

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
        self.mar_dict = {}
        self.xf_dict = {}
        self.last_image = False
        self.xf_status_queue = deque()
        self.marcollect_queue = deque()

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
        self.logger.info('SercatGatherer.run')

        # Get redis connection
        red = redis.Redis(connection_pool=self.redis_pool)

        while self.go:
            # # Check if the run info has changed on the disk
            # if self.CheckMarcollect():
            #     mlines = self.GetMarcollect()
            #     mparsed = self.ParseMarcollect(mlines)
            #     if mparsed:
            #         self.marcollect_queue.appendleft(mparsed.copy())

            # 1 run check for every 5 image checks
            for __ in range(5):
                # Check if the image file has changed
                if self.check_for_image_collected():
                    xparsed = self.get_image_data()
                    if xparsed:
                        self.xf_status_queue.appendleft(xparsed.copy())
                        #Publish to Redis
                        red.publish("filecreate:%s" % "JDSJJD", xparsed.get("image_name", ""))
                    break
                else:
                    time.sleep(0.1)
            if self.one_run:
                break

    def stop(self):
        """
        Stop the loop
        """
        self.logger.debug('SercatGatherer.stop')

        self.go = False

    def set_host(self):
        """
        Use os.uname to set files to watch
        """
        self.logger.debug('SercatGatherer.set_host')

        #figure out which host we are on
        host = os.uname()[1]

        #now grab the file locations, beamline from settings
        if SETTINGS.has_key(host):
            self.marcollect, self.image_data_file, self.beamline = SETTINGS[host]
        else:
            print "ERROR - no settings for this host"
            sys.exit(9)

    """
    Collected Image Information
    """
    # def GetXFStatusTime(self):
    #     """
    #     Returns modification time of xf_status
    #     """
    #     return(self.image_time)

    # def GetXFStatusData(self):
    #     """
    #     Returns dict of xf_status
    #     """
    #     if len(self.xf_status_queue) > 0:
    #         return self.xf_status_queue.pop()
    #     else:
    #         return False

    def get_image_data(self):
        """
        Called if image information file modification time is newer than the time in memory
        """
        #get the line of the xf_status
        image_lines = self.get_image_lines()

        #parse the lines
        image_lines_parsed = self.parse_image_lines(image_lines)

        #if there are lines after parsing i.e. this is a real file, add the info to the
        #database and then look at the image
        return image_lines_parsed

    def GetLastImage(self):
        """
        Returns the last image as taken from xf_status
        """
        return(self.last_image)

    def check_for_image_collected(self):
        """
        Returns True if image information file has been changed, False if not
        """
        tries = 0
        while tries < 5:
            try:
                statinfo = os.stat(self.image_data_file)
                break
            except :
                if tries == 4:
                    return False
                tries += 1

        #the modification time has not changed
        if (self.image_time == statinfo.st_mtime):
            return(False)
        #the file has changed
        else:
            self.image_time = statinfo.st_mtime
            return(True)

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
        os.system('rm -f ./tmp_xf_status')
        return(in_lines)

    def parse_image_lines(self, lines):
        """
        Parse the lines from the image information file and return a dict that
        is somewhat intelligible. Expect the file to look something like:
        8288 /data/BM_Emory_jrhorto.raw/xdc5/x13/x13_015/XDC-5_Pn13_r1_1.0400
        """

        out_dict = {'adsc_number'  : '',
                    'image_name'   : '',
                    'directory'    : '',
                    'image_prefix' : '',
                    'run_number'   : '',
                    'image_number' : '',
                    'status'       : 'None'}
        try:
            for i in range(len(lines)):
                sline = lines[i].split()
                if len(sline) == 2:
                    if sline[1].strip() == '<none>':
                        self.logger.debug('xf_status empty')
                        out_dict = False
                        break
                    else:
                        try:
                            out_dict['adsc_number'] = int(sline[0])
                            out_dict['image_name'] = sline[1]
                            #set this for retrieval
                            self.last_image = int(sline[1])
                            out_dict['directory'] = os.path.dirname(sline[1])
                            out_dict['image_prefix'] = '_'.join(
                                os.path.basename(sline[1]).split('_')[:-1])
                            out_dict['run_number'] = int(os.path.basename(
                                sline[1]).split('_')[-1].split(".")[0])
                            out_dict['image_number'] = int(sline[1].split('.')[-1])
                            out_dict['status'] = 'SUCCESS'
                            break
                        except:
                            self.logger.exception(
                                'Exception in RAPD_ADSC_Server::ParseXFStatus %s' % lines[i])
                            out_dict = False
                            break
            self.logger.debug('RAPD_ADSC_Server::ParseXFStatus - %s' % out_dict['image_name'])
            return out_dict
        except:
            self.logger.exception('Failure to parse xf_status - error in format?')
            return False

    """
    Run information methods
    """
    def GetMarcollectTime(self):
        """
        Returns modification time of run file
        """
        return self.run_time

    def GetMarcollectData(self):
        """
        Returns dict of marcollect
        """
        self.logger.debug('GetMarcollectData')
        if len(self.marcollect_queue) > 0:
            return self.marcollect_queue.pop()
        else:
            return False

    def CheckMarcollect(self):
        """
        return True if marcollect has been changed, False if not
        """
        tries = 0
        while tries < 5:
            try:
                statinfo = os.stat(self.marcollect)
                break
            except:
                if tries == 4:
                    return False
                tries += 1

        #the modification time has not changed
        if self.run_time == statinfo.st_mtime:
            return False
        #the file has changed
        else:
            self.mar_time = statinfo.st_mtime
            return True

    def GetMarcollect(self):
        """
        return contents of marcollect
        """
        self.logger.debug('RAPD_ADSC_Server::GetMarcollect')
        #copy the file to prevent conflicts with other programs
        os.system('cp '+self.marcollect+' ./tmp_marcollect')
        #read in the lines of the file
        in_lines = open('./tmp_marcollect', 'r').readlines()
        #remove the temporary file
        os.system('rm -f ./tmp_marcollect')
        return in_lines

    def ParseMarcollect(self, lines):
        """
        Parse the lines from the file marcollect and return a dict that
        is somewhat intelligible
        NB - only used with one line run-containing marcollect so far
        """
        self.logger.debug('RAPD_ADSC_Server::ParseMarcollect')
        #self.logger.debug(lines)

        try:
            out_dict = {'Runs' : {}}
            for i in range(len(lines)):
                sline = lines[i].split(':')
                if sline[0] == 'Directory':
                    if sline[1].strip().endswith('/'):
                        out_dict['Directory'] = sline[1].strip()[:-1]
                    else:
                        out_dict['Directory'] = sline[1].strip()
                elif sline[0] == 'Image_Prefix':
                    if sline[1].strip().endswith('_'):
                        out_dict['Image_Prefix'] = sline[1].strip()[:-1]
                    else:
                        out_dict['Image_Prefix'] = sline[1].strip()
                elif sline[0] == 'Mode':
                    out_dict['Mode'] = sline[1].strip()
                elif sline[0] == 'ADC':
                    out_dict['ADC'] = sline[1].strip()
                elif sline[0] == 'Anomalous':
                    out_dict['Anomalous'] = sline[1].strip()
                elif sline[0] == 'Anom_Wedge':
                    out_dict['Anom_Wedge'] = sline[1].strip()
                elif sline[0] == 'Compression':
                    out_dict['Compression'] = sline[1].strip()
                elif sline[0] == 'Binning':
                    out_dict['Binning'] = sline[1].strip()
                elif sline[0] == 'Comment':
                    out_dict['Comment'] = sline[1].strip()
                elif sline[0] == 'Beam_Center':
                    out_dict['Beam_Center'] = sline[1].strip()
                elif sline[0] == 'MAD':
                    out_dict['MAD'] = sline[1].strip()
                elif sline[0] == 'Energy to Use':
                    pass

                #handle the run lines
                elif sline[0] == 'Run(s)':
                    run_num = 0
                    for j in range(i+1,len(lines)):
                        my_sline = lines[j].split()
                        if len(my_sline) > 0:
                            out_dict['Runs'][str(run_num)] = {'file_source' : 'adsc',
                                                         'Run'          : my_sline[0],
                                                         'Start'        : my_sline[1],
                                                         'Total'        : my_sline[2],
                                                         'Distance'     : my_sline[3],
                                                         '2-Theta'      : my_sline[4],
                                                         'Phi'          : my_sline[5],
                                                         'Kappa'        : my_sline[6],
                                                         'Omega'        : my_sline[7],
                                                         'Axis'         : my_sline[8],
                                                         'Width'        : my_sline[9],
                                                         'Time'         : my_sline[10],
                                                         'De-Zngr'      : my_sline[11],
                                                         'Directory'    : out_dict['Directory'],
                                                         'Image_Prefix' : out_dict['Image_Prefix'],
                                                         'Anomalous'    : 'No' }
                            run_num += 1
                            if 'Yes' in out_dict['Anomalous']:
                                out_dict['Runs'][str(run_num-1)]['Anomalous'] = 'Yes'
                                out_dict['Runs'][str(run_num)] = {'file_source' : 'adsc',
                                                             'Run'          : str(100+int(my_sline[0])),
                                                             'Start'        : my_sline[1],
                                                             'Total'        : my_sline[2],
                                                             'Distance'     : my_sline[3],
                                                             '2-Theta'      : my_sline[4],
                                                             'Phi'          : my_sline[5],
                                                             'Kappa'        : my_sline[6],
                                                             'Omega'        : my_sline[7],
                                                             'Axis'         : my_sline[8],
                                                             'Width'        : my_sline[9],
                                                             'Time'         : my_sline[10],
                                                             'De-Zngr'      : my_sline[11],
                                                             'Directory'    : out_dict['Directory'],
                                                             'Image_Prefix' : out_dict['Image_Prefix'],
                                                             'Anomalous'    : 'Yes'}
                                run_num += 1
            if not out_dict['MAD']:
                out_dict['MAD'] = 'No'

            self.logger.debug("Resulting dict")
            self.logger.debug(out_dict)

            return(out_dict)

        except:
            self.logger.exception('Failure to parse marcollect - error in format?')
            return(False)

    def AddMarcollect(self,data,attempt=0):
        """
        Add a new marcollect to the MySQL database
        """
        self.logger.debug('RAPD_ADSC_Server::AddMarcollect %d' % attempt)

        if attempt > 2:
            self.logger.debug('FAILED TO ADD MARCOLLECT AFTER 3 TRIES - Giving Up!')
            return(False)

        #connect to the database
        try:
            self.mar_dict = data.copy()
            self.cursor.execute("""INSERT INTO run_status (adc,
                                                           anom_wedge,
                                                           anomalous,
                                                           beam_center,
                                                           binning,
                                                           comment,
                                                           compression,
                                                           directory,
                                                           image_prefix,
                                                           mad,
                                                           mode,
                                                           beamline) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                                                           (data['ADC'],
                                                            data['Anom_Wedge'],
                                                            data['Anomalous'],
                                                            data['Beam_Center'],
                                                            data['Binning'],
                                                            data['Comment'],
                                                            data['Compression'],
                                                            data['Directory'],
                                                            data['Image_Prefix'],
                                                            data['MAD'],
                                                            data['Mode'],
                                                            self.beamline))
            self.connection.commit()

        except _mysql_exceptions.IntegrityError , (errno, strerror):
            if errno == 1062:
                self.logger.exception('This run_status is already in the database')
                if self.beamline == 'T':
                    self.logger.warning(data)
                    try:
                        self.cursor.execute("""UPDATE run_status SET adc          = %s,
                                                                 anom_wedge   = %s,
                                                                 anomalous    = %s,
                                                                 beam_center  = %s,
                                                                 binning      = %s,
                                                                 comment      = %s,
                                                                 compression  = %s,
                                                                 directory    = %s,
                                                                 image_prefix = %s,
                                                                 mad          = %s,
                                                                 mode         = %s,
                                                                 beamline     = %s WHERE directory = %s AND image_prefix = %s""",
                                                           (data['ADC'],
                                                            data['Anom_Wedge'],
                                                            data['Anomalous'],
                                                            data['Beam_Center'],
                                                            data['Binning'],
                                                            data['Comment'],
                                                            data['Compression'],
                                                            data['Directory'],
                                                            data['Image_Prefix'],
                                                            data['MAD'],
                                                            data['Mode'],
                                                            self.beamline,
                                                            data['Directory'],
                                                            data['Image_Prefix']))
                        self.connection.commit()
                        self.logger.debug('Run Status entered')
                    except:
                        self.logger.exception("Exception in updating run_status")
            else:
                self.logger.exception('ERROR : unknown IntegrityError exception in Database::AddMarcollect')

        except _mysql_exceptions.OperationalError , (errno, strerror):
            if errno == 2006:
                self.logger.exception('Connection to MySQL database lost. Will attempt to reconnect.')
                self.Connect2SQL()
                self.AddMarcollect(data,attempt=attempt+1)
            else:
                self.logger.exception('ERROR : unknown OperationalError in Database::AddMarcollect')
        except:
            self.logger.exception('ERROR : unknown exception in Database::AddMarCollect')

        #add the runs even if we have an error with adding the marcollect
        results = []
        # for run in data['Runs'].keys():
        #     results.append(self.AddRun(data['Runs'][run]))

        if True in results:
            return True
        else:
            return False

    # def AddRun(self,run,attempt=0):
    #     """
    #     Add a new run to the MySQL database
    #     """
    #     self.logger.debug('RAPD_ADSC_Server::AddRun')
    #
    #     if attempt > 2:
    #         self.logger.warning('FAILED TO ADD RUN AFTER 3 TRIES - Giving Up!')
    #         return(False)
    #
    #     try:
    #         self.logger.debug("Adding run into database directory:%s image_prefix:%s run_number:%s" %(run['Directory'],run['Image_Prefix'],run['Run']))
    #         self.cursor.execute("""INSERT INTO runs (directory,
    #                                                  image_prefix,
    #                                                  run_number,
    #                                                  start,
    #                                                  total,
    #                                                  distance,
    #                                                  twotheta,
    #                                                  phi,
    #                                                  kappa,
    #                                                  omega,
    #                                                  axis,
    #                                                  width,
    #                                                  time,
    #                                                  de_zngr,
    #                                                  anomalous,
    #                                                  beamline) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
    #                                                  (run['Directory'],
    #                                                   run['Image_Prefix'],
    #                                                   run['Run'],
    #                                                   run['Start'],
    #                                                   run['Total'],
    #                                                   run['Distance'],
    #                                                   run['2-Theta'],
    #                                                   run['Phi'],
    #                                                   run['Kappa'],
    #                                                   run['Omega'],
    #                                                   run['Axis'],
    #                                                   run['Width'],
    #                                                   run['Time'],
    #                                                   run['De-Zngr'],
    #                                                   run['Anomalous'],
    #                                                   self.beamline))
    #         self.connection.commit()
    #         return(True)
    #
    #     except _mysql_exceptions.IntegrityError , (errno, strerror):
    #         if errno == 1062:
    #             self.logger.exception('Run is already in the database')
    #             if self.beamline == 'T':
    #                 self.logger.debug(run)
    #                 self.cursor.execute("""UPDATE runs SET directory    = %s,
    #                                                        image_prefix = %s,
    #                                                        run_number   = %s,
    #                                                        start        = %s,
    #                                                        total        = %s,
    #                                                        distance     = %s,
    #                                                        twotheta     = %s,
    #                                                        phi          = %s,
    #                                                        kappa        = %s,
    #                                                        omega        = %s,
    #                                                        axis         = %s,
    #                                                        width        = %s,
    #                                                        time         = %s,
    #                                                        de_zngr      = %s,
    #                                                        anomalous    = %s,
    #                                                        beamline     = %s WHERE directory = %s AND image_prefix = %s AND run_number = %s AND start = %s""",
    #                                                        (run['Directory'],
    #                                                         run['Image_Prefix'],
    #                                                         run['Run'],
    #                                                         run['Start'],
    #                                                         run['Total'],
    #                                                         run['Distance'],
    #                                                         run['2-Theta'],
    #                                                         run['Phi'],
    #                                                         run['Kappa'],
    #                                                         run['Omega'],
    #                                                         run['Axis'],
    #                                                         run['Width'],
    #                                                         run['Time'],
    #                                                         run['De-Zngr'],
    #                                                         run['Anomalous'],
    #                                                         self.beamline,
    #                                                         run['Directory'],
    #                                                         run['Image_Prefix'],
    #                                                         run['Run'],
    #                                                         run['Start']))
    #                 self.connection.commit()
    #                 self.logger.debug("Run entered")
    #         else:
    #             self.logger.exception('ERROR : unknown IntegrityError exception in RAPD_ADSC_Server::AddRun')
    #         return(False)
    #
    #     except _mysql_exceptions.OperationalError , (errno, strerror):
    #         if errno == 2006:
    #             self.logger.exception('Connection to MySQL database lost. Will attempt to reconnect.')
    #             self.Connect2SQL()
    #             self.AddRun(run,attempt=attempt+1)
    #         else:
    #             self.logger.exception('ERROR : unknown OperationalError in RAPD_ADSC_Server::AddRun')
    #         return(False)
    #
    #     except:
    #         self.logger.exception('ERROR : unknown exception in RAPD_ADSC_Server::AddRun')
    #         return(False)


if __name__ == '__main__':

    #create the watcher instance
    watcher = SercatGatherer()

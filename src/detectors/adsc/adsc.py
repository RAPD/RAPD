"""
This file is part of RAPD

Copyright (C) 2009-2017, Cornell University
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
rapd_adsc provides a connection to the adsc image computer by connecting
via xmlrpclib to rapd_adscserver running on the adsc data collection
computer

If you are adapting rapd to your locality, you will need to check this
carefully
"""

import threading
import time
import os
import re
import pysent
import json
import xmlrpclib
import atexit
from rapd_site import secret_settings as secrets
from rapd_utils import date_adsc_to_sql

def print_dict(in_dict):
    keys = in_dict.keys()
    keys.sort()
    for key in keys:
        print key,'::',in_dict[key]
    print ''

months = { 'Jan' : '01',
           'Feb' : '02',
           'Mar' : '03',
           'Apr' : '04',
           'May' : '05',
           'Jun' : '06',
           'Jul' : '07',
           'Aug' : '08',
           'Sep' : '09',
           'Oct' : '10',
           'Nov' : '11',
           'Dec' : '12'}

def zerofillday(day_in):
    #print day_in
    intday = int(day_in)
    #print intday
    strday = str(intday)
    #print strday
    if len(strday) == 2:
        return(strday)
    else:
        return('0'+strday)

# def date_adsc_to_sql(datetime_in):
#     #print datetime_in
#     spldate = datetime_in.split()
#     #print spldate
#     time  = spldate[3]
#     #print time
#     year  = spldate[4]
#     #print year
#     month = months[spldate[1]]
#     #print month
#     day   = zerofillday(spldate[2])
#     #print day
#
#     date = '-'.join((year,month,day))
#     #print date
#     #print ' '.join((date,time))
#     return('T'.join((date,time)))

# class Q315_Monitor(threading.Thread):
#     """
#     Start a new thread which looks for changes via the server
#     Run from within Model
#     """
#     def __init__(self,beamline='C',notify=None,reconnect=None,logger=None):
#         logger.info('Q315_Monitor::__init__  beamline: %s' % beamline)
#
#         #initialize the thread
#         threading.Thread.__init__(self)
#
#         #passed-in variables
#         self.notify    = notify
#         self.reconnect = reconnect
#         self.beamline  = beamline
#         self.logger    = logger
#
#         #for stopping/starting
#         self.Go = True
#
#         #The modification times
#         self.xf_time  = 0
#         self.mar_time = 0
#
#         #set the adsc server
#         if beamline in secrets.keys():
#             self.logger.debug('Attmepting to conect to adsc monitor at %s' % secrets[beamline]['adsc_server'])
#             self.server = xmlrpclib.Server(secrets[beamline]['adsc_server'])
#             print self.server
#         #if the assigned beamline is not in the settings, use the localhost
#         else:
#             self.server = xmlrpclib.Server('http://127.0.0.1:8001')
#
#         #register for shutdown
#         atexit.register(self.Stop)
#
#         #start the thread
#         self.start()
#
#     def Stop(self):
#         self.logger.info('Q315_Monitor::Stop')
#         self.Go = False
#
#     def run(self):
#         self.logger.debug('Q315_Monitor::run')
#         #check xf_status 5 times per second, marcollect once
#         while (1):
#             #break out if stop is requested
#             if not self.Go:
#                 self.logger.debug('Stopping ADSC Monitor')
#                 break
#             try:
#                 marcollect_dict = self.server.GetMarcollectData()
#                 if (marcollect_dict):
#                     self.logger.debug("MARCOLLECT CHANGED")
#                     if self.notify:
#                         self.notify(("ADSC RUN STATUS CHANGED", marcollect_dict))
#             except:
#                 self.logger.exception('Q315_Monitor:: ERROR! - most likely there is not rapd_adscserver running where you are pointed')
#                 self.Go = False
#                 if self.reconnect:
#                     self.reconnect()
#                 break
#
#             for i in range(5):
#                 try:
#                     status_dict = self.server.GetXFStatusData()
#                     if (status_dict):
#                         self.logger.debug("XF_STATUS CHANGED")
#                         if status_dict['status'] == 'SUCCESS':
#                             if self.notify:
#                                 self.notify(("IMAGE STATUS CHANGED", status_dict))
#                 except:
#                     self.logger.exception('Q315_Monitor:: ERROR! Error in GetXFStatusData')
#
#                 #wait before checking again
#                 time.sleep(0.2)
#
#         self.logger.debug('Q315_Monitor while loop exited')
#
# class Hf4m_Monitor(threading.Thread):
#     """
#     A new thread which watches a list in redis - mod of Hf4m_Monitor
#     Run from within Model
#     """
#     def __init__(self,beamline='E',notify=None,reconnect=None,logger=None):
#         if (logger):
#             logger.info('Hf4m_Monitor::__init__  beamline: %s' % beamline)
#         else:
#             print 'Hf4m_Monitor::__init__  beamline: %s' % beamline
#         #initialize the thread
#         threading.Thread.__init__(self)
#
#         #passed-in variables
#         self.notify    = notify
#         self.reconnect = reconnect
#         self.beamline  = beamline
#         self.logger    = logger
#
#         self.red = None
#
#         #for stopping/starting
#         self.Go = True
#
#         #register for shutdown
#         atexit.register(self.Stop)
#
#         #start the thread
#         self.start()
#
#     def Stop(self):
#         if (self.logger):
#             self.logger.info('Hf4m_Monitor::Stop')
#         else:
#             print 'Hf4m_Monitor::Stop'
#         self.Go = False
#
#     def run(self):
#         if (self.logger):
#             self.logger.debug('Hf4m_Monitor::run')
#         else:
#             print 'Hf4m_Monitor::run'
#         #try:
#         #set the adsc server
#         if self.beamline in secrets.keys():
#             if self.logger:
#                 self.logger.debug('Attempting to connect to Redis database at at %s' % secrets[self.beamline]['remote_redis_ip'])
#             else:
#                 print 'Attempting to connect to Redis database at at %s' % secrets[self.beamline]['remote_redis_ip']
#             self.red = pysent.RedisManager(sentinel_host="remote.nec.aps.anl.gov",
# 									       sentinel_port=26379,
# 									       master_name="remote_master")
#         #if the assigned beamline is not in the settings, use the localhost
#         else:
#             self.red = pysent.RedisManager(sentinel_host="remote.nec.aps.anl.gov",
# 									       sentinel_port=26379,
# 									       master_name="remote_master")
#
#         #except:
#         #    if (self.logger):
#         #        self.logger.debug('Exception in starting Hf4m_Monitor::run')
#         #    else:
#         #        print 'Exception in starting Hf4m_Monitor::run'
#             time.sleep(5)
#             self.run()
#
#         # Watch the imagelist
#         image_list = "images_collected_"+self.beamline
#         if self.logger:
#             self.logger.debug('Hf4m_Monitor::Start listening')
#         else:
#             print 'Hf4m_Monitor::Start listening'
#         while (self.Go):
#             try:
#                 #try to pop the oldest image off the list
#                 new_image = self.red.rpop(image_list)
#                 if (new_image):
#                     if self.logger:
#                         self.logger.debug('Hf4m_Monitor::new image %s' % new_image)
#                     else:
#                         print 'Hf4m_Monitor::new image %s' % new_image
#                     if (new_image.endswith('.cbf')):
#                         self.notify(("NEW HF4M IMAGE", new_image))
#             except:
#                 if self.logger:
#                     self.logger.exception('Exception in while loop')
#                 else:
#                     print 'Exception in while loop'
#                 time.sleep(5)
#
#             #slow it down a little
#             time.sleep(0.1)


###############################################################################

def Q315ReadHeader(image, run_id=None, place_in_run=None, logger=False):
    """
    Given a full file name for an ADSC image (as a string), read the header and
    return a dict with all the header info
    """
    if logger:
        logger.debug('Q315ReadHeader %s' % image)

    #item:(pattern,transform)
    header_items = { 'header_bytes' : ("^HEADER_BYTES=\s*(\d+)\;", lambda x: int(x)),
                     'dim'          : ("^DIM=\s*(\d+)\;", lambda x: int(x)),
                     'byte_order'   : ("^BYTE_ORDER=\s*([\w_]+)\;", lambda x: str(x)),
                     'type'         : ("^TYPE=\s*([\w_]+)\;", lambda x: str(x)),
                     'size1'        : ("^SIZE1=\s*(\d+)\;", lambda x: int(x)),
                     'size2'        : ("^SIZE2=\s*(\d+)\;", lambda x: int(x)),
                     'pixel_size'   : ("^PIXEL_SIZE=\s*([\d\.]+)\;", lambda x: float(x)),
                     'bin'          : ("^BIN=\s*(\w*)\;", lambda x: str(x)),
                     'adc'          : ("^ADC=\s*(\w+)\;", lambda x: str(x)),
                     'detector_sn'  : ("^DETECTOR_SN=\s*(\d+)\;", lambda x: int(x)),
                     'collect_mode' : ("^COLLECT_MODE=\s*(\w*)\;", lambda x: str(x)),
                     'beamline'     : ("^BEAMLINE=\s*(\w+)\;", lambda x: str(x)),
                     'date'         : ("^DATE=\s*([\w\d\s\:]*)\;", date_adsc_to_sql),
                     'time'         : ("^TIME=\s*([\d\.]+)\;", lambda x: float(x)),
                     'distance'     : ("^DISTANCE=\s*([\d\.]+)\;", lambda x: float(x)),
                     'osc_range'    : ("^OSC_RANGE=\s*([\d\.]+)\;", lambda x: float(x)),
                     'phi'          : ("^PHI=\s*([\d\.]+)\;", lambda x: float(x)),
                     'osc_start'    : ("^OSC_START=\s*([\d\.]+)\;", lambda x: float(x)),
                     'twotheta'     : ("^TWOTHETA=\s*([\d\.]+)\;", lambda x: float(x)),
                     'thetadistance': ("^THETADISTANCE=\s*([\d\.]+)\;", lambda x: float(x)),
                      #'axis'         : ("^AXIS=\s*(\w+)\;", lambda x: str(x)),
                     'wavelength'   : ("^WAVELENGTH=\s*([\d\.]+)\;", lambda x: float(x)),
                     'beam_center_x': ("^BEAM_CENTER_X=\s*([\d\.]+)\;", lambda x: float(x)),
                     'beam_center_y': ("^BEAM_CENTER_Y=\s*([\d\.]+)\;", lambda x: float(x)),
                     'transmission' : ("^TRANSMISSION=\s*([\d\.]+)\;", lambda x: float(x)),
                     'puck'         : ("^PUCK=\s*(\w+)\;", lambda x: str(x)),
                     'sample'       : ("^SAMPLE=\s*([\d\w]+)\;" , lambda x: str(x)),
                     'ring_cur'     : ("^RING_CUR=\s*([\d\.]+)\;", lambda x: float(x)),
                     'ring_mode'    : ("^RING_MODE=\s*(.*)\;", lambda x: str(x)),
                     'aperture'     : ("^MD2_APERTURE=\s*(\d+)\;", lambda x: int(x)),
                     'period'       : ("^# Exposure_period\s*([\d\.]+) s", lambda x: float(x)),
                     'count_cutoff' : ("^# Count_cutoff\s*(\d+) counts", lambda x: int(x))}

    count = 0
    while (count < 10):
        try:
            rawdata = open(image,"rb").read()
            headeropen = rawdata.index("{")
            headerclose= rawdata.index("}")
            header = rawdata[headeropen+1:headerclose-headeropen]
            break
            #print header
        except:
            count +=1
            if logger:
                logger.exception('Error opening %s' % image)
            time.sleep(0.1)


    try:
        #tease out the info from the file name
        base = os.path.basename(image).rstrip(".img")
        #the parameters
        parameters = {'fullname'     : image,
                      'detector'     : 'ADSC-Q315',
                      'directory'    : os.path.dirname(image),
                      'image_prefix' : "_".join(base.split("_")[0:-2]),
                      'run_number'   : int(base.split("_")[-2]),
                      'image_number' : int(base.split("_")[-1]),
                      'axis'         : 'omega',
                      'run_id'       : run_id,
                      'place_in_run' : place_in_run}

        for label,pat in header_items.iteritems():
            pattern = re.compile(pat[0], re.MULTILINE)
            matches = pattern.findall(header)
            if len(matches) > 0:
                parameters[label] = pat[1](matches[-1])
            else:
                parameters[label] = None

        #if twotheta is in use, distance = twothetadist
        try:
            if (parameters['twotheta'] > 0 and parameters['thetadistance'] > 100):
                parameters['distance'] = parameters['thetadistance']

        except:
            if logger:
                logger.exception('Error handling twotheta for image %s' % image)

        #look for bad text in certain entries NECAT-code
        try:
            json.dumps(parameters['ring_mode'])
        except:
            parameters['ring_mode'] = 'Error'

        #return parameters to the caller
        return(parameters)

    except:
        if logger:
            logger.exception('Error reading the header for image %s' % image)

"""
This is the current header for HF4M AFAIK 2015.02.13

###CBF: VERSION 1.5, CBFlib v0.7.8 - Pixel Array detectors

data_1423862639_

_array_data.header_convention "ADSC_1.2"
_array_data.header_contents
;
# Detector: ADSC HF-4M, S/N H401,
# Pixel_size 0.00015 m x 0.00015 m
# Silicon sensor, thickness 0.000500 m
# Exposure_time 0.500000 s
# Exposure_period 0.500000 s
# Fri_Feb_13_13:23:52_2015
# Count_cutoff 200000000 counts
# N_excluded_pixels = 3900
# Wavelength 0.979100 A
# Detector_distance 0.250000 m
# Beam_xy (1231.50, 1263.50) pixels
# Start_angle 4.0000 deg.
# Angle_increment 0.5000 deg.
# Phi 4.0000 deg.
# Filter_Transmission 0.9988
# Source APS
# Administration NE-CAT
# Beam_Line ID_24_E
# Sample_Position J1
# Filter_Transmission 0.9988
# Source APS
# Administration NE-CAT
# Beam_Line ID_24_E
# Sample_Position J1
;

_array_data.data
;
--CIF-BINARY-FORMAT-SECTION--
"""

months = { 'Jan':'01',
           'Feb':'02',
           'Mar':'03',
           'Apr':'04',
           'May':'05',
           'Jun':'06',
           'Jul':'07',
           'Aug':'08',
           'Sep':'09',
           'Oct':'10',
           'Nov':'11',
           'Dec':'12' }

def Hf4mReadHeader(image,mode=None,run_id=None,place_in_run=None,logger=False):
    """
    Given a full file name for a Piltus image (as a string), read the header and
    return a dict with all the header info
    """
    # print "Hf4mReadHeader %s" % image
    if logger:
        logger.debug('Hf4mReadHeader %s' % image)
    else:
        print 'Hf4mReadHeader %s' % image

    def mmorm(x):
        d = float(x)
        if (d < 2):
            return(d*1000)
        else:
            return(d)

    #item:(pattern,transform)
    header_items = { 'detector_sn'  : ("S\/N ([\w\d\-]*)\s*", lambda x: str(x)),
                     'date'         : ("^# (\w{3}_\w{3}_\d+_\d+\:\d+\:\d+_\d+)\s*", lambda x: str(x).replace("__","_")),
                     'pixel_size'   : ("^# Pixel_size\s*([\d\.]+) m.*", lambda x: float(x)*1000),  # Convert to mm
                     'time'         : ("^# Exposure_time\s*([\d\.]+) s", lambda x: float(x)),
                     'period'       : ("^# Exposure_period\s*([\d\.]+) s", lambda x: float(x)),
                     'count_cutoff' : ("^# Count_cutoff\s*(\d+) counts", lambda x: int(x)),
                     'wavelength'   : ("^# Wavelength\s*([\d\.]+) A", lambda x: float(x)),
                     'distance'     : ("^# Detector_distance\s*([\d\.]+) m",mmorm),
	                 'transmission' : ("^# Filter_Transmission\s*([\d\.]+)", lambda x: float(x)),
                     'osc_start'    : ("^# Start_angle\s*([\d\.]+)\s*deg", lambda x: float(x)),
                     'osc_range'    : ("^# Angle_increment\s*([\d\.]*)\s*deg", lambda x: float(x)),
                     'twotheta'     : ("^# Detector_2theta\s*([\d\.]*)\s*deg", lambda x: float(x))}

    count = 0
    while (count < 10):
    	try:
            rawdata = open(image,"rb").read(1024)
            headeropen = 0
            headerclose= rawdata.index("--CIF-BINARY-FORMAT-SECTION--")
            header = rawdata[headeropen:headerclose]
            break
        except:
            count +=1
            if logger:
                logger.exception('Error opening %s' % image)
            else:
                print 'Error opening %s' % image
            time.sleep(0.1)

    try:
        #tease out the info from the file name
        base = os.path.basename(image).rstrip(".cbf")

        parameters = {'date'         : "Fri_Feb_13_13:23:52_2015",
                      'fullname'     : image,
                      'detector'     : 'HF4M',
                      'directory'    : os.path.dirname(image),
                      'image_prefix' : "_".join(base.split("_")[0:-2]),
                      'run_number'   : int(base.split("_")[-2]),
                      'image_number' : int(base.split("_")[-1]),
                      'axis'         : 'omega',
                      'collect_mode' : mode,
                      'run_id'       : run_id,
                      'place_in_run' : place_in_run,
                      'size1'        : 2100,
                      'size2'        : 2290,
                      'twotheta'     : 0.0}

        for label,pat in header_items.iteritems():
            # print label
            pattern = re.compile(pat[0], re.MULTILINE)
            matches = pattern.findall(header)
            if len(matches) > 0:
                parameters[label] = pat[1](matches[-1])
            else:
                parameters[label] = None

        # Convert date to something usable
        # Fri_Feb_13_13:23:52_2015 >> 2015_02_13T13:23:52
        try:
          split_date = parameters['date'].split('_')
          mo = months[split_date[1]]
          date = '%s_%s_%sT%s' % (split_date[4],mo,split_date[2],split_date[3])
          parameters['date'] = date
        except:
          parameters['date'] = "2015_02_13T13:23:52"

        return(parameters)

    except:
        if logger:
            logger.exception('Error reading the header for image %s' % image)
        else:
            print 'Error reading the header for image %s' % image




if __name__ == "__main__":

    """
    #If started on the command line, the header for the input file will be parsed and printed
    #print sys.argv[1]
    a = Q315ReadHeader("images/raster_snap_test_1_001.img")
    print_dict(a)
    """

    """
    #If started on the command line, run the AdscMonitor on the loclahost
    #set up logging
    LOG_FILENAME = '/tmp/rapd_adsc.log'
    # Set up a specific logger with our desired output level
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=100000, backupCount=5)
    #add a formatter
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('RAPD_ADSC.__main__')

    M= Q315_Monitor(beamline='Z',notify=None,reconnect=None,logger=logger)
    """

    """
    #testing
    #Test Hf4m_Monitor
    def notify(input):
        print input
    P = Hf4m_Monitor(beamline='E',notify=notify,reconnect=None,logger=None)
    """


    #Test the header reading
    test_image = "/gpfs9/users/harvard/Gaudet_E_1100/images/LBane/snaps/RG006_15_PAIR_0_0004.cbf"
    header = Hf4mReadHeader(test_image)
    import pprint
    pp = pprint.PrettyPrinter()
    pp.pprint(header)

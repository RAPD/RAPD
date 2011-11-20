__author__ = "Frank Murphy"
__copyright__ = "Copyright 2009,2010,2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2009/07/08"

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
import sys
import json
import logging, logging.handlers
import xmlrpclib
import atexit
from rapd_site import secret_settings as secrets
from rapd_utils import print_dict, date_adsc_to_sql

class ADSC_Monitor(threading.Thread):
    """
    Start a new thread which looks for changes via the server resideing on the
    beamline data collection computer running adsc control software
    Run from within Model via beamline_specific.py
    """
    def __init__(self,beamline='C',notify=None,reconnect=None,logger=None):
        logger.info('ADSC_Monitor::__init__  beamline: %s' % beamline)
        
        #initialize the thread
        threading.Thread.__init__(self)
        
        #passed-in variables
        self.notify    = notify
        self.reconnect = reconnect
        self.beamline  = beamline
        self.logger    = logger
        
        #for stopping/starting
        self.Go = True
        
        #The modification times
        self.xf_time  = 0
        self.mar_time = 0
            
        #set the adsc server
        if beamline in secrets.keys():
            self.logger.debug('Attmepting to conect to adsc monitor at %s' % secrets[beamline]['adsc_server'])
            self.server = xmlrpclib.Server(secrets[beamline]['adsc_server'])
            print self.server
        #if the assigned beamline is not in the settings, use the localhost
        else:
            self.server = xmlrpclib.Server('http://127.0.0.1:8001')
        
        #register for shutdown
        atexit.register(self.Stop)
        
        #start the thread
        self.start()
        
    def Stop(self):
        self.logger.info('ADSC_Monitor::Stop')
        self.Go = False
        
    def run(self):
        self.logger.debug('ADSC_Monitor::run')
        #check xf_status 5 times per second, marcollect once
        while (1):
            #break out if stop is requested
            if not self.Go:
                self.logger.debug('Stopping ADSC Monitor')
                break
            try:
                marcollect_dict = self.server.GetMarcollectData()
                if (marcollect_dict):
                    self.logger.debug("MARCOLLECT CHANGED")
                    if self.notify:
                        self.notify(("ADSC RUN STATUS CHANGED", marcollect_dict))
            except:
                self.logger.exception('ADSC_Monitor:: ERROR! - most likely there is not rapd_adscserver running where you are pointed')
                self.Go = False
                if self.reconnect:
                    self.reconnect()
                break
                
            for i in range(5):   
                try: 
                    status_dict = self.server.GetXFStatusData()
                    if (status_dict):
                        self.logger.debug("XF_STATUS CHANGED")
                        if status_dict['status'] == 'SUCCESS':
                            if self.notify:
                                self.notify(("IMAGE STATUS CHANGED", status_dict))
                except:
                    self.logger.exception('ADSC_Monitor:: ERROR! Error in GetXFStatusData') 
                
                #wait before checking again
                time.sleep(0.2)
        
        self.logger.debug('ADSC_Monitor while loop exited')
        
        
        
###############################################################################
    
def ReadHeader(image,logger=False):
    """
    Given a full file name for an ADSC image (as a string), read the header and
    return a dict with all the header info 
    """
    if logger:
        logger.debug('ReadHeader %s' % image)
        
    header_items = ['HEADER_BYTES',
                    'DIM',
                    'BYTE_ORDER',
                    'TYPE',
                    'SIZE1',
                    'SIZE2',
                    'PIXEL_SIZE',
                    'BIN',
                    'ADC',
                    'DETECTOR_SN',
                    'COLLECT_MODE',
                    'BEAMLINE',
                    'DATE',
                    'TIME',
                    'DISTANCE',
                    'OSC_RANGE',
                    'PHI',
                    'OSC_START',
                    'TWOTHETA',
                    'THETADISTANCE',
                    'TWOTHETADIST',
                    'AXIS',
                    'WAVELENGTH',
                    'BEAM_CENTER_X',
                    'BEAM_CENTER_Y',
                    'TRANSMISSION',
                    'PUCK',
                    'SAMPLE',
                    'RING_CUR',
                    'RING_MODE',
                    'MD2_APERTURE',
                    'MD2_PRG_EXP',
                    'MD2_NET_EXP',
                    'CREV',
                    'CCD',
                    'ACC_TIME',
                    'UNIF_PED',
                    'IMAGE_PEDESTAL',
                    'CCD_IMAGE_SATURATION',
                    'COLLECT_MODE']
    try:
        rawdata = open(image,"rb").read()
        headeropen = rawdata.index("{")
        headerclose= rawdata.index("}")
        header = rawdata[headeropen+1:headerclose-headeropen]
    except:
        if logger:
            logger.exception('Error opening %s' % image)
    
    try:    
        #give zeroed values for items that may be in some headers but not others
        parameters = { 'transmission': 0,
                       'beamline'    : 0,
                       'puck'        : 0,
                       'sample'      : 0,
                       'ring_cur'    : 0,
                       'ring_mode'   : 0,
                       'md2_aperture': 0,
                       'md2_prg_exp' : 0,
                       'md2_net_exp' : 0,
                       'acc_time'    : 0,
                       'flux'        : 0,
                       'beam_size_x' : 0,
                       'beam_size_y' : 0,
                       'gauss_x'     : 0,
                       'gauss_y'     : 0,
                       'thetadistance': 0 }
        
        for item in header_items:
            pattern = re.compile('^'+item+'='+r'(.*);', re.MULTILINE)
            matches = pattern.findall(header)
            if len(matches) > 0:
                parameters[item.lower()] = str(matches[-1])
            else:
                parameters[item.lower()] = '0'
                
        #Transform the adsc date to mysql
        parameters['date'] = date_adsc_to_sql(parameters['date'])
        
        #if twotheta is in use, distance = twothetadist
        try:
            if ( float(parameters['twotheta']) > 0.0 and float(parameters['thetadistance']) > 100.0):
                parameters['distance'] = parameters['thetadistance']
            if ( float(parameters['twotheta']) > 0.0 and float(parameters['twothetadist']) > 100.0):
                parameters['distance'] = parameters['twothetadist']
        except:
            if logger:
                logger.exception('Error handling twotheta for image %s' % image) 
        
        #look for bad text in certain entries NECAT-code
        try:
            json.dumps(parameters['ring_mode'])
        except:
            parameters['ring_mode'] = 'Error'
        
        #return the parameters fro the header
        return(parameters)
    
    except:
        if logger:
            logger.exception('Error reading the header for image %s' % image) 
    
if __name__ == "__main__":
    
    #If started on the command line, the header for the input file will be parsed and printed
    print sys.argv[1]
    a = ReadHeader(sys.argv[1])
    print_dict(a)
    
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
    
    M= ADSC_Monitor(beamline='Z',notify=None,reconnect=None,logger=logger)
    """

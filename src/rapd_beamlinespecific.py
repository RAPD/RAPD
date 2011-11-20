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
rapd_beamlinespecific has a number of functions that need to overloaded for
each specific beamline

This should serve as the nexus for customizing rapd to your site
"""
#
# The default settings for each beamline; Your modifications of rapd_site.py should
# have created the correct information in the imports here
#
from rapd_site import beamline_settings, secret_settings, secret_settings_general
import threading
import os
import time

#the extra time the RunWatcher will wait for an image file to appear before declaring 
#an aborted run
image_wait = 20

#
# Methods for watching for new run & image information
# 
# RAPD is developed with an ADSC CCD detector system
# You will have to create your own ImageMonitor and import it here
# if you do not use ADSC detectors
#
from rapd_adsc import ADSC_Monitor
from rapd_console import ConsoleRunMonitor
from rapd_site import NecatDetermineFlux as DetermineFlux
from rapd_site import NecatDetermineImageType as DetermineImageType
#
# Methods for connecting to the beamline control system
#
# RAPD is developed with CONSOLE as the beamline control system (by Malcolm Capel)
# This is currently use to monitor for aborts during data collection and to 
# get information in case of errors in the header of the image
#
from rapd_console import Console_RPC as BeamlineConnect
#BeamlineMonitor = False
#
# Methods for deriving experimental information from the image
#
# RAPD is developed with ADSC detector with some custom header manipulations
# This routine works for NE-CAT headers, but these are most likely customized
# so take a look
#
from rapd_adsc import ReadHeader as GetImageHeader
#
# Methods for negotiating the filesystem
#
#from rapd_site import GetUserDir         as GetUserDir
from rapd_site import GetDataRootDir     as GetDataRootDir 
from rapd_site import TransferToUI       as TransferToUI
from rapd_site import TransferToBeamline as TransferToBeamline
from rapd_site import CopyToUser         as CopyToUser
from rapd_site import TransferPucksToBeamline as TransferPucksToBeamline
from rapd_site import TransferMasterPuckListToBeamline as TransferMasterPuckListToBeamline


class ImageMonitor(threading.Thread):
    """
    The thread for monitoring the beamline for new images.
    Runs an ADSC monitor which watches xf_status and
    CONSOLE monitor which watches NE-CAT's control software.
    """
    def __init__(self,beamline='C',notify=None,logger=None):
        logger.info('ImageMonitor::__init__')
        
        #init the thread
        threading.Thread.__init__(self)

        self.beamline = beamline
        self.notify = notify
        self.logger = logger
        
        self.adsc_monitor_reconnect_attempts = 0
        self.console_monitor_reconnect_attempts = 0
        
        self.start()
        
    def run(self):
        self.logger.debug('ImageMonitor::run')
        
        #The Image monitor which checks xf_status and marcollect from adsc
        self.ADSC_MONITOR = ADSC_Monitor(beamline = self.beamline,
                                         notify = self.notify,
                                         reconnect = self.ADSC_Reconnect,
                                         logger = self.logger)
         
        #The console monitor which checks marcollect from console
        self.CONSOLE_MONITOR = ConsoleRunMonitor(beamline = self.beamline,
                                                 notify = self.notify,
                                                 reconnect = self.Console_Reconnect,
                                                 logger = self.logger)
    def ADSC_Reconnect(self):
        """
        Reconnection method for the ADSC_MONITOR
        """
        self.adsc_monitor_reconnect_attempts += 1
        self.logger.warning('ImageMonitor::ADSC_Reconnect try %d' % self.adsc_monitor_reconnect_attempts)
        if self.adsc_monitor_reconnect_attempts < 1000:
            self.ADSC_MONITOR = False
            time.sleep(10)
            self.ADSC_MONITOR = ADSC_Monitor(beamline = self.beamline,
                                             notify = self.notify,
                                             reconnect = self.ADSC_Reconnect,
                                             logger = self.logger)
        else:
            self.ADSC_MONITOR = False
            self.logger.warning('Too many ADSC monitor connection attempts - exiting')
            exit()
        
    def Console_Reconnect(self):
        """
        Reconnection method for the CONSOLE_MONITOR
        """
        self.console_monitor_reconnect_attempts += 1
        self.logger.warning('ImageMonitor::Console_Reconnect try %d' % self.console_monitor_reconnect_attempts)
        if self.console_monitor_reconnect_attempts < 1000:
            self.CONSOLE_MONITOR = False
            time.sleep(10)
            self.CONSOLE_MONITOR = ConsoleRunMonitor(beamline = self.beamline,
                                                     notify = self.notify,
                                                     reconnect = self.Console_Reconnect,
                                                     logger = self.logger)
        else:
            self.CONSOLE_MONITOR = False
            self.logger.warning('Too many Console monitor connection attempts - exiting')
            exit() 
        
        
        
class RunWatcher(threading.Thread):
    """
    RunWatcher will monitor for an abort while a run is being collected by
    querying the self.BEAMLINEMONITOR
    """
    def __init__(self,beamline,run_dict,alert,logger):
        logger.info('RunWatcher::__init__')
        
        #initialize the thread
        threading.Thread.__init__(self)
        
        #storing the passed-in variables
        self.beamline = beamline
        self.run_dict = run_dict
        self.ALERT = alert
        self.logger = logger
        self.run_id = run_dict['run_id']
        
        #flag for integrating
        self.INTEGRATING = False
        
        #run flag
        self.GO = True
        self.RESTART = False
        
        #now start
        self.start()
        
    def run(self):
        self.logger.debug('RunWatcher::run')  
        
        image_count = self.run_dict['start']
        image = os.path.join(self.run_dict['directory'],'_'.join((self.run_dict['image_prefix'],str(self.run_dict['run_number']),str(image_count).zfill(3)))+'.img')
        
        while(self.GO and (image_count < self.run_dict['total']+self.run_dict['start']-1)):
            #Only wait frame time + x seconds for frame            
            counter = 0
            while(counter < self.run_dict['time']+image_wait):
                if (os.path.exists(image)):
                    counter = 0 
                    image_count += 1
                    image = os.path.join(self.run_dict['directory'],'_'.join((self.run_dict['image_prefix'],str(self.run_dict['run_number']),str(image_count).zfill(3)))+'.img')
                    break
                else:
                    counter += 1
                    time.sleep(1)
            #the loop has been exited as counter > time alotted
            else:
                self.logger.debug('RunWatcher cannot find image: %s'%image)
                self.ALERT(run_id=self.run_id)
                break
     
     
    def Stop(self):
        self.logger.debug('RunWatcher::Stop')
        self.GO = False

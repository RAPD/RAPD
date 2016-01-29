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

__created__ = "2009-11-22"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"


import atexit
from collections import deque
import datetime
import logging
import os
import threading
import time

# from rapd_cluster import PerformAction
# from rapd_beamlinespecific import *
# from rapd_site import TransferPucksToBeamline, TransferMasterPuckListToBeamline
# import paramiko
# from rapd_console import ConsoleConnect as BeamlineConnect

class CloudMonitor(threading.Thread):
    """
    Monitors a database, organizes requests and then calls PerformAction
    to run the process on the cluster.
    """

    # Place to store requests
    request_queue = deque()

    #for stopping
    Go = True

    def __init__(self,
                 database,
                 settings,
                 reply_settings,
                 interval=30.):
        """
        Save passed variables, perform some startup and initiate thread

        Keyword arguments:
        database -- Adapter to the core database
        settings - rapd_site.secret_settings for the beamline
        reply_settings - tuple of (ip_address,port_number) for the ControllerServer which
                         listens for replies
        interval - the time in seconds between checks of the cloud
        logger - logger instance - required

        """

        self.logger = logging.getLogger("RAPDLogger")
        self.logger.info("CloudMonitor::__init__")

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.database = database
        self.settings = settings
        self.reply_settings = reply_settings
        self.interval = interval

        #register for shutdown
        atexit.register(self.stop)

        self.start()

    def stop(self):
        """
        Bring the cloud monitor loop to a halt.
        """

        self.logger.debug('Stopping')
        self.Go = False

    def run(self):
        """
        The thread starts running here.
        """

        self.logger.debug('CloudMonitor::run')

        # Save some space
        settings = self.settings

        #run the monitor as a loop
        while self.Go:
            #
            # The following section is for cloud-based beamline control events
            #
            # Minikappa requests
            if settings["CLOUD_MINIKAPPA"]:
                # Check the database
                minikappa_request = self.database.getMinikappaRequest()
                if (minikappa_request):
                    self.logger.debug(minikappa_request)
                    tmp = MinikappaHandler(request=minikappa_request,
                                           database=self.database)

            # Data collection run parameters request
            if settings["CLOUD_DATA_COLLECTION_PARAMS"]:
                datacollection_request = self.database.getDatacollectionRequest()
                if (datacollection_request):
                    self.logger.debug(datacollection_request)
                    tmp = DatacollectionHandler(request=datacollection_request,
                                                database=self.database)

            #
            # The following section is for cloud-based events
            #

            #query for new cloud requests
            request = self.DATABASE.getCloudRequest()
            #now look through the request
            if request:

                #Puck Request does not pass IP, so check it first.
                if request['request_type'] == 'setpuck':
                    self.logger.debug('Set Puck Request')
                    self.logger.debug(request)
                    tmp = PuckHandler(request,self.DATABASE,self.Secret_Settings,self.reply_settings,self.logger)

                #Spreadsheet uploading does not pass IP, so check it next.
                #Upon new spreadsheet upload, update the master puck list for console.
                elif request['request_type'] == 'newsheet':
                    self.logger.debug('New Spreadsheet Uploaded.  Change Master Puck List.')
                    self.logger.debug(request)
                    tmp = SheetHandler(request,self.DATABASE,self.Secret_Settings,self.reply_settings,self.logger)

                """
                The following section is for cloud-based events which are IP linked
                """
                #check the current jobs and the maximum allowed
                #if ( (request['ip_address'].startswith(self.Secret_Settings['local_ip_prefix']))):  # or (self.DATABASE.getCloudClearance())):
                #process the request
                #we have a download request
                if request['request_type'].startswith('down'):
                    self.logger.debug('Download request')
                    self.logger.debug(request)
                    tmp = DownloadHandler(request,self.DATABASE,self.Secret_Settings,self.reply_settings,logger=self.logger)

                #Reprocess request
                elif request['request_type'] == 'reprocess':
                    self.logger.debug('Reprocess request')
                    self.logger.debug(request)
                    tmp = ReprocessHandler(request,self.DATABASE,self.Secret_Settings,self.reply_settings,self.logger)

                #STAC Request
                elif request['request_type'] == 'stac':
                    self.logger.debug('STAC Request')
                    self.logger.debug(request)
                    tmp = StacHandler(request,self.DATABASE,self.Secret_Settings,self.reply_settings,self.logger)

                #SAD request
                elif (request['request_type'] == 'start-sad'):
                    self.logger.debug('SAD Request')
                    self.logger.debug(request)
                    tmp = SadHandler(request=request,
                                     database=self.DATABASE,
                                     settings=self.Secret_Settings,
                                     reply_settings=self.reply_settings,
                                     logger=self.logger)

                #MAD request
                elif (request['request_type'] == 'start-mad'):
                    self.logger.debug('MAD Request')
                    self.logger.debug(request)
                    tmp = MadHandler(request=request,
                                     database=self.DATABASE,
                                     settings=self.Secret_Settings,
                                     reply_settings=self.reply_settings,
                                     logger=self.logger)

                #MR request
                elif (request['request_type'] == 'start-mr'):
                    self.logger.debug('MR Request')
                    self.logger.debug(request)
                    tmp = MrHandler(request=request,
                                    database=self.DATABASE,
                                    settings=self.Secret_Settings,
                                    reply_settings=self.reply_settings,
                                    logger=self.logger)

                #FastIntegration request
                elif (request['request_type'] == 'start-fastin'):
                    self.logger.debug('FastIntegration Request')
                    self.logger.debug(request)
                    tmp = IntegrationHandler(request=request,
                                             database=self.DATABASE,
                                             settings=self.Secret_Settings,
                                             reply_settings=self.reply_settings,
                                             logger=self.logger)

                #Xia2 request
                elif (request['request_type'] == 'start-xiaint'):
                    self.logger.debug('Xia2 Request')
                    self.logger.debug(request)
                    tmp = IntegrationHandler(request=request,
                                             database=self.DATABASE,
                                             settings=self.Secret_Settings,
                                             reply_settings=self.reply_settings,
                                             logger=self.logger)

                #SimpleMerge Request
                elif request['request_type'] == 'smerge':
                    self.logger.debug('SimpleMerge Request')
                    self.logger.debug(request)
                    tmp = SimpleMergeHandler(request,self.DATABASE,self.Secret_Settings,self.reply_settings,self.logger)
            """
                else:
                    #put the request in the queue
                    self.request_queue.append(request)

                    #increment the queue in the database
                    self.DATABASE.addToCloudQueue()

                    #mark the request as queued
                    self.DATABASE.markCloudRequest(request['cloud_request_id'],'queued')

            #no cloud request, check the queue
            elif (len(self.request_queue) > 0):

                #check for clearance
                if True: #(self.DATABASE.getCloudClearance()):
                    request = self.request_queue.popleft()

                    #decrement the queue in the database
                    self.DATABASE.subtractFromCloudQueue()

                    #we have a download request
                    if request['request_type'].startswith('down'):
                        self.logger.debug('Download request')
                        self.logger.debug(request)
                        tmp = DownloadHandler(request,self.DATABASE,self.Secret_Settings,self.reply_settings,logger=self.logger)

                    #Reprocess request
                    elif request['request_type'] == 'reprocess':
                        self.logger.debug('Reprocess request')
                        tmp = StacHandler(request,self.DATABASE,self.Secret_Settings,self.reply_settings,self.logger,True)
            """
            time.sleep(self.interval)


class MinikappaHandler(threading.Thread):
    """
    Handles the signaling of the beamline with a minikappa setting in a separate thread.
    """

    def __init__(self, request, database):
        """
        Instantiate by saving passed variables and starting the thread.

        request - a dict describing the request
        database - instance of the rapd_database.Database
        """
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.info('MinikappaHandler::__init__')
        self.logger.debug(request)

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request        = request
        self.DATABASE       = database

        self.start()

    def run(self):
        """
        The new thread
        """

        self.logger.debug('MinikappaHandler::run')

        #get the timestamp into console format
        timestamp = self.request['timestamp'].replace('-','/').replace('T','_')[:-3]

        try:
            #send the request to the appropriate Console session
            myBEAMLINEMONITOR = BeamlineConnect(beamline=self.request['beamline'],
                                                logger=self.logger )

            myBEAMLINEMONITOR.PutStac(timestamp=timestamp,
                                             omega=self.request['omega'],
                                             kappa=self.request['kappa'],
                                             phi=self.request['phi'])

            #get rid of myBEAMLINEMONITOR
            myBEAMLINEMONITOR = None

            #mark that the request has been addressed
            self.DATABASE.markMinikappaRequest(self.request['minikappa_id'],'complete')
        except:
            self.logger.debug('Error in connecting to Console')

class PuckHandler(threading.Thread):
    """
    Handles creation of text files listing CrystalIDs for use by Console.
    """

    def __init__(self,request,database,settings,reply_settings,logger=None):
        """
        Instantiate by saving passed variables and starting the thread.

        request - a dict describing the request
        database - instance of the rapd_database.Database
        settings - secret_settings from rapd_site for the beamline
        reply_settings - tuple of (ip_address,port_number) for the ControllerServer which
                         listens for replies
        logger - logger instance

        """

        logger.info('PuckHandler::__init__')
        logger.debug(request)

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request         = request
        self.Secret_Settings = settings
        self.reply_settings  = reply_settings
        self.DATABASE        = database
        self.logger          = logger

        self.start()

    def run(self):
        """
        The thread runs.
        """

        self.logger.debug('PuckHandler::run')

        #get the timestamp into console format
        timestamp = self.request['timestamp'].replace('-','/').replace('T','_')[:-3]

        #mark that the request has been addressed
        self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')

       #Structure the request to the cluster
        if self.request['request_type'] == 'setpuck':
            #figure out what and where to transfer
            beamline = self.request['option1']
            puck_info = self.DATABASE.getSetPuckInfo(self.request['puckset_id'])
            #get CrystalIDs for each puck
            for puck in puck_info:
               if puck_info[puck] == 'None':
                  puck_contents = { puck : 'NULL' }
                  #create the files and send them to the specific beamline
                  TransferPucksToBeamline(beamline,puck_contents)
               else:
                  puck_contentsdict = self.DATABASE.getPuckInfo(puck_info[puck])
                  puck_contentslist = []
                  for crystal in puck_contentsdict:
                      puck_contentslist.append({'CrystalID': crystal['CrystalID'], 'PuckID': crystal['PuckID']})
                      puck_contents = { puck : puck_contentslist }
                  #create the files and send them to the specific beamline
                  TransferPucksToBeamline(beamline,puck_contents)

            #mark that the request has been addressed
            self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'complete')

class SheetHandler(threading.Thread):
    """
    Creates and sends the Master Puck List to console.
    """

    def __init__(self,request,database,settings,reply_settings,logger=None):
        """
        Instantiate by saving passed variables and starting the thread.

        request - a dict describing the request
        database - instance of the rapd_database.Database
        settings - secret_settings from rapd_site for the beamline
        reply_settings - tuple of (ip_address,port_number) for the ControllerServer which
                         listens for replies
        logger - logger instance

        """

        logger.info('SheetHandler::__init__')
        logger.debug(request)

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request         = request
        self.Secret_Settings = settings
        self.reply_settings  = reply_settings
        self.DATABASE        = database
        self.logger          = logger

        self.start()

    def run(self):
        """
        The thread runs.
        """

        self.logger.debug('SheetHandler::run')

        #get the timestamp into console format
        timestamp = self.request['timestamp'].replace('-','/').replace('T','_')[:-3]

        #mark that the request has been addressed
        self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')

        #get the master puck list
        all_pucks = self.DATABASE.getAllPucks(self.Secret_Settings['puck_cutoff'])
        for puck in all_pucks:
            puck.update(select=0)
        beamlines = ['C','E']
        for beamline in beamlines:
            current_pucks = self.DATABASE.getCurrentPucks(beamline)

            #transfer all available pucks and mark selected pucks as 1
            if current_pucks:
                for puck in all_pucks:
                    for chosen in current_pucks[0]:
                        if puck['PuckID'] == current_pucks[0][puck]:
                            puck.update(select=1)

            TransferMasterPuckListToBeamline(beamline, all_pucks)

        #mark that the request has been addressed
        self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'complete')

class DatacollectionHandler(threading.Thread):
    """
    Handles the signaling of the beamline with a datacollection setting in a separate thread.
    """

    def __init__(self,request,database,logger=None):
        logger.info('DatacollectionHandler::__init__')
        logger.debug(request)

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request        = request
        self.DATABASE       = database
        self.logger         = logger

        self.start()

    def run(self):
        self.logger.debug('DatacollectionHandler::run')

        #get the timestamp into console format
        timestamp = self.request['timestamp'].replace('-','/').replace('T','_')[:-3]

        try:
            #send the request to the appropriate Console session
            myBEAMLINEMONITOR = BeamlineConnect(beamline=self.request['beamline'],
                                                logger=self.logger)

            myBEAMLINEMONITOR.PutDatacollectionRedis(timestamp=timestamp,
                                                       omega_start=self.request['omega_start'],
                                                       delta_omega=self.request['delta_omega'],
                                                       number_images=self.request['number_images'],
                                                       time=self.request['time'],
                                                       distance=self.request['distance'],
                                                       transmission=self.request['transmission'],
                                                       kappa=self.request['kappa'],
                                                       phi=self.request['phi'])

            #get rid of myBEAMLINEMONITOR
            myBEAMLINEMONITOR = None

            #mark that the request has been addressed
            self.DATABASE.markDatacollectionRequest(self.request['datacollection_id'],'complete')
        except:
            self.logger.exception('Error connecting to Console in DatacollectionHandler')

class DownloadHandler(threading.Thread):
    """
    Handles the packing and transfer of downloads in a separate thread
    """
    def __init__(self,request,database,settings,reply_settings,logger=None):
        logger.info('DownloadHandler::__init__')
        logger.debug(request)

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request        = request
        self.DATABASE       = database
        self.SecretSettings = settings
        self.reply_settings = reply_settings
        self.logger         = logger

        self.start()

    def run(self):
        self.logger.debug('DownloadHandler::run')

        #mark that the request has been addressed
        self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')

        #Structure the request to the cluster
        if self.request['request_type'] == 'downproc':
            #figure out what and where to transfer
            down_info = self.DATABASE.getDownprocInfo(self.request)
            if (down_info):
                #the fastint pipeline
                if (len(down_info) == 2):
                    #update the request dict
                    self.request['download_file'] = down_info[0]
                    self.request['repr'] = down_info[1]
                    self.request['source_dir']  = False
                    self.request['image_files'] = False
                    self.request['work_dir']  = False
                #the xia2 pipeline
                elif (len(down_info) == 4):
                    source_dir,image_files,work_dir,repr = down_info
                    self.request['download_file'] = False
                    self.request['source_dir']  = source_dir
                    self.request['image_files'] = image_files
                    self.request['work_dir']  = work_dir
                    self.request['repr']  = repr
                #enter the request into cloud_current
                self.DATABASE.addCloudCurrent(self.request)

                #put request in to cluster to compress the image
                PerformAction(('DOWNLOAD',self.request,self.reply_settings),None,self.SecretSettings,self.logger)

            #unsuccessful run, so nothing to download
            else:
                pass
        elif (self.request['request_type'] in ('downsad','downshelx')):
            #figure out what and where to transfer
            down_info = self.DATABASE.getDownSadInfo(self.request)
            self.logger.debug(down_info)
            if (down_info):
                #update the request dict
                self.request['download_file'] = down_info[0]
                self.request['repr'] = down_info[1]
                #enter the request into cloud_current
                self.DATABASE.addCloudCurrent(self.request)
                #put request in to cluster to compress the image
                PerformAction(('DOWNLOAD',self.request,self.reply_settings),None,self.SecretSettings,self.logger)

        # MAD run
        elif (self.request['request_type'] in ('downmad','downmadshelx')):
            #figure out what and where to transfer
            down_info = self.DATABASE.getDownMadInfo(self.request)
            self.logger.debug(down_info)
            if (down_info):
                #update the request dict
                self.request['download_file'] = down_info[0]
                self.request['repr'] = down_info[1]
                #enter the request into cloud_current
                self.DATABASE.addCloudCurrent(self.request)
                #put request in to cluster to compress the image
                PerformAction(('DOWNLOAD',self.request,self.reply_settings),None,self.SecretSettings,self.logger)

        #Download cell analysis result from sad run
        elif (self.request['request_type'] in ('downsadcell',)):
            #figure out what to transfer
            down_info = self.DATABASE.getDownSadCellInfo(self.request)
            if (down_info):
                #update the request dict
                self.request['download_file'] = down_info[0]
                self.request['repr'] = down_info[1]
                #enter the request into cloud_current
                self.DATABASE.addCloudCurrent(self.request)
                #put request in to cluster to compress the image
                PerformAction(('DOWNLOAD',self.request,self.reply_settings),None,self.SecretSettings,self.logger)

        elif (self.request['request_type'] in ('download_mr',)):
            #figure out what to transfer
            down_info = self.DATABASE.getDownMrInfo(self.request)
            if (down_info):
                #update the request dict
                self.request['download_file'] = down_info[0]
                self.request['repr'] = down_info[1]
                #enter the request into cloud_current
                self.DATABASE.addCloudCurrent(self.request)
                #put request in to cluster to compress the image
                PerformAction(('DOWNLOAD',self.request,self.reply_settings),None,self.SecretSettings,self.logger)
        #Download cell analysis from a data analysis of a run
        elif (self.request['request_type'] in ('download_int',)):
            #figure out what to transfer
            down_info = self.DATABASE.getDownIntegrateInfo(self.request)
            if (down_info):
                #update the request dict
                self.request['download_file'] = down_info[0]
                self.request['repr'] = down_info[1]
                #enter the request into cloud_current
                self.DATABASE.addCloudCurrent(self.request)
                #put request in to cluster to compress the image
                PerformAction(('DOWNLOAD',self.request,self.reply_settings),None,self.SecretSettings,self.logger)

class ReprocessHandler(threading.Thread):
    """
    Handles the initialization of reprocessing runs in a separate thread
    """
    def __init__(self,request,database,settings,reply_settings,logger=None):
        logger.info('ReprocessHandler::__init__  %s' % str(request))

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request         = request
        self.DATABASE        = database
        self.SecretSettings  = settings
        self.reply_settings  = reply_settings
        self.logger          = logger

        self.start()

    def run(self):
        self.logger.debug('ReprocessHandler::run')

        #mark that the request has been addressed
        self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')

        #Structure the request to the cluster
        if self.request['request_type'] == 'reprocess':

            #get the settings
            my_settings          = self.DATABASE.getSettings(setting_id=self.request['new_setting_id'])
            original_result_dict = self.DATABASE.getResultById(self.request['original_id'],self.request['original_type'])

            #self.logger.debug(my_settings)
            #self.logger.debug(original_result_dict)

            my_data_root_dir = original_result_dict['data_root_dir']

            #header beam position settings will be overridden sometimes
            if (my_settings['x_beam'] == '0'):
                if self.request['original_type'] == 'single':
                    data =  self.DATABASE.getImageByImageID(image_id=original_result_dict['image_id'])
                elif self.request['original_type'] == 'pair':
                    data =  self.DATABASE.getImageByImageID(image_id=original_result_dict['image1_id'])
                #self.logger.debug(data)
                if (data['calc_beam_center_x'] > 0.0):
                     my_settings['x_beam'] = data['calc_beam_center_x']
                     my_settings['y_beam'] = data['calc_beam_center_y']

            self.logger.debug(my_settings)
            self.logger.debug(original_result_dict)

            if self.request['original_type'] == 'single':

                if self.request['additional_image'] == 0:                                                                                                   #AUTOINDEX
                    self.logger.debug('Single image autoindexing')                                                                                          #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                    data = self.DATABASE.getImageByImageID(original_result_dict['image_id'])                                                                #AUTOINDEX
                    self.logger.debug(data)                                                                                                                 #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                    # Get the correct directory to run in                                                                                                   #AUTOINDEX
                    # We should end up with top_level/2010-05-10/snap_99_001/                                                                               #AUTOINDEX
                    #the top level                                                                                                                          #AUTOINDEX
                    if my_settings['work_dir_override'] == 'False':                                                                                         #AUTOINDEX
                        my_toplevel_dir = os.path.dirname(original_result_dict['summary_short'].split('single')[0])                                         #AUTOINDEX
                    else:                                                                                                                                   #AUTOINDEX
                        my_toplevel_dir = my_settings['work_directory']                                                                                     #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                    #the type level                                                                                                                         #AUTOINDEX
                    my_typelevel_dir = 'single'                                                                                                             #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                    #the date level                                                                                                                         #AUTOINDEX
                    my_datelevel_dir = datetime.date.today().isoformat()                                                                                    #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                    #the lowest level                                                                                                                       #AUTOINDEX
                    my_sub_dir = os.path.basename(data['fullname']).replace('.img','').replace('.cbf','')                                                   #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                    #now join the three levels                                                                                                              #AUTOINDEX
                    my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)                                      #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                    #make sure this is an original directory                                                                                                #AUTOINDEX
                    if os.path.exists(my_work_dir_candidate):                                                                                               #AUTOINDEX
                        #we have already                                                                                                                    #AUTOINDEX
                        self.logger.debug('%s has already been used, will add qualifier' % my_work_dir_candidate)                                           #AUTOINDEX
                        for i in range(1,10000):                                                                                                            #AUTOINDEX
                            if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):                                                                #AUTOINDEX
                                my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))                                                            #AUTOINDEX
                                self.logger.debug('%s will be used for this image' % my_work_dir_candidate)                                             #AUTOINDEX
                                break                                                                                                                       #AUTOINDEX
                            else:                                                                                                                           #AUTOINDEX
                                i += 1                                                                                                                      #AUTOINDEX
                    #now make the candidate the used dir                                                                                                    #AUTOINDEX
                    my_work_dir = my_work_dir_candidate                                                                                                     #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                    #create a representation of the process for display                                                                                     #AUTOINDEX
                    my_repr = my_sub_dir+'.img'                                                                                                             #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                    #add the process to the database to display as in-process                                                                               #AUTOINDEX
                    process_id = self.DATABASE.addNewProcess( type = 'single',                                                                              #AUTOINDEX
                                                              rtype = 'reprocess',                                                                          #AUTOINDEX
                                                              data_root_dir = my_data_root_dir,                                                             #AUTOINDEX
                                                              repr = my_repr )                                                                              #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                    #add the ID entry to the data dict                                                                                                      #AUTOINDEX
                    #Is this used at all?                                                                                                                   #AUTOINDEX
                    data.update( { 'ID' : os.path.basename(my_work_dir),                                                                                    #AUTOINDEX
                                   'process_id' : process_id,                                                                                               #AUTOINDEX
                                   'repr' : my_repr } )                                                                                                     #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                    #now package directories into a dict for easy access by worker class                                                                    #AUTOINDEX
                    my_dirs = { 'work'          : my_work_dir,                                                                                              #AUTOINDEX
                                'data_root_dir' : my_data_root_dir }                                                                                        #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                    #add the request to my_settings so it can be passed on                                                                                  #AUTOINDEX
                    my_settings['request'] = self.request                                                                                                   #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                    #mark that the request has been addressed                                                                                               #AUTOINDEX
                    self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')                                                              #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                    #mark in the cloud_current table                                                                                                        #AUTOINDEX
                    self.DATABASE.addCloudCurrent(self.request)                                                                                             #AUTOINDEX
                                                                                                                                                            #AUTOINDEX
                    #connect to the server and autoindex the single image                                                                                   #AUTOINDEX
                    PerformAction(('AUTOINDEX',my_dirs,data,my_settings,self.reply_settings),my_settings,self.SecretSettings,self.logger)      #AUTOINDEX

                else:
                    self.logger.debug('Pair image autoindexing from singles')                                                                               #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                    #get the data for each image                                                                                                            #AUTOINDEX-PAIR
                    data1 = self.DATABASE.getImageByImageID(original_result_dict['image_id'])                                                               #AUTOINDEX-PAIR
                    data2 = self.DATABASE.getImageByImageID(self.request['additional_image'])                                                               #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                    #get the correct directory to run in                                                                                                    #AUTOINDEX-PAIR
                    # We should end up with top_level/2010-05-10/snap_99_001/                                                                               #AUTOINDEX-PAIR
                    #the top level                                                                                                                          #AUTOINDEX-PAIR
                    if my_settings['work_dir_override'] == 'False':                                                                                         #AUTOINDEX-PAIR
                        if ('/single/' in original_result_dict['work_dir']):                                                                                #AUTOINDEX-PAIR
                            my_toplevel_dir = os.path.dirname(original_result_dict['work_dir'].split('single')[0])                                          #AUTOINDEX-PAIR
                        elif ('/pair/' in original_result_dict['work_dir']):                                                                                #AUTOINDEX-PAIR
                            my_toplevel_dir = os.path.dirname(original_result_dict['work_dir'].split('pair')[0])                                            #AUTOINDEX-PAIR
                    else:                                                                                                                                   #AUTOINDEX-PAIR
                        my_toplevel_dir = my_settings['work_directory']                                                                                     #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                    #the type level                                                                                                                         #AUTOINDEX-PAIR
                    my_typelevel_dir = 'pair'                                                                                                               #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                    #the date level                                                                                                                         #AUTOINDEX-PAIR
                    my_datelevel_dir = datetime.date.today().isoformat()                                                                                    #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                    #the lowest level                                                                                                                       #AUTOINDEX-PAIR
                    my_sub_dir = '_'.join((data1['image_prefix'],str(data1['run_number']),'+'.join((str(data1['image_number']).lstrip('0'),str(data2['image_number']).lstrip('0')))))
                                                                                                                                                            #AUTOINDEX-PAIR
                    #now join the three levels                                                                                                              #AUTOINDEX-PAIR
                    my_work_dir_candidate = os.path.join(my_toplevel_dir,
                                                         my_typelevel_dir,
                                                         my_datelevel_dir,
                                                         my_sub_dir)
                                                                                                                                                            #AUTOINDEX-PAIR
                    #make sure this is an original directory                                                                                                #AUTOINDEX-PAIR
                    if os.path.exists(my_work_dir_candidate):                                                                                               #AUTOINDEX-PAIR
                        for i in range(1,10000):                                                                                                            #AUTOINDEX-PAIR
                            if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):                                                                #AUTOINDEX-PAIR
                                my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))                                                            #AUTOINDEX-PAIR
                                break                                                                                                                       #AUTOINDEX-PAIR
                            else:                                                                                                                           #AUTOINDEX-PAIR
                                i += 1                                                                                                                      #AUTOINDEX-PAIR
                    my_work_dir = my_work_dir_candidate                                                                                                     #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                    #create a representation of the process for display                                                                                     #AUTOINDEX-PAIR
                    my_repr = my_sub_dir+'.img'                                                                                                             #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                    #add the process to the database to display as in-process                                                                               #AUTOINDEX-PAIR
                    process_id = self.DATABASE.addNewProcess( type = 'pair',                                                                                #AUTOINDEX-PAIR
                                                              rtype = 'reprocess',                                                                          #AUTOINDEX-PAIR
                                                              data_root_dir = my_data_root_dir,                                                             #AUTOINDEX-PAIR
                                                              repr = my_repr )                                                                              #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                    #add the ID entry to the data dict                                                                                                      #AUTOINDEX-PAIR
                    #Is this used at all?                                                                                                                   #AUTOINDEX-PAIR
                    data1.update( { 'ID' : os.path.basename(my_work_dir),                                                                                   #AUTOINDEX-PAIR
                                    'process_id' : process_id,                                                                                              #AUTOINDEX-PAIR
                                    'repr' : my_repr } )                                                                                                    #AUTOINDEX-PAIR
                    data2.update( { 'ID' : os.path.basename(my_work_dir),                                                                                   #AUTOINDEX-PAIR
                                    'process_id' : process_id,                                                                                              #AUTOINDEX-PAIR
                                    'repr' : my_repr } )                                                                                                    #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                    #now package directories into a dict for easy access by worker class                                                                    #AUTOINDEX-PAIR
                    my_dirs = { 'work'          : my_work_dir,                                                                                              #AUTOINDEX-PAIR
                                'data_root_dir' : my_data_root_dir }                                                                                        #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                    #add the request to my_settings so it can be passed on                                                                                  #AUTOINDEX-PAIR
                    my_settings['request'] = self.request                                                                                                   #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                    #mark that the request has been addressed                                                                                               #AUTOINDEX-PAIR
                    self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')                                                              #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                    #mark in the cloud_current table                                                                                                        #AUTOINDEX-PAIR
                    self.DATABASE.addCloudCurrent(self.request)                                                                                             #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                    #connect to the server and autoindex the single image                                                                                   #AUTOINDEX-PAIR
                    PerformAction(('AUTOINDEX-PAIR',my_dirs,data1,data2,my_settings,self.reply_settings),my_settings,self.SecretSettings,self.logger)       #AUTOINDEX-PAIR

            elif (self.request['original_type'] == 'pair'):

                self.logger.debug('Pair image autoindexing from pair result')                                                                               #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                #get the data for each image                                                                                                                #AUTOINDEX-PAIR
                data1 = self.DATABASE.getImageByImageID(original_result_dict['image1_id'])                                                                  #AUTOINDEX-PAIR
                data2 = self.DATABASE.getImageByImageID(original_result_dict['image2_id'])                                                                  #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                #get the correct directory to run in                                                                                                        #AUTOINDEX-PAIR
                # We should end up with top_level/2010-05-10/snap_99_001/                                                                                   #AUTOINDEX-PAIR
                #the top level                                                                                                                              #AUTOINDEX-PAIR
                if my_settings['work_dir_override'] == 'False':                                                                                             #AUTOINDEX-PAIR
                    if ('/single/' in original_result_dict['work_dir']):                                                                                    #AUTOINDEX-PAIR
                        my_toplevel_dir = os.path.dirname(original_result_dict['work_dir'].split('single')[0])                                              #AUTOINDEX-PAIR
                    elif ('/pair/' in original_result_dict['work_dir']):                                                                                    #AUTOINDEX-PAIR
                        my_toplevel_dir = os.path.dirname(original_result_dict['work_dir'].split('pair')[0])                                                #AUTOINDEX-PAIR
                else:                                                                                                                                       #AUTOINDEX-PAIR
                    my_toplevel_dir = my_settings['work_directory']                                                                                         #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                #the type level                                                                                                                             #AUTOINDEX-PAIR
                my_typelevel_dir = 'pair'                                                                                                                   #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                #the date level                                                                                                                             #AUTOINDEX-PAIR
                my_datelevel_dir = datetime.date.today().isoformat()                                                                                        #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                #the lowest level                                                                                                                           #AUTOINDEX-PAIR
                my_sub_dir = '_'.join((data1['image_prefix'],str(data1['run_number']),'+'.join((str(data1['image_number']).lstrip('0'),str(data2['image_number']).lstrip('0')))))
                                                                                                                                                            #AUTOINDEX-PAIR
                #now join the three levels                                                                                                                  #AUTOINDEX-PAIR
                my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)                                          #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                #make sure this is an original directory                                                                                                    #AUTOINDEX-PAIR
                if os.path.exists(my_work_dir_candidate):                                                                                                   #AUTOINDEX-PAIR
                    #we have already                                                                                                                        #AUTOINDEX-PAIR
                    for i in range(1,10000):                                                                                                                #AUTOINDEX-PAIR
                        if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):                                                                    #AUTOINDEX-PAIR
                            my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))                                                                #AUTOINDEX-PAIR
                            break                                                                                                                           #AUTOINDEX-PAIR
                        else:                                                                                                                               #AUTOINDEX-PAIR
                            i += 1                                                                                                                          #AUTOINDEX-PAIR
                my_work_dir = my_work_dir_candidate                                                                                                         #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                #create a representation of the process for display                                                                                         #AUTOINDEX-PAIR
                my_repr = my_sub_dir+'.img'                                                                                                                 #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                #add the process to the database to display as in-process                                                                                   #AUTOINDEX-PAIR
                process_id = self.DATABASE.addNewProcess( type = 'pair',                                                                                    #AUTOINDEX-PAIR
                                                          rtype = 'reprocess',                                                                              #AUTOINDEX-PAIR
                                                          data_root_dir = my_data_root_dir,                                                                 #AUTOINDEX-PAIR
                                                          repr = my_repr )                                                                                  #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                #add the ID entry to the data dict                                                                                                          #AUTOINDEX-PAIR
                #Is this used at all?                                                                                                                       #AUTOINDEX-PAIR
                data1.update( { 'ID' : os.path.basename(my_work_dir),                                                                                       #AUTOINDEX-PAIR
                                'process_id' : process_id,                                                                                                  #AUTOINDEX-PAIR
                                'repr' : my_repr } )                                                                                                        #AUTOINDEX-PAIR
                data2.update( { 'ID' : os.path.basename(my_work_dir),                                                                                       #AUTOINDEX-PAIR
                                'process_id' : process_id,                                                                                                  #AUTOINDEX-PAIR
                                'repr' : my_repr } )                                                                                                        #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                #now package directories into a dict for easy access by worker class                                                                        #AUTOINDEX-PAIR
                my_dirs = { 'work'          : my_work_dir,                                                                                                  #AUTOINDEX-PAIR
                            'data_root_dir' : my_data_root_dir }                                                                                            #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                #add the request to my_settings so it can be passed on                                                                                      #AUTOINDEX-PAIR
                my_settings['request'] = self.request                                                                                                       #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                #mark that the request has been addressed                                                                                                   #AUTOINDEX-PAIR
                self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')                                                                  #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                #mark in the cloud_current table                                                                                                            #AUTOINDEX-PAIR
                self.DATABASE.addCloudCurrent(self.request)                                                                                                 #AUTOINDEX-PAIR
                                                                                                                                                            #AUTOINDEX-PAIR
                #connect to the server and autoindex the single image                                                                                       #AUTOINDEX-PAIR
                PerformAction(('AUTOINDEX-PAIR',my_dirs,data1,data2,my_settings,self.reply_settings),my_settings,self.SecretSettings,self.logger)           #AUTOINDEX-PAIR

class StacHandler(threading.Thread):
    """
    Handles the initialization of reprocessing runs in a separate thread
    """
    def __init__(self,request,database,settings,reply_settings,logger=None):
        logger.info('StacHandler::__init__  %s' % str(request))

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request         = request
        self.DATABASE        = database
        self.SecretSettings  = settings
        self.reply_settings  = reply_settings
        self.logger          = logger

        self.start()

    def run(self):
        self.logger.debug('StacHandler::run')

        #mark that the request has been addressed
        self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')

        #Structure the request to the cluster
        if self.request['request_type'] == 'stac':

            #get the settings
            my_settings          = self.DATABASE.getSettings(setting_id=self.request['new_setting_id'])
            original_result_dict = self.DATABASE.getResultById(self.request['original_id'],self.request['original_type'])
            my_data_root_dir     = original_result_dict['data_root_dir']


            if self.request['option1'] == 'multi':
                my_reference_result_dict = self.DATABASE.getResultById(self.request['result_id'],'integrate')
                self.request['correct.lp'] = os.path.join(os.path.dirname(my_reference_result_dict['xds_log']),'xds_lp_files','CORRECT.LP')
                self.request['dataset_repr'] = my_reference_result_dict['repr']
            else:
                self.request['correct.lp'] = None
                self.request['dataset_repr'] = None

            #generate some debugging info
            self.logger.debug(my_settings)
            self.logger.debug(original_result_dict)

            if self.request['original_type'] == 'single':

                self.logger.debug('STAC Single image autoindexing')                                                                                      #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                data = self.DATABASE.getImageByImageID(original_result_dict['image_id'])                                                                #AUTOINDEX
                self.logger.debug(data)                                                                                                                 #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                # Get the correct directory to run in                                                                                                   #AUTOINDEX
                # We should end up with top_level/2010-05-10/snap_99_001/                                                                               #AUTOINDEX
                #the top level                                                                                                                          #AUTOINDEX
                if my_settings['work_dir_override'] == 'False':                                                                                         #AUTOINDEX
                    my_toplevel_dir = os.path.dirname(original_result_dict['summary_short'].split('single')[0])                                         #AUTOINDEX
                else:                                                                                                                                   #AUTOINDEX
                    my_toplevel_dir = my_settings['work_directory']                                                                                     #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #the type level                                                                                                                         #AUTOINDEX
                my_typelevel_dir = 'single'                                                                                                             #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #the date level                                                                                                                         #AUTOINDEX
                my_datelevel_dir = datetime.date.today().isoformat()                                                                                    #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #the lowest level                                                                                                                       #AUTOINDEX
                my_sub_dir = os.path.basename(data['fullname']).replace('.img','')                                                                      #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #now join the three levels                                                                                                              #AUTOINDEX
                my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)                                      #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #make sure this is an original directory                                                                                                #AUTOINDEX
                if os.path.exists(my_work_dir_candidate):                                                                                               #AUTOINDEX
                    #we have already                                                                                                                    #AUTOINDEX
                    self.logger.debug('%s has already been used, will add qualifier' % my_work_dir_candidate)                                           #AUTOINDEX
                    for i in range(1,10000):                                                                                                            #AUTOINDEX
                        if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):                                                                #AUTOINDEX
                            my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))                                                            #AUTOINDEX
                            self.logger.debug('%s will be used for this image' % my_work_dir_candidate)                                             #AUTOINDEX
                            break                                                                                                                       #AUTOINDEX
                        else:                                                                                                                           #AUTOINDEX
                            i += 1                                                                                                                      #AUTOINDEX
                #now make the candidate the used dir                                                                                                    #AUTOINDEX
                my_work_dir = my_work_dir_candidate                                                                                                     #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #create a representation of the process for display                                                                                     #AUTOINDEX
                my_repr = my_sub_dir+'.img'                                                                                                             #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #add the process to the database to display as in-process                                                                               #AUTOINDEX
                process_id = self.DATABASE.addNewProcess(type='single',                                                                              #AUTOINDEX
                                                         rtype='reprocess',                                                                          #AUTOINDEX
                                                         data_root_dir=my_data_root_dir,                                                             #AUTOINDEX
                                                         repr=my_repr )                                                                              #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #add the ID entry to the data dict                                                                                                      #AUTOINDEX
                #Is this used at all?                                                                                                                   #AUTOINDEX
                data.update( { 'ID' : os.path.basename(my_work_dir),                                                                                    #AUTOINDEX
                               'process_id' : process_id,                                                                                               #AUTOINDEX
                               'repr' : my_repr,
                               'mk3_phi' : self.request['mk3_phi'],
                               'mk3_kappa' : self.request['mk3_kappa'],
                               'STAC file1' : original_result_dict['stac_file1'],
                               'STAC file2' : original_result_dict['stac_file2'],
                               'axis_align' : self.request['option1'],
                               'correct.lp' : self.request['correct.lp'],
                               'dataset_repr' : self.request['dataset_repr'] } )                                                                                                     #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #now package directories into a dict for easy access by worker class                                                                    #AUTOINDEX
                my_dirs = { 'work'          : my_work_dir,                                                                                              #AUTOINDEX
                            'data_root_dir' : my_data_root_dir }                                                                                        #AUTOINDEX
                                                                                                                                                        #AUTOINDEX                                                                                                   #AUTOINDEX
                #add the request to my_settings so it can be passed on                                                                                  #AUTOINDEX
                my_settings['request'] = self.request                                                                                                   #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #mark that the request has been addressed                                                                                               #AUTOINDEX
                self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')                                                              #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #mark in the cloud_current table                                                                                                        #AUTOINDEX
                self.DATABASE.addCloudCurrent(self.request)                                                                                             #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #connect to the server and autoindex the single image                                                                                   #AUTOINDEX
                PerformAction(('STAC',my_dirs,data,my_settings,self.reply_settings),my_settings,self.SecretSettings,self.logger)      #AUTOINDEX

            else:
                self.logger.debug('STAC Pair')                                                                                                          #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #get the data for each image                                                                                                            #AUTOINDEX-PAIR
                data1 = self.DATABASE.getImageByImageID(original_result_dict['image1_id'])                                                               #AUTOINDEX-PAIR
                data2 = self.DATABASE.getImageByImageID(original_result_dict['image2_id'])                                                               #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #get the correct directory to run in                                                                                                    #AUTOINDEX-PAIR
                # We should end up with top_level/2010-05-10/snap_99_001/                                                                               #AUTOINDEX-PAIR
                #the top level                                                                                                                          #AUTOINDEX-PAIR
                if my_settings['work_dir_override'] == 'False':                                                                                         #AUTOINDEX-PAIR
                    if ('/single/' in original_result_dict['work_dir']):                                                                                #AUTOINDEX-PAIR
                        my_toplevel_dir = os.path.dirname(original_result_dict['work_dir'].split('single')[0])                                          #AUTOINDEX-PAIR
                    elif ('/pair/' in original_result_dict['work_dir']):                                                                                #AUTOINDEX-PAIR
                        my_toplevel_dir = os.path.dirname(original_result_dict['work_dir'].split('pair')[0])                                            #AUTOINDEX-PAIR
                else:                                                                                                                                   #AUTOINDEX-PAIR
                    my_toplevel_dir = my_settings['work_directory']                                                                                     #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #the type level                                                                                                                         #AUTOINDEX-PAIR
                my_typelevel_dir = 'pair'                                                                                                               #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #the date level                                                                                                                         #AUTOINDEX-PAIR
                my_datelevel_dir = datetime.date.today().isoformat()                                                                                    #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #the lowest level                                                                                                                       #AUTOINDEX-PAIR
                my_sub_dir = '_'.join((data1['image_prefix'],str(data1['run_number']),'+'.join((str(data1['image_number']).lstrip('0'),str(data2['image_number']).lstrip('0')))))
                                                                                                                                                        #AUTOINDEX-PAIR
                #now join the three levels                                                                                                              #AUTOINDEX-PAIR
                my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)                                      #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #make sure this is an original directory                                                                                                #AUTOINDEX-PAIR
                if os.path.exists(my_work_dir_candidate):                                                                                               #AUTOINDEX-PAIR
                    for i in range(1,10000):                                                                                                            #AUTOINDEX-PAIR
                        if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):                                                                #AUTOINDEX-PAIR
                            my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))                                                            #AUTOINDEX-PAIR
                            break                                                                                                                       #AUTOINDEX-PAIR
                        else:                                                                                                                           #AUTOINDEX-PAIR
                            i += 1                                                                                                                      #AUTOINDEX-PAIR
                my_work_dir = my_work_dir_candidate                                                                                                     #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #create a representation of the process for display                                                                                     #AUTOINDEX-PAIR
                my_repr = my_sub_dir+'.img'                                                                                                             #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #add the process to the database to display as in-process                                                                               #AUTOINDEX-PAIR
                process_id = self.DATABASE.addNewProcess( type = 'pair',                                                                                #AUTOINDEX-PAIR
                                                          rtype = 'reprocess',                                                                          #AUTOINDEX-PAIR
                                                          data_root_dir = my_data_root_dir,                                                             #AUTOINDEX-PAIR
                                                          repr = my_repr )                                                                              #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #add the ID entry to the data dict                                                                                                      #AUTOINDEX-PAIR
                #Is this used at all?                                                                                                                   #AUTOINDEX-PAIR
                data1.update( { 'ID' : os.path.basename(my_work_dir),                                                                                   #AUTOINDEX-PAIR
                                'process_id' : process_id,                                                                                              #AUTOINDEX-PAIR
                                'repr' : my_repr,
                                'mk3_phi' : self.request['mk3_phi'],
                                'mk3_kappa' : self.request['mk3_kappa'],
                                'axis_align' : self.request['option1'],
                                'STAC file1' : original_result_dict['stac_file1'],                                                                      #AUTOINDEX-PAIR
                                'STAC file2' : original_result_dict['stac_file2'],
                                'correct.lp' : self.request['correct.lp'],
                                'dataset_repr' : self.request['dataset_repr'] })                                                                    #AUTOINDEX-PAIR

                data2.update( { 'ID' : os.path.basename(my_work_dir),                                                                                   #AUTOINDEX-PAIR
                                'process_id' : process_id,                                                                                              #AUTOINDEX-PAIR
                                'repr' : my_repr,
                                'mk3_phi' : self.request['mk3_phi'],
                                'mk3_kappa' : self.request['mk3_kappa'],
                                'axis_align' : self.request['option1'],
                                'STAC file1' : original_result_dict['stac_file1'],
                                'STAC file2' : original_result_dict['stac_file2'],
                                'correct.lp' : self.request['correct.lp'],
                                'dataset_repr' : self.request['dataset_repr'] })                                                                                                    #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #now package directories into a dict for easy access by worker class                                                                    #AUTOINDEX-PAIR
                my_dirs = { 'work'          : my_work_dir,                                                                                              #AUTOINDEX-PAIR
                            'data_root_dir' : my_data_root_dir }                                                                                        #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR                                                                                                              #AUTOINDEX-PAIR
                #add the request to my_settings so it can be passed on                                                                                  #AUTOINDEX-PAIR
                my_settings['request'] = self.request                                                                                                   #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #mark that the request has been addressed                                                                                               #AUTOINDEX-PAIR
                self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')                                                              #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #mark in the cloud_current table                                                                                                        #AUTOINDEX-PAIR
                self.DATABASE.addCloudCurrent(self.request)                                                                                             #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #connect to the server and autoindex the single image                                                                                   #AUTOINDEX-PAIR
                PerformAction(('STAC-PAIR',my_dirs,data1,data2,my_settings,self.reply_settings),my_settings,self.SecretSettings,self.logger)       #AUTOINDEX-PAIR

"""
  cloud_request_id: 34148
      request_type: start-mad
original_result_id: 994869
     original_type: integrate
       original_id: 70091
     data_root_dir: /gpfs2/users/necat/necat_E_1480
    new_setting_id: NULL
  additional_image: NULL
           mk3_phi: NULL
         mk3_kappa: NULL
         result_id: NULL
         input_sca: NULL
         input_mtz: NULL
         input_map: NULL
           ha_type: Se
         ha_number: 1
        shelxd_try: 1024
           sad_res: 0
          sequence:
           pdbs_id: NULL
              nmol: NULL
       frame_start: NULL
      frame_finish: NULL
            status: complete
        ip_address: 164.54.212.15
        puckset_id: NULL
           option1: NULL
           peak_id: 70090
     inflection_id: 70090
       hiremote_id: 70090
       loremote_id: 70090
         native_id: 70090
         timestamp: 2015-08-04 17:03:45
"""
class SadHandler(threading.Thread):
    """
    Handles the initialization of sad runs in a separate thread.
    """

    def __init__(self,request,database,settings,reply_settings,logger=None):
        """
        Initialize SadHandler.

        request - a dict contining a variety of information that comes from the request
        database - an instance of rapd_database.Database
        settings -
        reply_settings - a tuple of the ip address and port for the controller server
        logger - an instance of the logger
        """

        logger.info('SadHandler::__init__  %s' % str(request))

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request         = request
        self.DATABASE        = database
        self.SecretSettings  = settings
        self.reply_settings  = reply_settings
        self.logger          = logger
        self.start()

    def run(self):
        self.logger.debug('SadHandler::run')

        #mark that the request has been addressed
        self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')

        #Structure the request to the cluster
        if self.request['request_type'] == 'start-sad':
            #the original result dict
            original_result_dict = self.DATABASE.getResultById(self.request['original_id'],
                                                               self.request['original_type'])
            #get the settings
            my_settings = self.DATABASE.getSettings(setting_id=original_result_dict['settings_id'])
            #data root dir
            my_data_root_dir = original_result_dict['data_root_dir']
            #get the wavelength
            self.request['wavelength'] = original_result_dict['wavelength']
            #construct a repr for the merged data
            my_repr = original_result_dict['repr']

            # Get the correct directory to run in
            # We should end up with top_level/sad/2010-05-10/XXX_1_1-180/
            #the top level
            if my_settings['work_dir_override'] == 'False':
                if ('merge' in original_result_dict['work_dir']):
                    my_toplevel_dir = original_result_dict['work_dir'][:original_result_dict['work_dir'].index('merge')]
                else:
                    my_toplevel_dir = original_result_dict['work_dir'][:original_result_dict['work_dir'].index('integrate')]
            else:
                my_toplevel_dir = my_settings['work_directory']
            #the type level
            my_typelevel_dir = 'sad'
            #the date level
            my_datelevel_dir = datetime.date.today().isoformat()
            #the lowest level
            my_sub_dir = my_repr
            #now join the four levels
            my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)
            #make sure this is an original directory
            if os.path.exists(my_work_dir_candidate):
                #we have already
                self.logger.debug('%s has already been used, will add qualifier' % my_work_dir_candidate)
                for i in range(1,10000):
                    if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):
                        my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))
                        self.logger.debug('%s will be used for this image' % my_work_dir_candidate)
                        break
                    else:
                        i += 1
            #now make the candidate the used dir
            my_work_dir = my_work_dir_candidate

            #add the process to the database to display as in-process
            process_id = self.DATABASE.addNewProcess(type='sad',
                                                     rtype='original',
                                                     data_root_dir=my_data_root_dir,
                                                     repr=my_repr)
            #add the process id entry to the data dicts
            my_settings['process_id'] = process_id

            #now package directories into a dict for easy access by worker class
            my_dirs = {'work':my_work_dir,
                       'data_root_dir':my_data_root_dir}

            #accumulate the information into the data directory
            data = {'original':original_result_dict,
                    'repr':my_repr}

            #add the request to my_settings so it can be passed on
            my_settings['request'] = self.request

            #mark that the request has been addressed
            self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')
            #mark in the cloud_current table
            self.DATABASE.addCloudCurrent(self.request)
            #connect to the server and autoindex the single image
            #a = pprint.PrettyPrinter(indent=2)
            #a.pprint((('SAD',my_dirs,data,my_settings,self.reply_settings),my_settings,self.SecretSettings,self.logger))
            PerformAction(('SAD',my_dirs,data,my_settings,self.reply_settings),my_settings,self.SecretSettings,self.logger)

"""
{u'additional_image': None,
 u'cloud_request_id': 34148,
 u'data_root_dir': '/gpfs2/users/necat/necat_E_1480',
 u'frame_finish': None,
 u'frame_start': None,
 u'ha_number': 1,
 u'ha_type': 'Se',
 u'hiremote_id': 70090,
 u'inflection_id': 70090,
 u'input_map': None,
 u'input_mtz': None,
 u'input_sca': None,
 u'ip_address': '164.54.212.15',
 u'loremote_id': 70090,
 u'mk3_kappa': None,
 u'mk3_phi': None,
 u'native_id': 70090,
 u'new_setting_id': None,
 u'nmol': None,
 u'option1': None,
 u'original_id': 70091,
 u'original_result_id': 994869,
 u'original_type': 'integrate',
 u'pdbs_id': None,
 u'peak_id': 70090,
 u'puckset_id': None,
 u'request_type': 'start-mad',
 u'result_id': None,
 u'sad_res': 0.0,
 u'sequence': '',
 u'shelxd_try': 1024,
 u'status': 'request',
 u'timestamp': '2015-08-04T17:03:45'}
 """

class MadHandler(threading.Thread):
    """
    Handles the initialization of sad runs in a separate thread.
    """

    def __init__(self,request,database,settings,reply_settings,logger=None):
        """
        Initialize MadHandler.

        request - a dict contining a variety of information that comes from the request
        database - an instance of rapd_database.Database
        settings -
        reply_settings - a tuple of the ip address and port for the controller server
        logger - an instance of the logger
        """

        logger.info('MadHandler::__init__  %s' % str(request))

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request         = request
        self.DATABASE        = database
        self.SecretSettings  = settings
        self.reply_settings  = reply_settings
        self.logger          = logger
        self.start()

    def run(self):
        self.logger.debug('MadHandler::run')

        #mark that the request has been addressed
        self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')

        #Structure the request to the cluster
        if self.request['request_type'] == 'start-mad':

            # Get the actual data files locations for the agent
            type_trans = { "peak"       : "PEAK",
                           "inflection" : "INFL",
                           "hiremote"   : "HREM",
                           "loremote"   : "LREM",
                           "native"     : "NAT" }

            peak_results_dict = None
            for data_type in ("peak", "inflection", "hiremote", "loremote", "native"):

                self.logger.debug(data_type)

                # Is there this kind of data?
                if self.request[data_type+"_id"]:

                    self.logger.debug(data_type+"_id")

                    # Get type of data - integrate or merge
                    result = self.DATABASE.getTypeByResultId(self.request[data_type+"_id"],full=True)

                    # Get the information regarding the data
                    data_results = self.DATABASE.getResultById(result["id"],
                                                               result["type"])

                    self.logger.debug(str(data_results))

                    # Save if peak
                    if data_type == "peak":
                        peak_results_dict = data_results.copy()

                    # Save mtz for agent
                    self.request["mtz_%s" % type_trans[data_type]] = data_results["mtz_file"]

                # This data does not exist
                else:
                    self.request["mtz_%s" % type_trans[data_type]] = None

            self.logger.debug(str(peak_results_dict))

            # Blank out mtz_file to indicate that this is not SAD
            peak_results_dict["mtz_file"] = None

            #get the settings
            my_settings = self.DATABASE.getSettings(setting_id=peak_results_dict['settings_id'])

            #data root dir
            my_data_root_dir = peak_results_dict['data_root_dir']

            #construct a repr for the merged data
            my_repr = peak_results_dict['repr']

            # Get the correct directory to run in
            # We should end up with top_level/Mad/2010-05-10/XXX_1_1-180/

            # the top level
            if my_settings['work_dir_override'] == 'False':
                if ('merge' in peak_results_dict['work_dir']):
                    my_toplevel_dir = peak_results_dict['work_dir'][:peak_results_dict['work_dir'].index('merge')]
                else:
                    my_toplevel_dir = peak_results_dict['work_dir'][:peak_results_dict['work_dir'].index('integrate')]
            else:
                my_toplevel_dir = my_settings['work_directory']

            #the type level
            my_typelevel_dir = 'mad'

            #the date level
            my_datelevel_dir = datetime.date.today().isoformat()

            #the lowest level
            my_sub_dir = my_repr

            #now join the four levels
            my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)

            #make sure this is an original directory
            if os.path.exists(my_work_dir_candidate):
                #we have already
                self.logger.debug('%s has already been used, will add qualifier' % my_work_dir_candidate)
                for i in range(1,1000):
                    if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):
                        my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))
                        self.logger.debug('%s will be used for this image' % my_work_dir_candidate)
                        break
                    else:
                        i += 1

            #now make the candidate the used dir
            my_work_dir = my_work_dir_candidate

            #add the process to the database to display as in-process
            process_id = self.DATABASE.addNewProcess(type='mad',
                                                     rtype='original',
                                                     data_root_dir=my_data_root_dir,
                                                     repr=my_repr)

            #add the process id entry to the data dicts
            my_settings['process_id'] = process_id

            #now package directories into a dict for easy access by worker class
            my_dirs = {'work':my_work_dir,
                       'data_root_dir':my_data_root_dir}

            #accumulate the information into the data directory
            data = {'original':peak_results_dict,
                    'repr':my_repr}

            #add the request to my_settings so it can be passed on
            my_settings['request'] = self.request

            #mark in the cloud_current table
            self.DATABASE.addCloudCurrent(self.request)

            #connect to the server and autoindex the single image
            #a = pprint.PrettyPrinter(indent=2)
            PerformAction(('MAD',my_dirs,data,my_settings,self.reply_settings),my_settings,self.SecretSettings,self.logger)

class MrHandler(threading.Thread):
    """
    Handles the initialization of sad runs in a separate thread
    """
    def __init__(self,request,database,settings,reply_settings,logger=None):
        logger.info('MrHandler::__init__  %s' % str(request))

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request         = request
        self.DATABASE        = database
        self.SecretSettings  = settings
        self.reply_settings  = reply_settings
        self.logger          = logger

        self.start()

    def run(self):
        self.logger.debug('MrHandler::run')

        #mark that the request has been addressed
        self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')

        #Structure the request to the cluster
        if self.request['request_type'] == 'start-mr':

            my_pdb = self.transferFromUi()
            if my_pdb:
                #load the location of the pdb into the query
                if (my_pdb == "None"):
                    self.request['pdb'] = None
                    self.request['pdb_code'] = self.request['option1']
                else:
                    self.request['pdb'] = my_pdb
                #the original result dict
                original_result_dict = self.DATABASE.getResultById(id=self.request['original_id'],
                                                                   type=self.request['original_type'])
                #get the settings
                my_settings = self.DATABASE.getSettings(setting_id=original_result_dict['settings_id'])
                #data root dir
                my_data_root_dir = original_result_dict['data_root_dir']
                #get the wavelength
                self.request['wavelength'] = original_result_dict['wavelength']
                #construct a repr for the merged data
                my_repr = original_result_dict['repr']

                # Get the correct directory to run in
                # We should end up with top_level/sad/2010-05-10/XXX_1_1-180/
                #the top level
                if my_settings['work_dir_override'] == 'False':
                    if ('merge' in original_result_dict['work_dir']):
                        my_toplevel_dir = original_result_dict['work_dir'][:original_result_dict['work_dir'].index('merge')]
                    else:
                        my_toplevel_dir = original_result_dict['work_dir'][:original_result_dict['work_dir'].index('integrate')]
                else:
                    my_toplevel_dir = my_settings['work_directory']
                #the type level
                my_typelevel_dir = 'mr'
                #the date level
                my_datelevel_dir = datetime.date.today().isoformat()
                #the lowest level
                my_sub_dir = my_repr
                #now join the four levels
                my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)
                #make sure this is an original directory
                if os.path.exists(my_work_dir_candidate):
                    #we have already
                    self.logger.debug('%s has already been used, will add qualifier' % my_work_dir_candidate)
                    for i in range(1,10000):
                        if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):
                            my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))
                            self.logger.debug('%s will be used for this image' % my_work_dir_candidate)
                            break
                        else:
                            i += 1
                #now make the candidate the used dir
                my_work_dir = my_work_dir_candidate
                #add the process to the database to display as in-process
                process_id = self.DATABASE.addNewProcess(type='mr',
                                                         rtype='original',
                                                         data_root_dir=my_data_root_dir,
                                                         repr=my_repr)
                self.logger.debug("New process_id %d"%process_id)
                #add the process id entry to the data dicts
                my_settings['process_id'] = process_id
                #now package directories into a dict for easy access by worker class
                my_dirs = {'work':my_work_dir,
                           'data_root_dir':my_data_root_dir}

                #accumulate the information into the data directory
                data = {'original':original_result_dict,
                        'repr':my_repr}

                #add the request to my_settings so it can be passed on
                my_settings['request'] = self.request
                #mark that the request has been addressed
                self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')
                #mark in the cloud_current table
                self.DATABASE.addCloudCurrent(self.request)
                """
                print 'MR'
                print my_dirs
                print data
                print my_settings
                print self.reply_settings
                """
                #connect to the server and autoindex the single image
                #a = pprint.PrettyPrinter(indent=2)
                #a.pprint(('MR',my_dirs,data,my_settings,self.reply_settings))
                PerformAction(('MR',my_dirs,data,my_settings,self.reply_settings),my_settings,self.SecretSettings,self.logger)

    def transferFromUi(self):
        """
        Transfer the pdb from the User Interface Server to the local host
        """
        self.logger.debug('MrHander.TransferFromUi')

        #import for decoding
        import base64

        #set up simpler versions of the host parameters
        host     = self.SecretSettings['ui_host']
        port     = self.SecretSettings['ui_port']
        username = self.SecretSettings['ui_user']
        password = base64.b64decode(self.SecretSettings['ui_password'])

        try:

            #get the information on the pdb file to be uploaded
            if (self.request["pdbs_id"] == 0):
                return("None")
            else:
                pdb_dict = self.DATABASE.getPdbById(pdbs_id=self.request["pdbs_id"])

            if (pdb_dict):
                #create the log file
                paramiko.util.log_to_file('/tmp/paramiko.log')
                #create the Transport instance
                transport = paramiko.Transport((host, port))
                #connect with username and password
                transport.connect(username = username, password = password)
                #establish sftp client
                sftp = paramiko.SFTPClient.from_transport(transport)

                source = os.path.join(self.SecretSettings['ui_upload_dir'],pdb_dict['pdb_file'])
                target = os.path.join(self.SecretSettings['upload_dir'],str(pdb_dict['pdbs_id'])+'.pdb')
                self.logger.debug("source: %s"%source)
                self.logger.debug("target: %s" % target)
                sftp.get(source,target)

                sftp.close()
                transport.close()

                self.DATABASE.updatePdbLocation(pdbs_id=pdb_dict['pdbs_id'],
                                                location=target)

                return(target)
            else:
                return(False)
        except:
            self.logger.exception("MrHandler.transferFromUi Falied to transfer pdb file from UI to Local")


class IntegrationHandler(threading.Thread):
    """
    Handles the initialization of re-integrations in a separate thread.
    """

    def __init__(self,request,database,settings,reply_settings,logger=None):
        """
        Initialize the handler.

        request - a dict containing information on the request
        database - an instance of rapd_database.Database
        settings - dict from rapd_site describing settings for this rapd setup
        reply_settings - a tuple of ip address and port for the controller server to reply to
        logger - a logger instance
        """

        logger.info('IntegrationHandler::__init__  %s' % str(request))

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request         = request
        self.DATABASE        = database
        self.SecretSettings  = settings
        self.reply_settings  = reply_settings
        self.logger          = logger
        #start the new thread
        self.start()

    def run(self):
        """
        The new thread is now running
        """

        self.logger.debug('IntegrationHandler::run')
        try:
            #mark that the request has been addressed
            self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')

            #Structure the request to the cluster
            if self.request['request_type'] in ('start-xiaint','start-fastin'):
                #decide on request type
                if self.request['request_type'] == 'start-xiaint':
                    my_request_type = "XIA2"
                elif self.request['request_type'] == 'start-fastin':
                    my_request_type = "XDS"

                # Relabel the spacegroup request
                self.request['spacegroup'] = int(self.request.get('option1',0))

                #the original result dict
                original_result_dict = self.DATABASE.getResultById(id=self.request['original_id'],
                                                                   type='integrate')
                #get the settings
                my_settings = self.DATABASE.getSettings(setting_id=original_result_dict['settings_id'])
                #data root dir
                my_data_root_dir = original_result_dict['data_root_dir']
                #get the wavelength
                #if original_result_dict.has_key('wavelength'):
                #    self.request['wavelength'] = original_result_dict['wavelength']
                #else:
                self.request['wavelength'] = self.DATABASE.getWavelengthFromRunId(run_id=original_result_dict['run_id'])
                #construct a repr for the reprocessed data
                my_repr = "_".join(original_result_dict["repr"].split("_")[:-1])+"_"+str(self.request["frame_start"])+"-"+str(self.request["frame_finish"])
                # Get the correct directory to run in
                # We should end up with original['work_dir']/reprocess_#
                #the first candidate
                my_work_dir_candidate = os.path.join(original_result_dict["work_dir"],"reprocess")
                my_work_dir = '_'.join((my_work_dir_candidate,str(1)))
                #make sure this is an original directory
                if (os.path.exists('_'.join((my_work_dir_candidate,str(1))))):
                    #we have already
                    self.logger.debug('%s has already been used, will increment qualifier' % '_'.join((my_work_dir_candidate,str(1))))
                    for i in range(2,1000):
                        if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):
                            my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))
                            self.logger.debug('%s will be used for this image' % my_work_dir_candidate)
                            break
                        else:
                            i += 1
                    #now make the candidate the used dir
                    my_work_dir = my_work_dir_candidate

                self.request["work_dir"] = my_work_dir

                #add the process to the database to display as in-process
                process_id = self.DATABASE.addNewProcess(type=my_request_type,
                                                         rtype='reprocess',
                                                         data_root_dir=my_data_root_dir,
                                                         repr=my_repr)

                #create a result for this process as well
                integrate_result_id,result_id = self.DATABASE.makeNewResult(rtype='integrate',
                                                                            process_id=process_id,
                                                                            data_root_dir=my_data_root_dir)

                #add the process id entry to the data dicts
                my_settings['process_id'] = process_id
                #now package directories into a dict for easy access by worker class
                my_dirs = {'work':my_work_dir,
                           'data_root_dir':my_data_root_dir}

                #accumulate the information into the data directory
                data = {'original':original_result_dict,
                        'repr':my_repr}

                #add the request to my_settings so it can be passed on
                my_settings['request'] = self.request
                #mark that the request has been addressed
                self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')
                #mark in the cloud_current table
                self.DATABASE.addCloudCurrent(self.request)

                #connect to the server and send request
                #a = pprint.PrettyPrinter(indent=2)
                #a.pprint((my_request_type,my_dirs,data,my_settings,self.reply_settings))
                PerformAction((my_request_type,my_dirs,data,my_settings,self.reply_settings),my_settings,self.SecretSettings,self.logger)
        except:
            self.logger.exception("Error in IntegrationHandler")


class SimpleMergeHandler(threading.Thread):
    """
    Handles the initialization of simple merging runs in a separate thread
    """
    def __init__(self,request,database,settings,reply_settings,logger=None):
        logger.info('SimpleMergeHandler::__init__  %s' % str(request))

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request         = request
        self.DATABASE        = database
        self.SecretSettings  = settings
        self.reply_settings  = reply_settings
        self.logger          = logger

        self.start()

    def run(self):
        self.logger.debug('SimpleMergeHandler::run')

        #mark that the request has been addressed
        self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')

        #Structure the request to the cluster
        if self.request['request_type'] == 'smerge':
            #the original result dict
            original_result_dict = self.DATABASE.getResultById(self.request['original_id'],self.request['original_type'])
            #the secondary result dict
            #secondary_result_type = self.DATABASE.getTypeByResultId(self.request['additional_image'])
            secondary_result_dict = self.DATABASE.getResultById(self.request['additional_image'],"integrate")
            #get the settings
            my_settings = self.DATABASE.getSettings(setting_id=original_result_dict['settings_id'])

            my_data_root_dir = original_result_dict['data_root_dir']

            #construct a repr for the merged data
            my_repr = original_result_dict['repr']+'+'+secondary_result_dict['repr']

            # Get the correct directory to run in
            # We should end up with top_level/sad/2010-05-10/XXX_1_1-180/
            #the top level
            if my_settings['work_dir_override'] == 'False':
                if ('merge' in original_result_dict['work_dir']):
                    my_toplevel_dir = original_result_dict['work_dir'][:original_result_dict['work_dir'].index('merge')]
                else:
                    my_toplevel_dir = original_result_dict['work_dir'][:original_result_dict['work_dir'].index('integrate')]
            else:
                my_toplevel_dir = my_settings['work_directory']
            #the type level
            my_typelevel_dir = 'merge'
            #the date level
            my_datelevel_dir = datetime.date.today().isoformat()
            #the lowest level
            my_sub_dir = my_repr
            #now join the four levels
            my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)
            #make sure this is an original directory
            if os.path.exists(my_work_dir_candidate):
                #we have already
                self.logger.debug('%s has already been used, will add qualifier' % my_work_dir_candidate)
                for i in range(1,10000):
                    if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):
                        my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))
                        self.logger.debug('%s will be used for this image' % my_work_dir_candidate)
                        break
                    else:
                        i += 1
            #now make the candidate the used dir
            my_work_dir = my_work_dir_candidate

            #add the process to the database to display as in-process
            process_id = self.DATABASE.addNewProcess(type='merge',
                                                     rtype='reprocess',
                                                     data_root_dir=my_data_root_dir,
                                                     repr=my_repr)

            #make a new result for this process
            merge_result_id,result_id = self.DATABASE.makeNewResult(rtype='merge',
                                                                    process_id=process_id,
                                                                    data_root_dir=my_data_root_dir)

            #now package directories into a dict for easy access by worker class
            my_dirs = {'work':my_work_dir,
                       'data_root_dir':my_data_root_dir}

            #accumulate the information into the data directory
            data = {'original':original_result_dict,
                    'secondary':secondary_result_dict,
                    'repr':my_repr,
                    'process_id':process_id}

            #add the request to my_settings so it can be passed on
            my_settings['request'] = self.request

            #mark that the request has been addressed
            self.DATABASE.markCloudRequest(self.request['cloud_request_id'],'working')
            #mark in the cloud_current table
            self.DATABASE.addCloudCurrent(self.request)

            #connect to the server and autoindex the single image
            PerformAction(('SMERGE',my_dirs,data,my_settings,self.reply_settings),my_settings,self.SecretSettings,self.logger)

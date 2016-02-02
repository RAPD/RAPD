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
import importlib
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
    Monitors a core database, organizes requests and then calls PerformAction
    to run the process on the cluster.
    """

    # Place to store requests
    request_queue = deque()

    #for stopping
    Go = True

    # Handlers for cloud events
    possible_handlers = ("binary_merge",
                         "minikappa",
                         "data_collection_params",
                         "download",
                         "mr",
                         "reindex",
                         "reintegrate")
    handlers = {}

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
        reply_settings - tuple of (ip_address, port_number) for the ControllerServer which
                         listens for replies
        interval - the time in seconds between checks of the cloud
        logger - logger instance - required

        """

        # Get the logger instance
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

        # Run
        self.daemon = True
        self.start()

    def stop(self):
        """
        Bring the cloud monitor loop to a halt.
        """

        self.logger.debug("Stopping")
        self.Go = False

    def run(self):
        """
        The thread starts running here.
        """

        self.logger.debug("CloudMonitor::run")

        # Save some space
        settings = self.settings

        # Import the handlers
        self.import_handlers()

        #run the monitor as a loop
        while self.Go:
            #
            # The following section is for cloud-based beamline control events
            #
            # Minikappa requests
            if settings["CLOUD_MINIKAPPA"]:
                # Check the database
                minikappa_request = self.database.getMinikappaRequest()
                if minikappa_request:
                    __ = self.handlers["minikappa_handler"](request=minikappa_request,
                                                            database=self.database)

            # Data collection run parameters request
            if settings["CLOUD_DATA_COLLECTION_PARAMS"]:
                datacollection_request = self.database.getDatacollectionRequest()
                if datacollection_request:
                    __ = self.handlers["data_collection_params_handler"](
                        request=datacollection_request,
                        database=self.database)

            #
            # The following section is for cloud-based events
            #

            # Query for new cloud requests
            request = self.database.getCloudRequest()

            # Now look through the request
            if request:

                # # Puck Request does not pass IP, so check it first.
                # if request["request_type"] == "setpuck":
                #     self.logger.debug("Set Puck Request")
                #     self.logger.debug(request)
                #     __ = PuckHandler(request, self.database, self.Secret_Settings, self.reply_settings, self.logger)
                #
                # # Spreadsheet uploading does not pass IP, so check it next.
                # # Upon new spreadsheet upload, update the master puck list for console.
                # elif request["request_type"] == "newsheet":
                #     self.logger.debug("New Spreadsheet Uploaded.  Change Master Puck List.")
                #     self.logger.debug(request)
                #     __ = SheetHandler(request, self.database, self.Secret_Settings, self.reply_settings, self.logger)

                # Download request
                if request["request_type"].startswith("down"):
                    __ = self.handlers["data_collection_params_handler"](request,
                                                                         self.database,
                                                                         settings,
                                                                         self.reply_settings)

                #Reprocess request
                elif request["request_type"] == "reprocess":
                    __ = self.handlers["reindex_handler"](request=request,
                                                          database=self.database,
                                                          settings=settings,
                                                          reply_settings=self.reply_settings)

                # STAC Request
                elif request["request_type"] == "stac":
                    pass
                    # self.logger.debug("STAC Request")
                    # self.logger.debug(request)
                    # tmp = StacHandler(request,self.database,self.Secret_Settings,self.reply_settings,self.logger)

                # SAD request
                elif request["request_type"] == "start-sad":
                    __ = self.handlers["sad_handler"](request=request,
                                                      database=self.database,
                                                      settings=self.settings,
                                                      reply_settings=self.reply_settings)

                # MAD request
                elif request["request_type"] == "start-mad":
                    pass
                    # tmp = MadHandler(request=request,
                    #                  database=self.database,
                    #                  settings=self.Secret_Settings,
                    #                  reply_settings=self.reply_settings,
                    #                  logger=self.logger)

                # MR request
                elif request["request_type"] == "start-mr":
                    __ = self.handlers["mr_handler"](request=request,
                                                     database=self.database,
                                                     settings=self.settings,
                                                     reply_settings=self.reply_settings)

                # FastIntegration request
                elif request["request_type"] == "start-fastin":
                    __ = self.handlers["reintegrate_handler"](request=request,
                                                              database=self.database,
                                                              settings=self.settings,
                                                              reply_settings=self.reply_settings)

                # Xia2 request
                elif request["request_type"] == "start-xiaint":
                    __ = self.handlers["reintegrate_handler"](request=request,
                                                              database=self.database,
                                                              settings=self.settings,
                                                              reply_settings=self.reply_settings)

                # Binary Merge Request
                elif request["request_type"] == "smerge":
                    __ = self.handlers["binary_merge"](request=request,
                                                       database=self.database,
                                                       settings=self.settings,
                                                       reply_settings=self.reply_settings)
            """
                else:
                    #put the request in the queue
                    self.request_queue.append(request)

                    #increment the queue in the database
                    self.database.addToCloudQueue()

                    #mark the request as queued
                    self.database.markCloudRequest(request["cloud_request_id"],"queued")

            #no cloud request, check the queue
            elif (len(self.request_queue) > 0):

                #check for clearance
                if True: #(self.database.getCloudClearance()):
                    request = self.request_queue.popleft()

                    #decrement the queue in the database
                    self.database.subtractFromCloudQueue()

                    #we have a download request
                    if request["request_type"].startswith("down"):
                        self.logger.debug("Download request")
                        self.logger.debug(request)
                        tmp = DownloadHandler(request,self.database,self.Secret_Settings,self.reply_settings,logger=self.logger)

                    #Reprocess request
                    elif request["request_type"] == "reprocess":
                        self.logger.debug("Reprocess request")
                        tmp = StacHandler(request,self.database,self.Secret_Settings,self.reply_settings,self.logger,True)
            """
            time.sleep(self.interval)

    def import_handlers(self):
        """Import handlers for this site"""

        self.logger.debug("import_handlers")

        # Save some space
        settings = self.settings

        # Run through possible handlers and import them
        for handler in self.possible_handlers:
            self.logger.debug(settings)
            if settings["CLOUD_"+handler.upper()+"_HANDLER"]:
                self.logger.debug("Importing %s", handler)
                self.handlers[handler] = importlib.import_module("cloud.handlers.%s" % settings["CLOUD_"+handler.upper()+"_HANDLER"]).Handler

                # self.logger.debug(dir(self.handlers[handler]))
            else:
                self.logger.debug("Skipping %s", handler)

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

        logger.info("PuckHandler::__init__")
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

        self.logger.debug("PuckHandler::run")

        #get the timestamp into console format
        timestamp = self.request["timestamp"].replace("-","/").replace("T","_")[:-3]

        #mark that the request has been addressed
        self.DATABASE.markCloudRequest(self.request["cloud_request_id"],"working")

       #Structure the request to the cluster
        if self.request["request_type"] == "setpuck":
            #figure out what and where to transfer
            beamline = self.request["option1"]
            puck_info = self.DATABASE.getSetPuckInfo(self.request["puckset_id"])
            #get CrystalIDs for each puck
            for puck in puck_info:
               if puck_info[puck] == "None":
                  puck_contents = { puck : "NULL" }
                  #create the files and send them to the specific beamline
                  TransferPucksToBeamline(beamline,puck_contents)
               else:
                  puck_contentsdict = self.DATABASE.getPuckInfo(puck_info[puck])
                  puck_contentslist = []
                  for crystal in puck_contentsdict:
                      puck_contentslist.append({"CrystalID": crystal["CrystalID"], "PuckID": crystal["PuckID"]})
                      puck_contents = { puck : puck_contentslist }
                  #create the files and send them to the specific beamline
                  TransferPucksToBeamline(beamline,puck_contents)

            #mark that the request has been addressed
            self.DATABASE.markCloudRequest(self.request["cloud_request_id"],"complete")

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

        logger.info("SheetHandler::__init__")
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

        self.logger.debug("SheetHandler::run")

        #get the timestamp into console format
        timestamp = self.request["timestamp"].replace("-","/").replace("T","_")[:-3]

        #mark that the request has been addressed
        self.DATABASE.markCloudRequest(self.request["cloud_request_id"],"working")

        #get the master puck list
        all_pucks = self.DATABASE.getAllPucks(self.Secret_Settings["puck_cutoff"])
        for puck in all_pucks:
            puck.update(select=0)
        beamlines = ["C","E"]
        for beamline in beamlines:
            current_pucks = self.DATABASE.getCurrentPucks(beamline)

            #transfer all available pucks and mark selected pucks as 1
            if current_pucks:
                for puck in all_pucks:
                    for chosen in current_pucks[0]:
                        if puck["PuckID"] == current_pucks[0][puck]:
                            puck.update(select=1)

            TransferMasterPuckListToBeamline(beamline, all_pucks)

        #mark that the request has been addressed
        self.DATABASE.markCloudRequest(self.request["cloud_request_id"],"complete")



class StacHandler(threading.Thread):
    """
    Handles the initialization of reprocessing runs in a separate thread
    """
    def __init__(self,request,database,settings,reply_settings,logger=None):
        logger.info("StacHandler::__init__  %s" % str(request))

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
        self.logger.debug("StacHandler::run")

        #mark that the request has been addressed
        self.DATABASE.markCloudRequest(self.request["cloud_request_id"],"working")

        #Structure the request to the cluster
        if self.request["request_type"] == "stac":

            #get the settings
            my_settings          = self.DATABASE.getSettings(setting_id=self.request["new_setting_id"])
            original_result_dict = self.DATABASE.getResultById(self.request["original_id"],self.request["original_type"])
            my_data_root_dir     = original_result_dict["data_root_dir"]


            if self.request["option1"] == "multi":
                my_reference_result_dict = self.DATABASE.getResultById(self.request["result_id"],"integrate")
                self.request["correct.lp"] = os.path.join(os.path.dirname(my_reference_result_dict["xds_log"]),"xds_lp_files","CORRECT.LP")
                self.request["dataset_repr"] = my_reference_result_dict["repr"]
            else:
                self.request["correct.lp"] = None
                self.request["dataset_repr"] = None

            #generate some debugging info
            self.logger.debug(my_settings)
            self.logger.debug(original_result_dict)

            if self.request["original_type"] == "single":

                self.logger.debug("STAC Single image autoindexing")                                                                                      #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                data = self.DATABASE.getImageByImageID(original_result_dict["image_id"])                                                                #AUTOINDEX
                self.logger.debug(data)                                                                                                                 #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                # Get the correct directory to run in                                                                                                   #AUTOINDEX
                # We should end up with top_level/2010-05-10/snap_99_001/                                                                               #AUTOINDEX
                #the top level                                                                                                                          #AUTOINDEX
                if my_settings["work_dir_override"] == "False":                                                                                         #AUTOINDEX
                    my_toplevel_dir = os.path.dirname(original_result_dict["summary_short"].split("single")[0])                                         #AUTOINDEX
                else:                                                                                                                                   #AUTOINDEX
                    my_toplevel_dir = my_settings["work_directory"]                                                                                     #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #the type level                                                                                                                         #AUTOINDEX
                my_typelevel_dir = "single"                                                                                                             #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #the date level                                                                                                                         #AUTOINDEX
                my_datelevel_dir = datetime.date.today().isoformat()                                                                                    #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #the lowest level                                                                                                                       #AUTOINDEX
                my_sub_dir = os.path.basename(data["fullname"]).replace(".img","")                                                                      #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #now join the three levels                                                                                                              #AUTOINDEX
                my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)                                      #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #make sure this is an original directory                                                                                                #AUTOINDEX
                if os.path.exists(my_work_dir_candidate):                                                                                               #AUTOINDEX
                    #we have already                                                                                                                    #AUTOINDEX
                    self.logger.debug("%s has already been used, will add qualifier" % my_work_dir_candidate)                                           #AUTOINDEX
                    for i in range(1,10000):                                                                                                            #AUTOINDEX
                        if not os.path.exists("_".join((my_work_dir_candidate,str(i)))):                                                                #AUTOINDEX
                            my_work_dir_candidate = "_".join((my_work_dir_candidate,str(i)))                                                            #AUTOINDEX
                            self.logger.debug("%s will be used for this image" % my_work_dir_candidate)                                             #AUTOINDEX
                            break                                                                                                                       #AUTOINDEX
                        else:                                                                                                                           #AUTOINDEX
                            i += 1                                                                                                                      #AUTOINDEX
                #now make the candidate the used dir                                                                                                    #AUTOINDEX
                my_work_dir = my_work_dir_candidate                                                                                                     #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #create a representation of the process for display                                                                                     #AUTOINDEX
                my_repr = my_sub_dir+".img"                                                                                                             #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #add the process to the database to display as in-process                                                                               #AUTOINDEX
                process_id = self.DATABASE.addNewProcess(type="single",                                                                              #AUTOINDEX
                                                         rtype="reprocess",                                                                          #AUTOINDEX
                                                         data_root_dir=my_data_root_dir,                                                             #AUTOINDEX
                                                         repr=my_repr )                                                                              #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #add the ID entry to the data dict                                                                                                      #AUTOINDEX
                #Is this used at all?                                                                                                                   #AUTOINDEX
                data.update( { "ID" : os.path.basename(my_work_dir),                                                                                    #AUTOINDEX
                               "process_id" : process_id,                                                                                               #AUTOINDEX
                               "repr" : my_repr,
                               "mk3_phi" : self.request["mk3_phi"],
                               "mk3_kappa" : self.request["mk3_kappa"],
                               "STAC file1" : original_result_dict["stac_file1"],
                               "STAC file2" : original_result_dict["stac_file2"],
                               "axis_align" : self.request["option1"],
                               "correct.lp" : self.request["correct.lp"],
                               "dataset_repr" : self.request["dataset_repr"] } )                                                                                                     #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #now package directories into a dict for easy access by worker class                                                                    #AUTOINDEX
                my_dirs = { "work"          : my_work_dir,                                                                                              #AUTOINDEX
                            "data_root_dir" : my_data_root_dir }                                                                                        #AUTOINDEX
                                                                                                                                                        #AUTOINDEX                                                                                                   #AUTOINDEX
                #add the request to my_settings so it can be passed on                                                                                  #AUTOINDEX
                my_settings["request"] = self.request                                                                                                   #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #mark that the request has been addressed                                                                                               #AUTOINDEX
                self.DATABASE.markCloudRequest(self.request["cloud_request_id"],"working")                                                              #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #mark in the cloud_current table                                                                                                        #AUTOINDEX
                self.DATABASE.addCloudCurrent(self.request)                                                                                             #AUTOINDEX
                                                                                                                                                        #AUTOINDEX
                #connect to the server and autoindex the single image                                                                                   #AUTOINDEX
                PerformAction(("STAC",my_dirs,data,my_settings,self.reply_settings),my_settings,self.SecretSettings,self.logger)      #AUTOINDEX

            else:
                self.logger.debug("STAC Pair")                                                                                                          #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #get the data for each image                                                                                                            #AUTOINDEX-PAIR
                data1 = self.DATABASE.getImageByImageID(original_result_dict["image1_id"])                                                               #AUTOINDEX-PAIR
                data2 = self.DATABASE.getImageByImageID(original_result_dict["image2_id"])                                                               #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #get the correct directory to run in                                                                                                    #AUTOINDEX-PAIR
                # We should end up with top_level/2010-05-10/snap_99_001/                                                                               #AUTOINDEX-PAIR
                #the top level                                                                                                                          #AUTOINDEX-PAIR
                if my_settings["work_dir_override"] == "False":                                                                                         #AUTOINDEX-PAIR
                    if ("/single/" in original_result_dict["work_dir"]):                                                                                #AUTOINDEX-PAIR
                        my_toplevel_dir = os.path.dirname(original_result_dict["work_dir"].split("single")[0])                                          #AUTOINDEX-PAIR
                    elif ("/pair/" in original_result_dict["work_dir"]):                                                                                #AUTOINDEX-PAIR
                        my_toplevel_dir = os.path.dirname(original_result_dict["work_dir"].split("pair")[0])                                            #AUTOINDEX-PAIR
                else:                                                                                                                                   #AUTOINDEX-PAIR
                    my_toplevel_dir = my_settings["work_directory"]                                                                                     #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #the type level                                                                                                                         #AUTOINDEX-PAIR
                my_typelevel_dir = "pair"                                                                                                               #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #the date level                                                                                                                         #AUTOINDEX-PAIR
                my_datelevel_dir = datetime.date.today().isoformat()                                                                                    #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #the lowest level                                                                                                                       #AUTOINDEX-PAIR
                my_sub_dir = "_".join((data1["image_prefix"],str(data1["run_number"]),"+".join((str(data1["image_number"]).lstrip("0"),str(data2["image_number"]).lstrip("0")))))
                                                                                                                                                        #AUTOINDEX-PAIR
                #now join the three levels                                                                                                              #AUTOINDEX-PAIR
                my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)                                      #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #make sure this is an original directory                                                                                                #AUTOINDEX-PAIR
                if os.path.exists(my_work_dir_candidate):                                                                                               #AUTOINDEX-PAIR
                    for i in range(1,10000):                                                                                                            #AUTOINDEX-PAIR
                        if not os.path.exists("_".join((my_work_dir_candidate,str(i)))):                                                                #AUTOINDEX-PAIR
                            my_work_dir_candidate = "_".join((my_work_dir_candidate,str(i)))                                                            #AUTOINDEX-PAIR
                            break                                                                                                                       #AUTOINDEX-PAIR
                        else:                                                                                                                           #AUTOINDEX-PAIR
                            i += 1                                                                                                                      #AUTOINDEX-PAIR
                my_work_dir = my_work_dir_candidate                                                                                                     #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #create a representation of the process for display                                                                                     #AUTOINDEX-PAIR
                my_repr = my_sub_dir+".img"                                                                                                             #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #add the process to the database to display as in-process                                                                               #AUTOINDEX-PAIR
                process_id = self.DATABASE.addNewProcess( type = "pair",                                                                                #AUTOINDEX-PAIR
                                                          rtype = "reprocess",                                                                          #AUTOINDEX-PAIR
                                                          data_root_dir = my_data_root_dir,                                                             #AUTOINDEX-PAIR
                                                          repr = my_repr )                                                                              #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #add the ID entry to the data dict                                                                                                      #AUTOINDEX-PAIR
                #Is this used at all?                                                                                                                   #AUTOINDEX-PAIR
                data1.update( { "ID" : os.path.basename(my_work_dir),                                                                                   #AUTOINDEX-PAIR
                                "process_id" : process_id,                                                                                              #AUTOINDEX-PAIR
                                "repr" : my_repr,
                                "mk3_phi" : self.request["mk3_phi"],
                                "mk3_kappa" : self.request["mk3_kappa"],
                                "axis_align" : self.request["option1"],
                                "STAC file1" : original_result_dict["stac_file1"],                                                                      #AUTOINDEX-PAIR
                                "STAC file2" : original_result_dict["stac_file2"],
                                "correct.lp" : self.request["correct.lp"],
                                "dataset_repr" : self.request["dataset_repr"] })                                                                    #AUTOINDEX-PAIR

                data2.update( { "ID" : os.path.basename(my_work_dir),                                                                                   #AUTOINDEX-PAIR
                                "process_id" : process_id,                                                                                              #AUTOINDEX-PAIR
                                "repr" : my_repr,
                                "mk3_phi" : self.request["mk3_phi"],
                                "mk3_kappa" : self.request["mk3_kappa"],
                                "axis_align" : self.request["option1"],
                                "STAC file1" : original_result_dict["stac_file1"],
                                "STAC file2" : original_result_dict["stac_file2"],
                                "correct.lp" : self.request["correct.lp"],
                                "dataset_repr" : self.request["dataset_repr"] })                                                                                                    #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #now package directories into a dict for easy access by worker class                                                                    #AUTOINDEX-PAIR
                my_dirs = { "work"          : my_work_dir,                                                                                              #AUTOINDEX-PAIR
                            "data_root_dir" : my_data_root_dir }                                                                                        #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR                                                                                                              #AUTOINDEX-PAIR
                #add the request to my_settings so it can be passed on                                                                                  #AUTOINDEX-PAIR
                my_settings["request"] = self.request                                                                                                   #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #mark that the request has been addressed                                                                                               #AUTOINDEX-PAIR
                self.DATABASE.markCloudRequest(self.request["cloud_request_id"],"working")                                                              #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #mark in the cloud_current table                                                                                                        #AUTOINDEX-PAIR
                self.DATABASE.addCloudCurrent(self.request)                                                                                             #AUTOINDEX-PAIR
                                                                                                                                                        #AUTOINDEX-PAIR
                #connect to the server and autoindex the single image                                                                                   #AUTOINDEX-PAIR
                PerformAction(("STAC-PAIR",my_dirs,data1,data2,my_settings,self.reply_settings),my_settings,self.SecretSettings,self.logger)       #AUTOINDEX-PAIR


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

        logger.info("MadHandler::__init__  %s" % str(request))

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
        self.logger.debug("MadHandler::run")

        #mark that the request has been addressed
        self.DATABASE.markCloudRequest(self.request["cloud_request_id"],"working")

        #Structure the request to the cluster
        if self.request["request_type"] == "start-mad":

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
            my_settings = self.DATABASE.getSettings(setting_id=peak_results_dict["settings_id"])

            #data root dir
            my_data_root_dir = peak_results_dict["data_root_dir"]

            #construct a repr for the merged data
            my_repr = peak_results_dict["repr"]

            # Get the correct directory to run in
            # We should end up with top_level/Mad/2010-05-10/XXX_1_1-180/

            # the top level
            if my_settings["work_dir_override"] == "False":
                if ("merge" in peak_results_dict["work_dir"]):
                    my_toplevel_dir = peak_results_dict["work_dir"][:peak_results_dict["work_dir"].index("merge")]
                else:
                    my_toplevel_dir = peak_results_dict["work_dir"][:peak_results_dict["work_dir"].index("integrate")]
            else:
                my_toplevel_dir = my_settings["work_directory"]

            #the type level
            my_typelevel_dir = "mad"

            #the date level
            my_datelevel_dir = datetime.date.today().isoformat()

            #the lowest level
            my_sub_dir = my_repr

            #now join the four levels
            my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)

            #make sure this is an original directory
            if os.path.exists(my_work_dir_candidate):
                #we have already
                self.logger.debug("%s has already been used, will add qualifier" % my_work_dir_candidate)
                for i in range(1,1000):
                    if not os.path.exists("_".join((my_work_dir_candidate,str(i)))):
                        my_work_dir_candidate = "_".join((my_work_dir_candidate,str(i)))
                        self.logger.debug("%s will be used for this image" % my_work_dir_candidate)
                        break
                    else:
                        i += 1

            #now make the candidate the used dir
            my_work_dir = my_work_dir_candidate

            #add the process to the database to display as in-process
            process_id = self.DATABASE.addNewProcess(type="mad",
                                                     rtype="original",
                                                     data_root_dir=my_data_root_dir,
                                                     repr=my_repr)

            #add the process id entry to the data dicts
            my_settings["process_id"] = process_id

            #now package directories into a dict for easy access by worker class
            my_dirs = {"work":my_work_dir,
                       "data_root_dir":my_data_root_dir}

            #accumulate the information into the data directory
            data = {"original":peak_results_dict,
                    "repr":my_repr}

            #add the request to my_settings so it can be passed on
            my_settings["request"] = self.request

            #mark in the cloud_current table
            self.DATABASE.addCloudCurrent(self.request)

            #connect to the server and autoindex the single image
            #a = pprint.PrettyPrinter(indent=2)
            PerformAction(("MAD",my_dirs,data,my_settings,self.reply_settings),my_settings,self.SecretSettings,self.logger)

"""
This file is part of RAPD

Copyright (C) 2009-2016 Cornell University
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

#standard imports
import os
import sys
import threading
import time
import socket
import collections
import datetime

#custom RAPD imports
#from rapd_beamlinespecific import *
from rapd_beamlinespecific import Remote, ImageMonitor
from rapd_database import Database
from rapd_cluster import PerformAction, ControllerServer
from rapd_cloud import CloudMonitor
from rapd_console import ConsoleConnect as BeamlineConnect
from rapd_console import ConsoleFeeder
from rapd_pilatus import pilatus_read_header
from rapd_site import beamline_settings, secret_settings
from rapd_site import necat_determine_flux as determine_flux
from rapd_site import GetDataRootDir, TransferToUI, TransferToBeamline, CopyToUser
from rapd_adsc import Q315ReadHeader

#####################################################################
# The main Model Class                                              #
#####################################################################
class Model():
    """
    Main controlling code for the CORE.

    This is really more than just a model, probably model+controller.
    Coordinates the monitoring of data collection and the "cloud",
    as well as the running of processes and logging of all metadata

    """

    def __init__(self, site, logger):
        """
        Save variables and call init_settings.

        site - site designation that syncs with rapd_site sites
        logger - a logger instance - required

        """

        logger.info("Model::__init__")

        #passed-in variables
        self.site = site
        self.logger = logger

        # Initialize the settings from rapd_beamlinespecific
        self.init_settings()

    def init_settings(self):
        """
        Initialize a number of variables and read in the settings from rapd_beamlinespecific.
        """

        self.logger.debug("Model::init_settings  beamline: %s" % self.site)

        #set up the queue for keeping track of image pairs
        self.pair = collections.deque(["", ""], maxlen=2)
        self.pair_id = collections.deque(["", ""], maxlen=2)

        #queues for managing processes - this control will be moved in the future
        #the queue for controlling simultaneous image processing
        self.indexing_queue = collections.deque()
        self.indexing_active = collections.deque()
        #the queue system for managing diffraction-based centering
        self.diffcenter_queue = collections.deque()
        self.diffcenter_active = collections.deque()
        #the queue system for managing snapshot-based analysis
        self.quickanalysis_queue = collections.deque()
        self.quickanalysis_active = collections.deque()
        #for managing runs without going to the db
        self.current_run = {}
        self.past_runs = collections.deque(maxlen=10)
        self.current_image = None

        self.last_quickimage = 0

        #set the defaults
        try:
            #grab the settings from the rapd_site.py file
            if self.site in beamline_settings.keys():
                self.Settings = beamline_settings[self.site].copy()
                self.SecretSettings = secret_settings[self.site].copy()
            else:
                self.logger.debug("must be a test beamline")
                self.Settings = beamline_settings["T"].copy()
                self.Settings["beamline"] = self.site
                self.SecretSettings = secret_settings["T"].copy()
                self.SecretSettings["beamline"] = self.site

            #determine the current ip address
            s_tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s_tmp.connect(("google.com", 80))
            self.ip_address = s_tmp.getsockname()[0]
            s_tmp.close()
            self.socket = self.SecretSettings["controller_port"]

            #save starting directory position
            self.start_dir = os.getcwd()

            #the current data_root_dir (The base directory for user data collection for a trip
            self.data_root_dir = None
            self.Settings["data_root_dir"] = "DEFAULTS"
            self.Settings["setting_type"] = "GLOBAL"

            # Interfaces to more complicated actors - mainly NULL until we start
            #set up database interface
            self.DATABASE = Database(settings=self.SecretSettings,
                                     logger=self.logger)
            #update the DEFAULTS settings based on the data in rapd_site.py
            self.DATABASE.addSettings(settings=self.Settings)

            #watches as runs are collected
            #self.RUNWATCHERS = []

            #Server for receiving information from the cluster
            self.SERVER = False

            #watches for new collected images
            self.IMAGEMONITOR = False
            self.imagemonitor_reconnect_attempts = 0

            #watches the cloud requests
            self.CLOUDMONITOR = False

            #let them know we have success
            self.logger.debug("Model initialized")

        except:
            self.logger.exception("""FATAL ERROR - this beamline is proably not in
            the default settings table - edit rapd_beamlinespecific.py to rectify
            before restarting""")
            sys.exit()

    def Start(self):
        """
        Start monitoring the beamline.
        """

        self.logger.debug("Model::Start")

        #start the server for cluster feedback
        try:
            self.SERVER = ControllerServer(receiver=self.Receive,
                                           port=self.socket,
                                           logger=self.logger)
        except:
            self.logger.exception("CATASTROPHIC ERROR - cannot start \
            ControllerServer to receive cluster feedback")
            exit()

        #monitor for new images to be collected
        self.IMAGEMONITOR = ImageMonitor(beamline=self.site,
                                         notify=self.Receive,
                                         logger=self.logger)

        # watch the cloud for requests
        if self.SecretSettings["cloud_interval"] > 0.0:
            self.CLOUDMONITOR = CloudMonitor(database=self.DATABASE,
                                             settings=self.SecretSettings,
                                             reply_settings=(self.ip_address, self.socket),
                                             interval=self.SecretSettings["cloud_interval"],
                                             logger=self.logger)
        else:
            self.logger.debug("CLOUDMONITOR turned off")

        #start the status updating
        self.STATUSHANDLER = StatusHandler(
            db=self.DATABASE,
            ip_address=self.ip_address,
            data_root_dir=self.data_root_dir,
            beamline=self.site,
            dataserver_ip=self.SecretSettings["adsc_server"].split(":")[1][2:],
            cluster_ip=self.SecretSettings["cluster_host"],
            logger=self.logger
            )

        #connection to beamline
        if self.Settings["connect_to_beamline"]:
            self.BEAMLINE_CONNECTION = BeamlineConnect(beamline=self.site,
                                                       logger=self.logger)
        else:
            self.BEAMLINE_CONNECTION = False

        # Remote access handler
        if self.Settings["remote"]:
            self.logger.debug("Creating self.REMOTE")
            self.REMOTE = Remote(beamline=self.site,
                                 logger=self.logger)
        else:
            self.REMOTE = False
            self.logger.debug("Error creating self.REMOTE, set to False")

        # Test the cluster is available
        PerformAction(command=("TEST", (self.ip_address, self.socket)),
                      settings=self.Settings,
                      secret_settings=self.SecretSettings,
                      logger=self.logger)

    def Stop(self):
        """
        Stop the ImageMonitor,CloudMonitor and StatusRegistrar.
        """

        self.logger.info("Model::Stop")

        #the IMAGEMONITOR
        try:
            if self.IMAGEMONITOR:
                self.IMAGEMONITOR.Stop()
                self.IMAGEMONITOR = False
        except:
            self.IMAGEMONITOR = False

        #the CLOUDMONITOR
        try:
            if self.CLOUDMONITOR:
                self.CLOUDMONITOR.Stop()
                self.CLOUDMONITOR = False
        except:
            self.CLOUDMONITOR = False

        #the STATUSREGISTRAR
        try:
            if self.STATUSREGISTRAR:
                self.STATUSREGISTRAR.Stop()
                self.STATUSREGISTRAR = False
        except:
            self.STATUSREGISTRAR = False

    #################################################################
    # Handle a new image being recorded                             #
    #################################################################
    def add_adsc_image(self, data):
        """
        Handle an image to be added to the database from ADSC.

        The image is NOT presumed to be new, so it is checked against the database.
        There are several classes of images that are sorted out here:
            data - snaps and runs
            ignore - image ignored
                     tag defined in rapd_site ignore_tag

        """
        self.logger.debug("Model::add_adsc_image %s" % data["image_name"])

        #reset the reconnect attempts to 0 since we have connected
        self.imagemonitor_reconnect_attempts = 0

        #Save current image in class-level variable
        fullname = data["image_name"]
        dirname = os.path.dirname(fullname)
        self.current_image = fullname

        # Skip any handling?
        if dirname in self.Settings["analysis_shortcircuits"]:
            self.logger.info("Short-circuit")

        # Go ahead and handle the image
        else:

            # Derive the data_root_dir
            my_data_root_dir = GetDataRootDir(fullname=fullname,
                                              logger=self.logger)

            # Figure out if image in the current run...
            place = self.in_current_run(fullname)

            # Image is in the current run
            if isinstance(place, int):

                self.logger.info("%s in current run at position %d" % (fullname,
                                                                       place))

                # If not integrating trigger integration
                if self.current_run["status"] != "INTEGRATING":

                    # Handle getting to the party late
                    if place != 1:
                        self.logger.info("Creating first image in run")
                        fullname = "%s/%s_%03d.%s" % (
                            self.current_run["directory"],
                            self.current_run["image_prefix"],
                            int(self.current_run["start"]),
                            self.current_run["image_suffix"])

                    # Right on time
                    else:
                        pass
                        # fullname = data["image_name"]

                    #Get all the image information
                    header = self.get_adsc_header(
                        fullname=fullname,
                        run_id=self.current_run["run_id"],
                        drd=my_data_root_dir,
                        adsc_number=data["adsc_number"],
                        place=1)

                    #Add to database
                    db_result, __ = self.DATABASE.add_image(header)
                    header.update(db_result)

                    self.current_run["status"] = "INTEGRATING"
                    header["run"] = self.current_run.copy()
                    self.new_data_image(data=header)

            # Image is not in the current run
            else:

                # Image is a snap
                if place == "SNAP":

                    self.logger.debug("%s is a snap" % fullname)

                    #Get all the image information
                    header = self.get_adsc_header(
                        fullname=data["image_name"],
                        run_id=0,
                        drd=my_data_root_dir,
                        adsc_number=data["adsc_number"])

                    #Add to database
                    db_result, __ = self.DATABASE.add_image(header)
                    header.update(db_result)

                    #Run the image as a new data image
                    self.new_data_image(data=header)

                # Image is in a past run
                elif place == "PAST_RUN":
                    self.logger.info("In past run")
                    my_place, run = self.in_past_run(fullname)

                    if run:
                        if my_place == run["total"]:
                            self.logger.info("Final image in past run")

                            #Get all the image information
                            header = self.get_adsc_header(
                                fullname=data["image_name"],
                                run_id=run["run_id"],
                                drd=my_data_root_dir,
                                adsc_number=data["adsc_number"],
                                place=my_place)

                            #Add to database
                            db_result, __ = self.DATABASE.add_image(header)
                            header.update(db_result)

                            #tag the header with run data
                            header["run"] = run.copy()

                            #Now trigger integration - if not integrating
                            if run["status"] != "INTEGRATING":
                                run["status"] = "INTEGRATING"
                                self.new_data_image(data=header)

    def add_pilatus_image(self, fullname):
        """A new Pilatus6MF image has arrived"""

        self.logger.info("add_pilatus_image %s" % fullname)

        # Set current_image
        self.current_image = fullname
        dirname = os.path.dirname(fullname)

        # Short circuit for priming image
        if "priming_shot" in fullname:
            self.logger.info("Priming shot is ignored")
            return False

        # Short circuit for fast analysis
        if dirname in self.Settings["analysis_shortcircuits"]:
            self.logger.info("Short-circuit")
            return False

        # Non-short-circuit image
        else:

            # Derive the data_root_dir
            my_data_root_dir = GetDataRootDir(fullname=fullname,
                                              logger=self.logger)

            # Derive place of image in run
            place = self.in_current_run(fullname)

            # Image is in the current sweep of data
            if isinstance(place, int):
                self.logger.info("%s in current run at position %d" % \
                    (fullname, place))

                #If not integrating, continue
                if self.current_run["status"] != "INTEGRATING":

                    # Handle getting to the party late
                    if place != 1:
                        self.logger.info("Creating first image in run")
                        fullname = "%s/%s_%d_%04d.%s" % (
                            self.current_run["directory"],
                            self.current_run["prefix"],
                            self.current_run["run_number"],
                            int(self.current_run["start"]),
                            "cbf")
                    # Right on time
                    else:
                        pass
                        # fullname = data["image_name"]

                    #Get all the image information
                    header = self.get_pilatus_header(
                        fullname=fullname,
                        mode="RUN",
                        run_id=self.current_run["run_id"],
                        drd=my_data_root_dir,
                        place_in_run=1)

                    #Add to database & update local image data
                    db_result, status = self.DATABASE.add_pilatus_image(header)
                    header.update(db_result)
                    header["run"] = self.current_run

                    self.current_run["status"] = "INTEGRATING"
                    self.new_data_image(data=header)

                # Already integrating the run - no need to do a full query
                else:
                    self.logger.info("    Already integrating the run")

            # Not in the current sweep
            else:

                # A snap
                if place == "SNAP":

                    self.logger.debug("%s is a snap" % fullname)

                    #Get all the image information
                    header = self.get_pilatus_header(
                        fullname=fullname,
                        mode="SNAP",
                        run_id=0,
                        drd=my_data_root_dir)

                    #Add to database
                    db_result, status = self.DATABASE.add_pilatus_image(header)
                    header.update(db_result)

                    #Run the image as a new data image
                    self.new_data_image(data=header)

                # A past run
                elif place == "PAST_RUN":
                    self.logger.info("In past run")

                    # Get the run information for the past run
                    my_place, run = self.in_past_run(fullname)

                    # Have run data - handle appropriately
                    if run:
                        if my_place == run["total"]:
                            self.logger.info("Final image in past run")
                            #Get all the image information
                            header = self.get_pilatus_header(
                                fullname=fullname,
                                mode="RUN",
                                run_id=run["run_id"],
                                drd=my_data_root_dir,
                                place_in_run=my_place)

                            #Add to database
                            db_result, status = self.DATABASE.add_pilatus_image(header)
                            header.update(db_result)

                            #tag the header with run data
                            header["run"] = run

                            #Now trigger integration - if not integrating
                            if run["status"] != "INTEGRATING":
                                run["status"] = "INTEGRATING"
                                self.new_data_image(data=header)

    def get_adsc_header(self,
                        fullname,
                        run_id=0,
                        drd=None,
                        adsc_number=0,
                        place=1):
        """Get the ADSC image"s header data"""

        self.logger.debug("get_adsc_header %s run_id:%d" % (fullname, run_id))

        adsc_header = Q315ReadHeader(fullname, logger=self.logger)
        adsc_header["run_id"] = run_id
        adsc_header["data_root_dir"] = drd
        adsc_header["adsc_number"] = adsc_number

        #Grab extra data for the image
        adsc_header.update(self.BEAMLINE_CONNECTION.GetImageData())

        #Now perform beamline-specific calculations
        adsc_header = determine_flux(header_in=adsc_header,
                                     beamline=self.site,
                                     logger=self.logger)

        #Calculate beam center
        adsc_header["x_beam"], adsc_header["y_beam"] = \
            self.calculate_beam_center(
                d=adsc_header["distance"],
                v_offset=adsc_header["vertical_offset"])

        #update remote client
        if self.REMOTE and place == 1:
            self.REMOTE.add_image(adsc_header)

        return adsc_header

    def get_pilatus_header(self,
                           fullname,
                           mode,
                           run_id=None,
                           drd=None,
                           place_in_run=None):
        """Retrieve header information for a Pilatus image"""

        # Read the header
        header = pilatus_read_header(image=fullname,
                                     mode=mode,
                                     run_id=run_id,
                                     place_in_run=place_in_run,
                                     logger=self.logger)

        # Put data root dir in the header info
        header["data_root_dir"] = drd

        #Grab extra data for the image
        header.update(self.BEAMLINE_CONNECTION.GetImageData())

        #Now perform beamline-specific calculations
        header = determine_flux(header_in=header,
                                beamline=self.site,
                                logger=self.logger)

        #Calculate beam center
        header["x_beam"], header["y_beam"] = self.calculate_beam_center(
            float(header["distance"]))

        #update remote client
        if self.REMOTE:
            self.REMOTE.add_image(header)

        return header

    def calculate_beam_center(self, distance, v_offset=0):
        """ Return a beam center, given a distance """

        x_beam = distance**6 * self.Settings["beam_center_x_m6"] + \
                 distance**5 * self.Settings["beam_center_x_m5"] + \
                 distance**4 * self.Settings["beam_center_x_m4"] + \
                 distance**3 * self.Settings["beam_center_x_m3"] + \
                 distance**2 * self.Settings["beam_center_x_m2"] + \
                 distance * self.Settings["beam_center_x_m1"] + \
                 self.Settings["beam_center_x_b"] + \
                 v_offset

        y_beam = distance**6 * self.Settings["beam_center_y_m6"] + \
                 distance**5 * self.Settings["beam_center_y_m5"] + \
                 distance**4 * self.Settings["beam_center_y_m4"] + \
                 distance**3 * self.Settings["beam_center_y_m3"] + \
                 distance**2 * self.Settings["beam_center_y_m2"] + \
                 distance * self.Settings["beam_center_y_m1"] + \
                 self.Settings["beam_center_y_b"]

        return x_beam, y_beam

    def in_past_run(self, fullname):
        """Determine the place in a past run the image is
        """
        self.logger.info("in_past_run %s" % fullname)

        #tease out the info from the file name
        directory = os.path.dirname(fullname)
        base = os.path.basename(fullname).rstrip(".cbf").rstrip(".img")
        prefix = "_".join(base.split("_")[0:-2])
        run_number = int(base.split("_")[-2])
        image_number = int(base.split("_")[-1])

        #Check older runs
        for run in self.past_runs:
            if (run["directory"] == directory and
                    run["prefix"] == prefix and
                    run["run_number"] == run_number):
                if (run["start"] <= image_number and
                        image_number <= (run["start"] + run["total"] - 1)):
                    return image_number-run["start"]+1, run

        return False, False

    def in_current_run(self, fullname):
        """
        Determine if an image is in the currently active run - return
        place in run or False based on prefix,directory,run_id and image number
        """
        self.logger.info("in_current_run %s" % fullname)

        #tease out the info from the file name
        directory = os.path.dirname(fullname)
        base = os.path.basename(fullname).rstrip(".cbf").rstrip(".img")
        sbase = base.split("_")
        prefix = "_".join(sbase[0:-2])
        image_number = int(sbase[-1])
        run_number = int(sbase[-2])

        # A snap
        if run_number == 0:
            return "SNAP"

        # NOT a snap
        else:
            self.logger.debug("current_run %s" % str(self.current_run))
            self.logger.debug("%s %s %s %d %d" %(directory, base, prefix,
                                                 run_number, image_number))

            #there is a current run
            if self.current_run:
                self.logger.debug("There is a current_run")
                # The "/" addition if for HF4M
                if (self.current_run["directory"] == directory) or \
                   (self.current_run["directory"][:-1] == directory):
                    self.logger.debug("directories pass")

                    if self.current_run["prefix"] == prefix:
                        self.logger.debug("prefixes match")

                        if self.current_run["run_number"] == run_number:
                            self.logger.debug("run_numbers match")

                            # Update the remote system on the run
                            if self.REMOTE:
                                self.REMOTE.update_run_progress(
                                    run_position=image_number- \
                                        self.current_run.get("start", 1)+1,
                                    image_name=os.path.basename(fullname),
                                    run_data=self.current_run)

                            # Correct indention?
                            return image_number-self.current_run["start"]+1

                        # Run numbers do not match
                        else:
                            return "PAST_RUN"

                    # Prefixes do not match
                    else:
                        return "PAST_RUN"

                # Directories do not match
                else:
                    return "PAST_RUN"

            #there is no current run
            else:
                return "PAST_RUN"

    def new_data_image(self, data):
        """
        Handle the information that there is a new image in the database.

        There are several calsses of images:
            1. The image is standalone and will be autoindexed
            2. The image is one of a pair of images for autoindexing
            3. The image is first in a wedge of data collection
            4. The image is in the middle of a wedge of data collection
            5. The image is last in a wedge of data collection
        """

        self.logger.debug("Model::new_data_image %s" % data["fullname"])
        self.logger.debug(data)

        # Acquire the settings for this image in case they have changed via UI
        my_settings = self.DATABASE.getCurrentSettings(beamline=self.site)

        try:
            run_id = data["run_id"]
            run_total = self.current_run["total"]
        except:
            run_id = 0
            run_total = 0

        # derive the data_root_dir used by the web interface for so many things
        my_data_root_dir = data["data_root_dir"]
        # my_data_root_dir = GetDataRootDir(fullname=data["fullname"],
        #                                   logger=self.logger)

        #check the data_root_dir to see if it is a new one
        if my_data_root_dir != self.data_root_dir:

            #reset the pucks since we are presumably a new user
            #this works in a NO-CONSOLE version of pucks
            self.DATABASE.resetPucks(beamline=self.site)

            #we have a new drd - check for a previous setting
            self.logger.debug("DRD has changed to %s" % my_data_root_dir)
            check = self.DATABASE.checkNewDataRootDirSetting(data_root_dir=my_data_root_dir,
                                                             beamline=self.site)
            if check:
                self.logger.debug("Found and will employ settings this new data root dir")

            self.data_root_dir = my_data_root_dir

            #new settings have been returned - use them
            if check:
                my_settings = check
                self.logger.debug("copying check")
                self.logger.debug(my_settings)

        else:
            self.logger.debug("Data root directory is unchanged %s" % my_data_root_dir)
            #Update the current table in the database
            self.DATABASE.updateCurrent(my_settings)

        #sample identification
        #this is a hack for getting sample_id into the images
        if my_settings.has_key("puckset_id"):
            data = self.DATABASE.setImageSampleId(image_dict=data,
                                                  puckset_id=my_settings["puckset_id"])

        if (not run_id) and (data["collect_mode"] == "SNAP"):
            self.logger.debug("Image is standalone - autoindex")

            #add the image to self.pair
            self.pair.append(data["fullname"].lower())
            self.pair_id.append(data["image_id"])

            # Get the correct directory to run in
            # We should end up with top_level/2010-05-10/snap_99_001/
            #the top level
            #if my_settings["work_dir_override"] == "False":
            #    my_toplevel_dir = self.start_dir
            #else:
            my_toplevel_dir = my_settings["work_directory"]
            self.logger.debug("  my_toplevel_dir: %s" % my_toplevel_dir)

            #the type level
            my_typelevel_dir = "single"

            #the date level
            my_datelevel_dir = datetime.date.today().isoformat()

            #the lowest level
            my_sub_dir = os.path.basename(data["fullname"]).replace(".img", "").replace(".cbf", "")

            #now join the three levels
            my_work_dir_candidate = os.path.join(my_toplevel_dir,
                                                 my_typelevel_dir,
                                                 my_datelevel_dir,
                                                 my_sub_dir)

            #make sure this is an original directory
            if os.path.exists(my_work_dir_candidate):
                #we have already
                self.logger.debug("%s has already been used, will add qualifier" %
                                  my_work_dir_candidate)
                for i in range(1, 1000):
                    if not os.path.exists("_".join((my_work_dir_candidate, str(i)))):
                        my_work_dir_candidate = "_".join((my_work_dir_candidate, str(i)))
                        self.logger.debug("%s will be used for this image" % my_work_dir_candidate)
                        break
                    else:
                        i += 1

            #now make the candidate the used dir
            my_work_dir = my_work_dir_candidate
            self.logger.debug("  my_work_dir: %s" % my_work_dir)

            #now package directories into a dict for easy access by worker class
            my_dirs = {"work":my_work_dir,
                       "data_root_dir":my_data_root_dir}

            #create a representation of the process for display
            my_repr = ""
            if data.get("detector") == "PILATUS":
                my_repr = my_sub_dir+".cbf"
            else:
                my_repr = my_sub_dir+".img"

            #add the process to the database to display as in-process
            process_id = self.DATABASE.addNewProcess(type="single",
                                                     rtype="original",
                                                     data_root_dir=my_data_root_dir,
                                                     repr=my_repr)

            #add the ID entry to the data dict
            #Is this used at all?
            data.update({"ID":os.path.basename(my_work_dir),
                         "process_id":process_id,
                         "repr":my_repr})

            #If we are throttling autoindexing jobs
            if self.SecretSettings["throttle_strategy"] == True:
                #too many jobs already running - put this in the queue
                if len(self.indexing_active) >= self.SecretSettings["active_strategy_limit"]:
                    self.logger.debug("Adding autoindex to the queue")
                    self.indexing_queue.appendleft((
                        ("AUTOINDEX", my_dirs, data, my_settings, (self.ip_address, self.socket)),
                        my_settings,
                        self.SecretSettings,
                        self.logger))
                #go ahead and run, place marker in the queue
                else:
                    #connect to the server and autoindex the single image
                    self.logger.debug("less than %s processes active - run autoindexing" %
                                      self.SecretSettings["active_strategy_limit"])
                    self.indexing_active.append("autoindex")
                    PerformAction(
                        command=("AUTOINDEX",
                                 my_dirs,
                                 data,
                                 my_settings,
                                 (self.ip_address, self.socket)),
                        settings=my_settings,
                        secret_settings=self.SecretSettings,
                        logger=self.logger
                        )

            #No throttling - go ahead and run
            else:
                PerformAction(
                    command=("AUTOINDEX",
                             my_dirs,
                             data,
                             my_settings,
                             (self.ip_address, self.socket)),
                    settings=my_settings,
                    secret_settings=self.SecretSettings,
                    logger=self.logger
                    )
            #
            # AUTOINDEX-PAIR
            #
            #if the last two images have "pair" in their name - look closer
            self.logger.warning(self.pair)
            if "pair" in self.pair[0] and self.pair[1]:
                self.logger.debug("Potentially a pair of images")
                #everything matches up to the image number
                if (self.pair[0] != self.pair[1]) & (self.pair[0][:-8] == self.pair[1][:-8]):
                    self.logger.info("This looks like a pair to me: %s, %s" %
                                     (self.pair[1], self.pair[0]))

                    #get the data for the first image
                    data1 = self.DATABASE.getImageByImageID(image_id=self.pair_id[0])
                    #make a copy of the second pair to be LESS confusing
                    data2 = data.copy()

                    #make sure we are looking at an increment of one
                    if not data1["image_number"]+1 == data2["image_number"]:
                        return()

                    # Derive some directory names
                    # my_toplevel_dir & my_datelevel_dir should already be current
                    #the type level
                    my_typelevel_dir = "pair"

                    #the lowest level
                    my_sub_dir = "_".join(
                        (data1["image_prefix"], str(data1["run_number"]), "+".join(
                            (str(data1["image_number"]).lstrip("0"),
                             str(data2["image_number"]).lstrip("0")))
                        ))

                    #now join the three levels
                    my_work_dir_candidate = os.path.join(
                        my_toplevel_dir,
                        my_typelevel_dir,
                        my_datelevel_dir,
                        my_sub_dir
                        )

                    #make sure this is an original directory
                    if os.path.exists(my_work_dir_candidate):
                        #we have already
                        self.logger.debug("%s has already been used, will add qualifier" %
                                          my_work_dir_candidate)
                        for i in range(1, 10000):
                            if not os.path.exists("_".join((my_work_dir_candidate, str(i)))):
                                my_work_dir_candidate = "_".join((my_work_dir_candidate, str(i)))
                                self.logger.debug("%s will be used for this image" %
                                                  my_work_dir_candidate)
                                break
                            else:
                                i += 1
                    my_work_dir = my_work_dir_candidate

                    #now package directories into a dict for easy access by worker class
                    my_dirs = {"work"          : my_work_dir,
                               "data_root_dir" : my_data_root_dir}

                    #generate a representation of the process for display
                    my_repr = my_sub_dir+".img"

                    #add the process to the database to display as in-process
                    process_id = self.DATABASE.addNewProcess(
                        type="pair",
                        rtype="original",
                        data_root_dir=my_data_root_dir,
                        repr=my_repr
                        )

                    #add the ID entry to the data dict
                    data1.update({
                        "ID" : os.path.basename(my_work_dir),
                        "repr" : my_repr,
                        "process_id" : process_id
                        })
                    data2.update({
                        "ID" : os.path.basename(my_work_dir),
                        "repr" : my_repr,
                        "process_id" : process_id
                        })

                    if self.SecretSettings["throttle_strategy"] == True:
                        #too many jobs already running - put this in the queue
                        if len(self.indexing_active) >= \
                        self.SecretSettings["active_strategy_limit"]:
                            self.logger.debug("Adding pair indexing to the indexing queue")
                            self.indexing_queue.appendleft((
                                ("AUTOINDEX-PAIR",
                                 my_dirs,
                                 data1,
                                 data2,
                                 my_settings,
                                 (self.ip_address, self.socket)),
                                my_settings,
                                self.SecretSettings,
                                self.logger))
                        #go ahead and run, place marker in the queue
                        else:
                            #connect to the server and autoindex the single image
                            self.logger.debug("Less than two processes active \
                            - running autoindexing")
                            self.indexing_active.appendleft("autoindex-pair")
                            #connect to the server and get things done
                            PerformAction(
                                command=("AUTOINDEX-PAIR",
                                         my_dirs,
                                         data1,
                                         data2,
                                         my_settings,
                                         (self.ip_address, self.socket)),
                                settings=my_settings,
                                secret_settings=self.SecretSettings,
                                logger=self.logger
                                )
                    else:
                        #No throttling - go ahead and run
                        PerformAction(command=("AUTOINDEX-PAIR",
                                               my_dirs,
                                               data1,
                                               data2,
                                               my_settings,
                                               (self.ip_address, self.socket)),
                                      settings=my_settings,
                                      secret_settings=self.SecretSettings,
                                      logger=self.logger)


        #this is the runs portion of the data image handling
        else:
            self.logger.debug("This is a run")
            self.logger.debug(data)

            run_position = data["place_in_run"]

            self.logger.info("image_number:"+str(int(data["image_number"])))
            self.logger.info("run_id:"+str(run_id))
            self.logger.info("run_position:"+str(run_position))
            self.logger.info("run_total:"+str(run_total))

            #Make it easier to use run info
            run_dict = data["run"].copy()

            #the top level of the work directory
            #if self.Settings["work_dir_override"] == "False":
            #    my_toplevel_dir = self.start_dir
            #else:
            my_toplevel_dir = self.Settings["work_directory"]

            #the type level
            my_typelevel_dir = "integrate"
            #the date level
            my_datelevel_dir = datetime.date.today().isoformat()
            #the lowest level
            my_sub_dir = "_".join((str(data["image_prefix"]), str(data["run_number"])))
            #now construct the directory name
            my_work_dir_candidate = os.path.join(my_toplevel_dir,
                                                 my_typelevel_dir,
                                                 my_datelevel_dir,
                                                 my_sub_dir)
            #make sure this is an original directory
            if os.path.exists(my_work_dir_candidate):
                #we have already
                self.logger.debug("%s has already been used, will add qualifier" %
                                  my_work_dir_candidate)
                for i in range(1, 10000):
                    if not os.path.exists("_".join((my_work_dir_candidate, str(i)))):
                        my_work_dir_candidate = "_".join((my_work_dir_candidate, str(i)))
                        self.logger.debug("%s will be used for this image" % my_work_dir_candidate)
                        break
                    else:
                        i += 1
            my_work_dir = my_work_dir_candidate

            #now package directories into a dict for easy access by worker class
            my_dirs = {"work":my_work_dir,
                       "data_root_dir":my_data_root_dir}

            #create a represention of the process for display
            my_repr = my_sub_dir

            #if we are to integrate, do it
            try:
                #add the process to the database to display as in-process
                process_id = self.DATABASE.addNewProcess(type="integrate",
                                                         rtype="original",
                                                         data_root_dir=my_data_root_dir,
                                                         repr=my_repr)

                #Make a new result for the integration - should show up in the user interface?
                integrate_result_id, result_id = self.DATABASE.makeNewResult(rtype="integrate",
                                                                             process_id=process_id)

                #add the ID entry to the data dict
                data.update({"ID":os.path.basename(my_work_dir),
                             "repr":my_repr,
                             "process_id":process_id})

                #construct data for the processing
                out_data = {"run_data":run_dict,
                            "image_data":data}

                #connect to the server and autoindex the single image
                PerformAction(command=("INTEGRATE",
                                       my_dirs,
                                       out_data,
                                       my_settings,
                                       (self.ip_address, self.socket)),
                              settings=my_settings,
                              secret_settings=self.SecretSettings,
                              logger=self.logger)
            except:
                self.logger.exception("Exception when attempting to run RAPD \
                integration pipeline from Pilatus section")


    def Receive(self, message):
        """
        Receive information from ControllerServer (self.SERVER) and handle accordingly.

        Several return lengths are currently supported:
            2 - command, info
            3 - command, info, server
            5 - command,dirs,info,settings,results
            6 - command,dirs,info,settings,server,results
            7 - command, dirs, info1, info2, settings, server, results
        Otherwise the message will be taken as a naked command

        Several commands are handled:
            IMAGE STATUS CHANGED
            ADSC RUN STATUS CHANGED
            NEWIMAGE - new Pilatus image has arrived
            PILATUS RUN - new run in Pilatus style
            PILATUS_ABOORT - run has been aborted, Pilatus-style
            CONSOLE RUN STATUS CHANGED
            DIFF_CENTER
            QUICK_ANALYSIS
            STAC
            STAC-PAIR
            AUTOINDEX
            AUTOINDEX-PAIR
            INTEGRATE
            XDS - reintegration performed using the RAPD pipeline
            XIA2
            SMERGE
            BEAMCENTER
            SAD
            MAD
            MR
            STATS
            DOWNLOAD
            TEST
            SPEEDTEST
            DISTL_PARAMS_REQUEST - request from console for data
            CRYSTAL_PARAMS_REQUEST - request from console for data
        """

        self.logger.debug("Model::Receive")
        self.logger.debug("length returned %d" % len(message))
        self.logger.debug(message)

        try:
            #integrate
            if len(message) == 5:
                command, dirs, info, settings, results = message
            #autoindex,stac,diffcenter
            elif len(message) == 6:
                command, dirs, info, settings, server, results = message
            #autoindex-pair,stac-pair
            elif len(message) == 7:
                command, dirs, info1, info2, settings, server, results = message
            #download
            elif len(message) == 3:
                command, info, server = message
            elif len(message) == 2:
            #others
                command, info = message
            else:
                command = message
        except:
            #"OLD" format
            command = message

        #keep track adding to the database
        result_db = False
        trip_db = False

        # ADSC image - info is small dict from parsed xf_status
        if command == "IMAGE STATUS CHANGED":
            self.logger.debug("New image")
            self.add_adsc_image(info)

        # Pilatus image - info is fullname
        elif command == "NEWIMAGE":
            self.logger.debug("NEWIMAGE %s" % info)
            self.add_pilatus_image(info)

        elif command == "NEW HF4M IMAGE":
            self.logger.debug("NEW HF4M IMAGE %s" % info)
            self.addHf4mImage(info)

        # Pilatus run
        elif command == "PILATUS RUN":
            self.logger.debug("New pilatus run")
            self.logger.debug(info)
            #Save the current_run
            if self.current_run:
                self.past_runs.append(self.current_run.copy())
            #Set current_run to the new run
            self.current_run = info
            #Save to the database
            run_id = self.DATABASE.addRun(run=info,
                                          beamline=self.site)
            #Set the run_id that comes from the database for the current run
            if run_id:
                self.current_run["run_id"] = run_id

        elif command == "PILATUS_ABORT":
            self.logger.debug("Run aborted")
            if self.current_run:
                self.current_run["status"] = "ABORTED"

        elif command == "CONSOLE RUN STATUS CHANGED":
            #save to / check the db for this run
            self.logger.debug("get runid")
            run_id = self.DATABASE.addRun(run=info,
                                          beamline=self.site)
            self.logger.debug("run_id %s" % str(run_id))
            if self.current_run:
                if self.current_run["run_id"] == run_id:
                    self.logger.debug("Same run again")
                else:
                    self.logger.debug("New run %s" % str(info))
                    #save the current run
                    self.past_runs.append(self.current_run.copy())
                    #set current run to the new run
                    self.current_run = info
                    self.current_run["run_id"] = run_id
                    #self.sweepForMissedRunImages()
            else:
                self.logger.debug("New run %s" % str(info))
                #set current run to the new run
                self.current_run = info
                self.current_run["run_id"] = run_id

        elif command == "DIFF_CENTER":
            #add result to database
            result_db = self.DATABASE.addDiffcenterResult(dirs=dirs,
                                                          info=info,
                                                          settings=settings,
                                                          results=results)

            self.logger.debug("Added diffraction-based centering result: %s" % str(result_db))

            # Write the file for CONSOLE
            if result_db:
                TransferToBeamline(results=result_db,
                                   type="DIFFCENTER")

            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(process_id=info["process_id"],
                                               display_value="complete")

        elif command == "STAC":
            #add result to database
            result_db = self.DATABASE.addSingleResult(
                dirs=dirs,
                info=info,
                settings=settings,
                results=results
                )

            self.logger.debug("Added single result: %s", str(result_db))

            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(
                process_id=info["process_id"],
                display_value="complete"
                )
            #move the files to the server
            if result_db:
                #now mark the cloud database if this is a reprocess request
                if result_db["type"] in ("reprocess", "stac"):
                    #remove the process from cloud_current
                    self.DATABASE.removeCloudCurrent(
                        cloud_request_id=settings["request"]["cloud_request_id"]
                        )
                    #note the result in cloud_complete
                    self.DATABASE.enterCloudComplete(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        request_timestamp=settings["request"]["timestamp"],
                        request_type=settings["request"]["request_type"],
                        data_root_dir=settings["request"]["data_root_dir"],
                        ip_address=settings["request"]["ip_address"],
                        start_timestamp=settings["request"]["timestamp"],
                        result_id=result_db["result_id"],
                        archive=False
                        )
                    # Mark in cloud_requests
                    self.DATABASE.markCloudRequest(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        mark="complete"
                        )

                trip_db = self.DATABASE.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip(trip_id=record["trip_id"],
                                                 date=result_db["date"])
                        #now transfer the files
                        transferred = TransferToUI(
                            type="single",
                            settings=self.SecretSettings,
                            result=result_db,
                            trip=record,
                            logger=self.logger
                            )

                #this data is an "orphan"
                else:
                    self.logger.debug("Orphan result")
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult(
                        type="single",
                        root=dirs["data_root_dir"],
                        id=result_db["single_result_id"],
                        date=info["date"]
                        )
                    #copy the files to the UI host
                    dest = os.path.join(self.SecretSettings["ui_user_dir"], "orphans/single/")
                    #now transfer the files
                    transferred = TransferToUI(
                        type="single-orphan",
                        settings=self.SecretSettings,
                        result=result_db,
                        trip=trip_db,
                        logger=self.logger
                        )

            #the addition of result to db has failed, but still needs removed from the cloud
            else:
                if settings["request"]["request_type"] == "reprocess":
                    #remove the process from cloud_current
                    self.DATABASE.removeCloudCurrent(
                        cloud_request_id=settings["request"]["cloud_request_id"]
                        )
                    #note the result in cloud_complete
                    self.DATABASE.enterCloudComplete(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        request_timestamp=settings["request"]["timestamp"],
                        request_type=settings["request"]["request_type"],
                        data_root_dir=settings["request"]["data_root_dir"],
                        ip_address=settings["request"]["ip_address"],
                        start_timestamp=settings["request"]["timestamp"],
                        result_id=0,
                        archive=False
                        )
                    #mark in cloud_requests
                    self.DATABASE.markCloudRequest(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        mark="failure"
                        )

        elif command == "STAC-PAIR":
            #add result to database
            result_db = self.DATABASE.addPairResult(dirs=dirs,
                                                    info1=info1,
                                                    info2=info2,
                                                    settings=settings,
                                                    results=results)
            self.logger.debug("Added pair result: %s" % str(result_db))

            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(process_id=info1["process_id"],
                                               display_value="complete")

            #move the files to the server
            if result_db:
                #now mark the cloud database if this is a reprocess request
                if result_db["type"] in ("reprocess", "stac"):
                    #remove the process from cloud_current
                    self.DATABASE.removeCloudCurrent(
                        cloud_request_id=settings["request"]["cloud_request_id"])
                    #note the result in cloud_complete
                    self.DATABASE.enterCloudComplete(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        request_timestamp=settings["request"]["timestamp"],
                        request_type=settings["request"]["request_type"],
                        data_root_dir=settings["request"]["data_root_dir"],
                        ip_address=settings["request"]["ip_address"],
                        start_timestamp=settings["request"]["timestamp"],
                        result_id=result_db["result_id"],
                        archive=False
                        )
                    #mark in cloud_requests
                    self.DATABASE.markCloudRequest(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        mark="complete"
                        )

                trip_db = self.DATABASE.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip(trip_id=record["trip_id"],
                                                 date=result_db["date_2"])
                        #now transfer the files
                        transferred = TransferToUI(
                            type="pair",
                            settings=self.SecretSettings,
                            result=result_db,
                            trip=record,
                            logger=self.logger
                            )
                #this data is an "orphan"
                else:
                    self.logger.debug("Orphan result")
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult(type="pair",
                                                  root=dirs["data_root_dir"],
                                                  id=result_db["pair_result_id"],
                                                  date=info1["date"])
                    #copy the files to the UI host
                    dest = os.path.join(self.SecretSettings["ui_user_dir"], "orphans/pair/")
                    #now transfer the files
                    transferred = TransferToUI(
                        type="pair-orphan",
                        settings=self.SecretSettings,
                        result=result_db,
                        trip=trip_db,
                        logger=self.logger
                        )

            #the addition of result to db has failed, but still needs removed from the cloud
            else:
                if settings["request"]["request_type"] == "reprocess":
                    #remove the process from cloud_current
                    self.DATABASE.removeCloudCurrent(cloud_request_id=settings["request"]["cloud_request_id"])
                    #note the result in cloud_complete
                    self.DATABASE.enterCloudComplete(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        request_timestamp=settings["request"]["timestamp"],
                        request_type=settings["request"]["request_type"],
                        data_root_dir=settings["request"]["data_root_dir"],
                        ip_address=settings["request"]["ip_address"],
                        start_timestamp=settings["request"]["timestamp"],
                        result_id=0,
                        archive=False
                        )
                    #mark in cloud_requests
                    self.DATABASE.markCloudRequest(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        mark="failure"
                        )

        elif command == "AUTOINDEX":
            #Handle the ongoing throttling of autoindexing jobs
            if self.SecretSettings["throttle_strategy"] == True:
                #pop one marker off the indexing_active
                try:
                    self.indexing_active.pop()
                except:
                    pass
                if len(self.indexing_queue) > 0:
                    self.logger.debug("Running a command from the indexing_queue")
                    job = self.indexing_queue.pop()
                    self.indexing_active.appendleft("unknown")
                    #send the job to be done
                    PerformAction(command=job[0],
                                  settings=job[1],
                                  secret_settings=job[2],
                                  logger=job[3])

            #add result to database
            result_db = self.DATABASE.addSingleResult(dirs=dirs,
                                                      info=info,
                                                      settings=settings,
                                                      results=results)

            self.logger.debug("Added single result: %s" % str(result_db))

            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(process_id=info["process_id"],
                                               display_value="complete")

            #move the files to the server & other
            if result_db:

                #Update the Remote project
                if self.REMOTE:
                    wedges = self.DATABASE.getStrategyWedges(id=result_db["single_result_id"])
                    result_db["image_id"] = info["image_id"]
                    self.REMOTE.update_image_stats(result_db, wedges)

                #now mark the cloud database if this is a reprocess request
                if result_db["type"] in ("reprocess", "stac"):
                    #remove the process from cloud_current
                    self.DATABASE.removeCloudCurrent(
                        cloud_request_id=settings["request"]["cloud_request_id"]
                        )
                    #note the result in cloud_complete
                    self.DATABASE.enterCloudComplete(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        request_timestamp=settings["request"]["timestamp"],
                        request_type=settings["request"]["request_type"],
                        data_root_dir=settings["request"]["data_root_dir"],
                        ip_address=settings["request"]["ip_address"],
                        start_timestamp=settings["request"]["timestamp"],
                        result_id=result_db["result_id"],
                        archive=False
                        )
                    #mark in cloud_requests
                    self.DATABASE.markCloudRequest(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        mark="complete"
                        )

                trip_db = self.DATABASE.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip(
                            trip_id=record["trip_id"],
                            date=result_db["date"]
                            )
                        #now transfer the files
                        transferred = TransferToUI(
                            type="single",
                            settings=self.SecretSettings,
                            result=result_db,
                            trip=record,
                            logger=self.logger
                            )

                #this data is an "orphan"
                else:
                    self.logger.debug("Orphan result")
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult(
                        type="single",
                        root=dirs["data_root_dir"],
                        id=result_db["single_result_id"],
                        date=info["date"]
                        )
                    #copy the files to the UI host
                    dest = os.path.join(self.SecretSettings["ui_user_dir"], "orphans/single/")
                    #now transfer the files
                    transferred = TransferToUI(
                        type="single-orphan",
                        settings=self.SecretSettings,
                        result=result_db,
                        trip=trip_db,
                        logger=self.logger
                        )


            #the addition of result to db has failed, but still needs removed from the cloud
            else:
                if settings["request"]["request_type"] == "reprocess":
                    #remove the process from cloud_current
                    self.DATABASE.removeCloudCurrent(
                        cloud_request_id=settings["request"]["cloud_request_id"]
                        )
                    #note the result in cloud_complete
                    self.DATABASE.enterCloudComplete(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        request_timestamp=settings["request"]["timestamp"],
                        request_type=settings["request"]["request_type"],
                        data_root_dir=settings["request"]["data_root_dir"],
                        ip_address=settings["request"]["ip_address"],
                        start_timestamp=settings["request"]["timestamp"],
                        result_id=0,
                        archive=False
                        )
                    #mark in cloud_requests
                    self.DATABASE.markCloudRequest(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        mark="failure"
                        )


        elif command == "AUTOINDEX-PAIR":
            if self.SecretSettings["throttle_strategy"] == True:
                #pop one off the indexing_active
                try:
                    self.indexing_active.pop()
                except:
                    self.logger.exception("Error popping from self.indexing_active")
                if len(self.indexing_queue) > 0:
                    self.logger.debug("Running a command from the indexing_queue")
                    job = self.indexing_queue.pop()
                    self.indexing_active.appendleft("unknown")
                    PerformAction(command=job[0],
                                  settings=job[1],
                                  secret_settings=job[2],
                                  logger=job[3])

            result_db = self.DATABASE.addPairResult(
                dirs=dirs,
                info1=info1,
                info2=info2,
                settings=settings,
                results=results
                )
            self.logger.debug("Added pair result: %s" % str(result_db))

            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(process_id=info1["process_id"],
                                               display_value="complete")

            #move the files to the server
            if result_db:
                #now mark the cloud database if this is a reprocess request
                if result_db["type"] == "reprocess":
                    #remove the process from cloud_current
                    self.DATABASE.removeCloudCurrent(
                        cloud_request_id=settings["request"]["cloud_request_id"]
                        )
                    #note the result in cloud_complete
                    self.DATABASE.enterCloudComplete(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        request_timestamp=settings["request"]["timestamp"],
                        request_type=settings["request"]["request_type"],
                        data_root_dir=settings["request"]["data_root_dir"],
                        ip_address=settings["request"]["ip_address"],
                        start_timestamp=settings["request"]["timestamp"],
                        result_id=result_db["result_id"],
                        archive=False
                        )
                    #mark in cloud_requests
                    self.DATABASE.markCloudRequest(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        mark="complete"
                        )

                trip_db = self.DATABASE.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip(trip_id=record["trip_id"],
                                                 date=result_db["date_2"])
                        #now transfer the files
                        transferred = TransferToUI(type="pair",
                                                   settings=self.SecretSettings,
                                                   result=result_db,
                                                   trip=record,
                                                   logger=self.logger)
                #this data is an "orphan"
                else:
                    self.logger.debug("Orphan result")
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult(type="pair",
                                                  root=dirs["data_root_dir"],
                                                  id=result_db["pair_result_id"],
                                                  date=info["date"])
                    #now transfer the files
                    transferred = TransferToUI(type="pair-orphan",
                                               settings=self.SecretSettings,
                                               result=result_db,
                                               trip=trip_db,
                                               logger=self.logger)

            #the addition of result to db has failed, but still needs removed from the cloud
            else:
                if settings.has_key(["request"]):
                    if settings["request"]["request_type"] == "reprocess":
                        #remove the process from cloud_current
                        self.DATABASE.removeCloudCurrent(
                            cloud_request_id=settings["request"]["cloud_request_id"]
                            )
                        #note the result in cloud_complete
                        self.DATABASE.enterCloudComplete(
                            cloud_request_id=settings["request"]["cloud_request_id"],
                            request_timestamp=settings["request"]["timestamp"],
                            request_type=settings["request"]["request_type"],
                            data_root_dir=settings["request"]["data_root_dir"],
                            ip_address=settings["request"]["ip_address"],
                            start_timestamp=settings["request"]["timestamp"],
                            result_id=0,
                            archive=False
                            )
                        #mark in cloud_requests
                        self.DATABASE.markCloudRequest(
                            cloud_request_id=settings["request"]["cloud_request_id"],
                            mark="failure"
                            )

        # Integration
        elif command in ("INTEGRATE",):
            result_db = self.DATABASE.addIntegrateResult(dirs=dirs,
                                                         info=info,
                                                         settings=settings,
                                                         results=results)

            self.logger.debug("Added integration result: %s" % str(result_db))

            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(process_id=info["image_data"]["process_id"],
                                               display_value="complete")

            #move the files to the server
            if result_db:
                #Update the Remote project
                if self.REMOTE:
                    try:
                        wedges = self.DATABASE.getRunWedges(run_id=result_db["run_id"])
                    except:
                        self.logger.exception("Error in getting run wedges")
                    try:
                        self.REMOTE.update_run_stats(result_db=result_db, wedges=wedges)
                    except:
                        self.logger.exception("Error in updating run stats")

                trip_db = self.DATABASE.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip(trip_id=record["trip_id"],
                                                 date=result_db["date"])
                        #now transfer the files
                        transferred = TransferToUI(type="integrate",
                                                   settings=self.SecretSettings,
                                                   result=result_db,
                                                   trip=record,
                                                   logger=self.logger)
                #this data is an "orphan"
                else:
                    self.logger.debug("Orphan result")
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult(type="integrate",
                                                  root=dirs["data_root_dir"],
                                                  id=result_db["integrate_result_id"],
                                                  date=result_db["date"])

                    #now transfer the files
                    transferred = TransferToUI(type="integrate-orphan",
                                               settings=self.SecretSettings,
                                               result=result_db,
                                               trip=trip_db,
                                               logger=self.logger)

            #now place the files in the data_root_dir for the user to have and to hold
            if self.SecretSettings["copy_data"]:
                copied = CopyToUser(root=dirs["data_root_dir"],
                                    res_type="integrate",
                                    result=result_db,
                                    logger=self.logger)
            #the addition of result to db has failed, but still needs removed from the cloud
            #this is not YET an option so pass for now
            else:
                pass

        # Reintegration using RAPD pipeline
        elif command in ("XDS", "XIA2"):
            result_db = self.DATABASE.addReIntegrateResult(dirs=dirs,
                                                           info=info,
                                                           settings=settings,
                                                           results=results)
            self.logger.debug("Added reintegration result: %s" % str(result_db))

            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(process_id=settings["process_id"],
                                               display_value="complete")

            #move the files to the server
            if result_db:
                trip_db = self.DATABASE.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip(trip_id=record["trip_id"],
                                                 date=result_db["date"])
                        #now transfer the files
                        transferred = TransferToUI(type="integrate",
                                                   settings=self.SecretSettings,
                                                   result=result_db,
                                                   trip=record,
                                                   logger=self.logger)
                #this data is an "orphan"
                else:
                    self.logger.debug("Orphan result")
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult(
                        type="integrate",
                        root=dirs["data_root_dir"],
                        id=result_db["integrate_result_id"],
                        date=result_db["date"]
                        )

                    #now transfer the files
                    transferred = TransferToUI(
                        type="integrate-orphan",
                        settings=self.SecretSettings,
                        result=result_db,
                        trip=trip_db,
                        logger=self.logger
                        )

            #now place the files in the data_root_dir for the user to have and to hold
            if self.SecretSettings["copy_data"]:
                copied = CopyToUser(root=dirs["data_root_dir"],
                                    res_type="integrate",
                                    result=result_db,
                                    logger=self.logger)
            #the addition of result to db has failed, but still needs removed from the cloud
            #this is not YET an option so pass for now
            else:
                pass

        # Merging two wedges
        elif command == "SMERGE":
            self.logger.debug("SMERGE Received")
            self.logger.debug(dirs)
            self.logger.debug(info)
            self.logger.debug(settings)
            self.logger.debug(results)


            result_db = self.DATABASE.addSimpleMergeResult(dirs=dirs,
                                                           info=info,
                                                           settings=settings,
                                                           results=results)
            self.logger.debug("Added simple merge result: %s" % str(result_db))

            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(process_id=result_db["process_id"],
                                               display_value="complete")

            #move the files to the server
            if result_db:
                trip_db = self.DATABASE.getTrips(data_root_dir=dirs["data_root_dir"])
                self.logger.debug(trip_db)
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #now transfer the files
                        transferred = TransferToUI(type="smerge",
                                                   settings=self.SecretSettings,
                                                   result=result_db,
                                                   trip=record,
                                                   logger=self.logger)
                #this data is an "orphan"
                else:
                    self.logger.debug("Orphan result")
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult(type="smerge",
                                                  root=dirs["data_root_dir"],
                                                  id=result_db["integrate_result_id"],
                                                  date=result_db["date"])

                    #now transfer the files
                    transferred = TransferToUI(type="smerge-orphan",
                                               settings=self.SecretSettings,
                                               result=result_db,
                                               trip=trip_db,
                                               logger=self.logger)

                #now place the files in the data_root_dir for the user to have and to hold
                if self.SecretSettings["copy_data"]:
                    copied = CopyToUser(root=dirs["data_root_dir"],
                                        res_type="smerge",
                                        result=result_db,
                                        logger=self.logger)
                #the addition of result to db has failed, but still needs removed from the cloud
                #this is not YET an option so pass for now
                else:
                    pass


        # Merging two wedges
        elif command == "BEAMCENTER":
            self.logger.debug("BEAMCENTER Received")
            self.logger.debug(dirs)
            self.logger.debug(info)
            self.logger.debug(settings)
            self.logger.debug(results)

        elif command == "SAD":
            self.logger.debug("Received SAD result")
            result_db = self.DATABASE.addSadResult(dirs=dirs,
                                                   info=info,
                                                   settings=settings,
                                                   results=results)
            self.logger.debug("Added SAD result: %s" % str(result_db))

            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(process_id=settings["process_id"],
                                               display_value="complete")

            #move the files to the server
            if result_db:
                trip_db = self.DATABASE.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip(trip_id=record["trip_id"],
                                                 date=result_db["timestamp"])
                        #now transfer the files
                        transferred = TransferToUI(
                            type="sad",
                            settings=self.SecretSettings,
                            result=result_db,
                            trip=record,
                            logger=self.logger
                            )
                #this data is an "orphan"
                else:
                    self.logger.debug("Orphan result")
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult(
                        type="sad",
                        root=dirs["data_root_dir"],
                        id=result_db["sad_result_id"],
                        date=result_db["date"]
                        )

                    #now transfer the files
                    transferred = TransferToUI(type="sad-orphan",
                                               settings=self.SecretSettings,
                                               result=result_db,
                                               trip=trip_db,
                                               logger=self.logger)

            #now place the files in the data_root_dir for the user to have and to hold
            if self.SecretSettings["copy_data"]:
                if result_db["download_file"] != "None":
                    copied = CopyToUser(root=dirs["data_root_dir"],
                                        res_type="sad",
                                        result=result_db,
                                        logger=self.logger)
            #the addition of result to db has failed, but still needs removed from the cloud
            #this is not YET an option so pass for now
            else:
                pass

        elif command == "MAD":
            self.logger.debug("Received MAD result")

            result_db = self.DATABASE.addMadResult(dirs=dirs,
                                                   info=info,
                                                   settings=settings,
                                                   results=results)
            self.logger.debug("Added MAD result: %s" % str(result_db))

            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(process_id=settings["process_id"],
                                               display_value="complete")

            #move the files to the server
            if result_db:
                trip_db = self.DATABASE.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip(trip_id=record["trip_id"],
                                                 date=result_db["timestamp"])
                        #now transfer the files
                        transferred = TransferToUI(type="mad",
                                                   settings=self.SecretSettings,
                                                   result=result_db,
                                                   trip=record,
                                                   logger=self.logger)

            #now place the files in the data_root_dir for the user to have and to hold
            if self.SecretSettings["copy_data"]:
                if (result_db["download_file"] not in ["None", "FAILED"]):
                    copied = CopyToUser(root=dirs["data_root_dir"],
                                        res_type="mad",
                                        result=result_db,
                                        logger=self.logger)
            #the addition of result to db has failed, but still needs removed from the cloud
            #this is not YET an option so pass for now
            else:
                pass

        elif command == "MR":
            self.logger.debug("Received MR result")
            result_db = self.DATABASE.addMrResult(dirs=dirs,
                                                  info=info,
                                                  settings=settings,
                                                  results=results)
            #some debugging output
            self.logger.debug("Added MR result: %s" % str(result_db))

            #If the process is complete, mark it as such
            if result_db["mr_status"] != "WORKING":
                #mark the process as finished
                self.DATABASE.modifyProcessDisplay(process_id=result_db["process_id"],
                                                   display_value="complete")
            #move the files to the server
            if result_db:
                #Get the trip for this data
                trip_db = self.DATABASE.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip(trip_id=record["trip_id"],
                                                 date=result_db["timestamp"])
                        #now transfer the files
                        transferred = TransferToUI(type="mr",
                                                   settings=self.SecretSettings,
                                                   result=result_db,
                                                   trip=record,
                                                   logger=self.logger)

            #now place the files in the data_root_dir for the user to have and to hold
            if  self.SecretSettings["copy_data"]:
                all_mr_results = self.DATABASE.getMrTrialResult(result_db["mr_result_id"])
                #some debugging output
                self.logger.debug("Transfer MR file: ID %s" % result_db["mr_result_id"])
                if all_mr_results:
                    for mr_result in all_mr_results:
                        result_db["download_file"] = mr_result["archive"]
                        copied = CopyToUser(root=dirs["data_root_dir"],
                                            res_type="mr",
                                            result=result_db,
                                            logger=self.logger)

            #the addition of result to db has failed, but still needs removed from the cloud
            #this is not YET an option so pass for now
            else:
                pass


        elif command == "DOWNLOAD":
            #get the trip info
            trip_db = self.DATABASE.getTrips(data_root_dir=info["data_root_dir"])

            success = False
            if trip_db:
                for record in trip_db:
                    #move files to the server
                    transferred = TransferToUI(
                        type="download",
                        settings=self.SecretSettings,
                        result=info,
                        trip=record,
                        logger=self.logger
                        )
                    if transferred:
                        success = True

            #update the database
            if success:
                #note the result in cloud_complete
                self.DATABASE.enterCloudComplete(cloud_request_id=info["cloud_request_id"],
                                                 request_timestamp=info["timestamp"],
                                                 request_type=info["request_type"],
                                                 data_root_dir=info["data_root_dir"],
                                                 ip_address=info["ip_address"],
                                                 start_timestamp=0,
                                                 result_id=0,
                                                 archive=os.path.basename(info["archive"]))

                #mark in cloud_requests
                self.DATABASE.markCloudRequest(
                    cloud_request_id=info["cloud_request_id"],
                    mark="complete"
                    )

            #the transfer was not successful
            else:
                #note the result in cloud_complete
                self.DATABASE.enterCloudComplete(cloud_request_id=info["cloud_request_id"],
                                                 request_timestamp=info["timestamp"],
                                                 request_type=info["request_type"],
                                                 data_root_dir=info["data_root_dir"],
                                                 ip_address=info["ip_address"],
                                                 start_timestamp=0,
                                                 result_id=0,
                                                 archive=os.path.basename(info["archive"]))

                #mark in cloud_requests
                self.DATABASE.markCloudRequest(cloud_request_id=info["cloud_request_id"],
                                               mark="failure")

        elif command == "STATS":
            self.logger.debug("Received STATS result")

            #rearrange results
            results = server.copy()

            #self.logger.debug(info)
            #self.logger.debug(results)
            result_db = self.DATABASE.addStatsResults(info=info,
                                                      results=results)
            self.logger.debug("Added STATS result: %s" % str(result_db))

            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(process_id=info["process_id"],
                                               display_value="complete")

            #move the files to the server
            if result_db:
                #Get the trip for this data
                trip_db = self.DATABASE.getTrips(result_id=result_db["result_id"])
                #print trip_db
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip(trip_id=record["trip_id"],
                                                 date=result_db["timestamp"])
                        #now transfer the files
                        transferred = TransferToUI(type="stats",
                                                   settings=self.SecretSettings,
                                                   result=result_db,
                                                   trip=record,
                                                   logger=self.logger)
                #this data is an "orphan"
                else:
                    self.logger.debug("Orphan result")
                    #now transfer the files
                    transferred = TransferToUI(type="stats-orphan",
                                               settings=self.SecretSettings,
                                               result=result_db,
                                               trip=trip_db,
                                               logger=self.logger)

        elif command == "TEST":

            self.logger.debug("Cluster connection test successful")

        elif command == "SPEEDTEST":
            self.logger.debug("Cluster connection test successful")

        elif command == "DISTL_PARMS_REQUEST":
            self.logger.debug("DISTL params request for %s" % info)
            cf = ConsoleFeeder(mode="DISTL_PARMS_REQUEST",
                               db=self.DATABASE,
                               bc=self.BEAMLINE_CONNECTION,
                               data=info,
                               logger=self.logger)

        elif command == "CRYSTAL_PARMS_REQUEST":
            self.logger.debug("CRYSTAL params request for %s" % info)
            cf = ConsoleFeeder(mode="CRYSTAL_PARMS_REQUEST",
                               db=self.DATABASE,
                               bc=self.BEAMLINE_CONNECTION,
                               data=info,
                               logger=self.logger)

        elif command == "BEST_PARMS_REQUEST":
            self.logger.debug("BEST params request for %s" % info)
            cf = ConsoleFeeder(mode="BEST_PARMS_REQUEST",
                               db=self.DATABASE,
                               bc=self.BEAMLINE_CONNECTION,
                               data=info,
                               logger=self.logger)

        else:
            self.logger.info("Take no action for message")
            self.logger.info(message)

class StatusHandler(threading.Thread):
    """
    Handles logging of life for the RAPD Core process.
    """

    def __init__(self, db, ip_address, data_root_dir, beamline, dataserver_ip,
                 cluster_ip, logger):
        """
        Initialize the instance by saving variables.

        db - a connection to the rapd database instance
        ip_address - ip address of this model
        data_root_dir - the current data root directory
        beamline - the beamline desgnation for this rapd_model
        dataserver_ip - ip address of the computer hosting the process watching data collection
        cluster_ip - the ip address of the cluster which this rapd_model is sending jobs to
        logger - logger instance

        """

        logger.info("StatusHandler::__init__")

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.DATABASE = db
        self.ip_address = ip_address
        self.data_root_dir = data_root_dir
        self.site = beamline
        self.dataserver_ip = dataserver_ip
        self.cluster_ip = cluster_ip
        self.logger = logger

        #start the thread
        self.start()

    def run(self):
        """
        Starts the thread going.
        """

        self.logger.debug("StatusHandler::run")
        while True:
            #log the status of this Thread (the controller process)
            self.DATABASE.update_controller_status(controller_ip=self.ip_address,
                                                   data_root_dir=self.data_root_dir,
                                                   beamline=self.site,
                                                   dataserver_ip=self.dataserver_ip,
                                                   cluster_ip=self.cluster_ip)
            #now wait before next update
            time.sleep(30)

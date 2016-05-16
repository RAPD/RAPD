"""
Code for the coordination of site activities for a RAPD install - the monitoring
of data collection and the "cloud", as well as the running of processes and
logging of all metadata
"""

__license__ = """
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

# Standard imports
import collections
import datetime
import importlib
import logging
import os
import socket

# RAPD imports
from control.control_server import LaunchAction, ControllerServer
from utils.modules import load_module
from utils.site import get_ip_address
# from rapd_console import ConsoleFeeder
# from rapd_site import TransferToUI, TransferToBeamline, CopyToUser

# cloud_monitor = None
site_adapter = None
remote_adapter = None

#####################################################################
# The main Model Class                                              #
#####################################################################
class Model(object):
    """
    Main controller code for a RAPD site install
    """

    # Site instance data
    site_ids = []
    detectors = {}

    # Keeping track of image pairs
    pairs = {}
    pair_ids = {}

    # Controlling simultaneous image processing
    indexing_queue = collections.deque()
    indexing_active = collections.deque()

    # Managing runs and images without going to the db
    current_run = {}
    recent_runs = collections.deque(maxlen=1000)

    data_root_dir = None
    database = None

    server = None
    return_address = None

    image_monitor = None
    current_image = None
    # image_monitor_reconnect_attempts = 0

    cloud_monitor = None
    site_adapter = None
    remote_adapter = None

    def __init__(self, SITE, overwatch_id=None):
        """
        Save variables and start the process activity

        Keyword arguments
        SITE -- Site settings object
        overwatch_id -- id for optional overwatcher (default False)
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")

        # Passed-in variables
        self.site = SITE
        self.overwatch_id = overwatch_id

        # Instance variables
        try:
            self.return_address = (get_ip_address(), SITE.CONTROL_PORT)
        except socket.gaierror:
            self.return_address = ("127.0.0.1", SITE.CONTROL_PORT)

        self.logger.debug("self.return_address:%s", self.return_address)

        # Start the process
        self.run()

    def run(self):
        """
        Initialize monitoring the beamline.
        """

        self.logger.debug("Starting")

        # Process the site
        self.init_site()

        # Start connection to the core database
        self.connect_to_database()

        # Start the server for receiving communications
        self.start_server()

        # Import the detector
        self.init_detectors()

        # Start the run monitor
        self.start_run_monitor()

        # Start the image monitor
        self.start_image_monitor()

        # Start the cloud monitor
        # self.start_cloud_monitor()

        # Initialize the site adapter
        # self.init_site_adapter()

        # Initialize the remote adapter
        # self.init_remote_adapter()

        # # TESTING
        # while True:
        #     time.sleep(5)
        #     LaunchAction(command={"command":"ECHO",
        #                           "message":"Hello, world!",
        #                           "preferences":{},
        #                           "return_address":self.return_address},
        #                  #  launcher_address=("164.54.212.15", 50000),
        #                  launcher_address=("164.54.208.135", 50000),
        #                  settings=None)
        #
        #     preferences = {"strategy_type":"best", #Preferred program for strategy
        #                    "crystal_size_x":"100", #RADDOSE
        #                    "crystal_size_y":"100", #RADDOSE
        #                    "crystal_size_z":"100", #RADDOSE
        #                    "shape":"2.0", #BEST
        #                    "sample_type":"Protein", #LABELIT, BEST
        #                    "best_complexity":"none", #BEST
        #                    "susceptibility":"1.0", #BEST
        #                    "index_hi_res":0.0, #LABELIT
        #                    "spacegroup":"None", #LABELIT, BEST, beam_center
        #                    "solvent_content":0.55, #RADDOSE
        #                    "beam_flip":"False", #NECAT, when x and y are sent reversed.
        #                    "multiprocessing":"True", # Faster
        #                    "x_beam":"0",#Used if position not in header info
        #                    "y_beam":"0",#Used if position not in header info
        #                    "aimed_res":0.0, #BEST to override high res limit
        #                    "a":0.0, ##LABELIT
        #                    "b":0.0, ##LABELIT
        #                    "c":0.0, ##LABELIT
        #                    "alpha":0.0, #LABELIT
        #                    "beta":0.0, #LABELIT
        #                    "gamma":0.0, #LABELIT
        #                    #Change these if user wants to continue dataset with other crystal(s).
        #                    "reference_data_id": None, #MOSFLM
        #                    "reference_data": [
        #                        ["/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat",
        #                         0.0,
        #                         20.0,
        #                         "junk",
        #                         "P3"],
        #                        ["/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat",
        #                         40.0,
        #                         50.0,
        #                         "junk2",
        #                         "P3"]],
        #                    "mosflm_rot": 0.0, #MOSFLM
        #                    "mosflm_seg":1, #MOSFLM
        #                    "mosflm_start":0.0,#MOSFLM
        #                    "mosflm_end":360.0,#MOSFLM
        #                 }
        #     header1 = {"wavelength":1.000, #RADDOSE
        #                "detector":"ray300",
        #                "binning":"none", #
        #                "time":"1.00",  #BEST
        #                "twotheta":"0.00", #LABELIT
        #                "transmission":"20",  #BEST
        #                "osc_range":1.0,
        #                "distance":200.0,
        #                "count_cutoff":65535,
        #                "omega_start":0.0,
        #                "beam_center_x":"149.87", #22ID
        #                "beam_center_y":"145.16", #22ID
        #                "flux":"1.6e11", #RADDOSE
        #                "beam_size_x":"0.07", #RADDOSE
        #                "beam_size_y":"0.03", #RADDOSE
        #                "gauss_x":"0.03", #RADDOSE
        #                "gauss_y":"0.01", #RADDOSE
        #                "fullname":"/panfs/panfs0.localdomain/archive/ID_16_02_04_chrzas_feb_4_2016/SER4-TRYP_Pn3/SER4-TRYP_Pn3.0001",
        #                "phi":"0.000",
        #                "STAC file1":"/gpfs6/users/necat/Jon/RAPD_test/mosflm.mat", #XOAlign
        #                "STAC file2":"/gpfs6/users/necat/Jon/RAPD_test/bestfile.par", #XOAlign
        #                "axis_align":"long",    #long,all,a,b,c,ab,ac,bc #XOAlign
        #               }
        #     # LaunchAction(command={"command":"AUTOINDEX+STRATEGY",
        #     #                       "directories":{"work":"/home/schuerjp/temp"},
        #     #                       "header1":header1,
        #     #                       "header2":False,
        #     #                       "preferences":preferences,
        #     #                       "return_address":self.return_address
        #     #                      },
        #     #              # launcher_address=("164.54.212.15", 50000),
        #     #              launcher_address=("164.54.208.135", 50000),
        #     #              settings=None)
        #     time.sleep(60)

    def init_site(self):
        """Process the site definitions to set up instance variables"""

        # Single or multiple IDs
        # A string is input - one tag
        if isinstance(self.site.ID, str):
            self.site_ids = [self.site.ID]
            self.pairs[self.site.ID] = collections.deque(["", ""], 2)
            self.pair_ids[self.site.ID] = collections.deque(["", ""], 2)

        # Tuple or list
        elif isinstance(self.site.ID, tuple) or isinstance(self.site.ID, list):
            for site_id in self.site.ID:
                self.site_ids.append(site_id)
                self.pairs[site_id] = collections.deque(["", ""], 2)
                self.pair_ids[site_id] = collections.deque(["", ""], 2)

    def connect_to_database(self):
        """Set up database connection"""

        # Import the database adapter as database module
        # global database
        database = importlib.import_module('database.rapd_%s_adapter' % self.site.CONTROL_DATABASE)

        # Shorten it a little
        site = self.site

        # Instantiate the database connection
        self.database = database.Database(host=site.CONTROL_DATABASE_HOST,
                                          port=site.CONTROL_DATABASE_PORT,
                                          user=site.CONTROL_DATABASE_USER,
                                          password=site.CONTROL_DATABASE_PASSWORD)

    def start_server(self):
        """Start up the listening process for core"""

        self.server = ControllerServer(receiver=self.receive,
                                       port=self.site.CONTROL_PORT)

    def stop_server(self):
        """Stop the listening server on exit"""

        self.logger.debug("Stop core server")

        self.server.stop()

    def init_detectors(self):
        """Set up the detectors"""

        self.logger.debug("Setting up the detectors")

        # Shorten variable names
        site = self.site

        # A single detector
        if site.DETECTOR:
            detector, suffix = site.DETECTOR
            detector = detector.lower()
            # self.detectors[self.site_ids[0].lower()] = importlib.import_module("detectors.%s" % detector)
            self.detectors[self.site_ids[0].lower()] = load_module(detector, ("sites.detectors", "detectors"))

        # Multiple detectors
        elif site.DETECTORS:
            for site_id in self.site_ids:
                detector, suffix = site.DETECTORS[site_id]
                detector = detector.lower()
                # self.detectors[site_id.lower()] = importlib.import_module("detectors.%s" % detector)
                self.detectors[site_id.lower()] = load_module(detector, ("sites.detectors", "detectors"))

    def start_image_monitor(self):
        """Start up the image listening process for core"""

        self.logger.debug("Starting image monitor")

        # Shorten variable names
        site = self.site

        if site.IMAGE_MONITOR:
            # global image_monitor
            image_monitor = importlib.import_module("%s" % site.IMAGE_MONITOR.lower())

            # Instantiate the monitor
            self.image_monitor = image_monitor.Monitor(
                site=site,
                notify=self.receive,
                overwatch_id=self.overwatch_id)

    def start_run_monitor(self):
        """Start up the run information listening process for core"""

        self.logger.debug("Starting run monitor")

        # Shorten variable names
        site = self.site

        if site.RUN_MONITOR:
            # Import the specific run monitor module
            run_monitor = importlib.import_module("%s" % site.RUN_MONITOR.lower())
            self.logger.debug(run_monitor)
            self.run_monitor = run_monitor.Monitor(site=self.site,
                                                   notify=self.receive,
                                                   # Not using overwatch in run monitor - could if we wanted to
                                                   overwatch_id=None)

    def start_cloud_monitor(self):
        """Start up the cloud listening process for core"""

        # Shorten variable names
        site = self.site

        if site.CLOUD_MONITOR:
            # Import the specific cloud monitor as cloud_monitor module
            # global cloud_monitor
            cloud_monitor = importlib.import_module("%s" % site.CLOUD_MONITOR.lower())
            self.cloud_monitor = cloud_monitor.CloudMonitor(database=self.database,
                                                            settings=site.CLOUD_MONITOR_SETTINGS,
                                                            reply_settings=self.return_address,
                                                            interval=site.CLOUD_INTERVAL)

    def init_site_adapter(self):
        """Initialize the connection to the site"""

        # Shorten variable names
        site = self.site

        if site.SITE_ADAPTER:
            global site_adapter
            site_adapter = importlib.import_module("%s" % site.SITE_ADAPTER.lower())
            self.site_adapter = site_adapter.Adapter(settings=site.SITE_ADAPTER_SETTINGS)

    def init_remote_adapter(self):
        """Initialize connection to remote access system"""

        # Shorten variable names
        site = self.site

        if site.REMOTE_ADAPTER:
            global remote_adapter
            remote_adapter = importlib.import_module("%s" % site.REMOTE_ADAPTER.lower())
            self.remote_adapter = remote_adapter.Adapter(settings=site.REMOTE_ADAPTER_SETTINGS)

    def stop(self):
        """
        Stop the ImageMonitor,CloudMonitor and StatusRegistrar.
        """
        self.logger.info("Stopping")

    def add_image(self, image_data):
        """Handle a new image being recorded by the site"""

        # Unpack image_data
        fullname = image_data.get("fullname", None)
        site_tag = image_data.get("site_tag", None)

        self.logger.debug("Received new image %s", fullname)

        # Shortcut to detector
        detector = self.detectors[site_tag]

        # Save some typing
        dirname = os.path.dirname(fullname)

        # Directory is to be ignored
        if dirname in self.site.IMAGE_IGNORE_DIRECTORIES:
            self.logger.debug("Directory %s is marked to be ignored - skipping", dirname)
            return True

        # File contains an ingnore flag
        if any(ignore_string in fullname for ignore_string in self.site.IMAGE_IGNORE_STRINGS):
            self.logger.debug("Images contains an ignore flag - skipping")
            return True

        # Save current image to class-level variable
        self.current_image = fullname

        # Derive the data_root_dir
        data_root_dir = detector.get_data_root_dir(fullname)

        # Figure out if image in the current run...
        place, run_info = self.in_run(site_tag, fullname)

        # Image is in the current run
        if isinstance(place, int) and run_info == "current_run":

            self.logger.debug("%s is in the current run at position %d", fullname, place)

            # If not integrating trigger integration
            if self.current_run["status"] != "INTEGRATING":

                # Handle getting to the party late
                if place != 1:
                    self.logger.info("Creating first image in run")
                    first_image_fullname = detector.create_image_fullname(
                        directory=self.current_run["directory"],
                        image_prefix=self.current_run["image_prefix"],
                        run_number=self.current_run["run_number"],
                        image_number=self.current_run["start"])

                # Right on time
                else:
                    first_image_fullname = fullname

                header = detector.read_header(fullname=first_image_fullname,
                                              run_id=self.current_run["run_id"],
                                              place_in_run=1)

                # Add some data to the header
                header["run_id"] = self.current_run["run_id"]
                header["data_root_dir"] = data_root_dir

                # Add to database
                db_result = self.database.add_image(header)

                # Duplicate entry
                if db_result == False:
                    return False
                else:
                    header.update(db_result)

                # Mark the run as INTEGRATING
                self.current_run["status"] = "INTEGRATING"

                # Put data about run in the header object
                header["run"] = self.current_run.copy()

                # KBO
                self.new_data_image(header=header)

        # Image is a snap
        elif place == "SNAP":

            self.logger.debug("%s is a snap", fullname)

            # Get all the image information
            header = detector.read_header(fullname=fullname,
                                          beam_settings=self.site.BEAM_INFO[site_tag.upper()])

            # Add some data to the header - no run_id for snaps
            header["collect_mode"] = "SNAP"
            header["run_id"] = None
            header["site_tag"] = site_tag

            # Grab extra data for the image and add to the header
            if self.site_adapter:
                site_data = self.site_adapter.get_image_data()
                header.update(site_data)

            # Add to database
            db_result = self.database.add_image(header)

            # Duplicate entry
            if db_result == False:
                return False
            else:
                header.update(db_result)

            # Update remote client
            if self.remote_adapter:
                self.remote_adapter.add_image(header)

            # KBO
            self.new_data_image(header=header)

        # Image is in a past run
        elif isinstance(place, int) and isinstance(run_info, dict):

            self.logger.debug("%s is in a past run", fullname)

            # Figure out if image in the current run...
            past_place, past_run_info = self.in_past_run(fullname)

            if isinstance(past_place, int):

                self.logger.debug("Have past run data for %s", fullname)

            elif past_place == False:

                self.logger.debug("Unable to find past run data for %s", fullname)

        # No information is findable
        else:
            self.logger.debug("Unable to figure out %s", fullname)

    def add_run(self, run_dict):
        """
        Add potentially new run to RAPD system

        Keyword arguments
        run_data -- dict containing data describing the run
        """

        # Unpack the run_dict
        run_data = run_dict["run_data"]
        site_tag = run_dict["site_tag"]

        # Check if this run has already been collected - could be an array of dicts
        # that are runs that match or a False
        recent_run_data = self.database.get_run_data(site_tag=site_tag,
                                                     run_data=run_data,
                                                     minutes=60,
                                                     boolean=True)

        if recent_run_data != False:

            self.logger.debug("This run has already been recorded")

        else:

            # Save to the database
            run_id = self.database.add_run(site_tag=site_tag,
                                           run_data=run_data)

            # Save the current_run to somewhere handy
            if self.current_run:
                self.recent_runs.append(self.current_run.copy())

            # Set current_run to the new run
            self.current_run = run_data

            # Set the run_id that comes from the database for the current run
            if run_id:
                self.current_run["run_id"] = run_id


    # def add_adsc_image(self, data):
    #
    #     Handle an image to be added to the database from ADSC.
    #
    #     The image is NOT presumed to be new, so it is checked against the database.
    #     There are several classes of images that are sorted out here:
    #         data - snaps and runs
    #         ignore - image ignored
    #                  tag defined in rapd_site ignore_tag
    #
    #     """
    #     self.logger.debug("Model::add_adsc_image %s" % data["image_name"])
    #
    #     #reset the reconnect attempts to 0 since we have connected
    #     self.imagemonitor_reconnect_attempts = 0
    #
    #     #Save current image in class-level variable
    #     fullname = data["image_name"]
    #     dirname = os.path.dirname(fullname)
    #     self.current_image = fullname
    #
    #     # Skip any handling?
    #     if dirname in self.Settings["analysis_shortcircuits"]:
    #         self.logger.info("Short-circuit")
    #
    #     # Go ahead and handle the image
    #     else:
    #
    #         # Derive the data_root_dir
    #         my_data_root_dir = GetDataRootDir(fullname=fullname,
    #                                           logger=self.logger)
    #
    #         # Figure out if image in the current run...
    #         place = self.in_current_run(fullname)
    #
    #         # Image is in the current run
    #         if isinstance(place, int):
    #
    #             self.logger.info("%s in current run at position %d" % (fullname,
    #                                                                    place))
    #
    #             # If not integrating trigger integration
    #             if self.current_run["status"] != "INTEGRATING":
    #
    #                 # Handle getting to the party late
    #                 if place != 1:
    #                     self.logger.info("Creating first image in run")
    #                     fullname = "%s/%s_%03d.%s" % (
    #                         self.current_run["directory"],
    #                         self.current_run["image_prefix"],
    #                         int(self.current_run["start"]),
    #                         self.current_run["image_suffix"])
    #
    #                 # Right on time
    #                 else:
    #                     pass
    #                     # fullname = data["image_name"]
    #
    #                 #Get all the image information
    #                 header = self.get_adsc_header(
    #                     fullname=fullname,
    #                     run_id=self.current_run["run_id"],
    #                     drd=my_data_root_dir,
    #                     adsc_number=data["adsc_number"],
    #                     place=1)
    #
    #                 #Add to database
    #                 db_result, __ = self.database.add_image(header)
    #                 header.update(db_result)
    #
    #                 self.current_run["status"] = "INTEGRATING"
    #                 header["run"] = self.current_run.copy()
    #                 self.new_data_image(header=header)
    #
    #         # Image is not in the current run
    #         else:
    #
    #             # Image is a snap
    #             if place == "SNAP":
    #
    #                 self.logger.debug("%s is a snap" % fullname)
    #
    #                 #Get all the image information
    #                 header = self.get_adsc_header(
    #                     fullname=data["image_name"],
    #                     run_id=0,
    #                     drd=my_data_root_dir,
    #                     adsc_number=data["adsc_number"])
    #
    #                 # Add to database
    #                 db_result, __ = self.database.add_image(header)
    #                 header.update(db_result)
    #
    #                 # Run the image as a new data image
    #                 self.new_data_image(header=header)
    #
    #             # Image is in a past run
    #             elif place == "PAST_RUN":
    #                 self.logger.info("In past run")
    #                 my_place, run = self.in_past_run(fullname)
    #
    #                 if run:
    #                     if my_place == run["total"]:
    #                         self.logger.info("Final image in past run")
    #
    #                         #Get all the image information
    #                         header = self.get_adsc_header(
    #                             fullname=data["image_name"],
    #                             run_id=run["run_id"],
    #                             drd=my_data_root_dir,
    #                             adsc_number=data["adsc_number"],
    #                             place=my_place)
    #
    #                         #Add to database
    #                         db_result, __ = self.database.add_image(header)
    #                         header.update(db_result)
    #
    #                         #tag the header with run data
    #                         header["run"] = run.copy()
    #
    #                         #Now trigger integration - if not integrating
    #                         if run["status"] != "INTEGRATING":
    #                             run["status"] = "INTEGRATING"
    #                             self.new_data_image(header=header)

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
                    db_result, status = self.database.add_pilatus_image(header)
                    header.update(db_result)
                    header["run"] = self.current_run

                    self.current_run["status"] = "INTEGRATING"
                    self.new_data_image(header=header)

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
                    db_result, status = self.database.add_pilatus_image(header)
                    header.update(db_result)

                    #Run the image as a new data image
                    self.new_data_image(header=header)

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
                            db_result, status = self.database.add_pilatus_image(header)
                            header.update(db_result)

                            #tag the header with run data
                            header["run"] = run

                            #Now trigger integration - if not integrating
                            if run["status"] != "INTEGRATING":
                                run["status"] = "INTEGRATING"
                                self.new_data_image(header=header)

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
        if self.remote_adapter:
            self.remote_adapter.add_image(header)

        return header

    def in_past_run(self, fullname):
        """Determine the place in a past run the image is
        """
        self.logger.info("in_past_run %s" % fullname)

        # Check older runs
        for run_info in reversed(self.recent_runs):
            place, __ = self.in_run(fullname, run_info)
            # Next
            if place == "PAST_RUN":
                continue
            # Found the run
            elif isinstance(place, int):
                return in_run_result, run_info
            # SNAP - unlikely
            elif place == "SNAP":
                return "SNAP", None

        # Go through all runs and fail to find a run or snap
        else:
            return False, None

    def in_run(self, site_tag, fullname, run_info=None):
        """
        Determine if an image is in the currently active run - return
        place in run or False based on prefix,directory,run_id and image number

        Keyword arguments
        site_tag -- corresponds to ID in site file
        fullname -- full path name of the image in question
        run_info -- dict describing run
        """
        self.logger.debug("%s %s", site_tag, fullname)

        if run_info == None:
            if self.current_run == None:
                pass
            else:
                run_info = self.current_run

        # Save typing
        site = self.site

        # The detector
        detector = self.detectors[site_tag.lower()]

        # Tease out the info from the file name
        directory, basename, image_prefix, run_number, image_number = detector.parse_file_name(fullname)

        self.logger.debug("%s %s %s %s %s", directory, basename, image_prefix, run_number, image_number)

        # SNAP?
        if not self.database.query_in_run(site_tag=site_tag,
                                          directory=directory,
                                          image_prefix=image_prefix,
                                          run_number=run_number,
                                          image_number=image_number,
                                          minutes=60,
                                          boolean=True):
            return "SNAP", None

        # NOT a snap
        else:
            self.logger.debug("run_info %s", run_info)
            self.logger.debug("%s %s %s %d %d",
                              directory,
                              basename,
                              image_prefix,
                              run_number,
                              image_number)

            # There is information in the run
            if run_info:
                self.logger.debug("There is run_info")

                # Directory
                if run_info["directory"] == directory:
                    self.logger.debug("directories pass")

                    # Prefix
                    if run_info["prefix"] == prefix:
                        self.logger.debug("prefixes match")

                        # Run number
                        if run_info["run_number"] == run_number:
                            self.logger.debug("run_numbers match")

                            # Image number
                            if (image_number >= run_info["image_number_start"]) and (image_number <= run_info["image_number_end"]):
                                self.logger.debug("image numbers in line")

                                # Calculate the position of the image in the current run
                                run_position = image_number - run_info.get("start", 1) + 1

                                # Update the remote system on the run
                                if self.remote_adapter:
                                    self.remote_adapter.update_run_progress(
                                        run_position=run_position,
                                        image_name=basename,
                                        run_data=run_info)

                                # Return the run position for this image
                                return run_position, "current_run"

                            # Image numbers not in line
                            else:
                                return "PAST", None

                        # Run numbers do not match
                        else:
                            return "PAST", None

                    # Prefixes do not match
                    else:
                        return "PAST", None

                # Directories do not match
                else:
                    return "PAST", None

            # There is no current run
            else:
                return "PAST", None

    def new_data_image(self, header):
        """
        Handle the information that there is a new image in the database.

        There are several calsses of images:
            1. The image is standalone and will be autoindexed
            2. The image is one of a pair of images for autoindexing
            3. The image is first in a wedge of data collection
            4. The image is in the middle of a wedge of data collection
            5. The image is last in a wedge of data collection

        Keyword argument
        header -- dict containing lots of image information
        """

        self.logger.debug(header["fullname"])

        # Save some typing
        site = self.site
        data_root_dir = header["data_root_dir"]

        # Grab out some run information
        # try:
        #     run_id = data["run_id"]
        #     run_total = data["run"]["total"]
        # except:
        #     run_id = 0
        #     run_total = 0

        # # data_root_dir has changed
        # if data_root_dir != self.data_root_dir:
        #
        #     # We have a new drd - check for a previous setting
        #     self.logger.debug("DRD has changed to %s", data_root_dir)
        #     check = self.database.check_new_data_root_dir_setting(data_root_dir=data_root_dir,
        #                                                           site_id=site.ID)
        #     if check:
        #         self.logger.debug("Found and will employ settings this new data root dir")
        #
        #     # Set the instance data_root_dir to the new one
        #     self.data_root_dir = data_root_dir
        #
        #     # New settings have been returned - use them
        #     if check:
        #         process_settings = check
        #         self.logger.debug(process_settings)
        #
        # # No change in data_root_dir
        # else:
        #     self.logger.debug("Data root directory is unchanged %s", data_root_dir)
        #     # Update the current table in the database
        #     self.database.update_current(process_settings)

        # Sample identification
        # This is a hack for getting sample_id into the images
        # if process_settings.has_key("puckset_id"):
        #     data = self.database.setImageSampleId(image_dict=data,
        #                                           puckset_id=process_settings["puckset_id"])

        if header["collect_mode"] == "SNAP":

            # Add the image to self.pair
            self.pairs[header["site_tag"].upper()].append(header["fullname"].lower())
            self.pair_ids[header["site_tag"].upper()].append(header["image_id"])

            work_dir, new_repr = self.get_index_work_dir(type_level = "index_strategy_single",
                                                         image_data1 = header)

            # Now package directories into a dict for easy access by worker class
            new_dirs = {"work":work_dir,
                        "data_root_dir":data_root_dir}

            # Add the process to the database to display as in-process
            process_id = self.database.add_agent_process(agent_type="index+strategy:single",
                                                         request_type="original",
                                                         representation=new_repr,
                                                         progress=0,
                                                         display="show")

            # Add the ID entry to the header dict
            header.update({"agent_process_id":process_id,
                           "repr":new_repr})

            # Run autoindex and strategy agent
            LaunchAction(command=("AUTOINDEX",
                                  new_dirs,
                                  header,
                                  site.LAUNCH_SETTINGS,
                                  self.return_address),
                          settings=process_settings)

            # If the last two images have "pair" in their name - look more closely
            if ("pair" in self.pair[0]) and ("pair" in self.pair[1]):

                self.logger.debug("Potentially a pair of images")

                # Break down the image name
                directory1, basename1, prefix1, run_number1, image_number1 = detector.parse_file_name(self.pair[0])
                directory2, basename2, prefix2, run_number2, image_number2 = detector.parse_file_name(self.pair[1])

                # Everything matches up to the image number, which is incremented by 1
                if (directory1, basename1, prefix1) == (directory2, basename2, prefix2) and (image_number1 == image_number2-1):
                    self.logger.info("This looks like a pair to me: %s, %s" %
                                     (self.pair[1], self.pair[0]))

                    # Get the data for the first image
                    data1 = self.database.get_image_by_image_id(image_id=self.pair_id[0])

                    # Make a copy of the second pair to be LESS confusing
                    data2 = header.copy()

                    # Derive  directory and repr
                    work_dir, new_repr = self.get_index_work_dir(process_settings["work_directory"],
                                                           "pair",
                                                           data1,
                                                           data2)

                    # Now package directories into a dict for easy access by worker class
                    new_dirs = {"work"          : work_dir,
                                "data_root_dir" : data_root_dir}

                    # Add the process to the database to display as in-process
                    process_id = self.database.addNewProcess(
                        type="pair",
                        rtype="original",
                        data_root_dir=data_root_dir,
                        repr=new_repr)

                    # Add the ID entry to the data dict
                    data1.update({
                        "ID" : os.path.basename(work_dir),
                        "repr" : new_repr,
                        "process_id" : process_id
                        })
                    data2.update({
                        "ID" : os.path.basename(work_dir),
                        "repr" : new_repr,
                        "process_id" : process_id
                        })

                    # Run
                    LaunchAction(command=("AUTOINDEX-PAIR",
                                           new_dirs,
                                           data1,
                                           data2,
                                           process_settings,
                                           self.return_address),
                                  settings=process_settings)


        # This is the runs portion of the data image handling
        else:

            self.logger.debug("This is a run")
            self.logger.debug(data)

            run_position = data["place_in_run"]

            self.logger.info("image_number:"+str(int(data["image_number"])))
            self.logger.info("run_id:"+str(run_id))
            self.logger.info("run_position:"+str(run_position))
            self.logger.info("run_total:"+str(run_total))

            # Make it easier to use run info
            run_dict = data["run"].copy()

            # Derive  directory and repr
            work_dir, new_repr = self.get_index_work_dir(process_settings["work_directory"],
                                                   "integrate",
                                                   data)

            # Now package directories into a dict for easy access by worker class
            new_dirs = {"work"          : work_dir,
                        "data_root_dir" : data_root_dir}

            # If we are to integrate, do it
            try:
                # Add the process to the database to display as in-process
                process_id = self.database.addNewProcess(type="integrate",
                                                         rtype="original",
                                                         data_root_dir=data_root_dir,
                                                         repr=new_repr)

                # Make a new result for the integration - should show up in the user interface?
                integrate_result_id, result_id = self.database.makeNewResult(rtype="integrate",
                                                                             process_id=process_id)

                # Add the ID entry to the data dict
                data.update({"ID":os.path.basename(work_dir),
                             "repr":new_repr,
                             "process_id":process_id})

                # Construct data for the processing
                out_data = {"run_data":run_dict,
                            "image_data":data}

                # Connect to the server and autoindex the single image
                LaunchAction(command=("INTEGRATE",
                                       new_dirs,
                                       out_data,
                                       process_settings,
                                       self.return_address),
                              settings=process_settings)
            except:
                self.logger.exception("Exception when attempting to run RAPD \
                integration pipeline")


    def get_index_work_dir(self, type_level, image_data1, image_data2=False):
        """
        Return a valid working directory for rapd_agent to work in

        Keyword arguments
        type_level -- the type of indexing, single or pair
        image_data1 -- header information from the first image
        image_data2 -- header information from the second image
        """

        # Type level
        typelevel_dir = type_level

        # Date level
        datelevel_dir = datetime.date.today().isoformat()

        # Lowest level
        if type_level == "single":
            sub_dir = "%s:%s" % (image_data1["image_prefix"], image_data1["image_number"])
        elif type_level == "pair":
            sub_dir = "%s:%s+%s" % (image_data1["image_prefix"], image_data1["image_number"], image_data2["image_number"])

        # Use the last leg of the directory as the repr
        new_repr = sub_dir

        # Join the  levels
        work_dir_candidate = os.path.join(typelevel_dir,
                                          datelevel_dir,
                                          sub_dir)

        # # Make sure this is an original directory
        # if os.path.exists(work_dir_candidate):
        #     # Already exists
        #     for i in range(1, 1000):
        #         if not os.path.exists("_".join((work_dir_candidate, str(i)))):
        #             work_dir_candidate = "_".join((work_dir_candidate, str(i)))
        #             new_repr = "_".join((new_repr, str(i)))
        #             break
        #         else:
        #             i += 1

        return work_dir_candidate, new_repr

    def receive(self, message):
        """
        Receive information from ControllerServer (self.SERVER) and handle accordingly.

        Several return lengths are currently supported:
            2 - command, info
            3 - command, info, server
            5 - command, dirs, info, settings, results
            6 - command, dirs, info, settings, server,results
            7 - command, dirs, info1, info2, settings, server, results
        Otherwise the message will be taken as a naked command

        Several commands are handled:
            NEWIMAGE - new data image has arrived
            NEWRUN - new data run description has arived
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

        self.logger.debug("Model::receive")
        self.logger.debug("length returned %d" % len(message))
        self.logger.debug(message)

        try:
            # As a hangover from initial design, it is possible to determine
            # some command types based on the number objects passed in...

            # Integrate
            if len(message) == 5:
                command, dirs, info, settings, results = message

            # Autoindex, STAC
            elif len(message) == 6:
                command, dirs, info, settings, server, results = message

            # Autoindex-pair, STAC-pair
            elif len(message) == 7:
                command, dirs, info1, info2, settings, server, results = message

            # Download
            elif len(message) == 3:
                command, info, server = message

            # Others
            elif len(message) == 2:
                command, info = message

            # Anything else
            else:
                command = message
        except:

            # "OLD" format
            command = message

        # Keep track adding to the database
        result_db = False
        trip_db = False

        # New image
        # info is fullname
        if command == "NEWIMAGE":
            self.add_image(info)

        # NEWRUN
        # info is dict containing run information
        elif command == "NEWRUN":
            self.logger.debug("NEWRUN")
            self.logger.debug(info)
            self.add_run(info)

        # # Pilatus run
        # elif command == "PILATUS RUN":
        #     self.logger.debug("New pilatus run")
        #     self.logger.debug(info)
        #     #Save the current_run
        #     if self.current_run:
        #         self.recent_runs.append(self.current_run.copy())
        #     #Set current_run to the new run
        #     self.current_run = info
        #     #Save to the database
        #     run_id = self.database.add_run(run=info,
        #                                   site=self.site)
        #     #Set the run_id that comes from the database for the current run
        #     if run_id:
        #         self.current_run["run_id"] = run_id

        elif command == "PILATUS_ABORT":
            self.logger.debug("Run aborted")
            if self.current_run:
                self.current_run["status"] = "ABORTED"

        elif command == "CONSOLE RUN STATUS CHANGED":
            #save to / check the db for this run
            self.logger.debug("get runid")
            run_id = self.database.add_run(site_id=self.site,
                                           run_data=info)
            self.logger.debug("run_id %s" % str(run_id))
            if self.current_run:
                if self.current_run["run_id"] == run_id:
                    self.logger.debug("Same run again")
                else:
                    self.logger.debug("New run %s" % str(info))
                    #save the current run
                    self.recent_runs.append(self.current_run.copy())
                    #set current run to the new run
                    self.current_run = info
                    self.current_run["run_id"] = run_id
                    #self.sweepForMissedRunImages()
            else:
                self.logger.debug("New run %s" % str(info))
                #set current run to the new run
                self.current_run = info
                self.current_run["run_id"] = run_id

        # elif command == "DIFF_CENTER":
        #     #add result to database
        #     result_db = self.database.addDiffcenterResult(dirs=dirs,
        #                                                   info=info,
        #                                                   settings=settings,
        #                                                   results=results)
        #
        #     self.logger.debug("Added diffraction-based centering result: %s" % str(result_db))
        #
        #     # Write the file for CONSOLE
        #     if result_db:
        #         TransferToBeamline(results=result_db,
        #                            type="DIFFCENTER")
        #
        #     #mark the process as finished
        #     self.database.modifyProcessDisplay(process_id=info["process_id"],
        #                                        display_value="complete")

        # elif command == "STAC":
        #     #add result to database
        #     result_db = self.database.addSingleResult(
        #         dirs=dirs,
        #         info=info,
        #         settings=settings,
        #         results=results
        #         )
        #
        #     self.logger.debug("Added single result: %s", str(result_db))
        #
        #     #mark the process as finished
        #     self.database.modifyProcessDisplay(
        #         process_id=info["process_id"],
        #         display_value="complete"
        #         )
        #     #move the files to the server
        #     if result_db:
        #         #now mark the cloud database if this is a reprocess request
        #         if result_db["type"] in ("reprocess", "stac"):
        #             #remove the process from cloud_current
        #             self.database.removeCloudCurrent(
        #                 cloud_request_id=settings["request"]["cloud_request_id"]
        #                 )
        #             #note the result in cloud_complete
        #             self.database.enterCloudComplete(
        #                 cloud_request_id=settings["request"]["cloud_request_id"],
        #                 request_timestamp=settings["request"]["timestamp"],
        #                 request_type=settings["request"]["request_type"],
        #                 data_root_dir=settings["request"]["data_root_dir"],
        #                 ip_address=settings["request"]["ip_address"],
        #                 start_timestamp=settings["request"]["timestamp"],
        #                 result_id=result_db["result_id"],
        #                 archive=False
        #                 )
        #             # Mark in cloud_requests
        #             self.database.markCloudRequest(
        #                 cloud_request_id=settings["request"]["cloud_request_id"],
        #                 mark="complete"
        #                 )
        #
        #         trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
        #         #this data has an associated trip
        #         if trip_db:
        #             for record in trip_db:
        #                 #update the dates for the trip
        #                 self.database.updateTrip(trip_id=record["trip_id"],
        #                                          date=result_db["date"])
        #                 #now transfer the files
        #                 transferred = TransferToUI(
        #                     type="single",
        #                     settings=self.SecretSettings,
        #                     result=result_db,
        #                     trip=record,
        #                     logger=self.logger
        #                     )
        #
        #         #this data is an "orphan"
        #         else:
        #             self.logger.debug("Orphan result")
        #             #add the orphan to the orphan database table
        #             self.database.addOrphanResult(
        #                 type="single",
        #                 root=dirs["data_root_dir"],
        #                 id=result_db["single_result_id"],
        #                 date=info["date"]
        #                 )
        #             #copy the files to the UI host
        #             dest = os.path.join(self.SecretSettings["ui_user_dir"], "orphans/single/")
        #             #now transfer the files
        #             transferred = TransferToUI(
        #                 type="single-orphan",
        #                 settings=self.SecretSettings,
        #                 result=result_db,
        #                 trip=trip_db,
        #                 logger=self.logger
        #                 )

        #     #the addition of result to db has failed, but still needs removed from the cloud
        #     else:
        #         if settings["request"]["request_type"] == "reprocess":
        #             #remove the process from cloud_current
        #             self.database.removeCloudCurrent(
        #                 cloud_request_id=settings["request"]["cloud_request_id"]
        #                 )
        #             #note the result in cloud_complete
        #             self.database.enterCloudComplete(
        #                 cloud_request_id=settings["request"]["cloud_request_id"],
        #                 request_timestamp=settings["request"]["timestamp"],
        #                 request_type=settings["request"]["request_type"],
        #                 data_root_dir=settings["request"]["data_root_dir"],
        #                 ip_address=settings["request"]["ip_address"],
        #                 start_timestamp=settings["request"]["timestamp"],
        #                 result_id=0,
        #                 archive=False
        #                 )
        #             #mark in cloud_requests
        #             self.database.markCloudRequest(
        #                 cloud_request_id=settings["request"]["cloud_request_id"],
        #                 mark="failure"
        #                 )
        #
        # elif command == "STAC-PAIR":
        #     #add result to database
        #     result_db = self.database.addPairResult(dirs=dirs,
        #                                             info1=info1,
        #                                             info2=info2,
        #                                             settings=settings,
        #                                             results=results)
        #     self.logger.debug("Added pair result: %s" % str(result_db))
        #
        #     #mark the process as finished
        #     self.database.modifyProcessDisplay(process_id=info1["process_id"],
        #                                        display_value="complete")
        #
        #     #move the files to the server
        #     if result_db:
        #         #now mark the cloud database if this is a reprocess request
        #         if result_db["type"] in ("reprocess", "stac"):
        #             #remove the process from cloud_current
        #             self.database.removeCloudCurrent(
        #                 cloud_request_id=settings["request"]["cloud_request_id"])
        #             #note the result in cloud_complete
        #             self.database.enterCloudComplete(
        #                 cloud_request_id=settings["request"]["cloud_request_id"],
        #                 request_timestamp=settings["request"]["timestamp"],
        #                 request_type=settings["request"]["request_type"],
        #                 data_root_dir=settings["request"]["data_root_dir"],
        #                 ip_address=settings["request"]["ip_address"],
        #                 start_timestamp=settings["request"]["timestamp"],
        #                 result_id=result_db["result_id"],
        #                 archive=False
        #                 )
        #             #mark in cloud_requests
        #             self.database.markCloudRequest(
        #                 cloud_request_id=settings["request"]["cloud_request_id"],
        #                 mark="complete"
        #                 )
        #
        #         trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
        #         #this data has an associated trip
        #         if trip_db:
        #             for record in trip_db:
        #                 #update the dates for the trip
        #                 self.database.updateTrip(trip_id=record["trip_id"],
        #                                          date=result_db["date_2"])
        #                 #now transfer the files
        #                 transferred = TransferToUI(
        #                     type="pair",
        #                     settings=self.SecretSettings,
        #                     result=result_db,
        #                     trip=record,
        #                     logger=self.logger
        #                     )
        #         #this data is an "orphan"
        #         else:
        #             self.logger.debug("Orphan result")
        #             #add the orphan to the orphan database table
        #             self.database.addOrphanResult(type="pair",
        #                                           root=dirs["data_root_dir"],
        #                                           id=result_db["pair_result_id"],
        #                                           date=info1["date"])
        #             #copy the files to the UI host
        #             dest = os.path.join(self.SecretSettings["ui_user_dir"], "orphans/pair/")
        #             #now transfer the files
        #             transferred = TransferToUI(
        #                 type="pair-orphan",
        #                 settings=self.SecretSettings,
        #                 result=result_db,
        #                 trip=trip_db,
        #                 logger=self.logger
        #                 )
        #
        #     #the addition of result to db has failed, but still needs removed from the cloud
        #     else:
        #         if settings["request"]["request_type"] == "reprocess":
        #             #remove the process from cloud_current
        #             self.database.removeCloudCurrent(
        #                 cloud_request_id=settings["request"]["cloud_request_id"]
        #                 )
        #             #note the result in cloud_complete
        #             self.database.enterCloudComplete(
        #                 cloud_request_id=settings["request"]["cloud_request_id"],
        #                 request_timestamp=settings["request"]["timestamp"],
        #                 request_type=settings["request"]["request_type"],
        #                 data_root_dir=settings["request"]["data_root_dir"],
        #                 ip_address=settings["request"]["ip_address"],
        #                 start_timestamp=settings["request"]["timestamp"],
        #                 result_id=0,
        #                 archive=False
        #                 )
        #             #mark in cloud_requests
        #             self.database.markCloudRequest(
        #                 cloud_request_id=settings["request"]["cloud_request_id"],
        #                 mark="failure"
        #                 )

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
                    LaunchAction(command=job[0],
                                  settings=job[1],
                                  secret_settings=job[2],
                                  logger=job[3])

            #add result to database
            result_db = self.database.addSingleResult(dirs=dirs,
                                                      info=info,
                                                      settings=settings,
                                                      results=results)

            self.logger.debug("Added single result: %s" % str(result_db))

            #mark the process as finished
            self.database.modifyProcessDisplay(process_id=info["process_id"],
                                               display_value="complete")

            #move the files to the server & other
            if result_db:

                #Update the Remote project
                if self.remote_adapter:
                    wedges = self.database.getStrategyWedges(id=result_db["single_result_id"])
                    result_db["image_id"] = info["image_id"]
                    self.remote_adapterAdapter.update_image_stats(result_db, wedges)

                #now mark the cloud database if this is a reprocess request
                if result_db["type"] in ("reprocess", "stac"):
                    #remove the process from cloud_current
                    self.database.removeCloudCurrent(
                        cloud_request_id=settings["request"]["cloud_request_id"]
                        )
                    #note the result in cloud_complete
                    self.database.enterCloudComplete(
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
                    self.database.markCloudRequest(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        mark="complete"
                        )

                trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.database.updateTrip(
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
                    self.database.addOrphanResult(
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
                    self.database.removeCloudCurrent(
                        cloud_request_id=settings["request"]["cloud_request_id"]
                        )
                    #note the result in cloud_complete
                    self.database.enterCloudComplete(
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
                    self.database.markCloudRequest(
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
                    LaunchAction(command=job[0],
                                  settings=job[1],
                                  secret_settings=job[2],
                                  logger=job[3])

            result_db = self.database.addPairResult(
                dirs=dirs,
                info1=info1,
                info2=info2,
                settings=settings,
                results=results
                )
            self.logger.debug("Added pair result: %s" % str(result_db))

            #mark the process as finished
            self.database.modifyProcessDisplay(process_id=info1["process_id"],
                                               display_value="complete")

            #move the files to the server
            if result_db:
                #now mark the cloud database if this is a reprocess request
                if result_db["type"] == "reprocess":
                    #remove the process from cloud_current
                    self.database.removeCloudCurrent(
                        cloud_request_id=settings["request"]["cloud_request_id"]
                        )
                    #note the result in cloud_complete
                    self.database.enterCloudComplete(
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
                    self.database.markCloudRequest(
                        cloud_request_id=settings["request"]["cloud_request_id"],
                        mark="complete"
                        )

                trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.database.updateTrip(trip_id=record["trip_id"],
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
                    self.database.addOrphanResult(type="pair",
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
                        self.database.removeCloudCurrent(
                            cloud_request_id=settings["request"]["cloud_request_id"]
                            )
                        #note the result in cloud_complete
                        self.database.enterCloudComplete(
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
                        self.database.markCloudRequest(
                            cloud_request_id=settings["request"]["cloud_request_id"],
                            mark="failure"
                            )

        # Integration
        elif command in ("INTEGRATE",):
            result_db = self.database.addIntegrateResult(dirs=dirs,
                                                         info=info,
                                                         settings=settings,
                                                         results=results)

            self.logger.debug("Added integration result: %s" % str(result_db))

            #mark the process as finished
            self.database.modifyProcessDisplay(process_id=info["image_data"]["process_id"],
                                               display_value="complete")

            #move the files to the server
            if result_db:
                #Update the Remote project
                if self.remote_adapter:
                    try:
                        wedges = self.database.getRunWedges(run_id=result_db["run_id"])
                    except:
                        self.logger.exception("Error in getting run wedges")
                    try:
                        self.remote_adapter.update_run_stats(result_db=result_db, wedges=wedges)
                    except:
                        self.logger.exception("Error in updating run stats")

                trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.database.updateTrip(trip_id=record["trip_id"],
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
                    self.database.addOrphanResult(type="integrate",
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
            result_db = self.database.addReIntegrateResult(dirs=dirs,
                                                           info=info,
                                                           settings=settings,
                                                           results=results)
            self.logger.debug("Added reintegration result: %s" % str(result_db))

            #mark the process as finished
            self.database.modifyProcessDisplay(process_id=settings["process_id"],
                                               display_value="complete")

            #move the files to the server
            if result_db:
                trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.database.updateTrip(trip_id=record["trip_id"],
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
                    self.database.addOrphanResult(
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


            result_db = self.database.addSimpleMergeResult(dirs=dirs,
                                                           info=info,
                                                           settings=settings,
                                                           results=results)
            self.logger.debug("Added simple merge result: %s" % str(result_db))

            #mark the process as finished
            self.database.modifyProcessDisplay(process_id=result_db["process_id"],
                                               display_value="complete")

            #move the files to the server
            if result_db:
                trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
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
                    self.database.addOrphanResult(type="smerge",
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
            result_db = self.database.addSadResult(dirs=dirs,
                                                   info=info,
                                                   settings=settings,
                                                   results=results)
            self.logger.debug("Added SAD result: %s" % str(result_db))

            #mark the process as finished
            self.database.modifyProcessDisplay(process_id=settings["process_id"],
                                               display_value="complete")

            #move the files to the server
            if result_db:
                trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.database.updateTrip(trip_id=record["trip_id"],
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
                    self.database.addOrphanResult(
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

            result_db = self.database.addMadResult(dirs=dirs,
                                                   info=info,
                                                   settings=settings,
                                                   results=results)
            self.logger.debug("Added MAD result: %s" % str(result_db))

            #mark the process as finished
            self.database.modifyProcessDisplay(process_id=settings["process_id"],
                                               display_value="complete")

            #move the files to the server
            if result_db:
                trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.database.updateTrip(trip_id=record["trip_id"],
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
            result_db = self.database.addMrResult(dirs=dirs,
                                                  info=info,
                                                  settings=settings,
                                                  results=results)
            #some debugging output
            self.logger.debug("Added MR result: %s" % str(result_db))

            #If the process is complete, mark it as such
            if result_db["mr_status"] != "WORKING":
                #mark the process as finished
                self.database.modifyProcessDisplay(process_id=result_db["process_id"],
                                                   display_value="complete")
            #move the files to the server
            if result_db:
                #Get the trip for this data
                trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.database.updateTrip(trip_id=record["trip_id"],
                                                 date=result_db["timestamp"])
                        #now transfer the files
                        transferred = TransferToUI(type="mr",
                                                   settings=self.SecretSettings,
                                                   result=result_db,
                                                   trip=record,
                                                   logger=self.logger)

            #now place the files in the data_root_dir for the user to have and to hold
            if  self.SecretSettings["copy_data"]:
                all_mr_results = self.database.getMrTrialResult(result_db["mr_result_id"])
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
            trip_db = self.database.getTrips(data_root_dir=info["data_root_dir"])

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
                self.database.enterCloudComplete(cloud_request_id=info["cloud_request_id"],
                                                 request_timestamp=info["timestamp"],
                                                 request_type=info["request_type"],
                                                 data_root_dir=info["data_root_dir"],
                                                 ip_address=info["ip_address"],
                                                 start_timestamp=0,
                                                 result_id=0,
                                                 archive=os.path.basename(info["archive"]))

                #mark in cloud_requests
                self.database.markCloudRequest(
                    cloud_request_id=info["cloud_request_id"],
                    mark="complete"
                    )

            #the transfer was not successful
            else:
                #note the result in cloud_complete
                self.database.enterCloudComplete(cloud_request_id=info["cloud_request_id"],
                                                 request_timestamp=info["timestamp"],
                                                 request_type=info["request_type"],
                                                 data_root_dir=info["data_root_dir"],
                                                 ip_address=info["ip_address"],
                                                 start_timestamp=0,
                                                 result_id=0,
                                                 archive=os.path.basename(info["archive"]))

                #mark in cloud_requests
                self.database.markCloudRequest(cloud_request_id=info["cloud_request_id"],
                                               mark="failure")

        elif command == "STATS":
            self.logger.debug("Received STATS result")

            #rearrange results
            results = server.copy()

            #self.logger.debug(info)
            #self.logger.debug(results)
            result_db = self.database.addStatsResults(info=info,
                                                      results=results)
            self.logger.debug("Added STATS result: %s" % str(result_db))

            #mark the process as finished
            self.database.modifyProcessDisplay(process_id=info["process_id"],
                                               display_value="complete")

            #move the files to the server
            if result_db:
                #Get the trip for this data
                trip_db = self.database.getTrips(result_id=result_db["result_id"])
                #print trip_db
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.database.updateTrip(trip_id=record["trip_id"],
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
                               db=self.database,
                               bc=self.BEAMLINE_CONNECTION,
                               data=info,
                               logger=self.logger)

        elif command == "CRYSTAL_PARMS_REQUEST":
            self.logger.debug("CRYSTAL params request for %s" % info)
            cf = ConsoleFeeder(mode="CRYSTAL_PARMS_REQUEST",
                               db=self.database,
                               bc=self.BEAMLINE_CONNECTION,
                               data=info,
                               logger=self.logger)

        elif command == "BEST_PARMS_REQUEST":
            self.logger.debug("BEST params request for %s" % info)
            cf = ConsoleFeeder(mode="BEST_PARMS_REQUEST",
                               db=self.database,
                               bc=self.BEAMLINE_CONNECTION,
                               data=info,
                               logger=self.logger)

        else:
            self.logger.info("Take no action for message")
            self.logger.info(message)

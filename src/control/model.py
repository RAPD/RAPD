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

    # Controlling simultaneous image processing
    indexing_queue = collections.deque()
    indexing_active = collections.deque()

    # Managing runs and images without going to the db
    recent_runs = collections.OrderedDict()

    data_root_dir = None
    database = None

    server = None
    return_address = None

    image_monitor = None
    run_monitor = None
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

    def init_site(self):
        """Process the site definitions to set up instance variables"""

        # Single or multiple IDs
        # A string is input - one tag
        if isinstance(self.site.ID, str):
            self.site_ids = [self.site.ID]
            self.pairs[self.site.ID] = collections.deque([("",0), ("",0)], 2)

        # Tuple or list
        elif isinstance(self.site.ID, tuple) or isinstance(self.site.ID, list):
            for site_id in self.site.ID:
                self.site_ids.append(site_id)
                self.pairs[site_id] = collections.deque([("",0), ("",0)], 2)

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
            self.detectors[self.site_ids[0].upper()] = load_module(detector, ("sites.detectors", "detectors"))

        # Multiple detectors
        elif site.DETECTORS:
            for site_id in self.site_ids:
                detector, suffix = site.DETECTORS[site_id]
                detector = detector.lower()
                self.detectors[site_id.upper()] = load_module(detector, ("sites.detectors", "detectors"))

    def start_image_monitor(self):
        """Start up the image listening process for core"""

        self.logger.debug("Starting image monitor")

        # Shorten variable names
        site = self.site

        if site.IMAGE_MONITOR:
            # import image_monitor
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
        """Stop the ImageMonitor,CloudMonitor and StatusRegistrar."""
        self.logger.info("Stopping")

    def add_image(self, image_data):
        """
        Handle a new image being recorded by the site

        Keyword argument
        image_data -- information gathered about the image, primarily from the header
        """

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

        # Derive the data_root_dir
        data_root_dir = detector.get_data_root_dir(fullname)

        # Figure out if image in the current run...
        run_id, place_in_run = self.in_run(site_tag, fullname)

        # Image is in a run
        if isinstance(place_in_run, int) and isinstance(run_id, int):

            self.logger.debug("%s is in run %s at position %s", fullname, run_id, place_in_run)

            # Save some typing
            current_run = self.recent_runs[run_id]

            # If not integrating trigger integration
            if not current_run.get("rapd_status", None) in ("INTEGRATING", "FINISHED"):

                # Right on time
                if place_in_run == 1:
                    # Get all the image information
                    header = detector.read_header(fullname=fullname,
                                                  beam_settings=self.site.BEAM_INFO[site_tag.upper()])
                    # Put data about run in the header object
                    header["collect_mode"] = "run"
                    header["run_id"] = run_id
                    header["run"] = self.recent_runs[run_id].copy()
                    header["place_in_run"] = 1
                    header["site_tag"] = site_tag

                    # Add to the database
                    db_result = self.database.add_image(header)

                    # Send to be processed
                    self.new_data_image(header=header)

                # Handle getting to the party late
                else:
                    self.logger.info("Creating first image in run")
                    first_image_fullname = detector.create_image_fullname(
                        directory=current_run.get("directory", None),
                        image_prefix=current_run.get("image_prefix", None),
                        run_number=current_run.get("run_number", None),
                        image_number=current_run.get("start_image_number", None))

                    # Now run through the normal channels with the first image
                    self.add_image({"site_tag": current_run.get("site_tag", None),
                                    "fullname": first_image_fullname})

        # Image is a snap
        elif run_id == "SNAP":

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


        # No information is findable
        else:
            self.logger.debug("Unable to figure out %s", fullname)

    def query_for_run(self, run_data, boolean=True):
        """
        Look in the local store and the database for run that matches input data

        Keyword argument
        run_data -- dict containing run information
        boolean -- return True/False (default True)
        """

        # Look in local store of information
        for run_id, run in self.recent_runs.iteritems():
            if run_data.get("run_id", 0) == run_id:
                if boolean:
                    return True
                else:
                    return run

        # Look in the database since the local attempt has failed
        return self.database.get_run_data(run_data=run_data,
                                          minutes=self.site.RUN_WINDOW,
                                          boolean=boolean)

    def query_in_run(self,
                     site_tag,
                     directory,
                     image_prefix,
                     run_number,
                     image_number,
                     minutes=0,
                     order="descending",
                     boolean=True):
        """
        Return True/False or with list of data depending on whether the image
        information could correspond to a run stored locally or in the database

        If the run is found in the local store, only the most recent match will
        be returned if running in boolean=False mode. If found in the database,
        all matching runs in the last minutes minutes will be returned

        Keyword arguments
        site_tag -- string describing site (default None)
        directory -- where the image is located
        image_prefix -- the image prefix
        run_number -- number for the run
        image_number -- number for the image
        minutes -- time window to look back into the data (default 0)
        boolean -- return just True if there is a or False
        """

        # Query local runs in reverse chronological order
        for run_id in reversed(self.recent_runs):
            run = self.recent_runs[run_id]
            if run.get("site_tag", None) == site_tag and \
               run.get("directory", None) == directory and \
               run.get("image_prefix", None) == image_prefix and \
               run.get("run_number", None) == run_number:

                # Check image number
                run_start = run.get("start_image_number")
                run_end = run.get("number_images") + run_start - 1
                if image_number >= run_start and image_number <= run_end:
                    if boolean:
                        return True
                    else:
                        return [run]

        # If no run has been identified in local store, then search database
        identified_runs = self.database.query_in_run(site_tag=site_tag,
                                                     directory=directory,
                                                     image_prefix=image_prefix,
                                                     run_number=run_number,
                                                     image_number=image_number,
                                                     minutes=minutes,
                                                     boolean=boolean)

        # If boolean, just return
        if boolean:
            return identified_runs
        if identified_runs == False:
            return False
        elif len(identified_runs) == 0:
            return False
        else:
            # Add to local store
            self.recent_runs[identified_runs[0]["run_id"]] = identified_runs[0]
            if boolean:
                return True
            else:
                return identified_runs



    def add_run(self, run_dict):
        """
        Add potentially new run to RAPD system

        Keyword arguments
        run_data -- dict containing data describing the run
        """

        # Unpack the run_dict
        run_data = run_dict["run_data"]

        # Check if this run has already been stored
        recent_run_data = self.query_for_run(run_data=run_data, boolean=True)

        # Run data already stored
        if recent_run_data == True:

            self.logger.debug("This run has already been recorded")

        # Run is new to RAPD
        else:

            # Save to the database
            run_id = self.database.add_run(run_data=run_data)

            # Update the run data with the db run_id
            run_data["run_id"] = run_id

            # Save the run_data to local store
            self.recent_runs[run_id] = run_data

        return True

    def in_past_run(self, fullname):
        """
        Determine the place in a past run the image is

        Keyword argument
        fullname -- the full path name for an image
        """

        self.logger.info("in_past_run %s", fullname)

        # Check older runs
        for run_info in reversed(self.recent_runs):
            place, __ = self.in_run(fullname, run_info)
            # Next
            if place == "PAST_RUN":
                continue
            # Found the run
            elif isinstance(place, int):
                return place, run_info
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

        # The detector
        detector = self.detectors[site_tag.upper()]

        # Tease out the info from the file name
        directory, basename, image_prefix, run_number, image_number = detector.parse_file_name(fullname)

        self.logger.debug("%s %s %s %s %s", directory, basename, image_prefix, run_number, image_number)

        # Look for run information for this image
        run_info = self.query_in_run(site_tag=site_tag,
                                     directory=directory,
                                     image_prefix=image_prefix,
                                     run_number=run_number,
                                     image_number=image_number,
                                     minutes=self.site.RUN_WINDOW,
                                     boolean=False)

        # No run information - SNAP
        if not run_info:
            return "SNAP", None

        # NOT a snap
        else:
            # run_info is a list of dicts - take most recent match
            run_info = run_info[0]

            self.logger.debug("run_info: %s", run_info)
            self.logger.debug("%s %s %s %s %s",
                              directory,
                              basename,
                              image_prefix,
                              run_number,
                              image_number)

            # Calculate the position of the image in the current run
            run_position = image_number - run_info.get("start_image_number", 1) + 1

            # Update the remote system on the run
            # if self.remote_adapter:
            #     self.remote_adapter.update_run_progress(
            #         run_position=run_position,
            #         image_name=basename,
            #         run_data=run_info)

            # Return the run position for this image
            return run_info["run_id"], run_position

    def new_data_image(self, header):
        """
        Handle the information that there is a new image in the database.

        There are several classes of images:
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
        site_tag = header["site_tag"].upper()

        if header.get("collect_mode", None) == "SNAP":

            # Add the image to self.pair
            self.pairs[site_tag].append((header["fullname"].lower(), header["image_id"]))

            work_dir, new_repr = self.get_work_dir(type_level="single",
                                                   image_data1=header)

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
            LaunchAction(command={"command":"INDEX+STRATEGY",
                                  "directories":new_dirs,
                                  "header1":header,
                                  "preferences":{},
                                  "return_address":self.return_address},
                         launcher_address=self.site.LAUNCH_SETTINGS["LAUNCHER_ADDRESS"],
                         settings=None)

            # If the last two images have "pair" in their name - look more closely
            if ("pair" in self.pairs[site_tag][0][0]) and ("pair" in self.pairs[site_tag][1][0]):

                self.logger.debug("Potentially a pair of images")

                # Break down the image name
                directory1, basename1, prefix1, run_number1, image_number1 = detector.parse_file_name(self.pairs[site_tag][0][0])
                directory2, basename2, prefix2, run_number2, image_number2 = detector.parse_file_name(self.pairs[site_tag][1][0])

                # Everything matches up to the image number, which is incremented by 1
                if (directory1, basename1, prefix1) == (directory2, basename2, prefix2) and (image_number1 == image_number2-1):
                    self.logger.info("This looks like a pair to me: %s, %s",
                                     self.pairs[site_tag][0][0],
                                     self.pairs[site_tag][1][0])

                    # Get the data for the first image
                    header1 = self.database.get_image_by_image_id(image_id=self.pairs[site_tag][0][1])

                    # Make a copy of the second pair to be LESS confusing
                    header2 = header.copy()

                    # Derive  directory and repr
                    work_dir, new_repr = self.get_work_dir(type_level="pair",
                                                           image_data1=header1,
                                                           image_data2=header2)

                    # Now package directories into a dict for easy access by worker class
                    new_dirs = {"work" : work_dir,
                                "data_root_dir" : data_root_dir}

                    # Add the process to the database to display as in-process
                    process_id = self.database.add_agent_process(agent_type="index+strategy:pair",
                                                                 request_type="original",
                                                                 representation=new_repr,
                                                                 progress=0,
                                                                 display="show")

                    # Add the ID entry to the header dict
                    header1.update({"agent_process_id":process_id,
                                    "repr":new_repr})
                    header2.update({"agent_process_id":process_id,
                                    "repr":new_repr})

                    # Run autoindex and strategy agent
                    LaunchAction(command={"command":"INDEX+STRATEGY",
                                          "directories":new_dirs,
                                          "header1":header1,
                                          "header2":header2,
                                          "preferences":{},
                                          "return_address":self.return_address},
                                 launcher_address=self.site.LAUNCH_SETTINGS["LAUNCHER_ADDRESS"],
                                 settings=None)


        # This is the runs portion of the data image handling
        else:

            # Make it easier to use run info
            run_position = header["place_in_run"]
            run_dict = header["run"].copy()

            # Derive  directory and repr
            work_dir, new_repr = self.get_work_dir(type_level="integrate",
                                                   image_data1=header)

            # Now package directories into a dict for easy access by worker class
            new_dirs = {"work" : work_dir,
                        "data_root_dir" : data_root_dir}

            # If we are to integrate, do it
            try:
                # Add the process to the database to display as in-process
                process_id = self.database.add_agent_process(agent_type="integrate",
                                                             request_type="original",
                                                             representation=new_repr,
                                                             progress=0,
                                                             display="show")

                # Add the ID entry to the header dict
                header.update({"agent_process_id":process_id,
                               "repr":new_repr})

                # # Add the ID entry to the data dict
                # data.update({"ID":os.path.basename(work_dir),
                #              "repr":new_repr,
                #              "process_id":process_id})

                # # Construct data for the processing
                # out_data = {"run_data":run_dict,
                #             "image_data":data}

                # Connect to the server and autoindex the single image
                LaunchAction(command={"command":"INTEGRATE",
                                      "directories":new_dirs,
                                      "image_data":header,
                                      "run_data":run_dict,
                                      "preferences":{},
                                      "return_address":self.return_address},
                             launcher_address=self.site.LAUNCH_SETTINGS["LAUNCHER_ADDRESS"],
                             settings=None)
            except:
                self.logger.exception("Exception when attempting to run RAPD \
                integration pipeline")

    def get_work_dir(self, type_level, image_data1, image_data2=False):
        """
        Return a valid working directory for rapd_agent to work in

        Keyword arguments
        type_level -- the type of work, single, pair, integrate
        image_data1 -- header information from the first image
        image_data2 -- header information from the second image
        """

        # Type level
        typelevel_dir = type_level

        # Date level
        datelevel_dir = datetime.date.today().isoformat()

        # Lowest level
        if type_level == "single":
            sub_dir = "%s:%s" % (image_data1["image_prefix"],
                                 image_data1["image_number"])
        elif type_level == "pair":
            sub_dir = "%s:%s+%s" % (image_data1["image_prefix"],
                                    image_data1["image_number"],
                                    image_data2["image_number"])

        elif type_level == "integrate":
            sub_dir = "%s" % image_data1["image_prefix"]

        # Use the last leg of the directory as the repr
        new_repr = sub_dir

        # Join the  levels
        work_dir_candidate = os.path.join(typelevel_dir,
                                          datelevel_dir,
                                          sub_dir)

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
        self.logger.debug("length returned %d", len(message))
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

        # elif command == "PILATUS_ABORT":
        #     self.logger.debug("Run aborted")
        #     if self.current_run:
        #         self.current_run["status"] = "ABORTED"

        # elif command == "CONSOLE RUN STATUS CHANGED":
        #     #save to / check the db for this run
        #     self.logger.debug("get runid")
        #     run_id = self.database.add_run(site_id=self.site,
        #                                    run_data=info)
        #     self.logger.debug("run_id %s" % str(run_id))
        #     if self.current_run:
        #         if self.current_run["run_id"] == run_id:
        #             self.logger.debug("Same run again")
        #         else:
        #             self.logger.debug("New run %s" % str(info))
        #             #save the current run
        #             self.recent_runs.append(self.current_run.copy())
        #             #set current run to the new run
        #             self.current_run = info
        #             self.current_run["run_id"] = run_id
        #             #self.sweepForMissedRunImages()
        #     else:
        #         self.logger.debug("New run %s" % str(info))
        #         #set current run to the new run
        #         self.current_run = info
        #         self.current_run["run_id"] = run_id

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
        #
        # elif command == "AUTOINDEX":
        #     #Handle the ongoing throttling of autoindexing jobs
        #     if self.SecretSettings["throttle_strategy"] == True:
        #         #pop one marker off the indexing_active
        #         try:
        #             self.indexing_active.pop()
        #         except:
        #             pass
        #         if len(self.indexing_queue) > 0:
        #             self.logger.debug("Running a command from the indexing_queue")
        #             job = self.indexing_queue.pop()
        #             self.indexing_active.appendleft("unknown")
        #             #send the job to be done
        #             LaunchAction(command=job[0],
        #                          settings=job[1],
        #                          secret_settings=job[2],
        #                          logger=job[3])
        #
        #     #add result to database
        #     result_db = self.database.addSingleResult(dirs=dirs,
        #                                               info=info,
        #                                               settings=settings,
        #                                               results=results)
        #
        #     self.logger.debug("Added single result: %s" % str(result_db))
        #
        #     #mark the process as finished
        #     self.database.modifyProcessDisplay(process_id=info["process_id"],
        #                                        display_value="complete")
        #
        #     #move the files to the server & other
        #     if result_db:
        #
        #         #Update the Remote project
        #         if self.remote_adapter:
        #             wedges = self.database.getStrategyWedges(id=result_db["single_result_id"])
        #             result_db["image_id"] = info["image_id"]
        #             self.remote_adapterAdapter.update_image_stats(result_db, wedges)
        #
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
        #                 self.database.updateTrip(
        #                     trip_id=record["trip_id"],
        #                     date=result_db["date"]
        #                     )
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
        #
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
        #
        #
        # elif command == "AUTOINDEX-PAIR":
        #     if self.SecretSettings["throttle_strategy"] == True:
        #         #pop one off the indexing_active
        #         try:
        #             self.indexing_active.pop()
        #         except:
        #             self.logger.exception("Error popping from self.indexing_active")
        #         if len(self.indexing_queue) > 0:
        #             self.logger.debug("Running a command from the indexing_queue")
        #             job = self.indexing_queue.pop()
        #             self.indexing_active.appendleft("unknown")
        #             LaunchAction(command=job[0],
        #                           settings=job[1],
        #                           secret_settings=job[2],
        #                           logger=job[3])
        #
        #     result_db = self.database.addPairResult(
        #         dirs=dirs,
        #         info1=info1,
        #         info2=info2,
        #         settings=settings,
        #         results=results
        #         )
        #     self.logger.debug("Added pair result: %s" % str(result_db))
        #
        #     #mark the process as finished
        #     self.database.modifyProcessDisplay(process_id=info1["process_id"],
        #                                        display_value="complete")
        #
        #     #move the files to the server
        #     if result_db:
        #         #now mark the cloud database if this is a reprocess request
        #         if result_db["type"] == "reprocess":
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
        #                 transferred = TransferToUI(type="pair",
        #                                            settings=self.SecretSettings,
        #                                            result=result_db,
        #                                            trip=record,
        #                                            logger=self.logger)
        #         #this data is an "orphan"
        #         else:
        #             self.logger.debug("Orphan result")
        #             #add the orphan to the orphan database table
        #             self.database.addOrphanResult(type="pair",
        #                                           root=dirs["data_root_dir"],
        #                                           id=result_db["pair_result_id"],
        #                                           date=info["date"])
        #             #now transfer the files
        #             transferred = TransferToUI(type="pair-orphan",
        #                                        settings=self.SecretSettings,
        #                                        result=result_db,
        #                                        trip=trip_db,
        #                                        logger=self.logger)
        #
        #     #the addition of result to db has failed, but still needs removed from the cloud
        #     else:
        #         if settings.has_key(["request"]):
        #             if settings["request"]["request_type"] == "reprocess":
        #                 #remove the process from cloud_current
        #                 self.database.removeCloudCurrent(
        #                     cloud_request_id=settings["request"]["cloud_request_id"]
        #                     )
        #                 #note the result in cloud_complete
        #                 self.database.enterCloudComplete(
        #                     cloud_request_id=settings["request"]["cloud_request_id"],
        #                     request_timestamp=settings["request"]["timestamp"],
        #                     request_type=settings["request"]["request_type"],
        #                     data_root_dir=settings["request"]["data_root_dir"],
        #                     ip_address=settings["request"]["ip_address"],
        #                     start_timestamp=settings["request"]["timestamp"],
        #                     result_id=0,
        #                     archive=False
        #                     )
        #                 #mark in cloud_requests
        #                 self.database.markCloudRequest(
        #                     cloud_request_id=settings["request"]["cloud_request_id"],
        #                     mark="failure"
        #                     )
        #
        # # Integration
        # elif command in ("INTEGRATE",):
        #     result_db = self.database.addIntegrateResult(dirs=dirs,
        #                                                  info=info,
        #                                                  settings=settings,
        #                                                  results=results)
        #
        #     self.logger.debug("Added integration result: %s" % str(result_db))
        #
        #     #mark the process as finished
        #     self.database.modifyProcessDisplay(process_id=info["image_data"]["process_id"],
        #                                        display_value="complete")
        #
        #     #move the files to the server
        #     if result_db:
        #         #Update the Remote project
        #         if self.remote_adapter:
        #             try:
        #                 wedges = self.database.getRunWedges(run_id=result_db["run_id"])
        #             except:
        #                 self.logger.exception("Error in getting run wedges")
        #             try:
        #                 self.remote_adapter.update_run_stats(result_db=result_db, wedges=wedges)
        #             except:
        #                 self.logger.exception("Error in updating run stats")
        #
        #         trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
        #         #this data has an associated trip
        #         if trip_db:
        #             for record in trip_db:
        #                 #update the dates for the trip
        #                 self.database.updateTrip(trip_id=record["trip_id"],
        #                                          date=result_db["date"])
        #                 #now transfer the files
        #                 transferred = TransferToUI(type="integrate",
        #                                            settings=self.SecretSettings,
        #                                            result=result_db,
        #                                            trip=record,
        #                                            logger=self.logger)
        #         #this data is an "orphan"
        #         else:
        #             self.logger.debug("Orphan result")
        #             #add the orphan to the orphan database table
        #             self.database.addOrphanResult(type="integrate",
        #                                           root=dirs["data_root_dir"],
        #                                           id=result_db["integrate_result_id"],
        #                                           date=result_db["date"])
        #
        #             #now transfer the files
        #             transferred = TransferToUI(type="integrate-orphan",
        #                                        settings=self.SecretSettings,
        #                                        result=result_db,
        #                                        trip=trip_db,
        #                                        logger=self.logger)
        #
        #     #now place the files in the data_root_dir for the user to have and to hold
        #     if self.SecretSettings["copy_data"]:
        #         copied = CopyToUser(root=dirs["data_root_dir"],
        #                             res_type="integrate",
        #                             result=result_db,
        #                             logger=self.logger)
        #     #the addition of result to db has failed, but still needs removed from the cloud
        #     #this is not YET an option so pass for now
        #     else:
        #         pass
        #
        # # Reintegration using RAPD pipeline
        # elif command in ("XDS", "XIA2"):
        #     result_db = self.database.addReIntegrateResult(dirs=dirs,
        #                                                    info=info,
        #                                                    settings=settings,
        #                                                    results=results)
        #     self.logger.debug("Added reintegration result: %s" % str(result_db))
        #
        #     #mark the process as finished
        #     self.database.modifyProcessDisplay(process_id=settings["process_id"],
        #                                        display_value="complete")
        #
        #     #move the files to the server
        #     if result_db:
        #         trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
        #         #this data has an associated trip
        #         if trip_db:
        #             for record in trip_db:
        #                 #update the dates for the trip
        #                 self.database.updateTrip(trip_id=record["trip_id"],
        #                                          date=result_db["date"])
        #                 #now transfer the files
        #                 transferred = TransferToUI(type="integrate",
        #                                            settings=self.SecretSettings,
        #                                            result=result_db,
        #                                            trip=record,
        #                                            logger=self.logger)
        #         #this data is an "orphan"
        #         else:
        #             self.logger.debug("Orphan result")
        #             #add the orphan to the orphan database table
        #             self.database.addOrphanResult(
        #                 type="integrate",
        #                 root=dirs["data_root_dir"],
        #                 id=result_db["integrate_result_id"],
        #                 date=result_db["date"]
        #                 )
        #
        #             #now transfer the files
        #             transferred = TransferToUI(
        #                 type="integrate-orphan",
        #                 settings=self.SecretSettings,
        #                 result=result_db,
        #                 trip=trip_db,
        #                 logger=self.logger
        #                 )
        #
        #     #now place the files in the data_root_dir for the user to have and to hold
        #     if self.SecretSettings["copy_data"]:
        #         copied = CopyToUser(root=dirs["data_root_dir"],
        #                             res_type="integrate",
        #                             result=result_db,
        #                             logger=self.logger)
        #     #the addition of result to db has failed, but still needs removed from the cloud
        #     #this is not YET an option so pass for now
        #     else:
        #         pass
        #
        # # Merging two wedges
        # elif command == "SMERGE":
        #     self.logger.debug("SMERGE Received")
        #     self.logger.debug(dirs)
        #     self.logger.debug(info)
        #     self.logger.debug(settings)
        #     self.logger.debug(results)
        #
        #
        #     result_db = self.database.addSimpleMergeResult(dirs=dirs,
        #                                                    info=info,
        #                                                    settings=settings,
        #                                                    results=results)
        #     self.logger.debug("Added simple merge result: %s" % str(result_db))
        #
        #     #mark the process as finished
        #     self.database.modifyProcessDisplay(process_id=result_db["process_id"],
        #                                        display_value="complete")
        #
        #     #move the files to the server
        #     if result_db:
        #         trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
        #         self.logger.debug(trip_db)
        #         #this data has an associated trip
        #         if trip_db:
        #             for record in trip_db:
        #                 #now transfer the files
        #                 transferred = TransferToUI(type="smerge",
        #                                            settings=self.SecretSettings,
        #                                            result=result_db,
        #                                            trip=record,
        #                                            logger=self.logger)
        #         #this data is an "orphan"
        #         else:
        #             self.logger.debug("Orphan result")
        #             #add the orphan to the orphan database table
        #             self.database.addOrphanResult(type="smerge",
        #                                           root=dirs["data_root_dir"],
        #                                           id=result_db["integrate_result_id"],
        #                                           date=result_db["date"])
        #
        #             #now transfer the files
        #             transferred = TransferToUI(type="smerge-orphan",
        #                                        settings=self.SecretSettings,
        #                                        result=result_db,
        #                                        trip=trip_db,
        #                                        logger=self.logger)
        #
        #         #now place the files in the data_root_dir for the user to have and to hold
        #         if self.SecretSettings["copy_data"]:
        #             copied = CopyToUser(root=dirs["data_root_dir"],
        #                                 res_type="smerge",
        #                                 result=result_db,
        #                                 logger=self.logger)
        #         #the addition of result to db has failed, but still needs removed from the cloud
        #         #this is not YET an option so pass for now
        #         else:
        #             pass
        #
        #
        # # Merging two wedges
        # elif command == "BEAMCENTER":
        #     self.logger.debug("BEAMCENTER Received")
        #     self.logger.debug(dirs)
        #     self.logger.debug(info)
        #     self.logger.debug(settings)
        #     self.logger.debug(results)
        #
        # elif command == "SAD":
        #     self.logger.debug("Received SAD result")
        #     result_db = self.database.addSadResult(dirs=dirs,
        #                                            info=info,
        #                                            settings=settings,
        #                                            results=results)
        #     self.logger.debug("Added SAD result: %s" % str(result_db))
        #
        #     #mark the process as finished
        #     self.database.modifyProcessDisplay(process_id=settings["process_id"],
        #                                        display_value="complete")
        #
        #     #move the files to the server
        #     if result_db:
        #         trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
        #         #this data has an associated trip
        #         if trip_db:
        #             for record in trip_db:
        #                 #update the dates for the trip
        #                 self.database.updateTrip(trip_id=record["trip_id"],
        #                                          date=result_db["timestamp"])
        #                 #now transfer the files
        #                 transferred = TransferToUI(
        #                     type="sad",
        #                     settings=self.SecretSettings,
        #                     result=result_db,
        #                     trip=record,
        #                     logger=self.logger
        #                     )
        #         #this data is an "orphan"
        #         else:
        #             self.logger.debug("Orphan result")
        #             #add the orphan to the orphan database table
        #             self.database.addOrphanResult(
        #                 type="sad",
        #                 root=dirs["data_root_dir"],
        #                 id=result_db["sad_result_id"],
        #                 date=result_db["date"]
        #                 )
        #
        #             #now transfer the files
        #             transferred = TransferToUI(type="sad-orphan",
        #                                        settings=self.SecretSettings,
        #                                        result=result_db,
        #                                        trip=trip_db,
        #                                        logger=self.logger)
        #
        #     #now place the files in the data_root_dir for the user to have and to hold
        #     if self.SecretSettings["copy_data"]:
        #         if result_db["download_file"] != "None":
        #             copied = CopyToUser(root=dirs["data_root_dir"],
        #                                 res_type="sad",
        #                                 result=result_db,
        #                                 logger=self.logger)
        #     #the addition of result to db has failed, but still needs removed from the cloud
        #     #this is not YET an option so pass for now
        #     else:
        #         pass
        #
        # elif command == "MAD":
        #     self.logger.debug("Received MAD result")
        #
        #     result_db = self.database.addMadResult(dirs=dirs,
        #                                            info=info,
        #                                            settings=settings,
        #                                            results=results)
        #     self.logger.debug("Added MAD result: %s" % str(result_db))
        #
        #     #mark the process as finished
        #     self.database.modifyProcessDisplay(process_id=settings["process_id"],
        #                                        display_value="complete")
        #
        #     #move the files to the server
        #     if result_db:
        #         trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
        #         #this data has an associated trip
        #         if trip_db:
        #             for record in trip_db:
        #                 #update the dates for the trip
        #                 self.database.updateTrip(trip_id=record["trip_id"],
        #                                          date=result_db["timestamp"])
        #                 #now transfer the files
        #                 transferred = TransferToUI(type="mad",
        #                                            settings=self.SecretSettings,
        #                                            result=result_db,
        #                                            trip=record,
        #                                            logger=self.logger)
        #
        #     #now place the files in the data_root_dir for the user to have and to hold
        #     if self.SecretSettings["copy_data"]:
        #         if (result_db["download_file"] not in ["None", "FAILED"]):
        #             copied = CopyToUser(root=dirs["data_root_dir"],
        #                                 res_type="mad",
        #                                 result=result_db,
        #                                 logger=self.logger)
        #     #the addition of result to db has failed, but still needs removed from the cloud
        #     #this is not YET an option so pass for now
        #     else:
        #         pass
        #
        # elif command == "MR":
        #     self.logger.debug("Received MR result")
        #     result_db = self.database.addMrResult(dirs=dirs,
        #                                           info=info,
        #                                           settings=settings,
        #                                           results=results)
        #     #some debugging output
        #     self.logger.debug("Added MR result: %s" % str(result_db))
        #
        #     #If the process is complete, mark it as such
        #     if result_db["mr_status"] != "WORKING":
        #         #mark the process as finished
        #         self.database.modifyProcessDisplay(process_id=result_db["process_id"],
        #                                            display_value="complete")
        #     #move the files to the server
        #     if result_db:
        #         #Get the trip for this data
        #         trip_db = self.database.getTrips(data_root_dir=dirs["data_root_dir"])
        #         #this data has an associated trip
        #         if trip_db:
        #             for record in trip_db:
        #                 #update the dates for the trip
        #                 self.database.updateTrip(trip_id=record["trip_id"],
        #                                          date=result_db["timestamp"])
        #                 #now transfer the files
        #                 transferred = TransferToUI(type="mr",
        #                                            settings=self.SecretSettings,
        #                                            result=result_db,
        #                                            trip=record,
        #                                            logger=self.logger)
        #
        #     #now place the files in the data_root_dir for the user to have and to hold
        #     if  self.SecretSettings["copy_data"]:
        #         all_mr_results = self.database.getMrTrialResult(result_db["mr_result_id"])
        #         #some debugging output
        #         self.logger.debug("Transfer MR file: ID %s" % result_db["mr_result_id"])
        #         if all_mr_results:
        #             for mr_result in all_mr_results:
        #                 result_db["download_file"] = mr_result["archive"]
        #                 copied = CopyToUser(root=dirs["data_root_dir"],
        #                                     res_type="mr",
        #                                     result=result_db,
        #                                     logger=self.logger)
        #
        #     #the addition of result to db has failed, but still needs removed from the cloud
        #     #this is not YET an option so pass for now
        #     else:
        #         pass
        #
        #
        # elif command == "DOWNLOAD":
        #     #get the trip info
        #     trip_db = self.database.getTrips(data_root_dir=info["data_root_dir"])
        #
        #     success = False
        #     if trip_db:
        #         for record in trip_db:
        #             #move files to the server
        #             transferred = TransferToUI(
        #                 type="download",
        #                 settings=self.SecretSettings,
        #                 result=info,
        #                 trip=record,
        #                 logger=self.logger
        #                 )
        #             if transferred:
        #                 success = True
        #
        #     #update the database
        #     if success:
        #         #note the result in cloud_complete
        #         self.database.enterCloudComplete(cloud_request_id=info["cloud_request_id"],
        #                                          request_timestamp=info["timestamp"],
        #                                          request_type=info["request_type"],
        #                                          data_root_dir=info["data_root_dir"],
        #                                          ip_address=info["ip_address"],
        #                                          start_timestamp=0,
        #                                          result_id=0,
        #                                          archive=os.path.basename(info["archive"]))
        #
        #         #mark in cloud_requests
        #         self.database.markCloudRequest(
        #             cloud_request_id=info["cloud_request_id"],
        #             mark="complete"
        #             )
        #
        #     #the transfer was not successful
        #     else:
        #         #note the result in cloud_complete
        #         self.database.enterCloudComplete(cloud_request_id=info["cloud_request_id"],
        #                                          request_timestamp=info["timestamp"],
        #                                          request_type=info["request_type"],
        #                                          data_root_dir=info["data_root_dir"],
        #                                          ip_address=info["ip_address"],
        #                                          start_timestamp=0,
        #                                          result_id=0,
        #                                          archive=os.path.basename(info["archive"]))
        #
        #         #mark in cloud_requests
        #         self.database.markCloudRequest(cloud_request_id=info["cloud_request_id"],
        #                                        mark="failure")
        #
        # elif command == "STATS":
        #     self.logger.debug("Received STATS result")
        #
        #     #rearrange results
        #     results = server.copy()
        #
        #     #self.logger.debug(info)
        #     #self.logger.debug(results)
        #     result_db = self.database.addStatsResults(info=info,
        #                                               results=results)
        #     self.logger.debug("Added STATS result: %s" % str(result_db))
        #
        #     #mark the process as finished
        #     self.database.modifyProcessDisplay(process_id=info["process_id"],
        #                                        display_value="complete")
        #
        #     #move the files to the server
        #     if result_db:
        #         #Get the trip for this data
        #         trip_db = self.database.getTrips(result_id=result_db["result_id"])
        #         #print trip_db
        #         #this data has an associated trip
        #         if trip_db:
        #             for record in trip_db:
        #                 #update the dates for the trip
        #                 self.database.updateTrip(trip_id=record["trip_id"],
        #                                          date=result_db["timestamp"])
        #                 #now transfer the files
        #                 transferred = TransferToUI(type="stats",
        #                                            settings=self.SecretSettings,
        #                                            result=result_db,
        #                                            trip=record,
        #                                            logger=self.logger)
        #         #this data is an "orphan"
        #         else:
        #             self.logger.debug("Orphan result")
        #             #now transfer the files
        #             transferred = TransferToUI(type="stats-orphan",
        #                                        settings=self.SecretSettings,
        #                                        result=result_db,
        #                                        trip=trip_db,
        #                                        logger=self.logger)
        #
        # elif command == "TEST":
        #     self.logger.debug("Cluster connection test successful")
        #
        # elif command == "SPEEDTEST":
        #     self.logger.debug("Cluster connection test successful")
        #
        # elif command == "DISTL_PARMS_REQUEST":
        #     self.logger.debug("DISTL params request for %s" % info)
        #     cf = ConsoleFeeder(mode="DISTL_PARMS_REQUEST",
        #                        db=self.database,
        #                        bc=self.BEAMLINE_CONNECTION,
        #                        data=info,
        #                        logger=self.logger)
        #
        # elif command == "CRYSTAL_PARMS_REQUEST":
        #     self.logger.debug("CRYSTAL params request for %s" % info)
        #     cf = ConsoleFeeder(mode="CRYSTAL_PARMS_REQUEST",
        #                        db=self.database,
        #                        bc=self.BEAMLINE_CONNECTION,
        #                        data=info,
        #                        logger=self.logger)
        #
        # elif command == "BEST_PARMS_REQUEST":
        #     self.logger.debug("BEST params request for %s" % info)
        #     cf = ConsoleFeeder(mode="BEST_PARMS_REQUEST",
        #                        db=self.database,
        #                        bc=self.BEAMLINE_CONNECTION,
        #                        data=info,
        #                        logger=self.logger)

        else:
            self.logger.info("Take no action for message")
            self.logger.info(message)

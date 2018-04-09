"""
Code for the coordination of site activities for a RAPD install - the monitoring
of data collection and the "cloud", as well as the running of processes and
logging of all metadata
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2009-2018 Cornell University
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
from pprint import pprint
# import redis
# import socket
import sys
import time

# RAPD imports
from control.control_server import LaunchAction, ControllerServer
from utils.modules import load_module
from utils.site import get_ip_address
from utils.text import json
from bson.objectid import ObjectId
# from rapd_console import ConsoleFeeder
# from rapd_site import TransferToUI, TransferToBeamline, CopyToUser

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
    # return_address = None
    alt_image_path_server = None
    image_monitor = None
    run_monitor = None
    cloud_monitor = None
    site_adapter = None
    remote_adapter = None

    def __init__(self, SITE, settings={}, overwatch_id=None):
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
        self.settings = settings
        self.overwatch_id = overwatch_id

        # Start the process
        self.run()

    def run(self):
        """
        Initialize monitoring the beamline.
        """

        self.logger.debug("Starting")

        # Process the site
        self.init_site()

        # Start connection pool to redis instance
        self.connect_to_redis()

        # Start connection to the core database
        self.connect_to_database()

        # Start the server for receiving communications
        self.start_server()

        # Import the detector
        self.init_detectors()

        # start the alt_image_path_server
        self.start_image_path_server()

        # start launcher manager
        self.start_launcher_manager()

        # Start the run monitor
        self.start_run_monitor()

        # Start the image monitor
        self.start_image_monitor()

        # Start the cloud monitor
        # self.start_cloud_monitor()

        # Initialize the site adapter (communicating with beamline)
        self.init_site_adapter()

        # Initialize the remote adapter
        # self.init_remote_adapter()

        # Launch an echo
        self.send_echo()

    def init_site(self):
        """Process the site definitions to set up instance variables"""

        # Single or multiple IDs
        # A string is input - one tag
        if isinstance(self.site.ID, str):
            self.site_ids = [self.site.ID]
            self.pairs[self.site.ID] = collections.deque([("", 0), ("", 0)], 2)

        # Tuple or list
        elif isinstance(self.site.ID, tuple) or isinstance(self.site.ID, list):
            for site_id in self.site.ID:
                self.site_ids.append(site_id)
                self.pairs[site_id] = collections.deque([("", 0), ("", 0)], 2)

    def connect_to_redis(self):
        """Connect to the redis instance"""
        redis_database = importlib.import_module('database.redis_adapter')

        self.redis_database = redis_database.Database(settings=self.site.CONTROL_DATABASE_SETTINGS)
        self.redis = self.redis_database.connect_to_redis()

    def stop_redis(self):
        """Make a clean Redis disconnection if using a pool connection."""
        self.logger.debug("Close Redis")

        self.redis_database.stop()

    def connect_to_database(self):
        """Set up database connection"""

        # Import the database adapter as database module
        # global database
        database = importlib.import_module('database.%s_adapter' % self.site.CONTROL_DATABASE)

        # Shorten it a little
        site = self.site

        # Instantiate the database connection
        if site.CONTROL_DATABASE_SETTINGS.get('DATABASE_STRING', False):
            self.database = database.Database(string=site.CONTROL_DATABASE_SETTINGS['DATABASE_STRING'])
        else:
            self.database = database.Database(host=site.CONTROL_DATABASE_SETTINGS['DATABASE_HOST'],
                                              #port=site.DATABASE_SETTINGS['DB_PORT'],
                                              user=site.CONTROL_DATABASE_SETTINGS['DATABASE_USER'],
                                              password=site.CONTROL_DATABASE_SETTINGS['DATABASE_PASSWORD'])
        #self.database = database.Database(string=site.CONTROL_DATABASE_SETTINGS['DATABASE_STRING'])

    def start_server(self):
        """Start up the listening process for core"""

        self.server = ControllerServer(receiver=self.receive,
                                       site=self.site)

    def stop_server(self):
        """Stop the listening server on exit"""

        self.logger.debug("Stop core server")

        self.server.stop()

    def init_detectors(self):
        """Set up the detectors"""

        self.logger.debug("Setting up the detectors")

        # Shorten variable names
        site = self.site

        import sites.detectors.necat_dectris_eiger16m

        # A single detector
        if site.DETECTOR:
            #detector, suffix = site.DETECTOR
            detector = site.DETECTOR
            detector = detector.lower()
            self.detectors[self.site_ids[0].upper()] = load_module(
                seek_module=detector,
                directories=("sites.detectors", "detectors"),
                logger=self.logger)

        # Multiple detectors
        elif site.DETECTORS:
            for site_id in self.site_ids:
                detector, suffix = site.DETECTORS[site_id]
                detector = detector.lower()
                self.detectors[site_id.upper()] = load_module(
                    seek_module=detector,
                    directories=("sites.detectors", "detectors"))

    def start_image_path_server(self):
        """Only start if self.site.ALT_IMAGE_SERVER_NAME is set"""
        # Check if module or class exists to get path of images in RAMDISK
        #if self.site.ALT_IMAGE_LOCATION and self.site.ALT_IMAGE_SERVER_NAME:
        if hasattr(self.site, 'ALT_IMAGE_LOCATION') and hasattr(self.site, 'ALT_IMAGE_SERVER_NAME'):
            self.logger.debug("Starting image path server")
            self.alt_image_path_server = {}
            for site_id in self.detectors.keys():
                if hasattr(self.detectors[site_id], self.site.ALT_IMAGE_SERVER_NAME):
                    self.alt_image_path_server[site_id] = eval('self.detectors[site_id].%s()'%self.site.ALT_IMAGE_SERVER_NAME)

    def start_launcher_manager(self):
        """Start up the launcher manager to hand off jobs"""
        self.logger.debug("Starting launcher monitor")
        launcher_manager = importlib.import_module("launch.rapd_launcher_manager")
        self.launcher_manager = launcher_manager.Launcher_Manager(site=self.site,
                                                                  overwatch_id=None)

    def stop_launcher_manager(self):
        """Stop the launcher manager"""
        self.logger.debug("Stopping launcher manager")
        self.launcher_manager.stop()

    def start_image_monitor(self):
        """Start up the image listening process for core"""

        if (self.settings["monitor"]):

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
                    clean_start=self.settings.get("clean_start", False),
                    overwatch_id=self.overwatch_id)

        else:
            self.logger.debug("NOT starting image monitor")

    def stop_image_monitor(self):
        """Stop the image listening process for core"""

        self.logger.debug("Stopping image monitor")
        if self.site.IMAGE_MONITOR:
            self.image_monitor.stop()

    def start_run_monitor(self):
        """Start up the run information listening process for core"""

        if (self.settings["monitor"]):

            self.logger.debug("Starting run monitor")

            # Shorten variable names
            site = self.site

            if site.RUN_MONITOR:
                # Import the specific run monitor module
                run_monitor = importlib.import_module("%s" % site.RUN_MONITOR.lower())
                self.run_monitor = run_monitor.Monitor(site=self.site,
                                                       notify=self.receive,
                                                       # Not using overwatch in run monitor
                                                       # could if we wanted to
                                                       overwatch_id=None)
        else:
            self.logger.debug("NOT starting run monitor")

    def stop_run_monitor(self):
        """Stop the run information listening process for core"""

        self.logger.debug("Stopping run monitor")
        if self.site.RUN_MONITOR:
            self.run_monitor.stop()

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
                                                            reply_settings=False,
                                                            interval=site.CLOUD_INTERVAL)

    def stop_cloud_monitor(self):
        """Stop the cloud listening process for core"""
        if site.CLOUD_MONITOR:
            self.cloud_monitor.stop()

    def init_site_adapter(self):
        """Initialize the connection to the site"""

        # Shorten variable names
        site = self.site

        if site.SITE_ADAPTER:
            site_adapter = importlib.import_module("%s" % site.SITE_ADAPTER.lower())
            self.site_adapter = site_adapter.Adapter(settings=site.SITE_ADAPTER_SETTINGS)

    def init_remote_adapter(self):
        """Initialize connection to remote access system"""

        # Shorten variable names
        site = self.site

        if site.REMOTE_ADAPTER:
            remote_adapter = importlib.import_module("%s" % site.REMOTE_ADAPTER.lower())
            self.remote_adapter = remote_adapter.Adapter(settings=site.REMOTE_ADAPTER_SETTINGS)

    def send_echo(self):
        """Send a test echo request to Launch"""

        # Construct a working directory and repr
        work_dir = self.get_work_dir(type_level="echo")

        # Run an echo to make sure everything is up
        command = {
            "command":"ECHO",
            "process":{
                "status":0,
                "source":"server"
                },
            "directories":{
                "work":work_dir
                }
            }
        self.send_command(command, "RAPD_JOBS")

    def send_command(self, command, channel="RAPD_JOBS"):
        """Send a command over redis for processing"""

        print "send_command"
        pprint(command)

        self.redis.lpush(channel, json.dumps(command))
        print "Command sent"

    def stop(self):
        """Stop the ImageMonitor,CloudMonitor and StatusRegistrar."""
        self.logger.info("Stopping")

        self.stop_redis()
        self.stop_server()
        self.stop_launcher_manager()
        self.stop_image_monitor()
        self.stop_run_monitor()
        #self.stop_cloud_monitor()

    def add_image(self, image_data):
        """
        Handle a new image being recorded by the site

        Keyword argument
        image_data -- information gathered about the image, primarily from the header
        """
        # Placeholder for site info not in image header
        site_header = {}

        # Unpack image_data
        fullname = image_data.get("fullname", None)
        site_tag = image_data.get("site_tag", None)

        self.logger.debug("Received new image %s", fullname)

        # Shortcut to detector
        detector = self.detectors[site_tag]

        # Check if it exists. May have been deleted from RAMDISK
        #if os.path.isfile(fullname) in (False, None):
        #    if self.site.ALT_IMAGE_LOCATION:
        #        fullname = detector.get_alt_path(fullname)

        # Save some typing
        dirname = os.path.dirname(fullname)

        for d in self.site.IMAGE_IGNORE_DIRECTORIES:
            if dirname.startswith(d):
                self.logger.debug("Directory %s is marked to be ignored - skipping", dirname)
                return True

        # File contains an ingnore flag
        if any(ignore_string in fullname for ignore_string in self.site.IMAGE_IGNORE_STRINGS):
            self.logger.debug("Images contains an ignore flag - skipping")
            return True

        # Figure out if image in the current run...
        run_id, place_in_run = self.in_run(site_tag, fullname)
        self.logger.debug("run_id: %s place_in_run:%s", str(run_id), str(place_in_run))

        # Image is in a run
        if isinstance(place_in_run, int):

            self.logger.debug("%s is in run %s at position %s", fullname, run_id, place_in_run)

            # Save some typing
            current_run = self.recent_runs[str(run_id)]

            self.logger.debug(current_run)

            # If not integrating trigger integration

            if not current_run.get("rapd_status", None) in ("INTEGRATING", "FINISHED"):
            #if True:
                #print 'run_status: %s'%current_run.get("rapd_status", None)
                # Right on time
                if place_in_run == 1:
                    # Grab extra data for the image and add to the header
                    if self.site_adapter:
                        if self.site_adapter.settings.has_key(site_tag.upper()):
                            site_data = self.site_adapter.get_image_data(site_tag.upper())
                        else:
                            site_data = self.site_adapter.get_image_data()
                        site_header = site_data

                    # Get all the image information
                    attempt_counter = 0
                    while attempt_counter < 5:
                        try:
                            attempt_counter += 1
                            if os.path.exists(fullname):
                                header = detector.read_header(
                                    fullname,
                                    beam_settings=self.site.BEAM_INFO[site_tag.upper()],
                                    extra_header=site_header)
                                break
                            else:
                                time.sleep(0.2)
                        except IOError:
                            self.logger.exception("Unable to access image")
                    else:
                        self.logger.error("Unable to access image after %d tries", attempt_counter)
                        return False

                    # Put data about run in the header object
                    header["collect_mode"] = "run"
                    header["run_id"] = str(run_id)
                    header["run"] = self.recent_runs[str(run_id)].copy()
                    header["place_in_run"] = 1
                    header["site_tag"] = site_tag

                    # Add to the database
                    image_id = self.database.add_image(data=header, return_type="id")

                    # Add extra stuff to the header
                    header["_id"] = image_id
                    header["xdsinp"] = detector.XDSINP

                    # Add the image template to the run information
                    header["run"]["image_template"] = detector.create_image_template(
                        image_prefix=header["image_prefix"],
                        run_number=header["run_number"]
                        )

                    # Send to be processed
                    self.new_data_image(image1=header)

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
        elif str(run_id) == "SNAP":

            self.logger.debug("%s is a snap", fullname)

            # Grab extra data for the image and add to the header
            if self.site_adapter:
                if self.site_adapter.settings.has_key(site_tag.upper()):
                    site_data = self.site_adapter.get_image_data(site_tag.upper())
                else:
                    site_data = self.site_adapter.get_image_data()
                site_header = site_data

            # Get all the image information
            attempt_counter = 0
            while attempt_counter < 5:
                try:
                    attempt_counter += 1
                    if os.path.exists(fullname):
                        header = detector.read_header(
                            fullname,
                            beam_settings=self.site.BEAM_INFO[site_tag.upper()],
                            extra_header=site_header)
                        # Break out of loop
                        break
                    else:
                        time.sleep(0.2)
                except IOError:
                    self.logger.exception("Unable to access image")
            else:
                self.logger.error("Unable to access image after %d tries", attempt_counter)
                return False

            # Add some data to the header - no run_id for snaps
            header["collect_mode"] = "SNAP"
            header["run_id"] = None
            header["site_tag"] = site_tag

            # Add to database
            image_id = self.database.add_image(data=header, return_type="id")
            if image_id:
                header["_id"] = image_id
            # Duplicate entry
            else:
                return False

            # Update remote client
            if self.remote_adapter:
                self.remote_adapter.add_image(header)

            # KBO
            self.new_data_image(image1=header)

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
        return self.database.get_run(run_data=run_data,
                                     minutes=self.site.RUN_WINDOW,
                                     return_type="boolean")

    def query_in_run(self,
                     site_tag,
                     directory,
                     image_prefix,
                     run_number,
                     image_number,
                     minutes=0,
                     order="descending",
                     return_type="boolean"):
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
        for run_id, run in self.recent_runs.iteritems():
            print 'run_id:%s'%run_id
            print 'run: %s'%run

            self.logger.debug("_id:%s run:%s" % (run_id, str(run)))

            if run.get("site_tag", None) == site_tag and \
               run.get("directory", None) == directory and \
               run.get("image_prefix", None) == image_prefix and \
               run.get("run_number", None) == run_number:

                # Check image number
                run_start = run.get("start_image_number")
                run_end = run.get("number_images") + run_start - 1
                if image_number >= run_start and image_number <= run_end:
                    if return_type == "boolean":
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
                                                     return_type=return_type)

        # If boolean, just return
        if return_type == "boolean":
            return identified_runs
        else:
            if identified_runs == False:
                return False
            elif return_type == "id":
                return identified_runs
            elif return_type == "dict":
                # Update the local store
                for run in identified_runs:
                    self.recent_runs[str(run["_id"])] = run
                # Return runs
                return identified_runs

    def add_run(self, run_dict):
        """
        Add potentially new run to RAPD system

        Keyword arguments
        run_data -- dict containing data describing the run
        """

        self.logger.debug(run_dict)

        # Unpack the run_dict
        run_data = run_dict["run_data"]

        # Check if this run has already been stored
        recent_run = self.query_for_run(run_data=run_data, boolean=True)

        # Run data already stored
        if recent_run == True:

            self.logger.debug("This run has already been recorded")

        # Run is new to RAPD
        else:

            self.logger.debug("Adding run")

            # Save to the database
            run_id = self.database.add_run(run_data=run_data, return_type="id")

            # Update the run data with the db run_id
            run_data["run_id"] = run_id

            # Save the run_data to local store
            self.recent_runs[run_id] = run_data

            self.logger.debug("run added to database")
            self.logger.debug(run_data)

        return True

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

        # Flag for snap
        could_be_snap = True

        # The detector
        detector = self.detectors[site_tag.upper()]

        # If the detector can determine if run or snap
        if hasattr(detector, "is_run_from_imagename"):
            # Make sure we have a function
            if type(detector.is_run_from_imagename) == "function":
                # See if we have a SNAP
                if detector.is_run_from_imagename(fullname) == True:
                    could_be_snap = False
                else:
                    return "SNAP", None

        # Tease out the info from the file name
        directory, basename, image_prefix, run_number, image_number = detector.parse_file_name(fullname)

        self.logger.debug("%s %s %s %s %s",
                          directory,
                          basename,
                          image_prefix,
                          run_number,
                          image_number)        

        # Look for run information for this image
        run_info = self.query_in_run(site_tag=site_tag,
                                     directory=directory,
                                     image_prefix=image_prefix,
                                     run_number=run_number,
                                     image_number=image_number,
                                     minutes=self.site.RUN_WINDOW,
                                     return_type="dict")

        # No run information
        if not run_info:
            # SNAP
            if could_be_snap:
                return "SNAP", None
            # RUN
            else:
                return "RUN", None

        # Have run information
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
            return run_info["_id"], run_position

    def new_data_image(self, image1):
        """
        Handle the information that there is a new image in the database.

        There are several classes of images:
            1. The image is standalone and will be autoindexed
            2. The image is one of a pair of images for autoindexing
            3. The image is first in a wedge of data collection
            4. The image is in the middle of a wedge of data collection
            5. The image is last in a wedge of data collection

        Keyword argument
        image1 -- dict containing lots of image information
        """
        def fix_fullname(inp, tag, dir_help=False):
            """Change fullname if using RAMDISK"""
            if self.site.ALT_IMAGE_LOCATION:
                fn = False
                if self.alt_image_path_server:
                    if self.alt_image_path_server.has_key(tag):
                        if hasattr(self.alt_image_path_server[tag], 'get_alt_path'):
                            fn = self.alt_image_path_server[tag].get_alt_path(inp.get('fullname'))
                else:
                    if hasattr(self.detectors[tag], 'get_alt_path'):
                        fn = self.detectors[tag].get_alt_path(inp.get('fullname'))
                if fn:
                    # For snaps
                    if inp.get('fullname', False):
                        inp.update({'fullname': fn})
                    # For integration
                    if inp.get('directory', False):
                        inp.update({'directory': os.path.dirname(fn)})
                    # For integration
                    if inp.get('run', False):
                        inp['run'].update({'directory': os.path.dirname(fn)})
            return inp

        self.logger.debug(image1["fullname"])

        # Save some typing
        site = self.site
        data_root_dir = image1["data_root_dir"]
        site_tag = image1["site_tag"].upper()

        #if self.site.ALT_IMAGE_LOCATION:
        #    fullname = detector.get_alt_path(fullname)

        if image1.get("collect_mode", None) == "SNAP":

            # Add the image to self.pair
            self.pairs[site_tag].append((image1["fullname"].lower(), image1["_id"]))

            work_dir = self.get_work_dir(type_level="single",
                                         image_data1=image1)

            # Now package directories into a dict for easy access by worker class
            directories = {"work":work_dir,
                           "data_root_dir":data_root_dir,
                           "plugin_directories":self.site.RAPD_PLUGIN_DIRECTORIES}

            # Get the session id
            session_id = self.get_session_id(image1)

            # Run autoindex and strategy plugin
            command = {"command":"INDEX",
                       "process":{
                           "image1_id":image1.get("_id"),
                           "image2_id":False,
                           "parent_id":False,
                           "result_id":str(ObjectId()),
                           "session_id":session_id,
                           "source":"server",
                           "status":0,
                       },
                       "directories":directories,
                       #"image1":image1,
                       "image1":fix_fullname(image1, site_tag),
                       "site_parameters":self.site.BEAM_INFO[image1["site_tag"]],
                       "preferences":{
                           "cleanup":False,
                           "json":False,
                       }
                      }

            self.send_command(command, "RAPD_JOBS")

            # If the last two images have "pair" in their name - look more closely
            if ("pair" in self.pairs[site_tag][0][0]) and ("pair" in self.pairs[site_tag][1][0]):
                self.logger.debug("Potentially a pair of images")

                # Break down the image name
                (directory1,
                 basename1,
                 prefix1,
                 run_number1,
                 image_number1) = self.detectors[site_tag].parse_file_name(self.pairs[site_tag][0][0])

                (directory2,
                 basename2,
                 prefix2,
                 run_number2,
                 image_number2) = self.detectors[site_tag].parse_file_name(self.pairs[site_tag][1][0])

                # Everything matches up to the image number, which is incremented by 1
                #if (directory1, basename1, prefix1) == (directory2, basename2, prefix2) and (image_number1 == image_number2-1):
                ### Have to modify for /epu/rdma since each image are in their own directory.
                #if (basename1, prefix1) == (basename2, prefix2) and (image_number1 == image_number2-1):
                if basename1[0:basename1.rfind('_')] == basename2[0:basename2.rfind('_')] and (image_number1 == image_number2-1):
                    self.logger.info("This looks like a pair to me: %s, %s",
                                     self.pairs[site_tag][0][0],
                                     self.pairs[site_tag][1][0])

                    # Make a copy of the second pair to be LESS confusing
                    image2 = image1.copy()

                    # Get the data for the first image
                    image1 = self.database.get_image_by_image_id(image_id=self.pairs[site_tag][0][1])

                    # Derive  directory and repr
                    work_dir = self.get_work_dir(type_level="pair",
                                                 image_data1=image1,
                                                 image_data2=image2)

                    # Now package directories into a dict for easy access by worker class
                    directories = {"work" : work_dir,
                                   "data_root_dir" : data_root_dir,
                                   "plugin_directories":self.site.RAPD_PLUGIN_DIRECTORIES}

                    # Get the session id
                    session_id = self.get_session_id(image1)

                    # Run autoindex and strategy plugin
                    command = {"command":"INDEX",
                               "process":{
                                   "image1_id":image1.get("_id"),
                                   "image2_id":image2.get("_id"),
                                   "parent_id":False,
                                   "result_id":str(ObjectId()),
                                   "session_id":session_id,
                                   "source":"server",
                                   "status":0,
                               },
                               "directories":directories,
                               #"image1":image1,
                               "image1":fix_fullname(image1, site_tag),
                               #"image2":image2,
                               "image2":fix_fullname(image2, site_tag),
                               "site_parameters":self.site.BEAM_INFO[image1["site_tag"]],
                               "preferences":{}
                              }

                    self.send_command(command, "RAPD_JOBS")

        # This is the runs portion of the data image handling
        else:

            # Make it easier to use run info
            run_position = image1["place_in_run"]

            # Derive  directory and repr
            work_dir = self.get_work_dir(type_level="integrate",
                                         image_data1=image1)

            # Now package directories into a dict for easy access by worker class
            directories = {"work":work_dir,
                           "data_root_dir":data_root_dir,
                           "plugin_directories":self.site.RAPD_PLUGIN_DIRECTORIES}

            # Get the session id
            session_id = self.get_session_id(image1)

            # Fix for RDMA file locations
            image1 = fix_fullname(image1, site_tag)
            # Pop out the run data
            run_data = image1.pop("run")
            xdsinp = image1.pop("xdsinp")

            # Construct and send command
            command = {
                "command":"INTEGRATE",
                "process":{
                    "image_id":image1.get("_id"),
                    "parent_id":False,
                    "result_id":str(ObjectId()),
                    "run_id":run_data.get("_id"),
                    "session_id":session_id,
                    "status":0,
                    "type":"plugin"
                    },
                "directories":directories,
                "data": {
                    "image_data":image1,
                    "run_data":run_data
                },
                "site_parameters":self.site.BEAM_INFO[image1["site_tag"]],
                "preferences":{
                    "analysis":True,
                    "cleanup":False,
                    "json":False,
                    "exchange_dir":self.site.EXCHANGE_DIR,
                    "run_mode":"server",
                    "xdsinp":xdsinp
                },
            }
            self.send_command(command, "RAPD_JOBS")

            # Set the run status
            self.recent_runs[image1["run_id"]]["rapd_status"] = "INTEGRATING"
            # TODO - update database version of run as well

    def get_session_id(self, header):
        """Get a session_id"""

        self.logger.debug("get_session_id")

        # Is the session information figured out by the image file name
        session_id = self.database.get_session_id(data_root_dir=header.get("data_root_dir", None))

        if (not session_id) or (session_id == "None"):

            self.logger.debug("No session_id from self.database.get_session_id")

            # Determine group_id
            if self.site.GROUP_ID:
                print "Have self.site.GROUP_ID"
                det_type, det_attribute, det_field = self.site.GROUP_ID
                if det_type == "stat":
                    attribute_value = os.stat(header.get("data_root_dir")).__getattribute__("st_%s" % det_attribute)
                    group_id = self.database.get_group(value=attribute_value,
                                                       field=det_field,
                                                       just_id=True)
            else:
                group_id = None

            session_id = self.database.create_session(
                data_root_dir=header.get("data_root_dir", None),
                group=group_id,
                site=header.get("site_tag", None)
            )

        self.logger.debug("session_id %s" % session_id)

        return session_id

    def get_work_dir(self, type_level, image_data1=False, image_data2=False):
        """
        Return a valid working directory for rapd_plugin to work in

        Keyword arguments
        type_level -- the type of work, single, pair, integrate, echo
        image_data1 -- header information from the first image (default = False)
        image_data2 -- header information from the second image (default = False)
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

        else:
            sub_dir = type_level

        # Join the  levels
        work_dir_candidate = os.path.join(typelevel_dir,
                                          datelevel_dir,
                                          sub_dir)

        return work_dir_candidate

    def handle_plugin_communication(self, message):
        """
        Handle incoming communications from plugins

        Keyword arguments
        message -- dict of pertinent information.
        """

        # Save the results for the plugin
        if "results" in message:

            # Save the result
            __ = self.database.save_plugin_result(message)

            """
            # Release hold on dataset in RAMDISK
            if self.site.ALT_IMAGE_LOCATION and self.site.ALT_IMAGE_SERVER_NAME:
                _id = False
                if message.get('process', False):
                    if message.get('process').get('status', 1) in (-1, 100):
                        # snaps
                        if message.get('process').has_key('image1_id'):
                            _id = message.get('process').get('image1_id', False)
                        # integration
                        if message.get('process').has_key('image_id'):
                            _id = message.get('process').get('image_id', False)
                        if _id:
                            # get the header from the DB
                            header = self.database.get_image_by_image_id(image_id=_id)
                            if self.alt_image_path_server.has_key(header.get('site_tag').upper()):
                                # send fullname to release_data
                                self.alt_image_path_server[header.get('site_tag').upper()].release_data(header.get('fullname'))
            """
    def receive(self, message):
        """
        Receive information from ControllerServer (self.SERVER) and handle accordingly.

        Keyword arguments
        message -- information to be preocessed, a dict

        Types currently handled: NEWIMAGE, NEWRUN
        """

        # self.logger.debug("Received: %s", message)

        command = message.get("command")
        self.logger.debug("Received message")

        # From a plugin
        if message.get("process", {}).get("type") == "plugin":
            self.handle_plugin_communication(message=message)

        # NEWIMAGE
        elif message.get("message_type", None) == "NEWIMAGE":
            self.add_image(message)

        # NEWRUN
        elif message.get("message_type", None) == "NEWRUN":
            self.add_run(message)

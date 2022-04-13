"""Generate a RAPD detector scaffold file"""

"""
This file is part of RAPD

Copyright (C) 2017, Cornell University
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

__created__ = "2017-1-19"
_maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
# import datetime
# import glob
# import logging
# import multiprocessing
# import os
# import pprint
# import pymongo
# import redis
# import shutil
# import subprocess
# import sys
# import time

# RAPD imports
from base import FileGenerator as CommandlineFileGenerator
from base import split_text_blob
# import commandline_utils
# import import detectors.detector_utils as detector_utils
# import utils

class FileGenerator(CommandlineFileGenerator):
    """File generator for detector wrapper"""

    def run(self):
        """The main actions of the module"""

        self.preprocess()

        self.write_file_docstring()
        self.write_license()
        self.write_docstrings()
        self.write_imports(write_list=("argparse",
                                       "from collections import OrderedDict",
                                       "importlib",
                                       "json",
                                       "os",
                                       "re",
                                       "shutil",
                                       "socket",
                                       "time",
                                       "uuid"),
                           added_rapd_imports=("from database.redis_adapter import Database as RedisDB",
                                               "utils.commandline",
                                               "from utils.text import json",))
        self.write_gatherer()
        self.write_commandline()
        self.write_main_func()
        self.write_main()

    def write_main_func(self, main_func_lines=False):
        """
        Write the main function
        """

        main_func_lines = [
            "def main(): ",
            "    \"\"\" ",
            "    The main process ",
            "    Setup logging and instantiate the gatherer ",
            "    \"\"\"\n ",
            "    # Get the commandline args ",
            "    commandline_args = get_commandline() \n",
            "    # Get the environmental variables ",
            "    environmental_vars = utils.site.get_environmental_variables() ",
            "    site = commandline_args.site \n",
            "    # If no commandline site, look to environmental args ",
            "    if site == None: ",
            "        if environmental_vars[\"RAPD_SITE\"]: ",
            "            site = environmental_vars[\"RAPD_SITE\"] \n",
            "    # Determine the site ",
            "    site_file = utils.site.determine_site(site_arg=site) \n",
            "    # Handle no site file ",
            "    if site_file == False: ",
            "        print text.error+\"Could not determine a site file. Exiting.\"+text.stop",
            "        sys.exit(9) \n",
            "    # Import the site settings ",
            "    SITE = importlib.import_module(site_file) \n",
            "    # Single process lock? ",
            "    utils.lock.file_lock(SITE.GATHERER_LOCK_FILE) \n",
            "    # Set up logging ",
            "    if commandline_args.verbose: ",
            "        log_level = 10 ",
            "    else: ",
            "        log_level = SITE.LOG_LEVEL ",
            "    logger = utils.log.get_logger(logfile_dir=SITE.LOGFILE_DIR, ",
            "                                  logfile_id=\"rapd_gatherer\", ",
            "                                  level=log_level ",
            "                                 ) ",
            "    logger.debug(\"Commandline arguments:\") ",
            "    for pair in commandline_args._get_kwargs(): ",
            "        logger.debug(\"  arg:%s  val:%s\" % pair) \n",
            "    # Instantiate the Gatherer ",
            "    GATHERER = Gatherer(site=SITE, ",
            "                        overwatch_id=commandline_args.overwatch_id) ",
        ]

        super(FileGenerator, self).write_main_func(main_func_lines=main_func_lines)

    def write_commandline(self):
        """
        Write the commandline parsing function
        """

        commandline_lines = [
            "def get_commandline():",
            "    \"\"\"",
            "    Get the commandline variables and handle them",
            "    \"\"\"\n",
            "    # Parse the commandline arguments",
            "    commandline_description = \"Data gatherer\"",
            "    parser = argparse.ArgumentParser(parents=[utils.commandline.base_parser],",
            "                                     description=commandline_description) \n",
            "    return parser.parse_args()\n"
        ]

        # Call the function in the parent class
        super(FileGenerator, self).write_commandline(description=False,
                                                     commandline_lines=commandline_lines)

    def write_gatherer(self):
        """Write the gatherer-specific functions"""

        # Any super-specific imports
        gatherer_imports = []
        self.output_function(gatherer_imports)

        # Information appears after imports
        gatherer_info = []
        self.output_function(gatherer_info)

        # Gatherer class
        gatherer_class = [
            "class Gatherer(object):",
            "    \"\"\"",
            "    Watches the beamline and signals images and runs over redis",
            "    \"\"\"\n"
            "    # For keeping track of file change times",
            "    run_time = 0",
            "    image_time = 0\n",
            "    # Host computer detail",
            "    ip_address = None\n",

            "    def __init__(self, site, overwatch_id=None):",
            "        \"\"\"",
            "        Setup and start the Gatherer",
            "        \"\"\"\n",
            "        # Get the logger Instance",
            "        self.logger = logging.getLogger(\"RAPDLogger\")\n",
            "        # Passed-in variables",
            "        self.site = site",
            "        self.overwatch_id = overwatch_id\n",
            "        self.logger.info(\"Gatherer.__init__\")\n",
            "        # Get our bearings",
            "        self.set_host()\n",
            "        # Connect to redis",
            "        self.connect()\n",
            "        # Running conditions",
            "        self.go = True\n",
            "        # Now run",
            "        self.run()\n",
            
            "    def run(self):",
            "        \"\"\"",
            "        The while loop for watching the files",
            "        \"\"\"",
            "        self.logger.info(\"Gatherer.run\")\n",
            "        # Set up overwatcher",
            "        self.ow_registrar = Registrar(site=self.site,",
            "                                      ow_type=\"gatherer\",",
            "                                      ow_id=self.overwatch_id)",
            "        self.ow_registrar.register({\"site_id\":self.site.ID})\n",
            "        # A RUN ONLY EXAMPLE",
            "        # Some logging",
            "        self.logger.debug(\"  Will publish new datasets on run_data:%s\" % self.tag)",
            "        self.logger.debug(\"  Will push new datasets onto runs_data:%s\" % self.tag)\n",
            "        try:",
            "            counter = 0",
            "            while self.go:\n",
            "                # NECAT uses a beamline Redis database to communicate",
            "                #----------------------------------------------------\n",
            "                # Check if the run info changed in beamline Redis DB.",
            "                current_run_raw = self.redis_beamline.get(\"RUN_INFO_SV\")\n",
            "                # New run information",
            "                if current_run_raw not in (None, \"\"):",
            "                    # Blank out the Redis entry",
            "                    self.redis_beamline.set(\"RUN_INFO_SV\", \"\")",
            "                    # Handle the run information",
            "                    self.handle_run(run_raw=current_run_raw)\n",
            "                # Have Registrar update status",
            "                if counter % 5 == 0:",
            "                    self.ow_registrar.update({\"site_id\":self.site.ID})",
            "                    counter = 0\n",
            "                # Increment counter",
            "                counter += 1\n",
            "                # Pause",
            "                time.sleep(1)",
            "        except KeyboardInterrupt:",
            "            self.stop()\n",
            "        # A RUN & IMAGES EXAMPLE",
            "        # Some logging",
            "        self.logger.debug(\"  Will publish new images on filecreate:%s\" % self.tag)",
            "        self.logger.debug(\"  Will push new images onto images_collected:%s\" % self.tag)",
            "        self.logger.debug(\"  Will publish new datasets on run_data:%s\" % self.tag)",
            "        self.logger.debug(\"  Will push new datasets onto runs_data:%s\" % self.tag)\n",
            "            while self.go:\n",
            "                # 5 rounds of checking",
            "                for ___ in range(5):",
            "                    # An example of file-based signalling",
            "                    # Check if the run info has changed on the disk",
            "                    if self.check_for_run_info():",
            "                        run_data = self.get_run_data()",
            "                        if run_data:",
            "                        # Handle the run information",
            "                        self.handle_run(run_raw=current_run_raw)\n",
            "                        # 20 image checks",
            "                        for __ in range(20):",
            "                            # Check if the image file has changed",
            "                            if self.check_for_image_collected():",
            "                                image_name = self.get_image_data()",
            "                                if image_name:",
            "                                    self.handle_image(image_name)",
            "                                break",
            "                            else:",
            "                                time.sleep(0.05)",

            "    def stop(self):",
            "        \"\"\"",
            "        Stop the loop",
            "        \"\"\"",
            "        self.logger.debug(\"Gatherer.stop\")\n",
            "        self.go = False\n",
            
            "    def set_host(self):",
            "        \"\"\"",
            "        Use os.uname to set files to watch",
            "        \"\"\"",
            "        self.logger.debug(\"Gatherer.set_host\")\n",
            "        # Figure out which host we are on",
            "        self.ip_address = socket.gethostbyaddr(socket.gethostname())[-1][0]",
            "        self.logger.debug(\"IP Address:\",self.ip_address)\n",
            "        # Now grab the file locations, beamline from settings",
            "        if self.site.GATHERERS.has_key(self.ip_address):",
            "            self.tag = self.site.GATHERERS[self.ip_address]",
            "            # Make sure we enforce uppercase for tag",
            "            self.tag = self.tag.upper()",
            "        else:",
            "            print \"ERROR - no settings for this host\"",
            "            self.tag = \"test\"\n",
            
            "    def connect(self):",
            "        \"\"\"",
            "        Connect to redis host",
            "        \"\"\"\n",
            "        self.logger.debug(\"Gatherer.connect\")\n",
            "        # Connect to RAPD Redis",
            "        self.redis_rapd = RedisDB(settings=self.site.CONTROL_DATABASE_SETTINGS)\n",
            "        # NECAT uses Redis to communicate with the beamline",
            "        # Connect to beamline Redis to monitor if run is launched",
            "        # self.redis_beamline = RedisDB(settings=self.site.SITE_ADAPTER_SETTINGS[self.tag])\n",
            "        # NECAT uses Redis to communicate with the remote system",
            "        # Connect to remote system Redis to monitor if run is launched",
            "        # self.redis_remote = RedisDB(settings=self.site.REMOTE_ADAPTER_SETTINGS)\n",
            
            "    def handle_run(self, run_raw):",
            "        \"\"\"",
            "        Handle the raw run information",
            "        \"\"\"\n",
            "        # Run information is encoded in JSON format",
            "        run_data = json.loads(current_run_raw)\n",
            "        # Determine if the run should be ignored\n",
            "        # If you need to manipulate the run information or add to it, here's the place\n",
            "        # Put into exchangable format",
            "        run_data_json = json.dumps(run_data)\n",
            "        # Publish to Redis",
            "        self.redis_rapd.publish(\"run_data:%s\" % self.tag, run_data_json)\n",
            "        # Push onto redis list in case no one is currently listening",
            "        self.redis_rapd.lpush(\"runs_data:%s\" % self.tag, run_data_json)\n",

            "    def handle_image(self, image_name):",
            "        \"\"\"",
            "        Handle a new image",
            "        \"\"\"\n",
            "        self.logger.debug(\"image_collected:%s %s\",",
            "                          self.tag,",
            "                          image_name)\n",
            "        # Publish to Redis",
            "        self.redis_rapd.publish(\"image_collected:%s\" % self.tag, image_name)\n",
            "        # Push onto redis list in case no one is currently listening",
            "        self.redis_rapd.lpush(\"images_collected:%s\" % self.tag, image_name)\n",

            "    # Used for file-based run information checking example",
            "    def check_for_run_info(self):",
            "        \"\"\"",
            "        Returns True if run_data_file has been changed, False if not",
            "        \"\"\"\n",
            "        # Make sure we have a file to check",
            "        if self.run_data_file:",
            "            tries = 0",
            "            while tries < 5:",
            "                try:",
            "                    statinfo = os.stat(self.run_data_file)",
            "                    break",
            "                except AttributeError:",
            "                    if tries == 4:",
            "                        return False",
            "                    time.sleep(0.01)",
            "                    tries += 1\n",
            "            # The modification time has not changed",
            "            if self.run_time == statinfo.st_ctime:",
            "                return False\n",
            "            # The file has changed",
            "            else:",
            "                self.run_time = statinfo.st_ctime",
            "                return True",
            "        else:",
            "            return False\n",
            "    # Used for file-based run information example",
            "    def get_run_data(self):",
            "        \"\"\"",
            "        Return contents of run data file",
            "        \"\"\"\n",
            "        if self.run_data_file:\n",
            "            # Copy the file to prevent conflicts with other programs",
            "            # Use the ramdisk if it is available",
            "            if os.path.exists(\"/dev/shm\"):",
            "                tmp_dir = \"/dev/shm/\"",
            "            else:",
            "                tmp_dir = \"/tmp/\"\n",
            "            tmp_file = tmp_dir+uuid.uuid4().hex",
            "            shutil.copyfile(self.run_data_file, tmp_file)\n",
            "            # Read in the pickled file",
            "            f = open(tmp_file, \"rb\")",
            "            raw_run_data = pickle.load(f)",
            "            f.close()",
            "            self.logger.debug(raw_run_data)\n",
            "            # Remove the temporary file",
            "            os.unlink(tmp_file)\n",
            "            # Standardize the run information",
            "            \"\"\"",
            "            The necessary fields are:",
            "                directory,",
            "                image_prefix,",
            "                run_number,",
            "                start_image_number,",
            "                number_images,",
            "                distance,",
            "                phi,",
            "                kappa,",
            "                omega,",
            "                osc_axis,",
            "                osc_start,",
            "                osc_width,",
            "                time,",
            "                transmission,",
            "                energy,",
            "                anomalous",
            "            \"\"\"",
            "            run_data = {",
            "                \"anomalous\":None,",
            "                \"beamline\":raw_run_data.get(\"beamline\", None),              # Non-standard",
            "                \"beam_size_x\":float(raw_run_data.get(\"beamsize\", 0.0)),     # Non-standard",
            "                \"beam_size_y\":float(raw_run_data.get(\"beamsize\", 0.0)),     # Non-standard",
            "                \"directory\":raw_run_data.get(\"directory\", None),",
            "                \"distance\":float(raw_run_data.get(\"dist\", 0.0)),",
            "                \"energy\":float(raw_run_data.get(\"energy\", 0.0)),",
            "                \"file_ctime\":datetime.datetime.fromtimestamp(self.run_time).isoformat(),",
            "                \"image_prefix\":raw_run_data.get(\"image_prefix\", None),",
            "                \"kappa\":None,",
            "                \"number_images\":int(float(raw_run_data.get(\"Nframes\", 0))),",
            "                \"omega\":None,",
            "                \"osc_axis\":\"phi\",",
            "                \"osc_start\":float(raw_run_data.get(\"start\", 0.0)),",
            "                \"osc_width\":float(raw_run_data.get(\"width\", 0.0)),",
            "                \"phi\":float(raw_run_data.get(\"start\", 0.0)),",
            "                \"run_number\":None,",
            "                \"site_tag\":self.tag,",
            "                \"start_image_number\":int(float(raw_run_data.get(\"first_image\", 0))),",
            "                \"time\":float(raw_run_data.get(\"time\", 0.0)),",
            "                \"transmission\":float(raw_run_data.get(\"trans\", 0.0)),",
            "                \"twotheta\":None",
            "            }\n",
            "        else:",
            "            run_data = False\n",
            "        return run_data\n",
            "    # Used for file-based image example",
            "    def check_for_image_collected(self):",
            "        \"\"\"",
            "        Returns True if image information file has new timestamp, False if not",
            "        \"\"\"\n",
            "        tries = 0",
            "        while tries < 5:",
            "            try:",
            "                statinfo = os.stat(self.image_data_file)",
            "                break",
            "            except:",
            "                if tries == 4:",
            "                    return False",
            "                time.sleep(0.01)",
            "                tries += 1\n",
            "        # The modification time has not changed",
            "        if self.image_time == statinfo.st_mtime:",
            "            return False",
            "        # The file has changed",
            "        else:",
            "            self.image_time = statinfo.st_mtime",
            "            return True\n",
        ]
        self.output_function(gatherer_class)
        

def get_commandline(args=None):
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """Generate a RAPD detector file scaffold"""

    my_parser = argparse.ArgumentParser(description=commandline_description)

    # Verbosity
    my_parser.add_argument("-v", "--verbose",
                        action="store_true",
                        dest="verbose",
                        help="Enable verbose feedback")

    # Test mode?
    my_parser.add_argument("-t", "--test",
                        action="store_true",
                        dest="test",
                        help="Run in test mode")

    # Test mode?
    my_parser.add_argument("-f", "--force",
                        action="store_true",
                        dest="force",
                        help="Allow overwriting of files")

    # Maintainer
    my_parser.add_argument("-m", "--maintainer",
                        action="store",
                        dest="maintainer",
                        default="Your name",
                        help="Maintainer's name")

    # Maintainer's email
    my_parser.add_argument("-e", "--email",
                        action="store",
                        dest="email",
                        default="Your email",
                        help="Maintainer's email")

    # File name to be generated
    my_parser.add_argument(action="store",
                        dest="file",
                        nargs="?",
                        default=False,
                        help="Name of file to be generated")

    # Pull from the input list
    if isinstance(args, list):
        return my_parser.parse_args(args)
    # Grab straight from the commandline
    else:
        return my_parser.parse_args()

def main():
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    commandline_args = get_commandline()

    print commandline_args

    file_generator = FileGenerator(commandline_args)
    file_generator.run()

if __name__ == "__main__":
    main()

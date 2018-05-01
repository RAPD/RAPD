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
                                       "json",
                                       "os",
                                       "re",
                                       "time"),
                           added_rapd_imports=("from database.redis_adapter import Database as RedisDB"
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
            "                                logfile_id=\"rapd_gatherer\", ",
            "                                level=log_level ",
            "                                ) ",
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

        # Import generic detectors
        gatherer_imports = [
            "# ADSC Q315",
            "# import detectors.adsc.adsc_q315 as detector",
            "# Dectris Pilatus 6M",
            "# import detectors.dectris.dectris_pilatus6m as detector"
            "# Rayonix MX300",
            "# import detectors.rayonix.rayonix_mx300 as detector",
            "# Rayonix MX300HS",
            "# import detectors.rayonix.rayonix_mx300hs as detector\n"
        ]
        self.output_function(gatherer_imports)

        # Information for detector setup
        gatherer_info = [
            "# Detector information",
            "# The RAPD detector type",
            "DETECTOR = \"rayonix_mx300\"",
            "# The detector vendor as it appears in the header",
            "VENDORTYPE = \"MARCCD\"",
            "# The detector serial number as it appears in the header",
            "DETECTOR_SN = 7",
            "# The detector suffix \"\" if there is no suffix",
            "DETECTOR_SUFFIX = \"\"",
            "# Template for image name generation ? for frame number places",
            "IMAGE_TEMPLATE = \"%s.????\"",
            "# Is there a run number in the template?",
            "RUN_NUMBER_IN_TEMPLATE = False",
            "# This is a version number for internal RAPD use",
            "# If the header changes, increment this number",
            "HEADER_VERSION = 1\n"
        ]
        self.output_function(gatherer_info)

        # # parse_file_name function
        # parse_file_name = [
        #     "def parse_file_name(fullname):",
        #     "    \"\"\"",
        #     "    Parse the fullname of an image and return",
        #     "    (directory, basename, prefix, run_number, image_number)",
        #     "    Keyword arguments",
        #     "    fullname -- the full path name of the image file",
        #     "    \"\"\"",
        #     "    # Directory of the file",
        #     "    directory = os.path.dirname(fullname)\n",
        #     "    # The basename of the file (i.e. basename - suffix)",
        #     "    basename = os.path.basename(fullname).rstrip(DETECTOR_SUFFIX)\n",
        #     "    # The prefix, image number, and run number",
        #     "    sbase = basename.split(\".\")",
        #     "    prefix = \".\".join(sbase[0:-1])",
        #     "    image_number = int(sbase[-1])",
        #     "    run_number = None",
        #     "    return directory, basename, prefix, run_number, image_number\n",
        # ]
        # self.output_function(parse_file_name)

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

            "    def stop(self):",
            "        \"\"\"",
            "        Stop the loop",
            "        \"\"\"",
            "        self.logger.debug(\"NecatGatherer.stop\")\n",
            "        self.go = False",
            "        self.redis_database.stop()",
            "        self.bl_database.stop()\n",
            "    def connect(self):",
            "        \"\"\"",
            "        Connect to redis host",
            "        \"\"\"\n",
            "        self.redis_database = RedisDB(settings=self.site.CONTROL_DATABASE_SETTINGS)",
            "        self.redis = self.redis_database.connect_to_redis()\n",
            "        # Connect to beamline Redis to monitor if run is launched",
            "        self.bl_database = redis_database.Database(settings=self.site.SITE_ADAPTER_SETTINGS[self.tag])",
            "        self.bl_redis = self.bl_database.connect_to_redis()",
                        
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

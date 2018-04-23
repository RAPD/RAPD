"""Simulate a data collection"""

"""
This file is part of RAPD

Copyright (C) 2018, Cornell University
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

__created__ = "2018-04-21"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
from argparse import RawTextHelpFormatter
# import from collections import OrderedDict
# import datetime
import glob
import hashlib
import importlib
import json
# import logging
# import multiprocessing
import os
from pprint import pprint
# import pymongo
# import re
# import redis
# import shutil
import subprocess
import sys
import time
import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
import test_sets
import database.redis_adapter as redis_adapter
import detectors.detector_utils as detector_utils
import utils.global_vars as rglobals
import utils.log
import utils.site as site
import utils.text as text
from bson.objectid import ObjectId

# Cache for test data
TEST_CACHE = rglobals.TEST_CACHE

# Software dependencies
VERSIONS = {
    # "eiger2cbf": ("160415",)
}

def print_welcome_message(printer):
    """Print a welcome message to the terminal"""

    message = """
RAPD Run Simulation
-------------------"""
    printer(message, 50, color="blue")

def main():
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    commandline_args = get_commandline()

    pprint(commandline_args)

    # Get the environmental variables
    environmental_vars = site.get_environmental_variables()

    # Output log file is always verbose
    log_level = 10

    # Set up logging
    # logger = utils.log.get_logger(logfile_dir="./",
    #                               logfile_id="rapd_test",
    #                               level=log_level,
    #                               console=commandline_args.test)

    # Set up terminal printer
    # Verbosity
    if commandline_args.verbose:
        terminal_log_level = 10
    else:
        terminal_log_level = 50

    tprint = utils.log.get_terminal_printer(verbosity=terminal_log_level,
                                            no_color=commandline_args.no_color)

    print_welcome_message(tprint)

    # Handle site - commandline only    
    if commandline_args.site:
        # Determine the site_file
        site_file = utils.site.determine_site(site_arg=commandline_args.site)

        # Error out if no site_file to import
        if site_file == False:
            print text.error+"Could not find a site file. Exiting.\n"+text.stop
            sys.exit(9)

        # Import the site settings
        # print "Importing %s" % site_file
        SITE = importlib.import_module(site_file)
    else:
        SITE = False

    # Do some checking on site & id
    if isinstance(SITE.ID, tuple):
        if len(SITE.ID) > 1:
            if commandline_args.id:
                if commandline_args.id in SITE.ID:
                    ID = commandline_args.id
                else:
                    print text.error+"Specified id not in site.ID. Exiting.\n"+text.stop
                    sys.exit(9)
            else:
                print text.error+"Site has multiple ids, need to define id using --id flag. Exiting.\n"+text.stop
                sys.exit(9)   
    else:
        if commandline_args.id:
            if commandline_args.id == SITE.ID:
                ID = commandline_args.id
            else:
                print text.error+"Specified id does not match site.ID. Exiting.\n"+text.stop
                sys.exit(9)
        else:
            ID = SITE.ID

    # Make sure directories are there
    if not os.path.exists(commandline_args.source):
        raise IOError("Source directory %s does not exist" % commandline_args.source)
    if not os.path.exists(commandline_args.target):
        raise IOError("Target directory %s does not exist" % commandline_args.target)

    # Set up redis connection
    if ID:
        redis_database = redis_adapter.Database(settings=SITE.CONTROL_DATABASE_SETTINGS)
        redis = redis_database.connect_to_redis()

    # Gather the images
    source_template = os.path.join(commandline_args.source, commandline_args.template)
    source_images = glob.glob(source_template)
    # pprint(source_images)

    # Gather the run info
    detector = detector_utils.get_detector_file(source_images[0])
    if isinstance(detector, dict):
        if detector.has_key("detector"):
            detector_target = detector.get("detector")
            detector_module = detector_utils.load_detector(detector_target)
    else:
        print text.error+"Don't understand this image. Exiting.\n"+text.stop
        sys.exit(9)

    first_image_header = detector_module.read_header(source_images[0])
    print "first"
    pprint(first_image_header)
    last_image_header = detector_module.read_header(source_images[-1])
    print "last"
    pprint(last_image_header)

    # Sleep for desired delay before "collection"
    time.sleep(commandline_args.delay)

    # Running as site?
    if ID:
        # Signal the run info
        run_data = {
                "anomalous":          None,
                "beamline":           first_image_header.get("beamline", None),              # Non-standard
                "beam_size_x":        float(first_image_header.get("beamsize", 0.0)),     # Non-standard
                "beam_size_y":        float(first_image_header.get("beamsize", 0.0)),     # Non-standard
                "directory":          first_image_header.get("directory", None),
                "distance":           float(first_image_header.get("distance", 0.0)),
                "energy":             float(first_image_header.get("energy", 0.0)),
                "image_prefix":       first_image_header.get("image_prefix", None),
                "kappa":              None,
                "number_images":      last_image_header['image_number'] - first_image_header['image_number'] + 1,
                "omega":              None,
                "osc_axis":           first_image_header.get("axis", "phi"),
                "osc_start":          float(first_image_header.get("osc_start", 0.0)),
                "osc_width":          float(first_image_header.get("osc_range", 0.0)),
                "phi":                float(first_image_header.get("osc_startstart", 0.0)),
                "run_number":         first_image_header.get("run_number", None),
                "site_tag":           ID,
                "start_image_number": first_image_header.get("image_number", 1),
                "testing_override":   True,
                "time":               float(first_image_header.get("time", 0.0)),
                "transmission":       float(first_image_header.get("transmission", 0.0)),
                "twotheta":           None
            }
        # Put into exchangable format
        run_data_json = json.dumps(run_data)
        if commandline_args.active:
            # Publish to Redis
            redis.publish("run_data:%s" % ID, run_data_json)
            # Push onto redis list in case no one is currently listening
            redis.lpush("runs_data:%s" % ID, run_data_json)

    # Start moving images
    for source_image in source_images:
        target_image = os.path.join(commandline_args.target, os.path.basename(source_image))
        print source_image, ">>>", target_image
        # Move image
        if commandline_args.active:
            shutil.copyfile(source_image, target_image)
            # Announce on redis
            if ID:
                # Publish to Redis
                redis.publish("image_collected:%s" % ID, target_image)
                # Push onto redis list in case no one is currently listening
                redis.lpush("images_collected:%s" % ID, target_image)
        
        # Sleep to simulate an image collection
        time.sleep(first_image_header.get("time", 0.0))
    
        # Sleep for desired interval
        time.sleep(commandline_args.interval)

    sys.exit()

def get_commandline():
    """
    Grabs the commandline
    """

    # Parse the commandline arguments
    commandline_description = "RAPD project testing"
    parser = argparse.ArgumentParser(description=commandline_description,
                                     formatter_class=RawTextHelpFormatter)

    # No color in terminal printing
    parser.add_argument("--color",
                        action="store_false",
                        dest="no_color",
                        help="Use colors in CLI")

    # Delay before frames are moved
    parser.add_argument("-d", "--delay",
                        action="store",
                        dest="delay",
                        type=float,
                        default=5.0,
                        help="Delay in seconds before first frame is copied")

    # ID for use with sites that have multiple ids
    parser.add_argument("--id",
                        action="store",
                        dest="id",
                        default=False,
                        help="Id for use with multi-id sites")

    # Interval beween frames copying
    parser.add_argument("-i", "--interval",
                        action="store",
                        dest="interval",
                        type=float,
                        default=0.0,
                        help="Interval in seconds between copying frames")

    # Force
    parser.add_argument("-f", "--force",
                        action="store_true",
                        dest="force",
                        help="Allow overwrite of test data")

    # Quiet output
    parser.add_argument("-q", "--quiet",
                        action="store_false",
                        dest="verbose",
                        help="Request less output")

    # Site information
    parser.add_argument("--site",
                        action="store",
                        dest="site",
                        default=False,
                        help="The site")
    
    # Source directory
    parser.add_argument("-s", "--source",
                        action="store",
                        dest="source",
                        default="./",
                        help="The source directory of images to use for simulation")

    # Target directory
    parser.add_argument("-t", "--target",
                        action="store",
                        dest="target",
                        default="./",
                        help="The target directory of images to use for simulation")

    # Template for images
    parser.add_argument("--template",
                        action="store",
                        dest="template",
                        default="*.cbf",
                        help="The template for images to use for simulation in glob-format")

    # Test mode
    parser.add_argument("--test",
                        action="store_false",
                        dest="active",
                        help="Run in test mode")

    args = parser.parse_args()

    if args.source == args.target:
        print "\n"+text.error+"!!ERROR!! Source and target directories cannot be the same"+text.stop+"\n"
        parser.print_help()
        sys.exit(-1)

    return args

if __name__ == "__main__":

    main()
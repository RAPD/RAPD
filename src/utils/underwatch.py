
# Standard imports
import argparse
import importlib
import json
import logging
import logging.handlers
import os
import pickle
import shutil
import socket
import sys
import time
import uuid

import redis

# RAPD imports
import utils.commandline
import utils.lock
import utils.log
import utils.site

from utils.overwatch import Registrar

def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """Data gatherer for SERCAT ID beamline"""
    parser = argparse.ArgumentParser(parents=[utils.commandline.base_parser],
                                     description=commandline_description)

    return parser.parse_args()


if __name__ == "__main__":

    # Get the commandline args
    commandline_args = get_commandline()
    print commandline_args

    # Determine the site
    site_file = utils.site.determine_site(site_arg=commandline_args.site)

    # Import the site settings
    SITE = importlib.import_module(site_file)

    RG = Registrar(site=SITE, ow_type="test", ow_id=commandline_args.overwatcher_id)
    RG.run()

"""This is a docstring for this container file"""

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

__created__ = "2017-09-21"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
# import argparse
from collections import OrderedDict
# import datetime
import glob
import hashlib
# import json
# import logging
# import multiprocessing
import os
from pprint import pprint
# import pymongo
# import re
# import redis
# import shutil
# import subprocess
# import sys
# import time
# import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils

def create_manifest(directory, write=True):
    """
    Creates a manifest for all files in a directory
    If write is True, will write files.sha in the dirctory
    """
    # Storage for results of hash
    records = OrderedDict()

    # Retrieve files in the directory and sort alphabetically
    globfiles = glob.glob(directory + "/*")
    globfiles.sort()

    # Run through files
    for globfile in globfiles:
        # It's a file
        if os.path.isfile(globfile):
            # Compute hash
            file_hash = hashlib.sha1(open(globfile, "r").read()).hexdigest()
            # Store hash
            records[globfile] = file_hash

    if write:
        with open("files.sha", "w") as output_file:
            for key, val in records.iteritems():
                output_file.write("%s  %s\n" % (val, key))

    # Return the dict
    return records

if __name__ == "__main__":
    create_manifest("./", True)

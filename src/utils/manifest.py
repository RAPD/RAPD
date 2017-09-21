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
# import from collections import OrderedDict
# import datetime
import glob
import hashlib
# import json
# import logging
# import multiprocessing
import os
# import pprint
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

    globfiles = glob.glob(directory+"/*")
    for globfile in globfiles:
        if os.path.isfile(globfile):
            file_hash = hashlib.sha1(open(globfile, "r").read()).hexdigest()
            print file_hash, globfile

if __name__ == "__main__":
    create_manifest("./", False)

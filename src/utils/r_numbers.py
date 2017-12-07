"""Handy utilities for number manipulation"""

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

__created__ = "2017-03-12"
_maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
# import argparse
# import from collections import OrderedDict
# import datetime
# import glob
# import json
# import logging
# import multiprocessing
# import os
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

# Software dependencies
VERSIONS = {
# "eiger2cbf": ("160415",)
}

def try_float(number, default="NO DEFAULT"):
    """Attempt to cast to a float, but return string if not"""
    try:
        return float(number)
    except ValueError:
        if default != "NO DEFAULT":
            return default
        else:
            return number

def try_int(number, default="NO DEFAULT"):
    """Attempt to cast to an int, but return string if not"""
    try:
        return int(number)
    except ValueError:
        if default != "NO DEFAULT":
            return default
        else:
            return number

def main():
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    print "main"

if __name__ == "__main__":

    # Execute code
    main()

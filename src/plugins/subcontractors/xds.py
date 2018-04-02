"""Methods for using XDS"""

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

__created__ = "2017-06-30"
__maintainer__ = "Frank Murphy"
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
# import urllib2
# import uuid

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
# import utils.credits as credits

# Software dependencies
VERSIONS = {
# "eiger2cbf": ("160415",)
}

def get_avg_mosaicity_from_integratelp():
    """
    Parse the INTEGRATE.LP file and extract information
    about the mosaicity.
    """

    lp = open('INTEGRATE.LP', 'r').readlines()

    for linenum, line in enumerate(lp):
        if 'SUGGESTED VALUES FOR INPUT PARAMETERS' in line:
            avg_mosaicity_line = lp[linenum + 2]
    avg_mosaicity = float(avg_mosaicity_line.strip().split(' ')[-1])

    return avg_mosaicity

def get_isa_from_correctlp():
    """
    Parses the CORRECT.LP file to extract information
    """

    lp = open('CORRECT.LP', 'r').readlines()
    for i, line in enumerate(lp):
        if 'ISa\n' in line:
            isa_line = lp[i + 1]
            break
    isa = float(isa_line.strip().split()[-1])

    return isa

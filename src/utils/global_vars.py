"""This is a docstring for this container file"""

"""
This file is part of RAPD

Copyright (C) 2017-2018, Cornell University
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

__created__ = "2017-04-24"
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

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils


# Caches for data
CIF_CACHE = "/tmp/rapd_cache/cif_files"
TEST_CACHE = "/tmp/rapd_cache/test_data"

# NE-CAT PDBQ Server
# tries in order
#PDBQ_SERVER = "https://rapd.nec.aps.anl.gov/pdbq"
PDBQ_SERVER = ["https://rapd2.nec.aps.anl.gov/pdbq",
               "https://wwwdev.ebi.ac.uk/pdbe/search/pdb",
               "http://www.rcsb.org/pdb/rest"]
               #"https://www.ebi.ac.uk/pdbe",

# Timeout for phaser MR process
PHASER_TIMEOUT = 2000
#PHASER_TIMEOUT = 10

# Time outs for Autointdex+strategies.
LABELIT_TIMEOUT = 120
XOALIGN_TIMEOUT = 30
DISTL_TIMEOUT = 30
STRATEGY_TIMEOUT = 60

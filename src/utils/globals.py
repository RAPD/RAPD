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


CIF_CACHE = "/tmp/rapd_cache/cif_files"
PDBQ_SERVER = "remote.nec.aps.anl.gov:3030"

# Timeout for phaser MR process
PHASER_TIMEOUT = 5000

# Software versions that work with RAPD
SOFTWARE_VERSIONS = {
    "AIMLESS": (
        "version 0.5",
        ),
    "FREERFLAG": (
        "version 2.2",
    ),
    "GNUPLOT": (
        "gnuplot 4.2",
        "gnuplot 5.0",
    ),
    "MTZ2VARIOUS": (
        "version 1.1",
    ),
    "POINTLESS": (
        "version 1.10",
        ),
    "TRUNCATE": (
        "version 7.0",
    ),
    "XDS": (
        "VERSION Nov 1, 2016",
    ),

}

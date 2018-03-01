"""PDB utilities"""

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

__created__ = "2017-04-27"
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

# IOTBX Imports
import iotbx.pdb
import iotbx.pdb.mmcif

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils


def cif_as_pdb(args):
    """
    Convert CIF files to PDB format

    Taken directly from IOTBX program cif_as_pdb.py
    """
    for file_name in args:
        try:
            assert os.path.exists(file_name)
            # print "Converting %s to PDB format." %file_name
            cif_input = iotbx.pdb.mmcif.cif_input(file_name=file_name)
            hierarchy = cif_input.construct_hierarchy()
            basename = os.path.splitext(os.path.basename(file_name))[0]
            iotbx.pdb.write_whole_pdb_file(
                file_name=basename+".pdb",
                output_file=None,
                processed_pdb_file=None,
                pdb_hierarchy=hierarchy,
                crystal_symmetry=cif_input.crystal_symmetry(),
                ss_annotation=cif_input.extract_secondary_structure(),
                append_end=True,
                atoms_reset_serial_first_value=None,
                link_records=None)
        except Exception, e:
            print "Error converting %s to PDB format:" % file_name
            print " ", str(e)
            continue

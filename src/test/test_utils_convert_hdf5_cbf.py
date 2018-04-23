"""This is a docstring for this file"""

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

__created__ = "2017-02-09"
_maintainer__ = "Your name"
__email__ = "Your email"
__status__ = "Development"

# Standard imports
import argparse
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
import subprocess
# import sys
# import time
import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
import utils.convert_hdf5_cbf as convert_hdf5_cbf

# class ExampleTestCase(unittest.TestCase):
#     """Example test fixture with setUp and tearDown"""
#
#     def setUp(self):
#         """Set up the test fixture"""
#
#         self.widget = Widget('The widget')
#
#     def tearDown(self):
#         """Tear down the test fixture"""
#
#         self.widget.dispose()
#         self.widget = None
#
#     def test_default_size(self):
#         self.assertEqual(self.widget.size(), (50,50),
#                          'incorrect default size')
#
#     def test_resize(self):
#         self.widget.resize(100,150)
#         self.assertEqual(self.widget.size(), (100,150),
#                          'wrong size after resize')

class TestDependencies(unittest.TestCase):
    """Example test fixture WITHOUT setUp and tearDown"""

    def test_executable(self):
        """Make sure the eiger2cbf executable is present"""

        p = subprocess.Popen(["eiger2cbf"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        assert stderr.startswith("EIGER HDF5 to CBF converter")
        assert stdout.startswith("Usage:")

    def test_version(self):
        """Make sure the eiger2cbf executable is an acceptable version"""

        p = subprocess.Popen(["eiger2cbf"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        found = False
        for version in convert_hdf5_cbf.VERSIONS["eiger2cbf"]:
            if version in stderr:
                found = True
                break

        assert found == True

def get_commandline():
    """
    Grabs the commandline
    """

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Parse image file header"
    parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    parser.add_argument("-c", "--commandline",
                        action="store_true",
                        dest="commandline",
                        help="Generate commandline argument parsing")

    # File name to be generated
    parser.add_argument(action="store",
                        dest="file",
                        nargs="?",
                        default=False,
                        help="Name of file to be generated")

    return parser.parse_args()

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    print "main"

    unittest.main(verbosity=2)

if __name__ == "__main__":

    commandline_args = get_commandline()

    main(args=commandline_args)

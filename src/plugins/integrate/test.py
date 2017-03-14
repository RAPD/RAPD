"""This is a docstring for this file"""

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

__created__ = "2017-03-06"
__maintainer__ = "Your name"
__email__ = "Your email"
__status__ = "Development"

# Standard imports
import argparse
# import datetime
from distutils.spawn import find_executable
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
import time
import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
import agents.rapd_agent_integrate as rapd_agent_integrate

class TestDependencies(unittest.TestCase):
    """Example test fixture WITHOUT setUp and tearDown"""

    def test_aimless(self):
        """Make sure the aimless executable is present"""

        test = find_executable("aimless")
        self.assertNotEqual(test, None)

    def test_aimless_version(self):
        """Make sure the aimless executable is an acceptable version"""

        subproc = subprocess.Popen(["aimless"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        time.sleep(2.0)
        subproc.terminate()
        stdout, _ = subproc.communicate()
        found = False
        for version in rapd_agent_integrate.VERSIONS["aimless"]:
            if version in stdout:
                found = True
                break

        assert found == True

    def test_freerflag(self):
        """Make sure the freerflag executable is present"""

        test = find_executable("freerflag")
        self.assertNotEqual(test, None)

    def test_freerflag_version(self):
        """Make sure the freerflag executable is an acceptable version"""

        subproc = subprocess.Popen(["freerflag"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        time.sleep(2.0)
        subproc.terminate()
        stdout, _ = subproc.communicate()
        found = False
        for version in rapd_agent_integrate.VERSIONS["freerflag"]:
            if version in stdout:
                found = True
                break

        assert found == True

    def test_gnuplot(self):
        """Make sure the gnuplot executable is present"""

        test = find_executable("gnuplot")
        self.assertNotEqual(test, None)

    def test_gnuplot_version(self):
        """Make sure the aimless executable is an acceptable version"""

        subproc = subprocess.Popen(["gnuplot", "--version"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        subproc.wait()
        stdout, _ = subproc.communicate()
        found = False
        for version in rapd_agent_integrate.VERSIONS["gnuplot"]:
            if version in stdout:
                found = True
                break

        assert found == True

    def test_mtz2various(self):
        """Make sure the mtz2various executable is present"""

        test = find_executable("mtz2various")
        self.assertNotEqual(test, None)

    def test_mtz2various_version(self):
        """Make sure the mtz2various executable is an acceptable version"""

        subproc = subprocess.Popen(["mtz2various"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        time.sleep(2.0)
        subproc.terminate()
        stdout, _ = subproc.communicate()
        found = False
        for version in rapd_agent_integrate.VERSIONS["mtz2various"]:
            if version in stdout:
                found = True
                break

        assert found == True

    def test_pointless(self):
        """Make sure the pointless executable is present"""

        test = find_executable("pointless")
        self.assertNotEqual(test, None)

    def test_pointless_version(self):
        """Make sure the pointless executable is an acceptable version"""

        subproc = subprocess.Popen(["pointless"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        time.sleep(2.0)
        subproc.terminate()
        stdout, _ = subproc.communicate()
        found = False
        for version in rapd_agent_integrate.VERSIONS["pointless"]:
            if version in stdout:
                found = True
                break

        assert found == True

    def test_truncate(self):
        """Make sure the truncate executable is present"""

        test = find_executable("truncate")
        self.assertNotEqual(test, None)

    def test_truncate_version(self):
        """Make sure the truncate executable is an acceptable version"""

        subproc = subprocess.Popen(["truncate"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        time.sleep(2.0)
        subproc.terminate()
        stdout, _ = subproc.communicate()
        found = False
        for version in rapd_agent_integrate.VERSIONS["truncate"]:
            if version in stdout:
                found = True
                break

        assert found == True

    def test_xds(self):
        """Make sure the xds executable is present"""

        test = find_executable("xds")
        self.assertNotEqual(test, None)

    def test_xds_version(self):
        """Make sure the xds executable is an acceptable version"""

        subproc = subprocess.Popen(["xds"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subproc.wait()
        stdout, _ = subproc.communicate()

        found = False
        for version in rapd_agent_integrate.VERSIONS["xds"]:
            if version in stdout:
                found = True
                break

        assert found == True

    def test_xds_par(self):
        """Make sure the xds_par executable is present"""

        test = find_executable("xds_par")
        self.assertNotEqual(test, None)

    def test_xds_par_version(self):
        """Make sure the xds executable is an acceptable version"""

        subproc = subprocess.Popen(["xds_par"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subproc.wait()
        stdout, _ = subproc.communicate()

        found = False
        for version in rapd_agent_integrate.VERSIONS["xds_par"]:
            if version in stdout:
                found = True
                break

        assert found == True





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
#
# class ExampleTestCaseLight(unittest.TestCase):
#     """Example test fixture WITHOUT setUp and tearDown"""
#
#     def test_default_size(self):
#         self.assertEqual(self.widget.size(), (50,50),
#                          'incorrect default size')
#
#     def test_resize(self):
#         self.widget.resize(100,150)
#         self.assertEqual(self.widget.size(), (100,150),
#                          'wrong size after resize')

def get_commandline():
    """
    Grabs the commandline
    """

    # Parse the commandline arguments
    commandline_description = "Test rapd_agent_integrate"
    parser = argparse.ArgumentParser(description=commandline_description)

    # Verbosity
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        dest="verbose",
                        help="Verbose output")
    #
    # # File name to be generated
    # parser.add_argument(action="store",
    #                     dest="file",
    #                     nargs="?",
    #                     default=False,
    #                     help="Name of file to be generated")

    # Print help message is no arguments
    # if len(sys.argv[1:])==0:
    #     parser.print_help()
    #     parser.exit()

    return parser.parse_args()

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    if args.verbose:
        verbosity = 2
    else:
        verbosity = 1

    unittest.main(verbosity=verbosity)

if __name__ == "__main__":

    COMMANDLINE_ARGS = get_commandline()

    main(args=COMMANDLINE_ARGS)

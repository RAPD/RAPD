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

__created__ = "2017-03-07"
_maintainer__ = "Your name"
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
# import time
import unittest
from distutils.spawn import find_executable

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
import plugin

class TestDependencies(unittest.TestCase):
    """Example test fixture WITHOUT setUp and tearDown"""

    def test_best(self):
        """Make sure the best executable is present"""

        test = find_executable("best")
        self.assertNotEqual(test, None)

    def test_best_version(self):
        """Make sure the best executable is an acceptable version"""

        subproc = subprocess.Popen(["best"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        subproc.wait()
        stdout, _ = subproc.communicate()
        found = False
        for version in plugin.VERSIONS["best"]:
            if version in stdout:
                found = True
                break

        assert found == True

    def test_gnuplot(self):
        """Make sure the gnuplot executable is present"""

        test = find_executable("gnuplot")
        self.assertNotEqual(test, None)

    def test_gnuplot_version(self):
        """Make sure the gnuplot executable is an acceptable version"""

        subproc = subprocess.Popen(["gnuplot", "--version"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        subproc.wait()
        stdout, _ = subproc.communicate()
        found = False
        for version in plugin.VERSIONS["gnuplot"]:
            if version in stdout:
                found = True
                break

        assert found == True

    def test_labelit(self):
        """
        Make sure the labelit executable is present

        It is not yet figured out how to test the version of labelit yet.
        """

        test = find_executable("labelit.index")
        self.assertNotEqual(test, None)

    def test_raddose(self):
        """
        Make sure the raddose executable is present

        It is not yet figured out how to test the version of raddose yet.
        """

        test = find_executable("raddose")
        self.assertNotEqual(test, None)

def get_dependencies_tests():
    """Return a suite with dependencies tests"""

    return unittest.TestLoader().loadTestsFromTestCase(TestDependencies)

def get_all_tests():
    """Return a suite with all tests"""

    return unittest.TestLoader().loadTestsFromTestCase(TestDependencies)

def compare_results(result1, result2, tprint):
    """Result comparison logic for unit testing"""

    """
    results
        distl_results
            good Bragg spots []
        Labelit results
            labelit_cell [[],[]]
            mosflm_sg []
        Best ANOM results
            strategy anom phi start [0]
            strategy anom rot range
        Best results
            strategy phi start
            strategy rot range
    """

    tprint("    DISTL", 10, "white")
    assert result1["results"]["distl_results"]["good Bragg spots"] == \
           result2["results"]["distl_results"]["good Bragg spots"]

    tprint("    Labelit", 10, "white")
    assert result1["results"]["Labelit results"]["labelit_cell"] == \
           result2["results"]["Labelit results"]["labelit_cell"]

    assert result1["results"]["Labelit results"]["mosflm_sg"] == \
           result2["results"]["Labelit results"]["mosflm_sg"]

    tprint("    Best standard strategy", 10, "white")
    assert result1["results"]["Best results"]["strategy phi start"] == \
           result2["results"]["Best results"]["strategy phi start"]

    assert result1["results"]["Best results"]["strategy rot range"] == \
           result2["results"]["Best results"]["strategy rot range"]

    tprint("    Best anomalous strategy", 10, "white")
    assert result1["results"]["Best ANOM results"]["strategy anom phi start"] == \
           result2["results"]["Best ANOM results"]["strategy anom phi start"]

    assert result1["results"]["Best ANOM results"]["strategy anom rot range"] == \
           result2["results"]["Best ANOM results"]["strategy anom rot range"]

    return True


def get_commandline():
    """
    Grabs the commandline
    """

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Parse image file header"
    parser = argparse.ArgumentParser(description=commandline_description)

    # Verbosity
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        dest="verbose",
                        help="Enable verbose output")

    # A True/False flag
    # parser.add_argument("-c", "--commandline",
    #                     action="store_true",
    #                     dest="commandline",
    #                     help="Generate commandline argument parsing")

    # File name to be generated
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

    print "main"

    if args.verbose:
        verbosity = 2
    else:
        verbosity = 1

    unittest.main(verbosity=verbosity)

if __name__ == "__main__":

    commandline_args = get_commandline()

    main(args=commandline_args)

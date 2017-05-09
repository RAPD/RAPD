"""Test code for HCMerge RAPD plugin"""

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

__created__ = "2017-05-09"
__maintainer__ = "Kay Perry"
__email__ = "kperry@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
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
import subprocess
import sys
import time
import unittest
# import urllib2
# import uuid
from distutils.spawn import find_executable

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
# import utils.credits as credits
import plugin

class TestDependencies(unittest.TestCase):
    """Example test fixture WITHOUT setUp and tearDown"""

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

def get_dependencies_tests():
    """Return a suite with dependencies tests"""

    return unittest.TestLoader().loadTestsFromTestCase(TestDependencies)

def get_all_tests():
    """Return a suite with all tests"""

    return unittest.TestLoader().loadTestsFromTestCase(TestDependencies)

def compare_results(result1, result2, tprint):
    """Result comparison logic for unit testing"""

    # A little example
    tprint("    DISTL", 10, "white")
    assert result1["results"]["distl_results"]["good Bragg spots"] == \
           result2["results"]["distl_results"]["good Bragg spots"]

    return True

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

        main()

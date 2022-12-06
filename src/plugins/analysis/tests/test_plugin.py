'''Test code for analysis RAPD plugin'''

'''
This file is part of RAPD

Copyright (C) 2017-2023, Cornell University
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
'''

__created__ = '2017-04-06'
__maintainer__ = 'Frank Murphy'
__email__ = 'fmurphy@anl.gov'
__status__ = 'Development'

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
from distutils.spawn import find_executable

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
import plugins.analysis.plugin as plugin

def test_dependencies() -> None:
    '''Test to see if required packages are present'''
    
    # GNUPLOT
    test_gnuplot = find_executable('gnuplot')
    assert test_gnuplot != None
    subproc = subprocess.Popen([test_gnuplot, '--version'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    subproc.wait()
    stdout, _ = subproc.communicate()
    found = False
    for version in plugin.VERSIONS['gnuplot']:
        if version in stdout:
            found = True
            break
    assert found == True

    # PHENIX
    test_phenix = find_executable('phenix.version')
    assert test_phenix != None
    subproc = subprocess.Popen([test_phenix],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    subproc.wait()
    stdout, _ = subproc.communicate()
    found = False
    for version in plugin.VERSIONS['phenix']:
        if version in stdout:
            found = True
            break
    assert found == True



if __name__ == '__main__':
    test_dependencies()
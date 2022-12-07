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
import multiprocessing
import os
from pprint import pprint
# import pymongo
# import re
# import redis
import shutil
import subprocess
import sys
import time
import unittest
from distutils.spawn import find_executable

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
import utils
import plugins.analysis.commandline as commandline

def test_construct_command() -> None:
    '''Test to see if plugin performs its action'''

    class commandline_args():
        clean = False
        data_file = '../../../../test_data/test_free.mtz'
        db_settings = False
        dir_up = False
        exchange_dir = False
        json = True
        logging = False
        no_color = True
        show_plots = False
        nproc = max(1, multiprocessing.cpu_count() - 1)
        pdbquery = False
        progress = False
        quite = False
        run_mode = 'interactive'
        sample_type = 'protein'
        test = False

    # Construct the command
    command = commandline.construct_command(commandline_args=commandline_args)
    pprint(command)
    '''
    {'command': 'ANALYSIS',
    'directories': {'work': '/Users/fmurphy/workspace/rapd/src/plugins/analysis/tests/rapd_analysis_test_free'},
    'input_data': {'data_file': '/Users/fmurphy/workspace/rapd/test_data/test_free.mtz',
                    'db_settings': False},
    'preferences': {'clean': False,
                    'json': True,
                    'nproc': 11,
                    'progress': False,
                    'run_mode': 'interactive',
                    'sample_type': 'protein',
                    'show_plots': False,
                    'test': False},
    'process_id': '00bcd6e4767711ed9f39f218983605f6'}
    '''
    assert command['command'] == 'ANALYSIS'
    assert 'directories' in command
    assert 'input_data' in command
    assert 'preferences' in command
    assert 'process_id' in command

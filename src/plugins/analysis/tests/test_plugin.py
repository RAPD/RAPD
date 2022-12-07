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

def test_action() -> None:
    '''Test to see if plugin performs its action'''

    # Make sure there is no interfering directory present
    shutil.rmtree('./rapd_analysis_thaum1_01s-01d_1_free')

    # Get the commandline args
    # commandline_args = commandline.get_commandline()
    class commandline_args():
        clean = False
        data_file = '../../../../test_data/thaum1_01s-01d_1_free.mtz'
        db_settings = False
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

    # Set up terminal printing
    tprint = utils.log.get_terminal_printer(verbosity=1,
                                            no_color=True,
                                            progress=False)

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()

    # Should working directory go up or down?
    if environmental_vars.get("RAPD_DIR_INCREMENT") in ("up", "UP"):
        commandline_args.dir_up = True
    else:
        commandline_args.dir_up = False

    # Construct the command
    command = commandline.construct_command(commandline_args=commandline_args)
    # print(command)

    plugin = utils.modules.load_module(seek_module="plugin",
                                       directories=["plugins.analysis"],
                                       logger=False)
    plugin_instance = plugin.RapdPlugin(command=command, processed_results=False, tprint=tprint, logger=False)
    plugin_instance.start()
    plugin_instance.join()

    assert os.path.exists('./rapd_analysis_thaum1_01s-01d_1_free')
    assert os.path.exists('./rapd_analysis_thaum1_01s-01d_1_free/xtriage.log')
    assert os.path.exists('./rapd_analysis_thaum1_01s-01d_1_free/molrep_rf_90.jpg')
    assert os.path.exists('./rapd_analysis_thaum1_01s-01d_1_free/result.json')

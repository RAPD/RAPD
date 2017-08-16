"""Information used by index plugin"""

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

__created__ = "2017-04-05"
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

# Information for BEST detector-inf.dat that may be missing
BEST_INFO = {
    "mx300hs": "mx300hs     mar300  300.00 0.0781250 3840 3840 0.001   0 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
    "pilatus6m": "pilatus6m    6m      434.64 0.172000  2463 2527  0.004 0 0.50 0.0  0.0 0.030  pck DC DA 0  0",
    "eiger9m": "eiger9m     9m      245.20 0.075000  3110 3269  0.000003 0 0.50 0.0 0.0 0.030 pck DC DA 0  0",
}

DEFAULT_PREFERENCES = {
    # JSON output?
    #command["preferences"]["json"] = commandline_args.json
    #command["preferences"]["progress"] = commandline_args.progress

    # Show plots (for ui or just command line??)
    "show_plots" : False,

    # Strategy type (*best, mosflm)
    "strategy_type" : 'best',

    # Best
    # best_complexity (*none, min, full)
    "best_complexity" : 'none', 
    "shape": 2.0,
    "susceptibility": 1.0,
    "aimed_res": 0.0,

    # Best & Labelit
    # sample_type (*Protein, DNA, RNA, Ribosome, Peptide)
    "sample_type": 'Protein',
    "spacegroup": False,
    "unitcell": False, #[100.0, 100.0 ,100.0, 90.0, 90.0, 90.0 ]

    # Labelit
    "index_hi_res": 0.0,
    # for overriding beam center
    #"x_beam": commandline_args.beamcenter[0],
    #"y_beam": commandline_args.beamcenter[1],
    "beam_search": 0.2,

    # Mosflm
    "mosflm_rot": 0.0,
    "mosflm_seg": 1,
    "mosflm_start": 0.0,
    "mosflm_end": 360.0,
    "reference_data": None,
    "reference_data_id": None,
    
    # Raddose
    # crystal dimensions in microns
    "crystal_size_x": 100.0,
    "crystal_size_y": 100.0,
    "crystal_size_z": 100.0,
    "solvent_content": 0.55,

    # Unknown
    "beam_flip": False,
    "multiprocessing": True,
    # Change these if user wants to continue dataset with other crystal(s).
    # "reference_data_id": None, #MOSFLM
    # #"reference_data_id": 1,#MOSFLM
    # #"reference_data": [['/gpfs6/users/necat/Jon/RAPD_test/index09.mat', 0.0, 30.0, 'junk_1_1-30',
    #                      'P41212']],#MOSFLM
    # 'reference_data': [['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',
    #                     0.0,
    #                     20.0,
    #                     'junk',
    #                     'P3'],
    #                    ['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',
    #                     40.0,
    #                     50.0,
    #                     'junk2',
    #                     'P3']
    #                   ],#MOSFLM

   
    }

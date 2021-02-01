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

# # Information for BEST detector-inf.dat that may be missing
# BEST_INFO = {
#     "q4": "q4          q4      188.00 0.0816000 2304 2304   2.5   0 1.30 0.0 20.0 0.030  512 DC DA 0  0",
#     "q4-2x":       "q4-2x       q4-2x   188.00 0.1632000 1152 1152   2.5   0 1.30 0.0 20.0 0.030  512 DC DA 0  0",
#     "q210":        "q210        q210    210.00 0.0512000 4096 4096   2.5   0 1.30 0.0 20.0 0.030  512 DC DA 0  0",
#     "q210-2x":     "q210-2x     q210-2x 210.00 0.1024000 2048 2048   2.5   0 1.30 0.0 20.0 0.030  512 DC DA 0  0",
#     "q315":        "q315        q315    315.00 0.0512000 6144 6144   2.5   0 1.30 0.0 36.0 0.030  512 DC DA 0  0",
#     "q315-2x":     "q315-2x     q315-2x 315.00 0.1024000 3072 3072   2.5   0 1.30 0.0 10.0 0.030  512 DC DA 0  0",
#     "mar165":      "mar165      mar165  161.95 0.0794140 2048 2048   7.0   0 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
#     "mar225":      "mar225      mar225  225.00 0.0730000 3072 3072   2.6   0 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
#     "rax225":      "rax225      rax225  225.00 0.0730000 3072 3072 120.0  60 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
#     "pck225":      "pck225      mar225  225.00 0.0730000 3072 3072   2.6   0 1.40 0.0 10.0 0.035  pck DC DA 0  0",
#     "mar325":      "mar325      mar325  325.02 0.0793500 4096 4096   2.6   0 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
#     "mar2300":     "mar2300     mpck150 345.00 0.1500000 2300 2300  80.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
#     "image2300":   "image2300   mimg150 345.00 0.1500000 2300 2300  80.0   0 1.30 0.0 10.0 0.045 4600 AD AB 1  1",
#     "mar2000":     "mar2000     mpck150 300.00 0.1500000 2000 2000  66.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
#     "image2000":   "image2000   mimg150 300.00 0.1500000 2000 2000  66.0   0 1.30 0.0 10.0 0.045 4000 AD AB 1  1",
#     "mar1600":     "mar1600     mpck150 240.00 0.1500000 1600 1600  48.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
#     "image1600":   "image1600   mimg150 240.00 0.1500000 1600 1600  48.0   0 1.30 0.0 10.0 0.045 3200 AD AB 1  1",
#     "mar1200":     "mar1200     mpck150 180.00 0.1500000 1200 1200  34.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
#     "image1200":   "image1200   mimg150 180.00 0.1500000 1200 1200  34.0   0 1.30 0.0 10.0 0.045 2400 AD AB 1  1",
#     "mar3450":     "mar3450     mpck100 345.00 0.1000000 3450 3450 108.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
#     "image3450":   "image3450   mimg100 345.00 0.1000000 3450 3450 108.0   0 1.30 0.0 10.0 0.045 6900 AD AB 1  1",
#     "mar3000":     "mar3000     mpck100 300.00 0.1000000 3000 3000  87.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
#     "image3000":   "image3000   mimg100 300.00 0.1000000 3000 3000  87.0   0 1.30 0.0 10.0 0.045 6000 AD AB 1  1",
#     "mar2400":     "mar2400     mpck100 240.00 0.1000000 2400 2400  62.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
#     "image2400":   "image2400   mimg100 240.00 0.1000000 2400 2400  62.0   0 1.30 0.0 10.0 0.045 4800 AD AB 1  1",
#     "mar1800":     "mar1800     mpck100 180.00 0.1000000 1800 1800  42.0   0 1.30 0.0 10.0 0.045 pck  DC DA 0  1",
#     "mx300":       "mx300       mar300  300.00 0.0730000 8192 8192   2.6   0 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
#     "mx300hs":     "mx300hs     mar300  300.00 0.0781250 3840 3840 0.001   0 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
#     "image1800":   "image1800   mimg100 180.00 0.1000000 1800 1800  42.0   0 1.30 0.0 10.0 0.045 3600 AD AB 1  1",
#     "raxis":       "raxis       raxis   300.00 0.1000000 3000 2990 180.0  60 1.30 0.0 17.0 0.045 6000 DC DA 1  0",
#     "ESRF_ID14-1": "ESRF_ID14-1 q210    209.72 0.102400  2048 2048  2.6   0 1.50 0.0 20.0 0.035  512 DC DA 0  0",
#     "ESRF_ID14-2": "ESRF_ID14-2 q4      188.01 0.081600  2304 2304  2.6   0 1.50 0.0 20.0 0.035  512 DC DA 0  0",
#     "ESRF_ID14-3": "ESRF_ID14-3 q4r     188.01 0.081600  2304 2304  2.6   0 1.50 0.0 20.0 0.035  512 DC DA 0  0",
#     "ESRF_ID14-4": "ESRF_ID14-4 q315    315.15 0.102588  3072 3072  2.5   0 1.50 0.0 39.0 0.050  512 DC DA 0  0",
#     "ESRF_BM14":   "ESRF_BM14   mar225  224.84 0.073190  3072 3072  4.2   0 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
#     "ESRF_ID23-1": "ESRF_ID23-1 q315    315.15 0.102588  3072 3072  2.5   0 1.50 0.0 40.0 0.050  512 DC DA 0  0",
#     "ESRF_ID23-2": "ESRF_ID23-2 mar225  225.04 0.073254  3072 3072  3.0   0 1.40 0.0 10.0 0.035 4096 DC DA 0  0",
#     "ESRF_ID29":   "ESRF_ID29   q315    315.00 0.102588  3072 3072  2.5   0 1.50 0.0 40.0 0.050  512 DC DA 0  0",
#     "pilatus6m":   "pilatus6m   6m      434.64 0.172000  2463 2527  0.004 0 0.50 0.0  0.0 0.030  pck DC DA 0  0",
#     "pilatus2m":   "pilatus2m   2m      254.00 0.172000  1475 1679  0.004 0 0.50 0.0  0.0 0.020  pck DC DA 0  0",
#     "eiger9m":     "eiger9m     9m      245.20 0.075000  3110 3269  0.000003 0 0.50 0.0 0.0 0.030 pck DC DA 0  0",
#     "eiger16m":    "eiger16m    16m     327.80 0.075000  4150 4371  0.000003 0 0.50 0.0  0.0 0.030  pck DC DA 0  0",
# }

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
    # OLD
    "multiprocessing": True,
    # 8 will be full speed. If set to 1, then everything is run sequentially
    "nproc" : 8,
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


DETECTOR_TO_BEST = {
    "ADSC": "q315",
    "ADSC-Q315": "q315",
    "ADSC-HF4M": "hf4m",
    "mar_165": "mar165",
    "mar300": "mar300",
    "Pilatus-6M": "pilatus6m",
    "PILATUS": "pilatus6m",
    "raxis":"raxis",
    "rayonix_mx225": "mar225",
    "rayonix_mx300": "mx300",
    "rayonix_mx300hs": "mx300hs",
    "ray300": "ray300",
    "Dectris Eiger 9M": "eiger9m",
    "Eiger-9M": "eiger9m",
    "Eiger-16M": "eiger16m",
    "Eiger2-16M": "eiger2-16m",
    }
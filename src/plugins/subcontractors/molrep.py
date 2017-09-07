"""Methiods for running BEST"""

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

__created__ = "2017-08-25"
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
import math
# import multiprocessing
# import os
from pprint import pprint
# import pymongo
# import re
# import redis
# import shutil
# import subprocess
import sys
# import time
# import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
from utils.r_numbers import try_int, try_float

def parse_raw_output(raw_output):
    """
    Parse Molrep self rotation function output
    """

    if isinstance(raw_output, str):
        raw_output = raw_output.split("\n")

    output_lines = []
    pat = {}
    pseudotranslation_detected = False
    for line in raw_output:
        output_lines.append(line)
        if line.startswith("INFO: pseudo-translation was detected"):
            ind1 = output_lines.index(line)
            pseudotranslation_detected = True
        if line.startswith("INFO:  use keyword: \"PST\""):
            ind2 = output_lines.index(line)

    # Pseudotranslation detected, so handle
    if pseudotranslation_detected:
        for line in output_lines[ind1:ind2]:
            split = line.split()
            if split[0] == "Origin":
                origin = {
                    "peak": split[-2],
                    "psig": split[-1]
                }
                pat["origin"] = origin
            if split[0].isdigit():
                junk1 = {
                    "peak": split[-2],
                    "psig": split[-1]
                }
                pat[split[0]] = junk1
            if split[0] == "Peak":
                ind3 = output_lines.index(line)
                pat[split[1][:-1]].update({"frac x": output_lines[ind3+1].split()[-3]})
                pat[split[1][:-1]].update({"frac y": output_lines[ind3+1].split()[-2]})
                pat[split[1][:-1]].update({"frac z": output_lines[ind3+1].split()[-1]})

    # Organize the return data
    results = {
        "pseudotranslation_detected": pseudotranslation_detected,
        "pseudotranslation_peak": pat,
    }

    return results

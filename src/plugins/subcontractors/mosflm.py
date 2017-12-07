"""Methoids wrapping labelit"""

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

__created__ = "2017-05-11"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
# import from collections import OrderedDict
# import datetime
# import glob
# import json
# import logging
# import multiprocessing
import os
from pprint import pprint
# import pymongo
# import re
# import redis
# import shutil
# import subprocess
import sys
# import time
# import unittest
# import urllib2
# import uuid

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
# import utils.credits as credits
from utils.r_numbers import try_float, try_int

# Software dependencies
VERSIONS = {
    # "eiger2cbf": ("160415",)
}

def parse_strategy(inp, anom=False):
    """
    Parsing Mosflm strategy.
    """

    # Handle list or string
    if isinstance(inp, str):
        if len(inp) < 50:
            return False
        in_lines = inp.split("\n")
    elif isinstance(inp, list):
        in_lines = inp
    else:
        return False

    output = {}
    log = []
    strategy = {"sweeps":[],
                "stats":{}}

    in_strat = False
    # Flag for using multiple segments in the mosflm strategy
    segments = False

    run_number = 0
    for line_number, line in enumerate(in_lines):

        # Append to log
        log.append(line)

        if line.startswith(" Checking completeness of data"):
            in_strat = True
            index_start_line = line_number

        if line.startswith(" This may take some time......"):
            in_strat = True
            segments = True

            index_start_line = line_number

        if in_strat:
            # print line_number, line

            # mosflm_segments has been invoked
            if segments:
                # Parse strategy
                if line.startswith(" From phi="):
                    # print ">>>", line
                    run_number += 1
                    sline = line.split()
                    start = float(sline[2])
                    end = float(sline[4])
                    # print "    run_number: %d start: %f  end: %f" % (run_number, start, end)
                    strategy["sweeps"].append({
                        "run_number": run_number,
                        "phi_start": start,
                        "phi_end": end,
                        "phi_range": end - start
                    })
                    anom_completeness = None
                    completeness = None
            # Non-segments
            else:
                # Run number
                if line.startswith(" Run number "):
                    run_number = int(line.split()[2])
                    # print "    run number: %d" % run_number
                    if run_number > 1:
                        strategy["sweeps"].append({
                            "run_number": run_number-1,
                            "phi_start": start,
                            "phi_end": end,
                            "phi_range": end - start
                        })

                    anom_completeness = None
                    completeness = None

                # Parse strategy
                if line.startswith(" From phi="):
                    sline = line.split()
                    start = float(sline[2])
                    end = float(sline[4])
                    # print "    start: %f  end: %f" % (start, end)

            if line.startswith(" These segments contain"):
                # Normal completeness
                if "% of the unique data" in line:
                    sline = line.split()
                    completeness = float(line.split()[3][:-1])
                    # print "    completeness: %f" % completeness
                # Anomalous completeness
                elif "% of the possible anomalous pairs" in line:
                    sline = line.split()
                    anom_completeness = float(line.split()[3][:-1])
                    # print "    anom_completeness: %f" % anom_completeness
                # Predicted reflections
                elif "predicted reflections and" in line:
                    sline = line.split()
                    reflections_total = int(sline[3])
                    reflections_unique = int(sline[7])
                    # print "    relfections total: %d unique: %d" % (reflections_total, reflections_unique)

            elif line.startswith(" Mean Multiplicity"):
                sline = line.split()
                multiplicity = float(line.split()[3])
                # print "    multiplicity: %f" % multiplicity

            elif line.startswith(" This is "):
                # print ">>>", line
                if "percent of the unique data for this spacegroup" in line:
                    percent_unique_data = float(line.split()[2])
                    # print "    percent_unique_data: %f" % percent_unique_data

            # if line_number > (index_start_line + 50):
            #     print "out"
            #     in_strat = False

    if not segments:
        strategy["sweeps"].append({
            "run_number": run_number,
            "phi_start": start,
            "phi_end": end,
            "phi_range": end - start
        })
    strategy["stats"] = {
        "completeness_norm": completeness if completeness else percent_unique_data,
        "completeness_anom": anom_completeness,
        "percent_unique_data": percent_unique_data,
        "multiplicity": multiplicity,
        "reflections_total": reflections_total,
        "reflections_unique": reflections_unique
    }
    # pprint(strategy)

    return {
        "log": log,
        "status": True,
        "strategy": strategy,
    }

def ParseOutputMosflm_strat(self, inp, anom=False):
    """
    Parsing Mosflm strategy.
    """
    if self.verbose:
        self.logger.debug('Parse::ParseOutputMosflm_strat')

    # try:
    temp = []
    strat = []
    res = []
    start = []
    end = []
    ni = []
    rn = []
    seg = False

    # osc_range  = str(self.header.get('osc_range'))
    if self.vendortype in ('Pilatus-6M', 'ADSC-HF4M'):
        osc_range = '0.2'
    else:
        if float(self.header.get('osc_range')) < 0.5:
            osc_range = '0.5'
        else:
            osc_range  = str(self.header.get('osc_range'))
    distance   = self.header.get('distance')
    mosflm_seg = self.preferences.get("mosflm_seg", 1)

    index = False
    index_res = False
    for x, line in enumerate(inp):
        # print mosflm_seg, seg, x, line.rstrip()
        temp.append(line)
        if mosflm_seg != 1:
            if line.startswith(' This may take some time......'):
                index = x
                seg = True
            if line.startswith(' Testing to find the best combination'):
                index = x
                seg = True
        else:
            if line.startswith(' Checking completeness of data'):
                index = x
        if line.startswith(' Breakdown as a Function of Resolution'):
            index_res = temp.index(line)
        if line.startswith(' Mean multiplicity'):
            index_mult = temp.index(line)
            mult2 = ((temp[index_mult]).split()[-1])
        if line.count('** ERROR ** The matrix Umat is not a simple rotation matrix'):
            if self.multicrystalstrat:
                return "sym"
    if seg:
        strat.append(temp[index:index + 10 + 2*int(mosflm_seg)])
    elif index:
        strat.append(temp[index:index + 12])
    counter = 0
    for line in strat:
        # print "strat", line
        comp = line[3].split()[3]
        while counter < int(mosflm_seg):
            s1 = float(line[5 + counter].split()[1])
            e1 = float(line[5 + counter].split()[3])
            images1 = int((e1 - s1) / float(osc_range))
            ni.append(images1)
            if s1 < 0:
                s1 += 360
            if s1 > 360:
                s1 -= 360
            start.append(s1)
            if e1 < 0:
                e1 += 360
            if e1 > 360:
                e1 -= 360
            end.append(e1)
            counter += 1
            rn.append(counter)
    if index_res:
        res.append(temp[index_res:index_res + 17])
    for line in res:
        resolution = line[15].split()[0]
    if anom:
        j1 = ' anom '
    else:
        j1 = ' '
    data = {'strategy'+j1+'run number': rn,
            'strategy'+j1+'phi start': start,
            'strategy'+j1+'phi end': end,
            'strategy'+j1+'num of images': ni,
            'strategy'+j1+'resolution': resolution,
            'strategy'+j1+'completeness': comp,
            'strategy'+j1+'redundancy': mult2,
            'strategy'+j1+'distance': distance,
            'strategy'+j1+'image exp time': self.time,
            'strategy'+j1+'delta phi': osc_range}
    return data

    # except:
    #     self.logger.exception('**Error in Parse.ParseOutputMosflm_strat**')
    #     return(None)

if __name__ == "__main__":
    print "mosflm"
    input_file = sys.argv[1]
    print "Reading %s" % input_file
    input_lines = open(input_file, "r").read()
    parse_strategy(input_lines)

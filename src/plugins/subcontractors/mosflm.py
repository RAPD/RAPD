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
#import argparse
#import os
from pprint import pprint
import sys
#from utils.r_numbers import try_float, try_int

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
    anom_completeness = None
    completeness = None

    run_number = 0
    for line_number, line in enumerate(in_lines):

        # Append to log
        log.append(line)
        
        if line.count('From ') and line.count('degrees') and not line.count('phi='):
            # print ">>>", line
            run_number += 1
            sline = line.split()
            start = float(sline[1])
            end = float(sline[3])
            # print "    run_number: %d start: %f  end: %f" % (run_number, start, end)
            strategy["sweeps"].append({
                "run_number": run_number,
                "phi_start": start,
                "phi_end": end,
                "phi_range": end - start
            })
        if line.count('percent of the unique data for this spacegroup'):
            completeness = line.split()[2]
        if line.count('Completeness of anomalous pairs is'):
            anom_completeness = line.split()[5][:-1]
        if line.count("predicted reflections and"):
            sline = line.split()
            reflections_total = int(sline[3])
            reflections_unique = int(sline[7])
        if line.count("Mean multiplicity"):
            multiplicity = line.split()[-1]

    strategy["stats"] = {
        "completeness_norm": completeness,
        "completeness_anom": anom_completeness,
        "percent_unique_data": completeness,
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

if __name__ == "__main__":
    print "mosflm"
    input_file = sys.argv[1]
    print "Reading %s" % input_file
    input_lines = open(input_file, "r").read()
    parse_strategy(input_lines)

"""Methods for running Phaser in RAPD"""

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

__created__ = "2017-05-24"
__maintainer__ = "Frnak Murphy"
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
import os
from pprint import pprint
# import pymongo
# import re
# import redis
# import shutil
import signal
import subprocess
# import sys
# import time
# import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils


def run_phaser_pdbquery(command):
    """
    Run phaser for pdbquery
    """
    # Change to correct directory
    os.chdir(command["work_dir"])

    # Setup params
    run_before = command.get("run_before", False)
    copy = command.get("copy", 1)
    resolution = command.get("res", False)
    datafile = command.get("data")
    input_pdb = command.get("pdb")
    spacegroup = command.get("spacegroup")
    cell_analysis = command.get("cell analysis", False)
    name = command.get("name", spacegroup)
    large_cell = command.get("large", False)
    timeout = command.get("timeout", False)

    # Construct the phaser command file
    command = "phaser << eof\nMODE MR_AUTO\n"
    command += "HKLIn %s\nLABIn F=F SIGF=SIGF\n" % datafile

    # CIF or PDB?
    structure_format = "PDB"
    if input_pdb[-3:].lower() == "cif":
        structure_format = "CIF"
    command += "ENSEmble junk %s %s IDENtity 70\n" % (structure_format, input_pdb)
    command += "SEARch ENSEmble junk NUM %s\n" % copy
    command += "SPACEGROUP %s\n" % spacegroup
    if cell_analysis:
        command += "SGALTERNATIVE SELECT ALL\n"
        # Set it for worst case in orth
        # number of processes to run in parallel where possible
        command += "JOBS 1\n"
    else:
        command += "SGALTERNATIVE SELECT NONE\n"
    if run_before:
        # Picks own resolution
        # Round 2, pick best solution as long as less that 10% clashes
        command += "PACK SELECT PERCENT\n"
        command += "PACK CUTOFF 10\n"
    else:
        # For first round and cell analysis
        # Only set the resolution limit in the first round or cell analysis.
        if resolution:
            command += "RESOLUTION %s\n" % resolution
        else:
            # Otherwise it runs a second MR at full resolution!!
            # I dont think a second round is run anymore.
            # command += "RESOLUTION SEARCH HIGH OFF\n"
            if large_cell:
                command += "RESOLUTION 6\n"
            else:
                command += "RESOLUTION 4.5\n"
        command += "SEARCH DEEP OFF\n"
        # Don"t seem to work since it picks the high res limit now.
        # Get an error when it prunes all the solutions away and TF has no input.
        # command += "PEAKS ROT SELECT SIGMA CUTOFF 4.0\n"
        # command += "PEAKS TRA SELECT SIGMA CUTOFF 6.0\n"

    # Turn off pruning in 2.6.0
    command += "SEARCH PRUNE OFF\n"

    # Choose more top peaks to help with getting it correct.
    command += "PURGE ROT ENABLE ON\nPURGE ROT NUMBER 3\n"
    command += "PURGE TRA ENABLE ON\nPURGE TRA NUMBER 1\n"

    # Only keep the top after refinement.
    command += "PURGE RNP ENABLE ON\nPURGE RNP NUMBER 1\n"
    command += "ROOT %s\neof\n" % name

    # Write the phaser command file
    phaser_com_file = open("phaser.com", "w")
    phaser_com_file.writelines(command)
    phaser_com_file.close()

    # Run the phaser process
    phaser_proc = subprocess.Popen(["sh phaser.com"],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     shell=True,
                                     preexec_fn=os.setsid)
    try:
        stdout, _ = phaser_proc.communicate(timeout=timeout)

        # Write the log file
        with open("phaser.log", "w") as log_file:
            log_file.write(stdout)

        # Return results
        return {"pdb_code": input_pdb.replace(".pdb", "").upper(),
                "log": stdout,
                "status": "COMPLETE"}

    # Run taking too long
    except subprocess.TimeoutExpired:
        print "  Timeout of %ds exceeded - killing %d" % (timeout, phaser_proc.pid)
        os.killpg(os.getpgid(phaser_proc.pid), signal.SIGTERM)
        return {"pdb_code": input_pdb.replace(".pdb", "").upper(),
                "log": "Timed out after %d seconds" % timeout,
                "status": "ERROR"}

def parse_phaser_output(phaser_log):
    """Parse Phaser log file"""

    # The phased process has timed out
    if phaser_log[0].startswith("Timed out after"):
        phaser_result = {"solution": False,
                         "message": "Timed out"}

    # Looks like process completed
    else:
        pdb = False
        solution_start = False
        clash = "NC"
        end = False
        temp = []
        tncs = False
        nmol = 0
        for index, line in enumerate(phaser_log):
            temp.append(line)
            directory = os.getcwd()
            if line.count("SPACEGROUP"):
                spacegroup = line.split()[-1]
            if line.count("Solution") or line.count("Partial Solution "):
                if line.count("written"):
                    if line.count("PDB"):
                        pdb = line.split()[-1]
                    if line.count("MTZ"):
                        mtz = line.split()[-1]
                if line.count("RFZ="):
                    solution_start = index
            if line.count("SOLU SET"):
                solution_start = index
            if line.count("SOLU ENSEMBLE"):
                end = index
        if solution_start:
            for line in phaser_log[solution_start:end]:
                if line.count("SOLU 6DIM"):
                    nmol += 1
                for param in line.split():
                    if param.startswith("RFZ"):
                        if param.count("=") == 1:
                            rfz = param[param.find("=")+param.count("="):]
                    if param.startswith("RF*0"):
                        rfz = "NC"
                    if param.startswith("TFZ"):
                        if param.count("=") == 1:
                            tfz = param[param.find("=")+param.count("="):]
                    if param.startswith("TF*0"):
                        tfz = "NC"
                    if param.startswith("PAK"):
                        clash = param[param.find("=")+param.count("="):]
                    if param.startswith("LLG"):
                        llgain = float(param[param.find("=")+param.count("="):])
                    if param.startswith("+TNCS"):
                        tncs = True
        if not pdb:
            phaser_result = {"solution": False,
                             "message": "No solution"}
        else:
            phaser_result = {"solution": True,
                             "pdb": pdb,
                             "mtz": mtz,
                             "gain": llgain,
                             "rfz": rfz,
                             "tfz": tfz,
                             "clash": clash,
                             "dir": directory,
                             "spacegroup": spacegroup,
                             "tNCS": tncs,
                             "nmol": nmol,
                             "adf": None,
                             "peak": None,
                            }

    pprint(phaser_result)
    return phaser_result

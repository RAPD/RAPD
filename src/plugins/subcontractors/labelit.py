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

def parse_output(labelit_output, iteration=0):
    """
    Parses Labelit results and filters for specific errors. Cleans up the output AND looks for best
    solution then passes info back to caller.

    Code adapted from work by J.Schuermann
    """

    labelit_output = labelit_output.split("\n")

    # Holders for parsed data
    result_lines = []
    labelit_sol = []
    pseudotrans = False
    multi_sg = False
    few_spots = False
    min_spots = False
    spot_problem = False
    labelit_face = []
    labelit_solution = []
    labelit_metric = []
    labelit_fit = []
    labelit_rmsd = []
    labelit_spots_fit = []
    labelit_system = []
    labelit_cell = []
    labelit_volume = []
    labelit_bc = {}
    mosflm_face = []
    mosflm_solution = []
    mosflm_sg = []
    mosflm_beam_x = []
    mosflm_beam_y = []
    mosflm_distance = []
    mosflm_res = []
    mosflm_mos = []
    mosflm_rms = []

    # TESTING
    #return ('min_spots', 28)
    #return "failed"
    #return "junk"
    #return ("min_good_spots", 28)
    #return "fix_labelit"
    #return "no_pair"
    #return "bad_input"
    #return "bumpiness"
    #return "mosflm_error"
    #return "eiger_cbf_error"
    

    # If results empty, then fail
    if len(labelit_output) == 0:
        return "failed"

    # Check for errors
    for index, line in enumerate(labelit_output):
        if len(line) > 1:
            if line.startswith("distl_minimum_number_spots"):
                min_spots = line
            if line.startswith("RuntimeError:"):
                return "failed"
            if line.startswith("ValueError:"):
                return "failed"
            if line.startswith("Labelit finds no reasonable solution"):
                # if self.multiproc:
                return "failed"
                # else:
                    # return "no index"
            if line.startswith("No_Indexing_Solution: Unreliable model"):
                # if self.multiproc:
                return "failed"
                # else:
                    # return "no index"
            if line.startswith("No_Indexing_Solution: (couldn\"t find 3 good basis vectors)"):
                # if self.multiproc:
                return "failed"
                # else:
                #     return "no index"
            if line.startswith("MOSFLM_Warning: MOSFLM logfile declares FATAL ERROR"):
                # if self.multiproc:
                return "failed"
                # else:
                #     return "no index"
            if line.startswith("ValueError: min()"):
                # if self.multiproc:
                return "failed"
                # else:
                    # return "no index"
            if line.startswith("Spotfinder Problem:"):
                spot_problem = True
            if line.startswith("InputFileError: Input error: File header must contain the sample-to\
-detector distance in mm; value is 0."):
                return "fix_labelit"
            if line.startswith("InputFileError: Input error:"):
                return "no_pair"
            if line.startswith("Have "):
                few_spots = int(line.split()[1].rstrip(";"))
            if line.startswith("UnboundLocalError"):
                return "bad_input"
            if line.startswith("divide by zero"):
                return "bumpiness"
            # Could give error is too many choices with close cell dimensions, but...
            if line.startswith("No_Lattice_Selection: In this case"):
                multi_sg = True
                error_lg = line.split()[11]
            if line.startswith("No_Lattice_Selection: The known_symmetry"):
                return "bad_input"
            if line.startswith("MOSFLM_Warning: MOSFLM does not give expected results on r_"):
                return "mosflm_error"
            if line.count("TypeError: unsupported operand type(s) for %: 'NoneType' and 'int'"):
                return "eiger_cbf_error"
            
            # Save the beam center
            if line.startswith("Beam center"):
                labelit_bc["labelit_x_beam"] = line.split()[3][:-3]
                labelit_bc["labelit_y_beam"] = line.split()[5][:-3]

            # Now save line numbers for parsing Labelit and Mosflm results
            if line.startswith("Solution"):
                result_lines.append(index)
            # Find lines for Labelit"s pseudotrans
            if line.startswith("Analysis"):
                pseudotrans = True
                result_lines.append(index)
            if line.startswith("Transforming the lattice"):
                pseudotrans = True

    # No extra parsing to do
    if len(result_lines) == 0:
        if spot_problem:
            if min_spots:
                # print "min spots", labelit_output
                spots_count = int(labelit_output[-2].split("=")[1])
                return ("min_spots", spots_count)
            else:
                return "failed"
        elif multi_sg:
            return "bad_input"
        else:
            return "failed"

    # Parse Labelit results
    for line in labelit_output[result_lines[0]:]:
        # Solution
        if len(line.split()) == 15:
            labelit_sol.append(line.split())
            labelit_face.append(line.split()[0])
            labelit_solution.append(line.split()[1])
            labelit_metric.append(line.split()[2])
            labelit_fit.append(line.split()[3])
            labelit_rmsd.append(line.split()[4])
            labelit_spots_fit.append(line.split()[5])
            labelit_system.append(line.split()[6:8])
            labelit_cell.append(line.split()[8:14])
            labelit_volume.append(line.split()[14])

    # If multiple indexing choice for same SG... taking care of it.
    if multi_sg:
        return ("fix_cell", error_lg, labelit_sol)

    # Getting Mosflm results with Labelit pseudotrans present
    if len(result_lines) == 3:
        mosflm_lines = labelit_output[result_lines[1]+1:result_lines[2]-1]
    # If no pseudotrans...
    else:
        # pprint(labelit_output)
        mosflm_lines = labelit_output[result_lines[1]+1:]

    #  Parse Mosflm results
    for line in mosflm_lines:
        run = True
        if len(line.split()) == 9:
            result_line = 1
            mosflm_face.append(line.split()[0])
            if line.split()[0].startswith(":)"):
                mosflm_index = "index"+line.split()[1].zfill(2)
        elif len(line.split()) == 8:
            result_line = 0
            mosflm_face.append(" ")
        else:
            run = False
        if run:
            mosflm_solution.append(line.split()[0+result_line])
            mosflm_sg.append(line.split()[1+result_line])
            mosflm_beam_x.append(line.split()[2+result_line])
            mosflm_beam_y.append(line.split()[3+result_line])
            mosflm_distance.append(line.split()[4+result_line])
            mosflm_res.append(try_float(line.split()[5+result_line]))
            mosflm_mos.append(try_float(line.split()[6+result_line]))
            mosflm_rms.append(line.split()[7+result_line])

    # Sometimes Labelit works with few spots, sometimes it doesn"t...
    # When it doesn't, then rerun
    if few_spots:
        if os.path.exists(mosflm_index) == False:
            return ("min_good_spots", few_spots)

    data = {"labelit_face": labelit_face,
            "labelit_solution": labelit_solution,
            "labelit_metric": labelit_metric,
            "labelit_fit": labelit_fit,
            "labelit_rmsd": labelit_rmsd,
            "labelit_spots_fit": labelit_spots_fit,
            "labelit_system": labelit_system,
            "labelit_cell": labelit_cell,
            "labelit_volume": labelit_volume,
            "labelit_iteration": iteration,
            "labelit_bc": labelit_bc,
            "pseudotrans": pseudotrans,
            "mosflm_face": mosflm_face,
            "mosflm_solution": mosflm_solution,
            "mosflm_sg": mosflm_sg,
            "mosflm_beam_x": mosflm_beam_x,
            "mosflm_beam_y": mosflm_beam_y,
            "mosflm_distance": mosflm_distance,
            "mosflm_res": mosflm_res,
            "mosflm_mos": mosflm_mos,
            "mosflm_rms": mosflm_rms,
            "mosflm_index": mosflm_index,
            "output": labelit_output}

    return data

def parse_labelit_files_OLD(bestfile_lines, mat_lines, sub_lines, mode="all"):
    """
    Parse the lines from bestfile.par
    Transplant from xutils.getLabelitCell
    NOW IN PLUGIN
    """

    run2 = False
    run3 = False
    cell = False
    sym = False
    for line in bestfile_lines:
        # print line
        if line.startswith('CELL'):
            if len(line.split()) == 7:
                cell = [try_float(item) for item in line.split()[1:]]
            else:
                run2 = True
        if line.startswith('SYMMETRY'):
            if len(line.split()) == 2:
                sym = line.split()[1]
            else:
                run3 = True
    # Sometimes bestfile.par is corrupt so I have backups to get cell and sym.
    if run2:
        for line in mat_lines:
            if len(line.split()) == 6:
                cell = [try_float(item) for item in line.split()]

    if run3:
        for line in sub_lines:
            if line.startswith('SYMMETRY'):
                sym = line.split()[1]

    # pprint(cell)
    # pprint(sym)

    if mode == 'all':
        return (cell, sym)
    elif mode == 'sym':
        return sym
    else:
        return cell

def get_labelit_stats(labelit_results, simple=False):
    """
    Returns stats from Labelit for determining beam center
    """

    output = {}

    # print "get_labelit_stats"
    # pprint(labelit_results)

    if not isinstance(labelit_results, dict):
        raise Exception("labelit_output needs to be a dict for this function")

    # Set the limit of parsing
    if simple:
        limit = 1
    else:
        limit = 2

    for index in range(0, limit):
        # Best stats
        if index == 0:
            face_index = labelit_results.get("mosflm_face").index(":)")
            spacegroup = labelit_results.get("mosflm_sg")[face_index]
            solution = labelit_results.get("mosflm_solution")[face_index]
        # P1 stats
        else:
            face_index = labelit_results.get("mosflm_solution").index("1")
            solution = "1"

        mos_rms = float(labelit_results.get("mosflm_rms")[face_index])
        mos_x = float(labelit_results.get("mosflm_beam_x")[face_index])
        mos_y = float(labelit_results.get("mosflm_beam_y")[face_index])
        solution_index = labelit_results.get("labelit_solution").index(solution)
        metric = float(labelit_results.get("labelit_metric")[solution_index])
        rmsd = float(labelit_results.get("labelit_rmsd")[solution_index])
        volume = int(labelit_results.get("labelit_volume")[solution_index])

        if index == 0:
            output["best"] = {
                "spacegroup": spacegroup,
                "mos_rms": mos_rms,
                "mos_x" :mos_x,
                "mos_y": mos_y,
                "metric": metric,
                "rmsd": rmsd,
                "sol": solution
            }
        else:
            output["P1"] = {
                "mos_rms": mos_rms,
                "mos_x": mos_x,
                "mos_y": mos_y,
                "rmsd": rmsd
            }

    if simple:
        return (spacegroup, mos_rms, metric, volume)
    else:
        return output

#
# Functions for modifying labelit runs

def decrease_mosflm_resolution(iteration):
    """Increases resolution of mosflm run"""

    if os.path.isfile("index01"):
        # Open and modify preferences
        preferences = open("dataset_preferences.py", "a")
    
        # Open index01 and grab out resolution
        for line in open("index01", "r").readlines():
            if line.startswith("RESOLUTION"):
                new_res = float(line.split()[1])+1.00
                preferences.write("\n#iteration %d\nmosflm_integration_reslimit_override = %.1f\n" % \
                                  (iteration, new_res))
        preferences.close()
    
        return new_res

def decrease_spot_requirements(spot_count):
    """Decrease the required spot count in an attempt to get indexing to work"""

    if spot_count < 25:
        return False
    else:
        # Update dataset preferences to have lower spot number requirement
        with open("dataset_preferences.py", "a") as preferences:
            preferences.write("distl_minimum_number_spots_for_indexing=%d\n" % spot_count)

        return spot_count

def decrease_good_spot_requirements(min_spots):
    """
    Sometimes Labelit gives an eror saying that there aren't enough 'good spots' for Mosflm. Not a
    Labelit failure error. Forces Labelit/Mosflm to give result regardless. Sometimes causes failed
    index.
    """

    with open("dataset_preferences.py", "a") as preferences:
        preferences.write("model_refinement_minimum_N=%d" % min_spots)
    """
    with open("dataset_preferences.py", "r") as preferences:
        for line in preferences:
            print line
    """
    return min_spots

def no_bumpiness():
    """
    Get rid of distl_profile_bumpiness line in dataset_preferences.py.
    """

    input_lines = open("dataset_preferences.py", "r").readlines()

    removed = False
    with open("dataset_preferences.py", "w") as preferences:
        for line in input_lines:
            if line.startswith("distl_profile_bumpiness"):
                removed = True
            else:
                preferences.write(line)

    return removed

def fix_multiple_cells(lattice_group, labelit_solution):
    """
    Pick correct cell (lowest rmsd) if multiple cell choices are possible in user selected SG
    """

    rmsd = []
    min_rmsd = False
    for index in range(2):
        if index == 1:
            min_rmsd = min(rmsd)
        for line in labelit_solution:
            if line[7] == lattice_group:
                if index == 0:
                    rmsd.append(float(line[4]))
                else:
                    #if line[4] == str(min_rmsd):
                    if float(line[4]) == min_rmsd:
                        #cell_cmd = "known_cell=%s,%s,%s,%s,%s,%s " % (line[8],
                        #                                              line[9],
                        #                                              line[10],
                        #                                              line[11],
                        #                                              line[12],
                        #                                              line[13])
                        #return cell_cmd
                        return "known_setting=%s "%line[1]

def main():
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    print "main"

    args = get_commandline()

def get_commandline():
    """
    Grabs the commandline
    """

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Generate a generic RAPD file"

    my_parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    my_parser.add_argument("-c", "--commandline",
                           action="store_true",
                           dest="commandline",
                           help="Generate commandline argument parsing")

    # File name to be generated
    my_parser.add_argument(action="store",
                           dest="file",
                           nargs="?",
                           default=False,
                           help="Name of file to be generated")

    # Print help message is no arguments
    if len(sys.argv[1:])==0:
        my_parser.print_help()
        my_parser.exit()

    return my_parser.parse_args()

if __name__ == "__main__":

    # Execute code
    main()

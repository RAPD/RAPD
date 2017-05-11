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

    print ">>>>parse_output"

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
                return "fix labelit"
            if line.startswith("InputFileError: Input error:"):
                return "no pair"
            if line.startswith("Have "):
                # self.min_good_spots = line.split()[1].rstrip(";")
                few_spots = True
            if line.startswith("UnboundLocalError"):
                return "bad input"
            if line.startswith("divide by zero"):
                return "bumpiness"
            # Could give error is too many choices with close cell dimensions, but...
            if line.startswith("No_Lattice_Selection: In this case"):
                multi_sg = True
                error_lg = line.split()[11]
            if line.startswith("No_Lattice_Selection: The known_symmetry"):
                return "bad input"
            if line.startswith("MOSFLM_Warning: MOSFLM does not give expected results on r_"):
                return "mosflm error"
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
                return ("min spots", labelit_output[-1])
            else:
                return "failed"
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
            mosflm_res.append(line.split()[5+result_line])
            mosflm_mos.append(line.split()[6+result_line])
            mosflm_rms.append(line.split()[7+result_line])

    # Sometimes Labelit works with few spots, sometimes it doesn"t...
    if few_spots:
        if os.path.exists(mosflm_index) == False:
            return "min good spots"

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

    pprint(data)
    return data

# def getLabelitStats(self,inp=False,simple=False):
#   """
#   Returns stats from Labelit for determining beam center. (Extra parsing from self.labelit_results)
#   """
#   if self.verbose:
#     self.logger.debug('Utilities::getLabelitStats')
#   output = {}
#   try:
#     if inp:
#       j1 = '[inp]'
#     else:
#       j1 = ''
#     if simple:
#       x = 1
#     else:
#       x = 2
#     if type(eval('self.labelit_results%s'%j1).get('Labelit results')) == dict:
#       for i in range(0,x):
#         if i == 0:
#           ind = eval('self.labelit_results%s'%j1).get('Labelit results').get('mosflm_face').index(':)')
#           sg   = eval('self.labelit_results%s'%j1).get('Labelit results').get('mosflm_sg')[ind]
#           sol  = eval('self.labelit_results%s'%j1).get('Labelit results').get('mosflm_solution')[ind]
#         else:
#           #P1 stats
#           ind = eval('self.labelit_results%s'%j1).get('Labelit results').get('mosflm_solution').index('1')
#           sol = '1'
#         mos_rms = eval('self.labelit_results%s'%j1).get('Labelit results').get('mosflm_rms')[ind]
#         mos_x = eval('self.labelit_results%s'%j1).get('Labelit results').get('mosflm_beam_x')[ind]
#         mos_y = eval('self.labelit_results%s'%j1).get('Labelit results').get('mosflm_beam_y')[ind]
#         ind1  = eval('self.labelit_results%s'%j1).get('Labelit results').get('labelit_solution').index(sol)
#         met  = eval('self.labelit_results%s'%j1).get('Labelit results').get('labelit_metric')[ind1]
#         rmsd = eval('self.labelit_results%s'%j1).get('Labelit results').get('labelit_rmsd')[ind1]
#         vol = eval('self.labelit_results%s'%j1).get('Labelit results').get('labelit_volume')[ind1]
#         if i == 0:
#           output['best'] = {'SG':sg, 'mos_rms':mos_rms, 'mos_x':mos_x, 'mos_y':mos_y, 'metric':met, 'rmsd':rmsd, 'sol':sol}
#         else:
#           output['P1']   = {'mos_rms':mos_rms, 'mos_x':mos_x, 'mos_y':mos_y, 'rmsd':rmsd}
#       if simple:
#         return(sg,mos_rms,met,vol)
#       else:
#         eval('self.labelit_results%s'%j1).update({'labelit_stats': output})
#   except:
#     self.logger.exception('**Error in Utils.getLabelitStats**')


def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    print "main"

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

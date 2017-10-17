"""This is a docstring for this file"""

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

__created__ = "2017-02-02"
_maintainer__ = "David Neau"
__email__ = "dneau@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
import sys

from utils.text import json
from bson.objectid import ObjectId

class INP2DICT(object):
    def __init__(self, xdsinp, xdsdict):
        self.xdsinp = xdsinp
        self.xdsdict = xdsdict
        self.run()

    def run(self):

        temp = open(self.xdsinp, 'r').readlines()
        inp=[]
        for line in temp:
            inp.append(line.strip())
        temp=[]

        untrusted_index=1
        xds_dict = {}

        # A list of experiment dependent keywords that should not make up a
        # minimal description of an XDS.INP file or values that you would
        # want to possibly change based on conditions.
        exp_deps = [
            'BACKGROUND_RANGE',
            "BEAM_DIVERGENCE",
            "BEAM_DIVERGENCE_E.S.D.",
            'DATA_RANGE',
            'DETECTOR_DISTANCE',
            'EXCLUDE_DATA_RANGE',
            'EXCLUDE_RESOLUTION_RANGE',
            'FIT_B-FACTOR_TO_REFERENCE_DATA_SET',
            "FRIEDEL'S_LAW",
            "INCLUDE_RESOLUTION_RANGE",
            'JOB',
            'ORGX',
            'ORGY',
            'OSCILLATION_RANGE',
            'MAXIMUM_NUMBER_OF_JOBS',
            'MAXIMUM_NUMBER_OF_PROCESSORS',
            'NAME_TEMPLATE_OF_DATA_FRAMES',
            'NUMBER_OF_IMAGES_IN_CACHE',
            "REFLECTING_RANGE_E.S.D.",
            'REFERENCE_DATA_SET',
            "REFLECTING_RANGE",
            'SPACE_GROUP_NUMBER',
            'SPOT_RANGE',
            'UNIT_CELL_CONSTANTS',
            'X-RAY_WAVELENGTH',
            ]

        for line in inp:
            # Skip if line begins with "!" or has a length too short to contain
            # an XDS keyword.
            if line.startswith('!') or len(line) < 4:
                pass
            else:
                # If the line contains a comment signaled by an "!", ignore that section.
                keyline = line.split('!')[0].strip()
                # If the line contains only a single keyword, value pair -
                # add that pair to the dict.
                # EXCEPTION: if kerword contains 'UNTRUSTED' add and index to it
                # before adding it to the dict.
                # EXCEPTION: If keyword is part of exp_deps list, don't add to the dict.
                for i in range (0, keyline.count('=')):
                    keyline, sep, value = keyline.rpartition('=')
                    splitkey = keyline.split(' ')
                    keyline = ' '.join(splitkey[0:-1])
                    key = splitkey[-1]
                    if 'UNTRUSTED' in key:
                        key = '%s%s' %(key,untrusted_index)
                        untrusted_index+=1
                    if key not in exp_deps:
                        xds_dict[key] = value

        print "XDSINP = {"
        for key, val in xds_dict.iteritems():
            print "    \"%s\": \"%s\"," % (key, str(val))

        print "    }"

        # The OrderedDict
        print "XDSINP =  OrderedDict(["
        for key, val in xds_dict.iteritems():
            print "    (\"%s\", \"%s\")," % (key, str(val))

        print "    ])"
        # with open(self.xdsdict, "w") as file:
        #     json.dump(xds_dict, file)


        return()

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    number_of_args = len(sys.argv) - 1
    if number_of_args >= 2:
        INP2DICT(xdsinp=sys.argv[1],xdsdict=sys.argv[2])
    else:
        INP2DICT(xdsinp=sys.argv[1], xdsdict='XDSDICT.json')

def get_commandline():
    """
    Grabs the commandline
    """

    # Parse the commandline arguments
    commandline_description = "Generate a generic RAPD file"
    parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    parser.add_argument("-c", "--commandline",
                        action="store_true",
                        dest="commandline",
                        help="Generate commandline argument parsing")

    # File name to be generated
    parser.add_argument(action="store",
                        dest="file",
                        nargs="?",
                        default=False,
                        help="Name of file to be generated")

    return parser.parse_args()

if __name__ == "__main__":

    # Get the commandline args
    commandline_args = get_commandline()

    # Execute code
    main(args=commandline_args)

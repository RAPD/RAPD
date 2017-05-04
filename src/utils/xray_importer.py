"""Tool for importing X-ray files into RAPD"""

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

__created__ = "2017-05-04"
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
# import urllib2
# import uuid

from iotbx import reflection_file_reader, file_reader

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
# import utils.credits as credits

# Software dependencies
VERSIONS = {
# "eiger2cbf": ("160415",)
}


# Preprocess function from Kay Perry
def preprocess(self):
    """
    Before running the main process
    - change to the current directory
    - copy files to the working directory
    - convert all files to cctbx usable format and save in self
    - test reflection files for acceptable format (XDS and unmerged mtz only)
    - ensure all files are the same format
    """

    self.logger.debug('HCMerge::Prechecking files: %s' % str(self.datasets))

    if self.precheck:

        # mtz and xds produce different file formats.  Check for type to do duplicate comparison specific to file type.
        types = []
        hashset = {}
        for dataset in self.datasets:
            reflection_file = reflection_file_reader.any_reflection_file(file_name=dataset)
            types.append(reflection_file.file_type()) # Get types for format test
            hashset[dataset] = hashlib.md5(open(dataset, 'rb').read()).hexdigest() # hash for duplicates test

            # Test for SCA format
            if reflection_file.file_type() == 'scalepack_no_merge_original_index' or reflection_file.file_type() == 'scalepack_merge':
                self.logger.error('HCMerge::Scalepack format. Aborted')
                raise ValueError("Scalepack Format. Unmerged mtz format required.")

            # Test reflection files to make sure they are XDS or MTZ format
            elif reflection_file.file_type() != 'xds_ascii' and reflection_file.file_type() != 'ccp4_mtz':
                self.logger.error('HCMerge::%s Reflection Check Failed.  Not XDS format.' % reflection_file.file_name())
                raise ValueError("%s has incorrect file format. Unmerged reflections in XDS format only." % reflection_file.file_name())

            # Test for all the same format
            elif len(set(types)) > 1:
                self.logger.error('HCMerge::Too Many File Types')
                raise ValueError("All files must be the same type and format.")

            # Test reflection files to make sure they have observations
            elif ((reflection_file.file_type() == 'xds_ascii') and (reflection_file.file_content().iobs.size() == 0)):
                self.logger.error('HCMerge::%s Reflection Check Failed.  No Observations.' % reflection_file.file_name())
                raise ValueError("%s Reflection Check Failed. No Observations." % reflection_file.file_name())
            elif ((reflection_file.file_type() == 'ccp4_mtz') and (reflection_file.file_content().n_reflections() == 0)):
                self.logger.error('HCMerge::%s Reflection Check Failed.  No Observations.' % reflection_file.file_name())
                raise ValueError("%s Reflection Check Failed. No Observations." % reflection_file.file_name())

            # Test reflection file if mtz and make sure it isn't merged by checking for amplitude column
            elif ((reflection_file.file_type() == 'ccp4_mtz') and ('F' in reflection_file.file_content().column_labels())):
                self.logger.error('HCMerge::%s Reflection Check Failed.  Must be unmerged reflections.' % reflection_file.file_name())
                raise ValueError("%s Reflection Check Failed. Must be unmerged reflections." % reflection_file.file_name())

        # Test reflection files to make sure there are no duplicates
        combos_temp =  self.make_combinations(self.datasets,2)
        for combo in combos_temp:
            if hashset[combo[0]] == hashset[combo[1]]:
                self.datasets.remove(combo[1]) # Remove second occurrence in list of datasets
                self.logger.error('HCMerge::Same file Entered Twice. %s deleted from list.' % combo[1])

    # Make and move to the work directory
    if os.path.isdir(self.dirs['work']) == False:
        os.makedirs(self.dirs['work'])
        os.chdir(self.dirs['work'])
    else:
        combine_dir = self.create_subdirectory(prefix='COMBINE', path=self.dirs['work'])
        os.chdir(combine_dir)
    # convert all files to mtz format
    # copy the files to be merged to the work directory
    for count, dataset in enumerate(self.datasets):
        hkl_filename = str(count)+'_'+dataset.rsplit("/",1)[1].rsplit(".",1)[0]+'.mtz'
        if self.user_spacegroup != 0:
            sg = space_group_symbols(self.user_spacegroup).universal_hermann_mauguin()
            self.logger.debug('HCMerge::Converting %s to %s and copying to Working Directory.' % (str(hkl_filename), str(sg)))
            out_file = hkl_filename.rsplit(".",1)[0]
            command = []
            command.append('pointless hklout '+hkl_filename+'> '+out_file+'_import.log <<eof \n')
            command.append('xdsin '+dataset+' \n')
            command.append('lauegroup %s \n' % sg)
            command.append('choose spacegroup %s \n' % sg)
            command.append('eof\n')
            comfile = open(out_file+'_import.sh','w')
            comfile.writelines(command)
            comfile.close()
            os.chmod('./'+out_file+'_import.sh',0755)

            p = subprocess.Popen(self.cmd_prefix+' ./'+out_file+'_import.sh',
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE).wait()
        else:
            self.logger.debug('HCMerge::Copying %s to Working Directory.' % str(dataset))
            p = subprocess.Popen('pointless -copy xdsin ' + dataset + ' hklout ' + hkl_filename,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE).wait()
        # Make a list of filenames
        self.data_files.append(hkl_filename)

reflection_file_types = (
    "ccp4_mtz",
    "scalepack_merge",
    "scalepack_no_merge_original_index",
    "xds_ascii",
    "xds_integrate_hkl",
)

xray_column_synonyms = {
    # Indices
    "H": ("H",),
    "K": ("K",),
    "L": ("L",),

    # Unmerged intensities
    "I": ("I", "IOBS"),
    "SIGI": ("SIGI", "SIGMA(IOBS)"),

    # Merged intensities
    "IMEAN": ("IMEAN",),
    "SIGIMEAN": ("SIGIMEAN",),

    # Structure factors
    "F": ("F",),
    "SIGF": ("SIGF",),

    # Merged, but unmerged
    "I(+)": ("I(+)",),
    "I(-)": ("I(-)",),
    "SIGI(+)": ("SIGI(+)",),
    "SIGI(-)": ("SIGI(-)",),

    # Merged, but unmerged
    "F(+)": ("F(+)",),
    "F(-)": ("F(-)",),
    "SIGF(+)": ("SIGF(+)",),
    "SIGF(-)": ("SIGF(-)",),

    "DANO": ("DANO",),
    "SIGDANO": ("SIGDANO",),

    "ISYM": ("ISYM",),                  # merged
    "M/ISYM": ("M/ISYM",),              # unmerged

    "BATCH": ("BATCH",),

    "FRACTIONCALC": ("FRACTIONCALC",),  # Partiality of reflection mergable.mtz
    "XDET": ("XDET", "XD"),             # X position on detector
    "YDET": ("YDET", "YD"),             # Y position on detector
    "ROT": ("ROT",),                    # Rotation position of reflection mergable.mtz
    "ZD": ("ZD",),                      # XDS_ASCII - centroid of image numbers that recorded the
                                        #             Bragg peak

    "LP": ("LP",),          # mergable.mtz
    "FLAG": ("FLAG",),      # mergable.mtz
    "PSI": ("PSI",),        # XDS_ASCII - value of Schwarzenbach and Flack's psi-angle
    "CORR": ("CORR",),      # XDS_ASCII - percentage of correlation between observed and expected
                            #             reflection profile
    "PEAK": ("PEAK",),      # XDS_ASCII - percentage of observed reflection intensity
    "RLP": ("RLP",),        # XDS_ASCII - reciprocal LP-correction factor that has been applied to
                            #             this reflection



    "FreeR_flag": ("FreeR_flag",),

    "": ("",),
    "": ("",),
    "": ("",),


    "": ("",),

}

def main():
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    print "main"

    args = get_commandline()

    datafiles = args.datafiles

    for input_datafile in datafiles:

        print "\n", input_datafile

        datafile = reflection_file_reader.any_reflection_file(file_name=input_datafile)

        print type(datafile)

        file_type = datafile.file_type()

        print "  file_type", datafile.file_type()
        # print "  miller_arrays", dir(datafile.as_miller_arrays()[0])

        # Get the columns
        # MTZ
        if file_type == "ccp4_mtz":
            columns = datafile.file_content().column_labels()
        # XDS
        elif file_type == "xds_ascii":
            columns = get_xds_ascii_columns(input_datafile)

        # Unhandled
        else:
            raise Exception("Unable to handle file of type %s" % file_type)

        print columns

def get_file_type(reflection_file):
    """Return the file type"""

    if not isinstance(datafile, iotbx.reflection_file_reader.any_reflection_file):
        reflection_file = datafile

def get_columns(datafile):
    """Return a list of columns for the input file"""

    pass

def get_xds_ascii_columns(datafile):
    """Look at a text file ang return an array of columns"""

    columns = []

    inlines = open(datafile, "r").read(6144)
    for line in inlines.split("\n"):
        if line.startswith("!ITEM_"):
            columns.append(line.replace("!ITEM_", "").split("=")[0])
        elif not line.startswith("!"):
            break

    return columns

def determine_if_unmerged(datafile, columns=None):
    """Determine if a file is unmerged"""

    if columns == None:

        pass

def get_commandline():
    """
    Grabs the commandline
    """

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Generate a generic RAPD file"

    my_parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    my_parser.add_argument("-t", "--type",
                           action="store",
                           dest="output_type",
                           default="intensities_unmerged",
                           choices=["intensities_unmerged",],
                           help="Type of file to be imported to")

    # File name to be generated
    my_parser.add_argument(action="store",
                           dest="datafiles",
                           nargs="+",
                           default=False,
                           help="Datafile(s) to be imported")

    # Print help message is no arguments
    if len(sys.argv[1:])==0:
        my_parser.print_help()
        my_parser.exit()

    return my_parser.parse_args()

if __name__ == "__main__":

    # Execute code
    main()

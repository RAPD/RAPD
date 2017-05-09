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
import os
from pprint import pprint
# import pymongo
# import re
# import redis
# import shutil
import subprocess
import sys
import tempfile
import time
# import unittest
# import urllib2
# import uuid

from iotbx import reflection_file_reader, file_reader

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
from utils.xutils import fix_mtz_to_sca
# import utils.credits as credits

# Software dependencies
# Software dependencies
VERSIONS = {
    "aimless": (
        "version 0.5",
        ),
    "freerflag": (
        "version 2.2",
    ),
    # "gnuplot": (
    #     "gnuplot 4.2",
    #     "gnuplot 5.0",
    # ),
    "mtz2various": (
        "version 1.1",
    ),
    "pointless": (
        "version 1.10",
        ),
    "truncate": (
        "version 7.0",
    ),
    "xds": (
        "VERSION Nov 1, 2016",
        ),
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

DATA_FILE_CCTBX_TYPES = (
    "ccp4_mtz",
    "scalepack_merge",
    "scalepack_no_merge_original_index",
    "xds_ascii",
    "xds_integrate_hkl",
)

XRAY_COLUMN_SYNONYMS = {

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
}

# File suffixes used by RAPD
RAPD_FILE_SUFFIXES = {
    "mergable_mtz": "_mergable.mtz",
    "minimal_mergeable_mtz": "_min_mergeable.mtz",
    "minimal_refl_anom_mtz": "_min_anom.mtz",
    "minimal_refl_mtz": "_min.mtz",
    "minimal_rfree_mtz": "_min_rfree.mtz",
    "rfree_mtz": "_rfree.mtz",
    "scalepack_anomalous": "_ANOM.sca",
    "scalepack_merge": ".sca",
    "scalepack_no_merge_original_index": "_nmoi.sca",
    "xds_corrected": "_ASCII.HKL",
    "xds_integrated": ".HKL",
}

# Column signatures for file put out by RAPD
RAPD_FILE_SIGNATURES = {
    "mergable_mtz": (
        "ccp4_mtz",
        [
            'H',
            'K',
            'L',
            'M_ISYM',
            'BATCH',
            'I',
            'SIGI',
            'FRACTIONCALC',
            'XDET',
            'YDET',
            'ROT',
            'LP',
            'FLAG',
        ],
    ),
    "minimal_mergeable_mtz": (
        "ccp4_mtz",
        [
            "H",
            "K",
            "L",
            "M/ISYM",
            "BATCH",
            "I",
            "SIGI",
        ]
    ),
    "minimal_refl_mtz": ("ccp4_mtz",
                         ['H',
                          'K',
                          'L',
                          'IMEAN',
                          'SIGIMEAN',
                         ],
                        ),
    "minimal_refl_anom_mtz": ("ccp4_mtz",
                              ['H',
                               'K',
                               'L',
                               'IMEAN',
                               'SIGIMEAN',
                               'I(+)',
                               'SIGI(+)',
                               'I(-)',
                               'SIGI(-)',
                              ],
                             ),
    "minimal_rfree_mtz": (
        "ccp4_mtz",
        [
            'H',
            'K',
            'L',
            'FreeR_flag',
            'IMEAN',
            'SIGIMEAN',
            'F',
            'SIGF',
        ]
    ),
    "rfree_mtz": (
        "ccp4_mtz",
        [
            'H',
            'K',
            'L',
            'FreeR_flag',
            'IMEAN',
            'SIGIMEAN',
            'I(+)',
            'SIGI(+)',
            'I(-)',
            'SIGI(-)',
            'F',
            'SIGF',
            'DANO',
            'SIGDANO',
            'F(+)',
            'SIGF(+)',
            'F(-)',
            'SIGF(-)',
            'ISYM'
        ],
    ),
    "scalepack_anomalous": (
        "scalepack_merge",
        [
            'H',
            'K',
            'L',
            'I(+)',
            'SIGI(+)',
            'I(-)',
            'SIGI(-)',
        ],
    ),
    "scalepack_merge": (
        "scalepack_merge",
        [
            'H',
            'K',
            'L',
            'I',
            'SIGI',
        ],
    ),
    "scalepack_no_merge_original_index": (
        "scalepack_no_merge_original_index",
        [
            "H",
            "K",
            "L",
            "H0",
            "K0",
            "L0",
            "BATCH",
            "UNK",
            "UNK",
            "UNK",
            "I",
            "SIGI",
        ]
    ),
    "xds_corrected": (
        "xds_ascii",
        [
            'H',
            'K',
            'L',
            'IOBS',
            'SIGMA(IOBS)',
            'XD',
            'YD',
            'ZD',
            'RLP',
            'PEAK',
            'CORR',
            'PSI',
        ],
    ),
    "xds_integrated": (
        "xds_integrate_hkl",
        [
            'H',
            'K',
            'L',
            'IOBS',
            'SIGMA',
            'XCAL',
            'YCAL',
            'ZCAL',
            'RLP',
            'PEAK',
            'CORR',
            'MAXC',
            'XOBS',
            'YOBS',
            'ZOBS',
            'ALF0',
            'BET0',
            'ALF1',
            'BET1',
            'PSI',
            'ISEG',
        ],
    ),
}

# Conversions that RAPD can and cannot perform
RAPD_CONVERSIONS = {
    ("mergable_mtz", "minimal_mergeable_mtz"): True,
    ("mergable_mtz", "minimal_refl_anom_mtz"): True,
    ("mergable_mtz", "minimal_refl_mtz"): True,
    ("mergable_mtz", "minimal_rfree_mtz"): True,
    ("mergable_mtz", "rfree_mtz"): True,
    ("mergable_mtz", "scalepack_anomalous"): True,
    ("mergable_mtz", "scalepack_merge"): True,

    ("minimal_refl_anom_mtz", "minimal_refl_mtz"): True,
    ("minimal_refl_anom_mtz", "minimal_rfree_mtz"): True,
    ("minimal_refl_anom_mtz", "scalepack_anomalous"): True,
    ("minimal_refl_anom_mtz", "rfree_mtz"): True,
    ("minimal_refl_anom_mtz", "scalepack_merge"): True,

    ("minimal_refl_mtz", "minimal_rfree_mtz"): False,
    ("minimal_refl_mtz", "scalepack_merge"): True,

    ("minimal_rfree_mtz", "minimal_refl_mtz"): False,
    ("minimal_rfree_mtz", "scalepack_merge"): True,

    ("rfree_mtz", "scalepack_anomalous"): True,
    ("rfree_mtz", "scalepack_merge"): True,

    ("scalepack_anomalous", "minimal_refl_anom_mtz"): True,
    ("scalepack_anomalous", "minimal_refl_mtz"): True,
    ("scalepack_anomalous", "rfree_mtz"): True,
    ("scalepack_anomalous", "scalepack_merge"): True,

    ("scalepack_merge", "minimal_refl_mtz"): True,
    ("scalepack_merge", "minimal_rfree_mtz"): True,

    ("scalepack_no_merge_original_index", "minimal_mergeable_mtz"): True,
    ("scalepack_no_merge_original_index", "minimal_refl_anom_mtz"): False,
    ("scalepack_no_merge_original_index", "minimal_refl_mtz"): False,
    ("scalepack_no_merge_original_index", "minimal_rfree_mtz"): False,
    ("scalepack_no_merge_original_index", "rfree_mtz"): False,
    ("scalepack_no_merge_original_index", "scalepack_anomalous"): False,
    ("scalepack_no_merge_original_index", "scalepack_merge"): False,
    ("scalepack_no_merge_original_index", ""): False,
    ("scalepack_no_merge_original_index", ""): False,

    ("xds_corrected", "mergable_mtz"): True,
    ("xds_corrected", "minimal_mergeable_mtz"): True,
    ("xds_corrected", "minimal_refl_anom_mtz"): False,
    ("xds_corrected", "minimal_rfree_mtz"): False,
    ("xds_corrected", "rfree_mtz"): True,
    ("xds_corrected", "scalepack_anomalous"): False,
    ("xds_corrected", "scalepack_merge"): False,

    ("xds_integrated", "mergable_mtz"): True,
    ("xds_integrated", "minimal_mergeable_mtz"): True,
    ("xds_integrated", "minimal_refl_anom_mtz"): False,
    ("xds_integrated", "minimal_rfree_mtz"): False,
    ("xds_integrated", "rfree_mtz"): True,
    ("xds_integrated", "scalepack_anomalous"): False,
    ("xds_integrated", "scalepack_merge"): False,
    ("xds_integrated", "xds_corrected"): False,
}

def main():
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    args = get_commandline()

    datafiles = args.datafiles

    for input_file_name in datafiles:

        print "\nInput file name: %s" % input_file_name

        datafile = reflection_file_reader.any_reflection_file(file_name=input_file_name)

        file_type = datafile.file_type()

        print "  CCTBX file type", datafile.file_type()

        # Get the columns
        columns = get_columns(datafile)
        print "  columns:", columns

        # Get the RAPD file type
        rapd_file_type = get_rapd_file_type(input_file_name)

        print "  RAPD file type:", rapd_file_type

        print "  Formats possible to be converted to:"
        for conversion, possible in RAPD_CONVERSIONS.iteritems():
            if conversion[0] == rapd_file_type:
                if possible:
                    print "      %s" % conversion[1]

        if rapd_file_type == "xds_corrected":
            print "convert_xds_corrected_to_minimal_mergeable_mtz >> %s" % \
                  convert_xds_corrected_to_minimal_mergeable_mtz(input_file_name, overwrite=True)

        if rapd_file_type == "xds_integrated":
            print "convert_xds_integrated_to_minimal_mergeable_mtz >> %s" % \
                  convert_xds_integrated_to_minimal_mergeable_mtz(input_file_name, overwrite=True)

        if rapd_file_type == "scalepack_merge":
            print convert_scalepack_merge_to_minimal_refl_mtz(input_file_name,
                                                              "minimal_refl_mtz.mtz",
                                                              True)
            print convert_scalepack_merge_to_minimal_rfree_mtz(input_file_name,
                                                               "minimal_rfree_mtz.mtz",
                                                               True)

        elif rapd_file_type == "minimal_refl_mtz":
            print convert_minimal_refl_mtz_to_scalepack_merge(input_file_name, "foo.sca", True)

        elif rapd_file_type == "minimal_rfree_mtz":
            print convert_minimal_rfree_mtz_to_scalepack_merge(input_file_name, "foo.sca", True)

        elif rapd_file_type == "scalepack_anomalous":
            print convert_scalepack_anomalous_to_minimal_refl_anom_mtz(input_file_name, "minimal_refl_anom_mtz.mtz", True)
            print convert_scalepack_anomalous_to_rfree_mtz(input_file_name, "rfree_mtz.mtz", True)
            print convert_scalepack_anomalous_to_minimal_refl_mtz(input_file_name, "minimal_refl_mtz.mtz", True)
            print convert_scalepack_anomalous_to_scalepack_merge(input_file_name, "foo_merge.sca", True)

        elif rapd_file_type == "mergable_mtz":
            print "convert_mergable_mtz_to_minimal_mergeable_mtz >> %s" % \
                  convert_mergable_mtz_to_minimal_mergeable_mtz(input_file_name, overwrite=True)
            # print "convert_mergable_mtz_to_minimal_refl_anom_mtz >> %s"  % \
            #       convert_mergable_mtz_to_minimal_refl_anom_mtz(input_file_name, overwrite=True)
            # print "convert_mergable_mtz_to_minimal_refl_mtz >> %s" % \
            #       convert_mergable_mtz_to_minimal_refl_mtz(input_file_name, overwrite=True)
            # print "convert_mergable_mtz_to_minimal_rfree_mtz >> %s" % \
            #       convert_mergable_mtz_to_minimal_rfree_mtz(input_file_name, overwrite=True)

        elif rapd_file_type == "minimal_refl_anom_mtz":
            # print "  convert_minimal_refl_anom_mtz_to_minimal_refl_mtz >> %s" % \
            #       convert_minimal_refl_anom_mtz_to_minimal_refl_mtz(input_file_name, overwrite=True)
            # print "  convert_minimal_refl_anom_mtz_to_minimal_rfree_mtz >> %s" % \
            #       convert_minimal_refl_anom_mtz_to_minimal_rfree_mtz(input_file_name,
            #                                                          overwrite=True)
            # print "convert_minimal_refl_anom_mtz_to_scalepack_anomalous >> %s " % \
            #       convert_minimal_refl_anom_mtz_to_scalepack_anomalous(input_file_name,
            #                                                            overwrite=True)
            # print "convert_minimal_refl_anom_mtz_to_rfree_mtz >> %s " % \
            #       convert_minimal_refl_anom_mtz_to_rfree_mtz(input_file_name, overwrite=True)
            print "convert_minimal_refl_anom_mtz_to_scalepack_merge >> %s " % \
                  convert_minimal_refl_anom_mtz_to_scalepack_merge(input_file_name,
                                                                   overwrite=True)

        elif rapd_file_type == "scalepack_no_merge_original_index":
            print "convert_scalepack_no_merge_original_index_to_minimal_mergeable_mtz >> %s" % \
                  convert_scalepack_no_merge_original_index_to_minimal_mergeable_mtz(
                      input_file_name,
                      overwrite=True)


#
# High-level functions
#
def convert_intensities_files(input_file_names,
                              output_rapd_type,
                              output_file_names=False,
                              force=False,
                              cell=False):
    """
    Convert multiple input files to a requested RAPD file type.

    Keyword arguments
    -----------------
    input_file_names - list or tuple of input files to be converted
    output_rapd_type - type of file to convert to. If RAPD is unable to convert to a requested
                       format from the input file, it will throw an Exception.
    output_file_names - list or tuple of output file names for the converted files
    force - allow overwrite of files if True
    cell - a tuple of cell dimensions & angles. Only necessary if a file input is
           scalepack no merge original index

    Returns a list of the converted file names
    """

    # Make sure the input_file_names is a list or tuple
    if not (isinstance(input_file_names, list) or \
            isinstance(input_file_names, tuple)):
        raise Exception("input_file_names should be a list or tuple")

    # Make sure all the files exist
    for input_file in input_file_names:
        if not os.path.exists(input_file):
            raise Exception("%s does not exist" % input_file)

    if output_file_names:
        # Make sure the output_file_names is a list or tuple
        if not (isinstance(output_file_names, list) or \
                isinstance(output_file_names, tuple)):
            raise Exception("output_file_names should be a list or tuple")

        # Make sure that there are output file names for all input_file_names
        if not len(output_file_names) == len(output_file_names):
            raise Exception("Mismatch in number of input and output file names")
    else:
        # Create some Falses for output file names
        output_file_names = [False] * len(input_file_names)

    # Is the final format understood?
    if not output_rapd_type in RAPD_FILE_SIGNATURES:
        raise Exception("Output type %s is not a format that is understood by \
RAPD" % output_rapd_type)

    # Is the cell either False or a tuple
    if cell:
        if not isinstance(cell, tuple):
            raise Exception("cell should be a tuple")
        if not len(cell) == 6:
            raise Exception("cell should have 6 real numbers for a, b, c, alpha, beta, gamma")

    # Run through and convert files
    output_files = []
    for input_file_name, output_file_name in zip(input_file_names, output_file_names):
        # print input_file_name, output_rapd_type, output_file_name, force
        output_files.append(convert_intensities_file(input_file_name,
                                                     output_rapd_type,
                                                     output_file_name,
                                                     force,
                                                     cell))

    return output_files

def convert_intensities_file(input_file_name,
                             output_rapd_type,
                             output_file_name=False,
                             force=False,
                             cell=False):
    """
    Convert input file to a requested RAPD file type.

    Keyword arguments
    -----------------
    input_file_name - filename of file to be converted
    output_rapd_type - type to be converted to. Must be in RAPD_FILE_SIGNATURES
    output_file_name - name of the file to be created by the conversion. Must have
                    the proper suffix
    force - allows overwrite of files if True
    cell - a tuple of cell dimensions & angles. Only necessary if a file input is
           scalepack no merge original index

    Returns the output file name
    """

    # Is the final format understood?
    if not output_rapd_type in RAPD_FILE_SIGNATURES:
        raise Exception("Output type %s is not a format that is understood by \
RAPD" % output_rapd_type)

    # Check to make sure source_file exists
    if not os.path.exists(input_file_name):
        raise Exception("%s does not exist" % input_file_name)

    # Read in input file
    reflection_file = reflection_file_reader.any_reflection_file(file_name=\
                      input_file_name)
    # Get CCTBX type
    input_file_cctbx_type = reflection_file.file_type()
    # Is the initial format understood?
    if not input_file_cctbx_type in data_file_cctbx_types:
        raise Exception("%s is not a format that is understood by RAPD" % \
                        input_file_cctbx_type)
    # Get the RAPD column signature
    input_columns = get_columns(reflection_file)
    input_rapd_type = get_rapd_file_type(input_columns)
    if not input_rapd_type:
        raise Exception("Input data file %s is not a format that is understood \
by RAPD" % input_file_name)

    # If the file is already in the desired format, return it
    if input_rapd_type == output_rapd_type:
        return input_file_name

    # Can the conversion be made?
    if not RAPD_CONVERSIONS.get((input_rapd_type, output_rapd_type)):
        raise Exception("RAPD is unable to convert from %s to %s" % \
                        (input_rapd_type, output_rapd_type))

    # Handle the output file name
    if output_file_name:
        # Only the file suffix after the "." is insisted upon
        if not output_file_name.endswith(RAPD_FILE_SUFFIXES[output_rapd_type].split("."[-1])):
            raise Exception("Output file suffix does not match RAPD standards. \
Please change to %s" % RAPD_FILE_SUFFIXES[output_rapd_type])
    else:
        # Create output file name from the input
        output_file_name = replace_suffix(input_file_name,
                                          input_rapd_type,
                                          output_rapd_type)
    if not force:
        if os.path.exists(output_file_name):
            raise Exception("%s already exists. Exiting" % output_file_name)

    # Is the cell either False or a tuple
    if cell:
        if not isinstance(cell, tuple):
            raise Exception("cell should be a tuple")
        if not len(cell) == 6:
            raise Exception("cell should have 6 real numbers for a, b, c, alpha, beta, gamma")

    # Perform the conversion
    main_module = sys.modules[__name__]
    method_to_call = getattr(main_module, "convert_%s_to_%s" % (input_rapd_type, output_rapd_type))
    if input_rapd_type == "scalepack_no_merge_original_index":
        output_file = method_to_call(source_file_name=input_file_name,
                                     dest_file_name=output_file_name,
                                     cell=cell,
                                     overwrite=force,
                                     clean=True)

    else:
        output_file = method_to_call(source_file_name=input_file_name,
                                     dest_file_name=output_file_name,
                                     overwrite=force,
                                     clean=True)

    return output_file

#
# Low-level functions
#
def get_columns(datafile):
    """
    Return a list of columns for a datafile

    datafile is a phenix any_reflection_file
    """

    # Determine file type
    file_type = datafile.file_type()

    # MTZ
    if file_type == "ccp4_mtz":
        columns = datafile.file_content().column_labels()
    # XDS
    elif file_type == "xds_ascii":
        columns = get_xds_ascii_columns(datafile)
    elif file_type == "xds_integrate_hkl":
        columns = get_xds_integrate_hkl_columns(datafile)
    elif file_type == "scalepack_merge":
        columns = get_scalepack_merge_columns(datafile)
    elif file_type == "scalepack_no_merge_original_index":
        columns = get_scalepack_no_merge_columns(datafile)
    else:
        # for d in dir(datafile.file_content()):
        #     print d
        columns = False

    return columns

def get_scalepack_merge_columns(datafile):
    """
    Look at an scalepack_merge file and return an array of columns

    datafile should be iotbx.reflection_file_reader.any_reflection_file
    """

    hi_len = 0
    inlines = open(datafile.file_name(), "r").read(6144)
    for line in inlines.split("\n")[3:]:
        # print line
        my_len = len(line.split())
        # print my_len, line
        hi_len = max(my_len, hi_len)

    # print hi_len

    if hi_len == 5:
        columns = ["H", "K", "L", "I", "SIGI"]
    elif hi_len == 7:
        columns = ["H", "K", "L", "I(+)", "SIGI(+)", "I(-)", "SIGI(-)"]
    else:
        columns = False

    return columns

def get_scalepack_no_merge_columns(datafile):
    """
    Returns columns for a scalepack no merge original index file
    """

    columns = ["H", "K", "L", "H0", "K0", "L0", "BATCH", "UNK", "UNK", "UNK", "I", "SIGI"]

    return columns

def get_xds_ascii_columns(datafile):
    """
    Look at an xds_ascii file and return an array of columns

    datafile should be iotbx.reflection_file_reader.any_reflection_file
    """

    columns = []

    inlines = open(datafile.file_name(), "r").read(6144)
    for line in inlines.split("\n"):
        if line.startswith("!ITEM_"):
            columns.append(line.replace("!ITEM_", "").split("=")[0])
        elif not line.startswith("!"):
            break

    return columns

def get_xds_integrate_hkl_columns(datafile):
    """
    Look at an xds_integrate_hkl file and return an array of columns

    datafile should be iotbx.reflection_file_reader.any_reflection_file
    """

    columns = []
    next_line = False
    inlines = open(datafile.file_name(), "r").read(2048)
    for line in inlines.split("\n"):
        if line.startswith("!H,K,L") or next_line:
            columns += line[1:].strip().rstrip(",").split(",")
            if next_line:
                next_line = False
                break
            else:
                next_line = True
        elif line.startswith("!END_OF_HEADER"):
            break

    return columns

def get_rapd_file_type(file_name):
    """Returns RAPD-defined file type, if known. False if not"""

    # Read in input file
    reflection_file = reflection_file_reader.any_reflection_file(file_name=\
                      file_name)

    columns = get_columns(reflection_file)
    cctbx_file_type = reflection_file.file_type()

    # Look for signature
    for rapd_file_type, signature in RAPD_FILE_SIGNATURES.iteritems():
        signature_file_type, cols = signature
        if cctbx_file_type == signature_file_type and columns == cols:
            break
    else:
        rapd_file_type = False

    return rapd_file_type

def replace_suffix(input_file_name, input_rapd_type, output_rapd_type):
    """Replace a file suffix with as much of a RAPD suffix as possible"""

    # Full suffix replacement
    # print RAPD_FILE_SUFFIXES[input_rapd_type]
    # print RAPD_FILE_SUFFIXES[output_rapd_type]
    if input_file_name.endswith(RAPD_FILE_SUFFIXES[input_rapd_type]):
        output_file_name = input_file_name.replace(RAPD_FILE_SUFFIXES[input_rapd_type],
                                                   RAPD_FILE_SUFFIXES[output_rapd_type])
    # Just post "." suffix replacement
    else:
        output_file_name = ".".join(
            input_file_name.split(".")[:-1]+[RAPD_FILE_SUFFIXES[output_rapd_type]]
            )

    return output_file_name

#
# FILE CONVERSION METHODS
#
def convert_mergable_mtz_to_minimal_refl_anom_mtz(source_file_name,
                                                  dest_file_name=False,
                                                  overwrite=True,
                                                  clean=True):
    """
    Convert reflection file

    mergable_mtz - a standard RAPD file format of integrated X-ray intensities
    minimal_refl_anom_mtz - minimal mtz file containing anomalous intensities

    Keyword arguments
    -----------------
    source_file_name - file to be converted
    dest_file_name - name of converted file. RAPD will name a file appropriately if this is False
                     (default = False)
    overwrite - converted file will overwrite previous if preset (default = True)
    clean - remove intermediate files if True (default = True)
    """

    source_format = "mergable_mtz"
    dest_format = "minimal_refl_anom_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Merge the data
    aimless_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd = "aimless hklin %s hklout %s" % (source_file_name, aimless_file)
    aimless_proc = subprocess.Popen([cmd, "<<eof"],
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=True)
    aimless_proc.stdin.write("ANOMALOUS ON\n")
    aimless_proc.stdin.write("SCALES CONSTANT\n")
    aimless_proc.stdin.write("SDCORRECTION NOREFINE FULL 1 0 0 PARTIAL 1 0 0\n")
    aimless_proc.stdin.write("CYCLES 0\n")
    aimless_proc.stdin.write("END\n")
    aimless_proc.stdin.write("eof\n")
    _, _ = aimless_proc.communicate()

    # Prune away unwanted columns
    cmd = "cad hklin1 %s hklout %s" % (aimless_file, dest_file_name)
    cad_proc = subprocess.Popen([cmd, "<<eof"],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True)
    cad_proc.stdin.write("LABIN FILE 1 E1=IMEAN E2=SIGIMEAN E3=I(+) E4=SIGI(+) E5=I(-) \
E6=SIGI(-)\n")
    cad_proc.stdin.write("SORT H K L\n")
    cad_proc.stdin.write("END\n")
    cad_proc.stdin.write("eof\n")
    cad_proc.wait()

    # Clean up
    if clean:
        files_to_remove = (
            aimless_file,
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_mergable_mtz_to_minimal_mergeable_mtz(source_file_name,
                                                  dest_file_name=False,
                                                  overwrite=True,
                                                  clean=True):
    """
    Convert reflection file

    mergable_mtz - a standard RAPD file format of integrated X-ray intensities
    minimal_mergeable_mtz - minimal mergeable mtz file containing intensities and batch information

    Keyword arguments
    -----------------
    source_file_name - file to be converted
    dest_file_name - name of converted file. RAPD will name a file appropriately if this is False
                     (default = False)
    overwrite - converted file will overwrite previous if preset (default = True)
    clean - remove intermediate files if True (default = True)
    """

    source_format = "mergable_mtz"
    dest_format = "minimal_mergeable_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Prune away unwanted columns
    cmd = "mtzutils hklin1 %s hklout %s" % (source_file_name, dest_file_name)
    mtzutils_proc = subprocess.Popen([cmd, "<<eof"],
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     shell=True)
    mtzutils_proc.stdin.write("INCLUDE M/ISYM BATCH I SIGI\n")
    mtzutils_proc.stdin.write("EXCLUDE FRACTIONCALC XDET YDET ROT LP FLAG\n")
    mtzutils_proc.stdin.write("END\n")
    mtzutils_proc.stdin.write("eof\n")
    mtzutils_proc.wait()

    return dest_file_name

def convert_mergable_mtz_to_minimal_refl_mtz(source_file_name,
                                             dest_file_name=False,
                                             overwrite=True,
                                             clean=True):
    """Convert file"""

    source_format = "mergable_mtz"
    dest_format = "minimal_refl_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Merge the data
    aimless_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd = "aimless hklin %s hklout %s" % (source_file_name, aimless_file)
    aimless_proc = subprocess.Popen([cmd, "<<eof"],
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=True)
    aimless_proc.stdin.write("ANOMALOUS OFF\n")
    aimless_proc.stdin.write("SCALES CONSTANT\n")
    aimless_proc.stdin.write("SDCORRECTION NOREFINE FULL 1 0 0 PARTIAL 1 0 0\n")
    aimless_proc.stdin.write("CYCLES 0\n")
    aimless_proc.stdin.write("END\n")
    aimless_proc.stdin.write("eof\n")
    _, _ = aimless_proc.communicate()

    # Prune away unwanted columns
    cmd = "cad hklin1 %s hklout %s" % (aimless_file, dest_file_name)
    cad_proc = subprocess.Popen([cmd, "<<eof"],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True)
    cad_proc.stdin.write("LABIN FILE 1 E1=IMEAN E2=SIGIMEAN\n")
    cad_proc.stdin.write("SORT H K L\n")
    cad_proc.stdin.write("END\n")
    cad_proc.stdin.write("eof\n")
    cad_proc.wait()

    # Clean up
    if clean:
        files_to_remove = (
            aimless_file,
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_mergable_mtz_to_minimal_rfree_mtz(source_file_name,
                                              dest_file_name=False,
                                              overwrite=True,
                                              clean=True):
    """Convert file"""

    source_format = "mergable_mtz"
    dest_format = "minimal_rfree_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Merge the data
    aimless_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd = "aimless hklin %s hklout %s" % (source_file_name, aimless_file)
    aimless_proc = subprocess.Popen([cmd, "<<eof"],
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=True)
    aimless_proc.stdin.write("ANOMALOUS OFF\n")
    aimless_proc.stdin.write("SCALES CONSTANT\n")
    aimless_proc.stdin.write("SDCORRECTION NOREFINE FULL 1 0 0 PARTIAL 1 0 0\n")
    aimless_proc.stdin.write("CYCLES 0\n")
    aimless_proc.stdin.write("END\n")
    aimless_proc.stdin.write("eof\n")
    _, _ = aimless_proc.communicate()

    # Truncate the data
    truncate_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd = "truncate hklin %s hklout %s" % (aimless_file, truncate_file)
    truncate_proc = subprocess.Popen([cmd, "<<eof"],
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     shell=True)
    truncate_proc.stdin.write("END\n")
    truncate_proc.stdin.write("eof\n")
    _, _ = truncate_proc.communicate()

    # Set the free R flag
    freer_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd = "freerflag hklin %s hklout %s" % (truncate_file, freer_file)
    freerflag_proc = subprocess.Popen([cmd, "<<eof"],
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      shell=True)
    freerflag_proc.stdin.write("END\n")
    freerflag_proc.stdin.write("eof\n")
    freerflag_proc.wait()

    # Prune away unwanted columns
    cmd = "cad hklin1 %s hklout %s" % (freer_file, dest_file_name)
    cad_proc = subprocess.Popen([cmd, "<<eof"],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True)
    cad_proc.stdin.write("LABIN FILE 1 E1=FreeR_flag E2=IMEAN E3=SIGIMEAN E4=F E5=SIGF\n")
    cad_proc.stdin.write("SORT H K L\n")
    cad_proc.stdin.write("END\n")
    cad_proc.stdin.write("eof\n")
    cad_proc.wait()

    # Clean up
    if clean:
        files_to_remove = (
            aimless_file,
            truncate_file,
            freer_file,
            "ANOMPLOT",
            "CORRELPLOT",
            "NORMPLOT",
            "ROGUES",
            "ROGUEPLOT",
            "SCALES"
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_mergable_mtz_to_rfree_mtz(source_file_name,
                                      dest_file_name=False,
                                      overwrite=True,
                                      clean=True):
    """Convert file"""

    source_format = "mergable_mtz"
    dest_format = "rfree_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Merge the data
    aimfile = next(tempfile._get_candidate_names()) + ".mtz"
    aimless_proc = subprocess.Popen(["aimless",
                                     "hklin",
                                     source_file_name,
                                     "hklout",
                                     aimfile
                                    ],
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

    aimless_proc.stdin.write("anomalous on\n")
    aimless_proc.stdin.write("scales constant\n")
    aimless_proc.stdin.write("sdcorrection norefine full 1 0 0 partial 1 0 0\n")
    aimless_proc.stdin.write("cycles 0\n")
    aimless_proc.stdin.write("END\n")
    aimless_proc.wait()

    # Truncate the data
    truncfile = next(tempfile._get_candidate_names()) + ".mtz"
    truncate_proc = subprocess.Popen(["truncate",
                                      "hklin",
                                      aimfile,
                                      "hklout",
                                      truncfile,
                                     ],
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
    truncate_proc.stdin.write("END\n")
    stdout, stderr = truncate_proc.communicate()

    # Set the free R flag
    freerflag_proc = subprocess.Popen(["freerflag",
                                       "hklin",
                                       truncfile,
                                       "hklout",
                                       dest_file_name
                                      ],
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)

    freerflag_proc.stdin.write("END\n")
    freerflag_proc.wait()

    # Clean up
    if clean:
        files_to_remove = (
            aimfile,
            truncfile,
            "ANOMPLOT",
            "CORRELPLOT",
            "NORMPLOT",
            "ROGUES",
            "ROGUEPLOT",
            "SCALES"
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_mergable_mtz_to_scalepack_anomalous(source_file_name,
                                                dest_file_name=False,
                                                overwrite=True,
                                                clean=True):
    """Convert file"""

    source_format = "mergable_mtz"
    dest_format = "scalepack_anomalous"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Convert mergable_mtz to rfree_mtz
    rfree_file = next(tempfile._get_candidate_names()) + ".mtz"
    convert_mergable_mtz_to_rfree_mtz(source_file_name=source_file_name,
                                      dest_file_name=rfree_file,
                                      overwrite=overwrite,
                                      clean=clean)


    # Convert the rfree_mtz to scalepack_anomalous
    mtz2various_proc = subprocess.Popen(["mtz2various",
                                         "hklin",
                                         rfree_file,
                                         "hklout",
                                         dest_file_name],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

    mtz2various_proc.stdin.write("OUTPUT SCALEPACK\n")
    mtz2various_proc.stdin.write("labin I(+)=I(+) SIGI(+)=SIGI(+) I(-)=I(-) \
    SIGI(-)=SIGI(-)\n")
    mtz2various_proc.stdin.write("END\n")
    # mtz2various_proc.stdin.write()
    mtz2various_proc.wait()

    # Fix some known converted scalepack problems
    fix_mtz_to_sca(dest_file_name)

    # Clean up
    if clean:
        files_to_remove = (
            rfree_file,
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_mergable_mtz_to_scalepack_merge(source_file_name,
                                            dest_file_name=False,
                                            overwrite=True,
                                            clean=True):
    """Convert file"""

    source_format = "mergable_mtz"
    dest_format = "scalepack_merge"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Convert mergable_mtz to rfree_mtz
    rfree_file = next(tempfile._get_candidate_names()) + ".mtz"
    convert_mergable_mtz_to_rfree_mtz(source_file_name=source_file_name,
                                      dest_file_name=rfree_file,
                                      overwrite=overwrite,
                                      clean=clean)

    # Convert the rfree_mtz to scalepack_anomalous
    mtz2various_proc = subprocess.Popen(["mtz2various",
                                         "hklin",
                                         rfree_file,
                                         "hklout",
                                         dest_file_name],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

    mtz2various_proc.stdin.write("OUTPUT SCALEPACK\n")
    mtz2various_proc.stdin.write("labin I=IMEAN SIGI=SIGIMEAN\n")
    mtz2various_proc.stdin.write("END\n")
    # mtz2various_proc.stdin.write()
    mtz2various_proc.wait()

    # Fix some known converted scalepack problems
    fix_mtz_to_sca(dest_file_name)

    # Clean up
    if clean:
        files_to_remove = (
            rfree_file,
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_minimal_refl_anom_mtz_to_minimal_refl_mtz(source_file_name,
                                                      dest_file_name=False,
                                                      overwrite=True,
                                                      clean=True):
    """Convert file"""

    source_format = "minimal_refl_anom_mtz"
    dest_format = "minimal_refl_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Prune away unwanted columns
    cmd = "cad hklin1 %s hklout %s" % (source_file_name, dest_file_name)
    cad_proc = subprocess.Popen([cmd, "<<eof"],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True)
    cad_proc.stdin.write("LABIN FILE 1 E1=IMEAN E2=SIGIMEAN\n")
    cad_proc.stdin.write("SORT H K L\n")
    cad_proc.stdin.write("END\n")
    cad_proc.stdin.write("eof\n")
    cad_proc.wait()

    return dest_file_name

def convert_minimal_refl_anom_mtz_to_minimal_rfree_mtz(source_file_name,
                                                       dest_file_name=False,
                                                       overwrite=True,
                                                       clean=True):
    """Convert file"""

    source_format = "minimal_refl_anom_mtz"
    dest_format = "minimal_rfree_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Truncate the data
    truncate_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd = "truncate hklin %s hklout %s" % (source_file_name, truncate_file)
    truncate_proc = subprocess.Popen([cmd, "<<eof"],
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     shell=True)
    truncate_proc.stdin.write("END\n")
    truncate_proc.stdin.write("eof\n")
    _, _ = truncate_proc.communicate()

    # Sort the file and prune columns
    cad_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd = "cad hklin1 %s hklout %s" % (truncate_file, cad_file)
    cad_proc = subprocess.Popen([cmd, "<<eof"],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True)

    cad_proc.stdin.write("LABIN FILE 1 E1=IMEAN E2=SIGIMEAN E3=F E4=SIGF\n")
    cad_proc.stdin.write("SORT H K L\n")
    cad_proc.stdin.write("END\n")
    cad_proc.stdin.write("eof\n")
    cad_proc.wait()

    # Set the free R flag
    cmd = "freerflag hklin %s hklout %s" % (cad_file, dest_file_name)
    freerflag_proc = subprocess.Popen([cmd, "<<eof"],
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      shell=True)
    freerflag_proc.stdin.write("END\n")
    freerflag_proc.stdin.write("eof\n")
    freerflag_proc.wait()

    # Clean up
    if clean:
        files_to_remove = (
            truncate_file,
            cad_file,
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_minimal_refl_anom_mtz_to_rfree_mtz(source_file_name,
                                               dest_file_name=False,
                                               overwrite=True,
                                               clean=True):
    """Convert file"""

    source_format = "minimal_refl_anom_mtz"
    dest_format = "rfree_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Truncate the data
    truncate_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd = "truncate hklin %s hklout %s" % (source_file_name, truncate_file)
    truncate_proc = subprocess.Popen([cmd, "<<eof"],
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     shell=True)
    truncate_proc.stdin.write("END\n")
    truncate_proc.stdin.write("eof\n")
    _, _ = truncate_proc.communicate()

    # Set the free R flag
    cmd = "freerflag hklin %s hklout %s" % (truncate_file, dest_file_name)
    freerflag_proc = subprocess.Popen([cmd, "<<eof"],
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      shell=True)
    freerflag_proc.stdin.write("END\n")
    freerflag_proc.stdin.write("eof\n")
    freerflag_proc.wait()

    # Clean up
    if clean:
        files_to_remove = (
            truncate_file,
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_minimal_refl_anom_mtz_to_scalepack_anomalous(source_file_name,
                                                         dest_file_name=False,
                                                         overwrite=True,
                                                         clean=True):
    """Convert file"""

    source_format = "minimal_refl_anom_mtz"
    dest_format = "scalepack_anomalous"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Convert
    cmd = "mtz2various hklin %s hklout %s" % (source_file_name, dest_file_name)
    mtz2various_proc = subprocess.Popen([cmd, "<<eof"],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=True)

    mtz2various_proc.stdin.write("OUTPUT SCALEPACK\n")
    mtz2various_proc.stdin.write("labin I(+)=I(+) SIGI(+)=SIGI(+) I(-)=I(-) SIGI(-)=SIGI(-)\n")
    mtz2various_proc.stdin.write("END\n")
    mtz2various_proc.stdin.write("eof\n")
    mtz2various_proc.wait()

    # Fix some known converted scalepack problems
    fix_mtz_to_sca(dest_file_name)

    return dest_file_name

def convert_minimal_refl_anom_mtz_to_scalepack_merge(source_file_name,
                                                     dest_file_name=False,
                                                     overwrite=True,
                                                     clean=True):
    """Convert file"""

    source_format = "minimal_refl_anom_mtz"
    dest_format = "scalepack_merge"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Convert
    cmd = "mtz2various hklin %s hklout %s" % (source_file_name, dest_file_name)
    mtz2various_proc = subprocess.Popen([cmd, "<<eof"],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=True)

    mtz2various_proc.stdin.write("OUTPUT SCALEPACK\n")
    mtz2various_proc.stdin.write("labin I=IMEAN SIGI=SIGIMEAN\n")
    mtz2various_proc.stdin.write("END\n")
    mtz2various_proc.stdin.write("eof\n")
    mtz2various_proc.wait()

    # Fix some known converted scalepack problems
    fix_mtz_to_sca(dest_file_name)

    return dest_file_name

def convert_minimal_refl_mtz_to_scalepack_merge(source_file_name,
                                                dest_file_name=False,
                                                overwrite=True,
                                                clean=True):
    """Convert file"""

    source_format = "minimal_refl_anom_mtz"
    dest_format = "scalepack_merge"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Convert
    cmd = "mtz2various hklin %s hklout %s" % (source_file_name, dest_file_name)
    mtz2various_proc = subprocess.Popen([cmd, "<<eof"],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=True)

    mtz2various_proc.stdin.write("OUTPUT SCALEPACK\n")
    mtz2various_proc.stdin.write("labin I=IMEAN SIGI=SIGIMEAN\n")
    mtz2various_proc.stdin.write("END\n")
    mtz2various_proc.stdin.write("eof\n")
    mtz2various_proc.wait()

    # Fix some known converted scalepack problems
    fix_mtz_to_sca(dest_file_name)

    return dest_file_name

def convert_minimal_rfree_mtz_to_scalepack_merge(source_file_name,
                                                 dest_file_name=False,
                                                 overwrite=True,
                                                 clean=True):
    "Wraps file convert"
    return convert_minimal_refl_mtz_to_scalepack_merge(source_file_name,
                                                       dest_file_name,
                                                       overwrite,
                                                       clean)

def convert_rfree_mtz_to_scalepack_anomalous(source_file_name,
                                             dest_file_name=False,
                                             overwrite=True,
                                             clean=True):
    """Convert file"""

    source_format = "rfree_mtz"
    dest_format = "scalepack_anomalous"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    mtz2various_proc = subprocess.Popen(["mtz2various",
                                         "hklin",
                                         source_file_name,
                                         "hklout",
                                         dest_file_name],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

    mtz2various_proc.stdin.write("OUTPUT SCALEPACK\n")
    mtz2various_proc.stdin.write("labin I(+)=I(+) SIGI(+)=SIGI(+) I(-)=I(-) SIGI(-)=SIGI(-)\n")
    mtz2various_proc.stdin.write("END\n")
    # mtz2various_proc.stdin.write()
    mtz2various_proc.wait()

    # Fix some known converted scalepack problems
    fix_mtz_to_sca(dest_file_name)

    return dest_file_name

def convert_rfree_mtz_to_scalepack_merge(source_file_name,
                                         dest_file_name=False,
                                         overwrite=True,
                                         clean=True):
    """Convert file"""

    source_format = "rfree_mtz"
    dest_format = "scalepack_merge"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    mtz2various_proc = subprocess.Popen(["mtz2various",
                                         "hklin",
                                         source_file_name,
                                         "hklout",
                                         dest_file_name],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

    mtz2various_proc.stdin.write("OUTPUT SCALEPACK\n")
    mtz2various_proc.stdin.write("labin I=IMEAN SIGI=SIGIMEAN\n")
    mtz2various_proc.stdin.write("END\n")
    # mtz2various_proc.stdin.write()
    mtz2various_proc.wait()

    # Fix some known converted scalepack problems
    fix_mtz_to_sca(dest_file_name)

    return dest_file_name

def convert_scalepack_anomalous_to_minimal_refl_anom_mtz(source_file_name,
                                                         dest_file_name=False,
                                                         overwrite=False,
                                                         clean=True):
    """Convert file"""

    source_format = "scalepack_anomalous"
    dest_format = "minimal_refl_anom_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Convert the file to mtz
    unsorted_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd =  "scalepack2mtz hklin %s hklout %s" % (source_file_name, unsorted_file)
    scalepack2mtz_proc = subprocess.Popen([cmd, "<<eof"],
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          shell=True
                                         )
    scalepack2mtz_proc.stdin.write("ANOMALOUS YES\n")
    scalepack2mtz_proc.stdin.write("END\n")
    scalepack2mtz_proc.stdin.write("eof\n")
    scalepack2mtz_proc.wait()

    # Sort the file into correct CCP4 format
    cmd = "cad hklin1 %s hklout %s" % (unsorted_file, dest_file_name)
    cad_proc = subprocess.Popen([cmd, "<<eof"],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True)

    cad_proc.stdin.write("LABIN FILE 1 ALL\n")
    cad_proc.stdin.write("SORT H K L\n")
    cad_proc.stdin.write("END\n")
    cad_proc.stdin.write("eof\n")
    cad_proc.wait()

    # Clean up
    if clean:
        files_to_remove = (
            unsorted_file,
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_scalepack_anomalous_to_minimal_refl_mtz(source_file_name,
                                                    dest_file_name=False,
                                                    overwrite=False,
                                                    clean=True):
    """Convert file"""

    source_format = "scalepack_anomalous"
    dest_format = "minimal_refl_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Convert the file to mtz
    unsorted_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd =  "scalepack2mtz hklin %s hklout %s" % (source_file_name,
                                                       unsorted_file)
    scalepack2mtz_proc = subprocess.Popen([cmd, "<<eof"],
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          shell=True
                                         )
    scalepack2mtz_proc.stdin.write("ANOMALOUS YES\n")
    scalepack2mtz_proc.stdin.write("END\n")
    scalepack2mtz_proc.stdin.write("eof\n")
    scalepack2mtz_proc.wait()

    # Sort the file into correct CCP4 format
    cmd = "cad hklin1 %s hklout %s" % (unsorted_file, dest_file_name)
    cad_proc = subprocess.Popen([cmd, "<<eof"],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True)

    cad_proc.stdin.write("LABIN FILE 1 E1=IMEAN E2=SIGIMEAN\n")
    cad_proc.stdin.write("SORT H K L\n")
    cad_proc.stdin.write("END\n")
    cad_proc.stdin.write("eof\n")
    cad_proc.wait()

    # Clean up
    if clean:
        files_to_remove = (
            unsorted_file,
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_scalepack_anomalous_to_rfree_mtz(source_file_name,
                                             dest_file_name=False,
                                             overwrite=False,
                                             clean=True):
    """Convert file"""

    source_format = "scalepack_anomalous"
    dest_format = "rfree_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Convert the file to mtz
    unsorted_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd =  "scalepack2mtz hklin %s hklout %s" % (source_file_name, unsorted_file)
    scalepack2mtz_proc = subprocess.Popen([cmd, "<<eof"],
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          shell=True
                                         )
    scalepack2mtz_proc.stdin.write("ANOMALOUS YES\n")
    scalepack2mtz_proc.stdin.write("END\n")
    scalepack2mtz_proc.stdin.write("eof\n")
    scalepack2mtz_proc.wait()

    # Truncate the data
    truncate_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd = "truncate hklin %s hklout %s" % (unsorted_file, truncate_file)
    truncate_proc = subprocess.Popen([cmd, "<<eof"],
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     shell=True)
    truncate_proc.stdin.write("END\n")
    truncate_proc.stdin.write("eof\n")
    stdout, stderr = truncate_proc.communicate()

    # Sort the file into correct CCP4 format
    cmd = "cad hklin1 %s hklout %s" % (truncate_file, dest_file_name)
    cad_proc = subprocess.Popen([cmd, "<<eof"],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True)

    cad_proc.stdin.write("LABIN FILE 1 ALL\n")
    cad_proc.stdin.write("SORT H K L\n")
    cad_proc.stdin.write("END\n")
    cad_proc.stdin.write("eof\n")
    cad_proc.wait()

    # Clean up
    if clean:
        files_to_remove = (
            unsorted_file,
            truncate_file,
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_scalepack_anomalous_to_scalepack_merge(source_file_name,
                                                   dest_file_name=False,
                                                   overwrite=False,
                                                   clean=True):
    """Convert file"""

    source_format = "scalepack_anomalous"
    dest_format = "scalepack_merge"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Convert the file to mtz
    unsorted_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd =  "scalepack2mtz hklin %s hklout %s" % (source_file_name,
                                                       unsorted_file)
    scalepack2mtz_proc = subprocess.Popen([cmd, "<<eof"],
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          shell=True
                                         )
    scalepack2mtz_proc.stdin.write("ANOMALOUS YES\n")
    scalepack2mtz_proc.stdin.write("END\n")
    scalepack2mtz_proc.stdin.write("eof\n")
    scalepack2mtz_proc.wait()

    # Sort the file into correct CCP4 format
    cad_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd = "cad hklin1 %s hklout %s" % (unsorted_file, cad_file)
    cad_proc = subprocess.Popen([cmd, "<<eof"],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True)

    cad_proc.stdin.write("LABIN FILE 1 E1=IMEAN E2=SIGIMEAN\n")
    cad_proc.stdin.write("SORT H K L\n")
    cad_proc.stdin.write("END\n")
    cad_proc.stdin.write("eof\n")
    cad_proc.wait()

    # Convert to .sca file
    convert_minimal_refl_mtz_to_scalepack_merge(cad_file,
                                                dest_file_name,
                                                overwrite,
                                                clean)

    # Clean up
    if clean:
        files_to_remove = (
            unsorted_file,
            cad_file
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_scalepack_merge_to_minimal_refl_mtz(source_file_name,
                                                dest_file_name=False,
                                                overwrite=False,
                                                clean=True):
    "Convert file"

    source_format = "scalepack_merge"
    dest_format = "minimal_refl_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Convert the file to mtz
    unsorted_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd =  "scalepack2mtz hklin %s hklout %s" % (source_file_name,
                                                       unsorted_file)
    scalepack2mtz_proc = subprocess.Popen([cmd, "<<eof"],
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          shell=True
                                         )
    scalepack2mtz_proc.stdin.write("ANOMALOUS NO\n")
    scalepack2mtz_proc.stdin.write("END\n")
    scalepack2mtz_proc.stdin.write("eof\n")
    scalepack2mtz_proc.wait()

    # Sort the file into correct CCP4 format
    cmd = "cad hklin1 %s hklout %s" % (unsorted_file, dest_file_name)
    cad_proc = subprocess.Popen([cmd, "<<eof"],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True)

    cad_proc.stdin.write("LABIN FILE 1 E1=IMEAN E2=SIGIMEAN\n")
    cad_proc.stdin.write("SORT H K L\n")
    cad_proc.stdin.write("END\n")
    cad_proc.stdin.write("eof\n")
    cad_proc.wait()

    # Clean up
    if clean:
        files_to_remove = (
            unsorted_file,
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_scalepack_merge_to_minimal_rfree_mtz(source_file_name,
                                                 dest_file_name=False,
                                                 overwrite=False,
                                                 clean=True):
    "Convert file"

    source_format = "scalepack_merge"
    dest_format = "minimal_rfree_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Convert the file to mtz
    unsorted_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd =  "scalepack2mtz hklin %s hklout %s" % (source_file_name,
                                                       unsorted_file)
    scalepack2mtz_proc = subprocess.Popen([cmd, "<<eof"],
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          shell=True
                                         )
    scalepack2mtz_proc.stdin.write("ANOMALOUS NO\n")
    scalepack2mtz_proc.stdin.write("END\n")
    scalepack2mtz_proc.stdin.write("eof\n")
    scalepack2mtz_proc.wait()

    # Truncate the data
    truncate_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd = "truncate hklin %s hklout %s" % (unsorted_file, truncate_file)
    truncate_proc = subprocess.Popen([cmd, "<<eof"],
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     shell=True)
    truncate_proc.stdin.write("END\n")
    truncate_proc.stdin.write("eof\n")
    stdout, stderr = truncate_proc.communicate()

    # Sort the file into correct CCP4 format
    cad_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd = "cad hklin1 %s hklout %s" % (truncate_file, cad_file)
    cad_proc = subprocess.Popen([cmd, "<<eof"],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True)
    cad_proc.stdin.write("LABIN FILE 1 E1=IMEAN E2=SIGIMEAN E3=F E4=SIGF\n")
    cad_proc.stdin.write("SORT H K L\n")
    cad_proc.stdin.write("END\n")
    cad_proc.stdin.write("eof\n")
    cad_proc.wait()

    # Set the free R flag
    cmd = "freerflag hklin %s hklout %s" % (cad_file, dest_file_name)
    freerflag_proc = subprocess.Popen([cmd, "<<eof"],
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      shell=True)
    freerflag_proc.stdin.write("END\n")
    freerflag_proc.stdin.write("eof\n")
    freerflag_proc.wait()

    # Clean up
    if clean:
        files_to_remove = (
            unsorted_file,
            truncate_file,
            cad_file
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_scalepack_no_merge_original_index_to_minimal_mergeable_mtz(
        source_file_name,
        dest_file_name=False,
        cell=(90, 90, 90, 90, 90, 90),
        overwrite=False,
        clean=True):
    """Convert file"""

    source_format = "scalepack_no_merge_original_index"
    dest_format = "minimal_mergeable_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Convert the file to mtz
    # pointless_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd = "pointless -c scain %s hklout %s" % (source_file_name, dest_file_name)
    pointless_proc = subprocess.Popen([cmd, "<<eof"],
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      shell=True
                                     )
    pointless_proc.stdin.write("CELL %f %f %f %f %f %f \n" % cell)
    pointless_proc.stdin.write("END\n")
    pointless_proc.stdin.write("eof\n")
    pointless_proc.wait()

    return dest_file_name

def convert_xds_corrected_to_mergable_mtz(source_file_name,
                                          dest_file_name=False,
                                          overwrite=False,
                                          clean=True):
    """Convert file"""

    source_format = "xds_corrected"
    dest_format = "mergable_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    pointless_proc = subprocess.Popen(["pointless",
                                       "-c",
                                       "xdsin",
                                       source_file_name,
                                       "hklout",
                                       dest_file_name
                                      ],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE
                                     )
    pointless_proc.wait()

    return dest_file_name

def convert_xds_corrected_to_minimal_mergeable_mtz(source_file_name,
                                                   dest_file_name=False,
                                                   overwrite=False,
                                                   clean=True):
    """Convert file"""

    source_format = "xds_corrected"
    dest_format = "minimal_mergeable_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Import using pointless
    pointless_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd = "pointless -c xdsin %s hklout %s" % (source_file_name, pointless_file)
    pointless_proc = subprocess.Popen([cmd, "<<eof"],
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      shell=True
                                     )
    pointless_proc.stdin.write("END\n")
    pointless_proc.stdin.write("eof\n")
    pointless_proc.wait()

    # Prune away unwanted columns
    cmd = "mtzutils hklin1 %s hklout %s" % (pointless_file, dest_file_name)
    mtzutils_proc = subprocess.Popen([cmd, "<<eof"],
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     shell=True)
    mtzutils_proc.stdin.write("INCLUDE M/ISYM BATCH I SIGI\n")
    mtzutils_proc.stdin.write("EXCLUDE FRACTIONCALC XDET YDET ROT LP FLAG\n")
    mtzutils_proc.stdin.write("END\n")
    mtzutils_proc.stdin.write("eof\n")
    mtzutils_proc.wait()

    # Clean up
    if clean:
        files_to_remove = (
            pointless_file,
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_xds_corrected_to_rfree_mtz(source_file_name,
                                       dest_file_name=False,
                                       overwrite=False,
                                       clean=True):
    """Convert file"""

    source_format = "xds_corrected"
    dest_format = "rfree_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Convert to mergable
    mergable_file = next(tempfile._get_candidate_names()) + ".mtz"
    pointless_proc = subprocess.Popen(["pointless",
                                       "-c",
                                       "xdsin",
                                       source_file_name,
                                       "hklout",
                                       mergable_file
                                      ],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE
                                     )
    pointless_proc.wait()

    # Convert mergable to rfree
    dest_file_name = convert_mergable_mtz_to_rfree_mtz(source_file_name=mergable_file,
                                                       dest_file_name=dest_file_name,
                                                       overwrite=overwrite,
                                                       clean=clean)

    # Clean up
    if clean:
        files_to_remove = (
            mergable_file,
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_xds_integrated_to_mergable_mtz(source_file_name,
                                           dest_file_name=False,
                                           overwrite=False,
                                           clean=True):
    """Convert file"""

    source_format = "xds_integrated"
    dest_format = "mergeable_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    pointless_proc = subprocess.Popen(["pointless",
                                       "-c",
                                       "xdsin",
                                       source_file_name,
                                       "hklout",
                                       dest_file_name
                                      ],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE
                                     )
    pointless_proc.wait()

    return dest_file_name

def convert_xds_integrated_to_minimal_mergeable_mtz(source_file_name,
                                                    dest_file_name=False,
                                                    overwrite=False,
                                                    clean=True):
    """Convert file"""

    source_format = "xds_integrated"
    dest_format = "minimal_mergeable_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Import using pointless
    pointless_file = next(tempfile._get_candidate_names()) + ".mtz"
    cmd = "pointless -c xdsin %s hklout %s" % (source_file_name, pointless_file)
    pointless_proc = subprocess.Popen([cmd, "<<eof"],
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      shell=True
                                     )
    pointless_proc.stdin.write("END\n")
    pointless_proc.stdin.write("eof\n")
    pointless_proc.wait()

    # Prune away unwanted columns
    cmd = "mtzutils hklin1 %s hklout %s" % (pointless_file, dest_file_name)
    mtzutils_proc = subprocess.Popen([cmd, "<<eof"],
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     shell=True)
    mtzutils_proc.stdin.write("INCLUDE M/ISYM BATCH I SIGI\n")
    mtzutils_proc.stdin.write("EXCLUDE FRACTIONCALC XDET YDET ROT LP FLAG\n")
    mtzutils_proc.stdin.write("END\n")
    mtzutils_proc.stdin.write("eof\n")
    mtzutils_proc.wait()

    # Clean up
    if clean:
        files_to_remove = (
            pointless_file,
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def convert_xds_integrated_to_rfree_mtz(source_file_name,
                                        dest_file_name=False,
                                        overwrite=False,
                                        clean=True):
    """Convert file"""

    source_format = "xds_integrated"
    dest_format = "rfree_mtz"

    # Name of resulting file
    if not dest_file_name:
        dest_file_name = replace_suffix(source_file_name,
                                        source_format,
                                        dest_format)

    # Check if we are going to overwrite
    if os.path.exists(dest_file_name) and not overwrite:
        raise Exception("%s already exists. Exiting" % dest_file_name)

    # Convert to mergable
    mergable_file = next(tempfile._get_candidate_names()) + ".mtz"
    pointless_proc = subprocess.Popen(["pointless",
                                       "-c",
                                       "xdsin",
                                       source_file_name,
                                       "hklout",
                                       mergable_file
                                      ],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE
                                     )
    pointless_proc.wait()

    # Convert mergable to rfree
    dest_file_name = convert_mergable_mtz_to_rfree_mtz(source_file_name=mergable_file,
                                                       dest_file_name=dest_file_name,
                                                       overwrite=overwrite,
                                                       clean=clean)

    # Clean up
    if clean:
        files_to_remove = (
            mergable_file,
        )

        for file_to_remove in files_to_remove:
            os.unlink(file_to_remove)

    return dest_file_name

def get_commandline():
    """Grabs the commandline"""

    # print "get_commandline"

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

"""Hierarchical clustering and merging of data for RAPD plugin"""

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

__created__ = "2012-08-09"
__maintainer__ = "Kay Perry"
__email__ = "kperry@anl.gov"
__status__ = "Development"

# This is an active RAPD plugin
RAPD_PLUGIN = True

# This plugin's type
PLUGIN_TYPE = "HCMERGE"
PLUGIN_SUBTYPE = "EXPERIMENTAL"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "4cba"
VERSION = "1.0.0"

# Standard imports
# import argparse
from collections import OrderedDict
# import datetime
import glob
import json
import logging
import logging.handlers
import multiprocessing
import os
from pprint import pprint
# import pymongo
import re
# import redis
import shutil
import stat
import subprocess
import sys
import time
# import unittest
# import urllib2
import uuid

from multiprocessing import Process, cpu_count
import matplotlib
# Force matplotlib to not use any Xwindows backend.
# Must be called before any other matplotlib/pylab import.
matplotlib.use('Agg')
import hashlib
from itertools import combinations, groupby
from operator import itemgetter

from iotbx import reflection_file_reader
from cctbx import miller
from cctbx.array_family import flex
from cctbx.sgtbx import space_group_symbols
from scipy.cluster.hierarchy import linkage, dendrogram, to_tree
#from hcluster import linkage, dendrogram

import cPickle as pickle  # For storing dicts as pickle files for later use

# RAPD imports
#import plugins.assess_integrated_data.plugin as assess_integrated_data_plugin
#import plugins.assess_integrated_data.commandline as assess_integrated_data_commandline
import plugins.subcontractors.aimless as aimless
import utils.commandline_utils as commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
import utils.credits as credits
import utils.text as rtext
import info

# Software dependencies
VERSIONS = {
    "aimless": (
        "0.5",
    ),
    "gnuplot": (
        "gnuplot 4.2",
        "gnuplot 5.0",
    ),
    "pointless": (
        "1.10.23",
    )
}

# Threshold for CC - below will be highlighted in the table
HIGHLIGHT_THRESHOLD = 0.9


def tryint(s):
    try:
        return int(s)
    except ValueError:
        return s
     
def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]

def sort_nicely(l):
    """ Sort the given list in the way that humans expect.
    """
    l.sort(key=alphanum_key)

def combine_wrapper(args):
    """
    Wrapper for mutiple arguments passing into combine
    """
    return combine(*args)


def combine(in_files, out_file, cmd_prefix, strict, user_spacegroup):
    """
    Combine XDS_ASCII.HKL files using POINTLESS
    in_files = list of files

    cmd_prefix
    strict
    user_spacegroup
    """
    # print 'HCMerge::Pair-wise joining of %s using pointless.' % str(in_files)
    # logger.debug(
    #     'HCMerge::Pair-wise joining of %s using pointless.' % str(in_files))
    command = []
    command.append('pointless hklout '+out_file +
                   '_pointless.mtz> '+out_file+'_pointless.log <<eof \n')

    for hklin in in_files:
        command.append('hklin '+hklin+' \n')
        # Add ability to do batches
    # Make TOLERANCE huge to accept unit cell variations when in sloppy mode.
    if strict != False:
        command.append('tolerance 1000.0 \n')
    # Add LAUEGROUP if user has chosen a spacegroup
    if user_spacegroup:
        command.append('lauegroup %s \n' % space_group_symbols(
            user_spacegroup).universal_hermann_mauguin())
        command.append('choose spacegroup %s \n' % space_group_symbols(
            user_spacegroup).universal_hermann_mauguin())
    command.append('eof\n')
    # print command
    comfile = open(out_file+'_pointless.sh', 'w')
    comfile.writelines(command)
    comfile.close()
    os.chmod('./'+out_file+'_pointless.sh', 0755)
    # p = subprocess.Popen('qsub -N combine -sync y ./'+out_file+'_pointless.sh',shell=True).wait()
    p = subprocess.Popen(cmd_prefix+' ./'+out_file+'_pointless.sh',
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE).communicate()

    if user_spacegroup == 0:
        # Sub-routine for different point groups
        if (p[0] == '' and p[1] == '') == False:
            pass
            # logger.debug(
            #     'HCMerge::Error Messages from %s pointless log. %s' % (out_file, str(p)))
        if ('WARNING: Cannot combine reflection lists with different symmetry' or 'ERROR: cannot combine files belonging to different crystal systems') in p[1]:
            # logger.debug(
            #     'HCMerge::Different symmetries. Placing %s in best spacegroup.' % str(in_files))
#            print 'HCMerge::Error Messages from %s pointless log. %s' % (out_file, str(p))
        if any(x in p[1] for x in pointless_error):
            print 'HCMerge::Different symmetries. Placing %s in best spacegroup.' % str(in_files)
            for hklin in in_files:
                cmd = []
                cmd.append('pointless hklin '+hklin +
                           ' hklout '+hklin+'> '+hklin+'_p.log \n')
                subprocess.Popen(
                    cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait()
            p = subprocess.Popen(cmd_prefix+' ./'+out_file+'_pointless.sh',
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE).communicate()
            if 'WARNING: Cannot combine reflection lists with different symmetry' in p[1]:
                # logger.debug(
                #     'HCMerge::Still different symmetries after best spacegroup.  Reducing %s to P1.' % str(in_files))
                for hklin in in_files:
                    cmd = []
                    hklout = hklin.rsplit('.', 1)[0]+'p1.mtz'
                    cmd.append('pointless hklin '+hklin+' hklout ' +
                               hklout+'> '+hklin+'_p1.log <<eof \n')
                    cmd.append('lauegroup P1 \n')
                    cmd.append('choose spacegroup P1 \n')
                    cmd.append('eof\n')
                    cmdfile = open('p1_pointless.sh', 'w')
                    cmdfile.writelines(cmd)
                    cmdfile.close()
                    os.chmod('./p1_pointless.sh', 0755)
                    p1 = subprocess.Popen('p1_pointless.sh',
                                          shell=True,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE).communicate()
                command = [x.replace('.mtz', 'p1.mtz')
                           for x in command if any('hklin')]
                comfile = open(out_file+'_pointless.sh', 'w')
                comfile.writelines(command)
                comfile.close()
                p = subprocess.Popen(cmd_prefix+' ./'+out_file+'_pointless.sh',
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE).communicate()

    # Check for known FATAL ERROR of unable to pick LAUE GROUP due to not enough reflections
    plog = open(out_file+'_pointless.log', 'r').readlines()
    for num, line in enumerate(plog):
        if line.startswith('FATAL ERROR'):
            # Go to the next line for error message
            if 'ERROR: cannot decide on which Laue group to select\n' in plog[num+1]:
                # logger.debug(
                #     'HCMerge::Cannot automatically choose a Laue group.  Forcing solution 1.')
                for num, itm in enumerate(command):
                    if itm == 'eof\n':
                        command.insert(num, 'choose solution 1\n')
                        break
            comfile = open(out_file+'_pointless.sh', 'w')
            comfile.writelines(command)
            comfile.close()
            # Run pointless again with new keyword
            p = subprocess.Popen(cmd_prefix+' ./'+out_file+'_pointless.sh',
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE).wait()
            if 'ERROR: cannot combine files belonging to different crystal systems' in plog[num+1]:
                # logger.debug(
                #     'HCMerge:: Forcing P1 due to different crystal systems in %s.' % str(in_files))
                for hklin in in_files:
                    cmd = []
                    hklout = hklin.rsplit('.', 1)[0]+'p1.mtz'
                    cmd.append('pointless hklin '+hklin+' hklout ' +
                               hklout+'> '+hklin+'_p1.log <<eof \n')
                    cmd.append('lauegroup P1 \n')
                    cmd.append('choose spacegroup P1 \n')
                    cmd.append('eof\n')
                    cmdfile = open('p1_pointless.sh', 'w')
                    cmdfile.writelines(cmd)
                    cmdfile.close()
                    os.chmod('./p1_pointless.sh', 0755)
                    p1 = subprocess.Popen('p1_pointless.sh',
                                          shell=True,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE).communicate()
                command = [x.replace('.mtz', 'p1.mtz')
                           for x in command if any('hklin')]
                comfile = open(out_file+'_pointless.sh', 'w')
                comfile.writelines(command)
                comfile.close()
                p = subprocess.Popen(cmd_prefix+' ./'+out_file+'_pointless.sh',
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE).communicate()

def get_cc_aimless(in_file):
    """
    Calculate correlation coefficient (CC) between two datasets which have been combined
    by pointless.  Uses aimless.  Reads in an mtz file.
    """

    # print 'HCMerge::get_cc_aimless::Obtain correlation coefficient from %s' % in_file

    # Read in mtz file
    # mtz_file = reflection_file_reader.any_reflection_file(
    #     file_name=in_file+'_pointless.mtz')
    mtz_file = in_file+'_pointless.mtz'
    log_file = in_file+"_aimless.log"
    com_file = in_file+"_aimless.sh"
    # Create aimless command file
    aimless_lines = ['#!/bin/tcsh\n',
                        'aimless hklin %s hklout %s << eof > %s \n' % (mtz_file, "foo.mtz", log_file),
                        'anomalous on\n',
                        'scales constant\n',
                        'exclude sdmin 2.0\n'
                        'sdcorrection fixsdb noadjust norefine both 1.0 0.0 \n']
#                        'sdcorrection norefine full 1 0 0 partial 1 0 0\n',
#                        'cycles 0\n']
    with open(com_file, "w") as command_file:
        for line in aimless_lines:
            command_file.write(line)
    os.chmod(com_file, stat.S_IRWXU)

    # Run aimless
    cmd = './%s' % com_file
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    stdout, stderr = p.communicate()

    # Parse the file
    # graphs, summary = aimless.parse_aimless(log_file)
    cc_results = aimless.get_cc(log_file)
    # print graphs
    # print cc_results

    # Return CC
    return (in_file, cc_results.get("cc", {}).get((1, 2), 0))


class RapdPlugin(multiprocessing.Process):
    """
    RAPD plugin class

    Command format:
    {
       "command":"hcmerge",
       "directories":
           {
               "work": "hcmerge"                   # Where to perform the work
           },
       "site_parameters": {}                       # Site data
       "preferences": {}                           # Settings for calculations
       "return_address":("127.0.0.1", 50000)       # Location of control process
    }
    """

    results = {}

    def __init__(self, command, tprint=False, logger=False):
        """Initialize the merging processing using agglomerative hierachical clustering process"""

        # If the logging instance is passed in...
        if logger:
            self.logger = logger
        else:
            # Otherwise get the logger Instance
            self.logger = logging.getLogger("RAPDLogger")
            self.logger.debug("__init__")

        # Keep track of start time
        self.start_time = time.time()
        # Store tprint for use throughout
        if tprint:
            self.tprint = tprint
        # Dead end if no tprint passed
        else:
            def func(arg=False, level=False, verbosity=False, color=False):
                pass
            self.tprint = func

        # Some logging
        self.logger.info(command)

        # Store passed-in variables
        self.command = command

        self.dirs = self.command['directories']
        # List of original data files to be merged.  Currently expected to be ASCII.HKL
        self.datasets = self.command['input_data']['datasets']
        self.settings = self.command['preferences']

        # Variables
#        self.cmdline = self.settings['cmdline']
#        self.process_id = self.settings['process_id']

        # Variables for holding filenames and results
        self.data_files = []            # List of data file names
        self.graphs = {}
        self.results = {}
        self.merged_files = []            # List of prefixes for final files.
        # dict for keeping track of file identities
        # Dict will hold prefix as key and pair of file names as value
        self.id_list = OrderedDict()
        self.dirs['data'] = os.path.join(
            self.command['directories']['work'], "DATA")

        # Establish setting defaults
        # Check for agglomerative clustering linkage method
        # Options for linkage are:
        # single: the single/min/nearest algorithm. (alias)
        # complete: the complete/max/farthest algorithm. (alias)
        # average: the average/UPGMA algorithm. (alias)
        # weighted: the weighted/WPGMA algorithm. (alias)
        # centroid: the centroid/UPGMC algorithm. (alias)
        # median: the median/WPGMC algorithm. (alias)
        # ward: the Ward/incremental algorithm. (alias)
        if self.settings.has_key('method'):
            self.method = self.settings['method']
        else:
            self.method = 'complete'

        # Check for cutoff value
        if self.settings.has_key('cutoff'):
            # CC 1/2 value passed in by user
            self.cutoff = self.settings['cutoff']
        else:
            self.cutoff = 0.95

        # Check for filename for merged dataset
        if self.settings.has_key('prefix'):
            self.prefix = self.settings['prefix']
        else:
            self.prefix = 'merged'

        # Check for user-defined spacegroup
        if self.settings.has_key('spacegroup'):
            self.user_spacegroup = self.settings['spacegroup']
        else:
            self.user_spacegroup = 0  # Default to None

        # Check for unit cell.  This is a list.
        if self.settings.has_key('unitcell'):
            self.unitcell = self.settings['unitcell']
        else:
            self.unitcell = False

        # Check for user-defined high resolution cutoff
        if self.settings.has_key('resolution'):
            self.resolution = self.settings['resolution']
        else:
            self.resolution = 0  # Default high resolution limit to 0

        # Check for file cleanup
        if self.settings.has_key('clean'):
            self.clean = self.settings['clean']
        else:
            self.clean = True

        # Check whether to make all clusters or the first one that exceeds the cutoff
        if self.settings.has_key('all_clusters'):
            self.all_clusters = self.settings['all_clusters']
        else:
            self.all_clusters = False

        # Check whether to add labels to the dendrogram
        if self.settings.has_key('labels'):
            self.labels = self.settings['labels']
        else:
            self.labels = False

        # Check whether to start at the beginning or skip to a later step
        if self.settings.has_key('start_point'):
            self.start_point = self.settings['start_point']
        else:
            self.start_point = 'start'

        # Check whether to skip prechecking files during preprocess
        if self.settings.has_key('precheck'):
            self.precheck = self.settings['precheck']
        else:
            self.precheck = True

        # Set resolution for dendrogram image
        if self.settings.has_key('dpi'):
            self.dpi = self.settings['dpi']
        else:
            self.dpi = 100

        # Set running in strict or sloppy mode
        if self.settings.has_key('strict'):
            if self.settings.has_key('spacegroup') or self.settings.has_key('unitcell'):
                self.strict = True
            else:
                self.strict = self.settings['strict']
        else:
            self.strict = False

        # Check on number of processors
        if self.settings.has_key('nproc'):
            self.nproc = self.settings['nproc']
        else:
            try:
                self.nproc = cpu_count()
            # cpu_count() can raise NotImplementedError
            except:
                self.nproc = 1

        # Check on whether job should be run on a cluster
        if self.settings.has_key('cluster_use'):
            if self.settings['cluster_use'] == True:
                self.cmd_prefix = 'qsub -N combine -sync y'
            else:
                self.cmd_prefix = 'sh'
        else:
            self.cmd_prefix = 'sh'

        Process.__init__(self, name="hcmerge")
        self.start()

    def run(self):
        """Execution path of the plugin"""
        # Need to change to work also when data is still collecting.  Currently set up for when
        # data collection is complete.

        # Provide a flag for whether data is still being collected or is complete
        try:
            if self.start_point == 'start':
                self.preprocess()
                self.process()
                self.postprocess()
            else:
                pkl_file = self.datasets
                self.rerun(pkl_file)
        except ValueError, Argument:
            self.logger.error('HCMerge::Failure to Run.')
            self.logger.exception(Argument)

        self.print_credits()

    def preprocess(self):
        """
        Before running the main process
        - change to the current directory
        - copy files to the working directory
        - convert all files to cctbx usable format and save in self
        - test reflection files for acceptable format (XDS and unmerged mtz only)
        - ensure all files are the same format
        """
        self.tprint("Preprocess: Prechecking files")
        self.logger.debug('HCMerge::Prechecking files: %s' %
                          str(self.datasets))

        # Nicely sort datasets
        # sort_nicely(self.datasets)

        if self.precheck:
            # mtz and xds produce different file formats.  Check for type to do duplicate comparison specific to file type.
            types = []
            hashset = {}
            for dataset in self.datasets:
                reflection_file = reflection_file_reader.any_reflection_file(
                    file_name=dataset)
                # Get types for format test
                types.append(reflection_file.file_type())
                hashset[dataset] = hashlib.md5(
                    open(dataset, 'rb').read()).hexdigest()  # hash for duplicates test
                # Test for SCA format
                if reflection_file.file_type() == 'scalepack_no_merge_original_index' and self.unitcell == False:
                    self.logger.error(
                        'HCMerge::Unit Cell required for scalepack no merge original index format.')
                # Test for all the same format
                elif len(set(types)) > 1:
                    self.logger.error('HCMerge::Too Many File Types')
                    raise ValueError(
                        "All files must be the same type and format.")
                # Test reflection files to make sure they have observations
                elif ((reflection_file.file_type() == 'xds_ascii') and (reflection_file.file_content().iobs.size() == 0)):
                    self.logger.error(
                        'HCMerge::%s Reflection Check Failed.  No Observations.' % reflection_file.file_name())
                    raise ValueError(
                        "%s Reflection Check Failed. No Observations." % reflection_file.file_name())
                elif ((reflection_file.file_type() == 'ccp4_mtz') and (reflection_file.file_content().n_reflections() == 0)):
                    self.logger.error(
                        'HCMerge::%s Reflection Check Failed.  No Observations.' % reflection_file.file_name())
                    raise ValueError(
                        "%s Reflection Check Failed. No Observations." % reflection_file.file_name())
                elif (((reflection_file.file_type() == 'scalepack_no_merge_original_index') or (reflection_file.file_type() == 'scalepack_merge')) and (reflection_file.file_content().i_obs.size() == 0)):
                    self.logger.error(
                        'HCMerge::%s Reflection Check Failed.  No Observations.' % reflection_file.file_name())
                    raise ValueError(
                        "%s Reflection Check Failed. No Observations." % reflection_file.file_name())
                # Test reflection file if mtz and make sure it isn't merged by checking for amplitude column
                # Pointless 1.10.23 now accepts merged files, so this check is no longer necessary in sloppy mode.
                elif ((self.strict == True) and (reflection_file.file_type() == 'ccp4_mtz') and ('F' in reflection_file.file_content().column_labels())):
                    self.logger.error(
                        'HCMerge::%s Reflection Check Failed.  Must be unmerged reflections in strict mode.' % reflection_file.file_name())
                    raise ValueError(
                        "%s Reflection Check Failed. Must be unmerged reflections in strict mode." % reflection_file.file_name())
                # Test reflection file if sca and make sure it isn't merged by checking file type
                # Pointless 1.10.23 now accepts merged files, so this check is no longer necessary in sloppy mode.
                elif ((self.strict == True) and reflection_file.file_type() == 'scalepack_merge'):
                    self.logger.error(
                        'HCMerge::Scalepack Merged format. Strict Mode On. Aborted.')
                    raise ValueError(
                        "Scalepack Format. Unmerged reflections required in Strict Mode.")

            # Test reflection files to make sure there are no duplicates
            combos_temp = self.make_combinations(self.datasets, 2)
            for combo in combos_temp:
                if hashset[combo[0]] == hashset[combo[1]]:
                    # Remove second occurrence in list of datasets
                    self.datasets.remove(combo[1])
                    self.logger.error(
                        'HCMerge::Same file Entered Twice. %s deleted from list.' % combo[1])

        # Make and move to the work directory
        os.chdir(self.dirs['work'])

        # convert all files to mtz format
        # copy the files to be merged to the work directory
        for count, dataset in enumerate(self.datasets):
            hkl_filename = str(count)+'_'+dataset.rsplit("/",
                                                         1)[1].rsplit(".", 1)[0]+'.mtz'
            if self.user_spacegroup != 0:
                sg = space_group_symbols(
                    self.user_spacegroup).universal_hermann_mauguin()
                self.logger.debug('HCMerge::Converting %s to %s and copying to Working Directory.' % (
                    str(hkl_filename), str(sg)))
                out_file = hkl_filename.rsplit(".", 1)[0]
                command = []
                command.append('pointless hklout '+hkl_filename +
                               '> '+out_file+'_import.log <<eof \n')
                command.append('xdsin '+dataset+' \n')
                command.append('lauegroup %s \n' % sg)
                command.append('choose spacegroup %s \n' % sg)
                if 'scalepack_no_merge_original_index' in set(types):
                    command.append('cell ' + str(self.unitcell[0]) + ' ' + str(self.unitcell[1]) + ' ' + str(self.unitcell[2]) +
                                   ' ' + str(self.unitcell[3]) + ' ' + str(self.unitcell[4]) + ' ' + str(self.unitcell[5]) + '\n')
                command.append('eof\n')
                comfile = open(out_file+'_import.sh', 'w')
                comfile.writelines(command)
                comfile.close()
                os.chmod('./'+out_file+'_import.sh', 0755)

                p = subprocess.Popen(self.cmd_prefix+' ./'+out_file+'_import.sh',
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE).wait()
            else:
                self.logger.debug(
                    'HCMerge::Copying %s to Working Directory.' % str(dataset))
                p = subprocess.Popen('pointless -copy xdsin ' + dataset + ' hklout ' + hkl_filename,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE).wait()
            # Make a list of filenames
            self.data_files.append(hkl_filename)

    def process(self):
        """
        Make 1x1 combinations, combine using pointless, scale, determine CC, make matrix and select dataset
        over CC cutoff
        """
        self.tprint("Process: Data Merging Started.")
        self.logger.debug('HCMerge::Data Merging Started.')

        # Make 1 x 1 combinations
        combos = self.make_combinations(self.data_files, 2)

        # lists for running the multiprocessing
        # jobs = []

        pool = multiprocessing.Pool(self.nproc)

        # combine the files with POINTLESS
        pool_arguments = []
        for pair in combos:
            # print pair
            outfile_prefix = str(pair[0].split('_')[0]) + \
                'x'+str(pair[1].split('_')[0])
            self.id_list[outfile_prefix] = pair
            #in_files, out_file, logger, cmd_prefix, strict, user_spacegroup
            pool_arguments.append(
                (pair, outfile_prefix, self.cmd_prefix, self.strict, self.user_spacegroup))
#            combine = pool.map(self.merge,id_list)
            # combine = Process(target=self.combine, args=(pair, outfile_prefix))
            # jobs.append(combine)
#            combine.start()
#                combine = self.combine(pair,outfile_prefix)

        r = pool.map(combine_wrapper, pool_arguments)
        # print r

        # When POINTLESS is complete, calculate correlation coefficient
        self.tprint("Process: Calculating CCs.")
        pairs_to_calculate_cc = []
        for pair in self.id_list.keys():
            self.results[pair] = {}
            if os.path.isfile(pair+'_pointless.mtz'):
                # First, get batch information from pointless mtz file
                batches = self.get_batch(pair+'_pointless.mtz')
                # Second, check if both datasets made it into the final mtz
                if len(batches) >= 2:
                    # Third, calculate the linear correlation coefficient if there are two datasets
                    if self.settings.get("cc_mode", "cctbx") == "cctbx":
                        self.results[pair]['CC'] = self.get_cc_pointless(
                            pair, batches)  # results are a dict with pair as key
                    else:
                        # self.results[pair]['CC'] = self.get_cc_aimless(
                        #     pair, batches)  # results are a dict with pair as key
                        pairs_to_calculate_cc.append(pair)
                else:
                    # If only one dataset in mtz, default to no correlation.
                    self.logger.error(
                        'HCMerge::%s_pointless.mtz has only one run. CC defaults to 0.' % pair)
                    self.results[pair]['CC'] = 0
            else:
                self.results[pair]['CC'] = 0

        # aimless for CC calculation
        if self.settings.get("cc_mode", "cctbx") == "aimless":
            r = pool.map(get_cc_aimless, pairs_to_calculate_cc)
            # print ">>>>"
            # pprint(r)
            for key, val in r:
                self.results[key]['CC'] = val
            # print "<<<<"

        #TODO
        # pprint(self.data_files)
        # pprint(self.results)
        # pprint(self.id_list)
        
        # Make chart of CC by pairs of files (and a CSV file)
        self.make_cc_chart()
        
        # Make relationship matrix
        self.matrix = self.make_matrix(self.method)

        # Find data above CC cutoff.  Key 0 is most wedges and above CC cutoff
        wedge_files = self.select_data(self.matrix, 1 - self.cutoff)

        # Merge files in selected wedges together using POINTLESS and AIMLESS
        self.merge_wedges(wedge_files)

        # Store the dicts for future use
        self.store_dicts({'data_files': self.data_files, 'id_list': self.id_list,
                          'results': self.results, 'graphs': self.graphs, 'matrix': self.matrix,
                          'merged_files': self.merged_files})

        # Make the summary text file for all merged files
        self.make_log(self.merged_files)

        # Make the dendrogram and write it out as a PNG
        self.make_dendrogram(self.matrix, self.dpi)
        self.logger.debug('HCMerge::Data merging finished.')

    def postprocess(self):
        """
        Data transfer, file cleanup and other maintenance issues.
        """

        # Send back results
        self.handle_return()

        self.logger.debug('HCMerge::Cleaning up in postprocess.')
        # Copy original datasets to a DATA directory
        commandline_utils.check_work_dir(self.dirs['data'], True)
        for file in self.data_files:
            shutil.move(file, self.dirs['data'])
        self.store_dicts({'data_files': self.data_files, 'id_list': self.id_list,
                          'results': self.results, 'graphs': self.graphs, 'matrix': self.matrix,
                          'merged_files': self.merged_files, 'data_dir': self.dirs['data']})
        # Check for postprocessing flags
        # Clean up mess
        if self.settings['clean']:
            self.clean_up()

    def clean_up(self):
        """
        Remove excess log files and tidy up the directory.
        safeext = list of file extensions which should be saved.
        """

        self.tprint("Clean up excess intermediate processing and log files")
        killlist = []
        killext = ['_pointless.sh', '_pointless.mtz',
                   '_pointless.log', '_pointless_p1.log']
        for ext in killext:
            for prefix in self.id_list:
                killlist.append(prefix+ext)
    #        for itm in self.merged_files:
    #            killlist.append(itm+'_aimless.sh')
        filelist = [f for f in os.listdir(self.dirs['work']) if f.endswith(".sh") or f.endswith(".log")
                    or f.endswith(".mtz")]
        purgelist = set(filelist).intersection(set(killlist))
    #        purgelist = [f for f in filelist if f not in safelist]
        for file in purgelist:
            os.remove(file)

    def handle_return(self):
        """Output data to consumer"""

        self.tprint("handle_return")

        run_mode = self.command["preferences"]["run_mode"]

        # Print results to the terminal?
        if run_mode == "interactive":
            self.print_results(self.merged_files)

        # Take care of JSON
        dendrogram = self.json_dendrogram(self.matrix, self.data_files)
        self.write_json({'data_files': self.data_files, 'id_list': self.id_list,
                         'results': self.results, 'graphs': self.graphs, 'matrix': self.matrix.tolist(),
                         'newick': dendrogram, 'merged_files': self.merged_files, 'data_dir': self.dirs['data']})

        # Traditional mode as at the beamline
        if run_mode == "server":
            pass
        # Run and return results to launcher
        elif run_mode == "subprocess":
            return {'data_files': self.data_files, 'id_list': self.id_list,
                    'results': self.results, 'graphs': self.graphs, 'matrix': self.matrix,
                    'merged_files': self.merged_files, 'data_dir': self.dirs['data']}

    def make_combinations(self, files, number=2):
        """
        Makes combinations using itertools
        files = list of files to be combined (usually self.data_files)
        number = number of files in a combination. For a pair, use 2
        """

        self.logger.debug(
            'HCMerge::Setting up %s as %s file combinations' % (str(files), number))
        combos = list()
        for i in combinations(files, number):
            combos.append(i)
        return(combos)

    def get_batch(self, in_file):
        """
        Obtain batch numbers from mtz file. Returns a list of tuples.
        """

        self.logger.debug(
            'HCMerge::get_batch %s from mtz file.' % str(in_file))

        batch_list = []
        batches = []
        reflection_file = reflection_file_reader.any_reflection_file(
            file_name=in_file)
        # Make a list of all the batch numbers
        for item in reflection_file.file_content().batches():
            batch_list.append(item.num())
        # Go through the list of batches, find the gaps and group by ranges
        for k, g in groupby(enumerate(batch_list), lambda x: x[0]-x[1]):
            group = list(map(itemgetter(1), g))
            batches.append((group[0], group[-1]))
        return(batches)

    def get_cc_aimless(self, in_file):
        """
        Calculate correlation coefficient (CC) between two datasets which have been combined
        by pointless.  Uses aimless.  Reads in an mtz file.
        """

        self.logger.debug('HCMerge::get_cc_aimless::Obtain correlation coefficient from %s with batches %s' % (
            str(in_file)))

        # Read in mtz file
        # mtz_file = reflection_file_reader.any_reflection_file(
        #     file_name=in_file+'_pointless.mtz')
        mtz_file = in_file+'_pointless.mtz'
        log_file = in_file+"_aimless.log"
        com_file = in_file+"_aimless.sh"
        # Create aimless command file
        aimless_lines = ['#!/bin/tcsh\n',
                         'aimless hklin %s hklout %s << eof > %s \n' % (mtz_file, "_aimless.mtz", log_file),
                         'anomalous on\n',
                         'scales constant\n',
                         'sdcorrection norefine full 1 0 0 partial 1 0 0\n',
                         'cycles 0\n']
        with open(com_file, "w") as command_file:
            for line in aimless_lines:
                command_file.write(line)
        os.chmod(com_file, stat.S_IRWXU)

        # Run aimless
        cmd = './%s' % com_file
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
        stdout, stderr = p.communicate()

        # Parse the file
        # graphs, summary = aimless.parse_aimless(log_file)
        cc_results = aimless.get_cc(log_file)
        # print graphs
        # print cc_results

        # Return CC
        return cc_results.get("cc", {}).get((1, 2), 0)

    def get_cc_pointless(self, in_file, batches):
        """
        Calculate correlation coefficient (CC) between two datasets which have been combined
        by pointless.  Uses cctbx.  Reads in an mtz file.
        """

        self.logger.debug('HCMerge::get_cc_pointless::Obtain correlation coefficient from %s with batches %s' % (
            str(in_file), str(batches)))

        # Read in mtz file
        mtz_file = reflection_file_reader.any_reflection_file(
            file_name=in_file+'_pointless.mtz')

        # Convert to miller arrays
        # ma[1] has batch information, ma[2] has I and SIGI
        ma = mtz_file.as_miller_arrays(merge_equivalents=False)

        # Set up objects to hold miller indices and data for both datasets
        data1 = flex.double()
        data2 = flex.double()
        indices1 = flex.miller_index()
        indices2 = flex.miller_index()

        run1_batch_start = batches[0][0]
        run1_batch_end = batches[0][1]
        run2_batch_start = batches[1][0]
        run2_batch_end = batches[1][1]

        # Separate datasets by batch
        for cnt, batch in enumerate(ma[1].data()):
            if batch >= run1_batch_start and batch <= run1_batch_end:
                data1.append(ma[2].data()[cnt])
                indices1.append(ma[2].indices()[cnt])
            elif batch >= run2_batch_start and batch <= run2_batch_end:
                data2.append(ma[2].data()[cnt])
                indices2.append(ma[2].indices()[cnt])

        crystal_symmetry = ma[1].crystal_symmetry()

        # Create miller arrays for each dataset and merge symmetry-related reflections
        my_millerset1 = miller.set(crystal_symmetry, indices=indices1)
        my_miller1 = miller.array(my_millerset1, data=data1)
        merged1 = my_miller1.merge_equivalents().array()

        my_millerset2 = miller.set(crystal_symmetry, indices=indices2)
        my_miller2 = miller.array(my_millerset2, data=data2)
        merged2 = my_miller2.merge_equivalents().array()

        # Obtain common set of reflections
        common1 = merged1.common_set(merged2)
        common2 = merged2.common_set(merged1)
#        common1, common2 = my_miller1.common_sets(my_miller2)
        # Deal with only 1 or 2 common reflections in small wedges
        if (len(common1.indices()) == 1 or len(common1.indices()) == 2):
            return(0)
        else:
            # Calculate correlation between the two datasets.
            cc = flex.linear_correlation(common1.data(), common2.data())
            self.logger.debug('HCMerge::Linear Correlation Coefficient for %s = %s.' % (
                str(in_file), str(cc.coefficient())))
            return(cc.coefficient())

    def scale(self, in_file, out_file, VERBOSE=False):
        """
        Scaling files using AIMLESS
        in_file = prefix for input mtz file from POINTLESS
        out_file = prefix for output mtz file
        """

        self.logger.debug(
            'HCMerge::Scale with AIMLESS in_file: %s as out_file: %s' % (in_file, out_file))
        command = []
        command.append('aimless hklin '+in_file+'_pointless.mtz hklout ' +
                       out_file+'_scaled.mtz > '+out_file+'_scaled.log <<eof \n')
        command.append('bins 10 \n')
        command.append('scales constant \n')
        command.append('anomalous on \n')
        command.append('output mtz scalepack merged \n')
        if self.resolution:
            command.append('resolution high %s \n' % self.resolution)
#        command.append('END \n')
        command.append('eof \n')
        comfile = open(in_file+'_aimless.sh', 'w')
        comfile.writelines(command)
        comfile.close()
        os.chmod(in_file+'_aimless.sh', 0755)
        p = subprocess.Popen(self.cmd_prefix+' ./'+in_file+'_aimless.sh',
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE).wait()

        # Check for maximum resolution and re-run scaling if resolution is too high
        scalog = open(out_file+'_scaled.log', 'r').readlines()
        if self.resolution:
            pass
        else:
            for num, line in enumerate(scalog):
                if line.startswith('Estimates of resolution limits: overall'):
                    # Go to the next line to check resolution
                    if scalog[num+1].endswith('maximum resolution\n'):
                        break
                    elif scalog[num+2].endswith('maximum resolution\n'):
                        break
                    # Make exception for really weak data
                    elif scalog[num+1].endswith('WARNING: weak data, all data below threshold'):
                        self.results['errormsg'].append(
                            'Weak Data.  Check %s_scaled.log.\n' % out_file)
                        break
                    elif scalog[num+2].endswith('WARNING: weak data, all data below threshold'):
                        self.results['errormsg'].append(
                            'Weak Data.  Check %s_scaled.log.\n' % out_file)
                        break
                    else:
                        new_res = min(
                            scalog[num+1].split()[8].rstrip('A'), scalog[num+2].split()[6].rstrip('A'))
                        self.logger.debug(
                            'HCMerge::Scale resolution %s' % new_res)
                        for num, itm in enumerate(command):
                            if itm == 'END \n':
                                command.insert(
                                    num, 'resolution high %s \n' % new_res)
                                break
                        comfile = open(out_file+'_aimless.sh', 'w')
                        comfile.writelines(command)
                        comfile.close()
                        p = subprocess.Popen(self.cmd_prefix+' ./'+in_file+'_aimless.sh',
                                             shell=True,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE).wait()

    def make_matrix(self, method):
        """
        Take all the combinations and make a matrix of their relationships using agglomerative
        hierarchical clustering, hcluster. Use CC as distance.
        self.id_list = OrderedDict of pairs of datasets
        self.results = Dict of values extracted from aimless log
        method = linkage method: single, average, complete, weighted
        Return Z, the linkage array
        """

        self.logger.info('HCMerge::make_matrix using method %s' % method)
        Y = []  # The list of distances, our equivalent of pdist
        for pair in self.id_list.keys():
            # grab keys with stats of interest, but ensure that keys go in numerical order
            cc = 1 - self.results[pair]['CC']
            Y.append(cc)
        self.logger.debug('HCMerge::Array of distances for matrix = %s' % Y)
        # The linkage defaults to single and euclidean
        Z = linkage(Y, method=method)
        return Z

    def select_data(self, Z, cutoff):
        """
        Select dataset above the CC of interest
        Z = linkage array
        self.data_files = list of datasets in working directory
        cutoff = CC of interest
        most_wedges = dict with the wedge number as key, list of data sets as value
        """

        self.logger.info('HCMerge::Apply cutoff to linkage array %s' % Z)
        node_list = {}  # Dict to hold new nodes
        for cnt, row in enumerate(Z):
            node_list[len(Z)+cnt+1] = [int(row[0]), int(row[1])]
        # Set up for making groups of all clusters below cutoff.  Turn most_wedges into a dict.
        # Default to most closely linked pair of wedges
        if any(item for item in Z.tolist() if item[2] < cutoff):
            most_wedges = {}
        else:
            most_wedges = {0: ([int(Z[0][0]), int(Z[0][1])], Z[0][2])}
        for cnt, item in enumerate(Z[::-1]):
            # Apply cutoff
            if item[2] <= cutoff:
                # Dict holding clusters using node ID as key
                most_wedges[cnt] = [int(item[0]), int(item[1])], item[2]
        # iteratively go through dict values and reduce to original leaves
        for i in most_wedges.values():
            # use set because it is faster than list
            while set(i[0]).intersection(set(node_list.keys())):
                self.replace_wedges(i[0], node_list)

        # Convert numbers to filenames
        for i in most_wedges:
            for cnt, item in enumerate(most_wedges[i][0]):
                most_wedges[i][0][cnt] = self.data_files[item]

#        # Convert to a flat list and remove the duplicates
#        most_wedges = set(list(chain.from_iterable(most_wedges)))
        self.logger.info('HCMerge::Selected wedges by node %s' % most_wedges)
        return most_wedges

    def replace_wedges(self, wedges, node_dict):
        """
        Helper function to go through a pair of nodes from linkage list and expand it to a flat
        list that has all the original leaves
        """

        self.logger.debug('HCMerge::Replace Wedges: %s' % wedges)
        for count, item in enumerate(wedges):
            if item in node_dict.keys():
                wedges[count] = node_dict[item][0]
                wedges.append(node_dict[item][1])
        return wedges

    def merge_wedges(self, wedge_files):
        """
        Merge all the separate wedges together at the cutoff value. Combines all files with POINTLESS then scales with AIMLESS.
        Parses AIMLESS log file for statistics
        Separated from process so that I can use it in rerun.
        Requires: wedge_files = flat list of all the original leaves.
        """

        self.logger.debug('HCMerge::Merge Wedges: %s' % wedge_files)
        # lists for running the multiprocessing
        jobs = []
        pool = multiprocessing.Pool(self.nproc)
        pool_arguments = []

        # Check for all_clusters flag
        if self.all_clusters:
            for cnt, cluster in enumerate(wedge_files.values()):
                pool_arguments.append(
                    (cluster[0], self.prefix+str(cnt), self.cmd_prefix, self.strict, self.user_spacegroup))
            r = pool.map(combine_wrapper, pool_arguments)
#                combine_all = Process(target=self.combine(
#                    cluster[0], self.prefix+str(cnt)))
#                jobs.append(combine_all)
#                combine_all.start()
#            for pair in jobs:
#                pair.join()
            # Scale the files with aimless
            for cnt, itm in enumerate(wedge_files):
                scale = Process(target=self.scale, args=(
                    self.prefix+str(cnt), self.prefix+str(cnt)))
                jobs.append(scale)
                scale.start()
            for pair in jobs:
                pair.join()
            for cnt, itm in enumerate(wedge_files):
                new_prefix = self.prefix+str(cnt)
                self.graphs[new_prefix], self.results[new_prefix] = aimless.parse_aimless(
                    self.prefix+str(cnt)+'_scaled.log')
                self.results[new_prefix]['files'] = wedge_files[itm][0]
                self.results[new_prefix]['CC'] = 1 - wedge_files[itm][1]
                self.merged_files.append(new_prefix)
        else:
            pool_arguments.append(
                (next(wedge_files.itervalues())[0], self.prefix, self.cmd_prefix, self.strict, self.user_spacegroup))
            r = pool.map(combine_wrapper, pool_arguments)
#            combine_all = Process(target=self.combine, args=(
#                next(wedge_files.itervalues())[0], self.prefix))
#            combine_all.start()
#            combine_all.join()
            # Scale the files with aimless
            scale = Process(target=self.scale, args=(self.prefix, self.prefix))
            scale.start()
            scale.join()
            self.graphs[self.prefix], self.results[self.prefix] = aimless.parse_aimless(
                self.prefix+'_scaled.log')
            self.results[self.prefix]['files'] = next(
                wedge_files.itervalues())[0]
            self.results[self.prefix]['CC'] = 1 - \
                next(wedge_files.itervalues())[1]
            self.merged_files.append(self.prefix)

    def make_dendrogram(self, matrix, resolution):
        """
        Make a printable dendrogram as either high resolution or low resolution (dpi) image.
        """
        self.logger.debug('HCMerge::Generating Dendrogram')
        # Make a dendrogram of the hierarchical clustering.  Options are from scipy.cluster.hierarchy.dendrogram
        try:
            import matplotlib.pylab
            if self.labels:
                dendrogram(matrix, color_threshold=1 - self.cutoff,
                           labels=self.data_files, leaf_rotation=-90)
                matplotlib.pylab.xlabel('Datasets')
                matplotlib.pylab.ylabel('1 - Correlation Coefficient')
                f = matplotlib.pylab.gcf()
                f.set_size_inches([8, 8])
                f.subplots_adjust(bottom=0.4)
            else:
                dendrogram(matrix, color_threshold=1 - self.cutoff)
            # Save a PNG of the plot
            matplotlib.pylab.savefig(
                self.prefix+'-dendrogram.png', dpi=resolution)
        except:
            dendrogram(matrix, color_threshold=1 - self.cutoff, no_plot=True)
            self.logger.error(
                'HCMerge::matplotlib.pylab unavailable in your version of cctbx.  Plot not generated.')

    def getNewick(self, node, newick, parentdist, leaf_names):
        """
        Get Newick format
        https://stackoverflow.com/questions/28222179/save-dendrogram-to-newick-format

        tree = scipy.cluster.hierarchy.to_tree(Z,False)
        getNewick(tree, "", tree.dist, leaf_names)
        """
        if node.is_leaf():
            return "%s:%.3f%s" % (leaf_names[node.id], parentdist - node.dist, newick)
        else:
            if len(newick) > 0:
                newick = "):%.3f%s" % (parentdist - node.dist, newick)
            else:
                newick = ");"
            newick = self.getNewick(
                node.get_left(), newick, node.dist, leaf_names)
            newick = self.getNewick(node.get_right(), ",%s" %
                                    (newick), node.dist, leaf_names)
            newick = "(%s" % (newick)
            return newick

    def make_cc_chart(self):
        """
        Make a chart of the correlation coefficients by file pairs.
        """
        # Create a dict of wedge names keyed by the index used by the plugin
        wedges = {}
        for data_file in self.data_files:
            key = data_file.split("_")[0]
            value = "_".join(data_file.split("_")[1:])
            wedges[key] = value
        
        # Create an array of keys to put file strings in proper numerical order
        wedge_keys =  wedges.keys()
#        wedge_keys = self.id_list.keys()
        wedge_keys.sort(key=lambda x: int(x))
        # print wedge_keys

        # Figure out the longest wedge name
        longest = 0
        for file_name in wedges.values():
            length = len(file_name)
            if length > longest:
                longest = length
        # print "Longest file name is %d characters" % longest

        self.tprint("\nTable of correlation coefficients\n", 50, "blue")

        # Print column headers
        count = longest
        while count > 0:
            # print count
            line = " "*longest+"  |"
            for key in wedge_keys[1:]:
                value = wedges[key]
                position = len(value)-count
                if position >= 0:
                    line += "   "+value[position]+"   |"
                else:
                    line += "       |"
            self.tprint(line, 50)
            count -= 1

        # Print the rows
        counter1 = 0
        for key1 in wedge_keys[:-1]:
            value = wedges[key1]
            line = " "+value+(" "*(longest-len(value)))+" |"
            counter2 = 1
            colorations = 0
            for key2 in wedge_keys[1:]:
                if counter2 > counter1:
                    if "x".join([key1, key2]) in self.results:
                        cc = self.results["x".join([key1, key2])]["CC"]
                    elif "x".join([key2, key1]) in self.results:
                        cc = self.results["x".join([key2, key1])]["CC"]
                    else:
                        cc = -1
                    if cc < HIGHLIGHT_THRESHOLD:
                        line += ((rtext.red+" %3.3f "+rtext.stop+"|") % cc)
                        colorations += 1
                    else:
                        line += " %3.3f |" % cc
                else:
                    line += "       |"
                counter2 += 1
            self.tprint("-"*(len(line)-(9*colorations)), 50)
            self.tprint(line, 50)
            counter1 += 1
        self.tprint("-"*(len(line)-(9*colorations))+"\n", 50)

        # Make a CSV
        csv_lines = []
        # Header
        csv_line = ""
        for key in wedge_keys[1:]:
            csv_line += ("," + wedges[key])
        csv_lines.append(csv_line)
        # Body
        counter1 = 0
        for key1 in wedge_keys[:-1]:
            value = wedges[key1]
            csv_line = value
            counter2 = 1
            colorations = 0
            for key2 in wedge_keys[1:]:
                # print counter1, counter2
                if counter2 > counter1:
                    if "x".join([key1, key2]) in self.results:
                        cc = self.results["x".join([key1, key2])]["CC"]
                        csv_line += (",%f" % cc)
                    elif "x".join([key2, key1]) in self.results:
                        cc = self.results["x".join([key2, key1])]["CC"]
                        csv_line += (",%f" % cc)
                    else:
                        csv_line += (",")
                else:
                    csv_line += (",")
                counter2 += 1
            counter1 += 1
            # print csv_line
            csv_lines.append(csv_line)

        # Write CSV
        with open("cc.csv", "w") as csv_file:
            for csv_line in csv_lines:
                csv_file.write(csv_line+"\n")

    def make_log(self, files):
        """
        Makes a log file of the merging results
        files = list of results files, prefix only
        """

        self.logger.debug('HCMerge::Write tabulated results to %s' %
                          (self.prefix + '.log'))

        # Make a comparison table of results
        # Set up list of lists for making comparison table
        table = [['', 'Correlation', 'Space Group', 'Resolution', 'Completeness',
                  'Multiplicity', 'I/SigI', 'Rmerge', 'Rmeas', 'Anom Rmeas',
                  'Rpim', 'Anom Rpim', 'CC 1/2', 'Anom Completeness', 'Anom Multiplicity',
                  'Anom CC', 'Anom Slope', 'Total Obs', 'Unique Obs']]
        key_list = ['CC', 'scaling_spacegroup', 'bins_high', 'completeness', 'multiplicity',
                    'isigi', 'rmerge_norm', 'rmeas_norm', 'rmeas_anom',
                    'rpim_norm', 'rpim_anom', 'cc-half', 'anom_completeness',
                    'anom_multiplicity', 'anom_correlation', 'anom_slope', 'total_obs', 'unique_obs']
        for file in files:
            row = [file]
            for item in key_list:
                # If it is a list, add first item from the list which is overall stat
                if type(self.results[file][item]) == list:
                    row.append(self.results[file][item][0])
                # Otherwise, add the entire contents of the item
                else:
                    row.append(self.results[file][item])
            table.append(row)
        # flip columns and rows since rows are so long
        table = zip(*table)
        out_file = self.prefix + '.log'
        out = open(out_file, 'w')
        table_print = MakeTables()
        table_print.pprint_table(out, table)
        out.close()

        # Append a key for merged file names
        out = open(out_file, 'a')
        for file in files:
            out.write(file + ' = ' + str(self.results[file]['files']) + '\n')
        out.close()

    def print_results(self, files):
        """
        Makes a log file of the merging results
        files = list of results files, prefix only
        """

        # Make a comparison table of results
        # Set up list of lists for making comparison table
        table = [['', 'Correlation', 'Space Group', 'Resolution', 'Completeness',
                  'Multiplicity', 'I/SigI', 'Rmerge', 'Rmeas', 'Anom Rmeas',
                  'Rpim', 'Anom Rpim', 'CC 1/2', 'Anom Completeness', 'Anom Multiplicity',
                  'Anom CC', 'Anom Slope', 'Total Obs', 'Unique Obs']]
        key_list = ['CC', 'scaling_spacegroup', 'bins_high', 'completeness', 'multiplicity',
                    'isigi', 'rmerge_norm', 'rmeas_norm', 'rmeas_anom',
                    'rpim_norm', 'rpim_anom', 'cc-half', 'anom_completeness',
                    'anom_multiplicity', 'anom_correlation', 'anom_slope', 'total_obs', 'unique_obs']
        for file in files:
            row = [file]
            for item in key_list:
                # If it is a list, add first item from the list which is overall stat
                if type(self.results[file][item]) == list:
                    row.append(self.results[file][item][0])
                # Otherwise, add the entire contents of the item
                else:
                    row.append(self.results[file][item])
            table.append(row)
        # flip columns and rows since rows are so long
        table = zip(*table)
        table_print = MakeTables()
        table_print.pprint_table(sys.stdout, table)

        # Append a key for merged file names
        for file in files:
            print(file + ' = ' + str(self.results[file]['files']) + '\n')

    def store_dicts(self, dicts):
        """
        Create pickle files of dicts with CC, aimless stats, combinations already processed, merged file list
        """

        self.logger.debug('HCMerge::Pickling Dicts')
        file = open(self.prefix + '.pkl', 'wb')
        pickle.dump(dicts, file)
        file.close()

    def get_dicts(self, file):
        """
        Extract dicts out of pickle file
        """

        self.logger.debug('HCMerge::UnPickling Dicts')
        tmp = pickle.load(open(file, 'rb'))
        for itm, val in tmp.iteritems():
            setattr(self, itm, val)

    def rerun(self, pkl_file):
        """
        Re-running parts of the agent
        self.dirs['data'] should be self.data_dir when pulled from pkl file
        """

        self.logger.debug('HCMerge::rerun')
        self.get_dicts(pkl_file)
        if self.start_point == 'clustering':
            # List for storing new merged files.
            self.merged_files = []
            os.chdir(self.dirs['work'])
            # Make new COMBINE directory and move data files over
            # combine_dir = self.create_subdirectory(prefix='COMBINE', path=self.dirs['work'])
            # os.chdir(combine_dir)
            self.logger.debug('HCMerge::Copying files from %s to %s' %
                              (self.data_dir, self.dirs['work']))
            for file in self.data_files:
                shutil.copy(self.data_dir + '/' + file, self.dirs['work'])

            # Make relationship matrix
            self.matrix = self.make_matrix(self.method)

            # Find data above CC cutoff.  Key 0 is most wedges and above CC cutoff
            wedge_files = self.select_data(self.matrix, 1 - self.cutoff)

            # Merge all wedges together
            self.merge_wedges(wedge_files)

            # Store the dicts for future use
            self.store_dicts({'data_files': self.data_files, 'id_list': self.id_list,
                              'results': self.results, 'graphs': self.graphs, 'matrix': self.matrix,
                              'merged_files': self.merged_files})

            # Make the summary text file for all merged files
            self.make_log(self.merged_files)

        else:
            pass
        # Make the dendrogram and write it out as a PNG
        self.make_dendrogram(self.matrix, self.dpi)

    def write_json(self, results):
        """Write a file with the JSON version of the results"""

        json_string = json.dumps(results)

        # Output to terminal?
        if self.settings.get("json", True):
            print json_string

        # Always write a file
        os.chdir(self.dirs['work'])
        with open("result.json", 'w') as outfile:
            outfile.writelines(json_string)

    def json_dendrogram(self, Z, leaf_names):
        """Make a Newick json suitable for use with http://bl.ocks.org/kueda/1036776 which uses d3 to make a phylogenetic tree"""

        tree = to_tree(Z, False)
        json = self.getNewick(tree, "", tree.dist, leaf_names)
        return json

    def print_credits(self):
        """Print credits for programs utilized by this plugin"""

        self.tprint(credits.HEADER, level=99, color="blue")

        programs = ["CCTBX", "AIMLESS", "POINTLESS"]
        info_string = credits.get_credits_text(programs, "    ")
        self.tprint(info_string, level=99, color="default")


class MakeTables:
    """
    From GITS blog: http://ginstrom.com/scribbles/2007/09/04/pretty-printing-a-table-in-python/
    In a class so that it can be used separately from the MergeMany pipeline.
    """

    def get_max_width(self, table, index):
        """Get the maximum width of the given column index"""

        return max([len(str(row[index])) for row in table])

    def pprint_table(self, out, table):
        """
        Prints out a table of data, padded for alignment
        out = Output stream (file-like object)
        table = The table to print. A list of lists.
        Each row must have the same number of columns.
        """

        col_paddings = []

        for i in range(len(table[0])):
            col_paddings.append(self.get_max_width(table, i))

        for row in table:
            # left col
            print >> out, row[0].ljust(col_paddings[0] + 1),
            # rest of the cols
            for i in range(1, len(row)):
                col = str(row[i]).rjust(col_paddings[i] + 2)
                print >> out, col,
            print >> out

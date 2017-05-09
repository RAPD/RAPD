'''
Created August 09, 2012
By Kay Perry, Frank Murphy

Distributed under the terms of the GNU General Public License.

This file is part of RAPD

RAPD is a free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 3 of the license,
or (at your option) any later version.

RAPD is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

rapd_agent_mergemany.py is a pipeline to be used by the rapd_cluster.py
                          process for combining multiple data wedges created by
                          the integration pipeline of rapd

This pipeline expects a command with:

datasets = list of all filenames to be merged

'''
from multiprocessing import Process, cpu_count
import matplotlib
# Force matplotlib to not use any Xwindows backend.  Must be called before any other matplotlib/pylab import.
matplotlib.use('Agg')
import os, subprocess, sys
#import stat
import logging, logging.handlers
#import threading
import hashlib
import shutil
from itertools import combinations
from collections import OrderedDict
from iotbx import reflection_file_reader
from cctbx import miller
from cctbx.array_family import flex
from cctbx.sgtbx import space_group_symbols
from hcluster import linkage,dendrogram

import cPickle as pickle # For storing dicts as pickle files for later use


class MergeMany(Process):
    """
    To merge multiple datasets from RAPD's integration pipeline
    """
    def __init__(self, input, logger):
        """
        Initialize the merging processing using agglomerative hierachical clustering process
        """

        logger.info('HCMerge::Initiating variables.')

        # Setting up data input
        self.input = input[0:4]
        self.controller_address = input[-1]
        self.logger = logger

        self.command = self.input[0]
        self.dirs = self.input[1]
#        self.datasets = self.command[2]['MergeMany'] # RAPD 1 - This is a dict of all results.  Each result is a dict.
        # List of original data files to be merged.  Currently expected to be ASCII.HKL
        self.datasets = self.input[2]
        self.settings = self.input[3]

        # Variables
        self.cmdline = self.settings['cmdline']
        self.process_id = self.settings['process_id']

        if 'work_dir_override' in self.settings:
            if (self.settings['work_dir_override'] == True or
                self.settings['work_dir_override'] == 'True'):
                self.dirs['work'] = self.settings['work_directory']

        # Variables for holding filenames and results
        self.data_files                    = []            # List of data file names
        self.graphs                        = {}
        self.results                       = {}
        self.merged_files                  = []            # List of prefixes for final files.
        # dict for keeping track of file identities
        self.id_list                       = OrderedDict() # Dict will hold prefix as key and pair of file names as value
        self.dirs['data']                  = 'DATA'
        
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
            self.cutoff = self.settings['cutoff'] # CC 1/2 value passed in by user
        else:
            self.cutoff = 0.95

        # Check for filename for merged dataset
        if self.settings.has_key('prefix'):
            self.prefix = self.settings['prefix']
        else:
            self.prefix = 'merged'

        # Check for user-defined spacegroup
        if self.settings.has_key('user_spacegroup'):
            self.user_spacegroup = self.settings['user_spacegroup']
        else:
            self.user_spacegroup = 0 # Default to None

        # Check for user-defined high resolution cutoff
        if self.settings.has_key('resolution'):
            self.resolution = self.settings['resolution']
        else:
            self.resolution = 0 # Default high resolution limit to 0

        # Check for file cleanup
        if self.settings.has_key('cleanup_files'):
            self.cleanup_files = self.settings['cleanup_files']
        else:
            self.cleanup_files = True

        # Check whether to make all clusters or the first one that exceeds the cutoff
        if self.settings.has_key('all_clusters'):
            self.all_clusters=self.settings['all_clusters']
        else:
            self.all_clusters = False

        # Check whether to add labels to the dendrogram
        if self.settings.has_key('labels'):
            self.labels=self.settings['labels']
        else:
            self.labels = False

        # Check whether to start at the beginning or skip to a later step
        if self.settings.has_key('start_point'):
            self.start_point=self.settings['start_point']
        else:
            self.start_point= 'start'
            
        # Check whether to skip prechecking files during preprocess
        if self.settings.has_key('precheck'):
            self.precheck=self.settings['precheck']
        else:
            self.precheck = True

        # Set resolution for dendrogram image
        if self.settings.has_key('dpi'):
            self.dpi=self.settings['dpi']
        else:
            self.dpi = 100
                        
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

        Process.__init__(self,name='MergeMany')
        self.start()

    def run(self):
        self.logger.debug('HCMerge::Data Merging Started.')
        # Need to change to work also when data is still collecting.  Currently set up for when
        # data collection is complete.

        # Provide a flag for whether data is still being collected or is complete
        try:
            if self.start_point == 'start':
                self.preprocess()
                self.process()
            else:
                pkl_file = self.datasets
                self.rerun(pkl_file)
            self.postprocess()
        except ValueError, Argument:
            self.logger.error('HCMerge::Failure to Run.')
            self.logger.exception(Argument)

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
        
    def process(self):
        """
        Make 1x1 combinations, combine using pointless, scale, determine CC, make matrix and select dataset
        over CC cutoff
        """

        self.logger.debug('HCMerge::Data Merging Started.')

        # Make 1 x 1 combinations
        combos = self.make_combinations(self.data_files,2)

        # lists for running the multiprocessing
        jobs                               = []

        # combine the files with POINTLESS
        for pair in combos:
            outfile_prefix = str(pair[0].split('_')[0])+'x'+str(pair[1].split('_')[0])
            self.id_list[outfile_prefix] = pair
#            combine = pool.map(self.merge,id_list)
            combine = Process(target=self.combine,args=(pair,outfile_prefix))
            jobs.append(combine)
#            combine.start()
#                combine = self.combine(pair,outfile_prefix)

        # Wait for all worker processes to finish
        numjobs = len(jobs)
        jobNum = 0
        while jobNum < numjobs:
            endjobNum = min(jobNum+self.nproc, numjobs)
            for job in jobs[jobNum:endjobNum]:
                job.start()
            for job in jobs[jobNum:endjobNum]:
                job.join()
            jobNum = endjobNum

        # When POINTLESS is complete, calculate correlation coefficient
        for pair in self.id_list.keys():
            self.results[pair] = {}
            if os.path.isfile(pair+'_pointless.mtz'):
                # First, get batch information from pointless log file
                batches = self.get_batch(pair)
                # Second, check if both datasets made it into the final mtz
                if (batches.get(1) and batches.get(2)):
                # Third, calculate the linear correlation coefficient if there are two datasets
                    self.results[pair]['CC'] = self.get_cc_pointless(pair,batches) # results are a dict with pair as key
                else:
                    # If only one dataset in mtz, default to no correlation.
                    self.logger.error('HCMerge::%s_pointless.mtz has only one run. CC defaults to 0.'% pair)
                    self.results[pair]['CC'] = 0
            else:
                self.results[pair]['CC'] = 0

        # Make relationship matrix
        matrix = self.make_matrix(self.method)

        # Find data above CC cutoff.  Key 0 is most wedges and above CC cutoff
        wedge_files = self.select_data(matrix, 1 - self.cutoff)

        # Merge files in selected wedges together using POINTLESS and AIMLESS
        self.merge_wedges(wedge_files)

        # Store the dicts for future use
        self.store_dicts({'data_files': self.data_files, 'id_list': self.id_list, 
                          'results': self.results, 'graphs': self.graphs, 'matrix': matrix,
                          'merged_files': self.merged_files})

		# Make the summary text file for all merged files
        self.make_log(self.merged_files)

        # Make the dendrogram and write it out as a PNG
        self.make_dendrogram(matrix, self.dpi)
        self.logger.debug('HCMerge::Data merging finished.')

    def process_continuous(self):
        """
        As wedges are collected, continuously make 1x1 combinations, combine using pointless, scale, determine CC,
        make matrix and select dataset over CC cutoff
        """

    def postprocess(self):
        """
        Data transfer, file cleanup and other maintenance issues.
        """

        self.logger.debug('HCMerge::Cleaning up in postprocess.')
        # Copy original datasets to a DATA directory
        data_dir = self.create_subdirectory(prefix='DATA', path=self.dirs['work'])
        for file in self.data_files:
	        shutil.copy(file,data_dir)
		self.get_dicts(self.prefix + '.pkl')
        self.store_dicts({'data_files': self.data_files, 'id_list': self.id_list, 
                          'results': self.results, 'graphs': self.graphs, 'matrix': self.matrix,
                          'merged_files': self.merged_files, 'data_dir': data_dir})
        # Check for postprocessing flags
        if self.settings['cleanup_files']:
            self.cleanup()
        if self.cmdline is False:
            self.write_db()
            self.results['status'] = 'SUCCESS'
            #print tables
        # Move final files to top directory
        for file in self.merged_files:
        	shutil.copy(file + '_scaled.mtz', self.dirs['work'])
        	shutil.copy(file + '_scaled.log', self.dirs['work'])        	
    	shutil.copy(self.prefix + '-dendrogram.png', self.dirs['work'])
    	shutil.copy(self.prefix + '.log', self.dirs['work'])
    	shutil.copy(self.prefix + '.pkl', self.dirs['work'])
       

    def make_combinations(self, files, number=2):
        """
        Makes combinations using itertools
        files = list of files to be combined (usually self.data_files)
        number = number of files in a combination. For a pair, use 2
        """

        self.logger.debug('HCMerge::Setting up %s as %s file combinations' % (str(files),number))
        combos = list()
        for i in combinations(files,number):
            combos.append(i)
        return(combos)

    def combine(self, in_files, out_file):
        """
        Combine XDS_ASCII.HKL files using POINTLESS
        in_files = list of files
        """

        self.logger.debug('HCMerge::Pair-wise joining of %s using pointless.' % str(in_files))
#        command = ['#!/bin/csh \n']
        command = []
        command.append('pointless hklout '+out_file+'_pointless.mtz> '+out_file+'_pointless.log <<eof \n')

        for hklin in in_files:
            command.append('hklin '+hklin+' \n')
            # Add ability to do batches
        # Make TOLERANCE huge to accept unit cell variations
        command.append('tolerance 1000.0 \n')
        # Add LAUEGROUP if user has chosen a spacegroup
        if self.user_spacegroup:
            command.append('lauegroup %s \n' % space_group_symbols(self.user_spacegroup).universal_hermann_mauguin())
            command.append('choose spacegroup %s \n' % space_group_symbols(self.user_spacegroup).universal_hermann_mauguin())
        command.append('eof\n')
        comfile = open(out_file+'_pointless.sh','w')
        comfile.writelines(command)
        comfile.close()
        os.chmod('./'+out_file+'_pointless.sh',0755)
#            p = subprocess.Popen('qsub -N combine -sync y ./'+out_file+'_pointless.sh',shell=True).wait()
        p = subprocess.Popen(self.cmd_prefix+' ./'+out_file+'_pointless.sh',
                             shell = True,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE).communicate()
#            p = utils.processCluster('sh '+out_file+'_pointless.sh')
        if self.user_spacegroup == 0:
            # Sub-routine for different point groups
            if (p[0] == '' and p[1] == '') == False:
                self.logger.debug('HCMerge::Error Messages from %s pointless log. %s' % (out_file, str(p)))
            if ('WARNING: Cannot combine reflection lists with different symmetry' or 'ERROR: cannot combine files belonging to different crystal systems') in p[1]:
                self.logger.debug('HCMerge::Different symmetries. Placing %s in best spacegroup.' % str(in_files))
                for hklin in in_files:
                    cmd = []
                    cmd.append('pointless hklin '+hklin+' hklout '+hklin+'> '+hklin+'_p.log \n')
                    subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE, stderr=subprocess.PIPE).wait()
                p = subprocess.Popen(self.cmd_prefix+' ./'+out_file+'_pointless.sh',
                                 shell = True,
                                 stdout = subprocess.PIPE,
                                 stderr = subprocess.PIPE).communicate()
                if 'WARNING: Cannot combine reflection lists with different symmetry' in p[1]:
                    self.logger.debug('HCMerge::Still different symmetries after best spacegroup.  Reducing %s to P1.' % str(in_files))
                    for hklin in in_files:
                        cmd = []
                        hklout = hklin.rsplit('.',1)[0]+'p1.mtz'
                        cmd.append('pointless hklin '+hklin+' hklout '+hklout+'> '+hklin+'_p1.log <<eof \n')
                        cmd.append('lauegroup P1 \n')
                        cmd.append('choose spacegroup P1 \n')
                        cmd.append('eof\n')
                        cmdfile = open('p1_pointless.sh','w')
                        cmdfile.writelines(cmd)
                        cmdfile.close()
                        os.chmod('./p1_pointless.sh',0755)
                        p1 = subprocess.Popen('p1_pointless.sh',
                                             shell = True,
                                             stdout = subprocess.PIPE,
                                             stderr = subprocess.PIPE).communicate()
                    command = [x.replace('.mtz', 'p1.mtz') for x in command if any('hklin')]
                    comfile = open(out_file+'_pointless.sh','w')
                    comfile.writelines(command)
                    comfile.close()
                    p = subprocess.Popen(self.cmd_prefix+' ./'+out_file+'_pointless.sh',
                                 shell = True,
                                 stdout = subprocess.PIPE,
                                 stderr = subprocess.PIPE).communicate()
                                                 
        # Check for known FATAL ERROR of unable to pick LAUE GROUP due to not enough reflections
        plog = open(out_file+'_pointless.log', 'r').readlines()
        for num,line in enumerate(plog):
            if line.startswith('FATAL ERROR'):
                # Go to the next line for error message
                if 'ERROR: cannot decide on which Laue group to select\n' in plog[num+1]:
                    self.logger.debug('HCMerge::Cannot automatically choose a Laue group.  Forcing solution 1.')
                    for num,itm in enumerate(command):
                        if itm == 'eof\n':
                            command.insert(num, 'choose solution 1\n' )
                            break
                comfile = open(out_file+'_pointless.sh','w')
                comfile.writelines(command)
                comfile.close()
                # Run pointless again with new keyword
                p = subprocess.Popen(self.cmd_prefix+' ./'+out_file+'_pointless.sh',
                                     shell=True,
                                     stdout = subprocess.PIPE,
                                     stderr = subprocess.PIPE).wait()
                if 'ERROR: cannot combine files belonging to different crystal systems' in plog[num+1]:
                    self.logger.debug('HCMerge:: Forcing P1 due to different crystal systems in %s.' % str(in_files))
                    for hklin in in_files:
                        cmd = []
                        hklout = hklin.rsplit('.',1)[0]+'p1.mtz'
                        cmd.append('pointless hklin '+hklin+' hklout '+hklout+'> '+hklin+'_p1.log <<eof \n')
                        cmd.append('lauegroup P1 \n')
                        cmd.append('choose spacegroup P1 \n')
                        cmd.append('eof\n')
                        cmdfile = open('p1_pointless.sh','w')
                        cmdfile.writelines(cmd)
                        cmdfile.close()
                        os.chmod('./p1_pointless.sh',0755)
                        p1 = subprocess.Popen('p1_pointless.sh',
                                             shell = True,
                                             stdout = subprocess.PIPE,
                                             stderr = subprocess.PIPE).communicate()
                    command = [x.replace('.mtz', 'p1.mtz') for x in command if any('hklin')]
                    comfile = open(out_file+'_pointless.sh','w')
                    comfile.writelines(command)
                    comfile.close()
                    p = subprocess.Popen(self.cmd_prefix+' ./'+out_file+'_pointless.sh',
                                 shell = True,
                                 stdout = subprocess.PIPE,
                                 stderr = subprocess.PIPE).communicate()

    
#        sts = os.waitpid(p.pid, 1)[1]

    def get_batch(self, in_file):
        """
        Obtain batch numbers from pointless log.
        """

        self.logger.debug('HCMerge::get_batch %s from pointless log.' % str(in_file))

        batches = {}
        log = open(in_file+'_pointless.log','r').readlines()

        for line in log:
            if ('consists of batches' in line):
                sline = line.split()
                run_number = int(sline[2])
                batch_start = int(sline[6])
                batch_end = int(sline[len(sline)-1])
                batches[run_number] = (batch_start,batch_end)
                self.logger.debug('%s has batches %d to %d' % (in_file,batch_start,batch_end))

        return(batches)

    def get_cc_pointless(self, in_file, batches):
        """
        Calculate correlation coefficient (CC) between two datasets which have been combined
        by pointless.  Uses cctbx.  Reads in an mtz file.
        """

        self.logger.debug('HCMerge::get_cc_pointless::Obtain correlation coefficient from %s with batches %s' % (str(in_file),str(batches)))

        # Read in mtz file
        mtz_file = reflection_file_reader.any_reflection_file(file_name=in_file+'_pointless.mtz')

        # Convert to miller arrays
        # ma[1] has batch information, ma[2] has I and SIGI
        ma = mtz_file.as_miller_arrays(merge_equivalents=False)

        # Set up objects to hold miller indices and data for both datasets
        data1 = flex.double()
        data2 = flex.double()
        indices1 = flex.miller_index()
        indices2 = flex.miller_index()

        run1_batch_start = batches[1][0]
        run1_batch_end = batches[1][1]
        run2_batch_start = batches[2][0]
        run2_batch_end = batches[2][1]

        # Separate datasets by batch
        for cnt,batch in enumerate(ma[1].data()):
            if batch >= run1_batch_start and batch <= run1_batch_end:
                data1.append(ma[2].data()[cnt])
                indices1.append(ma[2].indices()[cnt])
            elif batch >= run2_batch_start and batch <= run2_batch_end:
                data2.append(ma[2].data()[cnt])
                indices2.append(ma[2].indices()[cnt])

        crystal_symmetry=ma[1].crystal_symmetry()

        # Create miller arrays for each dataset and merge equivalent reflections
        my_millerset1 = miller.set(crystal_symmetry,indices=indices1)
        my_miller1 = miller.array(my_millerset1,data=data1)
        merged1 = my_miller1.merge_equivalents().array()

        my_millerset2 = miller.set(crystal_symmetry,indices=indices2)
        my_miller2 = miller.array(my_millerset2,data=data2)
        merged2 = my_miller2.merge_equivalents().array()

        # Obtain common set of reflections
        common1 = merged1.common_set(merged2)
        common2 = merged2.common_set(merged1)
        # Deal with only 1 or 2 common reflections in small wedges
        if (len(common1.indices()) == 1 or len(common1.indices()) == 2):
            return(0)
        else:
            # Calculate correlation between the two datasets.
            cc = flex.linear_correlation(common1.data(),common2.data())
            self.logger.debug('HCMerge::Linear Correlation Coefficient for %s = %s.' % (str(in_file),str(cc.coefficient())))
            return(cc.coefficient())


    def get_cc(self, in_files):
        """
        Calculate correlation coefficient (CC) between two datasets.  Uses cctbx.
        """

        # Read in reflection files
        file1 = reflection_file_reader.any_reflection_file(file_name=in_files[0])
        file2 = reflection_file_reader.any_reflection_file(file_name=in_files[1])

        # Convert to miller arrays
        # ma[2] has I and SIGI
        my_miller1 = file1.as_miller_arrays(merge_equivalents=False)
        my_miller2 = file2.as_miller_arrays(merge_equivalents=False)

        # Create miller arrays for each dataset and merge equivalent reflections

        # Obtain common set of reflections
        common1 = my_miller1[0].common_set(my_miller2[0])
        common2 = my_miller2[0].common_set(my_miller1[0])

        # Calculate correlation between the two datasets.
        cc = flex.linear_correlation(common1.data(),common2.data())
        return(cc.coefficient())

    def scale(self, in_file, out_file, VERBOSE=False):
        """
        Scaling files using AIMLESS
        in_file = prefix for input mtz file from POINTLESS
        out_file = prefix for output mtz file
        """

        self.logger.debug('HCMerge::Scale with AIMLESS in_file: %s as out_file: %s' % (in_file,out_file))
        command = []
        command.append('aimless hklin '+in_file+'_pointless.mtz hklout '+out_file+'_scaled.mtz > '+out_file+'_scaled.log <<eof \n')
        command.append('bins 10 \n')
        command.append('scales constant \n')
        command.append('anomalous on \n')
        command.append('output mtz scalepack merged \n')
        if self.resolution:
            command.append('resolution high %s \n' % self.resolution)
#        command.append('END \n')
        command.append('eof \n')
        comfile = open(in_file+'_aimless.sh','w')
        comfile.writelines(command)
        comfile.close()
        os.chmod(in_file+'_aimless.sh',0755)
        p = subprocess.Popen(self.cmd_prefix+' ./'+in_file+'_aimless.sh',
                             shell=True,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE).wait()

        # Check for maximum resolution and re-run scaling if resolution is too high
        scalog = open(out_file+'_scaled.log', 'r').readlines()
        if self.resolution:
            pass
        else:
            for num,line in enumerate(scalog):
                if line.startswith('Estimates of resolution limits: overall'):
                    # Go to the next line to check resolution
                    if scalog[num+1].endswith('maximum resolution\n'):
                        break
                    elif scalog[num+2].endswith('maximum resolution\n'):
                        break
                    # Make exception for really weak data
                    elif scalog[num+1].endswith('WARNING: weak data, all data below threshold'):
                        self.results['errormsg'].append('Weak Data.  Check %s_scaled.log.\n' % out_file)
                        break
                    elif scalog[num+2].endswith('WARNING: weak data, all data below threshold'):
                        self.results['errormsg'].append('Weak Data.  Check %s_scaled.log.\n' % out_file)
                        break
                    else:
                        new_res = min(scalog[num+1].split()[8].rstrip('A'),scalog[num+2].split()[6].rstrip('A'))
                        self.logger.debug('HCMerge::Scale resolution %s' % new_res)
                        for num,itm in enumerate(command):
                            if itm == 'END \n':
                                command.insert(num, 'resolution high %s \n' % new_res)
                                break
                        comfile = open(out_file+'_aimless.sh','w')
                        comfile.writelines(command)
                        comfile.close()
                        p = subprocess.Popen(self.cmd_prefix+' ./'+in_file+'_aimless.sh',
                                             shell=True,
                                             stdout = subprocess.PIPE,
                                             stderr = subprocess.PIPE).wait()

    def parse_aimless(self, in_file_prefix):
        """
        Parse the aimless logfile in order to pull out data for graph, and a results dictionary
          (for the plots and the results table).
        Returns a dictionary for graphs, dictionary for results.

        graphs dictionary - key = name of table
                          value = list of table rows where row0 (first row) holds the the column labels
                                    each row is a list
        results dictionary - key = name of result value
                           value = list of three numbers, 1 - Overall
                                                          2 - Inner Shell
                                                          3 - Outer Shell
        """
        self.logger.debug('HCMerge::Parse AIMLESS %s_scaled.log for statistics.' % in_file_prefix)

        # The list 'table_list' contains the names (as given in the aimless log) of the tables
        # you wish to extract data from.
        # Only tables with these names will be pulled out.
        table_list = ['Analysis against all Batches for all runs',
                      'Analysis against resolution',
                      'Completeness, multiplicity, Rmeas v. resolution',
                      'Correlations within dataset']

        flag = 0
        anom_cut_flag = 0
        results = {}
        graphs = {}
        scalog = open(in_file_prefix+'_scaled.log','r').readlines()
        # Remove all the empty lines
        scalog = [x for x in scalog if x !='\n']

        for line in scalog:
            if 'TABLE' in line:
                for title in table_list:
                    if title in line:
                        # Signal the potential start of a table (flag = 1), get title as key
                        # for dict and reinitialize the data lists.
                        table_title = line.rsplit(':',2)[1].rsplit(',',1)[0].strip()
                        data = []
                        flag = 1
            elif flag == 1:
                # Start of a table
                if line.startswith('$$'):
                    flag = 2
            elif flag == 2:
                # End of a table
                if line.startswith('$$'):
                    graphs[table_title] = data
                    flag = 0
                # Grab column headers for table
                elif len(line) > 0 and line.endswith('$$ $$\n'):
                    sline = line.strip('$$ $$\n').split()
                    data.append(sline)
                elif len(line) > 0 and line.split()[0].isdigit():
                    sline = line.split()
                    data.append(sline)
                    if anom_cut_flag == 1:
                        if sline[3] == '-' or sline[7] =='-':
                            pass
                        else:
                            anom_cc = float(sline[3])
                            anom_rcr = float(sline[7])
                            if anom_cc >= 0.3:
                                results['CC_cut'] = [ sline[2], sline[3] ]
                            if anom_rcr >= 1.5:
                                results['RCR_cut'] = [ sline[2], sline[7]]
                elif 'GRAPHS: Anom & Imean CCs' in line:
                # Signal for start of the anomalous table, to obtain CC_anom and RCR_anom
                    anom_cut_flag = 1
                elif anom_cut_flag == 1:
                    if line.startswith('Overall'):
                        anom_cut_flag = 0
                        results['CC_anom_overall'] = line.split()[1]
                        results['RCR_anom_overall'] = line.split()[5]
            # Grab statistics from results table at bottom of the log
            #bin resolution limits
            elif 'Low resolution limit' in line:
                results['bins_low']=line.rsplit(None,3)[1:4]
            elif 'High resolution limit' in line:
                results['bins_high'] = line.rsplit(None,3)[1:4]

            #Rmerge
            elif 'Rmerge  (within I+/I-)' in line:
                results['rmerge_anom'] = line.rsplit(None,3)[1:4]
            elif 'Rmerge  (all I+ and I-)' in line:
                results['rmerge_norm'] = line.rsplit(None,3)[1:4]

            #Rmeas
            elif 'Rmeas (within I+/I-)' in line:
                results['rmeas_anom'] = line.rsplit(None,3)[1:4]
            elif 'Rmeas (all I+ & I-)' in line:
                results['rmeas_norm'] = line.rsplit(None,3)[1:4]

            #Rpim
            elif 'Rpim (within I+/I-)' in line:
                results['rpim_anom'] = line.rsplit(None,3)[1:4]
            elif 'Rpim (all I+ & I-)' in line:
                results['rpim_norm'] = line.rsplit(None,3)[1:4]

            #Number of refections
            elif 'Total number of observations' in line:
                results['total_obs'] = line.rsplit(None,3)[1:4]
            elif 'Total number unique' in line:
                results['unique_obs'] = line.rsplit(None,3)[1:4]

            #I/sigI
            elif 'Mean((I)/sd(I))' in line:
                results['isigi'] = line.rsplit(None,3)[1:4]

            #CC1/2
            elif 'Mn(I) half-set correlation CC(1/2)' in line:
                results['CC_half'] = line.rsplit(None,3)[1:4]

            #Completeness
            elif line.startswith('Completeness'):
                results['completeness'] = line.rsplit(None,3)[1:4]
            elif 'Anomalous completeness' in line:
                results['anom_completeness'] = line.rsplit(None,3)[1:4]

            #Multiplicity
            elif line.startswith('Multiplicity'):
                results['multiplicity'] = line.rsplit(None,3)[1:4]
            elif 'Anomalous multiplicity' in line:
                results['anom_multiplicity'] = line.rsplit(None,3)[1:4]

            #Anomalous indicators
            elif 'DelAnom correlation between half-sets' in line:
                results['anom_correlation'] = line.rsplit(None,3)[1:4]
            elif 'Mid-Slope of Anom Normal Probability' in line:
                results['anom_slope'] =  line.rsplit(None,3)[1]

            #unit cell
            elif line.startswith('Average unit cell:'):
                results['scaling_unit_cell'] = line.rsplit(':',1)[1].split()

            #spacegroup
            elif line.startswith('Space group:'):
                results['scale_spacegroup'] = line.rsplit(':',1)[1].strip()

        return(results,graphs)

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
        Y = [] # The list of distances, our equivalent of pdist
        for pair in self.id_list.keys():
            # grab keys with stats of interest, but ensure that keys go in numerical order
            cc = 1 - self.results[pair]['CC']
            Y.append(cc)
        self.logger.debug('HCMerge::Array of distances for matrix = %s' % Y)
        Z = linkage(Y,method=method) # The linkage defaults to single and euclidean
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
        node_list = {} # Dict to hold new nodes
        for cnt,row in enumerate(Z):
            node_list[len(Z)+cnt+1] = [int(row[0]), int(row[1])]
        # Set up for making groups of all clusters below cutoff.  Turn most_wedges into a dict.
        # Default to most closely linked pair of wedges
        if any(item for item in Z.tolist() if item[2] < cutoff):
            most_wedges = {}
        else:
            most_wedges = {0: ([int(Z[0][0]),int(Z[0][1])], Z[0][2])}
        for cnt,item in enumerate(Z[::-1]):
            # Apply cutoff
            if item[2] <= cutoff:
                # Dict holding clusters using node ID as key
                most_wedges[cnt] = [int(item[0]),int(item[1])], item[2]
        # iteratively go through dict values and reduce to original leaves
        for i in most_wedges.values():
            # use set because it is faster than list
            while set(i[0]).intersection(set(node_list.keys())):
                self.replace_wedges(i[0],node_list)

        # Convert numbers to filenames
        for i in most_wedges:
            for cnt,item in enumerate(most_wedges[i][0]):
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
        for count,item in enumerate(wedges):
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
        # lists for running the multiprocessing
        jobs                               = []
        
        # Check for all_clusters flag
        if self.all_clusters:
            for cnt,cluster in enumerate(wedge_files.values()):
                combine_all = Process(target=self.combine(cluster[0], self.prefix+str(cnt)))
                jobs.append(combine_all)
                combine_all.start()
            for pair in jobs:
                pair.join()
            # Scale the files with aimless
            for cnt,itm in enumerate(wedge_files):
                scale = Process(target=self.scale,args=(self.prefix+str(cnt),self.prefix+str(cnt)))
                jobs.append(scale)
                scale.start()
            for pair in jobs:
                pair.join()
            for cnt,itm in enumerate(wedge_files):
                new_prefix = self.prefix+str(cnt)
                self.results[new_prefix],self.graphs[new_prefix] = self.parse_aimless(self.prefix+str(cnt))
                self.results[new_prefix]['files'] = wedge_files[itm][0]
                self.results[new_prefix]['CC'] = 1 - wedge_files[itm][1]
                self.merged_files.append(new_prefix)
        else:
            combine_all = Process(target=self.combine,args=(next(wedge_files.itervalues())[0],self.prefix))
            combine_all.start()
            combine_all.join()
            # Scale the files with aimless
            scale = Process(target=self.scale,args=(self.prefix,self.prefix))
            scale.start()
            scale.join()
            self.results[self.prefix],self.graphs[self.prefix] = self.parse_aimless(self.prefix)
            self.results[self.prefix]['files'] = next(wedge_files.itervalues())[0]
            self.results[self.prefix]['CC'] = 1 - next(wedge_files.itervalues())[1]
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
                dendrogram(matrix, color_threshold = 1 - self.cutoff, labels = self.data_files, leaf_rotation = -90)
                matplotlib.pylab.xlabel('Datasets')
                matplotlib.pylab.ylabel('1 - Correlation Coefficient')
                f = matplotlib.pylab.gcf()
                f.set_size_inches([8,8])
                f.subplots_adjust(bottom=0.4)
            else:
                dendrogram(matrix, color_threshold = 1 - self.cutoff)
            # Save a PNG of the plot
            matplotlib.pylab.savefig(self.prefix+'-dendrogram.png', dpi=resolution)
        except:
            dendrogram(matrix, color_threshold = 1 - self.cutoff, no_plot=True)
            self.logger.error('HCMerge::matplotlib.pylab unavailable in your version of cctbx.  Plot not generated.')
        
    def write_db(self):
        """
        Writes the results to a database, currently MySQL for RAPD
        """

        self.logger.debug('HCMerge::Write Results to Database')

    def make_log(self, files):
        """
        Makes a log file of the merging results
        files = list of results files, prefix only
        """

        self.logger.debug('HCMerge::Write tabulated results to %s' % (self.prefix + '.log'))

        # Make a comparison table of results
        # Set up list of lists for making comparison table
        table = [['', 'Correlation', 'Space Group', 'Resolution', 'Completeness', 
                  'Multiplicity', 'I/SigI', 'Rmerge', 'Rmeas', 'Anom Rmeas',
                  'Rpim', 'Anom Rpim', 'CC 1/2', 'Anom Completeness', 'Anom Multiplicity',
                  'Anom CC', 'Anom Slope', 'Total Obs', 'Unique Obs']]
        key_list = ['CC', 'scale_spacegroup', 'bins_high', 'completeness', 'multiplicity',
                    'isigi', 'rmerge_norm', 'rmeas_norm', 'rmeas_anom',
                    'rpim_norm', 'rpim_anom', 'CC_half', 'anom_completeness',
                    'anom_multiplicity', 'anom_correlation', 'anom_slope', 'total_obs', 'unique_obs']
        for file in files:
            row = [ file ]
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

    def cleanup(self):
        """
        Remove excess log files and tidy up the directory.
        safeext = list of file extensions which should be saved.
        """

        self.logger.debug('HCMerge::Cleanup excess log files.')
        killlist = []
        killext = ['_pointless.sh', '_pointless.mtz', '_pointless.log', '_pointless_p1.log']
        for ext in killext:
            for prefix in self.id_list:
                killlist.append(prefix+ext)
#        for itm in self.merged_files:
#            killlist.append(itm+'_aimless.sh')
        filelist = [ f for f in os.getcwd() if f.endswith(".sh") or f.endswith(".log")
                     or f.endswith(".mtz")]
        purgelist = set(filelist).intersection( set(killlist) )
#        purgelist = [f for f in filelist if f not in safelist]
        for file in purgelist:
            os.remove(file)

    def store_dicts(self, dicts):
        """
        Create pickle files of dicts with CC, aimless stats, combinations already processed, merged file list
        """

        self.logger.debug('HCMerge::Pickling Dicts')
        file = open(self.prefix + '.pkl','wb')
        pickle.dump(dicts,file)
        file.close()

    def get_dicts(self, file):
        """
        Extract dicts out of pickle file
        """

        self.logger.debug('HCMerge::UnPickling Dicts')
        tmp = pickle.load(open(file,'rb'))
        for itm,val in tmp.iteritems():
        	setattr(self, itm, val)

    def rerun(self, pkl_file):
        """
        Re-running parts of the agent
        self.dirs['data'] should be self.data_dir when pulled from pkl file
        """

        self.logger.debug('HCMerge::rerun')
        self.get_dicts(pkl_file)
        if self.start_point == 'clustering':
			self.merged_files = []						# List for storing new merged files.
        	# Make new COMBINE directory and move data files over
			combine_dir = self.create_subdirectory(prefix='COMBINE', path=self.dirs['work'])
			os.chdir(combine_dir)
			self.logger.debug('HCMerge::Copying files from %s to %s' % (self.data_dir,combine_dir))
			for file in self.data_files:
				shutil.copy(self.data_dir + '/' + file, combine_dir)

			# Make relationship matrix
			matrix = self.make_matrix(self.method)
        	   
            # Find data above CC cutoff.  Key 0 is most wedges and above CC cutoff
			wedge_files = self.select_data(matrix, 1 - self.cutoff)
    
            # Merge all wedges together
			self.merge_wedges(wedge_files)
    
            # Store the dicts for future use
			self.store_dicts({'data_files': self.data_files, 'id_list': self.id_list, 
                              'results': self.results, 'graphs': self.graphs, 'matrix': matrix,
                              'merged_files': self.merged_files})
                              
			# Make the summary text file for all merged files
			self.make_log(self.merged_files)
                              
        else:
            pass
        # Make the dendrogram and write it out as a PNG
        self.make_dendrogram(self.matrix, self.dpi)
            
    def create_subdirectory(self, n_dir_max=None, prefix="TEMP", path="", directory_number=None):
        """
        Make subdirectories as needed for all the many script, log and mtz files
        Is the same code as phenix create_temp_directory.  Replace if distributed with phenix.
        """
        
        if n_dir_max is None: 
            n_dir_max=1000
            temp_dir=prefix
        if directory_number is None:
            starting_number = 1
            ending_number = n_dir_max
            e = "Maximum number of directories is %d" %(n_dir_max)
        else:
            starting_number = directory_number
            ending_number = directory_number
            e = "The directory %s could not be created (it may already exist)" %(
                os.path.join(path, prefix + "_" + str(directory_number)))

        for i in xrange(starting_number, ending_number + 1):
            temp_dir = os.path.join(path, prefix + "_" + str(i))
            try:
                if not os.path.exists(temp_dir):
                    os.mkdir(temp_dir)
                    return os.path.join(os.getcwd(), temp_dir)
            except Exception, e: pass
        raise ValueError("Unable to create directory %s " %(temp_dir)+ "\nError message is: %s " %(str(e)))

 
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


if __name__ == '__main__':
    # Command Line Execution
    from optparse import OptionParser # For commandline option parsing

    LOG_FILENAME = 'hcmerge.log'
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=1000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    echo = logging.StreamHandler(sys.stdout)
    echo.setLevel(logging.DEBUG)
    echo.setFormatter(formatter)
    logger.addHandler(echo)

    command = 'MERGE'
    working_dir = os.getcwd()
    dirs = {'work': working_dir}
 
    usage = "usage: %prog [options] filelist or pickle file"
    parser = OptionParser(usage=usage)
    parser.add_option("-a", "--all", action="store_true", dest="all_clusters", default=False,
                      help = "make all agglomerative clusters greater than cutoff value")
    parser.add_option("-c", "--cutoff", dest="cutoff", type="float", default=0.95,
                      help = "set a percentage cutoff for the similarity between datasets")
    parser.add_option("-d", "--dpi", dest="dpi", type="int", default=100,
                      help = "set resolution in dpi for the dendrogram image")
    parser.add_option("-l", "--labels", action="store_true", dest="labels", default=False,
                      help = "add file names and labels to the dendrogram")
    parser.add_option("-n", "--nproc", dest="nproc", type="int", default=0,
                      help = "set number of processors")
    parser.add_option("-m", "--method", dest="method", type="string", default="complete",
                      help = "set alternative clustering method: single, complete, average, or weighted")
    parser.add_option("-o", "--output_prefix", dest="prefix", type="string", default="merged",
                      help = "set a prefix for output files. Used in rerun as the name of the .pkl file")
    parser.add_option("-p", "--precheck", action="store_false", dest="precheck", default=True,
                      help = "precheck for duplicate or incorrect data files, default=True")
#    parser.add_option("-q", "--qsub", action="store_true", dest="cluster_use", default=False,
#                      help = "use qsub on a cluster to execute the job, default is sh for a single computer")
    parser.add_option("-r", "--resolution", dest="resolution", type= "float", default=0,
                      help = "set a resolution cutoff for merging data")
    parser.add_option("-s", "--spacegroup", dest="spacegroup", type="string",
                      help = "set a user-defined spacegroup")
#    parser.add_option("-u", "--unit_cell", dest="cell", type="string",
#                      help = "set a unit cell for unmerged scalepack files")
    parser.add_option("-v", "--verbose", action="store_false", dest="cleanup_files", default=True,
                      help = "do not clean up excess script and log files")
    parser.add_option("-x", "--rerun", dest="start_point", type="string", default="start",
                      help = "use pickle file and run merging again starting at: clustering, dendrogram")
    (options,args) = parser.parse_args()
    files = args
    if len(files) > 1:
        # Get absolute path in case people have relative paths
        datasets = [os.path.abspath(x) for x in files]
    elif len(files) == 0:
        # print 'MergeMany requires a text file with a list of files (one per line) or a list of files on the command line'
        parser.print_help()
        sys.exit(9)
    elif files[0].split('.')[1].lower() == 'pkl':
        datasets = files[0]
    else:
        # Read in text file with each file on a separate line
        datasets = open(files[0],'rb').readlines()
        # Remove entries created from the blank lines in the file.  Compensating for returns at end of file.
        datasets = filter(lambda x: x != '\n',datasets)
        # Remove empty space on either side of the filenames
        datasets = [os.path.abspath(x.strip()) for x in datasets]


#    datasets = ['/gpfs5/users/necat/rapd/copper/trunk/integrate/2012-10-24/cmd13_1_1/cmd13_1_1_1/cmd13_1_1_1_XDS.HKL',
#                '/gpfs5/users/necat/rapd/copper/trunk/integrate/2012-10-24/cmd13_1_2/cmd13_1_2_2/cmd13_1_2_2_XDS.HKL'
#                ]
    settings = {'cmdline': True,
                'all_clusters': options.all_clusters,
                'dpi': options.dpi,
                'precheck': options.precheck,
                'cutoff': options.cutoff,
#                'cell': options.cell,
                'labels': options.labels,
                'prefix': options.prefix,
                'user_spacegroup': 0, # Default the user_spacegroup to None.
                'resolution': options.resolution,
                'cleanup_files': options.cleanup_files,
                'work_directory': working_dir,
                'work_dir_override': 'False',
                'process_id': '0',
                'cluster_use': 'False',
                'nproc': options.nproc,
                'start_point': options.start_point,

                }
    # Check to see if the user has set a spacegroup.  If so, then change from symbol to IUCR number.  Add to settings.
    try:
        if options.spacegroup:
            settings['user_spacegroup'] = space_group_symbols(options.spacegroup).number()
    except:
        print 'Unrecognized space group symbol.'
        sys.exit()
    try:
        method_list = ['single', 'complete', 'average', 'weighted']
        if [i for i in method_list if i in options.method]:
            settings['method'] = options.method
    except:
        print 'Unrecognized method.'
        sys.exit()
    try:
        rerun_list = ['start', 'clustering', 'dendrogram']
        if [i for i in rerun_list if i in options.start_point]:
            settings['start_point'] = options.start_point
    except:
        print 'Unrecognized option for rerunning HCMerge.'
        sys.exit()
    # Deal with negative integers and what happens if cpu_count() raises NotImplementedError
    if options.nproc <= 0:
        try:
            settings['nproc'] = cpu_count()
        except:
            settings['nproc'] = 1

    controller_address = ['127.0.0.1' , 50001]
    input = [command, dirs, datasets, settings, controller_address]
    # Call the handler.
    T = MergeMany(input, logger)
else:
    # Execution when Module is Imported
    # Set up logging
    LOG_FILENAME = '/gpfs5/users/necat/kay/rapd/merge.logger'
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=1000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    command = 'MERGE'
    dirs = { 'work': '/gpfs5/users/necat/kay/rapd/ribo/'
            }
    datasets = ['/gpfs5/users/necat/rapd/copper/trunk/integrate/2012-10-24/cmd13_1_1/cmd13_1_1_1/cmd13_1_1_1_XDS.HKL',
                '/gpfs5/users/necat/rapd/copper/trunk/integrate/2012-10-24/cmd13_1_2/cmd13_1_2_2/cmd13_1_2_2_XDS.HKL'
                ]
    settings = {'cmdline': False,
                'all_clusters': False,
                'labels': False,
                'method': 'complete',
                'cutoff': 0.95,
                'prefix': 'merged',
                'user_spacegroup': 0,
                'resolution': 0,
                'cleanup_files': True,
                'work_directory': '/gpfs5/users/necat/kay/rapd/',
                'work_dir_override': 'False',
                'process_id': '0',
                'cluster_use': True,
                'nproc': cpu_count(),

                }
    controller_address = ['127.0.0.1' , 50001]
    input = [command, dirs, datasets, settings, controller_address]
    # Call the handler.
    T = MergeMany(input, logger)

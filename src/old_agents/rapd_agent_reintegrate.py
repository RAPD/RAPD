"""
This file is part of RAPD

Copyright (C) 2011-2018, Cornell University
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

__created__ = "2011-02-24"
__maintainer__ = "David Neau"
__email__ = "dneau@anl.gov"
__status__ = "Production"

from multiprocessing import Process, Queue, Pipe
from rapd_communicate import Communicate
from rapd_agent_stats import AutoStats
#import jon_utilities as utils
from numpy import interp
import math
import os
import os.path
from xdsme.xds2mos import Xds2Mosflm
import logging
import logging.handlers
import pexpect
import subprocess
import time
import rapd_beamlinespecific as BLspec
import jon_utilities as Utils

class ReIntegration(Process, Communicate):
    '''
    This class accepts instructions from rapd_cluster in order to reintegrate
    previously collected data.  Reintegration can be done via xds or xia2.
    '''


    def __init__(self, input, logger):
        '''
        Constructor
        
        input is the tuple passed into this process, containing the command
        to be executed, a dict of relevant directories, a dict of data 
        parameters from the original integration, a dict of settings - 
        including the new request - and the controller address needed for
        rapd_communicate's PassBack2 function.
        
        logger is for logging progress and results of the process.
        '''
        self.input = input[0:4]
        self.controller_address = input[-1]
        self.logger = logger
        self.process_id = input[3]['process_id']
        self.cluster = self.input[3]['multiprocessing']
        self.summary = {}
        self.results = {'status' : 'Error'}
        Process.__init__(self,name='ReIntegration')
        self.start()
    
    def run(self):
        self.logger.debug('ReIntegration::run')
        self.preprocess()
        self.process()
        self.postprocess()
    
    def preprocess(self):
        '''
        Set up directory for reprocessing.
        '''
        reproc_dir = self.input[3]['request']['work_dir']
        if os.path.isdir(reproc_dir) == False:
            os.makedirs(reproc_dir)
        os.chdir(reproc_dir)
    
    def process(self):
        '''
        1. Check whether to use xds or xia2.
        2. Prepare for integration.
        3. Reintegrate.
        4. Send results back to calling process.
        '''
        self.logger.debug('ReIntegration::process')
        # Expand the input tuple.
        command, dirs, data, settings = self.input
        data_dir = dirs['data_root_dir']
        original_data = data['original']
        request = settings['request']
        results_queue = Queue()
        if command == 'XIA2':
            reintegration = Process(target = self.xia2_reintegration,
                                    args = (data_dir, original_data, request,
                                            results_queue) )
            reintegration.start()
        elif command == 'XDS':
            reintegration = Process(target = self.xds_reintegration,
                                    args = (data_dir, original_data, request,
                                            results_queue) )
            reintegration.start()
        else:
            self.logger.debug('Command sent to ReIntegration not XIA2 or XDS.')
            return()
        
        self.results = results_queue.get()
        if self.results['status'] == 'FAILED':
            self.results['status'] = 'Error'
        elif self.results['status'] == 'SUCCESS':
            self.logger.debug("self.results['files']['mtzfile'] = %s" % self.results['files']['mtzfile'])
            analysis_result = self.run_analysis(self.results['files']['mtzfile'], dirs['work'], self.results['first_image'], self.results['osc_range'])
            if analysis_result == 'FAILED':
                self.logger.debug('Stats analysis failed.')
        
    def postprocess(self):
        '''
        1. Send results to controlling process.
        2. Shutdown this class.
        '''
        self.logger.debug('ReIntegration::postprocess')
        self.logger.debug(self.results)
        self.input.append(self.results)
        self.sendBack2(self.input)
        #os._exit(0)
        
    
    def xia2_reintegration(self, data_dir, data, request, result):
        '''
        Reintegrate using xia2.
        '''
        crystal = '_'.join((data['image_prefix'],str(data['run_number'])))
        xinfo_name = crystal + '.xinfo'
        xiafiles = {'xia_log' : 'xia2.txt',
                    'xinfo' : xinfo_name}
        image_name = '_'.join((crystal, str(request['frame_start']).zfill(3) ))
        crystal = data['image_prefix']
        image_name += '.img'
        
        xia2_info = {'crystal' : crystal,
                     'project' : 'RAPD_REINT',
                     'wavelength' : request['wavelength'],
                     'image_name' : image_name,
                     'data_directory' : data['images_dir'],
                     'xbeam' : data['beam_center_x'],
                     'ybeam' : data['beam_center_y'],
                     'distance' : data['distance'],
                     'start' : str(request['frame_start']),
                     'end' : str(request['frame_finish']),
                     'xinfo' : xinfo_name
                     }
        if request.has_key('spacegroup'):
            xia2_info['spacegroup'] = request['spacegroup']
        self.create_xinfo(xia2_info)
        self.xia2_run(xinfo_name)
        
        last_line = open('xia2.txt','r').readlines()[-1]
        if last_line != 'Status: normal termination\n':
            self.logger.debug('xia2 failure, check logs!')
            results['status'] = 'FAILED'
            results.put(results)
            return()
        
        aimless_log = '_'.join((xia2_info['project'], crystal, 'aimless.log'))
        aimlessLog = os.path.join('LogFiles', aimless_log)
        results = self.prepare_results(aimlessLog, request['frame_start'],
                  request['frame_finish'], 'Xia2')
        
        mtz = '_'.join((xia2_info['project'], crystal, 'scaled.mtz'))
        mtzfile = os.path.join(crystal, 'scale', mtz)
        correct = os.path.join(crystal, 'DATA/DATA/integrate','CORRECT.LP')
        pointless = mtzfile.replace('scaled', 'sorted')
        os.system('mv %s pointless.mtz' % pointless)
        
        final_mtz = self.finish_data(mtzfile)
        if final_mtz != 'failed' and os.path.isfile(final_mtz):
            results.update({'status' : 'SUCCESS'})
            Xds2Mosflm(xds_file=correct,mat_file='reference.mat')
            sg = results['summary']['scale_spacegroup']
            cell = results['summary']['scaling_unit_cell']
            sca = 'ANOM.sca'
            shelxc_results = self.process_shelxC(cell, sg, sca)
            if shelxc_results != None:
                self.insert_shelx_results(shelxc_results)
            results['shelx_results'] = shelxc_results
        
        work_dir = request['work_dir']    
        if results['status'] == 'SUCCESS':
            results['files'] = self.clean_fs_xia2(work_dir, data['image_prefix'],
                                                  data['run_number'])
        result.put(results)
        return()
    
    
    
    def create_xinfo(self, xia2_info):
        '''
        Creates the .xinfo file to run xia2.
        '''
        self.logger.debug('ReIntegration::create_xinfo')
        
        content = ['BEGIN PROJECT %s\n' % xia2_info['project']]
        content.append('BEGIN CRYSTAL %s\n' % xia2_info['crystal'])
        content.append('BEGIN HA_INFO\n ATOM SE \n END HA_INFO\n\n')
        content.append('BEGIN WAVELENGTH DATA\n')
        content.append('WAVELENGTH %s\n' % xia2_info['wavelength'])
        content.append('END WAVELENGTH DATA\n')
        content.append('BEGIN SWEEP DATA\n')
        content.append('WAVELENGTH DATA\n')
        content.append('IMAGE %s\n' % xia2_info['image_name'])
        content.append('DIRECTORY %s\n' % xia2_info['data_directory'])
        content.append('BEAM %s %s\n' % (xia2_info['xbeam'],xia2_info['ybeam']))
        content.append('DISTANCE %s\n' % xia2_info['distance'])
        content.append('START_END %s %s\n' 
                       %(xia2_info['start'], xia2_info['end']))
        content.append('END SWEEP DATA\n\n')
        if xia2_info.has_key('spacegroup'):
            content.append('USER_SPACEGROUP %s' % xia2_info['spacegroup'])
        content.append('END CRYSTAL %s\n' % xia2_info['crystal'])
        content.append('END PROJECT %s\n' % xia2_info['project'])
        
        self.write_file(xia2_info['xinfo'], content)
        return()
    
    def xia2_run(self, xinfo):
        '''
        Controls the running of xia2.
        '''
        self.logger.debug('ReIntegration::xia2_run')
        if self.cluster:
            xia_command = ('"xia2 -3dr -xparallel 16 -parallel 8 -xinfo %s"'
                           % xinfo)
            command = ('qsub -sync y -b y -j y -N XIA2 -cwd %s' % xia_command)
        else:
            command = ('xia2 -3dr -xparallel 2 -parallel 2 -xinfo $s' % xinfo)
        
        p = pexpect.spawn(command)
        p.wait()
        return()
    
    def xds_reintegration(self, data_dir, data, request, result):
        '''
        Reintegrate data using xds.
        1. prep an input file.
        2. run xds jobs - XYCORR, INIT, COLSPOT, and IDXREF.
        3. Check the the initial jobs succeeded.
        4. run xds jobs - DEFPIX, INTEGRATE, and CORRECT.
        5. run pointless and aimless.
        6. Finish up integration.
        7. Return results.
        '''
        if request.has_key('spacegroup'):
            if request['spacegroup'] != 0:
                symm_info = self.find_xds_symm(request['spacegroup'])
                self.logger.debug('symm_info = %s' %symm_info)
            else:
                symm_info = None
        else:
            symm_info = None
        work_dir = request['work_dir']
        # If xds input file exists from original integration modify it.
        # Otherwise, create one from scratch.
        if '.log' in data['xds_log']:
            xds_input = data['xds_log'].replace('.log','.inp')
        elif '.LOG' in data['xds_log']:
            xds_input = data['xds_log'].replace('.LOG','.INP')

        if os.path.isfile(xds_input):
            run_data = self.modify_xdsinput(xds_input, request['frame_start'],
                                 request['frame_finish'])
        else:
            self.logger.debug ('Previous XDS input file does not exist.')
            results['status'] = 'FAILED'
            result.put(results)
        # Run inital xds jobs.
        #self.xds_run()
        self.xds_run2()
        
        # Modify XDS.INP for DEFPIX, INTEGRATE, and CORRECT.
        # Then run xds again.
        self.modify_input_for_integration(symm_info)
        #self.xds_run()
        self.xds_run2()
        
        # Run pointless and aimless.
        scaling_results = Queue()
        aimless_log = self.run_scaling(scaling_results,symm_info)
        results = self.prepare_results('aimless.log', request['frame_start'],
                  request['frame_finish'], 'XDS')
        correct = os.path.join(work_dir,'CORRECT.LP')
        
        final_mtz = self.finish_data('scaled.mtz')
        if final_mtz != 'failed' and os.path.isfile(final_mtz):
            results.update({'status' : 'SUCCESS'})
            Xds2Mosflm(xds_file=correct,mat_file='reference.mat')
            sg = results['summary']['scale_spacegroup']
            cell = results['summary']['scaling_unit_cell']
            sca = 'ANOM.sca'
            #shelxc_results = self.process_shelxC(cell, sg, sca)
            #if shelxc_results != None:
            #    self.insert_shelx_results(shelxc_results)
            #results['shelx_results'] = shelxc_results
            
        if results['status'] == 'SUCCESS':
            results['files'] = self.clean_fs_xds(work_dir, data['image_prefix'],
                                                  data['run_number'])
        results['first_image'] = run_data['first_image']
        results['osc_range'] = run_data['osc_range']
        result.put(results)
        return()
    
    def find_xds_symm(self, spacegroup):
        '''
        Converts spacegroup symbol to spacegroup number.
        And looks for appropriate unit cell constants.
        '''
        sym_dict = {'P1' : 1,
                    'P2' : 3, 'P21' : 4,
                    'C2' : 5,
                    'P222' : 16, 'P2221' : 17, 'P21212' : 18, 'P212121' : 19,
                    'C222' : 21, 'C2221' : 20,
                    'F222' : 22,
                    'I222' : 23, 'I212121' : 24,
                    'P4' : 75, 'P41' : 76, 'P42' : 77, 'P43' : 78,
                    'P422' : 89, 'P4212' : 90,
                    'P4122' : 91, 'P41212' : 92, 'P4222' : 93, 'P42212' : 94,
                    'P4322' : 95, 'P43212' : 96,
                    'I4' : 79, 'I41' : 80, 'I422' : 97, 'I4122' : 98,
                    'P3' : 143, 'P31' : 144, 'P32' : 145, 'P312' : 149, 
                    'P321' : 150, 'P3112' : 151, 'P3121' : 152, 'P3212' : 153,
                    'P3221' : 154, 'P6' : 168, 'P61' : 169, 'P65' : 170,
                    'P62' : 171, 'P64' : 172, 'P63' : 173, 'P622' : 177,
                    'P6122' : 178, 'P6522' : 179, 'P6222' : 180, 'P6422' : 181,
                    'P6322' : 182,
                    'R3' : 146, 'R32' : 155,
                    'P23' : 195, 'P213' : 198, 'P432' : 207, 'P4232' : 208,
                    'P4332' : 212, 'P4132' : 213,
                    'F23' : 196, 'F432' : 209, 'F4132' : 210,
                    'I23' : 197, 'I213' : 199, 'I432' : 211, 'I4132' : 214
                    }
        #sg_num = sym_dict[spacegroup]
        sg_num = int(spacegroup)
        if sg_num == 1:
            bravais = 'aP'
        elif sg_num in [3,4]:
            bravais = 'mP'
        elif sg_num == 5:
            bravais = 'mC'
        elif sg_num in [16, 17, 18, 19]:
            bravais = 'oP'
        elif sg_num in [21, 20]:
            bravais = 'oC'
        elif sg_num == 22:
            bravais = 'oF'
        elif sg_num in [23,24]:
            bravais = 'oI'
        elif sg_num in [75, 76, 77, 78, 89, 90, 91, 92, 93, 94, 95, 96]:
            bravais = 'tP'
        elif sg_num in [79, 80, 97, 98]:
            bravais = 'tI'
        elif sg_num in [143, 144,145,149,150,151,152,153,154,168,169,170,171,172,173,177,178,179,180,181,182]:
            bravais = 'hP'
        elif sg_num in [146, 155]:
            bravais = 'hR'
        elif sg_num in [195, 198, 207, 208, 212, 213]:
            bravais = 'cP'
        elif sg_num in [196, 209, 210]:
            bravais = 'cF'
        elif sg_num in [197, 199, 211, 214]:
            bravais = 'cI'
        symm_info = [sg_num, bravais]
        return(symm_info)
    
    def write_file(self, filename, file_input):
        '''
        Write a text file from a list of strings.
        '''
        self.logger.debug('write_file: filename = %s' %filename)
        with open(filename, 'w') as file:
            file.writelines(file_input)
        return()
    
    def xds_run(self):
        '''
        Controls running of xds.
        '''
        self.logger.debug('xds_run')
        if self.cluster:
            command = 'qsub -sync y -b y -j y -terse -o XDS.LOG -cwd xds_par'
        else:
            command = 'xds_par > XDS.LOG'
        p = pexpect.spawn(command)
        p.wait()
        return()
    
    def xds_run2(self):
        '''
        Controls running of xds.
        '''
        self.logger.debug('xds_run2')
        #import time
        if self.cluster:
            #import rapd_beamlinespecific as BLspec
            job = Process(target=BLspec.processCluster,args=(self,('xds_par','XDS.LOG','phase2.q')))
        else:
            #import jon_utilities as Utils
            job = Process(target=Utils.processLocal,args=(('xds_par','XDS.LOG'),self.logger))
        job.start()
        while job.is_alive():
           time.sleep(1)
        return()
    
    def modify_xdsinput(self, file, start, last):
        '''
        modify an existing xds input file.
        '''
        xdsinput = open(file, 'r').readlines()
        for i, value in enumerate(xdsinput):
            if value.startswith('JOB='):
                xdsinput[i] = 'JOB=XYCORR INIT COLSPOT IDXREF\n'
            elif value.startswith('SPOT_RANGE'):
                xdsinput[i] = ''
            elif value.startswith('DATA_RANGE'):
                xdsinput[i] = ('DATA_RANGE=%s %s\n' %(str(start), str(last)))
                #if start + 9 <= last:
                #    xdsinput[i]+=('SPOT_RANGE=%s %s\n' %(str(start), str(start + 9)))
                #if start + 89 <= last:
                #    xdsinput[i]+=('SPOT_RANGE=%s %s\n' %(str(start+84), str(start+89))) 
            elif value.startswith('INCLUDE_RESOLUTION_RANGE'):
                splitline = value.split('=')
                lowres = splitline[-1].split(' ')[0]
                xdsinput[i] = ('INCLUDE_RESOLUTION_RANGE=%s 0.0\n' % lowres)
            elif value.startswith('OSCILLATION_RANGE='):
                osc_range = value.strip().split('=')[-1].split('!')[0]
            elif value.startswith('NAME_TEMPLATE'):
                template = value.strip().split('=')[-1]
                pad = template.count('?')
                # replace first instance of '?' with the start image number, padded out with zeros
                # pad + 1 is needed to make sure the full number of digits are placed.
                first_image = template.replace('?', '%d'.zfill(pad+1) % start, 1)
                # replace the remaining '?'s with an empty string to remove them from the template
                first_image = first_image.replace('?','')
                #if '.img' in template:
                #    first_image = template.replace('???','%03d' % start)
                #elif '.cbf' in template:
                #    first_image = template.replace('????','%04d' % start)
            #if value.startswith('SPOT_RANGE'):
            #    xdsinput[i] = ('SPOT_RANGE=%s %s\n' %(str(start), str(last)))
        data = {'first_image':first_image, 'osc_range':osc_range}
        self.write_file('XDS.INP', xdsinput)
        return(data)
    
    def modify_input_for_integration(self, symm):
        '''
        Further modification of XDS.INP for integration and scaling.
        '''
        cell_line = False
        if symm != None:
            idxref = open('IDXREF.LP', 'r').readlines()
            for line in idxref:
                if symm[-1] in line:
                    cell_line = line.split()[-6:]
                    self.logger.debug('bravais = %s' %symm[-1])
                    self.logger.debug('line = %s' %line)
                    self.logger.debug('cell_line = %s' % cell_line)
                    break
        xdsinput = open('XDS.INP','r').readlines()
        for i, v in enumerate(xdsinput):
            if v.startswith('JOB='):
                xdsinput[i] = 'JOB=DEFPIX INTEGRATE CORRECT\n'
        if cell_line:
            unitcell = ''
            for item in cell_line:
                unitcell += '%s ' % item
            xdsinput.append('SPACE_GROUP_NUMBER=%s\n' % symm[0])
            xdsinput.append('UNIT_CELL_CONSTANTS=%s\n' % unitcell)
            xdsinput.append('MAXIMUM_NUMBER_OF_JOBS=16\n')
        self.write_file('XDS.INP', xdsinput)
        return()
    
    def run_scaling(self, update, symm):
        '''
        Controls the running of pointless and aimless, and returns results.
        '''
        # Find a resolution cutoff from the CORRECT.LP file.
        #res_cut = self.find_xds_resolution()
        self.run_pointless(symm)
        aimless_log = self.run_aimless(False)
        new_res_cut = False
        # Examine aimless results to find a new resolution cutoff.
        try:
            res_cut = self.find_aimless_resolution(aimless_log)
        except:
            update.put('Error')
            return()
        if res_cut != False:
            os.system('mv %s old_aimless.log' % aimless_log)
            aimless_log = self.run_aimless(res_cut)
            new_res_cut = self.find_aimless_resolution(aimless_log, res_cut)
        if new_res_cut != False:
            os.system('mv %s old_aimless2.log' % aimless_log)
            aimless_log = self.run_aimless(new_res_cut)
        
        return(aimless_log)
    
    def find_xds_resolution(self):
        '''
        Parse CORRECT.LP to find an inital resoluiton cutoff for aimless.
        '''
        self.logger.debug('find_xds_resoluiton')
        hi_res = False
        try:
            corlog = open('CORRECT.LP','r').readlines()
        except:
            return(hi_res)
        flag = 0
        keyline = 'SUBSET OF INTENSITY DATA WITH SIGNAL/NOISE >= -3.0'
        for line in corlog:
            try:
                if line.split()[-1] == 'INTEGRATE.HKL':
                    # Place holder until I figure out what to do with the ISa.
                    self.logger.debug('ISa = %s' % line.split()[2])
            except:
                pass
            if keyline in line:
                flag = 1
            if flag == 1:
                sline = line.split()
                if (len(sline) == 14 and sline[0][0].isdigit()):
                    if float(sline[8]) < 1.0:
                        new_hi_res = sline[0]
                        # Check to see if new high res cut is greater than old.
                        if hi_res == False or float(new_hi_res) < float(hi_res):
                            hi_res = new_hi_res
                        flag = 0
        return(hi_res)
    
    def run_pointless(self,symm):
        '''
        Controls the running of pointless.
        '''
        self.logger.debug('ReIntegration::run_pointless')
        if os.path.exists('XDS_ASCII.HKL') == False:
  	    raise RuntimeError('XDS_ASCII.HKL does not exist')
        mtz = 'pointless.mtz'
        log = 'pointless.log'
        if symm == None:
            command = ('pointless xdsin XDS_ASCII.HKL hklout %s << eof > %s\n'
            #command = ('/home/necat/programs/ccp4-6.4.0/ccp4-6.4.0/bin/pointless xdsin XDS_ASCII.HKL hklout %s << eof > %s\n'
            #command = ('pointless-1.10.13.linux64 xdsin XDS_ASCII.HKL hklout %s << eof > %s\n'
                   % (mtz, log) + 'SETTING C2 \n eof' )
        else:
            command = ('pointless -copy xdsin XDS_ASCII.HKL hklout %s << eof > %s\n'
            #command = ('pointless-1.10.13.linux64 -copy xdsin XDS_ASCII.HKL hklout %s << eof > %s\n'
                   % (mtz, log) + 'SETTING C2 \n eof')
        p = subprocess.Popen(command, shell = True)
        sts = os.waitpid(p.pid, 0)[1]
        return()
    
    def run_aimless(self, res_cut):
        '''
        Controls the running of aimless.
        '''
        self.logger.debug('ReIntegration::run_aimless - resolution = %s'
                          % res_cut)
        pointless_MTZ = 'pointless.mtz'
        aimless_MTZ = 'scaled.mtz'
        aimless_LOG = 'aimless.log'
        comfile = 'aimless.com'
        
        aimless_file = ['#!/bin/csh\n']
        aimless_file.append('aimless hklin %s\\\n' % pointless_MTZ)
        #aimless_file.append('/share/apps/necat/programs/ccp4-6.3.0/ccp4-6.3.0/bin/aimless hklin %s\\\n' % pointless_MTZ)
        aimless_file.append('hklout %s << eof\n' % aimless_MTZ)
        aimless_file.append('run 1 all\n')
        aimless_file.append('anomalous on\n')
        aimless_file.append('scales constant\n')
        aimless_file.append('sdcorrection norefine full 1 0 0 partial 1 0 0\n')
        aimless_file.append('cycles 0 \n')
        if res_cut != False:
            aimless_file.append('resolution_high %s\n' % str(res_cut))
        aimless_file.append('eof')
        
        self.write_file(comfile, aimless_file)
        os.system('chmod 755 %s' % comfile)
        if self.cluster:
            command = ('qsub -sync y -j y -o %s -cwd %s' % (aimless_LOG, comfile))
        else:
            command = ('%s > %s' % (aimless_LOG, comfile))
        p = subprocess.Popen(command, shell = True)
        sts = os.waitpid(p.pid, 0)[1]
        self.logger.debug ('aimless process complete.')
        return(aimless_LOG)
    
    def find_aimless_resolution(self, logfile, prev_hi_res=False):
        '''
        Finds a resolution cutoff from the results of aimless.
        Attempts to find CC(1/2) of 0.5.
        '''
        self.logger.debug('ReIntegration::find_aimless_resolution')
        cutoff=False
        scalog = open(logfile, 'r').readlines()
        for linenum, line in enumerate(scalog):
            if 'Estimates of resolution limits: overall' in line:
                res_lines = linenum
            elif 'High resolution limit' in line:
                current_high_res = line.split()[-1]
                self.logger.debug('		Current High Res = %s' %current_high_res)
        #if prev_hi_res == False:
        #    cutoff = scalog[res_lines + 1].split('=')[1].strip()[0:-1]
        #else:
        #    cutoff = scalog[res_lines + 1].split('=')[1].strip()[0:-1]
        cutoff = scalog[res_lines + 1].split('=')[1].strip()[0:-1]
        self.logger.debug('             Cutoff = %s' % cutoff)
        if cutoff == current_high_res:
            cutoff = False
        elif float(cutoff) > (float(current_high_res) + 1):
            cutoff = str( (float(cutoff) + float(current_high_res) + 1) / 2)
        return(cutoff)
    
    def prepare_results(self, log, frame_start, frame_finish, job):
        '''
        Prepares the results that will be sent to the UI.
        '''
        self.logger.debug('ReIntegration::pipe_results')
        graphs, tables = self.parse_aimless(log)
        aimlessHTML = self.aimless_plots(graphs,tables)
        try:
            parseHTML, summary = self.parse_results(log, frame_start, frame_finish, job)
        except:
            self.logger.debug('Results not parsed correctly.')
            pass
        try:
            longHTML = self.make_long_results(log)
        except:
            self.logger.debug('Long results not parsed correctly.')
            pass
        results = {'status' : 'WORKING',
                   'plots' : aimlessHTML,
                   'short' : parseHTML,
                   'long' : longHTML,
                   'summary' : summary}
        return(results)
    
    def parse_aimless(self, logfile):
        '''
        Parses the aimless logfile for graphs and results table.
        '''
        self.logger.debug('ReIntegration::parse_aimless')
        
        graphs = []
        tables = []
        tableHeaders=[]
        label_start= ['N', 'Imax', 'l', 'h', 'k', 'Range']
        
        log = open(logfile, 'r').readlines()
        for i,v in enumerate(log):
            if 'TABLE' in v:
                flag=0
                x = i
                header = []
                data = []
                while flag != 2 and x < len(log):
                    if 'GRAPH' in log[x]:
                        while log[x] !='\n' and log[x].split()[0] != '$$':
                            header.append(log[x].rstrip())
                            x+=1
                    elif log[x] == '\n':
                        x+=1
                    elif log[x].strip() == '$$':
                        flag+=1
                        x+=1
                    elif log[x].strip()[0].isdigit():
                        data.append(log[x].split())
                        x+=1
                    else:
                        if log[x].split()[0] in label_start:
                            header.append(log[x].strip())
                        x+=1
                #self.logger.debug(header)
                #self.logger.debug('')
                #self.logger.debug(data)
                flag = 0
                tableHeaders.append(header)
                tables.append(data)
        # Parse the table headers to get title, labels, and positions.
        for tableNum, head in enumerate(tableHeaders):
            collabels = head[-1].split()
            ycols=[]
            title=''
            for line in head:
                if ':' in line:
                    for i in line.split(':'):
                        if len(i) > 2 and 'GRAPHS' not in i and '$$' not in i:
                            if i[0].isdigit():
                                if ',' in i:
                                    tmp = i.split(',')
                                    xcol = int(tmp[0])-1
                                    for x in range (1, len(tmp), 1):
                                        ycols.append(int(tmp[x])-1)
                            else:
                                title = i.strip()
                        if title and ycols:
                            ylabels = []
                            xlabel = collabels[xcol]
                            # for plots vs resolution:
                            # change xlabel from 1/d^2 or 1/resol^2 to Dmid
                            if xlabel == '1/d^2' :
                                xlabel = 'Dmid (A)'
                            for y in ycols:
                                self.logger.debug(' y is %s' %y)
                                ylabels.append(collabels[y])
                            graph = title, xlabel, ylabels, xcol, \
                                    ycols, tableNum
                            # Reset the variable ycols and title
                            #self.logger.debug('graph = ')
                            #self.logger.debug(graph)
                            #self.logger.debug('')
                            ycols =[]
                            title=''
                            graphs.append(graph)

        return(graphs, tables)
    
    def aimless_plots(self, graphs, tables):
        """
        generate plots html file from aimless results
        """
        self.logger.debug('aimless_plots')
        # plotThese contains a list of graph titles that you want plotted 
        # additional plots may be requested by adding the title (stripped
        # of leading and trailing whitespace) to plotThese.
        plotThese = {
                     #'Mn(k) & 0k (at theta = 0) v range' : 'Scales',
                     #'B  v range'                        : 'Bfactor',
                     'Rmerge v Batch for all runs'       : 'R vs frame',
                     'I/sigma, Mean Mn(I)/sd(Mn(I))'     : 'I/sigma',
                     'Rmerge v Resolution'               : 'R vs Res',
                     'Average I,sd and Sigma'            : 'I vs Res',
                     'Completeness v Resolution'         : '%Comp',
                     'Multiplicity v Resolution'         : 'Redundancy',
                     'Rpim (precision R) v Resolution'   : 'Rpim',
                     'Rmeas, Rsym & PCV v Resolution'    : 'Rmeas',
                     'Rd vs. Dose difference'            : 'Rd',
                     'Anom & Imean CCs v resolution -'     : 'Anom Corr',
                     #'Rcp v. batch'			: 'Rcp',
                     'RMS correlation ratio'            : 'RCR'
                     }

        aimless_plot = """<html>
<head>
  <style type="text/css">
    body     { background-image: none; }
    .x-label { position:relative; text-align:center; top:10px; }
    .title   { font-size:30px; text-align:center; }
</style>
<script type="text/javascript">
$(function() {
    // Tabs
    $('.tabs').tabs();
});
</script>
</head>
<body>
<table>
  <tr>
    <td width="100%">
    <div class="tabs">
      <!-- This is where the tab labels are defined
           221 = tab2 (on page) tab2(full output tab) tab1 -->
      <ul>
"""
        # Define tab labels for each graph
        for i,graph in enumerate(graphs):
            if graph[0] in plotThese:
                title = plotThese[graph[0]]
                aimless_plot += '        <li><a href="#tabs-22' + str(i) + '">' + title + '</a></li>\n'
        aimless_plot += '      </ul>\n'

        # Define title and x-axis label for each graph
        for i,graph in enumerate(graphs):
            if graph[0] in plotThese:
                aimless_plot += '      <div id ="tabs-22' + str(i) + '">\n'
                aimless_plot += '        <div class="title"><b>'
                aimless_plot += graph[0] + '</b></div>\n'
                aimless_plot += '        <div id="chart' + str(i) + '_div" style='
                aimless_plot += '"width:800px;height:600px"></div>\n'
                aimless_plot += '        <div class="x-label">'
                aimless_plot += graph[1] + '</div>\n'
                aimless_plot += '      </div>\n'

        aimless_plot += """</div> <!-- End of Tabs -->
    </td>
  </tr>
</table>

<script id="source" language="javascript" type="text/javascript">
$(function () {

"""
        # varNames is a counter, such that the variables used for plotting
        # will simply be y+varName (i.e. y0, y1, y2, etc)
        # actual labels are stored transiently in varLabel, and added 
        # as comments next to the variable when it is initialized
        varNum=0
        for i,graph in enumerate(graphs):
            if graph[0] in plotThese:
                varLabel = []
                data = []

                aimless_plot += '    var '
                # graph[2] is the label for the y-values
                for ylabel in (graph[2]):
                    varLabel.append(ylabel)
                    var = 'y' + str(varNum)
                    varNum += 1
                    data.append(var)
                    if ylabel == graph[2][-1]:
                        aimless_plot += var + '= [];\n'
                    else:
                        aimless_plot += var + ' = [], '
                xcol = graph[3]
                for line in tables[graph[5]]:
                    for y,ycol in enumerate(graph[4]):
                        if line[ycol] != '-':
                            aimless_plot += '         ' + data[y] + '.push(['
                            aimless_plot += line[xcol] + ',' + line[ycol]
                            aimless_plot += ']);\n'

                aimless_plot += '    var plot' + str(i)
                aimless_plot += ' = $.plot($("#chart' + str(i) + '_div"), [\n'
                for x in range(0,len(data),1):
                    aimless_plot += '        {data: ' + data[x] + ', label:"'
                    aimless_plot += varLabel[x] + '" },\n'
                aimless_plot += '        ],\n'
                aimless_plot += '        { lines: {show: true},\n'
                aimless_plot += '          points: {show: false},\n'
                aimless_plot += "          selection: { mode: 'xy' },\n"
                aimless_plot += '          grid: {hoverable: true, '
                aimless_plot += 'clickable: true },\n'
                if graph[1] == 'Dmin (A)':
                    aimless_plot += '          xaxis: {ticks: [\n'
                    for line in tables[graph[5]]:
                        aimless_plot += '                         ['
                        aimless_plot += line[xcol] + ',"' + line[xcol+1]
                        aimless_plot += '"],\n'
                    aimless_plot += '                  ]},\n'
                aimless_plot += '    });\n\n'
        aimless_plot += """
    function showTooltip(x, y, contents) {
        $('<div id=tooltip>' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y + 5,
            left: x + 5,
            border: '1px solid #fdd',
            padding: '2px',
            'background-color': '#fee',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    }

    var previousPoint = null;
"""
        for i,graph in enumerate(graphs):
            if graph[0] in plotThese:
                aimless_plot += '    $("#chart' + str(i) + '_div").bind'
                aimless_plot += """("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (true) {
            if (item) {
                if (previousPoint != item.datapoint) {
                    previousPoint = item.datapoint;

                    $("#tooltip").remove();
"""
                if graph[1] == 'Dmin (A)':
                    aimless_plot += '                    '
                    aimless_plot += \
                    'var x = (Math.sqrt(1/item.datapoint[0])).toFixed(2),\n'
                else:
                    aimless_plot += '                    '
                    aimless_plot += 'var x = item.datapoint[0].toFixed(2),\n'
                aimless_plot += \
"""                        y = item.datapoint[1].toFixed(2);

                    showTooltip(item.pageX, item.pageY,
                                item.series.label + " at " + x + " = " + y);
                }
            }
            else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        }
    });
"""
        aimless_plot += '\n});\n</script>\n </body>\n</html>'

        try:
            with open('aimless_plot.html','w') as file:
                file.write(aimless_plot)
            return('aimless_plot.html')
        except IOError:
            self.logger.debug ('Could not create aimless plot html file.')
            return ('Error')

    def parse_results(self,aimless_log, start, finish, job):
        '''
        Parse the aimless log file for display to UI
        '''
        self.logger.debug('parse_results')
        results = {}
        results['wedge'] = str(start) + '-' + str(finish)
        # Pull out a summary of the aimless results
        aimless_lines = open(aimless_log, 'r').readlines()
        table_start = 0
        flag = 0
        #results['CC_cut'] = False
        #results['RCR_cut'] = False
        for i,v in enumerate(aimless_lines):
            if v.startswith('Summary data for'):
                table_start = i + 1
            #elif v.startswith('$GRAPHS: Anom & Imean CCs'):
            #    flag = 1
            #elif flag == 1 and v.startswith(' Overall'):
            #    flag = 0
            #    results['CC_anom_overall'] = v.split()[1]
            #    results['RCR_anom_overall'] = v.split()[5]
            #elif flag == 1:
            #    vsplit = v.split()
            #    if len(vsplit) > 1 and vsplit[0].isdigit():
            #        if vsplit[3] == '-' or vsplit[7] == '-':
            #            pass
            #        else:
            #            anom_cc = float(vsplit[3])
            #            anom_rcr = float(vsplit[7])
                        # self.logger.debug ('CC_anom = %s RCR_anom = %s' % (vsplit[3],vsplit[7]) )
            #            if anom_cc >= 0.3:
            #                results['CC_cut'] = [ vsplit[2], vsplit[3] ]
            #            if anom_rcr >= 1.5:
            #                results['RCR_cut'] = [ vsplit[2], vsplit[7] ]

        for i,v in enumerate(aimless_lines[table_start:]):
            vsplit = v.split()
            vstrip = v.strip()

            #bin resolution limits
            if vstrip.startswith('Low resolution limit'):
                results['bins_low'] = vsplit[3:6]
            elif vstrip.startswith('High resolution limit'):
                results['bins_high'] = vsplit[3:6]

            #Rmerge
            elif (vstrip.startswith('Rmerge  (all I+ and I-)')):
                results['rmerge'] = vsplit[5:8]
            #elif (vstrip.startswith('Rmerge in top intensity bin')):
            #    results['rmerge_top'] = [vsplit[5]]

            #Rmeas
            elif (vstrip.startswith('Rmeas (within I+/I-)')):
                results['rmeas_anom'] = vsplit[3:6]
            elif (vstrip.startswith('Rmeas (all I+ & I-)')):
                results['rmeas_norm'] = vsplit[5:8]

            #Rpim
            elif (vstrip.startswith('Rpim (within I+/I-)')):
                results['rpim_anom'] = vsplit[3:6]
            elif (vstrip.startswith('Rpim (all I+ & I-)')):
                results['rpim_norm'] = vsplit[5:8]

            #Bias
            #elif (vstrip.startswith('Fractional partial bias')):
            #    results['bias'] = vsplit[3:6]

            #Number of refections
            elif (vstrip.startswith('Total number of observations')):
                results['total_obs'] = vsplit[4:7]
            elif (vstrip.startswith('Total number unique')):
                results['unique_obs'] = vsplit[3:6]

            #I/sigI
            elif (vstrip.startswith('Mean((I)/sd(I))')):
                results['isigi'] = vsplit[1:4]

            #Completeness
            elif (vstrip.startswith('Completeness')):
                results['completeness'] = vsplit[1:4]
            elif (vstrip.startswith('Anomalous completeness')):
                results['anom_completeness'] = vsplit[2:5]

            #Multiplicity
            elif (vstrip.startswith('Multiplicity')):
                results['multiplicity'] = vsplit[1:4]
            elif (vstrip.startswith('Anomalous multiplicity')):
                results['anom_multiplicity'] = vsplit[2:5]

            #Anomalous indicators
            elif (vstrip.startswith('DelAnom correlation between half-sets')):
                results['anom_correlation'] = vsplit[4:7]
            elif (vstrip.startswith('Mid-Slope of Anom Normal Probability')):
                results['anom_slope'] = [vsplit[5]]

            #unit cell
            elif (vstrip.startswith('Average unit cell:')):
                results['scaling_unit_cell'] = vsplit[3:]

            #spacegroup
            elif (vstrip.startswith('Space group:')):
                results['scale_spacegroup'] = ''.join(vsplit[2:])
                break

        # extract mosaicity from INTEGRATE.LP
        lp = open ('INTEGRATE.LP','r').readlines()
        for linenum, line in enumerate(lp):
            if 'SUGGESTED VALUES FOR INPUT PARAMETERS' in line:
                avg_mosaicity_line = lp[linenum + 2]
        mosaicity = avg_mosaicity_line.strip().split(' ')[-1]

        # extract ISa from CORRECT.LP
        lp = open('CORRECT.LP', 'r').readlines()
        for i, line in enumerate(lp):
            if 'ISa\n' in line:
                isa_line = lp[i + 1]
                break
        ISa = isa_line.strip().split()[-1]
        #for k,v in results.iteritems():
        #    self.logger.debug (k,v)

        #Start constructing the parsed results html file       
        parseHTML = 'results.php'

        with open(parseHTML, 'w') as file:
            file.write('''<?php
//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);

session_cache_limiter();
session_start();

require('/var/www/html/rapd/login/config.php');
require('/var/www/html/rapd/login/functions.php');

if(allow_user() != "yes")
{
    if(allow_local_data($_SESSION[data]) != "yes")
    {
        include ('/login/no_access.html');
        exit();
    }
} else {
    $local = 0;
}
?>
<head>
<!-- Inline Stylesheet -->
<style type="text/css"><!--
    body {font-size: 17px; }
    table.integrate td, th {border-style: solid;
                   border-width: 2px;
                   border-spacing: 0;
                   border-color: gray;
                   padding: 5px;
                   text-align: center;
                   height: 2r10px;
                   font-size: 15px; }
    table.integrate tr.alt {background-color: #EAF2D3; }
--></style>
</head>
<body>
<div id="container">\n''')

            file.write('<div align="center">\n')
            file.write('<h3 class="green">%s Processing Results for images %s</h3>\n'
                       % (job, results['wedge']))
            spacegroupLine = ('<h2>Spacegroup: ' + results['scale_spacegroup']
                               + '</h2>\n')
            spacegroupLine += ('<h2>Unit Cell: ' +
                               ' '.join(results['scaling_unit_cell'])+ '</h2>\n')
            file.write(spacegroupLine)
            file.write('<h2>SIGMAR (Mosaicity): %s&deg</h2>\n' % mosaicity)
            file.write('<h2>Asymptotic limit of I/sigma (ISa) = %s</h2>\n' % ISa)
            file.write('<table class="integrate">\n')
            file.write('<tr><th></th><td>Overall</td><td>Inner Shell'
                       + '</td><td>Outer Shell</td></tr>\n')

            pairs1 = [('High resolution limit','bins_high'),
                      ('Low resolution limit','bins_low'),
                      ('Completeness','completeness'),
                      ('Multiplicity','multiplicity'),
                      ('I/sigma','isigi'),
                      ('Rmerge','rmerge'),
                      ('Rmeas(I)','rmeas_norm'),
                      ('Rmeas(I+/-)','rmeas_anom'),
                      ('Rpim(I)','rpim_norm'),
                      ('Rpim(I+/-)','rpim_anom'),
                      #('Partial bias','bias'),
                      ('Anomalous completeness','anom_completeness'),
                      ('Anomalous multiplicity','anom_multiplicity'),
                      ('Anomalous correlation','anom_correlation'),
                      ('Anomalous slope','anom_slope'),
                      ('Total observations','total_obs'),
                      ('Total unique','unique_obs')]

            count = 0
            for l,k in pairs1:
                if (count%2 == 0):
                    file.write('<tr><th>'+l+'</th>')
                else:
                    file.write('<tr class="alt"><th>'+l+'</th>')
                for v in results[k]:
                    file.write('<td>'+v.strip()+'</td>')
                if l == 'Anomalous slope':
                    file.write('<td>--</td><td>--</td>')
                file.write('</tr>\n')
                count += 1


            file.write('</table>\n</div><br>\n')

            # Now write an analysis of anomalous signal
            #slope = float(results['anom_slope'][0])
            #flag = False

            #file.write('<div align="left">')
            #file.write('<h3 class="green">Analysis for anomalous signal.</h3>\n')
            #file.write('<pre>An anomalous slope > 1 may indicate the presence '
            #           + 'of anomalous signal.\n')
            #file.write('This data set has a anomalous slope of %s.\n'
            #           % results['anom_slope'][0])
            #if slope > 1.1:
            #    file.write('Analysis of this data set indicates the presence '
            #               + 'of a significant anomalous signal.\n')
            #    flag = True
            #elif slope > 1.0:
            #    file.write('Analysis of this data set indicates either a weak '
            #               + 'or no anomalous signal.\n')
            #    flag = True
            #else:
            #    file.write('Analysis of this data set indicates no detectable '
            #               + 'anomalous signal.\n')

            #if flag == True and results['CC_cut'] != False:
            #    file.write('The anomalous correlation coefficient suggests the '
            #               + 'anomalous signal extends to %s Angstroms.\n'
            #               % results['CC_cut'][0] )
            #    file.write('(cutoff determined where CC_anom is above 0.3)\n')
            #if flag == True and results['RCR_cut'] != False:
            #    file.write('The r.m.s. correlation ratio suggests the anomalous '
            #               + 'signal extends to %s Angstroms.\n'
            #               % results['RCR_cut'][0] )
            #    file.write('(cutoff determined where RCR_anom is above 1.5)\n')
            #if (flag == True and
            #    results['CC_cut'] == False and results['RCR_cut'] == False):
            #    file.write('A cutoff for the anomalous signal could not '
            #               + 'be determined based on either the\n'
            #               + 'anomalous correlation coeffecient or '
            #               + 'by the r.m.s. correlation ratio\n\n')
            #file.write('</pre></div><br>\n')

            #now write the credits
            file.write('<div align="left"><pre>\n')
            file.write('RAPD used the following programs for integrating and' +
                       ' scaling the dataset:\n')
            file.write('  XDS        -  "Automatic processing of rotation ' +
                       'diffraction from crystals of initially unkown symmetry '
                       + 'and cell constants", W. Kabsch (1993) J. Appl. Cryst.'
                       + ' 26, 795-800.\n')
            file.write('  pointless  -  "The CCP4 Suite: Programs for Protein '
                       + 'Crystallography". Acta Cryst. D50, 760-763 \n')
            file.write('  aimless  -  Scaling and assessment of data quality. ' +
                       'P.R. Evans (2006) Acta Cryst. D62, 72-82.\n')
            file.write('  freerflag  -  "The CCP4 Suite: Programs for Protein '
                       + 'Crystallography". Acta Cryst. D50, 760-763 \n')
            file.write('  mtz2various  -  "The CCP4 Suite: Programs for Protein'
                       + ' Crystallography". Acta Cryst. D50, 760-763 \n')
            file.write('\n')
            file.write('</pre></div></div></body>')

            return(parseHTML, results)

    def make_long_results(self, logfile):
        '''
        Grab the contents of various logfiles and put them in a php file
        '''
        self.logger.debug('make_long_results')
        results = {}

        longHTML = 'long_results.php'

        with open(longHTML, 'w') as file:
            file.write('''<?php
//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);

session_cache_limiter();
session_start();

require('/var/www/html/rapd/login/config.php');
require('/var/www/html/rapd/login/functions.php');

if(allow_user() != "yes")
{
    if(allow_local_data($_SESSION[data]) != "yes")
    {
        include ('/login/no_access.html');
        exit();
    }
} else {
    $local = 0;
}
?>
<head>
  <!-- Inline Stylesheet -->
  <style type="text/css" media="screen"><!--
      body {
            background-image: none;
            font-size: 17px; 
           }
      table.display td {padding: 1px 7px;}
      tr.GradeD {font-weight: bold;}
      table.integrate td, th {border-style: solid;
                     border-width: 2px;
                     border-spacing: 0;
                     border-color: gray;
                     padding: 5px;
                     text-align: center;
                     height: 2r10px;
                     font-size: 15px; }
      table.integrate tr.alt {background-color: #EAF2D3; }
  --></style>
  <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.js"></script>
  <script type="text/javascript" charset="utf-8">
    $(document).ready(function(){
      $('.accordion').accordion({
         collapsible: true,
         autoHeight: false,
         active: 0          });
      $('#cell').dataTable({
         "bPaginate": false,
         "bFilter": false,
         "bInfo": false,
         "bSort": false,
         "bAutoWidth": false    });
      $('#pdb').dataTable({
         "bPaginate": false,
         "bFilter": false,
         "bInfo": false,
         "bSort": false,
         "bAutoWidth": false    });
         } );
  </script>
</head>
<body>\n''')
#<align="left">\n''')
            file.write('<div class="accordion">\n')
            file.write('<h3><a href="#">Click to view Pointless log file.</a></h3>\n')
            file.write('<div>\n<pre>\n')
            file.write('==========    pointless    ==========\n')
            pointless_log = logfile.replace('aimless', 'pointless')
            in_lines = open(pointless_log, 'r').readlines()
            for in_line in in_lines:
                file.write(in_line)
            file.write('</pre>\n</div>\n')
            file.write('<h3><a href="#">Click to view Aimless log file.</a></h3>\n')
            file.write('<div>\n<pre>\n')
            file.write('==========    aimless    ==========\n')
            in_lines = open(logfile, 'r').readlines()
            for in_line in in_lines:
                if 'applet' in in_line or in_line.startswith('codebase'):
                    pass
                else:
                    #if '&' in in_line:
                    #    in_line = inline.replace('&', '&amp')
                    if '<I' in in_line:
                        in_line = in_line.replace('<','&lt')
                        in_line = in_line.replace('>','&gt')
                    file.write(in_line)
            file.write('</pre>\n</div>\n')
            file.write('<h3><a href="#">Click to view INTEGRATE.LP.</a></h3>\n')
            file.write('<div>\n<pre>\n')
            file.write('==========    INTEGRATE.LP    ==========\n')
            if os.path.isfile('INTEGRATE.LP'):
                integrateLog = 'INTEGRATE.LP'
            else:
                integrateLog = logfile.replace('aimless', 'DATA_DATA_INTEGRATE')
            in_lines = open(integrateLog,'r').readlines()
            for in_line in in_lines:
                if '<I' in in_line:
                    in_line = in_line.replace('<','&lt')
                    in_line = in_line.replace('>','&gt')
                file.write(in_line)
            file.write('</pre>\n</div>\n')
            file.write('<h3><a href="#">Click to view CORRECT.LP.</a></h3>\n')
            file.write('<div>\n<pre>\n')
            file.write('==========   CORRECT.LP    ==========\n')
            if os.path.isfile('CORRECT.LP'):
                correctLog = 'CORRECT.LP'
            else:
                correctLog = logfile.replace('aimless', 'DATA_DATA_CORRECT')
            in_lines = open(correctLog, 'r').readlines()
            for in_line in in_lines:
                if '<I' in in_line:
                    in_line = in_line.replace('<','&lt')
                    in_line = in_line.replace('>','&gt')
                file.write(in_line)
            file.write('</pre>\n</div>\n</div>\n')
            file.write('</body>')

        return(longHTML)
    
    def finish_data(self, in_file):
        '''
        Some final manipulations to the data to generate an mtz containing a
        Rfree flag and sca-files for native and anomalous data.
        '''
        self.logger.debug('ReIntegration::finish_data')
        
        # Truncate the data.
        comfile = 'truncate.sh'
        contents = ['#!/bin/csh\n']
        contents.append('truncate hklin %s hklout truncated.mtz > truncate.log'
                        % in_file)
        contents.append(' << eof\n eof\n')
        self.write_file(comfile, contents)
        os.system('chmod 755 truncate.sh')
        p = subprocess.Popen('./truncate.sh', shell = True)
        sts = os.waitpid(p.pid, 0)[1]
        
        # Set the free R flag.
        comfile = 'freer.sh'
        contents =['#!/bin/csh\n']
        contents.append('freerflag hklin truncated.mtz hklout freer.mtz'
                       + ' > freer.log <<eof\n END\n eof\n')
        self.write_file(comfile, contents)
        os.system('chmod 755 freer.sh')
        p = subprocess.Popen('./freer.sh', shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        
        # Create the merged scalepack format file
        comfile = 'mtz2scaNAT.sh'
        contents = ['#!/bin/csh\n']
        contents.append('mtz2various hklin truncated.mtz hklout NATIVE.sca')
        contents.append(' > mtz2scaNAT.log << eof\n')
        contents.append('OUTPUT SCALEPACK\n')
        contents.append('labin I=IMEAN SIGI=SIGIMEAN\n')
        contents.append('END\n')
        contents.append('eof\n')
        self.write_file(comfile, contents)
        os.system('chmod 755 mtz2scaNAT.sh')
        p = subprocess.Popen('./mtz2scaNAT.sh', shell=True)
        sts=os.waitpid(p.pid,0)[1]
        # Edit the sca file to correct the format of the spacegroup.
        self.fixMtz2Sca('NATIVE.sca')
        Utils.fixSCA(self, 'NATIVE.sca')
        
        # Create an anomalous scalepack format file.
        comfile = 'mtz2scaANOM.sh'
        contents[1] = contents[1].replace('NATIVE.sca', 'ANOM.sca')
        contents[2] =contents[2].replace('NAT', 'ANOM')
        contents[4] = 'labin I(+)=I(+) SIGI(+)=SIGI(+) I(-)=I(-) SIGI(-)=SIGI(-)\n'
        self.write_file(comfile, contents)
        os.system('chmod 755 mtz2scaANOM.sh')
        p = subprocess.Popen('./mtz2scaANOM.sh', shell=True)
        sts = os.waitpid(p.pid,0)[1]
        # Edit the sca file to correct the format of the spacegroup.
        self.fixMtz2Sca('ANOM.sca')
        Utils.fixSCA(self, 'ANOM.sca')
        
        return('freer.mtz')
    
    def fixMtz2Sca(self, scafile):
        '''
        Corrects the format of the spacegroup name in the *.sca files.
        '''
        inlines = open(scafile,'r').readlines()
        symline = inlines[2]
        newline = (symline[:symline.index(symline.split()[6])]
                   +''.join(symline.split()[6:])+'\n')
        inlines[2] = newline
        self.write_file(scafile, inlines)
        return()
    
    def process_shelxC(self, unitcell, spacegroup, scafile):
        '''
        Runs shelxC on the data for determination of anomalous signal.
        '''
        self.logger.debug('ReIntegration::process_shelxC')
        try:
            command = 'shelxc junk << EOF\n'
            command += ('CELL %s \n' % ' '.join(unitcell))
            command += ('SPAG %s \n' % spacegroup)
            command += ('SAD %s \n' % scafile)
            command += 'EOF\n'
            shelx_log = []
            output0 = subprocess.Popen(
                        command, shell = True, stdout = subprocess.PIPE,
                        stderr = subprocess.STDOUT)
            for line in output0.stdout:
                shelx_log.append(line.strip())
            results = self.parse_shelxC(shelx_log)
            res = False
            for i,v in enumerate(results['shelx_dsig']):
                dsig = float(v)
                if dsig >= 1.0:
                    res = results['shelx_res'][i]
            results['shelx_rescut'] = res
            return(results)
        except:
            self.logger.exception('**Error in process_shelxC**')
            return(None)
    
    def insert_shelx_results(self, results):
        '''
        Inserts results of shelxC into the results html file.
        '''
        self.logger.debug('ReIntegration::insert_shelx_results')
        try:
            htmlfile = open('results.php','r').readlines()
            if results['shelx_rescut'] == False:
                insert_text = ('\nAnalysis by ShelxC finds no resolution shell '
                               + 'where d"/sig is greater than 1.0.\n\n')
                htmlfile.insert(-10, insert_text)
            else:
                insert_text = ('\nAnalysis by ShelxC finds d"/sig greater than 1.0'
                               + ' for at least on resolution shell.\n\n')
                htmlfile.insert(-10, insert_text)
                insert_text = '<div align="center">\n'
                insert_text += '<h3 class="green">ShelxC analysis of data</h3>\n'
                insert_text += '<table class="integrate">\n'
                insert_text += '<tr><th>Resl.</th>'
                for item in results['shelx_res']:
                    insert_text += '<td>' + item + '</td>'
                insert_text += '</tr>\n'
                insert_text += '<tr class="alt"><th>N(data)</th>'
                for item in results['shelx_data']:
                    insert_text += '<td>' + item + '</td>'
                insert_text += '</tr>\n'
                insert_text += '<tr><th>I/sig</th>'
                for item in results['shelx_isig']:
                    insert_text += '<td>' + item + '</td>'
                insert_text += '</tr>\n'
                insert_text += '<tr class="alt"><th>%Complete</th>'
                for item in results['shelx_comp']:
                    insert_text += '<td>' + item + '</td>'
                insert_text += '</tr>\n'
                insert_text += '<tr><th>d"/sig</th>'
                for item in results['shelx_dsig']:
                    insert_text += '<td>' + item + '</td>'
                insert_text += '</tr>\n'
                insert_text += '<caption>For zero signal d"/sig should be about 0.80'
                insert_text += '</caption>\n</table></div><br>\n'
                htmlfile.insert(-9, insert_text)
            self.write_file('results.php', htmlfile)
            return()
        except:
            self.logger.exception('**Error in insert_shelx_results**')
            return()
    
    def parse_shelxC(self, log):
        '''
        Parses shelxC results in order to pull out the table in the logfile.
        '''
        self.logger.debug('ReIntegration::parse_shelxC')
        try:
            shelxc_results = {}
            for line in log:
                if line.startswith('Resl'):
                    if line.split()[2] == '-':
                        shelxc_results['shelx_res'] = line.split()[3::2]
                    else:
                        shelxc_results['shelx_res'] = line.split()[2:]
                    #shelxc_results['shelx_res'] = line.split()[3::2]
                elif line.startswith('N(data)'):
                    shelxc_results['shelx_data'] = line.split()[1:]
                elif line.startswith('<I/sig>'):
                    shelxc_results['shelx_isig'] = line.split()[1:]
                elif line.startswith('%Complete'):
                    shelxc_results['shelx_comp'] = line.split()[1:]
                elif line.startswith('<d"/sig>'):
                    shelxc_results['shelx_dsig'] = line.split()[1:]
            return(shelxc_results)
        except:
            self.logger.exception('**Error in parse_shelxC**')
            return(False)
    
    def clean_fs_xds(self, dir, prefix, run_number):
        '''
        Cleans up the directory after a successful xds run.
        '''
        self.logger.debug('ReIntegration::clean_fs_xds')
        label = '_'.join([prefix,str(run_number)])
        if os.path.isdir('xds_lp_files') == False:
            os.mkdir('xds_lp_files')
        os.system('mv *.LP xds_lp_files/')
        os.system('mv freer.mtz %s_free.mtz' % label)
        os.system('mv NATIVE.sca %s_NATIVE.sca' % label)
        os.system('mv ANOM.sca %s_ANOM.sca' % label)
        os.system('mv pointless.mtz %s_mergable.mtz' % label)
        os.system('mv aimless.log %s_aimless.log' % label)
        os.system('mv aimless.com %s_aimless.com' % label)
        os.system('mv pointless.log %s_pointless.log' % label)
        os.system('mv XDS.LOG %s_xds.log' % label)
        os.system('mv XDS.INP %s_xds.inp' % label)
        os.system('mv XDS_ASCII.HKL %s_xds.hkl' % label)
        os.system('rm -f *.sh truncated.mtz')
        os.system('rm -f mcolspot* mintegrate*')
        os.system('rm -f freer.log truncated.log mtz2scaANOM.log mtz2scaNAT.log')
        os.system('rm -f junk_fa.hkl junk_fa.ins junk.hkl')
        
        # Compress data and log files
        os.system('tar -cjf %s.tar.bz2 *.sca *.mtz *.hkl *.log *.inp *.com XPARM.XDS' % label)
        file_base = os.path.join(dir, label)
        int_files = {'mergable' : file_base + '_mergable.mtz',
                     'mtzfile' : file_base + '_free.mtz',
                     'ANOM_sca' : file_base + '_ANOM.sca',
                     'NATIVE_sca' : file_base + '_NATIVE.sca',
                     'scala_log' : file_base + '_aimless.log',
                     'scala_com' : file_base + '_aimless.com',
                     'xds_data' : file_base + '_xds.hkl',
                     'xds_log' : file_base + '_xds.log',
                     'xds_com' : file_base + '_xds.inp',
                     'downloadable' : file_base + '.tar.bz2',
                     'CORRECT' : '%s/xds_lp_file/CORRECT.LP' % dir}
        return(int_files)

    def clean_fs_xia2(self, dir, prefix, run_number):
        '''
        Cleans up the directory after a successful xia2 run.
        '''
        self.logger.debug('ReIntegration::clean_fs_xia2')
        label = '_'.join([prefix,str(run_number)])
        os.system('mv freer.mtz %s_free.mtz' % label)
        os.system('mv NATIVE.sca %s_NATIVE.sca' % label)
        os.system('mv ANOM.sca %s_ANOM.sca' % label)
        os.system('mv pointless.mtz %s_mergable.mtz' % label)
        integrate_dir = ('%s/DATA/DATA/integrate/' % prefix)
        os.system('mv %sXDS_ASCII.HKL %s_xds.hkl' % (integrate_dir, label) )
        os.system('mv %sXDS.INP %s_xds.inp' % (integrate_dir, label) )
        # Remove nonessential directories and files.
        os.system('rm -rf %s data_files Harvest' % prefix)
        os.system('rm -f *.log *.sh, truncated.mtz XIA2.o*')
        # Compress files for download.
        os.system('tar -cjf %s.tar.bz2 *.sca *.mtz *.inp xia* LogFiles' % label)
        # Create dict for location of various files.
        label2 = os.path.join(dir,label)
        int_files = {'mergable' : label2 + '_mergable.mtz',
                     'mtzfile' : label2 + '_free.mtz',
                     'ANOM_sca' : label2 + '_ANOM.sca',
                     'NATIVE_sca' : label2 + '_NATIVE.sca',
                     'xds_data' : label2 + '_xds.hkl',
                     'xia2_com' : label2 + '.xinfo',
                     'xia2_log' : dir + '/xia2.txt',
                     'downloadable' : label2 + '.tar.bz2',
                     'CORRECT' : '%s/xds_lp_files/CORRECT.LP' % dir}
        return(int_files)
    
    def run_analysis (self, data, dir, first_image, osc_range):
        """
        Runs xtriage and other anlyses on the integrated data.
        """
        self.logger.debug('ReIntegration::run_analysis')
        analysis_dir = os.path.join(dir, 'analysis')
        if os.path.isdir(analysis_dir) == False:
            os.system('mkdir %s' % analysis_dir)
        x_beam = '%.2f' % self.input[2]['original']['beam_center_x']
        y_beam = '%.2f' % self.input[2]['original']['beam_center_y']
        distance = self.input[2]['original']['distance']  
        first = int(self.input[3]['request']['frame_start'])
        last = int(self.input[3]['request']['frame_finish'])
        total = last - first + 1
        run_dict = {'fullname'   : first_image,
                    'total'      : total,
                    'osc_range'  : osc_range,
                    'x_beam'     : x_beam,
                    'y_beam'     : y_beam,
                    'two_theta'  : None,
                    'distance'   : distance
                   }
        pdb_input = []
        pdb_dict = {}
        pdb_dict['run'] = run_dict
        pdb_dict['dir'] = analysis_dir
        pdb_dict['data'] = data
        pdb_dict['control'] = self.controller_address
        pdb_dict['process_id'] = self.process_id
        pdb_input.append(pdb_dict)
        self.logger.debug('ReIntegration::run_analysis::pdb_input')
        self.logger.debug(pdb_input)
        try:
            T = AutoStats(pdb_input, self.logger)
        except:
            self.logger.debug('    Execution of AutoStats failed')
            return('Failed')
        return('SUCCESS')

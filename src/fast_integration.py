"""
This file is part of RAPD

Copyright (C) 2009-2016, Cornell University
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

__created__ = "2010-09-07"
__maintainer__ = "David Neau"
__email__ = "dneau@anl.gov"
__status__ = "Production"

from multiprocessing import Process, Queue, Pipe
from rapd_communicate import Communicate
from rapd_agent_cell import PDBQuery
from rapd_agent_stats import AutoStats
from numpy import interp
import jon_utilities as utils
import math
import os
import os.path
import subprocess
import time
import threading
from xdsme.xds2mos import Xds2Mosflm
import logging
import logging.handlers
import pexpect

class FastIntegration(Process, Communicate):
    '''
    classdocs
    '''


    def __init__(self, input, logger):
        '''
        Constructor
        
        input is the tuple passed into this process, containing the command
        to be executed, a list of relevant directories, a list of data for
        the image and run, and a list of any user settings imposed
        
        pipe is the communication back to the calling process
        
        logger is for logging progress and results of the process
        '''
        self.input = input [0:4]
        self.controller_address = input[-1]
        # self.pipe = pipe
        self.logger = logger
        self.beamline = input[2]['image_data']['beamline']
        self.process_id = input[2]['image_data']['process_id']
        self.summary = {}
        self.results = {'status' : 'Error'}
        self.last_wedge = False
        Process.__init__(self,name='FastIntegration')
        self.start()
        
    def run(self):
        self.logger.debug('FastIntegrations::run')
        self.preprocess()
        self.process()
        self.postprocess()
        
    def preprocess(self):
        '''
        Things to do before the main process runs.
        1. Change to the correct working directory.
        '''
        self.logger.debug('FastIntegration::preprocess')
        if os.path.isdir(self.input[1]['work']) == False:
            os.makedirs(self.input[1]['work'])
        os.chdir(self.input[1]['work'])
    
    def process(self):
        '''
        Things to do in the main process
        1. Prepare initial xds processes and run them.
        2. Prepare the wedge integration and scaling processes and run them.
        3. Listen for an abort of data collection, 
            or a completion of processing.
        4. Send results back to calling process.
        '''
        self.logger.debug('FastIntegration::process')
        # Expand the input tuple
        command, dirs, data, settings = self.input
        if command != 'INTEGRATE':
            self.logger.debug('Command sent to FastIntegration not INTEGRATE')
            return()
        # Prepare and run initial xds processes.
        xds_data = self.convert_to_xds_data(data['image_data'], data['run_data'])
        xds_defaults = self.xds_default_input(xds_data)
        first = int(data['run_data']['start'])
        exp_time = int(data['image_data']['time'])
        total = int(data['run_data']['total'])
        osc_angle = float(data['run_data']['width'])
        self.xds_init(xds_defaults, first, total, osc_angle, exp_time)
        
        # Prepare and launch processing.
        num_images = int(data['run_data']['total'])
        image_template = os.path.join(data['image_data']['directory'],
                                      data['image_data']['image_prefix'])
        image_template += ('_' + str(data['run_data']['run_number']) + '_')
        last_image_num = first + num_images - 1
        last_image = image_template + str(last_image_num).zfill(3) + '.img'
        q = Queue()
        if os.path.isfile(last_image):
            integration = Process(target=self.xds_total,
                     args=(xds_defaults, first, num_images, image_template, q))
            integration.start()
        elif data['image_data']['binning'] == 'none':
            integration = Process(target=self.xds_processing_wait,
                args = (xds_defaults, first, num_images, image_template,
                exp_time, data['image_data']['osc_range'], q))
            integration.start()
        else:
            integration = Process(target=self.xds_processing, 
                args = (xds_defaults, first, num_images, image_template,
                data['image_data']['time'], data['image_data']['osc_range'], q))
            integration.start()
        
        proc_dir = None
        listen = q.get()
        while listen != 'Finished':
            self.results = listen[1]
            self.logger.debug ('results from a wedge returned.')
            #self.logger.debug ('listen = ' + listen)
            # self.logger.debug (self.results)
            proc_dir = listen[0]
            # Wait for next update to q
            listen = q.get()
        
        if proc_dir != None:    
            self.logger.debug('xds_processing finished, prepare clean up')
            last_data = os.path.join(proc_dir, proc_dir + '_scaled.mtz')
            last_correct = os.path.join(proc_dir, 'CORRECT.LP')
        
            if float(self.results['summary']['isigi'][0]) < 0.8:
                self.results['files'] = self.short_clean(proc_dir,
                                             data['image_data']['image_prefix'],
                                             data['image_data']['image_prefix'])
                self.results.update({'status' : 'FAILED'})
                return()

            final_mtz = self.finish_data(last_data)
            if final_mtz != 'failed' and os.path.isfile(final_mtz):
                self.results.update({'status' : 'SUCCESS'})
                Xds2Mosflm(xds_file=last_correct,mat_file='reference.mat')
                sg = self.results['summary']['scale_spacegroup']
                cell = self.results['summary']['scaling_unit_cell']
                sca = 'ANOM.sca'
                self.results['shelxc_results'] = self.process_shelxC(cell, sg, sca)
                if self.results['shelxc_results'] != None:
                    self.insert_shelx_results(self.results['shelxc_results'])
                #query_result = self.pdbquery(cell, final_mtz, dirs['work'])
                #if query_result == 'SUCCESS':
                #    pass
                    
        if self.results['status'] == 'SUCCESS':
            self.results['files'] = self.clean_fs(proc_dir,
                                        data['image_data']['image_prefix'],
                                        data['image_data']['run_number'])
        tmp = self.input[:]
        tmp.append(self.results)
        self.sendBack2(tmp)
    
        analysis_result = self.run_analysis(cell, self.results['files']['mtzfile'], dirs['work'])
        if analysis_result == 'FAILED':
            self.logger.debug('Stats analysis failed.')
    
    def postprocess(self):
        '''
        Things to do after the main process has run.
        1. Send final summary up the pipe.
        2. Close the pipe (?)
        3. Clean up the directory structure.
        4. Shutdown this class.
        '''
        self.logger.debug('FastIntegration::postprocess')
        # If processing was successful, clean up the directory tree,
        # otherwise, leave it messy to aid debugging.
        #if self.results['status'] == 'SUCCESS':
        #    self.clean_fs()
        print self.results
        self.input.append(self.results)
        self.logger.debug (self.input)
        # self.pipe.send(self.input)
        self.sendBack2(self.input)
        # Close this module.
        os._exit(0)
    
    def short_clean(self, dir, prefix, run_number):
        '''
        Cleans up the filesystem after a partially successful run.
        Partial success mean that XDS ran, but I/sigma in high resolution
        shell was less than 0.5.
        '''
        self.logger.debug('FastIntegration::short_clean')
        dir2 = os.path.join(dir,dir)
        os.system('mkdir xds_lp_files')
        os.system('mv initialXDS/*.LP xds_lp_files')
        os.system('mv %s/*.LP xds_lp_files' % dir)
        os.system('mv %s/*XPARM.XDS ./' % dir)
        os.system('mv %s_pointless.log %s_pointless.log' % (dir2, prefix) )
        os.system('mv %s_scaled.log %s_scaled.log' % (dir2, prefix) )
        os.system('mv %s_scaled.com %s_scala.com' % (dir2, prefix) )
        os.system('mv %s_pointless.mtz %s_mergable.mtz' % (dir2, prefix) )
        os.system('mv %s_scaled.mtz %s_scala.mtz' % (dir2, prefix) )
        os.system('mv %s/XDS.LOG %s_xds.log' % (dir, prefix) )
        os.system('mv %s/XDS.INP %s_xds.inp' % (dir, prefix) )
        os.system('mv %s/XDS_ASCII.HKL %s_xds.hkl' % (dir, prefix) )
        os.system('mv initialXDS/XDS.LOG initialxds.log')
        #os.system('mv initialXDS/XDS.INP initialxds.inp')
        os.system('rm -rf initialXDS')
        os.system('rm -rf wedge_*')
        os.system('tar -cjf %s_%s.tar.bz2 *.mtz *.log *.inp *.hkl *.XDS'
                  % (prefix, str(run_number) ) )
        work_dir = self.input[1]['work']
        file_base = os.path.join(work_dir,prefix)
        int_files = {'mergable' : '%s_mergable.mtz' % file_base,
                     'mtzfile' : '%s_scala.mtz' % file_base,
                     'scala_log' : '%s_scala.log' % file_base,
                     'scala_com' : '%s_scala.com' % file_base,
                     'xds_data' : '%s_xds.hkl' % file_base,
                     'xds_log' : '%s_xds.log' % file_base,
                     'xds_com' : '%s_xds.inp' % file_base,
                     'downloadable' : '%s_%s.tar.bz2' % (file_base, str(run_number)),
                     'CORRECT' : '%s/xds_lp_files/CORRECT.LP' % work_dir
                     }
        return(int_files)

    def clean_fs(self, dir, prefix, run_number):
        '''
        Cleans up the filesystem after a successful run,
        saving important files and erasing everything else
        '''
        self.logger.debug('clean_fs')
        os.system('mkdir xds_lp_files')
        os.system('mv initialXDS/*.LP xds_lp_files/')
        os.system('mv ' + dir + '/*XPARM.XDS ./') 
        os.system('mv ' + dir + '/*.LP xds_lp_files/')
        os.system('mv freer.mtz ' + prefix + '_free.mtz')
        os.system('mv NATIVE.sca ' + prefix + '_NATIVE.sca')
        os.system('mv ANOM.sca ' + prefix + '_ANOM.sca')
        dir2 = os.path.join(dir,dir)
        os.system('mv ' + dir2 + '_scaled.log ' + prefix + '_scala.log')
        os.system('mv ' + dir2 + '_scaled.com ' + prefix + '_scala.com')
        os.system('mv ' + dir2 + '_pointless.log ' + prefix + '_pointless.log')
        os.system('mv ' + dir2 + '_pointless.mtz ' + prefix + '_mergable.mtz')
        os.system('mv ' + dir + '/XDS.LOG ' + prefix + '_xds.log')
        os.system('mv ' + dir + '/XDS.INP ' + prefix + '_xds.inp')
        os.system('mv ' + dir + '/XDS_ASCII.HKL ' + prefix + '_xds.hkl')
        os.system('mv initialXDS/XDS.LOG initialxds.log')
        os.system('mv initialXDS/XDS.INP initialxds.inp')
        os.system('rm -f *.sh truncated.mtz')
        os.system('rm -f freer.log truncate.log mtz2scaANOM.log mtz2scaNAT.log')
        os.system('rm -rf initialXDS')
        os.system('rm -rf wedge_*')
        os.system('rm -f junk_fa.hkl junk_fa.ins junk.hkl')
        # Compress data files and log files.
        os.system('tar -cjf ' + '_'.join((prefix,str(run_number))) + 
                  '.tar.bz2 *.sca *.mtz *.hkl *.log *.inp *.XDS')
        work_dir = self.input[1]['work']
        file_base = os.path.join(work_dir, prefix)
        int_files = {'mergable' : file_base + '_mergable.mtz',
                     'mtzfile' : file_base + '_free.mtz',
                     'ANOM_sca' : file_base + '_ANOM.sca',
                     'NATIVE_sca' : file_base + '_NATIVE.sca',
                     'scala_log' : file_base + '_scala.log',
                     'scala_com' : file_base + '_scala.com',
                     'xds_data' : file_base + '_xds.hkl',
                     'xds_log' : file_base + '_xds.log',
                     'xds_com' : file_base + '_xds.inp',
                     'downloadable' : '_'.join((file_base,str(run_number))) + '.tar.bz2',
                     'CORRECT' : '%s/xds_lp_files/CORRECT.LP' % work_dir}
        return(int_files)
        
    def convert_to_xds_data(self, image_data, run_data):
        '''
        Pulls out information relevant to xds's processing of the run.
        Returns this information in a dict.
        '''
        #self.logger.debug('convert_to_xds_data image_data %s' % image_data)
        #self.logger.debug('convert_to_xds_data run_data %s' % run_data)
        self.logger.debug('FastIntegrate::convert_to_xds')
        # Set detector type.
        # Currently NE-CAT only has ADSC type detectors.
        detector_type = 'ADSC'
        # set xds data_template.
        data_template = os.path.join(image_data['directory'],
                                     image_data['image_prefix'])
        data_template = '_'.join([data_template,
                                  str(image_data['run_number']), '???.img'])
        # Calculate the xds beam center.
        px = float(image_data['y_beam']) / float(image_data['pixel_size'])
        py = float(image_data['x_beam']) / float(image_data['pixel_size'])
        # Ensure the beam center is on the detector.
        if px < 0 or px > float(image_data['size1']):
            raise RuntimeError, 'beam x coordinate outside detector'
        if py < 0 or py > float(image_data['size2']):
            raise RuntimeError, 'beam y coordinate outside detector'
        # Build a dict containing xds relevant data.
        xdsdata = {'data_template' : data_template,
                   'xbeam' : str(px), 'ybeam' : str(py),
                   'detector_type' : detector_type,
                   'wavelength' : str(image_data['wavelength']),
                   'NX' : str(image_data['size1']),
                   'NY' : str(image_data['size2']),
                   'QX' : str(image_data['pixel_size']),
                   'QY' : str(image_data['pixel_size']),
                   'overload' : str(image_data['ccd_image_saturation']),
                   'distance' : str(run_data['distance']),
                   'wavelength' : str(image_data['wavelength']),
                   'osc_range' : str(image_data['osc_range']),
                   'twotheta' : image_data['twotheta'],
                   'first_image' : str(run_data['start'])}
        return(xdsdata)

    def xds_default_input (self, data):
        '''
        Creates a list used to generate the default portion of XDS.IN file.
        '''
        self.logger.debug('xds_default_input data %s' % data)
        default = ['!*******************************************************\n']
        default.append('!============ DETECTOR PARAMETERS ============\n')
        default.append('DETECTOR=' + data['detector_type'] + '\n')
        default.append('MINIMUM_VALID_PIXEL_VALUE=1 OVERLOAD='
                       + data['overload'] + '\n')
        default.append('DIRECTION_OF_DETECTOR_X-AXIS=1.0 0.0 0.0\n')
        # Check for a two-theta tilt.
        # If two-theta not equal to 0.0, the direction of the detector y-axis
        # is offset, so that the vector equalts 0 cos(2-theta) sin(two-theta).
        if data['twotheta'] == 0.0:
            default.append('DIRECTION_OF_DETECTOR_Y-AXIS=0.0 1.0 0.0\n')
        else:
            twotheta = math.radians(data['twotheta'])
            tilty = str(math.cos(twotheta)).zfill(4)
            tiltz = str(math.sin(twotheta)).zfill(4)
            default.append('DIRECTION_OF_DETECTOR_Y-AXIS=0.0 %s %s\n' 
                           % (tilty, tiltz) )
        default.append('TRUSTED_REGION=0.0 1.00 !Trust to edge of detector\n')
        default.append('NX=' + data['NX'] + ' NY=' + data['NY'] +
                       ' QX=' + data['QX'] + ' QY=' + data['QY'] + '\n')
        default.append('!============ PROCESSING CONTROL PARAMETERS ============\n')
        #default.append('MAXIMUM_NUMBER_OF_PROCESSORS=1\n')
        default.append('MAXIMUM_NUMBER_OF_PROCESSORS=8\n')
        #default.append('MAXIMUM_NUMBER_OF_JOBS=16\n')
        default.append('!============ GEOMETRICAL PARAMETERS ============\n')
        default.append('!Beam center in pixels.\n')
        default.append('ORGX=' + data['xbeam'] + ' ORGY=' + data['ybeam'] + '\n')
        default.append('DETECTOR_DISTANCE=' + data['distance'] + ' !(mm)\n')
        default.append('ROTATION_AXIS= 1.0 0.0 0.0\n')
        default.append('OSCILLATION_RANGE=' + data['osc_range'] + '!degrees(>0)\n')
        default.append('X-RAY_WAVELENGTH=' + data['wavelength'] + '!Angstroem\n')
        default.append('INCIDENT_BEAM_DIRECTION=0.0 0.0 1.0\n')
        default.append('FRACTION_OF_POLARIZATION=0.95\n')
        default.append('POLARIZATION_PLANE_NORMAL=0.0 1.0 0.0\n')
        default.append('!========= PARAMETERS CONTROLLING REFINEMENTS =========\n')
        default.append('REFINE(IDXREF)=BEAM AXIS ORIENTATION CELL !DISTANCE\n')
        default.append('REFINE(INTEGRATE)=BEAM ORIENTATION CELL !DISTANCE AXIS\n')
        default.append('REFINE(CORRECT)=DISTANCE BEAM ORIENTATION CELL AXIS\n')
        default.append('!RAPD always assumes possible presence of an anomalous signal\n')
        default.append("FRIEDEL'S_LAW=FALSE\n")
        default.append('STRICT_ABSORPTION_CORRECTION=TRUE\n')
        default.append('!========= CRITERIA FOR ACCEPTING REFLECTIONS =========\n')
        default.append('!VALUE_RANGE_FOR_TRUSTED_DETECTOR_PIXELS= 6000 30000 \n')
        default.append('!Used by DEFPIX for excluding shaded parts of the detector\n')
        default.append('\n')
        default.append('INCLUDE_RESOLUTION_RANGE=50.0 0.0 !Angstroems;\n')
        default.append('!Used by DEFPIX,INTEGRATE,CORRECT\n')
        default.append('\n')
        default.append('!============ SELECTION OF DATA IMAGES ============\n')
        default.append('NAME_TEMPLATE_OF_DATA_FRAMES='
                       + data['data_template'] +'\n')
        default.append('!RAPD uses first 5 images for' +
                       ' background and spot picking\n')
        default.append('BACKGROUND_RANGE=' + data['first_image'] +
                       ' ' + str( int(data['first_image']) + 4) + '\n')
        #default.append('SPOT_RANGE= ' + data['first_image'] +
        #               ' ' + str( int(data['first_image']) + 4) + '\n')
        return(default)
    
    def xds_init(self, xds_defaults, first, total, osc_angle, exp_time):
        '''
        Runs the initial xds jobs
        (XYCORR, INIT, COLSPOT, IDXREF, and DEFPIX)
        '''
        successful_index = False
        count = 0
        #self.logger.debug('xds_init xds_defaults %s first %s last %s' 
        #                  % (xds_defaults, str(first), str(total)) )
        self.logger.debug('FastIntegration::xds_defaults')
        if os.path.isdir('initialXDS') == False:
            os.mkdir('initialXDS')
        os.chdir('initialXDS')
        wait = float(exp_time) + 5.0
        jobs = ['JOB=XYCORR INIT COLSPOT IDXREF\n']
        if osc_angle < 1.0:
            last = 5.0 // osc_angle
            if total < last:
                last = total
            last = int(last + first - 1)
        else:
            last = int(first) + 4
        if self.input[2]['image_data']['image_number'] < last:
            last_frame = (self.input[2]['image_data']['fullname'][0:-7] 
                          + str(last).zfill(3) + '.img')
            while os.path.isfile(last_frame) == False and count <= last:
                count += 1
                time.sleep(wait)
        count = 0
        while successful_index == False and count <= 100:
            data_range = ['SPOT_RANGE=' + str(first) + ' ' + str(last) + '\n']
            data_range.append('DATA_RANGE=' + str(first) + ' ' + str(last) + '\n')
            xdsin = jobs + xds_defaults + data_range
            self.write_script_file('XDS.INP', xdsin)
            os.system('xds_par > XDS.LOG')
            # Check to see if XDS was able to index off of 5 images.
            successful_index = self.check_xds_index('XDS.LOG')
            if successful_index == False:
                last += 1
                count += 1
                time.sleep(wait)
            
        jobs = ['JOB=DEFPIX\n']
        xdsin = jobs + xds_defaults + data_range
        self.write_script_file('XDS.INP', xdsin)
        os.system('xds > DEFPIX.LOG')
        os.chdir(self.input[1]['work'])
        return()

    def check_xds_index (self, logfile):
        '''
        Checks to see if xds successfully indexed.
        '''
        check = True
        index_error = '!!! ERROR !!! CANNOT CONTINUE WITH A TWO-DIMENSIONAL'
        log = open(logfile, 'r').readlines()
        for line in log:
            if index_error in line:
                check = False
                break
        return(check)

    def write_script_file (self, filename, file_input):
        self.logger.debug('write_script_file')
        with open(filename, 'w') as file:
            file.writelines(file_input)
        return()

    def xds_run(self, directory, q):
        self.logger.debug('xds_run')
        # Change lines below to change how XDS is launched.
        os.chdir(directory)
        # Command to launch xds on the computing cluster
        # -sync y synchronizes the process with the submitted job (i.e. it waits
        # for the job to finish), -b y tells qsub to intepret the job as a 
        # binary command rather than a shell script, - j y joins the jobs error
        # and output streams into one file, -pe mp 4 tells the job to use a
        # parallel environment (type is mp) of up to 4 processors, 
        # -terse suppresses the qsub command to only output the submitted jobs
        # job id (which is than caught by this script), -o XDS.LOG redirects the
        # output of the job to XDS.LOG, and -cwd tells the job to run in the
        # current working directory.
        if self.beamline == '24_ID_E':
            project = '-P e'
        elif self.beamline == '24_ID_C':
            project = '-P c'
        else:
            project = ''
        command = ('qsub -sync y -b y -j y %s -terse -o XDS.LOG -cwd xds_par' % project)
        p = pexpect.spawn(command)
        job = p.readline().strip()
        self.logger.debug('Start qsub job %s' % job)
        q.put(job)
        p.wait()
        #os.system(command)
        os.chdir('../')
        q.put(directory)
        return()
    
    def xds_total(self, xdsinput, first, images, template, queue):
        self.logger.debug('xds_total first %s images %s'
                          % (first, images) )
        # Controls processing by xds, pointless, and scala
        # when all images are already collected.
        xdsinput.insert(0, 'JOB=INTEGRATE CORRECT !YXCORR INIT COLSPOT IDXREF DEFPIX INTEGRATE CORRECT\n')
        xdsinput.insert(-1, 'MAXIMUM_NUMBER_OF_JOBS=14\n')
        last = first + images - 1
        proc_dir = self.prepare_integration(xdsinput, first, last)
        int_results = Queue()
        int_job = Process(target = self.xds_run,
                          args = (proc_dir, int_results))
        int_job.start()
        tmp = int_results.get()
        self.logger.debug ('Received job number %s' % tmp)
        tmp = int_results.get()
        
        # Check for an XDS error.
        logpath = os.path.join(tmp, 'XDS.LOG')
        log = open(logpath, 'r').readlines()
        for line in log:
            if 'forrtl' in line:
                # Try defining beam divergene and reflecting range explicitly.
                tmpinput = xdsinput[:]
                tmpinput.append('REFLECTING_RANGE=1.5 REFLECTING_RANGE_E.S.D.=0.15\n')
                tmpinput.append('BEAM_DIVERGENCE=0.921 BEAM_DIVERGENCE_E.S.D.=0.092\n')
                tmpinput.append('DATA_RANGE=%s %s' % (str(first), str(last)))
                path = os.path.join(tmp, 'XDS.INP')
                self.write_script_file(path, tmpinput)
                os.system('rm %s' % logpath)
                int_results2 = Queue()
                int_job2 = Process(target = self.xds_run,
                                   args = (tmp, int_results2))
                int_job2.start()
                tmp = int_results2.get()
                self.logger.debug('Received job number %s' % tmp)
                tmp = int_results2.get()
                log2 = open(logpath, 'r').readlines()
                for line in log2:
                    if 'forrtl' in line:
                        self.logger.debug('XDS encountered an unexpected error.')
                        self.logger.deubg('FastIntegration has failed.')
                        queue.put('Finished')
                        return()
        
        # Launch scaling once integration is finished
        scaling_results = Queue()
        scaling_job = Process(target = self.run_scaling,
                               args = (tmp, scaling_results))
        scaling_job.start()
        pass_back = scaling_results.get()
        if pass_back[1] != 'failed':
            queue.put(pass_back)
        self.logger.debug('exiting xds_total')
        queue.put('Finished')
        return()
    
    def xds_processing(self, xdsinput, first, images, template, exp_time, osc_angle, queue):
        self.logger.debug('xds_processing first %s images %s'
                          % (first, images) )
        # Controls processing by xds, pointless, and scala
        int_jobs=[]
        int_results=[]
        int_job_ids=[]
        scaling_jobs=[]
        scaling_results=[]
        sca_count = 0 # Counts how many scaling jobs have finished.
        last_frame = first + images - 1
        first_frame = first
        frame_count = first + 5
        look_for = template + str(frame_count).zfill(3) + '.img'
        finished_count = 0 # Counts how many integration jobs have finished.
        # Max wait time for new image = exp_time + 10 seconds.
        wait_time = exp_time + 30.0
        wedge_size = 10

        xdsinput.insert(0, 'JOB=INTEGRATE CORRECT\n')
        xdsinput.insert(-1, 'MAXIMUM_NUMBER_OF_PROCESSORS=8\n')
        xdsinput.insert(-1, 'MAXIMUM_NUMBER_OF_JOBS=14\n')

        time_process = Process(target = self.timer, args = (wait_time,))
        time_process.start()

        while frame_count <= last_frame:
            # If a scaling job has finished, return its results
            if (sca_count < len(scaling_jobs) and
                  scaling_jobs[sca_count].is_alive() == False):
                pass_back = scaling_results[sca_count].get()
                if pass_back[1] != 'failed':
                    self.logger.debug ('Passing back scaling results')
                    queue.put(pass_back)
                sca_count += 1
            # If any integrations have finished, start its scaling job.
            if  finished_count < len(int_jobs) and int_jobs[finished_count].is_alive() == False:
                tmp = int_results[finished_count].get()
                self.logger.debug('Integration finished!')
                self.logger.debug('finished_count = %i' % finished_count)
                scaling_results.append(Queue())
                scaling_jobs.append(Process(target = self.run_scaling,
                                            args = (tmp, scaling_results[-1])))
                scaling_jobs[-1].start()
                finished_count += 1
            # If next image file exists...
            if os.path.isfile(look_for) == True:
                # Reset the timer process
                if time_process.is_alive():
                    time_process.terminate()
                time_process = Process(target = self.timer, args = (wait_time,))
                time_process.start()
                # If frame_count divisble by 10, setup and run xds integrate job.
                if frame_count % wedge_size == 0:
                    proc_dir = self.prepare_integration(xdsinput, first, frame_count)
                    int_results.append(Queue())
                    int_jobs.append(Process(target = self.xds_run,
                                        args = (proc_dir, int_results[-1])))
                    int_jobs[-1].start()
                    int_job_ids.append(int_results[-1].get())
                    self.logger.debug ('Started wedge_1_%i as qsub job %s.'
                                       % (frame_count, int_job_ids[-1]))
                    #first_frame += 20
                # Increment the frame_count to look for next image
                frame_count += 1
                # Increment wedge sizes if data collections 
                # reach certain sizes.
                if frame_count == 99:
                    wedge_size = 20
                elif frame_count == 179:
                    wedge_size = 40
                    
                look_for = template + str(frame_count).zfill(3) + '.img'

            # If next image doesn't exist, check to see if timer has expired.
            # If time has expired, assume an abort occurred
            else:
                if time_process.is_alive() == False:
                    self.logger.debug ('Could not see image %s after waiting.'
                                        % look_for)
                    self.logger.debug ('RAPD assumes an abort has occurred.')
                    break

        # Now frame_count either equal to last_frame + 1 or RAPD sensed an abort
        # and frame_count is the last image observed + 1.
        # If frame_count - 1 is divisible by 10, the last xds job was already submitted.
        # Otherwise, a new xds job needs to be executed
        if (frame_count -1) % wedge_size != 0:
            proc_dir = self.prepare_integration(xdsinput, first_frame, frame_count - 1)
            int_results.append(Queue())
            int_jobs.append(Process(target = self.xds_run,
                                    args = (proc_dir, int_results[-1])))
            int_jobs[-1].start()
            int_job_ids.append(int_results[-1].get())
            self.logger.debug('Started wedge_1_%i as qsub job %s.'
                              % (frame_count -1, int_job_ids[-1]))

            
        # Once last integration is launched, monitor for end
        # of integrations.
        self.logger.debug ('length of int_jobs = %i' % len(int_jobs))
        self.logger.debug ('monitoring integration')
        self.logger.debug ('finished_count = %i, sca_count = %i'
               % (finished_count, sca_count))
        while finished_count < len(int_jobs):
            if int_jobs[finished_count].is_alive() == False:
                tmp = int_results[finished_count].get()
                scaling_results.append(Queue())
                scaling_jobs.append(Process(target = self.run_scaling,
                                        args = (tmp, scaling_results[-1])))
                scaling_jobs[-1].start()
                finished_count += 1
                self.logger.debug ('one integration finished')
                self.logger.debug ('finished_count = %i, sca_count = %i'
                      % (finished_count, sca_count))
            if (sca_count < len(scaling_jobs) and
                    scaling_jobs[sca_count].is_alive() == False):
                pass_back = scaling_results[sca_count].get()
                if pass_back[1] != 'failed':
                    self.logger.debug ('Passing back scaling results')
                    queue.put(pass_back)
                sca_count += 1
                self.logger.debug ('one scaling finished')
                self.logger.debug ('fnished_count = %i, sca_count = %i'
                      % (finished_count, sca_count))

        # Once integrations are finished, monitor any remaining
        # scaling jobs.
        self.logger.debug ('Monitoring scaling')
        # Check to see if any scaling jobs have finished
        for s in range(sca_count,len(scaling_jobs),1):
            pass_back = scaling_results[s].get()
            if pass_back[1] != 'failed':
                queue.put(pass_back)
            self.logger.debug ('one scaling finished')
            self.logger.debug ('sca_count = %i' % s)

        queue.put('Finished')
        self.logger.debug ('Exiting xds_processing')

        return()

    def timer(self, wait):
        '''
        Runs for wait time in seconds then expires
        '''
        time.sleep(wait)
        return()
    
    def abort_check(self, dir):
        self.logger.debug('abort_check on %s' % dir)
        xdslog = os.path.join(dir,'XDS.LOG')
        tmpfile = open(xdslog, 'r').readlines()
        for linenum,line in enumerate(tmpfile):
            if '!!! ERROR !!! CANNOT READ IMAGE' in line:
                filename = line.split()[-1]
                if os.path.isfile(filename):
                    return(False)
                else:
                    return(True)
            elif line.startswith(' IMAGE IER  SCALE'):
                for n in range(1,6,1):
                    splitline = tmpfile[linenum + n].split()
                    if splitline[1] == '-1':
                        return(True)
        return(False)

    def xds_processing_wait(self, xdsinput, first, images, template, exp_time, osc, queue):
        self.logger.debug('xds_processing first %s images %s'
                          % (first, images) )
        # Controls processing by xds, pointless, and scala
        # Used to launch a single xds job while data is still be collected.
        # Useful for unbinned data sets that tend to bog down the network
        # when multiple jobs are running at once.
        last_frame = first + images - 1
        
        xdsinput.insert(0, 'JOB=INTEGRATE CORRECT\n')
        wait_time = str(exp_time + 5.0)
        xdsinput.insert(-1, 'SECONDS=%s\n' % wait_time )
        
        proc_dir = self.prepare_integration(xdsinput, first, last_frame)
        int_results = Queue()
        int_job = Process(target = self.xds_run,
                            args = (proc_dir,int_results))
        int_job.start()
        tmp = int_results.get()
        self.logger.debug('Received job number %s' % tmp)
        tmp = int_results.get()
        # Launch scaling once integration is finished
        scaling_results = Queue()
        scaling_job = Process(target = self.run_scaling,
                              args = (tmp, scaling_results))
        scaling_job.start()
        pass_back = scaling_results.get()
        if pass_back[1] != 'failed':
            queue.put(pass_back)
        self.logger.debug('exiting xds_processing_wait')
        queue.put('Finished')
        return()
    
    def check_scala (self, logfile):
        '''
        Checks scala logfile for 'Normal termination'
        '''
        scala_worked = False
        #log_file = os.path.join(self.input[1]['work'], logfile)
        #self.logger.debug (log_file )
        log = open(logfile, 'r').readlines()
        for i in range (len(log)-1, 0, -1):
            if 'Normal termination' in log[i]:
                scala_worked = True
                break
        return(scala_worked)

    def prepare_integration(self, input, first, last):
        '''
        Prepares directory structure for wedge processing.
        Copies necessary files into the directory
        Writes and XDS.INP in the directory
        '''
        self.logger.debug('prepare_integration')
        # A list of files to be copied into the new directory
        files = ['XPARM.XDS', 'GAIN.cbf', 'X-CORRECTIONS.cbf',
                 'Y-CORRECTIONS.cbf', 'BLANK.cbf', 'BKGPIX.cbf']
        wedge_dir = '_'.join(['wedge', str(first), str(last)])
        if os.path.isdir(wedge_dir) == False:
            os.mkdir(wedge_dir)
        
        for file in files:
            copy_command = ('cp ' + os.path.join('initialXDS',file)
                            + ' ' + wedge_dir)
            os.system(copy_command)
            
        tmp_input = input[:]
        tmp_input.append('DATA_RANGE=' + str(first) + ' ' + str(last) + '\n')
        # tmp_input.append('MINUTE=1')
        path = os.path.join(wedge_dir,'XDS.INP')
        self.write_script_file(path, tmp_input)
        return(wedge_dir)
    
    def run_scaling(self, directory, update):
        '''
        Controls the running of XDS on each wedge.
        Then launches pointless, and scala for scaling.
        '''
        self.logger.debug('run_scaling directory %s' % directory)
        # update.put(False)
        os.chdir(directory)
        #self.xds_run(directory)
        res_cut = self.parse_correct()
        if self.run_pointless(directory) == False:
            self.logger.debug('Pointless failed to complete.')
            update.put([directory, 'failed'])
        scala_log = self.run_scala(directory, res_cut)

        try:
            res_cut = self.find_scala_resolution(scala_log)
        except:
            update.put([directory, 'failed'])
            return()
        
        if res_cut != False:
            os.system('mv ' + scala_log + ' old_scala.log')
            scala_log = self.run_scala(directory,res_cut)
        results = self.pipe_results(scala_log)
        if results == 'failed':
            self.logger.debug('Failed to properly return results.')
            self.logger.debug('Will continue anyway.')
            update.put([directory, results])
            return()
        else:
            self.logger.debug('run_scaling :: Received results from pipe_results') 
            update.put([directory, results])
            return()
    
    def parse_correct(self):
        '''
        Parse the CORRECT.LP file to determine an initial
        resolution for use by scala
        '''
        self.logger.debug('parse_correct')
        new_hi_res = False
        try:
            corlog = open('CORRECT.LP', 'r').readlines()
        except:
            return(new_hi_res)
        flag = 0
        keyline = 'SUBSET OF INTENSITY DATA WITH SIGNAL/NOISE >= -3.0'
        for line in corlog:
            try:
                if line.split()[-1] == 'INTEGRATE.HKL':
                    self.logger.debug('ISa = %s' % line.split()[2])
            except:
                pass
            if keyline in line:
                if flag == 0:
                    flag = 1
            if flag == 1:
                sline = line.split()
                if (len(sline) == 14 and sline[0][0].isdigit()):
                    if float(sline[8]) < 1.0:
                        # Check to see if new resolution is higher than old.
                        tmp_hi_res = sline[0]
                        if float(tmp_hi_res) < float(new_hi_res):
                            new_hi_res = tmp_hi_res
                        flag = 0
        return(new_hi_res)
            
    def run_pointless(self, prefix):
        '''
        Runs pointless after integration.
        '''
        try:
            self.logger.debug('run_pointless prefix %s' % prefix)
            pointlessMTZ = '_'.join([prefix, 'pointless.mtz'])
            pointlessLOG = pointlessMTZ.replace('mtz','log')
            # SETTING C2 ensures pointless chooses C2 rather than I2
            # when the choice exists.  This ensures compatibility of 
            # the chosen spacegroup with non-CCP4 programs.
            pointless_command = ('pointless xdsin XDS_ASCII.HKL hklout '
                                + pointlessMTZ + ' << eof > ' + pointlessLOG
                                + ' \n SETTING C2 \n eof')
            p = subprocess.Popen(pointless_command, shell = True)
            sts = os.waitpid(p.pid, 0)[1]
            # Check if pointless completed run.
            tmp = open(pointlessLOG, 'r').readlines()
            if tmp[-2].startswith('P.R.Evans'):
                return(True)
            else:
                return(False)
        except:
            self.logger.debug('Error in pointless')
            return(False)

    def run_scala(self, prefix, resolution):
        '''
        Runs scala for scaling.
        '''
        self.logger.debug('run_scala prefix %s resolution %s'
                          % (prefix, str(resolution) ) )
        scalaMTZ = '_'.join([prefix, 'scaled.mtz'])
        pointlessMTZ = scalaMTZ.replace('scaled', 'pointless')
        scalaLOG = scalaMTZ.replace('mtz', 'log')
        scala_comfile = scalaMTZ.replace('mtz', 'com')
        
        scala_file = ['#!/bin/csh\n']
        scala_file.append('scala hklin ' + pointlessMTZ + ' \\\n')
        scala_file.append('hklout ' + scalaMTZ + ' <<eof\n')
        scala_file.append('run 1 all\n')
        scala_file.append('anomalous on\n')
        scala_file.append('scales constant\n')
        scala_file.append('sdcorrection noadjust norefine both 1 0 0\n')
        scala_file.append('cycles 0\n')
        #scala_file.append('scales rotation spacing 5 ')
        #scala_file.append('bfactor on brotation spacing 10\n')
        #scala_file.append('tie bfactor 0.5\n')
        if resolution != False:
            scala_file.append('resolution_high ' + str(resolution) + '\n')
        scala_file.append('eof')
        
        self.write_script_file(scala_comfile, scala_file)
        os.system('chmod 755 ' + scala_comfile)
        #scala_runline = './' + scala_comfile + ' > ' + scalaLOG
        if self.beamline == '24_ID_C':
            project = '-P c'
        elif self.beamline == '24_ID_E':
            project = '-P e'
        else:
            project = ''
        scala_runline = ('qsub -sync y -j y %s -o ' % project)
        scala_runline += (scalaLOG +' -cwd ' + scala_comfile)
        p = subprocess.Popen(scala_runline, shell = True)
        sts = os.waitpid(p.pid, 0)[1]
        self.logger.debug('Scala qsub process completed')
        
        return(scalaLOG)
            
    def pipe_results (self, log):
        '''
        Return results back up the pipe
        '''
        self.logger.debug('pipe_results')
        graphs, tables = self.parse_scala(log)
        scalaHTML = self.scala_plots(graphs,tables)
        try:
            parseHTML, summary = self.parse_results(log)
        except:
            self.logger.debug('Results not parsed correctly.')
            pass
        try:
            longHTML = self.make_long_results(log)
        except:
            pass
        try:
            os.system('mv ' + scalaHTML + ' ' + self.input[1]['work'])
            os.system('mv ' + parseHTML + ' ' + self.input[1]['work'])
            os.system('mv ' + longHTML + ' '  + self.input[1]['work'])
            dirlong = os.path.join(self.input[1]['work'], longHTML)
            if os.path.isfile(dirlong) == False:
                self.logger.debug('long results file was not moved correctly')
        except:
            return('failed')
        results = {'status' : 'WORKING',
                        'plots' : scalaHTML,
                        'short' : parseHTML,
                        'long' : longHTML,
                        'summary' : summary}
        self.logger.debug('Returning results')
        self.logger.debug(results)
        tmp = self.input[:]
        tmp.append(results)
        # self.pipe.send(self.results)
        self.logger.debug('pipe_results:: calling sendback2')
        self.sendBack2(tmp)
        self.logger.debug('Results returned, exiting pipe_results')
        return(results)
    
    def find_scala_resolution(self, scalalog):
        '''
        Parse the scala logfile to find a realistic cutoff condition
        '''
        self.logger.debug('find_scala_resolution')
        scalog = open(scalalog, 'r').readlines()
        new_hi_res = False
        count = 0
        IsigI = 0
        hires = 0
        for line in scalog:
            if 'Average I,sd and Sigma' in line:
                count = 1
                #self.logger.debug ('Hi res I/sigI')
                #self.logger.debug ('====================')
            if count > 0:
                sline = line.split()
                if (len(sline) > 10 and sline[0].isdigit()):
                    #self.logger.debug ('%s %s' % (sline[2],sline[12]))
                    prev_IsigI = IsigI
                    prev_hires = hires
                    IsigI = float(sline[12])
                    hires = float(sline[2])
                    if IsigI < 2.0:
                        self.logger.debug ('Values to interpolate:')
                        self.logger.debug ('mn(I/sigI)   HiRes')
                        self.logger.debug ('%f     %f' %(prev_IsigI, prev_hires))
                        self.logger.debug ('%f     %f' %(IsigI, hires))
                        new_hi_res = interp([2.0],[IsigI,prev_IsigI],
                                            [hires,prev_hires])
                        self.logger.debug ('New hi res %f' % new_hi_res)
                        break
            if count > 0 and 'Overall' in line:
                break
        
        if new_hi_res != False:
            cutoff = str(new_hi_res[0])
        else:
            cutoff = False
        return(cutoff)            
                
    def parse_scala (self, logfile):
        """
        Parses the scala logfile in order
        to pull out data for graphs

        Returns a list of tuples called graphs
        and a nested list called tables:
        tuple in graphs contains:
            '<*graph title*>' , [data_labels], [table# , col#s]
            where:
                data_labels are the label for the X-axis and for any data
                table# gives a position for the table where the data is located
                col#s gives positions of the columns within the table that will
                    be plotted.

        tables contains all of the tables within the scala logfile
        such that table[n] is the nth table in the logfile
        and to read the data from table[n] you can loop as follows:
        (example would read out the 1st and 5th column of data)
        for line in table[n]:
            xValue = line[0]
            yValue = line[4]
        """
        self.logger.debug('parse_scala')
        log = open(logfile, 'r').readlines()

        # Initalize the variables that will be returned
        graphs = []
        tables = []

        # Initalize some variables to be used for parsing
        tableHeaders=[]
        label_start= ['N', 'Imax', 'l', 'h', 'k', 'Range']

        # Find and grab each table in the logfile
        for i,v in enumerate(log):
            if 'TABLE' in v:
                header = []
                data=[]
                while 'applet>' not in log[i]:
                    # Skip blank lines
                    if log[i] == '\n':
                        i+=1
                    # Pull out header information for table
                    elif 'GRAPHS' in log[i]:
                        while log[i] != '\n' and log[i].split()[0] != '$$':
                            header.append(log[i].strip())
                            i+=1
                    # If first character on line is a number, assume it's data.
                    elif log[i].strip()[0].isdigit():
                        data.append(log[i].split())
                        i+=1
                    else:
                        for start in label_start:
                            if log[i].strip().startswith(start):
                                header.append(log[i].strip())
                        i+=1
                tableHeaders.append(header)
                tables.append(data)
        # Parse the table headers to get titles, labels, and positions.
        for tableNum, head in enumerate(tableHeaders):
            collabels = head[-1].split()
            ycols=[]
            title=''
            for line in head:
                if ':' in line:
                    for i in line.split(':'):
                        if len(i) > 2 and 'GRAPHS' not in i and '$$' not in i:
                            if i[0].isdigit() and ',' in i:
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
                            # change xlabel from 1/d^2 or 1/resol^2 to Dmin
                            if xlabel == '1/d^2' or xlabel == '1/resol^2':
                                xlabel = 'Dmin (A)'
                            for y in ycols:
                                ylabels.append(collabels[y])
                            graph = title, xlabel, ylabels, xcol, \
                                    ycols, tableNum
                            # Reset the variable ycols and title
                            ycols =[]
                            title=''
                            graphs.append(graph)

        return(graphs, tables)
    
    def scala_plots(self, graphs, tables):
        """
        generate plots html file from scala results
        """
        self.logger.debug('scala_plots')
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
                     'RMS correlation ratio'            : 'RCR'
                     }

        scala_plot = """<html>
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
                scala_plot += '        <li><a href="#tabs-22' + str(i) + '">' + title + '</a></li>\n'
        scala_plot += '      </ul>\n'

        # Define title and x-axis label for each graph
        for i,graph in enumerate(graphs):
            if graph[0] in plotThese:
                scala_plot += '      <div id ="tabs-22' + str(i) + '">\n'
                scala_plot += '        <div class="title"><b>'
                scala_plot += graph[0] + '</b></div>\n'
                scala_plot += '        <div id="chart' + str(i) + '_div" style='
                scala_plot += '"width:800px;height:600px"></div>\n'
                scala_plot += '        <div class="x-label">'
                scala_plot += graph[1] + '</div>\n'
                scala_plot += '      </div>\n'

        scala_plot += """</div> <!-- End of Tabs -->
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

                scala_plot += '    var '
                # graph[2] is the label for the y-values
                for ylabel in (graph[2]):
                    varLabel.append(ylabel)
                    var = 'y' + str(varNum)
                    varNum += 1
                    data.append(var)
                    if ylabel == graph[2][-1]:
                        scala_plot += var + '= [];\n'
                    else:
                        scala_plot += var + ' = [], '
                xcol = graph[3]
                for line in tables[graph[5]]:
                    for y,ycol in enumerate(graph[4]):
                        if line[ycol] != '-':
                            scala_plot += '         ' + data[y] + '.push(['
                            scala_plot += line[xcol] + ',' + line[ycol]
                            scala_plot += ']);\n'

                scala_plot += '    var plot' + str(i)
                scala_plot += ' = $.plot($("#chart' + str(i) + '_div"), [\n'
                for x in range(0,len(data),1):
                    scala_plot += '        {data: ' + data[x] + ', label:"'
                    scala_plot += varLabel[x] + '" },\n'
                scala_plot += '        ],\n'
                scala_plot += '        { lines: {show: true},\n'
                scala_plot += '          points: {show: false},\n'
                scala_plot += "          selection: { mode: 'xy' },\n"
                scala_plot += '          grid: {hoverable: true, '
                scala_plot += 'clickable: true },\n'
                if graph[1] == 'Dmin (A)':
                    scala_plot += '          xaxis: {ticks: [\n'
                    for line in tables[graph[5]]:
                        scala_plot += '                         ['
                        scala_plot += line[xcol] + ',"' + line[xcol+1]
                        scala_plot += '"],\n'
                    scala_plot += '                  ]},\n'
                scala_plot += '    });\n\n'

        scala_plot += """
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
                scala_plot += '    $("#chart' + str(i) + '_div").bind'
                scala_plot += """("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (true) {
            if (item) {
                if (previousPoint != item.datapoint) {
                    previousPoint = item.datapoint;

                    $("#tooltip").remove();
"""
                if graph[1] == 'Dmin (A)':
                    scala_plot += '                    '
                    scala_plot += \
                    'var x = (Math.sqrt(1/item.datapoint[0])).toFixed(2),\n'
                else:
                    scala_plot += '                    '
                    scala_plot += 'var x = item.datapoint[0].toFixed(2),\n'
                scala_plot += \
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
        scala_plot += '\n});\n</script>\n </body>\n</html>'

        try:
            with open('scala_plot.html','w') as file:
                file.write(scala_plot)
            return('scala_plot.html')
        except IOError:
            self.logger.debug ('Could not create scala plot html file.')
            return ('Error')
        
    def parse_results(self,scala_log):
        '''
        Parse the scala log file for display to UI
        '''
        self.logger.debug('parse_results')
        results = {}
        wedge_split = scala_log.split('_')
        results['wedge'] = '-'.join(wedge_split[1:3])
        # Pull out a summary of the scala results
        scala_lines = open(scala_log, 'r').readlines()
        table_start = 0
        flag = 0
        results['CC_cut'] = False
        results['RCR_cut'] = False
        for i,v in enumerate(scala_lines):
            if v.startswith('Summary data for'):
                table_start = i + 1
            elif v.startswith('$GRAPHS: Anom & Imean CCs'):
                flag = 1
            elif flag == 1 and v.startswith(' Overall'):
                flag = 0
                results['CC_anom_overall'] = v.split()[1]
                results['RCR_anom_overall'] = v.split()[5]
            elif flag == 1:
                vsplit = v.split()
                if len(vsplit) > 1 and vsplit[0].isdigit():
                    if vsplit[3] == '-' or vsplit[7] == '-':
                        pass
                    else:
                        anom_cc = float(vsplit[3])
                        anom_rcr = float(vsplit[7])
                        # self.logger.debug ('CC_anom = %s RCR_anom = %s' % (vsplit[3],vsplit[7]) )
                        if anom_cc >= 0.3:
                            results['CC_cut'] = [ vsplit[2], vsplit[3] ]
                        if anom_rcr >= 1.5:
                            results['RCR_cut'] = [ vsplit[2], vsplit[7] ]
        
            
             
        for i,v in enumerate(scala_lines[table_start:]):
            vsplit = v.split()
            vstrip = v.strip()

            #bin resolution limits
            if vstrip.startswith('Low resolution limit'):
                results['bins_low'] = vsplit[3:6]
            elif vstrip.startswith('High resolution limit'):
                results['bins_high'] = vsplit[3:6]

            #Rmerge
            elif (vstrip.startswith('Rmerge      ')):
                results['rmerge'] = vsplit[1:4]
            elif (vstrip.startswith('Rmerge in top intensity bin')):
                results['rmerge_top'] = [vsplit[5]]

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
            elif (vstrip.startswith('Fractional partial bias')):
                results['bias'] = vsplit[3:6]

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
            file.write('<h3 class="green">Processing Results for images %s</h3>\n'
                       % results['wedge'])
            spacegroupLine = ('<h2>Spacegroup: ' + results['scale_spacegroup']
                               + '</h2>\n')
            spacegroupLine += ('<h2>Unit Cell: ' + 
                               ' '.join(results['scaling_unit_cell'])+ '</h2>\n')
            file.write(spacegroupLine)
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
                      ('Partial bias','bias'),
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
            slope = float(results['anom_slope'][0])
            flag = False
            
            file.write('<div align="left">')
            file.write('<h3 class="green">Analysis for anomalous signal.</h3>\n')
            file.write('<pre>An anomalous slope > 1 may indicate the presence ' 
                       + 'of anomalous signal.\n')
            file.write('This data set has a anomalous slope of %s.\n'
                       % results['anom_slope'][0])
            if slope > 1.1:
                file.write('Analysis of this data set indicates the presence '
                           + 'of a significant anomalous signal.\n')
                flag = True
            elif slope > 1.0:
                file.write('Analysis of this data set indicates either a weak '
                           + 'or no anomalous signal.\n')
                flag = True
            else:
                file.write('Analysis of this data set indicates no detectable '
                           + 'anomalous signal.\n')
            
            if flag == True and results['CC_cut'] != False:
                file.write('The anomalous correlation coefficient suggests the '
                           + 'anomalous signal extends to %s Angstroms.\n'
                           % results['CC_cut'][0] )
                file.write('(cutoff determined where CC_anom is above 0.3)\n')
            if flag == True and results['RCR_cut'] != False:
                file.write('The r.m.s. correlation ratio suggests the anomalous '
                           + 'signal extends to %s Angstroms.\n' 
                           % results['RCR_cut'][0] )
                file.write('(cutoff determined where RCR_anom is above 1.5)\n')
            if (flag == True and 
                results['CC_cut'] == False and results['RCR_cut'] == False):
                file.write('A cutoff for the anomalous signal could not '
                           + 'be determined based on either the\n'
                           + 'anomalous correlation coeffecient or '
                           + 'by the r.m.s. correlation ratio\n\n')
            file.write('</pre></div><br>\n')
            

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
            file.write('  scala  -  Scaling and assessment of data quality. ' +
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
        Grab the content of passed in files and put them in a php file
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
  <!--<script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.js"></script>-->
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
      $('#pdb1').dataTable({
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
            pointless_log = logfile.replace('scaled', 'pointless')
            in_lines = open(pointless_log, 'r').readlines()
            for in_line in in_lines:
                if '<I' in in_line or '<P' in in_line or '<H':
                    in_line = in_line.replace('<','&lt')
                    in_line = in_line.replace('>','&gt')
                file.write(in_line)
            file.write('</pre>\n</div>\n')
            file.write('<h3><a href="#">Click to view Scala log file.</a></h3>\n')
            file.write('<div>\n<pre>\n')
            file.write('==========    scala    ==========\n')
            in_lines = open(logfile, 'r').readlines()
            for in_line in in_lines:
                if 'applet' in in_line or in_line.startswith('codebase'):
                    pass
                else:
                    #if '&' in in_line:
                    #    in_line.replace('&','&amp')
                    if '<I' in in_line:
                        in_line = in_line.replace('<','&lt')
                        in_line = in_line.replace('>','&gt')
                    file.write(in_line)
            file.write('</pre>\n</div>\n')
            file.write('<h3><a href="#">Click to view INTEGRATE.LP.</a></h3>\n')
            file.write('<div>\n<pre>\n')
            file.write('==========    INTEGRATE.LP    ==========\n')
            in_lines = open('INTEGRATE.LP', 'r').readlines()
            for in_line in in_lines:
                if '<I' in in_line:
                    in_line = in_line.replace('<','&lt')
                    in_line = in_line.replace('>','&gt')
                file.write(in_line)
            file.write('</pre>\n</div>\n')
            file.write('<h3><a href="#">Click to view CORRECT.LP.</a></h3>\n')
            file.write('<div>\n<pre>\n')
            file.write('==========   CORRECT.LP    ==========\n')
            in_lines = open('CORRECT.LP', 'r').readlines()
            for in_line in in_lines:
                #if '&' in in_line:
                #    in_line.replace('&','&amp')
                if '<I' in in_line:
                    in_line = in_line.replace('<','&lt')
                    in_line = in_line.replace('>','&gt')
                file.write(in_line)
            file.write('</pre>\n</div>\n</div>\n')
            file.write('</body>')
            
            return(longHTML)
        
    def finish_data (self, in_file):
        '''
        Finish the data by truncating and adding free R flag
        '''
        self.logger.debug('finish_data in_file %s' % in_file)
        
        # Truncate the data.
        comfile = open('truncate.sh', 'w')
        comfile.write('#!/bin/csh \n')
        comfile.write('truncate hklin ' + in_file + ' hklout truncated.mtz'
                      + ' > truncate.log << eof \n')
        comfile.write('eof \n')
        comfile.close()
        # Change permissions and run the file.
        os.system('chmod 755 truncate.sh')
        p = subprocess.Popen('./truncate.sh', shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        
        # Set the free R flag.
        comfile = open('freer.sh', 'w')
        comfile.write('#!/bin/csh \n')
        comfile.write('freerflag hklin truncated.mtz hklout freer.mtz'
                      + ' > freer.log << eof \n')
        comfile.write('END \n')
        comfile.write('eof \n')
        comfile.close()
        # Change permissions and run the file.
        os.system('chmod 755 freer.sh')
        p = subprocess.Popen('./freer.sh', shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        
        # Create merged scalepack format file
        comfile = open('mtz2scaNAT.sh', 'w')
        comfile.write('#!/bin/csh \n')
        comfile.write('mtz2various hklin truncated.mtz hklout NATIVE.sca'
                      + ' >mtz2scaNAT.log << eof \n')
        comfile.write('OUTPUT SCALEPACK \n')
        comfile.write('labin I(+)=IMEAN SIGI(+)=SIGIMEAN \n')
        comfile.write('END \n')
        comfile.write('eof \n')
        comfile.close()
        # Change permissions and run the file.
        os.system('chmod 755 mtz2scaNAT.sh')
        p = subprocess.Popen('./mtz2scaNAT.sh', shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        # Edit the sca file to correct the format of the spacegroup
        self.fixMtz2Sca('NATIVE.sca')
        utils.fixSCA(self, 'NATIVE.sca')
        
        # Create the unmerged scalepack format file
        comfile = open('mtz2scaANOM.sh','w')
        comfile.write('#!/bin/csh \n')
        comfile.write('mtz2various hklin truncated.mtz hklout ANOM.sca >'
                      + ' mtz2scaANOM.log << eof \n')
        comfile.write('OUTPUT SCALEPACK \n')
        comfile.write('labin I(+)=I(+) SIGI(+)=SIGI(+) I(-)=I(-)'
                      + ' SIGI(-)=SIGI(-)\n')
        comfile.write('END \n')
        comfile.write('eof \n')
        comfile.close()
        # Change permissions and run the file.
        os.system('chmod 755 mtz2scaANOM.sh')
        p = subprocess.Popen('./mtz2scaANOM.sh',shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        try:
            self.fixMtz2Sca('ANOM.sca')
            utils.fixSCA(self,'ANOM.sca')
        except:
            self.logger.debug('fixMtz2Sca failed to run.')
            self.logger.bebug('This is usually due to failure in truncate.')
            return('failed')
        
        return('freer.mtz')
    
    def fixMtz2Sca(self,scafile):
        """
        Fix the error in the sca file from mtz2various
        by eliminating the spaces in spacegroup
        """
        self.logger.debug('fixMtz2Sca file:%s' % scafile)

        inlines = open(scafile,'r').readlines()
        symline = inlines[2]
        newline = (symline[:symline.index(symline.split()[6])]
                   +''.join(symline.split()[6:])+'\n')
        inlines[2] = newline

        outfile = open(scafile,'w')
        for line in inlines:
            outfile.write(line)
        return()
    
    def process_shelxC(self, unitcell, spacegroup, scafile):
        '''
        Runs shelxC to find a resolution cutoff for the anomalous signal.
        '''
        self.logger.debug('FastIntegration::process_shelx(%s, %s, %s)'
                          % (unitcell, spacegroup,scafile))
        try:
            command = 'shelxc junk << EOF\n'
            command += 'CELL ' + ' '.join(unitcell) + '\n'
            command += 'SPAG ' + spacegroup + '\n'
            command += 'SAD ' + scafile + '\n'
            command += 'EOF\n'
            shelx_log = []
            output0 = subprocess.Popen(
                        command, shell = True, stdout = subprocess.PIPE,
                        stderr = subprocess.STDOUT)
            for line in output0.stdout:
                shelx_log.append(line.strip())
                self.logger.debug(line.rstrip())
            results = self.parse_shelxC(shelx_log)
            # Find where d"/sig is > 1.0
            res = False
            for i, v in enumerate(results['shelx_dsig']):
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
        inserts shelxC results into the brief results webpage.
        '''
        self.logger.debug('FastIntegration::insert_shelx_results')
        
        try:
            htmlfile = open('results.php', 'r').readlines()
            if results['shelx_rescut'] == False:
                insert_text = ('\nAnalysis by ShelxC finds no resolution shell '
                               + 'where d"/sig is greater than 1.0.\n\n')
                htmlfile.insert(-10, insert_text)
            else:
                insert_text = ('\nAnalysis by ShelxC finds d"/sig greater than 1.0'
                               + ' for at least one resolution shell.\n')
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
            open('results.php', 'w').writelines(htmlfile)
        except:
            self.logger.exception('**Error in insert_shelx_results**')
    
    def parse_shelxC(self, log):
        '''
        Parse the log output from shelxC.
        '''
        self.logger.debug('FastIntegration::parse_shelxC')
        try:
            shelxc_results ={}
            for line in log:
                if line.startswith('Resl'):
                    shelxc_results['shelx_res'] = line.split()[3::2]
                elif line.startswith('N(data)'):
                    shelxc_results['shelx_data'] = line.split()[1:]
                elif line.startswith('<I/sig>'):
                    shelxc_results['shelx_isig'] = line.split()[1:]
                elif line.startswith('%Complete'):
                    shelxc_results['shelx_comp'] = line.split()[1:]
                elif line.startswith('<d"/sig>'):
                    shelxc_results['shelx_dsig'] = line.split()[1:]
                #elif line.startswith('SHEL'):
                #    shelxc_results['shelx_rescut'] = line.split()[2]
            return(shelxc_results)
        except:
            self.logger.exception('**Error in parse_shelxC**')
            return(False)
    
    def pdbquery (self, cell, data, dir):
        """
        Calls the PDBQuery rapd agent module in order to check
        the PDB data bank for depositions with similar unit cell.
        cell should be the unit cell parameters as a tuple of strings.
        dir is the directory where the output of PDBQuery will be sent.
        data is full path to the sca file containing the data.
        """
        full_data = os.path.join(dir,data)
        self.logger.debug('FastIntegration::pdbquery')
        self.logger.debug('cell = %s' % cell)
        self.logger.debug('data = %s' % full_data)
        self.logger.debug('dir = %s' % dir)
        query_dir = os.path.join(dir, 'pdbquery')
        self.logger.debug('query_dir = %s' % query_dir)
        os.system('mkdir %s' %query_dir)
        # Construct the input to send to PDBQuery.
        try:
            pdb_input = []
            pdb_dict = {}
            #pdb_dict['cell'] = cell
            pdb_dict['dir'] = query_dir
            pdb_dict['data'] = full_data
            pdb_dict['passback'] = True
            pdb_input.append(pdb_dict)
            output0 = None
            output1 = Queue()
            output2 = None

            self.logger.debug(pdb_input)
         
            T = PDBQuery(pdb_input,output0,output1,output2,self.logger)
            T.join()
            results = output1.get()
            
            self.logger.debug(results)
            self.logger.debug('PDBQuery Complete')

            try:
                pdbq = open('pdbquery/jon_summary_cell.php', 'r').readlines()
                longHTML = open('long_results.php', 'r').readlines()
                longHTML.insert(66,'</div>\n')
                for i in range(len(pdbq)-21, 0, -1):
                    if 'body id="dt_example"' in pdbq[i]:
                        text = '      <h3><a href="#">Unit Cell Analysis.</a></h3>\n'
                        text += '      <div>\n'
                        longHTML.insert(66, text)
                    elif '//Tooltips' in pdbq[i]:
                        longHTML.insert(66, pdbq[i])
                        break
                    elif '</head>' in pdbq[i]:
                        longHTML.insert(66, '<div class="accordion">\n')
                        longHTML.insert(66, '<body>\n')
                        longHTML.insert(66, pdbq[i])
                    elif 'bAutoWidth' in pdbq[i]:
                        break
                    elif 'id="pdb"' in pdbq[i]:
                        line = ('        <table cellpadding="0" cellspacing="0"'
                               + ' border="0" class="display" id="pdb1">\n')
                        longHTML.insert(66, line)
                    else:
                        longHTML.insert(66, pdbq[i])
                # Remove some extraneous lines.
                for t in range(0, 5, 1):
                    junk = longHTML.pop(61)
                open('long_results.php', 'w').writelines(longHTML)
            except:
                self.logger.debug('Could not amend results to long.')

            try:
                HTMLfile = open('results.php', 'r').readlines()
                insert_text = '<h3 class="green">See Detail tab for unit cell analysis.</h3>\n'
                #insert_text += '<h2>Check Detail tab for more information</h2>\n'
                HTMLfile.insert(44, insert_text)
                open('results.php', 'w').writelines(HTMLfile)
            except:
                self.logger.debug('Could not amend results.php.')
        except:
            self.logger.debug('**Could not complete PDBQuery**')
            return('FAILED') 
        return('SUCCESS')
    
    def run_analysis (self, cell, data, dir):
        """
        Runs xtriage and other analyses on the integrated data.
        """
        self.logger.debug('FastIntegration::run_analysis')
        self.logger.debug('Unit cell = %s' % cell)
        self.logger.debug('data = %s' % data)
        self.logger.debug('directory = %s' % dir)
        
        analysis_dir = os.path.join(dir, 'analysis')
        self.logger.debug('analysis_dir = %s' % analysis_dir)
        if os.path.isdir(analysis_dir) == False:
            os.system('mkdir %s' %analysis_dir)
        # Construct the input to send to PDBQuery.
        try:
            pdb_input = []
            pdb_dict = {}
            #pdb_dict['cell'] = cell
            pdb_dict['dir'] = analysis_dir
            pdb_dict['data'] = data
            pdb_dict['passback'] = True
            pdb_dict['control'] = self.controller_address
            pdb_dict['process_id'] = self.process_id
            pdb_input.append(pdb_dict)
            output0 = Queue()
            output1 = Queue()
            output2 = None

            self.logger.debug(pdb_input)
            T = AutoStats(pdb_input,output0, self.logger)
            T.join()
            # Minor Change
            #results = output0.get()
           
        except:
        #    pass
            self.logger.debug('run_analysis: Autostats failed!')
            return('FAILED')
        self.logger.debug('AUTOSTATS FINISHED')
        return('SUCCESS')
        
class DataHandler(threading.Thread, Communicate):
    """
    Handles the data that is received from the incoming clientsocket

    Creates a new process by instantiating a subclassed multiprocessing.Process
    instance which will act on the information which is passed to it upon
    instantiation.  That class will then send back results on the pipe
    which it is passed and Handler will send that up the clientsocket.
    """
    def __init__(self,input,verbose=True):
        if verbose:
            print 'DataHandler::__init__'

        threading.Thread.__init__(self)

        self.input = input
        self.verbose = verbose

        self.start()

    def run(self):
        # Create a pipe to allow interprocess communication.
        #parent_pipe,child_pipe = Pipe()
        # Instantiate the integration case
        tmp = FastIntegration(self.input, logger)
        # Print out what would be sent back to the RAPD caller via the pipe
        # self.logger.debug parent_pipe.recv()

if __name__ == '__main__':
    # Set up logging
    LOG_FILENAME = '/gpfs1/users/necat/David/process/temp2/fast_integration.log'
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=1000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler
                      )
    # Construct test input
    command = 'INTEGRATE'
    dirs = { 'images' : \
             '/gpfs3/users/cornell/Ealick_Aug10/images/Megan/p31_16/',
             'data_root_dir' : 'gpfs3/users/cornell/Ealick_Aug10/images/Megan/p31_16/',
             'work' : '/gpfs1/users/necat/David/process/temp2',
             'html' : '/gpfs1/users/necat/David/process/temp2',
             'user' : '/home/dneau/RAPD_testing/test'}
    image_data = {'osc_start' : '0.00',
                  'osc_range' : '1.00',
                  'size1' : '3072',
                  'size2' : '3072',
                  'binning' : '2x2',
                  'image_prefix' : 'p31_16',
                  'beamline' : '24_ID_C',
                  'ID' : 'p31_16',
                  'distance' : '325.00',
                  'x_beam' : '157.9',
                  'y_beam' : '156.0',
                  'pixel_size' : '0.10259',
                  'wavelength' : '0.97918',
                  'run_number' : '1',
                  'twotheta' : 0.0,
                  'ccd_image_saturation' : '65535',
                  'directory' : '/gpfs3/users/cornell/Ealick_Aug10/images/Megan/p31_16/',
                  'fullname' : \
                  '/gpfs3/users/cornell/Ealick_Aug10/images/Megan/p31_16_1_005.img'}
    run_data = {'distance' : '325.0',
                'image_prefix' : 'p31_16',
                'run_number' : 1,
                'start' : 1,
                'time' : 1.0,
                'directory' : '/gpfs3/users/cornell/Ealick_Aug10/images/Megan/p31_16/',
                'total' : 30}
    data = {'image_data' : image_data,
            'run_data' : run_data}
    settings = {'spacegroup' : 'P2221',
                'work_directory' : '/home/dneau/RAPD_testing/test/mosflm_test',
                'work_dir_override' : 'False',
                'anomalous' : 'False'}
    controller_address = ['127.0.0.1' , 50001]
    input = [command, dirs, data, settings, controller_address]
    # Call the handler.
    T = DataHandler(input, logger)

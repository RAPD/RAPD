"""
This file is part of RAPD

Copyright (C) 2010-2018, Cornell University
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

__created__ = "2010-09-22"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Production"

"""
rapd_test_case gives an example of wrapping a very simple activity so that 
one can see roughly how to structure and activity class as a new process
using the multiprocessing module and how to send the resulting data back
"""
import threading, multiprocessing, os, sys, subprocess
import time, shutil, fpformat, math, paramiko
import logging, logging.handlers
import psyco
from rapd_communicate import Communicate

class ShelxC(multiprocessing.Process,Communicate):
    """
    This is an example class for RAPD's data processing
    functions.
    
    __init__ is merely used to stow variables passed in,
    to initialize the process, and to start the process 
    
    run is used to orchestrate events
    """

    def __init__(self,input,logger=None,verbose=True):       
        """
        Initialize the ShelxC process
        
        input   is whatever is passed in
        pipe    is the communication back to the calling process
        verbose is to set the level of output
        logger  is logging for debugging.
        """
        psyco.full()
        logger.info('ShelxC.__init__')
     
        self.input                              = input
        self.verbose                            = verbose
        self.logger                             = logger
        
        #Setting up data input
        self.setup                              = self.input[1]
        self.header                             = self.input[2]        
        self.preferences                        = self.input[3]   
        self.data                               = self.input[4]     
        self.controller_address                 = self.input[-1]
        self.shelx_log                          = []
        self.shelx_results                      = {}
        self.cell                               = False
        self.sca                                = False
        
        multiprocessing.Process.__init__(self,name='ShelxC')        
        #starts the new process
        self.start()
        
    def run(self):
        """
        Convoluted path of modules to run.
        """
        self.logger.debug('ShelxC::run')
        self.preprocess()
        self.preprocessShelx()
        self.postprocess()
        
    def preprocess(self):
        """
        Things to do before the main process runs
        1. Change to the correct directory
        2. Print out the reference for labelit
        """       
        self.logger.debug('ShelxC::preprocess')
        #change directory to the one specified in the incoming dict
        self.working_dir = self.setup.get('work')
        try:     
            os.makedirs(self.working_dir)    
        except:
            self.logger.exception('Could not make working dir.')            
        os.chdir(self.working_dir)
        
    def preprocessShelx(self):
        """
        Create SHELX CDE input.
        """
        self.logger.debug('ShelxC::preprocessShelx')
        try:        
            self.space_group = self.preferences.get('spacegroup')
            self.sca = self.data.get('input_sca')
            sca_file = open(self.sca, 'r').readlines()[2]
            if self.space_group != 'None':
                input_sg = self.space_group
            else:
                input_sg = sca_file.split()[6].upper()        
            c = sca_file.split()[:6]        
            self.cell = c[0] + ' ' + c[1] + ' ' + c[2] + ' ' + c[3] + ' ' + c[4] + ' ' + c[5] 
            self.processShelxC(input_sg)
                             
        except:
            self.logger.debug('***ERROR in preprocessShelx**')
               
    def processShelxC(self, input):
        """
        Run SHELX CD for input SG.
        """
        self.logger.debug('ShelxC::processShelxCD')
        try: 
            command  = 'shelxc junk <<EOF\n'
            command += 'CELL ' + self.cell + '\n'
            command += 'SPAG ' + str(input) + '\n'
            command += 'SAD '  + self.sca + '\n'
            command += 'FIND 1\n'
            command += 'SFAC Se\n'
            command += 'NTRY 5\n'
            command += 'EOF\n'
            self.shelx_log.append(command + '\n')        
            output0 = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in output0.stdout:
                self.shelx_log.append(line)
                self.logger.debug(line.rstrip())            
            shelx = self.ParseOutputShelx(self.shelx_log)
            self.shelx_results = { 'Shelx results'     : shelx    }                    
            if self.shelx_results['Shelx results'] == None:
                self.shelx_results = { 'Shelx results'     : 'FAILED'}
            
        except:
            self.logger.exception('**Error in processShelxCD**')
            
    def postprocess(self):
        """
        Cleanup and send back results.
        """
        self.logger.debug('ShelxC::postprocess')
        try:
            #Cleanup files
            rm = 'rm -rf junk*'
            os.system(rm)
            #Send back results
            self.results = {} 
            if self.shelx_results: 
                self.results.update(self.shelx_results)
            if self.results:
                self.input.append(self.results)
            #print self.results
            self.sendBack2(self.input)
            #Say strategy is complete.
            self.logger.debug('-------------------------------------')
            self.logger.debug('RAPD ShelxC complete.')
            self.logger.debug('Total elapsed time: ' + str(os.times()[2]) + ' seconds')#Don't know if that is correct time?
            self.logger.debug('-------------------------------------')
            #Say strategy is complete.
            print '\n-------------------------------------'
            print 'RAPD ShelxC complete.'
            print 'Total elapsed time: ' + str(os.times()[2]) + ' seconds'#Don't know if that is correct time?
            print '-------------------------------------'
            os._exit(0)
                    
        except:
            self.logger.exception('**Could not send results to pipe.**')
        
    def ParseOutputShelx(self, input):
        """
        Parse Shelx CDE output.
        """
        self.logger.debug('ShelxC::ParseOutputShelx')
        try:
            temp   = []
            shelxc_res = []            
            for line in input:
                line.rstrip()
                temp.append(line)
                if line.startswith(' Resl.'):
                    shelxc_res.extend(line.split()[3::2])
                if line.startswith(' N(data)'):
                    shelxc_data = line.split()[1:]
                if line.startswith(' <I/sig>'):
                    shelxc_isig = line.split()[1:]
                if line.startswith(' %Complete'):
                    shelxc_comp = line.split()[1:]
                if line.startswith(' <d"/sig>'):
                    shelxc_dsig = line.split()[1:]
                if line.startswith(' SHEL '):
                    res = line.split()[2]            
            shelx = { 'shelxc_res'      : shelxc_res,
                      'shelxc_data'     : shelxc_data,
                      'shelxc_isig'     : shelxc_isig,
                      'shelxc_comp'     : shelxc_comp,
                      'shelxc_dsig'     : shelxc_dsig,
                      'shelxc_rescut'   : res            }        
            return((shelx))
         
        except:
            self.logger.exception('**Error in ParseOutputShelx**')
            return ((None))    

class TestHandler(threading.Thread):    
    """
    Handles the data that is received from the incoming clientsocket
    
    Creates a new process by instantiating a subclassed multiprocessing.Process
    instance which will act on the information which is passed to it upon
    instantiation. That class will then send back results on the pipe 
    which it is passed and Handler will send that up the clientsocket.
    """
    def __init__(self,input, logger=None,verbose=True):
        if verbose:
            logger.debug('TestHandler::__init__')
        
        threading.Thread.__init__(self)
               
        self.input   = input
        self.verbose = verbose
        self.logger  = logger
        
        self.start()

    def run(self):
        #create a pipe to allow interprocess communication
        parent_pipe,child_pipe = multiprocessing.Pipe()
        #instantiate the test case
        tmp = ShelxC(self.input,logger=self.logger,verbose=True)
        
if __name__ == '__main__':
    #tag for log file
    #tag = os.path.basename(command).replace('rapdtmp','').replace('.json','')
    #start logging
    LOG_FILENAME = '/home/schuerjp/Data_processing/Frank/Output/rapd_jon.log'
    # Set up a specific logger with our desired output level
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=100000, backupCount=5)
    #add a formatter
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('ShelxC.__init__')
    
    #construct test input    
    input = ["AUTOINDEX", 
             
    #This is an example input dict used for testing this script.             
    #Input dict file. If autoindexing from two images, just include a third dict section for the second image header. 
             
  {#"my_directory" : "/home/schuerjp/Data_processing/Frank/Output",
   "work": "/home/schuerjp/Data_processing/Frank/Output",
   }, 
   
   
  {"puck": "A", 
   "md2_aperture": "70", 
   "sample": "6", 
   "ring_mode": "324 Singlets/~1.1% Coupling/Cogging", 
   "osc_start": "180.000", 
   "wavelength": "0.9792", 
   "sql_date": "2009-08-19 17:09:15", 
   "image_prefix": "mg1_snap", 
   "size1": "3072", 
   "size2": "3072", 
   "detector_sn": "911", 
   "osc_range": "1.0", 
   "adc": "slow", 
   "beamline": "24_ID_C", 
   "axis": "phi", 
   "type": "unsigned_short", 
   "binning": "2x2", 
   "byte_order": "little_endian", 
   "phi": "0.000", 
   "dim": "2", 
   "time": "1.00",  
   "twotheta": "0.00", 
   "date": "Wed Aug 19 17:09:15 2009",
   "adsc_number": "1", 
   "ID": "mg1_snap_99_001_1", 
   "pixel_size": "0.10259", 
   "distance": "320.84", 
   "run_number": "99", 
   "transmission": "10",  
   "ring_cur": "102.3", 
   "unif_ped": "1500", 
   "beam_center_y": "165.6", 
   "beam_center_x": "157.0",
   "directory": "/gpfs3/users/cornell/Crane_Aug09/images/gabriela/mg",
   "fullname": "/home/schuerjp/Data_processing/Frank/Images/ablongcshrt_99_001.img",
   "header_bytes": " 1024", 
   "image_number": "001", 
   "ccd_image_saturation": "65535",
   
   
   #"mk3_phi":"0.0",
   #"mk3_kappa":"0.0",
   "STAC file1": '/home/schuerjp/Data_processing/Frank/Output/DNA_mosflm.inp',
   "STAC file2": '/home/schuerjp/Data_processing/Frank/Output/bestfile.par',
   "axis_align": 'long',   
   "flux":'1.6e11',
   "beam_size_x":"0.07",
   "beam_size_y":"0.03",
   "gauss_x":'0.03',
   "gauss_y":'0.01'
   

    }, 



     
{  "min_exposure_per": "1", 
   "crystal_size_x": "100", 
   "crystal_size_y": "100",
   "crystal_size_z": "100", 
   "db_password": "necatuser",
   "numberMolAU": "1",
   "user_dir_override": "False",
   "shape": "2.0",
   "work_directory": "None", 
   "work_dir_override": "False", 
   "cluster_host": "164.54.212.165", 
   "beam_size_y": "0.02", 
   "beam_size_x": "0.07", 
   "sample_type": "Protein", 
   "best_complexity": "none", 
   "numberResidues": "250", 
   "beamline": "C",
   "cluster_port": 50000,
   "aperture": "AUTO", 
   "db_name": "rapd1", 
   "user_directory": "None", 
   "susceptibility": "1.0", 
   "transmission": "AUTO",
   "anomalous": "False", 
   "index_hi_res": 0.0, 
   "db_user": "rapd1",
   "db_host": "penguin2.nec.aps.anl.gov",
   "max_exposure_tot": "None", 
   "spacegroup": "P3",
   "solvent_content": 0.55,
   "beam_flip": "False",
   "multiprocessing":"True",
   "x_beam": "0",
   "y_beam": "0",
   "aimed_res": 0.0,
   "strategy_type": 'best',
   "mosflm_rot": 0.0,
   "mosflm_seg":1,
   "a":0.0,
   "b":0.0,
   "c":0.0,
   "alpha": 0.0,
   "beta":0.0,
   "gamma":0.0
   },
   
{  "input_sca": '/home/schuerjp/Data_processing/Frank/Datasets/PK_lu_peak.sca',
   #"input_sca": '/home/schuerjp/Data_processing/Frank/Datasets/RAPD_QA17_b_2_scaled.sca',
   "HA_type":'None',
   "HA_number": '0'
   },
   ('127.0.0.1',50001)]
        
    #call the handler
    T = TestHandler(input, logger=logger)       
        
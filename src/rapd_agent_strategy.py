'''
__author__ = "Jon Schuermann, Frank Murphy"
__copyright__ = "Copyright 2009,2010,2011 Cornell University"
__credits__ = ["Jon Schuermann","Frank Murphy","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2009/07/14"
'''

import multiprocessing
import os
import sys
import subprocess
import time
import shutil
import numpy
import logging,logging.handlers

from rapd_communicate import Communicate
from rapd_agent_stac import RunStac
import rapd_agent_utils as Utils
import rapd_agent_parse as Parse
import rapd_agent_summary as Summary

class AutoindexingStrategy(multiprocessing.Process,Communicate):
    def __init__(self,input,logger=None):
        logger.info('AutoindexingStrategy.__init__')
        self.st = time.time()
        self.input                              = input
        self.logger                             = logger
        #Setting up data input
        self.setup                              = self.input[1]
        self.header                             = self.input[2]
        self.header2                            = False
        if self.input[3].get('distance'):
            self.header2                            = self.input[3]
            self.preferences                        = self.input[4]
        else:
            self.preferences                        = self.input[3]
        self.controller_address                 = self.input[-1]
        
        #For testing individual modules
        self.test                               = False
        #Removes junk files and directories at end.
        self.clean                              = True
        #Start peak picking with error iteration=1 settings. Does not run with self.multiproc==True.
        self.labelit_settings1                  = False
        #Rerun Labelit using the Labelit calculated beam center. (Not working)
        self.labelit_beamcenter                 = False
        #Number of Labelit iterations to run. (Default is 4) added 2 more to test new Labelit options
        self.iterations                         = 6
        
        #Sets settings so I can view the HTML output on my machine (not in the RAPD GUI), and does not send results to database. 
        #******BEAMLINE SPECIFIC*****
        if self.header.has_key('acc_time'):
            self.beamline_use                   = True
            self.test                           = False
        else:
            self.beamline_use                   = False
        #******BEAMLINE SPECIFIC*****
        
        #Set times for processes. 'False' to disable.
        if self.header2:
            self.labelit_timer                      = 120
        else:
            self.labelit_timer                      = 90         
        #Set timer for distl. 'False' will disable.
        if self.header2:
            self.distl_timer                        = 60
        else:
            self.distl_timer                        = 30
        #Set Best timer. 'False' disables.
        self.best_timer                         = 90        
        #Set timer for STAC. 'False' will disable.
        self.stac_timer                         = 120    
        
        #Turns on multiprocessing for everything
        #Turns on all iterations of Labelit running at once, sorts out highest symmetry solution, then continues...(much better!!)
        if self.preferences.has_key('multiprocessing'):
            if self.preferences.get('multiprocessing') == 'True':
                self.multiproc                          = True
            else:
                self.multiproc                          = False
        #Set for Eisenberg peptide work.
        if self.preferences.get('sample_type') == 'Peptide':
            self.peptide     = True
        else:
            self.peptide     = False
        if self.preferences.has_key('strategy_type'):
            self.strategy   =     self.preferences.get('strategy_type')
        else:
            self.strategy   =     'best'
        #Check to see if STAC should run. stac_strac is not that useful since user will have to align crystal and take snap to make sure alignment is good.
        if self.header.has_key('mk3_phi') and self.header.has_key('mk3_kappa'):
            self.stac        = True
            self.stac_strat  = False
        else:
            self.stac        = False
            self.stac_strat  = False        
        #Check to see if multi-crystal strategy is requested.
        if self.preferences.get('reference_data_id') in (None, 0):
            self.multicrystalstrat = False
        else:
            self.multicrystalstrat = True
            self.strategy          = 'mosflm'
        #This is where I place my overall folder settings.
        self.working_dir                        = False    
        self.labelit_dir                        = False                        
        #this is where I have chosen to place my results
        self.auto_summary                       = False
        self.labelit_input                      = False
        self.labelit_log                        = False
        self.labelit_log0                       = []
        self.labelit_log1                       = []
        self.labelit_log2                       = []
        self.labelit_log3                       = []    
        self.labelit_log4                       = []    
        self.labelit_log5                       = []
        #self.ll                                 = {}
        self.labelit_results                    = {}
        self.labelit_summary                    = False
        self.labelit_failed                     = False
        self.distl_log                          = False
        self.distl_results                      = False
        self.distl_results0                     = False
        self.distl_results1                     = False        
        self.distl_summary                      = False
        #self.dl                                 = []
        self.raddose_log                        = False
        self.raddose_results                    = False
        self.raddose_summary                    = False
        self.best_log                           = []
        self.best_results                       = False
        self.best_summary                       = False
        self.best1_summary                      = False
        self.best_summary_long                  = False
        self.best_anom_log                      = []
        self.best_anom_results                  = False
        self.best_anom_summary                  = False
        self.best1_anom_summary                 = False
        self.best_anom_summary_long             = False
        self.best_failed                        = False
        self.best_anom_failed                   = False
        #self.bl                                 = {}
        self.mosflm_strat_log                   = []
        self.mosflm_strat_anom_log              = []
        self.mosflm_strat_results               = {}
        self.mosflm_strat_anom_results          = {}
        self.mosflm_strat_summary               = False
        self.mosflm_strat1_summary              = False
        self.mosflm_strat_summary_long          = False
        self.mosflm_strat_anom_summary          = False
        self.mosflm_strat1_anom_summary         = False
        self.mosflm_strat_anom_summary_long     = False
        #self.ml                                 = {}
        #Labelit settings
        self.index_number                       = False
        self.spacegroup                         = 'None'
        self.min_spots                          = False
        self.ignore_user_cell                   = False
        self.ignore_user_SG                     = False
        self.blank_image                        = False
        self.pseudotrans                        = False
        self.min_good_spots                     = False
        self.twotheta                           = False        
        #Raddose settings
        self.dose                               = False
        self.exp_dose_lim                       = False
        self.volume                             = False
        self.calc_num_residues                  = False     
        #Mosflm settings
        self.prev_sg                            = False      
        #extra features for BEST
        self.high_dose                          = False
        self.crystal_life                       = None
        self.iso_B                              = False
        #dicts for running the Queues
        self.labelit_jobs                       = {}
        self.best_jobs                          = {}
        self.mosflm_jobs                        = {}        
        #Settings for all programs
        self.beamline             = self.header.get('beamline')
        self.sample_type          = self.preferences.get('sample_type')
        self.time                 = str(self.header.get('time'))
        self.wavelength           = str(self.header.get('wavelength'))
        self.transmission         = float(self.header.get('transmission'))
        self.aperture             = str(self.header.get('md2_aperture'))    
        self.spacegroup           = self.preferences.get('spacegroup')
        self.flux                 = str(self.header.get('flux'))
        self.solvent_content      = str(self.preferences.get('solvent_content'))
        
        multiprocessing.Process.__init__(self,name='AutoindexingStrategy')
        self.start()
        
    def run(self):
        """
        Convoluted path of modules to run.
        """
        self.logger.debug('AutoindexingStrategy::run')
        self.preprocess()
        
        if self.stac:
            self.processSTAC()
        else:
            
            #Make the labelit.png image
            if self.test == False:
                self.makeImages(0)
            #Make the dataset_prefernces.py file
            self.preprocessLabelit()
            #Will only run if self.multiproc==False and option turned on from above. Looks for more spots in DISTL.
            if self.labelit_settings1:
                Utils.foldersLabelit(self,1)
                self.labelit_jobs[self.processLabelit(1)] = 1
            else:
                #Create the separate folders for the labelit runs, modify the dataset_preferences.py file, and launch for each iteration.
                Utils.foldersLabelit(self)
                self.labelit_jobs[self.processLabelit().keys()[0]] = 0
                #If self.multiproc==True runs all labelits at the same time.
                if self.multiproc:
                    for i in range(1,self.iterations):
                        job = self.errorLabelit(i)
                        self.labelit_jobs[job.keys()[0]] = i
            #Wait for the jobs to complete. Sends to postprocessLabelit as they finish.
            self.Queue('labelit')
            #Sorts labelit results by highest symmetry.
            if self.multiproc:
                self.labelitSort()
            #Puts logs from each labelit run together into a single log for the GUI.
            self.LabelitLog()
            #Rename the Mosflm files for STAC to run later if initiated by user.
            self.preprocessSTAC()
            #Start distl.signal_strength for the correct labelit iteration
            self.processDistl()
            if self.multiproc == False:
                self.postprocessDistl()
            #Run Raddose
            self.preprocessRaddose()
            self.processRaddose()
            
            #Calculate strategy
            if self.strategy == 'mosflm':
                self.mosflm_jobs.update(self.processMosflm(False))
                if self.multiproc == False:
                    self.Queue('mosflm')
                self.mosflm_jobs.update(self.processMosflm(True))
                self.Queue('mosflm')
            else:
                self.best_jobs.update(self.processBest(0,False))
                if self.multiproc == False:
                    self.Queue('best')
                self.best_jobs.update(self.processBest(0,True))
                self.Queue('best')
            #Get the distl results
            if self.multiproc:
                self.postprocessDistl()
            #Make PHP files for GUI, passback results, and cleanup.
            self.postprocess()                                                   
            
    def preprocess(self):
        """
        Setup the working dir in the RAM and save the dir where the results will go at the end.
        """       
        self.logger.debug('AutoindexingStrategy::preprocess')
        self.dest_dir = self.setup.get('work')
        if self.test:
            self.working_dir = self.dest_dir
        else:
            self.working_dir = '/dev/shm/'+self.dest_dir[1:]
        if os.path.exists(self.working_dir) == False:
            os.makedirs(self.working_dir)
        os.chdir(self.working_dir)
        #print out recognition of the program being used
        self.PrintInfo()
        
    def preprocessLabelit(self):
        """
        Setup extra parameters for Labelit if turned on. Will always set beam center from image header. 
        Creates dataset_preferences.py file for editing later in the Labelit error iterations if needed.
        """
        self.logger.debug('AutoindexingStrategy::preprocessLabelit')
        try:
            index_hi_res   = str(self.preferences.get('index_hi_res'))
            twotheta       = str(self.header.get('twotheta'))
            distance       = self.header.get('distance')
            flip           = self.preferences.get('beam_flip')  
            #Always specify the beam center.
            if self.preferences.has_key('x_beam'):
                if str(self.preferences.get('x_beam')) != '0':
                    x_beam         = str(self.preferences.get('x_beam'))
                else:
                    x_beam         = str(self.header.get('beam_center_x'))
            if self.preferences.has_key('y_beam'):
                if str(self.preferences.get('y_beam')) != '0':
                    y_beam         = str(self.preferences.get('y_beam'))
                else:
                    y_beam         = str(self.header.get('beam_center_y'))              
            preferences    = open('dataset_preferences.py','w')
            preferences.write('#####Base Labelit settings#####\n')           
            preferences.write('best_support=True\n')            
            #Set Mosflm RMSD tolerance larger
            preferences.write('mosflm_rmsd_tolerance=4.0\n')
            #If user wants to change the res limit for autoindexing.
            if index_hi_res != '0.0':
                preferences.write('distl_highres_limit='+index_hi_res+'\n')            
            #If Malcolm flips the beam center in the image header...
            if flip == 'True':
                preferences.write('autoindex_override_beam=('+y_beam+','+x_beam+')\n')
            else:
                preferences.write('autoindex_override_beam=('+x_beam+','+y_beam+')\n')            
            #If two-theta is being used, specify the angle and distance correctly.
            if twotheta.startswith('0'):
                preferences.write('beam_search_scope=0.2\n')
            else:
                self.twotheta = True                        
                preferences.write('beam_search_scope=0.5\n')
                preferences.write('autoindex_override_twotheta='+twotheta+'\n')
                preferences.write('autoindex_override_distance='+distance+'\n')
            #Only place where self.labelit_settings1 are set if True. Speeds up for weak crystals since iteration0 is not used.
            if self.labelit_settings1:
                preferences.write('distl.minimum_spot_area=7\n')
                #preferences.write('distl_aggressive = {"passthru_arguments":"-s3 7"}\n')
                #preferences.write('beam_search_scope=0.5\n')
                #preferences.write('distl_profile_bumpiness = 3\n')
            preferences.close()  
         
        except:
            self.logger.exception('**ERROR in preprocessLabelit**')
               
    def preprocessRaddose(self):
        """
        Create the raddose.com file which will run in processRaddose. Several beamline specific entries for flux and
        aperture size passed in from rapd_agent_site.py
        """
        self.logger.debug('AutoindexingStrategy::preprocessRaddose')
        try:
            #Get unit cell
            cell                      = Utils.getLabelitCell(self)
            #self.volume is calculated from first raddose run.
            if self.volume:
                num_mol_UC           = '1'
            else:
                num_mol_UC           = False
            #Adding these typically does not change the Best strategy much, if it at all.
            patm                 = False
            satm                 = False             
            if self.sample_type == 'Ribosome':
                crystal_size_x = '1'
                crystal_size_y = '0.5'
                crystal_size_z = '0.5'
            else:   
                #crystal dimensions (default 0.1 x 0.1 x 0.1 from rapd_agent_site.py)
                crystal_size_x = str(float(self.preferences.get('crystal_size_x'))/1000.0)
                crystal_size_y = str(float(self.preferences.get('crystal_size_y'))/1000.0)
                crystal_size_z = str(float(self.preferences.get('crystal_size_z'))/1000.0)
            if self.header.has_key('flux'):                
                beam_size_x = str(self.header.get('beam_size_x'))
                beam_size_y = str(self.header.get('beam_size_y')) 
                gauss_x     = str(self.header.get('gauss_x'))
                gauss_y     = str(self.header.get('gauss_y'))                           
            #**Beamline specific failsafe if aperture size is not sent correctly from MD2.
            if self.aperture == '0' or '-1':
                if self.beamline == '24_ID_C':
                    self.aperture = '70' 
                else:
                    self.aperture = '50'                    
            #Get max crystal size to calculate the shape.(Currently disabled in Best)
            max_size      = float(max(crystal_size_x,crystal_size_y,crystal_size_z))
            aperture      = float(self.aperture)/1000.0
            self.shape    = max_size/aperture
            #put together the command script for Raddose
            raddose = open('raddose.com', 'w+')
            setup = 'raddose << EOF\n'
            if beam_size_x and beam_size_y:
                setup += 'BEAM ' + beam_size_x+' '+beam_size_y+'\n'
            #Full-width-half-max of the beam
            setup += 'GAUSS '+gauss_x+' '+gauss_y+'\n'
            setup += 'IMAGES 1\n'
            if self.flux:
                setup += 'PHOSEC '+self.flux+'\n'
            else:
                setup += 'PHOSEC 3E10\n'
            if cell:
                setup += 'CELL '+cell+'\n'
            else:
                self.logger.debug('Could not get unit cell from bestfile.par')
            #Set default solvent content based on sample type. User can override.
            if self.solvent_content == '0.55':
                if self.sample_type == 'Protein':
                    setup += 'SOLVENT 0.55\n'
                else:
                    setup += 'SOLVENT 0.64\n'
            else:
                setup += 'SOLVENT '+str(self.solvent_content)+'\n'
            #Sets crystal dimensions. Input from dict (0.1 x 0.1 x 0.1 mm), but user can override.
            if crystal_size_x and crystal_size_y and crystal_size_z:
                setup += 'CRYSTAL '+crystal_size_x+' '+crystal_size_y+' '+crystal_size_z+'\n'
            if self.wavelength:
                setup += 'WAVELENGTH '+self.wavelength+'\n'
            if self.time:
                setup += 'EXPOSURE '+self.time+'\n'
            #Calculates number of residues in UC based on volume taken from first Raddose run.
            if self.sample_type and self.calc_num_residues:
                if self.sample_type == 'Protein':
                    setup += 'NRES '+str(self.calc_num_residues)+'\n'
                elif self.sample_type == 'DNA':
                    setup += 'NDNA '+str(self.calc_num_residues)+'\n'
                else:
                    setup += 'NRNA '+str(self.calc_num_residues)+'\n'
            #Used in the number_of_residues module.
            if num_mol_UC:
                setup += 'NMON '+num_mol_UC+'\n'
            if patm:
                setup += 'PATM '+patm+'\n'
            if satm:
                setup += 'SATM '+satm+'\n'
            setup += 'END\nEOF\n'
            raddose.writelines(setup)
            raddose.close()
            
        except:
            self.logger.exception('**ERROR in preprocessRaddose**')
                
    def preprocessSTAC(self):
        """
        Copy files for future STAC run.
        """
        self.logger.debug('AutoindexingStrategy::preprocessSTAC')  
        try:
            if self.labelit_results['Labelit results'] != 'FAILED':
                self.index_number = self.labelit_results.get('Labelit results').get('mosflm_index')
            copy = 'cp '+self.index_number+' DNA_mosflm.inp'
            os.system(copy)
            #Utils.fixBestfile(self)
        except:
            self.logger.exception('**Error in preprocessSTAC**')
    
    def processLabelit(self,iteration=0,input=False):
        """
        Construct the labelit command and run. Passes back dict with PID:iteration.
        """
        self.logger.debug('AutoindexingStrategy::processLabelit')   
        try:
            labelit_input = []            
            #If user specifies unit cell or space group it is input here.
            a = False
            b = False
            c = False
            alpha = False
            beta  = False
            gamma = False           
            if self.preferences.get('a') != 0.0:
                a = str(self.preferences.get('a'))
            if self.preferences.get('b') != 0.0:
                b = str(self.preferences.get('b'))
            if self.preferences.get('c') != 0.0:
                c = str(self.preferences.get('c'))
            if self.preferences.get('alpha') != 0.0:
                alpha = str(self.preferences.get('alpha'))
            if self.preferences.get('beta') != 0.0:
                beta = str(self.preferences.get('beta'))
            if self.preferences.get('gamma') != 0.0:
                gamma = str(self.preferences.get('gamma'))                                            
            #put together the command for labelit.index            
            command = 'labelit.index '                         
            #If first labelit run errors because not happy with user specified cell or SG then ignore user input in the rerun.
            if self.ignore_user_cell == False:
                if a and b and c:
                    if alpha and beta and gamma:
                        command += 'known_cell='+a+','+b+','+c+','+alpha+','+beta+','+gamma+' '
                    else:
                        command += 'known_cell='+a+','+b+','+c+',90,90,90 '            
            if self.ignore_user_SG == False:
                if self.spacegroup != 'None':
                    command += 'known_symmetry='+self.spacegroup+' '                                
            #For peptide crystals
            if self.peptide:
                command += 'codecamp.maxcell=80 codecamp.minimum_spot_count=10 '            
            #If multiple cell options possible according to Labelit, the correct one is passed back in this way in the rerun.
            #input from errorLabelitFixCell
            if input:
                command += input+' '
            command += self.header.get('fullname')+' '
            #If pair of images
            if self.header2:
                command += self.header2.get('fullname')+' '
            #run Labelit and capture the log file
            self.logger.debug(command)
            eval('self.labelit_log'+str(iteration)).append(command+'\n')
            labelit_output = {}
            if self.test == False:
                job = multiprocessing.Queue()
                #self.ll[str(iteration)] = multiprocessing.Queue()
                #dict = {'input':command,'output':job,'output2':self.ll[str(iteration)],'iteration':iteration,'logger':self.logger}
                dict = {'input':command,'output':job,'iteration':iteration,'logger':self.logger}
                run = multiprocessing.Process(target=LabelitAction,kwargs=dict).start()
                labelit_output[job.get()] = iteration
            else:
                labelit_output['junk'+str(iteration)] = iteration
            return(labelit_output)
               
        except:
            self.logger.exception('**Error in processLabelit**')
            
    def processDistl(self):
        """
        Setup Distl for multiprocessing if enabled.
        """
        self.logger.debug('AutoindexingStrategy::processDistl')
        try:
            distl_input = []
            distl_input.append(self.header.get('fullname'))                
            self.distl_output = multiprocessing.Queue()
            #For second image used in autoindexing (if given)
            if self.header2:
                distl_input.append(self.header2.get('fullname'))
            dict = {'input':distl_input,'output':self.distl_output,'logger':self.logger}
            run = multiprocessing.Process(target=DistlAction,kwargs=dict).start()
        except:
            self.logger.exception('**Error in ProcessDistl.**')
            
    def processRaddose(self):
        """ 
        Run Raddose twice and capture the log file. The first time capture cell volume to calculate number of residues 
        in the cell based on % solvent content. The second run gives the meaningful statistics. Probably an easier way,
        but it runs so fast it doesn't matter.
        """
        self.logger.debug('AutoindexingStrategy::processRaddose')
        self.raddose_log = []
        try:
            #Prints this if final Raddose is run.
            if self.calc_num_residues:
                self.raddose_log.append('The calculated number of residues in the UNIT CELL are '+str(self.calc_num_residues)+',\n')
                self.raddose_log.append('according to a solvent content of '+str(self.solvent_content)+'\n\n')                                
                self.raddose_log.append('Calculated flux according to transmission of '+str(self.transmission)+'% and\n')
                self.raddose_log.append('aperture size of '+str(self.aperture)+' microns.\n\n')
                self.raddose_log.append('Set flux to '+str(self.flux)+' photons per second.\n\n')                                  
                self.logger.debug('These Raddose results should be correct.')
                self.logger.debug('The calculated number of residues in the UNIT CELL are '+str(self.calc_num_residues))
                self.logger.debug('according to a solvent content of '+str(self.solvent_content))
                runbefore = True
            else:                
                runbefore = False
            execute = 'tcsh raddose.com'
            output = subprocess.Popen(execute,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)                                
            self.raddose_log.append(execute + '\n')
            for line in output.stdout:
                self.raddose_log.append(line)
                #self.logger.debug(line.rstrip())
        except:
            self.logger.exception('**ERROR in processRaddose**')
        raddose = Parse.ParseOutputRaddose(self,self.raddose_log)
        self.raddose_results = { 'Raddose results' : raddose }        
        if self.raddose_results['Raddose results'] == None:
            self.logger.debug('Raddose failed')
            self.raddose_results = { 'Raddose results' : 'FAILED'}
        #If first run, then calculate number of residues from volume and rerun.
        if runbefore == False:
            self.calc_num_residues = Utils.calcTotResNumber(self,self.volume)
            if self.calc_num_residues != None:
                self.preprocessRaddose()                        
                self.processRaddose() 
    
    def processBest(self,iteration=0,anom=False):
        """
        Construct the Best command and run. Passes back dict with PID:anom.
        """
        self.logger.debug('AutoindexingStrategy::processBest')
        try:
            if self.best_log == False:
                self.best_log = []
            log = []            
            jobs = {}
            #Change SG if user selected higher Laue group.
            if self.ignore_user_SG == False and anom == False:
                if self.spacegroup != 'None':
                    Utils.fixBestSG(self)
            image_number = []
            image_number.append(os.path.basename(self.header.get('fullname'))[-7:-4])
            #If pair of images
            if self.header2:
                image_number.append(os.path.basename(self.header2.get('fullname'))[-7:-4])
            susceptibility          = str(self.preferences.get('susceptibility'))
            best_complexity         = str(self.preferences.get('best_complexity'))
            max_exposure_tot        = 'None'
            min_exposure_per        = str(self.preferences.get('min_exposure_per'))
            bin                     = str(self.header.get('binning'))
            osc_range               = str(self.header.get('osc_range'))                
            if self.preferences.has_key('shape'):
                shape                   = str(self.preferences.get('shape'))
            else:
                shape = '2'
            """
            if self.shape == False:
                self.shape = 2.0                    
            """
            if self.preferences.get('aimed_res') != 0.0:        
                aimed_res               = str(self.preferences.get('aimed_res'))
            else:
                aimed_res = False
            #Tell Best if two-theta is being used.
            if int(float(self.header.get('twotheta'))) != 0:
                Utils.fixBestfile(self)
            #if Raddose failed, here are the defaults.
            if self.raddose_results:
                if self.raddose_results.get('Raddose results') != 'FAILED':
                    self.dose                = self.raddose_results.get('Raddose results').get('dose per image')
                    self.exp_dose_lim        = self.raddose_results.get('Raddose results').get('exp dose limit')
                else:
                    self.dose                = 100000.0
                    self.exp_dose_lim        = 300
            else:
                self.dose                = 100000.0
                self.exp_dose_lim        = 300            
            #If dose is so high less that one image can be collected to dose limit, then set the number of images to 
            #1 instead of 0.
            self.crystal_life = str(int(float(self.exp_dose_lim) / float(self.time)))
            if self.crystal_life == '0':
                self.crystal_life = '1'                                         
            #If dose is too high, warns user and sets to reasonable amount and reruns Best but give warning.
            if self.dose > 500000:
                self.dose                = 500000  
                self.exp_dose_lim        = 100
                self.high_dose           = True                  
            if self.high_dose:
                if iteration == 1:
                    self.dose                = 100000.0
                    self.exp_dose_lim        = 300
                if iteration == 2:
                    self.dose                = 100000.0
                    self.exp_dose_lim        = False
                if iteration == 3:
                    self.dose                = False
                    self.exp_dose_lim        = False
            #put together the command for labelit.index
            command = 'best -f q315'
            if bin == '2x2':
                command += '-2x'
            if self.time:                
                if self.high_dose:
                    command += ' -t 1.0'
                else:
                    command += ' -t '+self.time
            command += ' -e '+best_complexity
            command += ' -sh '+shape
            command += ' -su '+susceptibility
            """    
            if max_exposure_tot != 'None':
                command += ' -T ' + max_exposure_tot    
            """                
            if aimed_res:
                command += ' -r '+aimed_res            
            if self.iso_B:
                command += ' -w 1.0 '
            """
            if self.min_oscillation:
                command += ' -w ' + self.min_oscillation  
            """
            #For Best 3.4.4
            command += ' -Trans '+str(self.transmission)            
            command += ' -M '+min_exposure_per+' -DIS_MAX 1200 -DIS_MIN 125'
            
            #if self.sample_type != 'Ribosome':
            if self.dose:
                command += ' -GpS '+str(self.dose)
            if self.exp_dose_lim:
                command += ' -T '+str(self.exp_dose_lim)
            else:
                command += ' -w '+osc_range
            if anom:
                command += ' -a -o bestanom.plt'
            else:
                command += ' -o best.plt'
            command += ' -mos bestfile.dat bestfile.par '+str(self.index_number)+'_'+image_number[0]+'.hkl '
            if self.header2:
                command += str(self.index_number)+'_'+image_number[1]+'.hkl'
            self.logger.debug(command)
            if self.test:
                if anom:
                    jobs['junkanom'+str(iteration)] = 'anom'+str(iteration)
                else:
                    jobs['junkreg'+str(iteration)] = 'reg'+str(iteration)
            else:
                best_output = multiprocessing.Queue()
                dict = {'input':command,'output':best_output,'anomalous':anom,'logger':self.logger}
                run = multiprocessing.Process(target=BestAction,kwargs=dict).start()
                if anom:
                    jobs[best_output.get()] = 'anom'+str(iteration)
                else:
                    jobs[best_output.get()] = 'reg'+str(iteration)
            return(jobs)
        
        except:
            self.logger.exception('**Error in processBest**')
        
    def processMosflm(self,anom=False):
        """
        Creates Mosflm executable for running strategy and run. Passes back dict with PID:logfile.
        """
        self.logger.debug('AutoindexingStrategy::processMosflm')
        try:
            #Opens file from Labelit/Mosflm autoindexing and edit it to run a strategy.
            mosflm_rot = str(self.preferences.get('mosflm_rot'))
            mosflm_seg = str(self.preferences.get('mosflm_seg'))
            if self.multicrystalstrat:
                ref_data = self.preferences.get('reference_data')
            else:
                ref_data = False
            mat = []
            start = []
            end = []
            sg = []
            count = 1
            job = {}
            if ref_data:
                for line in ref_data:       
                    mat.append(line[0])
                    start.append(line[1])
                    end.append(line[2])
                    sg.append(line[4])
                    count += 1            
            if self.ignore_user_SG == False:
                if self.spacegroup != 'None':
                    Utils.fixMosflmSG(self)
                else:
                    if ref_data:
                        self.spacegroup = sg[0]
                        Utils.fixMosflmSG(self)
                        self.prev_sg = True                    
            temp = []
            if anom:                
                file      = str(self.index_number)+'_strat_anom'
            else:
                file      = str(self.index_number)+'_strat'                        
            log = file+'.out'
            copy  = 'cp '+str(self.index_number)+' '+file               
            self.logger.debug(copy)
            os.system(copy)                     
            orig = open(file,'r')
            new_line = 'SCANNER ADSC\n'
            if ref_data:
                for x in range(len(mat)):
                    new_line += 'MATRIX '+str(mat[x])+'\n'
                    new_line += 'STRATEGY start '+str(start[x])+' end '+str(end[x])+' PARTS '+str(count)+'\n'
                    new_line += 'GO\n'
                new_line += 'MATRIX '+str(self.index_number)+'.mat\n'
            if mosflm_rot == '0.0':
                if anom:                    
                    new_line += 'STRATEGY AUTO SPEEDUP 10 ANOMALOUS\n'
                else:
                    new_line += 'STRATEGY AUTO SPEEDUP 10\n'
            elif mosflm_seg != '1': 
                if anom:
                    new_line += 'STRATEGY AUTO ROTATE '+str(mosflm_rot)+' SEGMENTS '+str(mosflm_seg)+' SPEEDUP 10 ANOMALOUS\n'
                else:
                    new_line += 'STRATEGY AUTO ROTATE '+str(mosflm_rot)+' SEGMENTS '+str(mosflm_seg)+' SPEEDUP 10\n'           
            else:                
                if anom:
                    new_line += 'STRATEGY AUTO ROTATE '+str(mosflm_rot)+' SPEEDUP 10 ANOMALOUS\n'
                else:
                    new_line += 'STRATEGY AUTO ROTATE '+str(mosflm_rot)+' SPEEDUP 10\n'
            new_line += 'GO\n'
            new_line += 'STATS\n'                
            for line in orig:
                temp.append(line)            
                if line.startswith('ipmosflm COORDS'):
                    junk2 = temp.index(line)
                    out = self.index_number + '.out'
                    if anom:
                        new2 = os.path.basename(out).replace('.out','_strat_anom.out')
                    else:
                        new2 = os.path.basename(out).replace('.out','_strat.out')
                    newline = line.replace(out,new2)
                    temp.remove(line)                                        
                if line.startswith('BEST OFF'):
                    junk = temp.index(line)                
            temp.insert(junk2, newline) 
            temp.insert(junk, new_line)        
            orig.close()
            new = open(file,'w')
            new.writelines(temp)
            new.close()
            pid  = multiprocessing.Queue()
            dict = {'input':file,'output':pid,'logger':self.logger}
            run = multiprocessing.Process(target=MosflmAction,kwargs=dict).start()
            job[pid.get()] = log
            return(job)
        
        except:
            self.logger.exception('**Error in processMosflm**')
                             
    def processSTAC(self):
        """
        Run STAC using rapd_agent_stac.py
        """
        self.logger.debug('AutoindexingStrategy::processSTAC')
        try:
            params = {}
            params['stac_timer'] = self.stac_timer
            params['test'] = self.test
            params['gui'] = self.beamline_use
            params['dir'] = self.dest_dir
            params['clean'] = self.clean
            args1 = {}
            args1['input']   = self.input
            args1['params']  = params
            args1['logger']  = self.logger
            self.STAC = multiprocessing.Process(target=RunStac,kwargs=args1).start()
        
        except:
            self.logger.exception('**ERROR in processSTAC**')
    
    def postprocessLabelit(self,iteration=0,run_before=False,blank=False):
        """        
        Sends Labelit log for parsing and error checking for rerunning Labelit. Save output dicts.
        """        
        self.logger.debug('AutoindexingStrategy::postprocessLabelit') 
        log = []             
        try:
            Utils.foldersLabelit(self,iteration)
            labelit_failed = False
            if blank == False:
                #input = self.ll[str(iteration)].get()
                input = open('labelit.log','r').readlines()
                eval('self.labelit_log'+str(iteration)).append('\n\n')
                for line in input:
                    eval('self.labelit_log'+str(iteration)).append(line)
                    log.append(line)
                data = Parse.ParseOutputLabelit(self,log,iteration)
                if self.multiproc:
                    self.labelit_results[str(iteration)] = { 'Labelit results'  : data    }
                else:
                    self.labelit_results = { 'Labelit results'  : data     }
            else:
                error = 'Not enough spots for autoindexing.'
                self.logger.debug(error)               
                eval('self.labelit_log'+str(iteration)).append(error+'\n')
                if self.multiproc == False:
                    labelit_failed = True
                else:
                    return(None)
        except:
            self.logger.exception('**ERROR in postprocessLabelit**')
        
        #Do error checking and send to correct place according to iteration.
        #If Labelit results are OK, then...
        if type(data) == dict:
            if self.test == False:
                if self.multiproc == False:
                    self.makeImages(1)
        #If there is an error in Labelit, then...
        elif type(data) == tuple:
            if data[0] == 'min spots':     
                error = 'Labelit did not have enough spots to find a solution.'
                self.errorLabelitPost(iteration,error,run_before)
                if self.multiproc:                   
                    if run_before == False:
                        return (self.errorLabelitMin(iteration,data[1]))
                else:
                    if iteration >= 3:
                        labelit_failed = True
                    else:
                        return (self.errorLabelit(iteration))
            if data[0] == 'fix_cell':
                error = 'Labelit had multiple choices for user SG and failed.'
                self.errorLabelitPost(iteration,error,run_before)
                if self.multiproc:                   
                    if run_before == False:
                        return(self.errorLabelitFixCell(iteration,data[1],data[2]))
                else:
                    if iteration >= 3:
                        labelit_failed = True
                    else:
                        return (self.errorLabelitCellSG(iteration))
        else:
            out = {'bad input':{'error':'Labelit did not like your input unit cell dimensions or SG.','run':'self.errorLabelitCellSG(iteration)'},
                   'bumpiness':{'error':'Labelit settings need to be adjusted.','run':'self.errorLabelitBump(iteration)'},
                   'mosflm error':{'error':'Mosflm could not integrate your image.','run':'self.errorLabelitMosflm(iteration)'},
                   'min good spots':{'error':'Labelit did not have enough spots to find a solution','run':'self.errorLabelitGoodSpots(iteration)'}}
            if out.has_key(data):
                self.errorLabelitPost(iteration,out[data].get('error'),run_before)
                if self.multiproc:
                    if run_before == False:
                        return(eval(out[data].get('run')))
                else:
                    if iteration >= 3:
                        labelit_failed = True
                    else:
                        return(eval(out[data].get('run')))
            else:
                if data == None:
                    error = 'Labelit failed to find solution.'
                    self.errorLabelitPost(iteration,error,run_before)
                    if self.multiproc == False:
                        if iteration >= 3:
                            self.labelit_results = { 'Labelit results'  : 'FAILED'}
                            self.labelit_failed = True   
                            self.LabelitLog()
                            self.postprocess()             
                        else:
                            return (self.errorLabelit(iteration))
                #**Beamline specific**
                if data == 'fix labelit':           
                    #Not working very well. Only problem if SBGrid updates Labelit. 
                    #Problem since Malcolm writes 'twothetadistance' to image header and Labelit thinks it is the detector distance.
                    #error = 'Labelit adsc.py file not working. Will fix now.'
                    #self.logger.debug(error)
                    #eval('self.labelit_log'+str(iteration)).append(error)
                    #Utils.fixLabelit(self)
                    #return (self.processLabelit(iteration))
                    error = 'Distance is not getting read correctly from the image header.'
                    if self.multiproc:
                        self.errorLabelitPost(iteration,error,True)
                    else:
                        self.errorLabelitPost(3,error)
                        labelit_failed = True
                #If pair images are not a pair from the same crystal.
                if data == 'no pair':    
                    error = 'Images are not a pair.'
                    if self.multiproc:
                        self.logger.debug(error)
                        eval('self.labelit_log'+str(iteration)).append(error+'\n')
                    else:
                        self.logger.debug(error)
                        self.labelit_results = { 'Labelit results'  : 'FAILED'}
                        self.labelit_failed = True
                        self.LabelitLog()
                        self.postprocess()
                #Only active when self.labelit_cluster = False
                if data ==  'no index':
                    error = 'No solutions found in Labelit.'
                    self.errorLabelitPost(iteration,error,run_before)
                    if iteration >= 3:
                        labelit_failed = True
                    else:
                        return (self.errorLabelit(iteration))
        
        #If labelit failed finish up jobs with these commands.
        if labelit_failed:
            self.labelit_failed = True
            self.labelit_results = { 'Labelit results'  : 'FAILED'} 
            self.LabelitLog()
            if os.path.exists('DISTL_pickle'):
                self.makeImages(2)
            self.processDistl()
            self.postprocessDistl()
            self.postprocess()
        
    def postprocessDistl(self):
        """
        Send Distl log to parsing and make sure it didn't fail. Save output dict.
        """
        self.logger.debug('AutoindexingStrategy::postprocessDistl')
        if self.distl_log == False:
            self.distl_log = []        
        try:                         
            timer = 0
            pids = []
            time_out = False
            pids.append(self.distl_output.get())
            if self.header2:
                pids.append(self.distl_output.get())
            while len(pids) != 0:
                for pid in pids:
                    if Utils.stillRunning(self,pid):
                        time.sleep(1)
                        timer += 1
                        print 'Waiting for Distl to finish '+str(timer)+' seconds'
                        if self.distl_timer:
                            if timer >= self.distl_timer:
                                Utils.killChildren(self,pid)
                                pids.remove(pid)
                                print 'Distl timed out.'
                                self.logger.debug('Distl timed out.')
                                self.distl_log.append('Distl timed out\n')
                    else:
                        pids.remove(pid)
            readlog0 = open('distl0.txt','r').readlines()
            for line in readlog0:
                self.distl_log.append(line)
            if self.header2:
                readlog1 = open('distl1.txt','r').readlines()
                for line in readlog1:
                    self.distl_log.append(line)
        except:
            self.logger.exception('**Error in postprocessDistl.**')
        
        distl0 = Parse.ParseOutputDistl(self,readlog0)
        if distl0 == None:
            self.distl_results0 = { 'Distl results'     : 'FAILED'}
        else:
            self.distl_results0 = { 'Distl results'     : distl0    }        
        if self.header2:
            distl1 = Parse.ParseOutputDistl(self,readlog1)
            if distl1 == None:
                self.distl_results1 = { 'Distl results'     : 'FAILED'}
            else:                
                self.distl_results1 = { 'Distl results'     : distl1    }
            Utils.distlComb(self)
        else:
            self.distl_results = self.distl_results0
            
    def postprocessBest(self,input):
        """
        Send Best log to parsing and save output dict. Error check the results and rerun if neccessary.
        """
        self.logger.debug('AutoindexingStrategy::postprocessBest')
        try:
            log = []
            best_failed = False
            if self.test:
                Utils.foldersLabelit(self,3)
            if input.startswith('anom'):
                #file = self.bl['True'].get()
                file = open('best_anom.txt','r').readlines()
                anom = True
            else:
                #file = self.bl['False'].get()
                file = open('best.txt','r').readlines()
                anom = False
            iteration = int(input[-1])
            for line in file:
                log.append(line)
                if anom:
                    self.best_anom_log.append(line)
                else:                
                    self.best_log.append(line)
           
        except:
            self.logger.exception('**Error in postprocessBest.**')
                                    
        data = Parse.ParseOutputBest(self,log,anom)
        if self.labelit_results['Labelit results'] != 'FAILED':
            #Best error checking. Most errors caused by B-factor calculation problem. 
            #If no errors...
            if type(data) == dict:
                if anom:
                    self.best_anom_results = { 'Best ANOM results' : data }
                else:
                    self.best_results = { 'Best results' : data }
            else:
                #Possible error returns from parsing.
                if data == 'dosage too high':
                    self.high_dose = True
                out = {'None'           : 'No Best Strategy.',
                       'neg B'          : 'Adjusting resolution',
                       'isotropic B'    : 'Isotropic B detected',
                       'dosage too high': 'Dosage too high.'}                
                if out.has_key(data):
                    job = self.errorBestPost(iteration,out[data],anom)
                    if iteration >= 3:
                        best_failed = True
                    else:
                        return(job)                
                if data == 'bin':
                    #Binning is not set correctly on image header.
                    error = 'Binning not set correctly on image header.'
                    job = self.errorBestPost(3,error,anom)
                    best_failed = True               
                if data == 'sg':
                    self.logger.debug('User input SG not found in autoindexing, rerunning Best.')
                    self.ignore_user_SG = True
                    Utils.fixBestSGBack(self)
                    return(self.processBest(iteration,anom))
            if best_failed:
                if anom:
                    self.best_anom_results = { 'Best ANOM results' : 'FAILED'}
                    self.best_anom_failed = True
                else:
                    self.best_results = { 'Best results' : 'FAILED'}
                    self.best_failed = True
                                               
    def postprocessMosflm(self,input):
        """
        Pass Mosflm log into parsing and save output dict.
        """
        self.logger.debug('AutoindexingStrategy::postprocessMosflm')
        try:
            if input[-8:-4] == 'anom':
                anom = True
                j0 = ' ANOM '
                j1 = 'self.mosflm_strat_anom'
                j2 = 'Mosflm ANOM strategy results'
            else:
                anom = False
                j0 = ' '
                j1 = 'self.mosflm_strat'
                j2 = 'Mosflm strategy results'
            timer = 0
            log = []
            out = open(input,'r').readlines()
            for line in out:
                log.append(line)
                #self.logger.debug(line.rstrip())
            eval(j1+'_log').extend(log)
        except:
            self.logger.exception('**ERROR in postprocessMosflm**')
            
        data = Parse.ParseOutputMosflm_strat(self,log,anom)
        if data == None:
            self.logger.debug('No Mosflm'+j0+'strategy.')
            eval(j1+'_results').update({ j2 : 'FAILED' })
        else:
            eval(j1+'_results').update({ j2 : data })
            #Utils.fixBestfile(self)
                        
    def Queue(self,input='best'):
        """
        Queue for Labelit or Best.
        """
        self.logger.debug('AutoindexingStrategy::Queue')
        try:
            timed_out = False
            timer = 0
            labelit = False
            best = False
            mosflm = False
            pids = eval('self.'+input+'_jobs').keys()
            if pids != ['None']:
                counter = len(pids)
                while counter != 0:
                    for pid in pids:
                        if Utils.stillRunning(self,pid):
                            pass
                        else:                            
                            pids.remove(pid)                        
                            if input == 'labelit':
                                iteration = self.labelit_jobs[pid]
                                self.logger.debug('Finished Labelit'+str(iteration)) 
                                if iteration >= 10:
                                    iteration -=10
                                    job = self.postprocessLabelit(iteration,True)
                                else:
                                    job = self.postprocessLabelit(iteration,False)
                                if job != None:
                                    if self.multiproc:
                                        iteration +=10
                                        self.labelit_jobs[job.keys()[0]] = iteration
                                    else:
                                        self.labelit_jobs.update(job)
                                    pids.extend(job.keys())
                                else:
                                    counter -= 1                                
                            elif input == 'best':
                                self.logger.debug('Finished Best on '+str(self.best_jobs[pid])+' strategy')                        
                                job = self.postprocessBest(self.best_jobs[pid])
                                if job != None:
                                    self.best_jobs.update(job)
                                    pids.extend(job.keys())
                                else:
                                    counter -= 1
                            else:
                                self.logger.debug('Finished Mosflm on '+str(self.mosflm_jobs[pid])+' strategy')                        
                                job = self.postprocessMosflm(self.mosflm_jobs[pid])
                                if job != None:
                                    self.mosflm_jobs.update(job)
                                    pids.extend(job.keys())
                                else:
                                    counter -= 1                        
                    time.sleep(1)
                    timer += 1
                    if input == 'labelit':
                        print 'Waiting for Labelit to finish '+str(timer)+' seconds'
                        if self.labelit_timer:
                            if timer >= self.labelit_timer:
                                if self.multiproc:
                                    timed_out = True
                                    #Check folders to see why it timed out.
                                    self.clean = False
                                    break
                                else:
                                    iteration += 1
                                    if iteration <= 3:
                                        self.errorLabelit(iteration)                     
                                    else:
                                        break  
                    else:
                        print 'Waiting for strategy to finish '+str(timer)+' seconds'
                        if self.best_timer:
                            if timer >= self.best_timer:
                                timed_out = True        
                                break
                if timed_out:                   
                    if input == 'labelit':
                        self.logger.debug('Labelit timed out.')
                        print 'Labelit timed out.'
                    else:
                        self.logger.debug('Strategy timed out.')
                        print 'Strategy timed out.'
                    for pid in pids:                    
                        Utils.killChildren(self,pid)
                if input == 'labelit':
                    self.logger.debug('Labelit finished.')
                else:
                    self.logger.debug('Strategy finished.')
        
        except:
            self.logger.exception('**Error in Queue**')
           
    def LabelitLog(self):
        """
        Put the Lableit logs together.
        """
        self.logger.debug('AutoindexingStrategy::LabelitLog')
        try:
            if self.labelit_log == False:
                self.labelit_log = []
            for i in range(0,self.iterations):
                if eval('self.labelit_log'+str(i)):
                    self.labelit_log.append('-------------------------')
                    self.labelit_log.append('\nLABELIT ITERATION '+str(i)+'\n')
                    self.labelit_log.append('-------------------------\n')
                    for line in eval('self.labelit_log'+str(i)):                    
                        self.labelit_log.append(line)
                    self.labelit_log.append('\n')
                else:
                    self.labelit_log.append('\nLabelit iteration '+str(i)+' FAILED\n')        
        
        except:
            self.logger.exception('**ERROR in LabelitLog**')
        
    def labelitSort(self):
        """
        Sort out which iteration of Labelit has the highest symmetry and choose that solution. If
        Labelit does not find a solution, finish up the pipeline.
        """
        self.logger.debug('AutoindexingStrategy::labelitSort')
        temp = {}
        dict    = {}
        rms_list1 = []
        rms_list2 = []
        index = -1
        #sym = '0'
        try:
            for x in range(0,2):
                for i in range(0,self.iterations):
                    try:
                        face = self.labelit_results[str(i)].get('Labelit results').get('mosflm_face').index(':)')
                        sg = Utils.convertSG(self,self.labelit_results[str(i)].get('Labelit results').get('mosflm_sg')[face])
                        rms = self.labelit_results[str(i)].get('Labelit results').get('mosflm_rms')[face]
                        #Pick solution with highest symmetry
                        if x == 0:
                            if float(sg) >= index:
                                index = float(sg)
                        #If more than one solution, pick the one with the lowest Mosflm RMS.
                        else:
                            if float(sg) == index:
                                sym = sg
                                rms_list1.append(rms)
                                rms_list2.append(float(rms))
                                rms_min = numpy.argmin(rms_list2)
                                if rms == rms_list1[rms_min]:
                                   highest = str(i)
                    except:
                        pass
            #If there is a solution...
            if index != -1:
                self.labelit_results = self.labelit_results[highest]
                if self.spacegroup != 'None':
                    check_lg = Utils.checkSG(self,sym)
                    user_sg  = Utils.convertSG(self,self.spacegroup)
                    if user_sg == sym:
                        self.ignore_user_SG = False
                    if check_lg != [None]:
                        for line in check_lg:
                            if line.startswith(user_sg):
                                self.ignore_user_SG = False
                    else:
                        self.ignore_user_SG = True      
                path = 'labelit_iteration'+highest
                self.logger.debug('The sorted labelit solution was #'+highest)
                #Set self.labelit_dir and go to it and make an overlay jpeg.
                self.labelit_dir = os.path.join(self.working_dir,path)
                os.chdir(self.labelit_dir)                   
                if self.test == False:
                    self.makeImages(1)            
            else:
                self.logger.debug('No solution was found when sorting Labelit results.')
                self.labelit_failed = True
                self.labelit_results = { 'Labelit results'  : 'FAILED'} 
                path = 'labelit_iteration0'
                self.labelit_dir = os.path.join(self.working_dir,path)
                os.chdir(self.labelit_dir)
                self.LabelitLog()
                self.processDistl()
                self.postprocessDistl()
                if self.test == False:
                    if os.path.exists('DISTL_pickle'):
                        self.makeImages(2)
                self.best_failed = True
                self.best_anom_failed = True
                self.postprocess()
        
        except:
            self.logger.exception('**ERROR in labelitSort**')
        
    def PrintInfo(self):
        """
        Print information regarding programs utilized by RAPD
        """
        self.logger.debug('AutoindexingStrategy::PrintInfo')
        try:
            print '\nRAPD now using LABELIT'
            print '======================='
            print 'RAPD developed using Labelit'
            print 'Reference:  J. Appl. Cryst. 37, 399-409 (2004)'
            print 'Website:    http://adder.lbl.gov/labelit/ \n'
            print 'RAPD developed using Mosflm'
            print 'Reference: Leslie, A.G.W., (1992), Joint CCP4 + ESF-EAMCB Newsletter on Protein Crystallography, No. 26'
            print 'Website:   http://www.mrc-lmb.cam.ac.uk/harry/mosflm/ \n'
            print 'RAPD developed using RADDOSE'
            print 'Reference: Paithankar et. al. (2009)J. Synch. Rad. 16, 152-162.'
            print 'Website: http://biop.ox.ac.uk/www/garman/lab_tools.html/ \n'
            print 'RAPD developed using Best'
            print 'Reference: G.P. Bourenkov and A.N. Popov,  Acta Cryst. (2006). D62, 58-64'
            print 'Website:   http://www.embl-hamburg.de/BEST/ \n'
            self.logger.debug('RAPD now using LABELIT')
            self.logger.debug('=======================')
            self.logger.debug('RAPD developed using Labelit')
            self.logger.debug('Reference:  J. Appl. Cryst. 37, 399-409 (2004)')
            self.logger.debug('Website:    http://adder.lbl.gov/labelit/ \n')
            self.logger.debug('RAPD developed using Mosflm')
            self.logger.debug('Reference: Leslie, A.G.W., (1992), Joint CCP4 + ESF-EAMCB Newsletter on Protein Crystallography, No. 26')
            self.logger.debug('Website:   http://www.mrc-lmb.cam.ac.uk/harry/mosflm/ \n')
            self.logger.debug('RAPD developed using RADDOSE')
            self.logger.debug('Reference: Paithankar et. al. (2009)J. Synch. Rad. 16, 152-162.')
            self.logger.debug('Website: http://biop.ox.ac.uk/www/garman/lab_tools.html/ \n')
            self.logger.debug('RAPD developed using Best')
            self.logger.debug('Reference: G.P. Bourenkov and A.N. Popov,  Acta Cryst. (2006). D62, 58-64')
            self.logger.debug('Website:   http://www.embl-hamburg.de/BEST/ \n')
            
        except:
            self.logger.exception('**Error in PrintInfo**')        
        
    def makeImages(self, predictions):
        """
        Create images for iipimage server in an alternate process
        """
        self.logger.debug('AutoindexingStrategy::makeImages')
        try:
            #aggregate the source images
            src_images = []
            #1st image            
            src_images.append(self.header.get('fullname'))
            #if we have a pair
            if self.header2:
               src_images.append(self.header2.get('fullname'))   
            #A process-safe Queue for storing the resulting image names
            dict = {}
            dict['input']  = (src_images,predictions)
            dict['logger'] = self.logger
            dict['multi']  = self.multiproc
            #For raw image
            if predictions == 0:                   
                self.vips_images = multiprocessing.Queue()
                dict['output'] =  self.vips_images
            #for overlay images
            else:
                self.vips_images1 = multiprocessing.Queue()
                dict['output'] =  self.vips_images1
            job = multiprocessing.Process(target=makeImagesAction,kwargs=dict).start()
        
        except:
            self.logger.exception('**Error in makeImages.**')
    
    def postprocess(self):
        """
        Make all the HTML files, pass results back, and cleanup. 
        """
        self.logger.debug('AutoindexingStrategy::postprocess')
        output           = {}
        
        #Generate the proper summaries that go into the output HTML files
        if self.labelit_failed == False:
            if self.labelit_results:
                Summary.summaryLabelit(self)
                Summary.summaryAutoCell(self,True)
        if self.distl_results:
            Summary.summaryDistl(self)
        if self.raddose_results:
            Summary.summaryRaddose(self)
        #Decide when to get Best or Mosflm results
        if self.labelit_failed == False:
            if self.strategy == 'mosflm':
                self.htmlBestPlotsFailed()
                Summary.summaryMosflm(self,False)
                Summary.summaryMosflm(self,True)
            else:
                if self.best_failed:
                    if self.best_anom_failed:
                        self.htmlBestPlotsFailed()
                        Summary.summaryMosflm(self,False)
                        Summary.summaryMosflm(self,True)
                    else:
                        Summary.summaryMosflm(self,False)
                        Summary.summaryBest(self,True)
                        self.htmlBestPlots()
                elif self.best_anom_failed:
                    Summary.summaryMosflm(self,True)
                    Summary.summaryBest(self,False)
                    self.htmlBestPlots()
                else:
                    Summary.summaryBest(self,False)
                    Summary.summaryBest(self,True)
                    self.htmlBestPlots()
        else:
            self.htmlBestPlotsFailed()
        #Generate the long and short summary HTML files
        self.htmlSummaryShort()
        self.htmlSummaryLong()
        #Set STAC output to send back as None since it did not run.
        output['Stac summary html']  = 'None'
        
        #Get the raw tiff, autoindex_overlay, or distl_overlay of the diff pattern.
        if self.header2:
            f = 3
        else:
            f = 2
            output['image_path_raw_2']  = 'None'
            output['image_path_pred_2'] = 'None'
        for i in range(1,f):
            try:
                raw      = os.path.join(self.working_dir,self.vips_images.get())
                raw_path = os.path.join(self.dest_dir,os.path.basename(raw))
                raw_pid  = self.vips_images.get()            
                if raw_pid:
                    timer = 0
                    while Utils.stillRunning(self,raw_pid):
                        time.sleep(1)
                        timer += 1
                        print 'Waiting for ',raw,' ',str(timer),' seconds'
                output['image_path_raw_'+str(i)]  = raw_path
            except:
                self.logger.exception('**Could not find raw'+str(i)+'**')
                output['image_path_raw_'+str(i)]  = False
            try:
                if os.path.exists(os.path.join(self.labelit_dir,'DISTL_pickle')):
                    overlay         = self.vips_images1.get()
                    overlay_pid     = self.vips_images1.get()
                    labelit         = os.path.join(self.labelit_dir,overlay)
                    work            = os.path.join(self.working_dir,overlay)
                    path            = os.path.join(self.dest_dir,overlay)
                    if overlay_pid:
                        timer = 0
                        while Utils.stillRunning(self,overlay_pid):
                            time.sleep(1)
                            timer += 1
                            print 'Waiting for ',labelit,' ',str(timer),' seconds'
                    if os.path.exists(labelit):
                        shutil.copy(labelit,work)
                    output['image_path_pred_'+str(i)]  = path
                else:
                    output['image_path_pred_'+str(i)] = False
            except:
                self.logger.exception('**Could not find work'+str(i)+'**')
                output['image_path_pred_'+str(i)] = False                
        
        #Save path for files required for future STAC runs.                                
        try:
            if self.labelit_failed == False:
                files = {'1':'DNA_mosflm.inp','2':'bestfile.par'}
                for i in range(1,3):
                    shutil.copy(files[str(i)],self.working_dir)
                    stac_path = os.path.join(self.working_dir,files[str(i)])
                    path = os.path.join(self.dest_dir,files[str(i)])
                    if os.path.exists(stac_path):
                        output['STAC file'+str(i)] = path
                    else:
                        output['STAC file'+str(i)] = 'None'
            else:
                output['STAC file1'] = 'None'
                output['STAC file2'] = 'None'                
        except:
            self.logger.exception('**Could not update path of STAC files**')
            output['STAC file1'] = 'FAILED'
            output['STAC file2'] = 'FAILED'
        
        #Pass back paths for html files
        if self.beamline_use:
            e = '.php'
        else:
            e = '.html'
        files = {'0':{'file':'best_plots',       'name':'Best plots html'},
                 '1':{'file':'jon_summary_long', 'name':'Long summary html'},
                 '2':{'file':'jon_summary_short','name':'Short summary html'}}
        for i in range(0,3):
            try:
                a = files[str(i)].get('file')+e
                b = files[str(i)].get('name')
                path = os.path.join(self.working_dir,a)
                path2 = os.path.join(self.dest_dir,a)
                if os.path.exists(path):
                    output[b] = path2
                else:
                    output[b] = 'None'            
            except:
                self.logger.exception('**Could not update path of '+a+' file.**')
                output[b] = 'FAILED'        
        #Put all output files into a singe dict to pass back.
        output_files = {'Output files'   : output}
        
        #Put all the result dicts from all the programs run into one resultant dict and pass back.
        try:
            results = {}
            if self.labelit_results: 
                results.update(self.labelit_results)
            if self.distl_results:
                results.update(self.distl_results)
            if self.raddose_results:
                results.update(self.raddose_results)
            if self.best_results:
                results.update(self.best_results)
            if self.best_anom_results:
                results.update(self.best_anom_results)    
            if self.mosflm_strat_results:
                results.update(self.mosflm_strat_results)
            if self.mosflm_strat_anom_results:
                results.update(self.mosflm_strat_anom_results)  
            if output_files:
                results.update(output_files)
            if results:
                self.input.append(results)
            if self.beamline_use:
                self.sendBack2(self.input)
        except:
            self.logger.exception('**Could not send results to pipe.**')        
        
        #Cleanup my mess.
        try:
            os.chdir(self.working_dir)
            if self.clean:
                if self.test == False:
                    rm_folders = 'rm -rf labelit_iteration* dataset_preferences.py'
                    self.logger.debug('Cleaning up files and folders')
                    self.logger.debug(rm_folders)
                    os.system(rm_folders)                                                       
        except:
            self.logger.exception('**Could not cleanup**')
        
        #Move files from RAM to destination folder
        try:
            if self.beamline_use:
                if os.path.exists(self.dest_dir):
                    shutil.rmtree(self.dest_dir)
                shutil.move(self.working_dir,self.dest_dir)
            elif self.test:
                pass
            else:
                os.system('cp -R * '+self.dest_dir)
                os.system('rm -rf '+self.working_dir)
           
        except:
            self.logger.exception('**Could not move files from RAM to destination dir.**')
       
        #Say job is complete.
        t = round(time.time()-self.st)
        self.logger.debug('-------------------------------------')
        self.logger.debug('RAPD autoindexing/strategy complete.')
        self.logger.debug('Total elapsed time: '+str(t)+' seconds')
        self.logger.debug('-------------------------------------')
        print '\n-------------------------------------'
        print 'RAPD autoindexing/strategy complete.'
        print 'Total elapsed time: '+str(t)+' seconds'
        print '-------------------------------------'       
        #sys.exit(0) #did not appear to end script with some programs continuing on for some reason.
        os._exit(0)
        
    def htmlBestPlots(self):
        """
        generate plots html/php file
        """      
        self.logger.debug('AutoindexingStrategy::htmlBestPlots')        
        try:        
            run = True
            if self.best_failed == False:
                plot = open('best.plt','r').readlines()
            elif self.best_anom_failed == False:
                plot = open('bestanom.plt','r').readlines()
            else:
                self.htmlBestPlotsFailed()
                run = False
            if run:
                if self.beamline_use:
                    best_plot  = "<?php\n"
                    best_plot += "//prevents caching\n"
                    best_plot += 'header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");\n'
                    best_plot += 'header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");\n'
                    best_plot += 'header("Cache-Control: post-check=0, pre-check=0",false);\n'
                    best_plot += "session_cache_limiter();\n"
                    best_plot += "session_start();\n"
                    best_plot += "require('/var/www/html/rapd/login/config.php');\n"
                    best_plot += "require('/var/www/html/rapd/login/functions.php');\n"
                    best_plot +="//prevents unauthorized access\n"
                    best_plot +='if(allow_user() != "yes")\n'
                    best_plot +="{\n"
                    best_plot +='    if(allow_local_data($_SESSION[data]) != "yes")\n'
                    best_plot +="    {\n"
                    best_plot +="        include ('./login/no_access.html');\n"
                    best_plot +="        exit();\n"
                    best_plot +="    }\n"
                    best_plot +="}\n"                
                    best_plot += "?>\n\n"
                    best_plot += "<html>\n"
                else:                
                    best_plot = "<html>\n"
                best_plot += "  <head>\n"
                best_plot += '    <style type="text/css">\n'
                best_plot += "      body {\n"
                best_plot += "        background-image: none;\n"
                best_plot += "      }\n"
                best_plot += "       .y-label {width:7px; position:absolute; text-align:center; top:300px; left:15px; }\n"
                best_plot += "       .x-label {position:relative; text-align:center; top:10px; }\n"
                best_plot += "       .title {font-size:30px; text-align:center;} \n"
                best_plot += "    </style>\n"
                if self.beamline_use == False:
                    best_plot += '    <link href="layout.css" rel="stylesheet" type="text/css"></link>\n'
                    best_plot += '    <link type="text/css" href="../css/south-street/njquery-ui-1.7.2.custom.css" rel="stylesheet" />\n'
                    best_plot += '    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js" type="text/javascript"></script>\n'
                    best_plot += '    <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js" type="text/javascript"></script>\n'
                    best_plot += '    <script language="javascript" type="text/javascript" src="../js/flot/jquery.flot.js"></script>\n'
                best_plot += "    <script type='text/javascript'>\n"
                best_plot += '    $(function() {\n'
                best_plot += '        // Tabs\n'
                best_plot += "        $('.tabs').tabs();\n"
                best_plot += '    });\n'        
                best_plot += "    </script>\n\n"
                best_plot += "  </head>\n"
                best_plot += "  <body>\n"
                best_plot += "    <table>\n"
                best_plot += "      <tr> \n"
                best_plot += '        <td width="100%">\n'
                best_plot += '        <div class="tabs">\n'
                best_plot += "          <!-- This is where the tab labels are defined\n"
                best_plot += "               221 = tab2(on page) tab2(full output tab) tab1 -->\n"
                best_plot += "          <ul>\n"
                if self.best_failed == False:
                    best_plot += '            <li><a href="#tabs-221">Phi start</a></li>\n'
                else:
                    best_plot += '            <li><a href="#tabs-221">BEST FAILED</a></li>\n'
                if self.best_anom_failed == False:
                    best_plot += '            <li><a href="#tabs-222">ANOM Phi start</a></li>\n'
                else:
                    best_plot += '            <li><a href="#tabs-222">BEST ANOM FAILED</a></li>\n'
                best_plot += '            <li><a href="#tabs-223">Max delta Phi</a></li>\n'            
                if self.sample_type != 'Ribosome':
                    if self.dose:
                        best_plot += '            <li><a href="#tabs-224">Rad damage1</a></li>\n'
                        best_plot += '            <li><a href="#tabs-225">Rad damage2</a></li>\n'        
                best_plot += '            <li><a href="#tabs-226">Wilson Plot</a></li>\n'        
                best_plot += "          </ul>\n"
                if self.best_failed == False:
                    best_plot += '          <div id="tabs-221">\n'
                    best_plot += '            <div class=title><b>Min osc range for different completenesses</b></div>\n'
                    best_plot += '            <div id="chart5_div" style="width:800px;height:600px"></div>\n'
                    best_plot += '            <span class=y-label>P h i &nbsp R a n g e</span>\n'
                    best_plot += '            <div class=x-label>Phi Start</div>\n' 
                    best_plot += "          </div>\n"
                else:
                    best_plot += '          <div id="tabs-221">\n'
                    best_plot += '            <div class=title><b>BEST FAILED</b></div>\n'
                    best_plot += "          </div>\n"  
                if self.best_anom_failed == False:
                    best_plot += '          <div id="tabs-222">\n'
                    best_plot += '            <div class=title><b>Min osc range for different completenesses</b></div>\n'
                    best_plot += '            <div id="chart6_div" style="width:800px;height:600px"></div>\n'
                    best_plot += '            <span class=y-label>P h i &nbsp R a n g e</span>\n'
                    best_plot += '            <div class=x-label>Phi Start</div>\n' 
                    best_plot += "          </div>\n"
                else:
                    best_plot += '          <div id="tabs-222">\n'
                    best_plot += '            <div class=title><b>BEST ANOM FAILED</b></div>\n'
                    best_plot += "          </div>\n"  
                best_plot += '          <div id="tabs-223">\n'
                best_plot += '            <div class=title><b>Maximal Oscillation Width</b></div>\n'
                best_plot += '            <div id="chart2_div" style="width:800px;height:600px"></div>\n'
                best_plot += '            <span class=y-label>P h i &nbsp S t e p</span>\n'
                best_plot += '            <div class=x-label>Phi</div>\n' 
                best_plot += "          </div>\n"
                if self.sample_type != 'Ribosome':
                    if self.dose:
                        best_plot += '          <div id="tabs-224">\n'
                        best_plot += '            <div class=title><b>Intensity decrease due to radiation damage</b></div>\n'
                        best_plot += '            <div id="chart3_div" style="width:800px;height:600px"></div>\n'
                        best_plot += '            <span class=y-label>R e l a t i v e &nbsp I n t e n s i t y</span>\n'
                        best_plot += '            <div class=x-label>Cumulative exposure time (sec)</div>\n' 
                        best_plot += "          </div>\n"
                        best_plot += '          <div id="tabs-225">\n'
                        best_plot += '            <div class=title><b>Rdamage vs. Cumulative Exposure time</b></div>\n'
                        best_plot += '            <div id="chart4_div" style="width:800px;height:600px"></div>\n'
                        best_plot += '            <span class=y-label>R f a c t o r</span>\n'
                        best_plot += '            <div class=x-label>Cumulative exposure time (sec)</div>\n' 
                        best_plot += "          </div>\n"        
                best_plot += '          <div id="tabs-226">\n'
                best_plot += '            <div class=title><b>Wilson Plot</b></div>\n'
                best_plot += '            <div id="chart1_div" style="width:800px;height:600px"></div>\n'
                best_plot += '            <span class=y-label>I n t e n s i t y</span>\n'
                best_plot += '            <div class=x-label>1/Resolution<sup>2</sup></div>\n' 
                best_plot += "          </div>\n"
                best_plot += "        </div>\n"
                best_plot += "        <!-- End of Tabs -->\n"
                best_plot += "      </td>\n"
                best_plot += "     </tr>\n"
                best_plot += "  </table>\n\n"
                best_plot += '  <script id="source" language="javascript" type="text/javascript">\n'
                best_plot += "$(function () {\n\n"
                res              = []
                completeness     = []            
                completenessanom = []        
                for x in range(len(plot)):
                    if plot[x].startswith("% linelabel  = 'Theory'"):
                        wilson_theory_start = x + 1
                    if plot[x].startswith("% linelabel  = 'Pred.low errors'"):                
                        wilson_theory_end = x - 4
                        wilson_low_start = x + 1
                    if plot[x].startswith("% linelabel  = 'Pred.high errors'"):
                        wilson_low_end = x - 4
                        wilson_high_start = x + 1
                    if plot[x].startswith("% linelabel  = 'Experiment'"):
                        wilson_high_end = x - 1
                        wilson_exp_start = x + 6            
                    if plot[x].startswith("% toplabel  = 'Maximal oscillation width'"):
                        wilson_exp_end = x - 1
                    if plot[x].startswith("% linelabel  = 'resol. "):
                        res.append(x)
                    if plot[x].startswith("% linelabel  = 'compl"):
                        completeness.append(x)                                  
                wilson0 = plot[wilson_theory_start:wilson_theory_end]
                wilson1 = plot[wilson_low_start:wilson_low_end]
                wilson2 = plot[wilson_high_start:wilson_high_end]
                wilson3 = plot[wilson_exp_start:wilson_exp_end]
                best_plot += "    var wilson0 = [], wilson1 = [], wilson2 = [], wilson3 = [];\n"        
                for i in range(0,4):
                    for line in eval('wilson'+str(i)):
                        split = line.split()
                        if len(split) == 2:
                            x = split[0]
                            y = split[1]
                            best_plot += "    wilson"+str(i)+".push(["+x+","+y+"]);\n"        
                best_plot += "\n    var width0 = [], width1 = [], width2 = [], width3 = [], width4 = [];\n"
                width_label = []
                for i in range(0,5):
                    if i == 4:
                        temp = plot[res[i]+1:res[i]+182]
                    else:
                        temp = plot[res[i]+1:res[i+1]-5]
                    label = plot[res[i]].split()[4]
                    width_label.append('          { data: width'+str(i)+', label:"'+label+' A" },\n')
                    for line in temp:
                        split = line.split()
                        if len(split) == 2:
                            x = split[0]
                            y = split[1]
                            best_plot += "    width"+str(i)+".push(["+x+","+y+"]);\n"
                if self.sample_type != 'Ribosome':
                    if self.dose:
                        for x in range(0,2):
                            if x == 0:
                                damage_label = []
                                j1 = ''
                                i1 = 5
                                i2 = 0
                            else:
                                rdamage_label = []
                                j1 = 'r'
                                i1 = 15
                                i2 = 400
                            best_plot += "\n    var "+j1+"damage0 = [], "+j1+"damage1 = [], "+j1+"damage2 = [], "+j1+"damage3 = [], "+j1+"damage4 = [],\n"
                            best_plot += "        "+j1+"damage5 = [], "+j1+"damage6 = [], "+j1+"damage7 = [], "+j1+"damage8 = [], "+j1+"damage9 = [];\n"
                            label1 = []
                            for i in range(0,10):
                                if i == 9:
                                    temp = plot[res[i+i1]+1:res[i+i1]+102+i2]
                                else:
                                    temp = plot[res[i+i1]+1:res[i+i1+1]-5]
                                label = plot[res[i+i1]].split()[4]
                                label1.append('          { data: '+j1+'damage'+str(i)+', label:"'+label+' A" },\n')                
                                for line in temp:
                                    split = line.split()
                                    if len(split) == 2:
                                        x = split[0]
                                        y = split[1]
                                        best_plot += "    "+j1+"damage"+str(i)+".push([" +x+","+y+"]);\n"
                            eval(j1+'damage_label').extend(label1)
                for x in range(0,2):
                    run = False
                    if x == 0:
                        if self.best_failed == False:
                            com_label = []
                            com = completeness
                            phi_start = self.best_results.get('Best results').get('strategy phi start')
                            j1 = ''
                            run = True
                    else:
                        if self.best_anom_failed == False:
                            plotanom = open('bestanom.plt','r').readlines()
                            for x in range(len(plotanom)):   
                                if plotanom[x].startswith("% linelabel  = 'compl"):
                                    completenessanom.append(x)
                            comanom_label = []
                            com = completenessanom
                            phi_start = self.best_anom_results.get('Best ANOM results').get('strategy anom phi start')                    
                            j1 = 'anom'
                            run = True
                    if run:
                        junk = []
                        label1 = []
                        best_plot += "\n    var com"+j1+"0 = [], com"+j1+"1 = [], com"+j1+"2 = [], com"+j1+"3 = [], com"+j1+"4 = [], mark"+j1+" = [];\n"
                        for i in range(0,5):                
                            if i == 0:                    
                                temp = eval('plot'+j1)[com[i]+4:com[i+1]-4]
                            else:
                                temp = eval('plot'+j1)[com[i]+1:com[i+1]-4]
                            label = eval('plot'+j1)[com[i]].split()[4][:-1]
                            label1.append('          { data: com'+j1+str(i)+', label:"compl'+label+'" },\n')
                            for line in temp:
                                split = line.split()
                                if len(split) == 2:
                                    x = split[0]
                                    y = split[1]
                                    best_plot += "    com"+j1+str(i)+".push([" +x+","+y+"]);\n"                        
                                    if i == 0:
                                        junk.append(y)
                        junk.sort()
                        junk.reverse()
                        mark_max = junk[0]
                        best_plot += "    for (var i = 0; i < "+mark_max+"; i += 5)\n"
                        best_plot += "    mark"+j1+".push(["+phi_start[0]+",i]);\n"
                        eval('com'+j1+'_label').extend(label1)           
                best_plot += '\n    var plot1 = $.plot($("#chart1_div"),\n'
                best_plot += '        [ { data: wilson0, label:"theory" }, { data: wilson1, label: "low" },\n'
                best_plot += '          { data: wilson2, label: "high" }, { data: wilson3, label: "Experiment" }],\n'
                best_plot += "        { lines: { show: true},\n"
                best_plot += "          points: { show: false },\n"
                best_plot += "          selection: { mode: 'xy' },\n"
                best_plot += "          grid: { hoverable: true, clickable: true },\n"
                best_plot += "        });\n\n"            
                best_plot += '    var plot2 = $.plot($("#chart2_div"),\n'
                best_plot += '        [\n'
                for line in width_label:
                    best_plot += line
                best_plot += '        ],\n'
                best_plot += "        { lines: { show: true},\n"
                best_plot += "          points: { show: false },\n"
                best_plot += "          selection: { mode: 'xy' },\n"
                best_plot += "          grid: { hoverable: true, clickable: true },\n"
                best_plot += "        }); \n\n"            
                if self.sample_type != 'Ribosome':
                    if self.dose:
                        best_plot += '    var plot3 = $.plot($("#chart3_div"),\n'
                        best_plot += '        [\n'
                        for line in damage_label:
                            best_plot += line
                        best_plot += '        ],\n'
                        best_plot += "        { lines: { show: true},\n"
                        best_plot += "          points: { show: false },\n"
                        best_plot += "          selection: { mode: 'xy' },\n"
                        best_plot += "          grid: { hoverable: true, clickable: true },\n"
                        best_plot += "        }); \n\n"
                        best_plot += '    var plot4 = $.plot($("#chart4_div"),\n'
                        best_plot += '        [\n'
                        for line in rdamage_label:
                            best_plot += line
                        best_plot += '        ],\n'
                        best_plot += "        { lines: { show: true},\n"
                        best_plot += "          points: { show: false },\n"
                        best_plot += "          selection: { mode: 'xy' },\n"
                        best_plot += "          grid: { hoverable: true, clickable: true },\n"
                        best_plot += "        }); \n\n"
                if self.best_failed == False:
                    best_plot += '    var plot5 = $.plot($("#chart5_div"),\n'
                    best_plot += '        [\n'
                    for line in com_label:
                        best_plot += line
                    best_plot += '          {data: mark, label: "Best starting Phi", color: "black" }],\n'            
                    best_plot += "        { lines: { show: true},\n"
                    best_plot += "          points: { show: false },\n"
                    best_plot += "          selection: { mode: 'xy' },\n"
                    best_plot += "          grid: { hoverable: true, clickable: true },\n"
                    best_plot += "        }); \n\n"
                if self.best_anom_failed == False:            
                    best_plot += '    var plot6 = $.plot($("#chart6_div"),\n'
                    best_plot += '        [\n'
                    for line in comanom_label:
                        best_plot += line
                    best_plot += '          {data: markanom, label: "Best starting Phi", color: "black" }],\n'
                    best_plot += "        { lines: { show: true},\n"
                    best_plot += "          points: { show: false },\n"
                    best_plot += "          selection: { mode: 'xy' },\n"
                    best_plot += "          grid: { hoverable: true, clickable: true },\n"
                    best_plot += "        }); \n\n"       
                best_plot += "    function showTooltip(x, y, contents) {\n"
                best_plot += "        $('<div id="+"tooltip"+">' + contents + '</div>').css( {\n"
                best_plot += "            position: 'absolute',\n"
                best_plot += "            display: 'none',\n"
                best_plot += "            top: y + 5,\n"
                best_plot += "            left: x + 5,\n"
                best_plot += "            border: '1px solid #fdd',\n"
                best_plot += "            padding: '2px',\n"
                best_plot += "            'background-color': '#fee',\n"
                best_plot += "            opacity: 0.80\n"
                best_plot += '        }).appendTo("body").fadeIn(200);\n'
                best_plot += "    }\n\n"
                best_plot += "    var previousPoint = null;\n"
                best_plot += '    $("#chart1_div").bind("plothover", function (event, pos, item) {\n'
                best_plot += '        $("#x").text(pos.x.toFixed(2));\n'
                best_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
                best_plot += "        if (true) {\n"
                best_plot += "            if (item) {\n"
                best_plot += "                if (previousPoint != item.datapoint) {\n"
                best_plot += "                    previousPoint = item.datapoint;\n\n"
                best_plot += '                    $("#tooltip").remove();\n'
                best_plot += "                    var x = item.datapoint[0].toFixed(2),\n"
                best_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
                best_plot += "                    showTooltip(item.pageX, item.pageY,\n"
                best_plot += '                                item.series.label + " of " + x + " = " + y);\n'
                best_plot += "                }\n"
                best_plot += "            }\n"
                best_plot += "            else {\n"
                best_plot += '                $("#tooltip").remove();\n'
                best_plot += "                previousPoint = null;\n"
                best_plot += "            }\n"
                best_plot += "        }\n"
                best_plot += "    });\n\n"
                best_plot += '    $("#chart2_div").bind("plothover", function (event, pos, item) {\n'
                best_plot += '        $("#x").text(pos.x.toFixed(2));\n'
                best_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
                best_plot += "        if (true) {\n"
                best_plot += "            if (item) {\n"
                best_plot += "                if (previousPoint != item.datapoint) {\n"
                best_plot += "                    previousPoint = item.datapoint;\n\n"
                best_plot += '                    $("#tooltip").remove();\n'
                best_plot += "                    var x = item.datapoint[0].toFixed(2),\n"
                best_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
                best_plot += "                    showTooltip(item.pageX, item.pageY,\n"
                best_plot += '                                "max delta phi of " + y + " at phi=" + x);\n'
                best_plot += "                }\n"
                best_plot += "            }\n"
                best_plot += "            else {\n"
                best_plot += '                $("#tooltip").remove();\n'
                best_plot += "                previousPoint = null;\n"
                best_plot += "            }\n"
                best_plot += "        }\n"
                best_plot += "    });\n\n"
                if self.sample_type != 'Ribosome':
                    if self.dose:
                        best_plot += '    $("#chart3_div").bind("plothover", function (event, pos, item) {\n'
                        best_plot += '        $("#x").text(pos.x.toFixed(2));\n'
                        best_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
                        best_plot += "        if (true) {\n"
                        best_plot += "            if (item) {\n"
                        best_plot += "                if (previousPoint != item.datapoint) {\n"
                        best_plot += "                    previousPoint = item.datapoint;\n\n"
                        best_plot += '                    $("#tooltip").remove();\n'
                        best_plot += "                    var x = item.datapoint[0].toFixed(2),\n"
                        best_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
                        best_plot += "                    showTooltip(item.pageX, item.pageY,\n"
                        best_plot += '                                "at res=" + item.series.label + " after " + x + " seconds intensity drops to " + y);\n'
                        best_plot += "                }\n"
                        best_plot += "            }\n"
                        best_plot += "            else {\n"
                        best_plot += '                $("#tooltip").remove();\n'
                        best_plot += "                previousPoint = null;\n"
                        best_plot += "            }\n"
                        best_plot += "        }\n"
                        best_plot += "    });\n\n"
                        best_plot += '    $("#chart4_div").bind("plothover", function (event, pos, item) {\n'
                        best_plot += '        $("#x").text(pos.x.toFixed(2));\n'
                        best_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
                        best_plot += "        if (true) {\n"
                        best_plot += "            if (item) {\n"
                        best_plot += "                if (previousPoint != item.datapoint) {\n"
                        best_plot += "                    previousPoint = item.datapoint;\n\n"
                        best_plot += '                    $("#tooltip").remove();\n'
                        best_plot += "                    var x = item.datapoint[0].toFixed(2),\n"
                        best_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
                        best_plot += "                    showTooltip(item.pageX, item.pageY,\n"
                        best_plot += '                                "at res=" + item.series.label + " after " + x + " seconds Rdamage increases to " + y);\n'
                        best_plot += "                }\n"
                        best_plot += "            }\n"
                        best_plot += "            else {\n"
                        best_plot += '                $("#tooltip").remove();\n'
                        best_plot += "                previousPoint = null;\n"
                        best_plot += "            }\n"
                        best_plot += "        }\n"
                        best_plot += "    });\n\n"
                if self.best_failed == False:
                    best_plot += '    $("#chart5_div").bind("plothover", function (event, pos, item) {\n'
                    best_plot += '        $("#x").text(pos.x.toFixed(2));\n'
                    best_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
                    best_plot += "        if (true) {\n"
                    best_plot += "            if (item) {\n"
                    best_plot += "                if (previousPoint != item.datapoint) {\n"
                    best_plot += "                    previousPoint = item.datapoint;\n\n"
                    best_plot += '                    $("#tooltip").remove();\n'
                    best_plot += "                    var x = item.datapoint[0].toFixed(2),\n"
                    best_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
                    best_plot += "                    showTooltip(item.pageX, item.pageY,\n"
                    best_plot += '                                "start at " + x + " for " + y + " degrees");\n'
                    best_plot += "                }\n"
                    best_plot += "            }\n"
                    best_plot += "            else {\n"
                    best_plot += '                $("#tooltip").remove();\n'
                    best_plot += "                previousPoint = null;\n"
                    best_plot += "            }\n"
                    best_plot += "        }\n"
                    best_plot += "    });\n\n"                        
                if self.best_anom_failed == False:
                    best_plot += '    $("#chart6_div").bind("plothover", function (event, pos, item) {\n'
                    best_plot += '        $("#x").text(pos.x.toFixed(2));\n'
                    best_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
                    best_plot += "        if (true) {\n"
                    best_plot += "            if (item) {\n"
                    best_plot += "                if (previousPoint != item.datapoint) {\n"
                    best_plot += "                    previousPoint = item.datapoint;\n\n"
                    best_plot += '                    $("#tooltip").remove();\n'
                    best_plot += "                    var x = item.datapoint[0].toFixed(2),\n"
                    best_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
                    best_plot += "                    showTooltip(item.pageX, item.pageY,\n"
                    best_plot += '                                "start at " + x + " for " + y + " degrees");\n'
                    best_plot += "                }\n"
                    best_plot += "            }\n"
                    best_plot += "            else {\n"
                    best_plot += '                $("#tooltip").remove();\n'
                    best_plot += "                previousPoint = null;\n"
                    best_plot += "            }\n"
                    best_plot += "        }\n"
                    best_plot += "    });\n\n"
                best_plot += "});\n"
                best_plot += "</script>\n"
                best_plot += "</body>\n"
                best_plot += "</html>\n"
                if self.beamline_use:
                    file = 'best_plots.php'
                else:
                    file = 'best_plots.html'
                best_plot_file = open(file,'w')
                best_plot_file.writelines(best_plot)
                best_plot_file.close()
                if os.path.exists(file):
                    shutil.copy(file,self.working_dir)
        
        except:
            self.logger.exception('**ERROR in htmlBestPlots**')
            self.htmlBestPlotsFailed()
           
    def htmlBestPlotsFailed(self):
        """
        If Best failed or was not run, this is the resultant html/php file.
        """
        self.logger.debug('AutoindexingStrategy::htmlBestPlotsFailed')
        try:
            if self.beamline_use:
                best_plot  = "<?php\n"
                best_plot += "//prevents caching\n"
                best_plot += 'header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");\n'
                best_plot += 'header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");\n'
                best_plot += 'header("Cache-Control: post-check=0, pre-check=0",false);\n'
                best_plot += "session_cache_limiter();\n"
                best_plot += "session_start();\n"
                best_plot += "require('/var/www/html/rapd/login/config.php');\n"
                best_plot += "require('/var/www/html/rapd/login/functions.php');\n"
                best_plot += 'if(allow_user() != "yes")\n'
                best_plot += "{\n"
                best_plot += "    include ('./login/no_access.html');\n"
                best_plot += "    exit();\n"
                best_plot += "}\n"
                best_plot += "?>\n\n"
                best_plot += "<html>\n"
            else:                
                best_plot = "<html>\n"                     
            best_plot +='  <head>\n'
            best_plot +='    <style type="text/css" media="screen">\n'
            
            if self.beamline_use == False:
                best_plot +='      @import "../css/dataTables-1.5/media/css/demo_page.css";\n'
                best_plot +='      @import "../css/dataTables-1.5/media/css/demo_table.css";\n'          
            best_plot +='    body {\n'
            best_plot +='      background-image: none;\n'
            best_plot +='    }\n'
            best_plot +='    .dataTables_wrapper {position: relative; min-height: 75px; _height: 302px; clear: both;    }\n'
            best_plot +='    table.display td {padding: 1px 7px;}\n'
            best_plot +='    #dt_example h1 {margin-top: 1.2em; font-size: 1.5em; font-weight: bold; line-height: 1.6em; color: green;\n'
            best_plot +='                    border-bottom: 2px solid green; clear: both;}\n'
            best_plot +='    #dt_example h2 {font-size: 1.2em; font-weight: bold; line-height: 1.6em; color: #808080; clear: both;}\n'
            best_plot +='    #dt_example h3 {font-size: 1.4em; font-weight: bold; line-height: 1.6em; color: red; clear: both;}\n'
            best_plot +='    #dt_example h4 {font-size: 1.4em; font-weight: bold; line-height: 1.6em; color: orange; clear: both;}\n'
            best_plot +='    table.display tr.odd.gradeA { background-color: #eeffee;}\n'
            best_plot +='    table.display tr.even.gradeA { background-color: #ffffff;}\n'
            best_plot +='    </style>\n'
            if self.beamline_use == False:
                best_plot +='    <script type="text/javascript" language="javascript" src="../css/dataTables-1.5/media/js/jquery.js"></script>\n'
                best_plot +='    <script type="text/javascript" language="javascript" src="../css/dataTables-1.5/media/js/jquery.dataTables.js"></script>\n'
            best_plot +='    <script type="text/javascript" charset="utf-8">\n'
            best_plot +='      $(document).ready(function() {\n'           
            best_plot +="        $('#best').dataTable({\n"
            best_plot +='           "bPaginate": false,\n'
            best_plot +='           "bFilter": false,\n'
            best_plot +='           "bInfo": false,\n'
            best_plot +='           "bAutoWidth": false    });\n'
            best_plot +='      } );\n'
            best_plot +="    </script>\n\n\n"
            best_plot +=" </head>\n"
            best_plot +='  <body id="dt_example">\n'
            best_plot +='    <div id="container">\n'
            best_plot +='    <div class="full_width big">\n'
            best_plot +='      <div id="demo">\n'
            if self.strategy == 'mosflm':
                best_plot +='      <h4 class="results">Mosflm strategy was chosen so no plots are calculated.</h4>\n'
            else:
                best_plot +='      <h3 class="results">Best Failed. Could not calculate plots.</h3>\n'
            best_plot +="      </div>\n"
            best_plot +="    </div>\n"
            best_plot +="    </div>\n"
            best_plot +="  </body>\n"
            best_plot +="</html>\n"
            if self.beamline_use:
                file = 'best_plots.php'
            else:
                file = 'best_plots.html'
            best_plot_file = open(file,'w')
            best_plot_file.writelines(best_plot)
            best_plot_file.close()
            if os.path.exists(file):
                shutil.copy(file,self.working_dir)
                        
        except:
            self.logger.exception('**ERROR in htmlBestPlotsFailed**')
    
    def htmlSummaryLong(self):
        """
        Create HTML/php files for autoindex/strategy output results.
        """
        self.logger.debug('AutoindexingStrategy::htmlSummaryLong')
        try:            
            if self.beamline_use:
                file = 'jon_summary_long.php'
            else:
                file = 'jon_summary_long.html'
            jon_summary = open(file,'w')
            if self.beamline_use:
                jon_summary.write("<?php\n")
                jon_summary.write("//prevents caching\n")
                jon_summary.write('header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");\n')
                jon_summary.write('header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");\n')
                jon_summary.write('header("Cache-Control: post-check=0, pre-check=0",false);\n')
                jon_summary.write("session_cache_limiter();\n")
                jon_summary.write("session_start();\n")
                jon_summary.write("require('/var/www/html/rapd/login/config.php');\n")
                jon_summary.write("require('/var/www/html/rapd/login/functions.php');\n")
                jon_summary.write("//prevents unauthorized access\n")
                jon_summary.write('if(allow_user() != "yes")\n')
                jon_summary.write("{\n")
                jon_summary.write('    if(allow_local_data($_SESSION[data]) != "yes")\n')
                jon_summary.write("    {\n")
                jon_summary.write("        include ('./login/no_access.html');\n")
                jon_summary.write("        exit();\n")
                jon_summary.write("    }\n")
                jon_summary.write("}\n")
                jon_summary.write("?>\n\n")
            jon_summary.write('<html>\n')
            jon_summary.write('  <head>\n')
            jon_summary.write('    <style type="text/css" media="screen">\n')
            #jon_summary.write('      @import url("css/rapd.css");\n')
            """
            if self.beamline_use:
                jon_summary.write('      @import "css/demo_page.css";\n')
                jon_summary.write('      @import "css/demo_table.css";\n') 
            """    
            if self.beamline_use == False:
                jon_summary.write('      @import "../css/ndemo_page.css";\n')
                jon_summary.write('      @import "../css/ndemo_table.css";\n')                
                jon_summary.write('      @import "../css/south-street/jquery-ui-1.7.2.custom.css";\n')
            jon_summary.write('    body {\n')
            jon_summary.write('      background-image: none;\n')
            jon_summary.write('    }\n')
            jon_summary.write('    .dataTables_wrapper {position: relative; min-height: 75px; _height: 302px; clear: both;    }\n')
            jon_summary.write('    table.display td {padding: 1px 7px;}\n')
            #jon_summary.write('    #container {width: 800px; margin: 30px auto;padding: 0; margin-left:0px; margin-right:auto;}\n')
            #jon_summary.write('                    border-bottom: 2px solid green; clear: both;}\n')
            #jon_summary.write('    #dt_example h2 {font-size: 1.2em; font-weight: bold; line-height: 1.6em; color: #808080; clear: both;}\n')
            #jon_summary.write('    #dt_example h3 {font-size: 1.4em; font-weight: bold; line-height: 1.6em; color: red; clear: both;}\n')
            #jon_summary.write('    #dt_example h4 {font-size: 1.4em; font-weight: bold; line-height: 1.6em; color: orange; clear: both;}\n')
            #jon_summary.write('    table.display tr.odd.gradeA { background-color: #eeffee;}\n')
            #jon_summary.write('    table.display tr.even.gradeA { background-color: #ffffff;}\n')
            jon_summary.write('    </style>\n')
            if self.beamline_use == False:
                jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.js"></script>\n')
                jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.dataTables.js"></script>\n')
                jon_summary.write('    <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js" type="text/javascript"></script>\n')
            jon_summary.write('    <script type="text/javascript" charset="utf-8">\n')
            jon_summary.write('      $(document).ready(function() {\n')
            jon_summary.write("        $('#accordion').accordion({\n")
            jon_summary.write('           collapsible: true,\n')
            jon_summary.write('           active: false         });\n')
            if self.best_summary:
                jon_summary.write("        $('#best').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bAutoWidth": false    });\n') 
            if self.best_anom_summary:
                jon_summary.write("        $('#bestanom').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bAutoWidth": false    });\n') 
            if self.best_failed or self.strategy == 'mosflm':
                if self.mosflm_strat_summary:
                    jon_summary.write("        $('#strat').dataTable({\n")
                    jon_summary.write('           "bPaginate": false,\n')
                    jon_summary.write('           "bFilter": false,\n')
                    jon_summary.write('           "bInfo": false,\n')
                    jon_summary.write('           "bAutoWidth": false    });\n')     
            if self.best_anom_failed or self.strategy == 'mosflm':
                if self.mosflm_strat_anom_summary:
                    jon_summary.write("        $('#stratanom').dataTable({\n")
                    jon_summary.write('           "bPaginate": false,\n')
                    jon_summary.write('           "bFilter": false,\n')
                    jon_summary.write('           "bInfo": false,\n')
                    jon_summary.write('           "bAutoWidth": false    });\n')     
            if self.labelit_summary:                              
                jon_summary.write("        $('#mosflm').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bAutoWidth": false    });\n')                          
                jon_summary.write("        $('#labelit').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bAutoWidth": false    });\n')              
            if self.distl_summary:        
                jon_summary.write("        $('#distl').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bAutoWidth": false    });\n')              
            jon_summary.write('                } );\n')       
            jon_summary.write("    </script>\n\n\n")
            jon_summary.write(" </head>\n")
            jon_summary.write('  <body id="dt_example">\n')                    
            if self.best_summary:
                jon_summary.writelines(self.best_summary)
            if self.best_summary_long:
                jon_summary.writelines(self.best_summary_long)                                   
            if self.best_results:
                if self.best_results.get('Best results') == 'FAILED':
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('     <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')            
                    jon_summary.write('    <h4 class="results">Best Failed. Trying Mosflm strategy.</h3>\n')
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
            if self.mosflm_strat_summary:
                jon_summary.writelines(self.mosflm_strat_summary)    
            if self.mosflm_strat_summary_long:
                jon_summary.writelines(self.mosflm_strat_summary_long)                   
            if self.mosflm_strat_results:
                if self.mosflm_strat_results.get('Mosflm strategy results') == 'FAILED':
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('     <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')            
                    jon_summary.write('    <h3 class="results">Mosflm Strategy Failed. Could not calculate a strategy.</h3>\n')             
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
            if self.best_anom_summary:
                jon_summary.writelines(self.best_anom_summary) 
            if self.best_anom_summary_long:
                jon_summary.writelines(self.best_anom_summary_long)                                  
            if self.best_anom_results:
                if self.best_anom_results.get('Best ANOM results') == 'FAILED':
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('     <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')            
                    jon_summary.write('    <br>')
                    jon_summary.write('    <h4 class="results">Best Failed. Trying Mosflm ANOMALOUS strategy.</h3>\n')
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
            if self.mosflm_strat_anom_summary:
                jon_summary.writelines(self.mosflm_strat_anom_summary)  
            if self.mosflm_strat_anom_summary_long:
                jon_summary.writelines(self.mosflm_strat_anom_summary_long)                     
            if self.mosflm_strat_anom_results:
                if self.mosflm_strat_anom_results.get('Mosflm ANOM strategy results') == 'FAILED':
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('     <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')            
                    jon_summary.write('    <br>')
                    jon_summary.write('    <h3 class="results">Mosflm Strategy Failed. Could not calculate an ANOMALOUS strategy.</h3>\n')   
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
            if self.raddose_summary:
                jon_summary.writelines(self.raddose_summary) 
            if self.raddose_results:                     
                if self.raddose_results.get('Raddose results') == 'FAILED':
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('     <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')            
                    jon_summary.write('    <h4 class="results">Raddose failed. Using default dosage. Best results are still good.</h4>\n')  
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")                               
            if self.labelit_summary:
                jon_summary.writelines(self.labelit_summary)   
            if self.labelit_results:    
                if self.labelit_results.get('Labelit results') == 'FAILED':
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('     <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')            
                    jon_summary.write('    <h3 class="results">Autoindexing FAILED</h3>\n')
                    if self.blank_image:
                        jon_summary.write('    <h4 class="results">Not enough spots!!</h3>\n')
                    if self.header2:
                        jon_summary.write('    <h4 class="results">Pair of snapshots did not autoindex. Possibly not from same crystal.</h3>\n')
                    else:
                        jon_summary.write('    <h4 class="results">You can add "pair" to the snapshot name and collect one at 0 and 90 degrees. Much better for poor diffraction.</h3>\n')
                        jon_summary.write('    <h4 class="results">eg."snap_pair_99_001.img"</h3>\n')           
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
            if self.distl_summary:
                jon_summary.writelines(self.distl_summary)                    
            if self.distl_results:                    
                if self.distl_results.get('Distl results') == 'FAILED':
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('     <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')            
                    jon_summary.write('    <h4 class="results">Distl failed. Could not parse peak search file. If you see this, not an indexing problem. Best results are still good.</h4>\n')
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")   
            #jon_summary.write("      </div>\n")
            jon_summary.write('    <div id="container">\n')
            jon_summary.write('    <div class="full_width big">\n')
            jon_summary.write('      <div id="demo">\n')            
            jon_summary.write("      <h1 class='Results'>RAPD Logfile</h1>\n")
            jon_summary.write("     </div>\n")  
            jon_summary.write("     </div>\n")  
            jon_summary.write('      <div id="accordion">\n')
            jon_summary.write('        <h3><a href="#">Click to view log</a></h3>\n')
            jon_summary.write('          <div>\n')
            jon_summary.write('            <pre>\n')
            jon_summary.write('\n')
            jon_summary.write('---------------Autoindexing RESULTS---------------\n')
            jon_summary.write('\n')            
            if self.labelit_log:
                for line in self.labelit_log:
                    jon_summary.write('' + line )            
            else:
                jon_summary.write('---------------LABELIT FAILED---------------\n')
            jon_summary.write('\n')
            jon_summary.write('---------------Peak Picking RESULTS---------------\n')
            jon_summary.write('\n')
            if self.distl_log:
                for line in self.distl_log:
                    jon_summary.write('' + line )
            #Don't write error messages from programs that did not run.
            if self.labelit_results.get('Labelit results') != 'FAILED':
                jon_summary.write('\n')
                jon_summary.write('---------------Raddose RESULTS---------------\n')
                jon_summary.write('\n')                          
                if self.raddose_log:
                    for line in self.raddose_log:
                        jon_summary.write('' + line ) 
                else:
                    jon_summary.write('---------------RADDOSE FAILED---------------\n')  
                jon_summary.write('\n')
                jon_summary.write('\n')
                jon_summary.write('---------------Data Collection Strategy RESULTS---------------\n')
                jon_summary.write('\n')                                                 
                if self.best_log:
                    for line in self.best_log:
                        jon_summary.write('' + line )     
                else:
                    jon_summary.write('---------------BEST FAILED. TRYING MOSFLM STRATEGY---------------\n')
                if self.best_failed or self.strategy == 'mosflm' or self.multicrystalstrat:
                    if self.mosflm_strat_log:
                        jon_summary.write('\n')
                        jon_summary.write('---------------Data Collection Strategy RESULTS from Mosflm---------------\n')
                        jon_summary.write('\n')                                 
                        for line in self.mosflm_strat_log:
                            jon_summary.write('' + line )                                   
                    else:
                        jon_summary.write('---------------MOSFLM STRATEGY FAILED---------------\n') 
                           
                jon_summary.write('\n')
                jon_summary.write('---------------ANOMALOUS Data Collection Strategy RESULTS---------------\n')
                jon_summary.write('\n')                                 
                if self.best_anom_log:                    
                    for line in self.best_anom_log:
                        jon_summary.write('' + line ) 
                else:
                    jon_summary.write('---------------BEST ANOM STRATEGY FAILED. TRYING MOSFLM STRATEGY---------------\n')       
                if self.best_anom_failed or self.strategy == 'mosflm' or self.multicrystalstrat:
                    if self.mosflm_strat_anom_log:
                        jon_summary.write('\n')
                        jon_summary.write('---------------ANOMALOUS Data Collection Strategy RESULTS from Mosflm---------------\n')
                        jon_summary.write('\n')                                 
                        for line in self.mosflm_strat_anom_log:
                            jon_summary.write('' + line )     
                    else:
                        jon_summary.write('---------------MOSFLM ANOM STRATEGY FAILED---------------\n')
            jon_summary.write('            </pre>\n')
            jon_summary.write('          </div>\n')           
            jon_summary.write("      </div>\n")
            jon_summary.write("    </div>\n")
            jon_summary.write("  </body>\n")
            jon_summary.write("</html>\n")
            jon_summary.close()        
            if os.path.exists(file):
                shutil.copy(file,self.working_dir)
                
        except:
            self.logger.exception('**ERROR in htmlSummaryLong**')
           
    def htmlSummaryShort(self):
        """
        Create short summary HTML/php file for autoindex/strategy output results.
        """
        self.logger.debug('AutoindexingStrategy::htmlSummaryShort')
        try:            
            if self.beamline_use:
                file = 'jon_summary_short.php'
            else:
                file = 'jon_summary_short.html'
            jon_summary = open(file,'w')
            if self.beamline_use:
                jon_summary.write("<?php\n")
                jon_summary.write("//prevents caching\n")
                jon_summary.write('header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");\n')
                jon_summary.write('header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");\n')
                jon_summary.write('header("Cache-Control: post-check=0, pre-check=0",false);\n')
                jon_summary.write("session_cache_limiter();\n")
                jon_summary.write("session_start();\n")
                jon_summary.write("require('/var/www/html/rapd/login/config.php');\n")
                jon_summary.write("require('/var/www/html/rapd/login/functions.php');\n")
                jon_summary.write("//prevents unauthorized access\n")
                jon_summary.write('if(allow_user() != "yes")\n')
                jon_summary.write("{\n")
                jon_summary.write('    if(allow_local_data($_SESSION[data]) != "yes")\n')
                jon_summary.write("    {\n")
                jon_summary.write("        include ('./login/no_access.html');\n")
                jon_summary.write("        exit();\n")
                jon_summary.write("    }\n")
                jon_summary.write("}\n")
                jon_summary.write("?>\n\n")
            jon_summary.write('<html>\n')
            jon_summary.write('  <head>\n')
            jon_summary.write('    <style type="text/css" media="screen">\n')
            #jon_summary.write('      @import url("css/rapd.css");\n')
            if self.beamline_use == False:
                jon_summary.write('      @import "../css/ndemo_page.css";\n')
                jon_summary.write('      @import "../css/ndemo_table.css";\n')
            jon_summary.write('    body {\n')
            jon_summary.write('      background-image: none;\n')
            jon_summary.write('    }\n')
            jon_summary.write('    .dataTables_wrapper {position: relative; min-height: 75px; _height: 302px; clear: both;    }\n')
            jon_summary.write('    table.display td {padding: 1px 7px;}\n')    
            jon_summary.write('    </style>\n')
            if self.beamline_use == False:
                jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.js"></script>\n')
                jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.dataTables.js"></script>\n')
            jon_summary.write('    <script type="text/javascript" charset="utf-8">\n')
            jon_summary.write('      $(document).ready(function() {\n')
            if self.auto_summary:
                jon_summary.write("        $('#auto').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bAutoWidth": false    });\n')              
            if self.best_summary:
                jon_summary.write("        normSimpleBestTable = $('#best1').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bAutoWidth": false    });\n')  
            if self.best_anom_summary:
                jon_summary.write("        anomSimpleBestTable = $('#bestanom1').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bAutoWidth": false    });\n')  
            if self.best_failed or self.strategy == 'mosflm':
                if self.mosflm_strat_summary:
                    jon_summary.write("        $('#strat1').dataTable({\n")
                    jon_summary.write('           "bPaginate": false,\n')
                    jon_summary.write('           "bFilter": false,\n')
                    jon_summary.write('           "bInfo": false,\n')
                    jon_summary.write('           "bAutoWidth": false    });\n')  
            if self.best_anom_failed or self.strategy == 'mosflm':
                if self.mosflm_strat_anom_summary:
                    jon_summary.write("        $('#stratanom1').dataTable({\n")
                    jon_summary.write('           "bPaginate": false,\n')
                    jon_summary.write('           "bFilter": false,\n')
                    jon_summary.write('           "bInfo": false,\n')
                    jon_summary.write('           "bAutoWidth": false    });\n')  
            if self.best_summary:
                jon_summary.write('''
                     //Double click handlers for tables
                     $("#best1 tbody tr").dblclick(function(event) {
                            //Get the current data of the clicked-upon row
                            aData = normSimpleBestTable.fnGetData(this);
                            //Parse out the image prefix from the currently selected snap
                            var tmp_repr = image_repr.toString().split("_");
                            var tmp_repr2 = tmp_repr.slice(0,-2).join('_');
                            //Use the values from the line to fill the form
                            $("#image_prefix").val(tmp_repr2);
                            $("#omega_start").val(aData[1]);
                            $("#delta_omega").val(aData[5]);
                            $("#number_images").val(aData[4]);
                            $("#time").val(aData[6]);
                            $("#distance").val(aData[7]);
                            $("#transmission").val(aData[8]);
                            //Open up the dialog form
                            $('#dialog-form-datacollection').dialog('open');
                     }); \n''')
                if self.best_anom_summary:
                    jon_summary.write('''        
                     //Single click handlers  
                     $("#best1 tbody tr").click(function(event) {   
                             $(normSimpleBestTable.fnSettings().aoData).each(function (){ 
                             $(this.nTr).removeClass('row_selected'); 
                         }); 
                         $(anomSimpleBestTable.fnSettings().aoData).each(function (){ 
                             $(this.nTr).removeClass('row_selected'); 
                         }); 
                         $(event.target.parentNode).toggleClass('row_selected'); 
                     }); 
                
                     $("#bestanom1 tbody tr").click(function(event) {
                         $(normSimpleBestTable.fnSettings().aoData).each(function (){
                             $(this.nTr).removeClass('row_selected');
                         });
                         $(anomSimpleBestTable.fnSettings().aoData).each(function (){
                             $(this.nTr).removeClass('row_selected');
                         });
                         $(event.target.parentNode).toggleClass('row_selected');
                     }); \n''')
            if self.best_anom_summary:
                jon_summary.write('''
                     $("#bestanom1 tbody tr").dblclick(function(event) {
                            //Get the current data of the clicked-upon row
                            aData = anomSimpleBestTable.fnGetData(this);
                            //Parse out the image prefix from the currently selected snap
                            var tmp_repr = image_repr.toString().split("_");
                            var tmp_repr2 = tmp_repr.slice(0,-2).join('_');
                            //Use the values from the line to fill the form
                            $("#image_prefix").val(tmp_repr2);
                            $("#omega_start").val(aData[1]);
                            $("#delta_omega").val(aData[5]);
                            $("#number_images").val(aData[4]);
                            $("#time").val(aData[6]);
                            $("#distance").val(aData[7]);
                            $("#transmission").val(aData[8]);
                            //Open up the dialog form
                            $('#dialog-form-datacollection').dialog('open');
                     }); \n''')

            jon_summary.write('''
                 //The dialog form for data collection
                 $("#dialog-form-datacollection").dialog({
                        autoOpen: false,
                        width: 350,
                        modal: true,
                        buttons: {
                            'Send to Beamline': function() {
                                                //POST the data to the php tool
                                                $.ajax({
                                                    type: "POST",
                                                    url: "d_add_datacollection.php",
                                                    data: {prefix:$("#image_prefix").val(),
                                                           run_number:$("#run_number").val(),
                                                           image_start:$("#image_start").val(),
                                                           omega_start:$("#omega_start").val(),
                                                           delta_omega:$("#delta_omega").val(),
                                                           number_images:$("#number_images").val(),
                                                           time:$("#time").val(),
                                                           distance:$("#distance").val(),
                                                           transmission:$("#transmission").val(),
                                                           ip_address:my_ip,
                                                           beamline:my_beamline}
                                                });
                                $(this).dialog('close');
                            },
                            Cancel: function() {
                                $(this).dialog('close');
                            }
                        },
                 }); \n''')
            #The end of the Jquery
            jon_summary.write('      } );\n')
            jon_summary.write("    </script>\n\n\n")
            jon_summary.write(" </head>\n")
            jon_summary.write('  <body id="dt_example">\n')
            jon_summary.write('    <div id="container">\n')
            jon_summary.write('    <div class="full_width big">\n')
            jon_summary.write('      <div id="demo">\n')
            jon_summary.write('        <h1 class="results">Autoindexing summary for:</h1>\n')
            jon_summary.write("      <h2 class='results'>Image: "+self.header.get('fullname')+"</h2>\n") 
            if self.header2:
                jon_summary.write("      <h2 class='results'>Image: "+self.header2.get('fullname')+"</h2>\n")                          
            if self.prev_sg:
                jon_summary.write("      <h4 class='results'>Space group "+self.spacegroup+" selected from previous dataset.</h4>\n")
            else:
                if self.spacegroup != 'None':
                    jon_summary.write("      <h4 class='results'>User chose space group as "+self.spacegroup+"</h4>\n")
                    if self.ignore_user_SG == True:
                        jon_summary.write("      <h4 class='results'>Unit cell not compatible with user chosen SG.</h4>\n")           
            if self.pseudotrans:
                jon_summary.write("      <h4 class='results'>Caution. Labelit suggests the possible presence of pseudotranslation. Look at the log file for more info.</h4>\n")
            if self.auto_summary:
                jon_summary.writelines(self.auto_summary)            
            if self.labelit_results:                 
                if self.labelit_results.get('Labelit results') == 'FAILED':
                    jon_summary.write('    <h3 class="results">Autoindexing FAILED.</h3>\n')
                    if self.blank_image:
                        jon_summary.write('    <h4 class="results">Not enough spots!!</h3>\n')
                    if self.header2:
                        jon_summary.write('    <h4 class="results">Pair of snapshots did not autoindex. Possibly not from same crystal.</h3>\n')
                    else:
                        jon_summary.write('    <h4 class="results">You can add "pair" to the snapshot name and collect one at 0 and 90 degrees. Much better for poor diffraction.</h3>\n')
                        jon_summary.write('    <h4 class="results">eg."snap_pair_99_001.img"</h3>\n')           
                    jon_summary.write("      </div>\n")
                    jon_summary.write("    </div>\n")
                    jon_summary.write("    </div>\n")
            if self.best1_summary:
                jon_summary.writelines(self.best1_summary)                      
            if self.best_results:
                if self.best_results.get('Best results') == 'FAILED':
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('    <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')
                    jon_summary.write('    <h4 class="results">Best Failed. Trying Mosflm strategy.</h3>\n')
                    jon_summary.write("      </div>\n")
                    jon_summary.write("    </div>\n")
                    jon_summary.write("    </div>\n")
            if self.mosflm_strat1_summary:
                jon_summary.writelines(self.mosflm_strat1_summary)          
            if self.mosflm_strat_results:
                if self.mosflm_strat_results.get('Mosflm strategy results') == 'FAILED':
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('    <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')
                    jon_summary.write('    <h3 class="results">Mosflm Strategy Failed. Could not calculate a strategy.</h3>\n')
                    jon_summary.write("      </div>\n")
                    jon_summary.write("    </div>\n")
                    jon_summary.write("    </div>\n")                        
            if self.best1_anom_summary:
                jon_summary.writelines('       <br>\n')
                jon_summary.writelines(self.best1_anom_summary)          
            if self.best_anom_results:
                if self.best_anom_results.get('Best ANOM results') == 'FAILED':
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('    <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')
                    jon_summary.write('    <h4 class="results">Best Failed. Trying Mosflm ANOMALOUS strategy.</h3>\n')
                    jon_summary.write("      </div>\n")
                    jon_summary.write("    </div>\n")
                    jon_summary.write("    </div>\n")
            if self.mosflm_strat1_anom_summary:
                jon_summary.writelines(self.mosflm_strat1_anom_summary)          
            if self.mosflm_strat_anom_results:
                if self.mosflm_strat_anom_results.get('Mosflm ANOM strategy results') == 'FAILED':
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('    <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')
                    jon_summary.write('    <h3 class="results">Mosflm Strategy Failed. Could not calculate an ANOMALOUS strategy.</h3>\n') 
                    jon_summary.write("      </div>\n")
                    jon_summary.write("    </div>\n")
                    jon_summary.write("    </div>\n")    
            jon_summary.write('''
                <div id="dialog-form-datacollection" title="Send Datacollection Parameters to Beamline">
                    <p class="validateTips">All form fields are required.</p>
                    <form id="datacollection-form" method="POST" action="d_add_minikappa.php">
                    <fieldset>
                            <table>
                              <tr>
                                <td>
                                  <label for="image_prefix">Image prefix</label>
                                </td>
                                <td>
                                  <input type="text" name="image_prefix" id="image_prefix" value="" class="text ui-widget-content ui-corner-all" "size=6"/>
                                </td>
                              </tr>
                              <tr>
                                <td>
                                  <label for="run_number">Run number</label>
                                </td>
                                <td>
                                  <input type="text" name="run_number" id="run_number" value="1" class="text ui-widget-content ui-corner-all" "size=6"/>
                                </td>
                              </tr>
                              <tr>
                                <td>
                                  <label for="image_start">First image number</label>
                                </td>
                                <td>
                                  <input type="text" name="image_start" id="image_start" value="1" class="text ui-widget-content ui-corner-all" "size=6"/>
                                </td>
                              </tr>
                              <tr>
                                <td>
                                  <label for="name">Omega start (&deg;)</label>
                                </td>
                                <td>
                                  <input type="text" name="omega_start" id="omega_start" value="" class="text ui-widget-content ui-corner-all" "size=6"/>
                                </td>
                              </tr>
                              <tr>
                                <td>
                                  <label for="delta_omega">Delta omega (&deg;)</label>
                                </td>
                                <td>
                                  <input type="text" name="delta_omega" id="delta_omega" value="" class="text ui-widget-content ui-corner-all" "size=6"/>
                                </td>
                              </tr>
                              <tr>
                                <td>
                                  <label for="number_images">Number of images</label>
                                </td>
                                <td>
                                  <input type="text" name="number_images" id="number_images" value="" class="text ui-widget-content ui-corner-all" "size=6"/>
                                </td>
                              </tr>
                              <tr>
                                <td>
                                  <label for="time">Exposure time (s)</label>
                                </td>
                                <td>
                                  <input type="text" name="time" id="time" value="" class="text ui-widget-content ui-corner-all" "size=6"/>
                                </td>
                              </tr>
                              <tr>
                                <td>
                                  <label for="distance">Distance (mm)</label>
                                </td>
                                <td>
                                  <input type="text" name="distance" id="distance" value="" class="text ui-widget-content ui-corner-all" "size=6"/>
                                </td>
                              </tr>
                              <tr>
                                <td>
                                  <label for="transmission">Transmission (%)</label>
                                </td>
                                <td>
                                  <input type="text" name="transmission" id="transmission" value="" class="text ui-widget-content ui-corner-all" "size=6"/>
                                </td>
                              </tr>
                
                           </table>
                    </fieldset>
                    </form>
                </div> \n
                ''')
            jon_summary.write("  </body>\n")
            jon_summary.write("</html>\n")
            jon_summary.close()
            if os.path.exists(file):
                shutil.copy(file,self.working_dir)
        
        except:
            self.logger.exception('**ERROR in htmlSummaryShort**')
        
    def errorLabelitPost(self,iteration,error,run_before=False):
        """
        Do the logging for the error correction in Lableit.
        """
        self.logger.debug('AutoindexingStrategy::errorLabelitPost')
        try:
            if self.multiproc:                   
                if run_before:
                    self.logger.debug(error)
                    eval('self.labelit_log'+str(iteration)).append(error+'\n')
                    self.labelit_results[str(iteration)] = { 'Labelit results'  : 'FAILED'}
                    #eval('self.labelit_results'+str(iteration)).update({ 'Labelit results'  : 'FAILED'})
                else:                     
                    eval('self.labelit_log'+str(iteration)).append(error+' Retrying Labelit\n')
            else:                    
                if iteration >= 3:                
                    self.logger.debug('After 3 tries, '+error)
                    eval('self.labelit_log'+str(iteration)).append('After 3 tries, '+error+'\n')
                else:
                    iteration += 1
                    back_counter = 4 - iteration
                    self.logger.debug(error+' Retrying Labelit '+str(back_counter)+' more time(s)')                            
                    eval('self.labelit_log'+str(iteration)).append(error+' Retrying Labelit '+str(back_counter)+' more time(s)\n')
        
        except:
            self.logger.exception('**ERROR in errorLabelitPost**')

    def errorLabelit(self,iteration):
        """
        Labelit error correction. Set/reset setting in dataset_preferences.py according to error iteration.
        Commented out things were tried before.
        """
        self.logger.debug('AutoindexingStrategy::errorLabelit')
        try:
            temp = []
            #if in multiproc mode, create separate folders for Labelit runs.
            Utils.foldersLabelit(self,iteration)
            preferences    = open('dataset_preferences.py','a')
            if self.min_spots:
                preferences.write(self.min_spots+'\n')
            preferences.write('\n#iteration '+str(iteration)+'\n')
            if iteration == 1:
                preferences.write('distl.minimum_spot_area=6\n')
                if self.twotheta == False:
                    preferences.write('beam_search_scope=0.3\n')
                preferences.write('distl.minimum_signal_height=4.3\n')
                preferences.close()
                eval('self.labelit_log'+str(iteration)).append('\nLooking for long unit cell.\n')
                self.logger.debug('Looking for long unit cell.')
            elif iteration == 2:
                #Change it up and go for larger peaks like small molecule.
                preferences.write('distl.minimum_spot_height=6\n')
                #preferences.write('distl.minimum_signal_height=5.0\n')
                if self.twotheta == False:
                    preferences.write('beam_search_scope=0.3\n')
                #preferences.write('beam_search_scope=2\n')
                #preferences.write('distl_profile_bumpiness = 7\n')
                preferences.close()
                eval('self.labelit_log'+str(iteration)).append('\nChanging settings to look for stronger peaks (ie. small molecule).\n')
                self.logger.debug('Changing settings to look for stronger peaks (ie. small molecule).')
            elif iteration == 3:
                preferences.write('distl.minimum_spot_area=7\n')
                if self.twotheta == False:
                    preferences.write('beam_search_scope=0.3\n')
                preferences.write('distl.minimum_signal_height=1.2\n')
                preferences.close()
                eval('self.labelit_log'+str(iteration)).append('\nLooking for weak diffraction.\n')
                self.logger.debug('Looking for weak diffraction.')
            elif iteration == 4:
                #preferences.write('distl_aggressive = {"passthru_arguments":"-s3 7 -d1 3.7"}\n')
                preferences.write('distl.minimum_spot_area=8\n')
                if self.twotheta == False:
                    preferences.write('beam_search_scope=0.3\n')
                #preferences.write('distl.minimum_signal_height=5.0\n')
                #preferences.write('distl.minimum_spot_height=4.3\n')
                #preferences.write('beam_search_scope=0.5\n')
                #preferences.write('distl_profile_bumpiness=3\n')                
                preferences.close()
                eval('self.labelit_log'+str(iteration)).append('\nSetting spot picking level to 8.\n')
                self.logger.debug('Setting spot picking level to 8.')
            elif iteration == 5:
                #preferences.write('distl_aggressive = {"passthru_arguments":"-s3 6 -d1 3.7"}\n')
                preferences.write('distl.minimum_spot_area=6\n')
                if self.twotheta == False:
                    preferences.write('beam_search_scope=0.3\n')
                #preferences.write('distl.minimum_signal_height=5.0\n')
                #preferences.write('distl.minimum_spot_height=4.3\n')
                #preferences.write('distl_profile_bumpiness=5\n')
                preferences.close()
                eval('self.labelit_log'+str(iteration)).append('\nSetting spot picking level to 6.\n')
                self.logger.debug('Setting spot picking level to 6.')
                #eval('self.labelit_log' + str(iteration)).append('\nSetting spot bumpiness to 5.\n')
                #self.logger.debug('Setting spot bumpiness to 5.')
            return(self.processLabelit(iteration))
        
        except:
            self.logger.exception('**ERROR in errorLabelit**')
            eval('self.labelit_log'+str(iteration)).append('**ERROR in errorLabelit**\n')
            #return(None)
        
    def errorLabelitMin(self,iteration,line=False):
        """
        Labelit error correction. Reset min spots allowed. Set/reset setting in dataset_preferences.py according
        to error iteration. Only run in multiproc mode.
        """
        self.logger.debug('AutoindexingStrategy::errorLabelitMin')
        try:
            if line:
                spots = int(line.split()[2])
                #Minimum number of spots to define a blank image.
                if spots < 25:
                    self.logger.debug('Not enough spots to autoindex!')
                    eval('self.labelit_log'+str(iteration)).append('\nNot enough spots to autoindex!\n')
                    self.postprocessLabelit(iteration,True,True)
                    return(None)
                else:
                    preferences    = open('dataset_preferences.py','a')
                    preferences.write(line+'\n')
                    preferences.close()
                    return(self.processLabelit(iteration))
                    
        except:
            self.logger.exception('**ERROR in errorLabelitMin**')
            eval('self.labelit_log'+str(iteration)).append('\nCould not change spot finding settings in dataset_preferences.py file.\n')
            return(None)
        
    def errorLabelitFixCell(self,iteration,lg,labelit_sol):
        """
        Pick correct cell if multiple cell choices are possible in user selected SG and rerun Labelit.
        """
        self.logger.debug('AutoindexingStrategy::errorLabelitFixCell')
        try:
            for line in labelit_sol:
                if line[7] == lg:
                    cell = 'known_cell='+line[8]+','+line[9]+','+line[10]+','+line[11]+','+line[12]+','+line[13]
            return(self.processLabelit(iteration,input=cell))
            
        except:
            self.logger.exception('**Error in errorLabelitFixCell**')
            return(None)
    
    def errorLabelitCellSG(self,iteration):
        """
        #Retrying Labelit without using user specified unit cell params.
        """
        self.logger.debug('AutoindexingStrategy::errorLabelitCellSG')
        try:
            self.ignore_user_cell = True
            self.ignore_user_SG = True
            eval('self.labelit_log'+str(iteration)).append('\nIgnoring user cell and SG command and rerunning.\n')
            return (self.processLabelit(iteration))

        except:
            self.logger.exception('**ERROR in errorLabelitCellSG**')
            return(None)
    
    def errorLabelitBump(self,iteration):
        """
        Get rid of distl_profile_bumpiness line in dataset_preferences.py. Don't think I use much anyway.
        """
        self.logger.debug('AutoindexingStrategy::errorLabelitBump')
        try:
            temp1 = []
            preferences    = open('dataset_preferences.py','r')                                    
            for line in preferences:
                temp1.append(line)
                if line.startswith('distl_profile_bumpiness'):
                    temp1.remove(line)
            preferences.close()
            preferences = open('dataset_preferences.py','w')
            preferences.writelines(temp1)
            preferences.close()
            return (self.processLabelit(iteration))
                    
        except:
            self.logger.exception('**ERROR in errorLabelitBump**')
            eval('self.labelit_log'+str(iteration)).append('\nCould not remove distl_profile_bumpiness line in dataset_preferences.py file.\n')
            return(None)
        
    def errorLabelitGoodSpots(self,iteration):
        """
        Sometimes Labelit gives an eror saying that there aren't enough 'good spots' for Mosflm. Not a Labelit
        failure error. Forces Labelit/Mosflm to give result regardless. Sometimes causes failed index.
        """        
        self.logger.debug('AutoindexingStrategy::errorLabelitGoodSpots')
        try:
            Utils.foldersLabelit(self,iteration)
            preferences    = open('dataset_preferences.py','a')
            self.logger.debug('Changing preferences to allow less spots for autoindexing')
            if self.min_good_spots:
                preferences.write('\n#iteration '+str(iteration)+'\n')
                preferences.write('model_refinement_minimum_N='+str(self.min_good_spots))
                preferences.close()
                eval('self.labelit_log'+str(iteration)).append('\nSetting min number of good bragg spots to '+str(self.min_good_spots)+'.\n')
                self.logger.debug('Setting min number of good bragg spots to '+str(self.min_good_spots))
                return (self.processLabelit(iteration))
            else:
                return(None)
                
        except:
            self.logger.exception('**ERROR in errorLabelitGoodSpots**')
            eval('self.labelit_log'+str(iteration)).append('\nCould not change min number of good bragg spots settings in dataset_preferences.py file.\n')
            return(None)
    
    def errorLabelitMosflm(self,iteration):
        """
        Set Mosflm integration resolution lower. Seems to fix this error.
        """
        self.logger.debug('AutoindexingStrategy::errorLabelitMosflm')
        try:
            temp = []
            Utils.foldersLabelit(self,iteration)
            #'index01' will always be present since it is P1
            orig = open('index01','r')
            preferences = open('dataset_preferences.py','a')
            for line in orig:
                temp.append(line)
                if line.startswith('RESOLUTION'):
                    index = temp.index(line)
                    current_res = line.split()[1]
                    preferences.write('\n#iteration '+str(iteration)+'\n')
                    if iteration == 0:
                        new_res = float(current_res)+0.50
                    if iteration == 1:
                        new_res = float(current_res)+1.00
                    if iteration == 2:
                        new_res = float(current_res)+2.00
                    if iteration == 3:
                        new_res = float(current_res)+4.00    
                    preferences.write('mosflm_integration_reslimit_override = '+str(new_res)+'\n')
                    eval('self.labelit_log'+str(iteration)).append('\nDecreasing integration resolution to '+str(new_res)+' and rerunning.\n')
            orig.close()
            preferences.close()
            return (self.processLabelit(iteration))
            
        except:
            self.logger.exception('**ERROR in errorLabelitMosflm**')
            eval('self.labelit_log'+str(iteration)).append('\nCould not reset Mosflm resolution.\n')
            return(None)
         
    def errorBest(self,iteration,anom=False):
        """
        When Best fails, resets resolution in Mosflm (and rerun) before rerunning Best.
        """        
        self.logger.debug('AutoindexingStrategy::errorBest')
        try:
            temp = []
            file      = str(self.index_number)+'_res'
            copy  = 'cp '+str(self.index_number)+' '+file
            self.logger.debug(copy)
            os.system(copy)
            orig = open(file,'r')
            for line in orig:
                temp.append(line)
                if line.startswith('RESOLUTION'): 
                    index = temp.index(line)
                    current_res = line.split()[1]
                    if iteration == 1:
                        new_res     = float(current_res)+0.50
                    if iteration == 2:
                        new_res     = float(current_res)+1.00
                    if iteration == 3:
                        new_res     = float(current_res)+2.00
                    new_line    = 'RESOLUTION '+str(new_res)+'\n'
                    temp.remove(line)
                    temp.append(new_line)
            orig.close()
            new = open(file,'w')
            new.writelines(temp)
            new.close()
            state = '\nDecreasing resolution to '+str(new_res)+'.\n'
            if anom:
                self.best_anom_log.append(state)
            else:
                self.best_log.append(state)
            command = 'sh '+str(self.index_number)+'_res'
            self.logger.debug(command)
            os.system(command)
            
        except:
            self.logger.exception('**ERROR in errorBest**')
            self.best_log.append('\nCould not reset Mosflm resolution for Best.\n')
    
    def errorBestPost(self,iteration,error,anom=False):
        """
        Post error to proper log in postprocessBest.
        """
        try:
            if anom:                
                j  = ' ANOM'
                j1 = '_anom'
            else:
                anom = False
                j  = ''
                j1 = ''        
            self.logger.debug(error)    
            if iteration >= 3:
                self.logger.debug('After 3 tries, Best '+j+' failed. Will run Mosflm'+j+' strategy')
                self.logger.debug('Trying Mosflm '+j+' strategy.')
                eval('self.best'+j1+'_log').append('\nAfter 3 tries, Best'+j+' failed. Will run Mosflm'+j+' strategy\n')
                self.mosflm_jobs = self.processMosflm(anom)
                self.Queue('mosflm')
            else:
                iteration += 1
                back_counter = 4 - iteration
                self.logger.debug('Error in Best '+j+' strategy. Retrying Best '+str(back_counter)+' more time(s)')
                eval('self.best'+j1+'_log').append('\nError in Best '+j+' strategy. Retrying Best ' +  str(back_counter) + ' more time(s)\n')
                self.errorBest(iteration,anom)
                return(self.processBest(iteration,anom))        
        
        except:
            logger.exception('**Error in errorBestPost**')
        
def makeImagesAction(input,output,logger,multi=True):
    """
    Take input   = ([images],predictions)
         output  = multiprocessing.Queue
    Create vips pyramidal tiled tiffs using labelit and vips
    Return the full path filenames
    """
    logger.debug('makeImagesAction')
    try:    
        src_images,predictions = input
        list = []    
        if predictions == 0:
            labelit = 'labelit.png -large '
        elif predictions == 1:
            labelit = 'labelit.overlay_index -large '
        else:
            labelit = 'labelit.overlay_distl -large '
        for image in src_images:
            if predictions == 0:
                png_image1 = os.path.basename(image).replace('.img','.png')
            else:
                png_image1 = os.path.basename(image).replace('.img','_overlay.png')
            tif_image1 = png_image1.replace('.png','.tif')
            command = labelit+image+' '+png_image1+'; vips im_vips2tiff '+png_image1+' '+tif_image1+':jpeg:100,tile:192x192,pyramid; rm -rf '+png_image1
            logger.debug(command)
            myoutput = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            if multi == False:
                log = []
                for line in myoutput.stdout:
                    log.append(line)
            output.put(tif_image1)
            output.put(myoutput.pid)
    except:
        logger.exception('**Error in makeImagesAction**')
            
def LabelitAction(input,output,iteration,logger):
    """
    Running Labelit and put results into 'labelit.log' since subprocess stdout has bug and hangs process.
    """
    logger.debug('LabelitAction')
    try:    
        
        file = open('labelit.log','w')
        myoutput = subprocess.Popen(input,shell=True,stdout=file,stderr=file)
        output.put(myoutput.pid)
        file.close()
        """
        temp = []
        myoutput = subprocess.Popen(input,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        output.put(myoutput.pid)
        for line in myoutput.stdout:
            temp.append(line)
        output2.put(temp)
        """
    except:
        logger.exception('**Error in LabelitAction**')
    
def DistlAction(input,output,logger):
    """
    Get Distl stats for all images used to index at same time. Puts results in 'distl.txt' because of bug in 
    subprocess and stdout.
    """
    logger.debug('DistlAction')
    try:
        for x in range(len(input)):
            junk = open('distl'+str(x)+'.txt','w')
            command = 'distl.signal_strength '+input[x]
            logger.debug(command)
            myoutput = subprocess.Popen(command,shell=True,stdout=junk,stderr=junk)
            junk.close()
            output.put(myoutput.pid)
            
    except:
        logger.exception('**Error in DistlAction**')

def BestAction(input,output,anomalous,logger):
    """
    Run Best.
    """
    logger.debug('BestAction')
    try:
        if anomalous:
            file = open('best_anom.txt','w')
        else:
            file  = open('best.txt','w')
        file.write(input+'\n\n')
        myoutput  = subprocess.Popen(input,shell=True,stdout=file,stderr=file)
        file.close()
        output.put(myoutput.pid)
        """
        temp = []
        myoutput = subprocess.Popen(input,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        for line in myoutput.stdout:
            temp.append(line)
        output.put(myoutput.pid)
        output2.put(temp)
        """
    except:
        logger.exception('**Error in BestAction**')
    
def MosflmAction(input,output,logger):
    """
    Run Mosflm strategy.
    """
    logger.debug('MosflmAction')
    try:
        command = 'tcsh '+input
        myoutput = subprocess.Popen(command,shell=True)
        output.put(myoutput.pid)    
    except:
       logger.exception('**Error in MosflmAction**')

if __name__ == '__main__':
    #start logging
    #LOG_FILENAME = '/home/schuerjp/Data_processing/Frank/Output/rapd_jon.log'
    LOG_FILENAME = '/tmp/rapd_agent_strategy.log'
    # Set up a specific logger with our desired output level
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,maxBytes=100000,backupCount=5)
    #add a formatter
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('AutoindexingStrategy.__init__')   
    #construct test input    
    import ../test_data/rapd_auto_testinput as Input
    input = Input.input()
    tmp = AutoindexingStrategy(input,logger=logger)
    

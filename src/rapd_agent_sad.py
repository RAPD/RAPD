'''
__author__ = "Jon Schuermann, Frank Murphy"
__copyright__ = "Copyright 2010,2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2010/09/07"
'''

import multiprocessing
import os
import sys
import subprocess
import time
import shutil
import numpy
import logging,logging.handlers

from rapd_agent_cell import PDBQuery
from rapd_communicate import Communicate
import rapd_agent_utilities as Utils
import rapd_agent_parse as Parse
import rapd_agent_summary as Summary

class AutoSolve(multiprocessing.Process,Communicate):
    def __init__(self,input,logger=None):
        logger.info('AutoSolve.__init__')
        self.st = time.time()
        self.input                              = input
        self.logger                             = logger
        self.setup                              = self.input[1]
        self.data                               = self.input[2]        
        self.preferences                        = self.input[3]
        self.controller_address                 = self.input[-1]
        
        #For testing individual modules
        self.test                               = False
        #Removes junk files and directories at end.
        self.clean                              = False
        #For running multiple ShelxD jobs in parallel like SGXPRO.
        self.multiShelxD                        = True
        #Set to allow AutoSol to run on solution
        self.build                              = True
        #Set to make ShelxE run autotracing
        self.shelx_build                        = True
        #Set to run Phaser on possible structures.
        self.phaser                             = False
        #Set to calc ADF from Phaser results
        self.adf                                = True
               
        #variables to set
        self.autosol_timer                      = False
        self.autosol_log                        = []
        self.autosol_output                     = False
        self.autosol_output_inv                 = False
        self.autosol_results                    = False
        self.autosol_failed                     = False
        self.autosol_summary                    = False
        self.autobuild_timer                    = False
        self.autobuild_log                      = []
        self.autobuild_output                   = False
        self.autobuild_results                  = False
        self.autobuild_failed                   = False
        self.autobuild_summary                  = False
        self.pdbquery_timer                     = 20
        self.pdbquery_timer2                    = 60
        self.phaser_timer                       = False
        self.phaser_log                         = []
        self.phaser_output                      = False
        self.phaser_results                     = {}
        self.phaser_failed                      = False
        self.phaser_summary                     = False
        self.pdb                                = False
        self.mtz                                = False
        self.shelx_timer                        = False
        self.shelx_log0                         = {}
        self.shelx_log                          = []
        self.shelxe_queue                       = {}
        self.shelx_results0                     = {}
        self.shelx_results                      = False
        self.shelx_sg                           = False        
        self.shelxc_summary                     = False
        self.shelxd_summary                     = False
        self.shelxe_summary                     = False
        self.cell_summary                       = False
        self.pdb_summary                        = False
        self.percent                            = False
        self.tooltips                           = False
        self.shelxd_dict                        = {}
        self.shelx_plot                         = False
        self.shelx_nosol                        = False
        self.shelx_failed                       = False
        self.shelxd_failed                      = False
        self.cellA                              = False
        self.cell_output                        = {}
        self.cellAnalysis_results               = False
        self.cellJ                              = False
        self.cellJobs                           = {}
        self.both_hands                         = False
        self.pp                                 = False
        self.cell                               = False
        self.cell2                              = False
        self.space_group                        = False
        self.ha                                 = False
        self.ha_num                             = False
        self.ha_num1                            = False
        self.ha_num2                            = False
        self.solvent_content                    = False       
        self.incompatible_cell                  = False
        self.input_sg                           = False
        self.wave                               = False
        self.anom_signal                        = True
        self.cubic                              = False
        self.many_sites                         = False
        self.njobs                              = 1
        self.iteration                          = 0
        """
        self.sca = self.preferences.get('request').get('input_sca')            
        if os.path.exists(self.sca) == False:
            self.sca = self.data.get('original').get('mtz_file')
        """
        self.datafile = self.data.get('original').get('mtz_file')
        self.solvent_content  = self.preferences.get('solvent_content')
        self.sample_type = self.preferences.get('sample_type')
        self.space_group = self.preferences.get('spacegroup')
        self.solvent_content  = self.preferences.get('solvent_content')
        self.wave = self.preferences.get('request').get('wavelength')     
        self.ha  = self.preferences.get('request').get('ha_type')
        self.ha_num = self.preferences.get('request').get('ha_number')
        self.shelxd_try = self.preferences.get('request').get('shelxd_try')
        self.resolution = self.preferences.get('request').get('sad_res')
        self.nproc = multiprocessing.cpu_count()      
                 
        if self.preferences.get('request').get('input_map') == None:
            self.autobuild = False
        else:
            self.autobuild = True
        #Check if running from beamline and turn off testing if I forgot to.
        if self.preferences.get('request').has_key('request_type'):
            self.gui       = True
            self.test      = False
        else:
            self.gui       = False
        
        #******BEAMLINE SPECIFIC*****
        #host = os.uname()[1]
        type1 = os.uname()[4]
        if type1 == 'x86_64':
            self.cluster_use                = True
        else:
            self.cluster_use                = False
        #******BEAMLINE SPECIFIC*****
        
        multiprocessing.Process.__init__(self,name='AutoSolve')
        self.start()
        
    def run(self):
        """
        Convoluted path of modules to run.
        """
        self.logger.debug('AutoSolve::run')
        self.preprocess()
        if self.autobuild:
            self.processAutoBuild()
            self.postprocessAutoBuild()
        else:
            self.preprocessShelx()
            self.postprocess(False)
            if self.build:
                if self.shelx_nosol == False:
                    if self.shelx_build == False:
                        self.processAutoSol()
                    self.postprocessAutoSol()
            
        self.postprocess()
        
    def preprocess(self):
        """
        Things to do before the main process runs
        1. Change to the correct directory
        2. Print out the reference for SAD pipeline
        """       
        self.logger.debug('AutoSolve::preprocess')
        #change directory to the one specified in the incoming dict
        self.working_dir = self.setup.get('work')
        if os.path.exists(self.working_dir) == False:
            os.makedirs(self.working_dir)
        os.chdir(self.working_dir)
        #print out recognition of the program being used
        self.PrintInfo()
        if self.test:
            self.logger.debug('TEST IS SET "ON"')
        
    def preprocessShelx(self):
        """
        Create SHELX CDE input.
        """
        self.logger.debug('AutoSolve::preprocessShelx')
        try:        
            junk = []
            junk2 = []
            #Get unit cell and SG info
            Utils.getInfoCellSG(self)
            #Calculate cell volume to see if it is ribosome and turn off ShelxE building.
            Utils.checkVolume(self,Utils.calcVolume(self))
            if self.sample_type == 'Ribosome':
                self.shelx_build = False
            #Check data type
            file_type = self.datafile[-3:]
            if file_type == 'mtz':                
                Utils.mtz2sca(self)
            #Get rid of spaces in the sca file SG and *'s.
            Utils.fixSCA(self)
            #Check to see if anomalous signal present
            if self.gui:
                #self.anom_signal = Utils.checkAnom(self)
                pass            
            if self.anom_signal:
                #get shelxd_ntry if user changed it.
                if self.shelxd_try == 0:
                    self.shelxd_try = 960                
                
                #Check if SG is cubic.
                con = Utils.convertSG(self,self.input_sg)
                try:
                    if int(con) >= 196:
                        self.cubic = True
                except:
                    pass
                
                #Figure out which SG's to Run Shelx and do it.
                run_sg = Utils.subGroups(self,Utils.convertSG(self,self.input_sg),'shelx')
                jobs = {}
                sg_name = []
                if self.multiShelxD:
                    n = len(run_sg)
                    if self.cluster_use:
                        #Using the shelxd_mp64 the number of tries should be a multiple of 16.
                        self.njobs = self.shelxd_try/64
                        """
                        #OLD WAY: Get longest cell dimension
                        for line in self.cell2[:3]:
                            junk2.append(float(line))
                        long = max(junk2)
                        if long > 300:
                            self.njobs = self.shelxd_try/10
                        else:
                            if long > 150:
                                #With HT turned on tests showed 20-30tries/node is sweet spot for ProK.
                                self.njobs = self.shelxd_try/20
                            else:
                                self.njobs = self.shelxd_try/30
                        """
                        #Not to overload the 256 node cluster when someone tries 10000 trials in P422.
                        tot_jobs = self.njobs*n
                        if tot_jobs > 248:
                            self.njobs = 248/n
                        if self.njobs < 1:
                            self.njobs = 1                        
                    else:
                        self.njobs = self.nproc/n
                        if self.njobs == 0:
                            self.njobs = 1
                else:
                    self.njobs = 1
                if self.test:
                    for sg in run_sg:
                        sg2 = Utils.convertSG(self,sg,True)
                        sg_name.append(sg2)
                        Utils.folders(self,'Shelx_'+sg2)
                        self.processShelxCD(sg2)
                        if self.multiShelxD:
                            self.sortShelxD()
                        #self.postprocessShelx(sg2)
                        self.postprocessShelx(sg2,'all')
                        self.postprocessShelx(sg2)
                    if self.phaser:
                        self.processPDBQuery()
                        try:
                            self.cell_output = self.cellA.get()
                        except:
                            self.logger.debug('Could not read self.cellA.get()')
                            self.cell_output = self.cellA
                        if self.cell_output.keys() != ['None']:
                            self.cellJobs = self.cellJ.get()
                            for line in self.cell_output.keys():
                                self.postprocessPhaser(line)
                else:            
                    for sg in run_sg:
                        sg2 = Utils.convertSG(self,sg,True)
                        sg_name.append(sg2)
                        Utils.folders(self,'Shelx_'+sg2)
                        #Remove the ShelxE logs from the previous run if there was an error.
                        if os.path.exists('shelxe.log'):
                            os.system('rm -rf shelxe*')
                        jobs[sg2] = self.processShelxCD(sg2)
                    #Check to see if similar unit cells deposited in PDB
                    if self.phaser:
                        self.processPDBQuery()
                    if self.shelxd_failed == True:
                        self.shelxd_failed = False
                        self.shelx_build = False
                    self.shelxQueue(jobs)
                    if self.shelxd_failed == True:
                        if self.iteration <= 1:
                            self.iteration += 1
                            self.preprocessShelx()
                    if self.phaser:
                        try:
                            self.cell_output = self.cellA.get()
                        except:
                            self.logger.debug('Could not read self.cellA.get()')
                            self.cell_output = self.cellA
                        if self.cell_output.keys() != ['None']:
                            self.phaserQueue()
                self.sortShelx(sg_name)
                
            else:
                if self.phaser:
                    self.processPDBQuery()
                    try:
                        self.cell_output = self.cellA.get()
                    except:
                        self.logger.debug('Could not read self.cellA.get()')
                        self.cell_output = self.cellA
                    if self.cell_output.keys() != ['None']:
                        self.phaserQueue()
                self.shelx_failed = True
                self.shelx_nosol = True
          
        except:
            self.logger.exception('***ERROR in preprocessShelx**')
           
    def processPDBQuery(self):
        """
        Prepare and run PDBQuery.
        """
        self.logger.debug('AutoSolve::processPDBQuery')
        try:      
            mtz = self.data.get('original').get('mtz_file')
            pdb_input = []
            pdb_dict = {}
            pdb_dict['cell'] = self.cell2
            pdb_dict['dir'] = self.working_dir
            pdb_dict['data'] = mtz
            pdb_dict['test'] = self.test
            pdb_dict['type'] = self.sample_type
            pdb_dict['cluster'] = self.cluster_use
            pdb_dict['timer'] = self.pdbquery_timer
            pdb_dict['sc'] = str(self.solvent_content).zfill(3)
            pdb_dict['queue'] = False
            pdb_dict['gui'] = self.gui
            pdb_dict['passback'] = False
            pdb_input.append(pdb_dict)
            junk           = multiprocessing.Queue()
            self.cellA     = multiprocessing.Queue()
            self.cellJ     = multiprocessing.Queue()            
            args1 = {}
            args1['input']   = pdb_input
            args1['output0'] = junk
            args1['output1'] = self.cellA
            args1['output2'] = self.cellJ
            args1['logger']  = self.logger
            self.CELLANALYSIS = multiprocessing.Process(target=PDBQuery,kwargs=args1).start()
            self.percent = junk.get()
        
        except:
            self.logger.exception('**Could not check if other pdbs with similar cells were found**')
            self.cellA['None'] = 'None'
                
    def processAutoSol(self):
        """
        Preparing and starting phenix.autosol
        """
        self.logger.debug('AutoSolve::processAutoSol')
        try:
            resi = False
            command_inv = False
            if self.autosol_log == False:
                self.autosol_log = []
            seq = self.preferences.get('request').get('sequence')
            inv = self.shelx_results.get('Shelx results').get('shelxe_inv_sites')
            
            #Fix SG if H3/H32 is indicated
            sg = Utils.fixSG(self,self.shelx_sg)
                        
            #need path for sites files
            path  = os.path.join(os.getcwd(),'junk.ha')
            ipath = os.path.join(os.getcwd(),'junk_i.ha')
            
            command = 'phenix.autosol data='+self.datafile+' atom_type='+self.ha+' have_hand=True'+\
                      ' lambda='+str(self.wave)+' solvent_fraction='+str(self.solvent_content)+' space_group='+sg+\
                      ' quick=True nproc='+str(self.nproc)+' ncycle_refine=1'
            if self.sample_type == 'Ribosome':
                command += ' chain_type=RNA'
            else:
                command += ' chain_type='+self.sample_type
            if self.ha == 'Se':
                command += ' semet=True'
            if seq == '':
                resi = Utils.calcResNumber(self,self.shelx_sg,False)
                command += ' residues='+str(resi)
            else:
                command += ' sequence="'+seq+'"'            
            if self.both_hands == False:
                if inv == 'True':
                    command += ' sites='+self.ha_num2
                    command += ' sites_file='+ipath
                else:
                    command += ' sites='+self.ha_num1
                    command += ' sites_file='+path
            else:            
                command_inv = command
                command += ' sites='+self.ha_num1
                command += ' sites_file='+path
                command_inv += ' sites='+self.ha_num2
                command_inv += ' sites_file='+ipath
            self.autosol_log.append(command)
            self.logger.debug(command)            
            if self.test:
                print command
                if command_inv:
                    print command_inv            
            else:
                Utils.folders(self,'AutoSol_1')
                self.autosol_output = multiprocessing.Queue()               
                job = multiprocessing.Process(target=multiAutoSolAction(input=command,output=self.autosol_output,logger=self.logger)).start()                
                if self.both_hands:
                    Utils.folders(self,'AutoSol_2')
                    self.autosol_log.append(command_inv)
                    self.logger.debug(command_inv)
                    self.autosol_output_inv = multiprocessing.Queue()
                    job2 = multiprocessing.Process(target=multiAutoSolAction(input=command_inv,output=self.autosol_output_inv,logger=self.logger)).start()
                             
        except:
            self.logger.exception('**ERROR in processAutoSol**')
              
    def processAutoBuild(self):
        """
        Preparing and starting phenix.autobuild
        """
        self.logger.debug('AutoSolve::processAutoBuild')
        try:
            if self.autobuild_log == False:
                self.autobuild_log = []
            map = self.preferences.get('request').get('input_map')
            seq = self.preferences.get('request').get('sequence')
            command = 'phenix.autobuild data='+self.datafile+' map_file='+map+\
                          ' solvent_fraction='+str(self.solvent_content)+' chain_type='+self.sample_type+' sequence="'+seq+'"'\
                          ' number_of_parallel_models=1 n_cycle_build_max=1 n_cycle_rebuild_max=0 ncycle_refine=1 nproc=4'
            self.autobuild_log.append(command)
            self.logger.debug(command)
            if self.test:
                print command
            else:
                self.autobuild_output = multiprocessing.Queue()
                job = multiprocessing.Process(target=multiAutoBuildAction(input=command,output=self.autobuild_output,logger=self.logger)).start()
        
        except:
            self.logger.exception('**ERROR in processAutoBuild**')

    def processShelxCD(self,input):
        """
        Run SHELX CD for input SG.
        """
        self.logger.debug('AutoSolve::processShelxCD')
        try: 
            self.shelx_log0[input] = []
            pid = []
            #If user does not change preferences, I will calc the number of Se sites.
            if self.ha_num == 1 and self.ha == 'Se':
                self.ha_num = Utils.calcResNumber(self,input,True)
            #Based on original inputs but may catch mistakes still.
            if self.ha_num == 0:
                self.ha_num = 1
                if self.ha == 'None':
                    self.ha  = 'Se'
                    self.ha_num = Utils.calcResNumber(self,input,True)
            #Signal Utils.changeIns to modify INS file to find sites faster
            if self.ha_num > 30:
                self.many_sites = True
            #copy sca file to local directory so path isn't too long for SHELX
            sca = os.path.basename(self.datafile)
            shutil.copy(self.datafile,sca)
            command  = 'shelxc junk <<EOF\n'
            command += 'CELL '+self.cell+'\n'
            if float(self.resolution) != 0.0:
                command += 'SHEL 999 '+str(self.resolution)+'\n'
            command += 'SPAG '+str(input)+'\n'
            command += 'SAD ' +sca+'\n'
            command += 'FIND '+str(self.ha_num)+'\n'
            command += 'SFAC '+self.ha+'\n'
            command += 'EOF\n'
            self.shelx_log0[input].append(command+'\n')
            output0 = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            temp = []
            for line in output0.stdout:
                self.shelx_log0[input].append(line)
                temp.append(line)            
            #TESTING function
            if self.test:    
                #Utils.changeIns(self)
                pass
            else:
                if self.multiShelxD:
                    Utils.changeIns(self)
                    shelxd = {}
                    for i in range(0,self.njobs):
                        if os.path.exists('junk_fa.ins'):
                            cp1 = 'cp junk_fa.ins junk_fa'+str(i)+'.ins'
                            os.system(cp1)
                        if os.path.exists('junk_fa.hkl'):
                            cp2 = 'cp junk_fa.hkl junk_fa'+str(i)+'.hkl'
                            os.system(cp2)
                        if self.cluster_use:
                            if self.shelxd_failed == True:
                                command1 = 'shelxd_mp64 -L5 junk_fa'+str(i)
                            else:
                                command1 = 'shelxd_mp64 junk_fa'+str(i)
                            pid.append(Utils.processCluster(self,command1))
                        else:   
                            command1 = 'shelxd junk_fa'+str(i)
                            shelxd[i] = multiprocessing.Queue()                
                            job = multiprocessing.Process(target=multiShelxDAction(input=command1,output=shelxd[i],int=str(i),logger=self.logger)).start()
                            pid.append((shelxd[i]).get())
                        self.logger.debug(command1)
                else:
                    command1 = 'shelxd junk_fa\n'        
                    self.logger.debug(command1)            
                    self.shelx_log0[input].append(command1+'\n')                
                    shelxd = multiprocessing.Queue()
                    job = multiprocessing.Process(target=multiShelxDAction(input=command1,output=shelxd,int='-1',logger=self.logger)).start()
                    pid.append(shelxd.get())
                return(pid)
                                                               
        except:
            self.logger.exception('**Error in processShelxCD**')
           
    def processShelxE(self,input):
        """
        Run SHELX CDE for input SG.
        """
        self.logger.debug('AutoSolve::processShelxE')
        try:
            sc  = self.preferences.get('solvent_content')
            e_queue = {}
            command  = 'shelxe junk junk_fa -s'+str(sc)+' -m20 -h -b'
            if self.shelx_build:
                end = 5
            else:
                end = 3
            for i in range(1,end):
                if i == 1:
                    j = ''
                elif i == 2:
                    j = ' -i'
                elif i == 3:
                    j = ' -a1 -q'
                else:
                    j = ' -i -a1 -q'
                command1 = command+j
                self.shelx_log0[input].append(command1+'\n')
                if self.test:
                    print command1
                    e_queue[input+'_'+str(i)] = '1111'                
                else:        
                    if self.cluster_use:
                        e_queue[input+'_'+str(i)] = Utils.processCluster(self,command1)
                    else:
                        queue = multiprocessing.Queue()
                        job = multiprocessing.Process(target=multiShelxEAction(input=command1,output=queue,logger=self.logger,invert=i)).start()
                        e_queue[input+'_'+str(i)] = queue.get()                
            return(e_queue)
                       
        except:
            self.logger.exception('**Error in preprocessShelx**')
        
    def postprocessShelx(self,input,auto=None):
        """
        Read and process parsed Shelx output.
        """
        self.logger.debug('AutoSolve::postprocessShelx')
        try:
            fa = []
            temp = []
            tempe = []
            loge = False
            Utils.folders(self,'Shelx_'+input)
            temp.extend(self.shelx_log0[input])
            if self.multiShelxD:
                for i in range(0,self.njobs):
                    readlog = open('shelx'+str(i)+'.log','r')
                    for line in readlog:
                        if i == 0:                            
                            self.shelx_log0[input].append(line)
                        temp.append(line)
                    readlog.close()
                self.shelx_log0[input].append('---------------Just showing part of SHELXD Results---------------\n\n')                    
            else:
                readlog = open('shelx.log','r')
                for line in readlog:
                    temp.append(line)
                readlog.close()
            if self.test:
                if os.path.exists('shelxe.log') == False:
                    os.system('touch shelxe.log')
                if os.path.exists('shelxe_i.log') == False:
                    os.system('touch shelxe_i.log')
                if os.path.exists('shelxe_trace.log') == False:
                    os.system('touch shelxe_trace.log')
                if os.path.exists('shelxe_i_trace.log') == False:
                    os.system('touch shelxe_i_trace.log')            
            if self.shelx_build:
                if auto == None:
                    reade   = open('shelxe_trace.log','r')
                    readei  = open('shelxe_i_trace.log','r')
                elif auto == 'inv':
                    reade   = open('shelxe_trace.log','r')
                    readei  = open('shelxe_i.log','r')
                elif auto == 'ninv':
                    reade   = open('shelxe.log','r')
                    readei  = open('shelxe_i_trace.log','r')
                else:
                    reade   = open('shelxe.log','r')
                    readei  = open('shelxe_i.log','r')
            else:
                reade   = open('shelxe.log','r')
                readei  = open('shelxe_i.log','r')
            if os.path.exists('junk_fa.res'):
                fa_file = open('junk_fa.res','r')
                for line in fa_file:
                    fa.append(line)
                fa_file.close()
                for line in reade:
                    temp.append(line)
                    tempe.append(line)
                for line in readei:
                    temp.append(line)
                    tempe.append(line)
            reade.close()
            readei.close()
                            
        except:
            self.logger.exception('**Error in postprocessShelx**')
        
        shelx = Parse.ParseOutputShelx(self,temp,fa)
        if shelx == None:
            self.shelx_results0[input] = { 'Shelx results'  : 'FAILED'}
            self.shelx_failed = True
            self.clean = False
        elif shelx == 'array':
            self.shelxd_failed = True
            return('kill')
        elif shelx == 'trace failed inv':
            self.postprocessShelx(input,'inv')
        elif shelx == 'trace failed ninv':
            self.postprocessShelx(input,'ninv')
        elif shelx == 'trace failed both':
            self.postprocessShelx(input,'both')
        else:
            self.shelx_results0[input] = { 'Shelx results'  : shelx    }
            Utils.convertShelxFiles(self,input)
            if self.shelx_build:
                if auto == None:
                    loge = True
            else:
                loge = True
        if loge:
            for line in tempe:
                self.shelx_log0[input].append(line)
    
    def postprocessAutoSol(self):
        """
        Queue for running autosol for both hands and saving results.
        """
        self.logger.debug('AutoSolve::postprocessAutoSol')
        try:
            timer = 0
            if self.test == False:
                pid = self.autosol_output.get()
                while Utils.stillRunning(self,pid):    
                    print 'Waiting for AutoSol to finish '+str(timer)+' seconds'
                    time.sleep(30)
                    timer += 30
                    if self.autosol_timer:
                        if timer >= self.autosol_timer:
                            Utils.killChildren(self,pid)
                            print 'phenix.autosol timed out.'   
                            self.logger.debug('phenix.autosol timed out.')                   
                            self.autosol_log.append('phenix.autosol timed out\n')
                            break
            #For testing
            else:
                self.both_hands = True
            Utils.folders(self,'AutoSol_1')
            readlog = open('autosol.log','r')
            for line in readlog:
                self.autosol_log.append(line)
            readlog.close()
            autosol = Parse.ParseOutputAutoSol(self,self.autosol_log)
            if self.both_hands == False:
                if autosol['bayes-cc'] == 'ERROR':
                    self.autosol_results = { 'AutoSol results'     : 'FAILED'}
                    self.autosol_failed = True
                else:
                    self.autosol_results = { 'AutoSol results'     : autosol    }
            else:
                if self.test == False:
                    pid2 = self.autosol_output_inv.get()
                    while Utils.stillRunning(self,pid2):    
                        print 'Waiting for AutoSol to finish '+str(timer)+' seconds'
                        time.sleep(30)
                        timer += 30
                        if self.autosol_timer:
                            if timer >= self.autosol_timer:
                                Utils.killChildren(self,pid2)
                                print 'phenix.autosol timed out.'   
                                self.logger.debug('phenix.autosol timed out.')                   
                                self.autosol_log.append('phenix.autosol timed out\n')
                                break
                log = []
                Utils.folders(self,'AutoSol_2')
                readlog2 = open('autosol.log','r')
                self.autosol_log.append('\n------------------Inverse-Hand------------------\n')
                #self.logger.debug('\n------------------Inverse-Hand------------------\n')
                for line in readlog2:
                    log.append(line)                
                    self.autosol_log.append(line)
                readlog2.close()
                autosol2 = Parse.ParseOutputAutoSol(self,log)
                if autosol['bayes-cc'] == 'ERROR':
                    bcc1 = 0.0
                    if autosol2['bayes-cc'] == 'ERROR':
                        self.autosol_results = { 'AutoSol results'     : 'FAILED'}
                        self.autosol_failed = True
                else:
                    bcc1  = float(autosol.get('bayes-cc'))
                if self.autosol_failed == False:
                    if autosol2['bayes-cc'] == 'ERROR':
                        bcc2 = 0.0
                    else:
                        bcc2  = float(autosol2.get('bayes-cc'))
                    #Figure out which hand is correct.
                    if bcc1 > bcc2:
                        self.autosol_results = { 'AutoSol results'     : autosol    }
                    else:
                        self.autosol_results = { 'AutoSol results'     : autosol2    }
                                   
        except:
            self.logger.exception('**Error in postprocessAutoSol.**')
        
    def postprocessAutoBuild(self):
        """
        Get phenix.autobuild results.
        """
        self.logger.debug('AutoSolve::postprocessAutoBuild')
        try:                         
            temp = []
            dict = {}
            index = 1
            timer = 0
            parse = False
            finished = False
            if self.test == False:
                pid = self.autobuild_output.get()
                while Utils.stillRunning(self,pid):
                #while 1: #For testing
                    print 'Waiting for AutoBuild to finish ' + str(timer) + ' seconds'
                    if self.test:
                        readlog = open('autobuild2.log','r')
                    else:
                        readlog = open('autobuild.log','r')
                    for line in readlog:
                        temp.append(line)
                        if line.startswith('from: refine'):
                            end = line.split()[1]
                            if dict.has_key(end):
                                parse = False
                            else:
                                parse = line
                        if line.startswith('from: overall_best_refine'):
                            end = line.split()[1]                            
                            parse = line
                            finished = True
                    if parse:
                        start = index+1
                        index = temp.index(parse)+1
                        log = []
                        log.extend(temp[start:index])
                        dict[end] = index
                        autobuild = Parse.ParseOutputAutoBuild(self,log)
                        self.autobuild_results = { 'AutoBuild results'     : autobuild    }
                        if self.autobuild_results['AutoBuild results'] == None:
                            self.autobuild_results = { 'AutoBuild results'     : 'FAILED'}
                            self.autobuild_failed = True
                            self.clean = False
                        if finished:
                            self.logger.debug('phenix.autobuild is finished.')
                            print 'phenix.autobuild is finished.'
                            self.postprocess(True)
                            break
                        else:
                            self.postprocess(False)
                            parse = False
                    readlog.close()                    
                    time.sleep(10)
                    timer += 10           
                    if self.autobuild_timer:
                        if timer >= self.autobuild_timer:
                            Utils.killChildren(self,pid)                           
                            print 'phenix.autobuild timed out.'   
                            self.logger.debug('phenix.autobuild timed out.')                   
                            self.autobuild_log.append('phenix.autobuild timed out\n')
                            break            
            readlog = open('autobuild.log','r')
            for line in readlog:
                self.autobuild_log.append(line)
            readlog.close()                    
        
        except:
            self.logger.exception('**Error in postprocessAutoBuild.**')
            
    def postprocessPhaser(self,input):
        """
        Look at Phaser results.
        """
        self.logger.debug('AutoSolve::postprocessPhaser')
        try:
            if self.phaser_log == False:
                self.phaser_log = []
            Utils.folders(self,'Phaser_'+input)
            log = []
            logfile = open('PHASER.sum','r')
            for line in logfile:
                log.append(line)
                self.phaser_log.append(line)
            logfile.close()
            data = Parse.ParseOutputPhaser(self,log)
            self.phaser_results[input] = { 'AutoMR results' : data }
            if data == None:
                self.phaser_results[input] = { 'AutoMR results'     : 'FAILED'}
                self.clean = False
            if self.adf:
                if self.phaser_results[input].get('AutoMR results').get('AutoMR sg') != 'No solution':
                    pid = Utils.calcADF(self,input)
                    return (pid)
                else:
                    return ('0')
            else:
                self.phaser_results[input].get('AutoMR results')['AutoMR adf'] = 'None'
                self.phaser_results[input].get('AutoMR results')['AutoMR peak'] = 'None'
                         
        except:
            self.logger.exception('**ERROR in postprocessPhaser**')
        
    def shelxQueue(self,jobs):
        """
        Waits for the Shelx to finish then runs postprocessShelx.
        """
        self.logger.debug('AutoSolve::shelxQueue')
        try:        
            pid = []
            sg = []
            new_queue = {}
            e_queue = {}
            timed_out = False
            timer = 0
            kill = False
            early = False
            sg_name = jobs.keys()
            for set in jobs.values():
                pid.append(set)
            counter = len(pid)
            counter2 = counter
            while counter != 0:
                for sg in sg_name:
                    for job in jobs[sg]:
                        if Utils.stillRunningCluster(self,job):    
                            pass
                        elif Utils.stillRunning(self,job):    
                            pass
                        else:
                            jobs[sg].remove(job)
                            Utils.folders(self,'Shelx_'+sg)
                            #These files are only present if not running on head node??
                            if self.cluster_use:
                                shelxd_log = 'shelxd_mp64.o'+str(job)
                            else:
                                shelxd_log = 'shelxd.o'+str(job)
                            shelxe_log = 'shelxe.o'+str(job)
                            #Since the shelxd output is only used for plots, I can call them whatever I want.
                            if os.path.exists(shelxd_log):
                                number = str(len(jobs[sg]))
                                shutil.copy(shelxd_log,'shelx'+number+'.log')
                            #Check to see if job is shelxe and change output file name.
                            if os.path.exists(shelxe_log):
                                if e_queue[sg+'_1'] == job:
                                    shutil.copy(shelxe_log,'shelxe.log')
                                    if self.shelx_build:
                                        if os.path.exists('shelxe_i.log'):
                                            junk = self.postprocessShelx(sg,'all')
                                            if junk == 'kill':
                                                kill = True
                                            else:
                                                counter2 -= 1
                                if e_queue[sg+'_2'] == job:    
                                    shutil.copy(shelxe_log,'shelxe_i.log')
                                    if self.shelx_build:
                                        if os.path.exists('shelxe.log'):
                                            junk = self.postprocessShelx(sg,'all')
                                            if junk == 'kill':
                                                kill = True
                                            else:
                                                counter2 -= 1
                                if self.shelx_build:
                                    if e_queue[sg+'_3'] == job:
                                        shutil.copy(shelxe_log,'shelxe_trace.log')
                                    if e_queue[sg+'_4'] == job:
                                        shutil.copy(shelxe_log,'shelxe_i_trace.log')
                            if len(jobs[sg]) == 0:
                                #If error in ShelxE and has to rerun.
                                if e_queue.has_key(sg):
                                    self.postprocessShelx(sg)
                                    counter -= 1
                                    """
                                    #SAVE for self.cluster_use == False
                                    if self.shelxe_queue.has_key(sg_name[n]):
                                        junk = self.shelxe_queue[sg_name[n]]
                                        e_queue.update(junk)
                                        pid1 = junk.values()
                                        pid[n].extend(pid1)
                                        del self.shelxe_queue[sg_name[n]]
                                    else:
                                        counter -=1
                                    """
                                else:
                                    if self.multiShelxD:
                                        self.sortShelxD()
                                    pid1 = []
                                    junk = self.processShelxE(sg)
                                    e_queue.update(junk)
                                    pid1 = junk.values()
                                    jobs[sg].extend(pid1)
                                    e_queue[sg] = pid1
                time.sleep(1)
                timer += 1
                print 'Waiting for SHELXCDE to finish '+str(timer)+' seconds'
                if self.shelx_timer:
                    if timer >= self.shelx_timer:
                        timed_out = True
                        break
                if kill:
                    timed_out = True
                    break
                if self.shelx_build:
                    if counter2 == 0:
                        counter2 = -1
                        self.sortShelx(sg_name)
                        self.postprocess(False)
                        if self.shelx_nosol == False:
                            if self.build:
                                self.processAutoSol()
            if timed_out:
                self.logger.debug('SHELXCDE timed out.')
                print 'SHELXCDE timed out.'
                for sg in sg_name:                    
                    Utils.folders(self,'Shelx_'+sg)
                    if self.multiShelxD:
                        self.sortShelxD()
                    for job in jobs[sg]:
                        if self.cluster_use:
                            Utils.killChildrenCluster(self,job)
                        else:
                            Utils.killChildren(self,job)
            self.logger.debug('SHELXCDE finished.')
        
        except:
            self.logger.exception('**ERROR in shelxQueue**')
        
    def phaserQueue(self):
        """
        Queue for Phaser.
        """
        self.logger.debug('AutoSolve::phaserQueue')
        try:
            self.cellJobs = self.cellJ.get()
            if self.cellJobs:
                timed_out = False
                timer = 0
                adf_pids = []
                pids = self.cellJobs.keys()
                counter = len(pids)                
                while counter != 0:
                    for pid in pids:
                        if Utils.stillRunningCluster(self,pid):    
                            pass
                        elif Utils.stillRunning(self,pid):    
                            pass
                        else:
                            if self.cluster_use:
                                if self.adf:
                                    map = False
                                    for line in adf_pids:
                                        if line.startswith(pid):
                                            map = True
                                    if map:
                                        pids.remove(pid)
                                        counter -= 1
                                    else:
                                        adf = self.postprocessPhaser(self.cellJobs[pid])
                                        if adf != '0':
                                            adf_pids.append(adf)
                                            pids.remove(pid)
                                            pids.append(adf)
                                        else:
                                            pids.remove(pid)
                                            counter -= 1
                                else:
                                    self.postprocessPhaser(self.cellJobs[pid])
                                    pids.remove(pid)
                                    counter -= 1
                            else:
                                self.postprocessPhaser(self.cellJobs[pid])
                                pids.remove(pid)
                                counter -= 1
                    time.sleep(1)
                    timer += 1
                    print 'Waiting for Phaser to finish '+str(timer)+' seconds'
                    if self.phaser_timer:
                        if timer >= self.phaser_timer:
                            timed_out = True        
                            break
                if timed_out:
                    self.logger.debug('Phaser timed out.')
                    print 'Phaser timed out.'
                    for pid in pids:
                        if self.cluster_use:
                            Utils.killChildrenCluster(self,pid)
                        else:
                            Utils.killChildren(self,pid)
                self.logger.debug('Phaser finished.')
        
        except:
            self.logger.exception('**ERROR in phaserQueue**')
           
    def sortShelxD(self):
        """
        Sort best fa file from multiple ShelxD runs.
        """
        self.logger.debug('AutoSolve::sortShelxD')
        try:                    
            if self.njobs == 1:
                if os.path.exists('junk_fa0.res'):
                    shutil.copy('junk_fa0.res','junk_fa.res')
                if os.path.exists('junk_fa0.pdb'):
                    shutil.copy('junk_fa0.pdb','junk_fa.pdb')
            else:
                #cc = []
                ccw = []
                junk= []
                for i in range(0,self.njobs):
                    if os.path.exists('junk_fa'+str(i)+'.res'):
                        read = open('junk_fa'+str(i)+'.res','r')
                        for line in read:
                            if line.startswith('REM Best'):
                                #cc.append(line.split()[5])
                                ccw.append(line.split()[7])
                            if line.startswith('REM TRY'):
                                #cc.append(line.split()[4])
                                ccw.append(line.split()[6])
                        read.close()
                if len(ccw) != 0:
                    for line in ccw:
                        junk.append(float(line))
                    max_ccw = max(junk)
                    for line in ccw:
                        if line.startswith(str(max_ccw)):
                            index = ccw.index(line)                        
                    cp = 'cp junk_fa'+str(index)+'.res junk_fa.res'                
                    os.system(cp)
                    cp2 = 'cp junk_fa'+str(index)+'.pdb junk_fa.pdb'
                    os.system(cp2)
        
        except:
            self.logger.exception('**Error in sortShelxD**')
        
    def sortShelx(self,input):
        """
        Sort SHELX results to find most promising SG.
        """
        self.logger.debug('AutoSolve::sortShelx')
        try:
            cc = []
            cc_f = []
            ccw = []
            ccw_f = []
            fom = []
            fom_f = []
            fom_s = []
            inv = []
            nosol = []
            for line in input:
                cc.append(self.shelx_results0[line].get('Shelx results').get('shelxd_best_cc'))
                ccw.append(self.shelx_results0[line].get('Shelx results').get('shelxd_best_ccw'))
                fom.append(self.shelx_results0[line].get('Shelx results').get('shelxd_fom'))
                inv.append(self.shelx_results0[line].get('Shelx results').get('shelxe_inv_sites'))
                nosol.append(self.shelx_results0[line].get('Shelx results').get('shelxe_nosol'))
            for line in cc:
                cc_f.append(float(line))        
            max_cc = max(cc_f)
            index_cc = numpy.argmax(cc_f)
            for line in ccw:
                ccw_f.append(float(line))            
            max_ccw = max(ccw_f)
            index_ccw = numpy.argmax(ccw_f)
            for line in fom:
                junk2 = []
                for num in line:
                    junk2.append(float(num))
                    max1 = max(junk2)
                fom_f.append(max1)
                fom_s.append(str(max1))
            max_fom = max(fom_f)
            index_fom = numpy.argmax(fom_f)
            """
            for line in fom_s:
                if line.startswith(str(max_fom)):
                    index2_fom = fom_s.index(line)        
            """
            sg = input[index_ccw]
            if nosol[index_ccw] == 'True':
                self.both_hands = True
            if inv[index_ccw] == 'True':
                self.shelx_sg = Utils.convertSG(self,Utils.checkInverse(self,Utils.convertSG(self,sg))[0],True)
            else:
                self.shelx_sg = sg
            self.shelx_results = self.shelx_results0[sg]
            self.shelx_log = self.shelx_log0[sg]
            for x in range(len(input)):
                self.shelxd_dict[input[x]] = {'cc':cc[x],'ccw':ccw[x],'fom':fom_f[x]}
            if str(max_ccw).startswith('0.0'):
                self.shelx_nosol = True
            else:
                Utils.folders(self,'Shelx_'+sg)
                Utils.makeHAfiles(self)
                if len(ccw) == 1:
                    if max_ccw > 15:
                    #if max_ccw > 13:
                        pass
                    else:
                        self.shelx_nosol = True
                else:
                    if max_ccw > 15:
                        #pass               
                        if index_ccw == index_cc:
                            pass
                        elif index_ccw == index_fom:
                            pass
                        else:
                            self.shelx_nosol = True                
                    elif index_ccw == index_cc:
                        pass
                    elif index_ccw == index_fom:
                        pass
                    else:
                        self.shelx_nosol = True
            
        except:
            self.logger.exception('**ERROR in sortShelx**')
                       
    def postprocess(self,final=True):
        """
        Things to do after the main process runs
        1. Return the data through the pipe
        """
        self.logger.debug('AutoSolve::postprocess')
        #Run summary files for each program to print to screen        
        output = {}
        sad_status = {}
        failed = False
        if final:
            self.pp = True
        if self.autobuild:
            if self.autobuild_results:
                Summary.summaryAutoSol(self,True)
            self.htmlSummaryAutoSol()
            sad_status['sad_status'] = 'Working'
            try:
                if self.gui:    
                    html = 'jon_summary_autosol.php'
                else:
                    html = 'jon_summary_autosol.html'
                html_path = os.path.join(self.working_dir,html)
                if os.path.exists(html_path):
                    output['Autosol html'] = html_path
                else:
                    output['Autosol html'] = 'None'          
            except:
                self.logger.exception('**Could not update path of autosol html file.**')
                output['Autosol html']   = 'FAILED'                
            try:     
                if self.autobuild_failed:
                    output['Autosol best pdb']  = 'FAILED'
                    output['Autosol best mtz']  = 'FAILED'
                    output['Autosol tar']       = 'FAILED'
                    failed = True
                else:
                    tar = 'autosol_files.tar'
                    bz2tar = tar + '.bz2'
                    path = self.autobuild_results.get('AutoBuild results').get('AutoBuild_dir')+'/TEMP0'
                    shutil.copy(os.path.join(path,self.pdb),self.working_dir)
                    shutil.copy(os.path.join(path,self.mtz),self.working_dir)
                    pdb_path = os.path.join(self.working_dir,self.pdb)
                    mtz_path = os.path.join(self.working_dir,self.mtz)
                    tar_path = os.path.join(self.working_dir,tar)
                    bz2tar_path = os.path.join(self.working_dir,bz2tar)
                    os.chdir(self.working_dir)
                    if os.path.exists(pdb_path):
                        output['Autosol best pdb']  = pdb_path
                        tar1 = 'tar -cf ' + tar + ' ' + self.pdb
                        os.system(tar1)
                    else:
                        output['Autosol best pdb']  = 'None'
                    if os.path.exists(mtz_path):
                        output['Autosol best mtz']  = mtz_path
                        tar2 = 'tar -rf ' + tar + ' ' + self.mtz
                        os.system(tar2)
                    else:
                        output['Autosol best mtz']  = 'None'
                    if os.path.exists(tar_path):
                        bz2 = 'bzip2 -qf ' + tar_path
                        os.system(bz2)
                        if os.path.exists(bz2tar_path):
                            output['Autosol tar']  = bz2tar_path
                        else:
                            output['Autosol tar']  = 'None'
                    self.autosol_results = { 'AutoSol results'     : 'None'}            
            except:
                output['Autosol best pdb']  = 'FAILED'
                output['Autosol best mtz']  = 'FAILED'
                output['Autosol tar']       = 'FAILED'
                output['Autosol html']      = 'FAILED'
                failed = True
                self.clean = False
                self.logger.exception('**Could not put AutoBuild tar together**')                
            if final:
                if failed:
                    sad_status['sad_status'] = 'FAILED'
                else:
                    sad_status['sad_status'] = 'SUCCESS'
            else:
                sad_status['sad_status'] = 'WORKING'                    
        else:        
            if self.shelx_failed == False:
                if self.shelx_results:
                    Summary.summaryShelx(self)
                    self.plotShelx()
                    self.shelx_results.get('Shelx results').update({'shelx_no_solution': self.shelx_nosol})
            else:
                self.plotShelxFailed()
                self.shelx_results.get('Shelx results').update({'shelx_no_solution': True})
            if self.phaser:
                if self.cell_output:
                    Summary.summaryCell(self,'sad')
            self.htmlSummaryShelx()
            if self.build:
                if final:
                    if self.anom_signal:
                        if self.shelx_nosol == False:
                            if self.autosol_failed == False:
                                Summary.summaryAutoSol(self)                            
            self.htmlSummaryAutoSol()       
            try:
                if self.gui:
                    sl = 'jon_summary_shelx.php'
                else:
                    sl = 'jon_summary_shelx.html'
                shelx_path = os.path.join(self.working_dir,sl)
                if os.path.exists(shelx_path):
                    output['Shelx summary html']   = shelx_path
                else:
                    output['Shelx summary html']   = 'None'
            except:
                self.logger.exception('**Could not update path of shelx summary html file.**')
                output['Shelx summary html']   = 'FAILED'
                failed = True                        
            try:
                if self.gui:
                    sp = 'plots_shelx.php'
                else:
                    sp = 'plots_shelx.html'
                plots_path = os.path.join(self.working_dir,sp)
                if os.path.exists(plots_path):
                    output['Shelx plots html']   = plots_path
                else:
                    output['Shelx plots html']   = 'None'
            except:
                self.logger.exception('**Could not update path of shelx plots html file.**')
                output['Shelx plots html']   = 'FAILED'                
                failed = True                
            #tar and copy best Shelx files to working dir.
            if final == False:
                if self.anom_signal:
                    try:
                        tar = 'shelx_'+self.shelx_sg+'.tar'
                        bz = tar+'.bz2'
                        ha = self.shelx_sg+'.hat'
                        phs = self.shelx_sg+'.phs'
                        auto = self.shelx_results.get('Shelx results').get('shelxe_trace_pdb')
                        if os.path.exists(ha):
                            tar1 = 'tar -cf '+tar+' '+ha
                            os.system(tar1)
                        if os.path.exists(phs):
                            tar2 = 'tar -rf '+tar+' '+phs
                            os.system(tar2)
                        #tar up the shelxe autotraced pdb file
                        if self.shelx_build:
                            if self.shelx_nosol == False:
                                if auto != 'None':
                                    if os.path.exists(auto):
                                        junk = os.path.basename(auto)
                                        tar3 = 'tar -rf '+tar+' '+junk
                                        os.system(tar3)
                        if os.path.exists(tar):
                            bz2 = 'bzip2 -qf ' + tar
                            os.system(bz2)
                            if os.path.exists(bz):
                                shutil.copy(bz,self.working_dir)
                                bz_path = os.path.join(self.working_dir,bz)
                                self.shelx_results.get('Shelx results').update({'shelx_tar': bz_path})
                            else:
                                self.shelx_results.get('Shelx results').update({'shelx_tar': 'None'})
                        else:
                            self.shelx_results.get('Shelx results').update({'shelx_tar': 'None'})
                    except:
                        self.logger.exception('**Could not update path of shelx ha and phs files.**')
                        self.shelx_results.get('Shelx results').update({'shelx_tar': 'None'})
                        self.clean = False
                        failed = True
                    #For Phaser results from rapd_agent_cell
                    try:
                        if self.phaser:
                            if self.cell_output:
                                pdbs = self.cell_output.keys()
                                if pdbs != ['None']:
                                    for pdb in pdbs:
                                        dir      = self.phaser_results[pdb].get('AutoMR results').get('AutoMR dir')
                                        pdb_file = self.phaser_results[pdb].get('AutoMR results').get('AutoMR pdb')
                                        mtz_file = self.phaser_results[pdb].get('AutoMR results').get('AutoMR mtz')
                                        adf_file = self.phaser_results[pdb].get('AutoMR results').get('AutoMR adf')
                                        peak_file = self.phaser_results[pdb].get('AutoMR results').get('AutoMR peak')
                                        pdb_path = os.path.join(dir,pdb_file)
                                        mtz_path = os.path.join(dir,mtz_file)
                                        if dir != 'No solution':
                                            tar = pdb+'.tar'
                                            tar_path = os.path.join(self.working_dir,tar)
                                            bz2tar = tar + '.bz2'
                                            bz2tar_path = os.path.join(self.working_dir,bz2tar)
                                            if os.path.exists(pdb_path):
                                                tar1 = 'tar -C '+dir+' -cf '+tar_path+' '+pdb_file
                                                os.system(tar1)
                                            if os.path.exists(mtz_path):
                                                tar2 = 'tar -C '+dir+' -rf '+tar_path+' '+mtz_file
                                                os.system(tar2)
                                            if os.path.exists(adf_file):
                                                tar3 = 'tar -C '+os.path.dirname(adf_file)+' -rf '+tar_path+' '+os.path.basename(adf_file)
                                                os.system(tar3)
                                            if os.path.exists(peak_file):
                                                tar4 = 'tar -C '+os.path.dirname(peak_file)+' -rf '+tar_path+' '+os.path.basename(peak_file)
                                                os.system(tar4)
                                            if os.path.exists(tar_path):
                                                bz2 = 'bzip2 -qf ' + tar_path
                                                os.system(bz2)
                                                if os.path.exists(bz2tar_path):
                                                    self.phaser_results[pdb].get('AutoMR results').update({'AutoMR tar': bz2tar_path})
                                                else:
                                                    self.phaser_results[pdb].get('AutoMR results').update({'AutoMR tar': 'None'})
                                        self.cell_output[pdb].update(self.phaser_results[pdb])
                                self.cellAnalysis_results = { 'Cell analysis results': self.cell_output }
                            else:
                                self.cellAnalysis_results = { 'Cell analysis results': 'None' }
                        else:
                            self.cellAnalysis_results = { 'Cell analysis results': 'None' }
                    except:
                        self.logger.exception('**Could not AutoMR results in postprocess.**')
                        self.cellAnalysis_results = { 'Cell analysis results': 'FAILED'}
                        self.clean = False
                        failed = True
                else:
                    #Parse.setShelxNoSignal(self)
                    self.cellAnalysis_results = { 'Cell analysis results': 'None' }
            try:
                if self.gui:
                    html = 'jon_summary_autosol.php'
                else:
                    html = 'jon_summary_autosol.html'
                html_path = os.path.join(self.working_dir, html)
                if os.path.exists(html_path):
                    output['Autosol html'] = html_path
                else:
                    output['Autosol html'] = 'None'
                #For AutoSol files
                if final:
                    if self.anom_signal:
                        if self.shelx_nosol == False:
                            if self.build:
                                if self.autosol_failed:
                                    output['Autosol tar']       = 'FAILED'
                                    failed = True
                                else:
                                    pdb = 'overall_best.pdb'
                                    mtz = 'overall_best_denmod_map_coeffs.mtz'
                                    tar = 'autosol_files.tar'
                                    bz2tar = tar + '.bz2'
                                    path = self.autosol_results.get('AutoSol results').get('directory')
                                    tar_path = os.path.join(self.working_dir,tar)
                                    bz2tar_path = os.path.join(self.working_dir,bz2tar)
                                    if os.path.exists(os.path.join(path,pdb)):
                                        tar1 = 'tar -C '+path+' -cf '+tar+' '+pdb
                                        os.system(tar1)
                                    if os.path.exists(os.path.join(path,mtz)):
                                        tar2 = 'tar -C '+path+' -rf '+tar+' '+mtz
                                        os.system(tar2)
                                    if os.path.exists(tar):
                                        bz2 = 'bzip2 -qf ' + tar
                                        os.system(bz2)
                                        shutil.copy(bz2tar,bz2tar_path)
                                        if os.path.exists(bz2tar_path):
                                            output['Autosol tar']  = bz2tar_path
                                        else:
                                            output['Autosol tar']  = 'None'
                                    sad_status['sad_status'] = 'Success'
                            else:
                                Parse.setAutoSolFalse(self)
                                output['Autosol tar']       = 'None'
                                self.autosol_results = { 'AutoSol results'     : 'None'}
                                #sad_status['sad_status'] = 'Success'
                        else:
                            output['Autosol tar']       = 'None'
                            self.autosol_results = { 'AutoSol results'     : 'None'}
                            #sad_status['sad_status'] = 'Success'
                    else:
                        output['Autosol tar']       = 'None'
                        self.autosol_results = { 'AutoSol results'     : 'None'}
                        #sad_status['sad_status'] = 'Success'                        
                else:
                    output['Autosol tar']       = 'None'
                    self.autosol_results = { 'AutoSol results'     : 'None'}
                    #sad_status['sad_status'] = 'Working'
            except:
                output['Autosol tar']       = 'FAILED'
                #output['Autosol html']      = 'FAILED'                
                #sad_status['sad_status'] = 'Failed'
                failed = True
                self.clean = False
                self.logger.exception('**Could not put AutoSol tar together**')
        try:
            self.output_files = {'Output files'   : output}            
        except:
            self.logger.exception('**Could not update the output dict.**')        
        #Get proper status.    
        if final:
            if failed:
                sad_status['sad_status'] = 'FAILED'
            else:
                sad_status['sad_status'] = 'SUCCESS'
        else:
            sad_status['sad_status'] = 'WORKING'
        #Put all the result dicts from all the programs run into one resultant dict and pass it along the pipe.
        try:
            self.results = {}
            if sad_status:
                self.results.update(sad_status)
            if self.shelx_results:
                self.results.update(self.shelx_results)
                #Utils.pp(self,self.shelx_results)
            if self.cellAnalysis_results:
                self.results.update(self.cellAnalysis_results)
            if self.autosol_results:
                self.results.update(self.autosol_results)
            if self.output_files:
                self.results.update(self.output_files)
            if self.results:
                if len(self.input) == 6:
                    del self.input[5]
                self.input.append(self.results)
            if self.gui:
                self.sendBack2(self.input)        
        except:
            self.logger.exception('**Could not send results to pipe.**')        
        if final:
            #Cleanup my mess.
            try:
                if self.clean:
                    os.chdir(self.working_dir)
                    rm_folders = 'rm -rf Shelx_*'
                    self.logger.debug('Cleaning up SHELX files and folders')
                    self.logger.debug(rm_folders)
                    os.system(rm_folders)
                    rm_folders2 = 'rm -rf Phaser_*'
                    self.logger.debug('Cleaning up Phaser files and folders')
                    self.logger.debug(rm_folders2)
                    os.system(rm_folders2)
                    rm_folders3 = 'rm -rf AutoSol_*'
                    self.logger.debug('Cleaning up AutoSol files and folders')
                    self.logger.debug(rm_folders3)
                    os.system(rm_folders3)
                    rm_files = 'rm -rf *.com *.sca *.phs *.hat'
                    self.logger.debug('Cleaning up misc files')
                    os.system(rm_files)
            except:
                self.logger.exception('**Could not cleanup**')           
            
            #Say job is complete.
            t = round(time.time()-self.st)
            self.logger.debug('-------------------------------------')
            self.logger.debug('RAPD AutoSolve complete.')
            self.logger.debug('Total elapsed time: ' + str(t) + ' seconds')
            self.logger.debug('-------------------------------------')
            print '\n-------------------------------------'
            print 'RAPD AutoSolve complete.'
            print 'Total elapsed time: ' + str(t) + ' seconds'
            print '-------------------------------------'        
            #sys.exit(0) #did not appear to end script with some programs continuing on for some reason.
            os._exit(0)     
        
    def plotShelx(self):
        """
        generate plots html/php file
        """      
        self.logger.debug('AutoSolve::plotShelx')
        try:        
            #if self.shelx_results:
            shelxc_res       = self.shelx_results.get('Shelx results').get('shelxc_res')
            shelxc_data      = self.shelx_results.get('Shelx results').get('shelxc_data')
            shelxc_isig      = self.shelx_results.get('Shelx results').get('shelxc_isig')
            shelxc_comp      = self.shelx_results.get('Shelx results').get('shelxc_comp')
            shelxc_dsig      = self.shelx_results.get('Shelx results').get('shelxc_dsig')            
            shelxd_try       = self.shelx_results.get('Shelx results').get('shelxd_try')            
            shelxd_cca       = self.shelx_results.get('Shelx results').get('shelxd_cca')
            shelxd_ccw       = self.shelx_results.get('Shelx results').get('shelxd_ccw')
            shelxd_fom       = self.shelx_results.get('Shelx results').get('shelxd_fom')
            shelxd_best_occ  = self.shelx_results.get('Shelx results').get('shelxd_best_occ')
            shelxd_best_try  = self.shelx_results.get('Shelx results').get('shelxd_best_try')
            shelxd_best_cc   = self.shelx_results.get('Shelx results').get('shelxd_best_cc')
            shelxd_best_ccw  = self.shelx_results.get('Shelx results').get('shelxd_best_ccw')            
            shelxe_cc        = self.shelx_results.get('Shelx results').get('shelxe_cc')
            shelxe_contrast  = self.shelx_results.get('Shelx results').get('shelxe_contrast')
            shelxe_con       = self.shelx_results.get('Shelx results').get('shelxe_con')
            shelxe_sites     = self.shelx_results.get('Shelx results').get('shelxe_sites')
            shelxe_res       = self.shelx_results.get('Shelx results').get('shelxe_res')
            shelxe_mapcc     = self.shelx_results.get('Shelx results').get('shelxe_mapcc')            
                 
            if self.gui:
                shelx_plot  = "<?php\n"
                shelx_plot += "//prevents caching\n"
                shelx_plot += 'header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");\n'
                shelx_plot += 'header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");\n'
                shelx_plot += 'header("Cache-Control: post-check=0, pre-check=0",false);\n'
                shelx_plot += "session_cache_limiter();\n"
                shelx_plot += "session_start();\n"
                shelx_plot += "require('/var/www/html/rapd/login/config.php');\n"
                shelx_plot += "require('/var/www/html/rapd/login/functions.php');\n"
                shelx_plot +="//prevents unauthorized access\n"
                shelx_plot +='if(allow_user() != "yes")\n'
                shelx_plot +="{\n"
                shelx_plot +='    if(allow_local_data($_SESSION[data]) != "yes")\n'
                shelx_plot +="    {\n"
                shelx_plot +="        include ('./login/no_access.html');\n"
                shelx_plot +="        exit();\n"
                shelx_plot +="    }\n"
                shelx_plot +="}\n"                
                shelx_plot += "?>\n\n"
                shelx_plot += "<html>\n"
            else:                
                shelx_plot = "<html>\n"
            shelx_plot += "  <head>\n"
            shelx_plot += '    <style type="text/css">\n'
            shelx_plot += "      body {\n"
            shelx_plot += "        background-image: none;\n"
            shelx_plot += "      }\n"
            shelx_plot += "       .y-label {width:7px; position:absolute; text-align:center; top:300px; left:15px; }\n"
            shelx_plot += "       .x-label {position:relative; text-align:center; top:10px; }\n"
            shelx_plot += "       .title {font-size:30px; text-align:center;} \n"
            shelx_plot += "    </style>\n"            
            if self.gui == False:
                shelx_plot += '    <link href="layout.css" rel="stylesheet" type="text/css"></link>\n'
                shelx_plot += '    <link type="text/css" href="../css/south-street/njquery-ui-1.7.2.custom.css" rel="stylesheet" />\n'
                shelx_plot += '    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js" type="text/javascript"></script>\n'
                shelx_plot += '    <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js" type="text/javascript"></script>\n'
                shelx_plot += '    <script language="javascript" type="text/javascript" src="../js/flot/jquery.flot.js"></script>\n'
            shelx_plot += "    <script type='text/javascript'>\n"
            shelx_plot += '    $(function() {\n'
            shelx_plot += '        // Tabs\n'
            shelx_plot += "        $('.tabs').tabs();\n"
            shelx_plot += '    });\n'        
            shelx_plot += "    </script>\n\n"        
            shelx_plot += "  </head>\n"
            shelx_plot += "  <body>\n"
            shelx_plot += "    <table>\n"
            shelx_plot += "      <tr> \n"
            shelx_plot += '        <td width="100%">\n'
            shelx_plot += '        <div class="tabs">\n'
            shelx_plot += "          <!-- This is where the tab labels are defined\n"
            shelx_plot += "               221 = tab2(on page) tab2(full output tab) tab1 -->\n"
            shelx_plot += "          <ul>\n"
            shelx_plot += '            <li><a href="#tabs-440">SHELXC1</a></li>\n'
            shelx_plot += '            <li><a href="#tabs-441">SHELXC2</a></li>\n'
            shelx_plot += '            <li><a href="#tabs-442">SHELXC3</a></li>\n'
            shelx_plot += '            <li><a href="#tabs-443">SHELXD1</a></li>\n'
            shelx_plot += '            <li><a href="#tabs-444">SHELXD2</a></li>\n'
            shelx_plot += '            <li><a href="#tabs-445">SHELXD4</a></li>\n'
            shelx_plot += '            <li><a href="#tabs-446">SHELXD5</a></li>\n'
            shelx_plot += '            <li><a href="#tabs-447">SHELXE1</a></li>\n'
            shelx_plot += '            <li><a href="#tabs-448">SHELXE2</a></li>\n'
            shelx_plot += '            <li><a href="#tabs-449">SHELXE3</a></li>\n'
            shelx_plot += "          </ul>\n"
            shelx_plot += '          <div id="tabs-440">\n'
            shelx_plot += '            <div class=title><b>Mean I/sig vs. Resolution</b></div>\n'
            shelx_plot += '            <div id="chart1_div2" style="width:750px;height:550px;margin-left:20;"></div>\n'
            shelx_plot += '            <span class=y-label>M e a n &nbsp I / s i g</span>\n'
            shelx_plot += '            <div class=x-label>Resolution(A)</div>\n' 
            shelx_plot += "          </div>\n"
            shelx_plot += '          <div id="tabs-441">\n'
            shelx_plot += '            <div class=title><b>Completeness vs. Resolution</b></div>\n'
            shelx_plot += '            <div id="chart2_div2" style="width:750px;height:550px;margin-left:20;"></div>\n'
            shelx_plot += '            <span class=y-label>C o m p l e t e n e s s</span>\n'
            shelx_plot += '            <div class=x-label>Resolution(A)</div>\n' 
            shelx_plot += "          </div>\n"            
            shelx_plot += '          <div id="tabs-442">\n'
            shelx_plot += '            <div class=title><b>Mean d"/sig vs. Resolution</b></div>\n'
            shelx_plot += '            <div id="chart3_div2" style="width:750px;height:550px;margin-left:20;"></div>\n'
            shelx_plot += '            <span class=y-label>M e a n &nbsp d" / s i g</span>\n'
            shelx_plot += '            <div class=x-label>Resolution(A)</div>\n' 
            shelx_plot += "          </div>\n"        
            shelx_plot += '          <div id="tabs-443">\n'
            shelx_plot += '            <div class=title><b>CCall vs. CCweak</b></div>\n'
            shelx_plot += '            <div id="chart4_div2" style="width:750px;height:550px;margin-left:20;"></div>\n'
            shelx_plot += '            <span class=y-label>C C a l l</span>\n'
            shelx_plot += '            <div class=x-label>CCweak</div>\n' 
            shelx_plot += "          </div>\n"
            shelx_plot += '          <div id="tabs-444">\n'
            shelx_plot += '            <div class=title><b>CCall vs. PATFOM</b></div>\n'
            shelx_plot += '            <div id="chart5_div2" style="width:750px;height:550px;margin-left:20;"></div>\n'
            shelx_plot += '            <span class=y-label>C C a l l</span>\n'
            shelx_plot += '            <div class=x-label>PATFOM</div>\n' 
            shelx_plot += "          </div>\n"
            shelx_plot += '          <div id="tabs-445">\n'
            shelx_plot += '            <div class=title><b>CCall vs Try</b></div>\n'
            shelx_plot += '            <div id="chart6_div2" style="width:750px;height:550px;margin-left:20;"></div>\n'
            shelx_plot += '            <span class=y-label>C C a l l</span>\n'
            shelx_plot += '            <div class=x-label>Try</div>\n' 
            shelx_plot += "          </div>\n"
            shelx_plot += '          <div id="tabs-446">\n'
            shelx_plot += '            <div class=title><b>Site Occupancy vs. Peak Number</b></div>\n'
            shelx_plot += '            <div id="chart7_div2" style="width:750px;height:550px;margin-left:20;"></div>\n'
            shelx_plot += '            <span class=y-label>S i t e &nbsp O c c u p a n c y</span>\n'
            shelx_plot += '            <div class=x-label>CCall</div>\n' 
            shelx_plot += "          </div>\n"
            shelx_plot += '          <div id="tabs-447">\n'
            shelx_plot += '            <div class=title><b>Contrast vs. Cycle</b></div>\n'
            shelx_plot += '            <div id="chart8_div2" style="width:750px;height:550px;margin-left:20;"></div>\n'
            shelx_plot += '            <span class=y-label>C o n t r a s t</span>\n'
            shelx_plot += '            <div class=x-label>Cycle</div>\n' 
            shelx_plot += "          </div>\n"
            shelx_plot += '          <div id="tabs-448">\n'
            shelx_plot += '            <div class=title><b>Connectivity vs. Cycle</b></div>\n'
            shelx_plot += '            <div id="chart9_div2" style="width:750px;height:550px;margin-left:20;"></div>\n'
            shelx_plot += '            <span class=y-label>C o n n e c t i v i t y</span>\n'
            shelx_plot += '            <div class=x-label>Cycle</div>\n' 
            shelx_plot += "          </div>\n"
            shelx_plot += '          <div id="tabs-449">\n'
            shelx_plot += '            <div class=title><b>Estimated CCmap vs. Resolution</b></div>\n'
            shelx_plot += '            <div id="chart10_div2" style="width:750px;height:550px;margin-left:20;"></div>\n'
            shelx_plot += '            <span class=y-label>C C m a p</span>\n'
            shelx_plot += '            <div class=x-label>Resolution(A)</div>\n' 
            shelx_plot += "          </div>\n"        
            shelx_plot += "        </div>\n"
            shelx_plot += "        <!-- End of Tabs -->\n"
            shelx_plot += "      </td>\n"
            shelx_plot += "     </tr>\n"
            shelx_plot += "  </table>\n\n"
            shelx_plot += '  <script id="source" language="javascript" type="text/javascript">\n'
            shelx_plot += "$(function () {\n\n"
            shelx_plot += "    var meanIsig = [];\n\n"        
            for x in range(len(shelxc_res)):            
                shelx_plot += "    meanIsig.push([-" + shelxc_res[x] + "," + shelxc_isig[x] + "]);\n"                        
            shelx_plot += "\n    var completeness = [];\n\n"                
            for x in range(len(shelxc_res)):            
                shelx_plot += "    completeness.push([-" + shelxc_res[x] + "," + shelxc_comp[x] + "]);\n"     
            shelx_plot += "\n    var dsig = [];\n\n"                
            for x in range(len(shelxc_res)):
                shelx_plot += "    dsig.push([-" + shelxc_res[x] + "," + shelxc_dsig[x] + "]);\n"     
            shelx_plot += "\n    var ccall = [];\n\n"                
            for x in range(len(shelxd_cca)):            
                shelx_plot += "    ccall.push([" + shelxd_ccw[x] + "," + shelxd_cca[x] + "]);\n"     
            shelx_plot += "\n    var patFom = [];\n\n"                
            for x in range(len(shelxd_cca)):            
                shelx_plot += "    patFom.push([" + shelxd_fom[x] + "," + shelxd_cca[x] + "]);\n"             
            shelx_plot += "\n    var ccallTry = [];\n\n"                
            for x in range(len(shelxd_cca)):            
                shelx_plot += "    ccallTry.push([" + shelxd_try[x] + "," + shelxd_cca[x] + "]);\n"     
            shelx_plot += "\n    var siteOcc = [];\n\n"                
            for x in range(len(shelxd_best_occ)):            
                shelx_plot += "    siteOcc.push([" + str(x+1) + "," + shelxd_best_occ[x] + "]);\n"     
            shelx_plot += "\n    var contrast = [], contrast2 = [];\n\n"                
            for i in range(0,20):
                shelx_plot += "    contrast.push([" + str(i+1) + "," + shelxe_contrast[i] + "]);\n"     
            for i in range(20,40):
                shelx_plot += "    contrast2.push([" + str(i-19) + "," + shelxe_contrast[i] + "]);\n"     
            shelx_plot += "\n    var con = [], con2 = [];\n\n"                
            for i in range(0,20):
                shelx_plot += "    con.push([" + str(i+1) + "," + shelxe_con[i] + "]);\n"     
            for i in range(20,40):
                shelx_plot += "    con2.push([" + str(i-19) + "," + shelxe_con[i] + "]);\n"     
            shelx_plot += "\n    var ccmap = [], ccmap2 = [];\n\n"                
            for i in range(0,10):
                shelx_plot += "    ccmap.push([-" + shelxe_res[i] + "," + shelxe_mapcc[i] + "]);\n"     
            for i in range(10,20):
                shelx_plot += "    ccmap2.push([-" + shelxe_res[i-10] + "," + shelxe_mapcc[i] + "]);\n"                            
            shelx_plot += '    var plot1 = $.plot($("#chart1_div2"),\n'
            shelx_plot += '        [ { data: meanIsig }],\n'
            shelx_plot += "        { lines: { show: true},\n"
            shelx_plot += "          points: { show: true },\n"
            shelx_plot += "          selection: { mode: 'xy' },\n"
            shelx_plot += "          grid: { hoverable: true, clickable: true },\n"
            shelx_plot += "          xaxis: { transform: function (v) { return Math.log(-v); },\n"
            shelx_plot += "                   inverseTransform: function (v) { return Math.exp(-v); },\n"
            shelx_plot += "                   tickFormatter: ( function negformat(val,axis){return -val.toFixed(axis.tickDecimals);} ) },\n"        
            shelx_plot += "          yaxis: {min:0}\n"
            shelx_plot += "        });\n\n"            
            shelx_plot += '    var plot2 = $.plot($("#chart2_div2"),\n'
            shelx_plot += '        [ { data: completeness }],\n'
            shelx_plot += "        { lines: { show: true},\n"
            shelx_plot += "          points: { show: true },\n"
            shelx_plot += "          selection: { mode: 'xy' },\n"
            shelx_plot += "          grid: { hoverable: true, clickable: true },\n"
            shelx_plot += "          xaxis: { transform: function (v) { return Math.log(-v); },\n"
            shelx_plot += "                   inverseTransform: function (v) { return Math.exp(-v); },\n"
            shelx_plot += "                   tickFormatter: ( function negformat(val,axis){return -val.toFixed(axis.tickDecimals);} ) },\n"        
            shelx_plot += "          yaxis: {min:0, max:100}\n"
            shelx_plot += "        }); \n\n"                    
            shelx_plot += '    var plot3 = $.plot($("#chart3_div2"),\n'
            shelx_plot += "        [ { data: dsig }],\n"
            shelx_plot += "        { lines: { show: true},\n"
            shelx_plot += "          points: { show: true },\n"
            shelx_plot += "          selection: { mode: 'xy' },\n"
            shelx_plot += "          grid: { hoverable: true, clickable: true },\n"
            shelx_plot += "          xaxis: { transform: function (v) { return Math.log(-v); },\n"
            shelx_plot += "                   inverseTransform: function (v) { return Math.exp(-v); },\n"
            shelx_plot += "                   tickFormatter: ( function negformat(val,axis){return -val.toFixed(axis.tickDecimals);} ) },\n"        
            shelx_plot += "          yaxis: {min:0}\n"
            shelx_plot += "        }); \n\n"
            shelx_plot += '    var plot4 = $.plot($("#chart4_div2"),\n'
            shelx_plot += '        [ { data: ccall }],\n'
            shelx_plot += "        { lines: { show: false},\n"
            shelx_plot += "          points: { show: true },\n"
            shelx_plot += "          selection: { mode: 'xy' },\n"
            shelx_plot += "          grid: { hoverable: true, clickable: true },\n"
            shelx_plot += "          yaxis: {min:0},\n"
            shelx_plot += "          xaxis: {min:0}\n"
            shelx_plot += "        }); \n\n"
            shelx_plot += '    var plot5 = $.plot($("#chart5_div2"),\n'
            shelx_plot += '        [ { data: patFom}],\n'
            shelx_plot += "        { lines: { show: false},\n"
            shelx_plot += "          points: { show: true },\n"
            shelx_plot += "          selection: { mode: 'xy' },\n"
            shelx_plot += "          grid: { hoverable: true, clickable: true },\n"
            shelx_plot += "          yaxis: {min:0},\n"
            shelx_plot += "          xaxis: {min:0}\n"
            shelx_plot += "        }); \n\n"        
            shelx_plot += '    var plot6 = $.plot($("#chart6_div2"),\n'
            shelx_plot += '        [ { data: ccallTry}],\n'
            shelx_plot += "        { lines: { show: false},\n"
            shelx_plot += "          points: { show: true },\n"
            shelx_plot += "          selection: { mode: 'xy' },\n"
            shelx_plot += "          grid: { hoverable: true, clickable: true },\n"
            shelx_plot += "          yaxis: {min:0}\n"
            shelx_plot += "        }); \n\n"   
            shelx_plot += '    var plot7 = $.plot($("#chart7_div2"),\n'
            shelx_plot += '        [ { data: siteOcc}],\n'
            shelx_plot += "        { lines: { show: true},\n"
            shelx_plot += "          points: { show: true },\n"
            shelx_plot += "          selection: { mode: 'xy' },\n"
            shelx_plot += "          grid: { hoverable: true, clickable: true },\n"
            shelx_plot += "          yaxis: {min:0,max:1.0}\n"
            shelx_plot += "        }); \n\n"   
            shelx_plot += '    var plot8 = $.plot($("#chart8_div2"),\n'
            shelx_plot += '        [ { data: contrast, label:"original"}, { data: contrast2, label:"inverted"}],\n'
            shelx_plot += "        { lines: { show: true},\n"
            shelx_plot += "          points: { show: true },\n"
            shelx_plot += "          selection: { mode: 'xy' },\n"
            shelx_plot += "          grid: { hoverable: true, clickable: true },\n"
            shelx_plot += "          yaxis: {min:0}\n"
            shelx_plot += "        }); \n\n"   
            shelx_plot += '    var plot9 = $.plot($("#chart9_div2"),\n'
            shelx_plot += '        [ { data: con, label:"original"}, { data: con2, label:"inverted"}],\n'
            shelx_plot += "        { lines: { show: true},\n"
            shelx_plot += "          points: { show: true },\n"
            shelx_plot += "          selection: { mode: 'xy' },\n"
            shelx_plot += "          grid: { hoverable: true, clickable: true },\n"
            shelx_plot += "          yaxis: {min:0}\n"
            shelx_plot += "        }); \n\n"   
            shelx_plot += '    var plot10 = $.plot($("#chart10_div2"),\n'
            shelx_plot += '        [ { data: ccmap, label:"original"}, { data: ccmap2, label:"inverted"}],\n'
            shelx_plot += "        { lines: { show: true},\n"
            shelx_plot += "          points: { show: true },\n"
            shelx_plot += "          selection: { mode: 'xy' },\n"
            shelx_plot += "          grid: { hoverable: true, clickable: true },\n"
            shelx_plot += "          xaxis: { transform: function (v) { return Math.log(-v); },\n"
            shelx_plot += "                   inverseTransform: function (v) { return Math.exp(-v); },\n"
            shelx_plot += "                   tickFormatter: ( function negformat(val,axis){return -val.toFixed(axis.tickDecimals);} ) },\n"        
            shelx_plot += "          yaxis: {min:0}\n"
            shelx_plot += "        }); \n\n"          
            shelx_plot += "    function showTooltip(x, y, contents) {\n"
            shelx_plot += "        $('<div id=\"tooltip\">' + contents + '</div>').css( {\n"
            shelx_plot += "            position: 'absolute',\n"
            shelx_plot += "            display: 'none',\n"
            shelx_plot += "            top: y + 5,\n"
            shelx_plot += "            left: x + 5,\n"
            shelx_plot += "            border: '1px solid #fdd',\n"
            shelx_plot += "            padding: '2px',\n"
            shelx_plot += "            'background-color': '#fee',\n"
            shelx_plot += "            opacity: 0.80\n"
            shelx_plot += '        }).appendTo("body").fadeIn(200);\n'
            shelx_plot += "    }\n\n"
            shelx_plot += "    var previousPoint = null;\n"
            shelx_plot += '    $("#chart1_div2").bind("plothover", function (event, pos, item) {\n'
            shelx_plot += '        $("#x").text(pos.x.toFixed(2));\n'
            shelx_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
            shelx_plot += "        if (true) {\n"
            shelx_plot += "            if (item) {\n"
            shelx_plot += "                if (previousPoint != item.datapoint) {\n"
            shelx_plot += "                    previousPoint = item.datapoint;\n\n"
            shelx_plot += '                    $("#tooltip").remove();\n'
            shelx_plot += "                    var x = -(item.datapoint[0].toFixed(2)),\n"
            shelx_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
            shelx_plot += "                    showTooltip(item.pageX, item.pageY,\n"
            shelx_plot += '                                "Resolution (A): " + x + ", Mean I/sig: " + y);\n'
            shelx_plot += "                }\n"
            shelx_plot += "            }\n"
            shelx_plot += "            else {\n"
            shelx_plot += '                $("#tooltip").remove();\n'
            shelx_plot += "                previousPoint = null;\n"
            shelx_plot += "            }\n"
            shelx_plot += "        }\n"
            shelx_plot += "    });\n\n"
            shelx_plot += '    $("#chart2_div2").bind("plothover", function (event, pos, item) {\n'
            shelx_plot += '        $("#x").text(pos.x.toFixed(2));\n'
            shelx_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
            shelx_plot += "        if (true) {\n"
            shelx_plot += "            if (item) {\n"
            shelx_plot += "                if (previousPoint != item.datapoint) {\n"
            shelx_plot += "                    previousPoint = item.datapoint;\n\n"
            shelx_plot += '                    $("#tooltip").remove();\n'
            shelx_plot += "                    var x = -(item.datapoint[0].toFixed(2)),\n"
            shelx_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
            shelx_plot += "                    showTooltip(item.pageX, item.pageY,\n"
            shelx_plot += '                                "Resolution (A): " + x + ", %Completeness: " + y);\n'
            shelx_plot += "                }\n"
            shelx_plot += "            }\n"
            shelx_plot += "            else {\n"
            shelx_plot += '                $("#tooltip").remove();\n'
            shelx_plot += "                previousPoint = null;\n"
            shelx_plot += "            }\n"
            shelx_plot += "        }\n"
            shelx_plot += "    });\n\n"
            shelx_plot += '    $("#chart3_div2").bind("plothover", function (event, pos, item) {\n'
            shelx_plot += '        $("#x").text(pos.x.toFixed(2));\n'
            shelx_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
            shelx_plot += "        if (true) {\n"
            shelx_plot += "            if (item) {\n"
            shelx_plot += "                if (previousPoint != item.datapoint) {\n"
            shelx_plot += "                    previousPoint = item.datapoint;\n\n"
            shelx_plot += '                    $("#tooltip").remove();\n'
            shelx_plot += "                    var x = -(item.datapoint[0].toFixed(2)),\n"
            shelx_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
            shelx_plot += "                    showTooltip(item.pageX, item.pageY,\n"
            shelx_plot += '                                \'Resolution (A): \' + x + \', Mean d"/sig: \' + y);\n'
            shelx_plot += "                }\n"
            shelx_plot += "            }\n"
            shelx_plot += "            else {\n"
            shelx_plot += '                $("#tooltip").remove();\n'
            shelx_plot += "                previousPoint = null;\n"
            shelx_plot += "            }\n"
            shelx_plot += "        }\n"
            shelx_plot += "    });\n\n"
            shelx_plot += '    $("#chart4_div2").bind("plothover", function (event, pos, item) {\n'
            shelx_plot += '        $("#x").text(pos.x.toFixed(2));\n'
            shelx_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
            shelx_plot += "        if (true) {\n"
            shelx_plot += "            if (item) {\n"
            shelx_plot += "                if (previousPoint != item.datapoint) {\n"
            shelx_plot += "                    previousPoint = item.datapoint;\n\n"
            shelx_plot += '                    $("#tooltip").remove();\n'
            shelx_plot += "                    var x = item.datapoint[0].toFixed(2),\n"
            shelx_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
            shelx_plot += "                    showTooltip(item.pageX, item.pageY,\n"
            shelx_plot += '                                "CCweak: " + x + ", CCall: " + y);\n'
            shelx_plot += "                }\n"
            shelx_plot += "            }\n"
            shelx_plot += "            else {\n"
            shelx_plot += '                $("#tooltip").remove();\n'
            shelx_plot += "                previousPoint = null;\n"
            shelx_plot += "            }\n"
            shelx_plot += "        }\n"
            shelx_plot += "    });\n\n"
            shelx_plot += '    $("#chart5_div2").bind("plothover", function (event, pos, item) {\n'
            shelx_plot += '        $("#x").text(pos.x.toFixed(2));\n'
            shelx_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
            shelx_plot += "        if (true) {\n"
            shelx_plot += "            if (item) {\n"
            shelx_plot += "                if (previousPoint != item.datapoint) {\n"
            shelx_plot += "                    previousPoint = item.datapoint;\n\n"
            shelx_plot += '                    $("#tooltip").remove();\n'
            shelx_plot += "                    var x = item.datapoint[0].toFixed(2),\n"
            shelx_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
            shelx_plot += "                    showTooltip(item.pageX, item.pageY,\n"
            shelx_plot += '                                "PATFOM: " + x + ", CCall: " + y);\n'
            shelx_plot += "                }\n"
            shelx_plot += "            }\n"
            shelx_plot += "            else {\n"
            shelx_plot += '                $("#tooltip").remove();\n'
            shelx_plot += "                previousPoint = null;\n"
            shelx_plot += "            }\n"
            shelx_plot += "        }\n"
            shelx_plot += "    });\n\n"                        
            shelx_plot += '    $("#chart6_div2").bind("plothover", function (event, pos, item) {\n'
            shelx_plot += '        $("#x").text(pos.x.toFixed(2));\n'
            shelx_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
            shelx_plot += "        if (true) {\n"
            shelx_plot += "            if (item) {\n"
            shelx_plot += "                if (previousPoint != item.datapoint) {\n"
            shelx_plot += "                    previousPoint = item.datapoint;\n\n"
            shelx_plot += '                    $("#tooltip").remove();\n'
            shelx_plot += "                    var x = item.datapoint[0].toFixed(2),\n"
            shelx_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
            shelx_plot += "                    showTooltip(item.pageX, item.pageY,\n"
            shelx_plot += '                                "Try: " + x + ", CCall: " + y);\n'
            shelx_plot += "                }\n"
            shelx_plot += "            }\n"
            shelx_plot += "            else {\n"
            shelx_plot += '                $("#tooltip").remove();\n'
            shelx_plot += "                previousPoint = null;\n"
            shelx_plot += "            }\n"
            shelx_plot += "        }\n"
            shelx_plot += "    });\n\n"
            shelx_plot += '    $("#chart7_div2").bind("plothover", function (event, pos, item) {\n'
            shelx_plot += '        $("#x").text(pos.x.toFixed(2));\n'
            shelx_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
            shelx_plot += "        if (true) {\n"
            shelx_plot += "            if (item) {\n"
            shelx_plot += "                if (previousPoint != item.datapoint) {\n"
            shelx_plot += "                    previousPoint = item.datapoint;\n\n"
            shelx_plot += '                    $("#tooltip").remove();\n'
            shelx_plot += "                    var x = item.datapoint[0].toFixed(2),\n"
            shelx_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
            shelx_plot += "                    showTooltip(item.pageX, item.pageY,\n"
            shelx_plot += '                                "Peak number: " + x + ", Site occupancy: " + y);\n'
            shelx_plot += "                }\n"
            shelx_plot += "            }\n"
            shelx_plot += "            else {\n"
            shelx_plot += '                $("#tooltip").remove();\n'
            shelx_plot += "                previousPoint = null;\n"
            shelx_plot += "            }\n"
            shelx_plot += "        }\n"
            shelx_plot += "    });\n\n"
            shelx_plot += '    $("#chart8_div2").bind("plothover", function (event, pos, item) {\n'
            shelx_plot += '        $("#x").text(pos.x.toFixed(2));\n'
            shelx_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
            shelx_plot += "        if (true) {\n"
            shelx_plot += "            if (item) {\n"
            shelx_plot += "                if (previousPoint != item.datapoint) {\n"
            shelx_plot += "                    previousPoint = item.datapoint;\n\n"
            shelx_plot += '                    $("#tooltip").remove();\n'
            shelx_plot += "                    var x = item.datapoint[0].toFixed(2),\n"
            shelx_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
            shelx_plot += "                    showTooltip(item.pageX, item.pageY,\n"
            shelx_plot += '                                "Cycle: " + x + ", Contrast: " + y);\n'
            shelx_plot += "                }\n"
            shelx_plot += "            }\n"
            shelx_plot += "            else {\n"
            shelx_plot += '                $("#tooltip").remove();\n'
            shelx_plot += "                previousPoint = null;\n"
            shelx_plot += "            }\n"
            shelx_plot += "        }\n"
            shelx_plot += "    });\n\n"
            shelx_plot += '    $("#chart9_div2").bind("plothover", function (event, pos, item) {\n'
            shelx_plot += '        $("#x").text(pos.x.toFixed(2));\n'
            shelx_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
            shelx_plot += "        if (true) {\n"
            shelx_plot += "            if (item) {\n"
            shelx_plot += "                if (previousPoint != item.datapoint) {\n"
            shelx_plot += "                    previousPoint = item.datapoint;\n\n"
            shelx_plot += '                    $("#tooltip").remove();\n'
            shelx_plot += "                    var x = item.datapoint[0].toFixed(2),\n"
            shelx_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
            shelx_plot += "                    showTooltip(item.pageX, item.pageY,\n"
            shelx_plot += '                                "Cycle: " + x + ", Connectivity: " + y);\n'
            shelx_plot += "                }\n"
            shelx_plot += "            }\n"
            shelx_plot += "            else {\n"
            shelx_plot += '                $("#tooltip").remove();\n'
            shelx_plot += "                previousPoint = null;\n"
            shelx_plot += "            }\n"
            shelx_plot += "        }\n"
            shelx_plot += "    });\n\n"
            shelx_plot += '    $("#chart10_div2").bind("plothover", function (event, pos, item) {\n'
            shelx_plot += '        $("#x").text(pos.x.toFixed(2));\n'
            shelx_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
            shelx_plot += "        if (true) {\n"
            shelx_plot += "            if (item) {\n"
            shelx_plot += "                if (previousPoint != item.datapoint) {\n"
            shelx_plot += "                    previousPoint = item.datapoint;\n\n"
            shelx_plot += '                    $("#tooltip").remove();\n'
            shelx_plot += "                    var x = -(item.datapoint[0].toFixed(2)),\n"
            shelx_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
            shelx_plot += "                    showTooltip(item.pageX, item.pageY,\n"
            shelx_plot += '                                "Resolution (A): " + x + ", Est. CCmap: " + y);\n'
            shelx_plot += "                }\n"
            shelx_plot += "            }\n"
            shelx_plot += "            else {\n"
            shelx_plot += '                $("#tooltip").remove();\n'
            shelx_plot += "                previousPoint = null;\n"
            shelx_plot += "            }\n"
            shelx_plot += "        }\n"
            shelx_plot += "    });\n\n"
            shelx_plot += "});\n"
            shelx_plot += "</script>\n"
            shelx_plot += "</body>\n"
            shelx_plot += "</html>\n"        
            self.shelx_plot = shelx_plot               
            if self.shelx_plot:
                if self.gui:
                    sp = 'plots_shelx.php'
                else:
                    sp = 'plots_shelx.html'                
                shelx_plot_file = open(sp,'w')
                shelx_plot_file.writelines(self.shelx_plot)
                shelx_plot_file.close()
                shutil.copy(sp,self.working_dir)
                
        except:
            self.logger.exception('**ERROR in plotShelx**')
            self.plotShelxFailed()
           
    def plotShelxFailed(self):
        """
        If Shelx failed runs this to generate html plot summary.
        """
        try:            
            if self.gui:
                shelx_plot  = "<?php\n"
                shelx_plot += "//prevents caching\n"
                shelx_plot += 'header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");\n'
                shelx_plot += 'header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");\n'
                shelx_plot += 'header("Cache-Control: post-check=0, pre-check=0",false);\n'
                shelx_plot += "session_cache_limiter();\n"
                shelx_plot += "session_start();\n"
                shelx_plot += "require('/var/www/html/rapd/login/config.php');\n"
                shelx_plot += "require('/var/www/html/rapd/login/functions.php');\n"
                shelx_plot += 'if(allow_user() != "yes")\n'
                shelx_plot += "{\n"
                shelx_plot += "    include ('./login/no_access.html');\n"
                shelx_plot += "    exit();\n"
                shelx_plot += "}\n"
                shelx_plot += "?>\n\n"
                shelx_plot += "<html>\n"
            else:                
                shelx_plot = "<html>\n"                     
            shelx_plot +='  <head>\n'
            shelx_plot +='    <style type="text/css" media="screen">\n'
            if self.gui == False:    
                shelx_plot +='      @import "dataTables-1.5/media/css/demo_page.css";\n'
                shelx_plot +='      @import "dataTables-1.5/media/css/demo_table.css";\n'          
            shelx_plot +='    body {\n'
            shelx_plot +='      background-image: none;\n'
            shelx_plot +='    }\n'
            shelx_plot +='    .dataTables_wrapper {position: relative; min-height: 75px; _height: 302px; clear: both;    }\n'
            shelx_plot +='    table.display td {padding: 1px 7px;}\n'
            shelx_plot +='    #dt_example h1 {margin-top: 1.2em; font-size: 1.5em; font-weight: bold; line-height: 1.6em; color: green;\n'
            shelx_plot +='                    border-bottom: 2px solid green; clear: both;}\n'
            shelx_plot +='    #dt_example h2 {font-size: 1.2em; font-weight: bold; line-height: 1.6em; color: #808080; clear: both;}\n'
            shelx_plot +='    #dt_example h3 {font-size: 1.4em; font-weight: bold; line-height: 1.6em; color: red; clear: both;}\n'
            shelx_plot +='    #dt_example h4 {font-size: 1.4em; font-weight: bold; line-height: 1.6em; color: orange; clear: both;}\n'
            shelx_plot +='    table.display tr.odd.gradeA { background-color: #eeffee;}\n'
            shelx_plot +='    table.display tr.even.gradeA { background-color: #ffffff;}\n'
            shelx_plot +='    </style>\n'
            if self.gui == False:    
                shelx_plot +='    <script type="text/javascript" language="javascript" src="dataTables-1.5/media/js/jquery.js"></script>\n'
                shelx_plot +='    <script type="text/javascript" language="javascript" src="dataTables-1.5/media/js/jquery.dataTables.js"></script>\n'
            shelx_plot +='    <script type="text/javascript" charset="utf-8">\n'
            shelx_plot +='      $(document).ready(function() {\n'           
            shelx_plot +="        $('#best').dataTable({\n"
            shelx_plot +='           "bPaginate": false,\n'
            shelx_plot +='           "bFilter": false,\n'
            shelx_plot +='           "bInfo": false,\n'
            shelx_plot +='           "bAutoWidth": false    });\n'
            shelx_plot +='      } );\n'
            shelx_plot +="    </script>\n\n\n"
            shelx_plot +=" </head>\n"
            shelx_plot +='  <body id="dt_example">\n'
            shelx_plot +='    <div id="container">\n'
            shelx_plot +='    <div class="full_width big">\n'
            shelx_plot +='      <div id="demo">\n'
            if self.anom_signal:
                shelx_plot +='      <h3 class="results">Shelx Failed. Could not calculate plots.</h3>\n'
            else:
                shelx_plot +='      <h3 class="results">There does not appear to be sufficient anomalous signal present.</h3>\n'
            shelx_plot +="      </div>\n"
            shelx_plot +="    </div>\n"
            shelx_plot +="    </div>\n"
            shelx_plot +="  </body>\n"
            shelx_plot +="</html>\n"            
            self.shelx_plot = shelx_plot
            if self.shelx_plot:
                if self.gui:
                    sp = 'plots_shelx.php'
                else:
                    sp = 'plots_shelx.html'                
                shelx_plot_file = open(sp,'w')
                shelx_plot_file.writelines(self.shelx_plot)
                shelx_plot_file.close()
                shutil.copy(sp,self.working_dir)
                
        except:
            self.logger.exception('**ERROR in plotShelxFailed**.')
           
    def htmlSummaryShelx(self):
        """
        Create HTML/php files for autoindex/strategy output results.
        """
        self.logger.debug('AutoSolve::htmlSummaryShelx')
        try:
            if self.gui:
                sl = 'jon_summary_shelx.php'
            else:
                sl = 'jon_summary_shelx.html'
            jon_summary = open(sl,'w')
            if self.gui:
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
            if self.gui == False:    
                jon_summary.write('      @import "../js/dataTables-1.5/media/css/demo_page.css";\n')
                jon_summary.write('      @import "../js/dataTables-1.5/media/css/demo_table.css";\n')                
                jon_summary.write('      @import "../css/south-street/jquery-ui-1.7.2.custom.css";\n')
            jon_summary.write('    body {\n')
            jon_summary.write('      background-image: none;\n')
            jon_summary.write('    }\n')
            jon_summary.write('    .dataTables_wrapper {position: relative; min-height: 75px; _height: 302px; clear: both;    }\n')
            jon_summary.write('    table.display td {padding: 1px 7px;}\n')
            jon_summary.write('    tr.GradeD {font-weight: bold;}\n')
            jon_summary.write('    </style>\n')
            if self.gui == False:    
                jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.js"></script>\n')
                jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.dataTables.js"></script>\n')
                jon_summary.write('    <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js" type="text/javascript"></script>\n')
            jon_summary.write('    <script type="text/javascript" charset="utf-8">\n')
            jon_summary.write('      $(document).ready(function() {\n')
            jon_summary.write("        $('#accordion-shelx').accordion({\n")
            jon_summary.write('           collapsible: true,\n')
            jon_summary.write('           active: false         });\n')
            if self.cell_summary:
                jon_summary.write("        $('#sad-cell').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bSort": false,\n') 
                jon_summary.write('           "bAutoWidth": false    });\n')             
            if self.pdb_summary:
                jon_summary.write("        $('#sad-pdb').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bSort": false,\n') 
                jon_summary.write('           "bAutoWidth": false    });\n')           
            if self.shelxc_summary:
                jon_summary.write("        $('#shelxc').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bSort": false,\n') 
                jon_summary.write('           "bAutoWidth": false    });\n')             
            if self.shelxd_summary:
                jon_summary.write("        $('#shelxd').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bAutoWidth": false    });\n')             
            if self.shelxe_summary:                              
                jon_summary.write("        $('#shelxe').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bAutoWidth": false    });\n')            
                jon_summary.write("        $('#shelxe2').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bAutoWidth": false    });\n')
            jon_summary.write('        $("button").button(); \n')
            if self.tooltips:
                jon_summary.writelines(self.tooltips)
            jon_summary.write('                } );\n')
            jon_summary.write("    </script>\n\n\n")
            jon_summary.write(" </head>\n")
            jon_summary.write('  <body id="dt_example">\n')
            if self.cell_summary:
                jon_summary.writelines(self.cell_summary)
            if self.pdb_summary:
                jon_summary.writelines(self.pdb_summary)            
            if self.incompatible_cell:
                jon_summary.write('    <div id="container">\n')
                jon_summary.write('     <div class="full_width big">\n')
                jon_summary.write('      <div id="demo">\n')            
                jon_summary.write('    <h4 class="results">User input SG not compatible with unit cell. Using SG from data instead.</h4>\n')
                jon_summary.write("      </div>\n")
                jon_summary.write("      </div>\n")
                jon_summary.write("      </div>\n")            
            if self.shelxc_summary:
                jon_summary.writelines(self.shelxc_summary)
            if self.shelxd_summary:
                jon_summary.writelines(self.shelxd_summary)           
            if self.shelx_nosol:
                jon_summary.write('    <div id="container">\n')
                jon_summary.write('     <div class="full_width big">\n')
                jon_summary.write('      <div id="demo">\n')            
                jon_summary.write('    <h4 class="results">SHELX did not appear to come up with an obvious solution.</h4>\n')
                jon_summary.write("      </div>\n")
                jon_summary.write("      </div>\n")
                jon_summary.write("      </div>\n")            
            if self.anom_signal==False:
                jon_summary.write('    <div id="container">\n')
                jon_summary.write('     <div class="full_width big">\n')
                jon_summary.write('      <div id="demo">\n')            
                jon_summary.write('    <h4 class="results">SHELX did not run since the anomalous signal is too low..</h4>\n')
                jon_summary.write("      </div>\n")
                jon_summary.write("      </div>\n")
                jon_summary.write("      </div>\n")            
            else:
                if self.shelxe_summary:
                    jon_summary.writelines(self.shelxe_summary)            
            jon_summary.write('    <div id="container">\n')
            jon_summary.write('    <div class="full_width big">\n')
            jon_summary.write('      <div id="demo">\n')            
            jon_summary.write("      <h1 class='Results'>RAPD Logfile</h1>\n")
            jon_summary.write("     </div>\n")  
            jon_summary.write("     </div>\n")  
            jon_summary.write('      <div id="accordion-shelx">\n')
            jon_summary.write('        <h3><a href="#">Click to view log of top solution</a></h3>\n')
            jon_summary.write('          <div>\n')
            jon_summary.write('            <pre>\n')
            jon_summary.write('\n')
            jon_summary.write('---------------Shelx RESULTS---------------\n')
            jon_summary.write('\n')            
            #jon_summary.write('---------------SHELX output too long--------------\n')            
            if self.shelx_log:
                for line in self.shelx_log:
                    if type(line)== str:                    
                        jon_summary.write('' + line )
            else:
                jon_summary.write('---------------SHELX FAILED---------------\n')            
            jon_summary.write('            </pre>\n')
            jon_summary.write('          </div>\n')           
            jon_summary.write("      </div>\n")
            jon_summary.write("    </div>\n")
            jon_summary.write("  </body>\n")
            jon_summary.write("</html>\n")
            jon_summary.close()        
            #copy html file to working dir
            shutil.copy(sl,self.working_dir)
            
        except:
            self.logger.exception('**ERROR in htmlSummaryShelx**')
           
    def htmlSummaryAutoSol(self):
        """
        Write html/php file for Phenix AutoSol results.
        """
        self.logger.debug('AutoSolve::htmlSummaryAutoSol')
        try:
            if self.gui:
                html = 'jon_summary_autosol.php'
            else:
                html = 'jon_summary_autosol.html'
            jon_summary = open(html,'w')
            if self.gui:
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
            if self.gui == False:     
                jon_summary.write('      @import "../js/dataTables-1.5/media/css/demo_page.css";\n')
                jon_summary.write('      @import "../js/dataTables-1.5/media/css/demo_table.css";\n')                
                jon_summary.write('      @import "../css/south-street/jquery-ui-1.7.2.custom.css";\n')
            jon_summary.write('    body {\n')
            jon_summary.write('      background-image: none;\n')
            jon_summary.write('    }\n')
            jon_summary.write('    .dataTables_wrapper {position: relative; min-height: 75px; _height: 302px; clear: both;    }\n')
            jon_summary.write('    table.display td {padding: 1px 7px;}\n')
            jon_summary.write('    </style>\n')        
            if self.gui == False:     
                jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.js"></script>\n')
                jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.dataTables.js"></script>\n')
                #jon_summary.write('    <script type="text/javascript" language="JavaScript" src="../js/jmol-12.1.13/Jmol.js"></script>\n')
                jon_summary.write('    <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js" type="text/javascript"></script>\n')                    
            jon_summary.write('    <script type="text/javascript" charset="utf-8">\n')
            jon_summary.write('      $(document).ready(function() {\n')
            jon_summary.write("        $('#accordion-autosol').accordion({\n")
            jon_summary.write('           collapsible: true,\n')
            jon_summary.write('           active: false         });\n')
            if self.autosol_summary:
                jon_summary.write("        $('#autosol').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bSort": false,\n') 
                jon_summary.write('           "bAutoWidth": false    });\n')        
            if self.autobuild_summary:
                jon_summary.write("        $('#autobuild').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bSort": false,\n') 
                jon_summary.write('           "bAutoWidth": false    });\n')        
            jon_summary.write('                } );\n')
            jon_summary.write("    </script>\n\n")
            jon_summary.write(" </head>\n")
            jon_summary.write('  <body id="dt_example">\n')                    
            if self.autobuild:
                if self.autobuild_summary:
                    jon_summary.writelines(self.autobuild_summary)
                if self.autobuild_failed:
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('     <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')            
                    jon_summary.write('    <h4 class="results">There was a problem in the Phenix AutoBuild run.</h4>\n')
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                if self.pdb.startswith('overall_best') == False:                
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('     <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')            
                    jon_summary.write('    <h4 class="results">Phenix Autobuild is currently running on your solution.</h4>\n')
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                else:
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('     <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')            
                    jon_summary.write('    <h3 class="results">Phenix Autobuild Complete.</h3>\n')
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
            else:
                #if self.pp:
                if self.autosol_summary:
                    jon_summary.writelines(self.autosol_summary)
                elif self.build == False:
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('     <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')            
                    jon_summary.write('    <h3 class="results">Phenix AutoSol not turned on.</h3>\n')
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")                    
                elif self.autosol_failed:
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('     <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')            
                    jon_summary.write('    <h3 class="results">There was a problem in the Phenix AutoSol run.</h3>\n')
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")                    
                elif self.anom_signal == False:
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('     <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')            
                    jon_summary.write('    <h4 class="results">SHELX did not run since the anomalous signal is too low..</h4>\n')
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                elif self.shelx_nosol:
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('     <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')            
                    jon_summary.write('    <h3 class="results">SHELX could not find a solution</h3>\n')
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")    
                else:
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('     <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')            
                    jon_summary.write('    <h4 class="results">Phenix AutoSol is currently running on your solution.</h4>\n')
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
                    jon_summary.write("      </div>\n")
            jon_summary.write('    <div id="container">\n')
            jon_summary.write('    <div class="full_width big">\n')
            jon_summary.write('      <div id="demo">\n')            
            jon_summary.write("      <h1 class='Results'>RAPD Logfile</h1>\n")
            jon_summary.write("     </div>\n")  
            jon_summary.write("     </div>\n")  
            jon_summary.write('      <div id="accordion-autosol">\n')
            jon_summary.write('        <h3><a href="#">Click to view log</a></h3>\n')
            jon_summary.write('          <div>\n')
            jon_summary.write('            <pre>\n')
            jon_summary.write('\n')
            if self.autobuild:
                jon_summary.write('---------------Phenix AutoBuild RESULTS---------------\n')
                jon_summary.write('\n')            
                if self.autobuild_log:
                    for line in self.autobuild_log:
                        jon_summary.write('' + line )            
                else:
                    jon_summary.write('---------------Phenix AutoBuild FAILED---------------\n')
            else:
                jon_summary.write('---------------Phenix AutoSol RESULTS---------------\n')
                jon_summary.write('\n')            
                if self.autosol_log:
                    for line in self.autosol_log:
                        jon_summary.write('' + line )            
                else:
                    jon_summary.write('---------------Phenix AutoSol FAILED---------------\n')         
            jon_summary.write('            </pre>\n')
            jon_summary.write('          </div>\n')           
            jon_summary.write("      </div>\n")
            jon_summary.write("    </div>\n")
            jon_summary.write("  </body>\n")
            jon_summary.write("</html>\n")
            jon_summary.close()
            shutil.copy(html,self.working_dir)
        
        except:
            self.logger.exception('**ERROR in htmlSummaryAutoSol**')
        
    def PrintInfo(self):
        """
        Print information regarding programs utilized by RAPD
        """
        self.logger.debug('AutoSolve::PrintInfo')
        try:
            print '\nRAPD now using Phenix and SHELX'
            print '======================='
            print 'RAPD developed using SHELX-97'
            print 'Reference:  Sheldrick, G.M. (2008) Acta Cryst. A64, 112-122'
            print 'Website: http://shelx.uni-ac.gwdg.de/SHELX/ \n'            
            print 'RAPD developed using Phenix'
            print 'Reference: Adams PD, et al.(2010) Acta Cryst. D66:213-221'
            print 'Website: http://www.phenix-online.org/ \n'
            print 'RAPD developed using AutoSol'
            print 'Reference: Terwilliger TC, et al. (2009) Acta Cryst. D65:582-601.'
            print 'Website: http://www.phenix-online.org/documentation/autosol.htm \n'
            print 'RAPD developed using AutoBuild'
            print 'Reference: Terwilliger TC, et al. (2008) Acta Cryst. D64:61-69.'
            print 'Website: http://www.phenix-online.org/documentation/autobuild.htm \n'            
            print 'RAPD developed using Phaser'
            print 'Reference: McCoy AJ, et al.(2007) J. Appl. Cryst. 40:658-674.'
            print 'Website: http://www.phenix-online.org/documentation/phaser.htm \n'
            print 'RAPD developed using Xtriage and Fest'
            print 'Reference: Zwart PH, et al. (2005)CCP4 Newsletter Winter:Contribution 7.'
            print 'Website: http://www.phenix-online.org/documentation/xtriage.htm\n'
            self.logger.debug('RAPD now using Phenix and SHELX')
            self.logger.debug('=======================')
            self.logger.debug('RAPD developed using SHELX-97')
            self.logger.debug('Reference:  Sheldrick, G.M. (2008). Acta Cryst. A64, 112-122')
            self.logger.debug('Website:    http://shelx.uni-ac.gwdg.de/SHELX/ \n')
            self.logger.debug('RAPD developed using Phenix')            
            self.logger.debug('Reference: Adams PD, et al.(2010) Acta Cryst. D66:213-221')
            self.logger.debug('Website: http://www.phenix-online.org/ \n')
            self.logger.debug('RAPD developed using AutoSol')
            self.logger.debug('Reference: Terwilliger TC, et al. (2009) Acta Cryst. D65:582-601.')
            self.logger.debug('Website: http://www.phenix-online.org/documentation/autosol.htm \n')
            self.logger.debug('RAPD developed using AutoBuild')
            self.logger.debug('Reference: Terwilliger TC, et al. (2008) Acta Cryst. D64:61-69.')
            self.logger.debug('Website: http://www.phenix-online.org/documentation/autobuild.htm \n')
            self.logger.debug('RAPD developed using Phaser')
            self.logger.debug('Reference: McCoy AJ, et al.(2007) J. Appl. Cryst. 40:658-674.')
            self.logger.debug('Website: http://www.phenix-online.org/documentation/phaser.htm \n')
            self.logger.debug('RAPD developed using Xtriage and Fest')
            self.logger.debug('Reference: Zwart PH, et al. (2005)CCP4 Newsletter Winter:Contribution 7.')
            self.logger.debug('Website: http://www.phenix-online.org/documentation/xtriage.htm\n')
                        
        except:
            self.logger.exception('**Error in PrintInfo**')

def multiAutoSolAction(input,output,logger):
    """
    Run phenix.autosol.
    """
    logger.debug('multiAutoSolAction')
    try:
        file = open('autosol.log','w')
        myoutput = subprocess.Popen(input,shell=True,stdout=file,stderr=file)
        output.put(myoutput.pid)
        file.close()
    except:
        logger.exception('**Error in multiAutoSolAction**')

def multiAutoBuildAction(input,output,logger):
    """
    Run phenix.autobuild.
    """
    logger.debug('multiAutoBuildAction')
    try:    
        file = open('autobuild.log','w')
        myoutput = subprocess.Popen(input,shell=True,stdout=file,stderr=file)
        output.put(myoutput.pid)
        file.close()
    except:
        logger.exception('**Error in multiAutoBuildAction**')

def multiAutoMR(input,output,logger):
    """
    Run phenix.automr.
    """
    logger.debug('multiAutoMR')
    try:    
        file = open('automr.log','w')
        myoutput = subprocess.Popen(input,shell=True,stdout=file,stderr=file)
        output.put(myoutput.pid)
        file.close()
    except:
        logger.exception('**Error in multiAutoMR**')

def multiShelxDAction(input,output,int,logger):
    """
    Run ShelxD.
    """
    logger.debug('multiShelxDAction')
    try:        
        if int == '-1':
            file = open('shelx.log','w')
        else:
            file = open('shelx'+str(int)+'.log','w')
        myoutput = subprocess.Popen(input,shell=True,stdout=file,stderr=file)
        output.put(myoutput.pid)
        file.close()
    except:
        logger.exception('**Error in multiShelxDAction**')
    
def multiShelxEAction(input,output,logger,invert=1):
    """
    Run ShelxE.
    """
    logger.debug('multiShelxEAction')
    try:
        if invert == 1:
            file = open('shelxe.log','w')
        elif invert == 2:
            file = open('shelxe_i.log','w')
        elif invert == 3:
            file = open('shelxe_trace.log','w')
        else:
            file = open('shelxe_i_trace.log','w')
        myoutput = subprocess.Popen(input,shell=True,stdout=file,stderr=file)
        output.put(myoutput.pid)
        file.close()
    except:
        logger.exception('**Error in multiShelxEAction**')
      
if __name__ == '__main__':
    #start logging
    LOG_FILENAME = '/tmp/rapd_agent_sad.log'
    # Set up a specific logger with our desired output level
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,maxBytes=100000,backupCount=5)
    #add a formatter
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('AutoSolve.__init__')
    import ../test_data/rapd_auto_testinput as Input
    input = Input.input()
    tmp = AutoSolve(input,logger=logger)
    

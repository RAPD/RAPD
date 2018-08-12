"""
This file is part of RAPD

Copyright (C) 2012-2018, Cornell University
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

__created__ = "2012-10-25"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Production"

from multiprocessing import Process, Queue, cpu_count
import os, time, shutil, numpy
from rapd_communicate import Communicate
import rapd_utils as Utils
import rapd_beamlinespecific as BLspec
import rapd_parse as Parse
import rapd_summary as Summary

class AutoSolve(Process, Communicate):
  def __init__(self, input, logger=None):
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
    #Submit 'unmerged original index' data to SHELXC.
    self.unmerged                           = True
    #For running multiple ShelxD jobs in parallel like SGXPRO.
    self.multiShelxD                        = True
    #Limit launching of SHELXD jobs to this number (FALSE to disable).
    self.shelxd_limit                       = 32
    #self.shelxd_limit                       = False
    #Set to allow AutoSol to run on solution
    self.autosol_build                      = True
    #Set to make ShelxE run autotracing
    self.shelx_build                        = True
    #Set to make Buccaneer build
    self.buccaneer_build                    = True
    #Set verbose output
    self.verbose                            = True
    
    #This is a dummy value to say there is signal present. There
    #are commented out lines that determine if signal is present and auto solve by SAD.
    self.anom_signal                        = True
    #variables to set
    self.autosol_timer                      = False
    self.autosol_log                        = []
    self.autosol_jobs                       = {}
    self.autosol_results                    = False
    self.autosol_failed                     = False
    self.autosol_summary                    = False
    self.autosol_data_file                   = False
    self.autosol_data_files                  = False
    self.autobuild_timer                    = False
    self.autobuild_log                      = []
    self.autobuild_output                   = False
    self.autobuild_results                  = False
    self.autobuild_failed                   = False
    self.autobuild_summary                  = False
    self.buccaneer_output                   = {}
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
    self.tooltips                           = False
    self.shelxd_dict                        = {}
    self.shelx_nosol                        = False
    self.shelx_failed                       = False
    self.shelxd_failed                      = False
    self.shelx_dir                          = False
    self.both_hands                         = False
    self.pp                                 = False
    self.cell                               = False
    self.cell2                              = False
    self.ha_num1                            = False
    self.ha_num2                            = False
    self.input_sg                           = False
    self.cubic                              = False
    self.many_sites                         = False
    self.no_data_file                        = False
    self.no_data_file2                       = False
    self.data_files                          = False
    self.njobs                              = 1
    self.iteration                          = 0
    self.sc                                 = {}
    
    self.data_file = self.data.get('original').get('mtz_file',None)
    if self.data_file == None:
      self.data_file = self.preferences.get('request').get('input_sca',None)
    if self.data_file == None:
      self.multi_input = True
    else:
      self.multi_input = False
    self.solvent_content  = self.preferences.get('solvent_content',0.55)
    #self.sample_type = self.preferences.get('sample_type','Protein')
    self.sample_type = self.preferences.get('request').get('sample_type','Protein')
    self.space_group = self.preferences.get('spacegroup')
    self.wave = self.preferences.get('request').get('wavelength')
    self.ha = self.preferences.get('request').get('ha_type','Se')
    self.ha_num = self.preferences.get('request').get('ha_number',0)
    self.shelxd_try = self.preferences.get('request').get('shelxd_try',1024)
    if self.shelxd_try == 0:
      self.shelxd_try = 1024
    #Set limit of 10240 tries
    if self.shelxd_try > 10240:
      self.shelxd_try = 10240
    self.resolution = self.preferences.get('request').get('sad_res')
    self.nproc = cpu_count()

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
    #self.cluster_use = Utils.checkCluster()
    self.cluster_use = BLspec.checkCluster()
    if self.cluster_use:
      self.test = False
      self.verbose = False
      #pass
    """
    else:
      if self.shelxd_try == 1024:
        self.shelxd_try = 100
    """
    #******BEAMLINE SPECIFIC*****
    
    Process.__init__(self,name='AutoSolve')
    self.start()
      
  def run(self):
    """
    Convoluted path of modules to run.
    """
    if self.verbose:
      self.logger.debug('AutoSolve::run')
    
    self.preprocess()
    
    #Only run if map is input and not implemented yet.
    if self.autobuild:
      self.processAutoBuild()
      self.postprocessAutoBuild()
    else:
      self.preprocessShelx()
      self.processShelx()
      
      self.postprocess(False)
      
      #Run Buccaneer on SHELXE phases
      if self.buccaneer_build:
        if self.shelx_nosol == False:
          #Buccaneer is launched in the shelxQueue because Shelx building may still be going on...(faster)
          if self.shelx_build == False:
            self.processBuccaneer()
          self.postprocessBuccaneer()
      if self.autosol_build:
        if self.shelx_nosol == False:
          #AutoSol is launched in the shelxQueue because Shelx building may still be going on...(faster)
          if self.shelx_build == False:
            self.processAutoSol()
          self.postprocessAutoSol()
          if self.autosol_failed == False:
            #Use Buccaneer to build into the AutoSol maps
            if self.buccaneer_build:
              self.processBuccaneer('autosol')
              self.postprocessBuccaneer()
    
    self.postprocess()
    
  def preprocess(self):
    """
    Things to do before the main process runs
    1. Change to the correct directory
    2. Print out the reference for SAD pipeline
    """
    if self.verbose:
      self.logger.debug('AutoSolve::preprocess')
    #change directory to the one specified in the incoming dict
    self.working_dir = self.setup.get('work')
    if os.path.exists(self.working_dir) == False:
      os.makedirs(self.working_dir)
    os.chdir(self.working_dir)
    self.unmerged_queue = {}
    if self.multi_input:
      self.preprocessMulti()
    else:
      #Check if integration completed and data_file exists.
      file_type = self.data_file[-3:].upper()
      f = False
      if file_type == 'MTZ':
        self.autosol_data_file = self.data_file
        #Run Scala on unmerged data to create SCA file.
        self.unmerged_queue['SAD'] = Queue()
        if self.unmerged:
          if os.path.basename(self.data_file).startswith('smerge'):
            if os.path.exists(self.data_file.replace('_freer','_sortedMergable')):
              f = self.data_file.replace('_freer','_sortedMergable')
          #Need to separate out the path because users create folders with '_free' in them.
          elif os.path.exists(os.path.join(os.path.dirname(self.data_file),os.path.basename(self.data_file).replace('_free','_mergable'))):
            f = os.path.join(os.path.dirname(self.data_file),os.path.basename(self.data_file).replace('_free','_mergable'))
          if f:
            #David cuts res in Aimless and mergable file comes from XDS ASCII out of Pointless.
            #Have to check resolution of two files and set high res limit to the merged limit if it is too high.
            d0 = Utils.getRes(self)
            d1 = Utils.getRes(self,f)
            if d0-d1 > 0.2:
              f = Utils.setRes(self,f,d0)
            Process(target=Utils.mtz2scaUM,args=(self,f,self.unmerged_queue['SAD'])).start()
          else:
            self.unmerged = False
            Process(target=Utils.mtz2sca,args=(self,self.data_file,self.unmerged_queue['SAD'])).start()
          """
          #There is no res cutoff in XDS file!
          elif os.path.exists(os.path.join(os.path.dirname(self.data_file),os.path.basename(self.data_file).replace('_free.mtz','_XDS.HKL'))):
            self.unmerged_queue['SAD'].put(os.path.join(os.path.dirname(self.data_file),os.path.basename(self.data_file).replace('_free.mtz','_XDS.HKL')))
          """
        else:
          Process(target=Utils.mtz2sca,args=(self,self.data_file,self.unmerged_queue['SAD'])).start()
        
      else:
        self.unmerged = False
    #Get unit cell and SG info (origin of self.input_sg)
    self.input_sg,self.cell,self.cell2,vol = Utils.getMTZInfo(self,False,False,True)
    #Calculate cell volume to see if it is ribosome and turn off ShelxE building.
    if Utils.calcResNumber(self,self.input_sg,False,vol) > 5000:
      self.shelx_build = False
    #print out recognition of the program being used
    self.PrintInfo()
    if self.test:
      self.logger.debug('TEST IS SET "ON"')
      
  def preprocessMulti(self):
    """
    Figure out which datasets are submitted and create SCA files for MAD datasets.
    """
    if self.verbose:
      self.logger.debug('AutoSolve::preprocessMulti')
    try:
      first = True
      #List of possible MAD and SIR datasets in order of hierarchy for cell and SG.
      datasets = ['mtz_NAT','mtz_PEAK','mtz_INFL','mtz_HREM','mtz_LREM','mtz_SIRA']
      self.autosol_data_files = {}
      for data in datasets:
        f = self.preferences.get('request').get(data)
        if f != None:
          self.unmerged_queue[data] = Queue()
          self.autosol_data_files[data] = f
          #inp = []
          #Save the hierarchy of which files exist to calc cell and SG.
          if first:
            self.data_file = f
            first = False
          if f[-3:].upper() == 'MTZ':
            #Convert mtz to sca file for SHELX
            if os.path.basename(f).startswith('smerge'):
              #inp.append(data.split('_')[-1])
              if os.path.exists(f.replace('_freer','_sortedMergable')):
                f = f.replace('_freer','_sortedMergable')
            elif os.path.exists(f.replace('_free','_mergable')):
              f = f.replace('_free','_mergable')
            #inp.append(f)
            if f.count('ergable.mtz'):
              #Process(target=Utils.mtz2scaUM,args=(self,inp,self.unmerged_queue[data])).start()
              Process(target=Utils.mtz2scaUM,args=(self,f,self.unmerged_queue[data])).start()
            else:
              #Process(target=Utils.mtz2sca,args=(self,inp,self.unmerged_queue[data])).start()
              Process(target=Utils.mtz2sca,args=(self,f,self.unmerged_queue[data])).start()
          else:
            out = os.path.join(os.getcwd(),os.path.basename(f))
            shutil.copy(f,out)
            self.unmerged_queue[data].put(out)
      if len(self.unmerged_queue.keys()) == 0:
        self.no_data_file = True
        self.postprocess(True)
      elif len(self.unmerged_queue.keys()) == 1:
        self.no_data_file2 = True
        self.postprocess(True)

    except:
      self.logger.exception('***ERROR in preprocessMulti**')

  def preprocessShelx(self):
    """
    Create SHELX CDE input.
    """
    if self.verbose:
      self.logger.debug('AutoSolve::preprocessShelx')
    try:
      #Check to see if anomalous signal present
      if self.gui:
        #self.anom_signal = Utils.checkAnom(self)
        pass
      if self.anom_signal:
        #Check if SG is cubic.
        con = Utils.convertSG(self,self.input_sg)
        try:
          if int(con) >= 196:
            self.cubic = True
        except:
          pass
        #Figure out which SG's to Run Shelx and do it.
        self.run_sg = Utils.subGroups(self,Utils.convertSG(self,self.input_sg),'shelx')
        #Setup the REDIS database for limiting all the jobs.
        if self.shelxd_limit:
          import redis,random
          self.red = redis.Redis('164.54.212.169',6380)#remote
          self.red_name = 'sad_throttler_%s'%random.randint(0,5000)
          for i in range(self.shelxd_limit):
            self.red.lpush(self.red_name,1)
        else:
          self.red_name = False
        if self.multiShelxD:
          #Number of SG's to try.
          n = len(self.run_sg)
          if self.cluster_use or self.test:
            #Using the shelxd_mp64 the number of tries should be a multiple of 16.
            #self.njobs = int(round(self.shelxd_try/512))
            if self.shelxd_try > 1025:
              self.njobs = int(round(self.shelxd_try/512))
            else:
              self.njobs = int(round(self.shelxd_try/256))
            if self.njobs < 1:
              self.njobs = 1
          else:
            self.njobs = int(self.nproc/n)
            if self.njobs == 0:
              self.njobs = 1
        else:
          self.njobs = 1
        if self.unmerged:
          if self.multi_input:
            self.data_files = {}
            for data in self.unmerged_queue.keys():
              self.data_files[data] = self.unmerged_queue[data].get()
          else:
            self.data_file = self.unmerged_queue['SAD'].get()
        elif self.data_file[-3:].upper() == 'MTZ':
          shutil.copy(self.data_file,os.getcwd())
          self.data_file = self.unmerged_queue['SAD'].get()
      else:
        self.shelx_failed = True
        self.shelx_nosol = True

    except:
      self.logger.exception('***ERROR in preprocessShelx**')
  
  def processAutoSol(self):
    """
    Preparing and starting phenix.autosol
    """
    if self.verbose:
      self.logger.debug('AutoSolve::processAutoSol')
    
    try:
      mad = False
      seq = self.preferences.get('request').get('sequence')
      inv = self.shelx_results.get('Shelx results').get('shelxe_inv_sites')
      
      #Fix SG if H3/H32 is indicated
      sg = Utils.fixSG(self,self.shelx_sg)
      
      command = 'phenix.autosol atom_type=%s have_hand=True solvent_fraction=%s space_group=%s quick=True nproc=%s ncycle_refine=1'%(
                  self.ha,self.solvent_content,sg,self.nproc)
      if self.multi_input:
        f = open('junk.eff','w')
        f.write('autosol {\n')
        if self.autosol_data_files.keys().count('mtz_SIRA') == 1:
          f.write('native { data = "%s"}\n'%self.autosol_data_files['mtz_NAT'])
          f.write('deriv { data = "%s"\n'%self.autosol_data_files['mtz_SIRA'])
          f.write('        lambda = %s}\n'%Utils.getWavelength(self,self.autosol_data_files['mtz_SIRA']))
        else:
          d = {'mtz_PEAK': 'peak','mtz_INFL': 'inf','mtz_HREM':'high','mtz_LREM':'low'}
          for data in self.autosol_data_files.keys():
            filename = self.autosol_data_files[data]
            f.write('wavelength { data = "%s"\n'%filename)
            f.write('             lambda = %s\n'%Utils.getWavelength(self,filename))
            f.write('             wavelength_name = %s}\n'%d[data])
        f.write('}\n')
        f.close()
        mad = True
      else:
        if self.autosol_data_file:
          command += ' data=%s'%self.autosol_data_file
        else:
          command += ' data=%s'%self.data_file.replace('.sca','.mtz')
      if self.sample_type == 'Ribosome':
        command += ' chain_type=RNA'
      else:
        command += ' chain_type=%s'%self.sample_type
      if self.ha == 'Se':
        command += ' semet=True'
      if seq == '':
        command += ' residues=%s'%Utils.calcResNumber(self,self.shelx_sg)
      else:
        command += ' sequence="%s"'%seq
      #need path for sites files
      path  = os.path.join(os.getcwd(),'junk.ha')
      ipath = path.replace('junk.ha','junk_i.ha')
      if self.both_hands == False:
        r = 1
        if inv == 'True':
          command += ' sites=%s sites_file=%s'%(self.ha_num2,ipath)
        else:
          command += ' sites=%s sites_file=%s'%(self.ha_num1,path)
      else:
        r = 2
        command_inv = command
        command += ' sites=%s sites_file=%s'%(self.ha_num1,path)
        command_inv += ' sites=%s sites_file=%s'%(self.ha_num2,ipath)
      if mad:
        command += ' %s'%os.path.join(os.getcwd(),'junk.eff')
        if self.both_hands:
          command_inv += ' %s'%os.path.join(os.getcwd(),'junk.eff')
      for i in range(r):
        if i == 0:
          c = command
        else:
          c = command_inv
        if self.verbose:
          self.logger.debug(c)
        self.autosol_log.append(c)
        Utils.folders(self,'AutoSol_%s'%i)
        print c
        if self.test:
          self.autosol_jobs[str(i)] = Process(target=Utils.processLocal,args=('ls',self.logger))
        else:
          #self.autosol_jobs[str(i)] = Process(target=Utils.processCluster,args=(self,(c,'autosol.log')))
          self.autosol_jobs[str(i)] = Process(target=BLspec.processCluster,args=(self,(c,'autosol.log')))
        self.autosol_jobs[str(i)].start()
    
    except:
      self.logger.exception('**ERROR in processAutoSol**')

  def processAutoBuild(self):
    """
    Preparing and starting phenix.autobuild
    """
    if self.verbose:
      self.logger.debug('AutoSolve::processAutoBuild')
    try:
      m = self.preferences.get('request').get('input_map')
      seq = self.preferences.get('request').get('sequence')
      command = 'phenix.autobuild map_file=%s solvent_fraction=%s chain_type=%s sequence="%s" '+\
                'number_of_parallel_models=1 n_cycle_build_max=1 n_cycle_rebuild_max=0 ncycle_refine=1 nproc=4'%(
                  seq,m,self.solvent_content,self.sample_type)
      if self.autosol_data_file:
        command += ' data=%s'%self.autosol_data_file
      else:
        command += ' data=%s'%self.data_file
      self.autobuild_log.append(command)
      if self.verbose:
        self.logger.debug(command)
      if self.test:
        print command
      else:
        #self.autobuild_output = multiprocessing.Process(target=Utils.processLocal,args=((command,'autobuild.log'),self.logger))
        #self.autobuild_output = Process(target=Utils.processCluster,args=(self,(command,'autobuild.log')))
        self.autobuild_output = Process(target=BLspec.processCluster,args=(self,(command,'autobuild.log')))
        self.autobuild_output.start()

    except:
      self.logger.exception('**ERROR in processAutoBuild**')

  def processBuccaneer(self,run='shelxe'):
    """
    Run Buccaneer for model building.
    """
    if self.verbose:
      self.logger.debug('AutoSolve::processBuccaneer')
    try:
      log = ['buc.log']
      if run == 'shelxe':
        dir1 = self.shelx_dir
        if self.both_hands:
          mtz = [os.path.join(dir1,'junk.mtz'),os.path.join(dir1,'junk_i.mtz')]
          pdb = [os.path.join(dir1,'buc_shelxe.pdb'),os.path.join(dir1,'buc_shelxe_inv.pdb')]
          log.append('buc_inv.log')
        elif self.shelx_results.get('Shelx results').get('shelxe_inv_sites') == 'True':
          mtz = [os.path.join(dir1,'junk_i.mtz')]
          pdb = [os.path.join(dir1,'buc_shelxe_inv.pdb')]
        else:
          mtz = [os.path.join(dir1,'junk.mtz')]
          pdb = [os.path.join(dir1,'buc_shelxe.pdb')]
      else:
        dir1 = self.autosol_results.get('AutoSol results').get('directory')
        mtz = [os.path.join(dir1,'overall_best_denmod_map_coeffs.mtz')]
        pdb = [os.path.join(dir1,'buc_autosol.pdb')]
      #Change to directory
      os.chdir(dir1)
      #Make seq file
      Utils.makeSeqFile(self)
      command  = 'cbuccaneer -stdin<<eof\ncolin-fo FP,SIGFP\ncolin-phifom PHIM,FOMM\n'
      command += 'seqin seq.pir\nanisotropy-correction\ncycles 3\njobs 12\n'
      for i in range(len(mtz)):
        c1 = command
        c1 += 'mtzin %s\npdbout %s\neof\n'%(mtz[i],pdb[i])
        if self.test == False:
          job = Process(target=Utils.processLocal,args=((c1,log[i]),self.logger))
          job.start()
          self.buccaneer_output[job] = os.path.join(os.getcwd(),log[i])

    except:
      self.logger.exception('**ERROR in processBuccaneer**')

  def processShelx(self):
    """
    Run SHELX for input SG.
    """
    if self.verbose:
      self.logger.debug('AutoSolve::processShelx')
    try:
      sg_name = []
      jobs    = {}
      job     = False
      
      def calc_ha(inp):
        if self.ha_num == 1 and self.ha in ('Se','Br','Cl','I'):
          num = Utils.calcResNumber(self,inp,True)
          if self.ha == 'Se':
            self.ha_num = num
          else:
            self.ha_num = num*2
        #Signal Utils.changeIns to modify INS file to find sites faster
        if self.ha_num > 30:
          self.many_sites = True

      #Start all the ShelxC jobs at the same time.
      for sg in self.run_sg:
        sg2 = Utils.convertSG(self,sg,True)
        sg_name.append(sg2)
        Utils.folders(self,'Shelx_%s'%sg2)
        #Run this on first SG only.
        if job == False:
          calc_ha(sg2)
        job = Process(target=self.processShelxCD,args=(sg2,),name='d_%s'%sg2)
        job.start()
        if self.test == False:
          #Remove the ShelxE logs from the previous run if there was an error.
          if os.path.exists('shelxe.log'):
            os.system('rm -rf shelxe*')
        jobs[sg2] = {'active':[job],'D':job}
      #If shelxD failed, don't waste the time trying to build.
      if self.shelxd_failed == True:
        self.shelxd_failed = False
        self.shelx_build = False
      self.shelxQueue(jobs)
      #Rerun if there was an error after fixing problem.
      if self.shelxd_failed == True:
        if self.iteration <= 1:
          self.iteration += 1
          self.preprocessShelx()
          self.processShelx()
      #Update the results after ShelxE building.
      self.sortShelx(sg_name)

    except:
      self.logger.exception('**ERROR in processShelx**')

  def processShelxCD(self,sg,output=False):
    """
    Run SHELX CD for input SG.
    """
    if self.verbose:
      self.logger.debug('AutoSolve::processShelxCD')
    
    def checkShelxC(counter=5):
      #Catch error when SHELX doesn't have enough memory to read unmerged dataset.
      rerun = False
      for line in open('shelxc.log','r').readlines():
        if line.count('** Not enough memory to store reflections'):
          rerun = True
      if rerun:
        if counter < 15:
          c = command[:-4]
          c+= 'MAXM %s\nEOF\n'%counter
          Utils.processLocal((c,'shelxc.log'),self.logger)
          counter +=1
          checkShelxC(counter)
        
    try:
      #Setup SHELXC command.
      command  = 'shelxc junk <<EOF\nCELL %s\n'%self.cell
      if float(self.resolution) != 0.0:
        command += 'SHEL 999 %s\n'%self.resolution
      command += 'SPAG %s\n'%sg
      if self.multi_input:
        for data in self.data_files.keys():
          #symlink sca file to local directory so path isn't too long for SHELX
          sca = os.path.basename(self.data_files[data])
          if os.path.exists(sca) == False:
            os.symlink(self.data_files[data],sca)
          command += '%s %s\n'%(data[data.find('_')+1:],sca)
      else:
        #symlink sca file to local directory so path isn't too long for SHELX
        sca = os.path.basename(self.data_file)
        if os.path.exists(sca) == False:
          os.symlink(self.data_file,sca)
        command += 'SAD %s\n'%sca
      command += 'FIND %s\nSFAC %s\nEOF\n'%(self.ha_num,self.ha)
      #self.shelx_log0[sg].append(command+'\n')
      
      #TESTING function
      if self.test:
        #Utils.changeIns(self)
        #print command
        pass
      else:
        Utils.processLocal((command,'shelxc.log'),self.logger)
        checkShelxC()
        if self.multiShelxD:
          Utils.changeIns(self)
          for i in range(self.njobs):
            if os.path.exists('junk_fa.ins'):
              os.system('cp junk_fa.ins junk_fa%s.ins'%i)
            if os.path.exists('junk_fa.hkl'):
              os.system('cp junk_fa.hkl junk_fa%s.hkl'%i)
            if self.cluster_use:
              log = os.path.join(os.getcwd(),'shelx%s.log'%i)
              #Remove old logs
              if os.path.exists(log):
                os.system('rm -rf %s'%log)
              if self.shelxd_failed == True:
                #L5 means 5000000 reflections possible
                command1 = 'shelxd -L5 junk_fa%s'%i
              else:
                command1 = 'shelxd junk_fa%s'%i
              if self.shelxd_limit != False:
                self.red.blpop(self.red_name)
              #Process(target=Utils.processCluster,args=(self,(command1,log,8,'phase1.q',self.red_name))).start()
              Process(target=BLspec.processCluster,args=(self,(command1,log,8,'phase1.q',self.red_name))).start()
              #Do a small wait to even out load on cluster nodes
              time.sleep(0.1)
            else:
              command1 = 'shelxd junk_fa%s'%i
              Process(target=Utils.processLocal,args=((command1,'shelx%s.log'%i),self.logger)).start()
        else:
          command1 = 'shelxd junk_fa\n'
          if self.verbose:
            self.logger.debug(command1)
          Process(target=Utils.processLocal,args=((command1,'shelx.log'),self.logger)).start()
        if self.verbose:
          self.logger.debug(command1)

    except:
      self.logger.exception('**Error in processShelxCD**')

  def processShelxE(self,inp,sc=False,trace=False):
    """
    Run SHELXE for input SG.
    """
    if self.verbose:
      self.logger.debug('AutoSolve::processShelxE')
    
    try:
      if trace:
        l = [(' -a1 -q','shelxe_trace.log'),(' -i -a1 -q','shelxe_i_trace.log')]
        #Eliminate write errors to same file
        if os.path.exists('junkt.hkl') == False:
          os.symlink('junk.hkl','junkt.hkl')
        command = 'shelxe junkt'
      else:
        l = [('','shelxe.log'),(' -i','shelxe_i.log')]
        command = 'shelxe junk'
      def run(inp):
        for i in range(len(l)):
          if self.test == False:
            if self.cluster_use:
              #Process(target=Utils.processCluster,args=(self,(inp+l[i][0],l[i][1],'phase2.q,phase1.q'))).start()
              #Process(target=Utils.processCluster,args=(self,(inp+l[i][0],l[i][1],'phase2.q'))).start()
              Process(target=BLspec.processCluster,args=(self,(inp+l[i][0],l[i][1],'phase2.q'))).start()
            else:
              Process(target=Utils.processLocal,args=((inp+l[i][0],l[i][1]),self.logger)).start()

      #command = 'shelxe junk junk_fa -s'+str(self.solvent_content)+' -m20 -h -b'
      #The -b refines the HA position after density is calculated and writes to .hat file!
      #-z adds time
      if sc:
        command += ' junk_fa -m10 -b'
        home = os.getcwd()
      else:
        command += ' junk_fa -s%s -m20 -b'%self.sc[inp]
      if self.ha in ('Se','S'):
        command += ' -h'
      if sc:
        if os.path.exists('junk_fa.res'):
          #Find accurate solvent content between 40-80%. 
          for x in range(40,85,5):
            os.chdir(home)
            Utils.copyShelxFiles(self,x)
            command1 = '%s -s0.%s'%(command,x)
            run(command1)
      else:
        run(command)

    except:
      self.logger.exception('**Error in processShelxE**')

  def postprocessShelx(self,inp,auto=None):
    """
    Read and process parsed Shelx output.
    """
    if self.verbose:
      self.logger.debug('AutoSolve::postprocessShelx')
    try:
      fa = []
      temp = []
      tempe = []
      self.shelx_log0[inp] = []
      Utils.folders(self,'Shelx_%s'%inp)
      #Grab the meaningful ShelxC output
      junk = open('shelxc.log','r').readlines()
      for line in junk:
        #if line.startswith(' ============='):
        if line.count('Reflections read from'):
          index = junk.index(line) -1
      temp.extend(junk[index:])
      self.shelx_log0[inp].extend(junk[index:])
      if self.multiShelxD:
        for i in range(0,self.njobs):
          readlog = open('shelx%s.log'%i,'r').readlines()
          for line in readlog:
            #Save the first shelxd output to display in the log to limit size.
            if i == 0:
              self.shelx_log0[inp].append(line)
            temp.append(line)
        self.shelx_log0[inp].append('---------------Just showing part of SHELXD Results---------------\n\n')
      else:
        readlog = open('shelx.log','r').readlines()
        for line in readlog:
          temp.append(line)
      l = ['shelxe.log','shelxe_i.log','shelxe_trace.log','shelxe_i_trace.log']
      if self.test:
        #Write dummy log files so script finishes.
        for i in range(len(l)):
          if os.path.exists(l[i]) == False:
            os.system('touch %s'%l[i])
      if self.shelx_build:
        #Grab the correct SHELXE log files.
        if auto == None:
          op = [l[2],l[3]]
        elif auto == 'inv':
          op = [l[2],l[1]]
        elif auto == 'ninv':
          op = [l[0],l[3]]
        else:
          op = [l[0],l[1]]
      else:
        op = [l[0],l[1]]
      reade   = open(op[0],'r').readlines()
      readei  = open(op[1],'r').readlines()
      if os.path.exists('junk_fa.res'):
        for line in open('junk_fa.res','r').readlines():
          fa.append(line)
        for line in reade:
          temp.append(line)
          tempe.append(line)
        for line in readei:
          temp.append(line)
          tempe.append(line)

    except:
      self.logger.exception('**Error in postprocessShelx**')
    shelx = Parse.ParseOutputShelx(self,temp,fa)
    if shelx == None:
      self.shelx_results0[inp] = { 'Shelx results'  : 'FAILED'}
      self.shelx_failed = True
      self.clean = False
    elif shelx == 'array':
      self.shelxd_failed = True
      return('kill')
    elif shelx == 'trace failed inv':
      self.postprocessShelx(inp,'inv')
    elif shelx == 'trace failed ninv':
      self.postprocessShelx(inp,'ninv')
    elif shelx == 'trace failed both':
      self.postprocessShelx(inp,'both')
    else:
      self.shelx_results0[inp] = { 'Shelx results' : shelx}
      Utils.convertShelxFiles(self,inp)
      for line in tempe:
        self.shelx_log0[inp].append(line)

  def postprocessShelxE_SC(self):
    """
    Figure out best solvent content for SG.
    """
    if self.verbose:
      self.logger.debug('AutoSolve::postprocessShelxE_SC')
    home = os.getcwd()
    try:
      x = []
      y = []
      for i in range(40,85,5):
        os.chdir(home)
        Utils.folders2(self,str(i))
        x.append(float(i))
        #Put together an input for parsing
        temp = []
        temp.extend((open('shelxe.log','r').readlines()))
        temp.extend((open('shelxe_i.log','r').readlines()))
        out = Parse.ParseOutputShelx(self,temp,(open('junk_fa.res','r').readlines()))
        #Find the max contrast and separate the reg and inv runs
        ind = out['shelxe_contrast'].index(max(out['shelxe_contrast']))
        if ind > len(out['shelxe_contrast'])/2:
          ind -= int(len(out['shelxe_contrast'])/2)
        c1 = out['shelxe_contrast'][:int(len(out['shelxe_contrast'])/2)]
        c2 = out['shelxe_contrast'][int(len(out['shelxe_contrast'])/2):]
        #Save the difference in Contrast
        y.append(float(c1[ind])-float(c2[ind]))
        #Save difference in Pseudo-CC (not smooth).
        #y.append(float(out['shelxe_cc2'][0])-float(out['shelxe_cc2'][1]))
      #Return the min or max of the polynomial as the SC.
      peak = round(float(numpy.polynomial.polynomial.Polynomial.fit(x,y,2).deriv(1).roots()[0]))*0.01
      if peak < 0.35:
        peak = 0.55
      elif peak > 0.85:
        peak = 0.55
      os.chdir(home)
      return (peak)

    except:
      self.logger.exception('**Error in postprocessShelxE_SC**')
      os.chdir(home)
      return(0.55)

  def postprocessAutoSol(self):
    """
    Queue for running autosol for both hands and saving results.
    """
    if self.verbose:
      self.logger.debug('AutoSolve::postprocessAutoSol')
    try:
      def parse(inp):
        Utils.folders(self,'AutoSol_%s'%inp)
        readlog = open('autosol.log','r').readlines()
        self.autosol_log.extend(readlog)
        return(Parse.ParseOutputAutoSol(self,readlog))
      
      autosol = {}
      bcc = {}
      timer = 0
      counter = len(self.autosol_jobs.keys())
      jobs = self.autosol_jobs.keys()
      while counter != 0:
        for job in jobs:
          if self.autosol_jobs[job].is_alive() == False:
            jobs.remove(job)
            autosol[job] = parse(job)
            counter -= 1
          if self.autosol_timer:
            if timer >= self.autosol_timer:
              Utils.killChildren(self,self.autosol_jobs[job].pid)
              autosol[job] = Parse.setAutoSolFalse('TO')
              if self.verbose:
                self.logger.debug('phenix.autosol timed out.')
              self.autosol_log.append('phenix.autosol timed out\n')
              counter -= 1
          time.sleep(1)
          timer += 1
      #Keys will be str(x).
      for x in range(len(autosol.keys())):
        if autosol[str(x)].get('bayes-cc',False) in ('ERROR','TO',False):
          bcc[str(x)] = 0.0
        else:
          bcc[str(x)] = float(autosol[str(x)].get('bayes-cc'))
      if sum(bcc.values()) == 0.0:
        self.autosol_results = { 'AutoSol results' : 'FAILED'}
        self.autosol_failed = True
      elif len(bcc.keys()) == 1:
        self.autosol_results = { 'AutoSol results' : autosol[bcc.keys()[0]] }
      else:
        if bcc['0'] > bcc['1']:
          self.autosol_results = { 'AutoSol results'     : autosol['0'] }
        else:
          self.autosol_results = { 'AutoSol results'     : autosol['1'] }

    except:
      self.logger.exception('**Error in postprocessAutoSol.**')

  def postprocessAutoBuild(self):
    """
    Get phenix.autobuild results.
    """
    if self.verbose:
      self.logger.debug('AutoSolve::postprocessAutoBuild')
    try:
      temp = []
      d = {}
      index = 1
      timer = 0
      parse = False
      finished = False
      if self.test == False:
        while self.autobuild_output.is_alive():
          if self.test:
            readlog = open('autobuild2.log','r').readlines()
          else:
            readlog = open('autobuild.log','r').readlines()
          for line in readlog:
            temp.append(line)
            if line.startswith('from: refine'):
              end = line.split()[1]
              if d.has_key(end):
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
            d[end] = index
            autobuild = Parse.ParseOutputAutoBuild(self,log)
            self.autobuild_results = { 'AutoBuild results'  : autobuild }
            if self.autobuild_results['AutoBuild results'] == None:
              self.autobuild_results = { 'AutoBuild results' : 'FAILED'}
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
          time.sleep(10)
          timer += 10
          if self.verbose:
            number = round(timer%1,1)
            if number in (0.0,30.0):
              print 'Waiting for AutoBuild to finish %s seconds'%timer
          if self.autobuild_timer:
            if timer >= self.autobuild_timer:
              Utils.killChildren(self,self.autobuild_output.pid)
              print 'phenix.autobuild timed out.'   
              self.logger.debug('phenix.autobuild timed out.')
              self.autobuild_log.append('phenix.autobuild timed out\n')
              break
      self.autobuild_log.extend(open('autobuild.log','r').readlines())

    except:
      self.logger.exception('**Error in postprocessAutoBuild.**')

  def postprocessBuccaneer(self):
    """
    Get Buccaneer results
    """
    if self.verbose:
      self.logger.debug('AutoSolve::postprocessBuccaneer')
    try:
      timer = 0
      jobs = self.buccaneer_output.keys()
      for i in range(0,len(jobs)):
        if self.test == False:
          while jobs[i].is_alive():
            time.sleep(1)
            timer += 1
            if self.autosol_timer:
              if timer >= self.autosol_timer:
                Utils.killChildren(self,jobs[i].pid)
                if self.verbose:
                  print 'Buccaneer timed out.'
                  self.logger.debug('Buccaneer timed out.')
                self.autosol_log.append('Buccaneer timed out\n')
                break
          #Remove finished jobs
          del self.buccaneer_output[jobs[i]]

    except:
      self.logger.exception('**Error in postprocessBuccaneer**')

  def shelxQueue(self,jobs):
    """
    Waits for the Shelx to finish then runs postprocessShelx.
    """
    if self.verbose:
        self.logger.debug('AutoSolve::shelxQueue')
    try:
        timed_out = False
        timer = 0
        kill = False
        sg_name = jobs.keys()
        counter = len(sg_name)
        counter2 = counter
        while counter != 0:
          for sg in sg_name:
            for job in jobs[sg].get('active'):
              if job.is_alive() == False:
                jobs[sg].get('active').remove(job)
                Utils.folders(self,'Shelx_%s'%sg)
                if jobs[sg].get('D',False) == job:
                  if self.multiShelxD:
                    self.sortShelxD()
                  l = []
                  #Get accurate SC for SG.
                  j = Process(target=self.processShelxE,args=(sg,True,False),name='e_test_%s'%sg)
                  j.start()
                  jobs[sg].update({'E_SC':j})
                  l.append(j)
                  jobs[sg].get('active').extend(l)
                elif jobs[sg].get('E_SC',False) == job:
                  #Save the SC for that SG.
                  self.sc[sg] = self.postprocessShelxE_SC()
                  #Launch regular SHELXE runs.
                  l = []
                  j = Process(target=self.processShelxE,args=(sg,False,False),name='e_nt_%s'%sg)
                  j.start()
                  jobs[sg].update({'E_NT':j})
                  l.append(j)
                  if self.shelx_build:
                    j1 = Process(target=self.processShelxE,args=(sg,False,True),name='e_t_%s'%sg)
                    j1.start()
                    jobs[sg].update({'E_T':j1})
                    l.append(j1)
                  jobs[sg].get('active').extend(l)
                elif jobs[sg].get('E_NT',False) == job:
                  j = self.postprocessShelx(sg,'notrace')
                  if self.shelx_build:
                    if j == 'kill':
                      kill = True
                    else:
                      counter2 -= 1
                  else:
                    counter -= 1
                elif jobs[sg].get('E_T',False) == job:
                  self.postprocessShelx(sg)
                  if self.shelx_build:
                    counter -= 1
          time.sleep(1)
          timer += 1
          """
          if self.verbose:
            number = round(timer%1,1)
            if number in (0.0,1.0):
              print 'Waiting for SHELXCDE to finish '+str(timer)+' seconds'
          """
          if self.shelx_timer:
            if timer >= self.shelx_timer:
              timed_out = True
              break
          if kill:
            timed_out = True
            break
          #Launch AutoSol if shelx building is turned on, b/c Shelx building may still be going on...
          if self.shelx_build:
            if counter2 == 0:
              counter2 = -1
              self.sortShelx(sg_name)
              self.postprocess(False)
              if self.shelx_nosol == False:
                if self.autosol_build:
                  self.processAutoSol()
                if self.buccaneer_build:
                  self.processBuccaneer()
        if timed_out:
          self.logger.debug('SHELXCDE timed out.')
          print 'SHELXCDE timed out.'
          for sg in sg_name:
            Utils.folders(self,'Shelx_%s'%sg)
            if self.multiShelxD:
              self.sortShelxD()
            for job in jobs[sg]:
              job.terminate()
        self.logger.debug('SHELXCDE finished.')
        #Remove the Redis database
        if self.shelxd_limit:
          self.red.delete(self.red_name)

    except:
      self.logger.exception('**ERROR in shelxQueue**')

  def sortShelxD(self):
    """
    Sort best fa file from multiple ShelxD runs.
    """
    if self.verbose:
      self.logger.debug('AutoSolve::sortShelxD')
    try:
      if self.njobs == 1:
        if os.path.exists('junk_fa0.res'):
          shutil.copy('junk_fa0.res','junk_fa.res')
        if os.path.exists('junk_fa0.pdb'):
          shutil.copy('junk_fa0.pdb','junk_fa.pdb')
      else:
        #ccw = []
        cfom = []
        for i in range(0,self.njobs):
          if os.path.exists('junk_fa%s.res'%i):
            for line in open('junk_fa%s.res'%i,'r').readlines():
              if line.startswith('REM Best'):
                #ccw.append(float(line.split()[7]))
                cfom.append(float(line.split()[9]))
              if line.startswith('REM TRY'):
                #ccw.append(float(line.split()[6]))
                cfom.append(float(line.split()[8]))
        """
        if len(ccw) != 0:
          index = numpy.argmax(ccw)
          os.system('cp junk_fa%s.res junk_fa.res'%index)
          os.system('cp junk_fa%s.pdb junk_fa.pdb'%index)
        """
        if len(cfom) != 0:
          index = numpy.argmax(cfom)
          os.system('cp junk_fa%s.res junk_fa.res'%index)
          os.system('cp junk_fa%s.pdb junk_fa.pdb'%index)
    except:
      self.logger.exception('**Error in sortShelxD**')

  def sortShelx(self,inp):
    """
    Sort SHELX results to find most promising SG.
    """
    if self.verbose:
      self.logger.debug('AutoSolve::sortShelx')
    try:
      cc = []
      cc_f = []
      ccw = []
      ccw_f = []
      fom = []
      fom_f = []
      #fom_s = []
      cfom = []
      cfom_f = []
      inv = []
      nosol = []
      for line in inp:
        cc.append(self.shelx_results0[line].get('Shelx results').get('shelxd_best_cc'))
        ccw.append(self.shelx_results0[line].get('Shelx results').get('shelxd_best_ccw'))
        cfom.append(self.shelx_results0[line].get('Shelx results').get('shelxd_best_cfom'))
        fom.append(self.shelx_results0[line].get('Shelx results').get('shelxd_fom'))
        inv.append(self.shelx_results0[line].get('Shelx results').get('shelxe_inv_sites'))
        nosol.append(self.shelx_results0[line].get('Shelx results').get('shelxe_nosol'))
      cc_f = [float(line) for line in cc]
      #max_cc = max(cc_f)
      index_cc = numpy.argmax(cc_f)
      ccw_f = [float(line) for line in ccw]
      #max_ccw = max(ccw_f)
      index_ccw = numpy.argmax(ccw_f)
      cfom_f = [float(line) for line in cfom]
      max_cfom = max(cfom_f)
      index_cfom = numpy.argmax(cfom_f)
      for line in fom:
        max1 = max([float(num) for num in line])
        fom_f.append(max1)
        #fom_s.append(str(max1))
      #max_fom = max(fom_f)
      index_fom = numpy.argmax(fom_f)
      #sg = inp[index_ccw]
      sg = inp[index_cfom]
      #if nosol[index_ccw] == 'True':
      if nosol[index_cfom] == 'True':
        self.both_hands = True
      #if inv[index_ccw] == 'True':
      if inv[index_cfom] == 'True':
        self.shelx_sg = Utils.convertSG(self,Utils.checkInverse(self,Utils.convertSG(self,sg))[0],True)
      else:
        self.shelx_sg = sg
      self.shelx_results = self.shelx_results0[sg]
      self.shelx_log = self.shelx_log0[sg]
      for x in range(len(inp)):
        self.shelxd_dict[inp[x]] = {'cc':cc[x],'ccw':ccw[x],'fom':fom_f[x],'cfom':cfom_f[x]}
      #if str(max_ccw).startswith('0.0'):
      if str(max_cfom).startswith('0.0'):
        self.shelx_nosol = True
      else:
        Utils.folders(self,'Shelx_%s'%sg)
        self.shelx_dir = os.getcwd()
        Utils.makeHAfiles(self)
        #Convert phs to mtz for model building
        if os.path.exists('junk.mtz') == False:
          Utils.phs2mtz(self,'junk.phs')
        if os.path.exists('junk_i.mtz') == False:
          Utils.phs2mtz(self,'junk_i.phs')
        
        #Check if solution is above thresholds
        if len(ccw) == 1:
          #if max_ccw < 13:
          if max_cfom < 25:
            self.shelx_nosol = True
        else:
          #Check if solution with highest ccw also has highest cc or fom.
          #if index_ccw not in (index_cc,index_fom):
          if index_cfom not in (index_cc,index_ccw,index_fom):
            self.shelx_nosol = True
      #Set solvent content
      if self.shelx_nosol == False:
        self.solvent_content = self.sc[sg]

    except:
      self.logger.exception('**ERROR in sortShelx**')

  def postprocess(self,final=True):
    """
    Things to do after the main process runs
    1. Return the data through the pipe
    """
    if self.verbose:
      self.logger.debug('AutoSolve::postprocess')
    #Run summary files for each program to print to screen        
    output = {}
    sad_status = {}
    failed = False
    if final:
      self.pp = True
      if self.no_data_file or self.no_data_file2:
        self.shelx_results = {}
        self.shelx_results['Shelx results'] = Parse.setShelxResults(self,'user input error')
        self.anom_signal = False
        self.shelx_failed = True
        sad_status['sad_status'] = 'SUCCESS'
    
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
          path = self.autobuild_results.get('AutoBuild results').get('AutoBuild_dir')+'/TEMP0'
          pdb = self.autobuild_results.get('AutoBuild results').get('AutoBuild_pdb')
          mtz = self.autobuild_results.get('AutoBuild results').get('AutoBuild_mtz')
          shutil.copy(os.path.join(path,pdb),self.working_dir)
          shutil.copy(os.path.join(path,mtz),self.working_dir)
          l= [(pdb,'Autosol best pdb'),(mtz,'Autosol best mtz')]
          os.chdir(self.working_dir)
          for i in range(len(l)):
            if os.path.exists(os.path.join(self.working_dir,l[i][0])):
              output[l[i][1]]  = os.path.join(self.working_dir,l[i][0])
              os.system('tar -rf %s %s'%(tar,l[i][0]))
            else:
              output[l[i][1]]  = 'None'
          if os.path.exists(os.path.join(self.working_dir,tar)):
            os.system('bzip2 -qf %s'%os.path.join(self.working_dir,tar))
            output['Autosol tar']  = os.path.join(self.working_dir,tar).replace('.tar','.tar.bz2')
          else:
            output['Autosol tar']  = 'None'
          #Save AutoSol Results to None since AutoBuild ran instead.
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
          self.shelx_results.get('Shelx results').update({'shelx_no_solution': str(self.shelx_nosol)})
      else:
        self.plotShelxFailed()
        self.shelx_results.get('Shelx results').update({'shelx_no_solution': 'True'})
      self.htmlSummaryShelx()
      if self.autosol_build:
        if final:
          if self.anom_signal:
            if self.shelx_nosol == False:
              if self.autosol_failed == False:
                Summary.summaryAutoSol(self)
      self.htmlSummaryAutoSol()
      #get path of html files
      if self.gui:
        e = '.php'
      else:
        e = '.html'
      l = [('jon_summary_shelx%s'%e,'Shelx summary html'),
           ('plots_shelx%s'%e,'Shelx plots html'),
           ('jon_summary_autosol%s'%e,'Autosol html')]
      for i in range(len(l)):
        try:
          if os.path.exists(os.path.join(self.working_dir,l[i][0])):
            output[l[i][1]] = os.path.join(self.working_dir,l[i][0])
          else:
            output[l[i][1]] = 'None'
        except:
          self.logger.exception('**Could not update path of %s file.**'%l[i][0])
          output[l[i][1]]   = 'FAILED'
          failed = True
      
      #tar and copy best Shelx files to working dir.
      #Set path assuming fail (backwards to save space).
      self.shelx_results.get('Shelx results').update({'shelx_tar': 'None'})
      if self.anom_signal:
        try:
          tar_path = os.path.join(self.working_dir,'shelx_%s.tar'%self.shelx_sg)
          #list all possible files
          l = [os.path.join(self.shelx_dir,'%s.hat'%self.shelx_sg),
               os.path.join(self.shelx_dir,'%s.phs'%self.shelx_sg),
               self.shelx_results.get('Shelx results').get('shelxe_trace_pdb'),
               os.path.join(self.shelx_dir,'buc_shelxe.pdb'),os.path.join(self.shelx_dir,'buc_shelxe_inv.pdb')]
          for f in l:
            if os.path.exists(f):
              os.system('tar -C %s -rf %s %s'%(os.path.dirname(f),tar_path,os.path.basename(f)))
          if os.path.exists(tar_path):
            os.system('bzip2 -qf %s'%tar_path)
            if os.path.exists('%s.bz2'%tar_path):
              self.shelx_results.get('Shelx results').update({'shelx_tar': '%s.bz2'%tar_path})
        except:
          self.logger.exception('**Could not update path of shelx ha and phs files.**')
          self.clean = False
          failed = True
      else:
        pass
        #Parse.setShelxNoSignal(self)
         
      try:
        #For AutoSol files
        #Set initial
        output['Autosol tar'] = 'None'
        if final:
          if self.anom_signal:
            if self.shelx_nosol == False:
              if self.autosol_build:
                if self.autosol_failed:
                  output['Autosol tar'] = 'FAILED'
                  failed = True
                else:
                  tar_path = os.path.join(self.working_dir,'autosol_files.tar')
                  dir1 = self.autosol_results.get('AutoSol results').get('directory')
                  #list all possible files
                  l = [os.path.join(dir1,'overall_best.pdb'),os.path.join(dir1,'overall_best_denmod_map_coeffs.mtz'),
                          os.path.join(dir1,'buc_autosol.pdb'),os.path.join(dir1,'overall_best_refine_data.mtz')]
                  for f in l:
                    if os.path.exists(f):
                      os.system('tar -C %s -rf %s %s'%(os.path.dirname(f),tar_path,os.path.basename(f)))
                  if os.path.exists(tar_path):
                    os.system('bzip2 -qf %s'%tar_path)
                    if os.path.exists('%s.bz2'%tar_path):
                      output['Autosol tar']  = '%s.bz2'%tar_path
                  sad_status['sad_status'] = 'Success'
              else:
                self.autosol_results = { 'AutoSol results': Parse.setAutoSolFalse()}
                #sad_status['sad_status'] = 'Success'
      except:
        output['Autosol tar'] = 'FAILED'
        failed = True
        self.clean = False
        self.logger.exception('**Could not put AutoSol tar together**')

    #Save dict with output files
    output_files = {'Output files' : output}
    #Utils.pp(output)
    #print self.shelx_results.get('Shelx results').get('shelx_tar')
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
      results = {}
      if sad_status:
        results.update(sad_status)
      if self.shelx_results:
        results.update(self.shelx_results)
      results.update({ 'Cell analysis results': 'None' })
      if self.autosol_results:
        results.update(self.autosol_results)
      results.update(output_files)
      if len(self.input) == 6:
        del self.input[5]
      self.input.append(results)
      if self.gui:
        self.sendBack2(self.input)
    except:
      self.logger.exception('**Could not send results to pipe.**')

    if final:
      #Cleanup my mess.
      try:
          if self.clean:
            os.chdir(self.working_dir)
            rm_folders = 'rm -rf Shelx_* Phaser_* AutoSol_* *.com *.sca *.phs *.hat'
            if self.verbose:
              self.logger.debug(rm_folders)
            os.system(rm_folders)

      except:
        self.logger.exception('**Could not cleanup**')

      #Say job is complete.
      t = round(time.time()-self.st)
      self.logger.debug('-------------------------------------')
      self.logger.debug('RAPD AutoSolve complete.')
      self.logger.debug('Total elapsed time: %s seconds'%t)
      self.logger.debug('-------------------------------------')
      print '\n-------------------------------------'
      print 'RAPD AutoSolve complete.'
      print 'Total elapsed time: %s seconds'%t
      print '-------------------------------------'        
      #sys.exit(0) #did not appear to end script with some programs continuing on for some reason.
      os._exit(0)

  def plotShelx(self):
    """
    generate plots html/php file
    """ 
    if self.verbose:     
      self.logger.debug('AutoSolve::plotShelx')
    #try:
    shelxc_res       = self.shelx_results.get('Shelx results').get('shelxc_res')
    shelxc_isig      = self.shelx_results.get('Shelx results').get('shelxc_isig')
    shelxc_comp      = self.shelx_results.get('Shelx results').get('shelxc_comp')
    shelxc_dsig      = self.shelx_results.get('Shelx results').get('shelxc_dsig')
    #shelxc_chi       = self.shelx_results.get('Shelx results').get('shelxc_chi-sq')
    shelxc_cc        = self.shelx_results.get('Shelx results').get('shelxc_cchalf')
    shelx_data       = self.shelx_results.get('Shelx results').get('shelx_data')
    shelxd_try       = self.shelx_results.get('Shelx results').get('shelxd_try')
    shelxd_cca       = self.shelx_results.get('Shelx results').get('shelxd_cca')
    shelxd_ccw       = self.shelx_results.get('Shelx results').get('shelxd_ccw')
    shelxd_fom       = self.shelx_results.get('Shelx results').get('shelxd_fom')
    #shelxd_cfom      = self.shelx_results.get('Shelx results').get('shelxd_cfom')
    shelxd_best_occ  = self.shelx_results.get('Shelx results').get('shelxd_best_occ')
    shelxe_contrast  = self.shelx_results.get('Shelx results').get('shelxe_contrast')
    shelxe_con       = self.shelx_results.get('Shelx results').get('shelxe_con')
    shelxe_res       = self.shelx_results.get('Shelx results').get('shelxe_res')
    shelxe_mapcc     = self.shelx_results.get('Shelx results').get('shelxe_mapcc')

    a = -1
    #Placeholders for specific settings for each plot
    l = [['SHELXC1','&ltI/sig&gt vs. Resolution','Resolution(A)','M e a n &nbsp I / s i g',
         'meanIsig',(shelxc_res,shelxc_isig),'"Resolution (A): " + x + ", Mean I/sig: " + y);\n'],
         ['SHELXC2','Completeness vs. Resolution','Resolution(A)','C o m p l e t e n e s s',
          'completeness',(shelxc_res,shelxc_comp),'"Resolution (A): " + x + ", %Completeness: " + y);\n'],
         ['SHELXC3','&ltd"/sig&gt vs. Resolution','Resolution(A)','M e a n &nbsp d" / s i g',
          'dsig',(shelxc_res,shelxc_dsig),'\'Resolution (A): \' + x + \', Mean d"/sig: \' + y);\n'],
         ['SHELXD1','CCall vs. CCweak','CCweak','C C a l l','ccall',
          (shelxd_ccw,shelxd_cca),'"CCweak: " + x + ", CCall: " + y);\n'],
         ['SHELXD2','CCall vs. PATFOM','PATFOM','C C a l l','patFOM',
          (shelxd_fom,shelxd_cca),'"PATFOM: " + x + ", CCall: " + y);\n'],
         ['SHELXD3','CCall vs Try','Try','C C a l l','ccallTry',
          (shelxd_try,shelxd_cca),'"Try: " + x + ", CCall: " + y);\n'],
         ['SHELXD4','Site Occupancy vs. Peak Number','Peak Number','S i t e &nbsp O c c u p a n c y',
          'siteOcc',(shelxd_ccw,shelxd_best_occ),'"Peak number: " + x + ", Site occupancy: " + y);\n'],
         ['SHELXE1','Contrast vs. Cycle','Cycle','C o n t r a s t','contrast',
          (None,shelxe_contrast),'"Cycle: " + x + ", Contrast: " + y);\n'],
         ['SHELXE2','Connectivity vs. Cycle','Cycle','C o n n e c t i v i t y','con',
          (None,shelxe_con),'"Cycle: " + x + ", Connectivity: " + y);\n'],
         ['SHELXE3','Estimated CCmap vs. Resolution','Resolution(A)','C C m a p','ccmap',
          (shelxe_res,shelxe_mapcc),'"Resolution (A): " + x + ", Est. CCmap: " + y);\n']]
    #Remove Shelxc_cc if run was not from unmerged data.
    if len(shelxc_cc) > 0:
      l.insert(3,['SHELXC4','CC(1/2) vs. Resolution','Resolution(A)','C C &nbsp h a l f',
                  'cc',(shelxc_res,shelxc_cc),'\'Resolution (A): \' + x + \', CC(1/2): \' + y);\n'],)
      a = 0
    if self.gui:
      sp = 'plots_shelx.php'
    else:
      sp = 'plots_shelx.html'
    shelx_plot = open(sp,'w')
    shelx_plot.write(Utils.getHTMLHeader(self,'plots'))
    shelx_plot.write("%4s$(function() {\n%6s$('.tabs').tabs();\n%4s});\n"%(3*('',)))
    shelx_plot.write("%4s</script>\n%2s</head>\n%2s<body>\n"%(3*('',)))
    shelx_plot.write('%4s<table>\n%6s<tr>\n%8s<td width="100%%">\n%10s<div class="tabs">\n%12s<ul>\n'%(5*('',)))
    for i in range(len(l)):
      shelx_plot.write('%14s<li><a href="#tabs-44%s">%s</a></li>\n'%('',i,l[i][0]))
    shelx_plot.write("%12s</ul>\n"%'')
    for i in range(len(l)):
      shelx_plot.write('%12s<div id="tabs-44%s">\n%14s<div class=title><b>%s</b></div>\n'%('',i,'',l[i][1]))
      shelx_plot.write('%14s<div id="chart%s_div2" style="width:750px;height:550px;margin-left:20;"></div>\n'%('',i))
      shelx_plot.write('%14s<div class=x-label>%s</div>\n%14s<span class=y-label>%s</span>\n%12s</div>\n'%('',l[i][2],'',l[i][3],''))
    shelx_plot.write("%10s</div>\n%8s</td>\n%6s</tr>\n%4s</table>\n"%(4*('',)))
    shelx_plot.write('%4s<script id="source" language="javascript" type="text/javascript">\n'%'')
    shelx_plot.write("%6s$(function () {\n"%'')
    string = '\n%8svar '%''
    for i in range(len(l)):
      l1 = []
      label = ['%10s[\n'%'']
      string1 = string
      #SHELXC plots
      if i < 4+a:
        for x in range(len(l[i][5][1])):
          var = '%s%s'%(l[i][4],x)
          string1 += '%s=[],'%var
          label.append('%12s{ data: %s, label:"%s" },\n'%('',var,shelx_data[x]))
          for y in range(len(l[i][5][0][x])):
            l1.append("%8s%s.push([-%s,%s]);\n"%('',var,l[i][5][0][x][y],l[i][5][1][x][y]))
      #SHELXE plots
      elif i > 7+a:
        tot = len(l[i][5][1])
        half = int(tot/2)
        for x in range(2):
          var = '%s%s'%(l[i][4],x)
          string1 += '%s=[],'%var
          if x == 0:
            label.append('%12s{ data: %s, label:"original" },\n'%('',var))
            for y in range(0,half):
              if l[i][5][0] == None:
                l1.append("%8s%s.push([%s,%s]);\n"%('',var,str(y+1),l[i][5][1][y]))
              else:
                l1.append("%8s%s.push([-%s,%s]);\n"%('',var,l[i][5][0][y],l[i][5][1][y]))
          else:
            label.append('%12s{ data: %s, label:"inverted" },\n'%('',var))
            for y in range(half,tot):
              if l[i][5][0] == None:
                l1.append("%8s%s.push([%s,%s]);\n"%('',var,str(y-(half-1)),l[i][5][1][y]))
              else:
                l1.append("%8s%s.push([-%s,%s]);\n"%('',var,l[i][5][0][y-half],l[i][5][1][y]))
      #SHELXD plots
      else:
        string1 += '%s=[],'%l[i][4]
        label.append('%12s{ data: %s },\n'%('',l[i][4]))
        if l[i][4] == 'siteOcc':
          for y in range(len(l[i][5][1])):
            l1.append("%8s%s.push([%s,%s]);\n"%('',l[i][4],str(y+1),l[i][5][1][y]))
        else:
          for y in range(len(l[i][5][0])):
            l1.append("%8s%s.push([%s,%s]);\n"%('',l[i][4],l[i][5][0][y],l[i][5][1][y]))
      label.append('%10s],\n'%'')
      if 3+a < i < 7+a:
        label.append('%10s{ lines: { show: false}, points: { show: true },\n'%'')
      else:
        label.append('%10s{ lines: { show: true}, points: { show: true },\n'%'')
      l[i].append(label)
      shelx_plot.write('%s;\n'%string1[:-1])
      for line in l1:
        shelx_plot.write(line)
    for i in range(len(l)):
      shelx_plot.write('%8svar plot%s = $.plot($("#chart%s_div2"),\n'%('',i,i))
      for line in l[i][-1]:
        shelx_plot.write(line)
      shelx_plot.write("%12sselection: { mode: 'xy' }, grid: { hoverable: true, clickable: true },\n"%'')
      if 3+a < i < 6+a:
        shelx_plot.write("%12sxaxis: {min:0},\n"%'')
      elif i not in (6+a,7+a,8+a,9+a):
        shelx_plot.write("%12sxaxis: { transform: function (v) { return Math.log(-v); },\n"%'')
        shelx_plot.write("%21sinverseTransform: function (v) { return Math.exp(-v); },\n"%'')
        shelx_plot.write("%21stickFormatter: ( function negformat(val,axis){return -val.toFixed(axis.tickDecimals);} ) },\n"%'')
      if i == 1:
        shelx_plot.write("%12syaxis: {min:0, max:100}\n"%'')
      elif i == 7+a:
        shelx_plot.write("%12syaxis: {min:0, max:1.0}\n"%'')
      else:
        shelx_plot.write("%12syaxis: {min:0}\n"%'')
      shelx_plot.write("%10s});\n"%'')
    shelx_plot.write("%8sfunction showTooltip(x, y, contents) {\n"%'')
    shelx_plot.write("%10s$('<div id=\"tooltip\">' + contents + '</div>').css( {\n"%'')
    shelx_plot.write("%12sposition: 'absolute',\n%12sdisplay: 'none',\n"%('',''))
    shelx_plot.write("%12stop: y + 5,\n%12sleft: x + 5,\n"%('',''))
    shelx_plot.write("%12sborder: '1px solid #fdd',\n%12spadding: '2px',\n"%('',''))
    shelx_plot.write("%12s'background-color': '#fee',\n%12sopacity: 0.80\n"%('',''))
    shelx_plot.write('%10s}).appendTo("body").fadeIn(200);\n%8s}\n%8svar previousPoint = null;\n'%(3*('',)))
    for i in range(len(l)):
      shelx_plot.write('%8s$("#chart%s_div2").bind("plothover", function (event, pos, item) {\n'%('',i))
      shelx_plot.write('%10s$("#x").text(pos.x.toFixed(2));\n'%'')
      shelx_plot.write('%10s$("#y").text(pos.y.toFixed(2));\n'%'')
      shelx_plot.write("%10sif (true) {\n%12sif (item) {\n"%('',''))
      shelx_plot.write("%14sif (previousPoint != item.datapoint) {\n"%'')
      shelx_plot.write("%18spreviousPoint = item.datapoint;\n"%'')
      shelx_plot.write('%18s$("#tooltip").remove();\n'%'')
      if i < 3+a or i == 9+a:
        shelx_plot.write("%18svar x = -(item.datapoint[0].toFixed(2)),\n"%'')
      else:
        shelx_plot.write("%18svar x = item.datapoint[0].toFixed(2),\n"%'')
      shelx_plot.write("%22sy = item.datapoint[1].toFixed(2);\n"%'')
      shelx_plot.write('%18sshowTooltip(item.pageX, item.pageY,\n%30s%s'%('','',l[i][6]))
      shelx_plot.write('%14s}\n%12s}\n%12selse {\n%14s$("#tooltip").remove();\n'%(4*('',)))
      shelx_plot.write("%14spreviousPoint = null;\n%12s}\n%10s}\n%8s});\n"%(4*('',)))
    shelx_plot.write("%6s});\n%4s</script>\n%2s</body>\n</html>\n"%(3*('',)))
    shelx_plot.close()
    if os.path.exists(sp):
      shutil.copy(sp,self.working_dir)
    """
    except:
      self.logger.exception('**ERROR in plotShelx**')
      self.plotShelxFailed()
    """
  def plotShelxFailed(self):
    """
    If Shelx failed runs this to generate html plot summary.
    """
    if self.no_data_file:
      error = 'The SAD pipeline was initiated before the data finished processing. Please wait and resubmit.'
    elif self.anom_signal:
      error ='Shelx Failed. Could not calculate plots.'
    else:
      error ='There does not appear to be sufficient anomalous signal present.'
    Utils.failedHTML(self,('plots_shelx',error))

  def htmlSummaryShelx(self):
    """
    Create HTML/php files for autoindex/strategy output results.
    """
    if self.verbose:
      self.logger.debug('AutoSolve::htmlSummaryShelx')
    try:
      if self.gui:
        sl = 'jon_summary_shelx.php'
      else:
        sl = 'jon_summary_shelx.html'
      jon_summary = open(sl,'w')
      jon_summary.write(Utils.getHTMLHeader(self,'anom'))
      jon_summary.write('%6s$(document).ready(function() {\n'%'')
      jon_summary.write("%8s$('#accordion-shelx').accordion({\n%11scollapsible: true,\n%11sactive: false });\n"%(3*('',)))
      if self.shelxc_summary:
        #If MAD data, then have to add extra table for CC's.
        fi = len(self.shelx_results.get('Shelx results').get('shelx_data'))
        if len(self.shelx_results.get('Shelx results').get('MAD_CC')) > 0:
          fi += 1
        for i in range(fi):
          jon_summary.write("%8s$('#shelxc%s').dataTable({\n"%('',i))
          jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,'\
                            '\n%11s"bSort": false,\n%11s"bAutoWidth": false });\n'%(5*('',)))
      if self.shelxd_summary:
        jon_summary.write("%8s$('#shelxd').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false });\n'%(4*('',)))
      if self.shelxe_summary:
        jon_summary.write("%8s$('#shelxe').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false });\n'%(4*('',)))
        jon_summary.write("%8s$('#shelxe2').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false });\n'%(4*('',)))
      if self.tooltips:
        jon_summary.writelines(self.tooltips)
      jon_summary.write('%6s});\n%4s</script>\n%2s</head>\n%2s<body id="dt_example">\n'%(4*('',)))
      if self.no_data_file or self.no_data_file2:
        jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
        if self.no_data_file:
          jon_summary.write('%7s<h3 class="results">The SAD pipeline was initiated before the data finished processing. Please wait and resubmit.</h3>\n'%'')
        else:
          jon_summary.write('%7s<h3 class="results">Not enough datasets were selected for the pipeline to run.</h3>\n'%'')
        jon_summary.write("%6s</div>\n%5s</div>\n%4s</div>\n"%(3*('',)))
      else:
        if self.shelxc_summary:
          jon_summary.writelines(self.shelxc_summary)
        if self.shelxd_summary:
          jon_summary.writelines(self.shelxd_summary)
        if self.shelxe_summary:
          jon_summary.writelines(self.shelxe_summary)
        else:
          jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
          if self.shelx_nosol:
            jon_summary.write('%7s<h4 class="results">SHELX did not appear to come up with an obvious solution.</h4>\n'%'')
          if self.anom_signal==False:
            jon_summary.write('%7s<h4 class="results">SHELX did not run since the anomalous signal is too low..</h4>\n'%'')
          jon_summary.write("%6s</div>\n%5s</div>\n%4s</div>\n"%(3*('',)))
        jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
        jon_summary.write("%7s<h1 class='Results'>RAPD Logfile</h1>\n%6s</div>\n%5s</div>\n"%(3*('',)))
        jon_summary.write('%5s<div id="accordion-shelx">\n'%'')
        jon_summary.write('%6s<h3><a href="#">Click to view log of top solution</a></h3>\n%6s<div>\n%7s<pre>\n'%(3*('',)))
        jon_summary.write('\n---------------Shelx RESULTS---------------\n\n')
        if self.shelx_log:
          for line in self.shelx_log:
            if type(line)== str:
              jon_summary.write(line)
        else:
          jon_summary.write('---------------SHELX FAILED---------------\n')
        jon_summary.write('%7s</pre>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(4*('',)))
      jon_summary.write("%2s</body>\n</html>\n"%'')
      jon_summary.close()
      #copy html file to working dir
      if os.getcwd() != self.working_dir:
        shutil.copy(sl,self.working_dir)

    except:
      self.logger.exception('**ERROR in htmlSummaryShelx**')

  def htmlSummaryAutoSol(self):
    """
    Write html/php file for Phenix AutoSol results.
    """
    if self.verbose:
      self.logger.debug('AutoSolve::htmlSummaryAutoSol')
    try:
      if self.gui:
        html = 'jon_summary_autosol.php'
      else:
        html = 'jon_summary_autosol.html'
      jon_summary = open(html,'w')
      jon_summary.write(Utils.getHTMLHeader(self))
      jon_summary.write('%6s$(document).ready(function() {\n'%'')
      jon_summary.write("%8s$('#accordion-autosol').accordion({\n%11scollapsible: true,\n%11sactive: false });\n"%(3*('',)))
      if self.autosol_summary: 
        jon_summary.write("%8s$('#autosol').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bSort": false,\n%11s"bAutoWidth": false });\n'%(5*('',)))
      if self.autobuild_summary:
        jon_summary.write("%8s$('#autobuild').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bSort": false,\n%11s"bAutoWidth": false });\n'%(5*('',)))
      jon_summary.write('%6s});\n%4s</script>\n%2s</head>\n%2s<body id="dt_example">\n'%(4*('',)))
      if self.no_data_file or self.no_data_file2:
        jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
        if self.no_data_file:
          jon_summary.write('%7s<h3 class="results">The SAD pipeline was initiated before the data finished processing. '\
                            'Please wait and resubmit.</h3>\n'%'')
        else:
          jon_summary.write('%7s<h3 class="results">Not enough datasets were selected for the pipeline to run.</h3>\n'%'')
        jon_summary.write('%6s</div>\n%5s</div>\n%4s</div>\n'%(3*('',)))
      else:
        if self.autobuild:
          if self.autobuild_summary:
            jon_summary.writelines(self.autobuild_summary)
          else:
            jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
            if self.autobuild_failed:
              jon_summary.write('%7s<h4 class="results">There was a problem in the Phenix AutoBuild run.</h4>\n'%'')
            elif self.autobuild_results.get('AutoBuild results').get('AutoBuild_pdb').startswith('overall_best') == False:                
              jon_summary.write('%7s<h4 class="results">Phenix Autobuild is currently running on your solution.</h4>\n'%'')
            else:
              jon_summary.write('%7s<h3 class="results">Phenix Autobuild Complete.</h3>\n'%'')
            jon_summary.write('%6s</div>\n%5s</div>\n%4s</div>\n'%(3*('',)))
        else:
          if self.autosol_summary:
            jon_summary.writelines(self.autosol_summary)
          else:
            jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
            if self.autosol_build == False:
              jon_summary.write('%7s<h3 class="results">Phenix AutoSol not turned on.</h3>\n'%'') 
            elif self.autosol_failed:
              jon_summary.write('%7s<h3 class="results">There was a problem in the Phenix AutoSol run.</h3>\n'%'')
            elif self.anom_signal == False:
              jon_summary.write('%7s<h4 class="results">SHELX did not run since the anomalous signal is too low..</h4>\n'%'')
            elif self.shelx_nosol:
              jon_summary.write('%7s<h3 class="results">SHELX could not find a solution</h3>\n'%'')
            else:
              jon_summary.write('%7s<h4 class="results">Phenix AutoSol is currently running on your solution.</h4>\n'%'')
            jon_summary.write('%6s</div>\n%5s</div>\n%4s</div>\n'%(3*('',)))
        jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
        jon_summary.write("%7s<h1 class='Results'>RAPD Logfile</h1>\n%6s</div>\n%5s</div>\n"%(3*('',)))
        jon_summary.write('%5s<div id="accordion-autosol">\n'%'')
        jon_summary.write('%6s<h3><a href="#">Click to view log</a></h3>\n%6s<div>\n%7s<pre>\n'%(3*('',)))
        if self.autobuild:
          jon_summary.write('---------------Phenix AutoBuild RESULTS---------------\n\n')
          if self.autobuild_log:
            for line in self.autobuild_log:
              jon_summary.write(line)
          else:
            jon_summary.write('---------------Phenix AutoBuild FAILED---------------\n')
        else:
          jon_summary.write('---------------Phenix AutoSol RESULTS---------------\n\n')
          if self.autosol_log:
            for line in self.autosol_log:
              jon_summary.write(line)
          else:
            jon_summary.write('---------------Phenix AutoSol FAILED---------------\n')
        jon_summary.write('%7s</pre>\n%6s</div>\n%5s</div>\n%4s</div>\n'%(4*('',)))
      jon_summary.write("%2s</body>\n</html>\n"%'')
      jon_summary.close()
      if os.getcwd() != self.working_dir:
        shutil.copy(html,self.working_dir)

    except:
      self.logger.exception('**ERROR in htmlSummaryAutoSol**')

  def PrintInfo(self):
    """
    Print information regarding programs utilized by RAPD
    """
    if self.verbose:
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
"""
def main():
  #start logging
  import logging,logging.handlers
  #LOG_FILENAME = os.path.join(os.getcwd(),'rapd.log')
  LOG_FILENAME = '/gpfs6/users/necat/Jon/RAPD_test/Output/rapd.log'
  #inp = Input.input()
  # Set up a specific logger with our desired output level
  logger = logging.getLogger('RAPDLogger')
  logger.setLevel(logging.DEBUG)
  # Add the log message handler to the logger
  handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,maxBytes=100000,backupCount=5)
  #add a formatter
  formatter = logging.Formatter("%(asctime)s - %(message)s")
  handler.setFormatter(formatter)
  logger.addHandler(handler)
  logger.info('__init__')
  
  import argparse
  #Parse the command line for commands.
  parser = argparse.ArgumentParser()
  parser.add_argument('inp' ,nargs='*', type=file, help='json')
  args = vars(parser.parse_args())
  inp = False
  if len(args['inp']) > 0:
    if args['inp'][0].endswith('.json'):
      from json import load
      inp = load(args['inp'][0])
      print 'got here'
  if inp == False:
    import jon_struc_input as Input
    inp = Input.input()
  AutoSolve(inp,logger=logger)
    
if __name__ == '__main__':
  main()
    
"""
if __name__ == '__main__':
  inp = ["SAD",
         {"work": "/gpfs6/users/necat/Jon/RAPD_test/Output",
          },
         #mtz_file is usually *_free.mtz out of integrate, reintegrate, or merged pipelines.
         {'original': {#'mtz_file': '/gpfs1/users/necat/rapd/copper/trunk/integrate/2010-12-15/yong2_3/yong2_free.mtz',
                       'mtz_file': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/SAD/PK_lu_peak_new_free.mtz',
                       #'mtz_file': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/3kh3-sf.mtz',#SOD1
                       #'mtz_file': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/SAD/p30_8_free.mtz',
                       #'mtz_file': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/SAD/p3_6_free.mtz',
                       #'mtz_file': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/SAD/P432_peptide.mtz',
                       #'mtz_file': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz',
                       #'mtz_file': '/gpfs5/users/necat/rapd/uranium/trunk/integrate/2015-08-10/AL_C5_edge_1/reprocess_1/AL_C5_edge_1_free.mtz',
                       #'mtz_file': None,
                       }
          }, 
         #input_sca was alternative input for reading HKL2000 processed datasets. This is still dev.
         #mtz_NAT, mtz_INFL, mtz_HREM, mtz_LREM, mtz_SIRA used for MAD pipeline. 
         {"request":{ #"input_sca": '/gpfs6/users/necat/Jon/RAPD_test/Datasets/SAD/PK_lu_peak.sca', 
                     #"input_sca": '/gpfs6/users/necat/Jon/RAPD_test/Datasets/SAD/crystal26_ANOM.sca',
                     #"mtz_NAT":'/gpfs5/users/necat/rapd/uranium/trunk/integrate/2012-10-20/w6lr_1/w6lr_1/w6lr_1_free.mtz',
                     #"mtz_NAT":'/gpfs5/users/necat/rapd/uranium/trunk/integrate/2012-11-25/44b16_rem_1/44b16_rem_1/44b16_rem_1_free.mtz',
                     #"mtz_NAT":'/gpfs5/users/necat/rapd/uranium/trunk/integrate/2012-10-24/BAS8-03_remote_1/BAS8-03_remote_1/BAS8-03_remote_1_free.mtz',
                     #"mtz_NAT":'/gpfs1/users/rockefeller/charles_C_1497/process/rapd/integrate/DN310_data20_1/DN310_data20_1/DN310_data20_1_free.mtz',
                     "mtz_NAT":None,
                     #"mtz_PEAK":'/gpfs5/users/necat/rapd/uranium/trunk/integrate/2012-10-24/BAS8-03_peak_1/BAS8-03_peak_1/BAS8-03_peak_1_free.mtz',
                     #"mtz_PEAK":'/gpfs7/users/GU/Schulman_Oct12/process/rapd/integrate/BAS8-03_peak_1/BAS8-03_peak_1/P4_peak_free.mtz',
                     #"mtz_PEAK":'/gpfs7/users/GU/Schulman_Oct12/process/BAS8-Zn/crystal-3/peak/P41/BAS8-03_peak_output.sca',
                     #"mtz_PEAK":'/gpfs7/users/harvard/Blacklow_Mar13/process/rapd/smerge/3-1-peak_1+3-1-peak_2/smerge_freer.mtz',
                     #"mtz_PEAK": '/gpfs5/users/necat/rapd/uranium/trunk/integrate/2015-07-20/D10_A4_p17_w1pk_1/D10_A4_p17_w1pk_1/D10_A4_p17_w1pk_1_free.mtz',
                     #"mtz_PEAK":None,
                     #"mtz_INFL":'/gpfs5/users/necat/rapd/uranium/trunk/integrate/2012-10-24/BAS8-03_inflect_1/BAS8-03_inflect_1/BAS8-03_inflect_1_free.mtz',
                     #"mtz_INFL":'/gpfs7/users/GU/Schulman_Oct12/process/BAS8-Zn/crystal-3/inflec/P41/BAS8-03_inflect_output.sca',
                     #"mtz_INFL":'/gpfs7/users/GU/Schulman_Oct12/process/rapd/integrate/BAS8-03_inflect_1/BAS8-03_inflect_1/P4_inf_free.mtz',
                     #"mtz_INFL":'/gpfs7/users/harvard/Blacklow_Mar13/process/rapd/smerge/3-1-inf_1+3-1-inf_2/smerge_freer.mtz',
                     #"mtz_INFL": '/gpfs5/users/necat/rapd/uranium/trunk/integrate/2015-07-20/D10_A4_p17_w1in_1/D10_A4_p17_w1in_1/D10_A4_p17_w1in_1_free.mtz',
                     "mtz_INFL":None,
                     #"mtz_HREM":'/gpfs5/users/necat/rapd/uranium/trunk/integrate/2012-10-24/BAS8-03_remote_1/BAS8-03_remote_1/BAS8-03_remote_1_free.mtz',
                     #"mtz_HREM":'/gpfs7/users/GU/Schulman_Oct12/process/rapd/integrate/BAS8-03_remote_1/BAS8-03_remote_1/P4_rem_free.mtz',
                     #"mtz_HREM":'/gpfs7/users/GU/Schulman_Oct12/process/BAS8-Zn/crystal-3/remote/P41/BAS8-03_remote_output.sca',
                     #"mtz_HREM":'/gpfs5/users/necat/rapd/uranium/trunk/integrate/2012-11-25/44b16_rem_1/44b16_rem_1/44b16_rem_1_free.mtz',
                     #"mtz_HREM":'/gpfs7/users/harvard/Blacklow_Mar13/process/rapd/smerge/3-1-remote_1+3-1-remote_2/smerge_freer.mtz',
                     #"mtz_HREM":'/gpfs5/users/necat/rapd/uranium/trunk/integrate/2015-07-20/D10_A4_p17_w1hr_1/D10_A4_p17_w1hr_1/D10_A4_p17_w1hr_1_free.mtz',
                     "mtz_HREM":None,
                     #"mtz_LREM":'/gpfs5/users/necat/rapd/uranium/trunk/integrate/2012-10-24/BAS8-03_remote_1/BAS8-03_remote_1/BAS8-03_remote_1_free.mtz',
                     "mtz_LREM":None,
                     #"mtz_SIRA":'/gpfs5/users/necat/rapd/uranium/trunk/integrate/2012-10-20/w6_1/w6_1/w6_1_free.mtz',
                     #"mtz_SIRA":'/gpfs5/users/necat/rapd/uranium/trunk/integrate/2012-11-25/43a11_1/43a11_1/43a11_1_free.mtz',
                     #"mtz_SIRA": '/gpfs5/users/necat/rapd/uranium/trunk/integrate/2012-10-24/BAS8-03_peak_1/BAS8-03_peak_1/BAS8-03_peak_1_free.mtz',
                     #"mtz_SIRA": '/gpfs1/users/rockefeller/charles_C_1497/process/rapd/integrate/DN31_data15_1/DN31_data15_1/DN31_data15_1_free.mtz',
                     "mtz_SIRA":None,
                     #"input_map": '',               
                     "input_map": None,
                     #"pdb": None,
                     "pdb": '/gpfs6/users/necat/Jon/RAPD_test/Pdb/prok.pdb',
                     'pdb_name': None,
                     #set to 0 mean to have Phaser automatically figure it out by Matthews.
                     'nmol': 0,
                     #'nmol': 6,
                     #If pdb == None and pdb_code != None, it will download the mmCIF from local PDB repository.
                     'pdb_code': None,
                     #'pdb_code':'2V8B',
                     # # of SHELXD trials to run per SG. Set to multiples of 16. May have to modify for your computer cluster.
                     #"shelxd_try": 1024,
                     "shelxd_try": 4048,
                     "ha_type":'Se',
                     #Set to 1 to let RAPD calculate # of Se based on 0.55 solvent content and 1 per 75 residues. 
                     "ha_number": 1,
                     #"ha_number": 20,
                     #To override SHELXC's high res limit. 
                     "sad_res": 0.0,
                     #"sad_res": 4,
                     "wavelength":0.9792,
                     #"wavelength":0.9179,#Br
                     #"wavelength":0.76890,#Sr
                     "ligand": False,
                     #"sample_type": 'DNA',
                     #Specifying sequence will be input to AutoSol.
                     "sequence": '',
                     #"sequence": 'mtttpkprta pavgsvflgg pfrqlvdprt gvmssgdqnv fsrliehfes rgttvynahr \
                     #            reawgaefls paeatrldhd eikaadvfva fpgvpaspgt hveigwasgm gkpmvlller \
                     #            dedyaflvtg lesqanveil rfsgteeive rldgavarvl grageptvig'
                     }
   
          },
   
         ('164.54.212.165',50001)
         ]

  import logging,logging.handlers
  #from extras import rapd_inputs
  #inp = rapd_inputs.phaserAnomInput()
  #import json
  #inp = json.loads(open('/gpfs5/users/necat/rapd/gadolinium/trunk/rapd_SAD-8wb7HN.json','r').read())
  #start logging
  LOG_FILENAME = os.path.join(inp[1].get('work'),'rapd.log')
  # Set up a specific logger with our desired output level
  logger = logging.getLogger('RAPDLogger')
  logger.setLevel(logging.DEBUG)
  # Add the log message handler to the logger
  handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,maxBytes=100000,backupCount=5)
  #add a formatter
  formatter = logging.Formatter("%(asctime)s - %(message)s")
  handler.setFormatter(formatter)
  logger.addHandler(handler)
  #logger.info('AutoSolve.__init__')
  AutoSolve(inp,logger=logger)
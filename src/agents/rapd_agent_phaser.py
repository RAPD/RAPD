"""
This file is part of RAPD

Copyright (C) 2010-2016, Cornell University
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
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Production"

from multiprocessing import Process, Queue
import os, time, shutil
from rapd_communicate import Communicate
import rapd_utils as Utils
import rapd_parse as Parse
import rapd_summary as Summary
import rapd_beamlinespecific as BLspec

class AutoMolRep(Process, Communicate):
  def __init__(self, input, logger=None):
    logger.info('AutoMolRep.__init__')
    
    self.st = time.time()
    self.input                              = input
    self.logger                             = logger
    #Setting up data input
    self.setup                              = self.input[1]
    self.data                               = self.input[2]
    self.preferences                        = self.input[3]
    self.controller_address                 = self.input[-1]
    
    #For testing individual modules
    self.test                               = False
    #Removes junk files and directories at end.
    self.clean                              = False
    #Calculate ADF for all solutions
    self.adf                                = True
    self.verbose                            = True
    
    #variables to set
    #self.phaser_timer                       = 600 #Timer will be double for full Phaser
    self.phaser_timer                       = False
    self.phaser_results                     = {}
    self.phaser_jobs                        = []
    self.output                             = {}
    self.cell_summary                       = False
    self.pdb_summary                        = False
    self.pdb_percent                        = False
    self.percent                            = False
    self.tooltips                           = False
    self.cell2                              = False
    self.solvent_content                    = False
    self.input_sg                           = False
    self.pdb_code                           = False
    self.run_before                         = False
    self.dres                               = False
    self.large_cell                         = False
    
    self.sample_type = self.preferences.get('sample_type','Protein')
    self.datafile = Utils.convertUnicode(self,self.data.get('original').get('mtz_file',None))
    if self.datafile == None:
      self.datafile = Utils.convertUnicode(self,self.preferences.get('request').get('input_sca'))
    self.nmol = self.preferences.get('request').get('nmol',False)
    #Used for printing summary html
    self.pdb_name = self.preferences.get('request').get('pdb_name',False)
    if self.pdb_name == None:
      self.pdb_name = False
    self.input_pdb = Utils.convertUnicode(self,self.preferences.get('request').get('pdb',None))
    if self.input_pdb == None:
      self.input_pdb = Utils.convertUnicode(self,self.preferences.get('request').get('pdb_code',None))
      #Used in SummaryCell for label.
      if self.input_pdb != None:
        
        self.pdb_code = True
    
    #Check if running from beamline and turn off testing if I forgot to.
    if self.preferences.get('request').has_key('request_type'):
      self.gui       = True
      self.test      = False
      self.verbose   = False
    else:
      self.gui       = False
    #******BEAMLINE SPECIFIC*****
    #self.cluster_use = Utils.checkCluster()
    self.cluster_use = BLspec.checkCluster()
    #******BEAMLINE SPECIFIC*****
    Process.__init__(self,name='AutoMolRep')
    #starts the new process
    self.start()

  def run(self):
    """
    Convoluted path of modules to run.
    """
    if self.verbose:
      self.logger.debug('AutoMolRep::run')
    self.preprocess()
    
    self.preprocessPhaser()
    self.Queue()
    self.postprocess()
    
  def preprocess(self):
    """
    Things to do before the main process runs
    1. Change to the correct directory
    2. Print out the reference for MR pipeline
    """
    if self.verbose:
      self.logger.debug('AutoMolRep::preprocess')
    #change directory to the one specified in the incoming dict
    self.working_dir = self.setup.get('work')
    if os.path.exists(self.working_dir) == False:
      os.makedirs(self.working_dir)
    os.chdir(self.working_dir)
    #Convert SCA to MTZ (if needed) and get unit cell and SG info and convert R3/H3
    self.input_sg,self.cell,self.cell2,vol = Utils.getMTZInfo(self,False,True,True)
    #Needed for running in different queues for more memory..
    if Utils.calcResNumber(self,self.input_sg,False,vol) > 5000:
      self.large_cell = True
    #Check if input_pdb is pdb file or pdbID.
    if self.input_pdb[-4:].upper() != '.PDB':
      if len(self.input_pdb) == 4:
        #self.input_pdb = Utils.downloadPDB(self,self.input_pdb)
        self.input_pdb = Utils.getmmCIF(self,self.input_pdb)
      else:
        self.postprocess(True)
    else:
      #Have to copy into working_dir to limit path length in Phaser
      try:
        shutil.copy(self.input_pdb,os.getcwd())
      except:
        if self.verbose:
          self.logger.debug('Cannot copy input pdb to working dir. Probably already there.')
      self.input_pdb = os.path.join(os.getcwd(),os.path.basename(self.input_pdb))
    #Check if pdb exists...
    if self.input_pdb == False:
      self.postprocess(True)
    else:
      self.dres = Utils.getRes(self)
      self.pdb_info = Utils.getPDBInfo(self,self.input_pdb)
      if self.pdb_info == False:
        self.postprocess(True)
      #If user requests to search for more mols, then allow.
      if self.nmol:
        if int(self.pdb_info['all'].get('NMol')) < int(self.nmol):
          self.pdb_info['all']['NMol'] = self.nmol
    if self.test:
      self.logger.debug('TEST IS SET "ON"')
    #print out recognition of the program being used
    self.PrintInfo()
      
  def preprocessPhaser(self):
    """
    Setup which PHASER jobs to run.
    """
    if self.verbose:
      self.logger.debug('AutoMolRep::preprocessPhaser')
    try:
      #Prune if only one chain present, b/c 'all' and 'A' will be the same.
      if len(self.pdb_info.keys()) == 2:
        for key in self.pdb_info.keys():
          if key != 'all':
            del self.pdb_info[key]
      for chain in self.pdb_info.keys():
        #only launch is greater than 20% solvent content
        if self.pdb_info[chain]['SC'] > 0.2:
          self.processPhaser(chain)
      #Set the running jobs for stats in html.
      if self.run_before == False:
        self.phaser_jobs = [key for key in self.phaser_results.keys() if key[-1] == '0']
      else:
        self.phaser_jobs = [key for key in self.phaser_results.keys() if key[-1] == '1']
      #Setup initial html file
      self.postprocess(False)

    except:
      self.logger.exception('**ERROR in AutoMolRep.preprocessPhaser**')

  def processPhaser(self,chain):
    """
    Run Phaser on input pdb file.
    """
    if self.verbose:
      self.logger.debug('AutoMolRep::processPhaser')
    
    def launchJob(inp2,k):
      """
      Launch Phaser job on cluster and pass back the process job and pid.
      """
      Utils.folders(self,k)
      #Remove leftover file if rerunning.
      if os.path.exists('adf.com'):
        os.system('rm -rf adf.com')
      queue = Queue()
      j = Process(target=RunPhaser,args=(inp2,queue,self.logger))
      j.start()
      queue.get()#For the log I am not using
      if self.output['jobs'] == None:
        self.output['jobs'] = {j:k}
        self.output['pids'] = {k:queue.get()}
      else:
        self.output['jobs'].update({j:k})
        self.output['pids'].update({k:queue.get()})
      #Setup initial results for all running jobs.
      self.phaser_results[k] = { 'AutoMR results' : Parse.setPhaserFailed('Still running')}
        
    try:
      sg_name = []
      #set lays in self.output if not there.
      self.output.setdefault('jobs',None)
      self.output.setdefault('pids',None)
      
      d = {'data':self.datafile,'pdb':self.pdb_info[chain]['file'],'verbose':self.verbose,
           'copy':self.pdb_info[chain]['NMol'],'test':self.test,'cluster':self.cluster_use,
           'res':Utils.setPhaserRes(self,self.pdb_info[chain]['res']),'large':self.large_cell,
           #'mwaa':self.pdb_info[chain]['MWaa'],'mwna':self.pdb_info[chain]['MWna'],
           }
      run_sg = Utils.subGroups(self,Utils.convertSG(self,self.input_sg),'phaser')
      #Run Phaser in all the space groups.
      for sg in run_sg:
        sg2 = Utils.convertSG(self,sg,True)
        sg_name.append(sg2)
        d['sg'] = sg2
        if self.run_before == False:
          key = '%s_%s_%s'%(sg2,chain,'0')
          d['run_before'] = False
          launchJob(d,key)
        #Run both fast and full Phaser at same time if in cluster mode
        if self.run_before or self.cluster_use:
          key = '%s_%s_%s'%(sg2,chain,'1')
          d['run_before'] = True
          launchJob(d,key)

    except:
      self.logger.exception('**ERROR in AutoMolRep.processPhaser**')

  def postprocessPhaser(self,inp):
    """
    Look at Phaser results.
    """
    if self.verbose:
      self.logger.debug('AutoMolRep::postprocessPhaser')
    try:
      #self.phaser_results[inp] = { 'AutoMR results' :  Parse.ParseOutputPhaser(self,open('%s.sum'%inp.split('_')[0],'r').readlines())}
      self.phaser_results[inp] = { 'AutoMR results' :  Parse.ParseOutputPhaser(self,open('phaser.log','r').readlines())}
      if self.adf:
        sg = self.phaser_results[inp].get('AutoMR results').get('AutoMR sg')
        if sg in ('No solution','Timed out','NA'):
          #Tells Queue job is finished
          os.system('touch adf.com')
        else:
          #Put path of map and peaks pdb in results
          self.phaser_results[inp].get('AutoMR results').update({'AutoMR adf': '%s_adf.map'%inp})
          self.phaser_results[inp].get('AutoMR results').update({'AutoMR peak':'%s_adf_peak.pdb'%inp})
          return('ADF')

    except:
      self.logger.exception('**ERROR in AutoMolRep.postprocessPhaser**')

  def postprocess(self,final=True):
    """
    Things to do after the main process runs
    1. Return the data through the pipe
    """
    if self.verbose:
      self.logger.debug('AutoMolRep::postprocess')
    #Run summary files for each program to print to screen
    output = {}
    results = {}
    output_files = False
    status = False
    cell_results = False
    failed = False
    #Setup output file name
    if self.phaser_results:
      Summary.summaryCell(self,'phaser')
    if self.input_pdb:
      self.htmlSummaryPhaser()
    else:
      Utils.failedHTML(self,('jon_summary_cell','Input PDB file does not exist.'))
    try:
      if self.gui:
        sl = 'jon_summary_cell.php'
      else:
        sl = 'jon_summary_cell.html'
      if os.path.exists(os.path.join(self.working_dir,sl)):
        output['Cell summary html'] = os.path.join(self.working_dir,sl)
      else:
        output['Cell summary html'] = 'None'
    except:
      self.logger.exception('**Could not update path of cell summary html file in AutoMolRep.postprocess.**')
      output['Cell summary html'] = 'FAILED'

    try:
      #Only tar up files at end to see if they show up in the user dir.
      #if final:
      if self.input_pdb:
        #pdb = os.path.basename(self.input_pdb)
        for sg in self.phaser_results.keys():
          dir1 = self.phaser_results[sg].get('AutoMR results').get('AutoMR dir')
          l = ['pdb','mtz','adf','peak']
          if dir1 not in ('No solution','Timed out','NA','DL Failed','Still running'):
            #pack all the output files in a tar and save the path in results.
            os.chdir(dir1)
            #tar = '%s_%s.tar'%(pdb[:-4],sg)
            tar = '%s_%s.tar'%(sg.split('_')[0],sg.split('_')[1])
            if os.path.exists('%s.bz2'%tar) == False:
              for p in l:
                f = self.phaser_results[sg].get('AutoMR results').get('AutoMR %s'%p)
                if os.path.exists(f):
                  os.system('tar -rf %s %s'%(tar,f))
              if os.path.exists(tar):
                os.system('bzip2 -qf %s'%tar)
              #Remove old tar's in working dir, if they exist and copy new one over.
              if os.path.exists(os.path.join(self.working_dir,'%s.bz2'%tar)):
                os.system('rm -rf %s'%os.path.join(self.working_dir,'%s.bz2'%tar))
              shutil.copy('%s.bz2'%tar,self.working_dir)
            self.phaser_results[sg].get('AutoMR results').update({'AutoMR tar': os.path.join(self.working_dir,'%s.bz2'%tar)})
          else:
            self.phaser_results[sg].get('AutoMR results').update({'AutoMR tar': 'None'})
      cell_results = { 'Cell analysis results': self.phaser_results }

    except:
      self.logger.exception('**Could not AutoMR results in AutoMolRep.postprocess.**')
      cell_results = { 'Cell analysis results': 'FAILED'}
      self.clean = False
      failed = True

    try:
      output_files = {'Output files' : output}
    except:
      self.logger.exception('**Could not update the output dict in AutoMolRep.postprocess.**')

    #Get proper status.
    if final:
      if failed:
        status = {'status': 'FAILED'}
      else:
        status = {'status': 'SUCCESS'}
    else:
      status = {'status': 'WORKING'}

    #Put all the result dicts from all the programs run into one resultant dict and pass it back.       
    try:
      if self.gui == False:
        if self.input[0] == "SAD":
          self.input.remove("SAD")
          self.input.insert(0,'MR')
      if status:
        results.update(status)
      if cell_results:
        results.update(cell_results)
      #Utils.pp(self,cell_results)
      if output_files:
        results.update(output_files)
      #Utils.pp(results)
      if self.gui:
        if results:
          if len(self.input) == 6:
            #Delete the previous Phaser results sent back.
            del self.input[5]
          self.input.append(results)
        self.sendBack2(self.input)

    except:
      self.logger.exception('**Could not send results to pipe in AutoMolRep.postprocess.**')

    if final:
      try:
        #Cleanup my mess.
        if self.clean:
          os.chdir(self.working_dir)
          if self.verbose:
            self.logger.debug('Cleaning up Phaser files and folders')
          os.system('rm -rf Phaser_* *.com *.pdb *.mtz *.sum')

      except:
        self.logger.exception('**Could not cleanup in AutoMolRep.postprocess**')

      #Say job is complete.
      t = round(time.time()-self.st)
      self.logger.debug(50*'-')
      self.logger.debug('RAPD AutoMolRep complete.')
      self.logger.debug('Total elapsed time: %s seconds'%t)
      self.logger.debug(50*'-')
      print 50*'-'
      print 'RAPD AutoMolRep complete.'
      print 'Total elapsed time: %s seconds'%t
      print 50*'-'
  
  def Queue(self):
    """
    queue system.
    """
    if self.verbose:
      self.logger.debug('AutoMolRep::Queue')
    try:
      timed_out = False
      timer = 0
      jobs = self.output['jobs'].keys()
      #set which jobs to watch.
      if self.run_before:
        jobs = [job for job in jobs if self.output['jobs'][job][-1] == '1']
      else:
        jobs = [job for job in jobs if self.output['jobs'][job][-1] == '0']
      counter = len(jobs)
      while counter != 0:
        for job in jobs:
          if job.is_alive() == False:
            jobs.remove(job)
            if self.verbose:
              self.logger.debug('Finished Phaser on %s'%self.output['jobs'][job])
            Utils.folders(self,self.output['jobs'][job])
            if self.adf:
              if os.path.exists('adf.com'):
                del self.output['pids'][self.output['jobs'][job]]
                counter -= 1
              else:
                key = self.output['jobs'].pop(job)
                p = self.postprocessPhaser(key)
                if p == 'ADF':
                  #Calculate ADF map.
                  adf = Process(target=Utils.calcADF,name='ADF%s'%key,args=(self,key))
                  adf.start()
                  jobs.append(adf)
                  self.output['jobs'][adf] = key
                else:
                  counter -= 1
                self.postprocess(False)
            else:
              self.postprocessPhaser(self.output['jobs'][job])
              del self.output['pids'][self.output['jobs'][job]]
              self.postprocess(False)
              counter -= 1
        time.sleep(0.2)
        timer += 0.2
        if self.verbose:
          number = round(timer%1,1)
          if number in (0.0,1.0):
            print 'Waiting for Phaser to finish %s seconds'%timer
        if self.phaser_timer:
          if timer >= self.phaser_timer:
            timed_out = True
            break
      if timed_out:
        self.logger.debug('Phaser timed out.')
        print 'Phaser timed out.'
        for job in jobs:
          self.phaser_results[self.output['jobs'][job]] = {'AutoMR results':Parse.setPhaserFailed('Timed out')}
          if self.cluster_use:
            #Utils.killChildrenCluster(self,self.output['pids'][self.output['jobs'][job]])
            BLspec.killChildrenCluster(self,self.output['pids'][self.output['jobs'][job]])
          else:
            Utils.killChildren(self,self.output['pids'][self.output['jobs'][job]])
      #Check if solution has been found.
      if self.run_before == False:
        self.checkSolution()
      self.logger.debug('Phaser finished.')

    except:
      self.logger.exception('**ERROR in AutoMolRep.Queue**')

  def checkSolution(self):
    """
    Check if solution is found. If not alter input and rerun.
    """
    if self.verbose:
      self.logger.debug('AutoMolRep::checkSolution')
    try:
      solution = False
      keys = self.phaser_results.keys()
      keys0 = [key for key in keys if key[-1] == '0']
      keys1 = [key for key in keys if key[-1] == '1']
      for key in keys0:
        sg = self.phaser_results[key].get('AutoMR results').get('AutoMR sg')
        if sg not in ('No solution','Timed out','NA'):
          solution = True
      if solution:
        #Kill the jobs and remove the results
        for k in keys1:
          if self.cluster_use:
            #Utils.killChildrenCluster(self,self.output['pids'][k])
            BLspec.killChildrenCluster(self,self.output['pids'][k])
          else:
            Utils.killChildren(self,self.output['pids'][k])
          del self.phaser_results[k]
      else:
        self.run_before = True
        #Remove results from quick run if no solution found.
        for k in keys0:
          del self.phaser_results[k]
        #Run the full Phaser jobs.
        if self.cluster_use == False:
          self.preprocessPhaser()
        else:
          self.phaser_jobs = keys1
          self.postprocess(False)
        self.Queue()

    except:
      self.logger.exception('**ERROR in AutoMolRep.checkSolution**')

  def htmlSummaryPhaser(self):
    """
    Create HTML/php files for autoindex/strategy output results.
    """
    if self.verbose:
      self.logger.debug('AutoMolRep::htmlSummaryPhaser')
    try:
      sl = 'jon_summary_cell.html'
      if self.gui:
        sl = sl.replace('html','php')
      jon_summary = open(sl,'w')
      jon_summary.write(Utils.getHTMLHeader(self,'phaser'))
      jon_summary.write('%6s$(document).ready(function() {\n'%'')
      #jon_summary.write("%8s$('#accordion').accordion({\n"%'')
      #jon_summary.write('%11scollapsible: true,\n%11sactive: false });\n'%('',''))
      if self.cell_summary:
        jon_summary.write("%8s$('#phaser-cell').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bSort": false,\n%11s"bAutoWidth": false});\n'%(5*('',)))
      if self.pdb_summary:
        jon_summary.write("%8s$('#phaser-pdb').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bSort": false,\n%11s"bAutoWidth": false});\n'%(5*('',)))
        #Style the button
        jon_summary.write('%8s$("button").button();\n'%'')
      if self.tooltips:
        jon_summary.writelines(self.tooltips)
      jon_summary.write('%6s});\n%4s</script>\n%2s</head>\n%2s<body id="dt_example">\n'%(4*('',)))
      if self.cell_summary:
        jon_summary.writelines(self.cell_summary)
      if self.pdb_summary:
        jon_summary.writelines(self.pdb_summary)
      """
      jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
      jon_summary.write("%7s<h1 class='Results'>RAPD Logfile</h1>\n%6s</div>\n%5s</div>\n"%(3*('',)))
      jon_summary.write('%5s<div id="accordion">\n%6s<h3><a href="#">Click to view log</a></h3>\n%6s<div>\n%7s<pre>\n'%(4*('',)))
      jon_summary.write('%7s</pre>\n%6s</div>\n%5s</div>\n%4s</div>\n%2s</body>\n</html>\n'%(5*('',)))
      """
      jon_summary.write('%2s</body>\n</html>\n'%'')
      jon_summary.close()        
      #copy html file to working dir
      shutil.copy(sl,self.working_dir)

    except:
      self.logger.exception('**ERROR in AutoMolRep.htmlSummaryPhaser**')

  def PrintInfo(self):
    """
    Print information regarding programs utilized by RAPD
    """
    if self.verbose:
      self.logger.debug('AutoMolRep::PrintInfo')
    try:
      self.logger.debug('RAPD now using Phenix and Phaser')
      self.logger.debug('=======================')
      self.logger.debug('RAPD developed using Phenix')
      self.logger.debug('Reference: Adams PD, et al.(2010) Acta Cryst. D66:213-221')
      self.logger.debug('Website: http://www.phenix-online.org/ \n')
      self.logger.debug('RAPD developed using Phaser')
      self.logger.debug('Reference: McCoy AJ, et al.(2007) J. Appl. Cryst. 40:658-674.')
      self.logger.debug('Website: http://www.phenix-online.org/documentation/phaser.htm \n')

    except:
      self.logger.exception('**Error in AutoMolRep.PrintInfo**')

class RunPhaser(Process):
  def __init__(self,inp,output=False,logger=None):
    """
    #The minimum input
    {'input':{'data':self.datafile,'pdb':self.input_pdb,'sg':self.sg,}
     'output','logger}
    """
    logger.info('RunPhaser.__init__')
    self.input                              = inp
    self.output                             = output
    self.logger                             = logger
    #setup params
    self.run_before                         = self.input.get('run_before',False)
    self.verbose                            = self.input.get('verbose',False)
    self.copy                               = self.input.get('copy',1)
    self.res                                = self.input.get('res',False)
    self.test                               = self.input.get('test',False)
    self.cluster_use                        = self.input.get('cluster',True) 
    self.datafile                           = self.input.get('data')
    self.input_pdb                          = self.input.get('pdb')
    self.sg                                 = self.input.get('sg')
    self.ca                                 = self.input.get('cell analysis',False)
    #self.mwaa                               = self.input.get('mwaa',False)
    #self.mwna                               = self.input.get('mwna',False)
    self.n                                  = self.input.get('name',self.sg)
    self.large_cell                         = self.input.get('large',False)
    
    Process.__init__(self,name='RunPhaser')
    self.start()

  def run(self):
    """
    Convoluted path of modules to run.
    """
    if self.verbose:
      self.logger.debug('RunPhaser::run')
    self.preprocess()
    self.process()

  def preprocess(self):
    """
    Setup Phaser input script.
    """
    if self.verbose:
      self.logger.debug('RunPhaser::preprocess')
    try:
      ft = 'PDB'
      command  = 'phaser << eof\nMODE MR_AUTO\n'
      command += 'HKLIn %s\nLABIn F=F SIGF=SIGF\n'%self.datafile
      if self.input_pdb[-3:].lower() == 'cif':
        ft = 'CIF'
      if os.path.exists(self.input_pdb):
        command += 'ENSEmble junk %s %s IDENtity 70\n'%(ft,self.input_pdb)
      else:
        command += 'ENSEmble junk %s ../%s IDENtity 70\n'%(ft,self.input_pdb)
      """
      #Makes LL-gain scores ~10% higher, but can decrease if residues are mis-identified. Not worth it.
      if self.mwaa:
        if self.mwaa > 0:
          command += 'COMPosition PROTein MW '+str(self.input['mwaa'])+' NUM '+str(self.input['copy'])+'\n'
      if self.mwna:
        if self.mwna > 0:
          command += 'COMPosition NUCLEIC MW '+str(self.input['mwna'])+' NUM '+str(self.input['copy'])+'\n'
      """
      command += 'SEARch ENSEmble junk NUM %s\n'%self.copy
      command += 'SPACEGROUP %s\n'%self.sg
      if self.ca:
        command += 'SGALTERNATIVE SELECT ALL\n'
        #Set it for worst case in orth
        command += 'JOBS 8\n'
      else:
        command += 'SGALTERNATIVE SELECT NONE\n'
      if self.run_before:
        #Picks own resolution
        #Round 2, pick best solution as long as less that 10% clashes
        command += 'PACK SELECT PERCENT\n'
        command += 'PACK CUTOFF 10\n'
      else:
        #For first round and cell analysis
        #Only set the resolution limit in the first round or cell analysis.
        if self.res:
          command += 'RESOLUTION %s\n'%self.res
        else:
          #Otherwise it runs a second MR at full resolution!!
          #I dont think a second round is run anymore.
          #command += 'RESOLUTION SEARCH HIGH OFF\n'
          if self.large_cell:
            command += 'RESOLUTION 6\n'
          else:
            command += 'RESOLUTION 4.5\n'
        command += 'SEARCH DEEP OFF\n'
        #Don't seem to work since it picks the high res limit now.
        #Get an error when it prunes all the solutions away and TF has no input.
        #command += 'PEAKS ROT SELECT SIGMA CUTOFF 4.0\n'
        #command += 'PEAKS TRA SELECT SIGMA CUTOFF 6.0\n'
      #Turn off pruning in 2.6.0
      command += 'SEARCH PRUNE OFF\n'
      #Choose more top peaks to help with getting it correct.
      command += 'PURGE ROT ENABLE ON\nPURGE ROT NUMBER 3\n'
      command += 'PURGE TRA ENABLE ON\nPURGE TRA NUMBER 1\n'
      #Only keep the top after refinement.
      command += 'PURGE RNP ENABLE ON\nPURGE RNP NUMBER 1\n'
      command += 'ROOT %s\neof\n'%self.n
      f = open('phaser.com','w')
      f.writelines(command)
      f.close()
      if self.output:
        self.output.put(command)

    except:
      self.logger.exception('**Error in RunPhaser.preprocess**')

  def process(self):
    """
    Run Phaser and pass back the pid.
    """
    if self.verbose:
      self.logger.debug('RunPhaser::process')

    try:
      command = 'tcsh phaser.com'
      if self.test:
        if self.output:
          import random
          self.output.put('junk%s'%random.randint(0,5000))
      else:
        if self.cluster_use:
          if self.large_cell:
            q = 'high_mem.q'
          else:
            q = 'all.q'
          if self.output:
            queue = Queue()
            #Process(target=Utils.processCluster,args=(self,(command,'phaser.log',q),queue)).start()
            Process(target=BLspec.processCluster,args=(self,(command,'phaser.log',q),queue)).start()
            self.output.put(queue.get())
          else:
            #Process(target=Utils.processCluster,args=(self,(command,'phaser.log',q))).start()
            Process(target=BLspec.processCluster,args=(self,(command,'phaser.log',q))).start()
        else:
          if self.output:
            queue = Queue()
            Process(target=Utils.processLocal,args=((command,'phaser.log'),self.logger,queue)).start()
            self.output.put(queue.get())
          else:
            Process(target=Utils.processLocal,args=((command,'phaser.log'),self.logger)).start()
    except:
      self.logger.exception('**Error in RunPhaser.process**')

class RunPhaser2(Process):
  def __init__(self,inp,output=False,logger=None):
    """
    ***TESTING for splitting up jobs further on the compute cluster***
    ***NOT ACTIVE***
    #The minimum input
    {'input':{'data':self.datafile,'pdb':self.input_pdb,'sg':self.sg,}
     'output','logger}
    """
    logger.info('RunPhaser.__init__')
    self.input                              = inp
    self.output                             = output
    self.logger                             = logger
    #setup params
    self.run_before                         = self.input.get('run_before',False)
    self.verbose                            = self.input.get('verbose',False)
    self.copy                               = self.input.get('copy',1)
    self.res                                = self.input.get('res',False)
    self.test                               = self.input.get('test',False)
    self.cluster_use                        = self.input.get('cluster',True) 
    self.datafile                           = self.input.get('data')
    self.input_pdb                          = self.input.get('pdb')
    self.sg                                 = self.input.get('sg')
    self.ca                                 = self.input.get('cell analysis',False)
    #self.mwaa                               = self.input.get('mwaa',False)
    #self.mwna                               = self.input.get('mwna',False)
    self.n                                  = self.input.get('name',self.sg)
    self.large_cell                         = self.input.get('large',False)
    
    Process.__init__(self,name='RunPhaser2')
    self.start()

  def run(self):
    """
    Convoluted path of modules to run.
    """
    if self.verbose:
      self.logger.debug('RunPhaser::run')
    self.preprocess()
    #self.process()

  def preprocess(self):
    import phaser
    if self.verbose:
      self.logger.debug('RunPhaser::preprocess')
    #try:
     #Read the dataset
    i = phaser.InputMR_DAT()
    i.setHKLI(self.datafile)
    #f = 'F'
    #sigf = 'SIGF'
    i.setLABI_F_SIGF('F','SIGF')
    i.setMUTE(True)
    r = phaser.runMR_DAT(i)
    if r.Success():
      for i in range(2):
        print self.process(r)
      
      
    
  def process(self,inp):
    import phaser
    r = inp
    res0 = 0.0
    i0 = phaser.InputMR_ELLG()
    i0.setSPAC_HALL(r.getSpaceGroupHall())
    i0.setCELL6(r.getUnitCell())
    i0.setMUTE(True)
    i0.setREFL_DATA(r.getDATA())
    i0.addENSE_PDB_ID("junk",self.input_pdb,0.7)
    #i.addSEAR_ENSE_NUM("junk",5)
    r1 = phaser.runMR_ELLG(i0)
    #print r1.logfile()
    if r1.Success():
      res0 = r1.get_target_resolution('junk')
    del(r1)
    return(res0)
    

  def preprocess_OLD(self):
    """
    Setup Phaser input script.
    """
    if self.verbose:
      self.logger.debug('RunPhaser::preprocess')
    try:
      command  = 'phaser << eof\nMODE MR_AUTO\n'
      command += 'HKLIn %s\nLABIn F=F SIGF=SIGF\n'%self.datafile
      if os.path.exists(self.input_pdb):
        command += 'ENSEmble junk PDB %s IDENtity 70\n'%self.input_pdb
      else:
        command += 'ENSEmble junk PDB ../%s IDENtity 70\n'%self.input_pdb
      """
      #Makes LL-gain scores ~10% higher, but can decrease if residues are mis-identified. Not worth it.
      if self.mwaa:
        if self.mwaa > 0:
          command += 'COMPosition PROTein MW '+str(self.input['mwaa'])+' NUM '+str(self.input['copy'])+'\n'
      if self.mwna:
        if self.mwna > 0:
          command += 'COMPosition NUCLEIC MW '+str(self.input['mwna'])+' NUM '+str(self.input['copy'])+'\n'
      """
      command += 'SEARch ENSEmble junk NUM %s\n'%self.copy
      command += 'SPACEGROUP %s\n'%self.sg
      if self.ca:
        command += 'SGALTERNATIVE SELECT ALL\n'
        #Set it for worst case in orth
        command += 'JOBS 8\n'
      else:
        command += 'SGALTERNATIVE SELECT NONE\n'
      if self.run_before:
        #Picks own resolution
        #Round 2, pick best solution as long as less that 10% clashes
        command += 'PACK SELECT PERCENT\n'
        command += 'PACK CUTOFF 10\n'
      else:
        #For first round and cell analysis
        #Only set the resolution limit in the first round or cell analysis.
        if self.res:
          command += 'RESOLUTION %s\n'%self.res
        else:
          #Otherwise it runs a second MR at full resolution!!
          #I dont think a second round is run anymore.
          #command += 'RESOLUTION SEARCH HIGH OFF\n'
          if self.large_cell:
            command += 'RESOLUTION 6\n'
          else:
            command += 'RESOLUTION 4.5\n'
        command += 'SEARCH DEEP OFF\n'
        #Don't seem to work since it picks the high res limit now.
        #Get an error when it prunes all the solutions away and TF has no input.
        #command += 'PEAKS ROT SELECT SIGMA CUTOFF 4.0\n'
        #command += 'PEAKS TRA SELECT SIGMA CUTOFF 6.0\n'
      #Turn off pruning in 2.6.0
      command += 'SEARCH PRUNE OFF\n'
      #Choose more top peaks to help with getting it correct.
      command += 'PURGE ROT ENABLE ON\nPURGE ROT NUMBER 3\n'
      command += 'PURGE TRA ENABLE ON\nPURGE TRA NUMBER 1\n'
      #Only keep the top after refinement.
      command += 'PURGE RNP ENABLE ON\nPURGE RNP NUMBER 1\n'
      command += 'ROOT %s\neof\n'%self.n
      f = open('phaser.com','w')
      f.writelines(command)
      f.close()
      if self.output:
        self.output.put(command)

    except:
      self.logger.exception('**Error in RunPhaser.preprocess**')

  def process_OLD(self):
    """
    Run Phaser and pass back the pid.
    """
    if self.verbose:
      self.logger.debug('RunPhaser::process')

    try:
      command = 'tcsh phaser.com'
      if self.test:
        if self.output:
          import random
          self.output.put('junk%s'%random.randint(0,5000))
      else:
        if self.cluster_use:
          if self.large_cell:
            q = 'high_mem.q'
          else:
            q = 'all.q'
          if self.output:
            queue = Queue()
            #Process(target=Utils.processCluster,args=(self,(command,'phaser.log',q),queue)).start()
            Process(target=BLspec.processCluster,args=(self,(command,'phaser.log',q),queue)).start()
            
            self.output.put(queue.get())
          else:
            #Process(target=Utils.processCluster,args=(self,(command,'phaser.log',q))).start()
            Process(target=BLspec.processCluster,args=(self,(command,'phaser.log',q))).start()
        else:
          if self.output:
            queue = Queue()
            Process(target=Utils.processLocal,args=((command,'phaser.log'),self.logger,queue)).start()
            self.output.put(queue.get())
          else:
            Process(target=Utils.processLocal,args=((command,'phaser.log'),self.logger)).start()
    except:
      self.logger.exception('**Error in RunPhaser.process**')

if __name__ == '__main__':
  #construct test input
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
  #start logging
  LOG_FILENAME = os.path.join(inp[1].get('work'),'rapd.log')
  # Set up a specific logger with our desired output level
  logger = logging.getLogger('RAPDLogger')
  logger.setLevel(logging.DEBUG)
  # Add the log message handler to the logger
  handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=100000, backupCount=5)
  #add a formatter
  formatter = logging.Formatter("%(asctime)s - %(message)s")
  handler.setFormatter(formatter)
  logger.addHandler(handler)
  AutoMolRep(inp,logger=logger)
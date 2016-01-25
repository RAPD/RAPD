"""
This file is part of RAPD

Copyright (C) 2011-2016, Cornell University
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

__created__ = "2011-12-09"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Production"

#Required params for script to run.
WORK_DIR = '/gpfs6/users/necat/Jon/RAPD_test/Temp'
#Known SG for images. P4 assumes lysozyme or thaumatin.
SPACEGROUP = 'P4'
#SPACEGROUP = 'None'

import warnings
#Remove stupid warnings about sha and md5.
with warnings.catch_warnings():
  warnings.filterwarnings("ignore", category=Warning)
  from multiprocessing import Process, Queue
  from threading import Thread
  import os
  import time, shutil, numpy, decimal, copy
  from rapd_communicate import Communicate
  from rapd_agent_strategy import RunLabelit
  import rapd_utils as Utils
  import rapd_beamlinespecific as BLspec

class FindBeamCenter(Process):
  def __init__(self, inp, output, logger=None):
    logger.info('FindBeamCenter.__init__')
    self.st = time.time()
    self.input,self.cpu,self.verbose,self.clean,self.ram,self.red = inp
    self.output                             = output
    self.logger                             = logger
    #Setting up data input
    self.setup                              = self.input[1]
    self.header                             = self.input[2]
    self.header2                            = False
    if self.input[3].has_key('distance'):
      self.header2                            = self.input[3]
      self.preferences                        = self.input[4]
    else:
      self.preferences                        = self.input[3]
    self.controller_address                 = self.input[-1]
    #Number of labelit runs to fine tune beam center and spacing from original
    #Should be even number for symmetry around original beam center
    self.iterations2                        = 10
    self.iterations2_space                  = 0.3
    #self.iterations2                        = 15
    #self.iterations2_space                  = 0.1
    #Sets the limit of the std dev (mm) of either x or y beam position in the top 10% of the solutions.
    self.std_dev                            = 0.1
    
    #Sets settings to check output on my machine and does not send results to database.
    #******BEAMLINE SPECIFIC*****
    #self.cluster_use = Utils.checkCluster()
    self.cluster_use = BLspec.checkCluster()
    
    if self.cluster_use:
      self.test                           = False
    else:
      self.test                           = True
    #******BEAMLINE SPECIFIC*****
    self.multiproc                          = True
    #Set times for processes. 'False' to disable.
    
    if self.header.get('fullname')[-3:] == 'cbf':
      self.pilatus = True
    else:
      self.pilatus = False
    #this is where I have chosen to place my results
    self.labelit_results                    = {}
    self.labelit_summary                    = False
    #Labelit settings
    self.twotheta                           = False
    self.labelit_jobs                       = {}
    self.results                            = {}
    self.runs                               = {}
    self.pool                               = {}
    #Settings for all programs
    self.x_beam         = self.header.get('beam_center_x')
    self.y_beam         = self.header.get('beam_center_y')
    self.working_dir    = self.setup.get('work')
    #self.sg             = self.header.get('spacegroup','None')
    self.distance       = os.path.basename(self.working_dir)
    
    Process.__init__(self,name='FindBeamCenter')
    self.start()
      
  def run(self):
    """
    Convoluted path of modules to run.
    """
    if self.verbose:
      self.logger.debug('FindBeamCenter::run')
    self.preprocess()
    self.sortJobs()
    self.queue()
    self.labelitSort()
    self.postprocess()
      
  def preprocess(self):
    """
    Setup the working dir in the RAM and save the dir where the results will go at the end.
    """ 
    if self.verbose:
      self.logger.debug('FindBeamCenter::preprocess')
    
    if os.path.exists(self.working_dir) == False:
      os.makedirs(self.working_dir)
    os.chdir(self.working_dir)
    #transfer images to /dev/shm on all cluster nodes
    if self.ram:
      self.transferImages()
    #print out recognition of the program being used
    #self.PrintInfo()
      
  def queue(self):
    """
    Queue for monitoring multiprocessing.process jobs.
    """
    if self.verbose:
      self.logger.debug('FindBeamCenter::queue')
    try:
      for run in self.pool.keys():
        self.postprocessJobs(self.pool[run].get())

    except:
      self.logger.exception('**Error in FindBeamCenter.queue**')
      
  def transferImages(self):
    """
    Copy images to RAM on nodes and wait for completion.
    """
    if self.verbose:
      self.logger.debug('FindBeamCenter::transferImages')
    try:
      pids = []
      end = 1
      if self.test == False:
        if self.header2:
          end = 2
        for i in range(0,end):
          if i == 0:
            orig = self.header.get('fullname')
            self.header['fullname'] = '/dev/shm/%s'%os.path.basename(orig)
          else:
            orig = self.header2.get('fullname')
            self.header2['fullname'] = '/dev/shm/%s'%os.path.basename(orig)
          command = 'cp %s %s'%(orig,os.path.join('/dev/shm',os.path.basename(orig)))
          #job = Process(target=Utils.rocksCommand,args=(self,command))
          job = Process(target=Blspec.rocksCommand,args=(self,command))
          job.start()
          pids.append(job)
        while len(pids) != 0:
          for job in pids:
            if job.is_alive() == False:
              pids.remove(job)
          time.sleep(2)

    except:
      self.logger.exception('**Error in FindBeamCenter.transferImages**')

  def postprocessJobs(self,inp):
    """
    Update the labelit results.
    """
    if self.verbose:
      self.logger.debug('FindBeamCenter::postprocessJobs')
    try:
      if inp != None:
        for key in inp:
          if self.labelit_results.has_key(key):
            self.labelit_results[key].update(inp[key])
          else:
            self.labelit_results[key] = inp[key]
            
    except:
      self.logger.exception('**Error in FindBeamCenter.postprocessJobs**')
  
  def postprocess(self):
    """
    Finish everything up.
    """
    if self.verbose:
      self.logger.debug('FindBeamCenter::postprocess')
    try:
      #Send back results
      self.output.put(self.results)
      #Cleanup folders
      if self.clean:
        #If images in RAM then delete. Could put in handler and run once...
        if self.ram:
          if self.header.get('fullname').startswith('/dev/shm'):
            #Utils.rocksCommand(self,'rm -rf %s'%self.header.get('fullname'))
            BLspec.rocksCommand(self,'rm -rf %s'%self.header.get('fullname'))
          if self.header2:
            if self.header2.get('fullname').startswith('/dev/shm'):
              #Utils.rocksCommand(self,'rm -rf %s'%self.header2.get('fullname'))
              BLspec.rocksCommand(self,'rm -rf %s'%self.header2.get('fullname'))
        #Cleanup folders in working dir.
        shutil.rmtree(self.working_dir,ignore_errors=True)
            
    except:
      self.logger.exception('**Error in FindBeamCenter.postprocess**')
  
  def sortJobs(self):
    """
    Decides how many Labelit jobs to run and sorts them among the processors available.
    """
    if self.verbose:
      self.logger.debug('FindBeamCenter::sortJobs')
    try:
      inp = {}
      #Save initial beam center.
      orig_x = self.x_beam
      orig_y = self.y_beam
      new_input = copy.copy(self.input)
      if self.header2:
        i = 4
      else:
        i = 3
      #Remove alternative way to input beam center.
      if self.input[i].has_key('x_beam'):
        #self.input[i].pop('x_beam')
        del self.input[i]['x_beam']
      if self.input[i].has_key('y_beam'):
        #self.input[i].pop('y_beam')
        del self.input[i]['y_beam']
      #Calculate new beam centers and save them.
      med = int(self.iterations2/2)
      for x in range(self.iterations2+1):
        if x <= med:
          new_x_beam = float(orig_x)-x*self.iterations2_space
        else:
          new_x_beam = float(orig_x)+(x-med)*self.iterations2_space
        for y in range(self.iterations2+1):
          if y <= med:
            new_y_beam = float(orig_y)-y*self.iterations2_space
          else:
            new_y_beam = float(orig_y)+(y-med)*self.iterations2_space
          name = 'bc_%s_%s'%(x,y)
          #Start the results by saving the new beam center.
          self.labelit_results[name] = {'beam_X': str(new_x_beam),'beam_Y': str(new_y_beam)}
          #Save the working path and new beam center to new input. 
          for z in range(i-1):
            junk = new_input[z+1].copy()
            if z == 0:
              junk.update({'work': os.path.join(os.getcwd(),name)})
            else:
              junk.update({'beam_center_x': str(new_x_beam),'beam_center_y': str(new_y_beam)})
            new_input[z+1] = junk
          inp[name] = copy.copy(new_input)
      #Split up the jobs and run on separate CPU's.
      tot2 = len(self.labelit_results)
      split = int(tot2/self.cpu)
      diff = tot2-(split*self.cpu)
      for x in range(self.cpu):
        runs = {}
        s = int(split*x)
        #Add left over runs to last run
        if x == self.cpu-1:
          f = int(split*(x+1)+diff)
        else:
          f = int(split*(x+1))
        for name in self.labelit_results.keys()[s:f]:
            runs[name] = inp[name]
        self.pool[str(x)] = Queue()
        inp1 = {'inp':(runs,self.clean,self.test,self.verbose,self.pilatus,self.red),'output':self.pool[str(x)],'logger':self.logger}
        Process(target=LabelitAction,kwargs=inp1).start()
    
    except:
      self.logger.exception('**ERROR in FindBeamCenter.sortJobs**')
      
  def labelitSort(self):
    """
    Figure out which round has the best index fit.
    """
    if self.verbose:
      self.logger.debug('FindBeamCenter::labelitSort')
    
    try:
      li = []
      stats = {}
      passed = True
      orig_sg = 1
      #if self.sg == None:
      if SPACEGROUP == 'None':
        find_sg = True
      else:
        find_sg = False
      #Label the SG and grab the solutions with the highest SG.
      for i in range(0,2):
        for run in self.labelit_results.keys():
          if run.startswith('bc_'):
            if type(self.labelit_results[run].get('Labelit results')) == dict:
              if i == 0:
                #Check for pseudotranslation, meaning bad snap!!!
                if self.labelit_results[run].get('Labelit results').get('pseudotrans'):
                  #passed = False
                  pass
                #Get Labelit stats and SG#
                Utils.getLabelitStats(self,run)
                sg = self.labelit_results[run].get('labelit_stats').get('best').get('SG')
                new_sg = float(Utils.convertSG(self,sg))
                self.labelit_results[run].update({'labelit_best_sg#': new_sg})
                if find_sg:
                  if new_sg > orig_sg:
                    SPACEGROUP = sg
                    orig_sg = new_sg
              else:
                #Make sure I compare same SG.
                if self.labelit_results[run].get('labelit_stats').get('best').get('SG') == SPACEGROUP:
                  li.append(run)
                else:
                  del self.labelit_results[run]
      #Calculate the number of solutions for 10% of correct SG and check if enough are present.
      l = len(li)
      if l > 0:
        top = int(round(l*0.1))
        if top < 5:
          if l < top:
            top = l
          else:
            top = 5
        """
        #Does not seem to matter.
        test = decimal.Decimal(l)/decimal.Decimal(len(runs))
        if test < decimal.Decimal('0.1'):
            passed = False
        """
        #Print results for testing.
        if self.verbose:
          #print 'Iteration=',str(self.iteration)
          print 'Total number of Labelit runs: %s'%len(self.labelit_results.keys())
          print 'Total number of solutions in %s: %s'%(SPACEGROUP, l)
          print 'Number of solutions in the top 10%% = %s'%top
          self.logger.debug('Total number of Labelit runs: %s'%len(self.labelit_results.keys()))
          self.logger.debug('Total number of solutions in %s: %s'%(SPACEGROUP, l))
          self.logger.debug('Number of solutions in the top 10%% = %s'%top)
        #Sort solutions in correct SG by each param
        ls = [("self.labelit_results[run].get('labelit_stats').get('P1').get('rmsd')","Labelit P1 RMSD"),
              ("self.labelit_results[run].get('labelit_stats').get('P1').get('mos_rms')","Mosflm P1 RMS"),
              ("self.labelit_results[run].get('labelit_stats').get('best').get('metric')","Labelit Metric"),
              ("self.labelit_results[run].get('labelit_stats').get('best').get('rmsd')","Labelit RMSD"),
              ("self.labelit_results[run].get('labelit_stats').get('best').get('mos_rms')","Mosflm RMS")]
        for z in range(5):
          dict1 = {}
          for run in li:
            dict1[run] = float(eval(ls[z][0]))
          li1 = dict1.values()
          li1.sort()
          #Grab the top 10%.
          li1_top = li1[:top]
          li2 = []
          for run in li:
            for line in li1_top:
              if dict1[run] == line:
                li2.append(run)
                li1_top.remove(line)
                if line == li1[0]:
                  top1 = run
          #Grab the Labelit beam centers and calculate the stats.
          x = []
          y = []
          for run in li2:
            x.append(float(self.labelit_results[run].get('Labelit results').get('labelit_bc').get('labelit_x_beam')))
            y.append(float(self.labelit_results[run].get('Labelit results').get('labelit_bc').get('labelit_y_beam')))
          #stats[li[z][1]] = {'avg_x': numpy.average(x), 'std_x': numpy.std(x), 'avg_y': numpy.average(y), 'std_y': numpy.std(y),
          #                      'sum_std': numpy.std(x)+numpy.std(y), 'j1': li[z][0], 'top': top1}
          stats[ls[z][1]] = {'avg_x': numpy.average(x), 'std_x': numpy.std(x), 'avg_y': numpy.average(y), 'std_y': numpy.std(y),
                             'sum_std': numpy.std(x)+numpy.std(y), 'j1': ls[z][0], 'top': top1}
        #Sort all results by lowest sum of std dev (x+y) and save the best.
        temp = []
        for i in range(2):
          for key in stats.keys():
            if i == 0:
              #First, save the lowest sum_std.
              temp.append(stats[key].get('sum_std'))
            else:
              if stats[key].get('sum_std') == temp[0]:
                #Check the std dev. 
                if decimal.Decimal(str(stats[key].get('std_x'))) > decimal.Decimal(str(self.std_dev)):
                  passed = False
                if decimal.Decimal(str(stats[key].get('std_y'))) > decimal.Decimal(str(self.std_dev)):
                  passed = False
                #Save best results for each distance for further calculations.
                self.results['orig_X'] = self.x_beam
                self.results['orig_Y'] = self.y_beam
                self.results['X'] = stats[key].get('avg_x')
                self.results['Y'] = stats[key].get('avg_y')
                self.results['passed'] = passed
                #best = stats[key].get('top')
                if self.verbose:
                  print '****************************************'
                  print 'At %s mm:'%self.distance
                  print 'Best stats from %s'%key
                  print 'X =%s std=%s'%(stats[key].get('avg_x'),stats[key].get('std_x'))
                  print 'Y =%s std=%s'%(stats[key].get('avg_y'),stats[key].get('std_y'))
                  print 'Good results=%s'%passed
                  print '****************************************'
                  self.logger.debug('****************************************')
                  self.logger.debug('At %s mm:'%self.distance)
                  self.logger.debug('Best stats from %s'%key)
                  self.logger.debug('X =%s std=%s'%(stats[key].get('avg_x'),stats[key].get('std_x')))
                  self.logger.debug('Y =%s std=%s'%(stats[key].get('avg_y'),stats[key].get('std_y')))
                  self.logger.debug('Good results=%s'%passed)
                  self.logger.debug('****************************************')
          if i == 0:
            temp.sort()
      else:
        self.results = {'passed':False}
            
    except:
      self.logger.exception('**ERROR in FindBeamCenter.labelitSort**')
      self.results = {'passed':False}

class LabelitAction(Process):
  """
  Run Labelit.
  """
  def __init__(self,inp,output,logger=None):
    logger.info('LabelitAction.__init__')
    self.st = time.time()
    self.input,self.clean,self.test,self.verbose,self.pilatus,self.red = inp
    self.output2                              = output
    self.logger                               = logger
    
    self.labelit_jobs                       = {}
    self.pool                               = {}
    self.working_dir                        = os.getcwd()
    self.multiproc                          = True
    
    #******BEAMLINE SPECIFIC*****
    #self.cluster_use = Utils.checkCluster()
    self.cluster_use = BLspec.checkCluster()
    #******BEAMLINE SPECIFIC*****
    
    #initialize the thread
    Process.__init__(self,name='LabelitAction')
    #start the process
    self.start()
      
  def run(self):
    if self.verbose:
      self.logger.debug('LabelitAction::run')
    
    self.processLabelit()
    self.Queue()
      
  def processLabelit(self):
    """
    Labelit error correction. Set/reset setting in dataset_preferences.py according to error iteration.
    Commented out things were tried before.
    """
    if self.verbose:
      self.logger.debug('LabelitAction::preprocessLabelit')
    try:
      params = {}
      params['test'] = self.test
      params['cluster'] = self.cluster_use
      params['redis'] = self.red
      params['iterations'] = 1
      """
      if self.pilatus:
        params['iterations'] = 1
      else:
        params['iterations'] = 4
      """
      #Otherwise too much goes to the log.
      params['verbose'] = False
      for name in self.input.keys():
        self.pool[name] = Queue()
        if self.red:
          self.red.blpop('bc_throttler')
        job = Process(target=RunLabelit,args=(self.input[name],self.pool[name],params,self.logger))
        job.start()
        self.labelit_jobs[job] = name

    except:
      self.logger.exception('**Error in LabelitAction.preprocessLabelit**')

  def Queue(self):
    """
    Queue for Labelit.
    """
    if self.verbose:
      self.logger.debug('LabelitAction::Queue')
    try:
      out = {}
      #pids = self.labelit_jobs.keys()[:100]
      for job in self.labelit_jobs.keys():
        iteration = self.labelit_jobs[job]
        out[str(iteration)] = self.pool[iteration].get()
        #clean up folders
        if self.clean:
          if os.path.exists(os.path.join(self.working_dir,str(iteration))):
            shutil.rmtree(os.path.join(self.working_dir,str(iteration)),ignore_errors=True)
      self.logger.debug('RunLabelit finished.')
      #Send back the results.
      self.output2.put(out)

    except:
      self.logger.exception('**Error in LabelitAction.Queue**')
      self.output2.put(None)

#class Handler(threading.Thread,Communicate):
class Handler(Process,Communicate):
  """
  Looks at the input to determine how to run the process. Runs the process and passes the results back.
  """
  def __init__(self,input,logger=None):
    logger.info('Handler.__init__')
    self.st = time.time()
    self.input                              = input
    if self.input == None:
      os._exit(0)
    self.logger                             = logger
    #Setting up data input
    self.setup                              = self.input[1]
    self.controller_address                 = self.input[-1]
    
    self.jobs                               = {}
    self.results                            = {}
    self.output                             = {}
    #Set a timer to limit length Labelit waits for results before aborting.
    self.timer                              = False
    #Cleanup all the folders and files after running.
    self.clean                              = True
    #Turn on verbose output.
    self.verbose                            = True
    #Setup a Redis database for comtrolling job submission to cluster. Its much faster and doesn't clog the queue.
    self.red                                = True
    #Copy images to RAM on all cluster nodes
    self.ram                                = True
    #Limit launching of LABELIT jobs to this number (FALSE to disable).
    self.job_limit                          = 256
    
    #Utils.pp(self.input)
    #******BEAMLINE SPECIFIC*****
    """
    if self.input[-2].get('aperture',False):
      self.beamline_use                   = True
    else:
      self.beamline_use                   = False
    """
    self.beamline_use                   = True
    #******BEAMLINE SPECIFIC*****
    #initialize the thread
    Process.__init__(self)
    
    #start the thread
    self.start()
      
  def run(self):
    if self.verbose:
      self.logger.debug('Handler::run')
    self.process()
    self.queue()
    self.sort()
    self.postprocess()
      
  def process(self):
    """
    Create input dict and send to FindBeamCenter.
    """
    if self.verbose:
      self.logger.debug('Handler::process')
    try:
      setup = self.setup.get('info')
      """
      njobs = len(setup)
      cpu = multiprocessing.cpu_count()
      ncpu = cpu/njobs
      if ncpu == 0:
          ncpu = 1
      """
      #Seems to give best load and speed on our cluster.
      ncpu = 1
      #Limit the number of Labelit jobs running at a time on cluster. Could use queue system on cluster, but this seems much faster.
      if self.job_limit:
        import redis
        self.red = redis.Redis('164.54.212.169',6380)#remote
        for i in range(self.job_limit):
          self.red.lpush('bc_throttler',1)

      od = self.input[1].get('work')
      for job in setup.keys():
        #if job in ('200'):
        new_input = []
        new_input.append(self.input[0])
        nd = os.path.join(od,job)
        new_input.append({'work':nd})
        for header in setup[job]:
          new_input.append(header)
        new_input.extend(self.input[-2:])
        self.output[job] = Queue()
        j = Process(target=FindBeamCenter,kwargs={'inp':(new_input,ncpu,self.verbose,self.clean,self.ram,self.red),
                                                         'output':self.output[job],'logger':self.logger})
        j.start()
        self.jobs[j] = job
        
    except:
      self.logger.exception('**Error in Handler.process**')
  
  def queue(self):
    """
    Queue for jobs running.
    """
    if self.verbose:
        self.logger.debug('Handler::queue')
    try:
        timer = 0
        jobs = self.jobs.keys()
        if jobs != ['None']:
          counter = len(jobs)
          while counter != 0:
            for job in jobs:
              if job.is_alive() == False:
                jobs.remove(job)
                distance = self.jobs[job]
                self.logger.debug('Finished distance %s'%distance)
                self.results[distance] = self.output[distance].get()
                counter -= 1
            time.sleep(2)
            timer += 2
            if self.verbose:
              print 'Waiting for Labelit to finish %s seconds'%timer
            if self.timer:
              if timer >= self.timer:
                timed_out = True
                #Check folders to see why it timed out.
                self.clean = False
                break 
        self.logger.debug('Labelit finished.')
        #Delete the redis database.
        if self.red:
          self.red.delete('bc_throttler')

    except:
      self.logger.exception('**Error in Handler.queue**')
      
  def sort(self):
    """
    Sort results by distance for calculations.
    """
    if self.verbose:
      self.logger.debug('Handler::sort')
    try:
      """
      #Utils.pp(self,self.results)
      #Q315
      self.results = {   '400': {    #'X': 156.69,
                                     'X': 156.65,
                                     'Y': 155.72999999999999,
                                     'orig_X': '156.67',
                                     'orig_Y': '155.70',
                                     'passed': True},
                          '500_0': {   'X': 156.25799999999998,
                                       'Y': 155.61000000000001,
                                       'orig_X': '156.19',
                                       'orig_Y': '155.61',
                                       'passed': True},
                          '500_1': {   'X': 156.25799999999998,
                                       'Y': 155.61000000000001,
                                       'orig_X': '156.19',
                                       'orig_Y': '155.61',
                                       'passed': True},
                          '500_2': {   'X': 156.262,
                                       'Y': 155.61799999999999,
                                       'orig_X': '156.19',
                                       'orig_Y': '155.61',
                                       'passed': True},
                          '500_3': {   'X': 156.25,
                                       'Y': 155.61000000000001,
                                       'orig_X': '156.19',
                                       'orig_Y': '155.61',
                                       'passed': True},
                          '550': {   'X': 156.00200000000001,
                                     'Y': 155.57599999999999,
                                     'orig_X': '155.97',
                                     'orig_Y': '155.56',
                                     'passed': True}
                      }
      
      #Pilatus
      self.results = {   '150': {   'X': 217.52400000000003,
                                   'Y': 221.81199999999998,
                                   #'diff_X': '-0.136',
                                   #'diff_Y': '-0.268',
                                   'passed': True,
                                   'orig_X': '217.66',
                                   'orig_Y': '222.08'},
                          '200': {   'X': 217.38666666666668,
                                   'Y': 221.73166666666668,
                                   #'diff_X': '-0.0633333333333',
                                   #'diff_Y': '-0.158333333333',
                                   'passed': True,
                                   'orig_X': '217.45',
                                   'orig_Y': '221.89'},
                          '300': {   'X': 217.31777777777774,
                                   'Y': 221.72888888888892,
                                   #'diff_X': '0.0777777777777',
                                   #'diff_Y': '-0.0811111111111',
                                   'passed': True,
                                   'orig_X': '217.24',
                                   'orig_Y': '221.81'},
                          '400': {   'X': 217.21818181818179,
                                   'Y': 221.64272727272729,
                                   #'diff_X': '0.0681818181818',
                                   #'diff_Y': '-0.167272727273',
                                   'passed': True,
                                   'orig_X': '217.15',
                                   'orig_Y': '221.81'},
                          '500': {   'X': 217.21333333333334,
                                   'Y': 221.60249999999996,
                                   #'diff_X': '0.103333333333',
                                   #'diff_Y': '-0.1375',
                                   'passed': True,
                                   'orig_X': '217.11',
                                   'orig_Y': '221.74'},
                          '600': {   'X': 217.17416666666668,
                                   'Y': 221.4433333333333,
                                   #'diff_X': '0.0741666666667',
                                   #'diff_Y': '-0.186666666667',
                                   'passed': True,
                                   'orig_X': '217.10',
                                   'orig_Y': '221.63'},
                          '700': {   'X': 217.17333333333329,
                                   'Y': 221.39166666666668,
                                   #'diff_X': '0.0233333333333',
                                   #'diff_Y': '-0.138333333333',
                                   'passed': True,
                                   'orig_X': '217.15',
                                   'orig_Y': '221.53'},
                          '800': {   'X': 217.3075,
                                   'Y': 221.41999999999999,
                                   #'diff_X': '0.0875',
                                   #'diff_Y': '-0.09',
                                   'passed': True,
                                   'orig_X': '217.22',
                                   'orig_Y': '221.51'},
                          '1000': {   'X': 217.32666666666668,
                                    'Y': 221.51416666666668,
                                    #'diff_X': '0.0466666666667',
                                    #'diff_Y': '-0.0958333333333',
                                    'passed': True,
                                    'orig_X': '217.28',
                                    'orig_Y': '221.61'},
                          '1200': {   'X': 217.28666666666672,
                                    'Y': 221.43166666666664,
                                    #'diff_X': '-0.0333333333333',
                                    #'diff_Y': '-0.148333333333',
                                    'passed': True,
                                    'orig_X': '217.32',
                                    'orig_Y': '221.58'},
                      }
      
      """
      #Separate out the same distance runs.
      res = {}
      new_res = {}
      for job in self.results.keys():
        if self.results[job].get('passed'):
          #If multiple runs at same distance.
          if job.count('_'):
            dis = job[:job.index('_')]
            if job.startswith(dis):
              if res.has_key(dis):
                l = []
                l.extend(res[dis])
                l.extend([job])
                res[dis] = l
              else:
                res[dis] = [job]
          else:
            new_res[int(float(job))] = self.results[job]
              
      #Calculate average and std. dev of same distance runs. Toss worst solution if std. dev > 0.1 and recalc average, if 3 or more at same distance.
      l = ['X','Y']
      for dis in res.keys():
        new_res[int(dis)] = {}
        for i in range(len(l)):
          recalc = False
          while 1:
            bp = []
            for run in res[dis]:
              bp.append(self.results[run].get(l[i]))
              orig = self.results[run].get('orig_%s'%l[i])
            avg = numpy.around(numpy.average(bp),decimals=2)
            std = numpy.std(bp)
            tmp = {l[i] : float(avg),'orig_%s'%l[i]:orig}
            new_res[int(float(dis))].update(tmp)
            #If at least 3 at same distance...
            if len(bp) > 2:
              if recalc:
                break
              else:
                if std > decimal.Decimal('0.1'):
                  recalc = True
                  junk = {}
                  for run in res[dis]:
                    x1 = self.results[run].get(l[i])
                    diff = numpy.absolute(x1-avg)
                    junk[diff] = run
                  l = junk.keys()
                  l.sort()
                  l.reverse()
                  for d in junk.keys():
                    if d == l[0]:
                      res[dis].remove(junk[d])
              if recalc == False:
                break
            else:
              break
      
      for dis in new_res.keys():
        #Remove 'passed' key
        if new_res[dis].has_key('passed'):
          del new_res[dis]['passed']
        for i in range(len(l)):
          #Figure out detector
          if new_res[dis].get(l[i]) > 200.0:
            pilatus = True
          else:
            pilatus = False
          #calculate beam shift.
          diff = new_res[dis].get(l[i]) - float(new_res[dis].get('orig_%s'%l[i]))
          new_res[dis].update({'diff_%s'%l[i] : str(diff)})
              
      #Calculate the 6th order polynomial from data if 3 or more distances present.
      if len(new_res.keys()) > 2:
        temp = {}
        #Write line for file to use for image header beam position (NE-CAT ONLY for CONSOLE).
        if pilatus:
          f = 'phi_bc_coeff.dat'
        else:
          f = 'phii_bc_coeff.dat'
        f1 = open(f,'w')
        for i in range(len(l)):
          d = new_res.keys()
          d.sort()
          bp = []
          for dis in d:
            bp.append(new_res[dis].get(l[i]))
          da = numpy.array(d)
          ba = numpy.array(bp)
          (AX,BX,CX,DX,EX,FX,GX) = numpy.polyfit(da,ba,6)
          temp['%s beam eq'%l[i]] = {"beam_center_%s_m6"%l[i].lower():AX,
                                     "beam_center_%s_m5"%l[i].lower():BX,
                                     "beam_center_%s_m4"%l[i].lower():CX,
                                     "beam_center_%s_m3"%l[i].lower():DX,
                                     "beam_center_%s_m2"%l[i].lower():EX,
                                     "beam_center_%s_m1"%l[i].lower():FX,
                                     "beam_center_%s_b"%l[i].lower():GX}
          print '%s %s %s %s %s %s %s\n'%(GX,FX,EX,DX,CX,BX,AX)
          f1.write('%s %s %s %s %s %s %s\n'%(GX,FX,EX,DX,CX,BX,AX))
        f1.close()
        new_res.update(temp)
        #Change ownership for SAMBA. DOESN'T WORK.
        #os.chown(f,'nobody','nobody')
      else:
        new_res['X beam eq'] = None
        new_res['Y beam eq'] = None
      
      #Overwrite self.results
      self.results = new_res
      #self.logger.debug(self.results)
           
    except:
      self.logger.exception('**Error in Handler.sort**')
  
  def postprocess(self):
    """
    Pass info back to the core.
    """
    if self.verbose:
      self.logger.debug('Handler::postprocess')
    try:
      #Summary.summaryLabelitBC(self)
      #self.htmlSummary()
      beam_status = {}
      beam_status['beam_status'] = 'SUCCESS'
      #Send back results
      try:
        self.results.update(beam_status)
        if self.results:
          self.input.append(self.results)
        if self.beamline_use:
          self.sendBack2(self.input)
        else:
          Utils.pp(self.results)
          #Save results to file so it can be read in RunCLuster if needed.
          Utils.pp2((self.results,os.path.join(self.input[1].get('work'),'bc.log')))
      except:
        self.logger.exception('**Could not send results to pipe.**')
      
      #Say job is complete.
      t = round(time.time()-self.st)
      self.logger.debug('-------------------------------------')
      self.logger.debug('RAPD beam center complete.')
      self.logger.debug('Total elapsed time: %s seconds'%t)
      self.logger.debug('-------------------------------------')
      print '\n-------------------------------------'
      print 'RAPD beam center complete.'
      print 'Total elapsed time: %s seconds'%t
      print '-------------------------------------'
      #return(self.results)
      #sys.exit(0) #did not appear to end script with some programs continuing on for some reason.
      os._exit(0)
      #sys.exit(0)

    except:
      self.logger.exception('**Error in Handler.postprocess**')

class RunCluster(Thread):
  def __init__(self,inp,logger=None):
    logger.info('RunCluster.__init__')
    self.image_dir            = inp
    self.logger               = logger
    #self.ex                   = ex
    #self.work_dir             = '/gpfs6/users/necat/Jon/RAPD_test/Temp'
    #self.work_dir             = os.getcwd()
    self.log = os.path.join(WORK_DIR,'bc.log')
    self.timer                = 600
    self.verbose              = True
    self.running              = False
    self.cluster_use          = False
    
    Thread.__init__(self)
    #start the thread
    self.start()
      
  def run(self):
    if self.verbose:
      self.logger.debug('RunCluster::run')
    
    self.conCluster()
    self.queue()
    
  def conCluster(self):
    """
    If not running on computer cluster, connect to node and launch.
    """
    try:
      command = '-pe smp 8 -o %s rapd3.python /gpfs5/users/necat/rapd/gadolinium/trunk/rapd_agent_beamcenter.py %s'%(self.log,self.image_dir)
      #os.chdir(self.work_dir)
      os.chdir(WORK_DIR)
      #self.pid = Utils.connectCluster(command)
      self.pid = BLspec.connectCluster(command)

    except:
      self.logger.exception('**Error in RunCluster::conCluster**')
      
  def queue(self):
    if self.verbose:
      self.logger.debug('RunCluster::queue')
    timer = 0
    while timer < self.timer:
      #if Utils.stillRunningCluster(self,self.pid) == False:
      if BLspec.stillRunningCluster(self,self.pid) == False:
        self.postprocess()
        break
      time.sleep(1)
      timer += 1
          
  def postprocess(self):
    """
    Print the log to the screen
    """
    if self.verbose:
      self.logger.debug('RunCluster::postprocess')
    #Need to wait for it to be written to disk.
    time.sleep(2)
    for line in open(self.log,'r').readlines():
      print line.rstrip()
    l = [os.path.join(WORK_DIR,'phi_bc_coeff.dat'),os.path.join(WORK_DIR,'phii_bc_coeff.dat')]
    for x in range(len(l)):
      if os.path.exists(l[x]):
        for line in open(l[x],'r').readlines():
          print line.rstrip()
        
def createInput(image_dir,logger):
  logger.debug('createInput')
  import glob
  
  try:
    l = glob.glob(os.path.join(image_dir,'*.cbf'))
    l1 = []
    l2 = []
    d = {}
    if len(l) == 0:
      #from rapd_adsc import AdscReadHeader as getHeader
      import aps_24ide as Detector
      l = glob.glob(os.path.join(image_dir,'*.img'))
    else:
      #from rapd_pilatus import PilatusReadHeader as getHeader
      import aps_24idc as Detector
    #Remove priming shot (NE-CAT ONLY)
    l.sort()
    l = [p for p in l if p.count('priming_shot') == False]
    for x in range(2):
      for i in l:
        if x == 0:
          #Get headers first
          header = Detector.read_header(i)
          l1.append({'beam_center_x' : header.get('beam_x'),
                       'beam_center_y' : header.get('beam_y'),
                       'spacegroup'    : SPACEGROUP,
                       'fullname'      : header.get('fullname'),
                       'distance'      : round(header.get('distance'))
                       })
          """
          #For overwriting an incorrect BC from a header.
          if round(header.get('distance')) == 1000.0:
            l1.append({'beam_center_x' : 145.30,
                       'beam_center_y' : 158.60,
                       #Assuming thaumatin or lysozyme
                       'spacegroup'    : SPACEGROUP,
                       'fullname'      : header.get('fullname'),
                       'distance'      : round(header.get('distance'))
                     })
          else:
            l1.append({'beam_center_x' : header.get('beam_x'),
                       'beam_center_y' : header.get('beam_y'),
                       #Assuming thaumatin or lysozyme
                       'spacegroup'    : SPACEGROUP,
                       'fullname'      : header.get('fullname'),
                       'distance'      : round(header.get('distance'))
                       })
          """
        else:
          #Then sort by distance for input
          l3 = []
          if i not in (l2):
            for y in range(2):
              for z in range(len(l1)):
                if y == 0:
                  if i == l1[z].get('fullname'):
                    dist = l1[z].get('distance')
                    l3.append(l1[z])
                    l2.append(l1[z].get('fullname'))
                elif l1[z].get('distance') == dist:
                  if l1[z].get('fullname') not in l2:
                    l3.append(l1[z])
                    l2.append(l1[z].get('fullname'))
            d[str(dist)] = tuple(l3[:2])
    #Utils.pp(d)
    inp = ["AUTOINDEX",{"work": WORK_DIR,"info": d},None,
           {"sample_type": "Protein","beam_flip": "False","multiprocessing":"True",
            "a":0.0,"b":0.0,"c":0.0,"alpha":0.0,"beta":0.0,"gamma":0.0},
           ("127.0.0.1",50001)]
    return(inp)
  
  except:
      logger.exception('**Error in Handler.postprocess**')
      print 'Could not create input script from folder specified!'
      return(None)

def main():
  """
  This pipeline has to be run on a computer cluster. It launches many Labelit autoindexing runs varying input beamcenter
  for each distance, then looks at all the refined beam center outputs and fits to a 6th order polymonial.
  """
  #start logging
  import logging,logging.handlers
  LOG_FILENAME = os.path.join(os.getcwd(),'rapd.log')
  #inp = Input.input()
  # Set up a specific logger with our desired output level
  logger = logging.getLogger('RAPDLogger')
  logger.setLevel(logging.DEBUG)
  # Add the log message handler to the logger
  handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,maxBytes=10000000,backupCount=5)
  #add a formatter
  formatter = logging.Formatter("%(asctime)s - %(message)s")
  handler.setFormatter(formatter)
  logger.addHandler(handler)
  logger.info('__init__')
  
  import argparse
  #Parse the command line for commands.
  parser = argparse.ArgumentParser(description='Run job on computer cluster.')
  parser.add_argument('inp' ,nargs='*', type=str, help='folder')
  args = vars(parser.parse_args())
  if len(args['inp']) == 0:
    image_dir = raw_input('In what folder do the direct beam shots exist?: ')
  else:
    image_dir = args['inp'][0]
  #if Utils.checkCluster():
  if BLspec.checkCluster():
    #Creates the input dict and passes it to the Handler.
    Handler(createInput(image_dir,logger),logger=logger)
  else:
    #Connect to the cluster and rerun this script if not launched on computer cluster.
    RunCluster(image_dir,logger=logger)
if __name__ == '__main__':
  main()

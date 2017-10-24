"""
This file is part of RAPD

Copyright (C) 2016-2017 Cornell University
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

__created__ = "2016-03-07"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Development"

"""
Provides generic interface for cluster interactions
"""

# Standard imports
import os
import time
import tempfile
import shlex

# Non-standard imports
import drmaa
import random
import subprocess

def check_cluster():
    """
    Quick check run at beginning of pipelines to see if job was subitted to computer cluster node (returns True) or
    run locally (returns False). The pipelines will use this to know whether to subprocess.Process subjobs or submit to
    compute cluster queueing system. This is the master switch for turning on or off a compute cluster.
    """
    import socket
    #Can create a list of names of your compute nodes for checking. Ours all start with 'scyld'.
    if socket.gethostname().startswith('scyld'):
        return True
    else:
        return False

def check_queue(inp):
    """
    Returns which cluster queue should be used with the pipeline.
    """
    d = {"INDEX+STRATEGY" : False,
         "BEAMCENTER"     : False,
         }
    return(d[inp])
    

def process_cluster_drmaa(self, inp, output=False):
    """
    Submit job to cluster using DRMAA (when you are already on the cluster).
    Main script should not end with os._exit() otherwise running jobs could be orphanned.
    To eliminate this issue, setup self.running = multiprocessing.Event(),
    self.running.set() in main script, then set it to False (self.running.clear())
    during postprocess to kill running jobs smoothly.
    Will not allow jobs to submit child processes!!!
    """

    s = False
    jt = False
    running = True
    log = False
    queue = False
    smp = 1
    name = False

    # Check if self.running is setup... used for Best and Mosflm strategies
    # because you can't kill child processes launched on cluster easily.
    try:
        __ = self.running
    except AttributeError:
        running = False

    # print inp
    if type(inp) != tuple:
        command = inp
    else:
      if len(inp) == 1:
        command = inp
      elif len(inp) == 2:
        command, log = inp
      elif len(inp) == 3:
        command, log, queue = inp
      elif len(inp) == 4:
        command, log, smp, queue = inp
      else:
        command, log, smp, queue, name = inp
    if queue == False:
        queue = "all.q"

    # Queues aren't used right now.


    # Setup path
    v = "-v PATH=/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/etc:\
/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/bin:\
/home/schuerjp/Programs/best:\
/home/schuerjp/Programs/RAPD/bin:\
/home/schuerjp/Programs/RAPD/share/phenix-1.10.1-2155/build/bin:\
/home/schuerjp/Programs/raddose-20-05-09-distribute-noexec/bin:\
/usr/local/bin:/bin:/usr/bin"
    #smp,queue,name = inp2
    #'-clear' can be added to the options to eliminate the general.q
    #options = '-clear -shell y -p -100 -q %s -pe smp %s'%(queue,smp)
    #options = '-V -l nodes=1:ppn=%s pbs.sh'%smp
    #options = '%s -l nodes=1:ppn=%s -S /bin/tcsh'%(v,smp)
    options = "%s -l nodes=1:ppn=%s" % (v, smp)
    s = drmaa.Session()
    s.initialize()
    jt = s.createJobTemplate()
    jt.workingDirectory = os.getcwd()
    jt.joinFiles = True
    jt.nativeSpecification = options
    jt.remoteCommand = command.split()[0]
    #jt.jobName = '%s'%random.randint(0,5000)
    if len(command.split()) > 1:
        jt.args = command.split()[1:]
    if log:
        # The ":" is required!
        jt.outputPath = ":%s" % os.path.join(os.getcwd(), log)

    # Submit the job to the cluster and get the job_id returned
    job = s.runJob(jt)

    # Return job_id.
    #if isinstance(output, dict):
    if output != False:
        output.put(job)

    # Cleanup the input script from the RAM.
    s.deleteJobTemplate(jt)

    # If multiprocessing.event is set, then run loop to watch until job or script has finished.
    if running:
        # Returns True if job is still running or False if it is dead. Uses CPU to run loop!!!
        decodestatus = {drmaa.JobState.UNDETERMINED: True,
                        drmaa.JobState.QUEUED_ACTIVE: True,
                        drmaa.JobState.SYSTEM_ON_HOLD: True,
                        drmaa.JobState.USER_ON_HOLD: True,
                        drmaa.JobState.USER_SYSTEM_ON_HOLD: True,
                        drmaa.JobState.RUNNING: True,
                        drmaa.JobState.SYSTEM_SUSPENDED: False,
                        drmaa.JobState.USER_SUSPENDED: False,
                        drmaa.JobState.DONE: False,
                        drmaa.JobState.FAILED: False}

        # Loop to keep hold process while job is running or ends when self.running event ends.
        while decodestatus[s.jobStatus(job)]:
            if self.running.is_set() == False:
                s.control(job, drmaa.JobControlAction.TERMINATE)
                self.logger.debug("job:%s terminated since script is done" % job)
                break
            time.sleep(1)

    # Otherwise just wait for it to complete.
    else:
        s.wait(job, drmaa.Session.TIMEOUT_WAIT_FOREVER)

    # Exit cleanly, otherwise master node gets event client timeout errors after 600s.
    s.exit()

    print "Job finished"
    
def process_cluster_old(self, inp, output=False):
    s = False
    jt = False
    running = True
    log = False
    queue = False
    smp = 1
    name = False
    l = []

    # Check if self.running is setup... used for Best and Mosflm strategies
    # because you can't kill child processes launched on cluster easily.
    try:
        __ = self.running
    except AttributeError:
        running = False

    # print inp
    if type(inp) != tuple:
        command = inp
    else:
      if len(inp) == 2:
        command, log = inp
      elif len(inp) == 3:
        command, log, queue = inp
      elif len(inp) == 4:
        command, log, smp, queue = inp
      else:
        command, log, smp, queue, name = inp
    if queue == False:
        queue = "all.q"
    # Queues aren't used right now.
    # Make an input script
    fname = 'qsub%s.sh'%random.randint(0,5000)
    f = open(fname,'w')
    print >>f, command
    f.close()

    # Setup path
    v = "-v PATH=/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/etc:\
/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/bin:\
/home/schuerjp/Programs/best:\
/home/schuerjp/Programs/RAPD/bin:\
/home/schuerjp/Programs/RAPD/share/phenix-1.10.1-2155/build/bin:\
/home/schuerjp/Programs/raddose-20-05-09-distribute-noexec/bin:\
/usr/local/bin:/bin:/usr/bin"
    
    qs = 'qsub -d %s -j oe '%os.getcwd()
    if log:
      qs += '-o %s '%os.path.join(os.getcwd(),log)
    qs += "%s -l nodes=1:ppn=%s %s" % (v, smp, fname)
    job = subprocess.Popen(qs,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    # Return job_id.
    #if isinstance(output, dict):
    if output != False:
      for line in job.stdout:
        l.append(line)
      output.put(l[0])
   
    print "Job finished"

def process_cluster_OLD(inp):
    """
    Launch job on SERCAT's scyld cluster. Does not wait for jobs to end!
    """
    import utils.xutils as Utils
    import time
    running = True
    command = inp.get('command')
    log = inp.get('log', False)
    queue = inp.get('queue', False)
    smp = inp.get('smp',1)
    d = inp.get('dir', os.getcwd())
    name = inp.get('name', False)
    # Sends job/process ID back
    pid = inp.get('pid', False)
    l = []

    # Check if self.running is setup... used for Best and Mosflm strategies
    # because you can't kill child processes launched on cluster easily.
    """
    try:
        __ = self.running
    except AttributeError:
        running = False
    """
    # Make an input script if not input
    if command[-3] == '.sh':
      fname = command
    else:  
      fname = 'qsub%s.sh'%random.randint(0,5000)
      f = open(fname,'w')
      print >>f, command
      f.close()
    
    # Setup path
    v = "-v PATH=/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/etc:\
/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/bin:\
/home/schuerjp/Programs/best:\
/home/schuerjp/Programs/RAPD/bin:\
/home/schuerjp/Programs/RAPD/share/phenix-1.10.1-2155/build/bin:\
/home/schuerjp/Programs/raddose-20-05-09-distribute-noexec/bin:\
/usr/local/bin:/bin:/usr/bin"
    
    # Setup the qsub command
    qs = 'qsub -d %s -j oe '%d
    if log:
      if log.count('/'):
        qs += '-o %s '%log
      else:
        qs += '-o %s '%os.path.join(d,log)
    qs += "%s -l nodes=1:ppn=%s %s" % (v, smp, fname)
    
    #Launch the job on the cluster
    job = subprocess.Popen(qs,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    # Return job_id.
    #if isinstance(output, dict):
    for line in job.stdout:
      if len(line)!= 0:
        l.append(line)
    if pid != False:
      # For my pipelines
      if name == False:
        pid.put(l[0])
      else:
        # For Frank's main launcher
        pid.put(job.pid)
    # Wait for job to complete
    time.sleep(1)
    while check_qsub_job(l[0]):
      time.sleep(0.2)
    print "Job finished"

def process_cluster(command,
                   work_dir=False,
                   logfile=False,
                   batch_queue='rapd',
                   nproc=1,
                   logger=False,
                   name=False,
                   mp_event=False,
                   timeout=False,
                   pid_queue=False,
                   tag=False,
                   result_queue=False):
    """
    Submit job to cluster using DRMAA (when you are already on the cluster).
    Main script should not end with os._exit() otherwise running jobs could be orphanned.
    To eliminate this issue, setup self.running = multiprocessing.Event(), self.running.set() in main script,
    then set it to False (self.running.clear()) during postprocess to kill running jobs smoothly.
    
    command - command to run
    work_dir - working directory
    logfile - print results of command to this file
    batch_queue - specify a batch queue on the cluster (options are all.q, phase1.q, phase2.q, phase3.q, 
            index.q, general.q, high_mem.q, rosetta.q). If no queue is specified, it will run on any node.
    nproc - number of processor to reserve for the job on a single node. If # of slots 
            are not available, it will wait to launch until resources are free. 
    logger - logger event to pass status reports.
    name - Name of job as seen when running 'qstat' command.
    mp_event - Pass in the Multiprocessing.Event() that the plugin in uses to signal termination. 
               This way the job will be killed if the event() is cleared within the plugin.
    timeout - max time (in seconds) to wait for job to complete before it is killed. (default=False waits forever)
    pid_queue - pass back the jobIB through a multiprocessing.Queue()
    tag - used by RAPD to keep track of iterations of jobs. (required for result_queue, if used)
    result_queue - pass back the results in a multiprocessing.Queue() (requires tag)
    """

    """
    Launch job on SERCAT's scyld cluster. Does not wait for jobs to end!
    """
    fd = False
    # Setup path
    v = "PATH=/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/etc:\
/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/bin:\
/home/schuerjp/Programs/best:\
/home/schuerjp/Programs/RAPD/bin:\
/home/schuerjp/Programs/RAPD/share/phenix-1.10.1-2155/build/bin:\
/home/schuerjp/Programs/raddose-20-05-09-distribute-noexec/bin:\
/usr/local/bin:/bin:/usr/bin"

    if work_dir == False:
        work_dir = os.getcwd()
    if result_queue:
        if logfile == False:
            fd = tempfile.NamedTemporaryFile(dir=work_dir, delete=False)
            logfile = fd.name

    # Make an input script if not input
    if command[-3] == '.sh':
      fname = command
    else:  
      fname = 'qsub%s.sh'%random.randint(0,5000)
      with open(fname,'w') as f:
          print >>f, '#!/bin/bash'
          print >>f, '#PBS -j oe'
          print >>f, '#PBS -d %s'%work_dir
          print >>f, '#PBS -v %s'%v
          print >>f, '#PBS -q %s'%batch_queue
          if name:
              print >>f, '#PBS -N %s'%name
          if logfile:
              if logfile.count('/'):
                  print >>f, '#PBS -o %s'%logfile
              else:
                  print >>f, '#PBS -o %s'%os.path.join(work_dir,logfile)
          print >>f, '#PBS -l nodes=1:ppn=%s'%nproc
          print >>f, command+'\n'
          f.close()

    qs = ['qsub', fname]
    #Launch the job on the cluster
    proc = subprocess.Popen(qs,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

    stdout, stderr = proc.communicate()

    # Get the JobID
    job = stdout[:stdout.rfind('.')]
    
    # Send back PID if have pid_queue
    if pid_queue:
        pid_queue.put(job)
    try:
        while check_qsub_job(job):
          #time.sleep(0.2)
          time.sleep(2)
          kill_job(job)
          if mp_event:
              if mp_event.is_set() == False:
                  kill_job(job)
        print "Job finished"
    except:
        if logger:
            logger.debug('qsub_sercat.py was killed, but the launched job will continue to run')

    # Put results on a Queue, if given
    if result_queue:
        stdout = ""
        if os.path.isfile(logfile):
            with open(logfile, 'rb') as raw:
                for line in raw:
                    stdout += line
        
        result = {
            "pid": job,
            "returncode": False,
            "stdout": stdout,
            "stderr": '',
            "tag": tag
        }
        result_queue.put(result)
    
    # Delete logile if it was not asked to be saved
    if fd:
        os.unlink(logfile)

def process_cluster_beorun(inp):
    """
    Launch job on SERCAT's scyld cluster. Assumes job uses single processor.
    """
    running = True
    command = inp.get('command')
    log = inp.get('log', False)
    queue = inp.get('queue', False)
    smp = inp.get('smp',1)
    d = inp.get('dir', os.getcwd())
    name = inp.get('name', False)
    # Sends job/process ID back
    pid = inp.get('pid', False)
    l = []

    # Check if self.running is setup... used for Best and Mosflm strategies
    # because you can't kill child processes launched on cluster easily.
    """
    try:
        __ = self.running
    except AttributeError:
        running = False
    """
    qs = 'beorun -np 1 -nolocal %s'%command
    if log:
      if log.count('/'):
        qs += ' > %s '%log
      else:
        qs += ' > %s '%os.path.join(d,log)
    
    #Launch the job on the cluster
    job = subprocess.Popen(qs,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    # Return job_id.
    #if isinstance(output, dict):
    if pid != False:
      pid.put(job.pid)
    job.wait()
    print "Job finished"
    
def check_qsub_job(job):
  """
  Check to see if process and/or its children and/or children's children are still running.
  """
  print 'gh1'
  running = False
  output = subprocess.check_output(['/usr/bin/qstat'])
  for line in output.splitlines():
    if line.split()[0] == job:
      print line.split()[4]
      if line.split()[4] in ['Q', 'R']:
        running = True
  return(running)

def kill_job(job):
    print 'gh'
    output = subprocess.check_output(['/usr/bin/qdel', job])
    print 'killed job: %s'%job
    time.sleep(1)

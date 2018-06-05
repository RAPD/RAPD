"""
This file is part of RAPD

Copyright (C) 2016-2018 Cornell University
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
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

"""
Provide generic interface for cluster interactions
"""

# Standard imports
import drmaa
import os
import redis
import subprocess
import time
import tempfile
from multiprocessing import Process
from functools import wraps

def checkCluster():
    """
    Quick check run at beginning of pipelines to see if job was subitted to computer cluster node (returns True) or
    run locally (returns False). The pipelines will use this to know whether to subprocess.Process subjobs or submit to
    compute cluster queueing system. This is the master switch for turning on or off a compute cluster.
    """
    import socket
    #Can create a list of names of your compute nodes for checking. Ours all start with 'compute-'.
    if socket.gethostname().startswith('compute-'):
        return True
    else:
        return False

def checkClusterConn(self):
  """
  Check if execution node can talk to head node through port 536. Used for testing to see if
  subjobs can submit jobs on compute cluster. All nodes should have ability to execute jobs.
  """
  if self.verbose:
    self.logger.debug('Utilities::checkClusterConn')
  try:
    command = 'qping -info gadolinium 536 qmaster 1'
    job = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    for line in job.stdout:
      self.logger.debug(line)

  except:
    self.logger.exception('**ERROR in Utils.checkClusterConn**')

def check_queue(inp):
    """
    Returns which cluster batch queue should be used with the plugin.
    """
    d = {"ECHO"           : 'general.q',
         "INDEX"          : 'index.q',
         #"INDEX"          : 'phase1.q',
         "BEAMCENTER"     : 'all.q',
         "XDS"            : 'all.q',
         #"INTEGRATE"      : 'integrate.q',
         "INTEGRATE"      : 'all.q',
         }
    
    return(d[inp])
  
def get_nproc_njobs():
    """Return the nproc and njobs for an XDS integrate job"""
    return (4, 10)
  
def determine_nproc(command):
    """Determine how many processors to reserve on the cluster for a specific job type."""
    nproc = 1
    if command in ('INDEX', 'INTEGRATE'):
        nproc = 4
    return nproc
  
def fix_command_OLD(message):
    """
    Adjust the command passed in in install-specific ways
    """
    # Adjust the working directory for the launch computer
    work_dir_candidate = os.path.join(
        message["directories"]["launch_dir"],
        message["directories"]["work"])

    # Make sure this is an original directory
    if os.path.exists(work_dir_candidate):
        # Already exists
        for i in range(1, 1000):
            if not os.path.exists("_".join((work_dir_candidate, str(i)))):
                work_dir_candidate = "_".join((work_dir_candidate, str(i)))
                break
            else:
                i += 1
    # Now make the directory
    if os.path.exists(work_dir_candidate) == False:
        os.makedirs(work_dir_candidate)

    # Modify command
    message["directories"]["work"] = work_dir_candidate

    return message


def connectCluster(inp, job=True):
  """
  Used by rapd_agent_beamcenter.py or when a user wants to launch jobs from beamline computer,
  which is not a compute node on cluster, this will login to head node and launch job without
  having them have the login info. Can setup with password or ssh host keys.
  """
  import paramiko
  bc = False
  st = ''
  if job:
    command = 'qsub -j y -terse -cwd -b y '
    command += inp
    print command
    print 'Job ID:'
  else:
    command = inp
  #Use this to say job is beam center calculation.
  if inp.startswith('-pe'):
    bc = True
    #Remove previous beam center results from directory before launching new one.
    st = 'rm -rf bc.log phi*.dat\n'
  client = paramiko.SSHClient()
  client.load_system_host_keys()
  client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
  client.connect(hostname='gadolinium',username='necat')
  stdin,stdout,stderr = client.exec_command('cd %s\n%s%s'%(os.getcwd(),st,command))
  #stdin,stdout,stderr = client.exec_command('cd %s\n%s'%(os.getcwd(),command))
  for line in stdout:
    print line.strip()
    if bc:
      return(line.strip())
  client.close()

#class Cluster_Event():
#    def __init__(self):
#        pass
def mp_job(func):
    """
    wrapper to run processCluster in a multiprocessing.Process to avoid
    threading problems in DRMAA with multiple jobs sent to same session.
    """
    
    @wraps(func)
    def wrapper(**kwargs):
        #job = False
        job = Process(target=func, kwargs=kwargs)
        job.start()
        job.join()
    return wrapper

def mp_job_NEW(func):
    """
    wrapper to run processCluster in a multiprocessing.Process to avoid
    threading problems in DRMAA with multiple jobs sent to same session.
    """
    # If command starts with rapd.launch then mp.Process it.
    @wraps(func)
    def wrapper(**kwargs):
        job = False
        if kwargs['command'].count('rapd.launch '):
            job = Process(target=func, kwargs=kwargs)
            job.start()
        # wait for the job to finish and join
        if job:
            job.join()
        else:
            return func(**kwargs)
    return wrapper

def process_cluster_fix_OLD(func):
    """
    wrapper to run processCluster in a multiprocessing.Process to avoid
    threading problems in DRMAA with multiple jobs sent to same session.
    """
    # If command starts with any in list, then mp.Process it.
    l = ['labelit.index', 'best -f', 'mosflm_strat']
    @wraps(func)
    def wrapper(**kwargs):
        job = False
        for s in l:
            if kwargs['command'].count(s):
                job = Process(target=func, kwargs=kwargs)
                job.start()
                break
        # wait for the job to finish and join
        if job:
            job.join()
        else:
            return func(**kwargs)
    return wrapper

@mp_job_NEW
def process_cluster(command,
                   work_dir=False,
                   logfile=False,
                   batch_queue='all.q',
                   nproc=1,
                   logger=False,
                   name=False,
                   mp_event=False,
                   timeout=False,
                   pid_queue=False,
                   tag=False,
                   result_queue=False):
    """
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
    def kill_job(session, job, logger=False):
        """kill the job on the cluster."""
        session.control(job, drmaa.JobControlAction.TERMINATE)
        if logger:
            logger.debug('job:%s terminated on cluster'%job)

    s = False
    jt = False
    fd = False
    if work_dir == False:
        work_dir = os.getcwd()
    if result_queue:
        if logfile == False:
            fd = tempfile.NamedTemporaryFile(dir=work_dir, delete=False)
            logfile = fd.name
    if not batch_queue:
         batch_queue ='all.q'
    
    counter = 0

    #'-clear' can be added to the options to eliminate the general.q
    options = '-clear -shell y -p -100 -q %s -pe smp %s'%(batch_queue, nproc)
    s = drmaa.Session()
    s.initialize()
    jt = s.createJobTemplate()
    jt.workingDirectory=work_dir
    jt.joinFiles=True
    jt.nativeSpecification=options
    # Path to the executable command
    jt.remoteCommand=command.split()[0]
    # Rest of command
    if len(command.split()) > 1:
        jt.args=command.split()[1:]
    if logfile:
        #the ':' is required!
        jt.outputPath=':%s'%logfile
    if name:
        jt.jobName=name
    #submit the job to the cluster and get the job_id returned
    job = s.runJob(jt)
    
    #return job_id.
    if pid_queue:
        pid_queue.put(job)

    #cleanup the input script from the RAM.
    s.deleteJobTemplate(jt)

    #If multiprocessing.event is set, then run loop to watch until job or script has finished.
    #Returns True if job is still running or False if it is dead. Uses CPU to run loop!!!
    decodestatus = {drmaa.JobState.UNDETERMINED: True,
                    drmaa.JobState.QUEUED_ACTIVE: True,
                    drmaa.JobState.SYSTEM_ON_HOLD: True,
                    drmaa.JobState.USER_ON_HOLD: True,
                    drmaa.JobState.USER_SYSTEM_ON_HOLD: True,
                    drmaa.JobState.RUNNING: True,
                    drmaa.JobState.SYSTEM_SUSPENDED: False,
                    drmaa.JobState.USER_SUSPENDED: False,
                    drmaa.JobState.DONE: False,
                    drmaa.JobState.FAILED: False,
                    }
    try:
        #Loop to keep hold process while job is running or ends when self.running event ends.
        while decodestatus[s.jobStatus(job)]:
            if mp_event:
                if mp_event.is_set() == False:
                    kill_job(s, job, logger)
                    break
            if timeout:
                if counter > timeout:
                    kill_job(s, job, logger)
                    break
            time.sleep(1)
            counter += 1
    except:
        if logger:
            logger.debug('qsub.py was killed, but the launched job will continue to run')
    
    # Used for passing back results to queue
    if result_queue:
        # stdout and stderr are joined
        stdout = ""
        if os.path.isfile(logfile):
            with open(logfile, 'rb') as raw:
                for line in raw:
                    stdout += line
            # Delete logile if it was not asked to be saved
            if fd:
                os.unlink(logfile)
        # Setup the result dict to pass back
        result = {'pid': job,
                  #"returncode": proc.returncode,
                  "stdout": stdout,
                  "stderr": '',
                  "tag": tag}
        result_queue.put(result)

    #Exit cleanly, otherwise master node gets event client timeout errors after 600s.
    if s:
        s.exit()

def kill_job(inp, logger=False):
  """
  Kill jobs on cluster. The JobID is sent in and job is killed. Must be launched from
  a compute node on the cluster. Used in pipelines to kill jobs when timed out or if
  a solution in Phaser is found in the first round and the second round jobs are not needed.
  """
  if logger:
      logger.debug('Utilities::killChildrenCluster')
  try:
      command = 'qdel %s'%inp
      if logger:
          logger.debug(command)
      os.system(command)
  except:
      if logger:
          logger.exception('**Could not kill the jobs on the cluster**')

def stillRunningCluster(self,jobid):
  """
  Check to see if process and/or its children and/or children's children are still running. Must
  be launched from compute node. 
  OBSOLETE if using DRMAA for job submission
  """
  try:
    running = False
    if self.cluster_use:
      command = 'qstat'
    else:
      command = 'rapd2.python /gpfs5/users/necat/rapd/gadolinium/trunk/qstat.py'
    output = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    for line in output.stdout:
      if len(line.split()) > 0:
        if line.split()[0] == jobid:
          running = True
    return(running)
  except:
    self.logger.exception('**ERROR in Utils.stillRunningCluster**')

def rocksCommand(self,inp):
  """
  Run Rocks command on all cluster nodes. Mainly used by rapd_agent_beamcenter.py to copy
  specific images to /dev/shm on each node for processing in RAM.
  """
  if self.verbose:
    self.logger.debug('Utilities::rocksCommand')
  try:
    command = '/opt/rocks/bin/rocks run host compute "%s"'%inp
    processLocal("ssh necat@gadolinium '%s'"%command,self.logger)

  except:
      self.logger.exception('**ERROR in Utils.rocksCommand**')

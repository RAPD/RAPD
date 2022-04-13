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
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Development"

"""
Provides generic interface for cluster interactions
"""

# Standard imports
import os
import stat
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
    Returns which cluster batch queue should be used with the plugin.

    d = {"ECHO"           : 'general.q',
         #"INDEX"          : 'phase3.q',
         "INDEX"          : 'phase1.q',
         "BEAMCENTER"     : 'all.q',
         "XDS"            : 'all.q',
         "INTEGRATE"      : 'phase2.q'
         }
    return(d[inp])
    """
    return 'rapd'

def get_nproc_njobs():
    """Return the nproc and njobs for an XDS integrate job"""
    return (4, 3)

def determine_nproc(command):
    """Determine how many processors to reserve on the cluster for a specific job type."""
    nproc = 1
    if command in ('INDEX', 'INTEGRATE'):
        nproc = 4
    return nproc

def fix_command(message):
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
    if os.path.isdir(work_dir_candidate) == False:
        os.makedirs(work_dir_candidate)

    # Modify command
    message["directories"]["work"] = work_dir_candidate

    # Filesystem is NOT shared
    # For header_1 & header_2
    for header_iter in ("1", "2"):
        header_key = "header%s" % header_iter
        if header_key in message:
            # Values that need changed
            for value_key in ("fullname", "directory"):
                # Store originals
                message[header_key][value_key+"_orig"] = message[header_key][value_key]

                # Change
                for prepended_string in ("/raw", "/archive"):
                    if message[header_key][value_key].startswith(prepended_string):
                        message[header_key][value_key] = message[header_key][value_key].replace(prepended_string, "/panfs/panfs0.localdomain"+prepended_string)

    return message

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
    v = "-v PATH=/home/schuerjp/Programs/ghostscript/bin:\
/home/schuerjp/Programs/magick/bin:\
/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/etc:\
/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/bin:\
/home/schuerjp/Programs/best:\
/home/schuerjp/Programs/RAPD/bin:\
/home/schuerjp/Programs/RAPD/share/phenix-1.10.1-2155/build/bin:\
/home/schuerjp/Programs/raddose-20-05-09-distribute-noexec/bin:\
/usr/local/XDS-INTEL64_Linux_x86_64:\
/usr/local/bin:/bin:/usr/bin, CCP4=/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0"
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

    print("Job finished")

def mp_job(func):
    """
    wrapper to run process_cluster in a multiprocessing.Process.
    """
    @wraps(func)
    def wrapper(**kwargs):
        #job = False
        job = Process(target=func, kwargs=kwargs)
        job.start()
        job.join()
    return wrapper

#@mp_job
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
    counter = 0
    # Setup path NOT USED
    v = "PATH=/home/schuerjp/Programs/ghostscript/bin:\
/home/schuerjp/Programs/magick/bin:\
/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/etc:\
/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/bin:\
/home/schuerjp/Programs/best:\
/home/schuerjp/Programs/RAPD/bin:\
/home/schuerjp/Programs/RAPD/share/phenix-1.10.1-2155/build/bin:\
/home/schuerjp/Programs/raddose-20-05-09-distribute-noexec/bin:\
/usr/local/XDS-INTEL64_Linux_x86_64:\
/usr/local/bin:/bin:/usr/bin"

    if work_dir == False:
        work_dir = os.getcwd()
    os.chdir(work_dir)
    if result_queue:
        if logfile == False:
            fd = tempfile.NamedTemporaryFile(dir=work_dir, delete=False)
            logfile = fd.name

    # Make an input script if not input
    if command[-3] == '.sh':
      fname = command
    else:
      #fname = 'qsub%s.sh'%random.randint(0,5000)
      fname = os.path.join(os.getcwd(),'qsub%s.sh'%random.randint(0,5000))
      #print fname
      with open(fname,'w') as f:
          print('#!/bin/bash', file=f)
          print('#PBS -S /bin/bash', file=f)
          print('#PBS -j oe', file=f)
          print('#PBS -d %s'%work_dir, file=f)
          print('#PBS -v %s'%v, file=f)
          #print >>f, '#PBS -V'
          # print >>f, '#PBS -v PBS_O_SHELL=/bin/bash'
          print('#PBS -q %s'%batch_queue, file=f)
          if name:
              print('#PBS -N %s'%name, file=f)
          if logfile:
              if logfile.count('/'):
                  print('#PBS -o %s'%logfile, file=f)
              else:
                  print('#PBS -o %s'%os.path.join(work_dir,logfile), file=f)
          print('#PBS -l nodes=1:ppn=%s'%nproc, file=f)
          print('/bin/bash\n', file=f)
          print(command+'\n\n', file=f)
          f.close()

    os.chmod(fname, stat.S_IRWXU)
    qs = ['qsub', fname]
    #qs = 'qsub %s'%fname
    #Launch the job on the cluster
    path = os.environ.copy()
    proc = subprocess.Popen(qs, env=path,
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
          if mp_event:
              if mp_event.is_set() == False:
                  kill_job(job)
                  break
          if timeout:
              if counter > timeout:
                  kill_job(job)
                  break
          time.sleep(1)
          counter += 1
        print("Job finished")
    except:
        if logger:
            logger.debug('qsub.py was killed, but the launched job will continue to run')

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

    # Delete the .sh file if generated
    #os.unlink(fname)

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
    print("Job finished")

def check_qsub_job(job):
  """
  Check to see if process and/or its children and/or children's children are still running.
  """
  running = False
  output = subprocess.check_output(['/usr/bin/qstat'])
  for line in output.splitlines():
    if line.split()[0] == job:
      if line.split()[4] in ['Q', 'R']:
        running = True
  return(running)

def kill_job(job):
    output = subprocess.check_output(['/usr/bin/qdel', job])
    print('killed job: %s'%job)
    time.sleep(1)

"""
Provides a simple launcher adapter that will launch processes via qsub
"""

__license__ = """
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

__created__ = "2016-03-08"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import logging
import json
import os
from subprocess import Popen
import drmaa
import time

# RAPD imports
import utils.launch_tools as launch_tools
from multiprocessing import Queue, Process

class LauncherAdapter(object):
    """
    An adapter for launcher process.

    Will launch requested job via qsub on current machine.

    NB - this adapter is highly specific to SERCAT install.
    """

    def __init__(self, site, message, settings):
        """
        Initialize the adapter

        Keyword arguments
        site -- imported site definition module
        message -- command from the control process
        settings --
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.debug("__init__")

        self.site = site
        self.message = message
        self.settings = settings

        # Decode message
        #self.decoded_message = json.loads(self.message)

        self.run()

    def run(self):
        """
        Orchestrate the adapter's actions
        """

        # Adjust the message to this site
        self.fix_command()
        
        # Get the new working directory
        work_dir = self.message["directories"]["work"]
        #self.logger.debug("work_dir: %s"%work_dir)
        
        # Get the launcher directory - in launcher specification
        # Add command_files to keep files isolated
        qsub_dir = self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"][self.site.LAUNCHER_ID]["launch_dir"]+"/command_files"

        # Put the message into a rapd-readable file
        #command_file = launch_tools.write_command_file(qsub_dir, self.message["command"], json.dumps(self.decoded_message))
        command_file = launch_tools.write_command_file(qsub_dir, self.message["command"], self.message)
        
        # The command has to come in the form of a script on the SERCAT install
        site_tag = self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"][self.site.LAUNCHER_ID]["site_tag"]
        command_line = "rapd.launch -vs %s %s" % (site_tag, command_file)
        #command_line = "tcsh\nrapd.launch -vs %s %s" % (site_tag, command_file)
        #command_script = launch_tools.write_command_script(command_file.replace(".rapd", ".sh"), command_line)
        #self.logger.debug("command: %s"%command_line)
        """
        # Set the path for qsub
        qsub_path = "PATH=/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/etc:\
/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/bin:\
/home/schuerjp/Programs/best:\
/home/schuerjp/Programs/RAPD/bin:\
/home/schuerjp/Programs/RAPD/share/phenix-1.10.1-2155/build/bin:\
/home/schuerjp/Programs/raddose-20-05-09-distribute-noexec/bin:\
/usr/local/bin:/bin:/usr/bin"
        """
        # Parse a label for qsub job from the command_file name
        qsub_label = os.path.basename(command_file).replace(".rapd", "")
        
        # Determine the number of precessors to reserve for job
        nproc = self.determine_nproc()
        
        # Determine which cluster queue to run
        queue = self.determine_queue()
        
        q = Queue()
        job = Process(target=processCluster, kwargs={'command':command_line,
                                                   'work_dir':work_dir,
                                                   'logfile':False,
                                                   'queue':queue,
                                                   'nproc':nproc,
                                                   'logger':self.logger,
                                                   'name':qsub_label,
                                                   'mp_event':False,
                                                   'timeout':False,
                                                   'output_jobID':q})
        job.start()
        # This will be passed back to a monitor that will watch the jobs and kill ones that run too long.
        jobID = q.get()
        print jobID

        
        """
        # Determine the processor specs to be used
        def determine_qsub_proc(command):
            #Determine the queue to use
            if command.startswith("index"):
                qsub_proc = "nodes=1:ppn=4"
            else:
                qsub_proc = "nodes=1:ppn=1"
            return qsub_proc
        qsub_proc = determine_qsub_proc(self.decoded_message["command"])

        # Call the launch process on the command file
        # qsub_command = "qsub -cwd -V -b y -N %s %s rapd.python %s %s" %
        #       (qsub_label, qsub_queue, command_file_path, command_file)
        # qsub_command = "qsub -d %s -v %s -N %s -l %s %s" % (
        #     qsub_dir, qsub_path, qsub_label, qsub_proc, command_script)
        qsub_command = "qsub -d %s -v %s -N %s -l %s %s" % (
            qsub_dir, qsub_path, qsub_label, qsub_proc, command_script)
        
        # Launch it
        self.logger.debug(qsub_command)
        p = Popen(qsub_command, shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        """

    def fix_command(self):
        """
        Adjust the command passed in in install-specific ways
        """

        # Adjust the working directory for the launch computer
        work_dir_candidate = os.path.join(
            self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"][self.site.LAUNCHER_ID]["launch_dir"],
            self.message["directories"]["work"])

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
        #self.decoded_message["directories"]["work"] = work_dir_candidate
        self.message["directories"]["work"] = work_dir_candidate

    def determine_nproc(self):
        """Determine how many processors to reserve on the cluster for a specific job type."""
        nproc = 1
        #if self.message['command'] in ('INDEX', 'INTEGRATE'):
        if self.message['command'] in ('INDEX'):
            nproc = 4
        return nproc
    
    def determine_queue(self):
        """Determine the cluster queue for the main job."""
        """
        if self.message['command'] == 'INDEX':
            return('index.q')
        if self.message['command'] == 'INTEGRATE':
            return('phase2.q')
        else:
            return('phase1.q')
        """
        return 'phase3.q'

def processCluster(command,
                   work_dir,
                   logfile=False,
                   queue='all.q',
                   nproc=1,
                   logger=False,
                   name=False,
                   mp_event=False,
                   timeout=False,
                   output_jobID=False):
    """
    Submit job to cluster using DRMAA (when you are already on the cluster).
    Main script should not end with os._exit() otherwise running jobs could be orphanned.
    To eliminate this issue, setup self.running = multiprocessing.Event(), self.running.set() in main script,
    then set it to False (self.running.clear()) during postprocess to kill running jobs smoothly.
    
    command - command to run
    work_dir - working directory
    logfile - print results of command to this file
    queue - specify a queue on the cluster (options are all.q, phase1.q, phase2.q, phase3.q, 
            index.q, general.q, high_mem.q, rosetta.q). If no queue is specified, it will run on any node.
    nproc - number of processor to reserve for the job on a single node. If # of slots 
            are not available, it will wait to launch until resources are free. 
    logger - logger event to pass status reports.
    mp_event - Pass in the Multiprocessing.Event() that the plugin in uses to signal termination. 
               This way the job will be killed if the event() is cleared within the plugin.
    timeout - max time (in seconds) to wait for job to complete before it is killed. (default=False waits forever)
    name - Name of job as seen when running 'qstat' command.
    output_jobID - pass back the jobIB through a multiprocessing.Queue()
    """
    def kill_job(session, job, logger=False):
        """kill the job on the cluster."""
        session.control(job, drmaa.JobControlAction.TERMINATE)
        if logger:
            logger.debug('job:%s terminated on cluster'%job)
    
    #try:
    s = False
    jt = False
    counter = 0
    #'-clear' can be added to the options to eliminate the general.q
    options = '-clear -shell y -p -100 -q %s -pe smp %s'%(queue, nproc)
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
    if output_jobID:
        output_jobID.put(job)
    #cleanup the input script from the RAM.
    s.deleteJobTemplate(jt)

    #If multiprocessing.event is set, then run loop to watch until job or script has finished.
    #if mp_event:
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
        #time.sleep(0.2)
        time.sleep(1)
        counter += 1
    #Exit cleanly, otherwise master node gets event client timeout errors after 600s.
    s.exit()
    """
    except:
        
        if logger:
            logger.exception('**ERROR in Utils.processCluster**')
        #Cleanup if error.
        if s:
            if jt:
                s.deleteJobTemplate(jt)
            s.exit()
    """
if __name__ == "__main__":
    import multiprocessing
    import threading
    event = multiprocessing.Event()
    event.set()
    #threading.Thread(target=run_job).start()
    processCluster(command='touch junk',
                   #work_dir='/gpfs6/users/necat/Jon/RAPD_test/Output',
                   work_dir='/gpfs5/users/necat/rapd/rapd2_t/single/2017-08-09/B_14:612',
                   logfile='/gpfs6/users/necat/Jon/RAPD_test/Output/temp.log',
                   queue='index.q',
                   nproc=2,
                   name='TEST',
                   mp_event=event,
                   timeout=False,)
    time.sleep(2)
    print 'event cleared'
    event.clear()
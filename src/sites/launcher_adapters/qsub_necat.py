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
        message -- command from the control process, encoded as JSON
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
        
        """

        # Get the launcher directory - in launcher specification
        # Add command_files to keep files isolated
        qsub_dir = self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"][self.site.LAUNCHER_ID]["launch_dir"]+"/command_files"

        # Put the message into a rapd-readable file
        command_file = launch_tools.write_command_file(qsub_dir, self.decoded_message["command"], json.dumps(self.decoded_message))

        # The command has to come in the form of a script on the SERCAT install
        site_tag = self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"][self.site.LAUNCHER_ID]["site_tag"]
        command_line = "rapd.launch -vs %s %s" % (site_tag, command_file)
        command_script = launch_tools.write_command_script(command_file.replace(".rapd", ".sh"), command_line)

        # Set the path for qsub
        qsub_path = "PATH=/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/etc:\
/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/bin:\
/home/schuerjp/Programs/best:\
/home/schuerjp/Programs/RAPD/bin:\
/home/schuerjp/Programs/RAPD/share/phenix-1.10.1-2155/build/bin:\
/home/schuerjp/Programs/raddose-20-05-09-distribute-noexec/bin:\
/usr/local/bin:/bin:/usr/bin"

        # Parse a label for qsub job from the command_file name
        qsub_label = os.path.basename(command_file).replace(".rapd", "")

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
    def processCluster(self,inp,output=False):
      """
      Submit job to cluster using DRMAA (when you are already on the cluster).
      Main script should not end with os._exit() otherwise running jobs could be orphanned.
      To eliminate this issue, setup self.running = multiprocessing.Event(), self.running.set() in main script,
      then set it to False (self.running.clear()) during postprocess to kill running jobs smoothly.
      """
    
      #if self.verbose:
        #self.logger.debug('Utilities::processCluster')
    
      import drmaa,time
      try:
        s = False
        jt = False
        running = True
        log = False
        queue = False
        smp = 1
        name = False
        #Check if self.running is setup... used for Best and Mosflm strategies
        #because you can't kill child processes launched on cluster easily.
        try:
          temp = self.running
        except AttributeError:
          running = False
    
        if len(inp) == 1:
          command = inp
        elif len(inp) == 2:
          command,log = inp
        elif len(inp) == 3:
          command,log,queue = inp
        elif len(inp) == 4:
          command,log,smp,queue = inp
        else:
          command,log,smp,queue,name = inp
        if queue == False:
          queue = 'all.q'
        #smp,queue,name = inp2
        #'-clear' can be added to the options to eliminate the general.q
        options = '-clear -shell y -p -100 -q %s -pe smp %s'%(queue,smp)
        s = drmaa.Session()
        s.initialize()
        jt = s.createJobTemplate()
        jt.workingDirectory=os.getcwd()
        jt.joinFiles=True
        jt.nativeSpecification=options
        jt.remoteCommand=command.split()[0]
        if len(command.split()) > 1:
          jt.args=command.split()[1:]
        if log:
          #the ':' is required!
          jt.outputPath=':%s'%log
        #submit the job to the cluster and get the job_id returned
        job = s.runJob(jt)
        #return job_id.
        if output:
          output.put(job)
    
        #cleanup the input script from the RAM.
        s.deleteJobTemplate(jt)
    
        #If multiprocessing.event is set, then run loop to watch until job or script has finished.
        if running:
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
            if self.running.is_set() == False:
              s.control(job,drmaa.JobControlAction.TERMINATE)
              self.logger.debug('job:%s terminated since script is done'%job)
              break
            #time.sleep(0.2)
            time.sleep(1)
        #Otherwise just wait for it to complete.
        else:
          s.wait(job, drmaa.Session.TIMEOUT_WAIT_FOREVER)
        #Exit cleanly, otherwise master node gets event client timeout errors after 600s.
        s.exit()
    
      except:
        self.logger.exception('**ERROR in Utils.processCluster**')
        #Cleanup if error.
        if s:
          if jt:
            s.deleteJobTemplate(jt)
          s.exit()
    
      finally:
        if name!= False:
          self.red.lpush(name,1)

    def fix_command(self):
        """
        Adjust the command passed in in install-specific ways
        """

        # Adjust the working directory for the launch computer
        work_dir_candidate = os.path.join(
            self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"][self.site.LAUNCHER_ID]["launch_dir"],
            #self.decoded_message["directories"]["work"])
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

        # Modify command
        #self.decoded_message["directories"]["work"] = work_dir_candidate
        self.message["directories"]["work"] = work_dir_candidate
        """
        # Filesystem is NOT shared
        # For header_1 & header_2
        for header_iter in ("1", "2"):
            header_key = "header%s" % header_iter
            if header_key in self.decoded_message:
                # Values that need changed
                for value_key in ("fullname", "directory"):
                    # Store originals
                    self.decoded_message[header_key][value_key+"_orig"] = self.decoded_message[header_key][value_key]

                    # Change
                    for prepended_string in ("/raw", "/archive"):
                        if self.decoded_message[header_key][value_key].startswith(prepended_string):
                            self.decoded_message[header_key][value_key] = self.decoded_message[header_key][value_key].replace(prepended_string, "/panfs/panfs0.localdomain"+prepended_string)
        """
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
#from multiprocessing import Queue, Process
from multiprocessing import Process
from multiprocessing import Queue as mp_Queue
from threading import Thread


# RAPD imports
import utils.launch_tools as launch_tools
import sites.cluster.necat as cluster

class LauncherAdapter(Thread):
    """
    An adapter for launcher process.

    Will launch requested job via qsub on current machine.

    NB - this adapter is highly specific to NECAT install.
    """

    def __init__(self, site, message, settings):
        """
        Initialize the adapter

        Keyword arguments
        site -- imported site definition module
        message -- command from the control process
        settings --
        """
        Thread.__init__(self)

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.debug("__init__")

        self.site = site
        self.message = message
        self.settings = settings

        self.run()

    def run(self):
        """
        Orchestrate the adapter's actions
        """

        # Adjust the message to this site
        self.fix_command()

        # Get the new working directory
        work_dir = self.message["directories"]["work"]

        # Get the launcher directory - Add command_files to keep files isolated
        qsub_dir = self.message["directories"]["launch_dir"]+"/command_files"

        # Put the message into a rapd-readable file
        #command_file = launch_tools.write_command_file(qsub_dir, self.message["command"], json.dumps(self.decoded_message))
        command_file = launch_tools.write_command_file(qsub_dir, self.message["command"], self.message)

        # Set the site tag from input
        site_tag = launch_tools.get_site_tag(self.message)

        # The command to launch the job
        command_line = "rapd.launch -vs %s %s" % (site_tag, command_file)
        #self.logger.debug("command: %s"%command_line)

        # Parse a label for qsub job from the command_file name
        qsub_label = os.path.basename(command_file).replace(".rapd", "")

        # Determine the number of precessors to request for job
        nproc = self.determine_nproc()

        # Determine which cluster queue to run
        #queue = self.determine_queue()
        queue = cluster.check_queue(self.message['command'])

        # Setup a Queue to retreive the jobID.
        q = mp_Queue()

        # Setup the job and launch it.
        job = Process(target=cluster.process_cluster,
                      kwargs={'command':command_line,
                              'work_dir':work_dir,
                              'logfile':False,
                              'batch_queue':queue,
                              'nproc':nproc,
                              'logger':self.logger,
                              'name':qsub_label,
                              'mp_event':False,
                              'timeout':False,
                              'pid_queue':q,
                              })
        job.start()
        # This will be passed back to a monitor that will watch the jobs and kill ones that run too long.
        jobID = q.get()
        print jobID
        
        # This joins the jobs so no defunct pythons left.
        job.join()
        
        #while job.is_alive():
        #    time.sleep(1)

    def fix_command(self):
        """
        Adjust the command passed in in install-specific ways
        """
        # Adjust the working directory for the launch computer
        work_dir_candidate = os.path.join(
            self.message["directories"]["launch_dir"],
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
        #if self.message['command'] in ('INDEX'):
        if self.message['command'] in ('INDEX', 'INTEGRATE'):
            nproc = 4
        return nproc

if __name__ == "__main__":
    #import multiprocessing
    #import threading
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
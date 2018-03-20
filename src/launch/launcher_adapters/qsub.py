"""
Provides a simple launcher adapter that will launch processes via qsub
"""

__license__ = """
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

__created__ = "2016-03-08"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import logging
import os
from subprocess import Popen
import drmaa
import time
#from multiprocessing import Queue, Process
from multiprocessing import Process
from multiprocessing import Queue as mp_Queue
from Queue import Queue as t_Queue
from threading import Thread

# RAPD imports
import utils.launch_tools as launch_tools
from utils.modules import load_module
from utils.text import json
from bson.objectid import ObjectId

#class LauncherAdapter(Thread):
class LauncherAdapter(object):
    """
    An adapter for launcher process.

    Will launch requested job via qsub on current machine.
    """

    def __init__(self, site, message, settings):
        """
        Initialize the adapter

        Keyword arguments
        site -- imported site definition module
        message -- command from the control process
        settings --
        """
        #Thread.__init__(self)

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
        if self.message['command'] == 'ECHO':
            echo = load_module(seek_module='launch.launcher_adapters.echo_simple')
            # send message to simple_echo
            echo.LauncherAdapter(self.site, self.message, self.settings)
        else:
            # Load the cluster adapter for the site.
            cluster = load_module(seek_module=self.site.CLUSTER_ADAPTER)
    
            # Adjust the message to this site
            # Get the new working directory. Message only has second part of the path.
            #self.message = cluster.fix_command(self.message)
            self.message = launch_tools.fix_command(self.message)
    
            # Get the new working directory
            work_dir = self.message["directories"]["work"]
    
            # Get the launcher directory - Add command_files to keep files isolated
            qsub_dir = self.message["directories"]["launch_dir"]+"/command_files"
    
            # Put the message into a rapd-readable file
            command_file = launch_tools.write_command_file(qsub_dir, self.message["command"], self.message)
    
            # Set the site tag from input
            site_tag = launch_tools.get_site_tag(self.message).split('_')[0]
    
            # The command to launch the job
            command_line = "rapd.launch -vs %s %s" % (site_tag, command_file)
    
            # Parse a label for qsub job from the command_file name
            qsub_label = os.path.basename(command_file).replace(".rapd", "")
    
            # Determine the number of precessors to request for job
            nproc = cluster.determine_nproc(self.message['command'])
    
            # Determine which cluster queue to run
            queue = cluster.check_queue(self.message['command'])
            
            Thread(target=cluster.process_cluster,
                          kwargs={'command':command_line,
                                  'work_dir':work_dir,
                                  'logfile':False,
                                  'batch_queue':queue,
                                  'nproc':nproc,
                                  'logger':self.logger,
                                  'name':qsub_label,
                                  'mp_event':False,
                                  'timeout':False,
                                  'pid_queue':False,
                                  }).start()
            
            """
            # Setup a Queue to retreive the jobID.
            q = mp_Queue()
            #q = t_Queue()
    
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
            
            cluster.process_cluster(command=command_line,
                                    work_dir=work_dir,
                                    logfile=False,
                                    batch_queue=queue,
                                    nproc=nproc,
                                    logger=self.logger,
                                    name=qsub_label,
                                    mp_event=False,
                                    timeout=False,
                                    pid_queue=False,
                                    )
            """
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

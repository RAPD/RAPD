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
#import logging
import os
#from subprocess import Popen
#import drmaa
#import time
#from multiprocessing import Process
#from multiprocessing import Queue as mp_Queue
#from Queue import Queue as t_Queue
from threading import Thread
import json

# RAPD imports
#import utils.launch_tools as launch_tools
from utils.modules import load_module
#from utils.text import json
#from bson.objectid import ObjectId

command_file = '/gpfs6/users/necat/rapd2/command_files/INTEGRATE__ncmuo.rapd'
message = json.loads(open(command_file, 'r').read())

cluster = load_module(seek_module="sites.cluster.necat")

# Get the new working directory
work_dir = message["directories"]["work"]

# Set the site tag from input
site_tag = 'NECAT'

# The command to launch the job
command_line = "rapd.launch -vs %s %s" % (site_tag, command_file)

# Parse a label for qsub job from the command_file name
qsub_label = os.path.basename(command_file).replace(".rapd", "")

nproc = 1
queue ='phase1.q,general.q'

Thread(target=cluster.process_cluster,
              kwargs={'command':command_line,
                      'work_dir':work_dir,
                      'logfile':False,
                      'batch_queue':queue,
                      'nproc':nproc,
                      'logger':False,
                      'name':qsub_label,
                      'mp_event':False,
                      'timeout':False,
                      'pid_queue':False,
                      }).start()



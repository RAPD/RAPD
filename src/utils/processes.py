"""This is a docstring for this container file"""

"""
This file is part of RAPD

Copyright (C) 2017, Cornell University
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

__created__ = "2017-05-10"
__maintainer__ = "Your name"
__email__ = "Your email"
__status__ = "Development"

# Standard imports
from pprint import pprint
import sys, os, signal
import shlex
#import time
import subprocess
from subprocess import Popen, PIPE, STDOUT
from multiprocessing import Pool

def local_subprocess(command,
                     logfile=False,
                     pid_queue=False,
                     result_queue=False,
                     tag=False):
    """
    Run job as subprocess on local machine. based on xutils.processLocal

    Arguments
    ---------
    commands - a dict with various data for running. Recognized fields are:
        command - the command to be run in the subprocess
        logfile - name of a logfile to be generated. The logfile will be STDOUT+STDERR
        pid_queue - a multiprocessing.Queue for placing PID of subprocess in
        tag - an identifying tag to be useful to the caller
    """

    if logfile:
        out = open(logfile, "w")
        err = out
    else:
        out = subprocess.PIPE
        err = subprocess.PIPE

    proc = subprocess.Popen(shlex.split(command),
                            stdout=out,
                            stderr=err,
                            #stderr=STDOUT,
                            )

    # Send back PID if have pid_queue
    if pid_queue:
        pid_queue.put(proc.pid)

    if logfile:
        proc.wait()
        out.close()
    else:
        try:
            # Get the stdout and stderr from process
            stdout, stderr = proc.communicate()
        except KeyboardInterrupt:
            #sys.exit()
            os._exit()

    # Put results on a Queue, if given
    if result_queue:
        if logfile:
            stdout = open(logfile, "r").read()
            stderr = None
        result = {
            "pid": proc.pid,
            "returncode": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "tag": tag
        }
        result_queue.put(result)

    # Write out a log file, if name passed in
    # if logfile:
    #     print "In logfile %s" % logfile
    #     with open(logfile, "w") as out_file:
    #         out_file.write(stdout)
    #         out_file.write(stderr)

def mp_pool_FUTURE(nproc=8):
    """Setup and return a multiprocessing.Pool to launch jobs"""
    pool = Pool(processes=nproc)
    return pool

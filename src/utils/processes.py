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
# import argparse
# import from collections import OrderedDict
# import datetime
# import glob
# import json
# import logging
# import multiprocessing
# import os
from pprint import pprint
# import pymongo
# import re
# import redis
# import shutil
import subprocess
# import sys
# import time
# import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils


def local_subprocess(commands):
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
    pprint(commands)
    command = commands.get("command", False)
    logfile = commands.get("logfile", False)
    pid_queue = commands.get("pid_queue", False)
    result_queue = commands.get("result_queue", False)
    tag = commands.get("tag", False)

    # Run the process
    proc = subprocess.Popen(command,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    # Send back PID if have pid_queue
    if pid_queue:
        pid_queue.put(proc.pid)

    # Get the stdout and stderr from process
    stdout, stderr = proc.communicate()
    # print stdout
    # print stderr

    # Put results on a Queue, if given
    if result_queue:
        result = {
            "pid": proc.pid,
            "status": proc.returncode,
            "stdout": stdout,
            "stderr": stderr
        }
        result_queue.put(result)

    # Write out a log file, if name passed in
    if logfile:
        with open(logfile, "w") as out_file:
            out_file.write(stdout)
            out_file.write(stderr)

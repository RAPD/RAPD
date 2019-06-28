"""This is a docstring for this container file"""

"""
This file is part of RAPD

Copyright (C) 2017-2018, Cornell University
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
import sys
import os
import signal
import shlex
#import time
#import subprocess32 as subprocess
from subprocess import Popen, call, PIPE, STDOUT
from multiprocessing import Pool, Manager, cpu_count
from multiprocessing.pool import ThreadPool
from multiprocessing.managers import BaseManager
from utils.site import get_ip_address
from queue import Queue
from threading import Thread

import traceback
#from multiprocessing.pool import Pool
#import multiprocessing

# Shortcut to multiprocessing's logger
def error(msg, *args):
    return multiprocessing.get_logger().error(msg, *args)

class LogExceptions(object):
    def __init__(self, callable):
        self.__callable = callable

    def __call__(self, *args, **kwargs):
        try:
            result = self.__callable(*args, **kwargs)

        except Exception as e:
            # Here we add some debugging help. If multiprocessing's
            # debugging is on, it will arrange to log the traceback
            error(traceback.format_exc())
            # Re-raise the original exception so the Pool worker can
            # clean up
            raise

        # It was fine, give a normal answer
        return result

#class LoggingPool(Pool):
#    def apply_async(self, func, args=(), kwds={}, callback=None):
#        return Pool.apply_async(self, LogExceptions(func), args, kwds, callback)



class LocalSubprocess(Thread):

    done = False

    def __init__(self,
                 command=False,
                 logfile=False,
                 pid_queue=False,
                 result_queue=False,
                 tag=False):

        print "LocalSubprocess command: %s" % command
        print "                logfile: %s" % logfile

        self.stdout = None
        self.stderr = None

        self.command=command
        self.logfile=logfile
        self.pid_queue=pid_queue
        self.result_queue=result_queue
        self.tag=tag

        Thread.__init__(self)

    def run(self):

        print "LocalSubprocess.run"

        if not self.command:
            self.command = 'ls'
        command = self.command.split(" ")
        print os.getcwd()

        p = subprocess.Popen(command,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        self.stdout, self.stderr = p.communicate()

        print "STDOUT"
        print self.stdout
        print "STDERR"
        print self.stderr

        if self.logfile:
            print "LocalSubprocess.logfile"
            with open(self.logfile, "w") as out_file:
                out_file.write(self.stdout)
                out_file.write(self.stderr)

        done = True
        print "LocalSubprocess.done"

# myclass = MyClass()
# myclass.start()
# myclass.join()
# print myclass.stdout

class QueueManager(BaseManager):
    """Setup a multiprocessing.manager to pass results queue through Process or apply.
       This is a way to get a queue across different machines. 
       DID NOT WORK because you cannot close the manager server?!?"""
    def __init__(self,
                 ip=False,
                 port=20100,
                 authkey=None,
                 manager=False):

        self.ip = ip
        self.port = port
        self.authkey = authkey
      
        if not self.ip:
            self.ip = get_ip_address()
    
    def setup_manager(self):
        """Setup manager on host machine running job."""
        queue = Queue.Queue()
        self.register('get_queue', callable=lambda:queue)
        manager = BaseManager(address=(self.ip, self.port), authkey=self.authkey)
        #m = QueueManager(address=(get_ip_address(), 50000), authkey=self.authkey)
        #self.queue_server = manager.get_server()
        #self.queue_server.serve_forever()
        self.queue_server = manager.start()
        print dir(queue)
        
        
        #print dir(manager)
        #print dir(self.queue_server)
        #print self.queue_server.address
        
        #return queue
        
    def stop_manager(self):
        #self.queue_server.shutdown()
        self.queue_server.stop()
    
    def setup_client(self):
        """Setup remote client and return remote queue."""
        self.register('get_queue')
        manager = BaseManager(address=(self.ip, self.port), authkey=self.authkey)
        manager.connect()
        queue = manager.get_queue()
        return queue

def mp_manager():
    # This is a way to get a queue across different machines. 
    # DID NOT WORK because you cannot close the manager server?!?

    queue = Queue()
    class QueueManager(BaseManager): pass
    
    QueueManager.register('get_queue', callable=lambda:queue)
    m = QueueManager(address=(get_ip_address(), 20100), authkey=None)
    #m.start()
    s = m.get_server()
    print dir(s)
    stop_timer = threading.Timer(1, lambda:s.stop_event.set())
    QueueManager.register('stop', callable=lambda:stop_timer.start())
    s.serve_forever()
    return (m, queue)

def mp_client(inp):
   # This is a way to get a queue across different machines. 
    # DID NOT WORK because you cannot close the manger server?!?

    class QueueManager(BaseManager): pass
    QueueManager.register('get_queue')
    #QueueManager.register('stop')
    m = QueueManager(address=(inp[0],inp[1]), authkey=None)
    m.connect()
    queue = m.get_queue()
    return (m, queue)


def local_subprocess(command,
                     logfile=False,
                     pid_queue=False,
                     result_queue=False,
                     tag=False,
                     shell=False):
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
    # Need the PIPE otherwise PHENIX jobs dont finish for some reason... 
    if shell:
        # If requesting shell
        proc = Popen(command, 
                     stdout=PIPE,
                     stderr=PIPE,
                     shell=True,
                     bufsize=-1)
    elif isinstance(command, basestring):
        # If command is a string and no shell.
        proc = Popen(shlex.split(command), 
                     stdout=PIPE,
                     stderr=PIPE,
                     bufsize=-1)
    else:
        # no shell and command is a list already.
        proc = Popen(command, 
                     stdout=PIPE,
                     stderr=PIPE,
                     bufsize=-1)
    # print "  running...", command
    # Send back PID if have pid_queue
    if pid_queue:
        pid_queue.put(proc.pid)

    try:
        # Get the stdout and stderr from process
        stdout, stderr = proc.communicate()
        # print "  done..."
    except KeyboardInterrupt:
        #sys.exit()
        os._exit()

    # Put results on a Queue, if given
    if result_queue:
        result = {
            "pid": proc.pid,
            "returncode": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "tag": tag
        }
        result_queue.put(result)

    # Write out a log file, if name passed in
    if logfile:
        try:
            with open(logfile, "w") as out_file:
                out_file.write(stdout)
                out_file.write(stderr)
        # Found that jobs not getting effectively killed by multiprocess Pool at times
        except IOError:
            pass

    # print "  finished...", command

def total_nproc():
    """Returns the nproc on machine."""
    return cpu_count()

#@staticmethod
def mp_pool(nproc=8):
    """Setup and return a multiprocessing.Pool to launch jobs"""
    return Pool(processes=nproc)

def mp_manager():
    return Manager()

@staticmethod
def mp_pool_TESTING(nproc=8):
    return LoggingPool(processes=nproc)

def thread_pool(nproc=8):
    return ThreadPool(processes=nproc)

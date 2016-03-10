"""
This file is part of RAPD

Copyright (C) 2016, Cornell University
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
import time

# Non-standard imports
import drmaa

def process_cluster(self, inp, output=False):
    """
    Submit job to cluster using DRMAA (when you are already on the cluster).
    Main script should not end with os._exit() otherwise running jobs could be orphanned.
    To eliminate this issue, setup self.running = multiprocessing.Event(),
    self.running.set() in main script, then set it to False (self.running.clear())
    during postprocess to kill running jobs smoothly.
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
    v = "-v PATH=/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/etc:\
/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/bin:\
/home/schuerjp/Programs/best:\
/home/schuerjp/Programs/RAPD/bin:\
/home/schuerjp/Programs/RAPD/share/phenix-1.10.1-2155/build/bin:\
/home/schuerjp/Programs/raddose-20-05-09-distribute-noexec/bin:\
/usr/local/bin:/bin:/usr/bin"
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
    if len(command.split()) > 1:
        jt.args = command.split()[1:]
    if log:
        # The ":" is required!
        jt.outputPath = ":%s" % os.path.join(os.getcwd(), log)

    # Submit the job to the cluster and get the job_id returned
    job = s.runJob(jt)

    # Return job_id.
    if isinstance(output, dict):
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

    print "Job finished"

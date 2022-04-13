"""pdbquery RAPD plugin"""

"""
This file is part of RAPD
c
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

__created__ = "2019-02-21"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Development"

# This is an active RAPD plugin
RAPD_PLUGIN = True

# This plugin's type
DATA_TYPE = "MX"
PLUGIN_TYPE = "MR"
PLUGIN_SUBTYPE = "EXPERIMENTAL"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "c33b"
VERSION = "2.0.0"

# Standard imports
from distutils.spawn import find_executable
import glob
import logging
from multiprocessing import cpu_count
from threading import Thread
import os
from pprint import pprint
import shutil
import time
import importlib
import random

# RAPD 
from bson.objectid import ObjectId
from plugins.subcontractors.rapd_phaser import run_phaser
from plugins.subcontractors.rapd_cctbx import get_pdb_info, get_mtz_info, get_res
from plugins.get_cif.plugin import check_pdbq
from utils import archive
import utils.credits as rcredits
import utils.exceptions as exceptions
import utils.global_vars as rglobals
from utils.text import json
import utils.xutils as xutils
from utils.processes import local_subprocess, mp_pool, mp_manager
import info

# NE-CAT REST PDB server
#PDBQ_SERVER = rglobals.PDBQ_SERVER

# Software dependencies
VERSIONS = {
    "gnuplot": (
        "gnuplot 4.2",
        "gnuplot 5.0",
    )
}

class RapdPlugin(Thread):
    """
    RAPD plugin class

    Command format:
    {
       "command":"MR",
       "directories":
           {
               "work": ""                          # Where to perform the work
           },
       "input_data": {
           'data_file': file,
           'struct_file': file },
       "preferences": {}                           # Settings for calculations
    }
    """
    # Run rigid-body refinement after MR.
    #rigid = False

    # Parameters
    large_cell = False
    laue = False
    dres = 0.0

    # Holders for passed-in info
    command = None
    #preferences = {}
    
    # Holders for launched Phaser jobs
    jobs = {}

    # Holders for results
    phaser_results = {}
    # Results that are sent back
    results = {}
    
    # Initial status
    status = 1
    status_incr = 1

    redis = False
    pool = False
    batch_queue = False
    manager = False

    # Timers for processes
    phaser_timer = rglobals.PHASER_TIMEOUT

    def __init__(self, command, site=False, processed_results=False, tprint=False, logger=False, verbosity=False):
        """Initialize the plugin"""
        Thread.__init__ (self)

        # If the logging instance is passed in...
        if logger:
            self.logger = logger
        else:
            # Otherwise get the logger Instance
            self.logger = logging.getLogger("RAPDLogger")
            self.logger.debug("__init__")

        # Keep track of start time
        self.start_time = time.time()
        # Store tprint for use throughout
        if tprint:
            self.tprint = tprint
        # Dead end if no tprint passed
        else:
            def func(arg=False, level=False, verbosity=False, color=False):
                """Dummy function"""
                pass
            self.tprint = func
        
        # Used for sending results back to DB referencing a dataset
        self.processed_results = processed_results

        # Some logging
        self.logger.info(command)

        self.verbose = verbosity

        # Store passed-in variables
        self.site = site
        self.command = command
        self.preferences = self.command.get("preferences", {})

        # Params
        self.working_dir = self.command["directories"].get("work", os.getcwd())

        # Input data MTZ file
        self.data_file = xutils.convert_unicode(self.command["input_data"].get("data_file"))
        # Input PDB/mmCIF file or PDB code.
        self.struct_file = xutils.convert_unicode(self.command["input_data"].get("struct_file"))

        # Save preferences
        self.clean = self.preferences.get("clean", True)
        # Calc ADF for each solution (creates a lot of big map files).
        self.adf = self.preferences.get("adf", False)

        # Check if there is a computer cluster and load adapter.
        self.computer_cluster = xutils.load_cluster_adapter(self)

        if self.computer_cluster:
            self.launcher = self.computer_cluster.process_cluster
            self.batch_queue = self.computer_cluster.check_queue(self.command.get('command'))
        else:
            # if NOT using a computer cluster setup a multiprocessing.pool and manager for queues. 
            self.launcher = local_subprocess
            self.pool = mp_pool(self.preferences.get("nproc", cpu_count()-1))
            self.manager = mp_manager()

        # Set Python path for subcontractors.rapd_phaser
        self.rapd_python = "rapd.python"
        if self.site and hasattr(self.site, "RAPD_PYTHON_PATH"):
            self.rapd_python = self.site.RAPD_PYTHON_PATH

    def run(self):
        """Execution path of the plugin"""

        self.preprocess()
        self.process()
        self.postprocess()

    def preprocess(self):
        """Set up for plugin action"""
        
        self.logger.debug("preprocess")
        
        # Record a starting time
        self.start_time = time.time()

        # Register progress
        self.tprint(arg=0, level="progress")

        # Construct the results
        self.construct_results()
        
        # Let everyone know we are working on this
        self.send_results(self.results)

        # Get running instance of PDB server
        self.repository = check_pdbq(self.tprint, self.logger)

        # Change into working directory
        xutils.create_folder(self.working_dir)
        
        # Copy data file to working dir to minimize char length in Phaser.
        data_path = os.path.join(os.getcwd(), os.path.basename(self.data_file))
        if not os.path.exists(data_path):
            os.symlink(self.data_file, data_path)
            self.data_file = data_path

        # Glean some information on the input file
        input_spacegroup, cell, volume = get_mtz_info(self.data_file)
        # Get high resolution limt from MTZ
        self.dres = get_res(self.data_file)
        # Determine the Laue group from the MTZ
        input_spacegroup_num = xutils.convert_spacegroup(input_spacegroup)
        self.laue = xutils.get_sub_groups(input_spacegroup_num, "laue")

        # Throw some information into the terminal
        self.tprint("\nDataset information", color="blue", level=10)
        self.tprint("  Data file: %s" % self.data_file, level=10, color="white")
        self.tprint("  Spacegroup: %s  (%s)" % (input_spacegroup, input_spacegroup_num),
                    level=10,
                    color="white")
        self.tprint("  Cell: %f.2 %f.2 %f.2 %f.2 %f.2 %f.2" % tuple(cell),
                    level=10,
                    color="white")
        self.tprint("  Volume: %f.1" % volume, level=10, color="white")
        self.tprint("  Resolution: %f.1" % self.dres, level=10, color="white")
        # self.tprint("  Subgroups: %s" % self.laue, level=10, color="white")

        # Set by number of residues in AU. Ribosome (70s) is 24k.
        est_res_number = xutils.calc_res_number(input_spacegroup,
                                                     se=False,
                                                     volume=volume,
                                                     sample_type=self.preferences.get("type", "protein"),
                                                     solvent_content=self.preferences.get("solvent_content", 0.55))
        if est_res_number > 5000:
            self.large_cell = True
            self.phaser_timer = self.phaser_timer * 1.5

        # Check if mmCIF, PDB, or PDB code and get file.
        if not self.struct_file:
            self.postprocess_invalid_input_file()
        # Check if mmCIF, PDB, or PDB code and get file.
        elif self.struct_file[-4:].upper() in ('.PDB','.CIF'):
            # Copy to local directory because of character limit in Phaser.
            struc_path = os.path.join(os.getcwd(), os.path.basename(self.struct_file))
            if not os.path.exists(struc_path):
                os.symlink(self.struct_file, struc_path)
                self.struct_file = struc_path
            # Get PDB info
            self.pdb_info = get_pdb_info(self.struct_file, self.data_file, self.dres)
        # Use PDB code to download mmCIF file
        elif len(self.struct_file) == 4:
            # Download file from PDB code and get PDB info
            repository = check_pdbq(self.tprint, self.logger)
            self.struct_file = repository.download_cif(self.struct_file, os.path.join(os.getcwd(),self.struct_file.lower()+'.cif'))
            self.pdb_info = get_pdb_info(self.struct_file, self.data_file, self.dres)
        else:
            self.postprocess_invalid_input_file()

        #If user requests to search for more mols, then allow.
        if self.preferences.get('nmol', False):
            #if int(self.pdb_info['all'].get('NMol')) < int(self.nmol):
                #self.pdb_info['all']['NMol'] = self.nmol
            self.pdb_info['all']['NMol'] = self.preferences.get('nmol', False)

        # Check for dependency problems
        self.check_dependencies()

        # Connect to Redis (computer cluster sends results via Redis)
        if self.preferences.get("run_mode") == "server" or self.computer_cluster:
            self.connect_to_redis()

    def update_status(self, stat=False):
        """Update the status of the run."""
        if stat:
            self.results["process"]["status"] = int(stat)
            self.tprint(arg=int(stat), level="progress", color="orange")
        
        else:
            self.status += self.status_incr
            if self.status > 90:
                self.status = 90
            self.results["process"]["status"] = int(self.status)
            self.tprint(arg=int(self.status), level="progress", color="orange")

    def calculate_status_increment(self, njobs):
        """Calculate an int for incrementing job status."""
        self.status_incr = int(90/njobs)

    def check_dependencies(self):
        """Make sure dependencies are all available"""

        # Any of these missing, dead in the water
        #TODO reduce external dependencies
        #for executable in ("bzip2", "gunzip", "phaser", "phenix.cif_as_pdb", "tar"):
        for executable in ("gunzip", "phaser"):
            if not find_executable(executable):
                self.tprint("Executable for %s is not present, exiting" % executable,
                            level=30,
                            color="red")
                self.results["process"]["status"] = -1
                self.results["error"] = "Executable for %s is not present" % executable
                self.write_json()
                raise exceptions.MissingExecutableException(executable)

        # If no gnuplot turn off printing
        # if self.preferences.get("show_plots", True) and (not self.preferences.get("json", False)):
        #     if not find_executable("gnuplot"):
        #         self.tprint("\nExecutable for gnuplot is not present, turning off plotting",
        #                     level=30,
        #                     color="red")
        #         self.preferences["show_plots"] = False
    
    def construct_results(self):
        """Create the self.results dict"""
        
        self.results["command"] = self.command

        # Copy over details of this run
        #self.results["command"] = self.command.get("command")
        #self.results["preferences"] = self.preferences

        # Describe the process
        self.results["process"] = self.command.get("process", {})
        # Move process_id
        #self.results["process"]["process_id"] = self.command.get("process_id")
        self.results["process"]["process_id"] = self.command.pop("process_id", None)
        # Status is now 1 (starting)
        self.results["process"]["status"] = self.status
        # Process type is plugin
        self.results["process"]["type"] = "plugin"
        # Give it a result_id
        self.results["process"]["result_id"] = str(ObjectId())
        
        # Add link to processed dataset
        if self.processed_results:
            #self.results["process"]["result_id"] = self.processed_results["process"]["result_id"]
            # This links to MongoDB results._id
            self.results["process"]["parent_id"] = self.processed_results.get("process", {}).get("result_id", False)
            # This links to a session
            self.results["process"]["session_id"] = self.processed_results.get("process", {}).get("session_id", False)
            # Identify parent type
            self.results["process"]["parent"] = self.processed_results.get("plugin", {})
            # The repr
            self.results["process"]["repr"] = self.processed_results.get("process", {}).get("repr", "Unknown")

        # Describe plugin
        self.results["plugin"] = {
            "data_type": DATA_TYPE,
            "type": PLUGIN_TYPE,
            "subtype": PLUGIN_SUBTYPE,
            "id": ID,
            "version": VERSION
        }

        # Add fields to results
        self.results["results"] = {
            "mr_results": {},
            "archive_files": [],
            "data_produced": [],
            "messages": [],
            "errors": [],
            "for_display": []
        }
    
    def connect_to_redis(self):
        """Connect to the redis instance"""
        redis_database = importlib.import_module('database.redis_adapter')
        self.redis = redis_database.Database(settings=self.site.CONTROL_DATABASE_SETTINGS,
                                             logger=self.logger)

    def send_results(self):
        """Let everyone know we are working on this"""

        self.logger.debug("send_results")

        if self.preferences.get("run_mode") == "server":

            self.logger.debug("Sending back on redis")

            #pprint(self.results)
            # Transcribe results
            json_results = json.dumps(self.results)

            # Get redis instance
            if not self.redis:
                self.connect_to_redis()

            # Send results back
            self.redis.lpush("RAPD_RESULTS", json_results)
            self.redis.publish("RAPD_RESULTS", json_results)

    def process(self):
        """Run plugin action"""

        self.process_phaser()

        self.jobs_monitor()

    def process_phaser(self, full=False):
        """Start Phaser for input pdb"""

        self.logger.debug("process_phaser")

        self.tprint("\nStarting molecular replacement", level=30, color="blue")
        self.tprint("  Assembling Phaser runs", level=10, color="white")

        def launch_job(inp):
            """Launch the Phaser job"""
            #self.logger.debug("process_phaser Launching %s"%inp['name'])
            tag = 'Phaser_%d' % random.randint(0, 10000)
            if self.computer_cluster:
                # Create a unique identifier for Phaser results
                inp['tag'] = tag
                # Send Redis settings so results can be sent thru redis
                inp['db_settings'] = self.site.CONTROL_DATABASE_SETTINGS
                # Don't need result queue since results will be sent via Redis
                queue = False
            else:
                inp['pool'] = self.pool
                # Add result queue
                queue = self.manager.Queue()
                inp['result_queue'] = queue

            # Launch the job
            job, pid = run_phaser(**inp)
            self.jobs[job] = {'name': inp['name'],
                              'pid' : pid,
                              'tag' : tag,
                              'result_queue': queue,
                              'spacegroup': inp['spacegroup'] # Need for jobs that timeout.
                              }

        # Determine which SG's to run MR.
        run_sg = xutils.get_sub_groups(self.laue, "phaser")
        # Prune if only one chain present, b/c 'all' and 'A' will be the same.
        if len(self.pdb_info.keys()) == 2:
            for key in self.pdb_info.keys():
                if key != 'all':
                    del self.pdb_info[key]
        # Only launch is greater than 20% solvent content
        for chain in self.pdb_info.keys():
            if self.pdb_info[chain]['SC'] > 0.2:
                #if pdb_info[chain]["res"] != 0.0:
                # Set copy to minimum of 1
                copy = self.pdb_info[chain]["NMol"]
                if copy == 0:
                    copy = 1
                # Set recommended resolution for MR
                res = xutils.set_phaser_res(self.pdb_info[chain]["res"],
                                            self.large_cell,
                                            self.dres)
                for sg in run_sg:
                    # Convert SG number to name
                    sg = xutils.convert_spacegroup(sg, True)
                    # Setup MR job description
                    job_description = {
                        "data_file": self.data_file,
                        "struct_file": self.pdb_info[chain]["file"],
                        "spacegroup": sg,
                        "ncopy": copy,
                        "adf": self.adf,
                        #"test": self.preferences.get("test", False),
                        "resolution": res,
                        "launcher": self.launcher,
                        "tag": False,
                        "batch_queue": self.batch_queue,
                        "rapd_python": self.rapd_python}
                    
                    # Launch quick MR (default)
                    if not full:
                        # Change folder
                        name = "%s_%s_0" % (sg, chain)
                        work_dir = os.path.abspath(os.path.join(self.working_dir, name))
                        xutils.create_folder(work_dir)
                        job_description.update({"work_dir": work_dir,
                                                "name": name})
                        launch_job(job_description)
                    # Launch full MR
                    if self.computer_cluster or full:
                        name = "%s_%s_1" % (sg, chain)
                        work_dir = os.path.abspath(os.path.join(self.working_dir, name))
                        xutils.create_folder(work_dir)
                        job_description.update({"work_dir": work_dir,
                                                "full": True,
                                                "name": name})
                        launch_job(job_description)
                
            else:
                self.postprocess_phaser(chain, {"solution": False,
                                                "message": "% Solvent < 20%"})

        # Save number of jobs launched for correct status reply
        if not full:
            if self.computer_cluster:
                self.calculate_status_increment(len(self.jobs.keys()))
            else:
                self.calculate_status_increment(len(self.jobs.keys())*2)

    def postprocess_phaser(self, job_name, results):
        """fix Phaser results and pass back"""
        self.logger.debug("postprocess_phaser")

        # Copy tar to working dir
        if results.get("tar", False):
            orig = results.get("tar", {"path":False}).get("path")
            if orig:
                new = os.path.join(self.working_dir, os.path.basename(orig))
                # If old file in working dir, remove it and recopy.
                if os.path.exists(new):
                    os.unlink(new)
                shutil.copy(orig, new)
                results["tar"]["path"] = new

        # Send back results skipping whether quick or full run.
        #self.results['results']['mr_results'][job_name[:-2]].append(results)
        self.results['results']['mr_results'].update({job_name[:-2] : results})
        # Show results in log 
        #self.logger.debug(results)

        # Save results for command line
        self.phaser_results[job_name] = {"results": results}
        # Update the status number
        self.update_status()
        # Move transferring files
        self.transfer_files(results)
        # Passback new results to RAPD
        self.send_results()

    def jobs_monitor(self, full=False):
        """Monitor running jobs and finsh them when they complete."""

        self.logger.debug("jobs_monitor")

        def finish_job(job):
            """Finish the jobs and send to postprocess_phaser"""
            info = self.jobs.pop(job)
            #print 'Finished Phaser on %s with id: %s'%(info['name'], info['tag'])
            self.logger.debug('Finished Phaser on %s'%info['name'])
            if self.computer_cluster:
                results_json = self.redis.get(info['tag'])
                results = json.loads(results_json)
                self.postprocess_phaser(info['name'], results)
                self.redis.delete(info['tag'])
                """
                try:
                    # This try/except is for when results aren't in Redis in time.
                    results = json.loads(results_json)
                    self.postprocess_phaser(info['name'], results)
                    self.redis.delete(info['tag'])
                except Exception as e:
                    self.logger.error('Error '+ str(e))
                    #self.logger.error('results_json: %s'%results_json)
                    #print 'PROBLEM: %s %s'%(info['name'], info['output_id'])
                    #print results_json
                """
            else:
                results = info['result_queue'].get()
                self.postprocess_phaser(info['name'], json.loads(results.get('stdout')))
            jobs.remove(job)

        # Signal to the pool that no more processes will be added
        if self.pool and full:
            self.pool.close()

        timed_out = False
        timer = 0
        if full:
            jobs = [job for job in self.jobs.keys() if self.jobs[job]['name'][-1] == '1']
        else:
            jobs = [job for job in self.jobs.keys() if self.jobs[job]['name'][-1] == '0']

        # Run loop to see when jobs finish
        while len(jobs):
            for job in jobs:
                if self.pool:
                    if job.ready():
                        finish_job(job)
                elif job.is_alive() == False:
                    finish_job(job)
            time.sleep(1)
            timer += 1
            """
            if self.verbose:
              if round(timer%1,1) in (0.0,1.0):
                  print 'Waiting for AutoStat jobs to finish '+str(timer)+' seconds'
            """
            if self.phaser_timer:
                if timer >= self.phaser_timer:
                    timed_out = True
                    break
        if timed_out:
            if self.verbose:
                self.logger.debug('MR timed out.')
                print 'MR timed out.'
            for job in self.jobs.keys():
                if self.computer_cluster:
                    # Kill job on cluster:
                    self.computer_cluster.kill_job(self.jobs[job].get('pid'))
                else:
                    # terminate the job
                    job.terminate()
                # Get the job info
                info = self.jobs.pop(job)
                print 'Timeout Phaser on %s'%info['name']
                self.logger.debug('Timeout Phaser on %s'%info['name'])
                # Send timeout result to postprocess
                self.postprocess_phaser(info['name'], {"solution": False,
                                                       "spacegroup": info['spacegroup'],
                                                       "message": "Timed out"})
                # Delete the Redis key
                if self.redis:
                    self.redis.delete(info['output_id'])

        # Join the self.pool if used
        if self.pool and full:
            # Close the multiprocessing.manager
            self.manager.shutdown()
            self.pool.join()

        if self.verbose and self.logger:
            self.logger.debug('MR.jobs_monitor finished.')

        #Check if solution has been found.
        if not full:
          self.check_solution()

    def check_solution(self):
        """
        Check if solution is found. If not alter input and rerun.
        """

        self.logger.debug("check_solution")

        solution = False
        keys0 = [key for key in self.phaser_results.keys() if key[-1] == '0']
        keys1 = [key for key in self.phaser_results.keys() if key[-1] == '1']
        for key in keys0:
            sol = self.phaser_results[key].get('results').get('solution', False)
            if sol not in ('No solution','Timed out','NA', False, None):
                solution = True
        if solution:
            #Kill the jobs and remove the full results since not needed.
            for job in keys1:
                if self.computer_cluster:
                    # Kill job on cluster:
                    self.computer_cluster.kill_job(self.jobs[job].get('pid'))
                else:
                    # terminate the job
                    job.terminate()
                del self.phaser_results[job]
            # Close the pool to new jobs and join the thread.
            if self.pool:
                # Close the multiprocessing.manager
                self.manager.shutdown()
                self.pool.close()
                self.pool.join()
            # Update status
            self.update_status(90)
            # Send updated status
            self.send_results()
        else:
            # Remove results from quick run if no solution found.
            for k in keys0:
                del self.phaser_results[k]
            # Run the full Phaser jobs.
            if not self.computer_cluster:
                self.process_phaser(full=True)
            # Monitor the full jobs for when the finish
            self.jobs_monitor(full=True)

    def transfer_files(self, result):
        """
        Transfer files to a directory that the control can access
        """

        self.logger.debug("transfer_files")

        #if self.preferences.get("exchange_dir", False):
        if self.command["directories"].get("exchange_dir", False):
            # Determine and validate the place to put the data
            target_dir = os.path.join(
                #self.preferences["exchange_dir"], os.path.split(self.working_dir)[1])
                self.command["directories"].get("exchange_dir" ), os.path.split(self.working_dir)[1])
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            # Copy compressed results files to exchange dir and update path.
            l = ["map_1_1", "map_2_1", 'pdb', 'mtz', 'tar', 'adf', 'peak']
            for f in l:
                if result.get(f, False):
                    archive_dict = result.get(f, {})
                    archive_file = archive_dict.get("path", False)
                    if archive_file:
                        # Copy data
                        target = os.path.join(target_dir, os.path.basename(archive_file))
                        # Copy files for now to make sure they are produced
                        shutil.copyfile(archive_file, target)
                        """
                        if f in ("map_1_1", "map_2_1", 'tar'):
                            shutil.move(archive_file, target)
                        else:
                            # Once we know this works we can switch to moving files.
                            shutil.copyfile(archive_file, target)
                        """
                        # Store new path information
                        archive_dict["path"] = target
                        # Add to the results.data_produced array
                        if f in ('pdb', 'mtz', 'tar', 'adf', 'peak'):
                            self.results["results"]["data_produced"].append(archive_dict)
                        # Also put PDB path in 'for_display' results
                        if f in ('pdb', "map_1_1", "map_2_1", 'adf', 'peak'):
                            self.results["results"]["for_display"].append(archive_dict)

            """
            # If there is data produced (Used for files that could be passed to another Plugin later)
            files_to_move = ("pdb", "mtz", "adf", "peak")
            for key in files_to_move:
                if result.get(key, None):
                    file_to_move = result.pop(key)
                    if os.path.exists(file_to_move):
                        # Move data
                        target = os.path.join(
                            target_dir, os.path.basename(file_to_move))
                        shutil.move(file_to_move, target)
                        # Compress data
                        arch_prod_file, arch_prod_hash = archive.compress_file(target)
                        # Remove the file that was compressed
                        os.unlink(target)
                        # Store information
                        new_data_produced = {
                            "path": arch_prod_file,
                            "hash": arch_prod_hash,
                            "description": '%s_%s'%(result.get("spacegroup"), key)
                        }
                        # Add the file to results.data_produced array
                        self.results["results"]["data_produced"].append(
                            new_data_produced)

            # If there is an archive 
            #self.logger.debug("result", result)
            archive_dict = result.get("tar", {})
            #self.logger.debug("archive_dict %s", archive_dict)
            archive_file = archive_dict.get("path", False)
            #self.logger.debug("archive_file %s", archive_file)
            if archive_file:
                # Move the file
                target = os.path.join(
                    target_dir, os.path.basename(archive_file))
                #self.logger.debug("target %s", target)
                shutil.move(archive_file, target)
                # Store information
                archive_dict["path"] = target
                # Add to the results.archive_files array
                self.results["results"]["archive_files"].append(
                    archive_dict)
            """
    def postprocess_invalid_input_file(self):
        """Make a proper result for PDB that could not be downloaded"""
        self.logger.debug("postprocess_invalid_input_file")
        # Save message
        self.results['results']['errors'].append('Invalid input structure file')
        # Update the status number
        self.update_status(100)
        # Passback new results to RAPD
        self.send_results()
        # Kill the plugin early
        os._exit(0)

    def postprocess(self):
        """Clean up after plugin action"""

        self.logger.debug("postprocess")

        self.tprint(arg=90, level="progress")

        # Cleanup my mess.
        self.clean_up()

        # Finished
        self.update_status(100)
        self.tprint(arg=100, level="progress")

        #pprint(self.results)

        self.write_json()

        # Send Final results
        self.send_results()

        # print results if run from commandline
        if self.tprint:
            self.print_results()

        # Print credits
        self.print_credits()
        
        # Message in logger
        t = round(time.time()-self.start_time)
        self.logger.debug('MR finished in %s seconds'%t)

    def clean_up(self):
        """Clean up the working directory"""

        self.logger.debug("clean_up")

        self.tprint("  Cleaning up", level=30, color="white")

        if self.command["preferences"].get("clean", False):
            self.logger.debug("Cleaning up Phaser files and folders")

            # Change to work dir
            os.chdir(self.working_dir)
            keep =  glob.glob("*.*")
            keep = [f for f in keep if not f.count(os.path.splitext(os.path.basename(self.struct_file))[0])]
            keep = [f for f in keep if not f.count(os.path.splitext(os.path.basename(self.data_file))[0])]
            dir_con = glob.glob("*")
            for target in dir_con:
                if target not in keep:
                    try:
                        if target.count('.'):
                            os.unlink(target)
                        else:
                            shutil.rmtree(target)
                    except:
                        self.logger.debug('Could not remove %s'%target)

    def print_results(self):
        """Print the results to the commandline"""

        self.logger.debug("print_results")

        self.tprint("\nResults", level=99, color="blue")

        def print_header_line():
            """Print the table header line"""
            self.tprint(("    {:^14} {:^14} {:^14} {:^14} {:^14} {:^14} {:^14} {}").format(
                "Space Group",
                "Search model",
                "# placed",
                "LL-Gain",
                "RF Z-score",
                "TF Z-score",
                "# Clashes",
                "Info",
                #width=str(longest_field)),
                ),
                        level=99,
                        color="red")

        def print_result_line(key, my_result):
            """Print the result line in the table"""
            # Split out chains
            sg = key.split('_')[0]
            c = key.split('_')[1]
            if c == 'all':
                chain = "all chains"
            else:
                chain = "chain %s"%c

            self.tprint("    {:^14} {:^14} {:^14} {:^14} {:^14} {:^14} {:^14} {}".format(
                sg,
                chain,
                my_result.get("nmol", "-"),
                my_result.get("gain", "-"),
                my_result.get("rfz", "-"),
                my_result.get("tfz", "-"),
                my_result.get("clash", "-"),
                my_result.get("message", ""),
                ),
                        level=99,
                        color="green")

        print_header_line()

        for sg in self.results['results']['mr_results'].keys():
            # Get the result in question
            my_result = self.results['results']['mr_results'][sg]

            # Print the result line
            print_result_line(sg, my_result)

    def write_json(self):
        """Print out JSON-formatted result"""

        json_string = json.dumps(self.results)
        
         # If running in JSON mode, print to terminal
        if self.preferences.get("run_mode") == "json":
            print json_results

        # Output to terminal?
        #if self.preferences.get("json", False):
        #    print json_string

        # Always write a file
        os.chdir(self.working_dir)
        with open("result.json", "w") as outfile:
            outfile.writelines(json_string)

    def print_credits(self):
        """Print credits for programs utilized by this plugin"""

        self.tprint(rcredits.HEADER,
                    level=99,
                    color="blue")

        programs = ["CCTBX", "PHENIX", "PHASER"]
        info_string = rcredits.get_credits_text(programs, "    ")

        self.tprint(info_string, level=99, color="black")

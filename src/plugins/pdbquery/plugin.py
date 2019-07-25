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

__created__ = "2017-04-20"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Development"

# This is an active RAPD plugin
RAPD_PLUGIN = True

# This plugin's type
DATA_TYPE = "MX"
PLUGIN_TYPE = "PDBQUERY"
PLUGIN_SUBTYPE = "EXPERIMENTAL"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "9a2e"
VERSION = "2.0.0"

# Standard imports
from distutils.spawn import find_executable
import glob
import logging
#from multiprocessing import Process
from multiprocessing import cpu_count
from threading import Thread
import os
from pprint import pprint
import random
import shutil
import sys
import time
import importlib
import random

# RAPD 
from bson.objectid import ObjectId
from plugins.subcontractors.rapd_phaser import run_phaser
from plugins.subcontractors.rapd_cctbx import get_pdb_info, get_mtz_info, get_res, get_spacegroup_info
from plugins.get_cif.plugin import check_pdbq
# from plugins.subcontractors.parse import parse_phaser_output, set_phaser_failed
from utils import archive
import utils.credits as rcredits
import utils.exceptions as exceptions
import utils.global_vars as rglobals
from utils.text import json
import utils.xutils as xutils
from utils.processes import local_subprocess, mp_pool, mp_manager

import info

# NE-CAT REST PDB server
PDBQ_SERVER = rglobals.PDBQ_SERVER

# Software dependencies
VERSIONS = {
    "gnuplot": (
        "gnuplot 4.2",
        "gnuplot 5.0",
    )
}

#class RapdPlugin(Process):
class RapdPlugin(Thread):
    """
    RAPD plugin class

    Command format:
    {
       "command":"pdbquery",
       "directories":
           {
               "work": ""                          # Where to perform the work
           },
       "site_parameters": {}                       # Site data
       "preferences": {}                           # Settings for calculations
       "return_address":("127.0.0.1", 50000)       # Location of control process
    }
    """

    # Settings
    # Calc ADF for each solution (creates a lot of big map files).
    #adf = False
    percent = 0.01
    # Run rigid-body refinement after MR.
    #rigid = False

    # Parameters
    cell = None
    est_res_number = 0
    large_cell = False
    input_spacegroup = False
    input_spacegroup_num = 0
    laue = False
    dres = 0.0
    volume = 0

    # Holders for passed-in info
    command = None
    preferences = {}
    
    # Holders for launched Phaser jobs
    cell_output = {}
    jobs = {}

    # Holders for pdb ids
    custom_structures = []
    common_contaminants = []
    search_results = []

    # Holders for results
    # Actual Phaser job results
    phaser_results = {}
    # Results that are sent back
    results = {}
    # Initial status
    status = 1
    
    redis = False
    pool = False
    batch_queue = False

    # Timers for processes
    phaser_timer = rglobals.PHASER_TIMEOUT

    #def __init__(self, command, processed_results=False, computer_cluster=False, tprint=False, logger=False, verbosity=False):
    def __init__(self, site, command, processed_results=False, tprint=False, logger=False, verbosity=False):
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
        
        self.test = self.preferences.get("test", False)
        #self.test = self.preferences.get("test", True) # Limit number of runs on cluster
        
        #self.sample_type = self.preferences.get("type", "protein")
        #self.solvent_content = self.preferences.get("solvent_content", 0.55)
        self.clean = self.preferences.get("clean", True)
        # self.verbose = self.command["preferences"].get("verbose", False)
        self.data_file = xutils.convert_unicode(self.command["input_data"].get("data_file"))
        # Used for setting up Redis connection
        self.db_settings = self.command["input_data"].get("db_settings")
        #self.nproc = self.preferences.get("nproc", 1)

        # If no launcher is passed in, use local_subprocess in a multiprocessing.Pool
        self.computer_cluster = xutils.load_cluster_adapter(self)
        if self.computer_cluster:
            self.launcher = self.computer_cluster.process_cluster
            self.batch_queue = self.computer_cluster.check_queue(self.command.get('command'))
        else:
            self.launcher = local_subprocess
            self.pool = mp_pool(self.preferences.get("nproc", cpu_count()-1))
            self.manager = mp_manager()

        # Setup a multiprocessing pool if not using a computer cluster.
        #if not self.computer_cluster:
        #    self.pool = mp_pool(self.nproc)
        
        # Set Python path for subcontractors.rapd_phaser
        self.rapd_python = "rapd.python"
        if self.site:
            if hasattr(self.site, "RAPD_PYTHON_PATH"):
                self.rapd_python = self.site.RAPD_PYTHON_PATH

    def run(self):
        """Execution path of the plugin"""

        self.preprocess()
        self.process()
        self.postprocess()

    def preprocess(self):
        """Set up for plugin action"""
        
        # Get running instance of PDB server
        self.repository = check_pdbq(self.tprint, self.logger)
        #print self.repository

        # Construct the results
        self.construct_results()

        # self.tprint("preprocess")
        self.tprint(arg=0, level="progress")

        # Glean some information on the input file
        input_spacegroup, self.cell, volume = get_mtz_info(self.data_file)
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
        self.tprint("  Cell: %f.2 %f.2 %f.2 %f.2 %f.2 %f.2" % tuple(self.cell),
                    level=10,
                    color="white")
        self.tprint("  Volume: %f.1" % volume, level=10, color="white")
        self.tprint("  Resolution: %f.1" % self.dres, level=10, color="white")
        # self.tprint("  Subgroups: %s" % self.laue, level=10, color="white")

        # Set by number of residues in AU. Ribosome (70s) is 24k.
        self.est_res_number = xutils.calc_res_number(input_spacegroup,
                                                     se=False,
                                                     volume=volume,
                                                     #sample_type=self.sample_type,
                                                     sample_type=self.preferences.get("type", "protein"),
                                                     #solvent_content=self.solvent_content
                                                     solvent_content=self.preferences.get("solvent_content", 0.55))
        if self.est_res_number > 5000:
            self.large_cell = True
            self.phaser_timer = self.phaser_timer * 1.5

        # Check for dependency problems
        self.check_dependencies()
        
        # Connect to Redis (computer cluster sends results via Redis)
        if self.preferences.get("run_mode") == "server" or self.computer_cluster:
            self.connect_to_redis()

    def update_status(self):
        """Update the status of the run."""
        iter = 90/len(self.cell_output.keys())
        self.status += iter
        if self.status > 90:
            self.status = 90
        self.results["process"]["status"] = int(self.status)

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
        self.results["preferences"] = self.preferences

        # Describe the process
        self.results["process"] = self.command.get("process", {})
        # Add process_id
        self.results["process"]["process_id"] = self.command.get("process_id")
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
            "custom_structures": [],
            "common_contaminants": [],
            "search_results": [],
            "archive_files": [],
            "data_produced": [],
            "for_display": []
        }
    
    def connect_to_redis(self):
        """Connect to the redis instance"""
        redis_database = importlib.import_module('database.redis_adapter')
        #redis_database = redis_database.Database(settings=self.db_settings)
        #self.redis = redis_database.connect_to_redis()
        self.redis = redis_database.Database(settings=self.db_settings,
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

        if self.command["input_data"].get("pdbs", False):
            self.add_custom_pdbs()

        if self.preferences.get("search", False):
            self.query_pdbq()

        if self.preferences.get("contaminants", False):
            self.add_contaminants()

        self.process_phaser()

        self.jobs_monitor()

    def add_custom_pdbs(self):
        """Add custom pdb codes to the screen"""

        self.logger.debug("add_custom_pdbs")
        self.tprint("\nAdding input PDB codes", level=10, color="blue")

        # Query the server for information and add to self.cell_output
        cif_check = self.repository.check_for_pdbs(self.command["input_data"].get("pdbs"))
        self.cell_output.update(cif_check)
        self.custom_structures = cif_check.keys()

    def query_pdbq(self):
        """
        Check if cell is found in PDBQ

        Places relevant pdbs into self.cell_output
        """

        self.logger.debug("query_pdbq")
        self.tprint("\nSearching for similar unit cells in the PDB", level=10, color="blue")
        
        def connect_pdbq(previous_results, permutations, end):
            """Function to query the PDBQ server"""

            all_results = previous_results.copy()

            # Fields for search parameters
            fields = ["a", "b", "c", "alpha", "beta", "gamma"]

            for permute_counter in range(end):
                search_params = {}
                for field_index, field in enumerate(fields):
                    search_params[field] = \
                        [self.cell[permutations[permute_counter][field_index]] -
                         self.cell[permutations[permute_counter][field_index]] *
                         self.percent/2,
                         self.cell[permutations[permute_counter][field_index]] +
                         self.cell[permutations[permute_counter][field_index]] *
                         self.percent/2]
                #print "search_params", search_params
                #all_results.update(self.repository.cell_search(search_params))
                search_results = self.repository.cell_search(search_params)
                all_results.update(search_results)

            # Return all results
            return all_results

        def limit_pdbq_results(pdbq_results, limit):
            """Filter repeats out of query"""
            entries_beyond_limit = pdbq_results.keys()[:limit+1]
            for p in pdbq_results.keys():
                if p in entries_beyond_limit:
                    del pdbq_results[p]
            return pdbq_results

        permute = False
        end = 1
        permutations = [(0, 1, 2, 3, 4, 5), (1, 2, 0, 4, 5, 3), (2, 0, 1, 5, 3, 4)]

        # Check for orthorhombic
        if self.laue == "16":
            permute = True

        # Check monoclinic when Beta is near 90.
        if self.laue in ("3", "5"):
            if 89.0 < self.cell[4] < 91.0:
                permute = True

        if permute:
            end = len(permutations)

        # Limit the minimum number of results
        no_limit = False
        if self.computer_cluster:
            if self.large_cell:
                limit = 10
            elif permute:
                limit = 60
            else:
                no_limit = True
                limit = 40
        else:
            limit = 8

        # Limit the unit cell difference to 25%. Also stops it if errors are received.
        pdbq_results = {}
        counter = 0
        while counter < 25:
            self.tprint("  Querying server at %s" % PDBQ_SERVER,
                        level=20,
                        color="white")

            # Connect to and query the PDBQ server
            pdbq_results = connect_pdbq(pdbq_results, permutations, end)

            # Handle results
            if pdbq_results:
                for line in pdbq_results.keys():
                    # Remove anything bigger than 4 letters
                    if len(line) > 4:
                        del pdbq_results[line]

                # Do not limit number of results if many models come out really close in cell
                # dimensions.
                if counter in (0, 1):
                    # Limit output
                    if no_limit == False:
                        pdbq_results = limit_pdbq_results(pdbq_results, limit)
                else:
                    pdbq_results = limit_pdbq_results(pdbq_results, limit)

            # Not enough results
            if len(pdbq_results) < limit:
                counter += 1
                self.percent += 0.01
                self.logger.debug("Not enough PDB results. Going for more...")
            else:
                break

        # There will be results!
        if pdbq_results:
            # Test mode = only one PDB
            if self.test:
                my_pdbq_results = {
                    pdbq_results.keys()[0]: pdbq_results[pdbq_results.keys()[0]],
                    pdbq_results.keys()[1]: pdbq_results[pdbq_results.keys()[1]],
                    pdbq_results.keys()[2]: pdbq_results[pdbq_results.keys()[2]],
                    }
                pdbq_results = my_pdbq_results
            self.search_results = pdbq_results.keys()
            self.cell_output.update(pdbq_results)

            self.tprint("  %d relevant PDB files found on the PDBQ server" % \
                        len(pdbq_results.keys()),
                        level=50,
                        color="white")
        else:
            self.logger.debug("Failed to find pdb with similar cell.")
            self.tprint("No relevant PDB files found on the PDBQ server",
                        level=50,
                        color="red")

    def add_contaminants(self):
        """
        Add common PDB contaminants to the search list.

        Adds files to self.cell_output
        """
        self.logger.debug("add_common_pdb")
        self.tprint("\nAdding common contaminants to PDB screen",
                    level=10,
                    color="blue")

        # Save these codes in a separate list so they can be separated in the Summary.
        common_contaminants = info.CONTAMINANTS.copy()
        self.common_contaminants = common_contaminants.keys()

        # Remove PDBs from self.common if they were already caught by unit cell dimensions.
        for contaminant in self.common_contaminants:
            if contaminant in self.cell_output:
                del common_contaminants[contaminant]
                self.common_contaminants.remove(contaminant)

        # Test mode = only one PDB
        if self.test:
            my_contaminants = {
                common_contaminants.keys()[0]: common_contaminants[common_contaminants.keys()[0]]
                }
            common_contaminants = my_contaminants
            self.common_contaminants = common_contaminants.keys()

        # Put contaminants in list to be screened
        self.tprint("  %d contaminants added to screen" % len(common_contaminants),
                    level=10,
                    color="white")
        # print common_contaminants
        self.cell_output.update(common_contaminants)

    def process_phaser(self):
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
                #inp['db_settings'] = self.site.CONTROL_DATABASE_SETTINGS
                # Don't need result queue since results will be sent via Redis
                queue = False
            else:
                inp['pool'] = self.pool
                # Add result queue
                queue = self.manager.Queue()
                inp['result_queue'] = queue
            
            #if self.pool:
            #    inp['pool'] = self.pool
            #else:
            #    inp['tag'] = tag
            #job, pid, tag = run_phaser(**inp)
            job, pid = run_phaser(**inp)
            self.jobs[job] = {'name': inp['name'],
                              'pid' : pid,
                              'tag' : tag,
                              'result_queue': queue,
                              'spacegroup': inp['spacegroup'] # Need for jobs that timeout.
                              }

        # Run through the pdbs
        for pdb_code in self.cell_output.keys():

            self.tprint("    %s" % pdb_code, level=30, color="white")

            l = False
            copy = 1

            # Create directory for MR
            xutils.create_folders(self.working_dir, "Phaser_%s" % pdb_code)
            cif_file = pdb_code.lower() + ".cif"
            
            # Get the structure file
            if self.test and os.path.exists(cif_file):
                cif_path = os.path.join(os.getcwd(), cif_file)
            else:
                cif_path = self.repository.download_cif(pdb_code, os.path.join(os.getcwd(), cif_file))
            
            if not cif_path:
                self.postprocess_invalid_code(pdb_code)
            else:
                # If mmCIF, checks if file exists or if it is super structure with
                # multiple PDB codes, and returns False, otherwise sends back SG.
                spacegroup_pdb = xutils.fix_spacegroup(get_spacegroup_info(cif_path))
                if not spacegroup_pdb:
                    del self.cell_output[pdb_code]
                    continue

                # Now check all SG's
                spacegroup_num = xutils.convert_spacegroup(spacegroup_pdb)
                lg_pdb = xutils.get_sub_groups(spacegroup_num, "laue")
                self.tprint("      %s spacegroup: %s (%s)" % (cif_path, spacegroup_pdb, spacegroup_num),
                            level=10,
                            color="white")
                self.tprint("      subgroups: %s" % str(lg_pdb), level=10, color="white")
    
                # SG from data
                data_spacegroup = xutils.convert_spacegroup(self.laue, True)
                # self.tprint("      Data spacegroup: %s" % data_spacegroup, level=10, color="white")
    
                # Fewer mols in AU or in common_contaminents.
                if pdb_code in self.common_contaminants or float(self.laue) > float(lg_pdb):
                    # if SM is lower sym, which will cause problems, since PDB is too big.
                    pdb_info = get_pdb_info(struct_file=cif_path,
                                            data_file=self.data_file,
                                            dres=self.dres,
                                            matthews=True,
                                            chains=True)
                    # Prune if only one chain present, b/c "all" and "A" will be the same.
                    if len(pdb_info.keys()) == 2:
                        for key in pdb_info.keys():
                            if key != "all":
                                del pdb_info[key]
                    copy = pdb_info["all"]["NMol"]
                    if copy == 0:
                        copy = 1
                    # If pdb_info["all"]["res"] == 0.0:
                    if pdb_info["all"]["SC"] < 0.2:
                        # Only run on chains that will fit in the AU.
                        l = [chain for chain in pdb_info.keys() if pdb_info[chain]["res"] != 0.0]
    
                # More mols in AU
                elif float(self.laue) < float(lg_pdb):
                    pdb_info = get_pdb_info(struct_file=cif_path,
                                            data_file=self.data_file,
                                            dres=self.dres,
                                            matthews=True,
                                            chains=False)
                    copy = pdb_info["all"]["NMol"]
    
                # Same number of mols in AU.
                else:
                    pdb_info = get_pdb_info(struct_file=cif_path,
                                            data_file=self.data_file,
                                            dres=self.dres,
                                            matthews=False,
                                            chains=False)
    
                job_description = {
                    "work_dir": os.path.abspath(os.path.join(self.working_dir, "Phaser_%s" % pdb_code)), #
                    "data_file": self.data_file,
                    "struct_file": cif_path,
                    "name": pdb_code, #
                    "spacegroup": data_spacegroup,
                    "ncopy": copy,  #
                    #"test": self.test,
                    "cell_analysis": True,  #
                    #"large_cell": self.large_cell,
                    "resolution": xutils.set_phaser_res(pdb_info["all"]["res"],
                                                 self.large_cell,
                                                 self.dres),
                    "launcher": self.launcher,  #
                    "db_settings": self.db_settings,  #
                    "tag": False,  #
                    "batch_queue": self.batch_queue, #
                    "rapd_python": self.rapd_python}
    
                if not l:
                    launch_job(job_description)
                else:
                    for chain in l:
                        new_code = "%s_%s" % (pdb_code, chain)
                        xutils.folders(self, "Phaser_%s" % new_code)
                        job_description.update({
                            "work_dir": os.path.abspath(os.path.join(self.working_dir, "Phaser_%s" % \
                                new_code)),
                            "struct_file": pdb_info[chain]["file"],
                            "name":new_code,
                            "ncopy":pdb_info[chain]["NMol"],
                            "resolution":xutils.set_phaser_res(pdb_info[chain]["res"],
                                                        self.large_cell,
                                                        self.dres)})
                        launch_job(job_description)

    def postprocess_phaser(self, job_name, results):
        """fix Phaser results and pass back"""
        
        self.logger.debug("postprocess_phaser")
        self.logger.debug(results)

        # Add description to results
        results['description'] = self.cell_output[job_name.split('_')[0]].get('description')

        # Copy tar to working dir for commandline results
        if results.get("tar", False):
            orig = results.get("tar", {"path":False}).get("path")
            if orig:
                new = os.path.join(self.working_dir, os.path.basename(orig))
                # If old file in working dir, remove it and recopy.
                if os.path.exists(new):
                    os.unlink(new)
                shutil.copy(orig, new)
                results["tar"]["path"] = new
        
        # Copy pdbfile to working dir
        if results.get("pdb_file", False):
            orig = results.get("pdb_file")
            new = os.path.join(self.working_dir, os.path.basename(orig))
            # If old file in working dir, remove it and recopy.
            if os.path.exists(new):
                os.unlink(new)
            shutil.copy(orig, new)
            results["pdb_file"] = new
        
         # Three result types to run through
        types = (
            ("custom_structures", self.custom_structures),
            ("common_contaminants", self.common_contaminants),
            ("search_results", self.search_results)
        )
        # Run through result types
        for result_type, pdb_codes in types:
            if pdb_codes.count(job_name.split('_')[0]):
                # Add chains of PDB to correct list
                if len(job_name.split('_')) not in [1]:
                    pdb_codes.append(job_name)
                # Update results
                #self.results['results'][result_type][job_name] = results
                self.results['results'][result_type].append(results)
                break

        # Save results for command line
        self.phaser_results[job_name] = {"results": results}
        # Update the status number
        self.update_status()
        # Move transferring files
        self.transfer_files(results)
        # Passback new results to RAPD
        self.send_results()

    def transfer_files(self, result):
        """
        Transfer files to a directory that the control can access
        """

        self.logger.debug("transfer_files")

        #if self.preferences.get("exchange_dir", False):
        if self.command["directories"].get("exchange_dir", False):
            #self.logger.debug("transfer_files",
            #                 self.command["directories"].get("exchange_dir" ))

            # Determine and validate the place to put the data
            target_dir = os.path.join(
                #self.preferences["exchange_dir"], os.path.split(self.working_dir)[1])
                self.command["directories"].get("exchange_dir" ), os.path.split(self.working_dir)[1])
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            # If there is a pdb produced -> data_produced
            archive_dict = result.get("pdb", {})
            archive_file = archive_dict.get("path", False)
            if archive_file:
                # Copy data
                target = os.path.join(target_dir, os.path.basename(file_to_move))
                shutil.copyfile(file_to_move, target)
                # Store information
                archive_dict["path"] = target
                # Add to the results.data_produced array
                self.results["results"]["data_produced"].append(archive_dict)

            # # Maps & PDB
            # for my_map in ("map_1_1", "map_2_1", "pdb"):
            #     archive_dict = result.get(my_map, {})
            #     archive_file = archive_dict.get("path", False)
            #     if archive_file:
            #         # Move the file
            #         target = os.path.join(target_dir, os.path.basename(archive_file))
            #         shutil.move(archive_file, target)
            #         # Store information
            #     archive_dict["path"] = target
            #     # Add to the results.data_produced array
            #     self.results["results"]["data_produced"].append(archive_dict)

            # Maps & PDB
            for my_map in ("map_1_1", "map_2_1", "pdb"):
                archive_dict = result.get(my_map, {})
                archive_file = archive_dict.get("path", False)
                if archive_file:
                    # Move the file
                    target = os.path.join(target_dir, os.path.basename(archive_file))
                    shutil.move(archive_file, target)
                    # Store information
                    archive_dict["path"] = target
                    # Add to the results.archive_files array
                    self.results["results"]["for_display"].append(
                        archive_dict)

            # If there is an archive
            archive_dict = result.get("tar", {})
            archive_file = archive_dict.get("path", False)
            if archive_file:
                # Move the file
                target = os.path.join(
                    target_dir, os.path.basename(archive_file))
                self.logger.debug("target %s", target)
                shutil.move(archive_file, target)
                # Store information
                archive_dict["path"] = target
                # Add to the results.archive_files array
                self.results["results"]["archive_files"].append(
                    archive_dict)
        
    def postprocess_invalid_code(self, job_name):
        """Make a proper result for PDB that could not be downloaded"""
        
        results = {"solution": False,
                   "message": "invalid PDB code",
                   "description": self.cell_output[job_name].get("description")}

         # Three result types to run through
        types = (
            ("custom_structures", self.custom_structures),
            ("common_contaminants", self.common_contaminants),
            ("search_results", self.search_results)
        )
        # Run through result types
        for result_type, pdb_codes in types:
            if pdb_codes.count(job_name):
                self.results['results'][result_type][job_name] = results
                break

        # Save results for command line
        self.phaser_results[job_name] = {"results": results}
        # Update the status number
        self.update_status()
        # Passback new results to RAPD
        self.send_results()

    def jobs_monitor(self):
        """Monitor running jobs and finsh them when they complete."""

        def finish_job(job):
            """Finish the jobs and send to postprocess_phaser"""
            info = self.jobs.pop(job)
            self.tprint('    Finished Phaser on %s with id: %s'%(info['name'], info['tag']), level=30, color="white")
            self.logger.debug('Finished Phaser on %s'%info['name'])
            if self.computer_cluster:
                results_json = self.redis.get(info['tag'])
                # This try/except is for when results aren't in Redis in time.
                try:
                    results = json.loads(results_json)
                    self.postprocess_phaser(info['name'], results)
                    self.redis.delete(info['tag'])
                except Exception as e:
                    self.logger.error('Error '+ str(e))
                    #print 'PROBLEM: %s %s'%(info['name'], info['output_id'])
                    #print results_json
            else:
                results = info['result_queue'].get()
                # pprint(results.get('stdout', " "))
                # pprint(json.loads(results.get('stdout'," ")))
                # if results["stderr"]:
                #     print results["stderr"]
                self.postprocess_phaser(info['name'], json.loads(results.get('stdout', " ")))
            jobs.remove(job)
            
            #results_json = self.redis.get(info['tag'])
            # This try/except is for when results aren't in Redis in time.
            #try:
            #    results = json.loads(results_json)
            #    self.postprocess_phaser(info['name'], results)
            #    self.redis.delete(info['tag'])
            #except Exception as e:
            #    self.logger.error('Error'+ str(e))
                # print 'PROBLEM: %s %s'%(info['name'], info['tag'])
                # print results_json
                # self.logger.debug('PROBLEM: %s %s'%(info['name'], info['tag']))
                # self.logger.debug(results_json)
            
            #results = json.loads(results_json)
            #print results
            #self.postprocess_phaser(info['name'], results)
            #self.redis.delete(info['tag'])
            #jobs.remove(job)

        # Signal to the pool that no more processes will be added
        if self.pool:
            self.pool.close()

        timed_out = False
        timer = 0
        jobs = self.jobs.keys()

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
                self.logger.debug('AutoStat timed out.')
                print 'AutoStat timed out.'
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
                                                       "message": "Timed out"})
                # Delete the Redis key
                self.redis.delete(info['tag'])

        # Join the self.pool if used
        if self.pool:
            self.pool.join()

        if self.verbose and self.logger:
            self.logger.debug('PDBQuery.jobs_monitor finished.')

    def postprocess(self):
        """Clean up after plugin action"""

        self.tprint(arg=90, level="progress")

        # Cleanup my mess.
        self.clean_up()

        # Finished
        self.results["process"]["status"] = 100
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
        self.logger.debug('PDBquery finished')

    def clean_up(self):
        """Clean up the working directory"""

        self.tprint("  Cleaning up", level=30, color="white")

        if self.command["preferences"].get("clean", False):
            self.logger.debug("Cleaning up Phaser files and folders")

            # Change to work dir
            os.chdir(self.working_dir)
            """
            # Gather targets and remove
            files_to_clean = glob.glob("Phaser_*")
            for target in files_to_clean:
                shutil.rmtree(target)
            """
    def print_results(self):
        """Print the results to the commandline"""

        self.tprint("\nResults", level=99, color="blue")

        # pprint(self.results["results"])

        def get_longest_field(pdb_codes):
            """Calculate the ongest field in a set of results"""
            longest_field = 0
            for pdb_code in pdb_codes:
                if self.cell_output.has_key(pdb_code):
                    length = len(self.cell_output[pdb_code]["description"])
                    if length > longest_field:
                        longest_field = length
            return longest_field

        def print_header_line(longest_field):
            """Print the table header line"""
            self.tprint(("    {:4} {:^{width}} {:^14} {:^14} {:^14} {:^14} {}").format(
                "PDB",
                "Description",
                "LL-Gain",
                "RF Z-score",
                "TF Z-score",
                "# Clashes",
                "Info",
                width=str(longest_field)),
                        level=99,
                        color="white")

        def print_result_line(pdb_code, my_result, longest_field):
            """Print the result line in the table"""

            # print my_result

            self.tprint("    {:4} {:^{width}} {:^14} {:^14} {:^14} {:^14} {}".format(
                pdb_code,
                #self.cell_output[pdb_code]["description"],
                my_result.get("description", "-"),
                my_result.get("gain", "-"),
                my_result.get("rfz", "-"),
                my_result.get("tfz", "-"),
                my_result.get("clash", "-"),
                my_result.get("message", ""),
                width=str(longest_field)
                ),
                        level=99,
                        color="white")

        for tag, pdb_codes in (("User-input structures", self.custom_structures),
                               ("Common contaminants", self.common_contaminants),
                               ("Cell parameter search structures", self.search_results)):

            if pdb_codes:

                # Find out the longest description field
                longest_field = get_longest_field(pdb_codes)

                # Print header for table
                self.tprint("\n  %s" % tag, level=99, color="white")
                print_header_line(longest_field)

                # Run through the codes
                for pdb_code in pdb_codes:
                    if self.phaser_results.has_key(pdb_code):
                        # Get the result in question
                        my_result = self.phaser_results[pdb_code]["results"]
    
                        # Print the result line
                        print_result_line(pdb_code, my_result, longest_field)

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

        self.tprint(info_string, level=99, color="white")

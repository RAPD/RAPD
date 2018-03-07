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
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# This is an active RAPD plugin
RAPD_PLUGIN = True

# This plugin's type
PLUGIN_TYPE = "PDBQUERY"
PLUGIN_SUBTYPE = "EXPERIMENTAL"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "9a2e422625e811e79866ac87a3333966"
VERSION = "1.0.0"

# Standard imports
from distutils.spawn import find_executable
import glob
import logging
import multiprocessing
import os
from pprint import pprint
import signal
import shutil
import subprocess
import time
import urllib2

# RAPD imports
from plugins.subcontractors.phaser import parse_phaser_output, run_phaser_pdbquery
# from plugins.subcontractors.parse import parse_phaser_output, set_phaser_failed
import utils.credits as rcredits
import utils.exceptions as exceptions
import utils.global_vars as rglobals
from utils.text import json
from bson.objectid import ObjectId
# import utils.pdb as rpdb
import utils.xutils as xutils
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

class RapdPlugin(multiprocessing.Process):
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
    # Place that structure files may be stored
    cif_cache = "/tmp/rapd_cache/cif_files"
    # Calc ADF for each solution (creates a lot of big map files).
    adf = False
    percent = 0.01
    # Run rigid-body refinement after MR.
    rigid = False
    # Search for common contaminants.
    search_common = True

    sample_type = "protein"
    solvent_content = 0

    # Parameters
    cell = None
    cell_output = {}
    cell_summary = False
    est_res_number = 0
    tooltips = False
    pdb_summary = False
    large_cell = False
    input_spacegroup = False
    input_spacegroup_num = 0
    laue = False
    dres = 0.0
    volume = 0

    # Holders for passed-in info
    command = None
    preferences = {}

    # Holders for pdb ids
    custom_structures = []
    common_contaminants = []
    search_results = []

    # Holders for results
    phaser_results_raw = []
    phaser_results = {}
    results = {}

    # Timers for processes
    pdbquery_timer = 30
    phaser_timer = rglobals.PHASER_TIMEOUT

    def __init__(self, command, tprint=False, logger=False):
        """Initialize the plugin"""

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

        # Some logging
        self.logger.info(command)

        # Store passed-in variables
        self.command = command
        self.preferences = self.command.get("preferences", {})

        self.results["command"] = command
        self.results["process"] = {
            "process_id": self.command.get("process_id"),
            "status": 1}

        # pprint(command)

        # Params
        self.working_dir = self.command["directories"].get("work", os.getcwd())
        self.test = self.command["preferences"].get("test", False)
        self.sample_type = self.command["preferences"].get("type", "protein")
        self.solvent_content = self.command["preferences"].get("solvent_content", 0.55)
        self.cluster_use = self.command["preferences"].get("cluster", False)
        self.clean = self.command["preferences"].get("clean", True)
        # self.gui = self.command["preferences"].get("gui", True)
        # self.verbose = self.command["preferences"].get("verbose", False)
        self.datafile = xutils.convert_unicode(self.command["input_data"].get("datafile"))

        multiprocessing.Process.__init__(self, name="pdbquery")
        self.start()

    def run(self):
        """Execution path of the plugin"""

        self.preprocess()
        self.process()
        self.postprocess()

    def preprocess(self):
        """Set up for plugin action"""

        # self.tprint("preprocess")
        self.tprint(arg=0, level="progress")

        # Check the local pdb cache Location
        if self.cif_cache:
            if not os.path.exists(self.cif_cache):
                os.makedirs(self.cif_cache)

        # Glean some information on the input file
        self.input_spacegroup, self.cell, self.volume = xutils.get_mtz_info(self.datafile)
        self.dres = xutils.get_res(self.datafile)
        self.input_spacegroup_num = int(xutils.convert_spacegroup(self.input_spacegroup))
        self.laue = xutils.get_sub_groups(self.input_spacegroup_num, "simple")

        # Throw some information into the terminal
        self.tprint("\nDataset information", color="blue", level=10)
        self.tprint("  Data file: %s" % self.datafile, level=10, color="white")
        self.tprint("  Spacegroup: %s  (%d)" % (self.input_spacegroup, self.input_spacegroup_num),
                    level=10,
                    color="white")
        self.tprint("  Cell: %f %f %f %f %f %f" % tuple(self.cell), level=10, color="white")
        self.tprint("  Volume: %f" % self.volume, level=10, color="white")
        self.tprint("  Resolution: %f" % self.dres, level=10, color="white")
        self.tprint("  Subgroups: %s" % self.laue, level=10, color="white")

        # Set by number of residues in AU. Ribosome (70s) is 24k.
        self.est_res_number = xutils.calc_res_number(self.input_spacegroup,
                                                     se=False,
                                                     volume=self.volume,
                                                     sample_type=self.sample_type,
                                                     solvent_content=self.solvent_content)
        if self.est_res_number > 5000:
            self.large_cell = True
            self.phaser_timer = self.phaser_timer * 1.5

        # Check for dependency problems
        self.check_dependencies()

    def check_dependencies(self):
        """Make sure dependencies are all available"""

        # Any of these missing, dead in the water
        #TODO reduce external dependencies
        for executable in ("bzip2", "gunzip", "phaser", "phenix.cif_as_pdb", "tar"):
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

    def process(self):
        """Run plugin action"""

        # self.tprint("process")

        if self.command["input_data"].get("pdbs", False):
            self.add_custom_pdbs()

        if self.command["preferences"].get("search", False):
            self.query_pdbq()

        if self.command["preferences"].get("contaminants", False):
            self.add_contaminants()

        self.phaser_results_raw = self.process_phaser()

        self.postprocess_phaser(self.phaser_results_raw)

    def add_custom_pdbs(self):
        """Add custom pdb codes to the screen"""

        self.logger.debug("add_custom_pdbs")
        self.tprint("\nAdding input PDB codes", level=10, color="blue")

        # Query the server for information and add to self.cell_output
        for pdb_code in self.command["input_data"].get("pdbs"):

            # Make sure we are in upper case
            pdb_code = pdb_code.upper()

            # Query pdbq server
            try:
                response = urllib2.urlopen(urllib2.Request("%s/entry/%s" % \
                           (PDBQ_SERVER, pdb_code))).read()

                # Decode search result
                entry = json.loads(response)

            except urllib2.URLError as pdbq_error:
                self.tprint("  Error connecting to PDBQ server %s" % pdbq_error,
                            level=30,
                            color="red")
                entry = {"message": {"_entity-pdbx_description": [
                    "Unknown - unable to connect to PDBQ sever"
                ]}}

            # Grab the description
            description = entry["message"]["_entity-pdbx_description"][0]

            # Print info to console
            self.tprint("  %s - %s" % (pdb_code, description),
                        level=10,
                        color="white")

            # Save into self.cell_output
            self.cell_output.update({
                pdb_code: {
                    "description": description
                }
            })

            # Save IDs to easily used spot
            self.custom_structures.append(pdb_code)

            # Test mode = only one PDB
            if self.command["preferences"].get("test", False):
                break

    def query_pdbq(self):
        """
        Check if cell is found in PDBQ

        Places relevant pdbs into self.cell_output
        """

        self.logger.debug("query_pdbq")
        self.tprint("\nSearching for similar unit cells in the PDB", level=10, color="blue")

        def connect_pdbq(previous_results, permutations, end=0):
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
                print "search_params", search_params

                # Query server
                print "%s/search/" % PDBQ_SERVER
                response = urllib2.urlopen(urllib2.Request("%s/cell_search/" % \
                           PDBQ_SERVER, data=json.dumps(search_params))).read()

                # Decode search result
                search_results = json.loads(response)

                # Create handy description key
                for k in search_results.keys():
                    search_results[k]["description"] = \
                        search_results[k].pop("struct.pdbx_descriptor")

                # Add new results to previous
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
        if self.cluster_use:
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
                for line in pdbq_results:
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
            if self.command["preferences"].get("test", False):
                my_pdbq_results = {
                    pdbq_results.keys()[0]: pdbq_results[pdbq_results.keys()[0]],
                    pdbq_results.keys()[1]: pdbq_results[pdbq_results.keys()[1]],
                    pdbq_results.keys()[2]: pdbq_results[pdbq_results.keys()[2]],
                    }
                pdbq_results = my_pdbq_results
            self.search_results = pdbq_results.keys()[:]
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
        if self.command["preferences"].get("test", False):
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

        # Run through the pdbs
        commands = []
        for pdb_code in self.cell_output:

            self.tprint("    %s" % pdb_code, level=30, color="white")

            l = False
            copy = 1

            # Create directory for MR
            xutils.create_folders(self.working_dir, "Phaser_%s" % pdb_code)

            # Get the structure file
            pdb_file, spacegroup_pdb = self.get_pdb_file(pdb_code)

            # Now check all SG's
            spacegroup_num = xutils.convert_spacegroup(spacegroup_pdb)
            lg_pdb = xutils.get_sub_groups(spacegroup_num, "simple")
            self.tprint("      %s spacegroup: %s (%s)" % (pdb_file, spacegroup_pdb, spacegroup_num),
                        level=10,
                        color="white")
            self.tprint("      subgroups: %s" % str(lg_pdb), level=10, color="white")

            # SG from data
            data_spacegroup = xutils.convert_spacegroup(self.laue, True)
            # self.tprint("      Data spacegroup: %s" % data_spacegroup, level=10, color="white")

            # Fewer mols in AU or in self.common.
            if pdb_code in self.common_contaminants or float(self.laue) > float(lg_pdb):
                # if SM is lower sym, which will cause problems, since PDB is too big.
                # Need full path for copying pdb files to folders.
                pdb_info = xutils.get_pdb_info(os.path.join(os.getcwd(), pdb_file),
                                               dres=self.dres,
                                               matthews=True,
                                               cell_analysis=False,
                                               data_file=self.datafile)
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
                pdb_info = xutils.get_pdb_info(cif_file=pdb_file,
                                               dres=self.dres,
                                               matthews=True,
                                               cell_analysis=True,
                                               data_file=self.datafile)
                copy = pdb_info["all"]["NMol"]

            # Same number of mols in AU.
            else:
                pdb_info = xutils.get_pdb_info(cif_file=pdb_file,
                                               dres=self.dres,
                                               matthews=False,
                                               cell_analysis=True,
                                               data_file=self.datafile)

            job_description = {
                "work_dir": os.path.abspath(os.path.join(self.working_dir, "Phaser_%s" % pdb_code)),
                "data": self.datafile,
                "pdb": pdb_file,
                "name": pdb_code,
                "spacegroup": data_spacegroup,
                "copy": copy,
                "test": self.test,
                "cell analysis": True,
                "large": self.large_cell,
                "res": xutils.set_phaser_res(pdb_info["all"]["res"],
                                             self.large_cell,
                                             self.dres),
                "timeout": self.phaser_timer}

            if not l:
                commands.append(job_description)
            else:
                # d1 = {}
                for chain in l:
                    new_code = "%s_%s" % (pdb_code, chain)
                    xutils.folders(self, "Phaser_%s" % new_code)
                    job_description.update({
                        "work_dir": os.path.abspath(os.path.join(self.working_dir, "Phaser_%s" % \
                            new_code)),
                        "pdb":pdb_info[chain]["file"],
                        "name":new_code,
                        "copy":pdb_info[chain]["NMol"],
                        "res":xutils.set_phaser_res(pdb_info[chain]["res"],
                                                    self.large_cell,
                                                    self.dres)})

                    commands.append(job_description)

        # Run in pool
        pool = multiprocessing.Pool(self.preferences.get("nproc", 1))
        self.tprint("  Initiating Phaser runs", level=10, color="white")
        results = pool.map_async(run_phaser_pdbquery, commands)
        pool.close()
        pool.join()
        phaser_results = results.get()

        return phaser_results

    def postprocess_phaser(self, phaser_results):
        """
        Look at Phaser results.
        """

        self.logger.debug("postprocess_phaser")

        for phaser_result in phaser_results:

            # pprint(phaser_result)

            pdb_code = phaser_result["pdb_code"]
            phaser_lines = phaser_result["log"].split("\n")

            solution = True

            data = parse_phaser_output(phaser_lines)
            # pprint(data)
            # if not data:  # data["spacegroup"] in ("No solution", "Timed out", "NA", "DL FAILED"):
            # if data in ("No Solution", "Timed Out"):
            #     nosol = True
            # else:
            # Check for negative or low LL-Gain.
            if data.get("gain"):
                if data.get("gain") < 200.0:
                    # nosol = True
                    data = {"solution": False,
                            "message": "No solution"}
            # if nosol:
            self.phaser_results[pdb_code] = {"results": data}
            # else:
            #     self.phaser_results[pdb_code] = {"results": data}

    def get_pdb_file(self, pdb_code):
        """Retrieve/check for/uncompress/convert structure file"""

        # Set up some file names
        cif_file = pdb_code.lower() + ".cif"
        gzip_file = cif_file+".gz"
        cached_file = False

        # There is a local cache
        if self.cif_cache:
            cached_file = os.path.join(self.cif_cache, gzip_file)

            # Have cached version of the file
            if os.path.exists(cached_file):
                self.tprint("      Have cached cif file %s" % gzip_file, level=10, color="white")

            # DO NOT have cached version of file
            else:
                # Get the gzipped cif file from the PDBQ server
                self.tprint("      Fetching %s" % cif_file, level=10, color="white")
                try:
                    response = urllib2.urlopen(urllib2.Request(\
                               "%s/entry/get_cif/%s" % \
                               (PDBQ_SERVER, cif_file.replace(".cif", "")))\
                               , timeout=60).read()
                except urllib2.HTTPError as http_error:
                    self.tprint("      %s when fetching %s" % (http_error, cif_file),
                                level=50,
                                color="red")
                    return False

                # Write the  gzip file
                with open(cached_file, "wb") as outfile:
                    outfile.write(response)

            # Copy the gzip file to the cwd
            shutil.copy(cached_file, os.path.join(os.getcwd(), gzip_file))

        # No local CIF file cache
        else:
            # Get the gzipped cif file from the PDBQ server
            self.tprint("      Fetching %s" % cif_file, level=10, color="white")
            try:
                response = urllib2.urlopen(urllib2.Request(\
                           "%s/entry/get_cif/%s" % \
                           (PDBQ_SERVER, cif_file.replace(".cif", ""))), \
                           timeout=60).read()
            except urllib2.HTTPError as http_error:
                self.tprint("      %s when fetching %s" % (http_error, cif_file),
                            level=50,
                            color="red")
                return False

            # Write the  gzip file
            with open(gzip_file, "wb") as outfile:
                outfile.write(response)

        # Uncompress the gzipped file
        unzip_proc = subprocess.Popen(["gunzip", gzip_file])
        unzip_proc.wait()

        # If mmCIF, checks if file exists or if it is super structure with
        # multiple PDB codes, and returns False, otherwise sends back SG.
        spacegroup_pdb = xutils.fix_spacegroup(xutils.get_spacegroup_info(cif_file))

        # Remove codes that won't run or PDB/mmCIF's that don't exist.
        if spacegroup_pdb == False:
            del self.cell_output[pdb_code]
            return False

        # Convert from cif to pdb
        # rpdb.cif_as_pdb((cif_file,))
        # time.sleep(0.1)
        conversion_proc = subprocess.Popen(["phenix.cif_as_pdb", cif_file],
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
        conversion_proc.wait()
        pdb_file = cif_file.replace(".cif", ".pdb")

        return (pdb_file, spacegroup_pdb)

    def postprocess(self):
        """Clean up after plugin action"""

        # output = {}
        # status = False
        # output_files = False
        # cell_results = False
        # failed = False

        self.tprint(arg=90, level="progress")

        # Add tar info to automr results and take care of issue if no SCA file was input.
        def check_bz2(tar):
            """
            Remove old tar's in working dir, if they exist and copy new one
            over.
            """
            if os.path.exists(os.path.join(self.working_dir, "%s.bz2" % tar)):
                os.unlink(os.path.join(self.working_dir, "%s.bz2" % tar))
            shutil.copy("%s.bz2" % tar, self.working_dir)

        # Add fields to results
        self.results["custom_structures"] = {}
        self.results["common_contaminants"] = {}
        self.results["search_results"] = {}

        # Three result types to run through
        types = (
            ("custom_structures", self.custom_structures),
            ("common_contaminants", self.common_contaminants),
            ("search_results", self.search_results)
        )

        # Run through result types
        for result_type, pdb_codes in types:
            # print result_type
            # print pdb_codes

            # Process each result
            for pdb_code in pdb_codes:

                # Get the result in question
                phaser_result = self.phaser_results[pdb_code]["results"]
                # print phaser_result

                pdb_file = phaser_result.get("pdb")
                mtz_file = phaser_result.get("mtz")
                adf_file = phaser_result.get("adf")
                peak_file = phaser_result.get("peak")

                # print pdb_file

                # Success!
                if pdb_file:
                    # in ("No solution",
                    # "Timed out",
                    # "NA",
                    # "Still running",
                    # "DL Failed"):

                    # Pack all the output files into a tar and save the path
                    os.chdir(phaser_result.get("dir"))
                    tar_file = "%s.tar" % pdb_code

                    # Speed up in testing mode.
                    if self.command["preferences"].get("test", False) and \
                    os.path.exists("%s.bz2" % tar_file):
                        check_bz2(tar_file)
                        phaser_result.update({
                            "tar": os.path.join(self.working_dir, \
                            "%s.bz2" % tar_file)})
                    else:
                        file_list = [
                            pdb_file,
                            mtz_file,
                            adf_file,
                            peak_file,
                            # pdb_file.replace(".pdb", "_refine_001.pdb"),
                            # mtz_file.replace(".mtz", "_refine_001.mtz"),
                            ]

                        # Pack up results
                        # pprint(file_list)
                        append_tar = False
                        for my_file in file_list:
                            if my_file:
                                if os.path.exists(my_file):
                                    # print "Adding %s to %s" % (my_file, tar_file)
                                    if append_tar:
                                        tar_options = "rf"
                                    else:
                                        tar_options = "cf"
                                        append_tar = True
                                    tar_process = subprocess.Popen(
                                        ["tar %s %s %s" % (
                                            tar_options,
                                            tar_file,
                                            my_file)
                                        ],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=True)
                                    tar_process.wait()

                        # Compress the archive
                        if os.path.exists(tar_file):
                            # print "Compressing the archive"
                            bzip_process = subprocess.Popen(
                                ["bzip2", "-qf", tar_file],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
                            bzip_process.wait()

                            check_bz2(tar_file)
                            phaser_result.update({
                                "tar": os.path.join(self.working_dir, "%s.bz2" \
                                % tar_file)})
                        else:
                            phaser_result.update({"tar": None})

                # NOT Success
                else:
                    pass

                # Save into common results
                self.results[result_type][pdb_code] = phaser_result

        # Cleanup my mess.
        self.clean_up()

        # Finished
        self.results["process"]["status"] = 100
        self.tprint(arg=100, level="progress")
        pprint(self.results)

        # Notify inerested party
        self.handle_return()

    def clean_up(self):
        """Clean up the working directory"""

        self.tprint("  Cleaning up", level=30, color="white")

        if self.command["preferences"].get("clean", False):
            self.logger.debug("Cleaning up Phaser files and folders")

            # Change to work dir
            os.chdir(self.working_dir)

            # Gather targets and remove
            files_to_clean = glob.glob("Phaser_*")
            for target in files_to_clean:
                shutil.rmtree(target)

    def handle_return(self):
        """Output data to consumer"""

        run_mode = self.command["preferences"]["run_mode"]

        self.write_json()

        if run_mode == "interactive":
            self.print_results()
            self.print_credits()
        elif run_mode == "server":
            pass
        elif run_mode == "subprocess":
            return self.results
        elif run_mode == "subprocess-interactive":
            self.print_results()
            self.print_credits()
            return self.results

    def print_results(self):
        """Print the results to the commandline"""

        self.tprint("\nResults", level=99, color="blue")

        def get_longest_field(pdb_codes):
            """Calculate the ongest field in a set of results"""
            longest_field = 0
            for pdb_code in pdb_codes:
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

        def print_result_line(my_result, longest_field):
            """Print the result line in the table"""

            print my_result

            self.tprint("    {:4} {:^{width}} {:^14} {:^14} {:^14} {:^14} {}".format(
                pdb_code,
                self.cell_output[pdb_code]["description"],
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

                    # Get the result in question
                    my_result = self.phaser_results[pdb_code]["results"]

                    # Print the result line
                    print_result_line(my_result, longest_field)

    def write_json(self):
        """Print out JSON-formatted result"""

        json_string = json.dumps(self.results)

        # Output to terminal?
        if self.preferences.get("json", False):
            print json_string

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

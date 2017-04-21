"""pdbquery RAPD plugin"""

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
# import argparse
# import from collections import OrderedDict
# import datetime
# import glob
import json
import logging
import multiprocessing
import os
from pprint import pprint
# import pymongo
# import re
# import redis
import shutil
import subprocess32
import sys
import time
# import unittest
import urllib2
# import uuid

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
import utils.xutils as xutils
import info

# NE-CAT REST PDB server
PDBQ_SERVER = "remote.nec.aps.anl.gov:3030"

# Software dependencies
VERSIONS = {
    "gnuplot": (
        "gnuplot 4.2",
        "gnuplot 5.0",
    )
}

def phaser_func(command):
    """
    Run phaser
    """

    # Change to correct directory
    os.chdir(command["work_dir"])

    # Setup params
    run_before = command.get("run_before", False)
    copy = command.get("copy", 1)
    resolution = command.get("res", False)
    datafile = command.get("data")
    input_pdb = command.get("pdb")
    spacegroup = command.get("sg")
    cell_analysis = command.get("cell analysis", False)
    name = command.get("name", spacegroup)
    large_cell = command.get("large", False)
    timeout = command.get("timeout", False)


    # Construct the phaser command file
    command = "phaser << eof\nMODE MR_AUTO\n"
    command += "HKLIn %s\nLABIn F=F SIGF=SIGF\n" % datafile

    # CIF or PDB?
    structure_format = "PDB"
    if input_pdb[-3:].lower() == "cif":
        structure_format = "CIF"
    command += "ENSEmble junk %s %s IDENtity 70\n" % (structure_format, input_pdb)
    command += "SEARch ENSEmble junk NUM %s\n" % copy
    command += "SPACEGROUP %s\n" % spacegroup
    if cell_analysis:
        command += "SGALTERNATIVE SELECT ALL\n"
        # Set it for worst case in orth
        command += "JOBS 8\n"
    else:
        command += "SGALTERNATIVE SELECT NONE\n"
    if run_before:
        # Picks own resolution
        # Round 2, pick best solution as long as less that 10% clashes
        command += "PACK SELECT PERCENT\n"
        command += "PACK CUTOFF 10\n"
    else:
        # For first round and cell analysis
        # Only set the resolution limit in the first round or cell analysis.
        if resolution:
            command += "RESOLUTION %s\n" % resolution
        else:
            # Otherwise it runs a second MR at full resolution!!
            # I dont think a second round is run anymore.
            # command += "RESOLUTION SEARCH HIGH OFF\n"
            if large_cell:
                command += "RESOLUTION 6\n"
            else:
                command += "RESOLUTION 4.5\n"
        command += "SEARCH DEEP OFF\n"
        # Don"t seem to work since it picks the high res limit now.
        # Get an error when it prunes all the solutions away and TF has no input.
        # command += "PEAKS ROT SELECT SIGMA CUTOFF 4.0\n"
        # command += "PEAKS TRA SELECT SIGMA CUTOFF 6.0\n"

    # Turn off pruning in 2.6.0
    command += "SEARCH PRUNE OFF\n"

    # Choose more top peaks to help with getting it correct.
    command += "PURGE ROT ENABLE ON\nPURGE ROT NUMBER 3\n"
    command += "PURGE TRA ENABLE ON\nPURGE TRA NUMBER 1\n"

    # Only keep the top after refinement.
    command += "PURGE RNP ENABLE ON\nPURGE RNP NUMBER 1\n"
    command += "ROOT %s\neof\n" % name

    # Write the phaser command file
    phaser_com_file = open("phaser.com", "w")
    phaser_com_file.writelines(command)
    phaser_com_file.close()

    # Run the phaser process
    phaser_proc = subprocess32.Popen(["sh phaser.com"],
                                     stdout=subprocess32.PIPE,
                                     stderr=subprocess32.PIPE,
                                     shell=True,
                                     preexec_fn=os.setsid)
    try:
        stdout, _ = phaser_proc.communicate(timeout=timeout)
        # print stdout
        # print stderr
        return {"pdb_code": input_pdb.replace(".pdb", ""),
                "log": stdout,
                "status": "COMPLETE"}
    except subprocess32.TimeoutExpired:
        print "  killing %d" % phaser_proc.pid
        os.killpg(os.getpgid(phaser_proc.pid), signal.SIGTERM)
        return {"pdb_code": input_pdb.replace(".pdb", ""),
                "log": "Timed out after %d seconds" % timeout,
                "status": "ERROR"}

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
    input_sg = False
    input_sg_num = 0
    laue = False
    dres = 0.0
    common = []
    volume = 0
    phaser_results = {}
    jobs = {}
    pids = {}
    pdbquery_timer = 30

    phaser_timer = 2000 #was 600 but too short for mackinnon (144,144,288,90,90,90)

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

        pprint(command)

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

        self.tprint("preprocess")

        # Check the local pdb cache Location
        if self.cif_cache:
            if not os.path.exists(self.cif_cache):
                os.makedirs(self.cif_cache)

        # Glean some information on the input file
        self.input_sg, self.cell, self.volume = xutils.get_mtz_info(self.datafile)
        self.dres = xutils.get_res(self.datafile)
        self.input_sg_num = int(xutils.convert_spacegroup(self.input_sg))
        self.laue = xutils.get_sub_groups(self.input_sg_num, "simple")

        # Throw some information into the terminal
        self.tprint("\nDataset information", color="blue", level=10)
        self.tprint("  Data file: %s" % self.datafile, level=10, color="white")
        self.tprint("  Spacegroup: %s  (%d)" % (self.input_sg, self.input_sg_num),
                    level=10,
                    color="white")
        self.tprint("  Cell: %f %f %f %f %f %f" % tuple(self.cell), level=10, color="white")
        self.tprint("  Volume: %f" % self.volume, level=10, color="white")
        self.tprint("  Resolution: %f" % self.dres, level=10, color="white")
        self.tprint("  Subgroups: %s" % self.laue, level=10, color="white")

        # Set by number of residues in AU. Ribosome (70s) is 24k.
        self.est_res_number = xutils.calc_res_number(self.input_sg,
                                                     se=False,
                                                     volume=self.volume,
                                                     sample_type=self.sample_type,
                                                     solvent_content=self.solvent_content)
        if self.est_res_number > 5000:
            self.large_cell = True
            self.phaser_timer = 3000

    def process(self):
        """Run plugin action"""

        self.tprint("process")

        if self.command["input_data"].get("pdbs", False):
            self.add_custom_pdbs()

        if self.command["preferences"].get("search", False):
            self.query_pdbq()

        if self.command["preferences"].get("contaminants", False):
            self.add_contaminants()

        phaser_results_raw = self.process_phaser()

        pprint(phaser_results_raw)
        # self.postprocess_phaser(phaser_results_raw)
        # pprint(self.phaser_results)

    def add_custom_pdbs(self):
        """Add custom pdb codes to the screen"""

        self.logger.debug("add_custom_pdbs")
        self.tprint("\nAdding input PDB codes", level=10, color="blue")

        # Query the server for information and add to self.cell_output
        for pdb_code in self.command["input_data"].get("pdbs"):

            # Query pdbq server
            response = urllib2.urlopen(urllib2.Request("http://%s/entry/%s" % \
                       (PDBQ_SERVER, pdb_code))).read()

            # Decode search result
            entry = json.loads(response)

            # Grab the description
            description = entry["message"]["_entity-pdbx_description"][0]

            # Print info to console
            self.tprint("  %s - %s" % (pdb_code, description),
                        level=10,
                        color="white")

            # Save into self.cell_output
            self.cell_output.update({
                pdb_code: {
                    "Name": description
                }
            })

    def query_pdbq(self):
        """
        Check if cell is found in PDBQ

        Places relevant pdbs into self.cell_output
        """

        self.logger.debug("query_pdbq")
        self.tprint("Searching for similar unit cells in the PDB", level=10, color="blue")

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
                # print "search_params", search_params

                # Query server
                response = urllib2.urlopen(urllib2.Request("http://%s/pdb/rest/search/" % \
                           PDBQ_SERVER, data=json.dumps(search_params))).read()

                # Decode search result
                search_results = json.loads(response)

                # Create handy Name key
                for k in search_results.keys():
                    search_results[k]["Name"] = search_results[k].pop("struct.pdbx_descriptor")

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
            if len(pdbq_results.keys()) < limit:
                counter += 1
                self.percent += 0.01
                self.logger.debug("Not enough PDB results. Going for more...")
            else:
                break

        # There will be results!
        if pdbq_results:
            self.cell_output.update(pdbq_results)
            self.tprint("  %d relevant PDB files found on the PDBQ server" % len(pdbq_results.keys()),
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
        self.common = common_contaminants.keys()

        # Remove PDBs from self.common if they were already caught by unit cell dimensions.
        for contaminant in self.common:
            if contaminant in self.cell_output:
                del common_contaminants[contaminant]
                self.common.remove(contaminant)

        # Put contaminants in list to be screened
        self.tprint("  %d contaminants added to screen" % len(common_contaminants),
                    level=10,
                    color="white")
        self.cell_output.update(common_contaminants)

    def process_phaser(self):
        """Start Phaser for input pdb"""

        self.logger.debug("process_phaser")
        self.tprint("\nStarting molecular replacement", level=30, color="blue")

        self.tprint("  Assembling Phaser runs", level=10, color="white")

        # Run through the pdbs
        commands = []
        for code in self.cell_output.keys():

            self.tprint("    %s" % code, level=30, color="white")

            l = False
            copy = 1

            # Create directory for MR
            xutils.create_folders(self.working_dir, "Phaser_%s" % code)

            # Get the structure file
            pdb_file, sg_pdb = self.get_pdb_file(code)

            # Now check all SG's
            sg_num = xutils.convert_spacegroup(sg_pdb)
            lg_pdb = xutils.get_sub_groups(sg_num, "simple")
            self.tprint("      %s spacegroup: %s (%s)" % (pdb_file, sg_pdb, sg_num),
                        level=10,
                        color="white")
            self.tprint("      subgroups: %s" % str(lg_pdb), level=10, color="white")

            # SG from data
            data_spacegroup = xutils.convert_spacegroup(self.laue, True)
            # self.tprint("      Data spacegroup: %s" % data_spacegroup, level=10, color="white")

            # Fewer mols in AU or in self.common.
            if code in self.common or float(self.laue) > float(lg_pdb):
                # if SM is lower sym, which will cause problems, since PDB is too big.
                # Need full path for copying pdb files to folders.
                pdb_info = xutils.get_pdb_info(os.path.join(os.getcwd(), pdb_file),
                                               dres=self.dres,
                                               matthews=True,
                                               cell_analysis=False,
                                               data_file=self.datafile)
                #Prune if only one chain present, b/c "all" and "A" will be the same.
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
                "work_dir": os.path.abspath(os.path.join(self.working_dir, "Phaser_%s" % code)),
                "data": self.datafile,
                "pdb": pdb_file,
                "name": code,
                "sg": data_spacegroup,
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
                    new_code = "%s_%s" % (code, chain)
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
        pool = multiprocessing.Pool(2)
        self.tprint("  Initiating Phaser runs", level=10, color="white")
        results = pool.map_async(phaser_func, commands)
        pool.close()
        pool.join()
        phaser_results = results.get()

        return phaser_results

    def get_pdb_file(self, pdb_code):
        """Retrieve/check for/uncompress/convert structure file"""

        # The cif file name
        cif_file = pdb_code.lower() + ".cif"
        # print "cif_file", cif_file
        gzip_file = cif_file+".gz"
        # print "gzip_file", gzip_file
        cached_file = False

        # There is a local cache
        if self.cif_cache:
            cached_file = os.path.join(self.cif_cache, gzip_file)
            # print "cached_file", cached_file

            # Have cached version of the file
            if os.path.exists(cached_file):
                self.tprint("      Have cached cif file %s" % gzip_file, level=10, color="white")

            # DO NOT have cached version of file
            else:
                # Get the gzipped cif file from the PDBQ server
                self.tprint("      Fetching %s" % cif_file, level=10, color="white")
                try:
                    response = urllib2.urlopen(urllib2.Request(\
                               "http://%s/pdbq/entry/get_cif/%s" % \
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
                           "http://%s/pdbq/entry/get_cif/%s" % \
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
        unzip_proc = subprocess32.Popen(["gunzip", gzip_file])
        unzip_proc.wait()

        # If mmCIF, checks if file exists or if it is super structure with
        # multiple PDB codes, and returns False, otherwise sends back SG.
        sg_pdb = xutils.fix_spacegroup(xutils.get_spacegroup_info(cif_file))

        # Remove codes that won't run or PDB/mmCIF's that don't exist.
        if sg_pdb == False:
            del self.cell_output[pdb_code]
            return False

        # Convert from cif to pdb
        conversion_proc = subprocess32.Popen(["phenix.cif_as_pdb", cif_file],
                                             stdout=subprocess32.PIPE,
                                             stderr=subprocess32.PIPE)
        conversion_proc.wait()
        pdb_file = cif_file.replace(".cif", ".pdb")

        return (pdb_file, sg_pdb)

    def postprocess(self):
        """Clean up after plugin action"""

        self.tprint("postprocess")

def get_commandline():
    """Grabs the commandline"""

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Test pdbquery plugin"
    my_parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    my_parser.add_argument("-q", "--quiet",
                           action="store_false",
                           dest="verbose",
                           help="Reduce output")

    args = my_parser.parse_args()

    # Insert logic to check or modify args here

    return args

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    if args.verbose:
        verbosity = 2
    else:
        verbosity = 1

    unittest.main(verbosity=verbosity)

    if __name__ == "__main__":

        commandline_args = get_commandline()

        main(args=commandline_args)
"""This is a docstring for this container file"""

"""
This file is part of RAPD

Copyright (C) 2010-2018, Cornell University
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

__created__ = "2010-11-10"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Development"

# Standard imports
import gzip
from multiprocessing import Pool, Process, Queue
import os
from pprint import pprint
import shutil
import subprocess
import sys
import time
import urllib2

# RAPD imports
from phaser_run import phaser_func
from plugins.subcontractors.parse import ParseOutputPhaser, setPhaserFailed
# import parse as Parse
# import summary as Summary
# from utils.communicate import rapd_send
# import utils.site as site_utils
import utils.global_vars as rglobals
from utils.text import json
from bson.objectid import ObjectId
import utils.xutils as xutils

PDBQ_SERVER = rglobals.PDBQ_SERVER

class PDBQuery(Process):

    # Settings
    # Place that structure files may be stored
    cif_cache = False
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
    cell_output = False
    cell_summary = False
    est_res_number = 0
    tooltips = False
    pdb_summary = False

    large_cell = False
    input_sg = False
    input_sg_num = 0
    laue = False
    dres = 0.0
    common = False
    volume = 0
    phaser_results = {}
    jobs = {}
    pids = {}
    pdbquery_timer = 30

    phaser_timer = 2000 #was 600 but too short for mackinnon (144,144,288,90,90,90)


    def __init__(self, command, output=None, tprint=False, logger=None):

        # If the logging instance is passed in...
        if logger:
            self.logger = logger
        else:
            # Otherwise get the logger Instance
            self.logger = logging.getLogger("RAPDLogger")
            self.logger.debug("__init__")

        # Store tprint for use throughout
        if tprint:
            self.tprint = tprint
        # Dead end if no tprint passed
        else:
            def func(arg=False, level=False, verbosity=False, color=False):
                pass
            self.tprint = func

        # Stopwatch
        self.start_time = time.time()

        # Store inputs
        self.input = command
        self.output = output
        self.logger = logger

        # pprint(command)

        # Params
        self.working_dir = self.input["directories"].get("work", os.getcwd())
        self.test = self.input["preferences"].get("test", False)
        self.sample_type = self.input["preferences"].get("type", "protein")
        self.solvent_content = self.input["preferences"].get("solvent_content", 0.55)
        self.cluster_use = self.input["preferences"].get("cluster", False)
        self.clean = self.input["preferences"].get("clean", True)
        self.gui = self.input["preferences"].get("gui", True)
        # self.controller_address = self.input[0].get("control", False)
        self.verbose = self.input["preferences"].get("verbose", False)
        self.datafile = xutils.convert_unicode(self.input["input_data"].get("datafile"))

        Process.__init__(self, name="PDBQuery")
        self.start()

    def run(self):
        """
        Convoluted path of modules to run.
        """
        self.logger.debug("PDBQuery::run")

        self.preprocess()
        self.process()
        self.postprocess()

    def preprocess(self):
        """
        Check input file and convert to mtz if neccessary.
        """

        self.logger.debug("PDBQuery::preprocess")

        # Check the local pdb cache Location
        self.cif_cache = "/tmp/rapd_cache/cif_files"
        if not os.path.exists(self.cif_cache):
            os.makedirs(self.cif_cache)

        self.input_sg, self.cell, self.volume = xutils.get_mtz_info(self.datafile)
        self.dres = xutils.get_res(self.datafile)
        self.input_sg_num = int(xutils.convert_spacegroup(self.input_sg))
        self.laue = xutils.get_sub_groups(self.input_sg_num, "simple")

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

        if self.test:
            self.logger.debug("TEST IS SET \"ON\"")

    def process(self):
        """Main processing coordination"""

        self.query_pdbq()
        self.add_common_pdb()
        phaser_results_raw = self.process_phaser()
        self.postprocess_phaser(phaser_results_raw)
        pprint(self.phaser_results)

    def query_pdbq(self):
        """
        Check if cell is found in PDBQ

        Places relevant pdbs into self.cell_output
        """

        self.logger.debug("query_pdbq")
        self.tprint("Searching for similar unit cells in the PDB", level=10, color="blue")

        def connect_pdbq(inp):
            """Query the PDBQ server"""

            _d0_ = inp
            l1 = ["a", "b", "c", "alpha", "beta", "gamma"]
            for y in range(end):
                _d_ = {}
                for x in range(len(l1)):
                    _d_[l1[x]] = [self.cell[l2[y][x]] - self.cell[l2[y][x]] * self.percent/2,
                                  self.cell[l2[y][x]] + self.cell[l2[y][x]] *self.percent/2]
                # Query server
                response = urllib2.urlopen(urllib2.Request("%s/cell_search/" % \
                           PDBQ_SERVER, data=json.dumps(_d_))).read()
                j = json.loads(response)
                for k in j.keys():
                    j[k]["Name"] = j[k].pop("struct.pdbx_descriptor")
                _d0_.update(j)
            return _d0_

        def limitOut(inp):
            """Filter repeates out of query"""
            l = inp.keys()[:i+1]
            for p in inp.keys():
                if l.count(p) == 0:
                    del inp[p]
            return inp

        pdbq_results = {}
        permute = False
        end = 1
        l2 = [(0, 1, 2, 3, 4, 5), (1, 2, 0, 4, 5, 3), (2, 0, 1, 5, 3, 4)]
        # Check for orthorhombic
        if self.laue == "16":
            permute = True
        # Check monoclinic when Beta is near 90.
        if self.laue in ("3", "5"):
            if 89.0 < self.cell[4] < 91.0:
                permute = True
        if permute:
            end = len(l2)
        # Limit the minimum number of results
        no_limit = False
        if self.cluster_use:
            if self.large_cell:
                i = 10
            elif permute:
                i = 60
            else:
                no_limit = True
                i = 40
        else:
            i = 8
        counter = 0

        # Limit the unit cell difference to 25%. Also stops it if errors are received.
        while counter < 25:
            self.tprint("  Querying server at %s" % PDBQ_SERVER,
                        level=20,
                        color="white")
            pdbq_results = connect_pdbq(pdbq_results)
            if len(pdbq_results.keys()) != 0:
                for line in pdbq_results.keys():
                    # remove anything bigger than 4 letters
                    if len(line) > 4:
                        del pdbq_results[line]

                # Do not limit number of results if many models come out really close in cell
                # dimensions.
                if counter in (0, 1):
                    #Limit output
                    if no_limit == False:
                        pdbq_results = limitOut(pdbq_results)
                else:
                    pdbq_results = limitOut(pdbq_results)
            if len(pdbq_results.keys()) < i:
                counter += 1
                self.percent += 0.01
                self.logger.debug("Not enough PDB results. Going for more...")
            else:
                break
        if len(pdbq_results.keys()) > 0:
            self.cell_output = pdbq_results
            self.tprint("  %d relevant PDB files found on the PDBQ server" % len(pdbq_results.keys()),
                        level=50,
                        color="white")
        else:
            self.cell_output = {}
            self.logger.debug("Failed to find pdb with similar cell.")
            self.tprint("No relevant PDB files found on the PDBQ server",
                        level=50,
                        color="red")

    def add_common_pdb(self):
        """
        Add common PDB contaminants to the search list.

        Adds files to self.cell_output
        """
        self.logger.debug("add_common_pdb")
        self.tprint("  Adding common contaminants to PDB screen")

        # Dict with PDB codes for common contaminants.
        common_contaminants = {
            "1E1O": {"Name": "LYSYL-TRNA SYNTHETASE, HEAT INDUCIBLE",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/e1/1e1o.cif"},
            "1ESO": {"Name": "CU, ZN SUPEROXIDE DISMUTASE",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/es/1eso.cif"},
            "1G6N": {"Name": "CATABOLITE GENE ACTIVATOR PROTEIN",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/g6/1g6n.cif"},
            "1GGE": {"Name": "PROTEIN (CATALASE HPII)",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/gg/1gge.cif"},
            "1I6P": {"Name": "CARBONIC ANHYDRASE",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/i6/1i6p.cif"},
            "1OEE": {"Name": "HYPOTHETICAL PROTEIN YODA",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/oe/1oee.cif"},
            "1OEL": {"Name": "GROEL (HSP60 CLASS)",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/oe/1oel.cif"},
            "1PKY": {"Name": "PYRUVATE KINASE",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/pk/1pky.cif"},
            "1X8F": {"Name": "2-dehydro-3-deoxyphosphooctonate aldolase",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/x8/1x8f.cif"},
            "1Z7E": {"Name": "protein ArnA",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/z7/1z7e.cif"},
            "2JGD": {"Name": "2-OXOGLUTARATE DEHYDROGENASE E1 COMPONENT",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/jg/2jgd.cif"},
            "2QZS": {"Name": "glycogen synthase",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/qz/2qzs.cif"},
            "2VF4": {"Name": "GLUCOSAMINE--FRUCTOSE-6-PHOSPHATE AMINOTRANSFERASE",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/vf/2vf4.cif"},
            "2Y90": {"Name": "PROTEIN HFQ",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/y9/2y90.cif"},
            "3CLA": {"Name": "TYPE III CHLORAMPHENICOL ACETYLTRANSFERASE",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/cl/3cla.cif"},
            "4UEJ": {"Name": "GALACTITOL-1-PHOSPHATE 5-DEHYDROGENASE",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/ue/4uej.cif"},
            "4QEQ": {"Name": "Lysozyme C",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/qe/4qeq.cif"},
            "2I6W": {"Name": "AcrB",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/i6/2i6w.cif"},
            "1NEK": {"Name": "Succinate dehydrogenase flavoprotein subunit",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/ne/1nek.cif"},
            "1TRE": {"Name": "TRIOSEPHOSPHATE ISOMERASE",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/tr/1tre.cif"},
            "1I40": {"Name": "INORGANIC PYROPHOSPHATASE",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/i4/1i40.cif"},
            "2P9H": {"Name": "Lactose operon repressor",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/p9/2p9h.cif"},
            "1PHO": {"Name": "PHOSPHOPORIN",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/ph/1pho.cif"},
            "1BTL": {"Name": "BETA-LACTAMASE",
                     "path": "/gpfs5/users/necat/rapd/pdbq/pdb/bt/1btl.cif"},
        }

        # Save these codes in a separate list so they can be separated in the Summary.
        self.common = common_contaminants.keys()

        # Remove PDBs from self.common if they were already caught by unit cell dimensions.
        for line in common_contaminants.keys():
            if self.cell_output.keys().count(line):
                del common_contaminants[line]
                self.common.remove(line)
        self.cell_output.update(common_contaminants)

    def process_phaser(self):
        """Start Phaser for input pdb"""

        self.logger.debug("process_phaser")
        self.tprint("\nStarting molecular replacement", level=30, color="blue")

        # POOL = Pool(processes=4)
        #
        # def launch_job(inp):
        #     """Run a phaser process and retrieve results"""
        #
        #     print "launch_job", inp
        #
        #     queue = Queue()
        #     result = POOL.apply_async(phaser_func, (inp, queue, self.logger))
        #
        #     # queue = Queue()
        #     # job = Process(target=RunPhaser, args=(inp, queue, self.logger))
        #     # job.start()
        #     # # Get results
        #     # queue.get()  # For the log I don"t use
        #     # self.jobs[job] = inp["name"]
        #     # self.pids[inp["name"]] = queue.get()

        # Run through the pdbs
        self.tprint("  Assembling Phaser runs", level=10, color="white")
        commands = []
        for code in self.cell_output.keys():

            self.tprint("    %s" % code, level=30, color="white")

            l = False
            copy = 1

            # Create directory for MR
            xutils.create_folders(self.working_dir, "Phaser_%s" % code)

            # The cif file name
            cif_file = os.path.basename(self.cell_output[code].get("path"))
            # print "cif_file", cif_file
            gzip_file = cif_file+".gz"
            # print "gzip_file", gzip_file
            cached_file = False

            # Is the cif file in the local cache?
            if self.cif_cache:
                cached_file = os.path.join(self.cif_cache, gzip_file)
                # print "cached_file", cached_file
                if os.path.exists(cached_file):
                    self.tprint("      Have cached cif file %s" % gzip_file, level=10, color="white")

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
                        continue

                    # Write the  gzip file
                    with open(cached_file, "wb") as outfile:
                        outfile.write(response)

                # Copy the gzip file to the cwd
                # print "Copying %s to %s" % (cached_file, os.path.join(os.getcwd(), gzip_file))
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
                    continue

                # Write the  gzip file
                with open(gzip_file, "wb") as outfile:
                    outfile.write(response)

            # Uncompress the gzipped file
            unzip_proc = subprocess.Popen(["gunzip", gzip_file])
            unzip_proc.wait()

            # If mmCIF, checks if file exists or if it is super structure with
            # multiple PDB codes, and returns False, otherwise sends back SG.
            sg_pdb = xutils.fix_spacegroup(xutils.get_spacegroup_info(cif_file))

            # Remove codes that won't run or PDB/mmCIF's that don't exist.
            if sg_pdb == False:
                del self.cell_output[code]
                continue

            # Convert from cif to pdb
            conversion_proc = subprocess.Popen(["phenix.cif_as_pdb", cif_file],
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE)
            conversion_proc.wait()
            cif_file = cif_file.replace(".cif", ".pdb")

            # Now check all SG's
            sg_num = xutils.convert_spacegroup(sg_pdb)
            lg_pdb = xutils.get_sub_groups(sg_num, "simple")
            self.tprint("      %s spacegroup: %s (%s)" % (cif_file, sg_pdb, sg_num),
                        level=10,
                        color="white")
            self.tprint("    subgroups: %s" % str(lg_pdb), level=10, color="white")

            # SG from data
            data_spacegroup = xutils.convert_spacegroup(self.laue, True)
            # self.tprint("      Data spacegroup: %s" % data_spacegroup, level=10, color="white")

            # Fewer mols in AU or in self.common.
            if code in self.common or float(self.laue) > float(lg_pdb):
                # if SM is lower sym, which will cause problems, since PDB is too big.
                # Need full path for copying pdb files to folders.
                pdb_info = xutils.get_pdb_info(os.path.join(os.getcwd(), cif_file),
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
                pdb_info = xutils.get_pdb_info(cif_file=cif_file,
                                               dres=self.dres,
                                               matthews=True,
                                               cell_analysis=True,
                                               data_file=self.datafile)
                copy = pdb_info["all"]["NMol"]

            # Same number of mols in AU.
            else:
                pdb_info = xutils.get_pdb_info(cif_file=cif_file,
                                               dres=self.dres,
                                               matthews=False,
                                               cell_analysis=True,
                                               data_file=self.datafile)

            job_description = {
                "work_dir": os.path.abspath(os.path.join(self.working_dir, "Phaser_%s" % code)),
                "data": self.datafile,
                "pdb": cif_file,
                "name": code,
                "verbose": self.verbose,
                "sg": data_spacegroup,
                "copy": copy,
                "test": self.test,
                "cluster": self.cluster_use,
                "cell analysis": True,
                "large": self.large_cell,
                "res": xutils.set_phaser_res(pdb_info["all"]["res"], self.large_cell, self.dres),
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

        # pprint(commands)
        # phaser_results = []
        # for command in commands:
        #     phaser_results.append(phaser_func(command))

        # Run in pool
        pool = Pool(2)
        self.tprint("    Initiating Phaser runs", level=10, color="white")
        results = pool.map_async(phaser_func, commands)
        pool.close()
        pool.join()
        phaser_results = results.get()

        return phaser_results

    def process_refine(self, inp):
        """
        Run phenix.refine rigid-body on solution. My old boss wanted this. Will be incorporated
        into future ligand finding pipeline. This can be enabled at top of script, but takes extra time.
        """
        if self.verbose:
            self.logger.debug("PDBQuery::process_refine")

        try:
            pdb = "%s.1.pdb" % inp
            info = xutils.getPDBInfo(self, pdb, False)
            command = "phenix.refine %s %s strategy=tls+rigid_body refinement.input.xray_data.labels=IMEAN,SIGIMEAN " % (pdb, self.datafile)
            command += "refinement.main.number_of_macro_cycles=1 nproc=2"
            chains = [chain for chain in info.keys() if chain != "all"]
            for chain in chains:
                command += ' refine.adp.tls="chain %s"' % chain
            if self.test == False:
                xutils.processLocal((command, "rigid.log"), self.logger)
            else:
                os.system("touch rigid.log")

        except:
            self.logger.exception("**ERROR in PDBQuery.process_refine**")

    def postprocess_phaser(self, phaser_results):
        """
        Look at Phaser results.
        """

        self.logger.debug("postprocess_phaser")

        for phaser_result in phaser_results:

            pprint(phaser_result)

            pdb_code = phaser_result["pdb_code"]
            phaser_lines = phaser_result["log"].split("\n")

            nosol = False

            data = ParseOutputPhaser(self, phaser_lines)
            pprint(data)
            if data["AutoMR sg"] in ("No solution", "Timed out", "NA", "DL FAILED"):
                nosol = True
            else:
                # Check for negative or low LL-Gain.
                if float(data["AutoMR gain"]) < 200.0:
                    nosol = True
            if nosol:
                self.phaser_results[pdb_code] = {"AutoMR results": \
                    setPhaserFailed("No solution")}
            else:
                self.phaser_results[pdb_code] = {"AutoMR results":data}

    def run_queue(self):
        """
        queue system.
        """

        self.logger.debug("PDBQuery::run_queue")

        try:
            timed_out = False
            timer = 0
            if self.jobs != {}:
                jobs = self.jobs.keys()
                while len(jobs) != 0:
                    for job in jobs:
                        if job.is_alive() == False:
                            jobs.remove(job)
                            code = self.jobs.pop(job)
                            xutils.folders(self, "Phaser_%s" % code)
                            new_jobs = []
                            if self.test == False:
                                del self.pids[code]
                            #if self.verbose:
                            self.logger.debug("Finished Phaser on %s" % code)
                            p = self.postprocess_phaser(code)
                            # if p.count("rigid"):
                            #     if os.path.exists("rigid.log") == False:
                            #         j = Process(target=self.process_refine, args=(code, ))
                            #         j.start()
                            #         new_jobs.append(j)
                            #         if self.test:
                            #             time.sleep(5)
                            # if p.count("ADF"):
                            #     if os.path.exists("adf.com") == False:
                            #         j = Process(target=xutils.calcADF, args=(self, code))
                            #         j.start()
                            #         new_jobs.append(j)
                            # if len(new_jobs) > 0:
                            #     for j1 in new_jobs:
                            #         self.jobs[j1] = code
                            #         jobs.append(j1)
                    time.sleep(0.2)
                    timer += 0.2
                    if self.phaser_timer:
                        if timer >= self.phaser_timer:
                            timed_out = True
                            break
                if timed_out:
                    for j in self.jobs.values():
                        if self.pids.has_key(j):
                            if self.cluster_use:
                                # TODO
                                # BLspec.killChildrenCluster(self,self.pids[j])
                                pass
                            else:
                                xutils.killChildren(self, self.pids[j])
                        if self.phaser_results.has_key(j) == False:
                            self.phaser_results[j] = {"AutoMR results": Parse.setPhaserFailed("Timed out")}
                    if self.verbose:
                        self.logger.debug("PDBQuery timed out.")
                        print "PDBQuery timed out."
            if self.verbose:
                self.logger.debug("PDBQuery.run_queue finished.")

        except:
            self.logger.exception("**ERROR in PDBQuery.run_queue**")

    def print_info(self):
        """
        Print information regarding programs utilized by RAPD
        """
        if self.verbose:
            self.logger.debug("PDBQuery::print_info")

        self.logger.debug("RAPD now using Phenix")
        self.logger.debug("=======================")
        self.logger.debug("RAPD developed using Phenix")
        self.logger.debug("Reference: Adams PD, et al.(2010) Acta Cryst. D66:213-221")
        self.logger.debug("Website: http://www.phenix-online.org/\n")
        self.logger.debug("RAPD developed using Phaser")
        self.logger.debug("Reference: McCoy AJ, et al.(2007) J. Appl. Cryst. 40:658-674.")
        self.logger.debug("Website: http://www.phenix-online.org/documentation/phaser.htm\n")

    def postprocess(self):
        """
        Put everything together and send back dict.
        """
        if self.verbose:
            self.logger.debug("PDBQuery::postprocess")

        output = {}
        status = False
        output_files = False
        cell_results = False
        failed = False

        # Add tar info to automr results and take care of issue if no SCA file was input.
        try:
            def check_bz2(tar):
                # Remove old tar's in working dir, if they exist and copy new one over.
                if os.path.exists(os.path.join(self.working_dir, "%s.bz2" % tar)):
                    os.system("rm -rf %s" % os.path.join(self.working_dir, "%s.bz2" % tar))
                shutil.copy("%s.bz2" % tar, self.working_dir)

            if self.cell_output:
                for pdb in self.phaser_results.keys():
                    pdb_file = self.phaser_results[pdb].get("AutoMR results").get("AutoMR pdb")
                    mtz_file = self.phaser_results[pdb].get("AutoMR results").get("AutoMR mtz")
                    adf_file = self.phaser_results[pdb].get("AutoMR results").get("AutoMR adf")
                    peak_file = self.phaser_results[pdb].get("AutoMR results").get("AutoMR peak")
                    if pdb_file not in ("No solution", "Timed out", "NA", "Still running", "DL Failed"):
                        #pack all the output files into a tar and save the path
                        os.chdir(self.phaser_results[pdb].get("AutoMR results").get("AutoMR dir"))
                        tar = "%s.tar" % pdb
                        #Speed up in testing mode.
                        if os.path.exists("%s.bz2" % tar):
                            check_bz2(tar)
                            self.phaser_results[pdb].get("AutoMR results").update({"AutoMR tar": os.path.join(self.working_dir, "%s.bz2" % tar)})
                        else:
                            l = [pdb_file, mtz_file, adf_file, peak_file, pdb_file.replace(".pdb", "_refine_001.pdb"), mtz_file.replace(".mtz", "_refine_001.mtz")]
                            for p in l:
                                if os.path.exists(p):
                                    os.system("tar -rf %s %s" % (tar, p))
                            if os.path.exists(tar):
                                os.system("bzip2 -qf %s" % tar)
                                check_bz2(tar)
                                self.phaser_results[pdb].get("AutoMR results").update({"AutoMR tar": os.path.join(self.working_dir, "%s.bz2" % tar)})
                            else:
                                self.phaser_results[pdb].get("AutoMR results").update({"AutoMR tar": "None"})
                    #Save everthing into one dict
                    if pdb in self.cell_output.keys():
                        self.phaser_results[pdb].update(self.cell_output[pdb])
                    else:
                        self.phaser_results[pdb].update(self.cell_output[pdb[:pdb.rfind("_")]])
                cell_results = {"Cell analysis results":self.phaser_results}
            else:
                cell_results = {"Cell analysis results":"None"}
        except:
            self.logger.exception("**Could not AutoMR results in postprocess.**")
            cell_results = {"Cell analysis results":"FAILED"}
            failed = True

        try:
            # Create the output html file
            os.chdir(self.working_dir)
            Summary.summaryCell(self, "pdbquery")
            self.html_summary()
            if self.gui:
                sl = "jon_summary_cell.php"
            else:
                sl = "jon_summary_cell.html"
            if os.path.exists(os.path.join(self.working_dir, sl)):
                output["Cell summary html"] = os.path.join(self.working_dir, sl)
            else:
                output["Cell summary html"] = "None"
        except:
            self.logger.exception("**Could not update path of shelx summary html file.**")
            output["Cell summary html"] = "FAILED"
            failed = True

        try:
            output_files = {"Output files":output}
        except:
            self.logger.exception("**Could not update the output dict.**")

        #Get proper status.
        if failed:
            status = {"status":"FAILED"}
            self.clean = False
        else:
            status = {"status":"SUCCESS"}

        #Put all the result dicts from all the programs run into one resultant dict and pass it along the pipe.
        try:
            results = {}
            if status:
                results.update(status)
            if cell_results:
                results.update(cell_results)
            if output_files:
                results.update(output_files)
            if results:
                self.input.append(results)
            if self.output != None:
                self.output.put(results)
            else:
                if self.gui:
                #   self.sendBack2(self.input)
                    rapd_send(self.controller_address, self.input)
        except:
            self.logger.exception("**Could not send results to pipe**")

        try:
            # Cleanup my mess.
            if self.clean:
                os.chdir(self.working_dir)
                os.system("rm -rf Phaser_* temp.mtz")
                if self.verbose:
                    self.logger.debug("Cleaning up Phaser files and folders")
        except:
            self.logger.exception("**Could not cleanup**")

        # Say job is complete.
        run_time = round(time.time() - self.start_time)
        self.logger.debug(50 * "-")
        self.logger.debug("RAPD PDBQuery complete.")
        self.logger.debug("Total elapsed time: %s seconds" % run_time)
        self.logger.debug(50*"-")
        if self.output == None:
            print 50*"-"
            print "\nRAPD PDBQuery complete."
            print "Total elapsed time: %s seconds" % run_time
            print 50*"-"

    def html_summary(self):
        """
        Create HTML/php files for autoindex/strategy output results.
        """
        if self.verbose:
            self.logger.debug("PDBQuery::html_summary")

        try:
            if self.gui:
                jon_summary = open("jon_summary_cell.php", "w")
            else:
                jon_summary = open("jon_summary_cell.html", "w")
            #jon_summary.write(xutils.getHTMLHeader(self,"phaser"))
            jon_summary.write(xutils.getHTMLHeader(self, "pdbquery"))
            jon_summary.write("%6s$(document).ready(function() {\n" % "")
            if self.gui:
                jon_summary.write("%8s$('button').button(); \n" % "")
            if self.cell_summary:
                jon_summary.write("%8s$('#pdbquery-cell').dataTable({\n" % "")
                jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bSort": false,\n%11s"bAutoWidth": false });\n' % (5*("", )))
            if self.search_common:
                jon_summary.write("%8s$('#pdbquery-cc').dataTable({\n" % "")
                jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bSort": false,\n%11s"bAutoWidth": false });\n' % (5*("", )))
            if self.pdb_summary:
                jon_summary.write("%8s$('#pdbquery-pdb').dataTable({\n" % "")
                jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bSort": false,\n%11s"bAutoWidth": false });\n' % (5*("", )))
            if self.tooltips:
                jon_summary.writelines(self.tooltips)
            jon_summary.write('%6s});\n%4s</script>\n%2s</head>\n%2s<body id="dt_example">\n'%(4*("",)))
            if self.cell_summary:
                jon_summary.writelines(self.cell_summary)
            if self.pdb_summary:
                jon_summary.writelines(self.pdb_summary)
            jon_summary.write("%2s</body>\n</html>\n" % "")
            jon_summary.close()

        except:
            self.logger.exception("**ERROR in PDBQuery.html_summary**")

        # Print attributions
        self.print_info()

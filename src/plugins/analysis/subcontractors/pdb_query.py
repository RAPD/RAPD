"""This is a docstring for this container file"""

"""
This file is part of RAPD

Copyright (C) 2010-2017, Cornell University
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
import json
from multiprocessing import Process, Queue
import os
from pprint import pprint
import shutil
import sys
import time
import urllib2

# RAPD imports
from agents.rapd_agent_phaser import RunPhaser
# import parse as Parse
# import summary as Summary
# from utils.communicate import rapd_send
import utils.xutils as xutils

PDBQ_SERVER = "remote.nec.aps.anl.gov:3030"

class PDBQuery(Process):

    # Settings
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


    def __init__(self, command, output=None, tprint=False, logger=False):

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

        pprint(command)

        # Params
        self.working_dir = self.input["directories"].get("work", os.getcwd())
        self.test = self.input["preferences"].get("test", False)
        self.sample_type = self.input["preferences"].get("type", "protein")
        self.solvent_content = self.input["preferences"].get("solvent_content", 0.55)
        self.cluster_use = self.input["preferences"].get("cluster", True)
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

        # try:
        self.input_sg, self.cell, self.volume = xutils.get_mtz_info(self.datafile)
        self.dres = xutils.get_res(self.datafile)
        self.input_sg_num = int(xutils.convert_sg(self.input_sg))
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
        sys.exit()

        if self.search_common:
            self.process_common_pdb()

        self.process_phaser()
        self.run_queue()

    def query_pdbq(self):
        """Check if cell is found in PDBQ"""

        self.logger.debug("query_pdbq")
        self.tprint("Searching for similar unit cells in the PDB", level=10, color="blue")

        def connect_pdbq(inp):
            """
            Query the PDBQ server

            Places relevant pdbs into self.cell_output
            """
            _d0_ = inp
            l1 = ["a", "b", "c", "alpha", "beta", "gamma"]
            for y in range(end):
                _d_ = {}
                for x in range(len(l1)):
                    _d_[l1[x]] = [self.cell[l2[y][x]] - self.cell[l2[y][x]] * self.percent/2,
                                  self.cell[l2[y][x]] + self.cell[l2[y][x]] *self.percent/2]
                # Query server
                response = urllib2.urlopen(urllib2.Request("http://%s/pdb/rest/search/" % \
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
            if 89.0 < float(self.cell2[4]) < 91.0:
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

    def process_common_pdb(self):
        """
        Add common PDB contaminants to the search list.
        """
        if self.verbose:
            self.logger.debug("PDBQuery::process_common_pdb")

        try:
            #Dict with PDB codes for common contaminants.
            d = {
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
            self.common = d.keys()

            # Remove PDBs from self.common if they were already caught by unit cell dimensions.
            for line in d.keys():
                if self.cell_output.keys().count(line):
                    del d[line]
                    self.common.remove(line)
            self.cell_output.update(d)

        except:
            self.logger.exception("**ERROR in PDBQuery.process_common_pdb**")


    def process_phaser(self):
        """
        Start Phaser for input pdb.
        """
        if self.verbose:
            self.logger.debug("PDBQuery::process_phaser")

        def launch_job(inp):
            queue = Queue()
            job = Process(target=RunPhaser, args=(inp, queue, self.logger))
            job.start()
            queue.get()  # For the log I don"t use
            self.jobs[job] = inp["name"]
            self.pids[inp["name"]] = queue.get()

        try:
            for code in self.cell_output.keys():
              #for code in ["4ER2"]:
                l = False
                copy = 1
                xutils.folders(self, "Phaser_%s" % code)
                f = os.path.basename(self.cell_output[code].get("path"))
                #Check if symlink exists and create if not.
                if os.path.exists(f) == False:
                    os.symlink(self.cell_output[code].get("path"), f)
                #If mmCIF, checks if file exists or if it is super structure with
                #multiple PDB codes, and returns False, otherwise sends back SG.
                sg_pdb = xutils.fixSG(self, xutils.getSGInfo(self, f))
                #Remove codes that won't run or PDB/mmCIF's that don't exist.
                if sg_pdb == False:
                    del self.cell_output[code]
                    continue
                #**Now check all SG's**
                lg_pdb = xutils.subGroups(self, xutils.convertSG(self, sg_pdb), "simple")
                #SG from data
                sg = xutils.convertSG(self, self.laue, True)
                #Fewer mols in AU or in self.common.
                if code in self.common or float(self.laue) > float(lg_pdb):
                    #if SM is lower sym, which will cause problems, since PDB is too big.
                    #Need full path for copying pdb files to folders.
                    pdb_info = xutils.getPDBInfo(self, os.path.join(os.getcwd(), f))
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
                #More mols in AU
                elif float(self.laue) < float(lg_pdb):
                    pdb_info = xutils.getPDBInfo(self, f, True, True)
                    copy = pdb_info["all"]["NMol"]
                #Same number of mols in AU.
                else:
                    pdb_info = xutils.getPDBInfo(self, f, False, True)

                d = {"data":self.datafile, "pdb":f, "name":code, "verbose":self.verbose, "sg":sg,
                     "copy":copy, "test":self.test, "cluster":self.cluster_use, "cell analysis":True,
                     "large":self.large_cell, "res":xutils.setPhaserRes(self, pdb_info["all"]["res"]),
                    }

                if l == False:
                    launch_job(d)
                else:
                    d1 = {}
                    for chain in l:
                        new_code = "%s_%s" % (code, chain)
                        xutils.folders(self, "Phaser_%s" % new_code)
                        d.update({"pdb":pdb_info[chain]["file"], "name":new_code, "copy":pdb_info[chain]["NMol"],
                                  "res":xutils.setPhaserRes(self, pdb_info[chain]["res"])})
                        launch_job(d)

        except:
            self.logger.exception("**ERROR in PDBQuery.process_phaser**")

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

    def postprocess_phaser(self, inp):
        """
        Look at Phaser results.
        """
        if self.verbose:
            self.logger.debug("PDBQuery::postprocess_phaser")

        try:
            nosol = False
            output = []
            if os.path.exists("phaser.log"):
                #For older versions of Phaser
                #data = Parse.ParseOutputPhaser(self,open("%s.sum"%inp,"r").readlines())
                data = Parse.ParseOutputPhaser(self, open("phaser.log", "r").readlines())
                if data["AutoMR sg"] in ("No solution", "Timed out", "NA", "DL FAILED"):
                    nosol = True
                else:
                    #Check for negative or low LL-Gain.
                    if float(data["AutoMR gain"]) < 200.0:
                        nosol = True
                if nosol:
                    self.phaser_results[inp] = {"AutoMR results":Parse.setPhaserFailed("No solution")}
                else:
                    self.phaser_results[inp] = {"AutoMR results":data}
                if self.rigid:
                    if nosol:
                        #Tells Queue job is finished
                        os.system("touch rigid.com")
                    else:
                        output.append("rigid")
                if self.adf:
                    if nosol:
                        #Tells Queue job is finished
                        os.system("touch adf.com")
                    else:
                        #Put path of map and peaks pdb in results
                        self.phaser_results[inp].get("AutoMR results").update({"AutoMR adf": "%s_adf.map" % inp})
                        self.phaser_results[inp].get("AutoMR results").update({"AutoMR peak":"%s_adf_peak.pdb" % inp})
                        output.append("ADF")
            elif self.test:
                #Set output for Phaser runs that didn't actually run.
                self.phaser_results[inp] = {"AutoMR results":Parse.setPhaserFailed("No solution")}

            return output

        except:
            self.logger.exception("**ERROR in PDBQuery.postprocess_phaser**")

    def run_queue(self):
        """
        queue system.
        """
        if self.verbose:
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
                            if p.count("rigid"):
                                if os.path.exists("rigid.log") == False:
                                    j = Process(target=self.process_refine, args=(code, ))
                                    j.start()
                                    new_jobs.append(j)
                                    if self.test:
                                        time.sleep(5)
                            if p.count("ADF"):
                                if os.path.exists("adf.com") == False:
                                    j = Process(target=xutils.calcADF, args=(self, code))
                                    j.start()
                                    new_jobs.append(j)
                            if len(new_jobs) > 0:
                                for j1 in new_jobs:
                                    self.jobs[j1] = code
                                    jobs.append(j1)
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

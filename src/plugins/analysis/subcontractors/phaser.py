"""This is a docstring for this file"""

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

__created__ = "2010-09-07"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
# import from collections import OrderedDict
# import datetime
# import glob
# import json
# import logging
# import multiprocessing
# import os
# import pprint
# import pymongo
# import re
# import redis
# import shutil
# import subprocess
import sys
# import time
# import unittest
# import uuid

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils

# Software dependencies
VERSIONS = {
# "eiger2cbf": ("160415",)
}

class RunPhaser(Process):
    def __init__(self, inp, output=False, logger=None):
        """
        #The minimum input
        {"input":{"data":self.datafile,"pdb":self.input_pdb,"sg":self.sg,}
         "output","logger}
        """
        logger.info("RunPhaser.__init__")
        self.input = inp
        self.output = output
        self.logger = logger
        # setup params
        self.run_before = self.input.get("run_before", False)
        self.verbose = self.input.get("verbose", False)
        self.copy = self.input.get("copy", 1)
        self.res = self.input.get("res", False)
        self.test = self.input.get("test", False)
        self.cluster_use = self.input.get("cluster", True)
        self.datafile = self.input.get("data")
        self.input_pdb = self.input.get("pdb")
        self.sg = self.input.get("sg")
        self.ca = self.input.get("cell analysis", False)
        #self.mwaa = self.input.get("mwaa", False)
        #self.mwna = self.input.get("mwna", False)
        self.n = self.input.get("name", self.sg)
        self.large_cell = self.input.get("large", False)

        Process.__init__(self, name="RunPhaser")
        self.start()

    def run(self):
        """
        Convoluted path of modules to run.
        """
        if self.verbose:
            self.logger.debug('RunPhaser::run')
        self.preprocess()
        self.process()

    def preprocess(self):
        """
        Setup Phaser input script.
        """
        if self.verbose:
            self.logger.debug("RunPhaser::preprocess")

        try:
            ft = "PDB"
            command  = "phaser << eof\nMODE MR_AUTO\n"
            command += "HKLIn %s\nLABIn F=F SIGF=SIGF\n" % self.datafile
            if self.input_pdb[-3:].lower() == "cif":
                ft = "CIF"
            if os.path.exists(self.input_pdb):
                command += "ENSEmble junk %s %s IDENtity 70\n" % (ft, self.input_pdb)
            else:
                command += "ENSEmble junk %s ../%s IDENtity 70\n" % (ft, self.input_pdb)
            """
            #Makes LL-gain scores ~10% higher, but can decrease if residues are mis-identified. Not worth it.
            if self.mwaa:
              if self.mwaa > 0:
                command += "COMPosition PROTein MW "+str(self.input["mwaa"])+" NUM "+str(self.input["copy"])+"\n"
            if self.mwna:
              if self.mwna > 0:
                command += "COMPosition NUCLEIC MW "+str(self.input["mwna"])+" NUM "+str(self.input["copy"])+"\n"
            """
            command += "SEARch ENSEmble junk NUM %s\n" % self.copy
            command += "SPACEGROUP %s\n" % self.sg
            if self.ca:
                command += "SGALTERNATIVE SELECT ALL\n"
                # Set it for worst case in orth
                command += "JOBS 8\n"
            else:
                command += "SGALTERNATIVE SELECT NONE\n"
            if self.run_before:
                # Picks own resolution
                # Round 2, pick best solution as long as less that 10% clashes
                command += "PACK SELECT PERCENT\n"
                command += "PACK CUTOFF 10\n"
            else:
                # For first round and cell analysis
                # Only set the resolution limit in the first round or cell analysis.
                if self.res:
                    command += "RESOLUTION %s\n" % self.res
                else:
                    # Otherwise it runs a second MR at full resolution!!
                    # I dont think a second round is run anymore.
                    # command += "RESOLUTION SEARCH HIGH OFF\n"
                    if self.large_cell:
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
            command += "ROOT %s\neof\n" % self.n
            f = open("phaser.com", "w")
            f.writelines(command)
            f.close()
            if self.output:
                self.output.put(command)

        except:
            self.logger.exception("**Error in RunPhaser.preprocess**")

    def process(self):
        """
        Run Phaser and pass back the pid.
        """
        if self.verbose:
            self.logger.debug("RunPhaser::process")

        try:
            command = "tcsh phaser.com"
            if self.test:
                if self.output:
                    import random
                    self.output.put("junk%s" % random.randint(0, 5000))
            else:
                # FALSE
                if False: # self.cluster_use:
                    if self.large_cell:
                        q = "high_mem.q"
                    else:
                        q = "all.q"
                    if self.output:
                        queue = Queue()
                        # Process(target=Utils.processCluster,args=(self,(command,"phaser.log",q),queue)).start()
                        # TODO
                        Process(target=BLspec.processCluster, args=(self, (command, "phaser.log", q), queue)).start()
                        self.output.put(queue.get())
                    else:
                        # Process(target=Utils.processCluster,args=(self,(command,"phaser.log",q))).start()
                        # TODO
                        Process(target=BLspec.processCluster, args=(self, (command, "phaser.log", q))).start()
                else:
                    if self.output:
                        queue = Queue()
                        Process(target=Utils.processLocal, args=((command, "phaser.log"), self.logger, queue)).start()
                        self.output.put(queue.get())
                    else:
                        Process(target=Utils.processLocal, args=((command, "phaser.log"), self.logger)).start()
        except:
          self.logger.exception("**Error in RunPhaser.process**")
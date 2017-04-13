"""
Phaser methods for pre-running to facilitate full phaser runs

NB - These methods must be run using phenix.python NOT rapd.python
"""

"""
This file is part of RAPD

Copyright (C) 2009-2017, Cornell University
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

__created__ = "2009-07-08"
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

# Phenix imports
import phaser

def run_phaser_module(args):
    """
    Run separate module of Phaser to get results before running full job.
    Setup so that I can read the data in once and run multiple modules.
    """

    print "run_phaser_module"

    res = 0.0
    z = 0
    sc = 0.0

    def run_ellg():
        print "run_ellg"
        res0 = 0.0
        i0 = phaser.InputMR_ELLG()
        i0.setSPAC_HALL(r.getSpaceGroupHall())
        i0.setCELL6(r.getUnitCell())
        i0.setMUTE(True)
        i0.setREFL_DATA(r.getDATA())
        i0.addENSE_PDB_ID("junk", args.pdb_file, 0.7)
        #i.addSEAR_ENSE_NUM("junk",5)
        r1 = phaser.runMR_ELLG(i0)
        #print r1.logfile()
        if r1.Success():
          res0 = r1.get_target_resolution('junk')
        del(r1)
        return res0

    def run_cca():
        print "run_cca"
        z0 = 0
        sc0 = 0.0
        i0 = phaser.InputCCA()
        i0.setSPAC_HALL(r.getSpaceGroupHall())
        i0.setCELL6(r.getUnitCell())
        i0.setMUTE(True)
        # Have to set high res limit!!
        i0.setRESO_HIGH(res0)
        if args.np > 0:
            i0.addCOMP_PROT_NRES_NUM(args.np, 1)
        if args.na > 0:
            i0.addCOMP_NUCL_NRES_NUM(args.na, 1)
        r1 = phaser.runCCA(i0)
        if r1.Success():
            z0 = r1.getBestZ()
            sc0 = 1-(1.23/r1.getBestVM())
        del(r1)
        return (z0, sc0)

    def run_ncs():
        print "run_ncs"
        i0 = phaser.InputNCS()
        i0.setSPAC_HALL(r.getSpaceGroupHall())
        i0.setCELL6(r.getUnitCell())
        i0.setREFL_DATA(r.getDATA())
        i0.setMUTE(True)
        r1 = phaser.runNCS(i0)
        print r1.logfile()
        print r1.loggraph().size()
        print r1.loggraph().__dict__.keys()
        if r1.Success():
            return r1

    def run_ano():
        print "run_ano"
        i0 = phaser.InputANO()
        i0.setSPAC_HALL(r.getSpaceGroupHall())
        i0.setCELL6(r.getUnitCell())
        i0.setREFL_DATA(r.getDATA())
        i0.setMUTE(True)
        r1 = phaser.runANO(i0)
        print r1.loggraph().__dict__.keys()
        print r1.loggraph().size()
        print r1.logfile()
        """
        o = phaser.Output()
        redirect_str = StringIO()
        o.setPackagePhenix(file_object=redirect_str)
        r1 = phaser.runANO(i0,o)
        """

        if r1.Success():
            print 'SUCCESS'
            return r1

    # Setup which modules are run
    # if inp:
    ellg = True
    ncs = False
    res0 = args.resolution
    if not (args.np or args.na or args.resolution):
        pass
    # else:
    #     ellg = False
    #     ncs = True

    # Read the dataset
    i = phaser.InputMR_DAT()
    print i
    i.setHKLI(args.data_file)
    i.setLABI_F_SIGF("F", "SIGF")
    i.setMUTE(False)
    r = phaser.runMR_DAT(i)
    print r
    if r.Success():
        if ellg:
            res = run_ellg()
        if args.matthews:
            z, sc = run_cca()
        if ncs:
            n = run_ncs()
    if args.matthews:
        # Assumes ellg is run as well.
        print ">>>", z, sc, res
        return (z, sc, res)
    elif ellg:
        #ellg run by itself
        return res
    else:
        # NCS
        return n

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    print args

    run_phaser_module(args)

def get_commandline():
    """
    Grabs the commandline
    """

    # print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Generate a generic RAPD file"
    my_parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    my_parser.add_argument("--json",
                           action="store_true",
                           dest="json",
                           help="JSON output only")

    # Protein residues
    my_parser.add_argument("--np",
                           dest="np",
                           default=0,
                           type=int,
                           help="Number of protein residues")

    # Nucleic acid residues
    my_parser.add_argument("--na",
                           dest="na",
                           default=0,
                           type=int,
                           help="Number of nucleic acid residues")

    # Resolution
    my_parser.add_argument("--resolution",
                           dest="resolution",
                           default=0.0,
                           type=float,
                           help="Resolution for calculations")

    # Calculate matthews coeff?
    my_parser.add_argument("--matthews",
                           action="store_true",
                           dest="matthews",
                           help="Perform matthews calculation")

    # Data file
    my_parser.add_argument("--data_file",
                           action="store",
                           dest="data_file",
                           default=False,
                           help="Data file input")

    # PDB file
    my_parser.add_argument("--pdb_file",
                           action="store",
                           dest="pdb_file",
                           default=False,
                           help="PDB file input")

    # Print help message is no arguments
    if len(sys.argv[1:])==0:
        my_parser.print_help()
        my_parser.exit()

    return my_parser.parse_args()

if __name__ == "__main__":

    commandline_args = get_commandline()

    main(args=commandline_args)

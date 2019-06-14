"""Methods for running Phaser in RAPD"""

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

__created__ = "2017-05-24"
__maintainer__ = "Frnak Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
# import json
# import multiprocessing
from multiprocessing import Process, Queue
#from Queue import Queue as tqueue
import os
from pprint import pprint
import signal
import subprocess
import stat
import json
import random
import shutil
import importlib
from functools import wraps
import tarfile
import time

# Phaser import
import phaser

# RAPD imports
from utils import archive
from utils.xutils import convert_unicode, calc_ADF_map

def connect_to_redis(settings):
    redis_database = importlib.import_module('database.redis_adapter')
    return redis_database.Database(settings=settings)

def run_phaser_pdbquery_script_OLD(command):
    """
    Run phaser for pdbquery
    """
    # Change to correct directory
    os.chdir(command["work_dir"])

    # Setup params
    full = command.get("full", False)
    copy = command.get("copy", 1)
    resolution = command.get("res", False)
    data_file = command.get("data")
    input_pdb = command.get("pdb", False)
    input_cif = command.get("cif", False)
    spacegroup = command.get("spacegroup")
    cell_analysis = command.get("cell analysis", False)
    name = command.get("name", spacegroup)
    large_cell = command.get("large", False)
    #timeout = command.get("timeout", False)
    launcher = command.get("launcher", False)
    test = command.get("test", False)

    # Construct the phaser command file
    command = "phaser << eof\nMODE MR_AUTO\n"
    command += "HKLIn %s\nLABIn F=F SIGF=SIGF\n" % data_file

    # CIF or PDB?
    if input_pdb:
        command += "ENSEmble junk PDB %s IDENtity 70\n" % input_pdb
    elif input_cif:
        command += "ENSEmble junk CIF %s IDENtity 70\n" % input_cif
    command += "SEARch ENSEmble junk NUM %s\n" % copy
    command += "SPACEGROUP %s\n" % spacegroup
    if cell_analysis:
        command += "SGALTERNATIVE SELECT ALL\n"
        # Set it for worst case in orth
        # number of processes to run in parallel where possible
        command += "JOBS 1\n"
    else:
        command += "SGALTERNATIVE SELECT NONE\n"
    if full:
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
    os.chmod("phaser.com", stat.S_IRWXU)

    if launcher:
        pid_queue = Queue()
        if test:
            proc = Process(target=launcher,
                           kwargs={"command": 'ls',
                                   "pid_queue": pid_queue,
                                   })
        else:

            proc = Process(target=launcher,
                           kwargs={"command": os.path.join(os.getcwd(), 'phaser.com'),
                                   "logfile": os.path.join(os.getcwd(), "phaser.log"),
                                   "pid_queue": pid_queue,
                                   })
        proc.start()
        return (proc, pid_queue.get())

    """
    # Run the phaser process
    phaser_proc = subprocess.Popen(["sh phaser.com"],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     shell=True,
                                     preexec_fn=os.setsid)
    try:
        #stdout, _ = phaser_proc.communicate(timeout=timeout)
        stdout, _ = phaser_proc.communicate()

        # Write the log file
        with open("phaser.log", "w") as log_file:
            log_file.write(stdout)

        # Return results
        return {"pdb_code": input_pdb.replace(".pdb", "").upper(),
                "log": stdout,
                "status": "COMPLETE"}

    # Run taking too long
    except subprocess.TimeoutExpired:
        print "  Timeout of %ds exceeded - killing %d" % (timeout, phaser_proc.pid)
        os.killpg(os.getpgid(phaser_proc.pid), signal.SIGTERM)
        return {"pdb_code": input_pdb.replace(".pdb", "").upper(),
                "log": "Timed out after %d seconds" % timeout,
                "status": "ERROR"}
    """


def parse_phaser_output_script_OLD(phaser_log):
    """Parse Phaser log file"""

    # The phased process has timed out
    if phaser_log[0].startswith("Timed out after"):
        phaser_result = {"solution": False,
                         "message": "Timed out"}

    # Looks like process completed
    else:
        pdb = False
        solution_start = False
        clash = "NC"
        end = False
        temp = []
        tncs = False
        nmol = 0
        for index, line in enumerate(phaser_log):
            #print line
            temp.append(line)
            directory = os.getcwd()
            if line.count("SPACEGROUP"):
                spacegroup = line.split()[-1]
            if line.count("Solution") or line.count("Partial Solution "):
                if line.count("written"):
                    if line.count("PDB"):
                        pdb = line.split()[-1]
                    if line.count("MTZ"):
                        mtz = line.split()[-1]
                if line.count("RFZ="):
                    solution_start = index
            if line.count("SOLU SET"):
                solution_start = index
            if line.count("SOLU ENSEMBLE"):
                end = index
        if solution_start:
            for line in phaser_log[solution_start:end]:
                if line.count("SOLU 6DIM"):
                    nmol += 1
                for param in line.split():
                    if param.startswith("RFZ"):
                        if param.count("=") == 1:
                            rfz = param[param.find("=")+param.count("="):]
                    if param.startswith("RF*0"):
                        rfz = "NC"
                    if param.startswith("TFZ"):
                        if param.count("=") == 1:
                            tfz = param[param.find("=")+param.count("="):]
                    if param.startswith("TF*0"):
                        tfz = "NC"
                    if param.startswith("PAK"):
                        clash = param[param.find("=")+param.count("="):]
                    if param.startswith("LLG"):
                        llgain = float(
                            param[param.find("=")+param.count("="):])
                    if param.startswith("+TNCS"):
                        tncs = True
        if not pdb:
            phaser_result = {"solution": False,
                             "message": "No solution"}
        else:
            phaser_result = {"solution": True,
                             "pdb": pdb,
                             "mtz": mtz,
                             "gain": llgain,
                             "rfz": rfz,
                             "tfz": tfz,
                             "clash": clash,
                             "dir": directory,
                             "spacegroup": spacegroup,
                             "tNCS": tncs,
                             "nmol": nmol,
                             "adf": None,
                             "peak": None,
                             }

    pprint(phaser_result)
    return phaser_result


def mp_job(func):
    """
    wrapper to write command script and launch by multiprocessing.Process or Pool.
    Will use the following input keys and remove them before launching:
       'script' - signal to say the script has been written
       'computer_cluster' - signal to launch on computer cluster
       'pool' - The multiprocessing.Pool if launched on local machine
       'test' - run in test mode (used for debugging)
    """

    def write_script(inp):
        # write Phaser command script.
        fo = os.path.join(inp.get('work_dir'), 'phaser_script.py')
        with open(fo, 'w') as f:
            f.write('from plugins.subcontractors.rapd_phaser import run_phaser\n')
            f.write('input = %s\n' % str(inp))
            f.write('run_phaser(**input)\n')
            f.close()
        return fo

    @wraps(func)
    def wrapper(**kwargs):
        os.chdir(kwargs.get('work_dir', os.getcwd()))
        if not kwargs.get('script', False):
            # Pop out the launcher
            launcher = kwargs.pop('launcher', None)
            # Pop out the batch_queue
            batch_queue = kwargs.pop('batch_queue', None)
            # Pop out the results_queue
            result_queue = kwargs.pop('result_queue', None)
            # Create a unique identifier for Phaser results
            #kwargs['output_id'] = 'Phaser_%d' % random.randint(0, 10000)
            # Grab the RAPD python path (if available)
            rapd_python = kwargs.pop('rapd_python', 'rapd.python')
            # Signal to launch run
            kwargs['script'] = True
            if kwargs.get('pool', False):
                # If running on local machine
                pool = kwargs.pop('pool')
                f = write_script(kwargs)
                proc = pool.apply_async(launcher,
                                        kwds={"command": "%s %s" % (rapd_python, f),
                                              "logfile": os.path.join(convert_unicode(kwargs.get('work_dir')), 'rapd_phaser.log'),
                                              "result_queue" : result_queue,
                                               })
                #return (proc, 'junk', kwargs['output_id'])
                return (proc, 'junk')
            else:
                # If running on computer cluster
                f = write_script(kwargs)
                pid_queue = Queue()
                proc = Process(target=launcher,
                               kwargs={"command": "%s %s" % (rapd_python, f),
                                       "logfile": os.path.join(kwargs.get('work_dir'), 'rapd_phaser.log'),
                                       "pid_queue": pid_queue,
                                       "batch_queue": batch_queue,
                                       })
                proc.start()
                #return (proc, pid_queue.get(), kwargs['output_id'])
                return (proc, pid_queue.get())
        else:
            # Remove extra input params used to setup job
            l = ['script', 'test']
            for k in l:
                # pop WON'T error out if key not found!
                _ = kwargs.pop(k, None)
            # Just launch job
            return func(**kwargs)
    return wrapper

@mp_job
def run_phaser(data_file,
               struct_file,
               spacegroup,
               db_settings=False,
               tag=False,
               work_dir=False,
               adf=False,
               name=False,
               ncopy=1,
               cell_analysis=False,
               resolution=False,
               full=False,
               ):
    """
    Run Phaser and passes results back to RAPD Redis DB
    **Requires Phaser src code!**

    data_file - input data as mtz (required)
    struct_file - input search model path in mmCIF or PDB format (required)
    spacegroup - The space group to run MR (required)

    tag - a Redis key where the results are sent (cluster mode)
    db_settings - Redis connection settings for sending results (cluster mode)
    work_dir - working directory (defaults to current working dir)
    name - root name for output files (defaults to spacegroup)
    ncopy - number of molecules to search for
    cell_analysis - internal RAPD signal so all possible SG's are searched
    resolution - high res limit to run MR (float)
    full - signal to run more comprehensive MR
    """
    phaser_log = False
    # Change to work_dir
    if not work_dir:
        work_dir = os.getcwd()
    os.chdir(work_dir)

    if not name:
        name = spacegroup

    # Read the dataset
    i = phaser.InputMR_DAT()
    i.setHKLI(convert_unicode(data_file))
    i.setLABI_F_SIGF('F', 'SIGF')
    i.setMUTE(True)
    r = phaser.runMR_DAT(i)
    if r.Success():
        i = phaser.InputMR_AUTO()
        # i.setREFL_DATA(r.getREFL_DATA())
        # i.setREFL_DATA(r.DATA_REFL())
        i.setREFL_F_SIGF(r.getMiller(), r.getFobs(), r.getSigFobs())
        i.setCELL6(r.getUnitCell())
        if struct_file[-3:].lower() == "cif":
            #i.addENSE_CIF_ID('model', cif, 0.7)
            ### Typo in PHASER CODE!!!###
            i.addENSE_CIT_ID('model', convert_unicode(struct_file), 0.7)
        else:
            i.addENSE_PDB_ID('model', convert_unicode(struct_file), 0.7)
        i.addSEAR_ENSE_NUM("model", ncopy)
        i.setSPAC_NAME(spacegroup)
        if cell_analysis:
            i.setSGAL_SELE("ALL")
            # Set it for worst case in orth
            # number of processes to run in parallel where possible
            i.setJOBS(1)
        else:
            i.setSGAL_SELE("NONE")
        if full:
            # Picks own resolution
            # Round 2, pick best solution as long as less that 10% clashes
            i.setPACK_SELE("PERCENT")
            i.setPACK_CUTO(0.1)
            #command += "PACK CUTOFF 10\n"
        else:
            # For first round and cell analysis
            # Only set the resolution limit in the first round or cell analysis.
            if resolution:
                i.setRESO_HIGH(resolution)
            else:
                i.setRESO_HIGH(6.0)
            i.setSEAR_DEEP(False)
            # Don"t seem to work since it picks the high res limit now.
            # Get an error when it prunes all the solutions away and TF has no input.
            # command += "PEAKS ROT SELECT SIGMA CUTOFF 4.0\n"
            # command += "PEAKS TRA SELECT SIGMA CUTOFF 6.0\n"
        # Turn off pruning in 2.6.0
        i.setSEAR_PRUN(False)
        # Choose more top peaks to help with getting it correct.
        i.setPURG_ROTA_ENAB(True)
        i.setPURG_ROTA_NUMB(3)
        #command += "PURGE ROT ENABLE ON\nPURGE ROT NUMBER 3\n"
        i.setPURG_TRAN_ENAB(True)
        i.setPURG_TRAN_NUMB(1)
        #command += "PURGE TRA ENABLE ON\nPURGE TRA NUMBER 1\n"

        # Only keep the top after refinement.
        i.setPURG_RNP_ENAB(True)
        i.setPURG_RNP_NUMB(1)
        #command += "PURGE RNP ENABLE ON\nPURGE RNP NUMBER 1\n"
        i.setROOT(convert_unicode(name))
        # i.setMUTE(False)
        i.setMUTE(True)
        # Delete the setup results
        del(r)
        # launch the run
        r = phaser.runMR_AUTO(i)
        if r.Success():
            pass
            #if r.foundSolutions():
                #print "Phaser has found MR solutions"
                #print "Top LLG = %f" % r.getTopLLG()
                #print "Top PDB file = %s" % r.getTopPdbFile()
            #else:
                #print "Phaser has not found any MR solutions"
        else:
            print "Job exit status FAILURE"
            print r.ErrorName(), "ERROR :", r.ErrorMessage()
        
        # Save log files for debugging
        phaser_log = r.logfile()
        with open('phaser.log', 'w') as log:
            log.write(r.logfile())
            log.close()

    if r.foundSolutions():
        rfz = None
        tfz = None
        tncs = False
        # Parse results
        for p in r.getTopSet().ANNOTATION.split():
            if p.count('RFZ'):
                if p.count('=') in [1]:
                    rfz = float(p.split('=')[-1])
            if p.count('RF*0'):
                rfz = "NC"
            if p.count('TFZ'):
                if p.count('=') in [1]:
                    tfz = p.split('=')[-1]
                    if tfz == '*':
                        tfz = 'arbitrary'
                    else:
                        tfz = float(tfz)
            if p.count('TF*0'):
                tfz = "NC"
        tncs_test = [1 for line in r.getTopSet().unparse().splitlines()
                     if line.count("+TNCS")]
        tncs = bool(len(tncs_test))
        phaser_result = {"ID": name,
                         "solution": r.foundSolutions(),
                         "pdb": os.path.join(work_dir, r.getTopPdbFile()),
                         "mtz": os.path.join(work_dir, r.getTopMtzFile()),
                         "gain": float(r.getTopLLG()),
                         "rfz": rfz,
                         # "tfz": r.getTopTFZ(),
                         "tfz": tfz,
                         "clash": r.getTopSet().PAK,
                         "dir": os.getcwd(),
                         "spacegroup": r.getTopSet().getSpaceGroupName().replace(' ', ''),
                         "tNCS": tncs,
                         "nmol": r.getTopSet().NUM,
                         "adf": None,
                         "peak": None,
                         }

        # Calc ADF map
        if adf:
            if os.path.exists(phaser_result.get("pdb", False)) and os.path.exists(phaser_result.get("mtz", False)):
                adf_results = calc_ADF_map(data_file=data_file,
                                           mtz=phaser_result["mtz"],
                                           pdb=phaser_result["pdb"])
                if adf_results.get("adf"):
                    phaser_result.update({"adf": os.path.join(work_dir, adf_results.get("adf"))})
                if adf_results.get("peak"):
                    phaser_result.update({"peak": os.path.join(work_dir, adf_results.get("peak"))})
                #phaser_result.update({"adf": adf_results.get("adf", None),
                #                      "peak": adf_results.get("peak", None),})

        # New procedure for making tar of results
        # Create directory
        # Remove the run # from the name
        new_name = name[:-2]
        os.mkdir(new_name)
        # Go through and copy files to archive directory
        file_types = ("pdb", "mtz", "adf", "peak")
        for file_type in file_types:
            target_file = phaser_result.get(file_type, False)
            if target_file:
                if os.path.exists(target_file):
                    # Copy the file to the directory to be archived
                    shutil.copy(target_file, new_name+"/.")
        # Create the archive
        archive_result = archive.create_archive(new_name)
        archive_result["description"] = '%s_files'%new_name
        phaser_result["tar"] = archive_result
    else:
        phaser_result = {"ID": name,
                         "solution": False,
                         "message": "No solution"}
    # Add the phaser log
    if phaser_log:
        phaser_result.update({"logs": {"phaser": phaser_log}})

    if db_settings and tag:
        # Connect to Redis
        redis = connect_to_redis(db_settings)
        # Key should be deleted once received, but set the key to expire in 24 hours just in case.
        redis.setex(tag, 86400, json.dumps(phaser_result))
        # Do a little sleep to make sure results are in Redis for postprocess_phaser
        time.sleep(0.1)
    else:
        # Print the result so it can be seen thru the queue by reading stdout
        #print phaser_result
        print json.dumps(phaser_result)

def run_phaser_module(data_file,
                      result_queue=False,
                      cca=False,
                      tncs=False,
                      ellg=False,
                      struct_file=False,
                      dres=False,
                      np=0,
                      na=0,):
    """
    Run separate module of Phaser to get results before running full job.
    Setup so that I can read the data in once and run multiple modules.
    data_file - input dataset mtz file
    result_queue - pass results to queue
    cca - Run CCA to determine number of molecules in AU, and solvent content (Matthew's Coefficient calc)
    tncs - Run Anisotropy and tNCS correction on CID plots
    ellg - Run analysis to determonine optimum Phaser resolution MR.
    struct_file - input struct_file file. Could be a PDB or mmCIF file
    dres - resolution of dataset (ELLG, CCA)
    np - default number of protein residues (CCA)
    na - default number of nucleic acid residues (CCA)
    """

    target_resolution = 0.0
    z = 0
    solvent_content = 0.0

    def run_ellg():
        new_res = 0.0
        i0 = phaser.InputMR_ELLG()
        i0.setSPAC_HALL(r.getSpaceGroupHall())
        i0.setCELL6(r.getUnitCell())
        i0.setMUTE(True)
        i0.setREFL_DATA(r.getDATA())
        if struct_file[-3:] in ('cif'):
            i0.addENSE_CIT_ID('model', convert_unicode(struct_file), 0.7)
        else:
            i0.addENSE_PDB_ID("model", convert_unicode(struct_file), 0.7)
        r1 = phaser.runMR_ELLG(i0)
        #print r1.logfile()
        if r1.Success():
            # If it worked use the recommended resolution
            new_res = round(r1.get_target_resolution('model'), 1)
        del(r1)
        return new_res

    def run_cca(res):
        z0 = 0
        sc0 = 0.0
        i0 = phaser.InputCCA()
        i0.setSPAC_HALL(r.getSpaceGroupHall())
        i0.setCELL6(r.getUnitCell())
        i0.setMUTE(True)
        # Have to set high res limit!!
        i0.setRESO_HIGH(res)
        if np > 0:
            i0.addCOMP_PROT_NRES_NUM(np, 1)
        if na > 0:
            i0.addCOMP_NUCL_NRES_NUM(na, 1)
        r1 = phaser.runCCA(i0)
        #print r1.logfile()
        #print dir(r1)
        if r1.Success():
            z0 = r1.getBestZ()
            sc0 = round(1-(1.23/r1.getBestVM()), 2)
        del(r1)
        return (z0, sc0)

    def run_tncs():
        # CAN'T GET READABLE loggraph?!?
        i0 = phaser.InputNCS()
        i0.setSPAC_HALL(r.getSpaceGroupHall())
        i0.setCELL6(r.getUnitCell())
        i0.setREFL_DATA(r.getDATA())
        # i0.setREFL_F_SIGF(r.getMiller(),r.getF(),r.getSIGF())
        # i0.setLABI_F_SIGF(f,sigf)
        i0.setMUTE(True)
        # i0.setVERB(True)
        r1 = phaser.runNCS(i0)
        print dir(r1)
        print r1.logfile()
        # for l in r1.loggraph():
        #    print l
        print r1.loggraph().size()
        print r1.output_strings
        #print r1.hasTNCS()
        #print r1.summary()
        print r1.warnings()
        print r1.ErrorMessage()
        #print r1.getCentricE4()
        if r1.Success():
            return(r1.loggraph())

    def run_ano():
        #from cStringIO import StringIO
        i0 = phaser.InputANO()
        i0.setSPAC_HALL(r.getSpaceGroupHall())
        i0.setCELL6(r.getUnitCell())
        # i0.setREFL(p.getMiller(),p.getF(),p.getSIGF())
        # i0.setREFL_F_SIGF(r.getMiller(),r.getF(),r.getSIGF())
        # i0.setREFL_F_SIGF(p.getMiller(),p.getIobs(),p.getSigIobs())
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
            return(r1)

    # MAIN
    # Setup which modules are run
    # Read input MTZ file
    i = phaser.InputMR_DAT()
    i.setHKLI(convert_unicode(data_file))
    i.setLABI_F_SIGF('F', 'SIGF')
    i.setMUTE(True)
    r = phaser.runMR_DAT(i)
    if r.Success():
        if ellg:
            target_resolution = run_ellg()
        if cca:
            # Assumes ellg is run as well.
            z, solvent_content = run_cca(target_resolution)
        if tncs:
            n = run_tncs()
    if cca:
        out = {"z": z,
               "solvent_content": solvent_content,
               "target_resolution": target_resolution}
        if result_queue:
            result_queue.put(out)
        else:
            return out
    elif ellg:
        # ellg run by itself
        out = {"target_resolution": target_resolution}
        if result_queue:
            result_queue.put(out)
        else:
            return out
    else:
        # tNCS
        out = n
        if result_queue:
            result_queue.put(out)
        else:
            return out

    """
    if cca:
        out = {"z": z,
              "solvent_content": solvent_content,
              "target_resolution": target_resolution}
        #Assumes ellg is run as well.
        return out
    elif ellg:
        #ellg run by itself
        out = {"target_resolution": target_resolution}
        return out
    else:
        #tNCS
        return n
    """


def run_phaser_module_OLD(data_file, inp=False):
    """
    Run separate module of Phaser to get results before running full job.
    Setup so that I can read the data in once and run multiple modules.
    """
    # if self.verbose:
    #  self.logger.debug('Utilities::runPhaserModule')

    target_resolution = 0.0
    z = 0
    solvent_content = 0.0

    def run_ellg():
        res0 = 0.0
        i0 = phaser.InputMR_ELLG()
        i0.setSPAC_HALL(r.getSpaceGroupHall())
        i0.setCELL6(r.getUnitCell())
        i0.setMUTE(True)
        i0.setREFL_DATA(r.getDATA())
        if f[-3:] in ('cif'):
            i0.addENSE_CIT_ID('model', convert_unicode(f), 0.7)
        else:
            i0.addENSE_PDB_ID("model", convert_unicode(f), 0.7)
        # i.addSEAR_ENSE_NUM("junk",5)
        r1 = phaser.runMR_ELLG(i0)
        #print r1.logfile()
        if r1.Success():
            res0 = r1.get_target_resolution('model')
        del(r1)
        return res0

    def run_cca():
        z0 = 0
        sc0 = 0.0
        i0 = phaser.InputCCA()
        i0.setSPAC_HALL(r.getSpaceGroupHall())
        i0.setCELL6(r.getUnitCell())
        i0.setMUTE(True)
        # Have to set high res limit!!
        i0.setRESO_HIGH(res0)
        if np > 0:
            i0.addCOMP_PROT_NRES_NUM(np, 1)
        if na > 0:
            i0.addCOMP_NUCL_NRES_NUM(na, 1)
        r1 = phaser.runCCA(i0)
        #print r1.logfile()
        if r1.Success():
            z0 = r1.getBestZ()
            sc0 = 1-(1.23/r1.getBestVM())
        del(r1)
        return (z0, sc0)

    def run_ncs():
        i0 = phaser.InputNCS()
        i0.setSPAC_HALL(r.getSpaceGroupHall())
        i0.setCELL6(r.getUnitCell())
        i0.setREFL_DATA(r.getDATA())
        # i0.setREFL_F_SIGF(r.getMiller(),r.getF(),r.getSIGF())
        # i0.setLABI_F_SIGF(f,sigf)
        i0.setMUTE(True)
        # i0.setVERB(True)
        r1 = phaser.runNCS(i0)
        print r1.logfile()
        print r1.loggraph().size()
        print r1.loggraph().__dict__.keys()
        #print r1.getCentricE4()
        if r1.Success():
            return(r1)

    def run_ano():
        #from cStringIO import StringIO
        i0 = phaser.InputANO()
        i0.setSPAC_HALL(r.getSpaceGroupHall())
        i0.setCELL6(r.getUnitCell())
        # i0.setREFL(p.getMiller(),p.getF(),p.getSIGF())
        # i0.setREFL_F_SIGF(r.getMiller(),r.getF(),r.getSIGF())
        # i0.setREFL_F_SIGF(p.getMiller(),p.getIobs(),p.getSigIobs())
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
            return(r1)

    # Setup which modules are run
    matthews = False
    if inp:
        ellg = True
        ncs = False
        if type(inp) == str:
            f = inp
        else:
            np, na, res0, f = inp
            matthews = True
    else:
        ellg = False
        ncs = True

    # Read the dataset
    i = phaser.InputMR_DAT()
    i.setHKLI(convert_unicode(data_file))
    i.setLABI_F_SIGF('F', 'SIGF')
    i.setMUTE(True)
    r = phaser.runMR_DAT(i)
    if r.Success():
        if ellg:
            target_resolution = run_ellg()
        if matthews:
            z, solvent_content = run_cca()
        if ncs:
            n = run_ncs()
    if matthews:
        # Assumes ellg is run as well.
        # return (z,sc,res)
        return {"z": z,
                "solvent_content": solvent_content,
                "target_resolution": target_resolution}
    elif ellg:
        # ellg run by itself
        # return target_resolution
        return {"target_resolution": target_resolution}
    else:
        # NCS
        return n


"""
  except:
    #self.logger.exception('**ERROR in Utils.runPhaserModule')
    if matthews:
      return((0,0.0,0.0))
    else:
      return(0.0)
"""

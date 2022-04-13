import os, sys
from pprint import pprint
import importlib
import logging.handlers
from utils.processes import local_subprocess, mp_pool
import utils.xutils as xutils
import utils.log
import sites.necat as site
from utils.modules import load_module


def run_analysis(work_dir, logfile=False):
    """ RUN Analysis """
    import plugins.analysis.plugin
    import plugins.analysis.commandline
    
    if not os.path.exists(work_dir):
        os.mkdirs(work_dir)
    os.chdir(work_dir)
    
    if logfile:
        logger = get_logger(logfile)
    else:
        logger = False
    
    # Construct the pdbquery plugin command
    class AnalysisArgs(object):
        #Object containing settings for plugin command construction
        clean = True
        #datafile = '/gpfs6/users/necat/Jon/process/rapd/integrate/ehdbr1_7rna_1/ehdbr1_7rna_free.mtz'
        datafile = '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz'
        dir_up = False
        json = False
        nproc = 8
        #pdbquery = True  #TODO
        progress =  False
        #queue = plugin_queue
        run_mode = 'server'
        sample_type = "default"
        show_plots = False
        test = False
        computer_cluster = True
        db_settings = site.CONTROL_DATABASE_SETTINGS
    
    analysis_command = plugins.analysis.commandline.construct_command(AnalysisArgs)
    
    # The analysis plugin
    plugin = plugins.analysis.plugin
    
    # Run the plugin
    plugin_instance = plugin.RapdPlugin(analysis_command,
                                        #launcher=launcher,
                                        tprint=False,
                                        logger=logger)
    
    plugin_instance.start()

def run_pdbquery(work_dir, logfile):
    # RUN PDBQuery
    import plugins.pdbquery.plugin
    import plugins.pdbquery.commandline
    
    if not os.path.exists(work_dir):
        os.mkdirs(work_dir)
    os.chdir(work_dir)
    # Setup logger if logfile is given
    if logfile:
        logger = get_logger(logfile)
    else:
        logger = False
    
    #os.chdir('/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test')
    #launcher = local_subprocess
    
    # Construct the pdbquery plugin command
    class PdbqueryArgs(object):
        #Object for command construction
        clean = True
        #datafile = '/gpfs5/users/necat/rapd/copper/trunk/integrate/2018-06-07/P113_11_1/P113_11_1/P113_11_1_free.mtz'
        #data_file = '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz'
        #data_file = '/gpfs6/users/necat/Jon/RAPD_test/Output/thaum1_01s-01d_1_mergable.mtz'
        data_file = '/gpfs6/users/necat/Jon/RAPD_test/Output/thau_free.mtz'
        dir_up = False
        json = False
        nproc = 2
        progress = False
        run_mode = 'server'
        pdbs = False
        #pdbs = ['1111', '2qk9']
        contaminants = True
        ##run_mode = None
        search = True
        test = True
        #verbose = True
        #no_color = False
        db_settings = site.CONTROL_DATABASE_SETTINGS
        #output_id = False
        exchange_dir = '/gpfs6/users/necat/rapd2/exchange_dir'
    
    pdbquery_command = plugins.pdbquery.commandline.construct_command(PdbqueryArgs)
    
    # The pdbquery plugin
    plugin = plugins.pdbquery.plugin
    
    # Run the plugin
    plugin_instance = plugin.RapdPlugin(site=site,
                                        command=pdbquery_command,
                                        logger=logger)
    plugin_instance.start()

def run_mr(work_dir, logfile):
    #RUN MR
    import plugins.mr.plugin
    import plugins.mr.commandline
    import uuid
    
    if not os.path.exists(work_dir):
        os.mkdirs(work_dir)
    os.chdir(work_dir)
    #launcher = local_subprocess
    if logfile:
        logger = get_logger(logfile)
    else:
        logger = False
    
    # Construct the pdbquery plugin command
    class MRArgs(object):
        #Object for command construction
        clean = False
        #datafile = '/gpfs5/users/necat/rapd/copper/trunk/integrate/2018-06-07/P113_11_1/P113_11_1/P113_11_1_free.mtz'
        data_file = '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz'
        struct_file = '/gpfs6/users/necat/Jon/RAPD_test/Pdb/thau.pdb'
        dir_up = False
        json = False
        nproc = 11
        adf = False
        progress = False
        run_mode = 'server'
        #pdbs = False
        #pdbs = ['1111', '2qk9']
        #contaminants = True
        ##run_mode = None
        #search = True
        test = False
        #verbose = True
        #no_color = False
        db_settings = site.CONTROL_DATABASE_SETTINGS
        #output_id = False
        exchange_dir = '/gpfs6/users/necat/rapd2/exchange_dir'
    
    mr_command = plugins.mr.commandline.construct_command(MRArgs)
    
    # The pdbquery plugin
    plugin = plugins.mr.plugin
    
    # Run the plugin
    plugin_instance = plugin.RapdPlugin(site=site,
                                        command=mr_command,
                                        logger=logger)
    plugin_instance.start()

def run_rapd_phaser(work_dir, logfile=False):
    """ Run MR on local machine"""
    from plugins.subcontractors.rapd_phaser import run_phaser
    
    if not os.path.exists(work_dir):
        os.mkdirs(work_dir)
    os.chdir(work_dir)
    # logfile is always phaser.log
    
    # Setup local_subprocess
    launcher = local_subprocess
    pool = mp_pool(1)
    
    os.chdir('/gpfs6/users/necat/Jon/RAPD_test/Output')
    
    job_description = {
                        "work_dir": '/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test',
                        "datafile": '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz',
                        #"cif": "/gpfs5/users/necat/rapd/pdbq/pdb/th/1thw.cif",
                        "pdb": "/gpfs6/users/necat/Jon/RAPD_test/Pdb/thau.pdb",
                        "name": 'junk',
                        "spacegroup": 'P422',
                        "ncopy": 1,
                        "test": False,
                        "cell_analysis": True,
                        "large_cell": False,
                        "resolution": 6.0,
                        #"timeout": self.phaser_timer,
                        #"launcher": self.command["preferences"].get("launcher", False)
                        "launcher": launcher,
                        "computer_cluster": False,
                        "pool": pool,
                        #"results_queue": queue,
                        "db_settings": site.CONTROL_DATABASE_SETTINGS,
                        "output_id": False
                        }
    
    #Thread(target=run_phaser_pdbquery, kwargs=job_description).start()
    job, pid, output_id = run_phaser(**job_description)
    print(job)
    #print job.ready()
    while not job.ready():
        print('sleeping...')
        time.sleep(1)
    print(job.successful())
    #print dir(job)
    #print pid
    #print job.get()
    #print output_id
    pool.close()
    pool.join()

def run_calc_ADF(work_dir, logfile=False):
    data_file = '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz'
    pdb = '/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1.pdb'
    mtz = '/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1.mtz'
    
    if not os.path.exists(work_dir):
        os.mkdirs(work_dir)
    os.chdir(work_dir)
    #os.chdir('/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_mr_thau_free/P41212_all_0')
    
    adf_results = xutils.calc_ADF_map(data_file=data_file,
                               mtz=mtz,
                               pdb=pdb)
    print(adf_results)
    
def get_logger(log_path):
    """Setup logger for plugin"""
    #log = "/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_mr.log"
    dir, log_name = os.path.split(log_path)
    logger = utils.log.get_logger(logfile_dir=dir,
                                  logfile_id=log_name[:log_name.rfind(".")],
                                  level=1,
                                  #console=commandline_args.test
                                  console=False)
    return logger
    


# To run a plugin, fill in the info:
work_dir = '/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test'
logfile = '/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_mr.log'

#plugin to run
run_mr(work_dir, logfile)
    
    


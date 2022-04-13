import utils.archive as archive
import os, sys
import shutil
from pprint import pprint
import importlib
import random
import json
import time

from multiprocessing import Queue, Process
import logging
import logging.handlers

from utils.processes import local_subprocess, mp_pool
#from utils.xutils import convert_unicode
import utils.xutils as xutils
import utils.log

# The pdbquery plugin
#logger = logging.getLogger("RAPDLogger")
#logger.debug("__init__")

#LOG_FILENAME = '/gpfs6/users/necat/Jon/RAPD_test/Output/rapd.log'
#logger = logging.getLogger("RAPDLogger")
#logger.debug("__init__")
## Add the log message handler to the logger
#handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=100000, backupCount=5)
##add a formatter
#formatter = logging.Formatter("%(asctime)s - %(message)s")
#handler.setFormatter(formatter)
#logger.addHandler(handler)


# Set up logging
logger = utils.log.get_logger(logfile_dir="/gpfs6/users/necat/Jon/RAPD_test/Output",
                              logfile_id="rapd_mr",
                              level=1,
                              #console=commandline_args.test
                              console=False)

# Setup cluster
import sites.necat as site

from utils.modules import load_module
cluster_launcher = load_module(site.CLUSTER_ADAPTER)
launcher = cluster_launcher.process_cluster
# Setup local_subprocess
#launcher = local_subprocess


# Setup redis
redis_database = importlib.import_module('database.redis_adapter')
#redis_database = redis_database.Database(settings=site.CONTROL_DATABASE_SETTINGS)
redis = redis_database.Database(settings=site.CONTROL_DATABASE_SETTINGS)
#redis = redis_database.connect_to_redis()

"""
cif = '/gpfs6/users/necat/rapd2/integrate/2018-06-06/JDO_PUCK2_A14_Run4_1/rapd_pdbquery_JDO_PUCK2_A14_Run4_1_free/Phaser_1Z7E/1z7e.cif'
l = ['2FGE_E', '2FGE']
for i in l:
    print i.split('_')[0]
    print len(i.split('_'))
    if len(i.split('_')) not in [1]:
        print 'gh'




from plugins.subcontractors.rapd_cctbx import get_pdb_info
pdb_info = get_pdb_info(#cif_file='/gpfs6/users/necat/rapd2/integrate/2018-06-06/JDO_PUCK2_A14_Run4_1/rapd_pdbquery_JDO_PUCK2_A14_Run4_1_free/Phaser_1Z7E/1z7e.cif',
                        #cif_file='/gpfs6/users/necat/Jon/RAPD_test/Output/2yep.cif',
                        cif_file='/gpfs6/users/necat/Jon/RAPD_test/Pdb/thau.pdb',
                       dres=6.0,
                       matthews=True,
                       chains=False,
                       #data_file='/gpfs6/users/necat/rapd2/integrate/2018-06-05/JDO_PUCK2_A14_Run4_1/JDO_PUCK2_A14_Run4_1/JDO_PUCK2_A14_Run4_1_free.mtz',
                       #data_file='/gpfs5/users/necat/rapd/copper/trunk/integrate/2018-06-07/P113_11_1/P113_11_1/P113_11_1_free.mtz',
                       data_file = '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz'
                       )
pprint(pdb_info)
"""
"""
from plugins.subcontractors.rapd_phaser import run_phaser_module
tncs = run_phaser_module(data_file='/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz',
                         tncs=True)
print tncs
"""
"""
# Cleanup Redis
l = redis.keys('Phaser_*')
for k in l:
    redis.delete(k)
print redis.keys('Phaser_*')
print redis.get('Phaser_8858')

#os.chdir('/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test/rapd_pdbquery_P113_11_1_free')
#pprint(json.loads(open('result.json', 'r').read()))



from plugins.subcontractors.rapd_cctbx import get_pdb_info, get_mtz_info
mtz = '/gpfs5/users/necat/rapd/copper/trunk/integrate/2018-06-07/P113_11_1/P113_11_1/P113_11_1_free.mtz'
input_spacegroup, cell, volume = get_mtz_info(mtz)
input_spacegroup_num = xutils.convert_spacegroup(input_spacegroup)
print xutils.get_sub_groups(input_spacegroup_num, "simple")
"""
"""
# RUN Analysis
import plugins.analysis.plugin
import plugins.analysis.commandline
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
                                    launcher=launcher,
                                    tprint=False,
                                    logger=logger)

plugin_instance.start()

#analysis_result = plugin_queue.get()
#print analysis_result
"""
"""
# RUN PDBQuery
import plugins.pdbquery.plugin
import plugins.pdbquery.commandline

os.chdir('/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test')
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
"""
"""
data_file = '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz'
pdb = '/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1.pdb'
mtz = '/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_mr_thau_free/P41212_all_0/P41212_all_0.1.mtz'

os.chdir('/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_mr_thau_free/P41212_all_0')

adf_results = xutils.calc_ADF_map(data_file=data_file,
                           mtz=mtz,
                           pdb=pdb)
print adf_results
"""
"""
#RUN MR
import plugins.mr.plugin
import plugins.mr.commandline
import uuid

os.chdir('/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test')
#launcher = local_subprocess


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
                                    command=mr_command)
plugin_instance.start()
"""


from plugins.subcontractors.rapd_phaser import run_phaser

# Setup local_subprocess
launcher = local_subprocess
pool = mp_pool(1)

os.chdir('/gpfs6/users/necat/Jon/RAPD_test/Output')

job_description = {
                    #"work_dir": '/gpfs6/users/necat/Jon/RAPD_test/Output/Phaser_test',
                    "work_dir": '/gpfs6/users/necat/rapd2/integrate/2020-10-14/SAD020_16_1/rapd_pdbquery_SAD020_16_1_free/Phaser_4NPR',
                    "data_file": '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz',
                    "data_file": '',
                    #"cif": "/gpfs5/users/necat/rapd/pdbq/pdb/th/1thw.cif",
                    #"pdb": "/gpfs6/users/necat/Jon/RAPD_test/Pdb/thau.pdb",
                    "pdb": "/gpfs6/users/necat/Jon/RAPD_test/Pdb/thau.pdb",
                    "struct_file": '/gpfs6/users/necat/rapd2/integrate/2020-10-14/SAD020_16_1/rapd_pdbquery_SAD020_16_1_free/Phaser_4NPR/4npr.cif',
                    #"name": 'junk',
                    "name": '4NPR',
                    #"spacegroup": 'P422',
                    "spacegroup": 'P222',
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


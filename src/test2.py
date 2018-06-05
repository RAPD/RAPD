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

# The pdbquery plugin
logger = logging.getLogger("RAPDLogger")
logger.debug("__init__")

# Setup cluster
import sites.necat as site

from utils.modules import load_module
cluster_launcher = load_module(site.CLUSTER_ADAPTER)
launcher = cluster_launcher.process_cluster
# Setup local_subprocess
#launcher = local_subprocess


# Setup redis
redis_database = importlib.import_module('database.redis_adapter')
redis_database = redis_database.Database(settings=site.CONTROL_DATABASE_SETTINGS)
redis = redis_database.connect_to_redis()

"""
# Cleanup Redis
l = redis.keys('Phaser_*')
for k in l:
    redis.delete(k)
print redis.keys('Phaser_*')
print redis.get('Phaser_8858')

"""

"""
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

# The pdbquery plugin
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

import plugins.pdbquery.plugin
import plugins.pdbquery.commandline

os.chdir('/gpfs6/users/necat/Jon/RAPD_test/Output')
#launcher = local_subprocess

# Construct the pdbquery plugin command
class PdbqueryArgs(object):
    #Object for command construction
    clean = True
    #datafile = '/gpfs6/users/necat/Jon/process/rapd/integrate/ehdbr1_7rna_1/ehdbr1_7rna_free.mtz'
    datafile = '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz'
    dir_up = False
    json = False
    nproc = 2
    progress = False
    run_mode = 'server'
    computer_cluster = True
    #pdbs = False
    pdbs = ['1111', '2qk9']
    contaminants = True
    ##run_mode = None
    search = True
    test = True
    verbose = True
    #no_color = False
    db_settings = site.CONTROL_DATABASE_SETTINGS
    #output_id = False

pdbquery_command = plugins.pdbquery.commandline.construct_command(PdbqueryArgs)

# The pdbquery plugin
plugin = plugins.pdbquery.plugin

# Run the plugin
plugin_instance = plugin.RapdPlugin(command=pdbquery_command,
                                    launcher=launcher,
                                    logger=logger)
plugin_instance.start()


"""
from plugins.subcontractors.rapd_phaser import run_phaser

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
print job
#print job.ready()
while not job.ready():
    print 'sleeping...'
    time.sleep(1)
print job.successful()
#print dir(job)
#print pid
#print job.get()
#print output_id
pool.close()
pool.join()
"""
"""
#multiprocessing.log_to_stderr()
from plugins.subcontractors.rapd_phaser import run_phaser
import multiprocessing
from threading import Thread
import copy_reg
import types

multiprocessing.log_to_stderr()
#POOL = mp_pool(2)
POOL = multiprocessing.Pool(processes=2)
LAUNCHER = local_subprocess
INPUT = {'output_id': 'Phaser_6864', 
         'datafile': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz', 
         'name': u'5FGX', 
         #'work_dir': u'/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/Phaser_5FGX', 
         'work_dir': '/gpfs6/users/necat/Jon/RAPD_test/Output/test',
         #'script': True, 
         'cell_analysis': True, 
         'test': True, 
         'computer_cluster': False, 
         'large_cell': False, 
         'ncopy': 1, 
         'spacegroup': 'P422', 
         'resolution': 0.0, 
         'cif': u'/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/Phaser_5FGX/5fgx.cif',
         'db_settings': {'DATABASE_STRING': 'mongodb://rapd:shallowkillerbeg@remote.nec.aps.anl.gov:27017,remote-c.nec.aps.anl.gov:27017,rapd.nec.aps.anl.gov:27017/rapd?replicaSet=rs0', 
                         'REDIS_SENTINEL_HOSTS': (('164.54.212.172', 26379), ('164.54.212.170', 26379), ('164.54.212.169', 26379), ('164.54.212.165', 26379),('164.54.212.166', 26379)), 
                         'REDIS_HOST': '164.54.212.172', 'CONTROL_DATABASE': 'mongodb', 'REDIS_DB': 0, 'REDIS_PORT': 6379, 'DATABASE_NAME_DATA': 'rapd_data', 
                         'DATABASE_NAME_CLOUD': 'rapd_cloud', 'DATABASE_USER': 'rapd', 'DATABASE_NAME_USERS': 'rapd_users', 'REDIS_CONNECTION': 'sentinel', 
                         'REDIS_MASTER_NAME': 'remote_master', 'DATABASE_PASSWORD': 'shallowkillerbeg', 'DATABASE_HOST': '164.54.212.169'}, 
         }


#class MainClass(Process):
class MainClass(Thread):
    def __init__(self, command, pool=False, processed_results=False, launcher=False, tprint=False, logger=False, verbosity=False):
        Thread.__init__ (self)
        self.pool = pool
        #self.launcher = LAUNCHER
        #self.input = INPUT
        self.command = command
        self.launcher = launcher
        self.logger = logger
        self.jobs = {}
        
        self.db_settings = self.command["input_data"].get("db_settings")
        self.datafile = xutils.convert_unicode(self.command["input_data"].get("datafile"))
        self.working_dir = self.command["directories"].get("work", os.getcwd())
        #Process.__init__(self, name="pdbquery")
        
    def run(self):
        #Execution path of the plugin
        
        os.chdir(self.working_dir)
        #print dir(POOL.apply_async)
        #self.launch_job(self.input)
        self.launch_job(self.setup_inp())
        self.jobs_monitor()
    
    def setup_inp(self):
        job_description = {
                    #"work_dir": os.path.abspath(os.path.join(self.working_dir, "Phaser_%s" % pdb_code)),
                    'work_dir': '/gpfs6/users/necat/Jon/RAPD_test/Output/test',
                    "datafile": self.datafile,
                    #'datafile': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz', 
                    #"cif": cif_path,
                    'cif': '/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_pdbquery_thau_free/Phaser_5FGX/5fgx.cif',
                    #"pdb": cif_path,
                    #"name": pdb_code,
                    'name': '5FGX', 
                    #"spacegroup": data_spacegroup,
                    'spacegroup': 'P422', 
                    #"ncopy": copy,
                    'ncopy': 1, 
                    "test": True,
                    "cell_analysis": True,
                    "large_cell": False,
                    "resolution": 6.0,
                    #"timeout": self.phaser_timer,
                    #"launcher": self.launcher,
                    #"launcher": unwrap(self.launcher),
                    "computer_cluster": False,
                    "db_settings": self.db_settings,
                    "output_id": False}
        return job_description

    def launch_job(self, inp):
        #Launch the Phaser job#
        if self.pool:
            inp['pool'] = self.pool
            #inp['pool'] = POOL
        inp["launcher"] = self.launcher
        #inp["launcher"] = LAUNCHER
        #print inp
        #job, pid, output_id = launch_phaser(inp)
        job, pid, output_id = run_phaser(**inp)
        #job, pid, output_id = wrapper(inp)
        print job, pid, output_id
        self.jobs[job] = {'name': inp['name'],
                          'pid' : pid,
                          'output_id' : output_id}
    
    def jobs_monitor(self):
        timed_out = False
        timer = 0
        jobs = self.jobs.keys()
        
        #if self.pool:
            #self.pool.close()
        
        def finish_job(job):
            #Finish the jobs and send to postprocess_phaser
            info = self.jobs.pop(job)
            print 'Finished Phaser on %s'%info['name']
            #self.logger.debug('Finished Phaser on %s'%info['name'])
            # Send result to postprocess
            #self.postprocess_phaser(info['name'], json.loads(self.redis.get(info['output_id'])))
            # Delete the Redis key
            #self.redis.delete(info['output_id'])
            #p = self.postprocess_phaser(info['name'])
            jobs.remove(job)
        
        while len(jobs):
            for job in jobs:
                if self.pool:
                    print job.ready()
                    #print job.successful()
                    if job.ready():
                        finish_job(job)
                        
                elif job.is_alive() == False:
                    finish_job(job)
                    
            time.sleep(1)
            timer += 1
           
        # Close the self.pool if used
        if self.pool:
            self.pool.close()
            self.pool.join()

#mc = MainClass()
#mc.launch_job()
os.chdir('/gpfs6/users/necat/Jon/RAPD_test/Output/test')
#import plugins.pdbquery.plugin
import plugins.pdbquery.commandline
# Construct the pdbquery plugin command
class PdbqueryArgs(object):
    #Object for command construction
    clean = True
    #datafile = '/gpfs6/users/necat/Jon/process/rapd/integrate/ehdbr1_7rna_1/ehdbr1_7rna_free.mtz'
    datafile = '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz'
    dir_up = False
    json = False
    nproc = 4
    progress = False
    run_mode = 'server'
    computer_cluster = False
    pdbs = False
    contaminants = True
    ##run_mode = None
    search = True
    test = True
    verbose = True
    #no_color = False
    db_settings = site.CONTROL_DATABASE_SETTINGS
    output_id = False

#pdbquery_command = plugins.pdbquery.commandline.construct_command(PdbqueryArgs)
#print pdbquery_command

pdbquery_command = {'status': 0, 'preferences': {'search': True, 'computer_cluster': False, 'progress': False, 'clean': True, 'nproc': 2, 'test': True, 
                                                 'contaminants': True, 'run_mode': 'server'}, 
                                                 'directories': {'work': '/gpfs6/users/necat/Jon/RAPD_test/Output/test'}, 
                                                 'input_data': {'datafile': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz', 'pdbs': False, 
                                                                'db_settings': {'DATABASE_STRING': 'mongodb://rapd:shallowkillerbeg@remote.nec.aps.anl.gov:27017,remote-c.nec.aps.anl.gov:27017,rapd.nec.aps.anl.gov:27017/rapd?replicaSet=rs0', 
                                                                                'REDIS_SENTINEL_HOSTS': (('164.54.212.172', 26379), ('164.54.212.170', 26379), ('164.54.212.169', 26379), 
                                                                                                         ('164.54.212.165', 26379), ('164.54.212.166', 26379)), 
                                                                                'REDIS_HOST': '164.54.212.172', 'CONTROL_DATABASE': 'mongodb', 'REDIS_DB': 0, 'REDIS_PORT': 6379, 'DATABASE_NAME_DATA': 'rapd_data', 
                                                                                'DATABASE_NAME_CLOUD': 'rapd_cloud', 'DATABASE_USER': 'rapd', 'DATABASE_NAME_USERS': 'rapd_users', 
                                                                                'REDIS_CONNECTION': 'sentinel', 'REDIS_MASTER_NAME': 'remote_master', 'DATABASE_PASSWORD': 'shallowkillerbeg', 'DATABASE_HOST': '164.54.212.169'}}, 
                                                 'process_id': 'ea841d7a643211e89833ac9e17b77ddf', 
                                                 'command': 'PDBQUERY'}

# The pdbquery plugin
#plugin = plugins.pdbquery.plugin

# Run the plugin
plugin_instance = MainClass(command=pdbquery_command,
                                    launcher=LAUNCHER,
                                    pool=POOL,
                                    logger=logger)
plugin_instance.start()
#plugin_instance.run()
print 'DONE'
"""
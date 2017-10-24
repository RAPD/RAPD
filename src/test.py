import cbf
import json
import shutil
import os
import redis
from redis.sentinel import Sentinel
import time
from threading import Thread
from multiprocessing import Process, Queue, Event
import shlex
#import streamUtils as Utils
#from cctbx.regression.tst_adp_aniso_restraints import fd

def connect_redis_manager_HA(name="remote_master"):
    # Set up redis connection
    hosts = (("164.54.212.172", 26379),
             ("164.54.212.170", 26379),
             ("164.54.212.169", 26379),
             ("164.54.212.165", 26379),
             ("164.54.212.166", 26379)
            )
    
    # Connect to the sentinels
    sentinel = Sentinel(hosts)
    # Get the master redis instance
    return(sentinel.master_for(name))

#import utils.xutils as xutils
#cluster_launcher = xutils.load_cluster_adapter(self)
#launcher = cluster_launcher.process_cluster
import sites.cluster.sercat as cluster

launcher = cluster.process_cluster
"""
import multiprocessing
#import threading
event = multiprocessing.Event()
event.set()
#threading.Thread(target=run_job).start()
processCluster(command='touch junk',
               #work_dir='/gpfs6/users/necat/Jon/RAPD_test/Output',
               work_dir='/gpfs5/users/necat/rapd/rapd2_t/single/2017-08-09/B_14:612',
               logfile='/gpfs6/users/necat/Jon/RAPD_test/Output/temp.log',
               queue='index.q',
               nproc=2,
               name='TEST',
               mp_event=event,
               timeout=False,)
time.sleep(2)
print 'event cleared'
event.clear()
"""
q = Queue()
#q0 = Queue()
event = Event()
event.set()
inp_kwargs = {'command': 'sleep 20',
              'logfile': '/home/schuerjp/temp/junk.log',
              'nproc':2,
              'name':'TEST',
              'pid_queue': q,
              #'result_queue': q0,
              }
# Update batch queue info if using a compute cluster
#inp_kwargs.update(self.batch_queue)

#Launch the job
jobs = Process(target=launcher,
              kwargs=inp_kwargs)
jobs.start()
print q.get()
time.sleep(2)
print 'event cleared'
event.clear()

"""
import sites.detectors.necat_dectris_eiger16m as eiger
from detectors.detector_utils import merge_xds_input
#junk = []
l = ['UNTRUSTED_RECTANGLE', 'UNTRUSTED_ELLIPSE', 'UNTRUSTED_QUADRILATERAL']
inp1 = [
      ('TESTING', "TESTING"),
      ('UNTRUSTED_RECTANGLE1', 'TESTING'),
      ('UNTRUSTED_RECTANGLE2', ''),
      ]
for line in merge_xds_input(eiger.XDSINP, inp1):
    print line
"""
#new_inp = []
#for x in range(len(inp1)):
#    for line in eiger.XDSINP:
#        if line.count(inp1[x][0]):
"""
for line in eiger.XDSINP:
    #print "%s%s"%('='.join(line), '\n')
    #if line[0].count('UNTRUSTED_RECTANGLE'):
    #    line = ("UNTRUSTED_RECTANGLE", line[1])
    #print "%s%s"%('='.join(line), '\n')
    #for x in range(len(l)):
    #    if line[0].count(l[x]):
    #        line = (l[x], line[1])
    for x in range(len(inp1)):
        if line[0] == inp1[x][0]:
            line = inp1.pop(x)
    print "%s%s"%('='.join(line), '\n')
if len(inp1) > 0:
    for line in inp1:
        print "%s%s"%('='.join(line), '\n')
"""
"""
labelit_tracker = {}
iteration = 0
#if labelit_tracker.get(iteration, False):
labelit_tracker.setdefault(iteration, {'nruns':0})
print labelit_tracker[iteration].setdefault('nruns', 0)
labelit_tracker[iteration]['nruns'] += 1
print labelit_tracker[iteration]
print labelit_tracker[iteration].get('nruns')
print labelit_tracker[iteration].setdefault('nruns', 0)

labelit_tracker[iteration]['nruns'] += 1

#labelit_tracker.setdefault('nruns', 1)
print labelit_tracker[iteration]
print labelit_tracker[iteration].get('nruns')
print labelit_tracker[iteration].setdefault('nruns', 1)


fin = '/gpfs6/users/necat/Jon/RAPD_test/Output/LWK09_H15_PAIR_0_000001.cbf'
fout = '/gpfs6/users/necat/Jon/RAPD_test/Output/test_01_000001.cbf'

data, header, miniheader = cbf.read(fin, True, True)

print header
print miniheader

cbf.write(fout, data)
"""
"""
file = '/gpfs5/users/necat/capel/images/eiger_test/MDB_CPS66_1_dheader-1.0.raw'
f = open(file,'r').read()
print json.loads(f.bytes)

import time
import os
temp = '/tmp/server.pid'
try:
  with open(temp,'w') as f:
      while True:
        print os.path.isfile(temp)
        time.sleep(2)

except:
  print 'rm -rf %s'%temp
  os.system('rm -rf %s'%temp)
"""
'/ramdisk/gpfs2/users/toronto/tempel_E_2861/images/Raj/runs/test/test2'
"""
#removes test2
#folder = '/ramdisk/gpfs2/users/toronto/tempel_E_2861/images/Raj/runs/test/test2'
folder0 = '/gpfs2/users/GU/UCLA_E_July2017/images/sawaya/sawaya_nnqqnySCN_tray4b1_p13_w12_1/nnqqnySCN_tray4b1_p13_w12_1_000001'
folder1 = '/gpfs2/users/GU/UCLA_E_July2017/images/sawaya/sawaya_nnqqnySCN_tray4b1_p13_w12_1'
#print int(os.popen("ls | wc -l").read())
print int(os.popen("ls /gpfs2/users/GU/UCLA_E_July2017/images/sawaya/sawaya_nnqqnySCN_tray4b1_p13_w12_1/*.cbf| wc -l").read())
print folder0[:folder0.rfind('_')+1]
print int(os.popen("ls %s*.cbf| wc -l"%folder0[:folder0.rfind('_')+1]).read())
"""

#folder = '/ramdisk/gpfs2/users/necat/Jon2/images/eiger_test/junk/junk_1_000001'
#print folder[:folder.rfind('/')]
#shutil.rmtree(folder)
#os.removedirs(folder[:folder.rfind('/')])
#print len([name for name in os.listdir(folder) if os.path.isfile(os.path.join(folder, name))])

"""
for dirpath, subdirs, filenames in os.walk(folder, topdown=False):
  print dirpath
  print subdirs
  print filenames

import tempfile
#fd = tempfile.NamedTemporaryFile(delete=False)
fd = tempfile.NamedTemporaryFile(dir='/gpfs6/users/necat/Jon/RAPD_test/Output', delete=False)
print fd
print fd.name
fd.close()
print fd
print fd.name

from utils.processes import local_subprocess, mp_pool
from multiprocessing import Queue

def f1(command,
       logfile=False,
       pid_queue=False,
       result_queue=False,
       tag=False,
       #*args, **kwargs
       ):
     return command
     print command
     print logfile
     print pid_queue
     print result_queue
     print tag
     pid_queue.put('90')
     result_queue.put('gh')

os.chdir('/gpfs6/users/necat/Jon/RAPD_test/Output')
pool = mp_pool(8)


pid_queue = Queue()
indexing_results_queue = Queue()
# setup input kwargs
command = 'ls'
log = 'junk.log'
iteration = 1

inp_kwargs = {"command": command,
              "logfile": log,
              "pid_queue": pid_queue,
              "result_queue": indexing_results_queue,
              "tag": iteration,
              }
args1 = (command, log, pid_queue, indexing_results_queue, iteration)
launcher = local_subprocess
launcher = f1
#f1(**inp_kwargs)
#f1(*args)
#run = f1(inp_kwargs)
#run = pool.apply_async(f1, kwds=inp_kwargs)
run = pool.apply_async(f1, (inp_kwargs,))
time.sleep(1)
print run.successful()
print dir(run)
print run.__dict__
#print run.get()
print pid_queue.get()
print indexing_results_queue.get()
pool.close()
pool.join()
"""

#red = connect_redis_manager_HA()

#red.delete('images_collected:NECAT_T')
#red.lpush('images_collected:NECAT_T', '/gpfs2/users/harvard/Wagner_E_3064/images/evangelos/snaps/GW02XF07_PAIR_0_000001.cbf')
#red.lpush('images_collected:NECAT_T', '/gpfs2/users/harvard/Wagner_E_3064/images/evangelos/snaps/GW02XF07_PAIR_0_000002.cbf')
#red.lpush('images_collected:NECAT_T', '/gpfs2/users/columbia/hendrickson_E_3093/images/wwang/runs/Hend03_04/Hend03_04_1_001075.cbf')
#red.lpush('images_collected:NECAT_T', '/gpfs2/users/columbia/hendrickson_E_3093/images/wwang/runs/CPS3509_03/CPS3509_03_1_000001.cbf')
#red.lpush('images_collected:NECAT_T', '/gpfs2/users/mskcc/patel_E_3080/images/hui/runs/hy_640_9/hy_640_9_1_000002.cbf')
#red.lpush('images_collected:NECAT_T', '/gpfs2/users/mskcc/patel_E_2891/images/juncheng/snaps/chengwI5_PAIR_0_000005.cbf'),
#red.lpush('images_collected:NECAT_T', '/gpfs2/users/mskcc/patel_E_2891/images/juncheng/snaps/chengwI5_PAIR_0_000006.cbf'),
#red.lpush('images_collected:NECAT_T', '/gpfs2/users/columbia/Mancia_E_3109/images/meagan/snaps/man2_3_0_000001.cbf'), # no index
#red.lpush('images_collected:NECAT_T', '/epu2/rdma/gpfs2/users/slri/sicheri_E_3136/images/Igor/runs/VP03_MKTYc/VP03_MKTYc_1_000001/VP03_MKTYc_1_000001.cbf'),
#red.lpush('images_collected:NECAT_T', '/epu2/rdma/gpfs2/users/slri/sicheri_E_3136/images/Igor/runs/VP03_MKTYc/VP03_MKTYc_1_000001/VP03_MKTYc_1_000002.cbf'),
#red.lpush('images_collected:NECAT_T', '/epu2/rdma/gpfs2/users/harvard/haowu_E_3143/images/liwang/runs/hw1_7/hw1_7_1_000001/hw1_7_1_000001.cbf'),

#print red.llen('RAPD_QSUB_JOBS_0')
#red.delete('RAPD_QSUB_JOBS_0')
#print red.llen('RAPD_JOBS')
#print red.llen("images_collected:NECAT_T")
#red.delete("images_collected:NECAT_T")
#print red.llen("images_collected:NECAT_T")
#print red.llen('run_info_T')

#print red.llen('run_data:NECAT_T')
#print red.llen('RAPD_RESULTS')
#red.delete('RAPD_RESULTS')
#print red.llen('run_info_T')
#print red.llen('RAPD_JOBS_WAITING')
#red.delete('RAPD_JOBS_WAITING')
#print red.llen('RAPD_JOBS_WAITING')
#print red.lrange('run_info_T', 0, 5)
#red.delete('images_collected_T')
#print red.llen('images_collected_T')
#red.close()


#red = Utils.connect_redis(ip='164.54.212.218')
#red.sadd('rapd_working', '/gpfs2/users/junk')
#red.sadd('rapd_working', '/gpfs2/users/junk')
#print red.smembers('rapd_working')
#pipe = red.pipeline()
#pipe.get('EIGER_DIRECTORY_SV')
#pipe.get('EIGER_SV')
#results = pipe.execute()
#print results
#red.close()

#path = '/ramdisk/gpfs2/users/nih/joyce_E_2908/images/gordon/snaps/3661__1_PAIR_0_000001/3661__1_PAIR_0_000001.cbf'
#print 'Does dir exist?: %s'%os.path.isdir(os.path.dirname(path))

#red = Utils.connect_redis(ip='127.0.0.1')
#print red.lrange('file-tracker-ram', 0, -1)
#pair = ['/epu/rdma/gpfs2/users/yale/steitz_e_2924/images/yang/snaps/csb02_05_pair_0_000002/csb02_05_pair_0_000002.cbf', 
#             '/epu/rdma/gpfs2/users/yale/steitz_e_2924/images/yang/snaps/csb02_04_pair_0_000001/csb02_04_pair_0_000001.cbf']
#print os.path.basename(pair[0][:pair[0].rfind('_')])
#print os.path.basename(self.pair[1][:self.pair[1].rfind('_')])



#import cbf
import json
import shutil
import os
import redis
from redis.sentinel import Sentinel
import time
from threading import Thread
from multiprocessing import Process, Queue, Event
import shlex
import subprocess
import re
from pprint import pprint
import inspect
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
    
def connect_sercat_redis():

    pool = redis.ConnectionPool(host="164.54.208.142",
    				port=6379,
    				db=0)
    # Save the pool for a clean exit.
    return redis.Redis(connection_pool=pool)

def connect_ft_redis():

    pool = redis.ConnectionPool(host="164.54.212.218",
            port=6379,
            db=0)
    # Save the pool for a clean exit.
    return redis.Redis(connection_pool=pool)
  
def connect_beamline():
    # C is 56, E is 125
    pool = redis.ConnectionPool(host="164.54.212.56",
            port=6379,
            db=0)
    # Save the pool for a clean exit.
    return redis.Redis(connection_pool=pool)

def processLocal(inp, logger=False, output=False):
    """
    Run job as subprocess on local machine.
    """

    # Logfile might be passed in
    if type(inp) == tuple:
        command, logfile = inp
    else:
        command = inp
        logfile = False

    # Run the process
    proc = subprocess.Popen(command,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    # Send back PID if have outlet
    if output:
        output.put(proc.pid)

    # Get the stdout and stderr from process
    stdout, stderr = proc.communicate()
    # print stdout
    # print stderr

    # Write out a log file, if name passed in
    if logfile:
        with open(logfile, "w") as out_file:
            out_file.write(stdout)
            out_file.write(stderr)

def clear_cluster():
    l = []
    inp = 'qstat'
    myoutput = subprocess.Popen(inp,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    for line in myoutput.stdout:
        split = line.split()
        if len(split) == 8:
            #print split
            if split[2].count('INDEX'):
                l.append(split[0])
            if split[2].count('INTEGRATE_'):
                l.append(split[0])
    for pid in l:
        os.system('qdel %s'%pid)

import sites.necat as site
if hasattr(site, 'ALT_IMAGE_LOCATION'):
    print 'gh'
if hasattr(site, 'junk'):
    print 'gh1'


#clear_cluster()
"""
from utils.modules import load_module
#import 
DETECTORS = {"NECAT_C":("NECAT_DECTRIS_PILATUS6MF", ""),
             "NECAT_E":("NECAT_DECTRIS_EIGER16M", ""),
             "NECAT_T":("NECAT_DECTRIS_EIGER16M", "")}
site_ids = ("NECAT_C", 'NECAT_E')

for site_id in site_ids:
    detector, suffix = DETECTORS[site_id]
    detector = detector.lower()
    detectors[site_id.upper()] = load_module(
        seek_module=detector,
        directories=("sites.detectors", "detectors"))

print detectors
"""
#import sites.detectors.necat_dectris_eiger16m as det
#print hasattr(det, 'FileLocation')
#rint inspect.isclass(det, 'FileLocation')
   



"""
jobs = {}
l = ['cbf-worker', 'cbf-main', 'data-handler']
output = subprocess.Popen('ps -eaf | grep python',shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
for line in output.stdout:
    split = line.split()
    for r in l:
        if split[-1].count(r):
            jobs[split[-1]] = {'time': int(self.timer + Config.HB_INT), 'score': 3}
    


#print "STAC file%s"%str(x+1)
def read_header(image,
                mode=None,
                run_id=None,
                place_in_run=None,
                logger=False):
    
    #Given a full file name for a Piltus image (as a string), read the header and
    #return a dict with all the header info
    
    # print "determine_flux %s" % image
    if logger:
        logger.debug("read_header %s" % image)

    # Make sure the image is a full path image
    image = os.path.abspath(image)
    
    count = 0
    while (count < 10):
        try:
            # Use 'with' to make sure file closes properly. Only read header.
            header = ""
            with open(image, "rb") as raw:
                for line in raw:
                    if line.count('Beam_xy'):
                        line = line.replace('27586.67, 29160.00', '2063.20, 2177.33')
                    header += line
                    #if line.count("Ring_current"):
                    #    break
            break
        except:
            count +=1
            if logger:
                logger.exception('Error opening %s' % image)
            time.sleep(0.1)
    
    new_image = image.replace('ALLER-003_Pn4', 'ALLER-003_Pn4_test')
    with open(new_image, "w") as new:
        new.write(header)
        new.close()
    
    
f = '/gpfs6/users/necat/Jon/RAPD_test/Images/SERCAT/ID/eiger/ALLER-003_Pn4_000100.cbf'
print read_header(f)
"""

"""
proc = subprocess.Popen('qstat',
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

"""
"""
import numpy
header = {}
#site_params = {'BEAM_FLUX': 8.2E11}
site_params = {'BEAM_FLUX': 5E12}
#site_params = {'BEAM_FLUX': 8E11}
header['transmission'] = 100.0
beam_size_x = 0.07
beam_size_y = 0.03
aperture = 0.01
new_x = beam_size_x
new_y = beam_size_y

if aperture < beam_size_x:
    new_x = aperture
if aperture < beam_size_y:
    new_y = aperture

# Calculate area of full beam used to calculate the beamline flux
# Assume ellipse, but same equation works for circle.
# Assume beam is uniform
full_beam_area = numpy.pi*(beam_size_x/2)*(beam_size_y/2)
#print 'full: %s'%full_beam_area

# Calculate the new beam area (with aperture) divided by the full_beam_area.
# Since aperture is round, it will be cutting off edges of x length until it matches beam height,
# then it would switch to circle
if beam_size_y <= aperture:
    # ellipse
    ratio = (numpy.pi*(aperture/2)*(beam_size_y/2)) / full_beam_area
    print 'ration0: %s'%ratio
else:
    # circle
    ratio = (numpy.pi*(aperture/2)**2) / full_beam_area
    print 'ration1: %s'%ratio
# Calculate the new_beam_area ratio to full_beam_area
flux = int(round(site_params.get('BEAM_FLUX') * (header.get('transmission')/100) * ratio))

# Return the flux and beam size
print flux
#return (flux, new_x, new_y)
calc = (8.8E12)/(2*numpy.pi*0.05*0.012)
print calc
calc = (8.8E12)/(numpy.pi*0.035*0.015)
print calc
"""
"""



pool = redis.ConnectionPool(host="164.54.212.169",
            port=6379,
            db=0)

red = redis.StrictRedis(connection_pool=pool)
#red = redis.Redis(connection_pool=pool)
print pool._created_connections, pool._in_use_connections, pool.max_connections
red.set('junk', 'junk')
print pool._created_connections, pool._in_use_connections, pool.max_connections
red.set('junk', '')
pool.disconnect()
print pool._created_connections, pool._in_use_connections, pool.max_connections, pool.pid
#print dir(red.connection_pool)
#print red.connection_pool._created_connections, red.connection_pool.pid
#l = red.client_list()
#for x in range(len(l)):
#    print l[x]['addr'], l[x]['cmd']
#pool.release()
#print pool._created_connections, pool._in_use_connections, pool.max_connections
#print 
"""

"""
f = open('/gpfs2/users/necat/Jon2/process/Minor/K11/P4/Phenix/helix.txt', 'r').readlines()
counter = 0
temp = []
for line in f:
    if line.count('serial_number'):
        counter += 1
        line = line[:line.find('=')+2] + str(counter) + '\n'
    if line.count('helix_identifier'):
        line = '%s"%s"\n'%(line[:line.find('=')+2], str(counter))
        #line = line[:line.find('=')+2] + \"str(counter)\"
    print line
    temp.append(line)
f1 = open('/gpfs2/users/necat/Jon2/process/Minor/K11/P4/Phenix/helix2.txt', 'w')
for line in temp:
    f1.write(line)
f1.close()


import sites.cluster.sercat as cluster
launcher = cluster.process_cluster

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

q = Queue()
#q0 = Queue()
#event = Event()
#event.set()
inp_kwargs = {'command': 'sleep 5',
              'logfile': '/home/schuerjp/temp/junk.log',
              'nproc':2,
              'name':'TEST',
              'pid_queue': q,
              #'result_queue': q0,
              #'timeout': 5,
              #'mp_event': event,
              }
# Update batch queue info if using a compute cluster
#inp_kwargs.update(self.batch_queue)

#Launch the job
jobs = Process(target=launcher,
              kwargs=inp_kwargs)
jobs.start()
print q.get()
jobs.join(1)
#print q0.get()
"""
#time.sleep(2)
#print 'event cleared'
#event.clear()

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

TIMER = 5
timer = 0
while True:
    if round(timer%TIMER,1) == 1.0:
        print timer
    time.sleep(0.2)
    timer += 0.2
"""


#d = {'fullname': '/gpfs1/users/duke/pei_C_3263/images/pei/runs/A6/0_0/A6_1_0001.cbf !Change to accurate path to data frames'}
#d = {'fullname': '/gpfs1/users/duke/pei_C_3263/images/pei/runs/A6/0_0/A6_1_0001.cbf'}
#print d['fullname'].replace(' !Change to accurate path to data frames', '')

red = connect_redis_manager_HA()

#red = connect_sercat_redis()
#connection = connect_beamline()
#red = connect_ft_redis()

#red.delete('RAPD_QSUB_JOBS_0')
#red.delete("images_collected:NECAT_E")
#red.delete("images_collected:NECAT_C")
#red.delete("run_data:NECAT_C")
#red.delete("run_data:NECAT_E")
#red.delete('RAPD_JOBS_WAITING')
#time.sleep(2)

#red.delete('images_collected:NECAT_E')
#red.lpush('images_collected:NECAT_C', '/gpfs1/users/necat/Jon2/images/junk/0_0/tst_0_0001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/harvard/Wagner_E_3064/images/evangelos/snaps/GW02XF07_PAIR_0_000001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/uic/yury_E_3441/images/zahra/snaps/ZB_YSP05_16_GGN_PAIR_0_000005.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/necat/necat_E_3100/images/Jon/runs/junk/junk_3_000001.cbf')
#time.sleep(1)
"""
red = connect_ft_redis()
l = red.smembers('working')
print l
for d in l:
    red.srem('working', d)
    #if d.count('/gpfs2/users/necat/necat_E_3100/images/Jon'):
    #   red.srem('working', d)
print red.smembers('working')
"""
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/harvard/Wagner_E_3064/images/evangelos/snaps/GW02XF07_PAIR_0_000002.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/columbia/hendrickson_E_3093/images/wwang/runs/Hend03_04/Hend03_04_1_001075.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/columbia/hendrickson_E_3093/images/wwang/runs/CPS3509_03/CPS3509_03_1_000001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/mskcc/patel_E_3080/images/hui/runs/hy_640_9/hy_640_9_1_000002.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/mskcc/patel_E_2891/images/juncheng/snaps/chengwI5_PAIR_0_000005.cbf'),
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/mskcc/patel_E_2891/images/juncheng/snaps/chengwI5_PAIR_0_000006.cbf'),
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/columbia/Mancia_E_3109/images/meagan/snaps/man2_3_0_000001.cbf'), # no index
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/slri/sicheri_E_3136/images/Igor/runs/VP03_MKTYc/VP03_MKTYc_1_000001/VP03_MKTYc_1_000001.cbf'),
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/slri/sicheri_E_3136/images/Igor/runs/VP03_MKTYc/VP03_MKTYc_1_000001/VP03_MKTYc_1_000002.cbf'),
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/harvard/haowu_E_3143/images/liwang/runs/hw1_7/hw1_7_1_000001/hw1_7_1_000001.cbf'),

#red.lpush('images_collected:SERCAT_ID', '/data/ID_GSK_20171101.raw/11_01_2017_APS22id/screen/GSK8P9_AR.0002'),
#red.lpush('images_collected:SERCAT_ID', '/data/ID_MDAnderson_mdanderson.raw/TJ/ATG_70164_07_13/IACS-07_Pn13.0001'),
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/sinai/jin_E_3213/images/babault/snaps/JJ1_A3_PAIR_0_000003/JJ1_A3_PAIR_0_000003.cbf')
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/yale/strobel_E_3222/images/caroline/runs/SAS001_14/SAS001_14_1_000001/SAS001_14_1_000001.cbf')
#red.lpush('images_collected:SERCAT_ID', '/data/raw/ID_17_11_08_20171108_AMA/CRC-5p2/CRC-5_Pn2.0001'),
#red.lpush('images_collected:SERCAT_ID', '/data/raw/ID_17_11_08_UNC_KE/Puck41_pn7_IDbeam_2/UNC-41_Pn7.0312'),
#red.lpush('images_collected:SERCAT_ID', '/data/ID_GSK_20171101.raw/11_01_2017_APS22id/screen/GSK8P9_AR.0002'),
#red.lpush('images_collected:SERCAT_ID', '/data//raw/BM_17_11_21_GSK_20171121/11_21_2017_APS22bm/screen/P300_GSK3925257A_2_r1_s.0001'),
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/fandm/piro_E_3242/images/christine/runs/149pN3F_x04/149pN3F_x04_1_000001/149pN3F_x04_1_000001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/mskcc/stewart_E_3436/images/yehuda/snaps/m6a_PAIR_0_000001.cbf')
"""
print red.llen('RAPD_QSUB_JOBS_0')
#red.delete('RAPD_QSUB_JOBS_0')
#print red.llen('run_info_C')
print red.llen('RAPD_JOBS')
#print red.llen("images_collected:SERCAT_ID")
#red.delete("images_collected:SERCAT_ID")
#print red.llen('run_data:SERCAT_ID')
#red.delete("run_data:SERCAT_ID")
print red.llen("images_collected:NECAT_E")
#red.delete("images_collected:NECAT_E")
print red.llen("images_collected:NECAT_C")
#red.delete("images_collected:NECAT_C")
print red.llen('run_data:NECAT_C')
#red.delete("run_data:NECAT_C")
print red.llen('run_data:NECAT_E')
#red.delete("run_data:NECAT_E")
#print red.llen('RAPD_RESULTS')
#red.delete('RAPD_RESULTS')
#print red.llen('run_info_T')
print red.llen('RAPD_JOBS_WAITING')
#red.delete('RAPD_JOBS_WAITING')
#print red.lrange('run_info_T', 0, 5)
#red.delete('images_collected_T')
print red.llen('images_collected_E')
#red.close()

"""

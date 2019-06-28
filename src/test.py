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
import sys
import utils.archive as archive
#import plugins.analysis.plugin
import utils.log
import utils.processes as process
import datetime

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

def connect_remote_redis():

    red = redis.Redis(host="164.54.212.169",
            port=6379,
            db=0)
    # Save the pool for a clean exit.
    return red


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
        #print split
        if len(split) == 8:
            #if split[2].split('-')[0] in ['INTE']:
              #l.append(split[0])
            if split[2].count('INDEX-'):
                l.append(split[0])
            #if split[4] == 'qw':
            #    l.append(split[0])
            
    for pid in l:
        print pid
        os.system('qdel %s'%pid)


#clear_cluster()

job = 'P21212_A_0'
print job[:-2]

"""
f = open('/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_index_CD546A_1_1_2_S.005_CD546A_1_1_2_S.004/result.json', 'r').read()
d = json.loads(f)
print d['results']['mosflm_results_norm']['strategy']['sweeps']



# smartie.py is a python script for parsing log files from CCP4
sys.path.append(os.path.join(os.environ["CCP4"],'share','smartie'))
import smartie

#aimless_log = '/gpfs5/users/necat/rapd/uranium/trunk/integrate/2018-08-01/Alex_2140_1_7000eV_1/Alex_2140_1_7000eV_1/Alex_2140_1_7000eV_1_aimless.log'
aimless_log = '/gpfs5/users/necat/rapd/uranium/trunk/integrate/2018-08-01/Alex_2140_1_7000eV_3/Alex_2140_1_7000eV_3/Alex_2140_1_7000eV_3_aimless.log'
#aimlog = open(aimless_log, 'r').readlines()
#print aimlog
log = smartie.parselog(aimless_log)
# The program expect there to be 10 tables in the aimless log file.
ntables = log.ntables()
if ntables != 10:
    #raise RuntimeError, '%s tables found in aimless output, program expected 10.' %ntables
    print '%s tables found in aimless output, program exepected 10.'

tables = []
for i in range(0,ntables):
    data = []
    # Ignore the Anisotropy analysis table (it's not always present
    # and if you don't ignore it, it causes problems when it is not
    # there.)
    if 'Anisotropy analysis' in log.tables()[i].title():
        pass
    else:
        for line in log.tables()[i].data().split('\n'):
            if line != '':
                data.append(line.split())
        tables.append(data)

print len(tables)
"""
"""
for line in dat_dirs:
    #print line
    if dir.count(line):
        print line

dat_dirs_check = [1 for line in dat_dirs if dir.count(line)]
check = bool(len(dat_dirs_check))
print check
print bool(len([1 for line in dat_dirs if dir.count(line)]))
print bool(len([1 for line in dat_dirs if os.path.dirname(image).count(line)]))

output_dict = {}
search = []
pdb_list = ['0thw', '1thw', '2thw','3thw','4thw','5thw','6thw','7thw']
results = {'0THW' : {'description':'0'},
           '1THW': {'description':'1'},
           '3THW': {'description':'3'},
           '7THW': {'description':'7'}}
for pdb in pdb_list:
    if results.get(pdb.upper(), False):
        output_dict[pdb.upper()] = {'description': results.get(pdb.upper()).get('description')}
    else:
        search.append(pdb)
q = 'pdb_id:(%s)'%" OR ".join(search)
print q
#search = [pdb for pdb in pdb_list if not results.keys().count(pdb)]
#search = [pdb_list.pop(x) for x, pdb in enumerate(pdb_list) if not results.keys().count(pdb.upper())]
#print search
#print pdb_list



image_data = command.get("data", {}).get("image_data")
run_data = command.get("data", {}).get("run_data")

image_data["start"] = run_data.get("start_image_number")
print image_data["start"]
"""
clear_cluster()

"""
input = ['DATA_RANGE = 1 1200\n']
#tmp = ['DATA_RANGE', '1 1200\n']
#tmp = input[-1].split('=')
#print tmp
#first, last = tmp[-1].split()
first, last = input[-1].split('=')[-1].split()
if int(last) == (int(1)+ int(1200) - 1):
    print 'gh'
#print first, type(first)
#print last, type(last)
"""

"""
cwd = '/gpfs6/users/necat/rapd2/integrate/2018-04-12/L13/rapd_analysis_L13_1_free'
os.chdir(cwd)
#command = "phenix.xtriage %s scaling.input.xray_data.obs_labels=\"I(+),\
#SIGI(+),I(-),SIGI(-)\" scaling.input.parameters.reporting.loggraphs=True" % '/gpfs6/users/necat/rapd2/integrate/2018-04-12/L13/L13_1/L13_1_free.mtz'
command = "molrep -f %s -i << stop\n_DOC  Y\n_RESMAX 4\n_RESMIN 9\nstop"% '/gpfs6/users/necat/rapd2/integrate/2018-04-12/L13/L13_1/L13_1_free.mtz'

pid_queue = Queue()
job = Process(target=process.local_subprocess, kwargs={'command': command,
                                                       'result_queue': pid_queue,
                                                       'logfile' : "molrep_selfrf.log",
                                                       'pid_queue':pid_queue,
                                                       'shell': True})
job.start()
print pid_queue.get()
print pid_queue.get()




cwd = '/gpfs6/users/necat/rapd2/integrate/2018-04-12/L13/rapd_analysis_L13_1_free'
os.chdir(cwd)
# Start logger
#id,_ = os.path.splitext(os.path.basename(fpath))
log = utils.log.get_logger(logfile_dir=cwd, logfile_id='testing')

plugin_queue = Queue()
plugin = plugins.analysis.plugin

analysis_command = {'preferences': {'dir_up': False, 'json': False, 'clean': True, 'nproc': 1, 'test': False, 'progress': False, 'pdbquery': False, 'show_plots': False, 'sample_type': 'default', 'run_mode': 'subprocess'}, 
                    'directories': {'work': u'/gpfs6/users/necat/rapd2/integrate/2018-04-12/L13/rapd_analysis_L13_1_free'}, 
                    'queue': plugin_queue, 
                    'input_data': {'datafile': u'/gpfs6/users/necat/rapd2/integrate/2018-04-12/L13/L13_1/L13_1_free.mtz'}, 
                    'process_id': 'ffbfd87e3e5711e8911c002590757122', 
                    'command': 'ANALYSIS'}


plugin_instance = plugin.RapdPlugin(analysis_command,
                                    logger = log,
                                    verbosity = True
                                    )

plugin_instance.start()

while True:
    analysis_result = plugin_queue.get()
    #self.results["results"]["analysis"] = analysis_result
    #self.send_results(self.results)
    print analysis_result['process']["status"]
    if analysis_result['process']["status"] in (-1, 100):
        print 'end'
        break

#analysis_result = plugin_queue.get()
#pprint(analysis_result)

#with open('/gpfs6/users/necat/Jon/RAPD_test/Output/logfile.log', 'w') as sys.stdout:
job = subprocess.Popen(shlex.split('eiger2cbf /gpfs6/users/necat/Jon/RAPD_test/Images/LSCAT/Ni-edge-n59d-kda28cl36cf57h_001_master.h5 1 /gpfs6/users/necat/Jon/RAPD_test/Output/cbf_files/Ni-edge-n59d-kda28cl36cf57h_001_000001.cbf'),
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
stdout, stderr = job.communicate()
#job.wait()
print stderr


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

red = connect_remote_redis()

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
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/cwru/kiser_E_3619/images/philip/runs/PDK014_1/PDK014_1_2_000001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/harvard/kahne_E_3623/images/tristan/runs/KAHN012_14/KAHN012_14_1_000001.cbf')
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
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/harvard/Wagner_E_3064/images/evangelos/snaps/GW02XF07_PAIR_0_000001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/columbia/hendrickson_E_3093/images/wwang/runs/Hend03_04/Hend03_04_1_001075.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/columbia/hendrickson_E_3093/images/wwang/runs/CPS3509_03/CPS3509_03_1_000001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/mskcc/patel_E_3080/images/hui/runs/hy_640_9/hy_640_9_1_000002.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/mskcc/patel_E_2891/images/juncheng/snaps/chengwI5_PAIR_0_000005.cbf'),
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/mskcc/patel_E_2891/images/juncheng/snaps/chengwI5_PAIR_0_000006.cbf'),
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/columbia/Mancia_E_3109/images/meagan/snaps/man2_3_0_000001.cbf'), # no index
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/slri/sicheri_E_3136/images/Igor/runs/VP03_MKTYc/VP03_MKTYc_1_000001/VP03_MKTYc_1_000001.cbf'),
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/slri/sicheri_E_3136/images/Igor/runs/VP03_MKTYc/VP03_MKTYc_1_000001/VP03_MKTYc_1_000002.cbf'),
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/harvard/haowu_E_3143/images/liwang/runs/hw1_7/hw1_7_1_000001/hw1_7_1_000001.cbf'),
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/upenn/christianson_E_3591/images/nicholas/runs/0004_12/0004_12_1_000001.cbf'),

#red.lpush('images_collected:NECAT_E', '/gpfs2/users/upenn/christianson_E_3591/images/jeremy/runs/JDO_PUCK2_A14_Run4/JDO_PUCK2_A14_Run4_1_000001.cbf'),
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/cornell/heninglin_E_3589/images/ian/runs/P113_11/P113_11_1_000001.cbf'),
#red.lpush('images_collected:NECAT_C', '/gpfs1/users/yale/konigsberg_C_3608/images/aristidis/runs/CPS4580_C1r1/0_0/CPS4580_C1r1_1_0001.cbf'),
#red.lpush('images_collected:NECAT_C', '/gpfs1/users/necat/necat_C_3303/images/Igor/runs/thaum5_05s_05d/0_0/thaum5_05s-05d_1_0001.cbf'),
#red.lpush('images_collected:NECAT_C', '/gpfs1/users/columbia/hendrickson_C_4084/images/liu/runs/BNL138_8/0_0/BNL138_8_1_0937.cbf'),

#red.lpush('images_collected:SERCAT_ID', '/data/ID_GSK_20171101.raw/11_01_2017_APS22id/screen/GSK8P9_AR.0002'),
#red.lpush('images_collected:SERCAT_ID', '/data/ID_MDAnderson_mdanderson.raw/TJ/ATG_70164_07_13/IACS-07_Pn13.0001'),
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/sinai/jin_E_3213/images/babault/snaps/JJ1_A3_PAIR_0_000003/JJ1_A3_PAIR_0_000003.cbf')
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/yale/strobel_E_3222/images/caroline/runs/SAS001_14/SAS001_14_1_000001/SAS001_14_1_000001.cbf')
#red.lpush('images_collected:SERCAT_ID', '/data/raw/ID_17_11_08_20171108_AMA/CRC-5p2/CRC-5_Pn2.0001'),
#red.lpush('images_collected:SERCAT_ID', '/data/raw/ID_17_11_08_UNC_KE/Puck41_pn7_IDbeam_2/UNC-41_Pn7.0312'),
#red.lpush('images_collected:SERCAT_ID', '/data/ID_GSK_20171101.raw/11_01_2017_APS22id/screen/GSK8P9_AR.0002'),
#red.lpush('images_collected:SERCAT_ID', '/data//raw/BM_17_11_21_GSK_20171121/11_21_2017_APS22bm/screen/P300_GSK3925257A_2_r1_s.0001'),
#red.lpush('images_collected:NECAT_E', '/epu2/rdma/gpfs2/users/fandm/piro_E_3242/images/christine/runs/149pN3F_x04/149pN3F_x04_1_000001/149pN3F_x04_1_000001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/cornell/heninglin_E_3513/images/ian/runs/apr4_127_05nme2/apr4_127_05nme2_1_000001.cbf')
#red.lpush('images_collected:NECAT_C', '/gpfs1/users/upenn/marmorstein_C_3520/images/adam/runs/DF_007_15/0_0/DF_007_15_1_0001.cbf')
#red.lpush('images_collected:NECAT_E', '/gpfs2/users/wustl/yuan_E_3516/images/feifei/runs/py3255/py3255_1_000001.cbf')
#red.lpush('images_collected:NECAT_E', '')
#print red.llen('run_data:NECAT_E')
#r = red.rpop('run_data:NECAT_E')
#red.lpush('runs_data:NECAT_E', r)
#print red.llen('run_data:NECAT_E')
#print red.llen('run_info_E')
#print red.llen('runs_data:NECAT_E')
#print red.llen('runs_data:NECAT_C')
#print red.lrange('runs_data:NECAT_E', 0, -1)
#print red
#red.delete('runs_data:NECAT_E')

#print red.lrange('run_data:NECAT_E', 0, -1)

#print red.llen('current_run_C')

print red.llen('RAPD_QSUB_JOBS_2')
#red.delete('RAPD_QSUB_JOBS_0')
print red.llen('images_collected:NECAT_E')
#red.delete("images_collected:NECAT_E")
print red.llen('images_collected:NECAT_C')
#red.delete("images_collected:NECAT_C")
print red.llen('run_info_E')
#red.delete('run_info_E')
print red.llen('run_info_C')
#red.delete('run_info_C')
print red.llen('runs_data:NECAT_E')
#print red.lrange('runs_data:NECAT_E', 0, 1)
#red.delete("runs_data:NECAT_E")
print red.llen('runs_data:NECAT_C')
#red.delete("runs_data:NECAT_C")
#print red.lrange('runs_data:NECAT_C', 0, -1)
#red.delete("runs_data:NECAT_C")
print red.llen('RAPD_JOBS_WAITING')
#red.delete('RAPD_JOBS_WAITING')
print red.llen('RAPD_QSUB_JOBS_2')
#red.delete('RAPD_QSUB_JOBS_2')





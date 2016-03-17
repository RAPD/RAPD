import os
#import rapd_utils as Utils
#import rapd_beamlinespecific as BLspec
#Utils.readMarHeader('/gpfs6/users/necat/Jon/Programs/CCTBX_x64/modules/dials_regression/image_examples/APS_22ID/junk_r1_1.0001')
from multiprocessing import Process, Queue
import subprocess
from src.sites.cluster.sercat import process_cluster2 

class Junk2(Process):
  def __init__(self):
    Process.__init__(self,)
    self.start()
  
  def run(self):
    self.test1()
    
  def test1(self):
    os.chdir('/home/schuerjp/temp/Junk')
    queue = Queue()
    #command = '/home/schuerjp/Programs/RAPD/bin/rapd.python /home/schuerjp/Programs/RAPD/src/agents/rapd_agent_strategy.py'
    command = '/home/schuerjp/Programs/RAPD/bin/rapd.python /home/schuerjp/Programs/RAPD/junk.py'
    #command = 'junk1.sh'
    job = Process(target=process_cluster2,args=(self,(command,'test.log'),queue))
    #job = Process(target=process_cluster2,args=(self,(command,'test.log')))
    job.start()
    print queue.get()
  
  def test2(self):
    os.chdir('/home/schuerjp/temp/Junk')
    f = open('junk1.sh','w')
    print >>f, "/home/schuerjp/Programs/RAPD/bin/rapd.python /home/schuerjp/Programs/RAPD/junk.py"
    f.close()
    command = 'qsub junk1.sh'
    myoutput = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  
  def test3(self):
    os.chdir('/home/schuerjp/temp/Junk')
    queue = Queue()
    command = 'touch this'
    job = Process(target=process_cluster2,args=(self,(command,'j.log'),queue))
    job.start()
    print queue.get() 
    
    
if __name__ == '__main__':
  Junk2()

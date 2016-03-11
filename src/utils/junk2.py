import os
import rapd_utils as Utils
import rapd_beamlinespecific as BLspec
#Utils.readMarHeader('/gpfs6/users/necat/Jon/Programs/CCTBX_x64/modules/dials_regression/image_examples/APS_22ID/junk_r1_1.0001')
from multiprocessing import Process, Queue

class Junk(Process):
  def __init__(self):
    Process.__init__(self,)
    self.start()
  
  def run(self):
    os.chdir('/home/schuerjp/temp')
    queue = Queue()
    command = '/home/schuerjp/Programs/RAPD/bin/rapd.python /home/schuerjp/Programs/RAPD/src/agents/rapd_agent_strategy.py'
    job = Process(target=BLspec.processClusterSercat,args=(self,(command,'labelit.log'),queue))
    job.start()
    print queue.get()
    
if __name__ == '__main__':
  Junk()
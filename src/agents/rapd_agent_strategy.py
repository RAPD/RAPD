"""
This file is part of RAPD

Copyright (C) 2009-2016, Cornell University
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

__created__ = "2009-07-14"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Production"

"""
An autoindex & strategy rapd_agent
"""

# Standard imports
from multiprocessing import Process, Queue, Event
import os
import shutil
import subprocess
import time

# RAPD imports
import rapd_beamlinespecific as BLspec
import src.agents.subcontractors.parse as Parse
import src.agents.subcontractors.summary as Summary
from src.agents.subcontractors.xoalign import RunXOalign
from utils.communicate import rapd_send
import utils.xutils as Utils

# This is an active rapd agent
RAPD_AGENT = True

# This handler's request type
AGENT_TYPE = "autoindex+strategy"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "3b3448aee4a811e59c0aac87a3333966"


class RapdAgent(Process):
  def __init__(self,input,logger=None):
    logger.info('AutoindexingStrategy.__init__')
    self.st = time.time()
    self.input                              = input
    self.logger                             = logger
    #Setting up data input
    self.setup                              = self.input[1]
    self.header                             = self.input[2]
    self.header2                            = False
    #if self.input[3].has_key('distance'):
    if self.input[3].has_key('fullname'):
        self.header2                            = self.input[3]
        self.preferences                        = self.input[4]
    else:
        self.preferences                        = self.input[3]
    self.controller_address                 = self.input[-1]

    #For testing individual modules (Will not run in Test mode on cluster!! Can be set at end of __init__.)
    self.test                               = False
    #Removes junk files and directories at end. (Will still clean on cluster!! Can be set at end of __init__.)
    self.clean                              = False
    #Runs in RAM (slightly faster), but difficult to debug.
    self.ram                                = False
    #Will not use RAM if self.cluster_use=True since runs would be on separate nodes. Slower (>10%). Mainly
    #used for rapd_agent_beamcenter.py to launch a lot of jobs at once.
    self.cluster_use                        = False
    #If self.cluster_use == True, you can specify a batch queue on your cluster. False to not specify.
    self.cluster_queue                      = 'index.q'
    #self.cluster_queue                      = False
    #Switch for verbose
    self.verbose                            = True
    #Number of Labelit iterations to run.
    self.iterations                         = 6

    #Set timer for distl. 'False' will disable.
    if self.header2:
        self.distl_timer                    = 60
    else:
        self.distl_timer                    = 30
    #Set strategy timer. 'False' disables.
    self.strategy_timer                     = 90
    #Set timer for XOAlign. 'False' will disable.
    self.xoalign_timer                      = 30

    #Turns on multiprocessing for everything
    #Turns on all iterations of Labelit running at once, sorts out highest symmetry solution, then continues...(much better!!)
    self.multiproc                          = True
    if self.preferences.has_key('multiprocessing'):
        if self.preferences.get('multiprocessing') == 'False':
            self.multiproc                          = False
    #Set for Eisenberg peptide work.
    self.sample_type = self.preferences.get('sample_type','Protein')
    if self.sample_type == 'Peptide':
        self.peptide     = True
    else:
        self.peptide     = False
    self.strategy = self.preferences.get('strategy_type','best')
    #Check to see if XOALign should run.
    if self.header.has_key('mk3_phi') and self.header.has_key('mk3_kappa'):
        self.minikappa        = True
    else:
        self.minikappa        = False
    #Check to see if multi-crystal strategy is requested.
    if self.preferences.get('reference_data_id') in (None, 0):
        self.multicrystalstrat = False
    else:
        self.multicrystalstrat = True
        self.strategy          = 'mosflm'

    #This is where I place my overall folder settings.
    self.working_dir                        = False
    #this is where I have chosen to place my results
    self.auto_summary                       = False
    self.labelit_log                        = {}
    self.labelit_results                    = {}
    self.labelit_summary                    = False
    self.labelit_failed                     = False
    self.distl_log                          = []
    self.distl_results                      = {}
    self.distl_summary                      = False
    self.raddose_results                    = False
    self.raddose_summary                    = False
    self.best_log                           = []
    self.best_results                       = False
    self.best_summary                       = False
    self.best1_summary                      = False
    self.best_summary_long                  = False
    self.best_anom_log                      = []
    self.best_anom_results                  = False
    self.best_anom_summary                  = False
    self.best1_anom_summary                 = False
    self.best_anom_summary_long             = False
    self.best_failed                        = False
    self.best_anom_failed                   = False
    self.rerun_best                         = False
    self.mosflm_strat_log                   = []
    self.mosflm_strat_anom_log              = []
    self.mosflm_strat_results               = {}
    self.mosflm_strat_anom_results          = {}
    self.mosflm_strat_summary               = False
    self.mosflm_strat1_summary              = False
    self.mosflm_strat_summary_long          = False
    self.mosflm_strat_anom_summary          = False
    self.mosflm_strat1_anom_summary         = False
    self.mosflm_strat_anom_summary_long     = False
    #Labelit settings
    self.index_number                       = False
    self.ignore_user_SG                     = False
    self.pseudotrans                        = False
    #Raddose settings
    self.volume                             = False
    self.calc_num_residues                  = False
    #Mosflm settings
    self.prev_sg                            = False
    #extra features for BEST
    self.high_dose                          = False
    self.crystal_life                       = None
    self.iso_B                              = False
    #dicts for running the Queues
    self.jobs                               = {}
    self.vips_images                        = {}

    #Settings for all programs
    self.beamline             = self.header.get('beamline')
    self.time                 = str(self.header.get('time','1.0'))
    self.wavelength           = str(self.header.get('wavelength'))
    self.transmission         = float(self.header.get('transmission'))
    #self.aperture             = str(self.header.get('md2_aperture'))
    self.spacegroup           = self.preferences.get('spacegroup')
    self.flux                 = str(self.header.get('flux'))
    self.solvent_content      = str(self.preferences.get('solvent_content',0.55))

    #Sets settings so I can view the HTML output on my machine (not in the RAPD GUI), and does not send results to database.
    #This is used to determine if job submitted by rapd_cluster or script was launched for testing.
    #******BEAMLINE SPECIFIC*****
    if self.header.has_key('acc_time'):
        self.gui                   = True
        self.test                  = False
        self.clean                 = True
        #self.verbose               = False
    else:
        self.gui                   = False
    #******BEAMLINE SPECIFIC*****

    Process.__init__(self,name='AutoindexingStrategy')
    self.start()

  def setup_cluster(self):
      """Import cluster functions"""

      self.logger.debug("setup_cluster")

      

  def run(self):
    """
    Convoluted path of modules to run.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::run')
    self.preprocess()
    if self.minikappa:
      self.processXOalign()
    else:
      #Make the labelit.png image
      self.makeImages(0)
      #Run Labelit
      self.processLabelit()

      #Gleb recommended, but in some cases takes several seconds to minutes longer to run Best??
      #if self.pilatus:
      #    if self.preferences.get('strategy_type') == 'best':
      #        self.processXDSbg()

      #Sorts labelit results by highest symmetry.
      self.labelitSort()
      #If there is a solution, then calculate a strategy.
      if self.labelit_failed == False:
        #Start distl.signal_strength for the correct labelit iteration
        self.processDistl()
        if self.multiproc == False:
            self.postprocessDistl()
        self.preprocessRaddose()
        self.processRaddose()
        self.processStrategy()
        self.Queue()
        #Get the distl results
        if self.multiproc:
            self.postprocessDistl()
      #Make PHP files for GUI, passback results, and cleanup.
      self.postprocess()

  def preprocess(self):
    """
    Setup the working dir in the RAM and save the dir where the results will go at the end.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::preprocess')
    #Determine detector vendortype
    self.vendortype = Utils.getVendortype(self,self.header)
    """
    #For determining detector type. Same notation as CCTBX.
    #Grab the beamline info from rapd_site.py that give the specifics of this beamline.
    #You will have to modify how a beamline/detector is selected. If multiple detectors
    #of same type, you could look at S/N.
    if self.header.get('fullname')[-3:] == 'cbf':
      if float(self.header.get('beam_center_y')) > 200.0:
        self.vendortype = 'Pilatus-6M'
      else:
        self.vendortype = 'ADSC-HF4M'
    else:
      self.vendortype = 'ADSC'
    """
    self.dest_dir = self.setup.get('work')
    if self.test or self.cluster_use:
      self.working_dir = self.dest_dir
    elif self.ram:
        self.working_dir = '/dev/shm/%s'%self.dest_dir[1:]
    else:
      self.working_dir = self.dest_dir
    if os.path.exists(self.working_dir) == False:
      os.makedirs(self.working_dir)
    os.chdir(self.working_dir)
    if self.verbose:
      #print out recognition of the program being used
      self.PrintInfo()
    #Setup event for job control on cluster
    if self.cluster_use:
      self.running = Event()
      self.running.set()

  def preprocessRaddose(self):
    """
    Create the raddose.com file which will run in processRaddose. Several beamline specific entries for flux and
    aperture size passed in from rapd_site.py
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::preprocessRaddose')
    try:
      #Get unit cell
      cell = Utils.getLabelitCell(self)
      nres = Utils.calcTotResNumber(self,self.volume)
      #Adding these typically does not change the Best strategy much, if it at all.
      patm                 = False
      satm                 = False
      if self.sample_type == 'Ribosome':
        crystal_size_x = '1'
        crystal_size_y = '0.5'
        crystal_size_z = '0.5'
      else:
        #crystal dimensions (default 0.1 x 0.1 x 0.1 from rapd_site.py)
        crystal_size_x = str(float(self.preferences.get('crystal_size_x'))/1000.0)
        crystal_size_y = str(float(self.preferences.get('crystal_size_y'))/1000.0)
        crystal_size_z = str(float(self.preferences.get('crystal_size_z'))/1000.0)
      if self.header.has_key('flux'):
        beam_size_x = str(self.header.get('beam_size_x'))
        beam_size_y = str(self.header.get('beam_size_y'))
        gauss_x     = str(self.header.get('gauss_x'))
        gauss_y     = str(self.header.get('gauss_y'))
      """
      #**Beamline specific failsafe if aperture size is not sent correctly from MD2.
      if self.aperture == '0' or '-1':
        if self.beamline == '24_ID_C':
          self.aperture = '70'
        else:
          self.aperture = '50'
      #Get max crystal size to calculate the shape.(Currently disabled in Best, because no one changes it)
      #max_size      = float(max(crystal_size_x,crystal_size_y,crystal_size_z))
      #aperture      = float(self.aperture)/1000.0
      #self.shape    = max_size/aperture
      #put together the command script for Raddose
      """
      raddose = open('raddose.com', 'w+')
      setup = 'raddose << EOF\n'
      if beam_size_x and beam_size_y:
        setup += 'BEAM %s %s\n'%(beam_size_x,beam_size_y)
      #Full-width-half-max of the beam
      setup += 'GAUSS %s %s\nIMAGES 1\n'%(gauss_x,gauss_y)
      if self.flux:
        setup += 'PHOSEC %s\n'%self.flux
      else:
        setup += 'PHOSEC 3E10\n'
      if cell:
        setup += 'CELL %s %s %s %s %s %s\n'%(cell[0],cell[1],cell[2],cell[3],cell[4],cell[5])
      else:
        self.logger.debug('Could not get unit cell from bestfile.par')
      #Set default solvent content based on sample type. User can override.
      if self.solvent_content == '0.55':
        if self.sample_type == 'Protein':
          setup += 'SOLVENT 0.55\n'
        else:
          setup += 'SOLVENT 0.64\n'
      else:
        setup += 'SOLVENT %s\n'%self.solvent_content
      #Sets crystal dimensions. Input from dict (0.1 x 0.1 x 0.1 mm), but user can override.
      if crystal_size_x and crystal_size_y and crystal_size_z:
        setup += 'CRYSTAL %s %s %s\n'%(crystal_size_x,crystal_size_y,crystal_size_z)
      if self.wavelength:
        setup += 'WAVELENGTH %s\n'%self.wavelength
      if self.time:
        setup += 'EXPOSURE %s\n'%self.time
      setup += 'NMON 1\n'
      if self.sample_type == 'Protein':
        setup += 'NRES %s\n'%nres
      elif self.sample_type == 'DNA':
        setup += 'NDNA %s\n'%nres
      else:
        setup += 'NRNA %s\n'%nres
      if patm:
        setup += 'PATM %s\n'%patm
      if satm:
        setup += 'SATM %s\n'%satm
      setup += 'END\nEOF\n'
      raddose.writelines(setup)
      raddose.close()

    except:
      self.logger.exception('**ERROR in preprocessRaddose**')

  def processLabelit(self):
    """
    Initiate Labelit runs.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::runLabelit')
    try:
      #Setup queue for getting labelit log and results in labelitSort.
      self.labelitQueue = Queue()
      params = {}
      params['test'] = self.test
      params['cluster'] = self.cluster_use
      params['verbose'] = self.verbose
      params['cluster_queue'] = self.cluster_queue
      params['vendortype'] = self.vendortype
      if self.working_dir == self.dest_dir:
        inp = self.input
      else:
        inp = []
        inp.append('AUTOINDEX')
        inp.append({'work': self.working_dir})
        inp.extend(self.input[2:])
      Process(target=RunLabelit,args=(inp,self.labelitQueue,params,self.logger)).start()

    except:
      self.logger.exception('**Error in processLabelit**')

  def processXDSbg(self):
    """
    Calculate the BKGINIT.cbf for the background calc on the Pilatis. This is
    used in BEST.
    Gleb recommended this but it does not appear to make much difference except take longer.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::processXDSbg')
    try:
      name = str(self.header.get('fullname'))
      temp = name[name.rfind('_')+1:name.rfind('.')]
      new_name = name.replace(name[name.rfind('_')+1:name.rfind('.')],len(temp)*'?')
      #range = str(int(temp))+' '+str(int(temp))
      command  = 'JOB=XYCORR INIT\n'
      command += Utils.calcXDSbc(self)
      command += 'DETECTOR_DISTANCE=%s\n'%self.header.get('distance')
      command += 'OSCILLATION_RANGE=%s\n'%self.header.get('osc_range')
      command += 'X-RAY_WAVELENGTH=%s\n'%self.wavelength
      command += 'NAME_TEMPLATE_OF_DATA_FRAMES=%s\n'%new_name
      #command += 'BACKGROUND_RANGE='+range+'\n'
      #command += 'DATA_RANGE='+range+'\n'
      command += 'BACKGROUND_RANGE=%s %s\n'%(int(temp),int(temp))
      command += 'DATA_RANGE=%s %s\n'%(int(temp),int(temp))
      command += 'DIRECTION_OF_DETECTOR_Y-AXIS=0.0 1.0 0.0\n'
      command += 'DETECTOR=PILATUS         MINIMUM_VALID_PIXEL_VALUE=0  OVERLOAD=1048500\n'
      command += 'SENSOR_THICKNESS=0.32        !SILICON=-1.0\n'
      command += 'NX=2463 NY=2527 QX=0.172  QY=0.172  !PILATUS 6M\n'
      command += 'DIRECTION_OF_DETECTOR_X-AXIS= 1.0 0.0 0.0\n'
      command += 'TRUSTED_REGION=0.0 1.05 !Relative radii limiting trusted detector region\n'
      command += 'UNTRUSTED_RECTANGLE= 487  493     0 2528\n'
      command += 'UNTRUSTED_RECTANGLE= 981  987     0 2528\n'
      command += 'UNTRUSTED_RECTANGLE=1475 1481     0 2528\n'
      command += 'UNTRUSTED_RECTANGLE=1969 1975     0 2528\n'
      command += 'UNTRUSTED_RECTANGLE=   0 2464   195  211\n'
      command += 'UNTRUSTED_RECTANGLE=   0 2464   407  423\n'
      command += 'UNTRUSTED_RECTANGLE=   0 2464   619  635\n'
      command += 'UNTRUSTED_RECTANGLE=   0 2464   831  847\n'
      command += 'UNTRUSTED_RECTANGLE=   0 2464  1043 1059\n'
      command += 'UNTRUSTED_RECTANGLE=   0 2464  1255 1271\n'
      command += 'UNTRUSTED_RECTANGLE=   0 2464  1467 1483\n'
      command += 'UNTRUSTED_RECTANGLE=   0 2464  1679 1695\n'
      command += 'UNTRUSTED_RECTANGLE=   0 2464  1891 1907\n'
      command += 'UNTRUSTED_RECTANGLE=   0 2464  2103 2119\n'
      command += 'UNTRUSTED_RECTANGLE=   0 2464  2315 2331\n'
      command += 'ROTATION_AXIS= 1.0 0.0 0.0\n'
      command += 'INCIDENT_BEAM_DIRECTION=0.0 0.0 1.0\n'
      command += 'FRACTION_OF_POLARIZATION=0.99 !default=0.5 for unpolarized beam\n'
      command += 'POLARIZATION_PLANE_NORMAL= 0.0 1.0 0.0\n'
      f = open('XDS.INP','w')
      f.writelines(command)
      f.close()
      Process(target=Utils.processLocal,args=('xds_par',self.logger)).start()

    except:
      self.logger.exception('**Error in ProcessXDSbg.**')

  def processDistl(self):
    """
    Setup Distl for multiprocessing if enabled.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::processDistl')
    try:
      self.distl_output = []
      l = ['','2']
      f = 1
      if self.header2:
        f = 2
      for i in range(0,f):
        if self.test:
          inp = 'ls'
          job = Process(target=Utils.processLocal,args=(inp,self.logger))
        else:
          inp = 'distl.signal_strength %s'%eval('self.header%s'%l[i]).get('fullname')
          job = Process(target=Utils.processLocal,args=((inp,'distl%s.log'%i),self.logger))
        job.start()
        self.distl_output.append(job)

    except:
      self.logger.exception('**Error in ProcessDistl.**')

  def processRaddose(self):
    """
    Run Raddose.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::processRaddose')
    self.raddose_log = []
    try:
      self.raddose_log.append('tcsh raddose.com\n')
      output = subprocess.Popen('tcsh raddose.com',shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
      output.wait()
      for line in output.stdout:
          self.raddose_log.append(line)

    except:
      self.logger.exception('**ERROR in processRaddose**')
    raddose = Parse.ParseOutputRaddose(self,self.raddose_log)
    self.raddose_results = { 'Raddose results' : raddose }
    if self.raddose_results['Raddose results'] == None:
      self.raddose_results = { 'Raddose results' : 'FAILED'}
      if self.verbose:
        self.logger.debug('Raddose failed')

  def processBest(self,iteration=0,runbefore=False):
    """
    Construct the Best command and run. Passes back dict with PID:anom.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::processBest')
    try:
      #Get the beamline settings from rapd_site.py.
      if self.vendortype in ['Pilatus-6M','ADSC-HF4M']:
        from rapd_site import settings_C as settings
      else:
        from rapd_site import settings_E as settings
      max_dis = settings.get('max_distance')
      min_dis = settings.get('min_distance')
      min_d_o = settings.get('min_del_omega')
      min_e_t = settings.get('min_exp_time')

      image_number = []
      image_number.append(self.header.get('fullname')[self.header.get('fullname').rfind('_')+1:self.header.get('fullname').rfind('.')])
      if self.header2:
        image_number.append(self.header2.get('fullname')[self.header2.get('fullname').rfind('_')+1:self.header2.get('fullname').rfind('.')])
      #Tell Best if two-theta is being used.
      if int(float(self.header.get('twotheta'))) != 0:
        Utils.fixBestfile(self)
      #if Raddose failed, here are the defaults.
      dose         = 100000.0
      exp_dose_lim = 300
      if self.raddose_results:
        if self.raddose_results.get('Raddose results') != 'FAILED':
          dose         = self.raddose_results.get('Raddose results').get('dose per image')
          exp_dose_lim = self.raddose_results.get('Raddose results').get('exp dose limit')
      #Set how many frames a crystal will last at current exposure time.
      self.crystal_life = str(int(float(exp_dose_lim) / float(self.time)))
      if self.crystal_life == '0':
        self.crystal_life = '1'
      #Adjust dose for ribosome crystals.
      if self.sample_type == 'Ribosome':
        dose = 500001
      #If dose is too high, warns user and sets to reasonable amount and reruns Best but give warning.
      if dose > 500000:
        dose           = 500000
        exp_dose_lim   = 100
        self.high_dose = True
        if iteration == 1:
          dose         = 100000.0
          exp_dose_lim = 300
        if iteration == 2:
          dose         = 100000.0
          exp_dose_lim = False
        if iteration == 3:
          dose         = False
          exp_dose_lim = False
      #put together the command for labelit.index
      if self.vendortype == 'Pilatus-6M':
        command = 'best -f pilatus6m'
      elif self.vendortype == 'ADSC-HF4M':
        command = 'best -f hf4m'
      else:
        command = 'best -f q315'
        if str(self.header.get('binning')) == '2x2':
            command += '-2x'
      if self.high_dose:
        command += ' -t 1.0'
      else:
        command += ' -t %s'%self.time
      command += ' -e %s -sh %s -su %s'%(self.preferences.get('best_complexity','none'),\
                                         self.preferences.get('shape','2.0'),self.preferences.get('susceptibility','1.0'))
      if self.preferences.get('aimed_res') != 0.0:
        command += ' -r %s'%self.preferences.get('aimed_res')
      command += ' -Trans %s'%self.transmission
      #Set minimum rotation width per frame. Different for PAR and CCD detectors.
      command += ' -w %s'%min_d_o
      #Set minimum exposure time per frame.
      command += ' -M %s'%min_e_t
      #Set min and max detector distance
      command += ' -DIS_MAX %s -DIS_MIN %s'%(max_dis,min_dis)
      #Fix bug in BEST for PAR detectors. Use the cumulative completeness of 99% instead of all bin.
      if self.vendortype in ('Pilatus-6M','ADSC-HF4M'):
        command += ' -low never'
      #set dose  and limit, else set time
      if dose:
        command += ' -GpS %s -DMAX 30000000'%dose
      else:
        command += ' -T 185'
      if runbefore:
        command += ' -p %s %s'%(runbefore[0],runbefore[1])
      command1 = command
      command1 += ' -a -o best_anom.plt -dna best_anom.xml'
      command += ' -o best.plt -dna best.xml'
      end = ' -mos bestfile.dat bestfile.par %s_%s.hkl '%(self.index_number,image_number[0])
      """
      if self.pilatus:
        if os.path.exists(os.path.join(self.working_dir,'BKGINIT.cbf')):
          end = ' -MXDS bestfile.par BKGINIT.cbf %s_%s.hkl '%(self.index_number,image_number[0])
      """
      if self.header2:
        end += '%s_%s.hkl'%(self.index_number,image_number[1])
      command  += end
      command1 += end
      d = {}
      jobs = {}
      l = [(command,''),(command1,'_anom')]
      st  = 0
      end1 = 2
      if runbefore:
        st  = runbefore[2]
        end1 = runbefore[3]
      for i in range(st,end1):
        log = os.path.join(os.getcwd(),'best%s.log'%l[i][1])
        if self.verbose:
          self.logger.debug(l[i][0])
        #Save the path of the log
        d.update({'log'+l[i][1]:log})
        if self.test == False:
          if self.cluster_use:
            jobs[str(i)] = Process(target=BLspec.processCluster, args=(self, (l[i][0], log, self.cluster_queue)))
          else:
            jobs[str(i)] = Process(target=BestAction, args=((l[i][0], log), self.logger))
          jobs[str(i)].start()
      #Check if Best should rerun since original Best strategy is too long for Pilatis using correct start and end from plots. (Way around bug in BEST.)
      if self.test == False:
        if runbefore == False:
          counter = 2
          while counter > 0:
            for job in jobs.keys():
              if jobs[job].is_alive() == False:
                del jobs[job]
                start,ran = self.findBestStrat(d['log'+l[int(job)][1]].replace('log','plt'))
                if start != False:
                    self.processBest(iteration,(start,ran,int(job),int(job)+1))
                counter -= 1
            time.sleep(0.1)

    except:
      self.logger.exception('**Error in processBest**')

  def processMosflm(self):
    """
    Creates Mosflm executable for running strategy and run. Passes back dict with PID:logfile.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::processMosflm')
    try:
      l = [('mosflm_strat','',''),('mosflm_strat_anom','_anom','ANOMALOUS')]
      #Opens file from Labelit/Mosflm autoindexing and edit it to run a strategy.
      mosflm_rot = str(self.preferences.get('mosflm_rot'))
      mosflm_seg = str(self.preferences.get('mosflm_seg'))
      mosflm_st  = str(self.preferences.get('mosflm_start'))
      mosflm_end = str(self.preferences.get('mosflm_end'))
      #Does the user request a start or end range?
      range1 = False
      if mosflm_st != '0.0':
        range1 = True
      if mosflm_end != '360.0':
        range1 = True
      if range1:
        if mosflm_rot == '0.0':
          #mosflm_rot = str(360/float(Utils.symopsSG(self,Utils.getMosflmSG(self))))
          mosflm_rot = str(360/float(Utils.symopsSG(self,Utils.getLabelitCell(self,'sym'))))
      #Save info from previous data collections.
      if self.multicrystalstrat:
        ref_data = self.preferences.get('reference_data')
        if self.spacegroup == 'None':
          self.spacegroup = ref_data[0][-1]
          Utils.fixMosflmSG(self)
          #For posting in summary
          self.prev_sg = True
      else:
        ref_data = False
      #Run twice for regular and anomalous strategies.
      for i in range(0,2):
        shutil.copy(self.index_number,l[i][0])
        temp = []
        #Read the Mosflm input file from Labelit and use only the top part.
        for x,line in enumerate(open(l[i][0],'r').readlines()):
          temp.append(line)
          if line.count('ipmosflm'):
              newline = line.replace(self.index_number,l[i][0])
              temp.remove(line)
              temp.insert(x,newline)
          if line.count('FINDSPOTS'):
              im = line.split()[-1]
          if line.startswith('MATRIX'):
              fi = x
        #Load the image as per Andrew Leslie for Mosflm bug.
        new_line = 'IMAGE %s\nLOAD\nGO\n'%im
        #New lines for strategy calculation
        if ref_data:
          for x in range(len(ref_data)):
            new_line += 'MATRIX %s\nSTRATEGY start %s end %s PARTS %s\nGO\n'%(ref_data[x][0],ref_data[x][1],ref_data[x][2],len(ref_data)+1)
          new_line += 'MATRIX %s.mat\n'%self.index_number
        if range1:
          new_line += 'STRATEGY START %s END %s\nGO\n'%(mosflm_st,mosflm_end)
          new_line += 'ROTATE %s SEGMENTS %s %s\n'%(mosflm_rot,mosflm_seg,l[i][2])
        else:
          if mosflm_rot == '0.0':
            new_line += 'STRATEGY AUTO %s\n'%l[i][2]
          elif mosflm_seg != '1':
            new_line += 'STRATEGY AUTO ROTATE %s SEGMENTS %s %s\n'%(mosflm_rot,mosflm_seg,l[i][2])
          else:
            new_line += 'STRATEGY AUTO ROTATE %s %s\n'%(mosflm_rot,l[i][2])
        new_line += 'GO\nSTATS\nEXIT\neof\n'
        if self.test == False:
          new = open(l[i][0],'w')
          new.writelines(temp[:fi+1])
          new.writelines(new_line)
          new.close()
          log = os.path.join(os.getcwd(),l[i][0]+'.out')
          inp = 'tcsh %s'%l[i][0]
          if self.cluster_use:
            Process(target=BLspec.processCluster,args=(self,(inp,log,self.cluster_queue))).start()
          else:
            Process(target=Utils.processLocal,args=(inp,self.logger)).start()

    except:
      self.logger.exception('**Error in processMosflm**')

  def processStrategy(self,iteration=False):
    """
    Initiate all the strategy runs using multiprocessing.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::processStrategy')
    try:
      if iteration:
        st  = iteration
        end = iteration+1
      else:
        st  = 0
        end = 5
        if self.strategy == 'mosflm':
          st = 4
        if self.multiproc == False:
          end = st+1
      for i in range(st,end):
        if i == 4:
          Utils.folders(self,self.labelit_dir)
          job = Process(target=self.processMosflm,name='mosflm%s'%i)
        else:
          Utils.foldersStrategy(self,os.path.join(os.path.basename(self.labelit_dir),str(i)))
          #Reduces resolution and reruns Mosflm to calc new files, then runs Best.
          job = Process(target=Utils.errorBest,name='best%s'%i,args=(self,i))
        job.start()
        self.jobs[str(i)] = job

    except:
      self.logger.exception('**Error in processStrategy**')

  def processXOalign(self):
    """
    Run XOalign using rapd_agent_xoalign.py
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::processXOalign')
    try:
      params = {}
      params['xoalign_timer'] = self.xoalign_timer
      params['test'] = self.test
      params['gui'] = self.gui
      params['dir'] = self.dest_dir
      params['clean'] = self.clean
      params['verbose'] = self.verbose
      Process(target=RunXOalign, args=(self.input, params, self.logger)).start()

    except:
      self.logger.exception('**ERROR in processXOalign**')

  def postprocessDistl(self):
    """
    Send Distl log to parsing and make sure it didn't fail. Save output dict.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::postprocessDistl')
    try:
      timer = 0
      while len(self.distl_output) != 0:
        for job in self.distl_output:
          if job.is_alive() == False:
            self.distl_output.remove(job)
        time.sleep(0.2)
        timer += 0.2
        if self.verbose:
          number = round(timer%1,1)
          if number in (0.0,1.0):
            print 'Waiting for Distl to finish %s seconds'%timer
        if self.distl_timer:
          if timer >= self.distl_timer:
            job.terminate()
            self.distl_output.remove(job)
            self.distl_log.append('Distl timed out\n')
            if self.verbose:
              print 'Distl timed out.'
              self.logger.debug('Distl timed out.')

      os.chdir(self.labelit_dir)
      f = 1
      if self.header2:
        f = 2
      for x in range(0,f):
        log = open('distl%s.log'%x,'r').readlines()
        self.distl_log.extend(log)
        distl = Parse.ParseOutputDistl(self,log)
        if distl == None:
          self.distl_results = {'Distl results':'FAILED'}
        else:
          self.distl_results[str(x)] = {'Distl results': distl}
      Utils.distlComb(self)

    except:
      self.logger.exception('**Error in postprocessDistl.**')

  def postprocessBest(self,inp,runbefore=False):
    """
    Send Best log to parsing and save output dict. Error check the results and rerun if neccessary.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::postprocessBest')
    try:
      xml = 'None'
      anom = False
      if inp.count('anom'):
        anom = True
      log = open(inp,'r').readlines()
      if os.path.exists(inp.replace('log','xml')):
        xml = open(inp.replace('log','xml'),'r').readlines()
      iteration = os.path.dirname(inp)[-1]
      if anom:
        self.best_anom_log.extend(log)
      else:
        self.best_log.extend(log)

    except:
      self.logger.exception('**Error in postprocessBest.**')

    data = Parse.ParseOutputBest(self,(log,xml),anom)
    #print data.get('strategy res limit')
    if self.labelit_results['Labelit results'] != 'FAILED':
      #Best error checking. Most errors caused by B-factor calculation problem.
      #If no errors...
      if type(data) == dict:
        data.update({'directory':os.path.dirname(inp)})
        if anom:
          self.best_anom_results = {'Best ANOM results':data}
        else:
          self.best_results = {'Best results':data}
        return('OK')
      else:
        if self.multiproc == False:
          out = {'None'        :'No Best Strategy.',
                 'neg B'       :'Adjusting resolution',
                 'isotropic B' :'Isotropic B detected'}
          if out.has_key(data):
            Utils.errorBestPost(self,iteration,out[data],anom)
        return('FAILED')

  def postprocessMosflm(self,inp):
    """
    Pass Mosflm log into parsing and save output dict.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::postprocessMosflm')
    try:
      if inp.count('anom'):
        l = ['ANOM','self.mosflm_strat_anom','Mosflm ANOM strategy results']
      else:
        l = ['','self.mosflm_strat','Mosflm strategy results']
      out = open(inp,'r').readlines()
      eval('%s_log'%l[1]).extend(out)
    except:
      self.logger.exception('**ERROR in postprocessMosflm**')

    data = Parse.ParseOutputMosflm_strat(self,out,inp.count('anom'))
    if data == None:
      if self.verbose:
        self.logger.debug('No Mosflm %s strategy.'%l[0])
      eval('%s_results'%l[1]).update({ l[2] : 'FAILED' })
    elif data == 'sym':
      if self.verbose:
        self.logger.debug('dataset symmetry not compatible with autoindex symmetry')
      eval('%s_results'%l[1]).update({ l[2] : 'SYM' })
    else:
      eval('%s_results'%l[1]).update({ l[2] : data })

  def Queue(self):
    """
    Queue for strategy.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::Queue')
    try:
      def set_best_results(i,x):
        #Set Best output if it failed after 3 tries
        if i == 3:
          if x == 0:
            self.best_results = { 'Best results' : 'FAILED'}
            self.best_failed = True
          else:
            self.best_anom_results = { 'Best ANOM results' : 'FAILED'}
            self.best_anom_failed = True

      st = 0
      if self.strategy == 'mosflm':
        st = 4
      #dict = {}
      #Run twice for regular(0) and anomalous(1) strategies
      l = ['','_anom']
      for x in range(0,2):
        for i in range(st,5):
          timed_out = False
          timer = 0
          job = self.jobs[str(i)]
          while 1:
            if job.is_alive() == False:
              if i == 4:
                log = os.path.join(self.labelit_dir,'mosflm_strat%s.out'%l[x])
              else:
                log = os.path.join(self.labelit_dir,str(i))+'/best%s.log'%l[x]
              break
            time.sleep(0.1)
            timer += 0.1
            if self.verbose:
              number = round(timer%1,1)
              if number in (0.0,1.0):
                print 'Waiting for strategy to finish %s seconds'%timer
            if self.strategy_timer:
              if timer >= self.strategy_timer:
                timed_out = True
                break
          if timed_out:
            set_best_results(i,x)
          else:
            if i == 4:
              self.postprocessMosflm(log)
            else:
              job1 = self.postprocessBest(log)
              if job1 == 'OK':
                break
              #If Best failed...
              else:
                if self.multiproc == False:
                  self.processStrategy(i+1)
                set_best_results(i,x)
            pass
      if self.test == False:
        if self.multiproc:
          if self.cluster_use:
            #kill child process on DRMAA job causes error on cluster.
            #turn off multiprocessing.event so any jobs still running on cluster are terminated.
            self.running.clear()
          else:
            #kill all the remaining running jobs
            for i in range(st,5):
              if self.jobs[str(i)].is_alive():
                if self.verbose:
                  self.logger.debug('terminating job: %s'%self.jobs[str(i)])
                Utils.killChildren(self,self.jobs[str(i)].pid)

    except:
      self.logger.exception('**Error in Queue**')

  def labelitSort(self):
    """
    Sort out which iteration of Labelit has the highest symmetry and choose that solution. If
    Labelit does not find a solution, finish up the pipeline.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::labelitSort')
    import numpy

    rms_list1 = []
    sg_list1 = []
    metric_list1 = []
    vol = []
    sg_dict  = {}
    sol_dict = {}
    sym = '0'
    try:
      #Get the results and logs
      self.labelit_results = self.labelitQueue.get()
      self.labelit_log = self.labelitQueue.get()

      for run in self.labelit_results.keys():
        if type(self.labelit_results[run].get('Labelit results')) == dict:
          #Check for pseudotranslation in any Labelit run
          if self.labelit_results[run].get('Labelit results').get('pseudotrans') == True:
              self.pseudotrans = True
          s,r,m,v = Utils.getLabelitStats(self,inp=run,simple=True)
          sg = Utils.convertSG(self,s)
          sg_dict[run] = sg
          sg_list1.append(float(sg))
          rms_list1.append(float(r))
          metric_list1.append(float(m))
          vol.append(v)
        else:
          #If Labelit failed, set dummy params
          sg_dict[run] = '0'
          sg_list1.append(0)
          rms_list1.append(100)
          metric_list1.append(100)
          vol.append('0')
      for x in range(len(sg_list1)):
        if sg_list1[x] == numpy.amax(sg_list1):
          #If its P1 look at the Mosflm RMS, else look at the Labelit metric.
          if str(sg_list1[x]) == '1.0':
            sol_dict[rms_list1[x]]    = self.labelit_results.keys()[x]
          else:
            sol_dict[metric_list1[x]] = self.labelit_results.keys()[x]
      l = sol_dict.keys()
      l.sort()
      #Best Labelit_results key
      highest = sol_dict[l[0]]
      #Since iter 5 cuts res, it is often the best. Only choose if its the only solution.
      if len(l) > 1:
        if highest == '5':
          highest = sol_dict[l[1]]
      #symmetry of best solution
      sym = sg_dict[highest]
      #If there is a solution...
      if sym != '0':
        self.logger.debug('The sorted labelit solution was #%s'%highest)
        #Save best results in corect place.
        self.labelit_results = self.labelit_results[highest]
        #Set self.volume for best solution
        self.volume = vol[int(highest)]
        #Set self.labelit_dir and go to it.
        self.labelit_dir = os.path.join(self.working_dir,highest)
        self.index_number = self.labelit_results.get('Labelit results').get('mosflm_index')
        os.chdir(self.labelit_dir)
        if self.spacegroup != 'None':
          check_lg = Utils.checkSG(self,sym)
          user_sg  = Utils.convertSG(self,self.spacegroup)
          if user_sg != sym:
            fixSG = False
            for line in check_lg:
              if line == user_sg:
                fixSG = True
            if fixSG:
              Utils.fixMosflmSG(self)
              Utils.fixBestSG(self)
            else:
              self.ignore_user_SG = True
        #Make an overlay jpeg
        self.makeImages(1)
      else:
        self.logger.debug('No solution was found when sorting Labelit results.')
        self.labelit_failed = True
        self.labelit_results = { 'Labelit results'  : 'FAILED'}
        self.labelit_dir = os.path.join(self.working_dir,'0')
        os.chdir(self.labelit_dir)
        self.processDistl()
        self.postprocessDistl()
        if os.path.exists('DISTL_pickle'):
            self.makeImages(2)
        self.best_failed = True
        self.best_anom_failed = True

    except:
      self.logger.exception('**ERROR in labelitSort**')

  def findBestStrat(self,inp):
    """
    Find the BEST strategy according to the plots.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::findBestStrat')

    def getBestRotRange(inp):
      """
      Parse lines from XML file.
      """
      try:
        p_s = []
        p_e = False
        for line in inp:
          if line.count('"phi_start"'):
            p_s.append(line[line.find('>')+1:line.rfind('<')])
          if line.count('"phi_end">'):
            p_e = line[line.find('>')+1:line.rfind('<')]
        #If BEST failed...
        if p_e == False:
          return('FAILED')
        else:
          return(int(round(float(p_e)-float(p_s[0]))))
      except:
        self.logger.exception('**Error in getBestRotRange**')
        return('FAILED')
    try:
      phi_st = []
      phi_rn = []
      st  = False
      end = False
      run = False
      if os.path.exists(inp):
        f = open(inp,'r').readlines()
        for x,line in enumerate(f):
          if line.startswith("% linelabel  = 'compl -99.%'"):
            st = x
          if line.startswith("% linelabel  = 'compl -95.%'"):
            end = x
        if st and end:
          for line in f[st:end]:
            if len(line.split()) == 2:
              phi_st.append(line.split()[0])
              phi_rn.append(int(line.split()[1]))
          min1 = min(phi_rn)
          #If xml exists, check if new strategy is at least 5 degrees less rotation range.
          if os.path.exists(inp.replace('.plt','.xml')):
            orig_range = getBestRotRange(open(inp.replace('.plt','.xml'),'r').readlines())
            if orig_range != 'FAILED':
              if orig_range - min1 >= 5:
                run = True
          else:
            run = True
      if run:
        return((str(phi_st[phi_rn.index(min1)]),str(min1)))
      else:
        return((False,False))

    except:
      self.logger.exception('**Error in findBestStrat**')
      return((False,False))

  def PrintInfo(self):
    """
    Print information regarding programs utilized by RAPD
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::PrintInfo')
    try:
      print '======================='
      print 'RAPD developed using Labelit'
      print 'Reference:  J. Appl. Cryst. 37, 399-409 (2004)'
      print 'Website:    http://adder.lbl.gov/labelit/ \n'
      print 'RAPD developed using Mosflm'
      print 'Reference: Leslie, A.G.W., (1992), Joint CCP4 + ESF-EAMCB Newsletter on Protein Crystallography, No. 26'
      print 'Website:   http://www.mrc-lmb.cam.ac.uk/harry/mosflm/ \n'
      print 'RAPD developed using RADDOSE'
      print 'Reference: Paithankar et. al. (2009)J. Synch. Rad. 16, 152-162.'
      print 'Website: http://biop.ox.ac.uk/www/garman/lab_tools.html/ \n'
      print 'RAPD developed using Best'
      print 'Reference: G.P. Bourenkov and A.N. Popov,  Acta Cryst. (2006). D62, 58-64'
      print 'Website:   http://www.embl-hamburg.de/BEST/ \n'
      print '======================='
      self.logger.debug('=======================')
      self.logger.debug('RAPD developed using Labelit')
      self.logger.debug('Reference:  J. Appl. Cryst. 37, 399-409 (2004)')
      self.logger.debug('Website:    http://adder.lbl.gov/labelit/ \n')
      self.logger.debug('RAPD developed using Mosflm')
      self.logger.debug('Reference: Leslie, A.G.W., (1992), Joint CCP4 + ESF-EAMCB Newsletter on Protein Crystallography, No. 26')
      self.logger.debug('Website:   http://www.mrc-lmb.cam.ac.uk/harry/mosflm/ \n')
      self.logger.debug('RAPD developed using RADDOSE')
      self.logger.debug('Reference: Paithankar et. al. (2009)J. Synch. Rad. 16, 152-162.')
      self.logger.debug('Website: http://biop.ox.ac.uk/www/garman/lab_tools.html/ \n')
      self.logger.debug('RAPD developed using Best')
      self.logger.debug('Reference: G.P. Bourenkov and A.N. Popov,  Acta Cryst. (2006). D62, 58-64')
      self.logger.debug('Website:   http://www.embl-hamburg.de/BEST/ \n')
      self.logger.debug('=======================')
    except:
      self.logger.exception('**Error in PrintInfo**')

  def makeImages(self,predictions):
    """
    Create images for iipimage server in an alternate process
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::makeImages')
    try:
      l = [('raw','labelit.png'),('overlay','labelit.overlay_index -large'),
           ('overlay','labelit.overlay_distl -large')]
      l1 = []
      #aggregate the source images
      src_images = []
      #1st image
      src_images.append(self.header.get('fullname'))
      #if we have a pair
      if self.header2:
        src_images.append(self.header2.get('fullname'))
      for image in src_images:
        if predictions == 0:
          png = '%s.png'%os.path.basename(image)[:-4]
        else:
          png = '%s_overlay.png'%os.path.basename(image)[:-4]
        tif = png.replace('.png','.tif')
        if self.test:
          command = 'ls'
        else:
          command = '%s %s %s; vips im_vips2tiff %s %s:jpeg:100,tile:192x192,pyramid; rm -rf %s'%(l[predictions][1],image,png,png,tif,png)
          #command = '%s %s %s; vips im_vips2tiff %s %s:jpeg:100,tile:192x192,pyramid'%(l[predictions][1],image,png,png,tif)
        job = Process(target=Utils.processLocal,args=(command,self.logger))
        #job = Process(target=Utils.processLocal,args=((command,'junk.log'),self.logger))
        job.start()
        l1.append((tif,job))

      self.vips_images[l[predictions][0]] = l1

    except:
      self.logger.exception('**Error in makeImages.**')

  def postprocess(self):
    """
    Make all the HTML files, pass results back, and cleanup.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::postprocess')
    output = {}
    #output_files = False
    #Generate the proper summaries that go into the output HTML files
    if self.labelit_failed == False:
      if self.labelit_results:
        Summary.summaryLabelit(self)
        Summary.summaryAutoCell(self,True)
    if self.distl_results:
      Summary.summaryDistl(self)
    if self.raddose_results:
      Summary.summaryRaddose(self)
    if self.labelit_failed == False:
      if self.strategy == 'mosflm':
        self.htmlBestPlotsFailed()
        Summary.summaryMosflm(self,False)
        Summary.summaryMosflm(self,True)
      else:
        if self.best_failed:
          if self.best_anom_failed:
            self.htmlBestPlotsFailed()
            Summary.summaryMosflm(self,False)
            Summary.summaryMosflm(self,True)
          else:
            Summary.summaryMosflm(self,False)
            Summary.summaryBest(self,True)
            self.htmlBestPlots()
        elif self.best_anom_failed:
          Summary.summaryMosflm(self,True)
          Summary.summaryBest(self,False)
          self.htmlBestPlots()
        else:
          Summary.summaryBest(self,False)
          Summary.summaryBest(self,True)
          self.htmlBestPlots()
    else:
      self.htmlBestPlotsFailed()
    #Generate the long and short summary HTML files
    self.htmlSummaryShort()
    self.htmlSummaryLong()
    #Set STAC output to send back as None since it did not run.
    output['Stac summary html']  = 'None'

    #Get the raw tiff, autoindex_overlay, or distl_overlay of the diff pattern.
    l = [('raw','image_path_raw'),('overlay','image_path_pred')]
    for x in range(len(l)):
      #Set output files defaults
      for i in range(2):
        output['%s_%s'%(l[x][1],i+1)] = 'None'
      run = True
      if x == 0:
        dir1 = self.working_dir
      else:
        dir1 = self.labelit_dir
        if os.path.exists(os.path.join(self.labelit_dir,'DISTL_pickle')) == False:
          run = False
      if run:
        for i in range(len(self.vips_images[l[x][0]])):
          try:
            f1 = os.path.join(dir1,self.vips_images[l[x][0]][i][0])
            job  = self.vips_images[l[x][0]][i][1]
            timer = 0
            while job.is_alive():
              time.sleep(0.2)
              timer += 0.2
              if self.verbose:
                number = round(timer%1,1)
                if number in (0.0,1.0):
                  print 'Waiting for %s %s seconds'%(f1,timer)
            if x != 0:
              if os.path.exists(f1):
                shutil.copy(f1,os.path.join(self.working_dir,os.path.basename(f1)))
            output['%s_%s'%(l[x][1],i+1)] = os.path.join(self.dest_dir,os.path.basename(f1))
          except:
            output['%s_%s'%(l[x][1],i+1)] = False

    #Save path for files required for future STAC runs.
    try:
      if self.labelit_failed == False:
        os.chdir(self.labelit_dir)
        #files = ['DNA_mosflm.inp','bestfile.par']
        #files = ['mosflm.inp','%s.mat'%self.index_number]
        files = ['%s.mat'%self.index_number,'bestfile.par']
        for x,f in enumerate(files):
          shutil.copy(f,self.working_dir)
          if os.path.exists(os.path.join(self.working_dir,f)):
            output['STAC file%s'%str(x+1)] = os.path.join(self.dest_dir,f)
          else:
            output['STAC file%s'%str(x+1)] = 'None'
      else:
        output['STAC file1'] = 'None'
        output['STAC file2'] = 'None'
    except:
      self.logger.exception('**Could not update path of STAC files**')
      output['STAC file1'] = 'FAILED'
      output['STAC file2'] = 'FAILED'

    #Pass back paths for html files
    if self.gui:
      e = '.php'
    else:
      e = '.html'
    l = [('best_plots%s'%e,'Best plots html'),
         ('jon_summary_long%s'%e,'Long summary html'),
         ('jon_summary_short%s'%e,'Short summary html')]
    for i in range(len(l)):
      try:
        path = os.path.join(self.working_dir,l[i][0])
        path2 = os.path.join(self.dest_dir,l[i][0])
        if os.path.exists(path):
          output[l[i][1]] = path2
        else:
          output[l[i][1]] = 'None'
      except:
        self.logger.exception('**Could not update path of %s file.**'%l[i][0])
        output[l[i][1]] = 'FAILED'
    #Put all output files into a singe dict to pass back.
    output_files = {'Output files' : output}
    # Put all the result dicts from all the programs run into one resultant dict and pass back.
    try:
      results = {}
      if self.labelit_results:
        results.update(self.labelit_results)
      if self.distl_results:
        results.update(self.distl_results)
      if self.raddose_results:
        results.update(self.raddose_results)
      if self.best_results:
        results.update(self.best_results)
      if self.best_anom_results:
        results.update(self.best_anom_results)
      if self.mosflm_strat_results:
        results.update(self.mosflm_strat_results)
      if self.mosflm_strat_anom_results:
        results.update(self.mosflm_strat_anom_results)
      results.update(output_files)
      self.input.append(results)
      if self.gui:
        # self.sendBack2(self.input)
        rapd_send(self.controller_address, self.input)
    except:
      self.logger.exception('**Could not send results to pipe.**')

    #Cleanup my mess.
    try:
      os.chdir(self.working_dir)
      if self.clean:
        if self.test == False:
          if self.verbose:
            self.logger.debug('Cleaning up files and folders')
          os.system('rm -rf labelit_iteration* dataset_preferences.py')
          for i in range(0,self.iterations):
            os.system('rm -rf %s'%i)
    except:
      self.logger.exception('**Could not cleanup**')

    #Move files from RAM to destination folder
    try:
      if self.working_dir == self.dest_dir:
        pass
      else:
        if self.gui:
          if os.path.exists(self.dest_dir):
            shutil.rmtree(self.dest_dir)
          shutil.move(self.working_dir,self.dest_dir)
        else:
          os.system('cp -R * %s'%self.dest_dir)
          os.system('rm -rf %s'%self.working_dir)
    except:
      self.logger.exception('**Could not move files from RAM to destination dir.**')

    #Say job is complete.
    t = round(time.time()-self.st)
    self.logger.debug('-------------------------------------')
    self.logger.debug('RAPD autoindexing/strategy complete.')
    self.logger.debug('Total elapsed time: %s seconds'%t)
    self.logger.debug('-------------------------------------')
    print '\n-------------------------------------'
    print 'RAPD autoindexing/strategy complete.'
    print 'Total elapsed time: %s seconds'%t
    print '-------------------------------------'
    #sys.exit(0) #did not appear to end script with some programs continuing on for some reason.
    #os._exit(0)

  def htmlBestPlots(self):
    """
    generate plots html/php file
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::htmlBestPlots')
    try:
      run = True
      plot = False
      plotanom = False
      dir1 = self.best_results.get('Best results').get('directory',False)
      dir2 = self.best_anom_results.get('Best ANOM results').get('directory',False)

      #Get the parsed results for reg and anom results and put them into a single dict.
      if dir1:
        plot = Parse.ParseOutputBestPlots(self,open(os.path.join(dir1,'best.plt'),'r').readlines())
        if dir2:
          plotanom = Parse.ParseOutputBestPlots(self,open(os.path.join(dir2,'best_anom.plt'),'r').readlines())
          plot.update({'companom':plotanom.get('comp')})
      elif dir2:
        plot = Parse.ParseOutputBestPlots(self,open(os.path.join(dir2,'best_anom.plt'),'r').readlines())
        plot.update({'companom':plot.pop('comp')})
      else:
        self.htmlBestPlotsFailed()
        run = False

      #Place holder for settings.
      l = [['Omega start','Min osc range for different completenesses','O m e g a &nbsp R a n g e','Omega Start',
            'comp','"start at " + x + " for " + y + " degrees");'],
           ['ANOM Omega start','Min osc range for different completenesses','O m e g a &nbsp R a n g e','Omega Start',
            'companom','"start at " + x + " for " + y + " degrees");'],
           ['Max delta Omega','Maximal Oscillation Width','O m e g a &nbsp S t e p','Omega',
            'width','"max delta Omega of " + y + " at Omega=" + x);'],
           ['Wilson Plot','Wilson Plot','I n t e n s i t y','1/Resolution<sup>2</sup>',
            'wilson','item.series.label + " of " + x + " = " + y);']]
      if self.sample_type != 'Ribosome':
        temp = [['Rad damage1','Intensity decrease due to radiation damage','R e l a t i v e &nbsp I n t e n s i t y',
                 'Cumulative exposure time (sec)','damage','"at res=" + item.series.label + " after " + x + " seconds intensity drops to " + y);'],
                ['Rad damage2','Rdamage vs. Cumulative Exposure time','R f a c t o r','Cumulative exposure time (sec)',
                 'rdamage','"at res=" + item.series.label + " after " + x + " seconds Rdamage increases to " + y);']]
        l.extend(temp)

      if run:
        if self.gui:
          f = 'best_plots.php'
        else:
          f = 'best_plots.html'
        best_plot = open(f,'w')
        best_plot.write(Utils.getHTMLHeader(self,'plots'))
        best_plot.write('%4s$(function() {\n%6s// Tabs\n'%('',''))
        best_plot.write("%6s$('.tabs').tabs();\n%4s});\n"%('',''))
        best_plot.write('%4s</script>\n%2s</head>\n%2s<body>\n%4s<table>\n%6s<tr>\n'%(5*('',)))
        best_plot.write('%8s<td width="%s">\n%10s<div class="tabs">\n%12s<ul>\n'%('','100%','',''))
        for i in range(len(l)):
          best_plot.write('%14s<li><a href="#tabs-22%s">%s</a></li>\n'%('',i,l[i][0]))
        best_plot.write("%12s</ul>\n"%'')
        for i in range(len(l)):
          best_plot.write('%12s<div id="tabs-22%s">\n'%('',i))
          if i == 0 and self.best_failed:
            best_plot.write('%14s<div class=title><b>BEST strategy calculation failed</b></div>\n'%'')
          elif i == 1 and self.best_anom_failed:
            best_plot.write('%14s<div class=title><b>BEST ANOM strategy calculation failed</b></div>\n'%'')
          else:
            best_plot.write('%14s<div class=title><b>%s</b></div>\n'%('',l[i][1]))
            best_plot.write('%14s<div id="chart%s_div" style="width:800px;height:600px"></div>\n'%('',i))
            best_plot.write('%14s<div class=x-label>%s</div>\n%14s<span class=y-label>%s</span>\n'%('',l[i][3],'',l[i][2]))
          best_plot.write("%12s</div>\n"%'')
        best_plot.write("%10s</div>\n%8s</td>\n%6s</tr>\n%4s</table>\n"%(4*('',)))
        best_plot.write('%4s<script id="source" language="javascript" type="text/javascript">\n'%'')
        best_plot.write("%2s$(function () {\n\n"%'')
        s = '    var '
        for i in range(len(l)):
          l1 = []
          l2 = []
          label = ['%6s[\n'%'']
          s1 = s
          #In case comp or companom are not present.
          if plot.has_key(l[i][4]):
            data = plot.get(l[i][4])
            for x in range(len(data)):
              var = '%s%s'%(l[i][4].upper(),x)
              s1 += '%s=[],'%var
              label.append('%8s{ data: %s, label:%s },\n'%('',var,data[x].keys()[0]))
              for y in range(len(data[x].get(data[x].keys()[0]))):
                l1.append('%4s%s.push([%s,%s]);\n'%('',var,data[x].get(data[x].keys()[0])[y][0],data[x].get(data[x].keys()[0])[y][1]))
                if l[i][4].startswith('comp') and x == 0:
                  l2.append(data[x].get(data[x].keys()[0])[y][1])
            if i == 0:
              best_plot.write('%s,mark=[];\n'%s1[:-1])
              label.append('%8s{ data: mark, label: "Best starting Omega", color: "black"},\n'%'')
            elif i == 1:
              best_plot.write('%s,markanom=[];\n'%s1[:-1])
              label.append('%8s{ data: markanom, label: "Best starting Omega", color: "black"},\n'%'')
            else:
              best_plot.write('%s;\n'%s1[:-1])
          label.append('%6s],\n'%'')
          l[i].append(label)
          for line in l1:
            best_plot.write(line)
          if len(l2) > 0:
            if i == 0:
              best_plot.write("%4sfor (var i = 0; i < %s; i += 5)\n"%('',max(l2)))
              best_plot.write("%4smark.push([%s,i]);\n"%('',self.best_results.get('Best results').get('strategy phi start')[0]))
            if i == 1:
              best_plot.write("%4sfor (var i = 0; i < %s; i += 5)\n"%('',max(l2)))
              best_plot.write("%4smarkanom.push([%s,i]);\n"%('',self.best_anom_results.get('Best ANOM results').get('strategy anom phi start')[0]))
        for i in range(len(l)):
          best_plot.write('%4svar plot%s = $.plot($("#chart%s_div"),\n'%('',i,i))
          for line in l[i][-1]:
            best_plot.write(line)
          best_plot.write("%6s{ lines: { show: true},\n%8spoints: { show: false },\n"%('',''))
          best_plot.write("%8sselection: { mode: 'xy' },\n%8sgrid: { hoverable: true, clickable: true },\n%6s});\n"%(3*('',)))
        best_plot.write( "%4sfunction showTooltip(x, y, contents) {\n"%'')
        best_plot.write("%6s$('<div id=tooltip>' + contents + '</div>').css( {\n%8sposition: 'absolute',\n"%('',''))
        best_plot.write("%8sdisplay: 'none',\n%8stop: y + 5,\n%8sleft: x + 5,\n%8sborder: '1px solid #fdd',\n"%(4*('',)))
        best_plot.write("%8spadding: '2px',\n%8s'background-color': '#fee',\n%8s opacity: 0.80\n"%(3*('',)))
        best_plot.write('%6s}).appendTo("body").fadeIn(200);\n%4s}\n%4svar previousPoint = null;\n'%(3*('',)))
        for i in range(len(l)):
          best_plot.write('%4s$("#chart%s_div").bind("plothover", function (event, pos, item) {\n'%('',i))
          best_plot.write('%6s$("#x").text(pos.x.toFixed(2));\n%6s$("#y").text(pos.y.toFixed(2));\n'%('',''))
          best_plot.write("%6sif (true) {\n%8sif (item) {\n%10sif (previousPoint != item.datapoint) {\n"%(3*('',)))
          best_plot.write('%14spreviousPoint = item.datapoint;\n%14s$("#tooltip").remove();\n'%('',''))
          best_plot.write('%14svar x = item.datapoint[0].toFixed(2),\n%18sy = item.datapoint[1].toFixed(2);\n'%('',''))
          best_plot.write('%14sshowTooltip(item.pageX, item.pageY,\n'%'')
          best_plot.write('%26s%s\n%10s}\n%8s}\n'%('',l[i][5],'',''))
          best_plot.write('%8selse {\n%10s$("#tooltip").remove();\n%10spreviousPoint = null;\n%8s}\n%6s}\n%4s});\n'%(6*('',)))
        best_plot.write( "%2s});\n%4s</script>\n%2s</body>\n</html>\n"%(3*('',)))
        best_plot.close()
        if os.path.exists(f):
          shutil.copy(f,self.working_dir)

    except:
      self.logger.exception('**ERROR in htmlBestPlots**')
      self.htmlBestPlotsFailed()

  def htmlBestPlotsFailed(self):
    """
    If Best failed or was not run, this is the resultant html/php file.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::htmlBestPlotsFailed')
    try:
      if self.strategy == 'mosflm':
        error = 'Mosflm strategy was chosen so no plots are calculated.'
      else:
        error = 'Best Failed. Could not calculate plots.'
      Utils.failedHTML(self,('best_plots',error))
      if self.gui:
        f = 'best_plots.php'
      else:
        f = 'best_plots.html'
      if os.path.exists(f):
        shutil.copy(f,self.working_dir)

    except:
      self.logger.exception('**ERROR in htmlBestPlotsFailed**')

  def htmlSummaryLong(self):
    """
    Create HTML/php files for autoindex/strategy output results.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::htmlSummaryLong')
    try:
      if self.gui:
        f = 'jon_summary_long.php'
      else:
        f = 'jon_summary_long.html'
      jon_summary = open(f,'w')
      jon_summary.write(Utils.getHTMLHeader(self,'strat'))
      jon_summary.write("%6s$(document).ready(function() {\n%8s$('#accordion').accordion({\n"%('',''))
      jon_summary.write('%11scollapsible: true,\n%11sactive: false         });\n'%('',''))
      if self.best_summary:
        jon_summary.write("%8s$('#best').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false    });\n'%(4*('',)))
      if self.best_anom_summary:
        jon_summary.write("%8s$('#bestanom').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false    });\n'%(4*('',)))
      if self.best_failed or self.strategy == 'mosflm':
        if self.mosflm_strat_summary:
          jon_summary.write("%8s$('#strat').dataTable({\n"%'')
          jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false    });\n'%(4*('',)))
      if self.best_anom_failed or self.strategy == 'mosflm':
        if self.mosflm_strat_anom_summary:
          jon_summary.write("%8s$('#stratanom').dataTable({\n"%'')
          jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false    });\n'%(4*('',)))
      if self.labelit_summary:
        jon_summary.write("%8s$('#mosflm').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false    });\n'%(4*('',)))
        jon_summary.write("%8s$('#labelit').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false    });\n'%(4*('',)))
      if self.distl_summary:
        jon_summary.write("%8s$('#distl').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false    });\n'%(4*('',)))
      jon_summary.write('%6s});\n%4s</script>\n%2s</head>\n%2s<body id="dt_example">\n'%(4*('',)))
      if self.best_summary:
        jon_summary.writelines(self.best_summary)
      if self.best_summary_long:
        jon_summary.writelines(self.best_summary_long)
      if self.best_results:
        if self.best_results.get('Best results') == 'FAILED':
          jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
          jon_summary.write('%7s<h4 class="results">Best Failed. Trying Mosflm strategy.</h3>\n'%'')
          jon_summary.write("%6s</div>\n%5s</div>\n%4s</div>\n"%(3*('',)))
      if self.mosflm_strat_summary:
        jon_summary.writelines(self.mosflm_strat_summary)
      if self.mosflm_strat_summary_long:
        jon_summary.writelines(self.mosflm_strat_summary_long)
      if self.mosflm_strat_results:
        if self.mosflm_strat_results.get('Mosflm strategy results') == 'FAILED':
          jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
          jon_summary.write('%7s<h3 class="results">Mosflm Strategy Failed. Could not calculate a strategy.</h3>\n'%'')
          jon_summary.write("%6s</div>\n%5s</div>\n%4s</div>\n"%(3*('',)))
      if self.best_anom_summary:
        jon_summary.writelines(self.best_anom_summary)
      if self.best_anom_summary_long:
        jon_summary.writelines(self.best_anom_summary_long)
      if self.best_anom_results:
        if self.best_anom_results.get('Best ANOM results') == 'FAILED':
          jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
          jon_summary.write('%7s<br><h4 class="results">Best Failed. Trying Mosflm ANOMALOUS strategy.</h3>\n'%'')
          jon_summary.write("%6s</div>\n%5s</div>\n%4s</div>\n"%(3*('',)))
      if self.mosflm_strat_anom_summary:
        jon_summary.writelines(self.mosflm_strat_anom_summary)
      if self.mosflm_strat_anom_summary_long:
        jon_summary.writelines(self.mosflm_strat_anom_summary_long)
      if self.mosflm_strat_anom_results:
        if self.mosflm_strat_anom_results.get('Mosflm ANOM strategy results') == 'FAILED':
          jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
          jon_summary.write('%7s<br><h3 class="results">Mosflm Strategy Failed. Could not calculate an ANOMALOUS strategy.</h3>\n'%'')
          jon_summary.write("%6s</div>\n%5s</div>\n%4s</div>\n"%(3*('',)))
      if self.raddose_summary:
        jon_summary.writelines(self.raddose_summary)
      if self.raddose_results:
        if self.raddose_results.get('Raddose results') == 'FAILED':
          jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
          jon_summary.write('%7s<h4 class="results">Raddose failed. Using default dosage. Best results are still good.</h4>\n'%'')
          jon_summary.write("%6s</div>\n%5s</div>\n%4s</div>\n"%(3*('',)))
      if self.labelit_summary:
        jon_summary.writelines(self.labelit_summary)
      if self.labelit_results:
        if self.labelit_results.get('Labelit results') == 'FAILED':
          jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
          jon_summary.write('%7s<h3 class="results">Autoindexing FAILED</h3>\n'%'')
          if self.header2:
            jon_summary.write('%7s<h4 class="results">Pair of snapshots did not autoindex. Possibly not from same crystal.</h3>\n'%'')
          else:
            jon_summary.write('%7s<h4 class="results">You can add "pair" to the snapshot name and collect '\
                              'one at 0 and 90 degrees. Much better for poor diffraction.</h3>\n'%'')
            jon_summary.write('%7s<h4 class="results">eg."snap_pair_99_001.img"</h3>\n'%'')
          jon_summary.write("%6s</div>\n%5s</div>\n%4s</div>\n"%(3*('',)))
      if self.distl_summary:
        jon_summary.writelines(self.distl_summary)
      if self.distl_results:
        if self.distl_results.get('Distl results') == 'FAILED':
          jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
          jon_summary.write('%7s<h4 class="results">Distl failed. Could not parse peak search file. '\
                            'If you see this, not an indexing problem. Best results are still good.</h4>\n'%'')
          jon_summary.write("%6s</div>\n%5s</div>\n%4s</div>\n"%(3*('',)))
      jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
      jon_summary.write("%7s<h1 class='Results'>RAPD Logfile</h1>\n%6s</div>\n%5s</div>\n"%(3*('',)))
      jon_summary.write('%5s<div id="accordion">\n%6s<h3><a href="#">Click to view log</a></h3>\n%6s<div>\n%7s<pre>\n'%(4*('',)))
      jon_summary.write('\n---------------Autoindexing RESULTS---------------\n\n')
      if self.labelit_log.has_key('run1'):
        for line in self.labelit_log['run1'][1:]:
          jon_summary.write(line)
      else:
        jon_summary.write('---------------LABELIT FAILED---------------\n')
      jon_summary.write('\n---------------Peak Picking RESULTS---------------\n\n')
      if self.distl_log:
        for line in self.distl_log:
          jon_summary.write(line)
      #Don't write error messages from programs that did not run.
      if self.labelit_results.get('Labelit results') != 'FAILED':
        jon_summary.write('\n---------------Raddose RESULTS---------------\n\n')
        if self.raddose_log:
          for line in self.raddose_log:
            jon_summary.write(line)
        else:
          jon_summary.write('---------------RADDOSE FAILED---------------\n')
        jon_summary.write('\n\n---------------Data Collection Strategy RESULTS---------------\n\n')
        if self.best_log:
          for line in self.best_log:
            jon_summary.write(line)
        else:
          jon_summary.write('---------------BEST FAILED. TRYING MOSFLM STRATEGY---------------\n')
        if self.best_failed or self.strategy == 'mosflm' or self.multicrystalstrat:
          if self.mosflm_strat_log:
            jon_summary.write('\n---------------Data Collection Strategy RESULTS from Mosflm---------------\n\n')
            for line in self.mosflm_strat_log:
              jon_summary.write(line)
          else:
            jon_summary.write('---------------MOSFLM STRATEGY FAILED---------------\n')
        jon_summary.write('\n---------------ANOMALOUS Data Collection Strategy RESULTS---------------\n\n')
        if self.best_anom_log:
          for line in self.best_anom_log:
            jon_summary.write(line)
        else:
          jon_summary.write('---------------BEST ANOM STRATEGY FAILED. TRYING MOSFLM STRATEGY---------------\n')
        if self.best_anom_failed or self.strategy == 'mosflm' or self.multicrystalstrat:
          if self.mosflm_strat_anom_log:
            jon_summary.write('\n---------------ANOMALOUS Data Collection Strategy RESULTS from Mosflm---------------\n\n')
            for line in self.mosflm_strat_anom_log:
              jon_summary.write(line)
          else:
            jon_summary.write('---------------MOSFLM ANOM STRATEGY FAILED---------------\n')
      jon_summary.write('%7s</pre>\n%6s</div>\n%5s</div>\n%4s</div>\n%2s</body>\n</html>\n'%(5*('',)))
      jon_summary.close()
      if os.path.exists(f):
        shutil.copy(f,self.working_dir)

    except:
      self.logger.exception('**ERROR in htmlSummaryLong**')

  def htmlSummaryShort(self):
    """
    Create short summary HTML/php file for autoindex/strategy output results.
    """
    if self.verbose:
      self.logger.debug('AutoindexingStrategy::htmlSummaryShort')
    try:
      if self.gui:
        f = 'jon_summary_short.php'
      else:
        f = 'jon_summary_short.html'
      jon_summary = open(f,'w')
      jon_summary.write(Utils.getHTMLHeader(self,'strat'))
      jon_summary.write("%6s$(document).ready(function() {\n"%'')
      if self.auto_summary:
        jon_summary.write("%8s$('#auto').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false });\n'%(4*('',)))
      if self.best_summary:
        jon_summary.write("%8snormSimpleBestTable = $('#best1').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false });\n'%(4*('',)))
      if self.best_anom_summary:
        jon_summary.write("%8sanomSimpleBestTable = $('#bestanom1').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false });\n'%(4*('',)))
      if self.best_failed or self.strategy == 'mosflm':
        if self.mosflm_strat_summary:
          jon_summary.write("%8s$('#strat1').dataTable({\n"%'')
          jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false });\n'%(4*('',)))
      if self.best_anom_failed or self.strategy == 'mosflm':
        if self.mosflm_strat_anom_summary:
          jon_summary.write("%8s$('#stratanom1').dataTable({\n"%'')
          jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false });\n'%(4*('',)))
      if self.best_summary:
        jon_summary.write('''
             //Double click handlers for tables
             $("#best1 tbody tr").dblclick(function(event) {
                    //Get the current data of the clicked-upon row
                    aData = normSimpleBestTable.fnGetData(this);
                    //Parse out the image prefix from the currently selected snap
                    var tmp_repr = image_repr.toString().split("_");
                    var tmp_repr2 = tmp_repr.slice(0,-2).join('_');
                    //Use the values from the line to fill the form
                    $("#image_prefix").val(tmp_repr2);
                    $("#omega_start").val(aData[1]);
                    $("#delta_omega").val(aData[5]);
                    $("#number_images").val(aData[4]);
                    $("#time").val(aData[6]);
                    $("#distance").val(aData[7]);
                    $("#transmission").val(aData[8]);
                    //Open up the dialog form
                    $('#dialog-form-datacollection').dialog('open');
             }); \n''')
        if self.best_anom_summary:
            jon_summary.write('''
             //Single click handlers
             $("#best1 tbody tr").click(function(event) {
                     $(normSimpleBestTable.fnSettings().aoData).each(function (){
                     $(this.nTr).removeClass('row_selected');
                 });
                 $(anomSimpleBestTable.fnSettings().aoData).each(function (){
                     $(this.nTr).removeClass('row_selected');
                 });
                 $(event.target.parentNode).toggleClass('row_selected');
             });

             $("#bestanom1 tbody tr").click(function(event) {
                 $(normSimpleBestTable.fnSettings().aoData).each(function (){
                     $(this.nTr).removeClass('row_selected');
                 });
                 $(anomSimpleBestTable.fnSettings().aoData).each(function (){
                     $(this.nTr).removeClass('row_selected');
                 });
                 $(event.target.parentNode).toggleClass('row_selected');
             }); \n''')
      if self.best_anom_summary:
        jon_summary.write('''
             $("#bestanom1 tbody tr").dblclick(function(event) {
                    //Get the current data of the clicked-upon row
                    aData = anomSimpleBestTable.fnGetData(this);
                    //Parse out the image prefix from the currently selected snap
                    var tmp_repr = image_repr.toString().split("_");
                    var tmp_repr2 = tmp_repr.slice(0,-2).join('_');
                    //Use the values from the line to fill the form
                    $("#image_prefix").val(tmp_repr2);
                    $("#omega_start").val(aData[1]);
                    $("#delta_omega").val(aData[5]);
                    $("#number_images").val(aData[4]);
                    $("#time").val(aData[6]);
                    $("#distance").val(aData[7]);
                    $("#transmission").val(aData[8]);
                    //Open up the dialog form
                    $('#dialog-form-datacollection').dialog('open');
             }); \n''')

      jon_summary.write('''
           //The dialog form for data collection
           $("#dialog-form-datacollection").dialog({
                  autoOpen: false,
                  width: 350,
                  modal: true,
                  buttons: {
                      'Send to Beamline': function() {
                                          //POST the data to the php tool
                                          $.ajax({
                                              type: "POST",
                                              url: "d_add_datacollection.php",
                                              data: {prefix:$("#image_prefix").val(),
                                                     run_number:$("#run_number").val(),
                                                     image_start:$("#image_start").val(),
                                                     omega_start:$("#omega_start").val(),
                                                     delta_omega:$("#delta_omega").val(),
                                                     number_images:$("#number_images").val(),
                                                     time:$("#time").val(),
                                                     distance:$("#distance").val(),
                                                     transmission:$("#transmission").val(),
                                                     ip_address:my_ip,
                                                     beamline:my_beamline}
                                          });
                          $(this).dialog('close');
                      },
                      Cancel: function() {
                          $(this).dialog('close');
                      }
                  },
           }); \n''')
      #The end of the Jquery
      jon_summary.write('%6s});\n%4s</script>\n%2s</head>\n%2s<body id="dt_example">\n'%(4*('',)))
      jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
      jon_summary.write('%7s<h1 class="results">Labelit autoindexing summary for:</h1>\n'%'')
      jon_summary.write("%7s<h2 class='results'>Image: %s</h2>\n"%('',self.header.get('fullname')))
      if self.header2:
        jon_summary.write("%7s<h2 class='results'>Image: %s</h2>\n"%('',self.header2.get('fullname')))
      if self.prev_sg:
        jon_summary.write("%7s<h4 class='results'>Space group %s selected from previous dataset.</h4>\n"%('',self.spacegroup))
      else:
        if self.spacegroup != 'None':
          jon_summary.write("%7s<h4 class='results'>User chose space group as %s</h4>\n"%('',self.spacegroup))
          if self.ignore_user_SG == True:
            jon_summary.write("%7s<h4 class='results'>Unit cell not compatible with user chosen SG.</h4>\n"%'')
      if self.pseudotrans:
        jon_summary.write("%7s<h4 class='results'>Caution. Labelit suggests the possible presence "\
                          "of pseudotranslation. Look at the log file for more info.</h4>\n"%'')
      if self.auto_summary:
        jon_summary.writelines(self.auto_summary)
      if self.labelit_results:
        if self.labelit_results.get('Labelit results') == 'FAILED':
          jon_summary.write('%7s<h3 class="results">Autoindexing FAILED.</h3>\n'%'')
          if self.header2:
            jon_summary.write('%7s<h4 class="results">Pair of snapshots did not autoindex. Possibly not from same crystal.</h3>\n'%'')
          else:
            jon_summary.write('%7s<h4 class="results">You can add "pair" to the snapshot name and collect one '\
                              'at 0 and 90 degrees. Much better for poor diffraction.</h3>\n'%'')
            jon_summary.write('%7s<h4 class="results">eg."snap_pair_99_001.img"</h3>\n'%'')
          jon_summary.write("%6s</div>\n%5s</div>\n%4s</div>\n"%(3*('',)))
      if self.best1_summary:
        jon_summary.writelines(self.best1_summary)
      if self.best_results:
        if self.best_results.get('Best results') == 'FAILED':
          jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
          jon_summary.write('%7s<h4 class="results">Best Failed. Trying Mosflm strategy.</h3>\n'%'')
          jon_summary.write("%6s</div>\n%5s</div>\n%4s</div>\n"%(3*('',)))
      if self.mosflm_strat1_summary:
        jon_summary.writelines(self.mosflm_strat1_summary)
      if self.mosflm_strat_results:
        jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
        if self.mosflm_strat_results.get('Mosflm strategy results') == 'FAILED':
          jon_summary.write('%7s<h3 class="results">Mosflm strategy failed. Could not calculate a strategy.</h3>\n'%'')
        elif self.mosflm_strat_results.get('Mosflm strategy results') == 'SYM':
          jon_summary.write('%7s<h3 class="results">Mosflm strategy failed because the SG or unit cell '\
                            'is not compatible with the reference dataset.</h3>\n'%'')
        jon_summary.write("%6s</div>\n%5s</div>\n%4s</div>\n"%(3*('',)))
      if self.best1_anom_summary:
        jon_summary.writelines('%4s<br>\n'%'')
        jon_summary.writelines(self.best1_anom_summary)
      if self.best_anom_results:
        if self.best_anom_results.get('Best ANOM results') == 'FAILED':
          jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
          jon_summary.write('%7s<h4 class="results">Best Failed. Trying Mosflm ANOMALOUS strategy.</h3>\n'%'')
          jon_summary.write("%6s</div>\n%5s</div>\n%4s</div>\n"%(3*('',)))
      if self.mosflm_strat1_anom_summary:
        jon_summary.writelines(self.mosflm_strat1_anom_summary)
      if self.mosflm_strat_anom_results:
        jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
        if self.mosflm_strat_anom_results.get('Mosflm ANOM strategy results') == 'FAILED':
          jon_summary.write('%7s<h3 class="results">Mosflm strategy failed. Could not calculate an ANOMALOUS strategy.</h3>\n'%'')
        elif self.mosflm_strat_anom_results.get('Mosflm ANOM strategy results') == 'SYM':
          jon_summary.write('%7s<h3 class="results">Mosflm strategy failed because the SG or unit '\
                            'cell is not compatible with the reference dataset.</h3>\n'%'')
        jon_summary.write("%6s</div>\n%5s</div>\n%4s</div>\n"%(3*('',)))
      jon_summary.write('''
          <div id="dialog-form-datacollection" title="Send Datacollection Parameters to Beamline">
              <p class="validateTips">All form fields are required.</p>
              <form id="datacollection-form" method="POST" action="d_add_minikappa.php">
              <fieldset>
                      <table>
                        <tr>
                          <td>
                            <label for="image_prefix">Image prefix</label>
                          </td>
                          <td>
                            <input type="text" name="image_prefix" id="image_prefix" value="" class="text ui-widget-content ui-corner-all" "size=6"/>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <label for="run_number">Run number</label>
                          </td>
                          <td>
                            <input type="text" name="run_number" id="run_number" value="1" class="text ui-widget-content ui-corner-all" "size=6"/>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <label for="image_start">First image number</label>
                          </td>
                          <td>
                            <input type="text" name="image_start" id="image_start" value="1" class="text ui-widget-content ui-corner-all" "size=6"/>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <label for="name">Omega start (&deg;)</label>
                          </td>
                          <td>
                            <input type="text" name="omega_start" id="omega_start" value="" class="text ui-widget-content ui-corner-all" "size=6"/>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <label for="delta_omega">Delta omega (&deg;)</label>
                          </td>
                          <td>
                            <input type="text" name="delta_omega" id="delta_omega" value="" class="text ui-widget-content ui-corner-all" "size=6"/>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <label for="number_images">Number of images</label>
                          </td>
                          <td>
                            <input type="text" name="number_images" id="number_images" value="" class="text ui-widget-content ui-corner-all" "size=6"/>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <label for="time">Exposure time (s)</label>
                          </td>
                          <td>
                            <input type="text" name="time" id="time" value="" class="text ui-widget-content ui-corner-all" "size=6"/>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <label for="distance">Distance (mm)</label>
                          </td>
                          <td>
                            <input type="text" name="distance" id="distance" value="" class="text ui-widget-content ui-corner-all" "size=6"/>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <label for="transmission">Transmission (%)</label>
                          </td>
                          <td>
                            <input type="text" name="transmission" id="transmission" value="" class="text ui-widget-content ui-corner-all" "size=6"/>
                          </td>
                        </tr>

                     </table>
              </fieldset>
              </form>
          </div> \n
          ''')
      jon_summary.write("%2s</body>\n</html>\n"%'')
      jon_summary.close()
      if os.path.exists(f):
        shutil.copy(f,self.working_dir)

    except:
      self.logger.exception('**ERROR in htmlSummaryShort**')

class RunLabelit(Process):
  def __init__(self,input,output,params,logger=None):
    """
    #The minimum input
    [   'AUTOINDEX',
    {   'work': '/gpfs6/users/necat/Jon/RAPD_test/Output'},
    {   'binning': '2x2',
        'distance': '550.0',
        'fullname': '/gpfs5/users/GU/WUSTL_Li_Feb12/images/M-native4/Feru2_6_091.img',
        'twotheta': '0.0'},
    {   'x_beam': '153.66', 'y_beam': '158.39'},
    ('127.0.0.1', 50001)]
    """
    logger.info('RunLabelit.__init__')
    self.st = time.time()
    self.input                              = input
    self.output                             = output
    self.logger                             = logger
    #Setting up data input
    self.setup                              = self.input[1]
    self.header                             = self.input[2]
    self.header2                            = False
    #if self.input[3].has_key('distance'):
    if self.input[3].has_key('fullname'):
      self.header2                        = self.input[3]
      self.preferences                    = self.input[4]
    else:
      self.preferences                    = self.input[3]
    #self.controller_address                 = self.input[-1]
    #params
    self.test                               = params.get('test',False)
    #Will not use RAM if self.cluster_use=True since runs would be on separate nodes. Adds 1-3s to total run time.
    self.cluster_use                        = params.get('cluster',True)
    #If self.cluster_use == True, you can specify a batch queue on your cluster. False to not specify.
    self.cluster_queue                      = params.get('cluster_queue',False)
    #Get detector vendortype for settings. Defaults to ADSC.
    self.vendortype                         = params.get('vendortype','ADSC')
    #Turn on verbose output
    self.verbose                            = params.get('verbose',False)
    #Number of Labelit iteration to run.
    self.iterations                         = params.get('iterations',6)
    #If limiting number of LABELIT run on cluster.
    self.red                                = params.get('redis',False)
    self.short                              = False
    if self.iterations != 6:
      self.short                          = True
    #Sets settings so I can view the HTML output on my machine (not in the RAPD GUI), and does not send results to database.
    #******BEAMLINE SPECIFIC*****
    if self.header.has_key('acc_time'):
      self.gui                   = True
      self.test                  = False
    else:
      self.gui                   = False
    #******BEAMLINE SPECIFIC*****
    #Set times for processes. 'False' to disable.
    if self.header2:
      self.labelit_timer                  = 180
    else:
      self.labelit_timer                  = 120
    #Turns on multiprocessing for everything
    #Turns on all iterations of Labelit running at once, sorts out highest symmetry solution, then continues...(much better!!)
    self.multiproc                          = True
    if self.preferences.has_key('multiprocessing'):
      if self.preferences.get('multiprocessing') == 'False':
        self.multiproc                  = False
    self.sample_type = self.preferences.get('sample_type','Protein')
    self.spacegroup  = self.preferences.get('spacegroup','None')

    #This is where I place my overall folder settings.
    self.working_dir                        = self.setup.get('work')
    #this is where I have chosen to place my results
    self.auto_summary                       = False
    self.labelit_input                      = False
    self.labelit_log                        = {}
    self.labelit_results                    = {}
    self.labelit_summary                    = False
    self.labelit_failed                     = False
    #Labelit settings
    self.index_number                       = False
    self.ignore_user_cell                   = False
    self.ignore_user_SG                     = False
    self.min_good_spots                     = False
    self.twotheta                           = False
    #dicts for running the Queues
    self.labelit_jobs                       = {}
    self.pids                               = {}

    Process.__init__(self,name='RunLabelit')
    self.start()

  def run(self):
    """
    Convoluted path of modules to run.
    """
    if self.verbose:
      self.logger.debug('RunLabelit::run')
    self.preprocess()
    #Make the initial dataset_prefernces.py file
    self.preprocessLabelit()
    if self.short:
      self.labelit_timer = 300
      Utils.foldersLabelit(self,self.iterations)
      #if a specific iteration is sent in then it only runs that one
      if self.iterations == 0:
        self.labelit_jobs[self.processLabelit().keys()[0]] = 0
      else:
        self.labelit_jobs[Utils.errorLabelit(self,self.iterations).keys()[0]] = self.iterations
    else:
      #Create the separate folders for the labelit runs, modify the dataset_preferences.py file, and launch for each iteration.
      Utils.foldersLabelit(self)
      #Launch first job
      self.labelit_jobs[self.processLabelit().keys()[0]] = 0
      #If self.multiproc==True runs all labelits at the same time.
      if self.multiproc:
        for i in range(1,self.iterations):
          self.labelit_jobs[Utils.errorLabelit(self,i).keys()[0]] = i
    self.Queue()
    if self.short == False:
      #Put the logs together
      self.labelitLog()
    self.postprocess()

  def preprocess(self):
    """
    Setup the working dir in the RAM and save the dir where the results will go at the end.
    """
    if self.verbose:
      self.logger.debug('RunLabelit::preprocess')
    if os.path.exists(self.working_dir) == False:
      os.makedirs(self.working_dir)
    os.chdir(self.working_dir)
    if self.test:
      if self.short == False:
        self.logger.debug('TEST IS ON')
        print 'TEST IS ON'

  def preprocessLabelit(self):
    """
    Setup extra parameters for Labelit if turned on. Will always set beam center from image header.
    Creates dataset_preferences.py file for editing later in the Labelit error iterations if needed.
    """
    if self.verbose:
      self.logger.debug('RunLabelit::preprocessLabelit')
    try:
      twotheta       = str(self.header.get('twotheta','0'))
      #distance       = str(self.header.get('distance'))
      x_beam         = str(self.preferences.get('x_beam',self.header.get('beam_center_x')))
      if x_beam == '0':
        x_beam     = str(self.header.get('beam_center_x'))
      y_beam         = str(self.preferences.get('y_beam',self.header.get('beam_center_y')))
      if y_beam == '0':
        y_beam     = str(self.header.get('beam_center_y'))
      binning = True
      if self.vendortype == 'ADSC':
        if self.header.get('binning') == 'none':
          binning = False
      """
      #For determining detector type. Should move to rapd_site probably.
      if self.header.get('fullname')[-3:] == 'cbf':
        if float(x_beam) > 200.0:
          self.vendortype = 'Pilatus-6M'
        else:
          self.vendortype = 'ADSC-HF4M'
      else:
        self.vendortype = 'ADSC'
        if self.header.get('binning') == 'none':
          binning = False
      """
      if self.test == False:
        preferences    = open('dataset_preferences.py','w')
        preferences.write('#####Base Labelit settings#####\n')
        preferences.write('best_support=True\n')
        #Set Mosflm RMSD tolerance larger
        preferences.write('mosflm_rmsd_tolerance=4.0\n')

        #If binning is off. Force Labelit to use all pixels(MAKES THINGS WORSE). Increase number of spots to use for indexing.
        if binning == False:
          preferences.write('distl_permit_binning=False\n')
          preferences.write('distl_maximum_number_spots_for_indexing=600\n')

        #If user wants to change the res limit for autoindexing.
        if str(self.preferences.get('index_hi_res','0.0')) != '0.0':
          #preferences.write('distl.res.outer='+index_hi_res+'\n')
          preferences.write('distl_highres_limit=%s\n'%self.preferences.get('index_hi_res'))
        #Always specify the beam center.
        #If Malcolm flips the beam center in the image header...
        if self.preferences.get('beam_flip','False') == 'True':
          preferences.write('autoindex_override_beam=(%s,%s)\n'%(y_beam,x_beam))
        else:
          preferences.write('autoindex_override_beam=(%s,%s)\n'%(x_beam,y_beam))
        #If two-theta is being used, specify the angle and distance correctly.
        if twotheta.startswith('0'):
          preferences.write('beam_search_scope=0.2\n')
        else:
          self.twotheta = True
          preferences.write('beam_search_scope=0.5\n')
          preferences.write('autoindex_override_twotheta=%s\n'%twotheta)
          #preferences.write('autoindex_override_distance='+distance+'\n')
        preferences.close()

    except:
      self.logger.exception('**ERROR in RunLabelit.preprocessLabelit**')

  def processLabelit(self, iteration=0, inp=False):
    """
    Construct the labelit command and run. Passes back dict with PID:iteration.
    """
    if self.verbose:
      self.logger.debug('RunLabelit::processLabelit')
    try:
      labelit_input = []
      #Check if user specific unit cell
      d = {'a': False, 'c': False, 'b': False, 'beta': False, 'alpha': False, 'gamma': False}
      counter = 0
      for l in d.keys():
        temp = str(self.preferences.get(l,0.0))
        if temp != '0.0':
          d[l] = temp
          counter += 1
      if counter != 6:
        d = False
      #put together the command for labelit.index
      command = 'labelit.index '
      #If first labelit run errors because not happy with user specified cell or SG then ignore user input in the rerun.
      if self.ignore_user_cell == False:
        if d:
          command += 'known_cell=%s,%s,%s,%s,%s,%s ' % (d['a'], d['b'], d['c'], d['alpha'], d['beta'], d['gamma'])
      if self.ignore_user_SG == False:
        if self.spacegroup != 'None':
          command += 'known_symmetry=%s ' % self.spacegroup
      #For peptide crystals. Doesn't work that much.
      if self.sample_type == 'Peptide':
        command += 'codecamp.maxcell=80 codecamp.minimum_spot_count=10 '
      if inp:
        command += '%s '%inp
      command += '%s '%self.header.get('fullname')
      #If pair of images
      if self.header2:
        command += '%s '%self.header2.get('fullname')
      #Save the command to the top of log file, before running job.
      if self.verbose:
        self.logger.debug(command)
      labelit_input.append(command)
      if iteration == 0:
        self.labelit_log[str(iteration)] = labelit_input
      else:
        self.labelit_log[str(iteration)].extend(labelit_input)
      labelit_jobs = {}
      #Don't launch job if self.test = True
      if self.test:
        labelit_jobs['junk%s'%iteration] = iteration
      else:
        log = os.path.join(os.getcwd(), 'labelit.log')
        #queue to retrieve the PID or JobIB once submitted.
        pid_queue = Queue()
        if self.cluster_use:
          #Delete the previous log still in the folder, otherwise the cluster jobs will append to it.
          if os.path.exists(log):
            os.system("rm -rf %s" % log)
          if self.short:
            if self.red:
              run = Process(target=BLspec.processCluster, args=(self, (command, log, 1, self.cluster_queue, "bc_throttler"), pid_queue))
            else:
              #run = Process(target=Utils.processCluster, args=(self,(command,log,'all.q'),queue))
              run = Process(target=BLspec.processCluster, args=(self, (command, log, self.cluster_queue), pid_queue))
          else:
            #run = Process(target=Utils.processCluster,args=(self,(command,log,'index.q'),queue))
            run = Process(target=BLspec.processCluster, args=(self, (command, log, self.cluster_queue), pid_queue))
        else:
          run = Process(target=Utils.processLocal, args=((command, log), self.logger, pid_queue))
        run.start()
        #Save the PID for killing the job later if needed.
        self.pids[str(iteration)] = pid_queue.get()
        labelit_jobs[run] = iteration
      #return a dict with the job and iteration
      return(labelit_jobs)

    except:
      self.logger.exception('**Error in RunLabelit.processLabelit**')

  def postprocessLabelit(self,iteration=0,run_before=False,blank=False):
    """
    Sends Labelit log for parsing and error checking for rerunning Labelit. Save output dicts.
    """
    if self.verbose:
      self.logger.debug('RunLabelit::postprocessLabelit')
    try:
      Utils.foldersLabelit(self,iteration)
      #labelit_failed = False
      if blank:
        error = 'Not enough spots for autoindexing.'
        if self.verbose:
          self.logger.debug(error)
        self.labelit_log[str(iteration)].extend(error+'\n')
        return(None)
      else:
        log = open('labelit.log','r').readlines()
        self.labelit_log[str(iteration)].extend('\n\n')
        self.labelit_log[str(iteration)].extend(log)
        data = Parse.ParseOutputLabelit(self,log,iteration)
        if self.short:
          #data = Parse.ParseOutputLabelitNoMosflm(self,log,iteration)
          self.labelit_results = { 'Labelit results' : data }
        else:
          #data = Parse.ParseOutputLabelit(self,log,iteration)
          self.labelit_results[str(iteration)] = { 'Labelit results' : data }
    except:
      self.logger.exception('**ERROR in RunLabelit.postprocessLabelit**')

    #Do error checking and send to correct place according to iteration.
    out = {'bad input': {'error':'Labelit did not like your input unit cell dimensions or SG.','run':'Utils.errorLabelitCellSG(self,iteration)'},
           'bumpiness': {'error':'Labelit settings need to be adjusted.','run':'Utils.errorLabelitBump(self,iteration)'},
           'mosflm error': {'error':'Mosflm could not integrate your image.','run':'Utils.errorLabelitMosflm(self,iteration)'},
           'min good spots': {'error':'Labelit did not have enough spots to find a solution','run':'Utils.errorLabelitGoodSpots(self,iteration)'},
           'no index': {'error':'No solutions found in Labelit.','run':'Utils.errorLabelit(self,iteration)'},
           'fix labelit': {'error':'Distance is not getting read correctly from the image header.','kill':True},
           'no pair': {'error':'Images are not a pair.','kill':True},
           'failed': {'error':'Autoindexing Failed to find a solution','kill':True},
           'min spots': {'error':'Labelit did not have enough spots to find a solution.','run1':'Utils.errorLabelitMin(self,iteration,data[1])',
                         'run2':'Utils.errorLabelit(self,iteration)'},
           'fix_cell': {'error':'Labelit had multiple choices for user SG and failed.','run1':'Utils.errorLabelitFixCell(self,iteration,data[1],data[2])',
                        'run2':'Utils.errorLabelitCellSG(self,iteration)'},
           }
    #If Labelit results are OK, then...
    if type(data) == dict:
      d = False
    #Otherwise deal with fixing and rerunning Labelit
    elif type(data) == tuple:
      d = data[0]
    else:
      d = data
    if d:
      if out.has_key(d):
        if out[d].has_key('kill'):
          if self.multiproc:
            Utils.errorLabelitPost(self,iteration,out[d].get('error'),True)
          else:
            Utils.errorLabelitPost(self,self.iterations,out[d].get('error'))
        else:
          Utils.errorLabelitPost(self,iteration,out[d].get('error'),run_before)
          if self.multiproc:
            if run_before == False:
              return(eval(out[d].get('run',out[d].get('run1'))))
          else:
            if iteration <= self.iterations:
              return(eval(out[d].get('run',out[d].get('run2'))))
      else:
        error = 'Labelit failed to find solution.'
        Utils.errorLabelitPost(self,iteration,error,run_before)
        if self.multiproc == False:
          if iteration <= self.iterations:
            return (Utils.errorLabelit(self,iteration))

  def postprocess(self):
    """
    Send back the results and logs.
    """
    if self.verbose:
      self.logger.debug('RunLabelit::postprocess')

    try:
      #Free up spot on cluster.
      if self.short and self.red:
        self.red.lpush('bc_throttler',1)

      #Pass back output
      self.output.put(self.labelit_results)
      if self.short == False:
        self.output.put(self.labelit_log)

    except:
      self.logger.exception('**ERROR in RunLabelit.postprocess**')

  def Queue(self):
    """
    Queue for Labelit.
    """
    if self.verbose:
      self.logger.debug('RunLabelit::Queue')
    try:
      timed_out = False
      timer = 0
      #labelit = False
      jobs = self.labelit_jobs.keys()
      #Set wait time longer to lower the load on the node running the job.
      if self.short:
        wait = 1
      else:
        wait = 0.1
      if jobs != ['None']:
        counter = len(jobs)
        while counter != 0:
          for job in jobs:
            if self.test:
              running = False
            else:
              running = job.is_alive()
            if running == False:
              jobs.remove(job)
              iteration = self.labelit_jobs[job]
              if self.verbose:
                self.logger.debug('Finished Labelit%s'%iteration)
                print 'Finished Labelit%s'%iteration
              #Check if job had been rerun, fix the iteration.
              if iteration >= 10:
                iteration -=10
                job = self.postprocessLabelit(iteration,True)
              else:
                job = self.postprocessLabelit(iteration,False)
              #If job is rerun, then save the iteration and pid.
              if job != None:
                if self.multiproc:
                    iteration +=10
                else:
                    iteration +=1
                self.labelit_jobs[job.keys()[0]] = iteration
                jobs.extend(job.keys())
              else:
                counter -= 1
          time.sleep(wait)
          timer += wait
          """
          if self.verbose:
              number = round(timer%1,1)
              if number in (0.0,1.0):
                  print 'Waiting for Labelit to finish '+str(timer)+' seconds'
          """
          if self.labelit_timer:
            if timer >= self.labelit_timer:
              if self.multiproc:
                timed_out = True
                break
              else:
                iteration += 1
                if iteration <= self.iterations:
                  Utils.errorLabelit(self,iteration)
                else:
                  timed_out = True
                  break
        if timed_out:
          self.logger.debug('Labelit timed out.')
          for job in jobs:
            i = self.labelit_jobs[job]
            if i >= 10:
              i -=10
            self.labelit_results[str(i)] = {'Labelit results': 'FAILED'}
            if self.cluster_use:
              #Utils.killChildrenCluster(self,self.pids[str(i)])
              BLspec.killChildrenCluster(self,self.pids[str(i)])
            else:
              Utils.killChildren(self,self.pids[str(i)])

      if self.short == False:
        self.logger.debug('Labelit finished.')

    except:
      self.logger.exception('**Error in RunLabelit.Queue**')

  def labelitLog(self):
    """
    Put the Labelit logs together.
    """
    if self.verbose:
      self.logger.debug('RunLabelit::LabelitLog')
    try:
      for i in range(0,self.iterations):
        if self.labelit_log.has_key(str(i)):
          junk = []
          junk.append('-------------------------\nLABELIT ITERATION %s\n-------------------------\n'%i)
          if i == 0:
            self.labelit_log['run1'] = ['\nRun 1\n']
          self.labelit_log['run1'].extend(junk)
          self.labelit_log['run1'].extend(self.labelit_log[str(i)])
          self.labelit_log['run1'].extend('\n')
        else:
          self.labelit_log['run1'].extend('\nLabelit iteration %s FAILED\n'%i)

    except:
      self.logger.exception('**ERROR in RunLabelit.LabelitLog**')

def BestAction(inp,logger,output=False):
  """
  Run Best.
  """
  logger.debug('BestAction')
  try:
    command,log = inp
    #Have to do this otherwise command is written to bottom of file??
    f = open(log,'w')
    f.write('\n\n'+command+'\n')
    f.close()
    f = open(log,'a')
    job = subprocess.Popen(command,shell=True,stdout=f,stderr=f)
    if output:
      output.put(job.pid)
    job.wait()
    f.close()
  except:
    logger.exception('**Error in BestAction**')

if __name__ == '__main__':
  #construct test input for Autoindexing/strategy
  #This is an example input dict used for testing this script.
  #Input dict file. If autoindexing from two images, just include a third dict section for the second image header.
  ###To see all the input options look at extras/rapd_input.py (autoindexInput)###

  inp = ["AUTOINDEX",
  {"work": "/gpfs6/users/necat/Jon/RAPD_test/Output",
   },

  #Info from first image
  {"wavelength": "0.9792", #RADDOSE
   "binning": "2x2", #LABELIT
   #"binning": "none", #
   "time": "1.00",  #BEST
   "twotheta": "0.00", #LABELIT
   "transmission": "20",  #BEST
   #"beam_center_x": "216.71", #PILATUS
   #"beam_center_y": "222.45", #PILATUS
   "beam_center_x": "150.72", #Q315
   "beam_center_y": "158.68", #Q315
   #"beam_center_x": "172.80", #HF4M
   #"beam_center_y": "157.18", #HF4M
   "flux":'1.6e11', #RADDOSE
   "beam_size_x":"0.07", #RADDOSE
   "beam_size_y":"0.03", #RADDOSE
   "gauss_x":'0.03', #RADDOSE
   "gauss_y":'0.01', #RADDOSE
   "fullname": "/gpfs2/users/chicago/Lewis_E_Dec15/images/snaps/NE51_H4_PAIR_0_001.img",

   #minikappa
   #Uncomment 'mk3_phi' and 'mk3_kappa' commands to tell script to run a minikappa alignment, instead of strategy.
   #"mk3_phi":"0.0", #
   #"mk3_kappa":"0.0", #
   "phi": "0.000",
   "STAC file1": '/gpfs6/users/necat/Jon/RAPD_test/mosflm.mat', #XOAlign
   "STAC file2": '/gpfs6/users/necat/Jon/RAPD_test/bestfile.par', #XOAlign
   "axis_align": 'long',    #long,all,a,b,c,ab,ac,bc #XOAlign
  },

   #Info from second image. Remove this dict if NOT present in run.
  {"wavelength": "0.9792", #RADDOSE
   "binning": "2x2", #LABELIT
   #"binning": "none", #
   "time": "1.00",  #BEST
   "twotheta": "0.00", #LABELIT
   "transmission": "20",  #BEST
   #"beam_center_x": "216.71", #PILATUS
   #"beam_center_y": "222.45", #PILATUS
   "beam_center_x": "150.72", #Q315
   "beam_center_y": "158.68", #Q315
   #"beam_center_x": "172.80", #HF4M
   #"beam_center_y": "157.18", #HF4M
   "flux":'1.6e11', #RADDOSE
   "beam_size_x":"0.07", #RADDOSE
   "beam_size_y":"0.03", #RADDOSE
   "gauss_x":'0.03', #RADDOSE
   "gauss_y":'0.01', #RADDOSE
   "fullname": "/gpfs2/users/chicago/Lewis_E_Dec15/images/snaps/NE51_H4_PAIR_0_002.img",

   #minikappa
   #Uncomment 'mk3_phi' and 'mk3_kappa' commands to tell script to run a minikappa alignment, instead of strategy.
   #"mk3_phi":"0.0", #
   #"mk3_kappa":"0.0", #
   "phi": "0.000",
   "STAC file1": '/gpfs6/users/necat/Jon/RAPD_test/mosflm.mat', #XOAlign
   "STAC file2": '/gpfs6/users/necat/Jon/RAPD_test/bestfile.par', #XOAlign
   "axis_align": 'long',    #long,all,a,b,c,ab,ac,bc #XOAlign
  },

  #Beamline params
  {"strategy_type": 'best', #Preferred program for strategy
   #"strategy_type": 'mosflm', #
   "crystal_size_x": "100", #RADDOSE
   "crystal_size_y": "100", #RADDOSE
   "crystal_size_z": "100", #RADDOSE
   "shape": "2.0", #BEST
   "sample_type": "Protein", #LABELIT, BEST
   "best_complexity": "none", #BEST
   "susceptibility": "1.0", #BEST
   "index_hi_res": 0.0, #LABELIT
   "spacegroup": "None", #LABELIT, BEST, beam_center
   #"spacegroup": "R3", #
   "solvent_content": 0.55, #RADDOSE
   "beam_flip": "False", #NECAT, when x and y are sent reversed.
   "multiprocessing":"True", #Specifies to use 4 cores to make Autoindex much faster.
   "x_beam": "0",#Used if position not in header info
   "y_beam": "0",#Used if position not in header info
   "aimed_res": 0.0, #BEST to override high res limit
   "a":0.0, ##LABELIT
   "b":0.0, ##LABELIT
   "c":0.0, ##LABELIT
   "alpha":0.0, #LABELIT
   "beta":0.0, #LABELIT
   "gamma":0.0, #LABELIT

   #Change these if user wants to continue dataset with other crystal(s).
   "reference_data_id": None, #MOSFLM
   #"reference_data_id": 1,#MOSFLM
   #"reference_data": [['/gpfs6/users/necat/Jon/RAPD_test/index09.mat', 0.0, 30.0, 'junk_1_1-30','P41212']],#MOSFLM
   'reference_data': [['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',0.0,20.0,'junk','P3'],['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',40.0,50.0,'junk2','P3']],#MOSFLM
   #MOSFLM settings for multisegment strategy (like give me best 30 degrees to collect). Ignored if "mosflm_rot" !=0.0
   "mosflm_rot": 0.0, #MOSFLM
   "mosflm_seg":1, #MOSFLM
   "mosflm_start":0.0,#MOSFLM
   "mosflm_end":360.0,#MOSFLM
    },

  ('127.0.0.1', 50001)#self.sendBack2 for sending results back to rapd_cluster.
  ]
  #start logging
  import logging, logging.handlers
  LOG_FILENAME = os.path.join(inp[1].get('work'),'rapd.log')
  #LOG_FILENAME = '/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_jon.log'
  # Set up a specific logger with our desired output level
  logger = logging.getLogger('RAPDLogger')
  logger.setLevel(logging.DEBUG)
  # Add the log message handler to the logger
  handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,maxBytes=100000,backupCount=5)
  #add a formatter
  formatter = logging.Formatter("%(asctime)s - %(message)s")
  handler.setFormatter(formatter)
  logger.addHandler(handler)
  RapdAgent(inp, logger=logger)

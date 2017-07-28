"""
Query the PDB for similar unit cell parameters
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2010-2017, Cornell University
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
__created__ = "2010-11-10"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Production"

# Standar imports
from multiprocessing import Process, Queue
import os
import shutil
import time
import urllib2

# RAPD imports
from rapd_agent_phaser import RunPhaser
import subcontractors.parse as Parse
import subcontractors.summary as Summary
from utils.communicate import rapd_send
import utils.xutils as Utils

class PDBQuery(Process):
  def __init__(self, input, output=None, logger=None):
    logger.info('PDBQuery.__init__')
    self.st = time.time()
    self.input = input
    self.output = output
    self.logger = logger

    #Input parameters
    self.percent                            = 0.01
    #Calc ADF for each solution (creates a lot of big map files).
    self.adf                                = False
    #Run rigid-body refinement after MR.
    self.rigid                              = False
    #Search for common contaminants.
    self.search_common                      = True

    #Params
    self.cell2                              = False
    self.working_dir                        = self.input[0].get('dir',os.getcwd())
    self.test                               = self.input[0].get('test',False)
    self.sample_type                        = self.input[0].get('type','Protein')
    self.cluster_use                        = self.input[0].get('cluster',True)
    self.clean                              = self.input[0].get('clean',True)
    self.gui                                = self.input[0].get('gui',True)
    self.controller_address                 = self.input[0].get('control',False)
    self.verbose                            = self.input[0].get('verbose',False)
    self.datafile                           = Utils.convertUnicode(self,self.input[0].get('data'))
    self.cell_output                        = False
    self.cell_summary                       = False
    self.tooltips                           = False
    self.pdb_summary                        = False
    self.large_cell                         = False
    self.input_sg                           = False
    self.laue                               = False
    self.dres                               = False
    self.common                             = False
    self.phaser_results                     = {}
    self.jobs                               = {}
    self.pids                               = {}
    self.pdbquery_timer                     = 30
    self.phaser_timer                       = 2000 #was 600 but too short for mackinnon (144,144,288,90,90,90)
    #Used as technicality
    self.solvent_content                    = 0.55

    Process.__init__(self,name='PDBQuery')
    self.start()

  def run(self):
    """
    Convoluted path of modules to run.
    """
    if self.verbose:
        self.logger.debug('PDBQuery::run')

    self.preprocess()
    #Utils.getSGInfo(self,'/gpfs5/users/necat/rapd/pdbq/pdb/y3/2y3e.cif')

    self.processPDB()
    if self.search_common:
      self.processCommonPDB()

    self.processPhaser()
    self.Queue()
    self.postprocess()

  def preprocess(self):
    """
    Check input file and convert to mtz if neccessary.
    """
    if self.verbose:
      self.logger.debug('PDBQuery::preprocess')
    try:
      self.input_sg,self.cell,self.cell2,vol = Utils.getMTZInfo(self,False,True,True)
      self.dres = Utils.getRes(self)
      self.laue = Utils.subGroups(self,Utils.convertSG(self,self.input_sg),'simple')
      #Set by number of residues in AU. Ribosome (70s) is 24k.
      if Utils.calcResNumber(self,self.input_sg,False,vol) > 5000:
        self.large_cell = True
        self.phaser_timer = 3000
      if self.test:
        self.logger.debug('TEST IS SET "ON"')
      self.PrintInfo()

    except:
      self.logger.exception('**ERROR in PDBQuery.preprocess**')

  def processPDB(self):
    """
    Check if cell is found in PDB.
    """
    if self.verbose:
      self.logger.debug('PDBQuery::processPDBCell')
    try:
      def connectRCSB(inp):
        l0 = inp
        l1 = ['length_a','length_b','length_c','angle_alpha','angle_beta','angle_gamma']
        querycell  = '<?xml version="1.0" encoding="UTF-8"?>'
        if permute:
          querycell  = '<orgPdbCompositeQuery version="1.0">'
        for y in range(end):
          if permute:
            querycell += '<queryRefinement><queryRefinementLevel>%s</queryRefinementLevel>'%y
            if y != 0:
              querycell += '<conjunctionType>or</conjunctionType>'
          querycell += '<orgPdbQuery><queryType>org.pdb.query.simple.XrayCellQuery</queryType>'
          for x in range(len(l1)):
            querycell += '<cell.%s.comparator>between</cell.%s.comparator>'%(2*(l1[x],))
            querycell += '<cell.%s.min>%s</cell.%s.min>'%(l1[x],float(self.cell2[l2[y][x]])-float(self.cell2[l2[y][x]])*self.percent/2,l1[x])
            querycell += '<cell.%s.max>%s</cell.%s.max>'%(l1[x],float(self.cell2[l2[y][x]])+float(self.cell2[l2[y][x]])*self.percent/2,l1[x])
          querycell += '</orgPdbQuery>'
          if permute:
            querycell += '</queryRefinement>'
            if y == end -1:
              querycell += '</orgPdbCompositeQuery>'
        self.logger.debug("Checking the PDB...")
        self.logger.debug(querycell)
        #Sometimes I get an error in urlopen saying it can't resolve the output from the PDB.
        try:
          #l0.extend(urllib2.urlopen(urllib2.Request('http://www.rcsb.org/pdb/rest/search',data=querycell)).read().split())
          l0.extend(urllib2.urlopen(urllib2.Request('http://www.rcsb.org/pdb/rest/search',data=querycell),timeout=10).read().split())
        except:
          pass
        return(l)

      def connectFrank(inp):
        import json
        _d0_ = inp
        l1 = ['a','b','c','alpha','beta','gamma']
        for y in range(end):
          _d_ = {}
          for x in range(len(l1)):
            _d_[l1[x]] = [float(self.cell2[l2[y][x]])-float(self.cell2[l2[y][x]])*self.percent/2,
                         float(self.cell2[l2[y][x]])+float(self.cell2[l2[y][x]])*self.percent/2]
          #Send to Frank thru urllib2
          response = urllib2.urlopen(urllib2.Request('http://remote.nec.aps.anl.gov:3030/pdb/rest/search/',data=json.dumps(_d_))).read()
          j = json.loads(response)
          for k in j.keys():
            j[k]['Name'] = j[k].pop('struct.pdbx_descriptor')
          #print j
          _d0_.update(j)
        return(_d0_)

      def limitOut(inp):
        l = inp.keys()[:i+1]
        for p in inp.keys():
          if l.count(p) == 0:
            del inp[p]
        return(inp)

      d = {}
      permute = False
      end = 1
      l2 = [(0,1,2,3,4,5),(1,2,0,4,5,3),(2,0,1,5,3,4)]
      #Check for orthorhombic
      if self.laue == '16':
        permute = True
      #Check monoclinic when Beta is near 90.
      if self.laue in ('3','5'):
        if 89.0 < float(self.cell2[4]) < 91.0:
          permute = True
      if permute:
        end = len(l2)
      #Limit the minimum number of results
      no_limit = False
      if self.cluster_use:
        if self.large_cell:
          i = 10
        elif permute:
          i = 60
        else:
          no_limit = True
          i = 40
      else:
        i = 8
      counter = 0
      #limit the unit cell difference to 25%. Also stops it if errors are received.
      while counter < 25:
        #l = connectRCSB(l)
        #l = connectePDB(l)
        d = connectFrank(d)
        if len(d.keys()) != 0:
          for line in d.keys():
            #remove anything bigger than 4 letters
            if len(line) > 4:
              del d[line]

          #Do not limit number of results if many models come out really close in cell dimensions.
          if counter in (0,1):
            #Limit output
            if no_limit == False:
              d = limitOut(d)
          else:
            d = limitOut(d)
        if len(d.keys()) < i:
          counter += 1
          self.percent += 0.01
          self.logger.debug("Not enough PDB results. Going for more...")
        else:
          break
      if len(d.keys()) > 0:
        self.cell_output = d
      else:
        self.cell_output = {}
        self.logger.debug('Failed to find pdb with similar cell.')

    except:
      self.logger.exception('**ERROR in PDBQuery.processPDBCell**')

  def processCommonPDB(self):
    """
    Add common PDB contaminants to the search list.
    """
    if self.verbose:
      self.logger.debug('PDBQuery::processCommonPDB')
    try:
      #Dict with PDB codes for common contaminants.
      d = {
      '1E1O': {   'Name': 'LYSYL-TRNA SYNTHETASE, HEAT INDUCIBLE',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/e1/1e1o.cif'},
      '1ESO': {   'Name': 'CU, ZN SUPEROXIDE DISMUTASE',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/es/1eso.cif'},
      '1G6N': {   'Name': 'CATABOLITE GENE ACTIVATOR PROTEIN',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/g6/1g6n.cif'},
      '1GGE': {   'Name': 'PROTEIN (CATALASE HPII)',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/gg/1gge.cif'},
      '1I6P': {   'Name': 'CARBONIC ANHYDRASE',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/i6/1i6p.cif'},
      '1OEE': {   'Name': 'HYPOTHETICAL PROTEIN YODA',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/oe/1oee.cif'},
      '1OEL': {   'Name': 'GROEL (HSP60 CLASS)',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/oe/1oel.cif'},
      '1PKY': {   'Name': 'PYRUVATE KINASE',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/pk/1pky.cif'},
      '1X8F': {   'Name': '2-dehydro-3-deoxyphosphooctonate aldolase',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/x8/1x8f.cif'},
      '1Z7E': {   'Name': 'protein ArnA',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/z7/1z7e.cif'},
      '2JGD': {   'Name': '2-OXOGLUTARATE DEHYDROGENASE E1 COMPONENT',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/jg/2jgd.cif'},
      '2QZS': {   'Name': 'glycogen synthase',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/qz/2qzs.cif'},
      '2VF4': {   'Name': 'GLUCOSAMINE--FRUCTOSE-6-PHOSPHATE AMINOTRANSFERASE',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/vf/2vf4.cif'},
      '2Y90': {   'Name': 'PROTEIN HFQ',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/y9/2y90.cif'},
      '3CLA': {   'Name': 'TYPE III CHLORAMPHENICOL ACETYLTRANSFERASE',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/cl/3cla.cif'},
      '4UEJ': {   'Name': 'GALACTITOL-1-PHOSPHATE 5-DEHYDROGENASE',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/ue/4uej.cif'},
      '4QEQ': {   'Name': 'Lysozyme C',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/qe/4qeq.cif'},
      '2I6W': {   'Name': 'AcrB',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/i6/2i6w.cif'},
      '1NEK': {   'Name': 'Succinate dehydrogenase flavoprotein subunit',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/ne/1nek.cif'},
      '1TRE': {   'Name': 'TRIOSEPHOSPHATE ISOMERASE',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/tr/1tre.cif'},
      '1I40': {   'Name': 'INORGANIC PYROPHOSPHATASE',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/i4/1i40.cif'},
      '2P9H': {   'Name': 'Lactose operon repressor',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/p9/2p9h.cif'},
      '1PHO': {   'Name': 'PHOSPHOPORIN',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/ph/1pho.cif'},
      '1BTL': {   'Name': 'BETA-LACTAMASE',
                  'path': '/gpfs5/users/necat/rapd/pdbq/pdb/bt/1btl.cif'},
      }
      #Save these codes in a separate list so they can be separated in the Summary.
      self.common = d.keys()
      #Remove PDBs from self.common if they were already caught by unit cell dimensions.
      for line in d.keys():
        if self.cell_output.keys().count(line):
          del d[line]
          self.common.remove(line)
      self.cell_output.update(d)

    except:
      self.logger.exception('**ERROR in PDBQuery.processCommonPDB**')


  def processPhaser(self):
    """
    Start Phaser for input pdb.
    """
    if self.verbose:
      self.logger.debug('PDBQuery::processPhaser')

    def launchJob(inp):
      queue = Queue()
      job = Process(target=RunPhaser,args=(inp,queue,self.logger))
      job.start()
      queue.get()#For the log I don't use
      self.jobs[job] = inp['name']
      self.pids[inp['name']] = queue.get()

    try:
      for code in self.cell_output.keys():
      #for code in ['4ER2']:
        l = False
        copy = 1
        Utils.folders(self,'Phaser_%s'%code)
        f = os.path.basename(self.cell_output[code].get('path'))
        #Check if symlink exists and create if not.
        if os.path.exists(f) == False:
          os.symlink(self.cell_output[code].get('path'),f)
        #If mmCIF, checks if file exists or if it is super structure with
        #multiple PDB codes, and returns False, otherwise sends back SG.
        sg_pdb = Utils.fixSG(self,Utils.getSGInfo(self,f))
        #Remove codes that won't run or PDB/mmCIF's that don't exist.
        if sg_pdb == False:
          del self.cell_output[code]
          continue
        #**Now check all SG's**
        lg_pdb = Utils.subGroups(self,Utils.convertSG(self,sg_pdb),'simple')
        #SG from data
        sg = Utils.convertSG(self,self.laue,True)
        #Fewer mols in AU or in self.common.
        if code in self.common or float(self.laue) > float(lg_pdb):
          #if SM is lower sym, which will cause problems, since PDB is too big.
          #Need full path for copying pdb files to folders.
          pdb_info = Utils.getPDBInfo(self,os.path.join(os.getcwd(),f))
          #Prune if only one chain present, b/c 'all' and 'A' will be the same.
          if len(pdb_info.keys()) == 2:
            for key in pdb_info.keys():
              if key != 'all':
                del pdb_info[key]
          copy = pdb_info['all']['NMol']
          if copy == 0:
            copy = 1
          #if pdb_info['all']['res'] == 0.0:
          if pdb_info['all']['SC'] < 0.2:
            #Only run on chains that will fit in the AU.
            l = [chain for chain in pdb_info.keys() if pdb_info[chain]['res'] != 0.0]
        #More mols in AU
        elif float(self.laue) < float(lg_pdb):
          pdb_info = Utils.getPDBInfo(self,f,True,True)
          copy = pdb_info['all']['NMol']
        #Same number of mols in AU.
        else:
          pdb_info = Utils.getPDBInfo(self,f,False,True)

        d = {'data':self.datafile,'pdb':f,'name':code,'verbose':self.verbose,'sg':sg,
             'copy':copy,'test':self.test,'cluster':self.cluster_use,'cell analysis':True,
             'large':self.large_cell,'res':Utils.setPhaserRes(self,pdb_info['all']['res']),
            }

        if l == False:
          launchJob(d)
        else:
          d1 = {}
          for chain in l:
            new_code = '%s_%s'%(code,chain)
            Utils.folders(self,'Phaser_%s'%new_code)
            d.update({'pdb':pdb_info[chain]['file'],'name':new_code,'copy':pdb_info[chain]['NMol'],
                      'res':Utils.setPhaserRes(self,pdb_info[chain]['res'])})
            launchJob(d)

    except:
      self.logger.exception('**ERROR in PDBQuery.processPhaser**')

  def processRefine(self,inp):
    """
    Run phenix.refine rigid-body on solution. My old boss wanted this. Will be incorporated
    into future ligand finding pipeline. This can be enabled at top of script, but takes extra time.
    """
    if self.verbose:
      self.logger.debug('PDBQuery::processRefine')
    try:
      pdb = '%s.1.pdb'%inp
      info = Utils.getPDBInfo(self,pdb,False)
      command  = 'phenix.refine %s %s strategy=tls+rigid_body refinement.input.xray_data.labels=IMEAN,SIGIMEAN '%(pdb,self.datafile)
      command += 'refinement.main.number_of_macro_cycles=1 nproc=2'
      chains = [chain for chain in info.keys() if chain != 'all']
      for chain in chains:
        command += ' refine.adp.tls="chain %s"'%chain
      if self.test == False:
        Utils.processLocal((command,'rigid.log'),self.logger)
      else:
        os.system('touch rigid.log')

    except:
      self.logger.exception('**ERROR in PDBQuery.processRefine**')

  def postprocessPhaser(self,inp):
    """
    Look at Phaser results.
    """
    if self.verbose:
      self.logger.debug('PDBQuery::postprocessPhaser')
    try:
      nosol = False
      output = []
      if os.path.exists('phaser.log'):
        #For older versions of Phaser
        #data = Parse.ParseOutputPhaser(self,open('%s.sum'%inp,'r').readlines())
        data = Parse.ParseOutputPhaser(self,open('phaser.log','r').readlines())
        if data['AutoMR sg'] in ('No solution','Timed out','NA','DL FAILED'):
          nosol = True
        else:
          #Check for negative or low LL-Gain.
          if float(data['AutoMR gain']) < 200.0:
            nosol = True
        if nosol:
          self.phaser_results[inp] = { 'AutoMR results' : Parse.setPhaserFailed('No solution')}
        else:
          self.phaser_results[inp] = { 'AutoMR results' : data }
        if self.rigid:
          if nosol:
            #Tells Queue job is finished
            os.system('touch rigid.com')
          else:
            output.append('rigid')
        if self.adf:
          if nosol:
            #Tells Queue job is finished
            os.system('touch adf.com')
          else:
            #Put path of map and peaks pdb in results
            self.phaser_results[inp].get('AutoMR results').update({'AutoMR adf': '%s_adf.map'%inp})
            self.phaser_results[inp].get('AutoMR results').update({'AutoMR peak':'%s_adf_peak.pdb'%inp})
            output.append('ADF')
      elif self.test:
        #Set output for Phaser runs that didn't actually run.
        self.phaser_results[inp] = { 'AutoMR results' : Parse.setPhaserFailed('No solution')}
      return(output)

    except:
      self.logger.exception('**ERROR in PDBQuery.postprocessPhaser**')

  def Queue(self):
    """
    queue system.
    """
    if self.verbose:
      self.logger.debug('PDBQuery::Queue')
    try:
      timed_out = False
      timer = 0
      if self.jobs != {}:
        jobs = self.jobs.keys()
        while len(jobs) != 0:
          for job in jobs:
            if job.is_alive() == False:
              jobs.remove(job)
              code = self.jobs.pop(job)
              Utils.folders(self,'Phaser_%s'%code)
              new_jobs = []
              if self.test == False:
                del self.pids[code]
              #if self.verbose:
              self.logger.debug('Finished Phaser on %s'%code)
              p = self.postprocessPhaser(code)
              if p.count('rigid'):
                if os.path.exists('rigid.log') == False:
                  j = Process(target=self.processRefine,args=(code,))
                  j.start()
                  new_jobs.append(j)
                  if self.test:
                    time.sleep(5)
              if p.count('ADF'):
                if os.path.exists('adf.com') == False:
                  j = Process(target=Utils.calcADF,args=(self,code))
                  j.start()
                  new_jobs.append(j)
              if len(new_jobs) > 0:
                for j1 in new_jobs:
                  self.jobs[j1] = code
                  jobs.append(j1)
          time.sleep(0.2)
          timer += 0.2
          if self.phaser_timer:
            if timer >= self.phaser_timer:
              timed_out = True
              break
        if timed_out:
          for j in self.jobs.values():
            if self.pids.has_key(j):
              if self.cluster_use:
                BLspec.killChildrenCluster(self,self.pids[j])
              else:
                Utils.killChildren(self,self.pids[j])
            if self.phaser_results.has_key(j) == False:
              self.phaser_results[j] = {'AutoMR results': Parse.setPhaserFailed('Timed out')}
          if self.verbose:
            self.logger.debug('PDBQuery timed out.')
            print 'PDBQuery timed out.'
      if self.verbose:
        self.logger.debug('PDBQuery.Queue finished.')

    except:
      self.logger.exception('**ERROR in PDBQuery.Queue**')

  def PrintInfo(self):
    """
    Print information regarding programs utilized by RAPD
    """
    if self.verbose:
      self.logger.debug('PDBQuery::PrintInfo')
    self.logger.debug('RAPD now using Phenix')
    self.logger.debug('=======================')
    self.logger.debug('RAPD developed using Phenix')
    self.logger.debug('Reference: Adams PD, et al.(2010) Acta Cryst. D66:213-221')
    self.logger.debug('Website: http://www.phenix-online.org/\n')
    self.logger.debug('RAPD developed using Phaser')
    self.logger.debug('Reference: McCoy AJ, et al.(2007) J. Appl. Cryst. 40:658-674.')
    self.logger.debug('Website: http://www.phenix-online.org/documentation/phaser.htm\n')

  def postprocess(self):
    """
    Put everything together and send back dict.
    """
    if self.verbose:
      self.logger.debug('PDBQuery::postprocess')
    output = {}
    status = False
    output_files = False
    cell_results = False
    failed = False

    #Add tar info to automr results and take care of issue if no SCA file was input.
    try:
      def check_bz2(tar):
        #Remove old tar's in working dir, if they exist and copy new one over.
        if os.path.exists(os.path.join(self.working_dir,'%s.bz2'%tar)):
          os.system('rm -rf %s'%os.path.join(self.working_dir,'%s.bz2'%tar))
        shutil.copy('%s.bz2'%tar,self.working_dir)

      if self.cell_output:
        for pdb in self.phaser_results.keys():
          pdb_file = self.phaser_results[pdb].get('AutoMR results').get('AutoMR pdb')
          mtz_file = self.phaser_results[pdb].get('AutoMR results').get('AutoMR mtz')
          adf_file = self.phaser_results[pdb].get('AutoMR results').get('AutoMR adf')
          peak_file = self.phaser_results[pdb].get('AutoMR results').get('AutoMR peak')
          if pdb_file not in ('No solution','Timed out','NA','Still running','DL Failed'):
            #pack all the output files into a tar and save the path
            os.chdir(self.phaser_results[pdb].get('AutoMR results').get('AutoMR dir'))
            tar = '%s.tar'%pdb
            #Speed up in testing mode.
            if os.path.exists('%s.bz2'%tar):
              check_bz2(tar)
              self.phaser_results[pdb].get('AutoMR results').update({'AutoMR tar': os.path.join(self.working_dir,'%s.bz2'%tar)})
            else:
              l = [pdb_file,mtz_file,adf_file,peak_file,pdb_file.replace('.pdb','_refine_001.pdb'),mtz_file.replace('.mtz','_refine_001.mtz')]
              for p in l:
                if os.path.exists(p):
                  os.system('tar -rf %s %s'%(tar,p))
              if os.path.exists(tar):
                os.system('bzip2 -qf %s'%tar)
                check_bz2(tar)
                self.phaser_results[pdb].get('AutoMR results').update({'AutoMR tar': os.path.join(self.working_dir,'%s.bz2'%tar)})
              else:
                self.phaser_results[pdb].get('AutoMR results').update({'AutoMR tar': 'None'})
          #Save everthing into one dict
          if pdb in self.cell_output.keys():
            self.phaser_results[pdb].update(self.cell_output[pdb])
          else:
            self.phaser_results[pdb].update(self.cell_output[pdb[:pdb.rfind('_')]])
        cell_results = { 'Cell analysis results': self.phaser_results}
      else:
        cell_results = { 'Cell analysis results': 'None' }
    except:
      self.logger.exception('**Could not AutoMR results in postprocess.**')
      cell_results = { 'Cell analysis results': 'FAILED'}
      failed = True

    try:
      #Create the output html file
      os.chdir(self.working_dir)
      Summary.summaryCell(self,'pdbquery')
      self.htmlSummary()
      if self.gui:
        sl = 'jon_summary_cell.php'
      else:
        sl = 'jon_summary_cell.html'
      if os.path.exists(os.path.join(self.working_dir,sl)):
        output['Cell summary html'] = os.path.join(self.working_dir,sl)
      else:
        output['Cell summary html'] = 'None'
    except:
      self.logger.exception('**Could not update path of shelx summary html file.**')
      output['Cell summary html']   = 'FAILED'
      failed = True

    try:
      output_files = {'Output files' : output}
    except:
      self.logger.exception('**Could not update the output dict.**')

    #Get proper status.
    if failed:
      status = {'status': 'FAILED'}
      self.clean = False
    else:
      status = {'status': 'SUCCESS'}

    #Put all the result dicts from all the programs run into one resultant dict and pass it along the pipe.
    try:
      results = {}
      if status:
        results.update(status)
      if cell_results:
        results.update(cell_results)
      if output_files:
        results.update(output_files)
      if results:
        self.input.append(results)
      if self.output != None:
        self.output.put(results)
      else:
        if self.gui:
        #   self.sendBack2(self.input)
          rapd_send(self.controller_address, self.input)
    except:
      self.logger.exception('**Could not send results to pipe.**')

    try:
      #Cleanup my mess.
      if self.clean:
        os.chdir(self.working_dir)
        os.system('rm -rf Phaser_* temp.mtz')
        if self.verbose:
          self.logger.debug('Cleaning up Phaser files and folders')
    except:
      self.logger.exception('**Could not cleanup**')

    #Say job is complete.
    t = round(time.time()-self.st)
    self.logger.debug(50*'-')
    self.logger.debug('RAPD PDBQuery complete.')
    self.logger.debug('Total elapsed time: %s seconds'%t)
    self.logger.debug(50*'-')
    if self.output == None:
      print 50*'-'
      print '\nRAPD PDBQuery complete.'
      print 'Total elapsed time: %s seconds'%t
      print 50*'-'

  def htmlSummary(self):
    """
    Create HTML/php files for autoindex/strategy output results.
    """
    if self.verbose:
      self.logger.debug('PDBQuery::htmlSummary')
    try:
      if self.gui:
        jon_summary = open('jon_summary_cell.php','w')
      else:
        jon_summary = open('jon_summary_cell.html','w')
      #jon_summary.write(Utils.getHTMLHeader(self,'phaser'))
      jon_summary.write(Utils.getHTMLHeader(self,'pdbquery'))
      jon_summary.write("%6s$(document).ready(function() {\n"%'')
      if self.gui:
        jon_summary.write("%8s$('button').button(); \n"%'')
      if self.cell_summary:
        jon_summary.write("%8s$('#pdbquery-cell').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bSort": false,\n%11s"bAutoWidth": false });\n'%(5*('',)))
      if self.search_common:
        jon_summary.write("%8s$('#pdbquery-cc').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bSort": false,\n%11s"bAutoWidth": false });\n'%(5*('',)))
      if self.pdb_summary:
        jon_summary.write("%8s$('#pdbquery-pdb').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bSort": false,\n%11s"bAutoWidth": false });\n'%(5*('',)))
      if self.tooltips:
        jon_summary.writelines(self.tooltips)
      jon_summary.write('%6s});\n%4s</script>\n%2s</head>\n%2s<body id="dt_example">\n'%(4*('',)))
      if self.cell_summary:
        jon_summary.writelines(self.cell_summary)
      if self.pdb_summary:
        jon_summary.writelines(self.pdb_summary)
      jon_summary.write('%2s</body>\n</html>\n'%'')
      jon_summary.close()

    except:
        self.logger.exception('**ERROR in PDBQuery.htmlSummary**')

if __name__ == '__main__':
  #construct test input
  import logging, logging.handlers
  inp = [{'dir' :  '/gpfs6/users/necat/Jon/RAPD_test/Output',
            #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/SAD/PK_lu_peak.sca',
            #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/SAD/PK_lu_peak_new_free.mtz',
            'data': '/gpfs6/users/necat/Jon/RAPD_test/Temp/Alex/freer.mtz',
            'cluster': True,
            'test': False,
            'verbose': True,
            #'type': 'Protein',
            'clean': False,
            'gui'  : False,
            'control': ('164.54.212.22',50001),
            'process_id': 11111,
            }]
  #start logging
  LOG_FILENAME = os.path.join(inp[0].get('dir'),'rapd.log')
  # Set up a specific logger with our desired output level
  logger = logging.getLogger('RAPDLogger')
  logger.setLevel(logging.DEBUG)
  # Add the log message handler to the logger
  handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=100000, backupCount=5)
  #add a formatter
  formatter = logging.Formatter("%(asctime)s - %(message)s")
  handler.setFormatter(formatter)
  logger.addHandler(handler)
  #logger.info('PDBQuery.__init__')
  PDBQuery(inp,output=None,logger=logger)

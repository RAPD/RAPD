"""
Provides a comprehensive statistical analysis of an integrated data set
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2011-2016, Cornell University
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
__created__ = "2011-02-02"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Production"

# Standard imports
from multiprocessing import Process, Queue
import os
import time

# RAPD imports
# from rapd_agent_cell import PDBQuery
# from rapd_agent_pp import LabelitPP
# import rapd_beamlinespecific as BLspec
import subcontractors.parse as Parse
import subcontractors.summary as Summary
from utils.communicate import rapd_send
import utils.xutils as Utils

class AutoStats(Process):
  def __init__(self, input, logger=None):
    logger.info('AutoStats.__init__')
    self.st = time.time()
    self.input                              = input
    self.logger                             = logger
    self.working_dir                        = self.input[0].get('dir',os.getcwd())
    self.datafile                           = self.input[0].get('data',False)
    self.gui                                = self.input[0].get('gui',True)
    self.clean                              = self.input[0].get('clean',True)
    self.test                               = self.input[0].get('test',False)
    self.controller_address                 = self.input[0].get('control',False)
    self.verbose                            = self.input[0].get('verbose',False)

    self.clean = False
    self.verbose = True

    #Check if precession photo info included in input
    if self.input[0].has_key('run'):
      self.pp                                 = True
    else:
      self.pp                                 = False

    self.stats_timer                            = 180
    self.xtriage_log                            = []
    self.jobs_output                            = {}
    self.pids                                   = {}
    self.xtriage_results                        = False
    self.xtriage_summary                        = False
    self.pts                                    = False
    self.twin                                   = False
    self.molrep_log                             = False
    self.molrep_results                         = False
    self.molrep_summary                         = False
    self.NCS_results                            = False
    self.sample_type                            = False
    self.failed                                 = False
    self.input_sg                               = False
    self.solvent_content                        = 0.55

    #******BEAMLINE SPECIFIC*****
    #self.cluster_use = Utils.checkCluster()
    self.cluster_use = BLspec.checkCluster()
    #******BEAMLINE SPECIFIC*****
    if self.test:
      self.clean = False
    Process.__init__(self,name='AutoStats')
    self.start()

  def run(self):
    """
    Convoluted path of modules to run.
    """
    if self.verbose:
      self.logger.debug('AutoStats::run')

    self.preprocess()

    self.processPDBQuery()

    if self.pp:
      self.processPP()

    if self.test:
      self.postprocessXtriage()
      self.postprocessMolrep()
      self.postprocessNCS()
    else:
      self.processXtriage()
      self.processMolrep()
      self.processNCS()
      self.Queue()

    self.postprocess()

  def preprocess(self):
    """
    Things to do before the main process runs
    1. Change to the correct directory
    2. Print out the reference for Stat pipeline
    """
    if self.verbose:
      self.logger.debug('AutoStats::preprocess')
    #Make the self.working_dir if it does not exist.
    if os.path.exists(self.working_dir) == False:
      os.makedirs(self.working_dir)
    #change directory to the one specified in the incoming dict
    os.chdir(self.working_dir)
    #print out recognition of the program being used
    self.PrintInfo()
    #Check if input file is sca and convert to mtz.
    if self.datafile:
      self.input_sg,self.cell,self.cell2,vol = Utils.getMTZInfo(self,False,True,True)
      #Change timer to allow more time for Ribosome structures.
      if Utils.calcResNumber(self,self.input_sg,False,vol) > 5000:
        self.stats_timer = 300
    if self.test:
      self.logger.debug('TEST IS SET "ON"')

  def processPDBQuery(self):
    """
    Prepare and run PDBQuery.
    """
    if self.verbose:
      self.logger.debug('AutoStats::processPDBQuery')
    try:
      self.cell_output = Queue()
      Process(target=PDBQuery,args=(self.input,self.cell_output,self.logger)).start()

    except:
      self.logger.exception('**Error in AutoStats.processPDBQuery**')

  def processXtriage(self):
    """
    Run phenix.xtriage.
    """
    if self.verbose:
      self.logger.debug('AutoStats::processXtriage')
    try:
      command  = '/share/apps/necat/programs/phenix-dev-1702/build/intel-linux-2.6-x86_64/bin/phenix.xtriage '
      command += '%s scaling.input.xray_data.obs_labels="I(+),SIGI(+),I(-),SIGI(-)" '%self.datafile
      #command += 'scaling.input.parameters.reporting.loggraphs=True'
      #command = 'phenix.xtriage %s scaling.input.xray_data.obs_labels="I(+),SIGI(+),I(-),SIGI(-)"'%self.datafile
      #command = 'phenix.xtriage %s scaling.input.xray_data.obs_labels="I(+),SIGI(+),I(-),SIGI(-)" loggraphs=True'%self.datafile
      if self.test:
        self.jobs_output[11111] = 'xtriage'
      else:
        xtriage_output = Queue()
        job = Process(target=Utils.processLocal,args=((command,'xtriage.log'),self.logger,xtriage_output))
        job.start()
        self.jobs_output[job] = 'xtriage'
        self.pids['xtriage'] = xtriage_output.get()

    except:
      self.logger.exception('**ERROR in AutoStat.processXtriage**')

  def processNCS2(self):
    """
    Run Phaser tNCS and anisotropy correction
    """
    if self.verbose:
      self.logger.debug('AutoStats::processNCS')
    try:
      #It won't create plots???
      Utils.runPhaserModule(self)

    except:
      self.logger.exception('**ERROR in AutoStat.processNCS**')

  def processNCS(self):
    """
    Run Phaser tNCS and anisotropy correction
    """
    if self.verbose:
      self.logger.debug('AutoStats::processNCS')
    try:
      command  = 'phenix.phaser << eof\nMODE NCS\n'
      command += 'HKLIn %s\nLABIn F=F SIGF=SIGF\neof\n'%self.datafile
      if self.test:
        self.jobs_output[11110] = 'NCS'
      else:
        output = Queue()
        job = Process(target=Utils.processLocal,args=((command,'phaser2.log'),self.logger,output))
        job.start()
        self.jobs_output[job] = 'NCS'
        self.pids['NCS'] = output.get()

    except:
      self.logger.exception('**ERROR in AutoStat.processNCS**')

  def processMolrep(self):
    """
    Run Molrep for SRF.
    """
    if self.verbose:
      self.logger.debug('AutoStats::processMolrep')
    try:
      command  = 'molrep -f %s -i <<stop\n_DOC  Y\n_RESMAX 4\n_RESMIN 9\nstop\n'%self.datafile
      if self.test:
        self.jobs_output[121212] = 'molrep'
      else:
        molrep_output = Queue()
        job = Process(target=Utils.processLocal,args=((command,'molrep.log'),self.logger,molrep_output))
        job.start()
        self.jobs_output[job] = 'molrep'
        self.pids['molrep'] = molrep_output.get()

    except:
      self.logger.exception('**ERROR in AutoStats.processMolrep**')

  def processPP(self):
    """
    Run labelit.precession_photo.
    """
    if self.verbose:
      self.logger.debug('AutoStats::processPP')
    try:
      self.pp_output = Queue()
      Process(target=LabelitPP,args=(self.input,self.pp_output,self.logger)).start()

    except:
      self.logger.exception('**ERROR in AutoStats.processPP**')

  def postprocessXtriage(self):
    """
    Sort Xtriage data.
    """
    if self.verbose:
      self.logger.debug('AutoStats::postprocessXtriage')
    try:
      if os.path.exists('logfile.log'):
        self.xtriage_results = { 'Xtriage results' : Parse.ParseOutputXtriage(self,open('logfile.log','r').readlines()) }
        #self.xtriage_results = { 'Xtriage results' : Parse.ParseOutputXtriage_NEW(self,open('logfile.log','r').readlines()) }
      else:
        self.xtriage_results = { 'Xtriage results' : Parse.setXtriageFailed(self)}
        self.failed = True
        self.clean = False
      if os.path.exists('xtriage.log'):
        self.xtriage_log = open('xtriage.log','r').readlines()

    except:
      self.logger.exception('**ERROR in AutoStats.postprocessXtriage**')

  def postprocessMolrep(self):
    """
    Sort Molrep data.
    """
    if self.verbose:
      self.logger.debug('AutoStats::postprocessMolrep')
    try:
      if os.path.exists('molrep_rf.ps'):
        Utils.convertImage(self,'molrep_rf.ps','molrep_rf.jpg')
        #self.molrep_log = open('molrep.doc','r').readlines()
        #data = Parse.ParseOutputMolrep(self,self.molrep_log)
        data = Parse.ParseOutputMolrep(self,open('molrep.doc','r').readlines())
      else:
        data = Parse.setMolrepFailed(self)
        self.failed = True
        self.clean = False
      data.update({'Molrep log':os.path.join(os.getcwd(),'molrep.doc'),
                   'Molrep jpg':os.path.join(os.getcwd(),'molrep_rf.jpg')})
      self.molrep_results = { 'Molrep results' : data }

    except:
      self.logger.exception('**ERROR in AutoStats.postprocessMolrep**')

  def postprocessNCS(self):
    if self.verbose:
      self.logger.debug('AutoStats::postprocessNCS')
    try:
      if os.path.exists('phaser2.log'):
        data = Parse.ParseOutputPhaserNCS(self,open('phaser2.log','r').readlines())
        #print data
        if len(data['CID'].keys()) > 0:
          self.NCS_results = { 'PhaserNCS results' : data }
        else:
          self.NCS_results = False

    except:
      self.logger.exception('**ERROR in AutoStats.postprocessNCS**')

  def Queue(self):
    """
    queue system.
    """
    if self.verbose:
      self.logger.debug('AutoStats::Queue')
    try:
      timed_out = False
      timer = 0
      jobs = self.jobs_output.keys()
      if jobs != ['None']:
        counter = len(jobs)
        while counter != 0:
          for job in jobs:
            if job.is_alive() == False:
              if self.jobs_output[job] == 'xtriage':
                self.postprocessXtriage()
              if self.jobs_output[job] == 'molrep':
                self.postprocessMolrep()
              if self.jobs_output[job] == 'NCS':
                self.postprocessNCS()
              jobs.remove(job)
              del self.pids[self.jobs_output[job]]
              counter -= 1
          time.sleep(0.2)
          timer += 0.2
          """
          if self.verbose:
            if round(timer%1,1) in (0.0,1.0):
                print 'Waiting for AutoStat jobs to finish '+str(timer)+' seconds'
          """
          if self.stats_timer:
            if timer >= self.stats_timer:
              timed_out = True
              break
        if timed_out:
          if self.verbose:
            self.logger.debug('AutoStat timed out.')
            print 'AutoStat timed out.'
          for pid in self.pids.values():
            #jobs are not sent to cluster
            Utils.killChildren(self,pid)
          for job in jobs:
            if self.jobs_output[job] == 'xtriage':
              self.postprocessXtriage()
            if self.jobs_output[job] == 'molrep':
              self.postprocessMolrep()
            if self.jobs_output[job] == 'NCS':
              self.postprocessNCS()
        if self.verbose:
          self.logger.debug('AutoStats Queue finished.')

    except:
      self.logger.exception('**ERROR in Autostat.Queue**')

  def PrintInfo(self):
    """
    Print information regarding programs utilized by RAPD
    """
    if self.verbose:
      self.logger.debug('AutoStats::PrintInfo')
    try:
      print '\nRAPD now using Phenix'
      print '======================='
      print 'RAPD developed using Phenix'
      print 'Reference: Adams PD, et al.(2010) Acta Cryst. D66:213-221'
      print 'Website: http://www.phenix-online.org/ \n'
      print 'RAPD developed using Xtriage and Fest'
      print 'Reference: Zwart PH, et al. (2005)CCP4 Newsletter Winter:Contribution 7.'
      print 'Website: http://www.phenix-online.org/documentation/xtriage.htm\n'
      self.logger.debug('RAPD now using Phenix')
      self.logger.debug('=======================')
      self.logger.debug('RAPD developed using Phenix')
      self.logger.debug('Reference: Adams PD, et al.(2010) Acta Cryst. D66:213-221')
      self.logger.debug('Website: http://www.phenix-online.org/ \n')
      self.logger.debug('RAPD developed using Xtriage and Fest')
      self.logger.debug('Reference: Zwart PH, et al. (2005)CCP4 Newsletter Winter:Contribution 7.')
      self.logger.debug('Website: http://www.phenix-online.org/documentation/xtriage.htm\n')

    except:
      self.logger.exception('**Error in AutoStats.PrintInfo**')

  def postprocess(self):
    """
    Run summaries, make php/html files, send data back, and clean up.
    """
    if self.verbose:
      self.logger.debug('AutoStats::postprocess')

    output = {}
    status = {}
    results = {}
    failed = False
    cell_results = False
    cell_out = False
    pp_results = False
    pp_out = False

    #Make the output html files
    self.plotXtriage()
    if self.xtriage_results:
      Summary.summaryXtriage(self)
    self.htmlSummaryXtriage()
    if self.molrep_results:
      Summary.summaryMolrep(self)
    self.htmlSummaryMolrep()

    if self.gui:
      e = '.php'
    else:
      e = '.html'
    l = [('jon_summary_xtriage%s'%e,'Xtriage summary html'),
          ('plots_xtriage%s'%e,'Xtriage plots html'),
          ('jon_summary_molrep%s'%e,'Molrep summary html')]
    for i in range(len(l)):
      try:
        path = os.path.join(self.working_dir,l[i][0])
        if os.path.exists(path):
          output[l[i][1]] = path
        else:
          output[l[i][1]] = 'None'
      except:
        self.logger.exception('**Could not update paths of %s file.**'%l[i][0])
        output[l[i][1]] = 'FAILED'
        failed = True

    #Get rapd_agent_cell results back
    try:
      cell_results = self.cell_output.get()
      if cell_results.has_key('status'):
        if cell_results['status'] == 'FAILED':
          failed = True
        del cell_results['status']
      if cell_results.has_key('Output files'):
        cell_out = cell_results['Output files']
        del cell_results['Output files']
    except:
      self.logger.exception('**Error importing rapd_agent_cell results**')

    #Get rapd_agent_pp results back
    try:
      if self.pp:
        pp_results = self.pp_output.get()
        if pp_results.has_key('status'):
          if pp_results['status'] == 'FAILED':
            failed = True
          del pp_results['status']
        if pp_results.has_key('Output files'):
          pp_out = pp_results['Output files']
          del pp_results['Output files']
      else:
        #Put together the dict from LabelitPP and create an html summary.
        pp_results = {'LabelitPP results': {'HK0 jpg':None,'H0L jpg':None,'0KL jpg':None}}
        Utils.failedHTML(self,('jon_summary_pp','Cannot create precession photos from merged datasets.'))
        if os.path.exists(os.path.join(self.working_dir,'jon_summary_pp%s'%e)):
          pp_out = {'LabelitPP summary html':os.path.join(self.working_dir,'jon_summary_pp%s'%e)}
        else:
          pp_out = {'LabelitPP summary html':'None'}

    except:
      self.logger.exception('**Error importing rapd_agent_cell results**')
    #Get proper status.
    if failed:
      status['status'] = 'FAILED'
    else:
      status['status'] = 'SUCCESS'
    #Put all the result dicts from all the programs run into one resultant dict and pass it along the pipe.
    try:
      results.update(status)
      if self.xtriage_results:
        results.update(self.xtriage_results)
      if self.molrep_results:
        results.update(self.molrep_results)
      if cell_results:
        results.update(cell_results)
      if pp_results:
        results.update(pp_results)
      if output:
        if cell_out:
          output.update(cell_out)
        if pp_out:
          output.update(pp_out)
        results.update(output)
      self.input.insert(0,'STATS')
      self.input.append(results)
      if self.gui:
        self.sendBack2(self.input)

    except:
      self.logger.exception('**Could not send results to pipe.**')

    try:
      #Cleanup my mess.
      if self.clean:
        if failed == False:
          if self.verbose:
            self.logger.debug('Cleaning up files')
          os.system('rm -rf *.ps *.btc *.tab *.xml *.com molrep.doc molrep.log logfile.log xtriage.log phaser2.log PHASER.mtz')
    except:
      self.logger.exception('**Could not cleanup**')

    #Say job is complete.
    t = round(time.time()-self.st)
    self.logger.debug('-------------------------------------')
    self.logger.debug('RAPD AutoStat complete.')
    self.logger.debug('Total elapsed time: %s seconds'%t)
    self.logger.debug('-------------------------------------')
    print '\n-------------------------------------'
    print 'RAPD AutoStat complete.'
    print 'Total elapsed time: %s seconds'%t
    print '-------------------------------------'

  def plotXtriage(self):
    """
    generate plots html/php file
    """
    if self.verbose:
      self.logger.debug('AutoStats::plotXtriage')
    try:
      #cid0 = False
      #cid1 = False
      anom       = self.xtriage_results.get('Xtriage results').get('Xtriage anom plot')
      intensity  = self.xtriage_results.get('Xtriage results').get('Xtriage int plot')
      #xtriage_i          = self.xtriage_results.get('Xtriage results').get('Xtriage i plot')
      nz         = self.xtriage_results.get('Xtriage results').get('Xtriage nz plot')
      l_test     = self.xtriage_results.get('Xtriage results').get('Xtriage l-test plot')
      #xtriage_z          = self.xtriage_results.get('Xtriage results').get('Xtriage z plot')
      if self.NCS_results:
        cid0 = self.NCS_results.get('PhaserNCS results').get('CID').get('before',False)
        cid1 = self.NCS_results.get('PhaserNCS results').get('CID').get('after',False)
      #List of params for parsing later.
      l = [['Intensity','Mean I vs. Resolution','Resolution(A)','M e a n &nbsp I',intensity,
            ("&lt I &gt smooth","&lt I &gt binning","&lt I &gt expected")],
           #['Z scores','Data Sanity and Completeness check','Resolution(A)','Z &nbsp S c o r e','z',
            #('Z_score','Completeness')],
           ['Anom_Signal','Anomalous Measurability','Resolution(A)','',anom,
            ('Obs_anom_meas','Smoothed')],
           #['I/sigI','Signal to Noise vs. Resolution','Resolution(A)','I / S i g I','i',
            #('Signal_to_Noise',)],
           ['NZ_Test','NZ Test','z','',nz,('Acen_obs','Acen_untwinned','Cen_obs','Cen_untwinned')],
           ['L_Test','L-Test','|I|','',l_test,('Obs','Acen_th_untwinned','Acen_th_perfect_twin')],
           ['CID0','CID before Anisotropic and tNCS correction','Z','',cid0,
            ('Acen_theo','Acen_twin','Acen_obs','Cen_theo','Cen_obs')],
           ['CID1','CID after Anisotropic and tNCS correction','Z','',cid1,
            ('Acen_theo','Acen_twin','Acen_obs','Cen_theo','Cen_obs')]
          ]
      e = len(l) - 2
      if self.NCS_results:
        #If job is killed early, it will only have the before CID.
        if cid0:
          e += 1
        if cid1:
          e += 1
      """
      if self.NCS_results:
        e = len(l)
      else:
        e = len(l) - 2
      """
      if nz != 'None':
        xtriage_plot = ''
        xtriage_plot += Utils.getHTMLHeader(self,'plots')
        xtriage_plot +="%4s$(function() {\n%6s$('.tabs').tabs();\n%4s});\n"%(3*('',))
        xtriage_plot +="%4s</script>\n%2s</head>\n%2s<body>\n%4s<table>\n%6s<tr>\n"%(5*('',))
        xtriage_plot +='%8s<td width="100%%">\n%10s<div class="tabs">\n%12s<ul>\n'%(3*('',))
        for i in range(e):
          xtriage_plot += '%14s<li><a href="#tabs-44%s">%s</a></li>\n'%('',i,l[i][0])
        xtriage_plot += "%12s</ul>\n"%''
        for i in range(e):
          xtriage_plot += '%12s<div id="tabs-44%s">\n%14s<div class=title><b>%s</b></div>\n'%('',i,'',l[i][1])
          xtriage_plot += '%14s<div id="chart%s_div3" style="width:750px;height:550px;margin-left:20;"></div>\n'%('',i)
          xtriage_plot += '%14s<div class=x-label>%s</div>\n%14s<span class=y-label>%s</span>\n%12s</div>\n'%('',l[i][2],'',l[i][3],'')
        xtriage_plot +="%10s</div>\n%8s</td>\n%6s</tr>\n%4s</table>\n"%(4*('',))
        xtriage_plot += '%4s<script id="source" language="javascript" type="text/javascript">\n'%''
        xtriage_plot += "%6s$(function () {\n"%''
        s = '\n%8svar '%''
        for i in range(e):
          l1 = []
          l2 = []
          label = ['%10s[\n'%'']
          s1 = s
          for x in range(len(l[i][4][0])-1):
            var = '%s%s'%(l[i][0].upper(),x)
            s1 += '%s=[],'%var
            label.append('%12s{ data: %s, label:"%s" },\n'%('',var,l[i][5][x]))
            for y in range(len(l[i][4])):
              if l[i][0] == 'Anom_Signal':
                l2.append(float(l[i][4][y][0]))
              if l[i][0] in ('Intensity','Anom_Signal'):
                l1.append("%8s%s.push([-%s,%s]);\n"%('',var,l[i][4][y][0],l[i][4][y][x+1]))
              else:
                l1.append("%8s%s.push([%s,%s]);\n"%('',var,l[i][4][y][0],l[i][4][y][x+1]))
          if l[i][0] == 'Anom_Signal':
            xtriage_plot += '%s,mark=[];\n'%s1[:-1]
            label.append('%12s{ data: mark, label:"min level for anom signal" },\n'%'')
          else:
            xtriage_plot += '%s;\n'%s1[:-1]
          label.append('%10s],\n'%'')
          l[i].append(label)
          for line in l1:
            xtriage_plot += line
          if l[i][0] == 'Anom_Signal':
            xtriage_plot += "%8sfor (var i = -%s; i < -%s; i +=0.25)\n%8smark.push([i,0.05]);\n"%('',max(l2),min(l2),'')
        for i in range(e):
          xtriage_plot += '%8svar plot%s = $.plot($("#chart%s_div3"),\n'%('',i,i)
          for line in l[i][-1]:
            xtriage_plot += line
          xtriage_plot += "%10s{ lines: { show: true},\n%12spoints: { show: true },\n"%('','')
          xtriage_plot += "%12sselection: { mode: 'xy' },\n%12sgrid: { hoverable: false, clickable: false },\n"%('','')
          if l[i][0] in ('Intensity','Anom_Signal'):
            xtriage_plot += "%12sxaxis: { transform: function (v) { return Math.log(-v); },\n"%''
            xtriage_plot += "%21sinverseTransform: function (v) { return Math.exp(-v); },\n"%''
            xtriage_plot += "%21stickFormatter: ( function negformat(val,axis){return -val.toFixed(axis.tickDecimals);} ) },\n"%''
          else:
            xtriage_plot += "%12sxaxis: {min:0},\n"%''
          xtriage_plot += "%12syaxis: {min:0},\n%10s});\n\n"%('','')
        """
        xtriage_plot += "%8sfunction showTooltip(x, y, contents) {\n"%''
        xtriage_plot += "%10s$('<div id=\"tooltip\">' + contents + '</div>').css( {\n"%''
        xtriage_plot += "%12sposition: 'absolute',\n%12sdisplay: 'none',\n"%('','')
        xtriage_plot += "%12stop: y + 5,\n%12sleft: x + 5,\n%12sborder: '1px solid #fdd',\n"%(3*('',))
        xtriage_plot += "%12spadding: '2px',\n%12s'background-color': '#fee',\n"%('','')
        xtriage_plot += '%12sopacity: 0.80\n%10s}).appendTo("body").fadeIn(200);\n'%('','')
        xtriage_plot += "%8s}\n%6s});\n%4s</script>\n%2s</body>\n</html>\n"%(4*('',))
        """
        xtriage_plot += "%6s});\n%4s</script>\n%2s</body>\n</html>\n"%(3*('',))
        if xtriage_plot:
          if self.gui:
            sp = 'plots_xtriage.php'
          else:
            sp = 'plots_xtriage.html'
          xtriage_plot_file = open(sp,'w')
          xtriage_plot_file.writelines(xtriage_plot)
          xtriage_plot_file.close()
      else:
        Utils.failedHTML(self,'plots_xtriage')

    except:
      self.logger.exception('**ERROR in AutoStats.plotXtriage**')
      Utils.failedHTML(self,'plots_xtriage')

  def htmlSummaryXtriage(self):
    """
    Create HTML/php files for xtriage output results.
    """
    if self.verbose:
      self.logger.debug('AutoStats::htmlSummaryXtriage')
    try:
      if self.xtriage_summary:
        if self.gui:
          sl = 'jon_summary_xtriage.php'
        else:
          sl = 'jon_summary_xtriage.html'
        jon_summary = open(sl,'w')
        jon_summary.write(Utils.getHTMLHeader(self,'xtriage'))
        jon_summary.write('%6s$(document).ready(function() {\n'%'')
        jon_summary.write("%8s$('#accordion-xtriage').accordion({\n%11scollapsible: true,\n%11sactive: false });\n"%(3*('',)))
        jon_summary.write("%8s$('#xtriage-auto2').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bSort": false,\n%11s"bAutoWidth": false });\n'%(5*('',)))
        jon_summary.write("%8s$('#xtriage_pat').dataTable({\n"%'')
        jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bSort": false,\n%11s"bAutoWidth": false });\n'%(5*('',)))
        if self.pts:
          jon_summary.write("%8s$('#xtriage_pts').dataTable({\n"%'')
          jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bSort": false,\n%11s"bAutoWidth": false });\n'%(5*('',)))
        if self.twin:
          jon_summary.write("%8s$('#xtriage_twin').dataTable({\n"%'')
          jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bSort": false,\n%11s"bAutoWidth": false });\n'%(5*('',)))
        jon_summary.write('%6s});\n%4s</script>\n%2s</head>\n%2s<body id="dt_example">\n'%(4*('',)))
        jon_summary.writelines(self.xtriage_summary)
        jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
        jon_summary.write("%7s<h1 class='Results'>Xtriage Output</h1>\n%6s</div>\n%5s</div>\n"%(3*('',)))
        jon_summary.write('%5s<div id="accordion-xtriage">\n'%'')
        jon_summary.write('%6s<h3><a href="#">Click to view Xtriage log</a></h3>\n%6s<div>\n%7s<pre>\n'%(3*('',)))
        if self.xtriage_log:
          for line in self.xtriage_log:
            jon_summary.write(line)
        else:
          jon_summary.write('---------------Xtriage FAILED---------------\n')
        jon_summary.write('%7s</pre>\n%6s</div>\n%5s</div>\n%4s</div>\n%2s</body>\n</html>\n'%(5*('',)))
        jon_summary.close()
      else:
        Utils.failedHTML(self,('jon_summary_xtriage','Input data could not be analysed, probably because resolution was too low.'))

    except:
      self.logger.exception('**ERROR in AutoStats.htmlSummaryXtriage**')

  def htmlSummaryMolrep(self):
    """
    Create HTML/php files for Molrep output results.
    """
    if self.verbose:
      self.logger.debug('AutoStats::htmlSummaryMolrep')
    try:
      if self.molrep_summary:
        molrep_log = self.molrep_results.get('Molrep results').get('Molrep log')
        if self.gui:
          sl = 'jon_summary_molrep.php'
        else:
          sl = 'jon_summary_molrep.html'
        jon_summary = open(sl,'w')
        jon_summary.write(Utils.getHTMLHeader(self))
        jon_summary.write('%6s$(document).ready(function() {\n'%'')
        jon_summary.write("%8s$('#accordion-molrep').accordion({\n"%'')
        jon_summary.write('%11scollapsible: true,\n%11sactive: false });\n'%('',''))
        if self.molrep_summary:
          jon_summary.write("%8s$('#molrep').dataTable({\n"%'')
          jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bSort": false,\n%11s"bAutoWidth": false});\n'%(5*('',)))
        jon_summary.write('%6s});\n%4s</script>\n%2s</head>\n%2s<body id="dt_example">\n'%(4*('',)))
        if self.molrep_summary:
          jon_summary.writelines(self.molrep_summary)
        else:
          jon_summary.write("%7s<h2 class='Results'>Error in molrep analysis</h1>\n"%'')
        jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
        jon_summary.write("%7s<h1 class='Results'>Molrep Output</h1>\n%6s</div>\n%5s</div>\n"%(3*('',)))
        jon_summary.write('%5s<div id="accordion-molrep">\n'%'')
        jon_summary.write('%6s<h3><a href="#">Click to view Molrep log</a></h3>\n%6s<div>\n%7s<pre>\n\n'%(3*('',)))
        if molrep_log:
          for line in open(molrep_log,'r').readlines():
            jon_summary.write(line)
        else:
          jon_summary.write('---------------Molrep FAILED---------------\n')
        jon_summary.write('%7s</pre>\n%6s</div>\n%5s</div>\n%4s</div>\n%2s</body>\n</html>\n'%(5*('',)))
        jon_summary.close()
      else:
        Utils.failedHTML(self,'jon_summary_molrep')

    except:
      self.logger.exception('**ERROR in AutoStats.htmlSummaryMolrep**')

if __name__ == '__main__':
  import logging,logging.handlers
  inp = [{ 'run':{'fullname':'/gpfs6/users/mizzou/tanner_E_443/images/Tanner/runs/AfUDPGlcD6/AfUDPGlcD6_1_001.img',
                   'total':90,
                   'osc_range':'1.0',
                   'x_beam':153.75,
                   'y_beam':158.93,
                   'binning':'2x2',
                   'two_theta':0.0,
                   'distance':'309.3',
                   },
            'dir' :  '/gpfs6/users/necat/Jon/RAPD_test/Output',
            #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/SAD/PK_lu_peak.sca',
            'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz',
            'cluster': True,
            'test': False,
            'verbose': True,
            'gui'  : False,
            'clean': False,
            'control': ('164.54.212.165',50001),
            'process_id': 11111,
            }]

  #start logging
  LOG_FILENAME = os.path.join(inp[0].get('dir'),'rapd.log')
  #LOG_FILENAME = '/gpfs6/users/necat/Jon/RAPD_test/Output/rapd_jon.log'
  # Set up a specific logger with our desired output level
  logger = logging.getLogger('RAPDLogger')
  logger.setLevel(logging.DEBUG)
  # Add the log message handler to the logger
  handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=100000, backupCount=5)
  #add a formatter
  formatter = logging.Formatter("%(asctime)s - %(message)s")
  handler.setFormatter(formatter)
  logger.addHandler(handler)
  AutoStats(inp,logger=logger)

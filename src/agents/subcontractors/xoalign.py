"""
This file is part of RAPD

Copyright (C) 2015-2016, Cornell University
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

__created__ = "2015-07-27"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Production"

# Standard imports
from multiprocessing import Process
import os
import time

# RAPD imports
import parse as Parse
import summary as Summary
from utils.communicate import rapd_send
import utils.xutils as Utils

class RunXOalign(Process):
  def __init__(self, input, params, logger=None):
        logger.info('RunXOalign.__init__')
        self.st = time.time()
        self.input                              = input
        self.logger                             = logger
        #Setting up data input
        self.header                             = self.input[2]
        self.header2                            = False
        if self.input[3].has_key('distance'):
            self.header2                            = self.input[3]
        self.controller_address                 = self.input[-1]

        self.auto1_summary                      = False
        self.xoalign_log                        = False
        self.xoalign_summary                    = False
        self.xoalign_failed                     = False
        self.xoalign_results                    = False

        #setup variables sent in as params.
        self.working_dir                        = params.get('dir',self.input[1].get('work'))
        self.test                               = params.get('test',False)
        self.gui                                = params.get('gui',True)
        self.stac_timer                         = params.get('timer',20)
        self.clean                              = params.get('clean',True)
        self.verbose                            = params.get('verbose',True)
        self.align                              = str(self.header.get('axis_align','long'))

        Process.__init__(self)
        self.start()

  def run(self):
        if self.verbose:
            self.logger.debug("RunXOalign::run")

        self.preprocess()
        self.process()
        self.postprocess()

  def preprocess(self):
        if self.verbose:
            self.logger.debug('RunXOalign::preprocess')
        #change directory to the one specified in the incoming dict
        if os.path.exists(self.working_dir) == False:
            os.makedirs(self.working_dir)
        os.chdir(self.working_dir)
        #print out recognition of the program being used
        #self.PrintInfo()

  def process(self):
    if self.verbose:
        self.logger.debug('RunXOalign::process')
    try:
      if self.header2:
          j1 = '2'
      else:
          j1 = ''
      omega = str(eval('self.header'+j1).get('phi'))
      kappa = str(eval('self.header'+j1).get('mk3_kappa'))
      phi   = str(eval('self.header'+j1).get('mk3_phi'))
      file1 = str(eval('self.header'+j1).get('STAC file1'))
      file2 = str(eval('self.header'+j1).get('STAC file2'))
    except:
        self.logger.exception('Problems getting info from input dict!!')

    #Need local ln for bestfile.par to get cell and SG info for summary html.
    try:
      if os.path.exists(os.path.basename(file2)) == False:
        os.symlink(file2,os.path.basename(file2))
    except:
      self.logger.exception('Cannot ln XOalign file into working directory.')
      self.xoalign_failed = True

    #Set SG info since it is not in Mosflm file.
    sg = False
    for line in open(os.path.basename(file2),'r').readlines():
      if line.startswith('SYMMETRY'):
        sg = line.split()[1]
      if line.startswith('CELL'):
        cell = line.split()[1:4]
    #Beamline geometry for omega, kappa, and phi
    o = '0.00071,-0.00334,0.99999'
    k = '-0.29095,-0.29243,0.91095'
    p = '0.00664,-0.00752,0.99995'
    #datum from image
    d = '%s,%s,%s'%(omega,kappa,phi)
    #self.align options are long, smart, anom, multi, all, a, b, c, ab, ac, bc
    #Ones that need more work: multi, smart, anom
    if self.align == 'all':
      a = []
    if self.align == 'a':
      a = ['a*','b*']
    if self.align == 'b':
      a = ['b*','a*']
    if self.align == 'c':
      a = ['c*','a*']
    if self.align == 'ab':
      a = ['[1 1 0]','[0 1 0]']
    if self.align == 'ac':
      a = ['[1 0 1]','[0 0 1]']
    if self.align == 'bc':
      a = ['[0 1 1]','[0 0 1]']
    if self.align == 'long':
      cell2 = [float(line) for line in cell]
      m = max(cell2)
      for x in range(len(cell2)):
        if cell2[x] == m:
          if x == 0:
            a = ['a*','b*']
          if x == 1:
            a = ['b*','a*']
          if x == 2:
            a = ['c*','a*']

    command = 'XOalign.py -O %s -K %s -P %s -D %s'%(o,k,p,d)
    if sg:
      command += ' -s %s'%sg
    if len(a) == 2:
      command += ' -V "%s" -W "%s"'%(a[0],a[1])
    command += ' %s'%file1
    #Run command locally and log output
    Utils.processLocal((command,'XOalign.log'),self.logger)

  def postprocess(self):
    if self.verbose:
      self.logger.debug('RunXOalign::postprocess')
    #Save logfile for HTML output.
    self.xoalign_log = open('XOalign.log','r').readlines()
    self.xoalign_results = Parse.ParseOutputXOalign(self,self.xoalign_log)
    if self.xoalign_failed == False:
      Summary.summaryAutoCell(self)
      Summary.summaryXOalign(self)
    self.htmlSummaryXOalign()
    #Account for missing file paths from autoindex pipeline.
    output = {'STAC file1':'None','STAC file2':'None','image_path_raw_1':'None','image_path_pred_1':'None','image_path_raw_2':'None',
              'image_path_pred_2':'None','Best plots html':'None','Long summary html':'None','Short summary html':'None',}
    f = 'jon_summary_xoalign.html'
    if self.gui:
      f = f.replace('html','php')
    if os.path.exists(os.path.join(self.working_dir,f)):
      output['XOalign summary html'] = os.path.join(self.working_dir,f)
    else:
      output['XOalign summary html'] = 'None'

    #Put all the result dicts from all the programs run into one resultant dict and pass it along the pipe.
    try:
      results = {}
      results.update({'Output files' : output})
      self.input.append(results)
      if self.gui:
        # self.sendBack2(self.input)
        rapd_send(self.controller_address, self.input)
    except:
      self.logger.exception('**xoalign.postprocess Could not send results to pipe.**')

    try:
      #Cleanup my mess.
      if self.clean:
        os.chdir(self.working_dir)
        rm = 'rm -rf bestfile.par XOalign.log'
        if self.verbose:
          self.logger.debug(rm)
        os.system(rm)
    except:
      self.logger.exception('**xoalign.postprocess Could not cleanup**')

    #Say job is complete.
    t = round(time.time()-self.st)
    self.logger.debug('-------------------------------------')
    self.logger.debug('RAPD XOalign complete.')
    self.logger.debug('Total elapsed time: %s seconds'%t)
    self.logger.debug('-------------------------------------')
    print '\n-------------------------------------'
    print 'RAPD XOalign complete.'
    print 'Total elapsed time: %s seconds'%t
    print '-------------------------------------'

  def htmlSummaryXOalign(self):
    """
    Create the html/php results file for XOalign.
    """
    if self.verbose:
      self.logger.debug('RunStac::htmlSummaryXOalign')
    try:
      if self.xoalign_failed == False:
        if self.gui:
          jon_summary = open('jon_summary_xoalign.php','w')
        else:
          jon_summary = open('jon_summary_xoalign.html','w')
        jon_summary.write(Utils.getHTMLHeader(self,'strat'))
        jon_summary.write("%6s$(document).ready(function() {\n%8s$('#accordion2').accordion({\n"%('',''))
        jon_summary.write('%11scollapsible: true,\n%11sactive: false         });\n'%('',''))
        if self.auto1_summary:
          jon_summary.write("%8s$('#xoalign-auto').dataTable({\n"%'')
          jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false    });\n'%(4*('',)))
        if self.xoalign_summary:
          jon_summary.write("%8sXOalignTable = $('#xoalign').dataTable({\n"%'')
          jon_summary.write('%11s"bPaginate": false,\n%11s"bFilter": false,\n%11s"bInfo": false,\n%11s"bAutoWidth": false    });\n'%(4*('',)))
        jon_summary.write('%8s//Tooltips\n'%'')
        jon_summary.write("%8s$('#xoalign thead th').each(function(){\n"%'')
        jon_summary.write("%11sif ($(this).text() == 'V1') {\n"%'')
        jon_summary.write("%16sthis.setAttribute('title','The crystal vector to be aligned parallel to the spindle axis');\n%11s}\n"%('',''))
        jon_summary.write("%11selse if ($(this).text() == 'V2') {\n"%'')
        jon_summary.write("%16sthis.setAttribute('title','The crystal vector describing the plane including the spindle and beam axes');\n%11s}\n%8s});\n"%(3*('',)))
        jon_summary.write("%8s// Handler for click events on the XOalign table\n"%'')
        jon_summary.write('%8s$("#xoalign tbody tr").click(function(event) {\n'%'')
        jon_summary.write("%11s//take highlight from other rows\n"%'')
        jon_summary.write("%11s$(XOalignTable.fnSettings().aoData).each(function (){\n"%'')
        jon_summary.write("%14s$(this.nTr).removeClass('row_selected');\n%11s});\n"%('',''))
        jon_summary.write("%11s//highlight the clicked row\n"%'')
        jon_summary.write("%11s$(event.target.parentNode).addClass('row_selected');\n%8s});\n"%('',''))
        jon_summary.write('%8s$("#xoalign tbody tr").dblclick(function(event) {\n'%'')
        jon_summary.write("%11s//Get the current data of the clicked-upon row\n"%'')
        jon_summary.write("%11saData = XOalignTable.fnGetData(this);\n"%'')
        jon_summary.write("%11s//Use the values from the line to fill the form\n"%'')
        jon_summary.write('%11svar omega = aData[3];\n%11svar kappa = aData[4];\n%11svar phi = aData[5];\n'%(3*('',)))
        jon_summary.write('%11s$.ajax({\n%16stype: "POST",\n%16surl: "d_add_minikappa.php",\n'%(3*('',)))
        jon_summary.write('%16sdata: { omega:omega,\n%23skappa:kappa,\n%23sphi:phi,\n'%(3*('',)))
        jon_summary.write('%23sip_address:my_ip,\n%23sbeamline:my_beamline }\n%11s});\n'%(3*('',)))
        jon_summary.write("%11s//Popup the success dialog\n"%'')
        jon_summary.write('%11sPopupSuccessDialog("Minikappa settings sent to beamline");\n%8s});\n'%('',''))
        jon_summary.write('%6s});\n%4s</script>\n\n%2s</head>\n'%(3*('',)))
        jon_summary.write('%2s<body id="dt_example">\n'%'')
        jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
        jon_summary.write('%7s<h1 class="results">Cell and SG summary for:</h1>\n'%'')
        jon_summary.write("%7s<h2 class='results'>Image: %s</h2>\n"%('',self.header.get('fullname')))
        if self.header2:
          jon_summary.write("%7s<h2 class='results'>Image: %s</h2>\n"%('',self.header2.get('fullname')))
        if self.auto1_summary:
          jon_summary.writelines(self.auto1_summary)
          jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
        if self.xoalign_summary:
          jon_summary.writelines(self.xoalign_summary)
        jon_summary.write('%4s<div id="container">\n%5s<div class="full_width big">\n%6s<div id="demo">\n'%(3*('',)))
        jon_summary.write("%7s<h1 class='Results'>XOalign Logfile</h1>\n"%'')
        jon_summary.write('%6s</div>\n%5s</div>\n%5s<div id="accordion2">\n'%(3*('',)))
        jon_summary.write('%6s<h3><a href="#">Click to view log</a></h3>\n%6s<div>\n%7s<pre>\n'%(3*('',)))
        jon_summary.write('\n---------------XOALIGN RESULTS---------------\n\n')
        if self.xoalign_log:
          for line in self.xoalign_log:
            jon_summary.write(line)
        else:
          jon_summary.write('---------------XOALIGN FAILED---------------\n')
        jon_summary.write('%7s</pre>\n%6s</div>\n%5s</div>\n%4s</div>\n%2s</body>\n</html>\n'%(5*('',)))
        jon_summary.close()
      else:
        Utils.failedHTML(self('jon_summary_stac','You MUST select a successful solution and NOT another XOalign alignment'))

    except:
      self.logger.exception('**Error in stac.htmlSummaryXOalign**')

if __name__ == '__main__':
  import logging,logging.handlers
  import jon_auto_input2 as Input
  inp = Input.input()
  #start logging
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
  #logger.info('RunStac.__init__')
  params = {'timer': 20,
            'test': False,
            'gui':False,
            'dir': '/gpfs6/users/necat/Jon/RAPD_test/Output'}
  RunXOalign(inp, params, logger=logger)

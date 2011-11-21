'''
__author__ = "Jon Schuermann, Frank Murphy"
__copyright__ = "Copyright 2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2011/02/02"
'''
import multiprocessing
import os
import sys
import subprocess
import time
import shutil
import logging,logging.handlers

from rapd_agent_cell import PDBQuery
from rapd_communicate import Communicate
import rapd_agent_utilities as Utils
import rapd_agent_parse as Parse
import rapd_agent_summary as Summary

class AutoStats(multiprocessing.Process,Communicate):
    def __init__(self,input,output0=None,logger=None):
        logger.info('AutoStats.__init__')
        self.st = time.time()
        self.input                              = input
        self.output0                            = output0
        self.logger                             = logger 
        if self.input[0].has_key('dir'):
            self.working_dir                        = self.input[0].get('dir')
        else:
            self.working_dir                        = os.getcwd()
        if self.input[0].has_key('data'):
            self.datafile                           = self.input[0].get('data')
        else:
            self.datafile                           = False
        if self.input[0].has_key('gui'):    
            self.gui                                = self.input[0].get('gui')
        else:
            self.gui                                = True
        if self.input[0].has_key('timer'):  
            self.stats_timer                        = self.input[0].get('timer')
        else:
            self.stats_timer                        = 180
        if self.input[0].has_key('cluster'):    
            self.cluster_use                        = self.input[0].get('cluster')
        else:
            self.cluster_use                        = True
        if self.input[0].has_key('test'):
            self.test                               = self.input[0].get('test')
        else:
            self.test                               = False
        if self.input[0].has_key('control'):    
            self.controller_address                 = self.input[0].get('control')
        else:
            self.controller_address                 = False
        if self.input[0].has_key('passback'):
            self.passback                           = self.input[0].get('passback')
        else:
            self.passback                           = False
        self.xtriage_log                            = []
        self.xtriage_log2                           = []
        self.jobs_output                            = {}
        self.xtriage_results                        = False
        self.xtriage_summary                        = False
        self.pts                                    = False
        self.twin                                   = False
        self.molrep_log                             = []
        self.molrep_results                         = False
        self.molrep_summary                         = False
        self.clean                                  = True
        self.failed                                 = False
        self.input_sg                               = False
        #self.cell_jobs                              = False
        self.cell_output                            = False
        self.sample_type                            = False
        
        #******BEAMLINE SPECIFIC*****
        type1 = os.uname()[4]        
        if type1 == 'x86_64':
            self.cluster_use                = True
        else:
            self.cluster_use                = False
        #******BEAMLINE SPECIFIC*****
        
        multiprocessing.Process.__init__(self,name='AutoStats')
        self.start()
        
    def run(self):
        """
        Convoluted path of modules to run.
        """
        self.logger.debug('AutoStats::run')
        self.preprocess()
        if self.failed == False:
            if self.test:
                self.processPDBQuery()
                self.postprocessXtriage()
                self.postprocessMolrep()
            else:
                self.processPDBQuery()
                self.processXtriage()        
                self.processMolrep()
                self.Queue()
        
        self.postprocess()
        
    def preprocess(self):
        """
        Things to do before the main process runs
        1. Change to the correct directory
        2. Print out the reference for Stat pipeline
        """       
        self.logger.debug('AutoStats::preprocess')
        #change directory to the one specified in the incoming dict    
        os.chdir(self.working_dir)
        #print out recognition of the program being used
        self.PrintInfo()
        #Check if input file is sca and convert to mtz.
        if self.datafile:
            file_type = self.datafile[-3:]
            if file_type == 'sca':
                #Convert sca to mtz
                Utils.fixSCA(self)
                Utils.sca2mtz(self)
            if self.failed == False:
                Utils.getInfoCellSG(self,self.datafile)
                #Change timer to allow more time for Ribosome structures.
                Utils.checkVolume(self,Utils.calcVolume(self))
                if self.sample_type:
                    self.stats_timer = 300
        if self.test:
            self.logger.debug('TEST IS SET "ON"')
                
    def processPDBQuery(self):
        """
        Prepare and run PDBQuery.
        """
        self.logger.debug('AutoStats::processPDBQuery')
        try:
            junk = multiprocessing.Queue()
            self.cell_output = multiprocessing.Queue()
            args1 = {}
            args1['input']  = self.input
            args1['output0'] = junk
            args1['output1'] = self.cell_output
            args1['logger'] = self.logger
            job = multiprocessing.Process(target=PDBQuery,kwargs=args1).start()
            self.pdb_percent = junk.get()
        
        except:
            self.logger.exception('**Error in AutoStats.processPDBQuery**')
        
    def processXtriage(self):
        """
        Run phenix.xtriage.
        """
        self.logger.debug('AutoStats::processXtriage')
        try:        
            command = 'phenix.xtriage '+self.datafile+' scaling.input.xray_data.obs_labels="I(+),SIGI(+),I(-),SIGI(-)"'                                   
            xtriage_output = multiprocessing.Queue()
            job = multiprocessing.Process(target=multiXtriage(input=command,output=xtriage_output,logger=self.logger)).start()
            self.jobs_output[(xtriage_output).get()] = 'xtriage'
        
        except:
            self.logger.exception('**ERROR in AutoStat.processXtriage**')
    
    def processMolrep(self):
        """
        Run Molrep for SRF.
        """
        self.logger.debug('AutoStats::processMolrep')
        try:            
            command  = 'molrep -f '+self.datafile+' -i <<stop\n'
            command += '_DOC  Y\n'
            #command += '_RFSIG 2\n'#didnt speed up (time=104)
            #command += '_NP 15\n'#didnt speed up (time=105)
            command += '_RESMAX 4\n'#(time=40)
            command += '_RESMIN 9\n'#(time=37)            
            command += 'stop\n'
            molrep_output = multiprocessing.Queue()
            job = multiprocessing.Process(target=multiMolrep(input=command,output=molrep_output,logger=self.logger)).start()
            self.jobs_output[(molrep_output).get()] = 'molrep'        
        
        except:
            self.logger.exception('**ERROR in AutoStats.processMolrep**')
    
    def processFFT(self):
        """
        Run FFT to make a Patterson map.
        """
        self.logger.debug('AutoStats::processFFT')
        try:
            command  = 'fft hklin '+self.datafile+' mapout junk.tmp<<eof1\n'
            command += 'labin I=IMEAN SIGI=SIGIMEAN\n'
            command += 'exclude sig1 4.0\n'
            command += 'xyzlim 0.0 1.0 0.0 1.0 0.0 1.0\n'
            command += 'end\n'
            command += 'eof1\n'
            command += 'mapmask mapin junk.tmp mapout pat.map<<eof2\n'
            command += 'truncate yes\n'
            command += 'end\n'
            command += 'eof2\n'
            file = open('scale2mtz.com','w')
            file.writelines(command)
            file.close()
            command2 = 'tcsh scale2mtz.com'
            temp = []
            myoutput = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        
        except:
            self.logger.exception('**ERROR in AutoStats.processFFT**')
            
    def postprocessXtriage(self):
        """
        Sort Xtriage data.
        """
        self.logger.debug('AutoStats::postprocessXtriage')
        try:
            logfile = open('logfile.log','r')
            for line in logfile:
                self.xtriage_log.append(line)
            logfile.close()
            data = Parse.ParseOutputXtriage(self,self.xtriage_log)
            if data == None:
                Parse.setXtriageFailed(self)
                self.clean = False
            else:
                self.xtriage_results = { 'Xtriage results' : data }
                log = open('xtriage.log','r')
                for line in log:
                    self.xtriage_log2.append(line)
                log.close()
                           
        except:
            self.logger.exception('**ERROR in AutoStats.postprocessXtriage**')
            Parse.setXtriageFailed(self)
            
    def postprocessMolrep(self):
        """
        Sort Molrep data.
        """
        self.logger.debug('AutoStats::postprocessMolrep')
        try:
            if os.path.exists('molrep_rf.ps'):
                Utils.convertImage(self,'molrep_rf.ps','molrep_rf.jpg')            
                logfile = open('molrep.doc','r')
                for line in logfile:
                    self.molrep_log.append(line)
                logfile.close()
                data = Parse.ParseOutputMolrep(self,self.molrep_log)
            else:
                data = None
            if data == None:
                Parse.setMolrepFailed(self)
                self.clean = False
            else:
                self.molrep_results = { 'Molrep results' : data }
        
        except:
            self.logger.exception('**ERROR in AutoStats.postprocessMolrep**')   
            Parse.setMolrepFailed(self)
            
    def Queue(self):
        """
        queue system.
        """
        self.logger.debug('AutoStats::Queue')
        try:
            timed_out = False
            timer = 0
            pids = self.jobs_output.keys()
            if pids != ['None']:
                counter = len(pids)                
                while counter != 0:
                    for pid in pids:
                        if Utils.stillRunningCluster(self,pid):    
                            pass
                        elif Utils.stillRunning(self,pid):   
                            pass
                        else:
                            if self.jobs_output[pid] == 'xtriage':
                                self.postprocessXtriage()
                            if self.jobs_output[pid] == 'molrep':
                                self.postprocessMolrep()
                            pids.remove(pid)
                            counter -= 1
                    time.sleep(1)
                    timer += 1
                    print 'Waiting for AutoStat jobs to finish '+str(timer)+' seconds'
                    if self.stats_timer:
                        if timer >= self.stats_timer:
                            timed_out = True
                            break          
                if timed_out:    
                    self.logger.debug('AutoStat timed out.')
                    print 'AutoStat timed out.'                    
                    for pid in pids:
                        if self.cluster_use:
                            Utils.killChildrenCluster(self,pid)
                        else:
                            Utils.killChildren(self,pid)                        
                        if self.jobs_output[pid] == 'xtriage':
                            self.postprocessXtriage()
                        if self.jobs_output[pid] == 'molrep':
                            self.postprocessMolrep()
                        
                        """
                        #Set output dict to pass back.
                        if self.jobs_output[pid] == 'xtriage':
                            Parse.setXtriageFailed(self)
                        if self.jobs_output[pid] == 'molrep':    
                            Parse.setMolrepFailed(self)
                        """                        
                self.logger.debug('AutoStats Queue finished.')
        
        except:
            self.logger.exception('**ERROR in Autostat.Queue**')
        
    def PrintInfo(self):
        """
        Print information regarding programs utilized by RAPD
        """
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
        self.logger.debug('AutoStats::postprocess')
     
        if self.failed:
            Parse.setXtriageFailed(self)
            Parse.setMolrepFailed(self)
            Utils.failedHTML(self,'plots_xtriage')
            Utils.failedHTML(self,'jon_summary_xtriage')
            Utils.failedHTML(self,'jon_summary_molrep')
        else:
            self.plotXtriage()
            Summary.summaryXtriage(self)
            self.htmlSummaryXtriage()
            Summary.summaryMolrep(self)
            self.htmlSummaryMolrep()
        output = {}
        status = {}
        failed = False
        cell_results = False
        cell_out = False
        
        try:
            if self.gui:
                sl = 'jon_summary_xtriage.php'
            else:
                sl = 'jon_summary_xtriage.html'                
            xtriage_path = os.path.join(self.working_dir,sl)
            if os.path.exists(xtriage_path):
                output['Xtriage summary html']   = xtriage_path
            else:
                output['Xtriage summary html']   = 'None'
        except:
            self.logger.exception('**Could not update path of xtriage summary html file.**')
            output['Xtriage summary html']   = 'FAILED'
            failed = True
        
        try:
            if self.gui:
                sl = 'plots_xtriage.php'
            else:
                sl = 'plots_xtriage.html'                
            xtriage_path = os.path.join(self.working_dir,sl)
            if os.path.exists(xtriage_path):
                output['Xtriage plots html']   = xtriage_path
            else:
                output['Xtriage plots html']   = 'None'
        except:
            self.logger.exception('**Could not update path of xtriage plots html file.**')
            output['Xtriage plots html']   = 'FAILED'
            failed = True
        
        try:
            if self.gui:
                sl = 'jon_summary_molrep.php'
            else:
                sl = 'jon_summary_molrep.html'                
            molrep_path = os.path.join(self.working_dir,sl)
            if os.path.exists(molrep_path):
                output['Molrep summary html']   = molrep_path
            else:
                output['Molrep summary html']   = 'None'
        except:
            self.logger.exception('**Could not update path of molrep summary html file.**')
            output['Molrep summary html']   = 'FAILED'
            failed = True
                
        #Get rapd_agent_cell results back       
        try:
            if self.passback:
                cell_results = self.cell_output.get()
                #Utils.pp(self,cell_results)
                if cell_results['status'] == 'FAILED':
                    failed = True
                del cell_results['status']
                cell_out = cell_results['Output files']
                del cell_results['Output files']
        except:
            self.logger.exception('**Error importing rapd_agent_cell results**')
        
        #Get proper status.
        if failed:
            status['status'] = 'FAILED'
        else:
            status['status'] = 'SUCCESS'
        #Put all the result dicts from all the programs run into one resultant dict and pass it along the pipe.
        try:
            results = {}
            if status:
                results.update(status)        
            if self.xtriage_results:
                #Utils.pp(self,self.xtriage_results)
                results.update(self.xtriage_results)
            if self.molrep_results:
                #Utils.pp(self,self.molrep_results)
                results.update(self.molrep_results)
            if cell_results:
                results.update(cell_results)
            if output:
                if self.passback:
                    if cell_results:
                        output.update(cell_out)
                results.update(output)
            if results:
                self.input.insert(0,'STATS')
                self.input.append(results)
            """
            if self.passback:
                if self.output0 != None:
                    self.output0.put(self.input)
            """        
            #else:
            if self.gui:
                self.sendBack2(self.input)
        
        except:
            self.logger.exception('**Could not send results to pipe.**')
               
        try:
            #Cleanup my mess.
            if self.clean:
                if failed == False:
                    rm = 'rm -rf *.ps *.btc *.tab *.xml'
                    self.logger.debug('Cleaning up files')
                    self.logger.debug(rm)
                    os.system(rm)                    
        except:
            self.logger.exception('**Could not cleanup**')
            
        #Say job is complete.
        t = round(time.time()-self.st)
        self.logger.debug('-------------------------------------')
        self.logger.debug('RAPD AutoStat complete.')
        self.logger.debug('Total elapsed time: ' + str(t) + ' seconds')
        self.logger.debug('-------------------------------------')
        print '\n-------------------------------------'
        print 'RAPD AutoStat complete.'
        print 'Total elapsed time: ' + str(t) + ' seconds'
        print '-------------------------------------'        
        #sys.exit(0) #did not appear to end script with some programs continuing on for some reason.
        os._exit(0)
                
    def plotXtriage(self):
        """
        generate plots html/php file
        """      
        self.logger.debug('AutoStats::plotXtriage')
        try:        
            if self.xtriage_results:               
                xtriage_anom       = self.xtriage_results.get('Xtriage results').get('Xtriage anom plot')
                xtriage_int        = self.xtriage_results.get('Xtriage results').get('Xtriage int plot')
                xtriage_i          = self.xtriage_results.get('Xtriage results').get('Xtriage i plot')
                xtriage_nz         = self.xtriage_results.get('Xtriage results').get('Xtriage nz plot')
                xtriage_l          = self.xtriage_results.get('Xtriage results').get('Xtriage l-test plot')
                xtriage_z          = self.xtriage_results.get('Xtriage results').get('Xtriage z plot')
                             
                if self.gui:
                    xtriage_plot  = "<?php\n"
                    xtriage_plot += "//prevents caching\n"
                    xtriage_plot += 'header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");\n'
                    xtriage_plot += 'header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");\n'
                    xtriage_plot += 'header("Cache-Control: post-check=0, pre-check=0",false);\n'
                    xtriage_plot += "session_cache_limiter();\n"
                    xtriage_plot += "session_start();\n"
                    xtriage_plot += "require('/var/www/html/rapd/login/config.php');\n"
                    xtriage_plot += "require('/var/www/html/rapd/login/functions.php');\n"
                    xtriage_plot +="//prevents unauthorized access\n"
                    xtriage_plot +='if(allow_user() != "yes")\n'
                    xtriage_plot +="{\n"
                    xtriage_plot +='    if(allow_local_data($_SESSION[data]) != "yes")\n'
                    xtriage_plot +="    {\n"
                    xtriage_plot +="        include ('./login/no_access.html');\n"
                    xtriage_plot +="        exit();\n"
                    xtriage_plot +="    }\n"
                    xtriage_plot +="}\n"                
                    xtriage_plot += "?>\n\n"
                    xtriage_plot += "<html>\n"
                else:                
                    xtriage_plot = "<html>\n"
                xtriage_plot += "  <head>\n"
                xtriage_plot += '    <style type="text/css">\n'
                xtriage_plot += "      body {\n"
                xtriage_plot += "        background-image: none;\n"
                xtriage_plot += "      }\n"
                xtriage_plot += "       .y-label {width:7px; position:absolute; text-align:center; top:300px; left:15px; }\n"
                xtriage_plot += "       .x-label {position:relative; text-align:center; top:10px; }\n"
                xtriage_plot += "       .title {font-size:30px; text-align:center;} \n"
                xtriage_plot += "    </style>\n"            
                if self.gui == False:
                    xtriage_plot += '    <link href="layout.css" rel="stylesheet" type="text/css"></link>\n'
                    xtriage_plot += '    <link type="text/css" href="../css/south-street/njquery-ui-1.7.2.custom.css" rel="stylesheet" />\n'
                    xtriage_plot += '    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js" type="text/javascript"></script>\n'
                    xtriage_plot += '    <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js" type="text/javascript"></script>\n'
                    xtriage_plot += '    <script language="javascript" type="text/javascript" src="../js/flot/jquery.flot.js"></script>\n'
                xtriage_plot += "    <script type='text/javascript'>\n"
                xtriage_plot += '    $(function() {\n'
                xtriage_plot += '        // Tabs\n'
                xtriage_plot += "        $('.tabs').tabs();\n"
                xtriage_plot += '    });\n'        
                xtriage_plot += "    </script>\n\n"        
                xtriage_plot += "  </head>\n"
                xtriage_plot += "  <body>\n"
                xtriage_plot += "    <table>\n"
                xtriage_plot += "      <tr> \n"
                xtriage_plot += '        <td width="100%">\n'
                xtriage_plot += '        <div class="tabs">\n'
                xtriage_plot += "          <!-- This is where the tab labels are defined\n"
                xtriage_plot += "               221 = tab2(on page) tab2(full output tab) tab1 -->\n"
                xtriage_plot += "          <ul>\n"
                xtriage_plot += '            <li><a href="#tabs-440">Intensity</a></li>\n'        
                xtriage_plot += '            <li><a href="#tabs-441">Z scores</a></li>\n'
                xtriage_plot += '            <li><a href="#tabs-442">Anom Signal</a></li>\n'            
                xtriage_plot += '            <li><a href="#tabs-443">I/sigI</a></li>\n'
                xtriage_plot += '            <li><a href="#tabs-444">NZ test</a></li>\n'                        
                xtriage_plot += '            <li><a href="#tabs-445">L-test</a></li>\n'
                xtriage_plot += "          </ul>\n"
                xtriage_plot += '          <div id="tabs-440">\n'
                xtriage_plot += '            <div class=title><b>Mean I vs. Resolution</b></div>\n'
                xtriage_plot += '            <div id="chart1_div3" style="width:750px;height:550px;margin-left:20;"></div>\n'
                xtriage_plot += '            <span class=y-label>M e a n &nbsp I</span>\n'
                xtriage_plot += '            <div class=x-label>Resolution(A)</div>\n' 
                xtriage_plot += "          </div>\n"
                xtriage_plot += '          <div id="tabs-441">\n'
                xtriage_plot += '            <div class=title><b>Data Sanity and Completeness check</b></div>\n'
                xtriage_plot += '            <div id="chart2_div3" style="width:750px;height:550px;margin-left:20;"></div>\n'
                xtriage_plot += '            <span class=y-label>Z &nbsp S c o r e</span>\n'
                xtriage_plot += '            <div class=x-label>Resolution(A)</div>\n' 
                xtriage_plot += "          </div>\n"            
                xtriage_plot += '          <div id="tabs-442">\n'
                xtriage_plot += '            <div class=title><b>Anomalous Measurability</b></div>\n'
                xtriage_plot += '            <div id="chart3_div3" style="width:750px;height:550px;margin-left:20;"></div>\n'
                xtriage_plot += '            <span class=y-label></span>\n'
                xtriage_plot += '            <div class=x-label>Resolution(A)</div>\n' 
                xtriage_plot += "          </div>\n"        
                xtriage_plot += '          <div id="tabs-443">\n'
                xtriage_plot += '            <div class=title><b>Signal to Noise vs. Resolution</b></div>\n'
                xtriage_plot += '            <div id="chart4_div3" style="width:750px;height:550px;margin-left:20;"></div>\n'
                xtriage_plot += '            <span class=y-label>I / S i g I</span>\n'
                xtriage_plot += '            <div class=x-label>Resolution(A)</div>\n' 
                xtriage_plot += "          </div>\n"
                xtriage_plot += '          <div id="tabs-444">\n'
                xtriage_plot += '            <div class=title><b>NZ Test</b></div>\n'
                xtriage_plot += '            <div id="chart5_div3" style="width:750px;height:550px;margin-left:20;"></div>\n'
                xtriage_plot += '            <span class=y-label></span>\n'
                xtriage_plot += '            <div class=x-label>z</div>\n' 
                xtriage_plot += "          </div>\n"
                xtriage_plot += '          <div id="tabs-445">\n'
                xtriage_plot += '            <div class=title><b>L-Test</b></div>\n'
                xtriage_plot += '            <div id="chart6_div3" style="width:750px;height:550px;margin-left:20;"></div>\n'
                xtriage_plot += '            <span class=y-label></span>\n'
                xtriage_plot += '            <div class=x-label>|I|</div>\n' 
                xtriage_plot += "          </div>\n"
                xtriage_plot += "        </div>\n"
                xtriage_plot += "        <!-- End of Tabs -->\n"
                xtriage_plot += "      </td>\n"
                xtriage_plot += "     </tr>\n"
                xtriage_plot += "  </table>\n\n"
                xtriage_plot += '  <script id="source" language="javascript" type="text/javascript">\n'
                xtriage_plot += "$(function () {\n\n"
                xtriage_plot += "    var Int1 = [], Int2 = [], Int3 = [];\n\n"        
                for x in range(len(xtriage_int)):
                    xtriage_plot += "    Int1.push([-"+xtriage_int[x][0]+","+xtriage_int[x][1]+"]);\n"
                    xtriage_plot += "    Int2.push([-"+xtriage_int[x][0]+","+xtriage_int[x][2]+"]);\n"
                    xtriage_plot += "    Int3.push([-"+xtriage_int[x][0]+","+xtriage_int[x][3]+"]);\n"
                xtriage_plot += "    var Z1 = [], Z2 = [];\n\n"        
                for x in range(len(xtriage_z)):
                    xtriage_plot += "    Z1.push([-"+xtriage_z[x][0]+","+xtriage_z[x][1]+"]);\n"
                    xtriage_plot += "    Z2.push([-"+xtriage_z[x][0]+","+xtriage_z[x][2]+"]);\n"
                xtriage_plot += "    var Anom1 = [], Anom2 = [], mark = [];\n\n"        
                junk = []
                for x in range(len(xtriage_anom)):
                    junk.append(float(xtriage_anom[x][0]))
                    xtriage_plot += "    Anom1.push([-"+xtriage_anom[x][0]+","+xtriage_anom[x][1]+"]);\n"
                    xtriage_plot += "    Anom2.push([-"+xtriage_anom[x][0]+","+xtriage_anom[x][2]+"]);\n"
                mark_max = min(junk)
                mark_min = max(junk)
                xtriage_plot += "    for (var i = -"+str(mark_min)+"; i < -" + str(mark_max) + "; i +=0.25)\n"            
                xtriage_plot += "    mark.push([i,0.05]);\n"
                xtriage_plot += "    var I1 = [];\n\n"     
                for x in range(len(xtriage_i)):
                    xtriage_plot += "    I1.push([-"+xtriage_i[x][0]+","+xtriage_i[x][1]+"]);\n"
                xtriage_plot += "    var NZ1 = [], NZ2 = [], NZ3 = [], NZ4 = [];\n\n"        
                for x in range(len(xtriage_nz)):
                    xtriage_plot += "    NZ1.push(["+xtriage_nz[x][0]+","+xtriage_nz[x][1]+"]);\n"
                    xtriage_plot += "    NZ2.push(["+xtriage_nz[x][0]+","+xtriage_nz[x][2]+"]);\n"
                    xtriage_plot += "    NZ3.push(["+xtriage_nz[x][0]+","+xtriage_nz[x][3]+"]);\n"
                    xtriage_plot += "    NZ4.push(["+xtriage_nz[x][0]+","+xtriage_nz[x][4]+"]);\n"
                xtriage_plot += "    var L1 = [], L2 = [], L3 = [];\n\n"        
                for x in range(len(xtriage_l)):
                    xtriage_plot += "    L1.push(["+xtriage_l[x][0]+","+xtriage_l[x][1]+"]);\n"
                    xtriage_plot += "    L2.push(["+xtriage_l[x][0]+","+xtriage_l[x][2]+"]);\n"
                    xtriage_plot += "    L3.push(["+xtriage_l[x][0]+","+xtriage_l[x][3]+"]);\n"
                xtriage_plot += '    var plot1 = $.plot($("#chart1_div3"),\n'
                xtriage_plot += '        [ { data: Int1,label:"&lt I &gt _smooth" },{data: Int2,label:"&lt I &gt _binning"},\n'
                xtriage_plot += '          {data: Int3,label:"&lt I &gt _expected"}],\n'
                xtriage_plot += "        { lines: { show: true},\n"
                xtriage_plot += "          points: { show: true },\n"
                xtriage_plot += "          selection: { mode: 'xy' },\n"
                xtriage_plot += "          grid: { hoverable: true, clickable: true },\n"
                xtriage_plot += "          xaxis: { transform: function (v) { return Math.log(-v); },\n"
                xtriage_plot += "                   inverseTransform: function (v) { return Math.exp(-v); },\n"
                xtriage_plot += "                   tickFormatter: ( function negformat(val,axis){return -val.toFixed(axis.tickDecimals);} ) },\n"        
                xtriage_plot += "          yaxis: {min:0}\n"
                xtriage_plot += "        });\n\n"            
                xtriage_plot += '    var plot2 = $.plot($("#chart2_div3"),\n'
                xtriage_plot += '        [ { data: Z1, label:"Z_score" },{ data: Z2, label:"Completeness" }],\n'
                xtriage_plot += "        { lines: { show: true},\n"
                xtriage_plot += "          points: { show: true },\n"
                xtriage_plot += "          selection: { mode: 'xy' },\n"
                xtriage_plot += "          grid: { hoverable: true, clickable: true },\n"
                xtriage_plot += "          xaxis: { transform: function (v) { return Math.log(-v); },\n"
                xtriage_plot += "                   inverseTransform: function (v) { return Math.exp(-v); },\n"
                xtriage_plot += "                   tickFormatter: ( function negformat(val,axis){return -val.toFixed(axis.tickDecimals);} ) },\n"        
                xtriage_plot += "          yaxis: {min:0}\n"
                xtriage_plot += "        }); \n\n"
                xtriage_plot += '    var plot3 = $.plot($("#chart3_div3"),\n'
                xtriage_plot += "        [ {data: Anom1,label:'Obs_anom_meas'},{data: Anom2,label:'Smoothed'},\n"
                xtriage_plot += "          { data: mark,label:'min level for anom signal'}],\n"
                xtriage_plot += "        { lines: { show: true},\n"
                xtriage_plot += "          points: { show: true },\n"
                xtriage_plot += "          selection: { mode: 'xy' },\n"
                xtriage_plot += "          grid: { hoverable: true, clickable: true },\n"
                xtriage_plot += "          xaxis: { transform: function (v) { return Math.log(-v); },\n"
                xtriage_plot += "                   inverseTransform: function (v) { return Math.exp(-v); },\n"
                xtriage_plot += "                   tickFormatter: ( function negformat(val,axis){return -val.toFixed(axis.tickDecimals);} ) },\n"        
                xtriage_plot += "          yaxis: {min:0}\n"
                xtriage_plot += "        }); \n\n"
                xtriage_plot += '    var plot4 = $.plot($("#chart4_div3"),\n'
                xtriage_plot += '        [ { data: I1,label:"Signal_to_Noise" }],\n'
                xtriage_plot += "        { lines: { show: true},\n"
                xtriage_plot += "          points: { show: true },\n"
                xtriage_plot += "          selection: { mode: 'xy' },\n"
                xtriage_plot += "          grid: { hoverable: true, clickable: true },\n"
                xtriage_plot += "          xaxis: { transform: function (v) { return Math.log(-v); },\n"
                xtriage_plot += "                   inverseTransform: function (v) { return Math.exp(-v); },\n"
                xtriage_plot += "                   tickFormatter: ( function negformat(val,axis){return -val.toFixed(axis.tickDecimals);} ) },\n"        
                xtriage_plot += "          yaxis: {min:0}\n"
                xtriage_plot += "        }); \n\n"
                xtriage_plot += '    var plot5 = $.plot($("#chart5_div3"),\n'
                xtriage_plot += '        [ { data: NZ1, label:"Acen_obs"},{ data: NZ2, label:"Acen_untwinned"},\n'
                xtriage_plot += '          { data: NZ3, label:"Cen_obs"},{ data: NZ4, label:"Cen_untwinned"}],\n'
                xtriage_plot += "        { lines: { show: true},\n"
                xtriage_plot += "          points: { show: true },\n"
                xtriage_plot += "          selection: { mode: 'xy' },\n"
                xtriage_plot += "          grid: { hoverable: true, clickable: true },\n"
                xtriage_plot += "          yaxis: {min:0},\n"
                xtriage_plot += "          xaxis: {min:0}\n"
                xtriage_plot += "        }); \n\n"        
                xtriage_plot += '    var plot6 = $.plot($("#chart6_div3"),\n'
                xtriage_plot += '        [ { data: L1,label:"Obs"},{ data: L2,label:"Acen_th_untwinned"},\n'
                xtriage_plot += '          { data: L3,label:"Acen_th_perfect_twin"}],\n'
                xtriage_plot += "        { lines: { show: true},\n"
                xtriage_plot += "          points: { show: true },\n"
                xtriage_plot += "          selection: { mode: 'xy' },\n"
                xtriage_plot += "          grid: { hoverable: true, clickable: true },\n"
                xtriage_plot += "          yaxis: {min:0},\n"
                xtriage_plot += "          xaxis: {min:0}\n"
                xtriage_plot += "        }); \n\n"   
                xtriage_plot += "    function showTooltip(x, y, contents) {\n"
                xtriage_plot += "        $('<div id=\"tooltip\">' + contents + '</div>').css( {\n"
                xtriage_plot += "            position: 'absolute',\n"
                xtriage_plot += "            display: 'none',\n"
                xtriage_plot += "            top: y + 5,\n"
                xtriage_plot += "            left: x + 5,\n"
                xtriage_plot += "            border: '1px solid #fdd',\n"
                xtriage_plot += "            padding: '2px',\n"
                xtriage_plot += "            'background-color': '#fee',\n"
                xtriage_plot += "            opacity: 0.80\n"
                xtriage_plot += '        }).appendTo("body").fadeIn(200);\n'
                xtriage_plot += "    }\n\n"
                xtriage_plot += "    var previousPoint = null;\n"
                xtriage_plot += '    $("#chart1_div3").bind("plothover", function (event, pos, item) {\n'
                xtriage_plot += '        $("#x").text(pos.x.toFixed(2));\n'
                xtriage_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
                xtriage_plot += "        if (true) {\n"
                xtriage_plot += "            if (item) {\n"
                xtriage_plot += "                if (previousPoint != item.datapoint) {\n"
                xtriage_plot += "                    previousPoint = item.datapoint;\n\n"
                xtriage_plot += '                    $("#tooltip").remove();\n'
                xtriage_plot += "                    var x = -(item.datapoint[0].toFixed(2)),\n"
                xtriage_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
                xtriage_plot += "                    showTooltip(item.pageX, item.pageY,\n"
                xtriage_plot += '                                item.series.label + " at " + x + " Resolution (A) ");\n'
                #xtriage_plot += '                                \'Resolution (A): \' + x + \', Mean d"/sig: \' + y);\n'
                #xtriage_plot += '                                "Resolution (A): " + x + ", Mean I/sig: " + y);\n'
                xtriage_plot += "                }\n"
                xtriage_plot += "            }\n"
                xtriage_plot += "            else {\n"
                xtriage_plot += '                $("#tooltip").remove();\n'
                xtriage_plot += "                previousPoint = null;\n"
                xtriage_plot += "            }\n"
                xtriage_plot += "        }\n"
                xtriage_plot += "    });\n\n"        
                xtriage_plot += '    $("#chart2_div3").bind("plothover", function (event, pos, item) {\n'
                xtriage_plot += '        $("#x").text(pos.x.toFixed(2));\n'
                xtriage_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
                xtriage_plot += "        if (true) {\n"
                xtriage_plot += "            if (item) {\n"
                xtriage_plot += "                if (previousPoint != item.datapoint) {\n"
                xtriage_plot += "                    previousPoint = item.datapoint;\n\n"
                xtriage_plot += '                    $("#tooltip").remove();\n'
                xtriage_plot += "                    var x = -(item.datapoint[0].toFixed(2)),\n"
                xtriage_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
                xtriage_plot += "                    showTooltip(item.pageX, item.pageY,\n"
                xtriage_plot += '                                "Resolution (A): " + x + ", %Completeness: " + y);\n'
                xtriage_plot += "                }\n"
                xtriage_plot += "            }\n"
                xtriage_plot += "            else {\n"
                xtriage_plot += '                $("#tooltip").remove();\n'
                xtriage_plot += "                previousPoint = null;\n"
                xtriage_plot += "            }\n"
                xtriage_plot += "        }\n"
                xtriage_plot += "    });\n\n"
                xtriage_plot += '    $("#chart3_div3").bind("plothover", function (event, pos, item) {\n'
                xtriage_plot += '        $("#x").text(pos.x.toFixed(2));\n'
                xtriage_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
                xtriage_plot += "        if (true) {\n"
                xtriage_plot += "            if (item) {\n"
                xtriage_plot += "                if (previousPoint != item.datapoint) {\n"
                xtriage_plot += "                    previousPoint = item.datapoint;\n\n"
                xtriage_plot += '                    $("#tooltip").remove();\n'
                xtriage_plot += "                    var x = -(item.datapoint[0].toFixed(2)),\n"
                xtriage_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
                xtriage_plot += "                    showTooltip(item.pageX, item.pageY,\n"
                xtriage_plot += '                                \'Resolution (A): \' + x + \', Mean d"/sig: \' + y);\n'
                xtriage_plot += "                }\n"
                xtriage_plot += "            }\n"
                xtriage_plot += "            else {\n"
                xtriage_plot += '                $("#tooltip").remove();\n'
                xtriage_plot += "                previousPoint = null;\n"
                xtriage_plot += "            }\n"
                xtriage_plot += "        }\n"
                xtriage_plot += "    });\n\n"
                xtriage_plot += '    $("#chart4_div3").bind("plothover", function (event, pos, item) {\n'
                xtriage_plot += '        $("#x").text(pos.x.toFixed(2));\n'
                xtriage_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
                xtriage_plot += "        if (true) {\n"
                xtriage_plot += "            if (item) {\n"
                xtriage_plot += "                if (previousPoint != item.datapoint) {\n"
                xtriage_plot += "                    previousPoint = item.datapoint;\n\n"
                xtriage_plot += '                    $("#tooltip").remove();\n'
                xtriage_plot += "                    var x = item.datapoint[0].toFixed(2),\n"
                xtriage_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
                xtriage_plot += "                    showTooltip(item.pageX, item.pageY,\n"
                xtriage_plot += '                                "CCweak: " + x + ", CCall: " + y);\n'
                xtriage_plot += "                }\n"
                xtriage_plot += "            }\n"
                xtriage_plot += "            else {\n"
                xtriage_plot += '                $("#tooltip").remove();\n'
                xtriage_plot += "                previousPoint = null;\n"
                xtriage_plot += "            }\n"
                xtriage_plot += "        }\n"
                xtriage_plot += "    });\n\n"
                xtriage_plot += '    $("#chart5_div3").bind("plothover", function (event, pos, item) {\n'
                xtriage_plot += '        $("#x").text(pos.x.toFixed(2));\n'
                xtriage_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
                xtriage_plot += "        if (true) {\n"
                xtriage_plot += "            if (item) {\n"
                xtriage_plot += "                if (previousPoint != item.datapoint) {\n"
                xtriage_plot += "                    previousPoint = item.datapoint;\n\n"
                xtriage_plot += '                    $("#tooltip").remove();\n'
                xtriage_plot += "                    var x = item.datapoint[0].toFixed(2),\n"
                xtriage_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
                xtriage_plot += "                    showTooltip(item.pageX, item.pageY,\n"
                xtriage_plot += '                                 item.series.label  );\n'
                #xtriage_plot += '                                "PATFOM: " + x + ", CCall: " + y);\n'
                xtriage_plot += "                }\n"
                xtriage_plot += "            }\n"
                xtriage_plot += "            else {\n"
                xtriage_plot += '                $("#tooltip").remove();\n'
                xtriage_plot += "                previousPoint = null;\n"
                xtriage_plot += "            }\n"
                xtriage_plot += "        }\n"
                xtriage_plot += "    });\n\n"                        
                xtriage_plot += '    $("#chart6_div3").bind("plothover", function (event, pos, item) {\n'
                xtriage_plot += '        $("#x").text(pos.x.toFixed(2));\n'
                xtriage_plot += '        $("#y").text(pos.y.toFixed(2));\n\n'
                xtriage_plot += "        if (true) {\n"
                xtriage_plot += "            if (item) {\n"
                xtriage_plot += "                if (previousPoint != item.datapoint) {\n"
                xtriage_plot += "                    previousPoint = item.datapoint;\n\n"
                xtriage_plot += '                    $("#tooltip").remove();\n'
                xtriage_plot += "                    var x = item.datapoint[0].toFixed(2),\n"
                xtriage_plot += "                        y = item.datapoint[1].toFixed(2);\n\n"
                xtriage_plot += "                    showTooltip(item.pageX, item.pageY,\n"
                xtriage_plot += '                                item.series.label );\n'
                xtriage_plot += "                }\n"
                xtriage_plot += "            }\n"
                xtriage_plot += "            else {\n"
                xtriage_plot += '                $("#tooltip").remove();\n'
                xtriage_plot += "                previousPoint = null;\n"
                xtriage_plot += "            }\n"
                xtriage_plot += "        }\n"
                xtriage_plot += "    });\n\n"        
                xtriage_plot += "});\n"
                xtriage_plot += "</script>\n"
                xtriage_plot += "</body>\n"
                xtriage_plot += "</html>\n"
                if xtriage_plot:
                    if self.gui:
                        sp = 'plots_xtriage.php'
                    else:
                        sp = 'plots_xtriage.html'                
                    xtriage_plot_file = open(sp,'w')
                    xtriage_plot_file.writelines(xtriage_plot)
                    xtriage_plot_file.close()
                    """
                    try:
                        shutil.copy(sp,self.working_dir)
                    except:
                        self.logger.debug('Could not copy plots_xtriage.html to home dir.')
                    """
            else:
                Utils.failedHTML(self,'plots_xtriage')
                
        except:
            self.logger.exception('**ERROR in AutoStats.plotXtriage**')
            Utils.failedHTML(self,'plots_xtriage')

    def htmlSummaryXtriage(self):
        """
        Create HTML/php files for xtriage output results.
        """
        self.logger.debug('AutoStats::htmlSummaryXtriage')
        try:
            if self.xtriage_summary:
                if self.gui:
                    sl = 'jon_summary_xtriage.php'
                else:
                    sl = 'jon_summary_xtriage.html'
                jon_summary = open(sl,'w')
                if self.gui:
                    jon_summary.write("<?php\n")
                    jon_summary.write("//prevents caching\n")
                    jon_summary.write('header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");\n')
                    jon_summary.write('header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");\n')
                    jon_summary.write('header("Cache-Control: post-check=0, pre-check=0",false);\n')
                    jon_summary.write("session_cache_limiter();\n")
                    jon_summary.write("session_start();\n")
                    jon_summary.write("require('/var/www/html/rapd/login/config.php');\n")
                    jon_summary.write("require('/var/www/html/rapd/login/functions.php');\n")
                    jon_summary.write("//prevents unauthorized access\n")
                    jon_summary.write('if(allow_user() != "yes")\n')
                    jon_summary.write("{\n")
                    jon_summary.write('    if(allow_local_data($_SESSION[data]) != "yes")\n')
                    jon_summary.write("    {\n")
                    jon_summary.write("        include ('./login/no_access.html');\n")
                    jon_summary.write("        exit();\n")
                    jon_summary.write("    }\n")
                    jon_summary.write("}\n")
                    jon_summary.write("?>\n\n")                
                jon_summary.write('<html>\n')
                jon_summary.write('  <head>\n')
                jon_summary.write('    <style type="text/css" media="screen">\n')
                if self.gui == False:    
                    jon_summary.write('      @import "../js/dataTables-1.5/media/css/demo_page.css";\n')
                    jon_summary.write('      @import "../js/dataTables-1.5/media/css/demo_table.css";\n')                
                    jon_summary.write('      @import "../css/south-street/jquery-ui-1.7.2.custom.css";\n')
                jon_summary.write('    body {\n')
                jon_summary.write('      background-image: none;\n')
                jon_summary.write('    }\n')
                jon_summary.write('    .dataTables_wrapper {position: relative; min-height: 75px; _height: 302px; clear: both;    }\n')
                jon_summary.write('    table.display td {padding: 1px 7px;}\n')
                jon_summary.write('    tr.GradeB {font-style: italic; color: gray;}\n')
                jon_summary.write('    tr.GradeD {font-weight: bold;}\n')
                jon_summary.write('    </style>\n')
                if self.gui == False:    
                    jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.js"></script>\n')
                    jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.dataTables.js"></script>\n')
                    jon_summary.write('    <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js" type="text/javascript"></script>\n')
                jon_summary.write('    <script type="text/javascript" charset="utf-8">\n')
                jon_summary.write('      $(document).ready(function() {\n')
                jon_summary.write("        $('#accordion-xtriage').accordion({\n")
                jon_summary.write('           collapsible: true,\n')
                jon_summary.write('           active: false         });\n')
                if self.xtriage_summary:
                    jon_summary.write("        $('#xtriage-auto2').dataTable({\n")
                    jon_summary.write('           "bPaginate": false,\n')
                    jon_summary.write('           "bFilter": false,\n')
                    jon_summary.write('           "bInfo": false,\n')
                    jon_summary.write('           "bSort": false,\n') 
                    jon_summary.write('           "bAutoWidth": false    });\n')                
                    jon_summary.write("        $('#xtriage_pat').dataTable({\n")
                    jon_summary.write('           "bPaginate": false,\n')
                    jon_summary.write('           "bFilter": false,\n')
                    jon_summary.write('           "bInfo": false,\n')
                    jon_summary.write('           "bSort": false,\n') 
                    jon_summary.write('           "bAutoWidth": false    });\n')                
                if self.pts:
                    jon_summary.write("        $('#xtriage_pts').dataTable({\n")
                    jon_summary.write('           "bPaginate": false,\n')
                    jon_summary.write('           "bFilter": false,\n')
                    jon_summary.write('           "bInfo": false,\n')
                    jon_summary.write('           "bSort": false,\n') 
                    jon_summary.write('           "bAutoWidth": false    });\n')               
                if self.twin:
                    jon_summary.write("        $('#xtriage_twin').dataTable({\n")
                    jon_summary.write('           "bPaginate": false,\n')
                    jon_summary.write('           "bFilter": false,\n')
                    jon_summary.write('           "bInfo": false,\n')
                    jon_summary.write('           "bSort": false,\n') 
                    jon_summary.write('           "bAutoWidth": false    });\n')               
                """
                if self.tooltips:
                    jon_summary.writelines(self.tooltips)
                """
                jon_summary.write('                } );\n')
                jon_summary.write("    </script>\n\n\n")
                jon_summary.write(" </head>\n")
                jon_summary.write('  <body id="dt_example">\n')
                if self.xtriage_summary:
                    jon_summary.writelines(self.xtriage_summary)
                else:
                    jon_summary.write("      <h2 class='Results'>Error in Xtriage analysis</h1>\n")            
                jon_summary.write('    <div id="container">\n')
                jon_summary.write('    <div class="full_width big">\n')
                jon_summary.write('      <div id="demo">\n')            
                jon_summary.write("      <h1 class='Results'>Xtriage Output</h1>\n")
                jon_summary.write("     </div>\n")  
                jon_summary.write("     </div>\n")  
                jon_summary.write('      <div id="accordion-xtriage">\n')
                jon_summary.write('        <h3><a href="#">Click to view Xtriage log</a></h3>\n')
                jon_summary.write('          <div>\n')
                jon_summary.write('            <pre>\n')
                jon_summary.write('\n')
                #jon_summary.write('---------------AutoMR RESULTS---------------\n')
                #jon_summary.write('\n')            
                if self.xtriage_log2:
                    for line in self.xtriage_log2:
                        jon_summary.write('' + line )            
                else:
                    jon_summary.write('---------------Xtriage FAILED---------------\n')         
                jon_summary.write('            </pre>\n')
                jon_summary.write('          </div>\n')           
                jon_summary.write("      </div>\n")
                jon_summary.write("    </div>\n")
                jon_summary.write("  </body>\n")
                jon_summary.write("</html>\n")
                jon_summary.close()        
                #copy html file to working dir
                #shutil.copy(sl,self.working_dir)
            else:
                Utils.failedHTML(self,'jon_summary_xtriage')
            
        except:
            self.logger.exception('**ERROR in AutoStats.htmlSummaryXtriage**')

    def htmlSummaryMolrep(self):
        """
        Create HTML/php files for Molrep output results.
        """
        self.logger.debug('AutoStats::htmlSummaryMolrep')
        try:
            if self.molrep_summary:
                molrep_log        = self.molrep_results.get('Molrep results').get('Molrep log')
                if self.gui:
                    sl = 'jon_summary_molrep.php'
                else:
                    sl = 'jon_summary_molrep.html'
                jon_summary = open(sl,'w')
                if self.gui:
                    jon_summary.write("<?php\n")
                    jon_summary.write("//prevents caching\n")
                    jon_summary.write('header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");\n')
                    jon_summary.write('header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");\n')
                    jon_summary.write('header("Cache-Control: post-check=0, pre-check=0",false);\n')
                    jon_summary.write("session_cache_limiter();\n")
                    jon_summary.write("session_start();\n")
                    jon_summary.write("require('/var/www/html/rapd/login/config.php');\n")
                    jon_summary.write("require('/var/www/html/rapd/login/functions.php');\n")
                    jon_summary.write("//prevents unauthorized access\n")
                    jon_summary.write('if(allow_user() != "yes")\n')
                    jon_summary.write("{\n")
                    jon_summary.write('    if(allow_local_data($_SESSION[data]) != "yes")\n')
                    jon_summary.write("    {\n")
                    jon_summary.write("        include ('./login/no_access.html');\n")
                    jon_summary.write("        exit();\n")
                    jon_summary.write("    }\n")
                    jon_summary.write("}\n")
                    jon_summary.write("?>\n\n")                
                jon_summary.write('<html>\n')
                jon_summary.write('  <head>\n')
                jon_summary.write('    <style type="text/css" media="screen">\n')
                if self.gui == False:    
                    jon_summary.write('      @import "../js/dataTables-1.5/media/css/demo_page.css";\n')
                    jon_summary.write('      @import "../js/dataTables-1.5/media/css/demo_table.css";\n')                
                    jon_summary.write('      @import "../css/south-street/jquery-ui-1.7.2.custom.css";\n')
                jon_summary.write('    body {\n')
                jon_summary.write('      background-image: none;\n')
                jon_summary.write('    }\n')
                jon_summary.write('    .dataTables_wrapper {position: relative; min-height: 75px; _height: 302px; clear: both;    }\n')
                jon_summary.write('    table.display td {padding: 1px 7px;}\n')
                jon_summary.write('    tr.GradeB {font-style: italic; color: gray;}\n')
                jon_summary.write('    tr.GradeD {font-weight: bold;}\n')
                jon_summary.write('    </style>\n')
                if self.gui == False:    
                    jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.js"></script>\n')
                    jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.dataTables.js"></script>\n')
                    jon_summary.write('    <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js" type="text/javascript"></script>\n')
                jon_summary.write('    <script type="text/javascript" charset="utf-8">\n')
                jon_summary.write('      $(document).ready(function() {\n')
                jon_summary.write("        $('#accordion-molrep').accordion({\n")
                jon_summary.write('           collapsible: true,\n')
                jon_summary.write('           active: false         });\n')
                if self.molrep_summary:
                    jon_summary.write("        $('#molrep').dataTable({\n")
                    jon_summary.write('           "bPaginate": false,\n')
                    jon_summary.write('           "bFilter": false,\n')
                    jon_summary.write('           "bInfo": false,\n')
                    jon_summary.write('           "bSort": false,\n') 
                    jon_summary.write('           "bAutoWidth": false    });\n')             
                """
                if self.tooltips:
                    jon_summary.writelines(self.tooltips)
                """
                jon_summary.write('                } );\n')
                jon_summary.write("    </script>\n\n\n")
                jon_summary.write(" </head>\n")
                jon_summary.write('  <body id="dt_example">\n')
                if self.molrep_summary:
                    jon_summary.writelines(self.molrep_summary)
                else:
                    jon_summary.write("      <h2 class='Results'>Error in molrep analysis</h1>\n")
                jon_summary.write('    <div id="container">\n')
                jon_summary.write('    <div class="full_width big">\n')
                jon_summary.write('      <div id="demo">\n')            
                jon_summary.write("      <h1 class='Results'>Molrep Output</h1>\n")
                jon_summary.write("     </div>\n")  
                jon_summary.write("     </div>\n")  
                jon_summary.write('      <div id="accordion-molrep">\n')
                jon_summary.write('        <h3><a href="#">Click to view Molrep log</a></h3>\n')
                jon_summary.write('          <div>\n')
                jon_summary.write('            <pre>\n')
                jon_summary.write('\n')
                #jon_summary.write('---------------AutoMR RESULTS---------------\n')
                #jon_summary.write('\n')            
                if molrep_log:
                    file = open(molrep_log,'r')
                    for line in file:
                        jon_summary.write('' + line )
                    file.close()
                else:
                    jon_summary.write('---------------Molrep FAILED---------------\n')         
                jon_summary.write('            </pre>\n')
                jon_summary.write('          </div>\n')           
                jon_summary.write("      </div>\n")
                jon_summary.write("    </div>\n")
                jon_summary.write("  </body>\n")
                jon_summary.write("</html>\n")
                jon_summary.close()        
                #copy html file to working dir
                #shutil.copy(sl,self.working_dir)
            else:
                Utils.failedHTML(self,'jon_summary_molrep')
            
        except:
            self.logger.exception('**ERROR in AutoStats.htmlSummaryMolrep**')
        
def multiXtriage(input, output, logger):
    """
    Run phenix.xtriage.
    """
    logger.debug('AutoStats.multiXtriage')
    try:    
        file = open('xtriage.log','w')
        myoutput = subprocess.Popen(input, shell=True, stdout=file, stderr=file)    
        output.put(myoutput.pid)
        file.close()            
    
    except:
        logger.exception('**Error in AutoStats.multiXtriage**')

def multiMolrep(input, output, logger):
    """
    Run Molrep SRF.
    """
    logger.debug('AutoStats.multiMolrep')
    try:    
        file = open('molrep.log','w')
        myoutput = subprocess.Popen(input, shell=True, stdout=file, stderr=file)    
        output.put(myoutput.pid)
        file.close()            
    except:
        logger.exception('**Error in AutoStats.multimolrep**')


if __name__ == '__main__':
    #start logging
    LOG_FILENAME = '/tmp/rapd_agent_stats.log'
    # Set up a specific logger with our desired output level
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=100000, backupCount=5)
    #add a formatter
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('AutoStats.__init__')
    output0 = None
    #output1 = None
    #output2 = None    
    #construct test input
    input = [{#'cell': ['67.875', '67.875', '102.148', '90.000', '90.000', '90.000'],
              #'cell': [57.805,57.805,150.204,90,90,90],
              'dir' :  '/tmp/Output',
              #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/SAD/PK_lu_peak.sca',
              #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/insulin.sca',
              #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/Y567A_ATrich_dTTP_free.mtz',
              #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/thau_free.mtz',
              #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/SAD/UGM_PTS.sca',
              #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/MR/1UXM_A4V_twin.mtz',
              #'data': '/gpfs6/users/necat/Jon/RAPD_test/Datasets/SAD/r3_tricky_ANOM.sca',
              'data': '../test_data/129i15_b_free.mtz',
              #'sc': '0.55',
              #'timer': 15,
              'cluster': True,
              'test': True,
              #'type': 'Protein',
              'queue': True,
              'gui'  : False,
              'control': ('000.000.000.000',50001),
              'passback': True,
              'process_id': 11111,               
              }]
    tmp = AutoStats(input,output0,logger=logger)
    #T = TestHandler(input,logger=logger)

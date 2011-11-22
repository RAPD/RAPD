'''
__author__ = "Jon Schuermann, Frank Murphy"
__copyright__ = "Copyright 2010,2011 Cornell University"
__credits__ = ["Jon Schuermann","Frank Murphy","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2010/09/07"
'''
import multiprocessing
import os
import sys
import subprocess
import time
import shutil
import logging,logging.handlers

from rapd_agent_cell import PDBQuery
from rapd_agent_sad import AutoSolve
from rapd_communicate import Communicate
import rapd_agent_utilities as Utils
import rapd_agent_parse as Parse
import rapd_agent_summary as Summary

class AutoMolRep(multiprocessing.Process, Communicate):
    def __init__(self,input,logger=None):
        logger.info('AutoMolRep.__init__')
        self.st = time.time()
        self.input                              = input
        self.logger                             = logger        
        #Setting up data input
        self.setup                              = self.input[1]
        self.data                               = self.input[2]        
        self.preferences                        = self.input[3]
        self.controller_address                 = self.input[-1]
        
        #For testing individual modules
        self.test                               = False
        #Removes junk files and directories at end.
        self.clean                              = False
        #Calculate ADF for all solutions
        self.adf                                = True
        
        #variables to set
        self.pdbquery_timer                     = 20
        self.pdbquery_timer2                    = 60
        self.phaser_timer                       = False
        self.phaser_log                         = False
        self.phaser_results                     = {}
        self.phaser_failed                      = False
        self.phaser_summary                     = False
        self.pdb                                = False
        self.mtz                                = False
        self.cell_summary                       = False
        self.pdb_summary                        = False
        self.pdb_percent                        = False
        self.tooltips                           = False
        self.cellAnalysis                       = {}
        self.cellAnalysis_results               = False
        self.sad_status                         = {}
        self.cell                               = False
        self.cell2                              = False
        self.solvent_content                    = False       
        self.incompatible_cell                  = False
        self.input_sg                           = False
        self.wave                               = False
        self.status                             = {}
        self.pdb_code                           = False
        self.run_before                         = False        
        self.sample_type                        = self.preferences.get('sample_type')
        self.datafile                           = self.data.get('original').get('mtz_file')
        self.solvent_content                    = self.preferences.get('solvent_content')        
        if self.preferences.has_key('request'):
            if self.preferences.get('request').has_key('nmol'):
                self.nmol = self.preferences.get('request').get('nmol')
                if self.nmol == 0:
                    self.nmol = False
            else:
                self.nmol = False
            if self.preferences.get('request').has_key('pdb_name'):
                self.pdb_name = self.preferences.get('request').get('pdb_name')
                if self.pdb_name == None:
                    self.pdb_name = False
            else:
                self.pdb_name = False
            if self.preferences.get('request').has_key('pdb'):
                self.input_pdb = self.preferences.get('request').get('pdb')
                if self.input_pdb == None:
                    if self.preferences.get('request').has_key('pdb_code'):            
                        self.input_pdb = self.preferences.get('request').get('pdb_code')
                        if len(str(self.input_pdb)) == 0:
                            self.input_pdb = 'None'
                        else:
                            self.pdb_code = True
                    else:
                        self.input_pdb = 'None'
                else:
                    #It has the pdb so continue.
                    pass
            else:
                self.input_pdb = 'None'
        else:
            self.input_pdb = 'None'
            self.nmol = False
        #Get the process ID to pass it back so RAPD know which results are passed back.
        if self.preferences.has_key('request'):     
            if self.preferences.has_key('process_id'):            
                self.process_id = self.preferences.get('process_id')
            else:
                self.process_id = 11111       
        """
        #Search for ligands if input.
        if self.preferences.get('request').get('ligand') == 'None':
            self.ligand = False
        else:
            self.ligand = self.preferences.get('request').get('ligand')        
        """
        #Check if running from beamline and turn off testing if I forgot to.
        if self.preferences.get('request').has_key('request_type'):
            self.gui       = True
            self.test      = False
        else:
            self.gui       = False
        self.nproc = multiprocessing.cpu_count()
        #******BEAMLINE SPECIFIC*****
        type1 = os.uname()[4]        
        if type1 == 'x86_64':
            self.cluster_use                = True
        else:
            self.cluster_use                = False
        #******BEAMLINE SPECIFIC*****
        
        multiprocessing.Process.__init__(self,name='AutoMolRep')        
        #starts the new process
        self.start()
        
    def run(self):
        """
        Convoluted path of modules to run.
        """
        self.logger.debug('AutoMolRep::run')
        self.preprocess()        
        if self.input_pdb == 'None':
            self.processPDBQuery()
        else:
            self.processPhaser()
            self.postprocess()
            
    def preprocess(self):
        """
        Things to do before the main process runs
        1. Change to the correct directory
        2. Print out the reference for MR pipeline
        """
        self.logger.debug('AutoMolRep::preprocess')
        #change directory to the one specified in the incoming dict
        self.working_dir = self.setup.get('work')
        if os.path.exists(self.working_dir) == False:
            os.makedirs(self.working_dir)
        os.chdir(self.working_dir)
        #print out recognition of the program being used
        self.PrintInfo()
        #Get unit cell and SG info
        Utils.getInfoCellSG(self)
        if self.test:
            self.logger.debug('TEST IS SET "ON"')
  
    def processPDBQuery(self):
        """
        Prepare and run PDBQuery.
        """
        self.logger.debug('AutoMolRep::processPDBQuery')
        try:
            pdb_input = []
            pdb_dict = {}
            pdb_dict['process_id'] = self.process_id
            #pdb_dict['cell'] = self.cell2
            pdb_dict['dir'] = self.working_dir
            pdb_dict['data'] = self.datafile
            pdb_dict['test'] = self.test
            pdb_dict['type'] = self.sample_type
            pdb_dict['cluster'] = self.cluster_use
            pdb_dict['timer'] = self.pdbquery_timer
            pdb_dict['sc'] = str(self.solvent_content).zfill(3)
            pdb_dict['queue'] = True
            pdb_dict['gui'] = self.gui
            pdb_input.append(pdb_dict)
            junk = multiprocessing.Queue()
            args1 = {}
            args1['input']  = pdb_input
            args1['output0'] = junk
            args1['logger'] = self.logger
            job = multiprocessing.Process(target=PDBQuery,kwargs=args1).start()            
            self.pdb_percent = junk.get()
        
        except:
            self.logger.exception('**ERROR in AutoMolRep.processPBDQuery**')
            
    def processPhaser(self):
        """
        Run Phaser on input pdb file.
        """
        self.logger.debug('AutoMolRep::processPhaser')
        try:
            if self.phaser_log == False:
                self.phaser_log = []
            sg_name = []
            phaser_output = {}
            self.phaser_jobs = {}
            #Check data type
            file_type = self.datafile[-3:]
            if file_type == 'sca':
                #Get rid of spaces in the sca file SG and *'s.
                Utils.fixSCA(self)
            #Check if input_pdb is pdb file or pdbID.
            if self.input_pdb[-4:].upper() != '.PDB':
                timer = 0
                pid = Utils.downloadPDB(self,self.input_pdb)
                while 1:
                    if Utils.stillRunningCluster(self,pid):
                        pass
                    elif Utils.stillRunning(self,pid):
                        pass
                    else:
                        break
                    time.sleep(1)
                    timer += 1
                    print 'Waiting for PDB download to finish ' + str(timer) + ' seconds'
                self.input_pdb = os.path.join(os.getcwd(),self.input_pdb+'.pdb')
            else:
                if os.path.exists(self.input_pdb):
                    try:
                        shutil.copy(self.input_pdb,os.getcwd())
                    except:
                        self.logger.debug('Cannot copy input pdb to working dir. Probably already there.')
                    self.input_pdb = os.path.join(os.getcwd(),os.path.basename(self.input_pdb))
            
            #Check if input pdb is right size. If not, then grab first segid.
            check_matthews = Utils.checkMatthews(self)
            self.logger.debug(check_matthews)
            #Get MW and theoretical number of mols in AU.
            pdb_info = Utils.getPDBmw(self,self.input_pdb)
            #check_matthews = Utils.checkMatthews(self)
            mw_mol = pdb_info['MW']
            mwaa   = pdb_info['MWaa']
            mwna   = pdb_info['MWna']
            copy   = pdb_info['NMol']
            res_in = pdb_info['NRes']
            if self.nmol:
                copy = str(self.nmol)
            
            #Allow for up to 10% clashes
            clash = int(round(0.1*res_in))
            if clash > 50:
                clash = 50
            
            #Run Phaser in all the space groups.
            run_sg = Utils.subGroups(self,Utils.convertSG(self,self.input_sg),'phaser')
            for sg in run_sg:
                sg2 = Utils.convertSG(self,sg,True)
                sg_name.append(sg2)
                Utils.folders(self,'Phaser_'+sg2)
                if os.path.exists('adf.com'):
                    os.system('rm -rf adf.com')
                file = open('phaser.com','w')
                command  = 'phaser << eof\n'
                command += 'TITLe junk\n'
                command += 'MODE MR_AUTO\n'
                command += 'HKLIn '+self.datafile+'\n'
                command += 'LABIn F=F SIGF=SIGF\n'
                command += 'ENSEmble junk PDB '+self.input_pdb+' IDENtity 70\n'
                if mwaa > 0:
                    command += 'COMPosition PROTein MW '+str(mwaa)+' NUM '+str(copy)+'\n'
                if mwna > 0:
                    command += 'COMPosition NUCLEIC MW '+str(mwna)+' NUM '+str(copy)+'\n'
                command += 'SEARch ENSEmble junk NUM '+str(copy)+'\n'
                if mw_mol > 150000:
                    command += 'RESOLUTION 6\n'
                else:
                    command += 'RESOLUTION 4\n'
                #Allow for some clashes if no solution was found before.
                if self.run_before:
                    command += 'PACK '+str(clash)+'\n'
                command += 'SPACEGROUP '+sg2+'\n'                
                command += 'RESCORE ROT ON\n'
                command += 'FINAL ROT STEP 1 SELECT PERCENT 75.0\n'
                command += 'FINAL ROT STEP 2 SELECT SIGMA 4.0\n'
                command += 'FINAL ROT SELECT NUM 1\n'
                command += 'RESCORE TRA ON\n'
                command += 'FINAL TRA STEP 1 SELECT PERCENT 75.0\n'
                command += 'FINAL TRA STEP 2 SELECT SIGMA 6.0\n'                
                command += 'FINAL TRA SELEct NUM 1\n'
                command += 'eof\n'
                file.writelines(command)
                file.close()
                command2 = 'tcsh phaser.com'
                self.phaser_log.append(command)            
                
                #Setup results for all running jobs.
                automr = {      'AutoMR nosol': 'Still running',
                                'AutoMR tar'  : 'None',
                                'AutoMR pdb'  : 'Still running',
                                'AutoMR mtz'  : 'Still running',
                                'AutoMR gain' : 'Still running',
                                'AutoMR rfz'  : 'Still running',
                                'AutoMR tfz'  : 'Still running',
                                'AutoMR clash': 'Still running',
                                'AutoMR dir'  : 'Still running',
                                'AutoMR sg'   : 'Still running',
                                'AutoMR adf'  : 'Still running',
                                'AutoMR peak' : 'Still running'        }
                self.phaser_results[sg2] = { 'AutoMR results' : automr }
                
                #Run command            
                if self.test:
                    #print command
                    pass
                else:               
                    if self.cluster_use:
                        self.phaser_jobs[Utils.processCluster(self,command2)] = sg2
                    else:
                        phaser_output[sg2] = multiprocessing.Queue()
                        self.PHASERPROCESS = multiprocessing.Process(target=multiPhaser(input=command, \
                                             output=phaser_output[sg2],logger=self.logger)).start()
                        self.phaser_jobs[(phaser_output[sg2]).get()] = sg2
                        
            if self.test:
                for sg in sg_name:
                    Utils.folders(self,'Phaser_'+sg)
                    self.postprocessPhaser(sg)
            else:
                self.Queue(self.phaser_jobs)
            #Check if solution has been found.
            if self.run_before == False:
                self.checkSolution()
                           
        except:
            self.logger.exception('**ERROR in AutoMolRep.processPhaser**')
        
    def postprocessPhaser(self,input):
        """
        Look at Phaser results.
        """
        self.logger.debug('AutoMolRep::postprocessPhaser')
        try:                
            if self.phaser_log == False:
                self.phaser_log = []
            log = []
            logfile = open('PHASER.sum','r')
            for line in logfile:
                log.append(line)
                self.phaser_log.append(line)
            logfile.close()
            data = Parse.ParseOutputPhaser(self,log)
            if data == None:
                self.phaser_results[input] = { 'AutoMR results'     : 'FAILED'}
                self.clean = False
                os.system('touch adf.com')
            else:
                self.phaser_results[input] = { 'AutoMR results' : data }
                if self.adf:
                    sg = self.phaser_results[input].get('AutoMR results').get('AutoMR sg')
                    if sg in ('No solution','Timed out','NA'):
                        self.phaser_results[input].get('AutoMR results')['AutoMR adf'] = 'None'
                        self.phaser_results[input].get('AutoMR results')['AutoMR peak'] = 'None'
                        os.system('touch adf.com')
                    else:
                        if self.test == False:
                            pid = Utils.calcADF(self,input)
                            return (pid)                             
                else:
                    self.phaser_results[input].get('AutoMR results')['AutoMR adf'] = 'None'
                    self.phaser_results[input].get('AutoMR results')['AutoMR peak'] = 'None'
                self.postprocess(False)
                                    
        except:
            self.logger.exception('**ERROR in AutoMolRep.postprocessPhaser**')
        
    def Queue(self,input):
        """
        queue system.
        """
        self.logger.debug('AutoMolRep::Queue')
        try:
            timed_out = False
            timer = 0
            pids = input.keys()
            if pids != ['None']:
                counter = len(pids)                
                while counter != 0:
                    for pid in pids:
                        if Utils.stillRunningCluster(self,pid):    
                            pass
                        elif Utils.stillRunning(self,pid):
                            pass
                        else:                            
                            self.logger.debug('Finished Phaser on '+ str(input[pid]))
                            Utils.folders(self,'Phaser_'+input[pid])
                            if self.adf:
                                if os.path.exists('adf.com'):
                                    pids.remove(pid)
                                    counter -= 1
                                else:
                                    sg = input.pop(pid)
                                    pids.remove(pid)
                                    p = self.postprocessPhaser(sg)
                                    pids.append(p)
                                    input[p]=sg
                            else:                                
                                self.postprocessPhaser(input[pid])
                                pids.remove(pid)
                                counter -= 1
                    time.sleep(1)
                    timer += 1
                    print 'Waiting for Phaser to finish ' + str(timer) + ' seconds'
                    if self.phaser_timer:
                        if timer >= self.phaser_timer:
                            timed_out = True        
                            break
                if timed_out:                   
                    self.logger.debug('Phaser timed out.')
                    print 'Phaser timed out.'
                    for pid in pids:
                        if self.cluster_use:
                            Utils.killChildrenCluster(self,pid)
                        else:
                            Utils.killChildren(self,pid)
                self.logger.debug('Phaser finished.')
        
        except:
            self.logger.exception('**ERROR in AutoMolRep.Queue**')
                      
    def checkSolution(self):
        """
        Check if solution is found. If not alter input and rerun.
        """
        self.logger.debug('AutoMolRep::checkSolution')
        try:
            solution = False
            for key in self.phaser_results.keys():
                sg = self.phaser_results[key].get('AutoMR results').get('AutoMR sg')
                if sg in ('No solution','Timed out','NA'):
                    pass
                else:
                    solution = True
            if solution == False:
                self.run_before = True
                self.processPhaser()
                
        except:
            self.logger.exception('**ERROR in AutoMolRep.checkSolution**')
        
    def postprocess(self,final=True):
        """
        Things to do after the main process runs
        1. Return the data through the pipe
        """
        self.logger.debug('AutoMolRep::postprocess')
        #Run summary files for each program to print to screen        
        output = {}
        failed = False
        if self.phaser_results:
            Summary.summaryCell(self,'phaser')
        self.htmlSummaryPhaser()
        try:
            if self.gui:
                sl = 'jon_summary_cell.php'
            else:
                sl = 'jon_summary_cell.html'
            cell_path = os.path.join(self.working_dir,sl)
            if os.path.exists(cell_path):
                output['Cell summary html']   = cell_path
            else:
                output['Cell summary html']   = 'None'                   
        except:
            self.logger.exception('**Could not update path of cell summary html file in AutoMolRep.postprocess.**')
            output['Cell summary html']   = 'FAILED'
                            
        try:
            pdb      = os.path.basename(self.input_pdb)
            for sg in self.phaser_results.keys():
                dir      = self.phaser_results[sg].get('AutoMR results').get('AutoMR dir')
                pdb_file = self.phaser_results[sg].get('AutoMR results').get('AutoMR pdb')                        
                mtz_file = self.phaser_results[sg].get('AutoMR results').get('AutoMR mtz')
                adf_file = self.phaser_results[sg].get('AutoMR results').get('AutoMR adf')
                peak_file = self.phaser_results[sg].get('AutoMR results').get('AutoMR peak')
                if dir in ('No solution','Timed out','NA','Still running'):
                    pass
                else:
                    tar = pdb[:-4]+'_'+sg+'.tar'
                    tar_path = os.path.join(self.working_dir,tar)
                    bz2tar = tar + '.bz2'
                    bz2tar_path = os.path.join(self.working_dir,bz2tar)
                    if os.path.exists(os.path.join(dir,pdb_file)):
                        tar1 = 'tar -C '+dir+' -cf '+tar_path+' '+pdb_file
                        os.system(tar1)
                    if os.path.exists(os.path.join(dir,mtz_file)):
                        tar2 = 'tar -C '+dir+' -rf '+tar_path+' '+mtz_file
                        os.system(tar2)
                    if os.path.exists(os.path.join(dir,'phaser.com')):
                        tar3 = 'tar -C '+dir+' -rf '+tar_path+' phaser.com'
                        os.system(tar3)
                    if os.path.exists(adf_file):
                        tar4 = 'tar -C '+os.path.dirname(adf_file)+' -rf '+tar_path+' '+os.path.basename(adf_file)
                        os.system(tar4)
                    if os.path.exists(peak_file):
                        tar5 = 'tar -C '+os.path.dirname(peak_file)+' -rf '+tar_path+' '+os.path.basename(peak_file)
                        os.system(tar5)   
                    if os.path.exists(tar_path):
                        bz2 = 'bzip2 -qf ' + tar_path
                        os.system(bz2)
                        if os.path.exists(bz2tar_path):
                            self.phaser_results[sg].get('AutoMR results').update({'AutoMR tar': bz2tar_path})
                        else:
                            self.phaser_results[sg].get('AutoMR results').update({'AutoMR tar': 'None'})
            self.cellAnalysis_results = { 'Cell analysis results': self.phaser_results }
        
        except:
            self.logger.exception('**Could not AutoMR results in AutoMolRep.postprocess.**')
            self.cellAnalysis_results = { 'Cell analysis results': 'FAILED'}
            self.clean = False
            failed = True
        
        try:
            self.output_files = {'Output files'   : output}            
        except:
            self.logger.exception('**Could not update the output dict in AutoMolRep.postprocess.**')       
        
        #Get proper status.
        if final:
            if failed:
                self.status['status'] = 'FAILED'
            else:
                self.status['status'] = 'SUCCESS'
        else:
            self.status['status'] = 'WORKING'
        
        #Put all the result dicts from all the programs run into one resultant dict and pass it back.       
        try:
            self.results = {}        
            if self.gui == False:
                if self.input[0] == "SAD":
                    self.input.remove("SAD")
                    self.input.insert(0,'MR')
            if self.status:
                self.results.update(self.status)            
            if self.cellAnalysis_results:
                self.results.update(self.cellAnalysis_results)
            if self.output_files:
                self.results.update(self.output_files)
            if self.gui:
                if self.results:
                    if len(self.input) == 6:
                        #Delete the previous Phaser results sent back.
                        del self.input[5]
                    self.input.append(self.results)            
                self.sendBack2(self.input)
        
        except:
            self.logger.exception('**Could not send results to pipe in AutoMolRep.postprocess.**')
        
        if final:
            try:
                #Cleanup my mess.
                if self.clean:
                    os.chdir(self.working_dir)
                    rm_folders2 = 'rm -rf Phaser_*'
                    self.logger.debug('Cleaning up Phaser files and folders')
                    self.logger.debug(rm_folders2)
                    os.system(rm_folders2)
                        
            except:
                self.logger.exception('**Could not cleanup in AutoMolRep.postprocess**')
            
            #Say job is complete.
            t = round(time.time()-self.st)
            self.logger.debug('-------------------------------------')
            self.logger.debug('RAPD AutoMolRep complete.')
            self.logger.debug('Total elapsed time: ' + str(t) + ' seconds')
            self.logger.debug('-------------------------------------')
            print '\n-------------------------------------'
            print 'RAPD AutoMolRep complete.'
            print 'Total elapsed time: ' + str(t) + ' seconds'
            print '-------------------------------------'        
            #sys.exit(0) #did not appear to end script with some programs continuing on for some reason.
            os._exit(0)
           
    def htmlSummaryPhaser(self):
        """
        Create HTML/php files for autoindex/strategy output results.
        """
        self.logger.debug('AutoMolRep::htmlSummaryPhaser')
        try:
            if self.gui:
                sl = 'jon_summary_cell.php'
            else:
                sl = 'jon_summary_cell.html'
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
            jon_summary.write("        $('#accordion').accordion({\n")
            jon_summary.write('           collapsible: true,\n')
            jon_summary.write('           active: false         });\n')
            if self.cell_summary:
                jon_summary.write("        $('#phaser-cell').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bSort": false,\n') 
                jon_summary.write('           "bAutoWidth": false    });\n')             
            if self.pdb_summary:
                jon_summary.write("        $('#phaser-pdb').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bSort": false,\n') 
                jon_summary.write('           "bAutoWidth": false    });\n')
                #Style the button
                jon_summary.write('        $("button").button(); \n')
            if self.tooltips:
                jon_summary.writelines(self.tooltips)
            jon_summary.write('                } );\n')
            jon_summary.write("    </script>\n\n\n")
            jon_summary.write(" </head>\n")
            jon_summary.write('  <body id="dt_example">\n')
            if self.cell_summary:
                jon_summary.writelines(self.cell_summary)
            if self.pdb_summary:
                jon_summary.writelines(self.pdb_summary)            
            if self.incompatible_cell:
                jon_summary.write('    <div id="container">\n')
                jon_summary.write('     <div class="full_width big">\n')
                jon_summary.write('      <div id="demo">\n')            
                jon_summary.write('    <h4 class="results">User input SG not compatible with unit cell. Using SG from data instead.</h4>\n')
                jon_summary.write("      </div>\n")
                jon_summary.write("      </div>\n")
                jon_summary.write("      </div>\n")       
            jon_summary.write('    <div id="container">\n')
            jon_summary.write('    <div class="full_width big">\n')
            jon_summary.write('      <div id="demo">\n')            
            jon_summary.write("      <h1 class='Results'>RAPD Logfile</h1>\n")
            jon_summary.write("     </div>\n")  
            jon_summary.write("     </div>\n")  
            jon_summary.write('      <div id="accordion">\n')
            jon_summary.write('        <h3><a href="#">Click to view log</a></h3>\n')
            jon_summary.write('          <div>\n')
            jon_summary.write('            <pre>\n')
            jon_summary.write('\n')
            if self.phaser_log:
                jon_summary.write('---------------Phaser RESULTS---------------\n')
                jon_summary.write('\n')            
                for line in self.phaser_log:
                    jon_summary.write('' + line )
            else:
                jon_summary.write('---------------Phaser FAILED---------------\n')         
            jon_summary.write('            </pre>\n')
            jon_summary.write('          </div>\n')           
            jon_summary.write("      </div>\n")
            jon_summary.write("    </div>\n")
            jon_summary.write("  </body>\n")
            jon_summary.write("</html>\n")
            jon_summary.close()        
            #copy html file to working dir
            shutil.copy(sl,self.working_dir)
            
        except:
            self.logger.exception('**ERROR in AutoMolRep.htmlSummaryPhaser**')
                           
    def PrintInfo(self):
        """
        Print information regarding programs utilized by RAPD
        """
        self.logger.debug('AutoMolRep::PrintInfo')
        try:
            print '\nRAPD now using Phenix and Phaser'
            print '======================='       
            print 'RAPD developed using Phenix'
            print 'Reference: Adams PD, et al.(2010) Acta Cryst. D66:213-221'
            print 'Website: http://www.phenix-online.org/ \n'        
            print 'RAPD developed using Phaser'
            print 'Reference: McCoy AJ, et al.(2007) J. Appl. Cryst. 40:658-674.'
            print 'Website: http://www.phenix-online.org/documentation/phaser.htm \n'
            self.logger.debug('RAPD now using Phenix and Phaser')
            self.logger.debug('=======================')
            self.logger.debug('RAPD developed using Phenix')            
            self.logger.debug('Reference: Adams PD, et al.(2010) Acta Cryst. D66:213-221')
            self.logger.debug('Website: http://www.phenix-online.org/ \n')
            self.logger.debug('RAPD developed using Phaser')
            self.logger.debug('Reference: McCoy AJ, et al.(2007) J. Appl. Cryst. 40:658-674.')
            self.logger.debug('Website: http://www.phenix-online.org/documentation/phaser.htm \n')
                        
        except:
            self.logger.exception('**Error in AutoMolRep.PrintInfo**')
  
def multiPhaser(input,output,logger):
    """
    Run Phaser.
    """
    logger.debug('multiPhaser')
    try:    
        file = open('phaser.log','w')
        myoutput = subprocess.Popen(input,shell=True,stdout=file,stderr=file)
        output.put(myoutput.pid)
        file.close()
    except:
        logger.exception('**Error in multiPhaser**')
        
if __name__ == '__main__':
    #start logging
    LOG_FILENAME = '/tmp/rapd_agent_mr.log'
    # Set up a specific logger with our desired output level
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=100000, backupCount=5)
    #add a formatter
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('AutoMolRep.__init__')
    import ../test_data/rapd_auto_testinput as Input
    input = Input.input()            
    #call the handler
    tmp = AutoMolRep(input,logger=logger)

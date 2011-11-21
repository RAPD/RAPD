'''
__author__ = "Jon Schuermann, Frank Murphy"
__copyright__ = "Copyright 2009,2010,2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2010/11/10"
'''

import multiprocessing
import os
import sys
import subprocess
import time
import shutil
import urllib2
import logging, logging.handlers

from rapd_communicate import Communicate
import rapd_agent_utilities as Utils
import rapd_agent_parse as Parse
import rapd_agent_summary as Summary

class PDBQuery(multiprocessing.Process,Communicate):
    def __init__(self,input,output0=None,output1=None,output2=None,logger=None):
        logger.info('PDBQuery.__init__')
        self.st = time.time()
        self.input                              = input
        self.logger                             = logger
        self.output0                            = output0
        self.output1                            = output1
        self.output2                            = output2
        
        #Input parameters
        self.percent                            = 0.02
        self.clean                              = True
        #Calc ADF for each solution (creates a lot of big map files)
        self.adf                                = False
        
        if self.input[0].has_key('cell'):
            self.cell2                              = self.input[0].get('cell')
        else:
            self.cell2                              = False       
        if self.input[0].has_key('dir'):
            self.working_dir                        = self.input[0].get('dir')
        else:
            self.working_dir                        = os.getcwd()
        if self.input[0].has_key('data'):
            self.datafile                           = self.input[0].get('data')
        else:
            self.datafile                           = False
        if self.input[0].has_key('test'):
            self.test                               = self.input[0].get('test')
        else:
            self.test                               = False
        if self.input[0].has_key('type'):
            self.sample_type                        = self.input[0].get('type')
        else:
            self.sample_type                        = 'Protein'
        if self.input[0].has_key('cluster'):    
            self.cluster_use                        = self.input[0].get('cluster')
        else:
            self.cluster_use                        = True
        if self.input[0].has_key('timer'):  
            self.pdbquery_timer                     = self.input[0].get('timer')
        else:
            self.pdbquery_timer                     = 20
        if self.input[0].has_key('sc'):    
            self.solvent_content                    = self.input[0].get('sc')
        else:
            self.solvent_content                    = 0.55
        if self.input[0].has_key('queue'):    
            self.queue                              = self.input[0].get('queue')
        else:
            self.queue                              = True
        if self.input[0].has_key('gui'):    
            self.gui                                = self.input[0].get('gui')
        else:
            self.gui                                = True
        if self.input[0].has_key('control'):    
            self.controller_address                 = self.input[0].get('control')
        else:
            self.controller_address                 = False
        if self.input[0].has_key('passback'):    
            self.passback                           = self.input[0].get('passback')
        else:
            self.passback                           = False    
                        
        self.cell_output                        = {}
        self.cell_output_results                = False
        self.cell_summary                       = False
        self.tooltips                           = False
        self.pdb_summary                        = False
        self.jobs_output                        = {}
        self.phaser_results                     = {}
        self.phaser_log                         = False
        self.phaser_timer                       = 900 #was 600 but too short for mackinnon (144,144,288,90,90,90)
        self.url                                = False
        self.pdbquery_finished                  = False        
        self.download_log                       = False        
        self.download_timer                     = 120
        self.status                             = {}
        
        multiprocessing.Process.__init__(self,name='PDBQuery')
        self.start()
        
    def run(self):
        """
        Convoluted path of modules to run.
        """
        self.logger.debug('PDBQuery::run')
        self.preprocess()        
        self.preprocessPDBCell()
        self.processDownloadPDB()
        if self.queue:
            if self.test:
                if self.cell_output.keys() != ['None']:
                    for line in self.cell_output.keys():
                        Utils.folders(self,'Phaser_'+line)
                        #self.processPhaser(line)
                        self.postprocessPhaser(line)
            else:
                self.Queue(self.jobs_output,False)
            self.postprocess()            
        else:
            if self.output2 != None:
                self.output2.put(self.jobs_output)           
        
    def preprocess(self):
        """
        Check input file and convert to mtz if neccessary.
        """
        self.logger.debug('PDBQuery::preprocess')
        try:
            self.PrintInfo()
            if self.datafile:
                file_type = self.datafile[-3:]
                if file_type == 'sca':
                    #Convert sca to mtz
                    Utils.sca2mtz(self)
                Utils.getInfoCellSG(self,self.datafile)
                """
                #Change timer to allow more time for Ribosome structures.
                Utils.checkVolume(self,Utils.calcVolume(self))
                if self.sample_type == 'Ribosome':
                    self.phaser_timer = 1200
                """
            if self.test:
                self.logger.debug('TEST IS SET "ON"')
                           
        except:
            self.logger.exception('**ERROR in PDBQuery.preprocess**')
            
    def preprocessPDBCell(self):
        """
        Try to get the unit cell info from the PDB up to 3 times.
        """
        self.logger.debug('PDBQuery::processPDBCell')
        try:        
            counter = 0
            while counter < 3:
                self.processPDBCell()
                timer = 0
                timeout = False
                while self.pdbquery_finished == False:
                    print 'Waiting for results from pdb.org '+ str(timer)+' seconds'
                    time.sleep(1)
                    timer += 1
                    if timer > self.pdbquery_timer:
                        self.logger.debug('Timed out waiting for PDBQuery.')
                        counter +=1
                        timeout = True
                        break
                if timeout == False:
                    break
            if self.output0 != None:
                self.output0.put(self.percent)                
            if self.queue:
                pass
            else:
                if self.cell_output == {}:
                    self.cell_output['None']= 'None'                
                if self.output1 != None:
                    self.output1.put(self.cell_output)
        
        except:
            self.logger.exception('**ERROR in PDBQuery.processPDBCell**')
            if self.queue == False:
                self.cell_output = {}
                self.cell_output['None']= 'None'
                if self.output1 != None:
                    self.output1.put(self.cell_output) 
        
    def processDownloadPDB(self):
        """
        Download and get info from pdb.
        """
        self.logger.debug('PDBQuery::processDownloadPDB')
        try:
            if self.download_log == False:
                self.download_log = []
            pdbs = self.cell_output.keys()
            download_jobs = {}
            if pdbs != ['None']:       
                if self.datafile:
                    for line in pdbs:
                        Utils.folders(self,'Phaser_'+line)
                        if self.test:
                            print 'Not downloading PDB file'                        
                        else:                           
                            if self.cluster_use:
                                download_jobs[Utils.downloadPDB(self,line)] = line
                            else:
                                Utils.downloadPDB(self,line)                                
                                self.processPhaser(line)
                    if self.cluster_use:
                        self.Queue(download_jobs,True)            
                else:
                    self.jobs_output['None'] = 'None'
            else:
                self.jobs_output['None'] = 'None'
                
        except:
            self.logger.exception('**ERROR in PDBQuery.processDownloadPDB**')
           
    def processPhaser(self,input):
        """
        Start Phaser for input pdb.
        """
        self.logger.debug('PDBQuery::processPhaser')
        try:
            pdb = input
            if self.phaser_log == False:
                self.phaser_log = []            
            file = pdb+'.pdb'
            pdbfile = open(file,'r')
            for crys in pdbfile:
                if crys.startswith('CRYST1'):
                    sg = Utils.fixSG(self,crys[55:67].upper().replace(' ',''))
            pdbfile.close()
            info = Utils.getPDBmw(self,file)
            mw   = info['MW']
            mwaa = info['MWaa']
            mwna = info['MWna']
            """
            #Allow up to 10% clashes
            res_in = info['NRes']
            clash = int(round(0.1*res_in))
            if clash > 50:
                clash = 50
            """
            command = 'phaser << eof\n'
            command += 'TITLe junk\n'
            command += 'MODE MR_AUTO\n'
            command += 'HKLIn '+self.datafile+'\n'
            command += 'LABIn F=F SIGF=SIGF\n'
            command += 'ENSEmble junk PDB '+file+' IDENtity 80\n'
            #command += 'COMPosition ENSEmble junk FRACtional 1.0\n' #Was confused if RNA was not recognized and gave neg ll-gain.
            if mwaa > 0:
                command += 'COMPosition PROTein MW '+str(mwaa)+'\n'
            if mwna > 0:
                command += 'COMPosition NUCLEIC MW '+str(mwna)+'\n'
            command += 'SEARch ENSEmble junk NUM 1\n'
            #May extend time too long
            #command += 'PACK '+str(clash)+'\n'
            if mw > 500000:
                command += 'RESOLUTION 6\n'
                #Set Phaser timer longer
                self.phaser_timer = 1500
            else:
                command += 'RESOLUTION 4\n'
            command += 'SPACEGROUP '+sg+'\n'
            command += 'RESCORE ROT ON\n'
            command += 'FINAL ROT STEP 1 SELECT PERCENT 75.0\n'
            command += 'FINAL ROT STEP 2 SELECT SIGMA 4.0\n'
            command += 'FINAL ROT SELECT NUM 1\n'
            command += 'RESCORE TRA ON\n'
            command += 'FINAL TRA STEP 1 SELECT PERCENT 75.0\n'
            command += 'FINAL TRA STEP 2 SELECT SIGMA 6.0\n'
            command += 'FINAL TRA SELEct NUM 1\n'
            command += 'eof\n'
            file2 = open('phaser.com','w')
            file2.writelines(command)
            file2.close()
            command2 = 'tcsh phaser.com'
            #self.logger.debug(command2)
            self.phaser_log.append(command2)
            if self.test:
                print command2
            else:                           
                if self.cluster_use:
                    self.jobs_output[Utils.processCluster(self,command2)] = pdb
                else:                            
                    phaser_output = {}
                    phaser_output[pdb] = multiprocessing.Queue()
                    self.PHASERPROCESS = multiprocessing.Process(target=multiPhaser(input=command2, \
                                         output=phaser_output[pdb], logger=self.logger)).start()
                    self.jobs_output[(phaser_output[pdb]).get()] = pdb
                    
        except:
            self.logger.exception('**ERROR in PDBQuery.processPhaser**')

    def processPDBCell(self):
        """
        Check if cell is found in PDB.
        """        
        self.logger.debug('PDBQuery::processPDBCell')
        try:
            counter = 0
            url = 'http://www.rcsb.org/pdb/rest/search'
            finished = False
            junk = []
            while counter < 3:
                input = []
                for line in self.cell2:
                    f = float(line)
                    diff = f*self.percent
                    input.append(f-diff)
                    input.append(f+diff)       
                querycell  = '<?xml version="1.0" encoding="UTF-8"?>'
                querycell += '<orgPdbQuery>'        
                querycell += '<queryType>org.pdb.query.simple.XrayCellQuery</queryType>'                
                querycell += '<cell.length_a.comparator>between</cell.length_a.comparator>'
                querycell += '<cell.length_a.min>'+str(input[0])+'</cell.length_a.min>'
                querycell += '<cell.length_a.max>'+str(input[1])+'</cell.length_a.max>'
                querycell += '<cell.length_b.comparator>between</cell.length_b.comparator>'
                querycell += '<cell.length_b.min>'+str(input[2])+'</cell.length_b.min>'
                querycell += '<cell.length_b.max>'+str(input[3])+'</cell.length_b.max>'
                querycell += '<cell.length_c.comparator>between</cell.length_c.comparator>'
                querycell += '<cell.length_c.min>'+str(input[4])+'</cell.length_c.min>'
                querycell += '<cell.length_c.max>'+str(input[5])+'</cell.length_c.max>'
                querycell += '<cell.angle_alpha.comparator>between</cell.angle_alpha.comparator>'
                querycell += '<cell.angle_alpha.min>'+str(input[6])+'</cell.angle_alpha.min>'
                querycell += '<cell.angle_alpha.max>'+str(input[7])+'</cell.angle_alpha.max>'
                querycell += '<cell.angle_beta.comparator>between</cell.angle_beta.comparator>'
                querycell += '<cell.angle_beta.min>'+str(input[8])+'</cell.angle_beta.min>'
                querycell += '<cell.angle_beta.max>'+str(input[9])+'</cell.angle_beta.max>'
                querycell += '<cell.angle_gamma.comparator>between</cell.angle_gamma.comparator>'
                querycell += '<cell.angle_gamma.min>'+str(input[10])+'</cell.angle_gamma.min>'
                querycell += '<cell.angle_gamma.max>'+str(input[11])+'</cell.angle_gamma.max>'
                querycell += '</orgPdbQuery>'
                self.logger.debug("Checking the PDB...")
                out = urllib2.urlopen(urllib2.Request(url,data=querycell)).read().split()
                if len(out[-1]) > 4:
                    result = out[:-1]
                else:
                    result = out
                if self.cluster_use:
                    junk.extend(result[0:9])
                else:
                    junk.extend(result[0:4])
                #Look for repeats and remove them.
                for line in junk:
                    if len(line) > 4:
                        junk.remove(line)
                    else:
                        cnt = junk.count(line)
                        if cnt != 1:            
                            junk.remove(line)
                if counter >= 2:
                    if len(junk) > 0:
                        finished = True
                    break                       
                else:
                    if self.cluster_use:
                        i = 5
                    else:
                        i = 2
                    if len(junk) < i:
                        counter += 1
                        self.percent += 0.01
                        self.logger.debug("Not enough PDB results. Going for more...")
                    else:
                        finished = True
                        break
                
            if finished:
                self.processGetInfo(junk)
            else:
                self.cell_output['None'] = 'None'
                self.logger.debug('Failed to find pdb with similar cell.')
            self.pdbquery_finished = True
                        
        except:
            self.logger.exception('**ERROR in PDBQuery.processPDBCell**')
        
    def processGetInfo(self,input):
        """
        Get PDB info for pdbIDs.
        """
        self.logger.debug('PDBQuery::getInfo')
        try:
            url = 'http://www.pdb.org/pdb/rest/describeMol?structureId='
            for pdb in input:
                temp = url+pdb
                req = urllib2.Request(temp)        
                f = urllib2.urlopen(req)
                result = f.readlines()
                temp2 = []
                temp3 = []
                if result:
                    for line in result:
                        temp2.append(line.strip())
                    for line in temp2:
                        if line.startswith('<polymerDescription description'):
                            temp3.append(line[33:-4])
                    self.cell_output[pdb] = {'Name' : temp3 }
                else:
                    self.logger.debug("Failed to retrieve results")
                    self.cell_output['None'] = 'None'
            self.pdbquery_finished = True
            
        except:
            self.logger.exception('**ERROR in PDBQuery.getInfo**')
        
    def postprocessPhaser(self,input):
        """
        Look at Phaser results.
        """
        self.logger.debug('PDBQuery::postprocessPhaser')
        try:                
            if self.phaser_log == False:
                self.phaser_log = []            
            log = []
            if os.path.exists('PHASER.sum'):
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
                            pid = Utils.calcADF(self,input)
                            return (pid)                             
                    else:
                        self.phaser_results[input].get('AutoMR results')['AutoMR adf'] = 'None'
                        self.phaser_results[input].get('AutoMR results')['AutoMR peak'] = 'None'
                                    
        except:
            self.logger.exception('**ERROR in PDBQuery.postprocessPhaser**')
        
    def Queue(self,input,download=False):
        """
        queue system.
        """
        self.logger.debug('PDBQuery::Queue')
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
                            Utils.folders(self,'Phaser_'+input[pid])
                            if download:
                                self.logger.debug('Finished downloading '+str(input[pid]))
                                self.processPhaser(input[pid])
                                pids.remove(pid)
                                counter -= 1
                            else:
                                self.logger.debug('Finished Phaser on '+str(input[pid]))
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
                    if download:
                        print 'Waiting for PDBQuery.download to finish ' + str(timer) + ' seconds'
                        if self.download_timer:
                            if timer >= self.download_timer:
                                timed_out = True        
                                break                    
                    else:
                        print 'Waiting for PDBQuery.Phaser to finish ' + str(timer) + ' seconds'
                        if self.phaser_timer:
                            if timer >= self.phaser_timer:
                                timed_out = True        
                                break                    
                if timed_out:
                    if download:
                        if timer:
                            self.logger.debug('PDBQuery.Download timed out after '+str(timer)+' seconds')
                        else:
                            self.logger.debug('PDBQuery.Download timed out.')
                        print 'PDBQuery.Download timed out.'
                    else:
                        if timer:
                            self.logger.debug('PDBQuery.Phaser timed out after '+str(timer)+' seconds')
                        else:
                            self.logger.debug('PDBQuery.Phaser timed out.')
                        print 'PDBQuery.Phaser timed out.'
                    for pid in pids:
                        if self.cluster_use:
                            Utils.killChildrenCluster(self,pid)
                        else:
                            Utils.killChildren(self,pid)
            if download:
                self.logger.debug('PDBQuery.Queue finished download.')
            else:
                self.logger.debug('PDBQuery.Queue finished Phaser.')    
        
        except:
            self.logger.exception('**ERROR in PDBQuery.Queue**')
        
    def PrintInfo(self):
        """
        Print information regarding programs utilized by RAPD
        """
        self.logger.debug('PDBQuery::PrintInfo')
        try:
            print '\nRAPD now using Phenix'
            print '======================='
            print 'RAPD developed using Phenix'
            print 'Reference: Adams PD, et al.(2010) Acta Cryst. D66:213-221'
            print 'Website: http://www.phenix-online.org/ \n'
            print 'RAPD developed using Phaser'
            print 'Reference: McCoy AJ, et al.(2007) J. Appl. Cryst. 40:658-674.'
            print 'Website: http://www.phenix-online.org/documentation/phaser.htm \n'
            self.logger.debug('RAPD now using Phenix')
            self.logger.debug('=======================')
            self.logger.debug('RAPD developed using Phenix')
            self.logger.debug('Reference: Adams PD, et al.(2010) Acta Cryst. D66:213-221')
            self.logger.debug('Website: http://www.phenix-online.org/ \n')
            self.logger.debug('RAPD developed using Phaser')
            self.logger.debug('Reference: McCoy AJ, et al.(2007) J. Appl. Cryst. 40:658-674.')
            self.logger.debug('Website: http://www.phenix-online.org/documentation/phaser.htm \n')
                        
        except:
            self.logger.exception('**Error in PDBQuery.PrintInfo**')
    
    def postprocess(self):
        """
        Put everything together and send back dict.
        """
        self.logger.debug('PDBQuery::postprocess')
        #Run summary files for each program to print to screen        
        output = {}        
        failed = False
        #Add tar infor to automr results and take care of issue if no SCA file was input.
        try:
            if self.cell_output:
                pdbs = self.cell_output.keys()
                if pdbs != ['None']:
                    for pdb in pdbs:
                        if self.jobs_output.keys() != ['None']:
                            if self.phaser_results.has_key(pdb):
                                dir      = self.phaser_results[pdb].get('AutoMR results').get('AutoMR dir')
                                pdb_file = self.phaser_results[pdb].get('AutoMR results').get('AutoMR pdb')
                                mtz_file = self.phaser_results[pdb].get('AutoMR results').get('AutoMR mtz')
                                adf_file = self.phaser_results[pdb].get('AutoMR results').get('AutoMR adf')
                                peak_file = self.phaser_results[pdb].get('AutoMR results').get('AutoMR peak')
                                pdb_path = os.path.join(dir,pdb_file)
                                mtz_path = os.path.join(dir,mtz_file)
                                if dir in ('No solution','Timed out','NA','Still running'):
                                    pass
                                else:
                                    tar = pdb+'.tar'
                                    tar_path = os.path.join(self.working_dir,tar)
                                    bz2tar = tar + '.bz2'
                                    bz2tar_path = os.path.join(self.working_dir,bz2tar)                        
                                    if os.path.exists(pdb_path):
                                        tar1 = 'tar -C '+dir+' -cf '+tar_path+' '+pdb_file
                                        os.system(tar1)
                                    if os.path.exists(mtz_path):
                                        tar2 = 'tar -C '+dir+' -rf '+tar_path+' '+mtz_file
                                        os.system(tar2)                           
                                    if os.path.exists(adf_file):
                                        tar3 = 'tar -C '+os.path.dirname(adf_file)+' -rf '+tar_path+' '+os.path.basename(adf_file)
                                        os.system(tar3)
                                    if os.path.exists(peak_file):
                                        tar4 = 'tar -C '+os.path.dirname(peak_file)+' -rf '+tar_path+' '+os.path.basename(peak_file)
                                        os.system(tar4)   
                                    if os.path.exists(tar_path):
                                        bz2 = 'bzip2 -qf ' + tar_path
                                        os.system(bz2)
                                        if os.path.exists(bz2tar_path):
                                            self.phaser_results[pdb].get('AutoMR results').update({'AutoMR tar': bz2tar_path})
                                        else:
                                            self.phaser_results[pdb].get('AutoMR results').update({'AutoMR tar': 'None'})                        
                                #self.cell_output[pdb].update(self.phaser_results[pdb])                            
                            else:
                                self.phaser_results[pdb] = {'AutoMR results' : Parse.setPhaserFailed()}                                
                        else:
                            self.phaser_results[pdb] = {'AutoMR results' : Parse.setPhaserFailed()}                            
                        self.cell_output[pdb].update(self.phaser_results[pdb])        
                    self.cell_output_results = { 'Cell analysis results': self.cell_output }
                else:
                    self.cell_output_results = { 'Cell analysis results': 'None' }  
            else:
                self.cell_output_results = { 'Cell analysis results': 'None' }
            
        except:
            self.logger.exception('**Could not AutoMR results in postprocess.**')
            self.cell_output_results = { 'Cell analysis results': 'FAILED'}
            failed = True
        
        os.chdir(self.working_dir)        
        if self.cell_output:
            #self.summaryCell()
            Summary.summaryCell(self,'pdbquery')
        self.htmlSummary()
       
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
            self.logger.exception('**Could not update path of shelx summary html file.**')
            output['Cell summary html']   = 'FAILED'
            failed = True
                
        try:
            self.output_files = {'Output files'   : output}            
        except:
            self.logger.exception('**Could not update the output dict.**')
        
        #Get proper status.
        if failed:
            self.status['status'] = 'FAILED'
        else:
            self.status['status'] = 'SUCCESS'
        
        #Put all the result dicts from all the programs run into one resultant dict and pass it along the pipe.
        try:
            self.results = {}
            if self.status:
                self.results.update(self.status)
            if self.cell_output_results:
                self.results.update(self.cell_output_results)
            if self.output_files:
                self.results.update(self.output_files)
            if self.results:
                self.input.append(self.results)
            #Utils.pp(self,self.results)
            if self.passback:
                if self.output1 != None:
                    self.output1.put(self.results)
            else:
                if self.gui:
                    self.sendBack2(self.input)
        
        except:
            self.logger.exception('**Could not send results to pipe.**')
        
        try:
            #Cleanup my mess.
            if self.clean:
                #os.chdir(self.working_dir)
                rm_folders2 = 'rm -rf Phaser_*'
                self.logger.debug('Cleaning up AutoMR files and folders')
                self.logger.debug(rm_folders2)
                os.system(rm_folders2)                                  
        except:
            self.logger.exception('**Could not cleanup**')
        
        #Say job is complete.
        t = round(time.time()-self.st)
        self.logger.debug('-------------------------------------')
        self.logger.debug('RAPD PDBQuery complete.')
        self.logger.debug('Total elapsed time: ' + str(t) + ' seconds')
        self.logger.debug('-------------------------------------')
        print '\n-------------------------------------'
        print 'RAPD PDBQuery complete.'
        print 'Total elapsed time: ' + str(t) + ' seconds'
        print '-------------------------------------'        
        #sys.exit(0) #did not appear to end script with some programs continuing on for some reason.
        os._exit(0)
        
    def htmlSummary(self):
        """
        Create HTML/php files for autoindex/strategy output results.
        """
        self.logger.debug('PDBQuery::htmlSummary')
        try:
            if self.gui:
                jon_summary = open('jon_summary_cell.php','w')    
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
            else:
                jon_summary = open('jon_summary_cell.html','w')           
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
            jon_summary.write('    tr.GradeD {font-weight: bold;}\n')
            jon_summary.write('    </style>\n')
            if self.gui == False:    
                jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.js"></script>\n')
                jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.dataTables.js"></script>\n')
                jon_summary.write('    <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js" type="text/javascript"></script>\n')
            jon_summary.write('    <script type="text/javascript" charset="utf-8">\n')
            jon_summary.write('      $(document).ready(function() {\n')
            jon_summary.write("        $('button').button(); \n")
            jon_summary.write("        $('#accordion-cell').accordion({\n")
            jon_summary.write('           collapsible: true,\n')
            jon_summary.write('           active: false         });\n')
            if self.cell_summary:
                jon_summary.write("        $('#pdbquery-cell').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bSort": false,\n') 
                jon_summary.write('           "bAutoWidth": false    });\n')             
            if self.pdb_summary:
                jon_summary.write("        $('#pdbquery-pdb').dataTable({\n")
                jon_summary.write('           "bPaginate": false,\n')
                jon_summary.write('           "bFilter": false,\n')
                jon_summary.write('           "bInfo": false,\n')
                jon_summary.write('           "bSort": false,\n') 
                jon_summary.write('           "bAutoWidth": false    });\n')
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
            jon_summary.write('    <div id="container">\n')
            jon_summary.write('    <div class="full_width big">\n')
            jon_summary.write('      <div id="demo">\n')            
            jon_summary.write("      <h1 class='Results'>RAPD Logfile</h1>\n")
            jon_summary.write("     </div>\n")  
            jon_summary.write("     </div>\n")  
            jon_summary.write('      <div id="accordion-cell">\n')
            jon_summary.write('        <h3><a href="#">Click to view log of top solution</a></h3>\n')
            jon_summary.write('          <div>\n')
            jon_summary.write('            <pre>\n')
            jon_summary.write('\n')
            jon_summary.write('---------------Phaser RESULTS---------------\n')
            jon_summary.write('\n')            
            jon_summary.write('---------------Phaser Too long---------------\n')
            """
            if self.phaser_log:
                for line in self.phaser_log:
                    jon_summary.write('' + line )            
            else:
                jon_summary.write('---------------Phaser FAILED---------------\n')         
            """
            jon_summary.write('            </pre>\n')
            jon_summary.write('          </div>\n')           
            jon_summary.write("      </div>\n")
            jon_summary.write("    </div>\n")
            jon_summary.write("  </body>\n")
            jon_summary.write("</html>\n")
            jon_summary.close()        
        
        except:
            self.logger.exception('**ERROR in PDBQuery.htmlSummary**')
  
def multiPhaser(input, output, logger):
    """
    Run Phaser.
    """
    logger.debug('PDBQuery.multiPhaser')
    try:    
        file = open('phaser.log','w')
        myoutput = subprocess.Popen(input,shell=True,stdout=file,stderr=file)    
        output.put(myoutput.pid)
        file.close()            
    except:
        logger.exception('**Error in PDBQuery.multiPhaser**')

if __name__ == '__main__':
    #start logging
    LOG_FILENAME = '/tmp/rapd_agent_cell.log'
    # Set up a specific logger with our desired output level
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=100000, backupCount=5)
    #add a formatter
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('PDBQuery.__init__')
    output0 = None
    output1 = None
    output2 = None    
    #construct test input
    input = [{#'cell': ['67.875', '67.875', '102.148', '90.000', '90.000', '90.000'],
              'cell': ['91.24', '128.19', '65.78', '90.00', '90.00', '90.00'],
              'dir' :  '/tmp/Output',
              'data': '../test_data/129i15_b_free.mtz',
              #'sc': '0.55',
              #'timer': 15,
              'cluster': True,
              'test': False,
              #'type': 'Protein',
              #'queue': True,
              'gui'  : False,
              'control': ('000.000.000.000',50001),
              #'passback': True,
              'process_id': 11111,                        
              }]
    T = PDBQuery(input,output0,output1,output2,logger=logger)

'''
__author__ = "Jon Schuermann, Frank Murphy"
__copyright__ = "Copyright 2009,2010,2011 Cornell University"
__credits__ = ["Jon Schuermann","Frank Murphy","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Claue"
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

class RunStac(multiprocessing.Process, Communicate):
    def __init__(self,input,params,logger=None):
        logger.info('RunStac.__init__')
        self.st = time.time()
        self.input                              = input        
        self.logger                             = logger
        self.params                             = params
        #Setting up data input
        self.setup                              = self.input[1]
        self.header                             = self.input[2]
        self.header2                            = False
        if self.input[3].has_key('distance'):
            self.header2                            = self.input[3]
            self.preferences                        = self.input[4]
        else:
            self.preferences                        = self.input[3]
        
        self.controller_address                 = self.input[-1]
        #setup variables sent in as params.
        if self.params.has_key('dir'):
            self.working_dir = self.params.get('dir')
        else:
            self.working_dir = self.setup.get('work')
        if self.params.has_key('test'):
            self.test = self.params.get('test')
        else:
            self.test = False            
        if self.params.has_key('gui'):
            self.gui = self.params.get('gui')
        else:
            self.gui = True
        if self.params.has_key('stac_timer'):
            self.stac_timer = self.params.get('stac_timer')
        else:
            self.stac_timer = 120
        if self.params.has_key('clean'):
            self.clean = self.params.get('clean')
        else:
            self.clean = True
        #self.clean = False
        #Turn on Ravelli strategy calculation for each alignment (time consuming and not really informative)
        self.stac_strat                         = False
        #Turn on translation if calibrated (NOT CALIBRATED)        
        self.stac_trans                         = False
        
        self.auto1_summary                      = False
        self.stacalign_log                      = False 
        self.stacstrat_log                      = False
        self.stac_align_summary                 = False
        self.stac_strat_summary                 = False        
        self.stac_failed                        = False
        self.align                              = False
        self.output_files                       = False
        self.results                            = False
        multiprocessing.Process.__init__(self,name='RunStac')
        self.start()
        
    def run(self):
        """
        Convoluted path of modules to run.
        """
        self.logger.debug('RunStac::run')
        self.preprocess()
        self.processSTACAlign()
        self.postprocessSTACAlign()                        
        if self.stac_strat:
            self.convertStacAlignxml_stratxml()
            self.processSTACStrat()
            self.postprocessSTACStrat()        
        self.postprocess()
            
    def preprocess(self):
        """
        Things to do before the main process runs
        1. Change to the correct directory
        2. Print out the reference for STAC pipeline
        """       
        self.logger.debug('RunStac::preprocess')
        #change directory to the one specified in the incoming dict
        if os.path.exists(self.working_dir) == False:
            os.makedirs(self.working_dir)
        os.chdir(self.working_dir)
        #print out recognition of the program being used
        self.PrintInfo()
        
    def processSTACAlign(self):
        """
        Perform a STAC alignment.
        """
        self.logger.debug('RunStac::processSTACAlign')                                       
        try:              
            if self.header2:        
                omega = str(self.header2.get('phi'))
                kappa = str(self.header2.get('mk3_kappa'))
                phi   = str(self.header2.get('mk3_phi'))
                file1 = str(self.header2.get('STAC file1'))
                file2 = str(self.header2.get('STAC file2'))            
                self.align = str(self.header2.get('axis_align'))                
            else:
                omega = str(self.header.get('phi'))
                kappa = str(self.header.get('mk3_kappa'))
                phi   = str(self.header.get('mk3_phi'))
                file1 = str(self.header.get('STAC file1'))
                file2 = str(self.header.get('STAC file2'))           
                self.align = str(self.header.get('axis_align'))
        
        except:
            self.logger.exception('ERROR in stac.processSTACAlign**')
            
        if self.gui:
            try:    
                shutil.copy(file1,self.working_dir)
                shutil.copy(file2,self.working_dir)
            except:
                self.logger.exception('Cannot copy STAC files into working directory.')
                self.stac_failed = True
                self.postprocess()
        
        try:         
            junk = open('DNA_STAC_Kappa_Settings','w')
            junk.write("<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?><kappa_collect_settings><motorSettings><motorName>Omega</motorName><motorValue>%7s</motorValue></motorSettings><motorSettings><motorName>Kappa</motorName><motorValue>%7s</motorValue></motorSettings><motorSettings><motorName>Phi</motorName><motorValue>%7s</motorValue></motorSettings><motorSettings><motorName>X</motorName><motorValue>0.261444</motorValue></motorSettings><motorSettings><motorName>Y</motorName><motorValue>-0.085559</motorValue></motorSettings><motorSettings><motorName>Z</motorName><motorValue>0.659333</motorValue></motorSettings><comment>BCM query performed by STAC</comment></kappa_collect_settings>" % (omega, kappa, phi))            
            junk.close()
            #stac  = 'export STACDIR=/gpfs1/users/necat/rapd/programs/STAC/v201105200256 \n'
            stac  = 'export STACDIR=/gpfs1/users/necat/rapd/programs/STAC/v201111051332 \n'
            stac += 'export BCMDEF=$STACDIR/config/BCM_24IDC.dat\n'
            stac += 'export RUNDIR='+os.getcwd()+'/\n'
            stac += 'export stacjars="$STACDIR/STAC.jar $STACDIR/plugins/ $STACDIR/src/"\n'
            stac += 'export stacjars="`ls $STACDIR/thirdparty/jars/*.jar` $stacjars"\n'
            stac += 'export stacjars="$STACDIR/thirdparty/EpicsClient/linux-x86/jca2.1.2/jca.jar $stacjars"\n'
            stac += 'export stacjars="$STACDIR/thirdparty/TangoClient/TangORB-5.1.0.jar $STACDIR/thirdparty/TangoClient/jive-5.0.1.jar $stacjars"\n'
            stac += 'export stacjars="$STACDIR/thirdparty/TineClient/tine.jar $stacjars"\n'
            stac += 'export stacjars="$STACDIR/thirdparty/xj3dm10/jars/linux.jar $STACDIR/thirdparty/xj3dm10/jars/dom4j.jar $STACDIR/thirdparty/xj3dm10/jars/HIDWrapper $STACDIR/thirdparty/xj3dm10/jars/vecmath.jar $STACDIR/thirdparty/xj3dm10/jars/gt2-main.jar $STACDIR/thirdparty/xj3dm10/jars/opengis.jar $STACDIR/thirdparty/xj3dm10/jars/units-0.01.jar $STACDIR/thirdparty/xj3dm10/jars/aviatrix3d-all.jar $STACDIR/thirdparty/xj3dm10/jars/dis.jar $STACDIR/thirdparty/xj3dm10/jars/gnu-regexp-1.0.8.jar $STACDIR/thirdparty/xj3dm10/jars/httpclient.jar $STACDIR/thirdparty/xj3dm10/jars/j3d-org-images.jar $STACDIR/thirdparty/xj3dm10/jars/j3d-org.jar $STACDIR/thirdparty/xj3dm10/jars/jinput.jar $STACDIR/thirdparty/xj3dm10/jars/jogl.jar $STACDIR/thirdparty/xj3dm10/jars/joal.jar $STACDIR/thirdparty/xj3dm10/jars/js.jar $STACDIR/thirdparty/xj3dm10/jars/dxinput.jar $STACDIR/thirdparty/xj3dm10/jars/jutils.jar $STACDIR/thirdparty/xj3dm10/jars/odejava.jar $STACDIR/thirdparty/xj3dm10/jars/uri.jar $STACDIR/thirdparty/xj3dm10/jars/vlc_uri.jar $stacjars"\n'
            stac += 'export stacjars="$STACDIR/thirdparty/xj3dm10/jars/xj3d-common.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-core.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-eai.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-ecmascript.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-external-sai.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-j3d.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-java-sai.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-jaxp.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-jsai.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-net.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-norender.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-ogl.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-parser.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-render.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-runtime.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-sai.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-sav.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-script-base.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-xml-util.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-images.jar $STACDIR/thirdparty/xj3dm10/jars/xj3d-xml.jar $STACDIR/thirdparty/xj3dm10/jars/log4j.jar $stacjars"\n'
            stac += 'for stacjar in $stacjars; do\n'
            stac += '    if [ -r $stacjar ]; then\n'
            stac += '      if [ -z $CLASSPATH ]; then\n'
            stac += '        export CLASSPATH=$stacjar\n'
            stac += '      else\n'
            stac += '        export CLASSPATH=$stacjar:$CLASSPATH\n'
            stac += '      fi\n'
            stac += '    fi\n'
            stac += 'done\n'
            stac += 'if [ -z $LD_LIBRARY_PATH ]; then\n'
            stac += '    export LD_LIBRARY_PATH=$STACDIR/thirdparty/EpicsClient/linux-x86/jca2.1.2/linux-x86/\n'
            stac += 'else\n'
            stac += '    export LD_LIBRARY_PATH=$STACDIR/thirdparty/EpicsClient/linux-x86/jca2.1.2/linux-x86/:$LD_LIBRARY_PATH\n'
            stac += 'fi\n'
            stac += 'export STAC_PARAMETERS=" -DSTACDIR="$STACDIR" -DBCMDEF="$BCMDEF\n'
            stac += 'export DNAKAPPA=IS_ALREADY_SETUP\n'
            stac += 'echo "BCMDEF  =" $BCMDEF\n'
            stac += 'echo "STACPARAMS    ="$STAC_PARAMETERS\n'
            stac += 'echo "DNAKAPPA      ="$DNAKAPPA\n'
            stac += 'par=stac.core.STAC_DNA_listener\n'
            stac += 'options=kappa_alignment\n'
            stac += 'workDir=$RUNDIR\n'
            stac += 'cd $RUNDIR\n'
            stac += 'java -DBCMDEF=$BCMDEF -DSPECDEF=$SPECDEF -DGNSDEF=$GNSDEF -DSTACDIR=$STACDIR -DSTAC_DEF_MOS_SETT=$STAC_DEF_MOS_SETT -DSTAC_DEF_MOS_MAT=$STAC_DEF_MOS_MAT -DSTAC_DEF_HKL=$STAC_DEF_HKL -DSTAC_DEF_XDS=$STAC_DEF_XDS $par $options $workDir $options2\n'            
            input = open('stac.com','w')
            input.writelines(stac)
            input.close()
            if self.align in ('smart','anom','multi'):
                self.editSTACfile()
            else:
                file = open('DNA_kappa_alignment_request','w')
                if self.align == 'all':
                    file.write("<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?><kappa_alignment_request><desired_orientation><v1>a*</v1><v2>b*</v2><close>true</close><comment></comment></desired_orientation><desired_orientation><v1>a*</v1><v2>c*</v2><close>true</close><comment></comment></desired_orientation><desired_orientation><v1>b*</v1><v2>a*</v2><close>true</close><comment></comment></desired_orientation><desired_orientation><v1>b*</v1><v2>c*</v2><close>true</close><comment></comment></desired_orientation><desired_orientation><v1>c*</v1><v2>a*</v2><close>true</close><comment></comment></desired_orientation><desired_orientation><v1>c*</v1><v2>b*</v2><close>true</close><comment></comment></desired_orientation><comment>First test parameter passed</comment></kappa_alignment_request>")        
                else:        
                    file.write("<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?><kappa_alignment_request>")                
                    temp = []               
                    if self.align == 'long':
                        cell = Utils.getLabelitCell(self).split()[:3]
                        for line in cell:
                            temp.append(float(line))
                        m = max(temp)
                        counter = 0
                        for x in range(len(cell)):
                            if cell[x].startswith(str(m)):
                                if x == 0:
                                    file.write("<desired_orientation><v1>a*</v1><v2>b*</v2><close>true</close><comment></comment></desired_orientation><desired_orientation><v1>a*</v1><v2>c*</v2><close>true</close><comment></comment></desired_orientation>")
                                if x == 1:
                                    file.write("<desired_orientation><v1>b*</v1><v2>a*</v2><close>true</close><comment></comment></desired_orientation><desired_orientation><v1>b*</v1><v2>c*</v2><close>true</close><comment></comment></desired_orientation>")
                                if x == 2:
                                    file.write("<desired_orientation><v1>c*</v1><v2>a*</v2><close>true</close><comment></comment></desired_orientation><desired_orientation><v1>c*</v1><v2>b*</v2><close>true</close><comment></comment></desired_orientation>")      
                    if self.align == 'a':
                        file.write("<desired_orientation><v1>a*</v1><v2>b*</v2><close>true</close><comment></comment></desired_orientation><desired_orientation><v1>a*</v1><v2>c*</v2><close>true</close><comment></comment></desired_orientation>")
                    if self.align == 'b':
                        file.write("<desired_orientation><v1>b*</v1><v2>a*</v2><close>true</close><comment></comment></desired_orientation><desired_orientation><v1>b*</v1><v2>c*</v2><close>true</close><comment></comment></desired_orientation>")
                    if self.align == 'c':
                        file.write("<desired_orientation><v1>c*</v1><v2>a*</v2><close>true</close><comment></comment></desired_orientation><desired_orientation><v1>c*</v1><v2>b*</v2><close>true</close><comment></comment></desired_orientation>")            
                    if self.align == 'ab':
                        file.write("<desired_orientation><v1>(1,1,0)</v1><v2></v2><close>true</close><comment></comment></desired_orientation>") 
                    if self.align == 'ac':
                        file.write("<desired_orientation><v1>(1,0,1)</v1><v2></v2><close>true</close><comment></comment></desired_orientation>") 
                    if self.align == 'bc':
                        file.write("<desired_orientation><v1>(0,1,1)</v1><v2></v2><close>true</close><comment></comment></desired_orientation>")                     
                    file.write("<comment>First test parameter passed</comment></kappa_alignment_request>")
                file.close()           
            command = 'sh stac.com'
            self.stacalign_output = multiprocessing.Queue()      
            job = multiprocessing.Process(target=STACAlignAction(input=command,output=self.stacalign_output,logger=self.logger)).start()
        
        except:
            self.logger.exception('**Error in processSTACAlign**')
        
    def postprocessSTACAlign(self):
        """
        Error checking in Stac Align.
        """
        self.logger.debug('RunStac::postprocessSTACAlign')
        if self.stacalign_log == False:
            self.stacalign_log = []
        
        try:            
            if self.test:
                os.chdir('/home/schuerjp/Data_processing/Frank/Output/labelit_iteration0')                        
            list = []            
            pid  = self.stacalign_output.get()
            timer = 0
            while Utils.stillRunning(self,pid):
                time.sleep(1)
                timer += 1
                print 'Waiting for STAC alignment to finish '+str(timer)+' seconds'
                if self.stac_timer:
                    if timer >= self.stac_timer:
                        Utils.killChildren(self,pid)
                        self.logger.debug('STAC alignment timed out.')
                        print 'STAC alignment timed out.'
                        self.stacalign_log.append('Stac alignment timed out\n')
                        break   
            
            #Get newest log in directory (only one should be there but just in case...)
            ls = 'ls -lsrt STAC_EXEC_LOG* > out'
            os.system(ls)
            out = ((open('out','r').readlines())[-1]).split()[-1]
            log = open(out,'r')
            orientations = open('STAC_DNA_kappa_alignment_response','r').readlines()[1]
            list.append(orientations)
            for line in log:
                self.stacalign_log.append(line)
                list.append(line)
            log.close()
            
        except:
            self.logger.exception('**Error in stac.postprocessSTACAlign**')
        data = Parse.ParseOutputStacAlign(self,list)
        self.stacalign_results = { 'STAC align results' : data }
        if self.stacalign_results['STAC align results'] == None:
            self.logger.debug('No STAC alignment.')
            self.stacalign_results = { 'STAC align results' : 'FAILED'}
            self.clean = False
    
    def editSTACfile(self):
        """
        edit stac.com for user selection option for alignment.
        """
        self.logger.debug('RunStac::editSTACfile')
        if self.stacalign_log == False:
            self.stacalign_log = []
        try:            
            multi = False
            #Utils.pp(self,self.input)
            if os.path.exists('stac.com'):
                stac = open('stac.com','r')
                temp = []
                if self.align == 'smart':
                    newline = 'options=kappa_orientation_request\noptions2=SmartSpotSeparation\n'
                elif self.align == 'multi':
                    multi = True
                    newline  = 'options=kappa_orientation_request\noptions2=MultiCrystalReference\n'
                    path = os.path.join(self.working_dir,'temp')
                    newline2 = 'export RUNDIR='+path+'/\n'
                else:
                    newline = 'options=kappa_orientation_request\noptions2=Anomalous\n'
                for line in stac:
                    temp.append(line)
                    if line.startswith('options'):
                        index = temp.index(line)
                        temp.remove(line)
                    if multi:
                        if line.startswith('export RUNDIR='):
                            index2 = temp.index(line)
                            temp.remove(line)
                            temp.insert(index2,newline2)
                temp.insert(index,newline)
                stac.close()
                file = open('prestac.com','w')
                file.writelines(temp)
                file.close()
                command = 'sh prestac.com'
                if multi:
                    try:
                        os.mkdir(path)
                    except:
                        self.logger.exception('temp directory already exists')
                    shutil.copy('prestac.com',path)
                    os.chdir(path)
                    shutil.copy(str(self.header.get('correct.lp')),path)
                output = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)                
                for line in output.stdout:
                    self.stacalign_log.append(line)
                    #self.logger.debug(line)
                if multi:
                    if os.path.exists('DNA_kappa_alignment_request'):
                        shutil.copy('DNA_kappa_alignment_request',self.working_dir)
                    os.chdir(self.working_dir)
            else:
                self.logger.exception('stac.com does NOT exist!!!')
             
        except:
            self.logger.exception('**ERROR in stac.editSTACfile**')
           
    def convertStacAlignxml_stratxml(self):
        """
        Create the DNA_kappa_strategy_request from the STAC_DNA_kappa_alignment_response.
        """
        self.logger.debug('RunStac::convertStacAlignxml_stratxml')
        try:            
            if self.test:
                self.labelit_dir = '/home/schuerjp/Data_processing/Frank/Output/labelit_iteration0'
                os.chdir(self.labelit_dir)
            #Create the DNA_kappa_strategy_request xml file   
            temp = []
            file = open(os.path.join(self.working_dir,'STAC_DNA_kappa_alignment_response'),'r')
            out  = open(os.path.join(self.working_dir,'DNA_kappa_strategy_request'),'w')
            #old file
            ka = 'kappa_alignment_response'
            st = '<status><code>ok</code></status>'
            po = 'possible_orientation'
            xx = '</kappa_strategy_request>'
            #new file
            ks = 'kappa_strategy_request'
            bl = ''
            dd = 'desired_datum'
            sr = '<standard_request><symmetry></symmetry></standard_request></kappa_strategy_request>'            
            for line in file:
                temp.append(line) 
                junk2 = line.replace(ka,ks)
                junk3 = junk2.replace(st,bl)
                junk4 = junk3.replace(po,dd)
                junk5 = junk4.replace(xx,sr)        
            temp.insert(1,junk5)
            file.close()
            out.writelines(temp[0:2])
            out.close()        
            temp2 = []
            file2 = open(os.path.join(self.working_dir,'stac.com'),'r')
            out2  = open(os.path.join(self.working_dir,'stac_strat.com'),'w')            
            kap_align = 'options=kappa_alignment'
            kap_strat = 'options=kappa_strategy'
            for line in file2:
                temp2.append(line)
                if line.startswith(kap_align): 
                    junk6 = temp2.index(line)               
                    junk7 = line.replace(kap_align,kap_strat)
                    temp2.remove(line)
            temp2.insert(junk6, junk7)        
            file2.close()
            out2.writelines(temp2)
            out2.close()
        
        except:
            self.logger.exception('**Error in stac.convertStacAlignxml_stratxml**')
        
    def processSTACStrat(self,counter = 0):
        """
        Perform a STAC alignment.
        """
        self.logger.debug('RunStac::processSTACStrat')
        try:                    
            if self.test:
                os.chdir('/home/schuerjp/Data_processing/Frank/Output/labelit_iteration0')
            self.stacstrat_output = multiprocessing.Queue()      
            job = multiprocessing.Process(target=STACStratAction(output=self.stacstrat_output,logger=self.logger )).start()
        
        except:
            self.logger.exception('**Error in stac.processSTACStrat**')
        
    def postprocessSTACStrat(self,counter = 0):
        """
        Error checking in Stac Strategy.
        """
        self.logger.debug('RunStac::postprocessSTACStrat')
        if self.stacstrat_log == False:
            self.stacstrat_log = []
        
        try:            
            if self.test:
                os.chdir('/home/schuerjp/Data_processing/Frank/Output/labelit_iteration0')
                    
            pid  = self.stacstrat_output.get()
            #stat = os.waitpid(pid,0)
            timer = 0
            while Utils.stillRunning(self,pid):
                time.sleep(1)
                timer += 1
                print 'Waiting for STAC strategy to finish ' + str(timer) + ' seconds'
                if self.stac_timer:
                    if timer >= self.stac_timer:
                        Utils.killChildren(self,pid)
                        print 'STAC strategy timed out.'       
                        self.logger.debug('STAC strategy timed out.')     
                        self.stacstrat_log.append('Stac strategy timed out\n')
                        break   
                    
            input = open('STAC_DNA_kappa_strategy_response','r').readlines()[1]                            
            ls = 'ls -lsrt STAC_EXEC_LOG* > out'
            os.system(ls)
            out = ((open('out','r').readlines())[-1]).split()[-1]        
            log = open(out,'r')
            for line in log:
                self.stacstrat_log.append(line)
            log.close()
            data = Parse.ParseOutputStacStrat(self,input)
            self.stacstrat_results = { 'STAC strat results' : data }
        
        except:
            self.logger.exception('**Error in stac.postprocessSTACStrat**')
            self.logger.exception('No STAC strategy.')
            self.stacstrat_results = { 'STAC strat results' : 'FAILED'}        
        
    def PrintInfo(self):
        """
        Print information regarding programs utilized by RAPD
        """
        self.logger.debug('RunStac::PrintInfo')
        try:
            print '\nRAPD now using STAC'
            print '======================='
            print 'RAPD developed using STAC'
            print 'Reference: "The Grenoble Instrumentation Group: the Cipriani and Ravelli Teams" EMBL Research Reports 2005, pp 211-223.'
            print 'Website:   http://emblorg.embl.de/aboutus/news/publications/research/2005/grenoble_ravellicipriani.pdf \n'            
            self.logger.debug('RAPD now using STAC')
            self.logger.debug('=======================')
            self.logger.debug('RAPD developed using STAC')
            self.logger.debug('Reference: "The Grenoble Instrumentation Group: the Cipriani and Ravelli Teams" EMBL Research Reports 2005, pp 211-223.')
            self.logger.debug('Website:   http://emblorg.embl.de/aboutus/news/publications/research/2005/grenoble_ravellicipriani.pdf \n')
                        
        except:
            self.logger.exception('**Error in stac.PrintInfo**')      
    
    def postprocess(self):
        """
        Things to do after the main process runs
        1. Return the data through the pipe
        """
        self.logger.debug('RunStac::postprocess')
        #Run summary files for each program to print to screen        
        output           = {}
        
        if self.stac_failed == False:
            Summary.summaryAutoCell(self)
            Summary.summarySTAC(self)
        self.htmlSummaryStac()
        #Account for missing file paths
        output['STAC file1']         = 'None'
        output['STAC file2']         = 'None'
        output['image_path_raw_1']   = 'None'
        output['image_path_pred_1']  = 'None'        
        output['image_path_raw_2']   = 'None'
        output['image_path_pred_2']  = 'None'    
        output['Best plots html']    = 'None'
        output['Long summary html']  = 'None'
        output['Short summary html'] = 'None'        
        try:
            if self.gui:
                ss2 = 'jon_summary_stac.php'
            else:
                ss2 = 'jon_summary_stac.html'                               
            stac3_path = os.path.join(self.working_dir,ss2)
            if os.path.exists(stac3_path):                 
                output['Stac summary html']   = stac3_path
            else:
                output['Stac summary html']   = 'None'                                    
        except:
            self.logger.exception('**stac.postprocess Could not update path of stac summary html file.**')
            output['Stac summary html']   = 'FAILED' 
            
        try:
            self.output_files = {'Output files'   : output}            
        except:
            self.logger.exception('**stac.postprocess Could not update the output dict.**')
                           
        #Put all the result dicts from all the programs run into one resultant dict and pass it along the pipe.
        try:
            self.results = {}
            if self.output_files:
                self.results.update(self.output_files)
            if self.results:
                self.input.append(self.results)
            if self.gui:
                if self.preferences.get('request').has_key('request_type'):            
                    self.sendBack2(self.input)
        except:
            self.logger.exception('**stac.postprocess Could not send results to pipe.**')
        
        try:
            #Cleanup my mess.
            if self.clean:
                os.chdir(self.working_dir)                
                rm1_folders = 'rm -rf orientation*'
                self.logger.debug(rm1_folders)
                os.system(rm1_folders)
                rm_files = 'rm -rf DNA_k* DNA_S* *.x out stac* STAC_* 1_* fort.8 strategy* *.x.str *.sca temp'
                self.logger.debug(rm_files)
                os.system(rm_files)
                #Remove all unneeded files
                if self.gui:
                    rm_files2 = 'rm -rf *.inp *.par *.com'
                    self.logger.debug(rm_files2)
                    os.system(rm_files2)
        except:
            self.logger.exception('**stac.postprocess Could not cleanup**')
        
        #Say job is complete.
        t = round(time.time()-self.st)
        self.logger.debug('-------------------------------------')
        self.logger.debug('RAPD STAC complete.')
        self.logger.debug('Total elapsed time: ' + str(t) + ' seconds')
        self.logger.debug('-------------------------------------')
        print '\n-------------------------------------'
        print 'RAPD STAC complete.'
        print 'Total elapsed time: ' + str(t) + ' seconds'
        print '-------------------------------------'
        #sys.exit(0) #did not appear to end script with some programs continuing on for some reason.
        os._exit(0)
                
    def htmlSummaryStac(self):
        """
        Create the html/php results file for STAC.
        """
        self.logger.debug('RunStac::htmlSummaryStac')
        try:            
            if self.stac_failed == False:
                if self.gui:
                    jon_summary = open('jon_summary_stac.php','w')      
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
                    jon_summary = open('jon_summary_stac.html','w')    
                jon_summary.write('<html>\n')
                jon_summary.write('  <head>\n')
                jon_summary.write('    <style type="text/css" media="screen">\n')
                if self.gui == False:
                    jon_summary.write('      @import "../css/ndemo_page.css";\n')
                    jon_summary.write('      @import "../css/ndemo_table.css";\n')
                jon_summary.write('    body {\n')
                jon_summary.write('      background-image: none;\n')
                jon_summary.write('    }\n')
                jon_summary.write('    .dataTables_wrapper {position: relative; min-height: 75px; _height: 302px; clear: both;    }\n')
                jon_summary.write('    table.display td {padding: 1px 7px;}\n')   
                jon_summary.write('    </style>\n')
                if self.gui == False:
                    jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.js"></script>\n')
                    jon_summary.write('    <script type="text/javascript" language="javascript" src="../js/dataTables-1.5/media/js/jquery.dataTables.js"></script>\n')
                    jon_summary.write('    <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js" type="text/javascript"></script>\n')
                jon_summary.write('    <script type="text/javascript" charset="utf-8">\n')
                jon_summary.write('      $(document).ready(function() {\n')                
                jon_summary.write("        $('#accordion2').accordion({\n")
                jon_summary.write('           collapsible: true,\n')
                jon_summary.write('           active: false         });\n')
                if self.auto1_summary:
                    jon_summary.write("        $('#stac-auto').dataTable({\n")
                    jon_summary.write('           "bPaginate": false,\n')
                    jon_summary.write('           "bFilter": false,\n')
                    jon_summary.write('           "bInfo": false,\n')
                    jon_summary.write('           "bAutoWidth": false    });\n')                  
                if self.stac_align_summary:
                    #jon_summary.write("        $('#stac_align').dataTable({\n")
                    jon_summary.write("        stacAlignTable = $('#stac_align').dataTable({\n")
                    jon_summary.write('           "bPaginate": false,\n')
                    jon_summary.write('           "bFilter": false,\n')
                    jon_summary.write('           "bInfo": false,\n')
                    jon_summary.write('        /* "aaSorting": [[ 2, "asc" ]],   */\n')
                    jon_summary.write('           "bAutoWidth": false    });\n')                    
                if self.stac_strat:
                    if self.stac_strat_summary:
                        jon_summary.write("        $('#stac_strat').dataTable({\n")
                        jon_summary.write('           "bPaginate": false,\n')
                        jon_summary.write('           "bFilter": false,\n')
                        jon_summary.write('           "bInfo": false,\n')
                        jon_summary.write('           "bAutoWidth": false    });\n')                          
                jon_summary.write('        //Tooltips\n')
                jon_summary.write("        $('#stac_align thead th').each(function(){\n")
                jon_summary.write("           if ($(this).text() == 'V1') {\n")
                jon_summary.write("                this.setAttribute('title','The crystal vector to be aligned parallel to the spindle axis');\n")
                jon_summary.write('           }\n')
                jon_summary.write("           else if ($(this).text() == 'V2') {\n")
                jon_summary.write("                this.setAttribute('title','The crystal vector to lay in the plane to the spindle and beam axes');\n")
                jon_summary.write('           }\n')
                jon_summary.write("           else if ($(this).text() == 'Omega') {\n")
                jon_summary.write("                this.setAttribute('title','The \"phi\" axis in ADXV data collection software');\n")
                jon_summary.write("           }\n")
                jon_summary.write("           else if ($(this).text() == 'Kappa') {\n")
                jon_summary.write("                this.setAttribute('title','The \"kappa\" axis in the MD2 software. Move in small steps.');\n")
                jon_summary.write("           }\n")
                jon_summary.write("           else if ($(this).text() == 'Phi') {\n")
                jon_summary.write("                this.setAttribute('title','The \"phi\" axis in the MD2 software. Move in small steps.');\n")
                jon_summary.write("           }\n")
                jon_summary.write("         });\n")
                jon_summary.write("         $('#stac_strat thead th').each(function(){\n")
                jon_summary.write("           if ($(this).text() == 'Omega Start') {\n")
                jon_summary.write("                this.setAttribute('title','The starting \"phi\" in ADXV data collection software');\n")
                jon_summary.write("           }\n")
                jon_summary.write("           else if ($(this).text() == 'Omega End') {\n")
                jon_summary.write("                this.setAttribute('title','The ending \"phi\" in ADXV data collection software');\n")
                jon_summary.write("           }\n")
                jon_summary.write("           else if ($(this).text() == 'Kappa') {\n")
                jon_summary.write("                this.setAttribute('title','The \"kappa\" axis in the MD2 software. Move in small steps.');\n")
                jon_summary.write("           }\n")
                jon_summary.write("           else if ($(this).text() == 'Phi') {\n")
                jon_summary.write("                this.setAttribute('title','The \"phi\" axis in the MD2 software. Move in small steps.');\n")
                jon_summary.write("           }\n")
                jon_summary.write("           else if ($(this).text() == 'Completeness') {\n")
                jon_summary.write("                this.setAttribute('title','Theoretical completeness');\n")
                jon_summary.write("           }\n")
                jon_summary.write("         });\n")
                jon_summary.write("        // Handler for click events on the STAC table\n")
                jon_summary.write('        $("#stac_align tbody tr").click(function(event) {\n')
                jon_summary.write("            //take highlight from other rows\n")
                jon_summary.write("            $(stacAlignTable.fnSettings().aoData).each(function (){\n")
                jon_summary.write("                $(this.nTr).removeClass('row_selected');\n")
                jon_summary.write("            });\n")
                jon_summary.write("            //highlight the clicked row\n")
                jon_summary.write("            $(event.target.parentNode).addClass('row_selected');\n")
                jon_summary.write("        });\n")
                jon_summary.write('        $("#stac_align tbody tr").dblclick(function(event) {\n')
                jon_summary.write("            //Get the current data of the clicked-upon row\n")
                jon_summary.write("            aData = stacAlignTable.fnGetData(this);\n")
                jon_summary.write("            //Use the values from the line to fill the form\n")
                jon_summary.write('            var omega = aData[3];\n')
                jon_summary.write('            var kappa = aData[4];\n')
                jon_summary.write('            var phi = aData[5];\n')
                jon_summary.write('''        $.ajax({
                    type: "POST",
                    url: "d_add_minikappa.php",
                    data: { omega:omega,
                            kappa:kappa,
                            phi:phi,
                            ip_address:my_ip,
                            beamline:my_beamline }
            });\n''')
                jon_summary.write("            //Popup the success dialog \n")
                jon_summary.write('            PopupSuccessDialog("Minikappa settings sent to beamline"); \n')
                jon_summary.write('        }); //Close for  $("#stac_align tbody").click(function(event) {\n')
                #jon_summary.write('        $("#dialog-submit").dialog({\n')
                #jon_summary.write("            autoOpen: false,\n")
                #jon_summary.write('            show: "blind",\n')
                #jon_summary.write('            hide: "blind",\n')
                #jon_summary.write('            title: "Success"\n')          
                #jon_summary.write("        });\n")
                jon_summary.write('      });\n')
                jon_summary.write("    </script>\n\n\n")
                jon_summary.write(" </head>\n")
                jon_summary.write('  <body id="dt_example">\n')
                jon_summary.write('    <div id="container">\n')
                jon_summary.write('    <div class="full_width big">\n')
                jon_summary.write('      <div id="demo">\n')
                jon_summary.write('        <h1 class="results">STAC summary for:</h1>\n')
                jon_summary.write("      <h2 class='results'>Image: " + self.header.get('fullname') + "</h2>\n") 
                if self.header2:
                    jon_summary.write("      <h2 class='results'>Image: " + self.header2.get('fullname') + "</h2>\n")
                if self.auto1_summary:
                    jon_summary.writelines(self.auto1_summary) 
                    jon_summary.write('    <div id="container">\n')
                    jon_summary.write('    <div class="full_width big">\n')
                    jon_summary.write('      <div id="demo">\n')
                if self.stac_align_summary:
                    jon_summary.writelines(self.stac_align_summary)                    
                if self.stacalign_results:
                    if self.stacalign_results.get('STAC align results') == 'FAILED':
                        jon_summary.write('    <div id="container">\n')
                        jon_summary.write('    <div class="full_width big">\n')
                        jon_summary.write('      <div id="demo">\n')
                        jon_summary.write('    <h4 class="results">STAC alignment Failed.</h3>\n')
                        jon_summary.write("      </div>\n")
                        jon_summary.write("    </div>\n")
                        jon_summary.write("    </div>\n")
                if self.stac_strat:
                    if self.stac_strat_summary:
                        jon_summary.writelines(self.stac_strat_summary)                    
                    if self.stacstrat_results:
                        if self.stacstrat_results.get('STAC strat results') == 'FAILED':
                            jon_summary.write('    <div id="container">\n')
                            jon_summary.write('    <div class="full_width big">\n')
                            jon_summary.write('      <div id="demo">\n')
                            jon_summary.write('    <h4 class="results">STAC strategy Failed.</h3>\n')
                            jon_summary.write("      </div>\n")
                            jon_summary.write("    </div>\n")
                            jon_summary.write("    </div>\n")            
                jon_summary.write('    <div id="container">\n')
                jon_summary.write('    <div class="full_width big">\n')
                jon_summary.write('      <div id="demo">\n')            
                jon_summary.write("      <h1 class='Results'>STAC Logfile</h1>\n")
                jon_summary.write("     </div>\n")  
                jon_summary.write("     </div>\n")  
                jon_summary.write('      <div id="accordion2">\n')
                jon_summary.write('        <h3><a href="#">Click to view log</a></h3>\n')
                jon_summary.write('          <div>\n')
                jon_summary.write('            <pre>\n')
                jon_summary.write('\n')
                jon_summary.write('---------------STAC RESULTS---------------\n')
                jon_summary.write('\n')            
                if self.stacalign_log:
                    for line in self.stacalign_log:
                        jon_summary.write('' + line )            
                else:
                    jon_summary.write('---------------STAC FAILED---------------\n')                                
                jon_summary.write('            </pre>\n')
                jon_summary.write('          </div>\n')           
                jon_summary.write("      </div>\n")
                jon_summary.write("    </div>\n")                
                jon_summary.write("  </body>\n")
                #jon_summary.write('<div id="dialog-submit">\n')
                #jon_summary.write('  <p>STAC settings have been sent to the beamline</p>\n')
                #jon_summary.write('</div>\n')
                jon_summary.write("</html>\n")
                jon_summary.close()
            else:                
                if self.gui:
                    jon_summary = open('jon_summary_stac.php','w')      
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
                    jon_summary = open('jon_summary_stac.html','w')    
                jon_summary.write('<html>\n')
                jon_summary.write('  <head>\n')
                jon_summary.write('    <style type="text/css" media="screen">\n')
                if self.gui == False:
                    jon_summary.write('      @import "dataTables-1.5/media/css/demo_page.css";\n')
                    jon_summary.write('      @import "dataTables-1.5/media/css/demo_table.css";\n')
                jon_summary.write('    body {\n')
                jon_summary.write('      background-image: none;\n')
                jon_summary.write('    }\n')
                jon_summary.write('    .dataTables_wrapper {position: relative; min-height: 75px; _height: 302px; clear: both;    }\n')
                jon_summary.write('    table.display td {padding: 1px 7px;}\n')   
                jon_summary.write('    </style>\n')
                if self.gui == False:
                    jon_summary.write('    <script type="text/javascript" language="javascript" src="dataTables-1.5/media/js/jquery.js"></script>\n')
                    jon_summary.write('    <script type="text/javascript" language="javascript" src="dataTables-1.5/media/js/jquery.dataTables.js"></script>\n')
                jon_summary.write('    <script type="text/javascript" charset="utf-8">\n')
                jon_summary.write('      $(document).ready(function() {\n')                                
                jon_summary.write('      } );\n')
                jon_summary.write("    </script>\n\n\n")
                jon_summary.write(" </head>\n")
                jon_summary.write('  <body id="dt_example">\n')
                jon_summary.write('    <div id="container">\n')
                jon_summary.write('    <div class="full_width big">\n')
                jon_summary.write('      <div id="demo">\n')
                jon_summary.write('        <h3 class="results">You MUST select a successful solution and NOT another STAC alignment</h3>\n')      
                jon_summary.write("      </div>\n")
                jon_summary.write("    </div>\n")
                jon_summary.write("    </div>\n")    
                jon_summary.write("  </body>\n")
                jon_summary.write("</html>\n")
                jon_summary.close() 
        except:
            self.logger.exception('**Error in stac.htmlSummaryStac**')

def STACAlignAction(input,output,logger):
    """
    Run Stac Alignment in multiprocessor mode.
    """
    logger.debug('STACAlignAction')
    try:
        logger.debug(input)
        junk = open('stac_align.log','a')
        myoutput = subprocess.Popen(input,shell=True,stdout=junk,stderr=junk)
        junk.close() 
        output.put(myoutput.pid)
    except:
        logger.exception('**Error in stac.STACAlignAction**')
    
def STACStratAction(output,logger):
    """
    Run Stac Strategy in multiprocessor mode.
    """
    logger.debug('STACStratAction')
    try:
        command = 'sh stac_strat.com'
        logger.debug(command)
        junk = open('stac_strat.log','a')
        myoutput = subprocess.Popen(command,shell=True,stdout=junk,stderr=junk)
        junk.close() 
        output.put(myoutput.pid)     
    except:
        logger.exception('**Error in stac.STACStratAction**')

if __name__ == '__main__':
    #start logging
    LOG_FILENAME = '/tmp/rapd_agent_stac.log'
    # Set up a specific logger with our desired output level
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,maxBytes=100000,backupCount=5)
    #add a formatter
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('RunStac.__init__')
    import ../test_data/rapd_auto_testinput as Input
    input = Input.input()
    params = {'stac_timer': 120,
              'test': False,
              'gui':False,
              'dir': '/tmp/RAPD_test/Output'}  
    T = RunStac(input,params,logger=logger)
    

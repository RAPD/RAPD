'''
__author__ = "Jon Schuermann, Frank Murphy"
__copyright__ = "Copyright 2009,2010,2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2011/04/19"
'''

import os
import subprocess
import time
import shutil
import logging,logging.handlers

import rapd_agent_utilities as Utils

def summaryLabelit(self):
    """
    Print Labelit results to screen and create variable with results for the summary_short and summary_long php files.
    """
    self.logger.debug('Summary::summaryLabelit')
    try:
        labelit_face      = self.labelit_results.get('Labelit results').get('labelit_face')
        labelit_solution  = self.labelit_results.get('Labelit results').get('labelit_solution')               
        labelit_metric    = self.labelit_results.get('Labelit results').get('labelit_metric')
        labelit_fit       = self.labelit_results.get('Labelit results').get('labelit_fit')
        labelit_rmsd      = self.labelit_results.get('Labelit results').get('labelit_rmsd')
        labelit_spots_fit = self.labelit_results.get('Labelit results').get('labelit_spots_fit')
        labelit_system    = self.labelit_results.get('Labelit results').get('labelit_system')
        labelit_cell      = self.labelit_results.get('Labelit results').get('labelit_cell')         
        labelit_volume    = self.labelit_results.get('Labelit results').get('labelit_volume')
        mosflm_face       = self.labelit_results.get('Labelit results').get('mosflm_face')
        mosflm_solution   = self.labelit_results.get('Labelit results').get('mosflm_solution')
        mosflm_sg         = self.labelit_results.get('Labelit results').get('mosflm_sg')
        mosflm_beam_x     = self.labelit_results.get('Labelit results').get('mosflm_beam_x')
        mosflm_beam_y     = self.labelit_results.get('Labelit results').get('mosflm_beam_y')
        mosflm_distance   = self.labelit_results.get('Labelit results').get('mosflm_distance')
        mosflm_res        = self.labelit_results.get('Labelit results').get('mosflm_res')
        mosflm_mos        = self.labelit_results.get('Labelit results').get('mosflm_mos')
        mosflm_rms        = self.labelit_results.get('Labelit results').get('mosflm_rms')
        output            = self.labelit_results.get('Labelit results').get('output')            
        #mosaicity      = str(self.labelit_results.get('Labelit results').get('mosaicity'))
    except:
        self.logger.exception('**summaryLabelit Could not print Labelit indexing results to screen**')                    
    #create self.labelit_summary for resultant php files.
    try:                
        labelit  ='    <div id="container">\n'
        labelit +='    <div class="full_width big">\n'
        labelit +='      <div id="demo">\n'                       
        labelit +='        <h1 class="results">Mosflm Integration Results</h1>\n'
        labelit +='        <table cellpadding="0" cellspacing="0" border="0" class="display" id="mosflm">\n'
        labelit +='          <thead align="center">\n'
        labelit +='            <tr>\n'
        labelit +='              <th>&nbsp</th>\n'
        labelit +='              <th>Solution</th>\n'
        labelit +='              <th>Spacegroup</th>\n'
        labelit +='              <th>Beam X</th>\n'
        labelit +='              <th>Beam Y</th>\n'
        labelit +='              <th>Distance</th>\n'
        labelit +='              <th>Resolution</th>\n'
        labelit +='              <th>Mosaicity</th>\n'
        labelit +='              <th>RMS</th>\n'
        labelit +='            </tr>\n'
        labelit +='          </thead>\n'
        labelit +='          <tbody align="center">\n'
        #labelit +='        </table>\n'    
        #If complexity set to 'full', then gets summary for all the wedges.
        for x in range(len(mosflm_solution)):                        
            labelit +='            <tr class="gradeA">\n'
            labelit +="              <td>"+mosflm_face[x]+"</td>\n"
            labelit +="              <td>"+mosflm_solution[x]+"</td>\n"
            labelit +="              <td>"+mosflm_sg[x]+"</td>\n"
            labelit +="              <td>"+mosflm_beam_x[x]+"</td>\n"
            labelit +="              <td>"+mosflm_beam_y[x]+"</td>\n"
            labelit +="              <td>"+mosflm_distance[x]+"</td>\n"
            labelit +="              <td>"+mosflm_res[x]+"</td>\n"
            labelit +="              <td>"+mosflm_mos[x]+"</td>\n"
            labelit +="              <td>"+mosflm_rms[x]+"</td>\n"
            labelit +="            </tr>\n"
        labelit +='          </tbody>\n'
        labelit +="        </table>\n"            
        labelit +="       </div>\n"            
        labelit +="      </div>\n"  
        labelit +="     </div>\n"  
        labelit +='    <div id="container">\n'
        labelit +='    <div class="full_width big">\n'
        labelit +='      <div id="demo">\n'                       
        labelit +='        <h1 class="results">Labelit Results</h1>\n'
        labelit +='        <table cellpadding="0" cellspacing="0" border="0" class="display" id="labelit">\n'
        labelit +='          <thead align="center">\n'
        labelit +='            <tr>\n'
        labelit +='              <th>&nbsp</th>\n'
        labelit +='              <th>Solution</th>\n'
        labelit +='              <th>Metric</th>\n'
        labelit +='              <th>Fit</th>\n'
        labelit +='              <th>RMSD</th>\n'
        labelit +='              <th># of Spots</th>\n'
        labelit +='              <th>Crystal System</th>\n'
        labelit +='              <th>a</th>\n'
        labelit +='              <th>b</th>\n'
        labelit +='              <th>c</th>\n'
        labelit +='              <th>&alpha;</th>\n'
        labelit +='              <th>&beta;</th>\n'
        labelit +='              <th>&gamma;</th>\n'
        labelit +='              <th>Volume</th>\n'
        labelit +='            </tr>\n'
        labelit +='          </thead>\n'
        labelit +='          <tbody align="center">\n'                
        for x in range(len(labelit_solution)):   
            system =   labelit_system[x][0]+' '+labelit_system[x][1]                
            labelit +='            <tr class="gradeA">\n'
            labelit +="              <td>"+labelit_face[x]+"</td>\n"
            labelit +="              <td>"+labelit_solution[x]+"</td>\n"
            labelit +="              <td>"+labelit_metric[x]+"</td>\n"
            labelit +="              <td>"+labelit_fit[x]+"</td>\n"
            labelit +="              <td>"+labelit_rmsd[x]+"</td>\n"
            labelit +="              <td>"+labelit_spots_fit[x]+"</td>\n"
            labelit +="              <td>"+system+"</td>\n"
            labelit +="              <td>"+labelit_cell[x][0]+"</td>\n"
            labelit +="              <td>"+labelit_cell[x][1]+"</td>\n"
            labelit +="              <td>"+labelit_cell[x][2]+"</td>\n"
            labelit +="              <td>"+labelit_cell[x][3]+"</td>\n"
            labelit +="              <td>"+labelit_cell[x][4]+"</td>\n"
            labelit +="              <td>"+labelit_cell[x][5]+"</td>\n"
            labelit +="              <td>"+labelit_volume[x]+"</td>\n"
            labelit +="            </tr>\n\n"                
        labelit +='          </tbody>\n'
        labelit +='        </table>\n'
        labelit +='      </div>\n'
        labelit +='     </div>\n' 
        labelit +='    </div>\n'                        
        self.labelit_summary = labelit
    except:
        self.logger.exception('**ERROR in Summary.summaryLabelit.**')

def summaryDistl(self):
    """
    Print Distl summary to screen and create variable for input into summary_long.php.
    """
    self.logger.debug('Summary::summaryDistl')
    #if self.distl_results:
    try:
        total_spots      = self.distl_results.get('Distl results').get('total spots')
        spots_in_res     = self.distl_results.get('Distl results').get('spots in res')
        good_spots       = self.distl_results.get('Distl results').get('good Bragg spots')
        distl_res        = self.distl_results.get('Distl results').get('distl res')
        labelit_res      = self.distl_results.get('Distl results').get('labelit res')
        max_cell         = self.distl_results.get('Distl results').get('max cell')
        ice_rings        = self.distl_results.get('Distl results').get('ice rings')
        overloads        = self.distl_results.get('Distl results').get('overloads')
        min              = self.distl_results.get('Distl results').get('min signal strength')
        max              = self.distl_results.get('Distl results').get('max signal strength')
        mean             = self.distl_results.get('Distl results').get('mean int signal')
    except:
        self.logger.exception('**summaryDistl Could not print Distl results to screen.**')
    
    #Create distl variable for summary_long.php
    try:            
        distl  ='    <div id="container">\n'
        distl +='    <div class="full_width big">\n'
        distl +='      <div id="demo">\n'                       
        distl +='        <h1 class="results">Peak Picking Results</h1>\n'
        distl +='        <table cellpadding="0" cellspacing="0" border="0" class="display" id="distl">\n'
        distl +='          <thead align="center">\n'
        distl +='            <tr>\n'
        distl +='              <th>Total Spots</th>\n'
        distl +='              <th>Spots in Res</th>\n'
        distl +='              <th>Good Bragg Spots</th>\n'
        distl +='              <th>Overloaded Spots</th>\n'
        distl +='              <th>Distl Res</th>\n'
        distl +='              <th>Labelit Res</th>\n'
        distl +='              <th>Max Cell</th>\n'
        distl +='              <th>Ice Rings</th>\n'
        distl +='              <th>Min Signal Strength</th>\n'
        distl +='              <th>Max Signal Strength</th>\n'
        distl +='              <th>Mean Int Signal</th>\n'       
        distl +='            </tr>\n'
        distl +='          </thead>\n'
        distl +='          <tbody align="center">\n'        
        #distl +='            <tr class="gradeA">\n'            
        for x in range(len(total_spots)):
            distl +='            <tr class="gradeA">\n'
            distl +="              <td>"+total_spots[x]+"</td>\n"
            distl +="              <td>"+spots_in_res[x]+"</td>\n"
            distl +="              <td>"+good_spots[x]+"</td>\n"
            distl +="              <td>"+overloads[x]+"</td>\n"
            distl +="              <td>"+distl_res[x]+"</td>\n"
            distl +="              <td>"+labelit_res[x]+"</td>\n"
            distl +="              <td>"+max_cell[x]+"</td>\n"
            distl +="              <td>"+ice_rings[x]+"</td>\n"     
            distl +="              <td>"+min[x]+"</td>\n"
            distl +="              <td>"+max[x]+"</td>\n"
            distl +="              <td>"+mean[x]+"</td>\n"            
            distl +="            </tr>\n"            
        distl +='          </tbody>\n'
        distl +="        </table>\n"
        distl +="       </div>\n"
        distl +="      </div>\n"
        distl +="     </div>\n"                  
        self.distl_summary = distl
            
    except:
        self.logger.exception('**ERROR in Summary.summaryDistl**')

def summaryRaddose(self):
    """
    print RADDOSE results to screen and create variable for php file. 
    """
    self.logger.debug('Summary::summaryRaddose')
    #if self.raddose_results:
    try:
        hen_lim       = self.raddose_results.get('Raddose results').get('henderson limit')
    except:
        self.logger.exception('**summaryRaddose Could not display RADDOSE results to screen.**')            
    #Create Raddose variable for summary_long.php
    try:
        raddose ='    <div id="container">\n'
        raddose +='    <div class="full_width big">\n'
        raddose +='     <div id="demo">\n'                                   
        raddose +='        <h1 class="results">Raddose Results</h1>\n'
        raddose +='    <table cellpadding="2" cellspacing="2" border="0" class="display" id="raddose">\n'
        raddose +='       <thead>\n'
        raddose +='            <tr>\n'
        raddose +='              <th></th>\n'
        raddose +='              <th></th>\n'
        raddose +='              <th></th>\n'
        raddose +='              <th></th>\n'
        raddose +='              <th></th>\n'
        raddose +='              <th></th>\n'
        raddose +='              <th></th>\n'
        raddose +='              <th></th>\n'
        raddose +='              <th></th>\n'
        raddose +='              <th></th>\n'
        raddose +='              <th></th>\n'
        raddose +='            </tr>\n'
        raddose +='          </thead>\n'
        raddose +='          <tbody align="left">\n'
        raddose +='            <tr>\n'
        raddose +='              <th>Dose (G/s)</th>\n'
        raddose +='              <td>'+str(self.dose)+'</td>\n'
        raddose +='            </tr>\n'
        raddose +='            <tr>\n'
        raddose +='              <th>Time in seconds to reach Henderson limit (20 MGy)</th>\n'
        raddose +='              <td>'+hen_lim+'</td>\n'
        raddose +='            </tr>\n'  
        raddose +='            <tr>\n'
        raddose +='              <th>Time in sec to reach experimental dose limit (30 MGy)</th>\n'
        raddose +='              <td>'+str(self.exp_dose_lim)+'</td>\n'
        raddose +='            </tr>\n'  
        raddose +='          </tbody>\n'
        raddose +="        </table>\n"
        raddose +="       </div>\n"
        raddose +="      </div>\n"
        raddose +="     </div>\n"                
        self.raddose_summary = raddose            
        
    except:
        self.logger.exception('**ERROR in Summary.summaryRaddose.**')
    
def summaryBest(self,anom=False):
    """
    print BEST results to screen and creates variable for php file.
    """
    self.logger.debug('Summary::summaryBest')        
    try:
        if anom:
            j  = 'self.best_anom_results'
            j1 = 'Best ANOM results'
            j2 = ' anom '
        else:
            j  = 'self.best_results'
            j1 = 'Best results'
            j2 = ' '
        run_number      = eval(j+".get('"+j1+"').get('strategy"+j2+"run number')")
        phi_start       = eval(j+".get('"+j1+"').get('strategy"+j2+"phi start')")
        num_images      = eval(j+".get('"+j1+"').get('strategy"+j2+"num of images')")
        delta_phi       = eval(j+".get('"+j1+"').get('strategy"+j2+"delta phi')")
        time            = eval(j+".get('"+j1+"').get('strategy"+j2+"image exp time')")
        distance        = eval(j+".get('"+j1+"').get('strategy"+j2+"distance')")
        phi_end         = eval(j+".get('"+j1+"').get('strategy"+j2+"phi end')")
        res_lim         = eval(j+".get('"+j1+"').get('strategy"+j2+"res limit')")
        completeness    = eval(j+".get('"+j1+"').get('strategy"+j2+"completeness')")
        redundancy      = eval(j+".get('"+j1+"').get('strategy"+j2+"redundancy')")
        rot_range       = eval(j+".get('"+j1+"').get('strategy"+j2+"rot range')")
        r_factor        = eval(j+".get('"+j1+"').get('strategy"+j2+"R-factor')")
        i_sig           = eval(j+".get('"+j1+"').get('strategy"+j2+"I/sig')")
        tot_time        = eval(j+".get('"+j1+"').get('strategy"+j2+"total exposure time')")
        data_col_time   = eval(j+".get('"+j1+"').get('strategy"+j2+"data collection time')")
        blind           = eval(j+".get('"+j1+"').get('strategy"+j2+"frac of unique in blind region')")
        attenuation     = float(eval(j+".get('"+j1+"').get('strategy"+j2+"attenuation')"))
        best_trans      = eval(j+".get('"+j1+"').get('strategy"+j2+"new transmission')")
        #best_trans = Utils.calcTransmission(self,attenuation)
        if self.sample_type != 'Ribosome':
            if self.high_dose:
                if float(max(time)) > 3.0:                                                
                    for x in range(len(time)):
                        time[x] = '3.0'
            if self.iso_B:
                if float(max(time)) > 2.0:                                                
                    for x in range(len(time)):
                        time[x] = '1.0'                                              
        total_images = 0
        for i in num_images:
            total_images += int(i)
        if anom:
            print '\n\n\tOptimal Plan of ANOMALOUS data collection'
        else:
            print '\n\n\t\tOptimal Plan of data collection'
        print '\t\t================================'
        print '\tResolution limit is set by the radiation damage\n'
        print '-----------------------------------------------------------------------------------'
        print ' N |  Phi_start |  N.of.images | Rot.width |  Exposure | Distance | % Transmission |'
        print '-----------------------------------------------------------------------------------'
        for x in run_number:
            number = int(x) - 1
            #print '%2s | %8s   | %7s      |%9s  | %9s | %7s  |     %3.0f      |' \
            print '%2s | %8s   | %7s      |%9s  | %9s | %7s  |     %3s      |' \
                % (x,phi_start[number],num_images[number],delta_phi[number],time[number],distance[number],best_trans[number])
        print '-----------------------------------------------------------------------------------'
        print 'Resolution limit                  : ',res_lim,'Angstrom'
        print 'Anomalous data                    : ',str(anom)
        print 'Phi_start - Phi_finish            : ',phi_start[0],'-',phi_end
        print 'Total rotation range              : ',rot_range,'degree'
        print 'Total N.of images                 : ',total_images
        print 'Overall Completeness              : ',completeness
        print 'Redundancy                        : ',redundancy
        print 'R-factor (outer shell)            : ',r_factor
        print 'I/Sigma (outer shell)             : ',i_sig
        print 'Total Exposure time               : ',tot_time,'sec'
        print 'Total Data Collection time        : ',data_col_time,'sec'
        print 'Frac of unique ref in blind region: ',blind
            
    except:
        self.logger.exception('**summaryBest. Could not display Best results to screen.**')        
    #Create Best variable for php files.
    try:
        best ='    <div id="container">\n'
        best +='    <div class="full_width big">\n'
        best +='     <div id="demo">\n'                                   
        if anom:
            best +='      <h1 class="results">ANOMALOUS data collection strategy</h1>\n'
        else:
            best +='      <h1 class="results">Data collection strategy</h1>\n'
        if self.high_dose:
            best +='      <h4 class="results">Dosage is too high! Crystal will last for '+self.crystal_life+' images. Strategy calculated from realistic dosage.</h4>\n'
        if anom:
            line = '        <table cellpadding="0" cellspacing="0" border="10" class="display" id="bestanom">\n'
            best += line
            best0 = line
            best1 ='        <table cellpadding="0" cellspacing="0" border="10" class="display" id="bestanom1">\n'             
        else:
            line = '        <table cellpadding="0" cellspacing="0" border="10" class="display" id="best">\n'
            best += line
            best0 = line
            best1 ='        <table cellpadding="0" cellspacing="0" border="10" class="display" id="best1">\n'
        best +='          <thead align="center">\n'
        best +='            <tr>\n'
        best +='              <th>N</th>\n'
        best +='              <th>Phi Start</th>\n'
        best +='              <th>Phi End</th>\n'
        best +='              <th>Rot Range</th>\n'
        best +='              <th>N of Images</th>\n'
        best +='              <th>Delta Phi</th>\n'
        best +='              <th>Exposure time</th>\n'
        best +='              <th>Distance</th>\n'
        best +='              <th>% Transmission</th>\n'
        best +='            </tr>\n'
        best +='          </thead>\n'
        best +='          <tbody align="center">\n'                    
        for x in run_number:
            number     = int(x) - 1
            se  = float(phi_start[number])+int(num_images[number])*(float(delta_phi[number]))
            if se > 360:
                sweep_end = str(se - 360)
            else:
                sweep_end = str(se)
            sweep_size = str(int(num_images[number])*(float(delta_phi[number])))
            if anom:
                best +='            <tr class="gradeD">\n'
            else:
                best +='            <tr class="gradeC">\n'
            best +="              <td>"+x+"</td>\n"
            best +="              <td><b>"+phi_start[number]+"</b></td>\n"
            best +="              <td><b>"+sweep_end+"</b></td>\n"
            best +="              <td><b>"+sweep_size+"</b></td>\n"
            best +="              <td>"+num_images[number]+"</td>\n"
            best +="              <td>"+delta_phi[number]+"</td>\n"
            best +="              <td>"+time[number]+"</td>\n"
            best +="              <td>"+distance[number]+"</td>\n"
            #best +="              <td>"+"%5.2f" %best_trans[number]+"</td>\n"
            best +="              <td>"+best_trans[number]+"</td>\n"
            best +="            </tr>\n\n"                
        best +='          </tbody>\n'  
        best +="        </table>\n"
        best +="       </div>\n"
        best +="      </div>\n"
        best +="     </div>\n"                
        if anom:
            self.best_anom_summary = best 
            self.best1_anom_summary = best.replace(best0,best1)
        else:
            self.best_summary = best 
            self.best1_summary = best.replace(best0,best1)       
        best_long ='    <div id="container">\n'
        best_long +='    <div class="full_width big">\n'
        best_long +='     <div id="demo">\n'                                  
        best_long +="      <h2 class='results'>Image: "+self.header.get('fullname')+"</h2>\n"
        if self.header2:
            best_long +="      <h2 class='results'>Image: "+self.header2.get('fullname')+"</h2>\n"
        if anom:
            best_long +='    <table cellpadding="2" cellspacing="2" border="0" class="display" id="bestanomdata">\n'
        else:
            best_long +='    <table cellpadding="2" cellspacing="2" border="0" class="display" id="bestdata">\n'
        best_long +='       <thead>\n'
        best_long +='            <tr>\n'
        best_long +='              <th></th>\n'
        best_long +='              <th></th>\n'
        best_long +='              <th></th>\n'
        best_long +='              <th></th>\n'
        best_long +='              <th></th>\n'
        best_long +='            </tr>\n'
        best_long +='          </thead>\n'
        best_long +='          <tbody align="left">\n'
        best_long +='            <tr>\n'
        best_long +='              <th>Resolution Limit</th>\n'
        best_long +='              <td>'+res_lim+' Angstroms</td>\n'
        best_long +='            </tr>\n'
        best_long +='            <tr>\n'
        best_long +='              <th>Anomalous data</th>\n'
        best_long +='              <td>'+str(anom)+'</td>\n'
        best_long +='            </tr>\n'  
        best_long +='            <tr>\n'
        best_long +='              <th>Phi_start - Phi_finish</th>\n'
        best_long +='              <td>'+phi_start[0]+'-'+phi_end+'</td>\n'
        best_long +='            </tr>\n'  
        best_long +='            <tr>\n'
        best_long +='              <th>Total rotation range</th>\n'
        best_long +='              <td>'+rot_range+' Degrees</td>\n'
        best_long +='            </tr>\n'  
        best_long +='            <tr>\n'
        best_long +='              <th>Total N.of images</th>\n'
        best_long +='              <td>'+str(total_images)+'</td>\n'
        best_long +='            </tr>\n'  
        best_long +='            <tr>\n'
        best_long +='              <th>Overall Completeness</th>\n'
        best_long +='              <td>'+completeness+'</td>\n'
        best_long +='            </tr>\n'  
        best_long +='            <tr>\n'
        best_long +='              <th>Redundancy</th>\n'
        best_long +='              <td>'+str(redundancy)+'</td>\n'
        best_long +='            </tr>\n'  
        best_long +='            <tr>\n'
        best_long +='              <th>R-factor (outer shell)</th>\n'
        best_long +='              <td>'+r_factor+'</td>\n'
        best_long +='            </tr>\n'  
        best_long +='            <tr>\n'
        best_long +='              <th>I/Sigma (outer shell)</th>\n'
        best_long +='              <td>'+i_sig+'</td>\n'
        best_long +='            </tr>\n'  
        best_long +='            <tr>\n'
        best_long +='              <th>Total Exposure time</th>\n'
        best_long +='              <td>'+tot_time+' sec</td>\n'
        best_long +='            </tr>\n'  
        best_long +='            <tr>\n'
        best_long +='              <th>Total Data Collection time</th>\n'
        best_long +='              <td>'+data_col_time+' sec</td>\n'
        best_long +='            </tr>\n'  
        best_long +='            <tr>\n'
        best_long +='              <th>Frac of unique ref in blind region</th>\n'
        best_long +='              <td>'+blind+'</td>\n'
        best_long +='            </tr>\n'    
        best_long +='          </tbody>\n'  
        best_long +="        </table>\n"
        best_long +="       </div>\n"
        best_long +="      </div>\n"
        best_long +="     </div>\n"
        if anom:
            self.best_anom_summary_long = best_long
        else:
            self.best_summary_long = best_long
            
    except:
        self.logger.exception('**Summary.summaryBest. Could not create Best html variable.**')
    
def summaryMosflm(self,anom=False):
    """
    Create html files Mosflm strategy.
    """
    self.logger.debug('Summary::summaryMosflm')
    if self.labelit_failed == False:
        try:
            if anom:
                j  = 'self.mosflm_strat_anom_results'
                j1 = 'Mosflm ANOM strategy results'
                j2 = ' anom '
            else:
                j  = 'self.mosflm_strat_results'
                j1 = 'Mosflm strategy results'
                j2 = ' '
            run_number      = eval(j+".get('"+j1+"').get('strategy"+j2+"run number')")
            phi_start       = eval(j+".get('"+j1+"').get('strategy"+j2+"phi start')")
            phi_end         = eval(j+".get('"+j1+"').get('strategy"+j2+"phi end')")
            num_images      = eval(j+".get('"+j1+"').get('strategy"+j2+"num of images')")
            res             = eval(j+".get('"+j1+"').get('strategy"+j2+"resolution')")
            completeness    = eval(j+".get('"+j1+"').get('strategy"+j2+"completeness')")
            redundancy      = eval(j+".get('"+j1+"').get('strategy"+j2+"redundancy')")
            distance        = eval(j+".get('"+j1+"').get('strategy"+j2+"distance')")
            time            = eval(j+".get('"+j1+"').get('strategy"+j2+"image exp time')")
            delta_phi       = eval(j+".get('"+j1+"').get('strategy"+j2+"delta phi')")            
            mosflm_trans = Utils.calcTransmission(self)            
            if self.multicrystalstrat:
                ref_data = self.preferences.get('reference_data')
                col = []
                for line in ref_data:       
                   col.append(line[3])
            if anom:
                print '\n\n\t\tOptimal Plan of ANOMALOUS data collection according to Mosflm'
            else:
                print '\n\n\t\tOptimal Plan of data collection according to Mosflm'
            print '\t\t================================\n'
            print '-----------------------------------------------------------------------------------'
            print ' N |  Phi_start |  N.of.images | Rot.width |  Exposure | Distance | % Transmission |'
            print '-----------------------------------------------------------------------------------'
            for x in run_number:
                number = int(x) - 1
                print '%2s | %8s   | %7s      |%9s  | %9s | %7s  |     %3.0f      |' \
                    % (x,phi_start[number],num_images[number],delta_phi,time,distance,mosflm_trans)            
        except:
            self.logger.exception('**summaryMosflm_strat Could not print Mosflm strategy to screen.**')            
        #Create Mosflm variable for php files.
        try:
            mosflm ='    <div id="container">\n'
            mosflm +='    <div class="full_width big">\n'
            mosflm +='     <div id="demo">\n'                                                  
            if anom:
                mosflm +='      <h1 class="results">Mosflm ANOMALOUS data collection strategy</h1>\n'
            else:
                mosflm +='      <h1 class="results">Mosflm data collection strategy</h1>\n'
            if self.high_dose:
                mosflm +='      <h4 class="results">Dosage is too high! Crystal will last for '+self.crystal_life+' images. Strategy calculated from realistic dosage.</h4>\n'
            if self.multicrystalstrat:
                for line in col:
                    mosflm +='       <h2 class="results">Data collected from '+line+' taken into account for strategy.</h2>\n'
            if anom:
                line    ='        <table cellpadding="0" cellspacing="0" border="10" class="display" id="stratanom">\n'
                mosflm += line
                mosflm0 = line
                mosflm1 = '        <table cellpadding="0" cellspacing="0" border="10" class="display" id="stratanom1">\n'
            else:
                line    ='        <table cellpadding="0" cellspacing="0" border="10" class="display" id="strat">\n'
                mosflm += line
                mosflm0 = line
                mosflm1 = '        <table cellpadding="0" cellspacing="0" border="10" class="display" id="strat1">\n'            
            mosflm +='          <thead align="center">\n'
            mosflm +='            <tr>\n'
            mosflm +='              <th>N</th>\n'
            mosflm +='              <th>Phi Start</th>\n'
            mosflm +='              <th>Phi End</th>\n'
            mosflm +='              <th>Rot Range</th>\n'
            mosflm +='              <th>N of Images</th>\n'
            mosflm +='              <th>Delta Phi</th>\n'
            mosflm +='              <th>Exposure time</th>\n'
            mosflm +='              <th>Distance</th>\n'
            mosflm +='              <th>% Transmission</th>\n'
            mosflm +='            </tr>\n'
            mosflm +='          </thead>\n'
            mosflm +='          <tbody align="center">\n'
            tot_sweep = []
            for x in run_number:
                number     = int(x) - 1
                sweep_end  = str(float(phi_start[number])+int(num_images[number])*(float(delta_phi)))
                sweep_size = str(int(num_images[number])*(float(delta_phi)))
                tot_sweep.append(float(sweep_size))
                if anom:
                    mosflm +='            <tr class="gradeD">\n'
                else:
                    mosflm +='            <tr class="gradeC">\n'
                mosflm +="              <td>"+str(x)+"</td>\n"
                mosflm +="              <td>"+str(phi_start[number])+"</td>\n"
                mosflm +="              <td>"+sweep_end+"</td>\n"
                mosflm +="              <td>"+sweep_size+"</td>\n"
                mosflm +="              <td>"+str(num_images[number])+"</td>\n"
                mosflm +="              <td>"+str(delta_phi)+"</td>\n"
                if self.high_dose:
                    mosflm +="              <td>1.00</td>\n"
                else:
                    mosflm +="              <td>"+time+"</td>\n"
                #mosflm +="              <td>" + time[number] + "</td>\n"
                mosflm +="              <td>"+distance+"</td>\n"
                mosflm +="              <td>"+"%5.2f"%mosflm_trans+"</td>\n"
                mosflm +="            </tr>\n\n"                
            mosflm +='          </tbody>\n'  
            mosflm +="        </table>\n"
            mosflm +="       </div>\n"
            mosflm +="      </div>\n"
            mosflm +="     </div>\n"            
            if anom:
                self.mosflm_strat_anom_summary = mosflm 
                self.mosflm_strat1_anom_summary = mosflm.replace(mosflm0,mosflm1)
            else:    
                self.mosflm_strat_summary = mosflm 
                self.mosflm_strat1_summary = mosflm.replace(mosflm0,mosflm1)            
            ni = sum(num_images)
            ts = sum(tot_sweep)
            mosflm_long ='    <div id="container">\n'
            mosflm_long +='    <div class="full_width big">\n'
            mosflm_long +='     <div id="demo">\n'                          
            mosflm_long +="      <h2 class='results'>Image: "+self.header.get('fullname')+"</h2>\n"
            if self.header2:
                mosflm_long +="      <h2 class='results'>Image: "+self.header2.get('fullname')+"</h2>\n"
            if anom:
                mosflm_long +='    <table cellpadding="2" cellspacing="2" border="0" class="display" id="mosflmanomdata">\n'
            else:
                mosflm_long +='    <table cellpadding="2" cellspacing="2" border="0" class="display" id="mosflmdata">\n'
            mosflm_long +='       <thead>\n'
            mosflm_long +='            <tr>\n'
            mosflm_long +='              <th></th>\n'
            mosflm_long +='              <th></th>\n'
            mosflm_long +='              <th></th>\n'
            mosflm_long +='              <th></th>\n'
            mosflm_long +='              <th></th>\n'
            mosflm_long +='            </tr>\n'
            mosflm_long +='          </thead>\n'
            mosflm_long +='          <tbody align="left">\n'
            mosflm_long +='            <tr>\n'
            mosflm_long +='              <th>Resolution Limit</th>\n'
            mosflm_long +='              <td>'+res+' Angstroms</td>\n'
            mosflm_long +='            </tr>\n'
            mosflm_long +='            <tr>\n'
            mosflm_long +='              <th>Anomalous data</th>\n'
            mosflm_long +='              <td>No</td>\n'
            mosflm_long +='            </tr>\n'  
            mosflm_long +='            <tr>\n'
            mosflm_long +='              <th>Phi_start - Phi_finish</th>\n'
            mosflm_long +='              <td>'+str(phi_start[0])+'-'+str(phi_end[-1])+'</td>\n'
            mosflm_long +='            </tr>\n'  
            mosflm_long +='            <tr>\n'
            mosflm_long +='              <th>Total rotation range</th>\n'
            mosflm_long +='              <td>'+str(ts)+' Degrees</td>\n'
            mosflm_long +='            </tr>\n'  
            mosflm_long +='            <tr>\n'
            mosflm_long +='              <th>Total N.of images</th>\n'
            mosflm_long +='              <td>'+str(ni)+'</td>\n'
            mosflm_long +='            </tr>\n'  
            mosflm_long +='            <tr>\n'
            mosflm_long +='              <th>Overall Completeness</th>\n'
            mosflm_long +='              <td>'+completeness+'</td>\n'
            mosflm_long +='            </tr>\n'  
            mosflm_long +='            <tr>\n'
            mosflm_long +='              <th>Redundancy</th>\n'
            mosflm_long +='              <td>'+str(redundancy)+'</td>\n'
            mosflm_long +='            </tr>\n'  
            mosflm_long +='          </tbody>\n'  
            mosflm_long +="        </table>\n"
            mosflm_long +="       </div>\n"
            mosflm_long +="      </div>\n"
            mosflm_long +="     </div>\n"
            if anom:
                self.mosflm_strat_anom_summary_long = mosflm_long
            else:
                self.mosflm_strat_summary_long = mosflm_long
        
        except:
            self.logger.exception('**Summary.summaryMosflm Could not Mosflm strategy html.**')           
    else:
        self.logger.debug('No Mosflm strategy')

def summaryShelx(self):
    """
    Print out SHELX CDE results to logger and create html/php variables.
    """
    self.logger.debug('Summary::summaryShelx')
    try:
        shelxc_res       = self.shelx_results.get('Shelx results').get('shelxc_res')
        shelxc_data      = self.shelx_results.get('Shelx results').get('shelxc_data')
        shelxc_isig      = self.shelx_results.get('Shelx results').get('shelxc_isig')
        shelxc_comp      = self.shelx_results.get('Shelx results').get('shelxc_comp')
        shelxc_dsig      = self.shelx_results.get('Shelx results').get('shelxc_dsig')            
        shelxd_try       = self.shelx_results.get('Shelx results').get('shelxd_try')            
        shelxd_cca       = self.shelx_results.get('Shelx results').get('shelxd_cca')
        shelxd_ccw       = self.shelx_results.get('Shelx results').get('shelxd_ccw')
        shelxd_fom       = self.shelx_results.get('Shelx results').get('shelxd_fom')
        #shelxd_best_occ  = self.shelx_results.get('Shelx results').get('shelxd_best_occ')
        shelxd_best_try  = self.shelx_results.get('Shelx results').get('shelxd_best_try')
        shelxd_best_cc   = self.shelx_results.get('Shelx results').get('shelxd_best_cc')
        shelxd_best_ccw  = self.shelx_results.get('Shelx results').get('shelxd_best_ccw')            
        shelxe_cc        = self.shelx_results.get('Shelx results').get('shelxe_cc')
        shelxe_contrast  = self.shelx_results.get('Shelx results').get('shelxe_contrast')
        shelxe_con       = self.shelx_results.get('Shelx results').get('shelxe_con')
        shelxe_sites     = self.shelx_results.get('Shelx results').get('shelxe_sites')
        shelxe_nosol     = self.shelx_results.get('Shelx results').get('shelxe_nosol')
        shelxe_fom       = self.shelx_results.get('Shelx results').get('shelxe_fom')
        shelxe_trace_pdb = self.shelx_results.get('Shelx results').get('shelxe_trace_pdb')
        shelxe_trace_cc  = self.shelx_results.get('Shelx results').get('shelxe_trace_cc')
        shelxe_nres      = self.shelx_results.get('Shelx results').get('shelxe_trace_nres')
                        
        shelxc  ='    <div id="container">\n'
        shelxc +='    <div class="full_width big">\n'
        shelxc +='      <div id="demo">\n'                       
        shelxc +='        <h1 class="results">SHELXC Results</h1>\n'
        shelxc +='        <table cellpadding="0" cellspacing="0" border="0" class="display" id="shelxc">\n'
        shelxc +='          <thead align="left">\n'            
        shelxc +='            <tr>\n'
        shelxc +='            </tr>\n'
        shelxc +='            <tr>\n'
        shelxc +='              <th>Resolution</th>\n'
        for i in range(0,10):
            shelxc +='              <th>'+shelxc_res[i]+'</th>\n'
        shelxc +='              <td>'+shelxc_res[10]+'</td>\n'
        """
        for line in shelxc_res:               
            shelxc +='              <th>'+line+'</th>\n'
        """
        shelxc +='            </tr>\n'            
        shelxc +='          </thead>\n'            
        shelxc +='          <tbody align="left">\n'                 
        shelxc +='            <tr class="gradeA">\n'
        shelxc +='              <th>N(data)</th>\n'
        for x in range(len(shelxc_data)):
            shelxc +="              <td>"+shelxc_data[x]+"</td>\n"
        shelxc +="            </tr>\n"
        shelxc +='            <tr class="gradeA">\n'
        shelxc +='              <th>Mean I/sig</th>\n'
        for x in range(len(shelxc_isig)):
            shelxc +="              <td>"+shelxc_isig[x]+"</td>\n"
        shelxc +="            </tr>\n"
        shelxc +='            <tr class="gradeA">\n'
        shelxc +='              <th>% Complete</th>\n'
        for x in range(len(shelxc_comp)):
            shelxc +="              <td>"+shelxc_comp[x]+"</td>\n"
        shelxc +="            </tr>\n"
        shelxc +='            <tr class="gradeA">\n'
        shelxc +='              <th>Mean d"/sig</th>\n'
        for x in range(len(shelxc_dsig)):
            shelxc +="              <td>"+shelxc_dsig[x]+"</td>\n"
        shelxc +="            </tr>\n"                        
        shelxc +='          </tbody>\n'            
        shelxc +="        </table>\n"            
        shelxc +="       </div>\n"            
        shelxc +="      </div>\n"  
        shelxc +="     </div>\n"  
        self.shelxc_summary = shelxc            
        
        shelxd  ='    <div id="container">\n'
        shelxd +='    <div class="full_width big">\n'
        shelxd +='      <div id="demo">\n'
        shelxd +='        <h1 class="results">SHELXD Results</h1>\n'
        if float(self.resolution) != 0.0:
            shelxd +='        <h4 class="results">User set SAD high resolution cutoff to '+str(self.resolution)+' Angstroms</h4>\n'
        shelxd +='        <table cellpadding="0" cellspacing="0" border="0" class="display" id="shelxd">\n'
        shelxd +='          <thead align="center">\n'
        shelxd +='            <tr>\n'
        shelxd +='              <th>Space Group</th>\n'
        shelxd +='              <th>Max CCall</th>\n'
        shelxd +='              <th>Max CCweak</th>\n'
        shelxd +='              <th>Max PATFOM</th>\n'
        shelxd +='            </tr>\n'
        shelxd +='          </thead>\n'
        shelxd +='          <tbody align="center">\n'
        sg = self.shelxd_dict.keys()
        for line in sg:
            inv_sg = Utils.convertSG(self,Utils.checkInverse(self,Utils.convertSG(self,line))[0],True)
            if self.shelx_nosol == False:
                if line == self.shelx_sg:
                    shelxd +='            <tr class="gradeD">\n'
                elif inv_sg == self.shelx_sg:
                    shelxd +='            <tr class="gradeD">\n'
                else:
                    shelxd +='            <tr class="gradeA">\n'  
            else:
                shelxd +='            <tr class="gradeA">\n'                       
            if line == inv_sg:
                shelxd +="              <td>"+line+"</td>\n"
            else:
                shelxd +="              <td>"+line+" ("+inv_sg+")</td>\n"
            """
            shelxd +="              <td>"+str(self.shelxd_dict[line][0])+"</td>\n"
            shelxd +="              <td>"+str(self.shelxd_dict[line][1])+"</td>\n"
            shelxd +="              <td>"+str(self.shelxd_dict[line][2])+"</td>\n"                
            """
            shelxd +="              <td>"+str(self.shelxd_dict[line].get('cc'))+"</td>\n"
            shelxd +="              <td>"+str(self.shelxd_dict[line].get('ccw'))+"</td>\n"
            shelxd +="              <td>"+str(self.shelxd_dict[line].get('fom'))+"</td>\n"          
            shelxd +="            </tr>\n\n"                           
        shelxd +='          </tbody>\n'
        shelxd +='        </table>\n'
        shelxd +='      </div>\n'
        shelxd +='     </div>\n'
        shelxd +='    </div>\n'            
        self.shelxd_summary = shelxd
                    
        shelxe  ='    <div id="container">\n'
        shelxe +='    <div class="full_width big">\n'
        shelxe +='      <div id="demo">\n'
        shelxe +='        <h1 class="results">SHELXE Results</h1>\n'
        if self.shelx_nosol:
            shelxe +='        <h4 class="results">SHELXE did NOT find a reliable solution, however here are the best results ('+str(self.shelx_sg)+')</h4>\n'
        else:
            shelxe +='        <h4 class="results">SHELXE may have found a solution in '+str(self.shelx_sg)+'</h4>\n'
            if shelxe_nosol == 'True':
                shelxe +='          <h4 class="results">SHELXE could not determine the "hand" reliably.</h4>\n'
        shelxe +='        <table cellpadding="0" cellspacing="0" border="0" class="display" id="shelxe">\n'
        shelxe +='          <thead align="center">\n'
        shelxe +='            <tr>\n'
        shelxe +='              <th>Site</th>\n'
        shelxe +='              <th>x</th>\n'
        shelxe +='              <th>y</th>\n'
        shelxe +='              <th>z</th>\n'
        shelxe +='              <th>occ*Z</th>\n'
        shelxe +='              <th>density</th>\n'
        shelxe +='            </tr>\n'
        shelxe +='          </thead>\n'
        shelxe +='          <tbody align="center">\n'
        for line in shelxe_sites:
            shelxe +='            <tr class="gradeA">\n'
            shelxe +="              <td>"+line.split()[0]+"</td>\n"
            shelxe +="              <td>"+line.split()[1]+"</td>\n"
            shelxe +="              <td>"+line.split()[2]+"</td>\n"
            shelxe +="              <td>"+line.split()[3]+"</td>\n"
            shelxe +="              <td>"+line.split()[4]+"</td>\n"
            shelxe +="              <td>"+line.split()[5]+"</td>\n"
            shelxe +="            </tr>\n"                           
        shelxe +='          </tbody>\n'
        shelxe +='        </table>\n'
        shelxe +='        <table cellpadding="0" cellspacing="0" border="0" class="display" id="shelxe2">\n'
        shelxe +='          <tbody align="left">\n'
        shelxe +='            <br>\n'
        shelxe +='            <tr>\n'
        shelxe +='              <th>SHELXE FOM</th>\n'
        shelxe +="              <td>"+shelxe_fom+"</td>\n"
        shelxe +='            </tr>\n'
        shelxe +='            <tr>\n'
        shelxe +='              <th>SHELXE Pseudo-free CC</th>\n'
        shelxe +="              <td>"+shelxe_cc+"</td>\n"
        shelxe +="            </tr>\n"                
        if self.shelx_build:
            shelxe +='            <tr>\n'
            shelxe +='              <th>SHELXE autotraced # of residues</th>\n'
            shelxe +="              <td>"+shelxe_nres+"</td>\n"
            shelxe +='            </tr>\n'
            shelxe +='            <tr>\n'
            shelxe +='              <th>SHELXE autotraced CC (>25 is good)</th>\n'
            shelxe +="              <td>"+shelxe_trace_cc+"</td>\n"
            shelxe +='            </tr>\n'
        shelxe +='          </tbody>\n'
        shelxe +='        </table>\n'
        if self.build:
            if self.shelx_nosol == False:
                if self.pp:
                    if self.autosol_failed:
                        shelxe +='          <h4 class="results">Phenix AutoSol FAILED.</h4>\n'                            
                    else:
                        shelxe +='          <h3 class="results">Phenix AutoSol completed successfully.</h3>\n'                            
                else:
                    if self.build:
                        shelxe +='          <h4 class="results">Phasing and autobuilding will now be attempted in Phenix AutoSol.</h4>\n'
        shelxe +='      </div>\n'
        shelxe +='     </div>\n'
        shelxe +='    </div>\n'            
        self.shelxe_summary = shelxe
    
    except:
        self.logger.exception('**ERROR in Summary.summaryShelx**')

def summaryAutoSol(self,autobuild=False):
    """
    Create html variables.
    """
    self.logger.debug('Summary::summaryAutoSol')
    try:
        #if self.autosol_results:               
        dir       = self.autosol_results.get('AutoSol results').get('directory')
        sg        = self.autosol_results.get('AutoSol results').get('sg')
        bayescc   = self.autosol_results.get('AutoSol results').get('bayes-cc')
        fom       = self.autosol_results.get('AutoSol results').get('fom')
        sites_st  = self.autosol_results.get('AutoSol results').get('sites_start')
        sites_ref = self.autosol_results.get('AutoSol results').get('sites_refined')
        res       = self.autosol_results.get('AutoSol results').get('res_built')
        side      = self.autosol_results.get('AutoSol results').get('side_built')
        chains    = self.autosol_results.get('AutoSol results').get('num_chains')
        mmcc      = self.autosol_results.get('AutoSol results').get('model-map_cc')
        r         = self.autosol_results.get('AutoSol results').get('r/rfree')
        
        if autobuild:
            #if self.autobuild_results:               
            res       = self.autobuild_results.get('AutoBuild results').get('AutoBuild_built')
            placed    = self.autobuild_results.get('AutoBuild results').get('AutoBuild_placed')
            chains    = self.autobuild_results.get('AutoBuild results').get('AutoBuild_chains')
            mmcc      = self.autobuild_results.get('AutoBuild results').get('AutoBuild_mmcc')
            rfree     = self.autobuild_results.get('AutoBuild results').get('AutoBuild_rfree')
            rfac      = self.autobuild_results.get('AutoBuild results').get('AutoBuild_rfac')
            score     = self.autobuild_results.get('AutoBuild results').get('AutoBuild_score')
            #self.pdb  = self.autobuild_results.get('AutoBuild results').get('AutoBuild_pdb')
            #self.mtz  = self.autobuild_results.get('AutoBuild results').get('AutoBuild_mtz')
            r = rfac+' / '+rfree
          
        autosol ='    <div id="container">\n'
        autosol +='    <div class="full_width big">\n'
        autosol +='     <div id="demo">\n'
        if autobuild:
            autosol +='     <h1 class="results">Phenix AutoBuild Results</h1>\n'
        else:
            autosol +='     <h1 class="results">Phenix AutoSol Results</h1>\n'
        autosol +='     <table cellpadding="2" cellspacing="2" border="0" class="display" id="autosol">\n'
        autosol +='       <thead align="left">\n'
        autosol +='            <tr>\n'
        autosol +='              <th>Phasing Results</th>\n'
        autosol +='              <th></th>\n'
        autosol +='              <th></th>\n'
        autosol +='              <th></th>\n'
        autosol +='              <th></th>\n'
        autosol +='            </tr>\n'
        autosol +='          </thead>\n'
        autosol +='          <tbody align="left">\n'
        autosol +='            <tr>\n'
        autosol +='              <th>Space Group</th>\n'
        autosol +='              <td>'+sg+'</td>\n'
        autosol +='            </tr>\n'
        autosol +='            <tr>\n'
        autosol +='              <th>Bayesian CC</th>\n'
        autosol +='              <td>'+bayescc+'</td>\n'
        autosol +='            </tr>\n'  
        autosol +='            <tr>\n'
        autosol +='              <th>FOM</th>\n'
        autosol +='              <td>'+fom+'</td>\n'
        autosol +='            </tr>\n'  
        autosol +='            <tr>\n'
        autosol +='              <th>Number of starting sites</th>\n'
        autosol +='              <td>'+sites_st+'</td>\n'
        autosol +='            </tr>\n'  
        autosol +='            <tr>\n'
        autosol +='              <th>Number of refined sites</th>\n'
        autosol +='              <td>'+sites_ref+'</td>\n'
        autosol +='            </tr>\n'  
        """
        autosol +='            <tr>\n'
        autosol +='              <th>Density modified R-factor</th>\n'
        autosol +='              <td>' + dmr + '</td>\n'
        autosol +='            </tr>\n'  
        """
        autosol +='            <tr>\n'
        autosol +='              <th></th>\n'
        autosol +='              <td></td>\n'
        autosol +='            </tr>\n'  
        autosol +='            <tr>\n'
        autosol +='              <th></th>\n'
        autosol +='              <td></td>\n'
        autosol +='            </tr>\n'
        autosol +='          </tbody>\n'
        autosol +='        <thead align="left">\n'
        autosol +='            <tr>\n'
        autosol +='              <th>Building Results</th>\n'
        autosol +='               <th></th>\n'
        autosol +='               <th></th>\n'
        autosol +='               <th></th>\n'
        autosol +='               <th></th>\n'
        autosol +='            </tr>\n'
        autosol +='          </thead>\n'
        autosol +='          <tbody align="left">\n'
        autosol +='            <tr>\n'
        autosol +='              <th>Number of residues built</th>\n'
        autosol +='              <td>'+res+'</td>\n'
        autosol +='            </tr>\n'  
        autosol +='            <tr>\n'
        autosol +='              <th>Number of side-chains built</th>\n'
        autosol +='              <td>'+side+'</td>\n'
        autosol +='            </tr>\n'  
        autosol +='            <tr>\n'
        autosol +='              <th>Total number of chains</th>\n'
        autosol +='              <td>'+chains+'</td>\n'
        autosol +='            </tr>\n'  
        autosol +='            <tr>\n'
        autosol +='              <th>model-map CC</th>\n'
        autosol +='              <td>'+mmcc+'</td>\n'
        autosol +='            </tr>\n'  
        autosol +='            <tr>\n'
        autosol +='              <th>Refined R/R-free</th>\n'
        autosol +='              <td>'+r+'</td>\n'
        autosol +='            </tr>\n'              
        if autobuild:
            autosol +='            <tr>\n'
            autosol +='              <th>Number of sequenced residues built</th>\n'
            autosol +='              <td>'+placed+'</td>\n'
            autosol +='            </tr>\n'  
            autosol +='            <tr>\n'
            autosol +='              <th>Build Score</th>\n'
            autosol +='              <td>'+score+'</td>\n'
            autosol +='            </tr>\n'    
        autosol +='          </tbody>\n'  
        autosol +="        </table>\n"
        autosol +="       </div>\n"
        autosol +="      </div>\n"
        autosol +="     </div>\n"
        """
        autosol +='    <div id="container">\n'
        autosol +='     <div class="full_width big">\n'
        autosol +='      <div id="demo">\n'
        autosol +="      <h1 class='Results'>Output PDB file</h1>\n"
        autosol +='       <div id="Jmol_mainWrapper">\n'
        autosol +='        <div style="margin:auto;width:550px;height:550px;border:solid 1px lightgray;padding: 0.5em;" id="jmol_box">\n'
        autosol +="         <script>\n"
        autosol +='            jmolInitialize("js/jmol-12.1.13",true);\n'
        autosol +='            jmolApplet(["100%","100%"],\n'
        autosol +='                        "load '+pdb+';select all; spacefill off; wireframe off; backbone off; cartoon on;color cartoon structure;set antialiasDisplay true;");\n'
        autosol +="         </script>\n"
        autosol +="        </div>\n"
        autosol +="        <h2 class='Results'>Tip: right-mouse click on Jmol to get access to additional Jmol functionality.</h2>\n"
        autosol +="       </div>\n"
        autosol +="      </div>\n"
        autosol +="     </div>\n"
        autosol +="    </div>\n"
        """            
        if autobuild:
            self.autobuild_summary = autosol
        else:
            self.autosol_summary = autosol
    
    except:
        self.logger.exception('**ERROR in Summary.summaryAutoSol**')

def summaryXtriage(self):
    """
    Create the summary info from Xtriage for html file.
    """
    self.logger.debug('Summary::summaryXtriage')
    try:
        if self.xtriage_results:               
            xtriage_anom       = self.xtriage_results.get('Xtriage results').get('Xtriage anom')
            xtriage_z          = self.xtriage_results.get('Xtriage results').get('Xtriage z-score')
            xtriage_pat        = self.xtriage_results.get('Xtriage results').get('Xtriage pat')
            xtriage_sum        = self.xtriage_results.get('Xtriage results').get('Xtriage summary')
            #xtriage_log        = self.xtriage_results.get('Xtriage results').get('Xtriage log')
            xtriage_pts        = self.xtriage_results.get('Xtriage results').get('Xtriage PTS')
            xtriage_pts_info   = self.xtriage_results.get('Xtriage results').get('Xtriage PTS info')
            xtriage_twin       = self.xtriage_results.get('Xtriage results').get('Xtriage twin')
            xtriage_twin_info  = self.xtriage_results.get('Xtriage results').get('Xtriage twin info')
            
            xtriage  ='    <div id="container">\n'
            xtriage +='    <div class="full_width big">\n'
            xtriage +='     <div id="demo">\n'
            xtriage +='     <h1 class="results">Unit Cell Info</h1>\n'
            xtriage +='        <table cellpadding="0" cellspacing="0" border="1" class="display" id="xtriage-auto2">\n'               
            xtriage +='          <thead align="center">\n'
            xtriage +='            <tr>\n'
            xtriage +='              <th>Space Group</th>\n'
            xtriage +='              <th>a</th>\n'
            xtriage +='              <th>b</th>\n'
            xtriage +='              <th>c</th>\n'
            xtriage +='              <th>&alpha;</th>\n'
            xtriage +='              <th>&beta;</th>\n'
            xtriage +='              <th>&gamma;</th>\n'
            xtriage +='            </tr>\n'
            xtriage +='          </thead>\n'
            xtriage +='          <tbody align="center">\n'
            xtriage +='            <tr class="gradeA">\n'
            xtriage +="              <td>"+self.input_sg+"</td>\n"
            xtriage +="              <td>"+self.cell2[0]+"</td>\n"
            xtriage +="              <td>"+self.cell2[1]+"</td>\n"
            xtriage +="              <td>"+self.cell2[2]+"</td>\n"
            xtriage +="              <td>"+self.cell2[3]+"</td>\n"
            xtriage +="              <td>"+self.cell2[4]+"</td>\n"
            xtriage +="              <td>"+self.cell2[5]+"</td>\n"
            xtriage +="            </tr>\n"
            xtriage +='          </tbody>\n'
            xtriage +='        </table>\n'
            xtriage +='       </div>\n'
            xtriage +='      </div>\n'
            xtriage +='     </div>\n'           
            xtriage +='    <div id="container">\n'
            xtriage +='    <div class="full_width big">\n'
            xtriage +='     <div id="demo">\n'
            xtriage +='     <h1 class="results">Patterson Analysis</h1>\n'
            if xtriage_pts:
                self.pts = True
                xtriage +='     <h4 class="results">WARNING! Pseudo-translation is detected.</h4>\n'            
            xtriage +='     <table cellpadding="2" cellspacing="2" border="0" class="display" id="xtriage_pat">\n'
            xtriage +='       <thead align="left">\n'
            xtriage +='            <tr>\n'
            xtriage +='              <th>Off-origin Peak</th>\n'
            xtriage +='              <th>Height (Percent compared to origin)</th>\n'
            """
            if xtriage_pat.get('1').has_key('dist'):
                xtriage +='              <th>Distance to origin</th>\n'
            """
            xtriage +='              <th>X</th>\n'
            xtriage +='              <th>Y</th>\n'
            xtriage +='              <th>Z</th>\n'
            xtriage +='            </tr>\n'
            xtriage +='          </thead>\n'
            xtriage +='          <tbody align="left">\n'
            peaks = xtriage_pat.keys()
            peaks.sort()
            for x in range(len(peaks)):
                if xtriage_pts:
                    xtriage +='            <tr class="gradeD">\n'
                else:
                    xtriage +='            <tr class="gradeA">\n'
                xtriage +='              <td>'+peaks[x]+'</td>\n'
                pk = xtriage_pat[peaks[x]].get('peak')
                xtriage +='              <td>'+pk+'</td>\n'
                xtriage +='              <td>'+xtriage_pat[peaks[x]].get('frac x')+'</td>\n'
                xtriage +='              <td>'+xtriage_pat[peaks[x]].get('frac y')+'</td>\n'
                xtriage +='              <td>'+xtriage_pat[peaks[x]].get('frac z')+'</td>\n'
                xtriage +='            </tr>\n'            
            xtriage +="          </tbody>\n"
            xtriage +="         </table>\n"           
            #if xtriage_pts_info.has_key('space group'):
            keys = xtriage_pts_info.keys()
            if len(keys) != 0:
                xtriage +='     <h4 class="results">If the observed pseudo-translationals are crystallographic, then the following info is possible.</h4>\n'           
                xtriage +='     <table cellpadding="2" cellspacing="2" border="0" class="display" id="xtriage_pts">\n'
                xtriage +='       <thead align="left">\n'
                xtriage +='            <tr>\n'
                xtriage +='              <th>Space Group</th>\n'
                xtriage +='              <th>Operator</th>\n'
                xtriage +='              <th>Unit Cell</th>\n'
                xtriage +='            </tr>\n'
                xtriage +='          </thead>\n'
                xtriage +='          <tbody align="left">\n'
                for key in keys:
                    xtriage +='            <tr class="gradeD">\n'
                    xtriage +='              <td>'+xtriage_pts_info[key].get('space group')+'</td>\n'
                    xtriage +='              <td>'+xtriage_pts_info[key].get('operator')+'</td>\n'
                    xtriage +='              <td>'+xtriage_pts_info[key].get('cell')+'</td>\n'
                    xtriage +='            </tr>\n'
                xtriage +="          </tbody>\n"
                xtriage +="         </table>\n"        
            xtriage +="        </div>\n"
            xtriage +="       </div>\n"
            xtriage +="     </div>\n"
        
            if xtriage_twin:
                self.twin = True
                laws = xtriage_twin_info.keys()
                xtriage +='    <div id="container">\n'
                xtriage +='    <div class="full_width big">\n'
                xtriage +='     <div id="demo">\n'
                xtriage +='     <h1 class="results">Twinning Analysis</h1>\n'
                xtriage +='     <h2 class="results">Carefully inspect the table and plots to determine if twinning may be present.</h2>\n'
                xtriage +='     <table cellpadding="2" cellspacing="2" border="0" class="display" id="xtriage_twin">\n'
                xtriage +='       <thead align="left">\n'
                xtriage +='            <tr>\n'
                xtriage +='              <th>Operator</th>\n'
                xtriage +='              <th>Type</th>\n'
                xtriage +='              <th>Axis</th>\n'
                xtriage +='              <th>Apparent SG</th>\n'
                xtriage +='              <th>R obs</th>\n'
                xtriage +='              <th>Britton alpha</th>\n'
                xtriage +='              <th>H-test alpha</th>\n'
                xtriage +='              <th>ML alpha</th>\n'
                xtriage +='            </tr>\n'
                xtriage +='          </thead>\n'
                xtriage +='          <tbody align="left">\n'
                for law in laws:
                    xtriage_twin_info[law]
                    xtriage +='            <tr class="gradeA">\n'                
                    xtriage +='              <td>'+law+'</td>\n'
                    xtriage +='              <td>'+xtriage_twin_info[law].get('type')+'</td>\n'
                    xtriage +='              <td>'+xtriage_twin_info[law].get('axis')+'</td>\n'
                    xtriage +='              <td>'+xtriage_twin_info[law].get('sg')+'</td>\n'
                    xtriage +='              <td>'+xtriage_twin_info[law].get('r_obs')+'</td>\n'
                    xtriage +='              <td>'+xtriage_twin_info[law].get('britton')+'</td>\n'
                    xtriage +='              <td>'+xtriage_twin_info[law].get('h-test')+'</td>\n'
                    xtriage +='              <td>'+xtriage_twin_info[law].get('ml')+'</td>\n'            
                    xtriage +='            </tr>\n'
                xtriage +="          </tbody>\n"
                xtriage +="         </table>\n"        
                xtriage +="        </div>\n"
                xtriage +="       </div>\n"
                xtriage +="     </div>\n"
                    
            if xtriage_sum:
                xtriage +='    <div id="container">\n'
                xtriage +='    <div class="full_width big">\n'
                xtriage +='     <div id="demo">\n'
                xtriage +='     <h1 class="results">Xtriage Summary</h1>\n'
                xtriage +='      <P>\n'
                for line in xtriage_sum:
                    xtriage +='         '+line+'\n'
                xtriage +='      </P>\n'
                xtriage +="        </div>\n"
                xtriage +="       </div>\n"
                xtriage +="     </div>\n"
                
            self.xtriage_summary = xtriage
    
    except:
        self.logger.exception('**ERROR in Summary.summaryXtraige**')
    
def summaryMolrep(self):
    """
    Prepare images nd tables for html output.
    """
    self.logger.debug('Summary::summaryMolrep')
    try:
        if self.molrep_results:
            molrep_jpg        = self.molrep_results.get('Molrep results').get('Molrep jpg')
            molrep_pts        = self.molrep_results.get('Molrep results').get('Molrep PTS')
            molrep_pk         = self.molrep_results.get('Molrep results').get('Molrep PTS_pk')
            
            molrep  ='    <div id="container">\n'
            molrep +='    <div class="full_width big">\n'
            molrep +='      <div id="demo">\n'       
            molrep +="      <h1 class='Results'>Molrep Self-Rotation Function</h1>\n"
            #molrep +="      <object data='"+molrep_jpg+"' align=center type='image/jpg'></object>\n"  
            #molrep +="      <div id='molrep_jpg'></div>\n"
            if self.gui:
                molrep +="      <div id='molrep_jpg' style='text-align:center'></div>\n"
            else:
                molrep +="      <div id='molrep_rf.jpg' style='text-align:center'></div>\n"
            if molrep_pts:
                peaks = molrep_pk.keys()           
                peaks.remove('origin')
                peaks.sort()
                o_pk = molrep_pk['origin'].get('peak')
                o_sig = molrep_pk['origin'].get('psig')
                molrep +='     <h4 class="results">WARNING pseudotranslation is detected</h4>\n'
                molrep +='     <table cellpadding="2" cellspacing="2" border="0" class="display" id="molrep">\n'
                molrep +='       <thead align="left">\n'
                molrep +='            <tr>\n'
                molrep +='              <th>Peak</th>\n'
                molrep +='              <th>Height</th>\n'
                molrep +='              <th>Height/sig</th>\n'
                molrep +='              <th>% of origin peak</th>\n'
                molrep +='              <th>X</th>\n'
                molrep +='              <th>Y</th>\n'
                molrep +='              <th>Z</th>\n'
                molrep +='            </tr>\n'
                molrep +='          </thead>\n'
                molrep +='          <tbody align="left">\n'            
                molrep +='            <tr class="gradeA">\n'
                molrep +='              <td>Origin</td>\n'
                molrep +='              <td>'+o_pk+'</td>\n'
                molrep +='              <td>'+o_sig+'</td>\n' 
                molrep +='              <td>100</td>\n'
                molrep +='              <td>0</td>\n'
                molrep +='              <td>0</td>\n'
                molrep +='              <td>0</td>\n'
                molrep +='            </tr>\n'
                for x in range(len(peaks)):
                    molrep +='            <tr class="gradeA">\n'
                    molrep +='              <td>'+peaks[x]+'</td>\n'
                    pk = molrep_pk[peaks[x]].get('peak')
                    sig = molrep_pk[peaks[x]].get('psig')
                    per = str(round(float(pk)/float(o_pk)*100))
                    molrep +='              <td>'+pk+'</td>\n'
                    molrep +='              <td>'+sig+'</td>\n'
                    molrep +='              <td>'+per+'</td>\n'
                    molrep +='              <td>'+molrep_pk[peaks[x]].get('frac x')+'</td>\n'
                    molrep +='              <td>'+molrep_pk[peaks[x]].get('frac y')+'</td>\n'
                    molrep +='              <td>'+molrep_pk[peaks[x]].get('frac z')+'</td>\n'
                    molrep +='            </tr>\n'
            molrep +="          </tbody>\n"
            molrep +="         </table>\n"        
            molrep +="        </div>\n"
            molrep +="       </div>\n"
            molrep +="     </div>\n"
            self.molrep_summary = molrep
        
    except:
        self.logger.exception('**ERROR in Summary.summaryMolrep**')

def summaryCell(self,input='phaser'):
    """
    Summary of unit cell analysis.
    """        
    self.logger.debug('Summary::summaryCell')
    try:           
        sol = []
        if input == 'phaser':
            title = 'phaser-cell'
            title2 = 'phaser-pdb'
        elif input == 'pdbquery':
            title = 'pdbquery-cell'
            title2 = 'pdbquery-pdb'
        else:
            title = 'sad-cell'
            title2 = 'sad-pdb'
        cell  ='    <div id="container">\n'
        cell +='    <div class="full_width big">\n'
        cell +='      <div id="demo">\n'                       
        cell +='        <h1 class="results">Unit Cell Analysis</h1>\n'
        cell +='        <table cellpadding="0" cellspacing="0" border="1" class="display" id="'+title+'">\n'         
        cell +='          <thead align="center">\n'
        cell +='            <tr>\n'
        cell +='              <th>a</th>\n'
        cell +='              <th>b</th>\n'
        cell +='              <th>c</th>\n'
        cell +='              <th>&alpha;</th>\n'
        cell +='              <th>&beta;</th>\n'
        cell +='              <th>&gamma;</th>\n'
        cell +='            </tr>\n'
        cell +='          </thead>\n'
        cell +='          <tbody align="center">\n'
        cell +='            <tr class="gradeA">\n'
        cell +="              <td>"+str(self.cell2[0])+"</td>\n"
        cell +="              <td>"+str(self.cell2[1])+"</td>\n"
        cell +="              <td>"+str(self.cell2[2])+"</td>\n"
        cell +="              <td>"+str(self.cell2[3])+"</td>\n"
        cell +="              <td>"+str(self.cell2[4])+"</td>\n"
        cell +="              <td>"+str(self.cell2[5])+"</td>\n"
        cell +="            </tr>\n"
        cell +='          </tbody>\n'
        cell +='        </table>\n'
        cell +='       </div>\n'
        cell +='      </div>\n'
        cell +='     </div>\n'        
        self.cell_summary = cell
        percent = False
        if input == 'phaser':
            pdbs = self.phaser_results.keys()
            percent = False
            #span = '4'
        else:
            if self.percent:
                percent = str(self.percent*100)
            pdbs = self.cell_output.keys()
            #span = '3'
        if pdbs != ['None']:
            opdb  ='    <div id="container">\n'
            opdb +='    <div class="full_width big">\n'
            opdb +='      <div id="demo">\n'
            if input != 'phaser':
                if percent:
                    opdb +='        <h4 class="results">Structures with unit cell dimensions within +/- '+percent+'%</h4>\n'
                else:
                    opdb +='        <h4 class="results">Structures with similar unit cell dimensions</h4>\n'
            opdb +='        <table cellpadding="0" cellspacing="0" border="0" class="display" id="'+title2+'">\n'
            opdb +='          <thead align="left">\n'            
            opdb +='            <tr>\n'
            opdb +="              <th colspan='2'></th>\n"
            #opdb +="              <th colspan='"+span+"' align='center'>Phaser Statistics</th>\n"
            opdb +="              <th colspan='4' align='center'>Phaser Statistics</th>\n"
            opdb +='            </tr>\n'
            opdb +='            <tr>\n'
            if input == 'phaser':
                opdb +='              <th>Space Group</th>\n'
            else:
                opdb +='              <th>PDB ID</th>\n'
            opdb +='              <th>Description</th>\n'
            opdb +='              <th>LL-Gain</th>\n'
            opdb +='              <th>RF Z-score</th>\n'
            opdb +='              <th>TF Z-score</th>\n'
            opdb +='              <th># of Clashes</th>\n'
            opdb +='              <th>&nbsp</th>\n'
            opdb +='            </tr>\n'
            opdb +='          </thead>\n'
            opdb +='          <tbody align="left">\n'
            for line in pdbs:
                llg   = self.phaser_results[line].get('AutoMR results').get('AutoMR gain')
                rfz   = self.phaser_results[line].get('AutoMR results').get('AutoMR rfz')
                tfz   = self.phaser_results[line].get('AutoMR results').get('AutoMR tfz')
                clash = self.phaser_results[line].get('AutoMR results').get('AutoMR clash')
                if llg == 'No solution':
                    opdb +='            <tr class="gradeA">\n'
                elif llg == 'Timed out':
                    opdb +='            <tr class="gradeA">\n'
                else:
                    sol.append(line)
                    opdb +='            <tr class="gradeD">\n'
                opdb +='              <td>'+line+'</td>\n'
                if input == 'phaser':
                    if self.pdb_name:
                        opdb +='              <td>'+self.pdb_name+'</td>\n'
                    elif self.pdb_code:
                        opdb +='              <td>'+os.path.basename(self.input_pdb)+'</td>\n'
                    else:
                        opdb +='              <td>search model pdb</td>\n'
                else:
                    #Only grabbing the first description to make table simpler.
                    if self.cell_output[line].has_key('Name'):
                        opdb +='              <td>'+self.cell_output[line].get('Name')[0][:50]+'</td>\n'
                    else:
                        opdb +='              <td>No Name</td>\n'
                opdb +='              <td>'+llg+'</td>\n'
                opdb +='              <td>'+rfz+'</td>\n'
                opdb +='              <td>'+tfz+'</td>\n'
                opdb +='              <td>'+clash+'</td>\n'
                if (llg in ('No solution','NA','Timed out','Still running')):
                    opdb +='              <td></td>\n'
                else:
                    opdb +='              <td><button id="mr:'+line+'">Download</button></td>\n'
                opdb +="            </tr>\n"
            opdb +='          </tbody>\n'            
            opdb +="        </table>\n"            
            opdb +="       </div>\n"            
            opdb +="      </div>\n"  
            opdb +="     </div>\n"
            if len(sol) != 0:
                #dir = self.phaser_results[sol[0]].get('AutoMR results').get('AutoMR dir')
                #tar_path = os.path.join(dir,sol[0]+'.tar.bz2')
                tar_path = os.path.join(self.working_dir,sol[0]+'.tar.bz2')
                tooltips  = '        //Tooltips\n'                    
                tooltips += "        $('#pdb tbody td').each(function(){\n"
                tooltips += "           if ($(this).text() == '"+sol[0]+"') {\n"
                tooltips += "                this.setAttribute('title','"+tar_path+"');\n"
                tooltips += '}\n'                    
                for line in sol[1:]:                    
                    #dir = self.phaser_results[line].get('AutoMR results').get('AutoMR dir')
                    #tar_path = os.path.join(dir,line+'.tar.bz2')
                    tar_path = os.path.join(self.working_dir,line+'.tar.bz2')
                    tooltips += "           else if ($(this).text() == '"+line+"') {\n"
                    tooltips += "                this.setAttribute('title','"+tar_path+"');\n"
                    tooltips += '}\n'
                tooltips += '});\n'
                self.tooltips = tooltips
                            
        else:
            opdb  ='    <div id="container">\n'
            opdb +='    <div class="full_width big">\n'
            opdb +='      <div id="demo">\n'
            if percent:
                opdb +='        <h4 class="results">There are no structures deposited in the PDB with unit cell dimensions within +- '+percent+' %</h4>\n'
            else:
                opdb +='        <h4 class="results">There are no structures in the PDB with similar unit cell dimensions</h4>\n'
            opdb +="       </div>\n"            
            opdb +="      </div>\n"  
            opdb +="     </div>\n"                        
        self.pdb_summary = opdb
    
    except:
        self.logger.exception('**ERROR in Summary.summaryCell**')

def summaryAutoCell(self,labelit=False):
    """
    show unit cell info in output html file.
    """
    #Grab unit cell results and creates variable for displaying in summary_short.php.
    self.logger.debug('Summary::summaryCell')
    try:
        if labelit:
            mosflm_res        = self.labelit_results.get('Labelit results').get('mosflm_res')
            mosflm_mos        = self.labelit_results.get('Labelit results').get('mosflm_mos')
        best = 'bestfile.par'
        if os.path.exists(best):
            file  = open('bestfile.par','r') 
            for line in file:
                if line.startswith('SYMMETRY'):
                    split = line.split()
                    symmetry = split[1]
                if line.startswith('CELL'):
                    split2 = line.split()
                    A      =  split2[1]
                    B      =  split2[2]
                    C      =  split2[3] 
                    alpha  =  split2[4]
                    beta   =  split2[5]
                    gamma  =  split2[6]                   
            file.close()                   
            if labelit:
                auto  ='        <table cellpadding="0" cellspacing="0" border="1" class="display" id="auto">\n'
            else:
                auto  ='        <table cellpadding="0" cellspacing="0" border="1" class="display" id="stac-auto">\n'
            auto +='          <thead align="center">\n'
            auto +='            <tr>\n'
            auto +='              <th>Space Group</th>\n'
            auto +='              <th>a</th>\n'
            auto +='              <th>b</th>\n'
            auto +='              <th>c</th>\n'
            auto +='              <th>&alpha;</th>\n'
            auto +='              <th>&beta;</th>\n'
            auto +='              <th>&gamma;</th>\n'
            if labelit:
                auto +='              <th>mosaicity</th>\n'
                auto +='              <th>resolution</th>\n'
            auto +='            </tr>\n'
            auto +='          </thead>\n'
            auto +='          <tbody align="center">\n'
            auto +='            <tr class="gradeA">\n'
            auto +="              <td>"+symmetry + "</td>\n"
            auto +="              <td>"+A+"</td>\n"
            auto +="              <td>"+B+"</td>\n"
            auto +="              <td>"+C+"</td>\n"
            auto +="              <td>"+alpha+"</td>\n"
            auto +="              <td>"+beta+"</td>\n"
            auto +="              <td>"+gamma+"</td>\n"
            if labelit:
                auto +="              <td>"+mosflm_mos[0]+"</td>\n"
                auto +="              <td>"+mosflm_res[0]+"</td>\n"
            auto +="            </tr>\n"
            auto +='          </tbody>\n'
            auto +='        </table>\n'
            auto +='       </div>\n'
            auto +='      </div>\n'
            auto +='     </div>\n'           
            if labelit:
                self.auto_summary = auto
            else:
                self.auto1_summary = auto

    except:
        self.logger.exception('**ERROR in Summary.summaryCell**')

def summarySTAC(self):
    """
    Generate STAC html/php file.
    """
    self.logger.debug('Summary::summarySTAC')
    try:    
        #STAC alignment results
        if self.stacalign_results:
            v1                           = self.stacalign_results.get('STAC align results').get('v1')
            v2                           = self.stacalign_results.get('STAC align results').get('v2')
            align_omega                  = self.stacalign_results.get('STAC align results').get('omega')
            align_kappa                  = self.stacalign_results.get('STAC align results').get('kappa')
            align_phi                    = self.stacalign_results.get('STAC align results').get('phi')
            trans                        = self.stacalign_results.get('STAC align results').get('trans')
            #align_rank                   = self.stacalign_results.get('STAC align results').get('rank')
            goni_lim                     = self.stacalign_results.get('STAC align results').get('goni limited')
            no_sol                       = self.stacalign_results.get('STAC align results').get('no_sol')
        #STAC strategy results       
        if self.stac_strat:            
            if self.stacstrat_results:
                if self.stacstrat_results.get('STAC strat results') != 'FAILED':
                    strat_id                     = self.stacstrat_results.get('STAC strat results').get('strat ID')
                    omega_start                  = self.stacstrat_results.get('STAC strat results').get('omega start')
                    omega_end                    = self.stacstrat_results.get('STAC strat results').get('omega finish')
                    strat_kappa                  = self.stacstrat_results.get('STAC strat results').get('kappa')
                    strat_phi                    = self.stacstrat_results.get('STAC strat results').get('phi')
                    completeness                 = self.stacstrat_results.get('STAC strat results').get('completeness')
                    strat_rank                   = self.stacstrat_results.get('STAC strat results').get('rank')                        
        a = '(1.0;0.0;0.0)'
        b = '(0.0;1.0;0.0)'
        c = '(0.0;0.0;1.0)'
        #Changing v1
        temp = []
        index1 = False
        index2 = False
        index3 = False        
        for line in v1:
            temp.append(line) 
            if line.startswith(a):
                index1= temp.index(line)
                temp.remove(line)
                temp.insert(index1,'a*')
            if line.startswith(b):
                index2= temp.index(line)
                temp.remove(line)
                temp.insert(index2,'b*')                
            if line.startswith(c):                 
                index3= temp.index(line)                   
                temp.remove(line)
                temp.insert(index3,'c*')
        v1 = temp           
        #Changing v2
        temp = []        
        index1 = False
        index2 = False
        index3 = False        
        for line in v2:
            temp.append(line) 
            if line.startswith(a):
                index1= temp.index(line)
                temp.remove(line)
                temp.insert(index1,'a*')
            if line.startswith(b):
                index2= temp.index(line)
                temp.remove(line)
                temp.insert(index2,'b*')                
            if line.startswith(c):                 
                index3= temp.index(line)                   
                temp.remove(line)
                temp.insert(index3,'c*')
        v2 = temp
        
        stac_align  ='        <h1 class="results">STAC Alignment Results</h1>\n'
        if self.align:
            if self.align == 'smart':
                stac_align +='        <h4 class="results">Alignment for maximum spot separation without blind zone.</h4>\n'
            if self.align == 'anom':
                stac_align +='        <h4 class="results">Alignment for bringing Bijvoet pairs to the same image.</h4>\n'
            if self.align == 'long':
                stac_align +='        <h4 class="results">Aligning the long axis parallel to the spindle axis.</h4>\n'
            if self.align == 'all':
                stac_align +='        <h4 class="results">Aligning each axis parallel to the spindle axis.</h4>\n'
            if self.align == 'a':
                stac_align +='        <h4 class="results">Aligning a* parallel to the spindle axis.</h4>\n'
            if self.align == 'b':
                stac_align +='        <h4 class="results">Aligning b* parallel to the spindle axis.</h4>\n'
            if self.align == 'c':
                stac_align +='        <h4 class="results">Aligning c* parallel to the spindle axis.</h4>\n'
            if self.align == 'ab':
                stac_align +='        <h4 class="results">Splitting a* and b* parallel to the spindle axis.</h4>\n'
            if self.align == 'ac':
                stac_align +='        <h4 class="results">Splitting a* and c* parallel to the spindle axis.</h4>\n'
            if self.align == 'bc':
                stac_align +='        <h4 class="results">Splitting b* and c* parallel to the spindle axis.</h4>\n'
            if self.align == 'multi':
                data = str(self.header.get('dataset_repr'))
                stac_align +='        <h4 class="results">Aligning crystal to same orientation as '+data+'.</h4>\n'
        stac_align +='        <table cellpadding="0" cellspacing="0" border="0" class="display" id="stac_align">\n'
        stac_align +='          <thead align="center">\n'
        stac_align +='            <tr>\n'
        stac_align +='              <th>ID</th>\n'
        stac_align +='              <th>V1</th>\n'
        stac_align +='              <th>V2</th>\n'
        stac_align +='              <th>Omega</th>\n'
        stac_align +='              <th>Kappa</th>\n'
        stac_align +='              <th>Phi</th>\n'
        if self.stac_trans:
            stac_align +='              <th>Translation</th>\n'
        #stac_align +='              <th>Rank</th>\n'
        stac_align +='            </tr>\n'
        stac_align +='          </thead>\n'
        stac_align +='          <tbody align="center">\n'                
        number = 1
        for x in range(len(v1)):
            stac_align +='            <tr class="gradeA">\n'
            stac_align +="              <td>" + str(number) + "</td>\n"
            stac_align +="              <td>" + v1[x] + "</td>\n"
            stac_align +="              <td>" + v2[x] + "</td>\n"
            stac_align +="              <td>%5.2f" % float(align_omega[x]) + "</td>\n"
            stac_align +="              <td>%5.2f" % float(align_kappa[x]) + "</td>\n"
            stac_align +="              <td>%5.2f" % float(align_phi[x]) + "</td>\n"
            if self.stac_trans:                
                stac_strat +="              <td>%5.2f" % float(trans[x]) + "</td>\n"
            #stac_align +="              <td>" + str(int(float(align_rank[x]))) + "</td>\n"
            stac_align +="            </tr>\n" 
            number +=1                       
        for x in range(len(no_sol)):
            stac_align +='            <tr class="gradeC">\n'
            stac_align +="              <td>no solution</td>\n"
            #stac_align +="              <td>" + no_sol[x][1] + "</td>\n"
            #stac_align +="              <td>" + no_sol[x][4] + "</td>\n"
            stac_align +="              <td>" + no_sol[x][0] + "</td>\n"
            stac_align +="              <td>" + no_sol[x][1] + "</td>\n"
            stac_align +="              <td>no solution</td>\n"
            stac_align +="              <td>no solution</td>\n"
            stac_align +="              <td>no solution</td>\n"
            if self.stac_trans:                
                stac_strat +="              <td>no solution</td>\n"
            #stac_align +="              <td>no solution</td>\n"
            stac_align +="            </tr>\n"  
        stac_align +='          </tbody>\n'
        stac_align +="        </table>\n"
        stac_align +="       </div>\n"
        stac_align +="      </div>\n"
        stac_align +="     </div>\n"   
       
        self.stac_align_summary = stac_align 
                    
        if self.stac_strat:
            if self.stacstrat_results:
                if self.stacstrat_results.get('STAC strat results') != 'FAILED':
                    stac_strat  ='    <div id="container">\n'
                    stac_strat +='    <div class="full_width big">\n'
                    stac_strat +='      <div id="demo">\n'                               
                    stac_strat +='        <h1 class="results">STAC Strategy Results</h1>\n'
                    stac_strat +='        <table cellpadding="0" cellspacing="0" border="0" class="display" id="stac_strat">\n'
                    stac_strat +='          <thead align="center">\n'
                    stac_strat +='            <tr>\n'
                    stac_strat +='              <th>ID</th>\n'
                    stac_strat +='              <th>Omega Start</th>\n'
                    stac_strat +='              <th>Omega End</th>\n'
                    stac_strat +='              <th>Kappa</th>\n'
                    stac_strat +='              <th>Phi</th>\n'        
                    stac_strat +='              <th>Completeness</th>\n'
                    stac_strat +='              <th>Rank</th>\n'
                    stac_strat +='            </tr>\n'
                    stac_strat +='          </thead>\n'
                    stac_strat +='          <tbody align="center">\n'                
                    for x in range(len(strat_id)):
                        stac_strat +='            <tr class="gradeA">\n'
                        stac_strat +="              <td>%5.2f" % float(strat_id[x]) + "</td>\n"
                        stac_strat +="              <td>%5.2f" % float(omega_start[x]) + "</td>\n"
                        stac_strat +="              <td>%5.2f" % float(omega_end[x]) + "</td>\n"
                        stac_strat +="              <td>%5.2f" % float(strat_kappa[x]) + "</td>\n"
                        stac_strat +="              <td>%5.2f" % float(strat_phi[x]) + "</td>\n"            
                        stac_strat +="              <td>%5.2f" % float(completeness[x]) + "</td>\n"
                        stac_strat +="              <td>%5.2f" % float(str(int(float(strat_rank[x])))) + "</td>\n"
                        stac_strat +="            </tr>\n"                        
                    stac_strat +='          </tbody>\n'
                    stac_strat +="        </table>\n"
                    stac_strat +="       </div>\n"
                    stac_strat +="      </div>\n"
                    stac_strat +="     </div>\n" 
                      
                    self.stac_strat_summary = stac_strat      
    
    except:
        self.logger.exception('**Error in Summary.summarySTAC**')

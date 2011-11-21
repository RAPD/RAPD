'''
__author__ = "Jon Schuermann, Frank Murphy"
__copyright__ = "Copyright 2009,2010,2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2011/02/02"
'''
import os
import subprocess
import time
import shutil
import math
import logging,logging.handlers

import rapd_agent_utilities as Utils

def setShelxNoSignal(self):
    """
    Output dict if no anomalous signal is present.
    """
    self.logger.debug('Parse::setShelxNoSignal')
    data  = { 'shelxc_res'      : 'no anom signal',
              'shelxc_data'     : 'no anom signal',
              'shelxc_isig'     : 'no anom signal',
              'shelxc_comp'     : 'no anom signal',
              'shelxc_dsig'     : 'no anom signal',                  
              'shelxd_try'      : 'no anom signal',
              'shelxd_cca'      : 'no anom signal',
              'shelxd_ccw'      : 'no anom signal',
              'shelxd_fom'      : 'no anom signal',
              'shelxd_best_occ' : 'no anom signal',
              'shelxd_best_try' : 'no anom signal',
              'shelxd_best_cc'  : 'no anom signal',
              'shelxd_best_ccw' : 'no anom signal',
              'shelxe_cc'       : 'no anom signal',
              'shelxe_mapcc'    : 'no anom signal',
              'shelxe_res'      : 'no anom signal',                  
              'shelxe_contrast' : 'no anom signal',
              'shelxe_con'      : 'no anom signal',
              'shelxe_sites'    : 'no anom signal',
              'shelxe_inv_sites': 'no anom signal',
              'shelxe_nosol'    : 'no anom signal',
              'shelx_ha'        : 'None',
              'shelx_phs'       : 'None',
              'shelx_tar'       : 'None'       }            
    self.shelx_results = {'Shelx results' : data}            
    
def setXtriageFailed(self):
    """
    Set output dict if Xtraige fails.
    """
    self.logger.debug('Parse::setXtriageFailed')
    xtriage = {'Xtriage anom'         : 'None',
               'Xtriage anom plot'    : 'None',
               'Xtriage int plot'     : 'None',
               'Xtriage i plot'       : 'None',
               'Xtriage z plot'       : 'None',
               'Xtriage nz plot'      : 'None',
               'Xtriage l-test plot'  : 'None',
               'Xtriage z-score'      : 'None',
               'Xtriage pat'          : 'None',
               #'Xtriage pat coor'     : 'None',
               #'Xtriage pat dist'     : 'None',
               #'Xtriage pat height'   : 'None',
               'Xtriage pat p-value'  : 'None',
               'Xtriage summary'      : 'None',
               'Xtriage log'          : 'None',
               'Xtriage PTS'          : 'None',
               'Xtriage PTS info'     : 'None',
               'Xtriage twin'         : 'None',
               'Xtriage twin info'    : 'None'       }     
    self.xtriage_results = {'Xtriage results': xtriage}
    
def setMolrepFailed(self):
    """
    Set output dict if Molrep fails.
    """
    self.logger.debug('Parse::setMolrepFailed')
    molrep  =  {'Molrep log'    : 'None',
                'Molrep jpg'    : 'None',
                'Molrep PTS'    : 'None',
                'Molrep PTS_pk' : 'None'}
    self.molrep_results = {'Molrep results': molrep}

def setAutoSolFalse(self):
    """
    set output dict for Autosol when it is disabled.
    """
    self.logger.debug('Parse::setAutoSolFalse')
    phenix = { 'directory'       : 'NA',
               'sg'              : 'NA',
               'wavelength'      : 'NA',
               'ha_type'         : 'NA',
               "f'"              : 'NA',
               'f"'              : 'NA',
               'bayes-cc'        : 'NA',
               'fom'             : 'NA',
               'sites_start'     : 'NA',
               'sites_refined'   : 'NA',
               'res_built'       : 'NA',
               'side_built'      : 'NA',
               'num_chains'      : 'NA',
               'model-map_cc'    : 'NA',
               'r/rfree'         : 'NA',
               #'den_mod_r'       : 'NA'
                                                       }
    self.autosol_results = { 'AutoSol results'     : phenix    }

def setPhaserFailed():
    """
    Return dict with all the params set to NA.
    """
    phaser = {      'AutoMR nosol': 'True',
                    'AutoMR tar'  : 'None',
                    'AutoMR pdb'  : 'Timed out',
                    'AutoMR mtz'  : 'Timed out',
                    'AutoMR gain' : 'Timed out',
                    'AutoMR rfz'  : 'Timed out',
                    'AutoMR tfz'  : 'Timed out',
                    'AutoMR clash': 'Timed out',
                    'AutoMR dir'  : 'Timed out',
                    'AutoMR sg'   : 'Timed out',
                    'AutoMR adf'  : 'Timed out',
                    'AutoMR peak' : 'Timed out'        }
    return(phaser)

def ParseOutputLabelit(self,input,iteration=0):
    """
    Parses Labelit results and filters for specific errors. Cleans up the output AND looks for best solution
    then passes info back to caller.
    """
    self.logger.debug('Parse::ParseOutputLabelit')
    tmp                = []
    junk               = []
    #junk3              = []
    labelit_sol        = []
    correct_pos        = -1
    results_pos        = -1
    no_sol             = -1
    self.max_cell      = 0
    self.bc            = False  
    pseudotrans        = False
    multi_sg           = False
    few_spots          = False
    labelit_face       = []
    labelit_solution   = []               
    labelit_metric     = []
    labelit_fit        = []
    labelit_rmsd       = []
    labelit_spots_fit  = []
    labelit_system     = []
    labelit_cell       = []         
    labelit_volume     = []
    mosflm_sol         = []
    mosflm_face        = []
    mosflm_solution    = []
    mosflm_sg          = []
    mosflm_beam_x      = []
    mosflm_beam_y      = []
    mosflm_distance    = []
    mosflm_res         = []
    mosflm_mos         = []
    mosflm_rms         = []
                               
    try:
        for line in input:
            line.rstrip()                
            tmp.append(line)
            if len(line) > 1:                
                if self.labelit_beamcenter:
                    if line.startswith('Beam center'):
                        self.bc = []
                        self.bc.append(line.split()[3][:6])
                        self.bc.append(line.split()[5][:6])
                        
                if line.startswith('Labelit finds no reasonable solution'):                                  
                    no_sol = line.find('Labelit finds no reasonable solution')
                    if no_sol != -1:
                        if self.multiproc:
                            return (('failed'))
                        else:
                            return (('no index'))                   
                
                if line.startswith('No_Indexing_Solution: Unreliable model'):
                    no_sol = line.find('No_Indexing_Solution: Unreliable model')
                    #print no_sol
                    if no_sol != -1:
                        if self.multiproc:
                            return (('failed'))
                        else:
                            return (('no index'))                                          
                    
                if line.startswith("No_Indexing_Solution: (couldn't find 3 good basis vectors)"):
                    no_sol = line.find("No_Indexing_Solution: (couldn't find 3 good basis vectors)")
                    #print no_sol
                    if no_sol != -1:
                        if self.multiproc:
                            return (('failed'))
                        else:
                            return (('no index'))              
                
                if line.startswith('MOSFLM_Warning: MOSFLM logfile declares FATAL ERROR'):
                    no_sol = line.find('MOSFLM_Warning: MOSFLM logfile declares FATAL ERROR')                        
                    if no_sol != -1:
                        if self.multiproc:
                            return (('failed'))
                        else:
                            return (('no index'))              
                    
                if line.startswith('ValueError: min()'):
                    no_sol = line.find('ValueError: min()')
                    if no_sol != -1:
                        if self.multiproc:
                            return (('failed'))
                        else:
                            return (('no index'))              
                
                if line.startswith('InputFileError: Input error: File header must contain the sample-to-detector distance in mm; value is 0.'):                                  
                    no_sol = line.find('InputFileError: Input error: File header must contain the sample-to-detector distance in mm; value is 0.')
                    if no_sol != -1:
                        return (('fix labelit'))                               
                
                if line.startswith('InputFileError: Input error:'):                                  
                    no_sol = line.find('InputFileError: Input error:')
                    if no_sol != -1:
                        return (('no pair'))
                                 
                if line.startswith('distl_minimum_number_spots'):
                    no_sol = line.find('distl_minimum_number_spots')
                    #self.min_spots = line
                    if no_sol != -1:
                        return (('min spots', line))                    
                                              
                if line.startswith('Have '):
                    #no_sol = line.find('Have ')
                    self.min_good_spots = line.split()[1].rstrip(';')
                    few_spots = True
                    """
                    if no_sol != -1:
                        return (('min good spots'))
                    """
                if line.startswith('UnboundLocalError'):
                    no_sol = line.find('UnboundLocalError')
                    if no_sol != -1:
                        return (('bad input'))
                
                if line.startswith('divide by zero'):
                    no_sol = line.find('divide by zero')
                    if no_sol != -1:
                        return (('bumpiness'))
                
                if line.startswith('No_Lattice_Selection: In this case'):
                    multi_sg=True
                    error_lg = line.split()[11]
                   
                if line.startswith('No_Lattice_Selection: The known_symmetry'):
                    no_sol = line.find('No_Lattice_Selection: The known_symmetry')                        
                    if no_sol != -1:
                        return (('bad input'))
                
                if line.startswith('MOSFLM_Warning: MOSFLM does not give expected results on r_'):
                    no_sol = line.find('MOSFLM_Warning: MOSFLM does not give expected results on r_')                        
                    if no_sol != -1:
                        return (('mosflm error'))
        if no_sol == -1:
            for x in range(len(tmp)):
                if tmp[x].startswith('Solution'):
                    junk.append(x)
                if tmp[x].startswith('Analysis'):
                    pseudotrans = True
                    junk.append(x)
            for line in tmp[junk[0]:]:
                #if line.startswith(':)' or ';(' or 'xx'):
                split_line = line.split()
                if len(split_line) == 15:                                    
                    labelit_sol.append(split_line)
            
            for x in range(len(labelit_sol)):
                labelit_face.append(labelit_sol[x][0])
                labelit_solution.append(labelit_sol[x][1])                       
                labelit_metric.append(labelit_sol[x][2])
                labelit_fit.append(labelit_sol[x][3])
                labelit_rmsd.append(labelit_sol[x][4])
                labelit_spots_fit.append(labelit_sol[x][5])
                labelit_system.append(labelit_sol[x][6:8])
                labelit_cell.append(labelit_sol[x][8:14])          
                labelit_volume.append(labelit_sol[x][14])  
            
            if multi_sg:
                return(('fix_cell',error_lg,labelit_sol))
                        
            for x in range(len(tmp)):
                if pseudotrans:
                    if junk[1] < x < junk[2]:
                        mosflm_sol.append(str(tmp[x]).split())
                elif x > junk[1]:
                    mosflm_sol.append(str(tmp[x]).split())
            for x in range(len(mosflm_sol)):
                if len(mosflm_sol[x]) == 9:
                    mosflm_face.append(mosflm_sol[x][0])
                    mosflm_solution.append(mosflm_sol[x][1])
                    mosflm_sg.append(mosflm_sol[x][2])
                    mosflm_beam_x.append(mosflm_sol[x][3])
                    mosflm_beam_y.append(mosflm_sol[x][4]) 
                    mosflm_distance.append(mosflm_sol[x][5])
                    mosflm_res.append(mosflm_sol[x][6])
                    mosflm_mos.append(mosflm_sol[x][7])
                    mosflm_rms.append(mosflm_sol[x][8])
                    if mosflm_sol[x][0].startswith(':)'):
                        sol = mosflm_sol[x][1]
                        if len(sol) == 1:
                            sol = '0' + sol       
                        #self.index_number.append("index" + sol)
                        mosflm_index = 'index' + sol                            
                if len(mosflm_sol[x]) == 8:
                    mosflm_face.append(' ')
                    mosflm_solution.append(mosflm_sol[x][0])
                    mosflm_sg.append(mosflm_sol[x][1])
                    mosflm_beam_x.append(mosflm_sol[x][2])
                    mosflm_beam_y.append(mosflm_sol[x][3]) 
                    mosflm_distance.append(mosflm_sol[x][4])
                    mosflm_res.append(mosflm_sol[x][5])
                    mosflm_mos.append(mosflm_sol[x][6])
                    mosflm_rms.append(mosflm_sol[x][7])

            if pseudotrans:
                self.pseudotrans = True                
            if few_spots:
                if os.path.exists(mosflm_index):
                    pass
                else:
                    return (('min good spots'))
        
        output         = tmp[:]            
        data = { 'labelit_face'     : labelit_face,
                 'labelit_solution' : labelit_solution,                                                          
                 'labelit_metric'   : labelit_metric,
                 'labelit_fit'      : labelit_fit,
                 'labelit_rmsd'     : labelit_rmsd,
                 'labelit_spots_fit': labelit_spots_fit,
                 'labelit_system'   : labelit_system,
                 'labelit_cell'     : labelit_cell,          
                 'labelit_volume'   : labelit_volume,
                 'labelit_iteration': str(iteration),                     
                 'mosflm_face'      : mosflm_face,
                 'mosflm_solution'  : mosflm_solution,
                 'mosflm_sg'        : mosflm_sg,
                 'mosflm_beam_x'    : mosflm_beam_x,
                 'mosflm_beam_y'    : mosflm_beam_y,
                 'mosflm_distance'  : mosflm_distance,
                 'mosflm_res'       : mosflm_res,
                 'mosflm_mos'       : mosflm_mos,
                 'mosflm_rms'       : mosflm_rms,
                 'mosflm_index'     : mosflm_index,
                 'output'           : output                  }
        #Utils.pp(self,data)                                                                                                                                              
        return((data))                                                            
                      
    except:
        self.logger.exception('**Error in Parse.ParseOutputLabelit**')
        return((None))                      
    
def ParseOutputDistl(self, input):     
    """
    parse distl.signal_strength
    """            
    self.logger.debug('Parse::ParseOutputDistl')
    try:    
        spot_total   = []
        spot_inres   = []
        good_spots   = []
        labelit_res  = []
        distl_res    = []
        max_cell     = []
        ice_rings    = []
        overloads    = []
        min          = []            
        max          = []            
        mean         = []                        
        signal_strength = False

        for line in input:
            strip = line.strip()
            if strip.startswith('Spot Total'):
                temp = (strip.split())[3]
                if temp == 'None':
                    temp = '0'
                spot_total.append(temp)
                #spot_total.append((strip.split())[3])
            if strip.startswith('In-Resolution Total'):
                temp = (strip.split())[3]
                if temp == 'None':
                    temp = '0'
                spot_inres.append(temp)
                #spot_inres.append((strip.split())[3])
            if strip.startswith('Good Bragg'):
                temp = (strip.split())[4]
                if temp == 'None':
                    temp = '0'
                good_spots.append(temp)
                #good_spots.append((strip.split())[4])
            if strip.startswith('Method 1'):
                temp = (strip.split())[4]
                if temp == 'None':
                    temp = '0'
                labelit_res.append(temp)
                #labelit_res.append((strip.split())[4])
            if strip.startswith('Method 2'):
                temp = (strip.split())[4]
                if temp == 'None':
                    temp = '0'
                distl_res.append(temp)
                #distl_res.append((strip.split())[4])
            if strip.startswith('Maximum unit cell'):
                temp = (strip.split())[4]
                if temp == 'None':
                    temp = '0'
                max_cell.append(temp)
                #max_cell.append((strip.split())[4])
            if strip.startswith('Ice Rings'):
                temp = (strip.split())[3]
                if temp == 'None':
                    temp = '0'
                ice_rings.append(temp)
                #ice_rings.append((strip.split())[3])
            if strip.startswith('In-Resolution Ovrld Spots'):
                temp = (strip.split())[4]
                if temp == 'None':
                    temp = '0'
                overloads.append(temp)
                #overloads.append((strip.split())[4])                                   
            if strip.startswith('Signals range'):
                signal_strength = True
                min.append(str(int(float((strip.split())[3]))))
                max.append(str(int(float((strip.split())[5]))))
                mean.append(str(int(float((strip.split())[10]))))
        if signal_strength == False:
            min.append('0')
            max.append('0')
            mean.append('0')

        distl = { 'total spots'             : spot_total,
                  'spots in res'            : spot_inres,
                  'good Bragg spots'        : good_spots,
                  'distl res'               : distl_res,
                  'labelit res'             : labelit_res,
                  'max cell'                : max_cell,
                  'ice rings'               : ice_rings,
                  'overloads'               : overloads,
                  'min signal strength'     : min,
                  'max signal strength'     : max,
                  'mean int signal'         : mean      }
                    
        #print distl        
        return ((distl))  
                        
    except:
        self.logger.exception('**Error in Parse.ParseOutputDistl**')
        return ((None))
        
def ParseOutputRaddose(self, input):
    """
    Looks for dose and cell volume. Passes info back to caller
    """
    self.logger.debug('Parse::ParseOutputRaddose')
    try:
        for line in input:
            if line.startswith('Total absorbed dose'):
                dose_per_image = float((line.split())[4])
            if line.startswith('Unit Cell Volume'):
                self.volume = float((line.split())[4])
            if line.startswith('** Time in sec'):
                exp_dose_lim = line.split()[11]
            if line.startswith('   Time in sec'):    
                hen_lim = line.split()[13]
                
        raddose = { 'dose per image'       :  dose_per_image,
                    'exp dose limit'       :  exp_dose_lim,
                    'henderson limit'      :  hen_lim  }
                            
        return ((raddose))
        
    except:
        self.logger.exception('**Error in Parse.ParseOutputRaddose**')
        return ((None))

def ParseOutputBest(self,input,anomalous=False):
    """
    cleans up the output and looks for errors to pass back for fixing and rerunning.
    passes info back to caller
    """
    self.logger.debug('Parse::ParseOutputBest')
    try:
        temp            = []
        junk1           = []
        strategy2       = []
        run_num         = []
        phi_start       = []
        num_images      = []
        delta_phi       = []
        time            = []
        distance        = []
        overlap         = []
        new_trans       = []
        pos             = []
        new             = False
        iso_B           = False
        anom            = None
        frac_unique_blind = None
        """
        for i in range(len(input)):
            if input[i].startswith('ERROR: scaling error > 100%'):                
                if input[i+1].startswith('These data can be used at the resolution'):
                    self.nbr = input[i+1].split()[9]
                return(('neg B'))
        """
        for i,line in enumerate(input):
            temp.append(line)
            #Check for errors first.
            if line.startswith(' ***any data cannot be measured for the given time!'):
                return (('dosage too high'))            
            if line.startswith(' no data can be measured with requested'):
                return (('dosage too high'))            
            if line.startswith(' Anisotropic B-factor can not be determined'):
                iso_B = True                                        
            if line.startswith('ERROR: negative B-factors'):
                return(('neg B'))
            if line.startswith('Determination of B-factor failed'):
                return(('neg B'))
            if line.startswith('ERROR: the deretmination of'):
                return(('neg B'))
            if line.startswith('ERROR: unknown spacegroup'):
                return(('sg'))            
            if line.startswith('  ERROR: Detector pixel'):
                return(('bin'))           
            """
            if line.startswith('ERROR'):
                return(('neg B'))
            junk = line.count('The results are inacurate!')
            if junk != 0:
                return(('neg B'))
            """
            #If no errors then continue...
            if line.startswith(' dge|'):
                position = i
            if line.startswith(' Resolution limit'):
                if len(line.split()) > 5:
                    res_lim = line.split()[2][1:]
                    trans = float(line.split()[6][:-1])
                    if len(line.split()) == 9:
                        dis = round(float(line.split()[8][1:-2]),-1)
                    else:
                        dis = round(float(line.split()[9][:-2]),-1)
                    attenuation = str(float(trans)*0.01).zfill(3)
                    if dis > 1200:
                        dis = '1200.0'                   
            if line.startswith(' Anomalous data'):
                anom = line.split()[3]
            if line.startswith(' Phi_start -'):
                data_col_end = line.split()[6]
            if line.startswith(' Total rotation range   '):
                rot_range = line.split()[4]
            if line.startswith(' Overall Completeness'):
                completeness = line.split()[3]
            if line.startswith(' Redundancy   '):
                redundancy = line.split()[2]
            if line.startswith(' R-factor '):
                r_factor        = line.split()[4]
                r_factor_outer  = line.split()[6][:-1]
            if line.startswith(' I/Sigma '):
                i_over_sig        = line.split()[4]
                i_over_sig_outer  = line.split()[6][:-1]
            if line.startswith(' Total Exposure time'):
                tot_exp_time      = line.split()[4]
            if line.startswith(' Total Data Collection'):
                tot_data_col_time = line.split()[5]
            if line.startswith('Fraction of unique'):    
                frac_unique_blind = line.split()[7]
        #Catches parameters not present in the low res wedge for low res datasets
        if anom == None:
            anom = str(anomalous)
        if frac_unique_blind == None:
            frac_unique_blind = '0.0'
        #If best_complexity is set to full, grab results for all wedges in strategy.
        run_number  = 1
        line_number = 2
        while temp[position + line_number].startswith(' ' + str(run_number)):
            strategy2.append(temp[position + line_number])
            run_num.append(strategy2[run_number - 1].split()[0])
            phi_start.append(strategy2[run_number - 1].split()[1])
            delta_phi.append(strategy2[run_number - 1].split()[2])
            t = float(strategy2[run_number - 1].split()[3])
            #Set time and transmission to minimize data collection time
            if trans == 100.0:
                new_trans.append(str(trans))
                time.append(strategy2[run_number - 1].split()[3])
            else:
                nt = t*trans
                if nt > 100:
                    new_trans.append('100.0')
                    time.append(str(round(nt*0.01)))
                else:
                    new_trans.append(str(round(nt)))
                    time.append('1.00')
            num_images.append(strategy2[run_number - 1].split()[4][:-2])
            distance.append(str(dis))
            overlap.append(strategy2[run_number - 1].split()[5])
            run_number += 1
            line_number += 1
        if iso_B:
            if float(min(delta_phi)) < 0.3:          
                return (('isotropic B'))       
        if anomalous:
            j1 = ' anom '
        else:
            j1 = ' '
        data = { 'strategy'+j1+'run number'                       : run_num,    
                 'strategy'+j1+'phi start'                        : phi_start,
                 'strategy'+j1+'num of images'                    : num_images,
                 'strategy'+j1+'delta phi'                        : delta_phi,
                 'strategy'+j1+'image exp time'                   : time,
                 'strategy'+j1+'distance'                         : distance,
                 'strategy'+j1+'overlap'                          : overlap,
                 'strategy'+j1+'res limit'                        : res_lim,
                 'strategy'+j1+'anom flag'                        : anom,
                 'strategy'+j1+'phi end'                          : data_col_end,
                 'strategy'+j1+'rot range'                        : rot_range,
                 'strategy'+j1+'completeness'                     : completeness,
                 'strategy'+j1+'redundancy'                       : redundancy,
                 'strategy'+j1+'R-factor'                         : r_factor + ' (' + r_factor_outer + ')',
                 'strategy'+j1+'I/sig'                            : i_over_sig + ' (' + i_over_sig_outer + ')',
                 'strategy'+j1+'total exposure time'              : tot_exp_time,
                 'strategy'+j1+'data collection time'             : tot_data_col_time,
                 'strategy'+j1+'frac of unique in blind region'   : frac_unique_blind,
                 'strategy'+j1+'attenuation'                      : attenuation,
                 'strategy'+j1+'new transmission'                 : new_trans     }
        return ((data))
                   
    except:
        self.logger.exception('**Error in Parse.ParseOutputBest**')
        return (('None'))
                 
def ParseOutputMosflm_strat(self,input,anom=False):
    """
    Parsing Mosflm strategy.
    """
    self.logger.debug('Parse::ParseOutputMosflm_strat')
    try:
        temp  = []
        strat = []
        res   = []
        start = []
        end   = []
        ni    = []
        rn    = []
        seg = False
        osc_range             = str(self.header.get('osc_range'))
        distance              = str(self.header.get('distance'))
        mosflm_seg            = str(self.preferences.get('mosflm_seg'))
        
        for line in input:
            temp.append(line)
            if mosflm_seg != '1':
                if line.startswith(' This may take some time......'):
                    index = temp.index(line)  
                    seg = True         
            else:
                if line.startswith(' Checking completeness of data'):
                    index = temp.index(line)
                
            if line.startswith(' Breakdown as a Function of Resolution'):
                index_res = temp.index(line)
                
            if line.startswith(' Mean multiplicity'):
                index_mult = temp.index(line)                       
                mult2 = ((temp[index_mult]).split()[-1])               
        if seg:
            strat.append(temp[index:index + 10 + 2*int(mosflm_seg)])
        else:
            strat.append(temp[index:index + 12])            
        
        counter = 0
        for line in strat:
            comp = line[3].split()[3]
            while counter < int(mosflm_seg):
                s1    = float(line[5 + counter].split()[1])
                e1    = float(line[5 + counter].split()[3])
                images1 = int((e1 - s1) / float(osc_range))
                ni.append(images1)
                if s1 < 0:
                    s1 += 360
                if s1 > 360:
                    s1 -= 360
                start.append(s1)
                if e1 < 0:
                    e1 += 360
                if e1 > 360:
                    e1 -= 360
                end.append(e1)             
                counter += 1
                rn.append(counter)            

        res.append(temp[index_res:index_res + 17])
        for line in res:                
            resolution = line[15].split()[0]
        
        if anom:
            j1 = ' anom '
        else:
            j1 = ' '
        data = {'strategy'+j1+'run number'            : rn,
                'strategy'+j1+'phi start'             : start,
                'strategy'+j1+'phi end'               : end,
                'strategy'+j1+'num of images'         : ni,
                'strategy'+j1+'resolution'            : resolution,
                'strategy'+j1+'completeness'          : comp,
                'strategy'+j1+'redundancy'            : mult2,
                'strategy'+j1+'distance'              : distance,
                'strategy'+j1+'image exp time'        : self.time,
                'strategy'+j1+'delta phi'             : osc_range                }
        
        #print (data)
        return((data))
        
    except:
        self.logger.exception('**Error in Parse.ParseOutputMosflm_strat**')
        return ((None))
    
def ParseOutputStacAlign(self, input):
    """
    parse Stac Alignment.
    """
    self.logger.debug('Parse::ParseOutputStacAlign')
    if self.test:
        os.chdir('/home/schuerjp/Data_processing/Frank/Output/labelit_iteration0')
                
    v1    = []
    v2    = []
    omega = []
    kappa = []
    phi   = []
    trans = []
    rank  = []
    no_sol = []
    goni = []
    
    try:    
        orientations = input[0]
        log = input[1:]
                
        split = (orientations.split('<possible_orientation>')[1:])
        for line in split:            
            v1_start = line.index('<v1>')
            v1_end   = line.index('</v1')
            v1.append(line[v1_start:v1_end].strip('<v1>'))
            v2_start = line.index('<v2>')
            v2_end   = line.index('</v2')
            v2.append(line[v2_start:v2_end].strip('<v2>'))
            omega_start = line.index('<omega>')
            omega_end   = line.index('</omega')
            omega.append(line[omega_start:omega_end].strip('<omega>'))
            kappa_start = line.index('<kappa>')
            kappa_end   = line.index('</kappa')
            kappa.append(line[kappa_start:kappa_end].strip('<kappa>'))
            phi_start = line.index('<phi>')
            phi_end   = line.index('</phi')
            phi.append(line[phi_start:phi_end].strip('<phi>'))
            trans_start = line.index('<trans>')
            trans_end   = line.index('</trans')
            trans.append(line[trans_start:trans_end].strip('<trans>'))
            rank_start = line.index('<rank>')
            rank_end   = line.index('</rank')
            rank.append(line[rank_start:rank_end].strip('<rank>'))
        
        for line in log:
            if line.startswith(' - Could not find solution'):                
                temp = []                
                junk1 = line.index('V1:')
                junk2 = line.index('V2:')
                temp.append(line[junk1+4:junk2-3])
                temp.append(line[junk2+4:-1])                
                no_sol.append(temp)
                
            if line.startswith(' - Goniometer does not allow the solution'):
                goni.append(line)
        
        stac = { 'v1'            :  v1,
                 'v2'            :  v2,
                 'omega'         : omega,
                 'kappa'         : kappa,
                 'phi'           : phi,
                 'trans'         : trans,
                 'rank'          : rank,
                 'no_sol'        : no_sol,
                 'goni limited'  : goni  }
        #print ((stac))                        
        return ((stac))
    
    except:
        self.logger.exception('**Error in Parse.ParseOutputStacAlign**')
        return ((None))
    
def ParseOutputStacStrat(self, input):
    """
    parse Stac Strategy.
    """
    self.logger.debug('Parse::ParseOutputStacStrat')
    if self.test:
        os.chdir('/home/schuerjp/Data_processing/Frank/Output/labelit_iteration0')
                
    strat_id    = []
    omegas      = []
    omegaf      = []
    kappa       = []
    phi         = []
    comp        = []
    rank        = []
    
    try:
        split = (input.split('<generated_sweep>')[1:])
        for line in split:              
            strat_id_start = line.index('<strategyID>')
            strat_id_end   = line.index('</strategyID>')
            strat_id.append(line[strat_id_start:strat_id_end].strip('<strategyID>'))
            omega1_start = line.index('<omegaStart>')
            omega1_end   = line.index('</omegaStart')
            omegas.append(line[omega1_start:omega1_end].strip('<omegaStart>'))
            omega2_start = line.index('<omegaEnd>')
            omega2_end   = line.index('</omegaEnd')
            omegaf.append(line[omega2_start:omega2_end].strip('<omegaEnd>'))
            kappa_start = line.index('<kappa>')
            kappa_end   = line.index('</kappa')
            kappa.append(line[kappa_start:kappa_end].strip('<kappa>'))
            phi_start = line.index('<phi>')
            phi_end   = line.index('</phi')
            phi.append(line[phi_start:phi_end].strip('<phi>'))
            comp_start = line.index('<completeness>')
            comp_end   = line.index('</completeness')
            comp.append(line[comp_start:comp_end].strip('<completeness>'))
            rank_start = line.index('<rank>')
            rank_end   = line.index('</rank')
            rank.append(line[rank_start:rank_end].strip('<rank>'))
        
        stac = { 'strat ID'      :  strat_id,
                 'omega start'   :  omegas,
                 'omega finish'  :  omegaf,
                 'kappa'         :  kappa,
                 'phi'           :  phi,
                 'completeness'  :  comp,
                 'rank'          :  rank     }
                 
        #print ((stac))                        
        return ((stac))
    
    except:
        self.logger.exception('**ERROR in Parse.ParseOutputStacStrat**')
        return ((None))

def ParseOutputShelx(self, input, input2):
    """
    Parse Shelx CDE output.
    """
    self.logger.debug('Parse::ParseOutputShelx')
    try:
        temp   = []
        temp2  = []
        shelxc_res = []
        shelxd_try = []
        shelxd_cca = []
        shelxd_ccw = []
        shelxd_fom = []
        #shelxe_cc = []
        shelxe_contrast = []
        shelxe_con = []
        shelxe_sites = []
        shelxe_mapcc = []
        shelxe_res = []
        fom = []
        se_cc = []
        build_cc = []
        build_nres = []
        contrast = []
        con = []
        index = []
        #index1 = []
        
        junk = []        
        junk2 = []
        junk3 = []
        sites_occ = []
        shelxc_dsig = False
        inverse = False
        nosol = False
        fa = True
        failed_inv = False
        failed_ninv = False
        par = False
        count = 0
        if input2 == []:
            fa = False
        
        for line in input:
            #line.rstrip()
            temp.append(line)
            if line.startswith(' ** ARRAYS TOO SMALL TO STORE REFLECTION DATA'):
                return ('array')
            junk1 = line.find('threads running in parallel')
            if junk1 != -1:
                par = True
            if line.startswith(' Resl.'):
                shelxc_res.extend(line.split()[3::2])
                while len(shelxc_res) < 11:
                    shelxc_res.append('0.00')
            if line.startswith(' N(data)'):
                shelxc_data = line.split()[1:]
                while len(shelxc_data) < 11:
                    shelxc_data.append('0')
            if line.startswith(' <I/sig>'):
                shelxc_isig = line.split()[1:]
                while len(shelxc_isig) < 11:
                    shelxc_isig.append('0.0')
            if line.startswith(' %Complete'):
                shelxc_comp = line.split()[1:]
                while len(shelxc_comp) < 11:
                    shelxc_comp.append('0.0')
            if line.startswith(' <d"/sig>'):
                shelxc_dsig = line.split()[1:]
                while len(shelxc_dsig)  < 11:
                    shelxc_dsig.append('0.00')
            if line.startswith(' Try  '):
                shelxd_try.append(line.split()[1][:-1])
                if par:
                    shelxd_cca.append(line[31:37].strip())
                    shelxd_ccw.append(line[38:43].strip())
                    shelxd_fom.append(line[73:80].strip())
                else:
                    shelxd_cca.append(line[23:30].strip())
                    shelxd_ccw.append(line[31:37].strip())
                    shelxd_fom.append(line[70:76].strip())
                    """
                    #old way
                    mis = line.split()[3]
                    if len(mis) > 10:
                        shelxd_cca.append(line.split()[3][8:])
                        slash = line.split()[4]
                        if len(slash) > 1:
                            shelxd_ccw.append(line.split()[4][1:-1])
                        else:
                            shelxd_ccw.append(line.split()[5][:-1])                    
                    else:
                        shelxd_cca.append(line.split()[4])
                        slash = line.split()[5]
                        if len(slash) > 1:
                            shelxd_ccw.append(line.split()[5][1:-1])
                        else:
                            shelxd_ccw.append(line.split()[6][:-1])
                    """
                #index1.append(temp.index(line))                
            if fa:            
                """
                if line.startswith(' Pseudo-free CC'):
                    junk.append((line.split()[3]))
                    #se_cc.append((line.split()[3]))
                """
                if line.startswith(' Estimated mean FOM ='):
                    fom.append(line.split()[4])
                    se_cc.append(line.split()[8])
                #if self.shelx_build:
                if line.startswith(' -i '):
                    junk.append(line.split()[1])
                if line.startswith('  +  SHELXE finished'):
                    index6 = temp.index(line)
                    #if temp[index6-3].startswith(' ** Unable to trace map'):
                    if temp[index6-3].startswith(' ** '):    
                        #print os.getcwd()
                        count += 1
                        if junk[-1] == 'invert':
                            failed_inv = True
                        if junk[-1] == 'NOT':
                            failed_ninv = True                   
                if line.startswith(' CC for partial structure'):
                    build_cc.append(line.split()[8])
                temp3 = line.find('residues left after pruning')
                if temp3 != -1:
                    build_nres.append(line.split()[0])
                temp4 = line.find('Chain tracing')
                if temp4 != -1:
                    #Check to see if autotracing is turned on. If not then set the results to 0.
                    if line.split()[0] == '0.0':
                        build_cc.append('0.000')
                        build_nres.append('0')
                        shelxe_contrast.append('')                    
                        if self.shelx_build:
                            for i in range(0,20):
                                contrast.append('0.000')
                                con.append('0.000')
                if line.startswith(' <wt> ='):
                    if line.split()[3] == 'Contrast':
                        #shelxe_contrast.append(line.split()[5][:-1])
                        contrast.append(line.split()[5][:-1])                        
                        #shelxe_con.append(line.split()[8])
                        con.append(line.split()[8])
                if line.startswith(' <mapCC>'):
                    shelxe_mapcc.extend(line.split()[1:]) 
                #Fix if low res is greater than 10A.
                if line.startswith(' d    inf'):
                    if len(line.split()[2]) == 1:
                        shelxe_res.extend(line.split()[3::2])                            
                    else:
                        shelxe_res.append('15.00')
                        shelxe_res.extend(line.split()[4::2])
        #If autotracing failed.
        if count > 0:
            if self.shelx_build:
                if count == 2:
                    return ('trace failed both')
                else:
                    if failed_inv:
                        return ('trace failed inv')
                    if failed_ninv:
                        return ('trace failed ninv')
        else:    
            l = len(shelxd_try)
            if l == 0:
                shelxd_try = ['1']
            else:
                if self.multiShelxD:            
                    shelxd_try = []
                    for i in range(1,l+1):
                        shelxd_try.append(str(i))
            """
            #Had to add since ShelxD does not print PATFOM if it is 0.00 for iteration
            for x in range(len(index1)):
                if temp[index1[x]+1].startswith(' PATFOM'):
                    shelxd_fom.append(temp[index1[x]+1].split()[1])
                else:
                    shelxd_fom.append('0.00')
            """
            if fa:
                for x in range(len(input)):
                    if input[x].startswith('  Site     x'):
                        index.append(x)
                    if input[x].startswith(' Site    x'):
                        index.append(x)        
                """
                shelxe_cc.append(junk[3])
                shelxe_cc.append(junk[-1])        
                """
                for line in contrast:
                    junk3.append(float(line))
                avg_contrast1 = sum(junk3[0:20])/20
                shelxe_contrast= contrast[0:20]
                shelxe_con = con[0:20]
                if self.shelx_build:
                    avg_contrast2 = sum(junk3[40:60])/20
                    shelxe_contrast.extend(contrast[40:60])
                    shelxe_con.extend(con[40:60])
                else:                
                    avg_contrast2 = sum(junk3[20:40])/20
                    shelxe_contrast.extend(contrast[20:40])
                    shelxe_con.extend(con[20:40])
                if avg_contrast1 > avg_contrast2:
                #if float(shelxe_cc[0]) > float(shelxe_cc[1]):           
                    #Here if ShelxE autotracing works.                
                    if self.shelx_build:
                        if os.path.exists('junk.pdb'):
                            shutil.copy('junk.pdb','shelxe_autotrace.pdb')
                            crap = os.path.join(os.getcwd(),'shelxe_autotrace.pdb')
                            shelxe_pdb = crap
                        else:
                            shelxe_pdb = 'None'
                    else:
                        shelxe_pdb = 'None'
                    shelxe_cc  = se_cc[0]
                    shelxe_fom = fom[0]
                    shelxe_trace_cc = build_cc[0]
                    shelxe_trace_nres = build_nres[0]                
                    shelxe_sites.extend(temp[index[0]+1:index[1]-1])            
                    #if float(shelxe_cc[0]) - float(shelxe_cc[1]) < 5:
                    if avg_contrast1 - avg_contrast2 < 0.05:
                        nosol = True
                else:
                    shelxe_sites.extend(temp[index[2]+1:index[3]-1])
                    inverse = True
                    #Here if ShelxE autotracing works.
                    if self.shelx_build:
                        if os.path.exists('junk_i.pdb'):
                            shutil.copy('junk_i.pdb','shelxe_autotraced.pdb')
                            crap = os.path.join(os.getcwd(),'shelxe_autotrace.pdb')
                            shelxe_pdb = crap
                        else:
                            shelxe_pdb = 'None'
                    else:
                        shelxe_pdb = 'None'
                    shelxe_fom = fom[1]
                    shelxe_cc  = se_cc[1]
                    shelxe_trace_cc = build_cc[1]
                    shelxe_trace_nres = build_nres[1]
                    #if float(shelxe_cc[1]) - float(shelxe_cc[0]) < 5:
                    if avg_contrast2 - avg_contrast1 < 0.05:
                        nosol = True                
                for line in input2:
                    temp2.append(line)
                    if line.startswith('REM Best'):
                        best_try = '1'
                        best_cc  = line.split()[5]
                        best_ccw = line.split()[7]
                    if line.startswith('REM TRY'):
                        best_try = line.split()[2]
                        best_cc  = line.split()[4]
                        best_ccw = line.split()[6]
                    if line.startswith('UNIT'):
                        index2 = temp2.index(line)
                    if line.startswith('HKLF'):
                        index3 = temp2.index(line)
                junk2.extend(temp2[index2+1:index3])
                for line in junk2:
                    sites_occ.append(line.split()[5])
            else:            
                shelxe_res = shelxc_res            
                for i in range(0,20):
                    shelxe_mapcc.append('0.00')    
                for i in range(0,40):
                    shelxe_contrast.append('0.00')
                    shelxe_con.append('0.00')                
                #shelxe_cc.append('0.00')
                shelxe_sites.append('1   0.0000   0.0000   0.0000   0.0000    0.000')
                best_try = '1'
                best_cc = '0.000'
                best_ccw= '0.000'
                sites_occ.append('0.0000')
                nosol = True           
                shelxe_fom = '0.000'
                shelxe_cc  = '0.000'
                shelxe_pdb = None
                shelxe_trace_cc = '0.000'
                shelxe_trace_nres = '0'
            #Fix issue if results are negative
            for line in shelxd_ccw:
                if line.startswith('-'):
                    index = shelxd_ccw.index(line)
                    shelxd_ccw.remove(line)
                    shelxd_ccw.insert(index,'0.00')
            for line in shelxd_cca:
                if line.startswith('-'):
                    index = shelxd_cca.index(line)
                    shelxd_cca.remove(line)
                    shelxd_cca.insert(index,'0.00')
            for line in shelxd_fom:
                if line.startswith('-'):
                    index = shelxd_fom.index(line)
                    shelxd_fom.remove(line)
                    shelxd_fom.insert(index,'0.00')       
                        
            #If SHELXD fails, set results to 0.0    
            if shelxc_dsig == False:
                shelxc_dsig = ['0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0']         
            if len(shelxd_fom) == 0:
                shelxd_fom = ['0.00']
            if len(shelxd_cca) == 0:
                shelxd_cca = ['0.00']
            if len(shelxd_ccw) == 0:
                shelxd_ccw = ['0.00']
                nosol = True
            
            shelx = { 'shelxc_res'         : shelxc_res,
                      'shelxc_data'        : shelxc_data,
                      'shelxc_isig'        : shelxc_isig,
                      'shelxc_comp'        : shelxc_comp,
                      'shelxc_dsig'        : shelxc_dsig,                  
                      'shelxd_try'         : shelxd_try,
                      'shelxd_cca'         : shelxd_cca,
                      'shelxd_ccw'         : shelxd_ccw,
                      'shelxd_fom'         : shelxd_fom,
                      'shelxd_best_occ'    : sites_occ,
                      'shelxd_best_try'    : best_try,
                      'shelxd_best_cc'     : best_cc,
                      'shelxd_best_ccw'    : best_ccw,
                      'shelxe_fom'         : shelxe_fom,
                      'shelxe_trace_pdb'   : shelxe_pdb,
                      'shelxe_trace_cc'    : shelxe_trace_cc,
                      'shelxe_trace_nres'  : shelxe_trace_nres,
                      'shelxe_cc'          : shelxe_cc,
                      'shelxe_mapcc'       : shelxe_mapcc,
                      'shelxe_res'         : shelxe_res,
                      'shelxe_contrast'    : shelxe_contrast,
                      'shelxe_con'         : shelxe_con,
                      'shelxe_sites'       : shelxe_sites,
                      'shelxe_inv_sites'   : str(inverse),
                      'shelxe_nosol'       : str(nosol)       }
            #print shelxe_trace_cc
            return((shelx))
     
    except:
        self.logger.exception('**Error in Parse.ParseOutputShelx**')
        return ((None))
    
def ParseOutputShelxC(self, input):
    """
    Parse Shelx CDE output.
    """
    self.logger.debug('Parse::ParseOutputShelxC')
    try:
        temp   = []
        temp2  = []
        shelxc_res = []
        shelxc_dsig = False
        
        for line in input:
            line.rstrip()
            temp.append(line)            
            """
            if line.startswith('** NO REFLECTIONS WITH  E >'):                    
                return (None)            
            """
            if line.startswith(' Resl.'):
                shelxc_res.extend(line.split()[3::2])
                while len(shelxc_res) < 11:
                    shelxc_res.append('0.00')
            if line.startswith(' N(data)'):
                shelxc_data = line.split()[1:]
                while len(shelxc_data) < 11:
                    shelxc_data.append('0')
            if line.startswith(' <I/sig>'):
                shelxc_isig = line.split()[1:]
                while len(shelxc_isig) < 11:
                    shelxc_isig.append('0.0')
            if line.startswith(' %Complete'):
                shelxc_comp = line.split()[1:]
                while len(shelxc_comp) < 11:
                    shelxc_comp.append('0.0')
            if line.startswith(' <d"/sig>'):
                shelxc_dsig = line.split()[1:]
                while len(shelxc_dsig)  < 11:
                    shelxc_dsig.append('0.00')
                    
        #If SHELXD fails, set results to 0.0    
        if shelxc_dsig == False:
            shelxc_dsig = ['0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0','0.0']
               
        shelx = { 'shelxc_res'      : shelxc_res,
                  'shelxc_data'     : shelxc_data,
                  'shelxc_isig'     : shelxc_isig,
                  'shelxc_comp'     : shelxc_comp,
                  'shelxc_dsig'     : shelxc_dsig,                  
                                                    }
        return((shelx))
     
    except:
        self.logger.exception('**Error in Parse.ParseOutputShelxC**')
        return ((None))
    
def ParseOutputAutoSol(self, input):
    """
    Parse phenix.autosol output.
    """
    self.logger.debug('Parse::ParseOutputAutoSol')
    try:
        tmp  = []
        for line in input:
            line.rstrip()
            tmp.append(line)
            if line.startswith('Working directory:'):
                dir = line.split()[2]
            if line.startswith('SG: '):
                sg = line[4:-1].replace(' ','')
            if line.startswith('Guesses of scattering factors'):
                ha_type = line.split()[5]
                index = tmp.index(line)
            if line.startswith('Solution #'):
                bayes_cc = line.split()[4]
                fom = line.split()[-1]
            if line.startswith('Sites:'):
                sites_start = line.split()[1]
                #sites_refined = line.split()[12]
                sites_refined = line.split()[-1]
            if line.startswith('  Residues built:'):
                res_built = line.split()[2]
            if line.startswith('  Side-chains built:'):
                side_built = line.split()[2]
            if line.startswith('  Chains:'):
                num_chains = line.split()[1]
            if line.startswith('  Overall model-map correlation:'):
                mm_cc = line.split()[3]
            if line.startswith('  R/R-free:'):
                r_rfree = line.split()[1]
            """
            if line.startswith('Density modification logfile'):
                dmr = line.split()[5][3:7]
            """
        scat_fac = tmp[index+2].split()[2:4]
        wave = tmp[index+2].split()[1]
        
        phenix = { 'directory'       : dir,
                   'sg'              : sg,
                   'wavelength'      : wave,
                   'ha_type'         : ha_type,
                   "f'"              : scat_fac[0],
                   'f"'              : scat_fac[1],
                   'bayes-cc'        : bayes_cc,
                   'fom'             : fom,
                   'sites_start'     : sites_start,
                   'sites_refined'   : sites_refined,
                   'res_built'       : res_built,
                   'side_built'      : side_built,
                   'num_chains'      : num_chains,
                   'model-map_cc'    : mm_cc,
                   'r/rfree'         : r_rfree,
                   #'den_mod_r'       : dmr
                                                       }                                 
        return ((phenix))
    
    except:
        self.logger.exception('**ERROR in Parse.ParseOutputAutoSol**')
        phenix = { 'directory'       : 'ERROR',
                   'sg'              : 'ERROR',
                   'wavelength'      : 'ERROR',
                   'ha_type'         : 'ERROR',
                   "f'"              : 'ERROR',
                   'f"'              : 'ERROR',
                   'bayes-cc'        : 'ERROR',
                   'fom'             : 'ERROR',
                   'sites_start'     : 'ERROR',
                   'sites_refined'   : 'ERROR',
                   'res_built'       : 'ERROR',
                   'side_built'      : 'ERROR',
                   'num_chains'      : 'ERROR',
                   'model-map_cc'    : 'ERROR',
                   'r/rfree'         : 'ERROR',
                   #'den_mod_r'       : 'ERROR'
                   }        
        return((phenix))    

def ParseOutputAutoBuild(self,input):
    """
    Parse phenix.autobuild.
    """
    self.logger.debug('Parse::ParseOutputAutoBuild')
    try:
        temp = []
        for line in input:
            line.rstrip()
            temp.append(line)
            if line.startswith('This is new best model with score'):
                index = temp.index(line)
            if line.startswith('Working directory:'):
                dir = line.split()[2]
            if line.startswith('Current overall_best model and map'):
                index2 = temp.index(line)
            if line.startswith('Model ('):
                pdb = line.split()[-1]
            if line.startswith('R and R-free:'):
                r = line.split()[3]
                rfree = line.split()[4]
            if line.startswith('Map-model CC:'):
                mmcc = line.split()[-1]
            if line.startswith('from: refine'):
                mtz = line.split()[-1]
            if line.startswith('from: overall_best_refine'):
                mtz = line.split()[-1]            
        resi_built = temp[index-1].split()[3][6:]
        seq_placed = temp[index-1].split()[4][7:]
        chains = temp[index-1].split()[5][7:]
        score = temp[index].split()[8]        
        autobuild = { 'AutoBuild_pdb'      : pdb,
                      'AutoBuild_mtz'      : mtz,
                      'AutoBuild_rfac'     : r,
                      'AutoBuild_rfree'    : rfree,
                      'AutoBuild_mmcc'     : mmcc,
                      'AutoBuild_built'    : resi_built,
                      'AutoBuild_placed'   : seq_placed,
                      'AutoBuild_chains'   : chains,
                      'AutoBuild_score'    : score,
                      'AutoBuild_dir'      : dir                                              
                                                     }
        #print (autobuild)
        return((autobuild))    
    
    except:
        self.logger.exception('**ERROR in Parse.ParseOutputAutoBuild**')
        return((None))
    
def ParseOutputAutoMR(self,input):
    """
    Parse AutoMR output.
    """
    self.logger.debug('Parse::ParseOutputAutoMR')
    try:
        nosol = False
        pdb = False
        temp = []
        for line in input:
            temp.append(line)
            if line.startswith('Files in directory'):
                mr_dir = line.split()[-1]
                cwd = os.getcwd()
                directory = os.path.join(cwd,mr_dir)
            if line.startswith(' Log likelihood gain for solution MR'):
                llgain = line.split()[-1]
            if line.startswith(' Output PDB files for solution MR'):
                pdb = line.split()[-1]
            if line.startswith(' Output MTZ files for solution MR'):
                mtz = line.split()[-1]
            if line.startswith('   Solution #1 annotation'):
                rfz = line.split()[4][4:]
                tfz = line.split()[5][4:]
            if line.startswith('   Solution annotation'):
                rfz = line.split()[3][4:]
                tfz = line.split()[4][4:]           
            if line.startswith('SPACE GROUP OF SOLUTION:'):
                sg = line[24:].strip()[1:-1].replace(' ','')
            if line.startswith('  mass'):
                res = int(line.split()[2][1:-1])/110
            if line.startswith('AutoMR Input failed'):
                nosol = True
            if line.startswith('No solutions found'):
                nosol = True                
        if pdb == False:
            nosol = True
            
        if nosol:
            automr = {      'AutoMR nosol': 'True',
                            'AutoMR tar'  : 'None',
                            'AutoMR pdb'  : 'No solution',
                            'AutoMR mtz'  : 'No solution',
                            'AutoMR gain' : 'No solution',
                            'AutoMR rfz'  : 'No solution',
                            'AutoMR tfz'  : 'No solution', 
                            'AutoMR dir'  : 'No solution',
                            'AutoMR sg'   : 'No solution',
                            'AutoMR adf'  : 'No solution',
                            'AutoMR peak' : 'No solution'
                                                         }
        else:
            automr = {      'AutoMR nosol': 'False',
                            'AutoMR pdb'  : pdb,
                            'AutoMR mtz'  : mtz,
                            'AutoMR gain' : llgain,
                            'AutoMR rfz'  : rfz,
                            'AutoMR tfz'  : tfz, 
                            'AutoMR dir'  : directory,
                            'AutoMR sg'   : sg
                                                          }                    
        return ((automr))
    
    except:
        self.logger.exception('**ERROR in Parse.ParseOutputAutoMR**')
        automr = {      'AutoMR nosol': 'True',
                        'AutoMR tar'  : 'None',
                        'AutoMR pdb'  : 'No solution',
                        'AutoMR mtz'  : 'No solution',
                        'AutoMR gain' : 'No solution',
                        'AutoMR rfz'  : 'No solution',
                        'AutoMR tfz'  : 'No solution', 
                        'AutoMR dir'  : 'No solution',
                        'AutoMR sg'   : 'No solution',
                        'AutoMR adf'  : 'No solution',
                        'AutoMR peak' : 'No solution'        
                                                     }
        return ((automr))
    
def ParseOutputPhaser(self,input):
    """
    Parse Phaser output.
    """
    self.logger.debug('Parse::ParseOutputPhaser')
    try:
        nosol = False
        pdb = False
        partial = False
        clash = False
        temp = []
        for line in input:
            temp.append(line)
            directory = os.getcwd()
            if line.startswith('FATAL RUNTIME ERROR: The composition'):
                return('matthews')
            if line.startswith('   Solution log-likelihood gain'):
                llgain = line.split()[-1]
                if float(llgain) < 0:
                    nosol = True
            if line.startswith('   Solution #1 log-likelihood gain'):
                llgain = line.split()[-1]
                if float(llgain) < 0:
                    nosol = True
            if line.startswith('   Solution written to PDB file'):
                pdb = line.split()[-1]
            if line.startswith('   Solution #1 written to PDB file'):
                pdb = line.split()[-1]
            if line.startswith('   Solution written to MTZ file'):
                mtz = line.split()[-1]
            if line.startswith('   Solution #1 written to MTZ file'):
                mtz = line.split()[-1]
            if line.startswith('   Solution #1 annotation'):
                rfz = line.split()[4][4:]
                tfz = line.split()[5][4:]
                clash = line.split()[6][4:]
            if line.startswith('   Solution annotation'):
                rfz = line.split()[3][4:]
                tfz = line.split()[4][4:]
                clash = line.split()[5][4:]
            if line.startswith('   SpaceGroup of Solution'):
                #sg = line[26:].strip()[1:-1].replace(' ','')
                #sg = line[26:].strip()[0:-1].replace(' ','')
                sg = line[26:].replace(' ','')
            if line.startswith('   SpaceGroup of Partial'):
                sg = line[34:].replace(' ','')
            if line.startswith('   Partial Solution '):
                partial = True
                split = line.split()
                if split[5] == 'PDB':
                    pdb = split[7]
                if split[5] == 'MTZ':
                    mtz = split[7]
                if split[3] == 'log-likelihood':
                    llgain = split[5]
                if split[3] == 'annotation':
                    rfz = line.split()[5][4:]
                    tfz = line.split()[6][4:]
                    clash = line.split()[7][4:]
            """
            if partial == False:
                if line.startswith('   Sorry - No solution'):
                    nosol = True            
            if line.startswith('AutoMR Input failed'):
                nosol = True
            if line.startswith('No solutions found'):
                nosol = True            
            if line.startswith('   Sorry - No solution'):
                nosol = True
            """
        if pdb == False:
            nosol = True
            
        if nosol:
            automr = {      'AutoMR nosol': 'True',
                            'AutoMR tar'  : 'None',
                            'AutoMR pdb'  : 'No solution',
                            'AutoMR mtz'  : 'No solution',
                            'AutoMR gain' : 'No solution',
                            'AutoMR rfz'  : 'No solution',
                            'AutoMR tfz'  : 'No solution',
                            'AutoMR clash': 'No solution',
                            'AutoMR dir'  : 'No solution',
                            'AutoMR sg'   : 'No solution',
                            'AutoMR adf'  : 'No solution',
                            'AutoMR peak' : 'No solution'        
                                                         }
            if clash:
                automr['AutoMR clash'] = clash
        else:
            automr = {      'AutoMR nosol': 'False',
                            'AutoMR pdb'  : pdb,
                            'AutoMR mtz'  : mtz,
                            'AutoMR gain' : llgain,
                            'AutoMR rfz'  : rfz,
                            'AutoMR tfz'  : tfz,
                            'AutoMR clash': clash,
                            'AutoMR dir'  : directory,
                            'AutoMR sg'   : sg,
                            'AutoMR adf'  : 'None',
                            'AutoMR peak' : 'None'
                                                          }                    
        #print automr
        return ((automr))
    
    except:
        self.logger.exception('**ERROR in Parse.ParseOutputPhaser**')
        automr = {      'AutoMR nosol': 'True',
                        'AutoMR tar'  : 'None',
                        'AutoMR pdb'  : 'No solution',
                        'AutoMR mtz'  : 'No solution',
                        'AutoMR gain' : 'No solution',
                        'AutoMR rfz'  : 'No solution',
                        'AutoMR tfz'  : 'No solution', 
                        'AutoMR clash': 'No solution',
                        'AutoMR dir'  : 'No solution',
                        'AutoMR sg'   : 'No solution',
                        'AutoMR adf'  : 'No solution',
                        'AutoMR peak' : 'No solution'        
                                                     }            
        return ((automr))

def ParseOutputXtriage(self,input):
    """
    Parse phenix.xtriage output.
    """    
    self.logger.debug('Parse::ParseOutputXtriage')
    try:
        temp = []
        junk = []
        junk2 = []
        anom = {}
        table = []
        int_plot = []
        z_plot = []
        anom_plot = []
        i_plot = []
        nz_plot = []
        ltest_plot = []
        pat_p = []
        pat = {}
        twin_info = {}
        summary = []
        log = []
        pts = False
        twin = False
        pat_st = False
        pat_dist = False
        skip = True
        pat_info = {}
        coset = []
        
        for line in input:
            temp.append(line)
            if line.startswith('bin '):
                junk.append(line)
            if line.startswith('##                    Basic statistics'):
                start = temp.index(line)
            if line.startswith('$TABLE:'):
                table.append(temp.index(line))
            if line.startswith('Basic analyses completed'):
                table.append(temp.index(line))
            if line.startswith('Twinning and intensity'):
                table.append(temp.index(line))    
            if line.startswith('  Multivariate Z score'):
                z_score = line.split()[4]
            if line.startswith(' Frac. coord.'):
                pat_x = line.split()[3]
                pat_y = line.split()[4]
                pat_z = line.split()[5]
            if line.startswith(' Distance to origin'):
                pat_dist = line.split()[4]
            if line.startswith(' Height (origin=100)'):
                pat_height = line.split()[3]
            if line.startswith(' p_value(height)'):
                pat_p = line.split()[2]
                if float(pat_p)<=0.05:
                    pts = True
            if line.startswith('Patterson analyses'):
                index1 = temp.index(line)
            if line.startswith('The full list of Patterson peaks is:'):
                pat_st = temp.index(line)
            if line.startswith('Systematic absences'):
                pat_fn = temp.index(line)
            if line.startswith('| Type | Axis   | R metric'):
                twin = True
                twin_st = temp.index(line)
            if line.startswith('M:  Merohedral twin law'):
                twin_fn = temp.index(line)
            if line.startswith('Statistics depending on twin'):
                twin2_st = temp.index(line)
            if line.startswith('  Coset number'):
                coset.append(temp.index(line))
            if line.startswith('The present crystal symmetry does not allow'):
                coset = False
        
        if pat_dist:
            data2 = {'frac x': pat_x,
                     'frac y': pat_y,
                     'frac z': pat_z,
                     'peak'  : pat_height,
                     'p-val' : pat_p,
                     'dist'  : pat_dist  }
            pat['1'] = data2
        else:
            skip = False
        
        if pat_st:
            i = 2
            for line in temp[pat_st+2:pat_fn]:
                split = line.split()
                if line.startswith('('):
                    if skip == False:                    
                        x = line[1:7].replace(' ','')
                        y = line[8:14].replace(' ','')
                        z = line[15:21].replace(' ','')
                        pk = line[25:34].replace(' ','')
                        p = line[38:-2].replace(' ','')
                        data = {'frac x'    : x,
                                'frac y'    : y,
                                'frac z'    : z,
                                'peak'      : pk,
                                'p-val'     : p}
                        pat[str(i)] = data
                        i +=1
                    skip = False              
                if line.startswith(' space group'):
                    pts = True
                    pts_sg = temp.index(line)
                    i1 = 1
                    for line2 in temp[pts_sg+1:pat_fn]:
                        if line2.split() != []:
                            a = line2.find('(')
                            b = line2.find(')')
                            c = line2.rfind('(')
                            d = line2.rfind(')')
                            sg = line2[:a-1].replace(' ','')+' '+line2[a:b+1].replace(' ','')
                            op = line2[b+1:c].replace(' ','')
                            ce = line2[c+1:d]
                            """
                            sg = line2[:23].replace(' ','')
                            op = line2[23:46].replace(' ','')
                            ce = line2[46:-2].replace(' ','')
                            """
                            data2 = {'space group'    : sg,
                                     'operator'       : op,
                                     'cell'           : ce}
                            pat_info[i1] = data2
                            i1 +=1
        if twin:
            for line in temp[twin_st+2:twin_fn-1]:
                split = line.split()
                law = split[11]            
                data = {'type'     : split[1],
                        'axis'     : split[3],
                        'r_metric' : split[5],
                        'd_lepage' : split[7],
                        'd_leb'    : split[9],
                        }
                twin_info[law] = data
            for line in temp[twin2_st+4:index1-2]:
                split = line.split()
                law = split[1]
                data = {'r_obs'      : split[5],
                        'britton'    : split[7],
                        'h-test'     : split[9],
                        'ml'         : split[11]}
                twin_info[law].update(data)
            if coset:
                for line in coset[1:]:
                    sg = temp[line][38:-2]
                    try:
                        for i in range(2,4):
                            law = temp[line+i].split()[1]
                            if twin_info.has_key(law):
                                twin_info[law].update({'sg':sg})
                    except:
                        self.logger.exception('Warning. Missing Coset info.')
            else:
                crap = {'sg':'NA'}
                for key in twin_info.keys():
                    twin_info[key].update(crap)
        for line in junk[10:20]:
            if len(line.split()) == 7:
                anom[line.split()[4]] = line.split()[6]
            else:
                anom[line.split()[4]] = '0.0000'
        for line in temp[table[0]+6:table[1]-3]:
            if len(line.split()) == 4:
                res = str(math.sqrt(1/float(line.split()[0])))
                temp2 = []       
                temp2.append(res)
                temp2.extend(line.split()[1:])
                int_plot.append(temp2)
        for line in temp[table[1]+6:table[2]-3]:
            if len(line.split()) == 3:
                res = str(math.sqrt(1/float(line.split()[0])))
                temp2 = []       
                temp2.append(res)
                temp2.extend(line.split()[1:])
                z_plot.append(temp2)
        if len(temp[table[2]+7].split()) == 3:
            for line in temp[table[2]+6:table[3]-3]:
                res = str(math.sqrt(1/float(line.split()[0])))
                temp2 = []       
                temp2.append(res)
                temp2.extend(line.split()[1:])
                anom_plot.append(temp2)        
            i_st    = table[3]+6
            i_fn    = table[4]-1
            nz_st   = table[5]+6
            nz_fn   = table[6]-3
            lt_st   = table[6]+6
            lt_fn   = table[6]+56
            l_st    = table[4]+2
            l_fn    = table[5]-4            
        else:
            for line in z_plot:
                anom_plot.append([line[0],'0.0','0.0'])
            i_st    = table[2]+6
            i_fn    = table[3]-1
            nz_st   = table[4]+6
            nz_fn   = table[5]-3
            lt_st   = table[5]+6
            lt_fn   = table[5]+56
            l_st    = table[3]+2
            l_fn    = table[4]-4
        
        for line in temp[i_st:i_fn]:
            if len(line.split()) == 2:
                res = str(math.sqrt(1/float(line.split()[0])))
                temp2 = []       
                temp2.append(res)
                temp2.extend(line.split()[1:])
                i_plot.append(temp2)
        for line in temp[nz_st:nz_fn]:
            nz_plot.append(line.split())
        for line in temp[index1+5:-3]:
            summary.append(line)
        for line in temp[lt_st:lt_fn]:
            ltest_plot.append(line.split())
    
        xtriage = {'Xtriage anom'         : anom,
                   'Xtriage anom plot'    : anom_plot,
                   'Xtriage int plot'     : int_plot,
                   'Xtriage i plot'       : i_plot,
                   'Xtriage z plot'       : z_plot,
                   'Xtriage nz plot'      : nz_plot,
                   'Xtriage l-test plot'  : ltest_plot,
                   'Xtriage z-score'      : z_score,
                   'Xtriage pat'          : pat,
                   'Xtriage pat p-value'  : pat_p,
                   'Xtriage summary'      : summary,
                   #'Xtriage log'          : log,
                   'Xtriage PTS'          : pts,
                   'Xtriage PTS info'     : pat_info,
                   'Xtriage twin'         : twin,
                   'Xtriage twin info'    : twin_info,       }        
        return ((xtriage))
    
    except:
        self.logger.exception('**ERROR in Parse.ParseOutputXtriage**')
        return ((None))
    
def ParseOutputMolrep(self,input):
    """
    Parse Molrep SRF output.
    """
    self.logger.debug('Parse::ParseOutputMolrep')
    try:
        log_path = os.path.join(os.getcwd(),'molrep.doc')
        srf_path = os.path.join(os.getcwd(),'molrep_rf.jpg')        
        temp = []
        pat = {}
        pts = False
        for line in input:
            temp.append(line)
            if line.startswith('INFO: pseudo-translation was detected'):
                ind1 = temp.index(line)
                pts = True
            if line.startswith('INFO:  use keyword: "PST"'):
                ind2 = temp.index(line)
        if pts:        
            for line in temp[ind1:ind2]:
                split = line.split()
                if split[0] == 'Origin':
                    junk = {'peak'     : split[-2],
                            'psig'     : split[-1]}
                    pat['origin'] = junk
                if split[0].isdigit():
                    junk1 = {'peak'     : split[-2],
                             'psig'     : split[-1]}
                    pat[split[0]] = junk1
                if split[0] == 'Peak':
                    ind3 = temp.index(line)
                    pat[split[1][:-1]].update({'frac x' : temp[ind3+1].split()[-3]})
                    pat[split[1][:-1]].update({'frac y' : temp[ind3+1].split()[-2]})
                    pat[split[1][:-1]].update({'frac z' : temp[ind3+1].split()[-1]})
        
        molrep  =  {'Molrep log'    : log_path,
                    'Molrep jpg'    : srf_path,
                    'Molrep PTS'    : pts,
                    'Molrep PTS_pk' : pat,
                                              }
        return ((molrep))
    
    except:
        self.logger.exception('**ERROR in Parse.ParseOutputMolrep**')
        return ((None))
    
if __name__ == '__main__':
    #start logging
    LOG_FILENAME = '/tmp/rapd_agent_parse.log'
    # Set up a specific logger with our desired output level
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=100000, backupCount=5)
    #add a formatter
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('Utilities.__init__')

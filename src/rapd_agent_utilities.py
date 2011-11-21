'''
__author__ = "Jon Schuermann, Frank Murphy"
__copyright__ = "Copyright 2009, NE-CAT"
__credits__ = ["Jon Schuermann","Frank Murphy","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3_clause"
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
import numpy
import pexpect 
import pprint
import paramiko
import logging,logging.handlers
import rapd_agent_parse as Parse

def calcADF(self,input):
    """
    Calc an ADF from MR phases.
    """
    self.logger.debug('Utilities::calcADF')
    try:        
        sg  = self.phaser_results[input].get('AutoMR results').get('AutoMR sg')
        mtz = self.phaser_results[input].get('AutoMR results').get('AutoMR mtz')
        pdb = self.phaser_results[input].get('AutoMR results').get('AutoMR pdb')
        dir = self.phaser_results[input].get('AutoMR results').get('AutoMR dir')
        mtz_path = os.path.join(dir,mtz)
        pdb_path = os.path.join(dir,pdb)            
        map  = input+'_adf.map'
        peak = input+'_adf_peak.pdb'            
        #Put path of map and peaks pdb in results
        self.phaser_results[input].get('AutoMR results')['AutoMR adf'] = os.path.join(os.getcwd(),map)
        self.phaser_results[input].get('AutoMR results')['AutoMR peak'] = os.path.join(os.getcwd(),peak)
        file_type = self.datafile[-3:]
        if file_type == 'mtz':
            command  = 'cad hklin1 '+mtz_path+' hklin2 '+self.datafile+' hklout adf_input.mtz<<eof3\n'
        else:        
            command  = 'scalepack2mtz hklin '+self.datafile+' hklout junk.mtz<<eof1\n'
            command += 'symm '+sg+'\n'
            command += 'anomalous yes\n'
            command += 'end\n'
            command += 'eof1\n'
            command += 'truncate hklin junk.mtz hklout junk2.mtz<<eof2\n'
            command += 'truncate yes\n'
            command += 'anomalous yes\n'
            command += 'end\n'
            command += 'eof2\n'
            command += 'cad hklin1 '+mtz_path+' hklin2 junk2.mtz hklout adf_input.mtz<<eof3\n'
        command += 'labin file 1 E1=FC  E2=PHIC E3=FOM\n'
        command += 'labin file 2 all\n'
        command += 'end\n'
        command += 'eof3\n'
        command += 'fft hklin adf_input.mtz mapout map.tmp<<eof4\n'
        command += 'scale F1 1.0\n'
        command += 'labin DANO=DANO SIG1=SIGDANO PHI=PHIC W=FOM\n'
        command += 'end\n'
        command += 'eof4\n'
        command += 'mapmask mapin map.tmp xyzin '+pdb_path+' mapout '+map+'<<eof5\n'
        command += 'border 5\n'
        command += 'end\n'
        command += 'eof5\n'
        command += 'peakmax mapin '+map+' xyzout '+peak+'<<eof6\n'
        command += 'numpeaks 50\n'
        command += 'end\n'
        command += 'eof6\n\n'
        adf = open('adf.com','w')
        adf.writelines(command)
        adf.close()
        adf_path = os.path.join(os.getcwd(),'adf.com')
        #self.logger.debug(command)
        temp = []
        if self.cluster_use:
            return (processCluster(self,adf_path,file=True))
        else:
            output = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            for line in output.stdout:
                temp.append(line)
            #return ('0')
        
    except:
        self.logger.exception('**Error in Utils.calcADF**')

def calcResNumber(self,sg,se=False):
    """
    Create the raddose.com file which will run in processRaddose. Several beamline specific entries for flux and
    aperture size included in the module.
    """
    self.logger.debug('Utilities::calcResNumber')
    try:
        volume = calcVolume(self)
        checkVolume(self,volume)
        num_residues = calcTotResNumber(self,volume)
        if sg == 'R3':
            if self.cell2[-1].startswith('120'):
                den = int(symopsSG(self,'H3'))
            else:
                den = int(symopsSG(self,sg))
        elif sg == 'R32':
            if self.cell2[-1].startswith('120'):
                den = int(symopsSG(self,'H32'))
            else:
                den = int(symopsSG(self,sg))        
        else:
            den = int(symopsSG(self,sg))        
        #Figure about 1 SeMet every 75 residues.
        if se:
            tot_se = num_residues/75
            num_se = tot_se/den
            if num_se == 0:
                num_se = 1
            return (num_se)
        else:
            tot_au = num_residues/den
            return (tot_au)
            
    except:
        self.logger.exception('**Error in Utils.calcResNumber**')
        if se:
            return(5)
        else:
            return(200)

def calcTotResNumber(self,volume):
    """
    Calculates number of residues in the unit cell for Raddose calculation. If cell volume bigger than 50000000, then 
    turns on Ribosome which makes changes so meaning strategy is presented.
    """
    try:
        self.logger.debug('Utilities::calcTotResNumber')
        checkVolume(self,volume)
        #Calculate number of residues based on solvent content in volume of cell.
        if self.sample_type == 'Protein':
            protein_content      = 1 - float(self.solvent_content)
            if volume:
                num_residues = int((float(volume)*float(protein_content))/135.3)
                #based on average MW of residue = 110 DA               
        elif self.sample_type == 'DNA':
            dna_content      = 1 - float(self.solvent_content)
            if volume:
                num_residues = int((float(volume)*float(dna_content))/273.9)
                #based on average MW of residue = 330 DA        
        else:
            rna_content      = 1 - float(self.solvent_content)
            if volume:
                num_residues = int((float(volume)*float(rna_content))/282.2)
                #based on average MW of residue = 340 DA
        return (num_residues)
    
    except:
        self.logger.exception('**Error in Utils.calcTotResNumber**')
        return (None)

def calcTransmission(self,attenuation=1):
    """
    Calculate appropriate setting for % transmission
    """
    self.logger.debug('Utilities::calcTransmission')
    try:
        #self.transmission = float(self.header.get('transmission'))
        if self.distl_results:
            if self.distl_results['Distl results'] != 'FAILED':
                temp    = self.distl_results.get('Distl results').get('mean int signal')
                mean_int_sig = float(max(temp))
                if mean_int_sig < 1:
                    mean_int_sig = -1
        else:
            mean_int_sig = -1
        
        #TESTING: Adjusting the '4000' number to give reasonable results for expected transmission setting.
        #if self.best_failed == False:    
        if mean_int_sig != -1:                    
            trans = int((4000/(mean_int_sig))*self.transmission*attenuation)
            if trans > 100:
                trans = int(100)
            if trans < 1:
                trans = int(1)
        else:
            trans = int(attenuation*self.transmission)  
        return (trans)
    
    except:
        self.logger.exception('**Error in Utils.calcTransmission**')
        return (1)

def calcVolume(self):
    """
    Calculate and return volume of unit cell.
    """
    self.logger.debug('Utilities::calcVolume')
    try:            
        log = []            
        #Run Raddose to get the volume of the cell.
        rad = open('raddose.com', 'w')
        setup = 'raddose << EOF\n'
        #put together the command script for Raddose            
        if type(self.cell) == list:
            cell = str(self.cell[0])+' '+str(self.cell[1])+' '+str(self.cell[2])+' '+ \
                            str(self.cell[3])+' '+str(self.cell[4])+' '+str(self.cell[5])
        else:
            cell = self.cell
        setup += 'CELL '+cell+'\n'
        setup += 'END\nEOF\n'
        rad.writelines(setup)
        rad.close()
        execute = 'tcsh raddose.com' 
        output = subprocess.Popen(execute, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)                                
        for line in output.stdout:
            log.append(line)
            #self.logger.debug(line.rstrip())                                
            if line.startswith('Unit Cell Volume'):
                volume = float((line.split())[4])
        return(volume)
    
    except:
        self.logger.exception('**Error in Utils.calcVolume**')
        return(None)

def changeIns(self):
    """
    Change the ins file for ShelxD to account for nproc in multiShelxD mode.
    """
    self.logger.debug('Utilities::changeIns')
    try:    
        ntry = self.shelxd_try/self.njobs
        if ntry == 0:
            ntry = 1
        cp = 'cp junk_fa.ins junk_fa_orig.ins'
        os.system(cp)
        ins_file = 'junk_fa.ins'
        junk = []
        fix = False
        file = open(ins_file,'r')
        for line in file:
            junk.append(line)
            if line.startswith('SEED'):
                index = junk.index(line)
                new_line = line.replace(line.split()[1],'0')                                        
                junk.remove(line)
                junk.insert(index, new_line)
            if line.startswith('NTRY'):
                index2 = junk.index(line)
                new_line2 = line.replace(line.split()[1],str(ntry))                                        
                junk.remove(line)
                junk.insert(index2, new_line2)            
            if line.startswith('PATS'):                
                if self.many_sites:
                    new = 'PATS 200\nWEED 0.3'
                    fix = True
                if self.cubic:
                    new = 'WEED 0.3'
                    fix = True    
                if fix:
                    index3 = junk.index(line)
                    new_line3 = line.replace(line.split()[0],new)
                    junk.remove(line)
                    junk.insert(index3,new_line3)                    
        file.close()
        file2 = open(ins_file,'w')
        file2.writelines(junk)
        file2.close()
    
    except:
        self.logger.exception('**Error in Utils.ChangeIns**')        

def checkAnom(self):
    """
    Check to see if anomalous signal is present in data.
    """
    try:
        signal = False
        scala_log = self.data.get('original').get('scala_log')
        #cc_anom   = self.data.get('original').get('cc_anom')
        log = open(scala_log,'r')
        for line in log:
            if line.startswith('  Completeness'):
                comp = line.split()[1]
            if line.startswith('  Multiplicity'):
                mult = line.split()[1]
            if line.startswith('  Anomalous completeness'):
                comp_anom = line.split()[2]
            if line.startswith('  Anomalous multiplicity'):
                mult_anom = line.split()[2]
            if line.startswith('  Mid-Slope of'):
                slope = line.split()[5]
            if line.startswith('  Rmerge    '):
                r = line.split()[1]
            if line.startswith('  Rpim (within'):
                rpim_anom = line.split()[3]
            if line.startswith('  Rpim (all'):
                rpim = line.split()[5]
            if line.startswith('  DelAnom correlation'):
                cc_anom = line.split()[4]
                
        if float(comp) > 70:
            if float(slope) > 1:
                if float(cc_anom) > 0.1:
                    #copy sca file to local directory so path isn't too long for SHELX
                    sca = os.path.basename(self.datafile)
                    shutil.copy(self.datafile,sca)           
                    command  = 'shelxc junk <<EOF\n'
                    command += 'CELL ' + self.cell + '\n'
                    command += 'SPAG ' + self.input_sg + '\n'
                    command += 'SAD '  + sca + '\n'
                    command += 'FIND 1' 
                    command += 'SFAC Se'
                    command += 'EOF\n'                    
                    output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    temp = []
                    for line in output.stdout:
                        temp.append(line)
                    #shelx = self.ParseOutputShelxC(temp)
                    shelx = Parse.ParseOutputShelxC(self,temp)
                    dsig = shelx.get('shelxc_dsig')
                    max_dsig = max(dsig)
                    if max_dsig > 1:
                        signal = True
                    else:
                        signal = False
        if signal:
            return (True)   
        else:            
            Parse.setShelxNoSignal(self)
            return (False)        
           
    except:
        self.logger.exception('**ERROR in Utils.checkAnom**')
        Parse.setShelxNoSignal(self)
        return(False)

def checkCell(self):
    """
    Do sanity check on user input SG.
    """
    self.logger.debug('Utilities::checkCell')
    try:
        command = 'phenix.reflection_file_converter ' + self.datafile + ' --space-group=' + self.space_group
        #self.logger.debug(command)
        output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.logger.debug('Checking Compatibility of cell to user input SG.')
        for line in output.stdout:
            self.logger.debug(line.rstrip())
            if line.startswith('AssertionError: Space group is incompatible'):
                self.incompatible_cell = True
                self.logger.debug('User input SG is NOT compatible with *.sca file SG. Using *.sca file SG instead.')
        
    except:
        self.logger.exception('**ERROR in Utils.checkCell**')

def checkInverse(self,input):
    """
    Check if inverse SG is possible.
    """
    self.logger.debug('Utilities::checkInverse')
    try:
        subgroups = {  '76' : ['78'],
                       '91' : ['95'],
                       '92' : ['96'],
                       '144': ['145'],
                       '151': ['153'],
                       '152': ['154'],
                       '169': ['170'],
                       '171': ['172'],
                       '178': ['179'],
                       '180': ['181'],
                       '212': ['213'] 
                       }
        
        if subgroups.has_key(input):
            sg = subgroups[input]
            return(sg)
        else:
            return([input])
    except:
        self.logger.exception('**ERROR in Utils.checkInverse**')

def checkMatthews(self):
    """
    Check Matthews to see if PDB file will fit in AU.
    """
    self.logger.debug('Utilities::checkMatthews')
    try:
        pdb_info = getPDBmw(self,self.input_pdb)
        check = 'OK'
        command  = 'phaser << eof\n'
        command += 'TITLe junk\n'
        command += 'MODE CCA\n'
        command += 'HKLIn '+self.datafile+'\n'
        command += 'LABIn F=F SIGF=SIGF\n'
        command += 'COMPosition PROTein MW '+str(pdb_info['MWaa'])+' NUM '+str(pdb_info['NMol'])+'\n'
        command += 'COMPosition NUCLEIC MW '+str(pdb_info['MWna'])+' NUM 1\n'
        command += 'eof\n'
        output = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        for line in output.stdout:
            if line.startswith('FATAL RUNTIME ERROR'):
                check = 'BAD'
        if check == 'BAD':
            name = os.path.basename(self.input_pdb)
            new_segid = pdb_info['SegID'][0]
            new_name = name[:-4]+'_'+new_segid+'.pdb'
            command2 = 'phenix.pdb_atom_selection '+name+' "chain '+new_segid+'" --write-pdb-file='+new_name
            output2 = subprocess.Popen(command2,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT).wait()
            self.input_pdb = os.path.join(os.getcwd(),new_name)
            check = 'Fixed'
        self.logger.debug('Utils.checkMatthews Results: '+check)
        
    except:
        self.logger.exception('**ERROR in Utils.checkMatthews')

def checkSG(self,input):
    """
    Check SG subgroups.
    """
    self.logger.debug('Utilities::checkSG')
    try:
        subgroups = {  '1'  : [None],
                       '5'  : [None],
                       '3'  : ['4'],
                       '22' : [None],
                       '23' : ['24'],
                       '21' : ['20'],
                       '16' : ['17','18','19'],
                       '79' : ['80','97','98'],
                       '75' : ['76','77','78','89','90','91','95','94','93','92','96'],
                       '143': ['144','145','149','151','153','150','152','154','168','169','170','171','172','173','177','178','179','180','181','182'],
                       '146': ['155'],
                       '196': [None],
                       '209': ['210'],
                       '197': ['199'],
                       '211': ['214'],
                       '195': ['198'],
                       '207': ['208','212','213'] }
        
        sg = subgroups[input]
        return(sg)
    
    except:
        self.logger.exception('**ERROR in Utils.checkSG**')        

def checkVolume(self,volume):
    """
    Check to see if unit cell is really big.
    """
    self.logger.debug('Utilities::checkVolume')
    try:
        #if float(volume) > 50000000.0: #For 70S
        if float(volume) > 25000000.0: #For 30S
            self.sample_type = 'Ribosome'
            self.solvent_content = 0.64
    except:
        self.logger.exception('**Error in Utils.checkVolume**')
        
def convertImage(self,input,output):
    """
    Convert image to new type.
    """
    self.logger.debug('Utilities::convertImage')
    try:       
        command = 'convert '+input+' '+output
        myoutput = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    except:
        self.logger.exception('**ERROR in Utils.convertImage**')
        
def convertSG(self, input, reverse=False):
    """
    Convert SG to SG#.
    """                
    self.logger.debug('Utilities::convertSG')
    try:
        intl2std =   {'P1'       : '1'  ,
                      'C2'       : '5'  ,
                      'C121'     : '5'  ,
                      'I121'     : '5.1',
                      'A121'     : '5.2',
                      'A112'     : '5.3',
                      'B112'     : '5.4',
                      'I112'     : '5.5',
                      'P2'       : '3'  ,
                      'P121'     : '3'  ,
                      'P21'      : '4'  ,
                      'P1211'    : '4'  ,
                      'F222'     : '22' ,
                      'I222'     : '23' ,
                      'I212121'  : '24' ,
                      'C222'     : '21' ,
                      'C2221'    : '20' ,
                      'P222'     : '16' ,
                      'P2221'    : '17' ,
                      'P2212'    : '17.1',
                      'P2122'    : '17.2',
                      'P21212'   : '18' ,
                      'P21221'   : '18.1',
                      'P22121'   : '18.2',
                      'P212121'  : '19' ,
                      'I4'       : '79' ,
                      'I41'      : '80' ,
                      'I422'     : '97' ,
                      'I4122'    : '98' ,
                      'P4'       : '75' ,
                      'P41'      : '76' ,
                      'P42'      : '77' ,
                      'P43'      : '78' ,
                      'P422'     : '89' ,
                      'P4212'    : '90' ,
                      'P4122'    : '91' ,
                      'P4322'    : '95' ,
                      'P4222'    : '93' ,
                      'P42212'   : '94' ,
                      'P41212'   : '92' ,
                      'P43212'   : '96' ,
                      'P3'       : '143',
                      'P31'      : '144',
                      'P32'      : '145',
                      'P312'     : '149',
                      'P3112'    : '151',
                      'P3212'    : '153',
                      'P321'     : '150',
                      'P3121'    : '152',
                      'P3221'    : '154',
                      'P6'       : '168',
                      'P61'      : '169',
                      'P65'      : '170',
                      'P62'      : '171',
                      'P64'      : '172',
                      'P63'      : '173',
                      'P622'     : '177',
                      'P6122'    : '178',
                      'P6522'    : '179',
                      'P6222'    : '180',
                      'P6422'    : '181',
                      'P6322'    : '182',
                      'R3'       : '146.1',
                      'H3'       : '146.2',
                      'R32'      : '155.1',
                      'H32'      : '155.2',
                      'F23'      : '196',
                      'F432'     : '209',
                      'F4132'    : '210',
                      'I23'      : '197',
                      'I213'     : '199',
                      'I432'     : '211',
                      'I4132'    : '214',
                      'P23'      : '195',
                      'P213'     : '198',
                      'P432'     : '207',
                      'P4232'    : '208',
                      'P4332'    : '212',
                      'P4132'    : '213'    }
        
        if reverse:                
            junk = intl2std.items()
            for line in junk:                
                if line[1] == input:                        
                    sg = line[0]  
        else:
            sg = intl2std[input]
        return(sg)
    
    except:
        self.logger.exception('**ERROR in Utils.convertSG**')

def convertShelxFiles(self,input):
    """
    Add symmetry to shelx HA pdb file.
    """
    self.logger.debug('Utilities::convertShelxFiles')
    try:
        inv = self.shelx_results0[input].get('Shelx results').get('shelxe_inv_sites')
        if inv == 'True':
            sg = convertSG(self,checkInverse(self,convertSG(self,input))[0],True)
        else:
            sg = input
        #Rename phs file
        if inv == 'True':
            if os.path.exists('junk_i.phs'):
                shutil.copy('junk_i.phs',sg+'.phs')
            if os.path.exists('junk_i.hat'):
                shutil.copy('junk_i.hat',sg+'.hat')
        else:
            if os.path.exists('junk.phs'):
                shutil.copy('junk.phs',sg+'.phs')
            if os.path.exists('junk.hat'):
                shutil.copy('junk.hat',sg+'.hat')
        
    except:
        self.logger.exception('**ERROR in Utils.convertShelxFiles**')

def denzo2mosflm(self):
    """
    Convert Denzo A matrix to Mosflm format.
    """
    self.logger.debug('Utilities::denzo2mosflm')
    if self.test:
        os.chdir('/home/schuerjp/Data_processing/Frank/Output/labelit_iteration0')
        align_omega = ['65.641']
    else:    
        align_omega                  = self.stacalign_results.get('STAC align results').get('omega')    
    
    try:        
        temp  = []
        temp2 = []
        temp3 = []
        ub = []
        input = open('name1.x','r')
        
        a1 = input[1].split()[0]
        a2 = input[1].split()[1]
        a3 = input[1].split()[2]
        b1 = input[2].split()[0]
        b2 = input[2].split()[1]
        b3 = input[2].split()[2]
        c1 = input[3].split()[0]
        c2 = input[3].split()[1]
        c3 = input[3].split()[2]
        
        line1 = 'UB             ' + c1 + ' ' + c2 + ' ' + c3 + '\n'
        line2 = '               ' + a1 + ' ' + a2 + ' ' + a3 + '\n'
        line3 = '               ' + b1 + ' ' + b2 + ' ' + b3 + '\n'
        
        omega = 'PHISTART         ' + align_omega[0] + '\n'
        cp = 'cp bestfile.par bestfile_old.par'
        self.logger.debug(cp)
        cp = shutil.copy()
        os.system(cp)
        bestfile = open('bestfile_old.par','r')               
        
        for line in bestfile:
            temp2.append(line)
            if line.startswith('PHISTART'):
                junk1 = temp2.index(line)
                temp2.remove(line)
            if line.startswith('UB'):
                junk = temp2.index(line)
                temp2.remove(line)
            if line.startswith('      '):
                temp2.remove(line)                        
        bestfile.close()
        temp2.insert(junk1,omega)
        temp2.insert(junk,line1)
        temp2.insert(junk+1,line2)
        temp2.insert(junk+2,line3)        
        input.close()
        out = open('bestfile.par','w')
        out.writelines(temp2)
        out.close()
        
    except:
        self.logger.exception('**Error in Utils.denzo2mosflm**')

def distlComb(self):
    """
    Combine distl results into 1 dict.
    """
    try:
        dict = {}
        if self.distl_results0.get('Distl results') == 'FAILED':
            self.distl_results = {'Distl results' : 'FAILED'}
        else:
            keys = self.distl_results0.get('Distl results').keys()
            for key in keys:
                temp = self.distl_results0.get('Distl results')[key]
                temp.extend(self.distl_results1.get('Distl results')[key])
                dict[key] = temp
            self.distl_results = {'Distl results' : dict}
    
    except:
        self.logger.exception('**Error in Utils.distlComb**')
    
def downloadPDB(self,input):
    """
    Download pdb.
    """
    self.logger.debug('Utilities::downloadPDB')
    try:
        pdb = input+'.pdb'                        
        getpdb = 'wget http://www.rcsb.org/pdb/files/'+pdb    
        if self.cluster_use:
            return (processCluster(self,getpdb))        
        else:                            
            temp = []
            output = subprocess.Popen(getpdb,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            for line in output.stdout:
                temp.append(line.rstrip())
    
    except:
        self.logger.exception('**Error in Utils.downloadPDB**')

def failedHTML(self,input):
    """
    Generates failed html to output for GUI.
    """
    self.logger.debug('Utilities::failedHTML')
    try:            
        if self.gui:
            file  = "<?php\n"
            file += "//prevents caching\n"
            file += 'header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");\n'
            file += 'header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");\n'
            file += 'header("Cache-Control: post-check=0, pre-check=0",false);\n'
            file += "session_cache_limiter();\n"
            file += "session_start();\n"
            file += "require('/var/www/html/rapd/login/config.php');\n"
            file += "require('/var/www/html/rapd/login/functions.php');\n"
            file += 'if(allow_user() != "yes")\n'
            file += "{\n"
            file += "    include ('./login/no_access.html');\n"
            file += "    exit();\n"
            file += "}\n"
            file += "?>\n\n"
            file += "<html>\n"
        else:                
            file = "<html>\n"                     
        file +='  <head>\n'
        file +='    <style type="text/css" media="screen">\n'
        if self.gui == False:    
            file +='      @import "dataTables-1.5/media/css/demo_page.css";\n'
            file +='      @import "dataTables-1.5/media/css/demo_table.css";\n'          
        file +='    body {\n'
        file +='      background-image: none;\n'
        file +='    }\n'
        file +='    .dataTables_wrapper {position: relative; min-height: 75px; _height: 302px; clear: both;    }\n'
        file +='    table.display td {padding: 1px 7px;}\n'
        file +='    #dt_example h1 {margin-top: 1.2em; font-size: 1.5em; font-weight: bold; line-height: 1.6em; color: green;\n'
        file +='                    border-bottom: 2px solid green; clear: both;}\n'
        file +='    #dt_example h2 {font-size: 1.2em; font-weight: bold; line-height: 1.6em; color: #808080; clear: both;}\n'
        file +='    #dt_example h3 {font-size: 1.4em; font-weight: bold; line-height: 1.6em; color: red; clear: both;}\n'
        file +='    #dt_example h4 {font-size: 1.4em; font-weight: bold; line-height: 1.6em; color: orange; clear: both;}\n'
        file +='    table.display tr.odd.gradeA { background-color: #eeffee;}\n'
        file +='    table.display tr.even.gradeA { background-color: #ffffff;}\n'
        file +='    </style>\n'
        if self.gui == False:    
            file +='    <script type="text/javascript" language="javascript" src="dataTables-1.5/media/js/jquery.js"></script>\n'
            file +='    <script type="text/javascript" language="javascript" src="dataTables-1.5/media/js/jquery.dataTables.js"></script>\n'
        file +='    <script type="text/javascript" charset="utf-8">\n'
        file +='      $(document).ready(function() {\n'
        file +='      } );\n'
        file +="    </script>\n\n\n"
        file +=" </head>\n"
        file +='  <body id="dt_example">\n'
        file +='    <div id="container">\n'
        file +='    <div class="full_width big">\n'
        file +='      <div id="demo">\n'
        if self.failed:
            file +='      <h3 class="results">Input data could not be analysed.</h3>\n'
        else:
            file +='      <h3 class="results">There was an error during data analysis or it timed out</h3>\n'
        file +="      </div>\n"
        file +="    </div>\n"
        file +="    </div>\n"
        file +="  </body>\n"
        file +="</html>\n"
        
        if file:
            if self.gui:
                #sp = 'plots_xtriage.php'
                sp = input+'.php'
            else:
                #sp = 'plots_xtriage.html'  
                sp = input+'.html'        
            junk = open(sp,'w')
            junk.writelines(file)
            junk.close()                
            if os.path.exists(os.path.join(self.working_dir,sp)):
                pass
            else:                
                shutil.copy(sp,self.working_dir)
                                
    except:
        self.logger.exception('**ERROR in Utils.failedHTML**.')

def fixBestSG(self):
    """
    Make user selected SG correct for BEST.
    """
    self.logger.debug('Utilities::fixBestSG')   
    try:        
        temp = []
        copy = 'cp bestfile.par bestfile_orig.par'
        self.logger.debug('Since user selected the space group, BEST files will be edited to match.')
        self.logger.debug(copy)
        os.system(copy)            
        orig = open('bestfile_orig.par','r').readlines()
        for line in orig:
            temp.append(line)
            if line.startswith('SYMMETRY'):
                split = line.split()
                if split[1] != self.spacegroup:
                    #new_line = 'SYMMETRY       ' + self.spacegroup + '\n'       
                    new_line = line.replace(split[1],self.spacegroup)
                    junk = temp.index(line)
                    temp.remove(line)
                    temp.insert(junk,new_line)
        new = open('bestfile.par','w')
        new.writelines(temp)
        new.close()    
    
    except:
        self.logger.exception('**ERROR in Utils.fixBestSG**')

def fixBestSGBack(self):
    """
    Best will fail if user selected SG is not found in autoindexing. This brings back the autoindexed SG.
    """
    self.logger.debug('Utilities::fixBestSGBack')
    try:
        self.logger.debug('The user selected SG was not found in autoindexing.')
        copy = 'cp bestfile_orig.par bestfile.par'
        self.logger.debug(copy)
        os.system(copy)
    
    except:
        self.logger.exception('**ERROR in Utils.fixBestSGBack**')

def fixBestfile(self):
    """
    Fix the 'BEAM SWUNG_OUT' line in case of 2 theta usage.
    """
    try:
        self.logger.debug('Utilities::fixBestfile')
        temp = []
        tt = False
        r3 = False
        bestpar = open('bestfile.par','r').readlines()
        for i,line in enumerate(bestpar):
            temp.append(line)
            if line.startswith('BEAM'):
                split = line.split()
                if split[1] == 'SWUNG_OUT':
                    tt = True
                    newline = 'BEAM           '+split[2]+' '+split[3] +'\n'
                    temp.remove(line)
                    temp.insert(i,newline)
            """
            #For STAC, but Sandor has corrected it now.
            if line.startswith('SYMMETRY'):
                split = line.split()[1]
                if split == 'H3':
                    r3 = True
                    newline = line.replace(split,'R3')
                    temp.remove(line)
                    temp.insert(i,newline)
            """
        if tt or r3:
            copy = 'cp bestfile.par bestfile_orig.par'
            os.system(copy)
            new = open('bestfile.par','w')
            new.writelines(temp)
            new.close()
    
    except:
        self.logger.exception('**ERROR in Utils.fixBestfile**')

def fixLabelit(self):
    """
    Change the distance line in the adsc.py file for Labelit.
    """
    self.logger.debug('Utilities::fixLabelit')
    try:            
        command = 'which labelit.index'
        l1 = '/home/sbgrid/programs/i386-linux/phenix/'
        l3 = 'cctbx_project/iotbx/detectors/'
        l4 = 'adsc.py'
        l5 = 'adsc_orig.py'        
        output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        for line in output.stdout:
            start = 28
            end   = line.find('build')
            ver = line[start:end]
        dir       = l1 + ver + l3
        path      = l1 + ver + l3 + l4                       
        copy_path = l1 + ver + l3 + l5            
        if self.test:                 
            l6 = 'junk.py'
            l7 = 'junk2.py'
            test_path = '/gpfs1/users/necat/rapd/programs/'
            paramiko.util.log_to_file('paramiko.log')
            username = 'necat'
            password = 'necatuser'
            transport = paramiko.Transport(('164.54.212.167'))
            transport.connect(username = username, password = password )
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.put(test_path+l5, test_path+l6)
            temp  = []
            old_line = "('DISTANCE','DISTANCE',float),"
            new_line = "          ('DISTANCE',r'\\nDISTANCE',float),\n"                
            file = sftp.open(test_path+l6,'r')
            for line in file:
                temp.append(line)
                if line.strip().startswith(old_line):
                    ind = temp.index(line)                                     
                    temp.remove(line)
                    temp.insert(ind, new_line)
            file2 = sftp.open(test_path+l7,'w')
            file2.writelines(temp)
            file.close()
            file2.close()
            sftp.close()
            transport.close()                
        else:
            paramiko.util.log_to_file('paramiko.log')
            username = 'sbgrid'
            password = 'Chicago$'
            transport = paramiko.Transport(('164.54.212.119'))
            transport.connect(username = username, password = password )
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.rename(path,copy_path)
            temp  = []
            old_line = "('DISTANCE','DISTANCE',float),"
            new_line = "          ('DISTANCE',r'\\nDISTANCE',float),\n"            
            try:            
                file = sftp.open(copy_path,'r')
                for line in file:
                    temp.append(line)
                    if line.strip().startswith(old_line):
                        ind = temp.index(line)                                     
                        temp.remove(line)
                        temp.insert(ind, new_line)
                file.close()
                file2 = sftp.open(path,'w')
                file2.writelines(temp)                
                file2.close()                
            except:
                self.logger.exception('Could not change adsc.py file so I will copy a known file over.')            
                sftp.put('/gpfs1/users/necat/rapd/programs/adsc.py', path)                                       
            sftp.close()
            transport.close()
      
    except:
        self.logger.exception('**ERROR in Utils.fixLabelit**')
    
def fixMosflmSG(self):
    """
    Make user selected SG correct for Mosflm.
    """
    self.logger.debug('Utilities::fixMosflSG')
    if self.test:
        self.index_number = 'index09'
        self.spacegroup = str(self.preferences.get('spacegroup'))
    try:
        temp = []
        file      = str(self.index_number)
        file2     = str(self.index_number) + '_orig'
        copy = 'cp ' + file + ' ' + file2
        self.logger.debug('Since user selected the space group, Mosflm files will be edited to match.')
        self.logger.debug(copy)
        os.system(copy)            
        orig = open(file,'r')
        for line in orig:
            temp.append(line)
            if line.startswith('SYMMETRY'):
                junk = temp.index(line)
                sg = line.split()[1]
                if sg != self.spacegroup:
                    new_line = 'SYMMETRY ' + self.spacegroup + '\n'                           
                    temp.remove(line)
                    temp.insert(junk, new_line)
        orig.close()
        new = open(file,'w')
        new.writelines(temp)
        new.close()    
    
    except:
        self.logger.exception('**ERROR in Utils.fixMosflmSG**')

def fixSCA(self,input=False):
    """
    #Fix spaces in SG and * in sca file.
    """
    self.logger.debug('Utilities::fixSCA')
    try:
        if input:
            sca = input
        else:
            sca = self.datafile
        old_sca = sca.replace('.sca','_orig.sca')
        shutil.copy(sca,old_sca)
        junk = open(old_sca, 'r').readlines()[2]
        sg = junk[61:-1]
        if input == False:
            if self.input_sg:
                junk2 = junk.replace(sg,self.input_sg)
        sca_file = open(old_sca, 'r')
        temp = []
        lines_fixed = 0
        for line in sca_file:
            temp.append(line)
            if input == False:
                if line.startswith(junk):
                    if self.input_sg:
                        temp.remove(line)
                        temp.insert(2,junk2)
            #Fix *'s in sca file
            if line.count('*'):
                temp.remove(line)
                lines_fixed += 1
        sca_file.close()        
        out = open(sca,'w')
        out.writelines(temp)
        out.close()
        self.logger.debug('Number of lines fixed in the SCA file: '+str(lines_fixed))
    
    except:
        self.logger.exception('**ERROR in Utils.fixSCA**')
       
def fixSG(self,input):
    """
    Fix input SG if R3/R32.
    """
    self.logger.debug('Utilities::fixSG')
    try:
        if input == 'H3':
            return ('R3')
        elif input == 'H32':
            return ('R32')
        elif input == 'R3:H':
            return ('R3')
        elif input == 'R32:H':
            return ('R32')        
        else:
            return(input)
    
    except:
       self.logger.exception('**ERROR in Utils.fixSG**')

def foldersLabelit(self,iteration=0):
    """
    Sets up new directory and changes to it for each error iteration in multiproc_labelit.
    """
    #self.logger.debug('Utilities::foldersLabelit')
    try:
        path = 'labelit_iteration' + str(iteration)
        self.labelit_dir = os.path.join(self.working_dir,path)            
        if os.path.exists(self.labelit_dir):
            os.chdir(self.labelit_dir)
        else:
            os.mkdir(self.labelit_dir)
            os.chdir(self.labelit_dir)
            pref = 'dataset_preferences.py'
            pref_path = os.path.join(self.working_dir,pref)
            shutil.copy(pref_path,pref)
    except:
        self.logger.exception('**Error in Utils.foldersLabelit**')
    
def folders(self,input):
    """
    Sets up new directory for programs.
    """
    try:
        path = str(input)
        dir = os.path.join(self.working_dir,path)
        if os.path.exists(dir) == False:
            os.mkdir(dir)
            #os.makedirs(dir)
        os.chdir(dir) 
    
    except:
        self.logger.exception('**Error in Utils.folders**')
        
def getInfoCellSG(self,input=False):
    """
    Get unit cell and SG from input data regardless of file type.
    """
    self.logger.debug('Utilities::getInfoCellSG')
    try:
        if input:
            sca = input
        else:
            sca = self.datafile        
        failed = False
        command = 'phenix.reflection_file_converter '+sca
        output = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        self.logger.debug('Getting cell and SG info from mtz file.')
        for line in output.stdout:
            if line.startswith('No reflection data found in input file'):
                failed = True
            else:
                if line.startswith('Unit cell:'):
                    if len(line.split()) == 8:
                        junk = line.split()[2:]
                        self.cell2 = []
                        self.cell2.append(junk[0][1:-1])
                        self.cell2.append(junk[1][:-1])
                        self.cell2.append(junk[2][:-1])
                        self.cell2.append(junk[3][:-1])
                        self.cell2.append(junk[4][:-1])
                        self.cell2.append(junk[5][:-1])
                        self.cell = self.cell2[0]+' '+self.cell2[1]+' '+self.cell2[2]+' '+self.cell2[3]+' '+self.cell2[4]+' '+self.cell2[5]
                if line.startswith('Space group:'):
                    par = line.find('(')
                    sg = line[12:par].upper().replace(' ','')
        if failed:
            #Do it the old way.
            junk = open(sca, 'r').readlines()[2]
            #Save unit cell info
            self.cell2 = junk.split()[:6]
            self.cell = self.cell2[0]+' '+self.cell2[1]+' '+self.cell2[2]+' '+self.cell2[3]+' '+self.cell2[4]+' '+self.cell2[5]            
            #Save correct SG info and fix sca file
            #self.input_sg = fixSG(self,(junk[61:-1].upper().replace(' ','')))
            sg = junk[61:-1].upper().replace(' ','')
        self.input_sg = fixSG(self,sg)
    
    except:
        self.logger.exception('**ERROR in Utils.getInfoCellSG**')

def getLabelitCell(self):
    """
    Get unit cell from Labelit results
    """
    self.logger.debug('Utilities::getLabelitCell')
    try:
        bestpar = open('bestfile.par', 'r')
        for line in bestpar:
            if line.startswith('CELL'):
                split = line.split()
                cell = split[1] + ' ' + split[2] + ' ' + split[3] + ' ' + split[4] + ' ' + split[5] + ' ' + split[6]
                return cell
        bestpar.close()
        
    except:
        self.logger.exception('**Error in Utils.getLabelitCell**')
        return (None)

def getPDBInfo(self,pdb):
    """
    Figure out what is in pdb.
    """
    self.logger.debug('Utilities::getPDBInfo')
    try:    
        command = 'phenix.pdb_interpretation '+pdb+' build_geometry_restraints_manager=False build_xray_structure=False'
        output = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        segid = {}
        index = []
        sid = []
        cl = []
        res = []
        temp = []
        for line in output.stdout:
            temp.append(line)
            if line.startswith('    Chain:'):
                sid.append(line.split()[1][1:-1])
            if line.startswith('          Classifications:'):
                cl.append(line.split()[1][2:-2])
            if line.startswith('        Number of residues'):
                res.append(line.split()[4][:-1])
        for x in range(len(cl)):
            if cl[x] != 'undetermined':
                junk = {'class': cl[x],
                        'nres' : res[x]}
                segid[sid[x]] = junk
        return (segid)
    
    except:
        self.logger.exception('**Error in Utils.getPDBInfo**')

def getPDBmw(self,pdb):
    """
    Figure out total MW in pdb.
    """
    self.logger.debug('Utilities::getPDBmw')
    try:    
        temp = []
        segid = []
        na = 0
        na1 = 0
        naw = 0
        na1w = 0
        aa = 0
        aaw = 0
        t = -1
        t2 = -1
        volume = calcVolume(self)
        checkVolume(self,volume)
        command = 'phenix.pdb.hierarchy '+pdb
        output = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        for i,line in enumerate(output.stdout):
            #print line
            temp.append(line)
            if line.startswith('    "common_rna_dna'):
                na = int(line.split()[1])
                naw = na*330
            #For more RNA?
            if line.startswith('    "other'):
                na1 = int(line.split()[1])
                na1w = na1*330
            if line.startswith('    "common_amino'):
                aa = int(line.split()[1])
                aaw = aa*110
            if line.startswith('  histogram of chain id frequency:'):
                t = i
            if line.startswith('  number of alt. '):
                t2 = i
        totna = na+na1
        totnaw = naw+na1w
        tot = totna+aa
        totw = naw+na1w+aaw
        #if self.solvent_content == 0.55:
        if totna > 0:
            if aa > 0:
                self.solvent_content = 0.6
                """
                if totna > aa:
                    self.sample_type = 'RNA'
                """
            else:
                self.solvent_content = 0.64
                self.sample_type = 'RNA'#or DNA?
        nmol = int(round(volume*(1-self.solvent_content))/(1.23*(totw)*int(symopsSG(self,self.input_sg))))
        if nmol == 0:
            nmol = 1
        for line in temp[t:t2]:
            if len(line.split()) == 2:
                segid.append(line.split()[0][1:-1])
        dict = {'MW'  :totw,
                'MWaa':aaw,
                'MWna':totnaw,
                'NMol':nmol,
                'NRes':tot,
                'SegID':segid}
        return (dict)
    
    except:
        self.logger.exception('**ERROR in Utils.getPDBmw**')
        return ('FAILED')    
    
def getResNumber(self,input):
    """
    Get number of residues from input pdb file.
    """
    self.logger.debug('Utilities::getResNumber')
    try:        
        command = 'moleman <<eof\n'
        command += 'read\n'
        #command += input+'\n'
        command += os.path.basename(input)+'\n'
        command += 'tally\n'
        command += 'quit\n'
        command += 'eof\n'        
        junk = open('moleman.com','w')
        junk.writelines(command)
        junk.close()
        command2 = 'tcsh moleman.com'        
        output = subprocess.Popen(command2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        #set defaults if lines not found
        prot_res = 200
        wat = 0        
        for line in output.stdout:
            if line.startswith(' Nr of waters found'):
                wat = int(line.split()[6][:-1])
            if line.startswith(' Total nr of residues'):
                tot_res = int(line.split()[6][:-1])
        prot_res = tot_res-wat
        return (prot_res)
    
    except:
        self.logger.exception('**ERROR in Utils.getResNumber**')
        return (200)
    
def killChildren(self, pid):
    """
    Kills the parent process, the children, and the children's children.
    """        
    parent = False
    child1 = False
    child2 = False
    c1 = []
    c2 = []
    self.logger.debug('Utilities::killChildren')    
    try:
        if self.test:
            os.chdir('/home/schuerjp/Data_processing/Frank/Output/')            
        ppid = 'ps -F -A | grep ' + str(pid)        
        output = subprocess.Popen(ppid, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)        
        for line in output.stdout:
            junk = line.split()
            if junk[1] == str(pid):
                parent = True
            if junk[2] == str(pid):
                child1 = True
                pid1 = junk[:][1]                
                c1.append(pid1)
                ppid2 = 'ps -F -A | grep ' + str(pid1)
                output2 = subprocess.Popen(ppid2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)        
                for line in output2.stdout:
                    junk2 = line.split()
                    if junk2[2] == str(pid1):
                        child2 = True
                        pid2 = junk2[:][1]
                        c2.append(pid2)                          
        if parent:  
            kill = 'kill -9 ' + str(pid)
            self.logger.debug(kill)
            os.system(kill)                
        if child1:
            for line in c1:
                kill1 = 'kill -9 ' + line
                self.logger.debug(kill1)                     
                os.system(kill1)                
        if child2:
            for line in c2:
                kill2 = 'kill -9 ' + line
                self.logger.debug(kill2)            
                os.system(kill2)
            
    except:
        self.logger.exception('**Could not kill the children?!?**')
    
def killChildrenCluster(self,input):
    """
    Kill jobs on cluster.
    """
    self.logger.debug('Utilities::killChildrenCluster')
    try:
        command = 'qdel '+str(input)
        self.logger.debug(command)
        os.system(command)
    
    except:
        self.logger.exception('**Could not kill the jobs on the cluster**')
    
def makeHAfiles(self):
    """
    make the input HA files for phenix.autosol.
    """
    self.logger.debug('Utilities::makeHAfiles')
    try:        
        counter = 0
        while counter <= 1:
            temp = []
            ha1 = []
            if counter == 0:
                ha = open('junk.hat','r')
                new_ha = open('junk.ha','w')
            else:
                ha = open('junk_i.hat','r')
                new_ha = open('junk_i.ha','w')            
            for line in ha:
                temp.append(line)
                if line.startswith('UNIT'):
                    index1 = temp.index(line)
            for line in temp[index1:]:
                if len(line.split()) == 7:
                    if line.split()[5].startswith('-') == False:
                        junk = line.split()[2]+' '+line.split()[3]+' '+line.split()[4]
                        ha1.append(junk)
            for line in ha1:
                new_ha.write(line+'\n')
            if counter == 0:
                self.ha_num1 = str(len(ha1))
            else:
                self.ha_num2 = str(len(ha1))
            ha.close()
            new_ha.close()
            counter += 1

    except:
        self.logger.exception('**ERROR in Utils.makeHAfiles**')

def makePeaksFromDistl(self,type='MAX'):
    """
    Function will make a denzo-formatted peaks file for each image in the DISTL_pickle
    WARNING: this must be run using labelit.python as the modules called by the pickled
    file are specific to DISTL, and I have not bothered to mod the pythonpath to look 
    for labelit modules as this would be very platform-specific. If I take the time to 
    figure this out in the future, this may change. 
    
    type can be either MAX = position of peak maximum
                       COM = position of peak center of mass
    """        
    self.logger.debug('Utilities::makePeaksFromDistl')
    if self.test:
        os.chdir('/gpfs6/users/necat/Jon/RAPD_test/Output/labelit_iteration4')
    
    try:
        #if self.beamline_use:
        command = 'labelit.python /home/schuerjp/Data_processing/eclipse/branch_jon/makepeaks_jon.py'
        self.logger.debug(command)
        os.system(command)
    
    except:
        self.logger.exception('**Error in Utils.makePeaksFromDistl**')

def mtz2sca(self):
    """
    Convert mtz file to SCA for Shelx.
    """
    try:
        command  = 'mtz2various hklin '+self.datafile+' hklout temp.sca<<eof\n'
        command += 'OUTPUT SCALEPACK\n' 
        command += 'labin  I(+)=I(+) SIGI(+)=SIGI(+) I(-)=I(-) SIGI(-)=SIGI(-)\n' 
        command += 'end\n'
        command += 'eof\n'
        file = open('mtz2sca.com','w')
        file.writelines(command)
        file.close()
        command2 = 'tcsh mtz2sca.com'
        temp = []
        myoutput = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        for line in myoutput.stdout:
            temp.append(line)        
        self.datafile = os.path.join(os.getcwd(),'temp.sca')
    
    except:
        self.logger.exception('**ERROR in Utils.mtz2sca**')

def pp(self,input):
    """
    Print out the list of dict pretty.
    """
    try:
        junk = pprint.PrettyPrinter(indent=4)
        junk.pprint(input)
    
    except:
        self.logger.exception('**Error in Utils.pp**')
    
def processCluster(self,input,file=False):
    """
    Run AutoMR on a separate node on the cluster.
    """
    self.logger.debug('Utilities::processCluster')
    try:
        if file:
            command = 'qsub -j y -terse -cwd '+input
        else:
            command = 'qsub -b y -j y -terse -cwd '+input
        myoutput = pexpect.spawn(command)
        job = myoutput.readline().strip()
        return(job)
    
    except:
        self.logger.exception('**ERROR in Utils.processCluster.**')        

def sca2mtz(self,res=False,run_before=False):
    """
    Convert sca file to mtz for Phaser.
    """
    self.logger.debug('Utilities::sca2mtz')
    try:   
        failed = False
        os.chdir(self.working_dir)
        path = os.path.join(self.working_dir,'temp.mtz')
        command  = 'scalepack2mtz hklin '+self.datafile+' hklout junk.mtz<<eof1\n'
        if res:
            command += 'resolution 30 '+res+'\n'
        command += 'end\n'
        command += 'eof1\n'
        command += 'truncate hklin junk.mtz hklout temp.mtz<<eof2\n'
        command += 'truncate yes\n'
        command += 'end\n'
        command += 'eof2\n'
        file = open('scale2mtz.com','w')
        file.writelines(command)
        file.close()
        command2 = 'tcsh scale2mtz.com'
        temp = []
        myoutput = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in myoutput.stdout:
            temp.append(line)        
            if line.startswith(' TRUNCATE:  LSQ: sigma is zero'):            
                failed = True
                for line in temp:
                    if line.startswith(' finishing resolution'):            
                        hi_res = line.split()[3]
                
        if failed:
            if run_before:
                self.failed = True
            else:
                run_before = True
                sca2mtz(self,hi_res,run_before)        
        else:
            rm = 'rm -f junk.mtz'
            os.system(rm)
            self.datafile = path
    
    except:
        self.logger.exception('**ERROR in Utils.sca2mtz**')

def stillRunningCluster(self,jobid):
    """
    Check to see if process and/or its children and/or children's children are still running.
    """
    try:
        if self.cluster_use:
            qstat = 'qstat'
            running = False
            output = subprocess.Popen(qstat, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in output.stdout:
                split = line.split()
                if split[0] == str(jobid):
                    running = True        
            return (running)
        else:
            return (False)
    
    except:
        self.logger.exception('**ERROR in Utils.stillRunningCluster**')
    
def stillRunning(self, pid):
    """
    Check to see if process and/or its children and/or children's children are still running.
    """
    parent = False
    child1 = False
    child2 = False
    c1 = []
    c2 = []
    #self.logger.debug('Utilities::stillRunning')    
    try:
        ppid = 'ps -F -A | grep ' + str(pid)        
        output = subprocess.Popen(ppid, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)        
        for line in output.stdout:
            junk = line.split()
            if junk[1] == str(pid):
                parent = True
            if junk[2] == str(pid):
                child1 = True
                pid1 = junk[:][1]                
                c1.append(pid1)
                ppid2 = 'ps -F -A | grep ' + str(pid1)
                output2 = subprocess.Popen(ppid2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)        
                for line in output2.stdout:
                    junk2 = line.split()
                    if junk2[2] == str(pid1):
                        child2 = True
                        pid2 = junk2[:][1]
                        c2.append(pid2)
        
        if parent or child1 or child2:
            return(True)
        else:
            return(False)                            
    
    except:
        self.logger.exception('**Error in Utils.stillRunning**')
        
def subGroups(self,input1,input2='shelx'):
    """
    Determine which SG's to run.
    """
    self.logger.debug('Utilities::subGroups')
    try:
        sg2 = False
        subgroups = {  '1'  : [None],
                       '5'  : [None],
                       '5.1': [None],
                       '5.2': [None],
                       '5.3': [None],
                       '5.4': [None],
                       '5.5': [None],
                       '3'  : ['4'],
                       '16' : ['17','17.1','17.2','18','18.1','18.2','19'],
                       '20' : ['21'],
                       '22' : [None],
                       '23' : ['24'],
                       '75' : ['76','77','78'],
                       '79' : ['80'],
                       '89' : ['90','91','95','94','93','92','96'],
                       '97' : ['98'],
                       '143': ['144','145'],
                       '149': ['151','153'],
                       '150': ['152','154'],
                       '146.1': [None],
                       '146.2': [None],
                       '155.1': [None],
                       '155.2': [None],
                       '168': ['169','170','171','172','173'],
                       '177': ['178','179','180','181','182'],
                       '196': [None],
                       '195': ['198'],
                       '197': ['199'],
                       '207': ['208','212','213'],
                       '209': ['210'],
                       '211': ['214']  }
        
        subgroups2 = { '3'  : ['3','4'],
                       '16' : ['16','17','17.1','17.2','18','18.1','18.2','19'],
                       '20' : ['20','21'],
                       '23' : ['23','24'],                       
                       '75' : ['75','76','77'],
                       '79' : ['79','80'],
                       '89' : ['89','90','91','94','93','92'],
                       '97' : ['97','98'],
                       '143': ['143','144'],
                       '149': ['149','151'],
                       '150': ['150','152'],
                       '168': ['168','169','171','173'],
                       '177': ['177','178','180','182'],
                       '195': ['195','198'],
                       '197': ['197','199'],
                       '207': ['207','208','212'],
                       '209': ['209','210'],
                       '211': ['211','214'] }
        
        subgroups3 = { '3'  : ['3','4'],
                       '16' : ['16','17','17.1','17.2','18','18.1','18.2','19'],
                       '20' : ['20','21'],
                       '23' : ['23','24'],
                       '75' : ['75','76','77','78'],
                       '79' : ['79','80'],
                       '89' : ['89','90','91','94','93','92','95','96'],
                       '97' : ['97','98'],
                       '143': ['143','144','145'],
                       '149': ['149','151','153'],
                       '150': ['150','152','154'],
                       '168': ['168','169','171','173','170','172'],
                       '177': ['177','178','180','182','179','181'],
                       '195': ['195','198'],
                       '197': ['197','199'],
                       '207': ['207','208','212','213'],
                       '209': ['209','210'],
                       '211': ['211','214'] }
                       
        if subgroups.has_key(input1):
            sg = input1
        else:            
            junk = subgroups.items()
            for line in junk:                
                if line[1].count(input1):
                    sg = line[0]        
        if input2 == 'shelx':
            if subgroups2.has_key(sg):
                sg2 = subgroups2[sg]
        else:
            if subgroups3.has_key(sg):
                sg2 = subgroups3[sg]
        if sg2:    
            return(sg2)
        else:
            return([sg])
            
    except:
        self.logger.exception('**ERROR in Utils.subGroups**')
    
def symopsSG(self,input):
    """
    Convert SG to SG#.
    """                
    self.logger.debug('Utilities::symopsSG')
    try:
        symops =     {'P1'       : '1'  ,
                      'C2'       : '4'  ,
                      'C121'     : '4'  ,
                      'I121'     : '4'  ,
                      'A121'     : '4'  ,
                      'A112'     : '4'  ,
                      'B112'     : '4'  ,
                      'I112'     : '4'  ,
                      'P2'       : '2'  ,
                      'P121'     : '2'  ,
                      'P21'      : '2'  ,
                      'P1211'    : '2'  ,
                      'F222'     : '16' ,
                      'I222'     : '8' ,
                      'I212121'  : '8' ,
                      'C222'     : '8' ,
                      'C2221'    : '8' ,
                      'P222'     : '4' ,
                      'P2221'    : '4' ,
                      'P2212'    : '4' ,
                      'P2122'    : '4' ,
                      'P21212'   : '4' ,
                      'P21221'   : '4' ,
                      'P22121'   : '4' ,
                      'P212121'  : '4' ,
                      'I4'       : '8' ,
                      'I41'      : '8' ,
                      'I422'     : '16' ,
                      'I4122'    : '16' ,
                      'P4'       : '4' ,
                      'P41'      : '4' ,
                      'P42'      : '4' ,
                      'P43'      : '4' ,
                      'P422'     : '8' ,
                      'P4212'    : '8' ,
                      'P4122'    : '8' ,
                      'P4322'    : '8' ,
                      'P4222'    : '8' ,
                      'P42212'   : '8' ,
                      'P41212'   : '8' ,
                      'P43212'   : '8' ,
                      'P3'       : '3',
                      'P31'      : '3',
                      'P32'      : '3',
                      'P312'     : '6',
                      'P3112'    : '6',
                      'P3212'    : '6',
                      'P321'     : '6',
                      'P3121'    : '6',
                      'P3221'    : '6',
                      'P6'       : '6',
                      'P61'      : '6',
                      'P65'      : '6',
                      'P62'      : '6',
                      'P64'      : '6',
                      'P63'      : '6',
                      'P622'     : '12',
                      'P6122'    : '12',
                      'P6522'    : '12',
                      'P6222'    : '12',
                      'P6422'    : '12',
                      'P6322'    : '12',
                      'R3'       : '3',
                      'H3'       : '9', 
                      'R32'      : '6',
                      'H32'      : '18',
                      'F23'      : '48',
                      'F432'     : '96',
                      'F4132'    : '96',
                      'I23'      : '24',
                      'I213'     : '24',
                      'I432'     : '48',
                      'I4132'    : '48',
                      'P23'      : '12',
                      'P213'     : '12',
                      'P432'     : '24',
                      'P4232'    : '24',
                      'P4332'    : '24',
                      'P4132'    : '24'    }            
        
        sg = symops[input]
        return(sg)
    
    except:
        self.logger.exception('**ERROR in Utils.symopsSG**')
         
if __name__ == '__main__':
    #start logging
    LOG_FILENAME = '/tmp/rapd_agent_utilities.log'
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

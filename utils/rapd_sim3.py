__author__ = "Frank Murphy"
__copyright__ = "Copyright 2009,2010,2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2009/10/27"

"""
rapd_sim2 is intended to help a person 'spoof' data collections for 
images by modifying a local xf_status - command line only
"""

import getopt
import sys
import os
import time
import threading
import random
import glob
from rapd_adsc import ReadHeader
from rapd_site import secret_settings_general


def get_command_line():
    """
    Handle the command line and pass back variables to main
    """
    print """
    RAPD_SIM2 
    =========
    
    Synopsis: Rapid Automated Processing of Data - Simulate collection 2
    ++++++++      
    
    Proper use: >[python2.6] rapd_sim.py C/E/T images
    ++++++++++
                
    +++++
    
          """

    verbose = False
    
    try:
        opts,args = getopt.getopt(sys.argv[1:],"v")
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        sys.exit(2)
    for o, a in opts:
        if o == '-v':
            #print 'VERBOSE'
            verbose = True
    
    if len(args) < 2:
        print 'Proper use: >[python2.6] rapd_sim.py C/E/T images'
        exit(3)
    
    return(args[0],verbose,args[1:])

class RunMaker:
    def __init__(self,beamline,images):
        
        self.images = images
        self.images.sort()
        self.beamline = beamline
        
        self.SiteDef()
        self.MakeRuns()
            
    def SiteDef(self):
        if self.beamline == 'C':
            self.marcollect = '/usr/local/ccd_dist_md2b_rpc/tmp/marcollect'
            self.xf_status = '/usr/local/ccd_dist_md2b_rpc/tmp/xf_status'
        else:
            self.marcollect = '/tmp/marcollect'
            self.xf_status = '/tmp/xf_status'
            
    def MakeRuns(self):
        
        #print out selected images
        print 'You selected '+str(len(self.images))+' files:'
        for path in self.images:
            print '           '+path
        
        #now prep and write the marcollect
        print 'Now updating /tmp/marcollect'
        outfile = open(self.marcollect,'w')
        
        header = ReadHeader(self.images[0])
        #print header
        
        #directory = os.path.dirname(self.images[0])
        directory = secret_settings_general['faux_coll_dir']
        outfile.write('Directory: '+directory+'\n')
        
        image_prefix = '_'.join(os.path.basename(self.images[0]).split('_')[:-2])
        outfile.write('Image_Prefix: '+image_prefix+'\n')
        
        outfile.write('Mode: Time \n')
        outfile.write('ADC: Slow \n')
        outfile.write('Anomalous: No \n')
        outfile.write('Anom_Wedge: 5 \n')
        outfile.write('Compression: None \n')
        
        binning = header['bin']
        outfile.write( 'Binning: '+binning+' \n')
        
        outfile.write( 'Comment: Spoofing \n')
        
        x_beam = header['beam_center_x']
        y_beam = header['beam_center_y']
        outfile.write( 'Beam_Center: '+str(x_beam)+'  '+str(y_beam)+' \n')
        outfile.write( '\n')
        outfile.write( 'MAD: No \n')
        outfile.write( 'Energy to Use: \n')
        outfile.write( '        12295.90000 eV ( 1.008338 A ) \n')
        outfile.write( '        12284.70000 eV ( 1.009257 A ) \n')
        outfile.write( '        12860.00000 eV ( 0.964108 A ) \n')
        outfile.write( '        12560.00000 eV ( 0.987136 A ) \n')
        outfile.write( '        12764.50000 eV ( 0.971321 A ) \n')
        outfile.write( 'Change Energy Never \n')
        outfile.write( '\n')
        outfile.write( 'Run(s): \n')
        outfile.write( '\n')
        
        run      = int(os.path.basename(self.images[0]).split('_')[-2])
        start    = os.path.basename(self.images[0]).split('_')[-1].split('.')[0]
        total    = len(self.images)
        distance = float(header['distance'])
        theta    = float(header['twotheta'])
        phi      = float(header['osc_start'])
        kappa    = 0.0
        omega    = 0.0
        width    = float(header['osc_range'])
        itime    = float(header['time'])
        
        outfile.write(' %2d    %3s     %3d   %6.2f     %5.2f   %5.2f   %5.2f   %5.2f   phi  %5.3f      %3.1f    N \n'%(run,start,total,distance,theta,phi,kappa,omega,width,itime))
        outfile.write('\n')
        outfile.close()
        
        #remove all files from the dummy directory
        print 'Removing all files from %s' % directory
        for file in glob.glob(os.path.join(directory,'*.img')):
            os.remove(file)

        print 'Now updating %s' % self.xf_status
        
        #get the adsc_number to start with
        if not os.path.exists(self.xf_status):
            #use random number generator for first adsc image number to make it less likely the image is in the database
            #the first 100 are avoided since there is saturation for some image names in the low end of the range
            counter = random.randint(100,2000)
            #counter = 0
        else:
            lines = open(self.xf_status,'r').readlines()
            for i in range(len(lines)):
                sline = lines[i].split()
                if len(sline) == 2:
                    if sline[1].strip() == '<none>':
                        #use random number generator for first adsc image number to make it less likely the image is in the database
                        #the first 100 are avoided since there is saturation for some image names in the low end of the range
                        counter = random.randint(100,2000)
                        #counter = 0
                        break
                    else:
                        try:
                            counter = int(sline[0])
                        except:
                            #use random number generator for first adsc image number to make it less likely the image is in the database
                            #the first 100 are avoided since there is saturation for some image names in the low end of the range
                            counter = random.randint(100,2000)
                            #counter = 0
                        break
            
        for path in (self.images):
            #create the new image name
            new_image = os.path.join(directory,os.path.basename(path))
            print path,new_image
            #make a link
            os.symlink(path,new_image)
            print '%s >>> %s' % (path,new_image)
            #now write the file
            counter += 1
            outfile = open(self.xf_status,'w')
            outfile.write(str(counter)+' '+os.path.abspath(new_image))
            outfile.close()
                
            #only sleep if we have mutiple images to simulate
            if len(self.images) > 1:
                time.sleep(5)

        print 'Finished with data simulation'

if __name__ == '__main__':
    beamline,verbose,files = get_command_line()
    print files
    a = RunMaker(beamline=beamline,images=files)
    
    
    
    

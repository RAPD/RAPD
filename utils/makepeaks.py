__author__ = "Frank Murphy"
__copyright__ = "Copyright 2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2007/01/01"

import sys
import pickle
import fpformat

def MakePeaksFromDistl(type='MAX'):
    """
    Function will make a denzo-formatted peaks file for each image in the DISTL_pickle
    WARNING: this must be run using labelit.python as the modules called by the pickled
    file are specific to DISTL, and I have not bothered to mod the pythonpath to look 
    for labelit modules as this would be very platform-specific. If I take the time to 
    figure this out in the future, this may change. 
    
    type can be either MAX = position of peak maximum
                       COM = position of peak center of mass
    """
    #read peaks from the DISTL_pickle
    openFile = open('DISTL_pickle', 'rb')
    loadedFile = pickle.load(openFile)
    for image in loadedFile.images.keys():
        distlPeaks = loadedFile.images[image]['inlier_spots']
        #now write the peaks#.file
        filename = 'peaks' + str(image) + '.file'
        outFile = open(filename, 'w')
        outFile.write('      7777    0.0    0.0          1          1   \n')
        for peak in distlPeaks:
            if type == 'MAX':
                x = peak.max_pxl_x()
                y = peak.max_pxl_y()
            elif type == 'COM':
                x = peak.ctr_mass_x()
                y = peak.ctr_mass_y()
            outFile.write('        15 %#6s %#6s          %3d        %3d\n' %(fpformat.fix(x, 1), fpformat.fix(y, 1), image, image))
        outFile.close()
        #record other items from the DISTL_pickle to a readable file distl_stats#.txt
        outFile = open('distl_stats' + str(image) + '.txt', 'w')
        outFile.write('#Written by Alloy\n')
        outFile.write('#Stats culled from DISTL_pickle\n')
        outFile.write('relpath='+loadedFile.images[image]['relpath']+'\n')
        outFile.write('distl_resolution='+str(loadedFile.images[image]['distl_resolution'])+'\n')
        outFile.write('resolution='+str(loadedFile.images[image]['resolution'])+'\n')
        outFile.write('maxcel='+str(loadedFile.images[image]['maxcel'])+'\n')             
        outFile.close()

if __name__ == '__main__':
    MakePeaksFromDistl()

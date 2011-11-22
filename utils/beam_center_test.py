__author__ = "Jon Schuermann"
__copyright__ = "Copyright 2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2011/10/28"

import warnings
#Remove stupid warnings about sha and md5.
with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category=DeprecationWarning)
    from rapd_site import settings_C as C
    from rapd_site import settings_E as E
import array
import numpy
import optparse

"""
Calculates the beam center based on the 6th order polynomial fit
to the A-frame rails for both the 24ID-C and 24ID-E beamlines.
"""
#If user inputs distance after command, grab it, otherwise ask for distance
input = optparse.OptionParser().parse_args()
lift = 0
if len(input[1]) == 0:
    distance = float(raw_input('crystal-to-detector distance: '))
    l = raw_input('detector lift (mm)? [0]: ')
    if l:
        lift = float(l)
elif len(input[1]) == 1:
    distance = float(optparse.OptionParser().parse_args()[1][0])
else:
    distance = float(optparse.OptionParser().parse_args()[1][0])
    lift = float(optparse.OptionParser().parse_args()[1][1])
#Print beam center for both beamlines
for i1 in range(0,2):
    if i1 == 0:
        bl = 'C'
    else:
        bl = 'E'
    print '****************************************'
    print '24ID-'+bl
    print 'beam_center_date: '+eval(bl+'.get("beam_center_date")')
    print '****************************************'
    print 'distance = '+str(distance)
    if lift!= 0:
        print 'detector lift = '+str(lift)
    #Print both y and y beam
    temp = []
    for i2 in range(0,2):
        if i2 == 0:
            beam = 'x'
        else:
            beam = 'y'
        #print beam+'-beam'
        #Grab 6th order polynomial equation that fits our rails and solve it.
        a = array.array('f')
        for i in range(6,0,-1):
            a.append(eval(bl+'.get("beam_center_'+beam+'_m'+str(i)+'")'))
        a.append(eval(bl+'.get("beam_center_'+beam+'_b")'))
        p = numpy.poly1d(a)
        x = round(numpy.polyval(p,distance),3)
        if i2 == 0:
            if lift != 0:
                x = x+lift
        temp.append(x)
    print '\nFor processing in HKL2000, add the following line under the "Macros" tab "before indexing":'
    print 'x beam '+str(temp[0])+' y beam '+str(temp[1])+'\n'
    #The X and Y are flipped in HKL compared to XDS
    print 'For processing in XDS, 2x2 binned images:'
    print 'ORGX '+str(round(temp[1]/0.10259,3))+' ORGY '+str(round(temp[0]/0.10259,3))+'\n'
    print 'For processing in XDS, unbinned images:'
    print 'ORGX '+str(round(temp[1]/0.05130,3))+' ORGY '+str(round(temp[0]/0.05130,3))+'\n'
    
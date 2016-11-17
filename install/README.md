# Requirements

## Linux
Modules that need to be installed before installing RAPD2 for CentOS:
yum install epel-release
yum install blas-devel lapack-devel atlas-sse3-devel atlas-devel openblas-devel libffi-devel ImageMagick-devel

## Crystallographic Software
Required software that should be installed prior to RAPD2 install:
BEST (http://www.embl-hamburg.de/BEST/)
CCP4 (http://www.ccp4.ac.uk/)
RADDOSE
MOSFLM (http://www.mrc-lmb.cam.ac.uk/harry/mosflm/)
XOalign.py (xdsme, https://code.google.com/p/xdsme/)
XDS (http://xds.mpimf-heidelberg.mpg.de/)

After installing BEST, you will have to go into the installation directory and inspect
'detector-inf.dat' to see if parameters for your detector are present. If not, you will
have to input the parameters for your detector and give it a unique name. Then use the
first column ('Name') and edit rapd_agent_strategy.py 'processBest' for the first line
in command to specify the name of the detector (ie. 'best -f pilatus6m').If this is not
correct, your strategies will not be very accurate.

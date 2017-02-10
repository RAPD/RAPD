# Requirements

## Linux






## Mac OS

## Crystallographic Software
Required software that should be installed prior to RAPD2 install:  
- BEST (http://www.embl-hamburg.de/BEST/)  
- CCP4 (http://www.ccp4.ac.uk/)  
- RADDOSE  
- MOSFLM (http://www.mrc-lmb.cam.ac.uk/harry/mosflm/)  
- XOalign.py (xdsme, https://code.google.com/p/xdsme/)  
- XDS (http://xds.mpimf-heidelberg.mpg.de/)  

After installing BEST, you will have to go into the installation directory and inspect
'detector-inf.dat' to see if parameters for your detector are present. If not, you will
have to input the parameters for your detector and give it a unique name. Then use the
first column ('Name') and edit rapd_agent_strategy.py 'processBest' for the first line
in command to specify the name of the detector (ie. 'best -f pilatus6m').If this is not
correct, your strategies will not be very accurate.


# Install Procedure

## Full Install
The full install is built on top of a Phenix distribution, and is necessary for the Control and Launcher processes, but potentially is more than necessary for the Gatherer processes.

##### Scientific Linux
These instructions are formulated for Scientific Linux 6.8, but apply for CentOS 6 as well.

Installing the Control process and dependencies  
1. Clone the RAPD repository where you like `git clone https://github.com/RAPD/RAPD.git`  
2. Navigate to the install directory and `./install`  
3. The install script will list any modules that need to be installed. The list is: `epel-release
blas-devel lapack-devel atlas-sse3-devel atlas-devel openblas-devel libffi-devel ImageMagick-devel`  
4. RAPD is built on top of the Phenix distribution, so you will need to obtain it. The install
script will instruct you on which file to get, and where to put it. Once you have the file where it should be, hit return in the install script window.  

## Minimal Install
The minimal install is useful for gatherer processes, not for data processing. It will fetch and install Python, add some modules to python, and then create scripts for RAPD to use.
1. Clone the RAPD repository where you like `git clone https://github.com/RAPD/RAPD.git`
2. Navigate to the install directory and `./install_min`
3.


### Scientific Linux
These instructions are formulated for Scientific Linux 6.8, but apply for CentOS 6 as well.




# Installing Databases
## Docker
Using Docker to install the required databases is a workable approach. To install Docker and the databases on a CentOS 6.8:  
1. Install the EPEL repository `sudo yum install epel-release`  
2. Install Docker `sudo yum install docker-io`  
3. Start the Docker daemon `sudo service docker start`  
4. Configure Docker to start on boot `sudo chkconfig docker on`  
5. Check if Docker is working `sudo docker run hello-world`  
6. Start Redis server `sudo docker run --name redisdb -p 6379:6379 -d redis:3.2`  
7. Start MongoDB server `sudo docker run --name mongodb -p 27017:27107 -d mongo:3.4`  




# Common Errors
### Mac OS X
#### Missing zlib
CCTBX will fail in building python if zlib is not installed for your system. The error looks like:  
`Traceback (most recent call last):
  File "modules/cctbx_project/libtbx/auto_build/install_base_packages.py", line 1457, in <module>
    installer(args=sys.argv, log=sys.stdout)
  File "modules/cctbx_project/libtbx/auto_build/install_base_packages.py", line 207, in __init__
    self.build_dependencies(packages=packages)
  File "modules/cctbx_project/libtbx/auto_build/install_base_packages.py", line 637, in build_dependencies
    getattr(self, 'build_%s'%i)()
  File "modules/cctbx_project/libtbx/auto_build/install_base_packages.py", line 729, in build_python
    self.set_python(op.abspath(python_exe))
  File "modules/cctbx_project/libtbx/auto_build/install_base_packages.py", line 402, in set_python
    self.check_python_dependencies()
  File "modules/cctbx_project/libtbx/auto_build/install_base_packages.py", line 394, in check_python_dependencies
    raise e
RuntimeError: Call to '/Users/frankmurphy/workspace/rapd_github/share/cctbx/base/bin/python -c 'import zlib'' failed with exit code 1
Process failed with return code 1`

CCTBX uses the Mac OS X system python to build, and if you want to check if zlib is indeed not importable, you may run python and try to import zlib:  
`/System/Library/Frameworks/Python.framework/Versions/2.7/bin/python`  
`>import zlib`  

To remedy this problem, you can update your system's tools by:  
`xcode-select --install`  

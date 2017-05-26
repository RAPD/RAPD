## Install Types
There are two install types available:
1. Full Install (`install`) -  built on top of a CCTBX distribution, and is necessary for commandline functionality, development and for the Control and Launcher processes at data collection facilities. The full install could potentially be more than necessary for the Gatherer processes.
2. Minimal Install(`install_min`) - useful for gatherer processes, not for data processing or commandline functionality. It will fetch and install Python, add some modules to python, and then create scripts for RAPD to use.

## Full Install
This is the install for running RAPD for processing, etc. It is a heavy install (sorry) to make sure all tools are present for people wishing to use all the features present in CCTBX.
#### Requirements
A number of packages are required for the full install to function properly. The install script searches and notifies if packages are Missing
- CentOS 6 and derivatives: `bzip2 gcc-c++ git make mesa-libGL-devel mesa-libGLU-devel openssl-devel patch subversion wget`

- CentOS 7 and derivatives: `bzip2 gcc-c++ git libffi-devel make mesa-libGL-devel mesa-libGLU-devel ncurses-devel openssl-devel patch python readline subversion wget`

- Ubuntu 16: `build-essential bzip2  git libgl1-mesa-dev libglu1-mesa-dev libncurses5-dev libssl-dev pkg-config python subversion wget zlib1g-dev`

#### Installing
1. Clone the RAPD repository where you like `git clone https://github.com/RAPD/RAPD.git rapd`  
2. Navigate to the install directory `cd rapd/install` and run the install `./install`  

## Minimal Install
This is an install for sites that are integrating RAPD into their systems and want a simple version on nodes for data watching, signaling, etc. Unable to process images, etc. with this install.
#### Requirements
#### Installing
1. Clone the RAPD repository where you like `git clone https://github.com/RAPD/RAPD.git`
2. Navigate to the install directory and `./install_min`

## Environmental Variables
RAPD uses environmental variables for setting some defaults:
* RAPD_AUTHOR_NAME - (development) if set, rapd.generate will put your name in generated files as author
* RAPD_AUTHOR_EMAIL - (development) if set, rapd.generate will put your email in generated files as author email
* RAPD_DIR_INCREMENT - if set to "up" or "UP" RAPD will increment directories up as it goes: `rapd_index_XXX_N, ... , rapd_index_XXX_1, rapd_index_XXX`  (newest to oldest) just like Phenix does. If it is set to anything else, RAPD will descend: `rapd_index_XXX, rapd_index_XXX_1, ... , rapd_index_XXX_N` (newest to oldest)
* RAPD_HOME - is set by RAPD when it sources the rapd.[c]shrc

# Databases
Running a full site installation requires both Redis and MongoDB. To understand why these are necessary and how to set them up, please see the documentation.
### Docker
Using Docker to install the required databases is a workable approach.
To install and run the databases using Docker:  
1. Check if Docker is working `sudo docker run hello-world`  
2. Start Redis server `sudo docker run --name redisdb -p 6379:6379 -d redis:3.2`  
3. Start MongoDB server `sudo docker run --name mongodb -p 27017:27107 -d mongo:3.4`  

# Crystallographic Software
Required software that should be installed prior to RAPD2 install:  
- BEST (http://www.embl-hamburg.de/BEST/)  
- CCP4 (http://www.ccp4.ac.uk/)  
- RADDOSE  
- MOSFLM (http://www.mrc-lmb.cam.ac.uk/harry/mosflm/)  
- XDSME (https://code.google.com/p/xdsme/)  
- XDS (http://xds.mpimf-heidelberg.mpg.de/)  

After installing BEST, you will have to go into the installation directory and inspect
'detector-inf.dat' to see if parameters for your detector are present. If not, you will
have to input the parameters for your detector and give it a unique name. Then use the
first column ('Name') and edit rapd_agent_strategy.py 'processBest' for the first line
in command to specify the name of the detector (ie. 'best -f pilatus6m').If this is not
correct, your strategies will not be very accurate.

# Known Errors

### CentOS 6
#### Problem building Cython
CCTBX can fail in building python at the cython step
`Installing cython...
  log file is /home/necat/rapd/share/cctbx/base_tmp/cython_install_log
  getting package cython-0.22.tar.gz...
    downloading from https://pypi.python.org/packages/source/C/Cython : 1.5 MB
    [0%.........20%.........40%.........60%.........80%.........100%]
  installing cython-0.22.tar.gz...
Traceback (most recent call last):
  File "modules/cctbx_project/libtbx/auto_build/install_base_packages.py", line 1457, in <module>
    installer(args=sys.argv, log=sys.stdout)
  File "modules/cctbx_project/libtbx/auto_build/install_base_packages.py", line 207, in __init__
    self.build_dependencies(packages=packages)
  File "modules/cctbx_project/libtbx/auto_build/install_base_packages.py", line 637, in build_dependencies
    getattr(self, 'build_%s'%i)()
  File "modules/cctbx_project/libtbx/auto_build/install_base_packages.py", line 981, in build_cython
    confirm_import_module="Cython")
  File "modules/cctbx_project/libtbx/auto_build/install_base_packages.py", line 543, in build_python_module_simple
    log=pkg_log)
  File "modules/cctbx_project/libtbx/auto_build/install_base_packages.py", line 302, in call
    return call(args, log=log, verbose=self.verbose, **kwargs)
  File "/home/necat/rapd/share/cctbx/modules/cctbx_project/libtbx/auto_build/installer_utils.py", line 81, in call
    raise RuntimeError("Call to '%s' failed with exit code %d" % (args, rc))
RuntimeError: Call to '/home/necat/rapd/share/cctbx/base/bin/python setup.py build ' failed with exit code 1`

This is due to interference from installed software with the installation. One solution is to change the startup sourcing (in my case I moved the .tcshrc to a temporary file and re-logged in) so that the interfering software is not initialized when you are installing.

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

#!/bin/tcsh -f

#
# WARNING - Images not yet working
#           Coming soon
#

set f = $1

#
# Check for necessary programs
#
set fail = 'False'

#wget
if ( ! -x `which wget` ) then
  echo 'No wget. Please install.'
  set fail = 'True'
endif

#gcc
if ( ! -x `which gcc` ) then
  echo 'No gcc. Please install.'
  echo 'Try yum install gcc'
  set fail = 'True'
endif

#g77
if ( ! -x `which g77` ) then
  echo 'No g77. Please install.'
  echo 'Try yum install compat-gcc*'
  set fail = 'True'
endif

#Check the flag
if ($fail == 'True') then
  exit
else
  echo 'All programs required for install present'
endif

#
# Look at the command line
#
if ($f == '') then
  echo 'Nothing selected for install'
  echo 'options are: all'
  echo '             python'
  echo '             ssh'
  echo '             database'
  echo '             images'
  echo '             php'
  echo '             numpy or scipy'
  echo ''
  exit
endif 

#
# Install Python-2.7   
#
if ($f == 'python' | $f == 'all') then
  if ( ! -e /usr/include/zlib.h ) then
    echo ''
    echo 'Installing zlib-devel'
    echo '====================='
    yum install zlib-devel -y
  endif

  echo ''
  echo 'Installing python2.7'
  echo '===================='
  wget http://www.python.org/ftp/python/2.7/Python-2.7.tgz
  tar -zxvf Python-2.7.tgz
  cd ./Python-2.7
  ./configure
  make
  make install
  cd ../
  rm -rf Python-2.7*
endif

#
# Get setuptools and paramiko
#
if ($f == 'ssh' | $f == 'all') then
  echo ''
  echo 'Installing setuptools'
  echo '====================='
  wget http://peak.telecommunity.com/dist/ez_setup.py
  /usr/local/bin/python2.7 ez_setup.py
  /usr/local/bin/python2.7 ez_setup.py -U setuptools
  rm -f ez_setup.py
  echo ''
  echo 'Installing paramiko'
  echo '==================='
  /usr/local/bin/easy_install-2.7 paramiko
endif 

#
# Install database interfaces
#
if ($f == 'database' | $f == 'all') then
  echo ''
  echo 'Installing mysql-devel'
  echo '======================'
  yum install mysql-devel -y
  echo ''
  echo 'Installing MySQLdb'
  echo '=================='
  /usr/local/bin/easy_install-2.7 mysql-python
endif

#
# Images
#
if ($f == 'images' | $f == 'all') then
  echo ''
  echo 'Installing vips'
  echo '======================'
  yum install glib2-devel libxml2-devel libjpeg-devel libtiff-devel -y
  wget http://www.vips.ecs.soton.ac.uk/supported/current/vips-7.26.7.tar.gz
  tar -xzvf vips-7.26.7.tar.gz
  cd vips-7.26.7
  ./configure
  make
  make install
  cd ../
  rm -rf vips-7.26.7 
  echo ''
endif

#
# PHP
#
if ($f == 'php' | $f == 'all') then
  echo ''
  echo 'Installing php json module'
  echo '=========================='
  yum install php-pear -y
  pecl install json
  echo  '; Enable json extension module' > /etc/php.d/json.ini 
  echo  'extension=json.so' >> /etc/php.d/json.ini
  /sbin/service httpd restart
endif

#
# numpy
#
if ($f == 'numpy'| $f == 'scipy' | $f == 'all') then
  echo ''
  echo 'Installing SciPy and Numpy'
  echo '=========================='
  if ( ! -e /usr/lib/libblas.a ) then
    echo 'Install blas'
    yum install blas-devel -y
  endif

  if ( ! -x `which gfortran` ) then
    echo 'Install gfortran'
    yum install gcc-gfortran -y
  endif
  
  if ( ! -x `which g++` ) then
    echo 'Install g++'
    yum install gcc-c++ -y
  endif

  if ( ! -e /usr/lib/liblapack.a ) then
    echo 'Install lapack'
    yum install lapack-devel -y
  endif

  echo 'Install numpy'
  wget http://sourceforge.net/projects/numpy/files/NumPy/1.6.1/numpy-1.6.1.tar.gz 
  tar -xzvf numpy-1.6.1.tar.gz
  cd numpy-1.6.1
  /usr/local/bin/python2.7 setup.py install
  cd ../
  rm -rf numpy-1.6.1
  rm -f numpy-1.6.1.tar.gz

  echo 'Install scipy'
  wget http://sourceforge.net/projects/scipy/files/scipy/0.10.0/scipy-0.10.0.tar.gz 
  tar -xzvf scipy-0.10.0.tar.gz
  cd scipy-0.10.0
  /usr/local/bin/python2.7 setup.py install
  cd ../
  rm -rf scipy-0.10.0
  rm -f scipy-0.10.0.tar.gz
endif



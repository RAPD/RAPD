#!/bin/tcsh -f

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
  set fail = 'True'
endif

#g77
#if ( ! -x `which g77` ) then
#  echo 'No g77. Please install.'
#  set fail = 'True'
#endif

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
  echo '             wxpython'
  echo '             ssh'
  echo '             database'
  echo '             images'
  echo '             php'
  echo ''
  exit
endif 

#
# Install Python-2.7   
#
if ($f == 'python' | $f == 'all') then
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
# Install wxPython 2.8.10.1
#
if ($f == 'wxpython') then
  echo ''
  echo 'Installing wxPython2.8.10.1'
  echo '==========================='
  wget http://downloads.sourceforge.net/wxpython/wxPython-src-2.8.10.1.tar.bz2
  bzip2 -d wxPython-src-2.8.10.1.tar.bz2
  tar -xvf wxPython-src-2.8.10.1.tar
  cd wxPython-src-2.8.10.1
  mkdir bld
  cd bld
  ../configure --prefix=/opt/wx/2.8.10 --with-gtk --with-gnomeprint --with-opengl --enable-optimize --enable-debug_flag --enable-debug_report --enable-geometry --enable-graphics_ctx --enable-sound --with-sdl --enable-mediactrl --enable-display --enable-unicode
  echo  'make $* \' > .make 
  echo  '  && make -C contrib/src/gizmos $* \' >> .make
  echo  '  && make -C contrib/src/stc $*'      >> .make
  echo  ''                                     >> .make
  chmod +x .make
  ./.make
  ./.make install
  set path = ( $path /opt/wx/2.8.10/bin )
  if ( ! $?LD_LIBRARY_PATH ) then
      setenv LD_LIBRARY_PATH  "/opt/wx/2.8.10/lib"
  else
      setenv LD_LIBRARY_PATH  "/opt/wx/2.8.10/lib":"$LD_LIBRARY_PATH"
  endif
  cd ../wxPython
  /usr/local/bin/python2.6 setup.py build_ext WX_CONFIG=/opt/wx/2.8.10/bin/wx-config --inplace --debug          
  /usr/local/bin/python2.6 setup.py install WX_CONFIG=/opt/wx/2.8.10/bin/wx-config
  cd ../../
  rm -rf wxPython-src-2.8.10.*

#
# Get the wxPython Demo
#
  echo ''
  echo 'Installing the wxPython demo'
  echo '============================'
  wget http://downloads.sourceforge.net/wxpython/wxPython-demo-2.8.10.1.tar.bz2
  bzip2 -d wxPython-demo-2.8.10.1.tar.bz2
  tar -xvf wxPython-demo-2.8.10.1.tar
  rm -rf wxPython-demo-2.8.10.1.tar*
  cd wxPython-2.8.10.1/demo
  echo 'Demo should be displayed if wxPython installation successful.'
  echo 'Exit the demo to continue'
  /usr/local/bin/python2.6 demo.py

  echo 'Please add the following lines to your .cshrc'
  echo '#############################################'
  echo '# wxPython '
  echo 'set path = ( $path /opt/wx/2.8.10/bin )'
  echo 'if ( ! $?LD_LIBRARY_PATH ) then'
  echo '    setenv LD_LIBRARY_PATH  "/opt/wx/2.8.10/lib"'
  echo 'else'
  echo '    setenv LD_LIBRARY_PATH  "/opt/wx/2.8.10/lib":"$LD_LIBRARY_PATH"'
  echo 'endif'
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
  yum install mysql-devel
  echo ''
  echo 'Installing MySQLdb'
  echo '=================='
  wget http://downloads.sourceforge.net/mysql-python/MySQL-python-1.2.3.tar.gz
  gunzip MySQL-python-1.2.3c1.tar.gz
  tar -xvf MySQL-python-1.2.3c1.tar
  cd MySQL-python-1.2.3c1
  /usr/local/bin/python2.7 setup.py build
  /usr/local/bin/python2.7 setup.py install
  cd ../
  rm -rf MySQL-python-1.2.3c1
endif

#
# Images
#
if ($f == 'images' | $f == 'all') then
  echo ''
  echo 'Installing vips'
  echo '======================'
  yum install vips
  echo ''
endif

#
# PHP
#
if ($f == 'php' | $f == 'all') then
  echo ''
  echo 'Installing php json module'
  echo '=========================='
  yum install php-pear
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
  echo 'Install blas'
  wget http://www.netlib.org/blas/blas.tgz
  tar xzf blas.tgz
  cd BLAS
  g77 -fno-second-underscore -O2 -c *.f
  ar r libfblas.a *.o
  ranlib libfblas.a
  rm -rf *.o
  cp libfblas.a /var/lib/libfblas.a
  setenv BLAS /var/lib/libfblas.a
  cd ../
  rm -rf BLAS
  rm -f blas.tgz

  echo 'Install lapack'
wget http://www.netlib.org/lapack/lapack.tgz
tar xzf lapack.tgz
cd lapack-3.2.2
cp INSTALL/make.inc.gfortran make.inc
make lapacklib
make clean
cp lapack_LINUX.a /var/lib/libflapack.a
ln -s /var/lib/libflapack.a /var/lib/liblapack.a
setenv LAPACK /var/lib/libflapack.a
cd ../
rm -rf  lapack-3.2.2
rm -f lapack.tgz

echo 'Install numpy'
wget http://downloads.sourceforge.net/project/numpy/NumPy/1.5.0/numpy-1.5.0.tar.gz
gunzip numpy-1.5.0.tar.gz
tar -xvf numpy-1.5.0.tar
cd numpy-1.5.0
/usr/local/bin/python2.6 setup.py install

cd ../
rm -rf numpy-1.5.0
rm -f numpy-1.5.0.tar


echo 'Install scipy'
wget http://downloads.sourceforge.net/project/scipy/scipy/0.8.0/scipy-0.8.0.tar.gz
gunzip scipy-0.8.0.tar.gz
tar -xvf scipy-0.8.0.tar
cd scipy-0.8.0
/usr/local/bin/python2.6 setup.py install
cd ../
rm -rf scipy-0.8.0
rm -f scipy-0.8.0.tar

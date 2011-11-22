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
  echo ''
  exit
endif 

#
# Install Python-2.6.5
#
if ($f == 'python' | $f == 'all') then
  echo ''
  echo 'Installing python2.6.5'
  echo '======================'
  wget http://www.python.org/ftp/python/2.6.5/Python-2.6.5.tgz
  tar -zxvf Python-2.6.5.tgz
  cd ./Python-2.6.5
  ./configure
  make
  make install
  cd ../
  rm -rf Python-2.6.5*
endif

#
# Install wxPython 2.8.11.0
#
if ($f == 'wxpython') then
  echo ''
  echo 'Installing wxPython2.8.11.0'
  echo '==========================='
  wget http://downloads.sourceforge.net/wxpython/wxPython-src-2.8.11.0.tar.bz2
  bzip2 -d wxPython-src-2.8.11.0.tar.bz2
  tar -xvf wxPython-src-2.8.11.0.tar
  cd wxPython-src-2.8.11.0
  mkdir bld
  cd bld
  ../configure --prefix=/opt/wx/2.8.11 --with-gtk --with-gnomeprint --with-opengl --enable-optimize --enable-debug_flag --enable-debug_report --enable-geometry --enable-graphics_ctx --enable-sound --with-sdl --enable-mediactrl --enable-display --enable-unicode
  echo  'make $* \' > .make 
  echo  '  && make -C contrib/src/gizmos $* \' >> .make
  echo  '  && make -C contrib/src/stc $*'      >> .make
  echo  ''                                     >> .make
  chmod +x .make
  ./.make
  ./.make install
  set path = ( $path /opt/wx/2.8.11/bin )
  if ( ! $?LD_LIBRARY_PATH ) then
      setenv LD_LIBRARY_PATH  "/opt/wx/2.8.11/lib"
  else
      setenv LD_LIBRARY_PATH  "/opt/wx/2.8.11/lib":"$LD_LIBRARY_PATH"
  endif
  cd ../wxPython
  /usr/local/bin/python2.6 setup.py build_ext WX_CONFIG=/opt/wx/2.8.11/bin/wx-config --inplace --debug          
  /usr/local/bin/python2.6 setup.py install WX_CONFIG=/opt/wx/2.8.11/bin/wx-config
  cd ../../
  rm -rf wxPython-src-2.8.11.*

#
# Get the wxPython Demo
#
  echo ''
  echo 'Installing the wxPython demo'
  echo '============================'
  wget http://downloads.sourceforge.net/wxpython/wxPython-demo-2.8.11.1.tar.bz2
  bzip2 -d wxPython-demo-2.8.11.1.tar.bz2
  tar -xvf wxPython-demo-2.8.11.1.tar
  rm -rf wxPython-demo-2.8.11.1.tar*
  cd wxPython-2.8.11.1/demo
  echo 'Demo should be displayed if wxPython installation successful.'
  echo 'Exit the demo to continue'
  /usr/local/bin/python2.6 demo.py
endif

#
# Get setuptools and paramiko
#
if ($f == 'ssh' | $f == 'all') then
  echo ''
  echo 'Installing setuptools'
  echo '====================='
  wget http://peak.telecommunity.com/dist/ez_setup.py
  /usr/local/bin/python2.6 ez_setup.py
  /usr/local/bin/python2.6 ez_setup.py -U setuptools
  rm -f ez_setup.py
  echo ''
  echo 'Installing paramiko'
  echo '==================='
  /usr/local/bin/easy_install-2.6 paramiko
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
  wget http://downloads.sourceforge.net/mysql-python/MySQL-python-1.2.3c1.tar.gz
  gunzip MySQL-python-1.2.3c1.tar.gz
  tar -xvf MySQL-python-1.2.3c1.tar
  cd MySQL-python-1.2.3c1
  /usr/local/bin/python2.6 setup.py build
  /usr/local/bin/python2.6 setup.py install
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

if ($f == 'wxpython') then
echo 'Please add the following lines to your .cshrc'
echo '#############################################'
endif

if ($f == 'wxpython') then
  echo '# wxPython '
  echo 'set path = ( $path /opt/wx/2.8.11/bin )'
  echo 'if ( ! $?LD_LIBRARY_PATH ) then'
  echo '    setenv LD_LIBRARY_PATH  "/opt/wx/2.8.11/lib"'
  echo 'else'
  echo '    setenv LD_LIBRARY_PATH  "/opt/wx/2.8.11/lib":"$LD_LIBRARY_PATH"'
  echo 'endif'
endif


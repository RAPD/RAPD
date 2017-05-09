#!/bin/bash
# Copyright (c) 2015 Cornell Universit

THIS_DIR=$(cd $(dirname $0); pwd)
THIS_FILE=$(basename $0)
SRC_DIR=$THIS_DIR"/sources"
PREFIX=$THIS_DIR
BATCH=0
FORCE=0
PLATFORM=$(uname -s)
INSTALL_ANACONDA=0

# Handle command line
while getopts "bfhavp:" x; do
    case "$x" in
        h)
            echo "usage: $0 [options]

Installs HCMERGE 1.0.1

    -f           no error if install prefix already exists
    -h           print this help message and exit
    -p PREFIX    install prefix, defaults to $PREFIX
"
            exit 2
            ;;
        b)
            BATCH=1
            ;;
        f)
            FORCE=1
            ;;
        p)
            PREFIX="$OPTARG"
            ;;
#
        ?)
            echo "Error: did not recognize option, please try -h"
            exit 1
            ;;
    esac
done

if [[ $BATCH == 0 ]] # interactive mode
then
  printf "
Welcome to HCMERGE

HCMERGE will be installed into $PREFIX
  
  - Press ENTER to confirm the location
  - Press CTRL-C to abort the installation
  - Or specify a different location below

[$PREFIX] >>> "
  read user_prefix
  if [[ $user_prefix != "" ]]; then
      case "$user_prefix" in
          *\ * )
              echo "ERROR: Cannot install into directories with spaces" >&2
              exit 1
              ;;
          *)
              eval PREFIX="$user_prefix"
              ;;
      esac
  fi
  CONDATAG="-c"
else
  CONDATAG="-yc"
fi # ! BATCH

# Check for directory already existing
if [[ ($FORCE == 0) && (-e $PREFIX) ]]; then
    printf "\033[91mERROR: File or directory already exists: $PREFIX\n" >&2
    printf "Use -f option to override\033[0m\n" >&2
    exit 1
fi

# Make the new directory
mkdir -p $PREFIX
if (( $? )); then
    echo "ERROR: Could not create directory: $PREFIX" >&2
    exit 1
fi

PREFIX=$(cd $PREFIX; pwd)

#
# CCTBX install
#
printf "\n\033[94mInstalling CCTBX\033[0m\n"
CCTBX_PREFIX_SRC=$SRC_DIR"/cctbx"
mkdir -p $CCTBX_PREFIX_SRC
CCTBX_PREFIX_TGT=$PREFIX"/share/cctbx"
mkdir -p $CCTBX_PREFIX_TGT
cd $CCTBX_PREFIX_SRC
if [[ $PLATFORM == "Darwin" ]]; then
  wget http://cci.lbl.gov/cctbx_build/dev-525/cctbx-installer-dev-525-mac-intel-osx-x86_64.tar.gz
  tar -xzf cctbx-installer-dev-525-mac-intel-osx-x86_64.tar.gz
  cd cctbx-installer-dev-525-mac-intel-osx-x86_64
  # Copy over license etc.
  cp LICENSE.txt $CCTBX_PREFIX_TGT"/."
  cp COPYRIGHT.txt $CCTBX_PREFIX_TGT"/."
  # Build
  ./install --prefix=$CCTBX_PREFIX_TGT --makedirs
  # Clean up step
  rm -rf $CCTBX_PREFIX_SRC
fi

# elif [[ $PLATFORM == "Linux" ]]; then
#   # Which linux?
#   if [ -f /etc/centos-release ]; then
#     DIST='CentOS'
#     REV=`cat /etc/centos-release | sed s/.*release\ // | sed s/\ .*//`
#     # Not sure if CentOS 7 will even work
#     if [ ${REV:0:1} == "7" ]; then
#        printf "  CentOS 7\n"
#        wget http://cci.lbl.gov/cctbx_build/results/2014_11_12_2205/cctbx_centos62_x86_64_py276_inc.selfx
#        mv cctbx_centos62_x86_64_py276_inc.selfx $CCTBX_PREFIX_TGT"/."
#        cd $CCTBX_PREFIX_TGT
#        perl cctbx_centos62_x86_64_py276_inc.selfx
#        rm cctbx_centos62_x86_64_py276_inc.selfx
#        cp LICENSE.txt $CCTBX_PREFIX_TGT"/."
#        cp COPYRIGHT.txt $CCTBX_PREFIX_TGT"/."
#     elif [ ${REV:0:1} == "6" ]; then
#        printf "  CentOS 6\n"
#        wget http://cci.lbl.gov/cctbx_build/results/2014_11_12_2205/cctbx_centos62_x86_64_py276_inc.selfx
#        mv cctbx_centos62_x86_64_py276_inc.selfx $CCTBX_PREFIX_TGT"/."
#        cd $CCTBX_PREFIX_TGT
#        perl cctbx_centos62_x86_64_py276_inc.selfx $PYTHON
#        #rm cctbx_centos62_x86_64_py276_inc.selfx
#        cp LICENSE.txt $CCTBX_PREFIX_TGT"/."
#        cp COPYRIGHT.txt $CCTBX_PREFIX_TGT"/."
#     elif [ ${REV:0:1} == "5" ]; then
#        printf "  CentOS 5\n"
#        wget http://cci.lbl.gov/cctbx_build/results/2014_11_12_2205/cctbx_centos59_x86_64_py276_inc.selfx
#        mv cctbx_centos59_x86_64_py276_inc.selfx $CCTBX_PREFIX_TGT"/."
#        cd $CCTBX_PREFIX_TGT
#        perl cctbx_centos59_x86_64_py276_inc.selfx
#        rm cctbx_centos59_x86_64_py276_inc.selfx
#        cp LICENSE.txt $CCTBX_PREFIX_TGT"/."
#        cp COPYRIGHT.txt $CCTBX_PREFIX_TGT"/."
#     fi
#   fi
# fi
cd $THIS_DIR
printf "\033[92mCCTBX install complete.\033[0m\n\n"

exit 1


#
# Install miniconda distribution
#
ANACONDA_SRC_PREFIX=$SRC_DIR"/anaconda"
ANACONDA_PREFIX=$PREFIX"/share/anaconda"
PYTHON=$ANACONDA_PREFIX"/bin/python"
cd $ANACONDA_SRC_PREFIX
if [[ $INSTALL_ANACONDA == 1 ]]; then
  printf "\n\033[94mInstalling Anaconda Python distibution\033[0m\n"
  if [[ $PLATFORM == "Darwin" ]]; then
    if [ -f Anaconda-2.2.0-MacOSX-x86_64.sh ]; then
      sh Anaconda-2.2.0-MacOSX-x86_64.sh -bfp $ANACONDA_PREFIX
    else
      printf "\033[91mError\n"
      printf "Installer expects Anaconda-2.2.0-MacOSX-x86_64.sh to be in $ANACONDA_SRC_PREFIX \033[0m\n"
      exit 1
    fi
  elif [[ $PLATFORM == "Linux" ]]; then
    if [ -f Anaconda-2.2.0-Linux-x86_64.sh ]; then
      sh Anaconda-2.2.0-Linux-x86_64.sh -bfp $ANACONDA_PREFIX
    else
      printf "\033[91mError\n"
      printf "Installer expects Anaconda-2.2.0-Linux-x86_64.sh to be in $ANACONDA_SRC_PREFIX \033[0m\n"
      exit 1
    fi
  fi
  # Conda-install some additional anaconda-based software
  CONDA=$ANACONDA_PREFIX/bin/conda
  $CONDA update  $CONDATAG https://conda.binstar.org/anaconda conda
  $CONDA update  $CONDATAG https://conda.binstar.org/anaconda anaconda
  $CONDA install $CONDATAG https://conda.binstar.org/anaconda pymongo
else
  printf "\n\033[94mInstalling Miniconda Python distibution\033[0m\n"
  if [[ $PLATFORM == "Darwin" ]]; then
    wget https://repo.continuum.io/miniconda/Miniconda-latest-MacOSX-x86_64.sh
    bash Miniconda-latest-MacOSX-x86_64.sh -bfp $ANACONDA_PREFIX
    rm Miniconda-latest-MacOSX-x86_64.sh
  elif [[ $PLATFORM == "Linux" ]]; then
    wget https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh
    bash Miniconda-latest-Linux-x86_64.sh -bfp $ANACONDA_PREFIX
    rm Miniconda-latest-Linux-x86_64.sh
  fi
  # Conda-install some additional anaconda-based software
  CONDA=$ANACONDA_PREFIX/bin/conda
  $CONDA update  $CONDATAG https://conda.binstar.org/anaconda
  $CONDA install $CONDATAG https://conda.binstar.org/anaconda scipy matplotlib redis-py pymongo
fi
# Pip-install some software
PIP=$ANACONDA_PREFIX/bin/pip
$PIP install --retries 5 fabio
$PIP install --retries 5 hcluster
printf "\033[92mPython install complete.\033[0m\n"

# #
# # Install mongodb distribution
# #
# printf "\n\033[94mInstalling mongodb 3.0.3\033[0m\n"
# MONGO_PREFIX_SRC=$SRC_DIR"/mongo"
# MONGO_PREFIX_TGT=$PREFIX"/share/mongo"
# cd $MONGO_PREFIX_SRC
# if [[ $PLATFORM == "Darwin" ]]; then
#   wget https://fastdl.mongodb.org/osx/mongodb-osx-x86_64-3.0.3.tgz
#   tar xzf mongodb-osx-x86_64-3.0.3.tgz
#   # tar xjf mongodb-osx-x86_64-3.0.3.tar.bz2
#   mv mongodb-osx-x86_64-3.0.3 $MONGO_PREFIX_TGT
#   rm mongodb-osx-x86_64-3.0.3.tgz
#  cd $THIS_DIR
# elif [[ $PLATFORM == "Linux" ]]; then
#   # Which linux?
#   if [ -f /etc/centos-release ]; then
#      DIST='CentOS'
#      REV=`cat /etc/centos-release | sed s/.*release\ // | sed s/\ .*//`
#      if [ ${REV:0:1} == "7" ]; then
#          printf "  CentOS 7\n"
#          wget https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-rhel70-3.0.3.tgz
#          tar xzf mongodb-linux-x86_64-rhel70-3.0.3.tgz
#          mv mongodb-linux-x86_64-rhel70-3.0.3 $MONGO_PREFIX_TGT
#          rm mongodb-linux-x86_64-rhel70-3.0.3.tgz
#          cd $THIS_DIR
#      elif [ ${REV:0:1} == "6" ]; then
#          printf "  CentOS 6\n"
#          wget https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-rhel62-3.0.3.tgz
#          tar xzf mongodb-linux-x86_64-rhel62-3.0.3.tgz
#          mv mongodb-linux-x86_64-rhel62-3.0.3 $MONGO_PREFIX_TGT
#          rm mongodb-linux-x86_64-rhel62-3.0.3.tgz
#          cd $THIS_DIR
#      elif [ ${REV:0:1} == "5" ]; then
#          printf "  CentOS 5\n"
#          wget https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-rhel55-3.0.3.tgz
#          tar xzf mongodb-linux-x86_64-rhel55-3.0.3.tgz
#          mv mongodb-linux-x86_64-rhel55-3.0.3 $MONGO_PREFIX_TGT
#          rm mongodb-linux-x86_64-rhel55-3.0.3.tgz
#          cd $THIS_DIR
#      fi
#   elif [ -f /etc/debian_version ]; then
#     DIST='Debian'
#     DTYPE=`sed -n 3p /etc/os-release | sed s/ID\=//`
#     if [ $DTYPE == "ubuntu" ]; then
#       printf "Ubuntu\n"
#       REV=`sed -n 6p /etc/os-release | sed s/VERSION_ID\=\"// | sed s/\.[0-9]*\"//`
#       if [ $REV == "12" ]; then
#         printf "  12\n"
#         wget https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu1204-3.0.3.tgz
#         tar xzf mongodb-linux-x86_64-ubuntu1204-3.0.3.tgz
#         mv mongodb-linux-x86_64-ubuntu1204-3.0.3 $MONGO_PREFIX_TGT
#         rm mongodb-linux-x86_64-ubuntu1204-3.0.3.tgz
#       fi
#     fi
#   fi
# fi
# printf "\033[92mMongoDB install complete.\033[0m\n"

# #
# # Install node.js distribution
# #
# printf "\n\033[94mInstalling node-v0.12.4\033[0m\n"
# NODE_PREFIX_SRC=$SRC_DIR"/node"
# NODE_PREFIX_TGT=$PREFIX"/share/node"
# cd $NODE_PREFIX_SRC
# if [[ $PLATFORM == "Darwin" ]]; then
#   wget http://nodejs.org/dist/v0.12.4/node-v0.12.4-darwin-x64.tar.gz
#   tar xjf node-v0.12.4-darwin-x64.tar.gz
#   mv node-v0.12.4-darwin-x64 $NODE_PREFIX_TGT
#   rm node-v0.12.4-darwin-x64.tar.gz
#   cd $THIS_DIR
# elif [[ $PLATFORM == "Linux" ]]; then
#  # Which linux?
#  if [ -f /etc/centos-release ]; then
#      # No version dependence yet!
#      wget http://nodejs.org/dist/v0.12.4/node-v0.12.4-linux-x64.tar.gz
#      tar xzf node-v0.12.4-linux-x64.tar.gz
#      mv node-v0.12.4-linux-x64 $NODE_PREFIX_TGT
#      rm node-v0.12.4-linux-x64.tar.gz
#      cd $THIS_DIR
#  fi
# fi
# printf "\033[92mNodeJS install complete.\033[0m\n"


#
# CCTBX install
#
printf "\n\033[94mInstalling CCTBX\033[0m\n"
CCTBX_PREFIX_SRC=$SRC_DIR"/cctbx"
CCTBX_PREFIX_TGT=$PREFIX"/share/cctbx"
mkdir -p $CCTBX_PREFIX_TGT
cd $CCTBX_PREFIX_SRC
if [[ $PLATFORM == "Darwin" ]]; then
  wget http://cci.lbl.gov/cctbx_build/results/2014_11_12_2205/cctbx_mac_x86_64_os_10_6_py276_inc.selfx
  mv cctbx_mac_x86_64_os_10_6_py276_inc.selfx $CCTBX_PREFIX_TGT"/."
  cp LICENSE.txt $CCTBX_PREFIX_TGT"/."
  cp COPYRIGHT.txt $CCTBX_PREFIX_TGT"/."
  cd $CCTBX_PREFIX_TGT
  perl cctbx_mac_x86_64_os_10_6_py276_inc.selfx
  rm cctbx_mac_x86_64_os_10_6_py276_inc.selfx
elif [[ $PLATFORM == "Linux" ]]; then
  # Which linux?
  if [ -f /etc/centos-release ]; then
    DIST='CentOS'
    REV=`cat /etc/centos-release | sed s/.*release\ // | sed s/\ .*//`
    # Not sure if CentOS 7 will even work
    if [ ${REV:0:1} == "7" ]; then
       printf "  CentOS 7\n"
       wget http://cci.lbl.gov/cctbx_build/results/2014_11_12_2205/cctbx_centos62_x86_64_py276_inc.selfx
       mv cctbx_centos62_x86_64_py276_inc.selfx $CCTBX_PREFIX_TGT"/."
       cd $CCTBX_PREFIX_TGT
       perl cctbx_centos62_x86_64_py276_inc.selfx
       rm cctbx_centos62_x86_64_py276_inc.selfx
       cp LICENSE.txt $CCTBX_PREFIX_TGT"/."
       cp COPYRIGHT.txt $CCTBX_PREFIX_TGT"/."
    elif [ ${REV:0:1} == "6" ]; then
       printf "  CentOS 6\n"
       wget http://cci.lbl.gov/cctbx_build/results/2014_11_12_2205/cctbx_centos62_x86_64_py276_inc.selfx
       mv cctbx_centos62_x86_64_py276_inc.selfx $CCTBX_PREFIX_TGT"/."
       cd $CCTBX_PREFIX_TGT
       perl cctbx_centos62_x86_64_py276_inc.selfx $PYTHON
       #rm cctbx_centos62_x86_64_py276_inc.selfx
       cp LICENSE.txt $CCTBX_PREFIX_TGT"/."
       cp COPYRIGHT.txt $CCTBX_PREFIX_TGT"/."
    elif [ ${REV:0:1} == "5" ]; then
       printf "  CentOS 5\n"
       wget http://cci.lbl.gov/cctbx_build/results/2014_11_12_2205/cctbx_centos59_x86_64_py276_inc.selfx
       mv cctbx_centos59_x86_64_py276_inc.selfx $CCTBX_PREFIX_TGT"/."
       cd $CCTBX_PREFIX_TGT
       perl cctbx_centos59_x86_64_py276_inc.selfx
       rm cctbx_centos59_x86_64_py276_inc.selfx
       cp LICENSE.txt $CCTBX_PREFIX_TGT"/."
       cp COPYRIGHT.txt $CCTBX_PREFIX_TGT"/."
    fi
  fi
fi
cd $THIS_DIR
printf "\033[92mCCTBX install complete.\033[0m\n\n"


# Set up rapd
# Create the bin directory
BINDIR=$PREFIX"/bin"
if [ ! -e $BINDIR ]
then
  mkdir $BINDIR
fi

# Create a script for calling rapd2.python
printf "Installing rapd executables\n"
SAFE_PREFIX=$(echo "$PREFIX" | sed -e 's/\//\\\//g')
cd $BINDIR
printf "rapd2.python\n"
sed -e "s/LIBTBX_PYEXE=.*/RAPD_PYEXE=$SAFE_PREFIX\/share\/anaconda\/bin\/python/" \
    -e "s/LIBTBX_BUILD=.*/LIBTBX_BUILD=$SAFE_PREFIX\/share\/cctbx\/cctbx_build/" \
    -e 's/LIBTBX_DISPATCHER_NAME="cctbx.python"/LIBTBX_DISPATCHER_NAME="rapd2.python"/' \
    -e 's/LIBTBX_PYEXE/RAPD_PYEXE/' \
    -e "s/DYLD_LIBRARY_PATH=\"/DYLD_LIBRARY_PATH=\"$SAFE_PREFIX\/share\/anaconda\/lib\:/g" \
    $PREFIX/share/cctbx/cctbx_build/bin/cctbx.python > ./rapd2.python
chmod +x ./rapd2.python

# Create the rapd.shrc script
printf "Wrting rapd.shrc\n"
cd $PREFIX
echo "# $PREFIX/rapd.shrc -- bash initialization script for RAPD2" > rapd.shrc
echo "#" >> rapd.shrc
echo "# (c) Copyright 2015, Cornell University" >> rapd.shrc
echo "" >> rapd.shrc
echo "# THIS IS AN AUTOMATICALLY GENERATED FILE." > rapd.shrc
echo "# DO NOT EDIT UNLESS YOU REALLY KNOW WHAT YOU ARE DOING." >> rapd.shrc
echo "" >> rapd.shrc
echo "# Setup paths for cctbx" >> rapd.shrc
echo "source $PREFIX/share/cctbx/cctbx_build/setpaths.sh" >> rapd.shrc
echo "" >> rapd.shrc
echo "# Add rapd2 bin to the path" >> rapd.shrc
echo "PATH=$BINDIR:\$PATH" >> rapd.shrc
echo "export PATH" >> rapd.shrc
echo "" >> rapd.shrc
echo "echo '==================================================='" >> rapd.shrc
echo "echo '                    RAPD v2.0.0                    '" >> rapd.shrc
echo "echo '==================================================='" >> rapd.shrc
echo "echo ' Thanks for using RAPD. Please visit RAPD on github'" >> rapd.shrc
echo "echo ' at https://github.com/RAPD/rapd2  Enjoy.'" >> rapd.shrc
echo "echo '==================================================='" >> rapd.shrc
echo "echo''" >> rapd.shrc

# Create the rapd.shrc script
printf "Wrting rapd.cshrc\n"
cd $PREFIX
echo "# $PREFIX/rapd.cshrc -- bash initialization script for RAPD2" > rapd.cshrc
echo "#" >> rapd.cshrc
echo "# (c) Copyright 2015, Cornell University" >> rapd.cshrc
echo "" >> rapd.cshrc
echo "# THIS IS AN AUTOMATICALLY GENERATED FILE." > rapd.cshrc
echo "# DO NOT EDIT UNLESS YOU REALLY KNOW WHAT YOU ARE DOING." >> rapd.cshrc
echo "" >> rapd.cshrc
echo "# Setup paths for cctbx" >> rapd.cshrc
echo "source $PREFIX/share/cctbx/cctbx_build/setpaths.csh" >> rapd.cshrc
echo "" >> rapd.cshrc
echo "# Add rapd2 bin to the path" >> rapd.cshrc
echo "setenv PATH $BINDIR:\$PATH" >> rapd.cshrc
echo "" >> rapd.cshrc
echo "echo '==================================================='" >> rapd.cshrc
echo "echo '                    RAPD v2.0.0                    '" >> rapd.cshrc
echo "echo '==================================================='" >> rapd.cshrc
echo "echo ' Thanks for using RAPD. Please visit RAPD on github'" >> rapd.cshrc
echo "echo ' at https://github.com/RAPD/rapd2  Enjoy.'          " >> rapd.cshrc
echo "echo '==================================================='" >> rapd.cshrc
echo "echo''" >> rapd.cshrc

printf "\033[92mRAPD installation is complete\033[0m\n\n"

printf "=====================================================================\n"
printf "=  INITIALIZING RAPD2 \n"
printf "= \n"
printf "=  sh and bash users: \n"
printf "=    source \"$PREFIX/rapd.shrc\" \n"
printf "=  You may want to add this line to your .profile or .bashrc file \n"
printf "= \n"
printf "=  csh and tcsh users: \n"
printf "=    source \"$PREFIX/rapd.cshrc\" \n"
printf "=  You may want to add this line to your .cshrc file. \n"
printf "=====================================================================\n"

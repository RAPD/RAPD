# RAPD
#
# VERSION 2.0.0

FROM centos:6
MAINTAINER Frank Murphy <fmurphy@anl.gov>

# Needed to build Phenix
RUN yum -y install bzip2 \
                   gcc-c++ \
                   git \
                   make \
                   mesa-libGL-devel \
                   mesa-libGLU-devel \
                   ncurses-devel \
                   openssl-devel \
                   patch \
                   subversion \
                   wget

WORKDIR /opt
RUN git clone -b iss008 https://github.com/RAPD/RAPD.git rapd
WORKDIR /opt/rapd/install
# RUN ./install -mb > install.log

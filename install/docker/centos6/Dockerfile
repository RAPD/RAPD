# RAPD
#
# VERSION 2.0.0

FROM centos:6
MAINTAINER Frank Murphy <fmurphy@anl.gov>

# Needed to build Phenix
RUN yum -y install gcc-c++ \
                   make \
                   wget \
                   subversion \
                   git \
                   bzip2 \
                   openssl-devel \
                   mesa-libGL-devel \
                   mesa-libGLU-devel \
                   patch

WORKDIR /opt
RUN git clone -b iss008 https://github.com/RAPD/RAPD.git rapd
WORKDIR /opt/rapd/install
# RUN ./install -mb > install.log

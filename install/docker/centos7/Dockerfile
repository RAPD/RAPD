# RAPD
#
# VERSION 2.0.0

FROM centos:7
MAINTAINER Frank Murphy <fmurphy@anl.gov>

# Needed to build Phenix
RUN yum -y install wget \
                   subversion \
                   git \
                   bzip2 \
                   openssl-devel \
                   gcc-c++ \
                   make \
                   mesa-libGL-devel \
                   mesa-libGLU-devel \
                   readline \
                   patch \
                   python

WORKDIR /opt
RUN git clone -b master https://github.com/RAPD/RAPD.git rapd
WORKDIR /opt/rapd/install
RUN ./install -mb

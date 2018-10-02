# RAPD
#
# VERSION 2.0.0

FROM centos:6.9
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
RUN adduser tester
USER tester
WORKDIR /home/tester
RUN git clone -b master https://github.com/RAPD/RAPD.git rapd
WORKDIR /home/tester/rapd/install
# RUN ./install -mb > install.log

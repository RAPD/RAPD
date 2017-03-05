# RAPD
#
# VERSION 2.0.0

FROM ubuntu:16.04
MAINTAINER Frank Murphy <fmurphy@anl.gov>

# Needed to build CCTBX
RUN  apt-get update \
  && apt-get install -y --no-install-recommends apt-utils \
  && apt-get install -y wget \
  && apt-get install -y subversion \
  && apt-get install -y git \
  && apt-get install -y make \
  && apt-get install -y bzip2 \
  && apt-get install -y gcc-c++ \
  && apt-get install -y mesa-libGL-devel \
  && apt-get install -y mesa-libGLU-devel

WORKDIR /opt
RUN mkdir cctbx
WORKDIR /opt/cctbx
RUN wget https://raw.githubusercontent.com/cctbx/cctbx_project/master/libtbx/auto_build/bootstrap.py
RUN python bootstrap.py --builder=cctbx

# WORKDIR /opt
# RUN git clone -b master https://github.com/RAPD/RAPD.git rapd
# WORKDIR /opt/rapd/install
# RUN ./install_cctbx

# RUN rpm --import https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-6 \
# && rpm -Uvh http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm \
# && rpm --import http://rpms.remirepo.net/RPM-GPG-KEY-remi \
# && rpm -Uvh http://rpms.famillecollet.com/enterprise/remi-release-6.rpm \
# && yum -y install blas-devel lapack-devel atlas-sse3-devel atlas-devel openblas-devel libffi-devel ImageMagick-devel git \
# && yum clean all

# BASH!
# RUN ln -snf /bin/bash /bin/sh

# RAPD
# WORKDIR /opt
# RUN git clone -b sercat https://github.com/RAPD/RAPD.git rapd
# WORKDIR /opt/rapd/install
# COPY phenix-installer-1.11.1-2575-intel-linux-2.6-x86_64-centos6.tar sources/phenix/
# RUN /bin/bash -c "./install -b"
# RUN /bin/bash -c "echo 'Finished with rapd install'"
# RUN /bin/bash -c "echo 'source /opt/rapd/rapd.shrc' >>/etc/bashrc"

# Clean up phenix install
# RUN /bin/bash -c "rm -f /opt/rapd/install/sources/phenix/phenix-installer-1.11.1-2575-intel-linux-2.6-x86_64-centos6.tar"
# RUN /bin/bash -c "rm -rf /opt/rapd/install/sources/phenix/phenix-installer-1.11.1-2575-intel-linux-2.6-x86_64-centos6"

# WORKDIR /opt/rapd/src

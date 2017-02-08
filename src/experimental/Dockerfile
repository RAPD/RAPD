# RAPD
#
# VERSION 2.0.0

FROM centos:6.7
MAINTAINER Frank Murphy <fmurphy@anl.gov>

# Needed to build Phenix
RUN rpm --import https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-6
RUN rpm -Uvh http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
RUN rpm --import http://rpms.remirepo.net/RPM-GPG-KEY-remi
RUN rpm -Uvh http://rpms.famillecollet.com/enterprise/remi-release-6.rpm
RUN yum -y --enablerepo=remi,remi-test install redis
RUN yum -y install blas-devel lapack-devel atlas-sse3-devel atlas-devel openblas-devel libffi-devel ImageMagick-devel git

# BASH!
RUN ln -snf /bin/bash /bin/sh

# RAPD
# WORKDIR /opt
# RUN git clone -b sercat https://github.com/RAPD/RAPD.git rapd
# WORKDIR /opt/rapd/install
# ADD phenix-installer-1.11.1-2575-intel-linux-2.6-x86_64-centos6.tar sources/phenix/
# RUN /bin/bash -c "./install -b"
# RUN /bin/bash -c "echo 'Finished with rapd install'"
# RUN /bin/bash -c "echo 'source /opt/rapd/rapd.shrc' >>/etc/bashrc"

# WORKDIR /opt/rapd/src

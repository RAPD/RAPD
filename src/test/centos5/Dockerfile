# RAPD
#
# VERSION 2.0.0

FROM centos:5
MAINTAINER Frank Murphy <fmurphy@anl.gov>

# Needed to build Phenix
RUN yum install -y wget
RUN wget https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-5
RUN rpm --import RPM-GPG-KEY-EPEL-5
RUN rpm -Uvh http://dl.fedoraproject.org/pub/epel/5/x86_64/epel-release-5-4.noarch.rpm
RUN rpm --import http://rpms.remirepo.net/RPM-GPG-KEY-remi
RUN rpm -Uvh http://rpms.famillecollet.com/enterprise/remi-release-5.rpm
RUN yum -y --enablerepo=remi,remi-test install redis
RUN yum -y install blas-devel lapack-devel atlas-sse3-devel atlas-devel openblas-devel libffi-devel ImageMagick-devel git

# BASH!
RUN ln -snf /bin/bash /bin/sh

# RAPD
WORKDIR /opt
RUN git clone -b sercat https://github.com/RAPD/RAPD.git rapd
WORKDIR /opt/rapd/install
ADD phenix-installer-1.10.1-2155-intel-linux-2.6-x86_64-centos5.tar sources/phenix/
RUN /bin/bash -c "./install -b"
RUN /bin/bash -c "echo 'Finished with rapd install'"
RUN /bin/bash -c "echo 'source /opt/rapd/rapd.shrc' >>/etc/bashrc"

WORKDIR /opt/rapd/src

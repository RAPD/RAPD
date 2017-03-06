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
  && apt-get install -y bzip2 \
  && apt-get install -y zlib1g-dev \
  && apt-get install -y libssl-dev \
  && apt-get install -y pkg-config \
  && apt-get install -y python \
  && apt-get install -y build-essential \
  && apt-get install -y libgl1-mesa-dev \
  && apt-get install -y libglu1-mesa-dev

# Install RAPD
WORKDIR /opt
RUN git clone -b master https://github.com/RAPD/RAPD.git rapd
WORKDIR /opt/rapd/install
RUN ./install_cctbx -b

# RAPD
#
# VERSION 2.0.0

FROM centos:7
MAINTAINER Frank Murphy <fmurphy@anl.gov>

# Needed to build Phenix
RUN yum -y install bzip2 \
                   gcc-c++ \
                   git \
                   libffi-devel \
                   make \
                   mesa-libGL-devel \
                   mesa-libGLU-devel \
                   ncurses-devel \
                   openssl-devel \
                   patch \
                   python \
                   readline \
                   subversion \
                   sudo \
                   wget

RUN echo -e "jkdskpakdjfdlkdvnlsjdsjk\njkdskpakdjfdlkdvnlsjdsjk" | (passwd root)
RUN adduser tester
RUN echo -e "bjsdjhdx\nbjsdjhdx" | (passwd tester)
RUN  echo "tester ALL=(ALL)       NOPASSWD: ALL" >> /etc/sudoers
USER tester
WORKDIR /home/tester
RUN wget https://sbgrid.org/wiki/downloads/sbgrid-1.0.660-Linux.tgz
RUN gunzip sbgrid-1.0.660-Linux.tgz
RUN tar xvf sbgrid-1.0.660-Linux.tar
WORKDIR /home/tester/sbgrid-1.0.660-Linux

# RUN git clone -b master https://github.com/RAPD/RAPD.git rapd
# WORKDIR /home/tester/rapd/install
# RUN ./install -mb

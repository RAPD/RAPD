FROM centos:centos6
MAINTAINER The CentOS Project <cloud-ops@centos.org>

RUN yum -y update; yum clean all
RUN yum -y install epel-release; yum clean all
RUN yum -y install redis; yum clean all

EXPOSE 6379

# CMD [ "redis-server" ]

# Install MongoDB
RUN echo -e "[mongodb]\nname=MongoDB Repository\nbaseurl=https://repo.mongodb.org/yum/redhat/6/mongodb-org/3.2/`uname -m`/\ngpgcheck=0\nenabled=1" > /etc/yum.repos.d/mongodb.repo && \
    yum install -y mongodb-org && \
    yum clean all && \
    chown -R mongod:mongod /var/lib/mongo

EXPOSE 27017

# Get nodejs set up
RUN curl -OL https://nodejs.org/dist/v6.9.2/node-v6.9.2-linux-x64.tar.gz
RUN tar -xzf node-v6.9.2-linux-x64.tar.gz
RUN rm node-v6.9.2-linux-x64.tar.gz
RUN echo 'export PATH=/node-v6.9.2-linux-x64/bin:$PATH' >>~/.bash_profile
ENV PATH="/node-v6.9.2-linux-x64/bin:${PATH}"

# Create app directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Install app dependencies
COPY package.json /usr/src/app/
RUN npm install; exit 0

# Bundle app source
COPY . /usr/src/app

 EXPOSE 3000
# CMD [ "npm", "start" ]

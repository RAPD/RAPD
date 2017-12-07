FROM node

# Install vim
RUN ["apt-get", "update"]
RUN ["apt-get", "install", "-y", "vim"]

# Create app directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Install app dependencies
COPY package.json /usr/src/app/
RUN npm install
RUN npm install -g forever

# Bundle app source
COPY . /usr/src/app

EXPOSE 80
CMD [ "npm", "start" ]

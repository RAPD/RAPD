#!/bin/bash

npm uninstall -g @angular/cli
npm cache clean --force
npm install -g @angular/cli@1.6.0-rc.0
rm -rf node_modules dist
npm install --save-dev @angular/cli@1.6.0-rc.0
npm install

#!/bin/bash

npm uninstall -g @angular/cli
npm cache verify
npm install -g @angular/cli@8.3.19
rm -rf node_modules dist
npm install --save-dev @angular/cli@8.3.19
npm install

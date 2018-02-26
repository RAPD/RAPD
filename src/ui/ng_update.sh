#!/bin/bash

npm uninstall -g @angular/cli
npm cache clean --force
npm install -g @angular/cli@6.0.0-beta.3
rm -rf node_modules dist
npm install --save-dev @angular/cli@6.0.0-beta.3
npm install

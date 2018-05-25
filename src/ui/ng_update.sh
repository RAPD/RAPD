#!/bin/bash

npm uninstall -g @angular/cli
npm cache verify
npm install -g @angular/cli@6.0.5
rm -rf node_modules dist
npm install --save-dev @angular/cli@6.0.5
npm install

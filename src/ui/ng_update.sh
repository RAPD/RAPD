#!/bin/bash

npm uninstall -g @angular/cli
npm cache verify
npm install -g @angular/cli@latest
rm -rf node_modules dist
npm install --save-dev @angular/cli@latest
npm install

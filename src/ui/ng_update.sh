#!/bin/bash

npm uninstall -g @angular/cli
npm cache verify
npm install -g @angular/cli@7.1.2
rm -rf node_modules dist
npm install --save-dev @angular/cli@7.1.2
npm install

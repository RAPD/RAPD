#!/bin/bash

#Script for starting the two DISTL servers used in diffraction based centering and quick analysis pipelines

nohup /share/apps/necat/programs/phenix-1.6.4-486/build/intel-linux-2.6-x86_64/bin/distl.mp_spotfinder_server_read_file distl.processors=2 distl.res.outer=4.0 distl.port=8125 > /dev/null 2>& 1 &
nohup /share/apps/necat/programs/phenix-1.6.4-486/build/intel-linux-2.6-x86_64/bin/distl.mp_spotfinder_server_read_file distl.processors=2 distl.port=8126 > /dev/null 2>& 1 &

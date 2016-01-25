#!/bin/bash

# ORIGINAL /share/apps/necat/programs/phenix-1.8.4-1496/build/intel-linux-2.6-x86_64/bin/distl.mp_spotfinder_server_read_file
# NEW /share/apps/necat/programs/CCTBX/build/bin/cctbx.python /share/apps/necat/programs/CCTBX/sources/cctbx_project/spotfinder/command_line/mp_spotfinder_server_read_file.py


nohup /share/apps/necat/programs/CCTBX/build/bin/cctbx.python /share/apps/necat/programs/CCTBX/sources/cctbx_project/spotfinder/command_line/mp_spotfinder_server_read_file.py distl.processors=2 distl.port=8125 > /dev/null 2>& 1 &
nohup /share/apps/necat/programs/CCTBX/build/bin/cctbx.python /share/apps/necat/programs/CCTBX/sources/cctbx_project/spotfinder/command_line/mp_spotfinder_server_read_file.py distl.processors=2 distl.port=8126 > /dev/null 2>& 1 &
nohup /share/apps/necat/programs/CCTBX/build/bin/cctbx.python /share/apps/necat/programs/CCTBX/sources/cctbx_project/spotfinder/command_line/mp_spotfinder_server_read_file.py distl.processors=2 distl.port=8127 > /dev/null 2>& 1 &
nohup /share/apps/necat/programs/CCTBX/build/bin/cctbx.python /share/apps/necat/programs/CCTBX/sources/cctbx_project/spotfinder/command_line/mp_spotfinder_server_read_file.py distl.processors=2 distl.port=8128 > /dev/null 2>& 1 &

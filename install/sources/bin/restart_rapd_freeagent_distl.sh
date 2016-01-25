#!/bin/bash

# Get pid and host name
a=`ps -eaf | grep "rapd_freeagent_distl.py" | grep -v "grep"`
pid=`echo ${a[0]} | cut -d" " -f2`
host=`hostname | cut -d"." -f1`

# Assign beamline
if [[ "$host" =~ "copper" ]]
then
  beamline='E'
fi
if [[ "$host" =~ "uranium" ]]
then
  beamline='C'
fi

# Kill the process
printf "\nKilling rapd_freeagent_distl.py process with pid $pid\n"
kill -9 $pid
sleep 5

# Start the process
echo "Starting the rapd_freeagent_distl  process"
nohup rapd2.python /gpfs5/users/necat/rapd/$host/trunk/rapd_freeagent_distl.py $beamline > /dev/null 2>&1 &

# Make sure the process is running
b=`ps -eaf | grep "rapd_freeagent_distl.py" | grep -v grep`
if [[ $b == *"/gpfs5/users/necat/rapd/$host/trunk/rapd_freeagent_distl.py $beamline"* ]]
  then
    new_pid=`echo ${b[0]} | cut -d" " -f2`
    printf "\033[92mNew rapd_freeagent_distl process running with pid $new_pid\033[0m\n\n"
  else
    printf "\033[91mERROR!!!\033[0m\n\n"
  fi
exit 0

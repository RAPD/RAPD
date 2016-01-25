#!/bin/bash

# Get pid and host name
a=`ps -eaf | grep "rapd_cluster.py" | grep -v "grep"`
pid=`echo ${a[0]} | cut -d" " -f2`
host=`hostname | cut -d"." -f1`

# Kill the process
printf "\nKilling rapd cluster process with pid $pid\n"
kill -9 $pid
sleep 5

# Start the process
echo "Starting the rapd cluster process"
#nohup rapd2.python /gpfs5/users/necat/rapd/$host/trunk/rapd_cluster.py > /dev/null 2>& 1 &
nohup rapd.python $SRCDIR/rapd_cluster.py > /dev/null 2>& 1 &

# Make sure the process is running
sleep 2s
b=`ps -eaf | grep "rapd_cluster.py" | grep -v grep`
if [[ "$b" == *"$SRCDIR/rapd_cluster.py"* ]]
  then
    new_pid=`echo ${b[0]} | cut -d" " -f2`
    printf "\033[92mNew rapd cluster process running with pid $new_pid\033[0m\n\n"
  else
    printf "\033[91mERROR!!!\033[0m\n\n"
  fi
exit 0

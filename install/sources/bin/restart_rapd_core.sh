#!/bin/bash

# Get pid, host and site
a=`ps -eaf | grep "rapd.py" | grep -v "grep"`
pid=`echo ${a[0]} | cut -d" " -f2`
host=`hostname | cut -d"." -f1`
site=`echo ${a[0]} | rev | cut -d" " -f1`

if [[ $a != "" ]]; then
  echo "rapd.py will be restarted with site identifier $site"
else
  if [[ $1 == "" ]]; then
    echo "Since there is no rapd.py process running, you need to put in a site indentifier on the command line."
    exit 1
  else
  	site=$1
  	echo "rapd.py will be started with site identifier $site"
  fi
fi

# Kill the process
printf "\nKilling rapd core process with pid $pid\n"
kill -9 $pid
sleep 5

# Start the process
echo "Starting the rapd core process"
nohup rapd2.python $SRCDIR/rapd.py $site > /dev/null 2>& 1 &

# Make sure the process is running
b=`ps -eaf | grep "rapd.py" | grep -v "grep"`
if [[ "$b" == *"$SRCDIR/rapd.py $site"* ]]
  then
    new_pid=`echo ${b[0]} | cut -d" " -f2`
    printf "\033[92mNew rapd core process running with pid $new_pid\033[0m\n\n"
  else
    printf "\033[91mERROR!!!\033[0m\n\n"
  fi
exit 0

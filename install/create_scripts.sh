#!/bin/bash

if [ -z "$RAPD_HOME" ]; then

  SAFE_PREFIX=$(echo "$RAPD_HOME" | sed -e 's/\//\\\//g')

  echo $RAPD_HOME
  echo $SAFE_PREFIX

  # # Create scripts
  # echo "#! /bin/bash" > ./rapd.control
  # echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py --managed_file $SAFE_PREFIX\/src\/control\/rapd_control.py \"\$@\"" >>./rapd.control
  # chmod +x ./rapd.control
  #
  # echo "#! /bin/bash" > ./rapd.gather
  # echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py --managed_file $SAFE_PREFIX\/src\/sites\/gather\/rapd_gather.py \"\$@\"" >>./rapd.gather
  # chmod +x ./rapd.gather
  #
  # echo "#! /bin/bash" > ./rapd.launcher
  # echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py --managed_file $SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/launch\/rapd_launcher.py \"\$@\"" >>./rapd.launcher
  # chmod +x ./rapd.launcher
  #
  # echo "#! /bin/bash" > ./rapd.launch
  # echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/launch\/rapd_launch.py \"\$@\"" >>./rapd.launch
  # chmod +x ./rapd.launch
  #
  # echo "#! /bin/bash" > ./rapd.overwatch
  # echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py \"\$@\"" >>./rapd.overwatch
  # chmod +x ./rapd.overwatch
else
  echo "The RAPD_HOME environmental variable must be set. Exiting"
  exit(9)
fi

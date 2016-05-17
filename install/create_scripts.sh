#!/bin/bash

if [ "$RAPD_HOME" != "" ]; then

  SAFE_PREFIX=$(echo "$RAPD_HOME" | sed -e 's/\//\\\//g')

  # Create scripts
  echo "#! /bin/bash" > ./rapd.control
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py --managed_file $SAFE_PREFIX\/src\/control\/rapd_control.py \"\$@\"" >>$SAFE_PREFIX\/bin\/rapd.control
  chmod +x $SAFE_PREFIX\/bin\/rapd.control

  echo "#! /bin/bash" > ./rapd.gather
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py --managed_file $SAFE_PREFIX\/src\/sites\/gather\/rapd_gather.py \"\$@\"" >>$SAFE_PREFIX\/bin\/rapd.gather
  chmod +x $SAFE_PREFIX\/bin\/rapd.gather

  echo "#! /bin/bash" > ./rapd.launcher
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py --managed_file $SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/launch\/rapd_launcher.py \"\$@\"" >>$SAFE_PREFIX\/bin\/rapd.launcher
  chmod +x $SAFE_PREFIX\/bin\/rapd.launcher

  echo "#! /bin/bash" > ./rapd.launch
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/launch\/rapd_launch.py \"\$@\"" >>$SAFE_PREFIX\/bin\/rapd.launch
  chmod +x $SAFE_PREFIX\/bin\/rapd.launch

  echo "#! /bin/bash" > ./rapd.overwatch
  echo "$SAFE_PREFIX\/bin\/rapd.python $SAFE_PREFIX\/src\/utils\/overwatch.py \"\$@\"" >>$SAFE_PREFIX\/bin\/rapd.overwatch
  chmod +x $SAFE_PREFIX\/bin\/rapd.overwatch

# Environmental var not set - don't run
else
  echo "The RAPD_HOME environmental variable must be set. Exiting"
  exit
fi

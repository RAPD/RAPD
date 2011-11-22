<?php

function remove_trip($username,$root_data_dir)
{
  echo "<P>function remove_trips $username,$root_data_dir.</P>";

  //load the configuration file
  require('/var/www/html/rapd/login/config.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db($db_name,$connection)or die(mysql_error());

  //make query to database
  $sql ="SELECT * FROM trips WHERE username='$username' AND data_root_dir='$root_data_dir'";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
  $sql = mysql_fetch_object($result);
  $trip_id = $sql ->trip_id;

  //get the number of rows in the result set
  $num = mysql_num_rows($result);

  //no matches
  if ($num == 0)
    {
      //nothing to do
      mysql_close($connection);
      echo "<P>Sorry, there is no match in the database for the trip you have requested to delete.</P>";
    }
  //more than one match (AN ERROR)
  elseif ($num > 1)
    {
      mysql_close($connection);
      echo "<P>Sorry, there is more than one entry in the trips database that matches.</P>";
      echo "<P>Please edit the database manually.</P>";
    }
  //one match, as it should be
  elseif ($num == 1)
    {
      //put results associated with this trip into the orphan_results table
      make_orphans($username,$root_data_dir);
      
      //now remove the trip from the trips table
      $db =  @mysql_select_db($db_name,$connection)or die(mysql_error());
      $sql_del = "DELETE FROM trips WHERE username='$username' AND data_root_dir='$root_data_dir'";
      $result = @mysql_query($sql_del,$connection) or die(mysql_error());
      mysql_close($connection);
      echo "<P>One trip removed.</P>";
      
      //now remove the directory structure for this trip
      rmdir_recursive("../../users/$username/$trip_id");
    }
}

function make_orphans($username,$data_root_dir)
{
  echo "function make_orphans $username,$data_root_dir</P>";

  //load configuration
  require('/var/www/html/rapd/login/config.php');

  //connect to to the proper db
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db =  @mysql_select_db('rapd_data',$connection)or die(mysql_error());

  //snaps
  $sql1    = "SELECT * FROM single_results WHERE data_root_dir='$data_root_dir'";
  $result1 = @mysql_query($sql1,$connection) or die(mysql_error());

  $counter = 0;
  while ($sql1 = mysql_fetch_object($result1))
    {
      $counter++;
      //put in the database
      $id   = $sql1 -> single_result_id;
      $date = $sql1 -> date;
      $sql2    = "INSERT INTO orphan_results (type,data_root_dir,result_id,date) VALUES ('single','$data_root_dir','$id','$date')";
      $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
    }
  echo "<P>$counter single-image results have been removed.</P>";
  //move the files
  shell_exec('mv ../../users/$username/$id/single/* ../../users/orphans/single/.');

  //pairs
  $sql1    = "SELECT * FROM pair_results WHERE data_root_dir='$_POST[data]'";
  $result1 = @mysql_query($sql1,$connection) or die(mysql_error());

  $counter = 0;
  while ($sql1 = mysql_fetch_object($result1))
    {
      ++$counter;
      //put in the database
      $id   = $sql1 -> pair_result_id;
      $date = $sql1 -> date;
      $sql2    = "INSERT INTO orphan_results (type,data_root_dir,result_id,date) VALUES ('pair','$_POST[data]','$id','$date')";
      $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
    }
  echo "<P>$counter image pair-results have been removed.</P>";
  //move the files
  shell_exec('mv ../../users/$username/$id/pairs/* ../../users/orphans/pairs/.');

  //runs
  $sql1    = "SELECT * FROM integrate_results WHERE data_root_dir='$_POST[data]'";
  $result1 = @mysql_query($sql1,$connection) or die(mysql_error());

  $counter = 0;
  while ($sql1 = mysql_fetch_object($result1))
    {
      $counter++;
      //put in the database
      $id   = $sql1 -> run_result_id;
      $date = $sql1 -> date;
      $sql2    = "INSERT INTO orphan_results (type,data_root_dir,result_id,date) VALUES ('run','$_POST[data]','$id','$date')";
      $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
    }
  echo "<P>$counter run results have been removed.</P>";
  //move the files
  shell_exec('mv ../../users/$username/$id/runs/* ../../users/orphans/runs/.');
}

function rmdir_recursive($dir) 
{ 
  // List the contents of the directory table 
  $dir_content = scandir($dir); 
  // Is it a directory? 
  if ($dir_content != FALSE) 
  {
    // For each directory entry 
    foreach($dir_content as $entry) 
    { 
      // Unix symbolic shortcuts, we go 
      if (! in_array($entry, array('.','..')))
      { 
        // We find the path from the beginning 
        $entry = $dir.'/'.$entry; 
        // This entry is not an issue: it clears 
        if (! is_dir($entry)) 
        { 
          unlink($entry); 
           echo "<P>unlink($entry)</P>";
        }  
        // This entry is a folder, it again on this issue 
        else 
        { 
          rmdir_recursive($entry); 
        } 
      } 
    }
  } 
  // It has erased all entries in the folder, we can now erase 
   echo "<P>rmdir($dir)</P>";
  rmdir($dir); 
} 


?>

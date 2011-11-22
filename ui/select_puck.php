<?php
  require('./login/config.php');
  require('./login/functions.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());

  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());

  //add the settings to the puck settings table
  $sql = "INSERT INTO puck_settings (beamline,
                                data_root_dir,
                                A,
                                B,
                                C,
                                D)
                       VALUES ('$_POST[beamline]',
                               '$_POST[datadir]',
                               '$_POST[PuckA]',
                               '$_POST[PuckB]',
                               '$_POST[PuckC]',
                               '$_POST[PuckD]')";

  $result = @mysql_query($sql,$connection) or die(mysql_error());

  //obtain puckset_id for new entry
  $puckset_id = @mysql_insert_id($connection);

  //add puckset_id to the current table
  $sql2 = "UPDATE current SET puckset_id=$puckset_id WHERE beamline='$_POST[beamline]'";
  $result2 = @mysql_query($sql2,$connection) or die(mysql_error());

//  if (mysql_affected_rows($connection) > 0)
//    {
//      echo("<h3>Puck selections for beamline $_POST[beamline] have been saved</h3><hr>");
//    } else {
//      echo("<h3>ERROR while attempting to save puck selections!</h3>");
//    }

  //change db to rapd_cloud
  $db = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());

  //add the request to the cloud_requests table
  $sqlcloud = "INSERT INTO cloud_requests (request_type,
                                data_root_dir,
                                status,
                                puckset_id,
                                option1)
                       VALUES ('setpuck',
                               '$_POST[datadir]',
                               'request',
                               '$puckset_id',
                                '$_POST[beamline]')";

  $resultcloud = @mysql_query($sqlcloud,$connection) or die(mysql_error());
?>

<p><a href="#" onclick="window.parent.tb_remove(); return false">Continue</a>




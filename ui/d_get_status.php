<?php 
  require('./login/config.php');
  require('./login/functions.php');

  $beamline = $_GET[beamline];
  //$beamline = 'E'; 

  //create output array and store result id as 1st value
  $arr = array();
  $arr[] = $beamline;

  // Get the ages in one JOINed query
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db         = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
  $sql        = "SELECT TIMESTAMPDIFF(SECOND,status_dataserver.timestamp,NOW()) AS dataserver_age, 
                        TIMESTAMPDIFF(SECOND,status_controller.timestamp,NOW()) AS controller_age, 
                        TIMESTAMPDIFF(SECOND,status_cluster.timestamp,NOW()) AS cluster_age 
                        FROM status_dataserver,status_cluster,status_controller 
                        WHERE status_cluster.ip_address=status_controller.cluster_ip 
                        AND status_dataserver.beamline='$beamline' 
                        AND status_controller.beamline='$beamline'";
  $result     = @mysql_query($sql,$connection) or die(mysql_error());
  $sql_object = mysql_fetch_object($result);

  $dataserver_age = $sql_object -> dataserver_age;
  $controller_age = $sql_object -> controller_age;
  $cluster_age    = $sql_object -> cluster_age;


  if ($dataserver_age) 
  { 
    $arr[] = $dataserver_age;
  }
  else
  {
    $arr[] = 100;
  }

  if ($controller_age)
  {
    $arr[] = $controller_age;
  }
  else
  {
    $arr[] = 100;
  }

  if ($cluster_age)
  {
    $arr[] = $cluster_age;
  }
  else
  {
    $arr[] = 100;
  }

  //Encode in JSON
  $out = json_encode($arr);
  print $out;  

?>


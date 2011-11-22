<?php
  require('./login/config.php');
  require('./login/functions.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());

  //Now put the request into cloud_requests
  $sql = "INSERT INTO minikappa (omega,kappa,phi,beamline,ip_address,status)
           VALUES ('$_POST[omega]','$_POST[kappa]','$_POST[phi]','$_POST[beamline]','$_POST[ip_address]','request')";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
?>

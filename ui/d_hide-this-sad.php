<?php 
  require('./login/config.php');
  require('./login/functions.php');

  $res_id  = $_GET[res_id];
  //$res_id =  33079;

  //
  // Set the display property of the give result id to hide
  //
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db         = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
  $sql        = "UPDATE results SET display='hide' WHERE result_id=$res_id";
  $result     = @mysql_query($sql,$connection) or die(mysql_error());
?>




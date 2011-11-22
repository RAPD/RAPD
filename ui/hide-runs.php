<?php 
  require('./login/config.php');
  require('./login/functions.php');

  $datadir  = $_GET[datadir];

  // Set the display property of all failed integrations to hide
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db         = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
  $sql        = "UPDATE results r RIGHT JOIN integrate_results i ON r.id=i.integrate_result_id SET r.display='hide' WHERE r.data_root_dir='$datadir' AND r.type='integrate' AND i.integrate_status!='SUCCESS' AND i.integrate_status!='SUCCESS'";
  $result     = @mysql_query($sql,$connection) or die(mysql_error());

  // Set the display property of all failed merges to hide
  $sql        = "UPDATE results r RIGHT JOIN merge_results m ON r.id=m.merge_result_id SET r.display='hide' WHERE r.data_root_dir='$datadir' AND r.type='merge' AND m.merge_status!='success'";
  $result     = @mysql_query($sql,$connection) or die(mysql_error());

?>


<?php 
  require('./login/config.php');
  require('./login/functions.php');

  $datadir  = $_GET[datadir];
  //$datadir = '/gpfs4/users/GU/Keenan_Apr10';
  //
  // Set the display property of all failed singles and snaps to hide
  // SINGLES
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db         = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
  $sql        = "UPDATE results r RIGHT JOIN single_results s ON r.id=s.single_result_id SET r.display='hide' WHERE r.data_root_dir='$datadir' AND r.type='single' AND s.best_norm_status!='SUCCESS' AND s.mosflm_norm_status!='SUCCESS'";
  $result     = @mysql_query($sql,$connection) or die(mysql_error());

  //PAIRS
  $sql2        = "UPDATE results r RIGHT JOIN pair_results p ON r.id=p.pair_result_id SET r.display='hide' WHERE r.data_root_dir='$datadir' AND r.type='pair' AND p.best_norm_status!='SUCCESS' AND p.mosflm_norm_status!='SUCCESS'";
  $result2    = @mysql_query($sql2,$connection) or die(mysql_error());


?>

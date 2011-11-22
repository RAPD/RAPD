<?php 
  require('./login/config.php');
  require('./login/functions.php');

  $datadir  = $_PUT[datadir];
  //$datadir = '/gpfs4/users/GU/Keenan_Apr10';
  //
  // Set the display property of all failed singles and snaps to show
  // SINGLES
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db         = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
  $sql        = "UPDATE results r JOIN single_results s ON r.id=s.single_result_id SET r.display='show' WHERE r.data_root_dir='$datadir' AND r.type='single'";
  $result     = @mysql_query($sql,$connection) or die(mysql_error());

  //PAIRS
  $sql2        = "UPDATE results r JOIN pair_results p ON r.id=p.pair_result_id SET r.display='show' WHERE r.data_root_dir='$datadir' AND r.type='pair'";
  $result2    = @mysql_query($sql2,$connection) or die(mysql_error());


?>

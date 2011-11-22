<?php 
  require('./login/config.php');
  require('./login/functions.php');

  $datadir  = $_GET[datadir];
  
  // Set the display property of all successful singles and snaps to show
  // SINGLES
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db         = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
  $sql        = "UPDATE results r JOIN single_results s ON r.id=s.single_result_id SET r.display='show' WHERE r.data_root_dir='$datadir' AND r.type='single' AND (s.best_norm_status='SUCCESS' OR s.mosflm_norm_status='SUCCESS' OR (s.summary_stac != 'None'))";
  $result     = @mysql_query($sql,$connection) or die(mysql_error());

  //PAIRS
  $sql2        = "UPDATE results r RIGHT JOIN pair_results p ON r.id=p.pair_result_id SET r.display='show' WHERE r.data_root_dir='$datadir' AND r.type='pair' AND (p.best_norm_status='SUCCESS' OR p.mosflm_norm_status='SUCCESS' OR (p.summary_stac != 'None'))";
  $result2    = @mysql_query($sql2,$connection) or die(mysql_error());
?>


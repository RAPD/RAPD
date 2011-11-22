<?php
  require('./login/config.php');
  require('./login/functions.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());

  //Now get the approximate position in the queue for processing
  $db   = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());
  $sql5 = "SELECT remote_concurrent_allowed,current_queue FROM cloud_state";
  $result5 = @mysql_query($sql5,$connection) or die(mysql_error());
  $return5 =  mysql_fetch_object($result5);
  $current_queue = $return5 -> current_queue;
  $allowed = $return5 -> remote_concurrent_allowed;

  $sql6 = "SELECT count(*) as cloud_count FROM cloud_current";
  $result6 = @mysql_query($sql6,$connection) or die(mysql_error());
  $return6 =  mysql_fetch_object($result6);
  $cloud_count = $return6 -> cloud_count; 

  //Add the pdb file to the database
  if ($_POST[pdb_file])
  {
    $short_file = basename($_POST[pdb_file]);
    $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
    $query1 = "INSERT INTO pdbs (pdb_file,
                                 pdb_name,
                                 pdb_description,
                                 username) 
                         VALUES ('$short_file',
                                 '$_POST[pdb_name]',
                                 '$_POST[pdb_description]',
                                 '$_POST[user]')"; 
     $result1 = @mysql_query($query1,$connection) or die(mysql_error());
     $pdbs_id = mysql_insert_id();
   }
   else if ($_POST[pdb_id])
   {
     $pdbs_id = 0;
   }
   else if ($_POST[prior_pdb])
   {
     $pdbs_id = $_POST[prior_pdb];
   }

  //Now put the request into cloud_requests
  $db   = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());
  $query2 = "INSERT INTO cloud_requests (request_type,
                                         original_result_id,
                                         original_type,
                                         original_id,
                                         data_root_dir,
                                         input_mtz,
                                         pdbs_id,
																				 nmol,
                                         ip_address,
                                         status,
                                         option1)
                                 VALUES ('$_POST[request_type]',
                                         '$_POST[original_result_id]',
                                         '$_POST[original_type]',
                                         '$_POST[original_id]',
                                         '$_POST[datadir]',
                                         '$_POST[input_mtz]',
                                         $pdbs_id,
																				 '$_POST[nmol]',
                                         '$_POST[ip]',
                                         'request',
                                         '$_POST[pdb_id]')";
  $result2 = @mysql_query($query2,$connection) or die(mysql_error());


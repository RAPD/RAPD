<?php
  echo("hello 1\n");
  require('./login/config.php');
  require('./login/functions.php');


  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
	
	//Get the variables
	$beamline = $_POST[beamline];
  $res_id_array = split('::',$_POST[res_id_array]);
  $drd = $_POST[datadir];
	//$snap_id = $_POST[snap_id];
	//$beamline = "E";
	//$res_id_array = split('::',"115535::");
	//$drd = "/gpfs3/users/necat/E-beamline_test_June2011";
	//$snap_id = "115539";
	$sql8 = 0;
	//echo("0");

	// Handle the runs
	if (sizeof($res_id_array) == 1)
  {
		//echo("ONE");
    $ref_id = 'NULL';
  } else {
		//echo("2");
    //Insert reference runs into the reference_run table
    $sql1 = "INSERT INTO reference_data (";
    $sql2 = ") VALUES (";
    $counter = 1;
    foreach ($res_id_array as $res_id)
    {
      if ($res_id)
      {
        if ($counter > 1) {$sql1 .= ",";}
        $sql1 .= "result_id_";
        $sql1 .= (string)$counter;
        if ($counter > 1) {$sql2 .= ",";}
        $sql2 .= $res_id;
        $counter += 1;
      }
    }
    $sql2 .= ')';
    $sql1 .= $sql2;

    //Write the data
    $result = @mysql_query($sql1,$connection) or die(mysql_error());
    //Get the reference_data_id
    $ref_id = @mysql_insert_id($connection);

		//echo($ref_id."\n");
	}	
    //Update the settings table with the new reference_data_id
    $sql3 = "SELECT setting_id FROM settings WHERE data_root_dir='$drd' AND setting_type='GLOBAL' ORDER BY setting_id DESC LIMIT 1";
    $result3 = @mysql_query($sql3,$connection) or die(mysql_error());
    $return3 = mysql_fetch_object($result3);
		echo($return3->setting_id);

    if ($return3)
    {
      $setting_id = $return3 -> setting_id;
    } else {
      $sql4 = "SELECT setting_id FROM settings WHERE data_root_dir='DEFAULTS' AND beamline='$beamline' AND setting_type='GLOBAL' ORDER BY setting_id DESC LIMIT 1";
      $result4 = @mysql_query($sql4,$connection) or die(mysql_error());
      $return4 =  mysql_fetch_object($result4);
      $setting_id = $return4 -> setting_id;
  }

	if ($sql8) {
		$result8 = @mysql_query($sql8);
	}

  //add the settings to the settings table
  $sql5 = "INSERT INTO settings (beamline,
                                  data_root_dir,
                                  multiprocessing,
                                  spacegroup,            
                                  sample_type,            
                                  solvent_content,            
                                  susceptibility,            
                                  crystal_size_x,            
                                  crystal_size_y,            
                                  crystal_size_z,            
                                  a,
                                  b,
                                  c,
                                  alpha,
                                  beta,
                                  gamma,
                                  work_dir_override,
                                  work_directory,
                                  beam_flip,
                                  x_beam,
                                  y_beam,
                                  index_hi_res,            
                                  strategy_type,            
                                  best_complexity,            
                                  mosflm_seg,
                                  mosflm_rot,
                                  min_exposure_per,            
                                  aimed_res,            
                                  beam_size_x,            
                                  beam_size_y,            
                                  integrate,            
                                  reference_data_id,            
                                  setting_type) SELECT beamline,
                                  data_root_dir,
                                  multiprocessing,
                                  spacegroup,
                                  sample_type,
                                  solvent_content,
                                  susceptibility,
                                  crystal_size_x,
                                  crystal_size_y,
                                  crystal_size_z,
                                  a,
                                  b,
                                  c,
                                  alpha,
                                  beta,
                                  gamma,
                                  work_dir_override,
                                  work_directory,
                                  beam_flip,
                                  x_beam,
                                  y_beam,
                                  index_hi_res,
                                  strategy_type,
                                  best_complexity,
                                  mosflm_seg,
                                  mosflm_rot,
                                  min_exposure_per,
                                  aimed_res,
                                  beam_size_x,
                                  beam_size_y,
                                  integrate,
                                  reference_data_id,
                                  setting_type FROM settings WHERE setting_id=$setting_id"; 
 
    $result5 = @mysql_query($sql5,$connection) or die(mysql_error());
    $new_setting_id = @mysql_insert_id($connection);

    //Now modify the settings entry to match what we know
    $sql6 = "UPDATE settings SET reference_data_id=$ref_id,data_root_dir='$drd',setting_type='GLOBAL' WHERE setting_id=$new_setting_id";
    $result6 = @mysql_query($sql6,$connection) or die(mysql_error());
  
    //Now update the current table to reflect the new settings IF we are the active drd
    $sql7 = "UPDATE current SET setting_id=$new_setting_id WHERE beamline='$beamline' AND data_root_dir='$drd'";
    $result7 = @mysql_query($sql7,$connection) or die(mysql_error()); 

?>

<?php
  require('./login/config.php');
  require('./login/functions.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());

  //Now put the request into cloud_requests
  $sql = "INSERT INTO datacollection (prefix,
                                      run_number,
                                      image_start,
                                      omega_start,
                                      delta_omega,
                                      number_images,
                                      time,
                                      distance,
                                      transmission,
                                      beamline,
                                      ip_address,
                                      status) VALUES ('$_POST[prefix]',
                                                      '$_POST[run_number]',
                                                      '$_POST[image_start]',
                                                      '$_POST[omega_start]',
                                                      '$_POST[delta_omega]',
                                                      '$_POST[number_images]',
                                                      '$_POST[time]',
                                                      '$_POST[distance]',
                                                      '$_POST[transmission]',
                                                      '$_POST[beamline]',
                                                      '$_POST[ip_address]',
                                                      'request')";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
?>

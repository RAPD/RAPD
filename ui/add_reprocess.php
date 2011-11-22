<?php
  require('./login/config.php');
  require('./login/functions.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());

  if ($_POST[reference_data] == 'None')
  {
  $sql = "INSERT INTO settings (beamline,
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
                                setting_type)
                          VALUES ('$_POST[beamline]',
                                '$_POST[data_root_dir]',
                                '$_POST[multiprocessing]',
                                '$_POST[spacegroup]',
                                '$_POST[sample_type]',
                                 $_POST[solvent_content],
                                 $_POST[susceptibility],
                                 $_POST[crystal_size_x],
                                 $_POST[crystal_size_y],
                                 $_POST[crystal_size_z],
                                 $_POST[a],
                                 $_POST[b],
                                 $_POST[c],
                                 $_POST[alpha],
                                 $_POST[beta],
                                 $_POST[gamma],
                                '$_POST[work_dir_override]',
                                '$_POST[work_directory]',
                                '$_POST[beam_flip]',
                                 $_POST[x_beam],
                                 $_POST[y_beam],
                                 $_POST[index_hi_res],
                                '$_POST[strategy_type]',
                                '$_POST[best_complexity]',
                                '$_POST[mosflm_seg]',
                                '$_POST[mosflm_rot]',
                                 $_POST[min_exposure_per],
                                 $_POST[aimed_res],
                                '$_POST[beam_size_x]',
                                '$_POST[beam_size_y]',
                                '$_POST[integrate]',
                                'SINGLE')";


  } else {

  //add the settings to the settings table
  $sql = "INSERT INTO settings (beamline,
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
                                setting_type)
                        VALUES ('$_POST[beamline]',
                                '$_POST[data_root_dir]',
                                '$_POST[multiprocessing]',
                                '$_POST[spacegroup]',
                                '$_POST[sample_type]',
                                 $_POST[solvent_content],
                                 $_POST[susceptibility],
                                 $_POST[crystal_size_x],
                                 $_POST[crystal_size_y],
                                 $_POST[crystal_size_z],
                                 $_POST[a],
                                 $_POST[b],
                                 $_POST[c],
                                 $_POST[alpha],
                                 $_POST[beta],
                                 $_POST[gamma],
                                '$_POST[work_dir_override]',
                                '$_POST[work_directory]',
                                '$_POST[beam_flip]',
                                 $_POST[x_beam],
                                 $_POST[y_beam],
                                 $_POST[index_hi_res],
                                '$_POST[strategy_type]',
                                '$_POST[best_complexity]',
                                '$_POST[mosflm_seg]',
                                '$_POST[mosflm_rot]',
                                 $_POST[min_exposure_per],
                                 $_POST[aimed_res],
                                '$_POST[beam_size_x]',
                                '$_POST[beam_size_y]',
                                '$_POST[integrate]',
                                 $_POST[reference_data],
                                'SINGLE')";
  }
  $result = @mysql_query($sql,$connection) or die(mysql_error());
  $new_setting_id = @mysql_insert_id($connection);

  // Get the imagenumber for the additional image
  $additional_image_result_number = $_POST[additional_image];
  if ($additional_image_result_number > 0)
  {
    $sql2    = "SELECT fullname,adsc_number from single_results WHERE single_result_id=$additional_image_result_number";
    $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
    $return2 = mysql_fetch_object($result2);
    $additional_image = $return2 -> fullname;
    $adsc_number      = $return2 -> adsc_number;
    
    $sql4    = "SELECT image_id FROM images WHERE fullname='$additional_image' AND adsc_number='$adsc_number'";
    $result4 = @mysql_query($sql4,$connection) or die(mysql_error());
    $return4 = mysql_fetch_object($result4);
    $additional_image_id = $return4 -> image_id;

  } else {
    $additional_image_id = 0;
  }

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

  if ($current_queue > 0)
  {
      $position = $current_queue + 1;
      echo("<h3>This process is currently number $position in the queue</h3>"); 
  } else if ($cloud_count == $allowed) {
      echo("<h3>This process is currently first in the queue</h3>");
  } else {
      echo("<h3>This process will be dispatched immediately</h3>");
  }

  //Now put the request into cloud_requests
  //$db   = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());
  $sql3 = "INSERT INTO cloud_requests (request_type,original_result_id,original_type,original_id,data_root_dir,
                                       ip_address,additional_image,new_setting_id,status)
           VALUES ('$_POST[request_type]','$_POST[original_result_id]','$_POST[original_type]','$_POST[original_id]',
                   '$_POST[data_root_dir]','$_POST[ip_address]','$additional_image_id','$new_setting_id','request')";
  $result3 = @mysql_query($sql3,$connection) or die(mysql_error());

  //The table of settings
  echo("<table>");
  echo("  <tr><td align=right width=250>Spacegroup Override:&nbsp         </td><td align=left>$_POST[spacegroup]</td></tr>\n");
  echo("  <tr><td align=right width=250>Sample Type:&nbsp                 </td><td align=left>$_POST[sample_type]</td></tr>\n");
  echo("  <tr><td align=right width=250>Solvent Fraction:&nbsp            </td><td align=left>$_POST[solvent_content]</td></tr>\n");
  //echo("  <tr><td align=right width=250>Radiation Susceptibility:&nbsp    </td><td align=left>$_POST[susceptibility]</td></tr>\n");
  //echo("  <tr><td align=right width=250>Crystal Size X:&nbsp              </td><td align=left>$_POST[crystal_size_x]</td></tr>\n");
  //echo("  <tr><td align=right width=250>Crystal Size Y:&nbsp              </td><td align=left>$_POST[crystal_size_y]</td></tr>\n");
  //echo("  <tr><td align=right width=250>Crystal Size Z:&nbsp              </td><td align=left>$_POST[crystal_size_z]</td></tr>\n");
  //echo("  <tr><td align=right width=250>Cell Parameters a:&nbsp           </td><td align=left>$_POST[a]</td></tr>\n");
  //echo("  <tr><td align=right width=250>b:&nbsp                           </td><td align=left>$_POST[b]</td></tr>\n");
  //echo("  <tr><td align=right width=250>c:&nbsp                           </td><td align=left>$_POST[c]</td></tr>\n");
  //echo("  <tr><td align=right width=250>&alpha:&nbsp                      </td><td align=left>$_POST[alpha]</td></tr>\n");
  //echo("  <tr><td align=right width=250>&beta:&nbsp                       </td><td align=left>$_POST[beta]</td></tr>\n");
  //echo("  <tr><td align=right width=250>&gamma:&nbsp                      </td><td align=left>$_POST[gamma]</td></tr>\n");
  echo("  <tr><td align=right width=250>Flip Beam Coordinates:&nbsp       </td><td align=left>$_POST[beam_flip]</td></tr>\n");
  echo("  <tr><td align=right width=250>Override X Beam:&nbsp             </td><td align=left>$_POST[x_beam]</td></tr>\n");
  echo("  <tr><td align=right width=250>Override Y Beam:&nbsp             </td><td align=left>$_POST[y_beam]</td></tr>\n");
  //echo("  <tr><td align=right width=250>Hi Res Cutoff - Peak Picking:&nbsp</td><td align=left>$_POST[index_hi_res]</td></tr>\n");
  echo("  <tr><td align=right width=250>Strategy Type:&nbsp               </td><td align=left>$_POST[strategy_type]</td></tr>\n");
  echo("  <tr><td align=right width=250>Strategy Complexity:&nbsp         </td><td align=left>$_POST[best_complexity]</td></tr>\n");
  echo("  <tr><td align=right width=250>Mosflm Segments:&nbsp             </td><td align=left>$_POST[mosflm_seg]</td></tr>\n");
  echo("  <tr><td align=right width=250>Mosflm Rotation:&nbsp             </td><td align=left>$_POST[mosflm_rot]</td></tr>\n");
  //echo("  <tr><td align=right width=250>Aimed Resolution:&nbsp            </td><td align=left>$_POST[aimed_res]</td></tr>\n");
  //echo("  <tr><td align=right width=250>Min Exposure per Image:&nbsp      </td><td align=left>$_POST[min_exposure_per]</td></tr>\n");
  echo("  <tr><td align=right width=250>Additional Image:&nbsp            </td><td align=left>$additional_image</td></tr>\n");
  echo("</table>\n");
  echo("<hr><br>\n");



?>
<p><a href="#" onclick="window.parent.tb_remove(); return false">Continue</a>





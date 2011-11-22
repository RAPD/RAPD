<?php
  require('./login/config.php');
  require('./login/functions.php');

  $form_type = $_POST[form_type];

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());

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
                               '$_POST[data_dir]',
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
                               '$_POST[reference_data_id]',
                               'GLOBAL')";



  $result = @mysql_query($sql,$connection) or die(mysql_error());
  $setting_id = @mysql_insert_id($connection);

  //if the form_type is naive or preset, then add the setting_id to presets table
  if ($form_type == 'naive' or $form_type == 'preset')
  {
    echo("<h3>Form type naive or preset</h3>");
   
    //see if there is already an entry for this data_root_dir
    $sql2 = "SELECT * FROM presets WHERE data_root_dir='$_POST[data_dir]'";
    $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
    if ( mysql_num_rows($result2) == 0 )
    {
      $sql3 = "INSERT INTO presets (setting_id,beamline,data_root_dir) VALUES ($setting_id,'$_POST[beamline]','$_POST[data_dir]')";
      $result3 = @mysql_query($sql3,$connection) or die(mysql_error());
    } else {
      $sql4 = "UPDATE presets SET setting_id=$setting_id,beamline='$_POST[beamline]' WHERE data_root_dir='$_POST[data_dir]'";
      $result4 = @mysql_query($sql4,$connection) or die(mysql_error());
    }
    if (mysql_affected_rows($connection) > 0)
    {
      echo("<h3>Presets for data root diresctory $_POST[data_dir] have been saved</h3><hr>");
    }  else {
      echo("<h3>ERROR while attempting to save current settings!</h3>");
    }

 
  } elseif ($form_type == 'current') {
    //else add setting_id to the current table
    //make sure there is a line in current table for this beamline
    $sql2 = "SELECT * FROM current WHERE beamline='$_POST[beamline]'";
    $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
    if ( mysql_num_rows($result2) == 0 )
    {
      $sql3 = "INSERT INTO current (beamline) VALUES ('$_POST[beamline]')";
      $result3 = @mysql_query($sql3,$connection) or die(mysql_error());
    } 
    //now modify the current table
    $sql4 = "UPDATE current SET data_root_dir='$_POST[data_dir]', setting_id=$setting_id WHERE beamline='$_POST[beamline]'";
    $result4 = @mysql_query($sql4,$connection) or die(mysql_error());

    if (mysql_affected_rows($connection) > 0)
    {
      echo("<h3>Current settings for beamline $_POST[beamline] have been saved</h3><hr>");
    } else {
      echo("<h3>ERROR while attempting to save current settings!</h3>");
    }
  }
  echo("<table>");
  echo("  <tr><td align=right width=250>Multirpocessing:&nbsp             </td><td align=left>$_POST[multiprocessing]</td></tr>\n");
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
  echo("  <tr><td align=right width=250>Integrate:&nbsp;                  </td><td align=left>$_POST[integrate]</td></tr>\n");
  echo("</table>\n");
  echo("<hr><br>\n");

?>
<p><a href="#" onclick="window.parent.tb_remove(); return false">Continue</a>





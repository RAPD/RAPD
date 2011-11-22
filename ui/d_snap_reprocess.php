<?php

  $result_id    = $_POST[result_id];
  $start_repr   = $_POST[start_repr];
  $ip_address   = $_POST[ip];
  $request_type = $_POST[type];  
  $datadir      = $_POST[datadir];

  //$result_id    = '56137';
  //$start_repr   = 'hsnap_272br2b_99_114.img';
  //$ip_address   = '164.543.212.22';
  //$request_type = 'reprocess';
  //$datadir      = '/gpfs2/users/GU/Sazinsky_Aug10';

  require('./login/config.php');
  require('./login/functions.php');
  require('./custom.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());

  //make sure the cloud is open for business
  $sql3 = "SELECT TIMESTAMPDIFF(second,timestamp,CURRENT_TIMESTAMP) FROM cloud_state";
  $result3 = @mysql_query($sql3,$connection) or die(mysql_error()); 
  $return3 = mysql_fetch_row($result3);
  $time = $return3[0];

  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());

  //retrive the type, id and setting_id for the given result_id
  $sql1          = "SELECT type,id,setting_id,data_root_dir FROM results WHERE result_id=$result_id";
  $result1       = @mysql_query($sql1,$connection) or die(mysql_error());
  $return1       = mysql_fetch_object($result1);
  $type          = $return1 -> type;
  $id            = $return1 -> id;
  $setting_id    = $return1 -> setting_id;
  $data_root_dir = $return1 -> data_root_dir;

  //query for the settings of the retrieved data
  $sql2    = "SELECT * FROM settings WHERE setting_id='$setting_id'";
  $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
  $return2 = mysql_fetch_object($result2);

  //now grab the data to fil the form
  $multiprocessing   = $return2 -> multiprocessing;
  $spacegroup        = $return2 -> spacegroup;
  $sample_type       = $return2 -> sample_type;
  $solvent_content   = $return2 -> solvent_content;
  $susceptibility    = $return2 -> susceptibility;
  $crystal_size_x    = $return2 -> crystal_size_x;
  $crystal_size_y    = $return2 -> crystal_size_y;
  $crystal_size_z    = $return2 -> crystal_size_z;
  $a                 = $return2 -> a;
  $b                 = $return2 -> b;
  $c                 = $return2 -> c;
  $alpha             = $return2 -> alpha;
  $beta              = $return2 -> beta;
  $gamma             = $return2 -> gamma;
  $work_dir_override = $return2 -> work_dir_override;
  $work_directory    = $return2 -> work_directory;
  $beam_flip         = $return2 -> beam_flip;
  $x_beam            = $return2 -> x_beam;
  $y_beam            = $return2 -> y_beam;
  $index_hi_res      = $return2 -> index_hi_res;
  $strategy_type     = $return2 -> strategy_type;
  $best_complexity   = $return2 -> best_complexity;
  $mosflm_seg        = $return2 -> mosflm_seg;
  $mosflm_rot        = $return2 -> mosflm_rot;
  $aimed_res         = $return2 -> aimed_res;
  $min_exposure_per  = $return2 -> min_exposure_per;
  $beam_size_x       = $return2 -> beam_size_x;
  $beam_size_y       = $return2 -> beam_size_y;
  $integrate         = $return2 -> integrate;
  //$reference_data_id = $return2 -> reference_data_id;

  if ($type == 'single') {
    //accumulate images to use in two image processing
    $sql3 ="SELECT results.id,single_results.repr FROM results LEFT JOIN single_results ON (results.id=single_results.single_result_id) WHERE results.data_root_dir='$data_root_dir' AND results.result_id!=$result_id AND results.type='single' ORDER BY results.result_id DESC";
    $result3 = @mysql_query($sql3,$connection) or die(mysql_error());

    $new_reprs   = array();
    $new_reprs[] = 'None';
    if (mysql_num_rows($result3) > 0) 
    {
      while ($return3 = mysql_fetch_object($result3)) 
      {
        $repr = $return3->repr;
        if (array_search($repr,$new_reprs)) 
        {
        } else {
          $new_reprs[$return3->id] = $repr;
        }
      }
    }
  }


  //Check for reference data currently active        
  $sql4 = "SELECT setting_id,reference_data_id FROM settings WHERE data_root_dir='$datadir' AND setting_type='GLOBAL' ORDER BY setting_id DESC LIMIT 1";
  $result4 = @mysql_query($sql4,$connection) or die(mysql_error());
  if (mysql_num_rows($result4) > 0) 
  {
    while ($return4 = mysql_fetch_object($result4)) 
    {
      $ref_data_id = $return4->reference_data_id;  
    }
  } else {
    $ref_data_id = NULL;
  }
?>

<html>
  <head>
    <style type="text/css">
      h3 {
        color: green;
      }
    </style>
  </head>

  <body>
  <div id="content">
  <form id='myForm' action='./d_add_reprocess.php' method='POST'>
  <!-- HIDDEN VARIABLES POSTED -->
  <input type="hidden" id="form_request_type" name="request_type" value="<? echo($request_type);?>">
  <input type="hidden" id="form_original_result_id" name="original_result_id" value="<? echo($result_id);?>">
  <input type="hidden" id="form_original_type"      value="<? echo($type);?>">
  <input type="hidden" id="form_original_id"        value="<? echo($id);?>">
  <input type="hidden" id="form_data_root_dir"      value="<? echo($data_root_dir);?>">
  <input type="hidden" id="form_ip_address"         value="<? echo($ip_address);?>">
  <input type="hidden" id="form_multiprocessing"    value="<? echo($multiprocessing);?>">
  <input type="hidden" id="form_work_dir_override"  value="<? echo($work_dir_override);?>">
  <input type="hidden" id="form_work_directory"     value="<? echo($work_directory);?>">
  <input type="hidden" id="form_susceptibility" value="<? echo($susceptibility);?>">
  <input type="hidden" id="form_crystal_size_x" value="<? echo($crystal_size_x);?>">
  <input type="hidden" id="form_crystal_size_y" value="<? echo($crystal_size_y);?>">
  <input type="hidden" id="form_crystal_size_z" value="<? echo($crystal_size_z);?>">
  <input type="hidden" id="form_a" value="<? echo($a);?>">
  <input type="hidden" id="form_b" value="<? echo($b);?>">
  <input type="hidden" id="form_c" value="<? echo($c);?>">
  <input type="hidden" id="form_alpha" value="<? echo($alpha);?>">
  <input type="hidden" id="form_beta" value="<? echo($beta);?>">
  <input type="hidden" id="form_gamma" value="<? echo($gamma);?>">
  <input type="hidden" id="form_index_hi_res" value="<? echo($index_hi_res);?>">
  <input type="hidden" id="form_aimed_res" value="<? echo($aimed_res);?>">
  <input type="hidden" id="form_min_exposure_per" value="<? echo($min_exposure_per);?>">
  <input type="hidden" id="form_beam_size_x" value="<? echo($beam_size_x);?>">
  <input type="hidden" id="form_beam_size_y" value="<? echo($beam_size_y);?>">
  <input type="hidden" id="form_integrate" value="<? echo($integrate);?>">
<!--
  <table>
    <tr>
      <td align='center' width='550'>
        <h3>Change Settings For Reprocessing <?echo($start_repr);?></h3>
      </td>
    </tr>
  </table>
-->
  <table>
    <tr>
      <td align="right" width="175">
        Spacegroup Overide 
      </td>
      <td>
        <select name="spacegroup" id="form_spacegroup">
<?php
  if ($spacegroup == "None") {
    echo("          <option value='None' selected='selected'>None</option>\n");
  } else { 
    echo("          <option value='None'>None</option>\n");
  }
  foreach ($bravais as $b) {
    if ($spacegroup == $intl2std[$b]) {
      echo("          <option value='$intl2std[$b]' selected='$intl2std[$b]'>$intl2std[$b]</option>\n");
    } else {
      echo("          <option value='$intl2std[$b]'>$intl2std[$b]</option>\n");
    }
    foreach ($subgroups[$b] as $s) {
      if ($spacegroup == $intl2std[$s]) {
        echo("          <option value='$intl2std[$s]' selected='$intl2std[$s]'>$intl2std[$s]</option>\n");
      } else {
        echo("          <option value='$intl2std[$s]'>$intl2std[$s] &nbsp;&nbsp;</option>\n");
      }
    }
  }

?>
        </select>
      </td>
    </tr>
  </table>
  <table>
    <tr>
      <td align="right" width="175">
        Sample Type
      </td>
      <td>
        <select name="sample_type" id="form_sample_type">
<?
  foreach ($types as $t) {
    if ($sample_type == $t) {
      echo("          <option value='$t' selected='$t'>$t</option>\n");
    } else {
      echo("          <option value='$t'>$t &nbsp;&nbsp;</option>\n");
    }
  }
?>
        </select>
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        Solvent Fraction (0.00-1.00)
      </td>
      <td>
        <input type="text" name="solvent_content" id="form_solvent_content" value="<?echo($solvent_content);?>" size=5> 
      </td>
    </tr>
<!--
    <tr>
      <td align="right" width="175">
        Radiation Susceptibility
      </td>
      <td>
        <input type="text" name="susceptibility" value="<?echo($susceptibility);?>" size=5> 
      </td>
    </tr>
-->
  </table>
<!--
  <table>
    <tr>
      <td align="right" width="175">
        Crystal Size (um) X
      </td>
      <td>
        <input type="text" name="crystal_size_x" value="<?echo($crystal_size_x);?>" size=5>
      </td>
      <td>Y</td>
      <td>
        <input type="text" name="crystal_size_y" value="<?echo($crystal_size_y);?>" size=5>
      </td>
      <td>Z</td>
      <td>
        <input type="text" name="crystal_size_z" value="<?echo($crystal_size_z);?>" size=5>
      </td>
    </tr>
  </table>
-->
<!--
  <table>
    <tr>
      <td align="right" width="175">
        Cell Parameters a
      </td>
      <td>
        <input type="text" name="a" value="<?echo($a);?>" size=5>
      </td>
      <td>b</td>
      <td>
        <input type="text" name="b" value="<?echo($b_cell);?>" size=5>
      </td>
      <td>c</td>
      <td>
        <input type="text" name="c" value="<?echo($c);?>" size=5>
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        &alpha 
      </td>
      <td>
        <input type="text" name="alpha" value="<?echo($alpha);?>" size=5>
      </td>
      <td>&beta</td>
      <td>
        <input type="text" name="beta" value="<?echo($beta);?>" size=5>
      </td>
      <td>&gamma</td>
      <td>
        <input type="text" name="gamma" value="<?echo($gamma);?>" size=5>
      </td>
    </tr>
  </table>
-->
  <table>
    <tr>
      <td align="right" width="175">
        Flip Beam Coordinates
      </td>
      <td>
        <select name="beam_flip" id="form_beam_flip">
<?
  if ($beam_flip == 'True') {
      echo("          <option value='True' selected='True'>True</option>\n");
      echo("          <option value='False'>False</option>\n");
    } else {
      echo("          <option value='True'>True</option>\n");
      echo("          <option value='False' selected='False'>False &nbsp;&nbsp;</option>\n");
    }
?>
        </select>
      </td>
    </tr>
  </table>
  <table>
    <tr>
      <td align="right" width="175">
        Override Beam X
      </td>
      <td>
        <input type="text" id="form_x_beam" name="x_beam" value="<? echo $x_beam; ?>" size=5>
      </td>
      <td width=5>
        Y
      </td>
      <td>
        <input type="text" id="form_y_beam" name="y_beam" value="<? echo $y_beam; ?>" size=5>
      </td>
    </tr>
  </table>


  <table>
    <tr>
      <td align='center' width='350'>
        
      </td>
    </tr>
  </table>
  <table>
<!--
    <tr>
      <td align="right" width="175">
        Hi Res Cutoff - Peak Picking
      </td>
      <td>
        <input type="text" name="index_hi_res" value="<? echo $index_hi_res; ?>" size=5> 
      </td>
    </tr> 
-->
    <tr>
      <td align="right" width="175">
        Strategy type
      </td>
      <td width="75">
        <select name="strategy_type" id="form_strategy_type">
<?
  if ($strategy_type == 'mosflm') {
      echo("          <option value='best'>Best</option>\n");
      echo("          <option value='mosflm' selected='mosflm'>Mosflm</option>\n");
  } else {
      echo("          <option value='best' selected='best'>Best</option>\n");
      echo("          <option value='mosflm'>Mosflm</option>\n");
    }
?>
        </select>
      </td>
    </tr>


    <tr>
      <td align="right" width="175">
        Best Complexity
      </td>
      <td>
        <select name="best_complexity" id="form_best_complexity">
<?
  foreach ($best_set as $b) {
    if ($best_complexity == $b) {
      echo("          <option value='$b' selected='$b'>$b</option>\n");
    } else {
      echo("          <option value='$b'>$b</option>\n");
    }
  }
?>
        </select>
      </td>
    </tr> 
  </table>

  <table>
    <tr>
      <td align="right" width="175">
        Mosflm Segments
      </td>
      <td width="75">
        <select name="mosflm_seg" id="form_mosflm_seg">
<?
  foreach ($seg_set as $s) {
    if ($mosflm_seg == $s) {
      echo("          <option value='$s' selected='$s'>$s</option>\n");
    } else {
      echo("          <option value='$s'>$s</option>\n");
    }
  }
?>
        </select>
      </td>
      <td>&nbsp;Rotation Range</td>
      <td>
        <input type="text" name="mosflm_rot" id="form_mosflm_rot" value="<?echo($mosflm_rot);?>" size=5>
      </td>
  </table>

<!--
  <table>
    <tr>
      <td align="right" width="175">
        Aimed Resolution 
      </td>
      <td>
        <input type="text" name="aimed_res" value="<? echo $aimed_res; ?>" size=5>
      </td>
    </tr>
  </table>
  <table>
    <tr>
      <td align="right" width="175">
        Min Exposure per Image
      </td>
      <td>
        <input type="text" name="min_exposure_per" value="<? echo $min_exposure_per; ?>" size=5> 
      </td>
    </tr>
  </table>
-->
<? if ($type == 'single') {
     echo("  <table>\n");
     echo("    <tr>\n");
     echo("      <td align='right' width='175'>\n");
     echo("        Additional Image\n");
     echo("      </td>\n");
     echo("      <td>\n");
     echo("        <select name='additional_image' id='form_additional_image'>\n");
     foreach ($new_reprs as $my_id => $repr) {
       echo("        <option value='$my_id'>$repr &nbsp;&nbsp;</option>\n");
     } 
     echo("        </select>\n");
     echo("      </td>\n");
     echo("    </tr>\n");
     echo("  </table>\n");
   }

   if (! is_null($ref_data_id))
   {
?>
  <table>
    <tr>
      <td align='right' width='175'>
        Include previous data
      </td>
      <td>
        <select name='reference_data' id="form_reference_data">
          <option value='<?echo($ref_data_id);?>'>Current &nbsp;&nbsp;</option>
          <option value='None'>None</option>
        </select>
      </td>
    </tr>
  </table>
<?
   } else {
     echo("  <input type='hidden' name='reference_data' id='form_reference_data' value='NULL'>\n");

   }  //end if
?>
</form>
</div>
</body>
</html>

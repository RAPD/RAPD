<?php

  $result_id    = $_GET[result_id];
  $start_repr   = $_GET[start_repr];
  $ip_address   = $_GET[ip];
  $request_type = $_GET[type];  
 
  require('./login/config.php');
  require('./login/functions.php');
  require('./custom.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
//  $db = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());

  //make sure the cloud is open for business
//  $sql3 = "SELECT TIMESTAMPDIFF(second,timestamp,CURRENT_TIMESTAMP) FROM cloud_state";
//  $result3 = @mysql_query($sql3,$connection) or die(mysql_error()); 
//  $return3 = mysql_fetch_row($result3);
//  $time = $return3[0];

  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());

  //retrieve the type, id and setting_id for the given result_id
  $sql1          = "SELECT type,id,setting_id,data_root_dir FROM results WHERE result_id=$result_id";
  $result1       = @mysql_query($sql1,$connection) or die(mysql_error());
  $return1       = mysql_fetch_object($result1);
  $type          = $return1 -> type;
  $id            = $return1 -> id;
  $setting_id    = $return1 -> setting_id;
  $data_root_dir = $return1 -> data_root_dir;

  //query for the settings of the retrieved data
//  $sql2    = "SELECT * FROM settings WHERE setting_id='$setting_id'";
//  $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
//  $return2 = mysql_fetch_object($result2);

  if ($type == 'single') {
    //accumulate images to use in two image processing
    $sql3 ="SELECT id FROM results WHERE data_root_dir='$data_root_dir' AND result_id!=$result_id AND type='single' ORDER BY result_id";
    $result3 = @mysql_query($sql3,$connection) or die(mysql_error());

    $new_reprs   = array();
    $new_ids     = array();
    $new_reprs[] = 'None';
    $new_ids     = 'None';
    if (mysql_num_rows($result3) > 0) {
      while ($return3 = mysql_fetch_object($result3)) {
        $single_result_id = $return3 -> id;
        //$new_ids[] = $single_result_id;
        //now get the image names
        $sql4    = "SELECT repr FROM single_results WHERE single_result_id=$single_result_id";
        $result4 = @mysql_query($sql4,$connection) or die(mysql_error());
        $return4 =  mysql_fetch_object($result4);
        $repr = $return4 -> repr;
        if (array_search($repr,$new_reprs)) {
        } else {
          $new_reprs[$single_result_id] = $repr;
        }
      }
    }
  }
  elseif ($type == 'pair') {
    
    pass;
  }
?>

<html>
  <head>
    <style type="text/css">
      h3 {
        color: green;
      }
    </style>
    <script type="text/javascript">
      jQuery(function($){
        $('#myForm').submit(function(){ 
          $.post($(this).attr('action'), $(this).serialize(), function(html) { 
            $('#content').html(html)
          })
          return false
        })
      })
    </script>


  </head>

  <body>
  <div id="content">
  <form id='myForm' action='./add_reprocess.php' method='POST'>
  <!-- HIDDEN VARIABLES POSTED -->
  <input type="hidden" name="request_type"       value="<? echo($request_type);?>">
  <input type="hidden" name="original_result_id" value="<? echo($result_id);?>">
  <input type="hidden" name="original_type"      value="<? echo($type);?>">
  <input type="hidden" name="original_id"        value="<? echo($id);?>">
  <input type="hidden" name="data_root_dir"      value="<? echo($data_root_dir);?>">
  <input type="hidden" name="ip_address"         value="<? echo($ip_address);?>">
  <input type="hidden" name="multiprocessing"    value="<? echo($multiprocessing);?>">
  <input type="hidden" name="work_dir_override"  value="<? echo($work_dir_override);?>">
  <input type="hidden" name="work_directory"     value="<? echo($work_directory);?>">
  <table>
    <tr>
      <td align='center' width='550'>
        <h3>Change Settings For Reprocessing <?echo($start_repr);?></h3>
      </td>
    </tr>
    </table>
  <table>
    <tr>
      <td align="right" width="175">
        Spacegroup Overide 
      </td>
      <td>
        <select name="spacegroup">
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
        echo("          <option value='$intl2std[$s]'>$intl2std[$s]</option>\n");
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
        <select name="sample_type">
<?
  foreach ($types as $t) {
    if ($sample_type == $t) {
      echo("          <option value='$t' selected='$t'>$t</option>\n");
    } else {
      echo("          <option value='$t'>$t</option>\n");
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
        <input type="text" name="solvent_content" value="<?echo($solvent_content);?>" size=5> 
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        Radiation Susceptibility
      </td>
      <td>
        <input type="text" name="susceptibility" value="<?echo($susceptibility);?>" size=5> 
      </td>
    </tr>
  </table>
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

  <table>
    <tr>
      <td align="right" width="175">
        Flip Beam Coordinates
      </td>
      <td>
        <select name="beam_flip">
<?
  if ($beam_flip == 'True') {
      echo("          <option value='True' selected='True'>True</option>\n");
      echo("          <option value='False'>False</option>\n");
    } else {
      echo("          <option value='True'>True</option>\n");
      echo("          <option value='False' selected='False'>False</option>\n");
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
        <input type="text" name="x_beam" value="<? echo $x_beam; ?>" size=5>
      </td>
      <td width=5>
        Y
      </td>
      <td>
        <input type="text" name="y_beam" value="<? echo $y_beam; ?>" size=5>
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
    <tr>
      <td align="right" width="175">
        Hi Res Cutoff - Peak Picking
      </td>
      <td>
        <input type="text" name="index_hi_res" value="<? echo $index_hi_res; ?>" size=5> 
      </td>
    </tr> 


    <tr>
      <td align="right" width="175">
        Strategy type
      </td>
      <td width="75">
        <select name="strategy_type">
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
        <select name="best_complexity">
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
        <select name="mosflm_seg">
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
        <input type="text" name="mosflm_rot" value="<?echo($mosflm_rot);?>" size=5>
      </td>
  </table>


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

<? if ($type == 'single') {
     echo("  <table>\n");
     echo("    <tr>\n");
     echo("      <td align='right' width='175'>\n");
     echo("        Additional Image\n");
     echo("      </td>\n");
     echo("      <td>\n");
     echo("        <select name='additional_image'>\n");
     foreach ($new_reprs as $my_id => $repr) {
       echo("        <option value='$my_id'>$repr</option>\n");
     } 
     echo("        </select>\n");
     echo("      </td>\n");
     echo("    </tr>\n");
     echo("  </table>\n");
   }
?>


  <table align="center">
    <tr>
      <td width="175">&nbsp</td>
      <td>
        <input type="submit" value="REPROCESS">
      </td>
    </tr>
  </table>


</form>
</div>
</body>
</html>

<?php
  //session_start();

  $result_id    = $_POST[result_id];
  $start_repr   = $_POST[start_repr];
 
  require('./login/config.php');
  require('./login/functions.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
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
  $spacegroup        = $return2 -> spacegroup;
  $sample_type       = $return2 -> sample_type;
  $solvent_content   = $return2 -> solvent_content;
  $susceptibility    = $return2 -> susceptibility;
  $crystal_size_x    = $return2 -> crystal_size_x;
  $crystal_size_y    = $return2 -> crystal_size_y;
  $crystal_size_z    = $return2 -> crystal_size_z;
  $a                 = $return2 -> a;
  $b_cell            = $return2 -> b;
  $c                 = $return2 -> c;
  $alpha             = $return2 -> alpha;
  $beta              = $return2 -> beta;
  $gamma             = $return2 -> gamma;
  $beam_flip         = $return2 -> beam_flip;
  $x_beam            = $return2 -> x_beam;
  $y_beam            = $return2 -> y_beam;
  $index_hi_res      = $return2 -> index_hi_res;
  $strategy_type     = $return2 -> strategy_type;
  $mosflm_seg        = $return2 -> mosflm_seg;
  $mosflm_rot        = $return2 -> mosflm_rot;
  $best_complexity   = $return2 -> best_complexity;
  $aimed_res         = $return2 -> aimed_res;
  $min_exposure_per  = $return2 -> min_exposure_per;
?>

<html>
  <body>
  <div id="content">
  <div id='settings_table'>
  <table>
    <tr>
      <td style="font-size:1em;" align="right" width='250'>
        Spacegroup Overide 
      </td>
      <td style="font-size:1em; padding:5px; color: green;">
        <?php echo $spacegroup; ?>
      </td>
    </tr>
  </table>
  <table>
    <tr>
      <td style="font-size:1em;" align="right" width='250'>
        Sample Type
      </td>
      <td style="font-size:1em; padding:5px; color: green;">
        <? echo $sample_type; ?>
      </td>
    </tr>
    <tr>
      <td style="font-size:1em;" align="right" width='250'>
        Solvent Fraction (0.00-1.00)
      </td>
      <td style="font-size:1em; padding:5px; color: green;">
        <?echo($solvent_content);?> 
      </td>
    </tr>
<!--
    <tr>
      <td style="font-size:1em;" align="right" width='250'>
        Radiation Susceptibility
      </td>
      <td style="font-size:1em; padding:5px; color: green;">
        <?echo($susceptibility);?> 
      </td>
    </tr>
-->
  </table>
<!--
  <table>
    <tr>
      <td style="font-size:1em;" align="right" width='250'>
        Crystal Size (um) X
      </td>
      <td style="font-size:1em; padding:5px;">
        <? echo($crystal_size_x); ?>
      </td>
      <td style="font-size:1em;">Y</td>
      <td style="font-size:1em; padding:5px;">
        <? echo($crystal_size_y); ?>
      </td>
      <td style="font-size:1em;">Z</td>
      <td style="font-size:1em; padding:5px;">
        <? echo($crystal_size_z); ?>
      </td>
    </tr>
  </table>
-->
<!--
  <table>
    <tr>
      <td style="font-size:1em;" align="right" width='250'>
        Cell Parameters a
      </td>
      <td style="font-size:1em; padding:5px; color:green;">
        <?echo($a);?>
      </td>
      <td style="font-size:1em;">b</td>
      <td style="font-size:1em; padding:5px; color:green;">
        <?echo($b_cell);?>
      </td>
      <td style="font-size:1em;">c</td>
      <td style="font-size:1em; padding:5px; color:green;">
        <?echo($c);?>
      </td>
    </tr>
    <tr>
      <td style="font-size:1em;" align="right" width='250'>
        &alpha 
      </td>
      <td style="font-size:1em; padding:5px; color:green;">
        <?echo($alpha);?>
      </td>
      <td style="font-size:1em;">&beta</td>
      <td style="font-size:1em; padding:5px; color:green;">
        <?echo($beta);?>
      </td>
      <td style="font-size:1em;">&gamma</td>
      <td style="font-size:1em; padding:5px; color:green;">
        <?echo($gamma);?>
      </td>
    </tr>
  </table>
-->
<?
  if ($beam_flip == 'True')
  {
?>
  <table>
    <tr>
      <td style="font-size:1em;" align="right" width='250'>
        Flip Beam Coordinates
      </td>
      <td style="font-size:1em; padding:5px; color:green;">
        <?echo $beam_flip;?>
      </td>
    </tr>
  </table>
<?
  }
  if ($x_beam > 0)
  {
?>
  <table>
    <tr>
      <td style="font-size:1em;" align="right" width='250'>
        Override Beam X
      </td>
      <td style="font-size:1em; padding:5px; color:green;">
        <? echo $x_beam; ?>
      </td>
      <td style="font-size:1em;" width=5>
        Y
      </td>
      <td style="font-size:1em; padding:5px; color:green;">
        <? echo $y_beam; ?>
      </td>
    </tr>
  </table>
<?
  }
?>

  <table>
    <tr>
      <td style="font-size:1em;" align='center' width='350'>
        
      </td>
    </tr>
  </table>
  <table>
<!--
    <tr>
      <td style="font-size:1em;" align="right" width='250'>
        Hi Res Cutoff - Peak Picking
      </td>
      <td style="font-size:1em; padding:5px; color:green;">
        <? echo $index_hi_res; ?> 
      </td>
    </tr> 
-->
    <tr>
      <td style="font-size:1em;" align="right" width='250'>
        Strategy Type      
      </td>
      <td style="font-size:1em; padding:5px; color:green;">
        <?echo $strategy_type;?>
      </td>
    </tr>
<?  
    if ($strategy_type == 'best')
    {
?>
    <tr>
      <td style="font-size:1em;" align="right" width='250'>
        Strategy Complexity
      </td>
      <td style="font-size:1em; padding:5px; color:green;">
        <?echo $best_complexity;?>
      </td>
    </tr>
<?  } else if ($strategy_type == 'mosflm')
    {
?>
    <tr>
      <td style="font-size:1em;" align="right" width='250'>
        Mosflm segments
      </td>
      <td style="font-size:1em; padding:5px; color:green;">
        <?echo $mosflm_seg;?>
      </td>
    </tr>
    <tr>
      <td style="font-size:1em;" align="right" width='250'>
        Mosflm total rotation
      </td>
      <td style="font-size:1em; padding:5px; color:green;">
        <?echo $mosflm_rot;?>
      </td>
    </tr>

<?  }  ?>


<!--
    <tr>
      <td style="font-size:1em;" align="right" width='250'>
        Aimed Resolution 
      </td>
      <td style="font-size:1em; padding:5px; color:green;">
        <? echo $aimed_res; ?>
      </td>
    </tr>
-->
  </table>
<!--
  <table>
    <tr>
      <td align="right" width='250' style="font-size:1em;">
        Min Exposure per Image
      </td>
      <td style="font-size:1em; padding:5px; color:green;">
        <? echo $min_exposure_per; ?> 
      </td>
    </tr>
  </table>
-->
</div>
</div>
</body>
</html>

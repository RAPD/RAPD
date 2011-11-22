<?php 
  require('./login/config.php');
  require('./login/functions.php');

  //Start handling the POST
  $datadir = $_GET[datadir];
  $lastid  = $_GET[id];
  //$datadir = "/gpfs3/users/necat/FM_Aug10";
  //$lastid = 0;

  //$count = 0;

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db(rapd_data,$connection)or die(mysql_error());        

  //build and issue the query
  $sql ="SELECT result_id,type,id FROM results WHERE data_root_dir='$datadir' AND result_id>$lastid ORDER BY result_id";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
 
  $arr = array();
  if (mysql_num_rows($result) > 0) {

    while ($sql = mysql_fetch_object($result)) {
      
      //if ($count > 19) { break; }

      $res_id = $sql -> result_id;
      $type   = $sql -> type;
      $id     = $sql -> id; 
                         
      if ($type == 'single')
      {
        //echo("SELECT * FROM single_results WHERE labelit_status='SUCCESS' AND single_result_id='$id' AND summary_stac!='None'");
        $sql2    = "SELECT * FROM single_results WHERE labelit_status='SUCCESS' AND single_result_id='$id' AND summary_stac='None'";
        $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
        if (mysql_num_rows($result2) > 0) 
        {
          $return2 = mysql_fetch_object($result2);

          $succ       = $return2 -> labelit_status;
          $repr       = $return2 -> repr;
          $spacegroup = $return2 -> labelit_spacegroup;
          $a          = $return2 -> labelit_a; 
          $b          = $return2 -> labelit_b;
          $c          = $return2 -> labelit_c;
          $alpha      = $return2 -> labelit_alpha;
          $beta       = $return2 -> labelit_beta;
          $gamma      = $return2 -> labelit_gamma;
          $mosaicity  = $return2 -> labelit_mosaicity;
          $metric     = $return2 -> labelit_metric;
          $res        = $return2 -> labelit_res;
          $spots_fit  = $return2 -> labelit_spots_fit;
          $ice_rings  = $return2 -> distl_ice_rings;
          $inres_spot = $return2 -> distl_spots_in_res;
          $rmsr       = $return2 -> labelit_rmsd;
        

          if ($succ == "SUCCESS")
          {
            //$count = $count + 1;
            $spots_metric = $spots_fit/$inres_spot;
            $webice = number_format((1.0 - (0.7*exp(-4/$res)) - (1.5*$rmsr) - (0.2*$mosaicity)),3); 
  
            $arr[] = $repr;
            $arr[] = $spacegroup;
            $arr[] = $a;
            $arr[] = $b;
            $arr[] = $c;
            $arr[] = $alpha;
            $arr[] = $beta;
            $arr[] = $gamma;
            $arr[] = $mosaicity;
            $arr[] = $res;
            $arr[] = $webice;
            $arr[] = $res_id;
          }
        }
      }
      elseif ($type == 'pair')
      {
        //echo("PAIR pair_result_id=$id\n");
        $sql2    = "SELECT * FROM pair_results WHERE labelit_status='SUCCESS' AND pair_result_id='$id'";
        $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
        if (mysql_num_rows($result2) > 0)
        {
          $return2 = mysql_fetch_object($result2);

          $succ       = $return2 -> labelit_status;
          $spacegroup = $return2 -> labelit_spacegroup;
          $repr       = $return2 -> repr;
          $a          = $return2 -> labelit_a;
          $b          = $return2 -> labelit_b;
          $c          = $return2 -> labelit_c;
          $alpha      = $return2 -> labelit_alpha;
          $beta       = $return2 -> labelit_beta;
          $gamma      = $return2 -> labelit_gamma;
          $mosaicity  = $return2 -> labelit_mosaicity;
          $metric     = $return2 -> labelit_metric;
          $res        = $return2 -> labelit_res;
          $spots_fit  = $return2 -> labelit_spots_fit;
          $ice_rings1 = $return2 -> distl_ice_rings_1;
          $ice_rings2 = $return2 -> distl_ice_rings_2;
          $tot_spot1  = $return2 -> distl_total_spots_1;
          $tot_spot2  = $return2 -> distl_total_spots_2;
          $good_spot1 = $return2 -> distl_good_bragg_spots_1;
          $good_spot2 = $return2 -> distl_good_bragg_spots_2;
          $rmsr       = $return2 -> labelit_rmsd;
  
          if ($succ == "SUCCESS")
          {
            //$count = $count + 1;
            $spots_metric = $spots_fit / ( $tot_spot1+ $tot_spot2) ;
            $webice = number_format((1.0 - (0.7*exp(-4/$res)) - (1.5*$rmsr) - (0.2*$mosaicity)),3);
  
            $arr[] = $repr;
            $arr[] = $spacegroup;
            $arr[] = $a;
            $arr[] = $b;
            $arr[] = $c;
            $arr[] = $alpha;
            $arr[] = $beta;
            $arr[] = $gamma;
            $arr[] = $mosaicity;
            $arr[] = $res;
            $arr[] = $webice;
            $arr[] = $res_id;
          }
        }
      }
    }
  } else {
    $arr[] = $res_id;
  }

  //Encode in JSON
  $out = json_encode($arr);
  print $out;  
?>


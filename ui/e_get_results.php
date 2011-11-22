<?php 
  require('./login/config.php');
  require('./login/functions.php');

  //Start handling the POST
  $datadir = $_GET[datadir];
  $lastid  = $_GET[id];
  //$datadir = "/gpfs1/users/necat/Feb02_2008_test";
  //$lastid = 0;
  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db(rapd_data,$connection)or die(mysql_error());        

  //build and issue the query
  $sql ="SELECT result_id,type,id,process_id,display FROM results WHERE data_root_dir='$datadir' AND result_id>$lastid ORDER BY result_id";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
  
  $arr = array();
  if (mysql_num_rows($result) > 0) {
    while ($sql = mysql_fetch_object($result)) {
      $res_id     = $sql -> result_id;
      $type       = $sql -> type;
      $id         = $sql -> id; 
      $process_id = $sql -> process_id;
      $display    = $sql -> display;

      if ($type == 'single')
      {
        $sql2    = "SELECT repr,type,best_norm_status,mosflm_norm_status,summary_stac,timestamp FROM single_results WHERE single_result_id='$id'";
        $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
        $sql2    = mysql_fetch_object($result2);
        $repr    = $sql2 -> repr;
        $type    = $sql2 -> type;
        $bstatus = $sql2 -> best_norm_status;  
        $mstatus = $sql2 -> mosflm_norm_status;
        $stac    = $sql2 -> summary_stac;
        $time    = $sql2 -> timestamp;
        $arr[] = "single";
        $arr[] = $display;
        $arr[] = $process_id;
        $arr[] = "<a class=\"image single $res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>\n";
        if (! (is_null($stac) or ($stac == 'None')))
        { 
          $arr[] = 'STAC';
        }
        elseif ($bstatus == 'SUCCESS')
        {
          if ($type == 'reprocess')
          {
            $arr[] = 'REPROCESS';
          }
          else if ($type == 'ref_strat')
          {
            $arr[] = 'REF_STRAT';
          }
          else
          {
            $arr[] = $bstatus;
          }
        }
        elseif ($mstatus == 'SUCCESS')
        {          
          if ($type == 'reprocess')
          {
            $arr[] = 'REPROCESS';
          }
          else if ($type == 'ref_strat')
          {
            $arr[] = 'REF_STRAT';
          }
          else
          {
            $arr[] = $mstatus;
          }
        }
        else
        {
          $arr[] = 'FAILED';
        }
      }
      elseif ($type == 'pair')
      {
        $sql2     = "SELECT repr,type,best_norm_status,mosflm_norm_status,timestamp FROM pair_results WHERE pair_result_id='$id'";
        $result2  = @mysql_query($sql2,$connection) or die(mysql_error());
        $sql2     = mysql_fetch_object($result2);
        $repr     = $sql2 -> repr;
        $type     = $sql2 -> type;
        $bstatus  = $sql2 -> best_norm_status;
        $mstatus  = $sql2 -> mosflm_norm_status;
        $time     = $sql2 -> timestamp;

        $arr[] = "pair";
        $arr[] = $display;
        $arr[] = $process_id;
        $arr[] = "<a class=\"image pair $res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>\n";
        //$arr[] = "<a class=\"image pair $res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>\n";
        if ($bstatus == 'SUCCESS')
        {
          if ($type == 'reprocess')
          {
            $arr[] = 'REPROCESS';
          }
          else
          {
            $arr[] = $bstatus;
          }
        }
        elseif ($mstatus == 'SUCCESS')
        {
          if ($type == 'reprocess')
          {
            $arr[] = 'REPROCESS';
          }
          else
          {
            $arr[] = $mstatus;
          }
        }
        else
        {
          $arr[] = 'FAILED';
        }
      }
      elseif ($type == 'integrate')
      {
        $sql2    = "SELECT integrate_status,repr,timestamp FROM integrate_results WHERE integrate_result_id='$id'";
        $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
        $sql2    = mysql_fetch_object($result2);
        $status  = $sql2->integrate_status;
        $repr    = $sql2->repr;
        $time    = $sql2->timestamp;
        $arr[]   = "run";
        $arr[]   = $display;
        $arr[]   = $process_id;
        $arr[]   = "<a class=\"image integrate $res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>\n";
        //$arr[]   = "<a class=\"image integrate $res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>\n";
        if ($status == 'SUCCESS' or $status == 'SUCCESS')
        {
          $arr[] = 'SUCCESS';
        }
        else 
        {
          $arr[] = 'FAILED'; 
        }
      }
    }
    $arr[] = $res_id;
  }
  else {
    $arr[] = $lastid;
  }

  //Encode in JSON
  $out = json_encode($arr);
  print $out;  
?>


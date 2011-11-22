<?php 
  require('./login/config.php');
  require('./login/functions.php');

  //Start handling the POST
  $datadir = $_GET[datadir];
  $lastid  = $_GET[id];
  $lasttimestamp = $_GET[timestamp];
  //$datadir = "/gpfs3/users/necat/Guest_Apr11";
	//$datadir = "/gpfs6/users/columbia/Mancia_Aug11B";
 	//$lastid = 0;
  //$lasttimestamp = '0';

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db(rapd_data,$connection)or die(mysql_error());        

  //build and issue the query
  $sql ="SELECT result_id,type,id,process_id,display,timestamp FROM results WHERE data_root_dir='$datadir' AND timestamp>'$lasttimestamp' ORDER BY timestamp";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
  
  $arr = array();
  if (mysql_num_rows($result) > 0) {
    while ($sql = mysql_fetch_object($result)) {
      $res_id     = $sql -> result_id;
      $type       = $sql -> type;
      $id         = $sql -> id; 
      $process_id = $sql -> process_id;
      $display    = $sql -> display;
      $timestamp  = $sql -> timestamp;

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
        // Append the timestamp
        $arr[] = $time;
        $arr[] = $res_id;
      }
      elseif ($type == 'pair')
      {
        $sql2     = "SELECT repr,type,best_norm_status,mosflm_norm_status,summary_stac,timestamp FROM pair_results WHERE pair_result_id='$id'";
        $result2  = @mysql_query($sql2,$connection) or die(mysql_error());
        $sql2     = mysql_fetch_object($result2);
        $repr     = $sql2 -> repr;
        $type     = $sql2 -> type;
        $bstatus  = $sql2 -> best_norm_status;
        $mstatus  = $sql2 -> mosflm_norm_status;
		$stac     = $sql2 -> summary_stac;
        $time     = $sql2 -> timestamp;

        $arr[] = "pair";
        $arr[] = $display;
        $arr[] = $process_id;
        $arr[] = "<a class=\"image pair $res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>\n";
        //$arr[] = "<a class=\"image pair $res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>\n";
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
        // Append the timestamp
        $arr[] = $time; 
        $arr[] = $res_id;
      }
      elseif ($type == 'integrate')
      {
        $sql2    = "SELECT integrate_status,type,repr,solved,timestamp,TIMESTAMPDIFF(SECOND,timestamp,NOW()) AS result_age FROM integrate_results WHERE integrate_result_id='$id'";
        $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
        $sql2    = mysql_fetch_object($result2);
        $status  = $sql2->integrate_status;
		$type    = $sql2->type;
        $repr    = $sql2->repr;
        $solved  = $sql2->solved;
        $time    = $sql2->timestamp;
        $result_age = $sql2->result_age;
        $arr[]   = "run";
        $arr[]   = $display;
        $arr[]   = $process_id;
        if ($status == 'SUCCESS')
        {
        	if ($solved == 'Yes')
        	{
				$arr[]   = "<a id=\"$res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr<img id=\"$res_id-more-icon\" src=\"./css/magnifying-glass-icon.png\"></a>";
        	}
        	else 
        	{
				$arr[]   = "<a id=\"$res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
        	}		
			if ($type == 'refastint')
			{
				$arr[] = 'REFASTINT';
			}
			else if ($type == 'rexia2')
			{
				$arr[] = 'REXIA2';
			}
			else
			{
				$arr[] = 'SUCCESS';
			}
        }
        elseif ($status == 'WORKING')
        {
          if ($result_age < 1800) 
          {
              $arr[] = "<a id=\"$res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\"><img id=\"$res_id-gif\" src=\"./css/images/ajax-loader.gif\">$repr</a>";
              $arr[] = 'WORKING';
          }
          else
          {
            $arr[]   = "<a id=\"$res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
            $arr[] = 'FINISHED';
          }
        }
        elseif ($status == 'FAILED')
        {
          $arr[] = "<a id=\"$res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
          $arr[] = 'FAILED';
        }
	else 
	{
	    $arr[] = "<a id=\"$res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">Error</a>";
      $arr[] = 'ERROR';
	}
        $arr[] = $time;
        $arr[] = $res_id;
      }
      elseif ($type == 'merge')
      {
        $sql2    = "SELECT merge_status,repr,solved,timestamp,TIMESTAMPDIFF(SECOND,timestamp,NOW()) AS result_age FROM merge_results WHERE merge_result_id='$id'";
        $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
        $sql2    = mysql_fetch_object($result2);
        $status  = $sql2->merge_status;
        $repr    = $sql2->repr;
        $solved  = $sql2->solved;
        $time    = $sql2->timestamp;
        $result_age = $sql2->result_age;
        $arr[]   = "merge";
        $arr[]   = $display;
        $arr[]   = $process_id;
        if ($status == 'SUCCESS')
        {
          if ($solved == 'Yes')
          {
            $arr[]   = "<a id=\"$res_id\" class=\"merge\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr<img id=\"$res_id-more-icon\" src=\"./css/magnifying-glass-icon.png\"></a>";
          	$arr[] = 'SUCCESS';
          }
          else
          {
            $arr[]   = "<a id=\"$res_id\" class=\"merge\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
          	$arr[] = 'SUCCESS';
          }
        }
        elseif ($status == 'WORKING')
        {
          if ($result_age < 1800)
          {
              $arr[] = "<a id=\"$res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\"><img id=\"$res_id-gif\" src=\"./css/images/ajax-loader.gif\">$repr</a>";
              $arr[] = 'WORKING';
          }
          else
          {
              $arr[]   = "<a id=\"$res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
              $arr[] = 'FINISHED';
          }
        }
        elseif ($status == 'FAILED')
        {
          $arr[] = "<a id=\"$res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
          $arr[] = 'FAILED';
        }
        else {
          $arr[] = "<a id=\"$res_id\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">Error</a>";
          $arr[] = 'FAILED';
        }
        $arr[] = $time;
        $arr[] = $res_id;
      }
      elseif ($type == 'sad')
      {
        $sql2    = "SELECT sad_status,repr,download_file,timestamp,TIMESTAMPDIFF(SECOND,timestamp,NOW()) AS result_age FROM sad_results WHERE sad_result_id='$id'";
        $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
        $sql2    = mysql_fetch_object($result2);
        $download_file = $sql2-> download_file;
        $status  = $sql2->sad_status;
        $repr    = $sql2->repr;
        $time    = $sql2->timestamp;
        $result_age = $sql2->result_age;
        $arr[]   = "sad";
        $arr[]   = $display;
        $arr[]   = $process_id;
        if ($status == 'SUCCESS')
        {
          if (! (is_null($download_file) or ($download_file == 'None')))
          {
            $arr[]   = "<a id=\"$res_id\" class=\"success\"  title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
            $arr[] = 'SUCCESS';
          } else {
            $arr[]   = "<a id=\"$res_id\" class=\"noautosol\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
            $arr[] = 'SUCCESS';
          }
        }
        elseif ($status == 'WORKING')
        {
          if ($result_age < 3000)
          {
              $arr[] = "<a id=\"$res_id\" class=\"working\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\"><img id=\"$res_id-gif\" src=\"./css/images/ajax-loader.gif\">$repr</a>";
              $arr[] = 'WORKING';
          }
          else
          {
            $arr[]   = "<a id=\"$res_id\" class=\"unknown\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
            $arr[] = 'UNKNOWN';
          }
        }
        elseif ($status == "FAILED")
        {
          $arr[]   = "<a id=\"$res_id\" class=\"failed\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
          $arr[] = 'FAILED'; 
        }
        else
        {
          $arr[]   = "<a id=\"$res_id\" class=\"failed\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
          $arr[] = 'FAILED'; 
        }
        // Append the timestamp
        $arr[] = $time;
        $arr[] = $res_id;
      }
      elseif ($type == 'mr')
      {
        $sql2    = "SELECT mr_status,repr,timestamp,TIMESTAMPDIFF(SECOND,timestamp,NOW()) AS result_age FROM mr_results WHERE mr_result_id='$id'";
        $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
        $sql2    = mysql_fetch_object($result2);
        $status  = $sql2->mr_status;
        $repr    = $sql2->repr;
        $time    = $sql2->timestamp;
        $result_age = $sql2->result_age;
        $arr[]   = "mr";
        $arr[]   = $display;
        $arr[]   = $process_id;
        //A solution has been found
        if ($status == 'SUCCESS')
        {
            
            $arr[]   = "<a id=\"$res_id\" class=\"success\"  title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
            $arr[] = 'SUCCESS';
        }
        //Finished, but no solution
        elseif ($status == 'COMPLETE')
        {
            
            $arr[]   = "<a id=\"$res_id\" class=\"failed\"  title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
            $arr[] = 'COMPLETE';
        }
        //Still working
        elseif ($status == 'WORKING')
        {
          //Still to be shown as active
          if ($result_age < 3000)
          {
              $arr[] = "<a id=\"$res_id\" class=\"working\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\"><img id=\"$res_id-gif\" src=\"./css/images/ajax-loader.gif\">$repr</a>";
              $arr[] = 'WORKING';
          }
          //Gone on too long - probably an error
          else
          {
            $arr[]   = "<a id=\"$res_id\" class=\"unknown\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
            $arr[] = 'UNKNOWN';
          }
        }
        //The pipeline has exited in error
        elseif ($status == "FAILED")
        {
          $arr[]   = "<a id=\"$res_id\" class=\"failed\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
          $arr[] = 'FAILED'; 
        }
        else
        {
          $arr[]   = "<a id=\"$res_id\" class=\"failed\" title=\"$time &#13;R-Click for Options\" href=\"#\" id=\"$res_id\" rel=\"\">$repr</a>";
          $arr[] = 'FAILED'; 
        }
        // Append the timestamp
        $arr[] = $time;
        $arr[] = $res_id;
      }
    }
    $arr[] = $timestamp;
  }
  else {
    $arr[] = $lasttimestamp;
  }

  //Encode in JSON
  $out = json_encode($arr);
  print $out;  
?>


<?php
  //session_start();

  //$datadir = $_SESSION[data];
  $datadir = "/gpfs4/users/necat/kay";
  $beamline  = $_POST[beamline];
  //$beamline = 'E';
  $form_type = "current";
//  $username = $_SESSION[username];
  $username = "SBMRI_Jin";
  require('./login/config.php');
//  require('./login/functions.php');
?>


<html>
  <head>
    <style type="text/css">
      h3 {
        color: green;
        font-size: 1em;
        margin-bottom: 0.25em;
      }
        #pucklist { width: 150px; height: 300px; padding: 0.5em; float: left; margin: 10px; }
        #container { width: 640px: height: 150px; padding: 10px; }
	#PuckA { width: 150px; height: 150px; padding: 0.5em; float: left; margin: 10px; }
    </style>
    <script type="text/javascript">
      jQuery(function($){
	$( "#pucks li" ).draggable({
	  appendTo: "body",
	  helper: "original",
	  revert: "invalid"
	});
	$( "#PuckA ul" ).droppable({
	  activeClass: "ui-state-default",
	  hoverClass: "ui-state-hover",
	  accept: ":not(.ui-sortable-helper)",
	  drop: function( event, ui ) {
	    $( this ).find( ".placeholder" ).remove();
	    //	    $( "<li></li>" ).text( ui.draggable.text() ).appendTo( this );
	  }
	});
      });
    </script>


  </head>

  <body>
<?php
  //make the connection to the database
      //  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $connection = @mysql_connect('kona','rapd1','necatm)nsteR!');
  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());

  //obtain current user
  if (allow_user() != "yes")
  {
    echo("You Must Be Logged into Assign Pucks.");
  } else {

    //query for the pucks for the current user
    $sql = "SELECT PuckID FROM samples WHERE username='$username' GROUP BY PuckID";
    $result = @mysql_query($sql,$connection) or die(mysql_error());
    $pucks = array();
    while ($row = mysql_fetch_array($result))
      {
        array_push($pucks, $row['0']);
      }    
  }
  //look at current table for this data_root_dir
  $sql = "SELECT puckset_id FROM current WHERE data_root_dir='$datadir'";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
  $num = mysql_num_rows($result); 
  if ($num == 0)
  {
    //no row means we are not working on an active data_root_directory
    //ask user to assign pucks
    echo("No Pucks Selected.");
  } else { 

    //if puckset_id present, then display selected pucks.
    $return = mysql_fetch_object($result);
    $puckset_id = $return -> puckset_id;

    //query for the settings of the retrieved data
    $sql = "SELECT * FROM puck_settings WHERE puckset_id='$puckset_id'";
    $result = @mysql_query($sql,$connection) or die(mysql_error());
    $return = mysql_fetch_object($result);

    //now grab the data to fill the form
    $puck_a   = $return -> A;
    $puck_b   = $return -> B;
    $puck_c   = $return -> C;
    $puck_d   = $return -> D;

  }


?>
<div id="container">
   <div id="pucklist" class="ui-widget-content">
      <h1 class="ui-widget-header">Available Pucks</h1>
      <div id="pucks">
        <UL>        
           <?
              foreach ($pucks as $p) {
                 echo("<li>".$p);
           //    if ($sample_type == $t) {
           //      echo("          <option value='$t' selected='$t'>$t</option>\n");
           //    } else {
           //      echo("          <option value='$t'>$t</option>\n");
           //    }
              }
           ?>
        </UL>
      </div>
   </div>
   <div id="PuckA" class="ui-widget-content">
       <h1 class="ui-widget-header">Puck A</h1>
         <UL>
           <li class="placeholder">Add your puck here</li>
         </UL>
   	</div>
   </div>
</div>

</body>
</html>

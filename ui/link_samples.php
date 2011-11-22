<?php
//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);

session_cache_limiter();
session_start();

require('./login/config.php');
require('./login/functions.php');

if(allow_user() != "yes")
{
    if(allow_local_data($_POST[data]) != "yes")
    {
        include ('./login/no_access.html');
        exit();
    } else {
        $local = 1;
    }
} else {
    $local = 0;
}
$_SESSION[data] = $_POST[data];
?>
<html>
  <head>
    <meta  http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title><? echo $_SESSION[username]; ?>@RAPD</title> 
    <link rel="shortcut icon" href="./css/favicon.ico" type="image/x-icon">
    <!-- thickbox -->
    <link type="text/css" href="css/thickbox.css"                             rel="stylesheet" />
    <!-- css for the image viewer -->
    <link type="text/css" href="css/iip.compressed.css"                       rel="stylesheet" />
    <link type="text/css" href="css/blending.css"                             rel="stylesheet" />
    <!-- dataTables -->
    <link type="text/css" href="css/ndemo_table.css"                          rel="stylesheet" />
    <link type="text/css" href="css/ndemo_page.css"                           rel="stylesheet" />
    <!-- jquery UI styling -->
    <link type="text/css" href="css/south-street/njquery-ui-1.7.2.custom.css" rel="stylesheet" />
    <!-- jeegoocontext css -->
    <link type="text/css" href="css/cm_blue/style.css"                        rel="stylesheet" />
    <!-- done with image viewer css -->
    <link type="text/css" href="css/d_rapd.css"                                rel="stylesheet" />

    <!-- Load up the javasript using google to make it faster remotely -->
    <script src="http://www.google.com/jsapi?key=ABQIAAAArmeu5LmO0GnPE-nZ0Fe1qhQOqcOQgkuU1c5Ip7P-iLN3BAQyDBR1yNT4dNxyOxjnbWKQzT76MupHkw"></script>


    <!-- Load up the javasript using google to make it faster remotely -->
    <!--<script src="http://www.google.com/jsapi"></script>-->
    <script>
      // Load jQuery
      google.load("jquery", "1.4.3"); //,{uncompressed : true});
      google.load("jqueryui", "1.8.5");
    </script>

  </head>
  <body class="banner">

    <!-- Get php variables into javascript -->
    <?php
      echo("<script type='text/javascript'>\n");
      echo("my_beamline = '$_POST[beamline]';\n");
      echo("my_ip = '$_SERVER[REMOTE_ADDR]';\n");
      echo("my_user = '$_POST[user]';\n");
      echo("my_datadir = '$_POST[data]';\n");
      echo("my_trip_id = '$_POST[trip_id]';\n");
      echo("</script>");
    ?>
    <script language="javascript" type="text/javascript" src="./js/jquery.dataTables.min.js"></script>
  

<script id="source" language="javascript" type="text/javascript">
$(document).ready(function() {
	oTable = $('#samples').dataTable( {
		"bProcessing": true,
	        "sAjaxSource": "getSamples.php?username="+my_user+"&datadir="+my_datadir,
	        "aoColumns": [
			    /* Unique Sample ID */ { "bVisible": false },
			    /* Filename */ null,
			    /* Puck ID */ null,
			    /* Sample Number */ { "sWidth": "3px" },
			    /* Crystal ID */ null,
			    /* Protein */ null,
			    /* Comment */ null,
			    /* Freezing Condition */ null,
			    /* Crystal Condition */ null,
			    /* Metal */ null,
			    /* Solvent Content */ null,
			    /* Person */ null,
			    /* Username */ { "bVisible": false },
			    /* Timestamp */ { "bVisible": false },
                            ],
	        "bAutoWidth": false,
                "bJQueryUI": true,
	      "iDisplayLength": 50
	} );
    $("#id_hideFilename").click( function() {
        oTable.fnSetColumnVis(1, this.checked);
    });
    $("#id_hidePuck").click( function() {
	oTable.fnSetColumnVis(2, this.checked);
    });
    $("#id_hideNumber").click( function() {
	oTable.fnSetColumnVis(3, this.checked);
    });
    $("#id_hideCrystal").click( function() {
	oTable.fnSetColumnVis(4, this.checked);
    });
    $("#id_hideProtein").click( function() {
	oTable.fnSetColumnVis(5, this.checked);
    });
    $("#id_hideComment").click( function() {
	oTable.fnSetColumnVis(6, this.checked);
    });
    $("#id_hideFreezeCond").click( function() {
	oTable.fnSetColumnVis(7, this.checked);
    });
    $("#id_hideCrystalCond").click( function() {
	oTable.fnSetColumnVis(8, this.checked);
    });
    $("#id_hideMetal").click( function() {
	oTable.fnSetColumnVis(9, this.checked);
    });
    $("#id_hideSolvent").click( function() {
	oTable.fnSetColumnVis(10, this.checked);
    });
    $("#id_hidePerson").click( function() {
	oTable.fnSetColumnVis(11, this.checked);
    });

    iTable = $('#images').dataTable({
              "bProcessing": true,
	      "sAjaxSource": "getImages.php?datadir="+my_datadir,
	        "aoColumns": [
			    /* Image */ null,
			    /* Space Group */ null,
			    /* a */ null,
			    /* b */ null,
			    /* c */ null,
			    /* alpha */ null,
			    /* beta */ null,
			    /* gamma */ null,
			    /* mosaicity */ null,
			    /* resolution */ null,
			    /* webice */ null,
			    /* Result_ID */ { "bVisible": false },
                            ],
	       "bAutoWidth": false,
                "bJQueryUI": true,
	   "iDisplayLength": 50
	       });
     /* Add a click handler to the rows */
   $('#images tbody').click(function(event) {
	  if ( $(event.target.parentNode).hasClass('row_selected') ) {
	     $(event.target.parentNode).removeClass('row_selected');
	  } else {
	     $(event.target.parentNode).addClass('row_selected');
	  };
        
    });

   $('table').live('submit', function() {
        //Assemble the variables to be passed on
        var sample_id = $('#sampleslist').val();
        //check for selected sample
        if (sample_id == "None") {
	  alert("A sample must be chosen.");
          return false;
	};

	var result_ids = new Array();
	var row = iTable.fnGetNodes();
        //grab data from selected rows and place in array.
 	for ( var i=0 ; i<row.length ; i++ )
	{
		if ( $(row[i]).hasClass('row_selected') )
		{
		  result_ids.push(iTable.fnGetData(i)[11]);
		}
	}
        //send data via ajax to update mysql db
        $.ajax({ url: "set_sample.php",
		   //	    dataType: "json",
                type: "POST",
		   data: { "sample_id": sample_id, "result_ids": JSON.stringify(result_ids)},
	     success: function(result)
		   {
		     alert('Samples and Results linked.');
                     $(iTable.fnGetNodes()).each(function (){
			 $(this).removeClass('row_selected');
                     });
                     oTable.fnDraw();
		   }   
	  })    
			  });
});


$(function() {
   //React to control button presses
   $('#go_to_main').click(function() {
       document.location.href = 'main.php';
   });

   $('#go_to_samples').click(function() {
       document.location.href = 'samples_main.php';
   });

   $('#go_to_trips').click(function() {
       document.location.href = 'link_samples_trip.php';
   });

   $('#go_to_logout').click(function() {
       document.location.href = 'login/logout.php';
   });
	// Tabs
	$('#tabs1').tabs();
	$('#tabs2').tabs();

	// Bind change to sheet select
        $('#sheet').change(function() {
	    oForm = document.forms[0];
        $.ajax({url: "samples_bysheet.php",
	       data: {"user": my_user,"sheet": oForm.elements['sheet'].value },
		   dataType: "json",
            success: function(data) {
              var options = '';
              for (var i in data) {
                options += '<option value="' + data[i][0] + '">' + data[i][1] + '</option>';
              }
            $("#sampleslist").html(options);

	    }
        });
   });


});


</script>
<noscript>
    <h1 align="center"><font color="#FF0000">Javascript is required to view this page.</font></h1>
</noscript>


<h1 style="font-size: 2.0em">RAPD Samples for <?php echo $_POST[user]; ?></h1>
<table>
  <tr>
    <td width="220">
    <!-- Tabs -->

    <div class="tabs" id="tabs1">
    <ul>

      <li><a href="#tabs-1">Form</a></li>
      <li><a href="#tabs-2">Controls</a></li>
    </ul>

    <!-- Information for Tabs -->
      <div class="tabs" id="tabs-1">
<form id="linksamples" action="set_sample.php" onSubmit='return false;'>

<?php
  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db($db_name,$connection)or die(mysql_error());

  //Select a sheet of samples
  $db = @mysql_select_db(rapd_data,$connection)or die(mysql_error());
  $sql ="SELECT sheetname FROM samples WHERE username='$_POST[user]' GROUP By sheetname";
  $xls = @mysql_query($sql,$connection) or die(mysql_error());

    echo("Spreadsheet:        <select name='sheet' id='sheet'>");
    echo("<option value='None'>None</option>");
    while ($row = mysql_fetch_array($xls))
      {
        echo("          <option value='$row[0]'>$row[0]</option>\n");
      };    
    echo("        </select><br>");
?>


<!-- Drop down list for samples -->

Sample:        <select name='sampleslist' id='sampleslist'>"
               <option value='None'>None</option>
               </select>

      </div>

      <div class="tabs" id="tabs-2">
    <?php
       if ($local == 1)
       {
    ?> 
              <button style='width:95%' class="fg-button ui-state-default ui-corner-all" id="go_to_logout" type="button">Logout</button>
    <?php
       } else {
    ?>
              <button style='width:95%' class="fg-button ui-state-default ui-corner-all" id="go_to_samples" type="button">Samples Nexus</button>
	<br>&nbsp;
              <button style='width:95%' class="fg-button ui-state-default ui-corner-all" id="go_to_trips" type="button">Trips</button>
	<br>&nbsp;
              <button style='width:95%' class="fg-button ui-state-default ui-corner-all" id="go_to_main" type="button">Main</button>
    <?php 
       }
    ?>

      </div>
    </div>
    </td>
    
    <td>

    <!-- Tabs -->
    <div class="tabs" id="tabs2">
       <ul>
        <li><a href="#tabs-3">Results</a></li>
        <li><a href="#tabs-4">Samples</a></li>
       </ul>

    <!-- Information for Tabs -->
    <div class="tabs" id="tabs-3">

    <h2>Available Results</h2>

    <!-- Table with checkboxes for images -->
       <div id="auto_wrapper" class="dataTables_wrapper">
         <table class="ranking" width="100%" id="images">
           <thead align="center">
             <tr>
             <th class="sorting">Image</th>
             <th class="sorting">Sym</th>
             <th class="sorting">a</th>
             <th class="sorting">b</th>
             <th class="sorting">c</th>
             <th class="sorting">&alpha</th>
             <th class="sorting">&beta</th>
             <th class="sorting">&gamma</th>
             <th class="sorting">Mosaicity</th>
             <th class="sorting">Resolution</th>
             <th class="sorting">WebIce</th>
             <th class="sorting">Result ID</th>
             </tr>
           </thead>
           <tbody align="center">
              <tr>
        	<td colspan="5" class="dataTables_empty">Loading data from server</td>
              </tr>
           </tbody>
         </table>
       </div>
     <br>
     <center><input type="submit" name="submit" value="Submit"></center>
     </form>

     </div>

     <div class="tabs" id="tabs-4">

     <h2>Samples Associated with Trip </h2>

     <!-- Show current samples associated with trip -->
       <div id="auto_wrapper" class="dataTables_wrapper">
          <table class="ranking" width="100%" id="samples">
            <thead align="center">
              <tr>
                <th>Unique Sample ID</th>
                <th>Filename</th>
                <th>Puck ID</th>
                <th> &#35; </th>
                <th>Crystal ID</th>
                <th>Protein</th>
                <th>Comment</th>
                <th>Freezing Condition</th>
                <th>Crystal Condition</th>
                <th>Metal</th>
                <th>Solvent Content</th>
                <th>Person</th>
                <th>Username</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody align="center">
              <tr>
        	<td colspan="5" class="dataTables_empty">Loading data from server</td>
              </tr>
            </tbody>
          </table>
       </div>

       <input type="checkbox" checked="checked" id="id_hideFilename">Filename
       <input type="checkbox" checked="checked" id="id_hidePuck">Puck ID
       <input type="checkbox" checked="checked" id="id_hideNumber">Number 
       <input type="checkbox" checked="checked" id="id_hideCrystal">Crystal ID
       <input type="checkbox" checked="checked" id="id_hideProtein">Protein
       <input type="checkbox" checked="checked" id="id_hideComment">Comment
       <input type="checkbox" checked="checked" id="id_hideFreezeCond">Freezing Condition
       <input type="checkbox" checked="checked" id="id_hideCrystalCond">Crystal Condition
       <input type="checkbox" checked="checked" id="id_hideMetal">Metal
       <input type="checkbox" checked="checked" id="id_hideSolvent">Solvent Content
       <input type="checkbox" checked="checked" id="id_hidePerson">Person
   
    </div>
    </div>

    </td>
  </tr>
</table>
</body>
</html>

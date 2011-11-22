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
    include ('./login/no_access.html');
    exit();
}
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

    <!-- Load up the MooTools Stuff -->
    <!-- Load up the javasript using google to make it faster remotely -->
    <script src="http://www.google.com/jsapi?key=ABQIAAAArmeu5LmO0GnPE-nZ0Fe1qhQOqcOQgkuU1c5Ip7P-iLN3BAQyDBR1yNT4dNxyOxjnbWKQzT76MupHkw"></script>
    <script>google.load("mootools", "1.2.5");</script>
    <script type="text/javascript" src="./js/mootools-1.2-more.js"></script> 
    <script type="text/javascript" src="./js/iipmooviewer-1.3_fm_alt.min.js"></script>
    <script type="text/javascript" src="./js/moocanvas-compressed.js"></script>

    <script type="text/javascript">

    function load_images(number_images,image_repr,image_string){
        //alert(image_string);
        var server = '/fcgi-bin/iipsrv.fcgi';
  	var fx1 = new Fx.Tween( 'targetframe', {duration:'long'} );
  	fx1.start('opacity',0).chain( function(){
                                          document.id('targetframe').empty();
  					  delete iip;
  					  iip = new IIP_FM( "targetframe", {   image:  [image_string],
  		                                                               server: server,
                                                                               credit: 'NE-CAT',
  						                               zoom: 1.0,
  						                               render: 'spiral',
                                                                               fm_mode: number_images,
                                                                               fm_image_reprs:image_repr
                                                                           }                
  					                   );
                                          this.callChain();
  				       }).chain( function(){ 
                                          fx1.start('opacity',1);
                                       });
    } //End of load_images 

    window.addEvent( 'domready', function(){
        new Tips( 'div#controls div h2', {
                  className: 'tip',
                  onShow: function(t){ t.setStyle('opacity',0); t.fade(0.7); },
                  onHide: function(t){ t.fade(0); }
        });
      });
    </script>

    <!-- Load up the javasript using google to make it faster remotely -->
    <!--<script src="http://www.google.com/jsapi"></script>-->
    <script>
      // Load jQuery
      google.load("jquery", "1.4.3"); //,{uncompressed : true});
      google.load("jqueryui", "1.8.5");
    </script>

  </head>
  <body class="banner">

    <script language="javascript" type="text/javascript" src="./js/jquery.dataTables.1.7.1.min.js"></script>
  
<script id="source" language="javascript" type="text/javascript">
$(document).ready(function() {
	oTable = $('#samples').dataTable( {
		"bProcessing": true,
		"bServerSide": false,
	        "sAjaxSource": "./samples_serverside.php",
	        "aoColumns": [
			    /* Unique Sample ID */ { "bVisible": false },
			    /* Filename */ null,
			    /* Puck ID */ null,
			    /* Sample Number */ { "sWidth": "3px" },
			    /* Crystal ID */ null,
			    /* Protein */ null,
			    /* Ligand */ null,
			    /* Comment */ null,
			    /* Freezing Condition */ null,
			    /* Crystal Condition */ null,
			    /* Metal */ null,
			    /* Project */ null,
			    /* Person */ null,
<?
     if (allow_access(Administrators) == "yes")
     {
       echo('			    /* Username */ { "bVisible": true },');
     } else {
       echo('			    /* Username */ { "bVisible": false },');
     }
?>
			    /* Timestamp */ { "bVisible": false },
			    /* Trip ID */ { "bVisible": false },
			    /* Trip Start */ null,
			    /* Trip End */ null,
			    /* Data Root Dir */  {"bVisible": false },
			    /* Beamline */ null,
                            ],
	        "bAutoWidth": false,
                 "bJQueryUI": true,
	      "iDisplayLength": 50,
	      "fnServerData": function ( sSource, aoData, fnCallback ) {
                 if ("<?php echo(allow_access(Administrators)) ?>" != "yes" ) {
                    aoData.push({"name":"username", "value": "<?php echo $_SESSION[username]; ?>"});
                 };
	         $.ajax( {
		     "dataType": 'json',
		         "type": "GET",
                          "url": sSource,
                         "data": aoData,
                      "success": fnCallback
		 });
	       },
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
    $("#id_hideLigand").click( function() {
	oTable.fnSetColumnVis(6, this.checked);
    });
    $("#id_hideComment").click( function() {
    oTable.fnSetColumnVis(7, this.checked);
    });
    $("#id_hideFreezeCond").click( function() {
	oTable.fnSetColumnVis(8, this.checked);
    });
    $("#id_hideCrystalCond").click( function() {
	oTable.fnSetColumnVis(9, this.checked);
    });
    $("#id_hideMetal").click( function() {
	oTable.fnSetColumnVis(10, this.checked);
    });
    $("#id_hideProject").click( function() {
	oTable.fnSetColumnVis(11, this.checked);
    });
    $("#id_hidePerson").click( function() {
	oTable.fnSetColumnVis(12, this.checked);
    });
    $("#id_hideUsername").click( function() {
	oTable.fnSetColumnVis(13, this.checked);
    });
    $("#id_hideStart").click( function() {
    oTable.fnSetColumnVis(16, this.checked);
    });
    $("#id_hideFinish").click( function() {
    oTable.fnSetColumnVis(17, this.checked);
    });
    $("#id_hideBeamline").click( function() {
    oTable.fnSetColumnVis(19, this.checked);
    });
    
    $('#samples tbody').dblclick( function(event) {
        /* double-click on the row to close it */
        $(oTable.fnGetNodes()).each(function (){
             oTable.fnClose(this);
	});
        /* double-click to open the row */
        var aPos = oTable.fnGetPosition(event.target.parentNode);
        oTable.fnOpen(event.target.parentNode, transientTable(), "info_row");
        get_images(oTable.fnGetData(aPos));
    });
    pTable = $('#projects').dataTable( {
		"bProcessing": true,
		"bServerSide": false,
	    "sAjaxSource": "./projects_serverside.php",
	      "aoColumns": [
			    /* Unique Project ID */ { "bVisible": false },
			    /* Project */ null,
			    /* Protein */ null,
			    /* Ligand */ null,
			    /* Project Type */ null,
			    /* Sequence */ null,
			    /* Molecular Weight */ null,
			    /* Solvent Content */ null,
			    /* Metal */ null,
			    /* Sites */ null,
			    /* PDB */ null,
<?
     if (allow_access(Administrators) == "yes")
     {
       echo('			    /* Username */ { "bVisible": true },');
     } else {
       echo('			    /* Username */ { "bVisible": false },');
     }
?>
			    /* Timestamp */ { "bVisible": false },
                            ],
	       "bAutoWidth": false,
            "bJQueryUI": true,
	   "iDisplayLength": 50,
	     "fnServerData": function ( sSource, aoData, fnCallback ) {
                 if ("<?php echo(allow_access(Administrators)) ?>" != "yes" ) {
                    aoData.push({"name":"username", "value": "<?php echo $_SESSION[username]; ?>"});
                 };
	         $.ajax( {
		     "dataType": 'json',
		         "type": "GET",
                          "url": sSource,
                         "data": aoData,
                      "success": fnCallback
		 });
	       },
 	} );

});

function transientTable() {
          var sOut = '   <div class="dataTables_wrapper"> ';
             sOut += '     <table class="ranking" id="images" border="1" cellpadding="0" cellspacing="0"> ';
             sOut += '       <thead align="center"> ';
             sOut += '         <tr> ';
             sOut += '           <th class="sorting">Image</th> ';
             sOut += '           <th class="sorting">Sym</th> ';
             sOut += '           <th class="sorting">a</th> ';
             sOut += '           <th class="sorting">b</th> ';
             sOut += '           <th class="sorting">c</th> ';
             sOut += '           <th class="sorting">&alpha</th> ';
             sOut += '           <th class="sorting">&beta</th> ';
             sOut += '           <th class="sorting">&gamma</th> ';
             sOut += '           <th class="sorting">Mosaicity</th> ';
             sOut += '           <th class="sorting">Resolution</th> ';
             sOut += '           <th class="sorting">WebIce</th> ';
             sOut += '           <th class="sorting">Result ID</th> ';
             sOut += '         </tr> ';
             sOut += '       </thead> ';
             sOut += '     <tbody align="center"> ';
             sOut += '         <tr> ';
             sOut += '           <td colspan="5" class="dataTables_empty">Loading data from server</td> ';
             sOut += '         </tr> ';
             sOut += '     </tbody> ';
             sOut += '   </table> ';
             sOut += ' </div> ';
  return sOut;
};

/* Query MySQL and fill transient Images Table*/
function get_images(samples) {
  var sample = samples[0];
  var my_trip_id = samples[14];
  var my_datadir = samples[18];
  iTable = $('#images').dataTable({
              "bProcessing": true,
	      "sAjaxSource": "getImages.php?sample_id="+sample,
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
	      "iDisplayLength": 10
	       });
  $('#images tbody').click( function(event) {
        /* click on the row to spawn image */
        var aPos = iTable.fnGetPosition(event.target.parentNode);
        var data = iTable.fnGetData(aPos);

	    var result = data[11];
        $.getJSON("get_result_data.php?res_id="+result+"&datadir="+my_datadir+"&trip_id="+my_trip_id, function(json) {
            image_mode    = json[4][0];
            if (image_mode == 'OLD')
            {
              image_string  = json[4][1];
              $("#mooviewer").hide();
              $("#old_images").empty();
              $("#old_images").append(image_string);
            }
            else if (image_mode == 'NEW')
            {
              number_images = json[4][1];
              image_repr    = json[4][2];
              image_string  = json[4][3];
              if ($('#tabs2').tabs().tabs('option', 'selected') == 3)
              {
                  $("#old_images").empty();
                  $("#mooviewer").show();
                  load_images(number_images,image_repr,image_string);
              } else {
                  image_shown = 'False';
                  $("#old_images").empty();
                  $("#targetframe").empty();
              }
            }
           $('#mooviewer').dialog('open');
	   load_images(number_images,image_repr,image_string);
        });

  });
};


$(function() {
   //React to control button presses
   $('#go_to_main').click(function() {
       document.location.href = 'main.php';
   });

   $('#go_to_samples').click(function() {
       document.location.href = 'samples_main.php';
   });

   $('#go_to_logout').click(function() {
       document.location.href = 'login/logout.php';
   });

   $('#mooviewer').dialog({ autoOpen: false,
			 height: 1000,
			 width: 1000,
                         modal: true,
   });
   //Increase dataTables max width
   $('.dataTables_wrapper').css('max-width', '1500');

	// Tabs
	$('#tabs1').tabs();
	$('#tabs2').tabs();

        $('#tabs-2').bind('tabsselect', function(event, ui) {
 	    if (ui.index == 3) {
                if (image_shown == 'False')
                {
                    image_shown = 'True';
                    if (image_mode == 'NEW')
                    {
                        $("#mooviewer").show();
                        load_images(number_images,image_repr,image_string);
                    }
                }
            }
        });

});

</script>
<noscript>
    <h1 align="center"><font color="#FF0000">Javascript is required to view this page.</font></h1>
</noscript>


<h1 style="font-size: 2.0em">RAPD Samples</h1>
<table>
<tr>
<td>
<!-- Tabs -->

<div id="tabs1">
<ul>

   <li><a href="#tabs-1">Samples</a></li>
   <li><a href="#tabs-2">Projects</a></li>
</ul>

<!-- Information for Tabs -->
<div id="tabs-1">

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
        <th>Ligand</th>
        <th>Comment</th>
        <th>Freezing Condition</th>
        <th>Crystal Condition</th>
        <th>Metal</th>
        <th>Project</th>
        <th>Person</th>
        <th>Username</th>
        <th>Timestamp</th>
        <th>Trip ID</th>
        <th>Trip Start</th>
        <th>Trip Finish</th>
        <th>Data Directory</th>
        <th>Beamline</th>
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
<input type="checkbox" checked="checked" id="id_hideLigand">Ligand
<input type="checkbox" checked="checked" id="id_hideComment">Comment
<input type="checkbox" checked="checked" id="id_hideFreezeCond">Freezing Condition
<input type="checkbox" checked="checked" id="id_hideCrystalCond">Crystal Condition
<input type="checkbox" checked="checked" id="id_hideMetal">Metal
<input type="checkbox" checked="checked" id="id_hideProject">Project
<input type="checkbox" checked="checked" id="id_hidePerson">Person

<?
     if (allow_access(Administrators) == "yes")
     {
       echo('<input type="checkbox" checked="checked" id="id_hideUsername">User');
     }
?>
<input type="checkbox" checked="checked" id="id_hideStart">Start
<input type="checkbox" checked="checked" id="id_hideFinish">Finish
<input type="checkbox" checked="checked" id="id_hideBeamline">Beamline
  
</div>
<div id="tabs-2">

<div id="auto_wrapper" class="dataTables_wrapper">
  <table class="ranking" width="100%" id="projects">
    <thead align="center">
      <tr>
        <th>Unique Project ID</th>
        <th>Project</th>
        <th>Protein</th>
        <th>Ligand</th>
        <th>Project Type</th>
        <th>Sequence</th>
        <th>Molecular Weight</th>
        <th>Solvent Content</th>
        <th>Metal</th>
        <th>Sites</th>
        <th>PDB</th>
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
  
</div>
              <div id='mooviewer' title="Image Viewer">
                <!-- Now insert our iipmooviewer div -->
                <div style="width:99%;height:95%;left:auto; top:5%" id="targetframe">
                </div>
              </div>
</div>
          </td>
          <td width="220">
<div class="tabs" id="tabs2">
<ul>

   <li><a href="#tabs-3">Controls</a></li>
</ul>

<!-- Information for Tabs -->
<div id="tabs-3">
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
              <button style='width:95%' class="fg-button ui-state-default ui-corner-all" id="go_to_main" type="button">Main</button>
<?php 
    }
?>
</div>
</div>
</td>
</tr>
</table>
</body>
</html>

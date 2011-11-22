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
    <link type="text/css" href="css/d_rapd.css"                               rel="stylesheet" />

    <!-- Load up the MooTools Stuff -->
    <script type="text/javascript" src="./js/mootools-1.2.5-core-nc.js"></script>
    <script type="text/javascript" src="./js/mootools-1.2-more.js"></script> 
    <script type="text/javascript" src="./js/iipmooviewer-1.3_fm.js"></script>
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
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.6.1/jquery.min.js"></script>
    <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.13/jquery-ui.min.js"></script>
    <script src="./js/jquery.dataTables.1.7.1.min.js" language="javascript" ></script>
    <script type="text/javascript" language="javascript" src="./js/jquery.jeegoocontext.1.2.2.min.js"></script>
    <script type="text/javascript" language="javascript" src="./js/jquery.livequery.js"></script>

<!-- Load up the javascript -->
    <script type="text/javascript" language="javascript" src="./d_rapd.js"></script>
  </head>
  <body>

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

  <!-- Tabs -->
  <table>
  <tr><td width="100%">
   <div class="tabs" id="tabs0">
    <ul>
      <li><a id="tabs0-tab0" href="#tabs0-0">Data</a></li>
      <li><a id="tabs0-tab1" href="#tabs0-1">Merging</a></li>
      <li><a id="tabs0-tab2" href="#tabs0-2">Structure</a></li>
    </ul>
    <div id="tabs0-0">
      <table id="wrapper" height="100%">
        <tr>
          <td width="220pixels">
            <div class="tabs" id="tabs0-tab0-tabs0">
              <ul>
                <li><a id="tabs0-tab0-tabs0-tab0" href="#tabs0-tab0-tabs0-0">Snaps</a></li>
                <li><a id="tabs0-tab0-tabs0-tab1" href="#tabs0-tab0-tabs0-1">Runs</a></li>
              </ul>
              <div id="tabs0-tab0-tabs0-0">
                <div id="snap_menu_wrapper" class="menu_wrapper">
                  <div id="snap_menu_in_process">
                    <!-- HERE IS WHERE IN-PROCESS INFO WILL BE PLACED -->
                  </div>
                  <div id="snap_menu" class="snap_menu">
                    <!-- HERE IS WHERE SNAPS WILL BE PUT BY DATABASE -->
                  </div>
                </div>
              </div>  <!-- end id="tabs0-tabs0-0" -->

              <div id="tabs0-tab0-tabs0-1">
                <div id="run_menu_wrapper" class="menu_wrapper">
                  <div id="run_menu_in_process">
                    <!-- HERE IS WHERE IN-PROCESS INFO WILL BE PLACED -->
                  </div>
                  <div id="run_menu" class="run_menu">
                    <!-- HERE IS WHERE RUNS WILL BE PUT BY DATABASE -->
                  </div>
                </div>
              </div> <!-- end id="tabs0-tab0-tabs0-1" -->
            </div> <!-- end class="tabs" id="tabs0-tab0-tabs0" -->
          </td>

          <td width="100%">
            <div class="tabs" id="tabs0-tab0-tabs1">
              <ul>
                <li id="tabs0-tab0-tabs1-tab0"><a href="#tabs0-tab0-tabs1-0">Summary</a></li>
                <li id="tabs0-tab0-tabs1-tab1"><a href="#tabs0-tab0-tabs1-1">MiniKappa</a></li>
                <li id="tabs0-tab0-tabs1-tab2"><a href="#tabs0-tab0-tabs1-2">Detail</a></li>
                <li id="tabs0-tab0-tabs1-tab3"><a href="#tabs0-tab0-tabs1-3">Images</a></li>
                <li id="tabs0-tab0-tabs1-tab4"><a href="#tabs0-tab0-tabs1-4">Plots</a></li>
				<li id="tabs0-tab0-tabs1-tab5"><a href="#tabs0-tab0-tabs1-5">Analysis</a></li>
                <li id="tabs0-tab0-tabs1-tab6"><a href="#tabs0-tab0-tabs1-6">Snaps</a></li>
                <li id="tabs0-tab0-tabs1-tab7"><a href="#tabs0-tab0-tabs1-7">Runs</a></li>
                <li id="tabs0-tab0-tabs1-tab8"><a href="#tabs0-tab0-tabs1-8">Samples</a></li>
              </ul>
              <div id="tabs0-tab0-tabs1-0">
                <div class="sample-summary"></div>
                <div id="summary" class="summary"></div>
              </div>
              <div id="tabs0-tab0-tabs1-1">
                <div class="sample-summary"></div>
                <div id="stac-summary"></div>
              </div>
              <div id="tabs0-tab0-tabs1-2">
                <div class="sample-summary"></div>
                <div id="detail" class="detail">
                  <!-- These sub-divs are for use in loading the integration results -->
                  <div id="detail1"></div>
                  <div id="detail2"></div>
                  <div id="detail3"></div>
                </div>
              </div>
              <div id="tabs0-tab0-tabs1-3">
                <div class="sample-summary"></div>
                <div id="images" class="images">
                  <div id="old_images"></div>
                  <div id='mooviewer'>
                    <!-- Now insert our iipmooviewer div -->
                    <div style="width:100%;height:100%;left:auto;" id="targetframe"></div>
                  </div>
                </div>
              </div>
              <div id="tabs0-tab0-tabs1-4">
                <div class="sample-summary"></div>
                <div id="plots" class="plots"></div>
              </div>
              <div id="tabs0-tab0-tabs1-5">
                <div class="sample-summary"></div>
                <div id="analysis_tabs" class="tabs">
                	<ul>
										<li id="analysis-cell"><a href="#analysis-cell-tab">Cell Summary</a></li>	
										<li id="analysis-xtriage"><a href="#analysis-xtriage-tab">Xtriage</a></li>
										<li id="analysis-plots"><a href="#analysis-plots-tab">Plots</a></li>
										<li id="analysis-molrep"><a href="#analysis-molrep-tab">Self Rotation</a></li>
									</ul>
									<div id="analysis-cell-tab">
										<div id="content_cell_summary"></div>
									</div>
									<div id="analysis-xtriage-tab">
										<div id="content_xtriage"></div>
									</div>
									<div id="analysis-plots-tab">
										<div id="content_plots"></div>
									</div>
									<div id="analysis-molrep-tab">
										<div id="content_molrep"></div>
									</div>
                </div>
              </div>
              <div id="tabs0-tab0-tabs1-6">
                <div id="snaps-ranked" class="ranked">
                  <div id="container">
                    <div id="auto_wrapper" class="dataTables_wrapper"> 
                      <table class="ranking" id="snaps-sort-table" border="1" cellpadding="0" cellspacing="0">
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
                            <th class="sorting">Mos</th>
                            <th class="sorting">Res</th>
                            <th class="sorting">Stat</th>
                            <th class="sorting">Result ID</th>
                          </tr>
                        </thead>
                        <tbody align="center">
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div> 
              </div> 
              <div id="tabs0-tab0-tabs1-7">
                <div id="runs-ranked" class="ranked">
                  <div id="container">
                    <div id="auto_wrapper" class="dataTables_wrapper">
                      <table class="ranking" id="runs-sort-table" border="1" cellpadding="0" cellspacing="0">
                        <thead align="center">
                          <tr>
                            <th class="sorting">Dataset</th>
                            <th class="sorting">Sym</th>
                            <th class="sorting">a</th>
                            <th class="sorting">b</th>
                            <th class="sorting">c</th>
                            <th class="sorting">&alpha</th>
                            <th class="sorting">&beta</th>
                            <th class="sorting">&gamma</th>
                            <th class="sorting">Res</th>
                            <th class="sorting">Comp</th>
                            <th class="sorting">Mult</th>
                            <th class="sorting">Rpim</th>
                            <th class="sorting">AnomSlope</th>
                            <th class="sorting">Result ID</th>
                          </tr>
                        </thead>
                        <tbody align="center">
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
							<!-- Samples Table Tab -->
              <div id="tabs0-tab0-tabs1-8">
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
								      </tr>
								    </thead>
								  <tbody align="center">
								      <tr>
									<td colspan="5" class="dataTables_empty">Loading data from server</td>
								      </tr>
								 </tbody>
								</table>

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

								</div>
              </div>
              <!-- end id="tabs0-tab0-tabs1-8" -->
            </div>
          </td>
        </tr>
      </table>
    </div>
    
    <!-- Merging Tab -->
    <div id="tabs0-1">
    </div>  <!-- end of id="tabs0-2" -->

    <!-- Structure Tab -->
    <div id="tabs0-2">
      <table id="wrapper" height="100%">
        <tr>
          <td width="220pixels">
            <div class="tabs" id="tabs0-tab2-tabs0">
              <ul>
                <li><a id="tabs0-tab2-tabs0-tab0" href="#tabs0-tab2-tabs0-0">SAD</a></li>
                <li><a id="tabs0-tab2-tabs0-tab1" href="#tabs0-tab2-tabs0-1">MR</a></li>
                <!--<li><a id="tabs0-tab2-tabs0-tab2" href="#tabs0-tab2-tabs0-2">Ligand</a></li>-->
              </ul>
              <div id="tabs0-tab2-tabs0-0">
                <div id="sad_menu_wrapper" class="menu_wrapper">
                  <div id="sad_menu_in_process">
                    <!-- HERE IS WHERE IN-PROCESS INFO WILL BE PLACED -->
                  </div>
                  <div id="sad_menu">
                    <!-- HERE IS WHERE RESULTS WILL BE PUT BY DATABASE -->
                  </div>
                </div>
              </div>
              <div id="tabs0-tab2-tabs0-1">
                <div id="mr_menu_wrapper" class="menu_wrapper">
                  <div id="mr_menu_in_process">
                    <!-- HERE IS WHERE IN-PROCESS INFO WILL BE PLACED -->
                  </div>
                  <div id="mr_menu">
                    <!-- HERE IS WHERE RESULTS WILL BE PUT BY DATABASE -->
                  </div>
                </div>
              </div>
              <div id="tabs0-tab2-tabs0-2">
                <div id="ligand_menu_wrapper" class="menu_wrapper">
                  <div id="ligand_menu_in_process">
                    <!-- HERE IS WHERE IN-PROCESS INFO WILL BE PLACED -->
                    Lorem ipsum
                  </div>
                  <div id="ligand_menu">
                    <!-- HERE IS WHERE RESULTS WILL BE PUT BY DATABASE -->
                    Lorem ipsum
                  </div>
                </div>
              </div>
            </div>
          </td>
          <td width="100%">
            <div class="tabs" id="tabs0-tab2-tabs1">
              <ul>
                <li><a id="tabs0-tab2-tabs1-tab0" href="#tabs0-tab2-tabs1-0">Summary</a></li>
                <li><a id="tabs0-tab2-tabs1-tab1" href="#tabs0-tab2-tabs1-1">Plots</a></li>
                <li><a id="tabs0-tab2-tabs1-tab2" href="#tabs0-tab2-tabs1-2">Autobuild</a></li>
              </ul>
              <div id="tabs0-tab2-tabs1-0">
                <div id="shelx-results"></div>
              </div>
              <div id="tabs0-tab2-tabs1-1">
                <div id="shelx-plots" class="plots"></div>
              </div>
              <div id="tabs0-tab2-tabs1-2">
                <div id="autosol-results"></div>
              </div>
            </div> 
          </td>
        </tr>
      </table>
    </div>  <!-- end of id="tabs0-3" -->
  </div> <!-- end of tabs0 -->
  </td>
  
  
  <td width="220px">
  <div class="tabs" id="tabs1">
    <ul>
      <li><a id="tabs1-tab0" href="#tabs1-0">Controls</a></li>
    </ul>
    <div id="tabs1-0">
      <div id="controls" class="controls">
        <!-- HERE IS WHERE CONTROLS WILL BE PLACED -->
        <?php
          if ($local == 1)
    	  {
        ?> 
        <button style='width:95%' class="fg-button ui-state-default ui-corner-all" id="go_to_logout" type="button">Logout</button>
        <?php
          } else {
        ?>
        <button style='width:95%' class="fg-button ui-state-default ui-corner-all" id="go_to_main" type="button">Main</button>
        <?php 
          }
          if (allow_access(Administrators) == "yes")
          {
        ?>
        <br>&nbsp;
        <button style='width:95%' class="fg-button ui-state-default ui-corner-all" id="go_to_trips" type="button">Trips</button>
        <?
          }
        ?>
        <br>&nbsp;
        <button style='width:95%' class="fg-button ui-state-default ui-corner-all" id="button_global_settings" type="button">Settings</button>
        <br>&nbsp;
<?php
     if ($local == 0)
    {
?>

              <button style='width:95%' class="fg-button ui-state-default ui-corner-all" id="puck-dialog" type="button">Pucks</button>
              <br>&nbsp;
<?php
    }
?>
        <div id='download_active'><button class="fg-button ui-state-default ui-corner-all" type="button" id="download-active">Download Processing</button></div>
        <div class="control-filler"></div> 
        <button style='width:95%' class="fg-button ui-state-default ui-corner-all" id="led_button" type="button">
          Remote Servers
          <div id='led_panel'>
            <table>
              <tr><td><button style='width:90px'><div id='controller'>Core</div></button></td></tr>
              <tr><td><button style='width:90px'><div id='cluster'>Cluster</div></button></td></tr>
              <tr><td><button style='width:90px'><div id='dataserver'>Data</div></button></td></tr> 
            </table>
          </div>
        </button>
        <button style='width:95%' class="fg-button ui-state-default ui-corner-all" type="button" id="reference_data_active">Reference Data Set</button>
      </div>
    </div>
  </div> <!-- end of tabs1 -->
  </td>
  
  </tr></table>
    <!--  Context menus -->
    <ul id='inprocessmenu' class="jeegoocontext cm_blue">
        <li id='hide-this-process'>Hide this process</li>
    </ul>

    <ul id="snapmenu" class="jeegoocontext cm_blue">
        <li>View
            <ul>
                <li id="snap_header">Header Info</li>
                <li id="snap_settings">Settings</li>
            </ul>
        </li>
        <li id="snap_reprocess">Reindex</li> 
        <li id="snap_kappa">MiniKappa Alignment</li>

			<!-- 
       <li>Reference Data
         <ul>
            <li id="make-snap-reference">Make this re for Kappa alignment</li>
            <li id="remove-snap-reference">Clear ref</li>
         </ul>
       </li>
			-->
        <li>Hide/Show
             <ul>
                <li id="hide-this-snap">Hide This Entry</li>
                <li id="hide-all-snaps">Hide Snap Failures</li>
                <li id="hide-all">Hide All Failures</li>
                <li id="show-success-snaps">Show Successful Snaps</li>
                <li id="show-all-snaps">Show All Snaps</li>
                <li id="show-all">Show All Results</li>
            </ul>
        </li>

    </ul>    
   
    <ul id="runmenu" class="jeegoocontext cm_blue">
       <li>View
         <ul>
           <li id="run_header">Header</li>
           <!--<li id="run_settings">Settings</li>-->
         </ul>
       </li>
       <li>Reference Data
         <ul>
            <li id="make-run-reference">Add This To Reference Set</li>
            <li id="remove-run-reference">Remove This From Reference Set</li>
         </ul>
       </li>
       <li>Reprocess
         <ul>
           <li id="run-xia2">Run Xia2</li>
           <li id="run-integrate">Run RAPD</li>
         </ul>
       </li>
       <li>Merge
	       <ul>
		       <li id="simple-merge">Merge 2 Wedges</li>
		     </ul>
		   </li>
       <li>Structure
         <ul>
           <li id='start-sad'>SAD</li>
           <li id='start-mr'>MR</li>
           <!--<li id='start-ligand'>Ligand Search</li>-->
         </ul>
       </li>
<?php
    if ($local == 0)
    {
?>
       <li id="run_download_process">Download Data</li>
<?php
    }
?>       <!-- <li>Report</li> -->
        <li>Hide/Show
             <ul>
                <li id="hide-this-run">Hide This Entry</li>
                <li id="hide-all-runs">Hide Run Failures</li>
                <li id="hide-all">Hide All Failures</li>
                <li id="show-success-runs">Show Successful Runs</li>
                <li id="show-all-runs">Show All Runs</li>
                <li id="show-all">Show All Results</li>
            </ul>
       </li>
    </ul>

    <!-- Contextual menu for SAD results -->

   <ul id="sadmenu-working" class="jeegoocontext cm_blue">
<?php
if ($local == 0)
{
?>
       <li id="shelx_download">Download Shelx Results</li>
<?php
}
?>
     <li>Hide/Show
        <ul>
           <li id="hide-this-sad">Hide This Entry</li>
           <li id="hide-all-sad">Hide All Failures</li>
           <li id="show-success-sads">Show Successful SAD Runs</li>
           <li id="show-all-sad">Show All SAD Runs</li>
       </ul>
     </li>
    </ul>


    <ul id="sadmenu-success" class="jeegoocontext cm_blue">
<?php
if ($local == 0)
{
?>
       <li>Download
         <ul>
           <li id="shelx_download">Download Shelx Results</li>
           <li id="sad_download">Download AutoMR Results</li>
         </ul>
       </li>
<?php
}
?>
       <li>Hide/Show
            <ul>
               <li id="hide-this-sad">Hide This Entry</li>
               <li id="hide-all-sad">Hide All Failures</li>
               <li id="show-success-sads">Show Successful SAD Runs</li>
               <li id="show-all-sad">Show All SAD Runs</li>
           </ul>
       </li>
    </ul>

	    <ul id="sadmenu-failed" class="jeegoocontext cm_blue">
	       <li>Hide/Show
	            <ul>
	               <li id="hide-this-sad">Hide This Entry</li>
	               <li id="hide-all-sad">Hide All Failures</li>
	               <li id="show-success-sads">Show Successful SAD Runs</li>
	               <li id="show-all-sad">Show All SAD Runs</li>
	           </ul>
	       </li>
	    </ul>



    <!-- Dialogs -->
    <div id='download-dialog'>Download Initiated<br>This can take some time...</div>
    <div id="dialog-generic"></div>
    <div id="dialog-transient">
        <div id="dialog-transient-success">
            <p></p>
        </div>
        <div id="dialog-transient-failure">
            <p></p>
        </div>
    </div>
    <!-- area to use for the downloading method -->
    <iframe src="" id="download-iframe" style="display:none;"></iframe>

</body>
</html>

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
    }
}
$_SESSION[data] = $_POST[data];
?>

<html>
  <head>
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
    <script src="http://www.google.com/jsapi"></script>
    <script>google.load("swfobject", "2.2", {uncompressed:true});</script>

    <script type="text/javascript">

    function load_images(number_images,image_repr,image_string){
        var server = "/fcgi-bin/iipsrv.fcgi";
        var image = image_string;
        var credit = image_repr;
        var flashvars = {
                server: server,
                image: image,
                navigation: true,
                credit: credit
        }
        var params = {
                scale: "noscale",
                bgcolor: "#000000",
                allowfullscreen: "true",
                allowscriptaccess: "always"
        }
        swfobject.embedSWF("js/IIPZoom.swf", "targetframe", "100%", "100%", "9.0.0","js/expressInstall.swf", flashvars, params);
    } //End of load_images
    </script>
<!--
        //alert(number_images);
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
-->
    <!-- Load up the javasript using google to make it faster remotely -->
    <!--<script src="http://www.google.com/jsapi"></script>-->
    <script>
      // Load jQuery
      google.load("jquery", "1.4.2");
      google.load("jqueryui", "1.7.2");
    </script>
    <!-- Load up the javascripts we use -->
    <script type="text/javascript" language="javascript" src="./js/flot/jquery.flot.js">              </script>
    <script type="text/javascript" language="javascript" src="./js/jquery.dataTables.min.js">    </script>
    <script type="text/javascript" language="javascript" src="./js/jquery.jeegoocontext.min.js"> </script>
    <script type="text/javascript" language="javascript" src="./js/thickbox.js">                 </script>
    <script type="text/javascript" language="javascript" src="./js/jquery.livequery.js">         </script>
  </head>

  <body>

  <table id="wrapper" height="100%">
    <tr>
      <td width="220pixels">
        <!-- Tabs -->
        <div class="tabs" id="tabs1">
          <ul>
            <li><a href="#tabs1-1">All</a></li>
            <li><a href="#tabs1-2">Snaps</a></li>
            <li><a href="#tabs1-3">Runs</a></li>
          </ul>
          <div id="tabs1-1">
            <h3 class="green">Snaps</h3>
            <div class="snap_menu_share_wrapper">
              <div id="snap_menu_share_in_process">
                <!-- HERE IS WHERE IN-PROCESS INFO WILL BE PLACED -->
              </div>
              <div id="snap_menu_share" class="snap_menu_share">
                <!-- HERE IS WHERE SNAPS WILL BE PUT BY DATABASE -->
              </div>
            </div>
            <h3 class="green">Runs</h3>
            <div class="run_menu_share_wrapper">
              <div id="run_menu_share" class="run_menu_share">
                <!-- HERE IS WHERE RUNS WILL BE PUT BY DATABASE -->
              </div>
            </div>
          </div>
          <div id="tabs1-2">
            <div class="snap_menu_wrapper">
              <div id="snap_menu_in_process">
                <!-- HERE IS WHERE IN-PROCESS INFO WILL BE PLACED -->
              </div>
              <div id="snap_menu" class="snap_menu">
                <!-- HERE IS WHERE SNAPS WILL BE PUT BY DATABASE -->
              </div>
            </div>
          </div>

          <div id="tabs1-3">
            <div class="run_menu_wrapper">
              <div id="run_menu_in_process">
                <!-- HERE IS WHERE IN-PROCESS INFO WILL BE PLACED -->
              </div>
              <div id="run_menu" class="run_menu">
                <!-- HERE IS WHERE RUNS WILL BE PUT BY DATABASE -->
              </div>
            </div>
          </div>
        </div>
      </td>

      <td width="100%">
        <div class="tabs" id="tabs2">
          <ul>
            <li><a href="#tabs2-1">Summary</a></li>
            <li><a href="#tabs2-2">Detail</a></li>
            <li><a href="#tabs2-3">Images</a></li>
            <li><a href="#tabs2-4">Plots</a></li>
            <li><a href="#tabs2-5">Ranked</a></li> 
          </ul>
          <div id="tabs2-1">
            <div id="summary" class="summary"></div>
          </div>
          <div id="tabs2-2">
            <div id="detail" class="detail">
              <!-- These sub-divs are for use in loading the integration results -->
              <div id="detail1"></div>
              <div id="detail2"></div>
              <div id="detail3"></div>
            </div>
          </div>
          <div id="tabs2-3">
            <div id="images" class="images">
              
              <div id="old_images">
              </div>

              <div id='mooviewer'>
                <!-- Now insert our iipmooviewer div -->
                <div style="width:100%;height:100%;left:auto;" id="targetframe" >
                </div>
              </div>

            </div>
          </div>
          <div id="tabs2-4">
            <div id="plots" class="plots"></div>
          </div>
          <div id="tabs2-5">
            <div id="ranked" class="ranked">
              <div id="container">
                <div id="auto_wrapper" class="dataTables_wrapper"> 
                  <table class="ranking" id="sort-table" border="1" cellpadding="0" cellspacing="0">
                    <thead align="center">
                      <tr>
                        <th class="sorting">Image</th>
                        <th class="sorting">sg</th>
                        <th class="sorting">a</th>
                        <th class="sorting">b</th>
                        <th class="sorting">c</th>
                        <th class="sorting">&alpha</th>
                        <th class="sorting">&beta</th>
                        <th class="sorting">&gamma</th>
                        <th class="sorting">mos</th>
                        <th class="sorting">res</th>
                        <th class="sorting">WebIce</th>
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
        <!-- End of Tabs -->
      </td>

      <td width="200pixels">
        <div class="tabs" id="tabs3">
          <ul>
            <li><a href="#tabs3-1">Controls</a></li>
          </ul>
          <div id="tabs3-1">
            <div id="controls" class="controls">
              <!-- HERE IS WHERE CONTROLS WILL BE PLACED -->

              <button style='width:100%' class="fg-button ui-state-default ui-corner-all" id="go_to_main" type="button">Main</button>
              <br>&nbsp;
              <a href="d_form.php?test=foo&datadir=<?php echo $_SESSION[data];?>&beamline=<?php echo $_POST[beamline];?>&height=650&width=570" class="thickbox" title="Modify Settings"><button style='width:100%' class="fg-button ui-state-default ui-corner-all" type="button" id="settings">Settings</button></a>
              <br>&nbsp;
              <button style='width:100%' class="fg-button ui-state-default ui-corner-all" type="button" id="merging">Merge</button>
              <br>&nbsp;
              <div id='download_active'><button class="fg-button ui-state-default ui-corner-all" type="button" id="download-active">Download Processing</button></div>
              <div id='image-control'>
                  Image<br>
                  <div id='image-control-1'></div>
                  <div id='image-control-2'></div>
                  <div id='image-control-3'>
                    <p><br><input id="checkbox.1" name="checkbox.1" type="checkbox">&nbsp;Predictions</input></p>
                  </div>
              </div>
              <div class="control-filler"></div> 

              <button style='width:100%' class="fg-button ui-state-default ui-corner-all" id="led_button" type="button">
                Remote Servers
                <div id='led_panel'>
                  <table>
                    <tr><td><button style='width:90px'><div id='controller'>Core</div></button></td></tr>
                    <tr><td><button style='width:90px'><div id='cluster'>Cluster</div></button></td></tr>
                    <tr><td><button style='width:90px'><div id='dataserver'>Data</div></button></td></tr> 
                  </table>
                </div>
              </button>

            </div>
          </div>
        </div>
        <!-- End of Tabs -->
      </td>
    </tr>
  </table>

  <script type='text/javascript'>

    my_ip        = 0;
    lastresultID = 0;
    lastrankID   = 0;
    lastcloudID  = 0;
    sortTable    = '' ;
    number_images   = 0;
    image_repr      = '';
    image_string    = '';
    image_mode      = 'NONE';
    image_shown     = 'False';
    // Is the cloud open for business? 1 = yes, 0 = no
    cloud_download  = '1';
    cloud_process   = '1';
    // Keep a count of downloads that are currently running
    downloads_active = 0;
    // Is this an administrator?
    admin = 'no';

    //Variables for modifying behavior based on state
    instance_local  = 'False';
    instance_active = 'False';
    waiting_for_cloud = 'False';

    function closeDownloadDialog(){
        if (downloads_active == 0) 
        {
            $('#download_active').slideToggle('slow');
        }
        var tmp = setTimeout(closedownloaddialog, 5000); 
    };
    function closedownloaddialog(){
        $('#download-dialog').dialog('close');
    }

    //
    // The main document ready function
    // 
    $(document).ready(function(){

        $('#download-dialog').dialog( { autoOpen: false,
                                        title: 'Download Initiated' });

        $('#snap_menu_in_process > div').jeegoocontext('inprocessmenu',{
                    livequery: true,
                    widthOverflowOffset: 0,
                    heightOverflowOffset: 1,
                    submenuLeftOffset: -4,
                    submenuTopOffset: -5,
                    onSelect: function(e, context){}
        });

        $('#snap_menu_share_in_process > div').jeegoocontext('inprocessmenu',{
                    livequery: true,
                    widthOverflowOffset: 0,
                    heightOverflowOffset: 1,
                    submenuLeftOffset: -4,
                    submenuTopOffset: -5,
                    onSelect: function(e, context){
                        if ($(context).attr('id'))
                        {
                            switch($(this).attr('id'))
                            {
                                case 'hide-this-process':
                                    //Hide immediately in the UI
                                    $('#snap_menu_share_in_process').find('#'+$(context).attr('id')).hide('slow'); //.remove();
                                    $('#snap_menu_in_process').find('#'+$(context).attr('id')).hide('slow'); //.remove();
                                    //Change database entry for display as hidden
                                    $.get('d_hide-this-process.php',{div_id : $(context).attr('id') });
                                    //
                                    break;
                            }
                        }
                    }
        });

        $('#snap_menu > a').jeegoocontext('snapmenu',{
                    livequery: true,
                    widthOverflowOffset: 0,
                    heightOverflowOffset: 1,
                    submenuLeftOffset: -4,
                    submenuTopOffset: -5,
                    onSelect: function(e, context){}
        });

        $('#snap_menu_share > a').jeegoocontext('snapmenu',{
                    livequery: true,
                    widthOverflowOffset: 0,
                    heightOverflowOffset: 1,
                    submenuLeftOffset: -4,
                    submenuTopOffset: -5,
                    onSelect: function(e, context){
                        if ($(context).attr('id') > 0)
                        {
                            switch($(this).attr('id'))
                            {
                                case 'hide-this-snap':
                                    //Hide immediately in the UI
                                    $('#snap_menu_share').find('#'+$(context).attr('id')).hide('slow'); //.remove();
                                    $('#snap_menu').find('#'+$(context).attr('id')).hide('slow'); //.remove();
                                    //Change database entry for display as hidden
                                    $.get('d_hide-this-snap.php',{res_id : $(context).attr('id') });
                                    //
                                    break;

                                case 'hide-all-snaps':
                                    //Delete the entries from the DOM
                                    $('#snap_menu_share').find('.grayed').hide('slow'); //.remove();
                                    $('#snap_menu').find('.grayed').hide('slow'); //.remove();     
                                    //Change the database entries  for display as hidden
                                    $.get('d_hide-snaps.php',{datadir : '<?php echo $_SESSION[data];?>' });
                                    //
                                    break;

                                case 'hide-all':
                                    //Remove the entries from the DOM
                                    $('#snap_menu_share').find('.grayed').hide('slow'); //.remove();
                                    $('#snap_menu').find('.grayed').hide('slow'); //.remove();
                                    $('#run_menu_share').find('.grayed').hide('slow'); //.remove();
                                    $('#run_menu').find('.grayed').hide('slow'); //.remove();
                                    //Change the database entries  for display as hidden
                                    $.get('d_hide-snaps.php',{datadir : '<?php echo $_SESSION[data];?>' });
                                    $.get('d_hide-runs.php',{datadir : '<?php echo $_SESSION[data];?>' });
                                    //
                                    break;

                                case 'show-success-snaps':
                                    //Change the database entries for display to show
                                    $.ajax({ async: false,
                                             url:  'd_show_success_snaps.php',
                                             data: 'datadir=<?php echo $_SESSION[data];?>' })
                                    //Remove all entries in the data areas
                                    $('#snap_menu_share').children().remove();
                                    $('#snap_menu').children().remove();
                                    $('#run_menu_share').children().remove();
                                    $('#run_menu').children().remove();
                                    //Re-load all the data
                                    lastresultID = 0;
                                    imagesRefresh('False');
                                    //
                                    break; 

                                case 'show-all-snaps':
                                    //Change the database entries for display to show   
                                    $.ajax({ async: false,
                                             url:   'd_show-snaps.php',
                                             data:  'datadir=<?php echo $_SESSION[data];?>' });
                                    //Remove all entries in the data areas
                                    $('#snap_menu_share').children().remove();
                                    $('#snap_menu').children().remove();
                                    $('#run_menu_share').children().remove();
                                    $('#run_menu').children().remove();
                                    //Re-load all the data
                                    lastresultID = 0;
                                    imagesRefresh('False'); 
                                    //
                                    break;
     
                                case 'show-all':
                                    //Change the database entries for display to show
                                    $.ajax({ async: true, 
                                             url:   'd_show-runs.php',
                                             data:  'datadir=<?php echo $_SESSION[data];?>' });
                                    $.ajax({ async: false,
                                             url:   'd_show-snaps.php',
                                             data:  'datadir=<?php echo $_SESSION[data];?>' });
                                    //Remove all entries in the data areas
                                    $('#snap_menu_share').children().remove();
                                    $('#snap_menu').children().remove();
                                    $('#run_menu_share').children().remove();
                                    $('#run_menu').children().remove();
                                    //Re-load all the data
                                    lastresultID = 0;
                                    imagesRefresh('False');
                                    //
                                    break;

                                case 'snap_settings':
                                    tb_show("Setings for "+$(context).text(),         "d_settings.php?height=620&width=550&result_id="+$(context).attr('id')+"&start_repr="+$(context).text());
                                    break;

                                case 'snap_header':
                                    tb_show("Header information for "+$(context).text(),"header.php?height=620&width=550&result_id="+$(context).attr('id')+"&start_repr="+$(context).text());
                                    break;

                                case 'snap_download_image':
                                    if (cloud_download == '1')
                                    {   
                                        //Request the download be processed
                                        $.get('get_download.php',{ datadir : '<?php echo $_SESSION[data];?>',
                                                                   id : $(context).attr('id'),
                                                                   type : 'downimage',
                                                                   ip : my_ip });
                                        //Open the dialog and remove the title bar
                                        $('#download-dialog').dialog('open')
                                            .parents(".ui-dialog")
                                            .find(".ui-dialog-titlebar")
                                            .remove();
                                        $('#download-dialog').dialog( "option", "height", "auto");
                                        waiting_for_cloud = 'True';
                                        closeDownloadDialog();
                                        downloads_active += 1;
                                    } else {
                                        alert('Sorry - downloading not currently enabled');
                                    }
                                    //
                                    break;
 
                                case 'snap_download_package':
                                    if (cloud_download == '1')
                                    {
                                        $.get('get_download.php',{ datadir : '<?php echo $_SESSION[data];?>',
                                                                   id : $(context).attr('id'),
                                                                   type : 'downpackage',
                                                                   ip : my_ip });                                    
                                        $('#download-dialog').dialog('open')
                                            .parents(".ui-dialog")
                                            .find(".ui-dialog-titlebar")
                                            .remove();
                                        $('#download-dialog').dialog( "option", "height", 'auto');
                                        waiting_for_cloud = 'True';
                                        closeDownloadDialog();
                                    } else {
                                        alert('Sorry - downloading not currently enabled');
                                    }
                                    //
                                    break;

                                case 'snap_reprocess':
                                    if (cloud_process == '1')
                                    {
                                        //popup a thickbox with the reprocessing
                                        tb_show("Reprocessing "+$(context).text(),"d_snap_reprocess.php?height=630&width=570&result_id="+$(context).attr('id')+"&start_repr="+$(context).text()+"&type=reprocess&ip="+my_ip);
                                    } else {
                                        alert('Sorry - processing not currently enabled');
                                    }
                                    //
                                    break;
                            }
                        } else {
                            alert("Reload the interface - you have a browser error!");
                        }
                    }
        });

        $('#run_menu > a').jeegoocontext('runmenu', {
                    livequery: true,
                    widthOverflowOffset: 0,
                    heightOverflowOffset: 1,
                    submenuLeftOffset: -4,
                    submenuTopOffset: -5,
                    onSelect: function(e, context){}
        });

        $('#run_menu_share > a').jeegoocontext('runmenu', {
                    livequery: true,
                    widthOverflowOffset: 0,
                    heightOverflowOffset: 1,
                    submenuLeftOffset: -4,
                    submenuTopOffset: -5,
                    onSelect: function(e, context){
                        if ($(context).attr('id') > 0)
                        {
                            switch($(this).attr('id'))
                            {
                                case 'hide-this-run':
                                    //Hide immediately in the UI
                                    $('#run_menu_share').find('#'+$(context).attr('id')).hide('slow'); //.remove();
                                    $('#run_menu').find('#'+$(context).attr('id')).hide('slow'); //.remove();
                                    //Change database entry for display as hidden
                                    $.get('d_hide-this-run.php',{res_id : $(context).attr('id') });
                                    //
                                    break;

                                case 'hide-all-runs':
                                    //Delete the entries from the DOM
                                    $('#run_menu_share').find('.grayed').hide('slow'); //.remove();
                                    $('#run_menu').find('.grayed').hide('slow'); //.remove();
                                    //Change the database entries  for display as hidden
                                    $.get('d_hide-runs.php',{datadir : '<?php echo $_SESSION[data];?>' });
                                    //
                                    break;

                                case 'hide-all':
                                    //Remove the entries from the DOM
                                    $('#snap_menu_share').find('.grayed').hide('slow'); //.remove();
                                    $('#snap_menu').find('.grayed').hide('slow'); //.remove();
                                    $('#run_menu_share').find('.grayed').hide('slow'); //.remove();
                                    $('#run_menu').find('.grayed').hide('slow'); //.remove();
                                    //Change the database entries  for display as hidden
                                    $.get('d_hide-snaps.php',{datadir : '<?php echo $_SESSION[data];?>' });
                                    $.get('d_hide-runs.php',{datadir : '<?php echo $_SESSION[data];?>' });
                                    //
                                    break;

                                case 'show-success-runs':
                                    //Change the database entries for display to show
                                    $.ajax({ async: false,
                                             url:  'd_show-success-runs.php',
                                             data: 'datadir=<?php echo $_SESSION[data];?>' })
                                    //Remove all entries in the data areas
                                    $('#snap_menu_share').children().remove();
                                    $('#snap_menu').children().remove();
                                    $('#run_menu_share').children().remove();
                                    $('#run_menu').children().remove();
                                    //Re-load all the data
                                    lastresultID = 0;
                                    imagesRefresh('False');
                                    //
                                    break;

                                case 'show-all-runs':
                                    //Change the database entries for display to show
                                    $.ajax({ async: false,
                                             url:   'd_show-runs.php',
                                             data:  'datadir=<?php echo $_SESSION[data];?>' });
                                    //Remove all entries in the data areas
                                    $('#snap_menu_share').children().remove();
                                    $('#snap_menu').children().remove();
                                    $('#run_menu_share').children().remove();
                                    $('#run_menu').children().remove();
                                    //Re-load all the data
                                    lastresultID = 0;
                                    imagesRefresh('False');
                                    //
                                    break;

                                case 'show-all':
                                    //Change the database entries for display to show
                                    $.ajax({ async: true, 
                                             url:   'd_show-runs.php',
                                             data:  'datadir=<?php echo $_SESSION[data];?>' });
                                    $.ajax({ async: false,
                                             url:   'd_show-snaps.php',
                                             data:  'datadir=<?php echo $_SESSION[data];?>' });
                                    //Remove all entries in the data areas
                                    $('#snap_menu_share').children().remove();
                                    $('#snap_menu').children().remove();
                                    $('#run_menu_share').children().remove();
                                    $('#run_menu').children().remove();
                                    //Re-load all the data
                                    lastresultID = 0;
                                    imagesRefresh('False');
                                    //
                                    break;

                                case 'run_settings':
                                    tb_show("Setings for "+$(context).text(),"d_settings.php?height=620&width=550&result_id="+$(context).attr('id')+"&start_repr="+$(context).text()+"&type=reprocess&ip="+my_ip);
                                    break;

                                case 'run_download_process':
                                    if (cloud_download == '1')
                                    {
                                        $.get('get_download.php',{ datadir : '<?php echo $_SESSION[data];?>',
                                                                   id : $(context).attr('id'),
                                                                   type : 'downproc',
                                                                   ip : my_ip });                                    
                                        $('#download-dialog').dialog('open')
                                            .parents(".ui-dialog")
                                            .find(".ui-dialog-titlebar")
                                            .remove();
                                        $('#download-dialog').dialog( "option", "height", 'auto');
                                        waiting_for_cloud = 'True';
                                        closeDownloadDialog();
                                    } else {
                                        alert('Sorry - downloading not currently enabled');
                                    }
                                    //
                                    break;

                                case 'run_download_image':
                                    if (cloud_download == '1')
                                    {
                                        $.get('get_download.php',{ datadir : '<?php echo $_SESSION[data];?>',
                                                                   id : $(context).attr('id'),
                                                                   type : 'downimage',
                                                                   ip : my_ip });
                                        $('#download-dialog').dialog('open')
                                            .parents(".ui-dialog")
                                            .find(".ui-dialog-titlebar")
                                            .remove();
                                        $('#download-dialog').dialog( "option", "height", 'auto');
                                        waiting_for_cloud = 'True';
                                        closeDownloadDialog();
                                    } else {
                                        alert('Sorry - downloading not currently enabled');
                                    }
                                    //
                                    break;

                                case 'run_download_package':
                                    if (cloud_download == '1') 
                                    {
                                        $.get('get_download.php',{ datadir : '<?php echo $_SESSION[data];?>',
                                                                   id : $(context).attr('id'),
                                                                   type : 'downpackage',
                                                                   ip : my_ip });
                                        $('#download-dialog').dialog('open')
                                          .parents(".ui-dialog")
                                          .find(".ui-dialog-titlebar")
                                          .remove();
                                        $('#download-dialog').dialog( "option", "height", 'auto');
                                        waiting_for_cloud = 'True';
                                        closeDownloadDialog();
                                    } else {
                                        alert('Sorry - downloading not currently enabled');
                                    }
                                    //
                                    break;

                                case 'run_reprocess':
                                    if (cloud_process == '1')
                                    {
                                        //popup a thickbox with the reprocessing
                                        tb_show("Reprocessing "+$(context).text(),"d_reprocess.php?height=630&width=570&result_id="+$(context).attr('id')+"&start_repr="+$(context).text()+"&type=reprocess&ip="+my_ip);
                                    } else {
                                        alert('Sorry - processing not currently enabled');
                                    }
                                    //
                                    break;
                            } //end of switch
                        } else {
                            alert("Reload the interface - you have a browser error!");
                        }
                    }
        });

        //Ranking datatable
        sortTable = $('#sort-table').dataTable({
                    "aoColumns": [ null,
                                   null,
                                   null,
                                   null,
                                   null,
                                   null,
                                   null,
                                   null,
                                   null,
                                   null,
                                   null,
                                   {"bVisible":false} ],
                    "aaSorting": [[ 10, "desc" ]],   
                    "bJQueryUI": true,   
                    "iDisplayLength": 25
        }); 
 
        // start the refreshing of images on the left
        timeoutID = setTimeout(GetInfoAndStart, 1);
      
        // Handler for click events on the ranking table
        $("#sort-table tbody").click(function(event) {
            //take highlight from other rows
            $(sortTable.fnSettings().aoData).each(function (){
                $(this.nTr).removeClass('row_selected');
            });
            //highlight the clicked row
            $(event.target.parentNode).addClass('row_selected');
            //get the result id from the hidden column of the table
            var res_id = sortTable.fnGetData(sortTable.fnGetPosition(event.target.parentNode))[11];

            //simulate a click on the snap_menu item which has this res_id
            //Make sure the selected from is in view
            $('.snap_menu_share_wrapper').animate({scrollTop: $('#snap_menu_share').find('#'+res_id).offset().top-$('.snap_menu_share').offset().top-100},500); 

            //Mark the current click as being viewed and clear the rest
            $("#snap_menu").children().removeClass("clicked");
            $("#run_menu").children().removeClass("clicked");
            $("#snap_menu_share").children().removeClass("clicked");
            $("#run_menu_share").children().removeClass("clicked");
            //$('#snap_menu').find('#'+res_id).addClass("clicked");
            $('#snap_menu_share').find('#'+res_id).addClass("clicked");
            //Load the data
            loadSnap(res_id);
        });

        //Tooltips for the sort table
        $('#sort-table thead th').each(function(){
            if ($(this).text() == 'WebIce') {
                this.setAttribute('title','Higher = Better');    
            }  
        });

        // Tabs
        $('#tabs1').tabs({remote:true});
        $('#tabs2').tabs({remote:true});
        $('#tabs3').tabs({remote:true});

        $('#tabs2').bind('tabsselect', function(event, ui) {
 	    if (ui.index == 2) {
                if (image_shown == 'False')
                {
                    image_shown = 'True';
                    if (image_mode == 'NEW')
                    {
                        $("#mooviewer").show();
                        $("#old_images").empty();
                        load_images(number_images,image_repr,image_string);
                    }
                }
            }
        });

        // load up the splash page
        $("#summary").load('splash.php');

        // Hide various elements 
        $('#download_active').hide();
        $('#mooviewer').hide(); 

        // The indicators for live usage
        $('#controller').prepend("<img src='css/images/LEDs/green-off-16.png'");
        $('#cluster').prepend("<img src='css/images/LEDs/green-off-16.png'");
        $('#dataserver').prepend("<img src='css/images/LEDs/green-off-16.png'");
        $('#led_button').hide();

        // hover states on the static widgets
        $('#dialog_link, ul#icons li').hover(
            function() { $(this).addClass('ui-state-hover'); },
            function() { $(this).removeClass('ui-state-hover'); }
        );

        // Void out normal context menu
        //React to clicks in the image tabs for snaps
        $('#snap_menu').delegate('a','click',function(e){  
          if( (!$.browser.msie && e.button == 0) || ($.browser.msie && e.button == 1) ) {
                var res_id = $(this).attr("id");
                //Mark the current click as being viewed and clear the rest
                $("#snap_menu").children().removeClass("clicked");
                $("#run_menu").children().removeClass("clicked");
                $("#snap_menu_share").children().removeClass("clicked");
                $("#run_menu_share").children().removeClass("clicked");         
                $("#snap_menu").find('#'+res_id).addClass("clicked");
                $("#snap_menu_share").find('#'+res_id).addClass("clicked");
                
                //Load the data
                loadSnap(res_id);
 
                //Update the highlighting in the ranking table
                //take highlight from other rows
                $(sortTable.fnSettings().aoData).each(function (){
                    if ($(this._aData)[11] == res_id)
                    {
                        $(this.nTr).addClass('row_selected');
                    } else {
                        $(this.nTr).removeClass('row_selected');
                    }
                });
                return false;
            } 
        });

        $('#run_menu').delegate('a','click',function(e){
            if( (!$.browser.msie && e.button == 0) || ($.browser.msie && e.button == 1) ) {
                //Mark the current click as being viewed and clear the rest
                $("#snap_menu").children().removeClass("clicked");
                $("#run_menu").children().removeClass("clicked");
                $("#snap_menu_share").children().removeClass("clicked");
                $("#run_menu_share").children().removeClass("clicked");
                $(this).addClass("clicked");
                //Load the data
                loadRun($(this).attr("id"));
            } 
        });  

        $('#snap_menu_share').delegate('a','click',function(e){
            var res_id = $(this).attr("id");
            if( (!$.browser.msie && e.button == 0) || ($.browser.msie && e.button == 1) ) {
                //Mark the current click as being viewed and clear the rest
                $("#snap_menu").children().removeClass("clicked");
                $("#run_menu").children().removeClass("clicked");
                $("#snap_menu_share").children().removeClass("clicked");
                $("#run_menu_share").children().removeClass("clicked");
                $("#snap_menu").find('#'+res_id).addClass("clicked");
                $("#snap_menu_share").find('#'+res_id).addClass("clicked");
                //Load the data
                loadSnap(res_id);

                //Update the highlighting in the ranking table
                //take highlight from other rows
                $(sortTable.fnSettings().aoData).each(function (){
                    if ($(this._aData)[11] == res_id)
                    {
                        $(this.nTr).addClass('row_selected');
                    } else {
                        $(this.nTr).removeClass('row_selected');
                    }
                });
            } 
        }); 

        $('#run_menu_share').delegate('a','click',function(e){
            if( (!$.browser.msie && e.button == 0) || ($.browser.msie && e.button == 1) ) {
                //Mark the current click as being viewed and clear the rest
                $("#snap_menu").children().removeClass("clicked");
                $("#run_menu").children().removeClass("clicked");
                $("#snap_menu_share").children().removeClass("clicked");
                $("#run_menu_share").children().removeClass("clicked");
                $(this).addClass("clicked");
                //Load the data
                loadRun($(this).attr("id"));
            } 
        }); 

        //React to control button presses  
        $('#go_to_main').click(function () { 
            document.location.href = 'main.php';
        });

    });
   
    //grab the IP address, etc
    function GetInfoAndStart(){
       //Get the computer's ip address
       my_ip = "<?php echo $_SERVER['REMOTE_ADDR'];?>"; 
       // start monitoring the status
       var timeoutID = setTimeout(statusMonitor, 15000);
       // now refresh for 1st time
       var timeoutID1 = setTimeout(imagesRefresh, 1000);
       // start monitoring the cloud
       var timeoutID3 = setTimeout(cloudMonitor, 10000);
       // start looking for processes going
       var timeoutID4 = setTimeout(processesRefresh,5000);
    };

    //refresh the snaps and runs on the left
    function imagesRefresh(again) {
        //update the snaps and runs
        prevlastresultID = lastresultID;
        $.getJSON("d_get_results.php?datadir=<?php echo $_SESSION[data];?>&id="+lastresultID, function(json) {
            if(json.length)
            {
                for(i=0; i < json.length-1; i=i+4)
                {
                    if (json[i] == "single")
                    {
                        if (json[i+1] != 'hide')
                        {
                            $('#snap_menu').prepend(json[i+2]);
                            $('#snap_menu_share').prepend(json[i+2]);
                            if (json[i+3] == "FAILED")
                            {
                                $('#snap_menu').children(":first").removeClass("image").addClass("grayed");
                                $('#snap_menu_share').children(":first").removeClass("image").addClass("grayed");
                            }
                            else if (json[i+3] == "REPROCESS")
                            {
                                $('#snap_menu').children(":first").removeClass("image").addClass("reprocess");
                                $('#snap_menu_share').children(":first").removeClass("image").addClass("reprocess");
                            }
                        }
                    }
                    else if (json[i] == "pair")
                    {
                        if (json[i+1] != 'hide')
                        {
                            $('#snap_menu').prepend(json[i+2]);
                            $('#snap_menu_share').prepend(json[i+2]);
                            if (json[i+3] == "FAILED")
                            {
                                $('#snap_menu').children(":first").removeClass("image").addClass("grayed");
                                $('#snap_menu_share').children(":first").removeClass("image").addClass("grayed");
                            }
                            else if (json[i+3] == "REPROCESS")
                            {
                                $('#snap_menu').children(":first").removeClass("image").addClass("reprocess");
                                $('#snap_menu_share').children(":first").removeClass("image").addClass("reprocess");
                            }
                        }
                    }
                    else if (json[i] == "run")
                    {
                        if (json[i+1] != 'hide')
                        {
                            $('#run_menu').prepend(json[i+2]);
                            $('#run_menu_share').prepend(json[i+2]);
                            if (json[i+3] == "FAILED")
                            {
                                $('#run_menu').children(":first").removeClass("image").addClass("grayed");
                                $('#run_menu_share').children(":first").removeClass("image").addClass("grayed");
                            }
                            else if (json[i+3] == "REPROCESS")
                            {
                                $('#run_menu').children(":first").removeClass("image").addClass("reprocess");
                                $('#run_menu_share').children(":first").removeClass("image").addClass("reprocess");
                            }
                        }
                    }
                }
                lastresultID = json[i];

                // Call a single refresh of the rankings
                if ( prevlastresultID < lastresultID )
                {
                    rankingRefresh();
                }
            }

            //Don't refresh if this is a one-off call
            if (again != 'False')
            {
                //Refresh again, flexibly
                if ( instance_active == 'True')
                {
                    //alert("Instance Active");
                    my_timeout_id = setTimeout(imagesRefresh, 30000);
                }
                else
                {
                    my_timeout_id = setTimeout(imagesRefresh, 30000);
                }
            }
        });
    };

    // Fill the ranking table
    function rankingRefresh() {
        //check the ranking results
        my_rank_id = lastrankID;
        $.getJSON("get_rankings.php?datadir=<?php echo $_SESSION[data];?>&id="+lastrankID, function(json) {
            if(json.length > 1) {
                for(i=0; i < json.length-1; i=i+12) {
                    sortTable.fnAddData([json.slice(i,i+12)],false);
                    lastrankID = json[i+11];
                }
                sortTable.fnDraw();
            }
            //"Intelligent" ranking refreshing
            if (my_rank_id < lastrankID)
            {
                my_timeout_id = setTimeout(rankingRefresh, 1000);
            }
        });
    };

    //refresh the display of currently active processes
    function processesRefresh(again) {
        //update the in process display
        $.getJSON("d_get_processes.php?datadir=<?php echo $_SESSION[data];?>", function(json) {
            if(json.length)
            {
                for(i=0; i < json.length-1; i=i+5)
                {
                    if (json[i] == "single")
                    {
                        if (json[i+1] == 'show')
                        {
                            // If the process is not displayed, add it
                            if (! $('#snap_menu_share_in_process').find('#'+json[i+2]).length)
                            {
                                $('#snap_menu_in_process').prepend(json[i+4]);
                                $('#snap_menu_share_in_process').prepend(json[i+4]);
                            }
                        } else {
                            $('#in_process_'+json[i+2]).remove();
                        }
                    }
                    if (json[i] == "pair")
                    {
                        if (json[i+1] == 'show')
                        {
                            // If the process is not displayed, add it
                            if (! $('#snap_menu_share_in_process').find('#'+json[i+2]).length)
                            {
                                $('#snap_menu_in_process').prepend(json[i+4]);
                                $('#snap_menu_share_in_process').prepend(json[i+4]);
                            }
                        } else {
                            $('#in_process_'+json[i+2]).remove();
                        }
                    }
                }
            }

            //Don't refresh if this is a one-off call
            if (again != 'False')
            {
                //Refresh again, flexibly
                if ( instance_active == 'True')
                {
                    my_timeout_id = setTimeout(processesRefresh, 30000);
                }
                else
                {
                    my_timeout_id = setTimeout(processesRefresh, 30000);
                }
            }
        });
    };

    //Update the status readout
    function statusMonitor() {
        $.getJSON("get_instance_info.php?datadir=<?php echo $_SESSION[data]; ?>&ip=<?php echo $_SERVER['REMOTE_ADDR'];?>", function(json) {
            //alert(json);
            instance_active = json[0];
            instance_local  = json[1];

            if (instance_active == 'True')
            //This is an active directory
            {
                $('#led_button').show();	
                $.getJSON("d_get_status.php?beamline=<?php echo $_POST[beamline];?>", function(json) {
                    my_beamline    = json[0];
                    dataserver_age = json[1];
                    controller_age = json[2];
                    cluster_age    = json[3];

                    if ( dataserver_age < 12 )
                    {
                        $('#dataserver').children().first().remove();
                        $('#dataserver').prepend("<img src='css/images/LEDs/green-on-16.png'");
                    } 
                    else if ( dataserver_age < 20 )
                    {
                        $('#dataserver').children().first().remove();
                        $('#dataserver').prepend("<img src='css/images/LEDs/yellow-on-16.png'");
                    }
                    else
                    {
                        $('#dataserver').children().first().remove();
                        $('#dataserver').prepend("<img src='css/images/LEDs/red-on-16.png'");
                    }

                    if ( controller_age < 12 )
                    {
                        $('#controller').children().first().remove();
                        $('#controller').prepend("<img src='css/images/LEDs/green-on-16.png'");
                    }
                    else if ( controller_age < 20 )
                    {
                        $('#controller').children().first().remove();
                        $('#controller').prepend("<img src='css/images/LEDs/yellow-on-16.png'");
                    }
                    else
                    {
                        $('#controller').children().first().remove();
                        $('#controller').prepend("<img src='css/images/LEDs/red-on-16.png'");
                    }

                    if ( cluster_age < 12 )
                    {
                        $('#cluster').children().first().remove();
                        $('#cluster').prepend("<img src='css/images/LEDs/green-on-16.png'");
                    }
                    else if ( cluster_age < 20 )
                    {
                        $('#cluster').children().first().remove();
                        $('#cluster').prepend("<img src='css/images/LEDs/yellow-on-16.png'");
                    }

                    else
                    {
                        $('#cluster').children().first().remove();
                        $('#cluster').prepend("<img src='css/images/LEDs/red-on-16.png'");
                    }

                    //trigger again
                    timeoutID = setTimeout(statusMonitor,30000);
                });
            }
            else
            //This is not an active directory - so update less frequently
            {
                $('#led_panel').hide();
                timeoutID = setTimeout(statusMonitor,100000);
            }
        });
    };

    function cloudMonitor() {
        //check the cloud results
        $.getJSON("d_get_cloud.php?datadir=<?php echo $_SESSION[data];?>&user=<?php echo $_POST[user];?>&trip_id=<?php echo $_POST[trip_id]; ?>&ip_address="+my_ip+"&id="+lastcloudID, function(json) {
            if(json.length > 1)
            {
              for(i=0; i < json.length-1; i=i+3)
              {
                  if (json[i] == "download")
                  {
                      $('#download-iframe').attr("src",json[i+1]);
                      $.getJSON("mark_cloud.php?id="+json[i+3]);
                      downloads_active -= 1;
                      if (downloads_active == 0)
                      {
                          $('#download_active').slideToggle("slow");
                          waiting_for_cloud = 'False';
                      }
                  }
                  else
                  {
                      if (json[i+1] == '1')
                      {
                          $('#snap_download_top').css('color','white');
                          $('#snap_download_image').css('color','white');
                          $('#snap_download_package').css('color','white');
                          $('#run_download_top').css('color','white');
                          $('#run_download_image').css('color','white');
                          $('#run_download_process').css('color','white');
                          $('#run_download_package').css('color','white');
                          cloud_download = '1';
                      }
                      else
                      {
                          $('#snap_download_top').css('color','red');
                          $('#snap_download_image').css('color','red');
                          $('#snap_download_package').css('color','red');
                          $('#run_download_top').css('color','red');
                          $('#run_download_image').css('color','red');
                          $('#run_download_process').css('color','red');
                          $('#run_download_package').css('color','red');
                          cloud_download = '0';
                      }
                      if (json[i+2] == '1')
                      {
                         $('#snap_reprocess').css('color','white');
                         $('#run_reprocess').css('color','white');
                         $('#simple-merge').css('color','white');
                         cloud_process = '1';
                      }
                      else
                      {
                         $('#snap_reprocess').css('color','red');
                         $('#run_reprocess').css('color','red');
                         $('#simple-merge').css('color','red');
                         cloud_process = '0';
                      }

                  }
              }
              lastcloudID = 0;
            }
            //fire again - if we are expecting something - 5sec, if not - 60 sec
            if ( waiting_for_cloud == 'True' )
            {
                var my_timeout_id = setTimeout(cloudMonitor, 5000);
            }
            else
            {
                var my_timeout_id = setTimeout(cloudMonitor, 5000);
            }
        });
    };





    //upon click, load up the data for the snap and fill the pages
    function loadSnap(my_res_id) {
      $.getJSON("get_result_data.php?res_id="+my_res_id+"&datadir=<?php echo $_SESSION[data]; ?>&trip_id=<?php echo $_POST[trip_id]; ?>", function(json) {
        if (json.length) {
 	  $("#summary").load(json[1]);
          $("#detail").empty(); 
          $("#detail").load(json[2]);
          image_mode    = json[3][0];
          if (image_mode == 'OLD')
          {
            image_string  = json[3][1];
            $("#mooviewer").hide();
            $("#old_images").empty(); 
            $("#old_images").append(image_string);
          }
          else if (image_mode == 'NEW') 
          {
            //alert(json[3]);
            number_images = json[3][1];
            image_repr    = json[3][2];
            image_string  = json[3][3];
            if ($('#tabs2').tabs().tabs('option', 'selected') == 2) 
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
          $("#plots").load(json[4]);
        }   
      });
    };

    //upon click, load up the data for the run and fill the pages
    function loadRun(my_res_id) {
      $.getJSON("get_result_data.php?res_id="+my_res_id+"&datadir=<?php echo $_SESSION[data]; ?>&trip_id=<?php echo $_POST[trip_id]; ?>", function(json) {
        if (json.length) { 
          // Load the summary display
          $("#summary").empty();
          $("#summary").load(json[1]); 
          // Load the detail display
          $("#detail").empty();
          $("#detail").html("<div id='container'><div id='detail1'></div> <div id='detail2'></div> <div id='detail3'></div></div>");
          $('#detail1').load(json[2][0], function(){
             $('#detail1').html("<pre>"+$('#detail1').html()+"</pre>");
          });
          $('#detail2').load(json[2][1], function(){
             $('#detail2').html("<pre>"+$('#detail2').html()+"</pre>");
          });
          $('#detail3').load(json[2][2], function(){
             $('#detail3').html("<pre>"+$('#detail3').html()+"</pre>");
          });
          // Load the images - none right now
          $("#mooviewer").hide();
          $("#old_images").load('run_images.php');
          // Load the plots
          $("#plots").load(json[4]);
        }   
      });
    };
    //(jQuery);


</script>

    <!--  Context menus -->
    <ul id='inprocessmenu' class="jeegoocontext cm_blue">
        <li id='hide-this-process'>Hide this process</li>
    </ul>


    <ul id="snapmenu" class="jeegoocontext cm_blue">
        <li>Hide
             <ul>
                <li id="hide-this-snap">This Entry</li>
                <li id="hide-all-snaps">Snap Failures</li>
                <li id="hide-all">All Failures</li>
            </ul>
       </li>
       <li>Show
            <ul>
                <li id="show-success-snaps">Successful Snaps</li>
                <li id="show-all-snaps">All Snaps</li>
                <li id="show-all">All Results</li>
            </ul>
       </li>
        <li>View
            <ul>
                <li id="snap_settings">Settings</li>
                <li id="snap_header">Header Info</li>
            </ul>
        </li>
        <li id="snap_reprocess">Reprocess</li> 
        <li id='snap_download_top'>Download
            <ul>
                <li id="snap_download_image">Image(s)</li>
                <li id="snap_download_package">All</li>
            </ul>
        </li>
        <!-- <li>Report</li> -->
    </ul>    
   
    <ul id="runmenu" class="jeegoocontext cm_blue">
        <li>Hide
             <ul>
                <li id="hide-this-run">This Entry</li>
                <li id="hide-all-runs">Run Failures</li>
                <li id="hide-all">All Failures</li>
            </ul>
       </li>
       <li>Show
            <ul>
                <li id="show-success-runs">Successful Runs</li>
                <li id="show-all-runs">All Runs</li>
                <li id="show-all">All Results</li>
            </ul>
       </li>
       <li id="run_settings">View Settings</li>
       <li id="run_reprocess">Reprocess</li> 
       <li>Merge
           <ul>
               <li id="simple-merge">Simple Merge</li>
               <li id="go-to-merge">Merging Workbench</li>
           </ul>
       </li>   
       <li id="run_download_top">Download
           <ul>
               <li id="run_download_image">Images</li>
               <li id="run_download_process">Processed Data</li> 
               <li id="run_download_package">All</li>
           </ul>
       </li>
       <!-- <li>Report</li> -->
    </ul>

    <!-- Dialogs -->
    <div id='download-dialog'>Download Initiated<br>This can take some time...</div>
 
    <!-- area to use for the downloading method -->
    <iframe src="" id="download-iframe" style="display:none;"></iframe>

</body>
</html>

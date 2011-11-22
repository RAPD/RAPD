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
    <link type="text/css" href="css/thickbox.css"                             rel="stylesheet" />
    <link type="text/css" href="css/ndemo_table.css"                          rel="stylesheet" />
    <link type="text/css" href="css/ndemo_page.css"                           rel="stylesheet" />
    <link type="text/css" href="css/south-street/njquery-ui-1.7.2.custom.css" rel="stylesheet" />
    <link type="text/css" href="css/cm_blue/style.css"                        rel="stylesheet" />

    <!-- css for the image viewer -->
    <link type="text/css" href="css/iip.compressed.css"                       rel="stylesheet" /> 
    <link type="text/css" href="css/blending.css"                             rel="stylesheet" />  

    <!-- done with image viewer css -->
    <link type="text/css" href="css/nrapd.css"                                 rel="stylesheet" />

    <!-- Load up the MooTools Stuff -->
    <!-- Load up the javasript using google to make it faster remotely -->
    <script src="http://www.google.com/jsapi"></script>
    <script>google.load("mootools", "1.2.4", {uncompressed:true});</script>
    <script type="text/javascript" src="./js/mootools-1.2-more.js"></script> 
    <script type="text/javascript" src="./js/iipmooviewer-1.3_fm.js"></script>
    <script type="text/javascript" src="./js/moocanvas-compressed.js"></script>

    <script type="text/javascript">

    function load_images(number_images,image_repr,image_string){
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

    <!-- Load up the javasript using google to make it faster remotely -->
    <!--<script src="http://www.google.com/jsapi"></script>-->
    <script>
      // Load jQuery
      google.load("jquery", "1.4.2");
      google.load("jqueryui", "1.7.2");
    </script>

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
              <div id="snap_menu" class="snap_menu">
                <!-- HERE IS WHERE SNAPS WILL BE PUT BY DATABASE -->
              </div>
            </div>
          </div>

          <div id="tabs1-3">
            <div class="run_menu_wrapper">
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
            <li><a href="#tabs2-1">Parsed</a></li>
            <li><a href="#tabs2-2">Full</a></li>
            <li><a href="#tabs2-3">Images</a></li>
            <li><a href="#tabs2-4">Plots</a></li>
            <li><a href="#tabs2-5">Ranked</a></li> 
          </ul>
          <div id="tabs2-1">
            <div id="parsed" class="parsed"></div>
          </div>
          <div id="tabs2-2">
            <div id="full" class="full">
              <!-- These sub-divs are for use in loading the integration results -->
              <div id="full1"></div>
              <div id="full2"></div>
              <div id="full3"></div>
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
              <br>&nbsp
              <a href="d_form.php?test=foo&datadir=<?php echo $_SESSION[data];?>&beamline=<?php echo $_POST[beamline];?>&height=650&width=570" class="thickbox" title="Modify Settings"><button style='width:100%' class="fg-button ui-state-default ui-corner-all" type="button" id="settings">Settings</button><a>
              <br>&nbsp
              <!-- <div id='beamline_access'></div> -->
              <div id='download_active'><button class="fg-button ui-state-default ui-corner-all" type="button" id="download-active">Download Processing</button></div>

              <div class="control-filler"></div> 

              <button style='width:100%' class="fg-button ui-state-default ui-corner-all" id="led_button" type="button">
              Remote Servers
              <div id='led_panel'>
                <table>
                  <tr><td><button style='width:90px'><div id='controller'>Controller</div></button></td></tr>
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
  <!-- Load up the javascripts we use -->
  <script type="text/javascript" language="javascript" src="./js/flot/jquery.flot.js">              </script>
  <script type="text/javascript" language="javascript" src="./js/jquery.dataTables.min.js">    </script>
  <script type="text/javascript" language="javascript" src="./js/jquery.jeegoocontext.min.js"> </script>
  <script type="text/javascript" language="javascript" src="./js/thickbox.js">                 </script>
  <script type="text/javascript" language="javascript" src="./js/jquery.livequery.js">         </script>
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
    admin = 'no';

    //Variables for modifying behavior based on state
    instance_local  = 'False';
    instance_active = 'False';
    waiting_for_cloud = 'False';

    //
    // The main document ready function
    // 
    $(document).ready(function(){

        $('.snap_menu > a').jeegoocontext('snapmenu',{
                    livequery: true,
                    widthOverflowOffset: 0,
                    heightOverflowOffset: 1,
                    submenuLeftOffset: -4,
                    submenuTopOffset: -5,
                    onSelect: function(e, context){}
        });

        $('.snap_menu_share > a').jeegoocontext('snapmenu',{
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
                                    $('#snap_menu_share').find('.grayed').remove();
                                    $('#snap_menu').find('.grayed').remove();     
                                    //Change the database entries  for display as hidden
                                    $.get('d_hide-snaps.php',{datadir : '<?php echo $_SESSION[data];?>' });
                                    //
                                    break;

                                case 'hide-all':
                                    //Remove the entries from the DOM
                                    $('#snap_menu_share').find('.grayed').remove();
                                    $('#snap_menu').find('.grayed').remove();
                                    $('#run_menu_share').find('.grayed').remove();
                                    $('#run_menu').find('.grayed').remove();
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
                                    imagesRefresh();
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
                                    imagesRefresh(); 
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
                                    imagesRefresh();
                                    //
                                    break;

                                case 'settings':
                                    tb_show("Setings for "+$(context).text(),         "d_settings.php?height=620&width=550&result_id="+$(context).attr('id')+"&start_repr="+$(context).text());
                                    break;

                                case 'header':
                                    tb_show("Header information for "+$(context).text(),"header.php?height=620&width=550&result_id="+$(context).attr('id')+"&start_repr="+$(context).text());
                                    break;

                                case 'download_image':
                                    $.getJSON("get_download.php?datadir=<?php echo $_SESSION[data];?>&id="+$(context).attr('id')+"&type=downimage&ip="+my_ip);
                                    $('#dialog').dialog('open')
                                      .parents(".ui-dialog")
                                      .find(".ui-dialog-titlebar")
                                      .remove();
                                    waiting_for_cloud = 'True';
                                    break;
 
                                case 'download_package':
                                    $.getJSON("get_download.php?datadir=<?php echo $_SESSION[data];?>&id="+$(context).attr('id')+"&type=downpackage&ip="+my_ip);
                                    $('#dialog').dialog('open')
                                      .parents(".ui-dialog")
                                      .find(".ui-dialog-titlebar")
                                      .remove();
                                    waiting_for_cloud = 'True';
                                    break;

                                case 'reprocess':
                                    //popup a thickbox with the reprocessing
                                    tb_show("Reprocessing "+$(context).text(),"d_reprocess.php?height=630&width=570&result_id="+$(context).attr('id')+"&start_repr="+$(context).text()+"&type=reprocess&ip="+my_ip);
                                    break;
                            }
                        } else {
                            alert("Reload the interface - you have a browser error!");
                        }
                    }
        });

        $('.run_menu > a').jeegoocontext('runmenu', {
                    livequery: true,
                    widthOverflowOffset: 0,
                    heightOverflowOffset: 1,
                    submenuLeftOffset: -4,
                    submenuTopOffset: -5,
                    onSelect: function(e, context){}
        });

        $('.run_menu_share > a').jeegoocontext('runmenu', {
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
                                    $('#run_menu_share').find('.grayed').remove();
                                    $('#run_menu').find('.grayed').remove();
                                    //Change the database entries  for display as hidden
                                    $.get('d_hide-runs.php',{datadir : '<?php echo $_SESSION[data];?>' });
                                    //
                                    break;

                                case 'hide-all':
                                    //Remove the entries from the DOM
                                    $('#snap_menu_share').find('.grayed').remove();
                                    $('#snap_menu').find('.grayed').remove();
                                    $('#run_menu_share').find('.grayed').remove();
                                    $('#run_menu').find('.grayed').remove();
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
                                    imagesRefresh();
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
                                    imagesRefresh();
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
                                    imagesRefresh();
                                    //
                                    break;

                                case 'settings':
                                    tb_show("Setings for "+$(context).text(),"d_settings.php?height=620&width=550&result_id="+$(context).attr('id')+"&start_repr="+$(context).text()+"&type=reprocess&ip="+my_ip);
                                    break;

                                case 'download_process':
                                    $.getJSON("get_download.php?datadir=<?php echo $_SESSION[data];?>&id="+$(context).attr('id')+"&type=downproc&ip="+my_ip);
                                    $('#dialog').dialog('open')
                                      .parents(".ui-dialog")
                                      .find(".ui-dialog-titlebar")
                                      .remove();
                                    waiting_for_cloud = 'True';
                                    break;

                                case 'download_image':
                                    $.getJSON("get_download.php?datadir=<?php echo $_SESSION[data];?>&id="+$(context).attr('id')+"&type=downimage&ip="+my_ip);
                                    $('#dialog').dialog('open')
                                      .parents(".ui-dialog")
                                      .find(".ui-dialog-titlebar")
                                      .remove();
                                    waiting_for_cloud = 'True';
                                    break;

                                case 'download_package':
                                    $.getJSON("get_download.php?datadir=<?php echo $_SESSION[data];?>&id="+$(context).attr('id')+"&type=downpackage&ip="+my_ip);
                                    $('#dialog').dialog('open')
                                      .parents(".ui-dialog")
                                      .find(".ui-dialog-titlebar")
                                      .remove();
                                    waiting_for_cloud = 'True';
                                    break;

                                case 'reprocess':
                                    //popup a thickbox with the reprocessing
                                    tb_show("Reprocessing "+$(context).text(),"d_reprocess.php?height=630&width=570&result_id="+$(context).attr('id')+"&start_repr="+$(context).text()+"&type=reprocess&ip="+my_ip);
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
            update_snap(res_id);
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
        $("#parsed").load('splash.php');

        // Hide various elements 
        $('#download_active').hide();
        $('#mooviewer').hide(); 

        // The indicators for live usage
        $('#controller').prepend("<img src='css/images/LEDs/green-off-16.png'");
        $('#cluster').prepend("<img src='css/images/LEDs/green-off-16.png'");
        $('#dataserver').prepend("<img src='css/images/LEDs/green-off-16.png'");
        $('#led_button').hide();

        // The download dialog 
        $('#dialog').dialog( {
       	    autoOpen: false,
//          open: function() { 
//            closeDialog(); 
//          },
            show: 'slide'
//          hide: 'clip'
        });

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
                update_snap(res_id);
 
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
                update_run($(this).attr("id"));
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
                update_snap(res_id);

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
                update_run($(this).attr("id"));
            } 
        }); 

        //React to control button presses  
        $('#go_to_main').click(function () { 
            document.location.href = 'main.php';
        });

    });
   


    //refresh the snaps and runs on the left
    function imagesRefresh() {
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
                                $('#snap_menu').children(":first").removeClass("image"); 
                                $('#snap_menu').children(":first").addClass("grayed"); 
                                $('#snap_menu_share').children(":first").removeClass("image"); 
                                $('#snap_menu_share').children(":first").addClass("grayed"); 
                            }
                            else if (json[i+3] == "REPROCESS")
                            {
                                $('#snap_menu').children(":first").removeClass("image");
                                $('#snap_menu').children(":first").addClass("reprocessed");
                                $('#snap_menu_share').children(":first").removeClass("image");
                                $('#snap_menu_share').children(":first").addClass("reprocessed");
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
                                $('#snap_menu').children(":first").removeClass("image"); 
                                $('#snap_menu').children(":first").addClass("grayed"); 
                                $('#snap_menu_share').children(":first").removeClass("image"); 
                                $('#snap_menu_share').children(":first").addClass("grayed"); 
                            }
                            else if (json[i+3] == "REPROCESS")
                            {
                                $('#snap_menu').children(":first").removeClass("image");
                                $('#snap_menu').children(":first").addClass("reprocessed");
                                $('#snap_menu_share').children(":first").removeClass("image");
                                $('#snap_menu_share').children(":first").addClass("reprocessed");
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
                                $('#run_menu').children(":first").removeClass("image"); 
                                $('#run_menu').children(":first").addClass("grayed"); 
                                $('#run_menu_share').children(":first").removeClass("image"); 
                                $('#run_menu_share').children(":first").addClass("grayed"); 
                            }
                            else if (json[i+3] == "REPROCESS")
                            {
                                $('#run_menu').children(":first").removeClass("image");
                                $('#run_menu').children(":first").addClass("reprocessed");
                                $('#run_menu_share').children(":first").removeClass("image");
                                $('#run_menu_share').children(":first").addClass("reprocessed");
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

            //Refresh again, flexibly
            if ( instance_active == 'True')
            {
                my_timeout_id = setTimeout(imagesRefresh, 3000);
            }
            else
            {
                my_timeout_id = setTimeout(imagesRefresh, 30000);
            }
        });
    };


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
            //alert(my_rank_id+"  "+lastrankID);
            if (my_rank_id < lastrankID)
            {
                //alert("refresh soon");
                my_timeout_id = setTimeout(rankingRefresh, 1000);
            }
        });
    };

    function cloudMonitor() {
        //check the cloud results
        $.getJSON("get_cloud.php?datadir=<?php echo $_SESSION[data];?>&user=<?php echo $_POST[user];?>&trip_id=<?php echo $_POST[trip_id]; ?>&ip_address="+my_ip+"&id="+lastcloudID, function(json) {
            if(json.length > 1) 
            {
              for(i=0; i < json.length-1; i=i+3) 
              {
                  if (json[i] == "download") 
                  {
                      $('#download-iframe').attr("src",json[i+1]);
                      $.getJSON("mark_cloud.php?id="+json[i+3]); 
                      $('#download_active').hide("slow");
                  }
              }
              lastcloudID = 0;
            }
            //fire again - if we are expecting something - 5sec, if not - 60 sec
            if ( waiting_for_cloud == 'True' )
            {
                my_timeout_id = setTimeout(cloudMonitor, 5000);
            }
            else
            {
                my_timeout_id = setTimeout(cloudMonitor, 60000);
            }
        });
    };


    //grab the IP address, etc
    function GetInfoAndStart(){
       //Get the computer's ip address
       my_ip = "<?php echo $_SERVER['REMOTE_ADDR'];?>"; 
       // start monitoring the status
       timeoutID = setTimeout(statusMonitor, 50);
       // now refresh for 1st time
       timeoutID1 = setTimeout(imagesRefresh, 1000);
       // Handle the user type                         
       //timeoutID2 = setTimeout(setUserType, 50);
       // start monitoring the cloud
       timeoutID3 = setTimeout(cloudMonitor, 10000);
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
                $.getJSON("get_status.php?beamline=<?php echo $_POST[beamline];?>", function(json) {
                    my_beamline    = json[0];
                    dataserver_age = json[1];
                    controller_age = json[2];
                    cluster_age    = json[3];

                    if ( dataserver_age < 120 )
                    {
                        $('#dataserver').children().first().remove();
                        $('#dataserver').prepend("<img src='css/images/LEDs/green-on-16.png'");
                    } 
                    else if ( dataserver_age < 200 )
                    {
                        $('#dataserver').children().first().remove();
                        $('#dataserver').prepend("<img src='css/images/LEDs/yellow-on-16.png'");
                    }
                    else
                    {
                        $('#dataserver').children().first().remove();
                        $('#dataserver').prepend("<img src='css/images/LEDs/red-on-16.png'");
                    }

                    if ( controller_age < 120 )
                    {
                        $('#controller').children().first().remove();
                        $('#controller').prepend("<img src='css/images/LEDs/green-on-16.png'");
                    }
                    else if ( controller_age < 200 )
                    {
                        $('#controller').children().first().remove();
                        $('#controller').prepend("<img src='css/images/LEDs/yellow-on-16.png'");
                    }
                    else
                    {
                        $('#controller').children().first().remove();
                        $('#controller').prepend("<img src='css/images/LEDs/red-on-16.png'");
                    }

                    if ( cluster_age < 120 )
                    {
                        $('#cluster').children().first().remove();
                        $('#cluster').prepend("<img src='css/images/LEDs/green-on-16.png'");
                    }
                    else if ( cluster_age < 200 )
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
                    timeoutID = setTimeout(statusMonitor,10000);
                });
            }
            else
            //This is not an active directory
            {
                $('#led_panel').hide();
                timeoutID = setTimeout(statusMonitor,120000);
            }
        });
    };

    //upon click, load up the data for the snap and fill the pages
    function update_snap(my_res_id) {
      $.getJSON("get_result_data.php?res_id="+my_res_id+"&datadir=<?php echo $_SESSION[data]; ?>&trip_id=<?php echo $_POST[trip_id]; ?>", function(json) {
        if (json.length) {
 	  $("#parsed").load(json[1]);
          $("#full").empty(); 
          $("#full").load(json[2]);
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
    function update_run(my_res_id) {
      $.getJSON("get_result_data.php?res_id="+my_res_id+"&datadir=<?php echo $_SESSION[data]; ?>&trip_id=<?php echo $_POST[trip_id]; ?>", function(json) {
        if (json.length) { 
          // Load the parsed display
          $("#parsed").empty();
          $("#parsed").load(json[1]); 
          // Load the full display
          $("#full").empty();
          $("#full").html("<div id='container'><div id='full1'></div> <div id='full2'></div> <div id='full3'></div></div>");
          $('#full1').load(json[2][0], function(){
             $('#full1').html("<pre>"+$('#full1').html()+"</pre>");
          });
          $('#full2').load(json[2][1], function(){
             $('#full2').html("<pre>"+$('#full2').html()+"</pre>");
          });
          $('#full3').load(json[2][2], function(){
             $('#full3').html("<pre>"+$('#full3').html()+"</pre>");
          });
          // Load the images - none right now
          $("#mooviewer").hide();
          $("#old_images").empty();
          // Load the plots
          $("#plots").load(json[4]);
        }   
      });
    };

//    function closeDialog(){
//      //timeoutID = setTimeout(closeIt, 10000);
//    }
//
//    function closeIt(){
//      $('#dialog').dialog("close");
//      $('#download_active').show("slow");
//    }
    //(jQuery);


</script>

    <!-- Download initiated dialog -->
    <div id="dialog">
      Download  Initiated<br>
       Please Be Patient
    </div>

    <!--  Context menus -->
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
                <li id="settings">Settings</li>
                <li id="header">Header Info</li>
            </ul>
        </li>
        <li id="reprocess">Reprocess</li> 
        <li>Download
            <ul>
                <li id="download_image">Image(s)</li>
                <!-- <li id="download_process">Processed Data</li> -->
                <li id="download_package">All</li>
            </ul>
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
        <li id="settings">View Settings</li>
        <!-- <li id="reprocess">Reprocess</li> -->
        <li>Download
            <ul>
                <li id="download_image">Images</li>
                <li id="download_process">Processed Data</li> 
                <li id="download_package">All</li>
            </ul>
        <!-- <li>Report</li> -->
    </ul>


 
    <!-- area to use for the downloading method -->
    <iframe src="" id="download-iframe" style="display:none;"></iframe>

</body>
</html>

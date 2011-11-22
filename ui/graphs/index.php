<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<?php  
//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);
session_cache_limiter();
session_start();

require('../login/functions.php');
?>
<html>
 <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <meta http-equiv="Pragma" content="no-cache">
    <title>NE-CAT Data Collection Analysis</title>
<link type="text/css" href="../css/south-street/njquery-ui-1.7.2.custom.css" rel="stylesheet" media="screen, projection"/>
<link type="text/css" href="../css/ui-daterangepicker.css" rel="stylesheet" media="screen, projection"/>
<link type="text/css" href="../css/rapd.css" rel="stylesheet" media="screen, projection"/>

    <!--[if IE]><script language="javascript" type="text/javascript" src="../js/flot/excanvas.min.js"></script><![endif]-->
  <script src="http://www.google.com/jsapi"></script>
  <script>
    google.load("jquery", "1.3.2");
    google.load("jqueryui", "1.8.2");
  </script>
    <script language="javascript" type="text/javascript" src="../js/flot/jquery.flot.js"></script>
    <script language="javascript" type="text/javascript" src="../js/flot/jquery.flot.selection.js"></script>
    <script language="javascript" type="text/javascript" src="../js/flot/jquery.flot.navigate.js"></script>
   <script language="javascript" type="text/javascript" src="../js/daterangepicker.jQuery.js"></script>
	<style type="text/css">
.fg-button {
   outline: 0; 
   margin:0 4px 0 0; 
   padding: .4em 1em; 
   text-decoration:none !important; 
   cursor:pointer; 
   position: relative; 
   text-align: center; 
   zoom: 1;
   }
	a.fg-button { float: center; }
	/* remove extra button width in IE */
	button.fg-button { width:10em; overflow:visible; }
	
	.fg-button-icon-left { padding-left: 2.1em; }
	.fg-button-icon-right { padding-right: 2.1em; }
	.fg-button-icon-left .ui-icon { right: auto; left: .2em; margin-left: 0; }
	.fg-button-icon-right .ui-icon { left: auto; right: .2em; margin-left: 0; }
	
	.fg-button-icon-solo { display:block; width:8px; text-indent: -9999px; }	 /* solo icon buttons must have block properties for the text-indent to work */	
	
	.fg-buttonset { float: center; margin-top: 10px}
	.fg-buttonset .fg-button { float: center; margin: 2px}
	.fg-buttonset-single .fg-button, 
	.fg-buttonset-multi .fg-button { margin-right: -1px;}
	/* Fix Tab Spacing */
    .ui-tabs .ui-tabs-nav li.ui-tabs-selected { padding-bottom: 0; border-bottom-width: 0; }

    .images-rot {
         display:block;
         position:relative; left:-365px; top:175px;
			-webkit-transform: rotate(-90deg); 
			-moz-transform: rotate(-90deg);			
			}

img#progress {position: relative; top: -400px; left: 350px;}
   .showprogress {z-index: 5; height: 100;}
   .hideprogress {z-index: -1; height: 0;}

	</style>
 	<!--[if IE]>
	<style>
		.images-rot {
			writing-mode: tb-rl;
                        filter: flipv fliph;
			right:-365px; top:175px;
		}
	</style>
	<![endif]-->
</head>

    <body>

<script id="source" language="javascript" type="text/javascript">
$(document).ready(function() {
    var options = {
        series: {
           bars: { show: true, barWidth: 1, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0 },
        xaxis: { tickDecimals: 0, ticks: 12},
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "hour";
    $(".yaxis").text(" Images ");
    $(".title").text(" Images By Hour ");
    $(".xaxis").text(" Hour ");
    $(".units").text(" (h) ");

    selectDates();
    get_data(options, series);


$("#date").click(function() {
      var options = {
        series: {
           bars: { show: true, barWidth: 43200000, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0 },
        xaxis: { mode: "time",
                 monthNames: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                },
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "date";
    $(".yaxis").text(" Images ");
    $(".title").text(" Images by Date ");
    $(".xaxis").text(" Time ");
    $(".units").text(" (d) ");
    get_data(options, series);
 });
$("#hour").click(function() {
    var options = {
        series: {
           bars: { show: true, barWidth: 1, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0 },
        xaxis: { tickDecimals: 0, ticks: 12 },
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "hour";
    $(".yaxis").text(" Images ");
    $(".title").text(" Images by Hour ");
    $(".xaxis").text(" Hour ");
    $(".units").text(" (h) ");
    get_data(options, series);
 });
 
$("#last24").click(function() {
    var curtime = <?php print time()?> * 1000;
    var yesterday = curtime - 86400000;
    var options = {
        series: {
           bars: { show: true, barWidth: 3000000, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0 },
        xaxis: { tickDecimals: 0, mode: "time", timeformat: "%H", ticks: 12, min: yesterday, max: curtime, tickFormatter: function (val, axis) {
        var d = new Date(val);
        return d.getHours()}
        },
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "last24";
    $(".yaxis").text(" Images ");
    $(".title").text(" Images Over Last 24 Hours ");
    $(".xaxis").text(" Time ");
    $(".units").text(" (h) ");
    get_data(options, series);
 });

$("#day").click(function() {
      var options = {
        series: {
           bars: { show: true, barWidth: 1, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0 },
        xaxis: { ticks: [[0, "Sunday"], [1, "Monday"], [2, "Tuesday"], [3,"Wednesday"], [4,"Thursday"], [5,"Friday"], [6,"Saturday"]]},
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "day";
    $(".yaxis").text(" Images ");
    $(".title").text(" Images by Day of the Week ");
    $(".xaxis").text(" Day of the Week ");
    $(".units").text(" (day) ");
    get_data(options, series);
 });
$("#wavelength").click(function() {
      var options = {
        series: {
           bars: { show: true, barWidth: 0.0001, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0 },
        xaxis: { tickDecimals: 3},
        x2axis: {ticks: [[0.8148, "Rb"], [0.9202, "Br"], [0.9792, "Se"],[1.0089, "Hg"],[1.0395, "Au"],[1.0722, "Pt"],[1.2545, "Ta"], [1.2820, "Zn"],[1.3779, "Cu"], [1.7433, "Fe"]]

},
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "wavelength";
    $(".yaxis").text(" Images ");
    $(".title").text(" Images by Wavelength ");
    $(".xaxis").text(" Wavelength ");
    $(".units").text(" (Angstroms) ");
    get_data(options, series);
});
$("#energy").click(function() {
      var options = {
        series: {
           bars: { show: true, barWidth: 0.5, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0 },
        xaxis: { tickDecimals: 0},
        x2axis: {ticks: [[15218, "Rb"], [13487, "Br"], [12663, "Se"],[12291, "Hg"],[11923, "Au"],[11568, "Pt"],[9884, "Ta"], [9697, "Zn"],[8999, "Cu"],[7112, "Fe"]]

},
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "energy";
    $(".yaxis").text(" Images ");
    $(".title").text(" Images by Energy ");
    $(".xaxis").text(" Energy ");
   $(".units").text(" (eV) ");
    get_data(options, series);
});
$("#distance").click(function() {
    var series = "distance";
    $(".yaxis").text(" Images ");
    $(".title").text(" Images by Distance ");
    $(".xaxis").text(" Distance ");
    $(".units").text(" (mm) ");
    get_data(options, series);
});
$("#aperture").click(function() {
    var series = "aperture";
    $(".yaxis").text(" Images ");
    $(".title").text(" Images by Aperture Size ");
    $(".xaxis").text(" Aperture Size ");
    $(".units").text(" (microns) ");
    get_data(options, series);
});
$("#transmission").click(function() {
      var options = {
        series: {
           bars: { show: true, barWidth: 0.01, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0 },
        xaxis: { tickDecimals: 1},
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "transmission";
    $(".yaxis").text(" Images ");
    $(".title").text(" Images by Transmission ");
    $(".xaxis").text(" Transmission ");
    $(".units").text(" (%) ");
    get_data(options, series);
});

$("#osc").click(function() {
      var options = {
        series: {
           bars: { show: true, barWidth: 0.05, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0 },
        xaxis: { tickDecimals: 1},
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "osc";
    $(".yaxis").text(" Images ");
    $(".title").text(" Images by Oscillation Range ");
    $(".xaxis").text(" Oscillation Range ");
    $(".units").html(" (<sup>o</sup>) ");
    get_data(options, series);
});

$("#exposure").click(function() {
      var options = {
        series: {
           bars: { show: true, barWidth: 0.25, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0 },
        xaxis: { tickDecimals: 1},
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "exposure";
    $(".yaxis").text(" Images ");
    $(".units").text(" (s) ");
    $(".title").text(" Images by Exposure Time ");
    $(".xaxis").text(" Exposure Time ");
    get_data(options, series);
});

$("#bin").click(function() {
      var options = {
        series: {
           bars: { show: true, barWidth: 1, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0 },
        xaxis: { ticks: [[0, "Binned"], [1, "UnBinned"]] },
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "bin";
    $(".yaxis").text(" Images ");
    $(".title").text(" Images by Binning ");
    $(".xaxis").text(" Binning ");
    $(".units").text(" ");
    get_bin(options, series);
});

$("#robot").click(function() {
      var options = {
        series: {
           bars: { show: true, barWidth: 1, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0 },
        xaxis: { ticks: [[0, "Manual"], [1, "A"], [2, "B"], [3, "C"], [4, "D"]] },
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "robot";
    $(".yaxis").text(" Images ");
    $(".title").text(" Images by Robot Use ");
    $(".xaxis").text(" Puck Location ");
    $(".units").text(" ");
    get_bin(options, series);
});

$("#stac").click(function() {
    var options = {
      series: {
         bars: { show: true, barWidth: 1, align: "center" }
         },
      legend: {show: true, noColumns: 4, position: "ne"},
      yaxis: { min: 0 },
      xaxis: { ticks: [[0, "No"], [1, "Yes"]] },
      grid: {color:"#000000", backgroundColor: "#fffaff"},
      selection: { mode: "xy", color: "#009999"},
      zoom: {
          interactive: true
      },
      pan: {
          interactive: true
      }
    };
  var series = "stac";
  $(".yaxis").text(" Images ");
  $(".title").text(" Images Reprocessed with STAC ");
  $(".xaxis").text(" STAC Use ");
  $(".units").text(" ");
  get_bin(options, series);
});

$("#datasets").click(function() {
      var options = {
        series: {
           bars: { show: true, barWidth: 43200000, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0 },
        xaxis: { mode: "time",
                 monthNames: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                },
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "datasets";
    $(".yaxis").text(" Runs ");
    $(".title").text(" Datasets By Date ");
    $(".xaxis").text(" Time ");
    $(".units").text(" (d) ");
    get_data(options, series);
});

$("#degrees").click(function() {
    var series = "degrees";
    $(".yaxis").text(" Runs ");
    $(".title").text(" Datasets by Degrees of Data");
    $(".xaxis").text(" Total Degrees of Data ");
    $(".units").html(" (<sup>o</sup>) ");
    get_data(options, series);
});

$("#resolution").click(function() {
      var options = {
        series: {
           bars: { show: true, barWidth: 0.1, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0 },
        xaxis: { tickDecimals: 1},
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "resolution";
    $(".yaxis").text(" Runs ");
    $(".title").text(" Datasets by Resolution");
    $(".xaxis").text(" Resolution ");
    $(".units").html(" (Angstroms) ");
    get_data(options, series);
});

$("#redundancy").click(function() {
    var options = {
      series: {
         bars: { show: true, barWidth: 0.1, align: "center" }
         },
      legend: {show: true, noColumns: 4, position: "ne"},
      yaxis: { min: 0 },
      xaxis: { tickDecimals: 1},
      grid: {color:"#000000", backgroundColor: "#fffaff"},
      selection: { mode: "xy", color: "#009999"},
      zoom: {
          interactive: true
      },
      pan: {
          interactive: true
      }
    };
  var series = "redundancy";
  $(".yaxis").text(" Runs ");
  $(".title").text(" Datasets by Redundancy");
  $(".xaxis").text(" Redundancy ");
  $(".units").html(" ");
  get_data(options, series);
});

$("#completeness").click(function() {
    var options = {
      series: {
         bars: { show: true, barWidth: 0.1, align: "center" }
         },
      legend: {show: true, noColumns: 4, position: "ne"},
      yaxis: { min: 0 },
      xaxis: { tickDecimals: 1},
      grid: {color:"#000000", backgroundColor: "#fffaff"},
      selection: { mode: "xy", color: "#009999"},
      zoom: {
          interactive: true
      },
      pan: {
          interactive: true
      }
    };
  var series = "completeness";
  $(".yaxis").text(" Runs ");
  $(".title").text(" Datasets by Completeness");
  $(".xaxis").text(" Completeness ");
  $(".units").html(" (%) ");
  get_data(options, series);
});

$("#r_merge").click(function() {
    var options = {
      series: {
         bars: { show: true, barWidth: 0.01, align: "center" }
         },
      legend: {show: true, noColumns: 4, position: "ne"},
      yaxis: { min: 0 },
      xaxis: { tickDecimals: 2},
      grid: {color:"#000000", backgroundColor: "#fffaff"},
      selection: { mode: "xy", color: "#009999"},
      zoom: {
          interactive: true
      },
      pan: {
          interactive: true
      }
    };
  var series = "r_merge";
  $(".yaxis").text(" Runs ");
  $(".title").text(" Datasets by Rmerge");
  $(".xaxis").text(" Rmerge ");
  $(".units").html("  ");
  get_data(options, series);
});

$("#r_pim").click(function() {
    var options = {
      series: {
         bars: { show: true, barWidth: 0.01, align: "center" }
         },
      legend: {show: true, noColumns: 4, position: "ne"},
      yaxis: { min: 0 },
      xaxis: { tickDecimals: 2},
      grid: {color:"#000000", backgroundColor: "#fffaff"},
      selection: { mode: "xy", color: "#009999"},
      zoom: {
          interactive: true
      },
      pan: {
          interactive: true
      }
    };
  var series = "r_pim";
  $(".yaxis").text(" Runs ");
  $(".title").text(" Datasets by Rpim");
  $(".xaxis").text(" Rpim ");
  $(".units").html("  ");
  get_data(options, series);
});

$("#samples").click(function() {
      var options = {
        series: {
           bars: { show: true, barWidth: 43200000, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0 },
        xaxis: { mode: "time",
                 monthNames: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                },
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "samples";
    $(".yaxis").text(" Samples ");
    $(".title").text(" Samples Mounted Via Robot");
    $(".xaxis").text(" Time ");
    $(".units").html(" (d) ");
    get_data(options, series);
});

$("#avgmount").click(function() {
      var options = {
        series: {
           bars: { show: true, barWidth: 0.1, align: "center" }
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        yaxis: { min: 0, tickDecimals: 0 },
        xaxis: { tickDecimals: 1},
        grid: {color:"#000000", backgroundColor: "#fffaff"},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "avgmount";
    $(".yaxis").text(" Number of Samples ");
    $(".title").text(" Time Per Sample Using Robot");
    $(".xaxis").text(" Time ");
    $(".units").html(" (min) ");
    get_data(options, series);
});

$("#xbeam").click(function() {
    var options = {
        series: {
           points: { show: true, align: "center"}
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        xaxis: { tickDecimals: 0},
        grid: {color:"#000000", backgroundColor: "#fffaff", hoverable: true, autoHighlight: true},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "xbeam";
    $(".yaxis").text(" X Beam (mm) ");
    $(".units").text(" ");
    $(".title").text(" Difference between Header X Beam and Refined X Beam ");
    $(".xaxis").text(" Image ID ");
      get_versus(options, series);
});

$("#ybeam").click(function() {
    var options = {
        series: {
           points: { show: true, align: "center"}
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        xaxis: { tickDecimals: 0},
        grid: {color:"#000000", backgroundColor: "#fffaff", hoverable: true, autoHighlight: true},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
    };
    var series = "ybeam";
    $(".yaxis").text(" Y Beam (mm) ");
    $(".units").text(" ");
    $(".title").text(" Difference between Header Y Beam and Refined Y Beam ");
    $(".xaxis").text(" Image ID ");
    get_versus(options, series);
});

$("#calcxbeam").click(function() {
    var options = {
        series: {
           points: { show: true, align: "center"}
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        xaxis: { tickDecimals: 0},
        grid: {color:"#000000", backgroundColor: "#fffaff", hoverable: true, autoHighlight: true},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
    };
    var series = "calcxbeam";
    $(".yaxis").text(" X Beam (mm) ");
    $(".units").text(" ");
    $(".title").text(" Difference between Calculated X Beam and Refined X Beam ");
    $(".xaxis").text(" Image ID ");
    get_versus(options, series);
});

$("#calcybeam").click(function() {
    var options = {
        series: {
           points: { show: true, align: "center"}
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        xaxis: { tickDecimals: 0},
        grid: {color:"#000000", backgroundColor: "#fffaff", hoverable: true, autoHighlight: true},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
    };
    var series = "calcybeam";
    $(".yaxis").text(" Y Beam (mm) ");
    $(".units").text(" ");
    $(".title").text(" Difference between Calculated Y Beam and Refined Y Beam ");
    $(".xaxis").text(" Image ID ");
    get_versus(options, series);
});

$("#pairxbeam").click(function() {
    var options = {
        series: {
           points: { show: true, align: "center"}
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        xaxis: { tickDecimals: 0},
        grid: {color:"#000000", backgroundColor: "#fffaff", hoverable: true, autoHighlight: true},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
      };
    var series = "pairxbeam";
    $(".yaxis").text(" X Beam (mm) ");
    $(".units").text(" ");
    $(".title").text(" Difference between Header X Beam and Refined X Beam from Pair Results");
    $(".xaxis").text(" Image ID ");
      get_versus(options, series);
});

$("#pairybeam").click(function() {
    var options = {
        series: {
           points: { show: true, align: "center"}
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        xaxis: { tickDecimals: 0},
        grid: {color:"#000000", backgroundColor: "#fffaff", hoverable: true, autoHighlight: true},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
    };
    var series = "pairybeam";
    $(".yaxis").text(" Y Beam (mm) ");
    $(".units").text(" ");
    $(".title").text(" Difference between Header Y Beam and Refined Y Beam from Pairs Results ");
    $(".xaxis").text(" Image ID ");
    get_versus(options, series);
});

$("#refdistance").click(function() {
    var options = {
        series: {
           points: { show: true, align: "center"}
           },
        legend: {show: true, noColumns: 4, position: "ne"},
        xaxis: { tickDecimals: 0},
        grid: {color:"#000000", backgroundColor: "#fffaff", hoverable: true, autoHighlight: true},
        selection: { mode: "xy", color: "#009999"},
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true
        }
    };
    var series = "distance";
    $(".yaxis").text(" Distance (mm) ");
    $(".units").text(" ");
    $(".title").text(" Difference between Header Distance and Refined Distance ");
    $(".xaxis").text(" Image ID ");
    get_versus(options, series);
  });
  
$("#phi").click(function() {
    var options = {
            series: {
               bars: { show: true, barWidth: 0.5, align: "center"}
               },
            legend: {show: true, noColumns: 2, position: "ne"},
            yaxis: { min: 0, tickDecimals: 0 },
            xaxis: { tickDecimals: 1},
            grid: {color:"#000000", backgroundColor: "#fffaff"},
            selection: { mode: "xy", color: "#009999"},
            zoom: {
                interactive: true
            },
            pan: {
                interactive: true
            }
          };
    var series = "phi";
    $(".yaxis").text(" Runs ");
    $(".units").html(" (<sup>o</sup>)  ");
    $(".title").text(" User Starting Phi Compared to Strategy Phi ");
    $(".xaxis").text(" Phi ");
    get_compare(options, series);
  });



});



function get_data(options, series) {
   var dates = get_dates();
   $.ajax({ url: "getData.php",
     dataType: "json",
     type: "POST",
     data: {"query": series, "start": dates.slice(0,10), "finish": dates.slice(-10), "user": $('select[name=username]').val()},
     success: function(result) 
      {
//      alert(result);
//      alert(result.toSource());
        makeplot(options, series, result);
        makeCheckboxes(options, series, result);
      }
    });
};

function makeplot(options, series, result) {
    var placeholder = $("#placeholder");
    var plot = $.plot(placeholder, result, options);

    if ((series == "wavelength" || series == "energy") && (result.toSource().toString().search("xaxis") != -1 )) {
      placeholder.unbind("plotselected")
      placeholder.bind("plotselected", function (event, ranges) {
        plot = $.plot(placeholder, result,
                     $.extend(true, {}, options, {
                         xaxis: { min: ranges.xaxis.from, max: ranges.xaxis.to },
                         x2axis: { min: ranges.x2axis.from, max: ranges.x2axis.to },
                         yaxis: { min: ranges.yaxis.from, max: ranges.yaxis.to }
                      }));
      });
    }
    else {
      placeholder.unbind("plotselected");
      placeholder.bind("plotselected", function (event, ranges) {
        plot = $.plot(placeholder, result,
                     $.extend(true, {}, options, {
                         xaxis: { min: ranges.xaxis.from, max: ranges.xaxis.to },
                         yaxis: { min: ranges.yaxis.from, max: ranges.yaxis.to }
                      }));
      });
    }

    placeholder.live("plotunselected", function (event) {
       plot = $.plot(placeholder, result, options)
    });


};

function makeCheckboxes (options, series, result) {
    // insert checkboxes 
    $("#choices").html(" ");
    var choiceContainer = $("#choices");
    $.each(result, function(key, val) {
        choiceContainer.append('<br/><input type="checkbox" name="' + key +
                               '" checked="checked" id="id' + key + '">' +
                               '<label for="id' + key + '">'
                                + val.label + '</label>');
    });
    choiceContainer.find("input").click(plotAccordingToChoices);

    function plotAccordingToChoices() {
        var data = [];
        choiceContainer.find("input:checked").each(function () {
            var key = $(this).attr("name");
            if (key && result[key])
                data.push(result[key]);
        });

        if (data.length > 0) {
           makeplot(options, series, data);
        };
    };
};
// Choose dates to view.  Limit to 3 months.
function selectDates () {
	// Set the default dates
    var dateText = Date.today().toString("M/d/yyyy");
    $("#dates").val(Date.parse(dateText).add(-3).months().toString("M/d/yyyy") + " to " + dateText);
	if($(window.parent.document).find('iframe').size()){
		var inframe = true;
	};
	// Make the daterangepicker widget
	$("#dates").daterangepicker({
 	    // Change this array to create custom ranges.
	 	presetRanges: [
			{text: '2011-3', dateStart: '10/4/2011', dateEnd: '12/20/2011' },
			{text: '2011-2', dateStart: '6/1/2011', dateEnd: '8/25/2011' },
			{text: '2011-1', dateStart: '2/1/2011', dateEnd: '4/27/2011' },
			{text: '2010-3', dateStart: '10/5/2010', dateEnd: '12/21/2010' },
			{text: '2010-2', dateStart: '6/2/2010', dateEnd: '8/26/2010' },
			{text: '2010-1', dateStart: '2/2/2010', dateEnd: '4/29/2010' },
			{text: '2009-3', dateStart: '10/6/2009', dateEnd: '12/23/2009' }
		], 
		posX: 0,
	 	posY: 300,
	 	arrows: true,
	 	dateFormat: 'm/d/yy',
	 	rangeSplitter: 'to',
	 	datepickerOptions: {
	 		changeMonth: true,
	 		changeYear: true
	 	},
	 	onOpen:function(){ if(inframe){ $(window.parent.document).find('iframe:eq(1)').width(700).height('35em');} }, 
	  	onClose: function(){ if(inframe){ $(window.parent.document).find('iframe:eq(1)').width('100%').height('5em');} },
	  	onDone: function() {
	        var dates = $("#dates").val();
	        var findsplit = dates.indexOf("to");
	  	    if (!(Date.parse(dates.substring(0,findsplit)) === null)) {
		  	    var start_date = Date.parse(dates.substring(0,findsplit));
		  	    var end_date = Date.parse(dates.substring(findsplit+3)).add(-3).months();
		  	    if (Date.compare(end_date,start_date) == 1) {
			  	    alert("Date range cannot be greater than 3 months.\nDate range has been reduced to 3 months.");
			  	    setTimeout(function() {$("#dates").val(start_date.toString("M/d/yyyy") + " to " + Date.parse(start_date).add(3).months().toString("M/d/yyyy"))},500);
		  	    };
            };
	  	}
	 }); 
    
};

function get_bin(options, series) {
    var dates = get_dates();
	$.ajax({ url: "getBin.php",
		dataType: "json",
        type: "POST",
        data: {"query": series, "start": dates.slice(0,10), "finish": dates.slice(-10), "user": $('select[name=username]').val()},
        success: function(result) 
	      {
	        makeplot(options, series, result);
	        makeCheckboxes(options, series, result);
	      }
	});
};

function get_compare(options, series) {
    var dates = get_dates();
	$.ajax({ url: "getComp.php",
		dataType: "json",
        type: "POST",
        data: {"query": series, "start": dates.slice(0,10), "finish": dates.slice(-10), "user": $('select[name=username]').val()},
        success: function(result) 
	      {
	        makeplot(options, series, result);
	        makeCheckboxes(options, series, result);
	      }
	});
};

function get_versus(options, series) {
    var dates = get_dates();
	$.ajax({ url: "getVersus.php",
	     dataType: "json",
	     type: "POST",
	     data: {"query": series, "start": dates.slice(0,10), "finish": dates.slice(-10), "user": $('select[name=username]').val()},
	     success: function(result) 
	      {
	        makeplot(options, series, result);
	        makeCheckboxes(options, series, result);
	        var placeholder = $("#placeholder");
	        var plot = $.plot(placeholder, result, options);
	
	        placeholder.bind("plothover", function (event, pos, item) {
	        $("#x").text(pos.x.toFixed(0));
	        $("#y").text(pos.y.toFixed(2));
	
	        if (item) {
	           if (previousPoint != item.datapoint) {
	               previousPoint = item.datapoint;
	
	               $("#tooltip").remove();
	               var x = item.datapoint[0].toFixed(0),
	                   y = item.datapoint[1].toFixed(2);
	
	               showTooltip(item.pageX, item.pageY,
	                      "Image " + x + " difference  = " + y);
	            }
	         }
	            else {
	                $("#tooltip").remove();
	                previousPoint = null;            
	            }
	    });
	
	      }
	  });
};

function get_dates() {
	//var start_date = $startdate.datepicker("getDate").toString("yyyy-MM-dd");
	//var end_date = $enddate.datepicker("getDate").toString("yyyy-MM-dd");
	var dates = $("#dates").val();
	$("#displaydates").text(dates);
	var findsplit = dates.indexOf("to");
	if (Date.parse(dates.substring(0,findsplit)) === null) {
	   var start_date = Date.parse(dates).toString("yyyy-MM-dd");
	   var end_date = Date.parse(dates).add(1).days().toString("yyyy-MM-dd");
	} else {
	   var start_date = Date.parse(dates.substring(0,findsplit)).toString("yyyy-MM-dd");
	   var end_date = Date.parse(dates.substring(findsplit+3)).toString("yyyy-MM-dd");
	};
	return start_date +" "+end_date;
};

// Show x and y coordinates
function showTooltip(x, y, contents) {
     $('<div id="tooltip">' + contents + '</div>').css( {
         position: 'absolute',
         display: 'none',
         top: y + 5,
         left: x + 5,
         border: '1px solid #fdd',
         padding: '2px',
         'background-color': '#fee',
         opacity: 0.80
     }).appendTo("body").fadeIn(200);
 };


// Ajax Loading Icon
$(function() {
  $("#progress").bind("ajaxStart", function(){
      $(this).removeClass("hideprogress");
      $(this).addClass("showprogress");
//    $(this).show();
    }).bind("ajaxStop", function(){
//      $(this).hide();
      $(this).removeClass("showprogress");
      $(this).addClass("hideprogress");
  });
});

$(function () {
   //React to control button presses
   $('#go_to_main').click(function() {
       document.location.href = '../main.php';
   });

   $('#go_to_samples').click(function() {
       document.location.href = '../samples_main.php';
   });

	// Tabs
	$('#tabs1').tabs();
	$('#tabs2').tabs();
 
});


	$(function(){
		//all hover and click logic for buttons
		$(".fg-button:not(.ui-state-disabled)")
		.hover(
			function(){ 
				$(this).addClass("ui-state-hover"); 
			},
			function(){ 
				$(this).removeClass("ui-state-hover"); 
			}
		)
		.mousedown(function(){
				$(this).parents('.fg-buttonset-single:first').find(".fg-button.ui-state-active").removeClass("ui-state-active");
				if( $(this).is('.ui-state-active.fg-button-toggleable, .fg-buttonset-multi .ui-state-active') ){ $(this).removeClass("ui-state-active"); }
				else { $(this).addClass("ui-state-active"); }	
		})
		.mouseup(function(){
			if(! $(this).is('.fg-button-toggleable, .fg-buttonset-single .fg-button,  .fg-buttonset-multi .fg-button') ){
				$(this).removeClass("ui-state-active");
			}
		});
	});



</script>
<noscript>
    <h1 align="center"><font color="#FF0000">Javascript is required to view this page.</font></h1>
</noscript>
<h1 class="green">NE-CAT Data Collection Statistics</h1>
<table id="wrapper" height="100%">
<tr>
<td width="300" valign="top">
<!-- Tabs -->

<div class="tabs" id="tabs1">
<ul>

   <li><a href="#tabs-1">Image Stats</a></li>
   <li><a href="#tabs-2">Sample Stats</a></li>
   <li><a href="#tabs-3">Data Stats</a></li>
   <li><a href="#tabs-4">Compare</a></li>
   <li><a href="#tabs-5">Controls</a></li>
</ul>

<!-- Information for Tabs -->
   <div class="tabs" id="tabs-1">

	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="last24">Last 24 Hours</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="hour">Hour</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="date">Date</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="day">Day of Week</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="wavelength">Wavelength</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="energy">Energy</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="distance">Distance</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="aperture">Aperture Size</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="transmission">Transmission</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="osc">Oscillation Range</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="exposure">Exposure Time</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="bin">Binning</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="robot">Robot Use</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="stac">STAC Use</button><br>
   </div>

   <div class="tabs" id="tabs-2">
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="samples">Samples</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="avgmount">Mount Time</button><br>
   </div>

   <div class="tabs" id="tabs-3">

	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="datasets">Datasets</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="degrees">Degrees of Data</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="resolution">Resolution</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="redundancy">Redundancy</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="completeness">Completeness</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="r_merge">Rmerge</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="r_pim">Rpim</button><br>

   </div>

   <div class="tabs" id="tabs-4">
    These options are for tracking the beamline and do not accept usernames.<br><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="xbeam">X Beam (Single)</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="ybeam">Y Beam (Single)</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="calcxbeam">Calculated X Beam (Single)</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="calcybeam">Calculated Y Beam (Single)</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="pairxbeam">X Beam (Pairs)</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="pairybeam">Y Beam (Pairs)</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="refdistance">Refined Distance</button><br>
	<button class="fg-button ui-state-default ui-priority-primary ui-corner-all" id="phi">Phi</button><br>
   </div>

   <div class="tabs" id="tabs-5">
        <button style='width:95%' class="fg-button ui-state-default ui-corner-all" id="go_to_samples" type="button">Samples Nexus</button><br>
        <button style='width:95%' class="fg-button ui-state-default ui-corner-all" id="go_to_main" type="button">Main</button><br>
        <br>
        After selecting dates and/or user, choose an option to reload the graph.<br>
        <br>
        <input type="text" id="dates" name="dates" onkeydown = "return false;" /><br>
<?php 
    echo('           Choose User: <select name="username">');
    // Default to 'ALL USERS'
    echo('<option value="all" selected="all">ALL</option>');
    if (allow_access(Administrators) == "yes")
    {
      
      require ("../login/config.php");

      //make the connection to the database
      $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
      $db = @mysql_select_db($db_name,$connection)or die(mysql_error());

      //build and issue the query
      $sql ="SELECT username FROM authorize GROUP BY username";
      $result = @mysql_query($sql,$connection) or die(mysql_error());
      while ($sql = mysql_fetch_object($result))
        {
           $uname = $sql -> username;
           echo "<option value=\"$uname\">$uname</option>";
           }
    } else {
      echo ('<option value="'.$_SESSION[username].'">'.$_SESSION[username].'</option>');
    };
    echo('                      </select>');
    
?>   
</div>

</td>
<td width="800" valign="top">
<!-- Tabs -->
<div class="tabs" id="tabs2">
<ul>
   <li><a href="#tabs-6">Plots</a></li>
</ul>

<!-- Information for Tabs -->
<div id="tabs-6">

<h1 align="center" class="green"><span class="title"></span></h1>
<h2 style="text-align: center;"><span id="displaydates"></span></h2>
<div align="center">
<span class="images-rot"><span class="yaxis"></span></span>

    <div id="placeholder" style="width:700px;height:400px; position:relative">
</div>
<br>
<span class="xaxis"></span><span class="units"></span>
</div>
Show:
<p id="choices" style="margin-left: 30px"></p>

<p id="runchoices" style="margin-left: 30px"></p>

</div>
<div><img src="../css/south-street/images/ajax-loader.gif" id="progress" class="ui-state-default ui-corner-all"></div>

</td>
</tr>
</table>
 </body>
</html>

<html>
<head>
  <style type="text/css">
    body     { background-image: none; }
    .x-label { position:relative; text-align:center; top:10px; }
    .title   { font-size:30px; text-align:center; }
</style>
<script type="text/javascript">
$(function() {
    // Tabs
    $('.tabs').tabs();
});
</script>
</head>
<body>
<table>
  <tr>
    <td width="100%">
    <div class="tabs">
      <!-- This is where the tab labels are defined
           221 = tab2 (on page) tab2(full output tab) tab1 -->
      <ul>
        <li><a href="#tabs-223">R vs frame</a></li>
        <li><a href="#tabs-227">I/sigma</a></li>
        <li><a href="#tabs-228">R vs Res</a></li>
        <li><a href="#tabs-229">I vs Res</a></li>
        <li><a href="#tabs-2212">%Comp</a></li>
        <li><a href="#tabs-2213">Redundancy</a></li>
        <li><a href="#tabs-2214">Rpim</a></li>
        <li><a href="#tabs-2215">Rmeas</a></li>
        <li><a href="#tabs-2216">Anom Corr</a></li>
        <li><a href="#tabs-2217">RCR</a></li>
      </ul>
      <div id ="tabs-223">
        <div class="title"><b>Rmerge v Batch for all runs</b></div>
        <div id="chart3_div" style="width:800px;height:600px"></div>
        <div class="x-label">N</div>
      </div>
      <div id ="tabs-227">
        <div class="title"><b>I/sigma, Mean Mn(I)/sd(Mn(I))</b></div>
        <div id="chart7_div" style="width:800px;height:600px"></div>
        <div class="x-label">Dmin (A)</div>
      </div>
      <div id ="tabs-228">
        <div class="title"><b>Rmerge v Resolution</b></div>
        <div id="chart8_div" style="width:800px;height:600px"></div>
        <div class="x-label">Dmin (A)</div>
      </div>
      <div id ="tabs-229">
        <div class="title"><b>Average I,sd and Sigma</b></div>
        <div id="chart9_div" style="width:800px;height:600px"></div>
        <div class="x-label">Dmin (A)</div>
      </div>
      <div id ="tabs-2212">
        <div class="title"><b>Completeness v Resolution</b></div>
        <div id="chart12_div" style="width:800px;height:600px"></div>
        <div class="x-label">Dmin (A)</div>
      </div>
      <div id ="tabs-2213">
        <div class="title"><b>Multiplicity v Resolution</b></div>
        <div id="chart13_div" style="width:800px;height:600px"></div>
        <div class="x-label">Dmin (A)</div>
      </div>
      <div id ="tabs-2214">
        <div class="title"><b>Rpim (precision R) v Resolution</b></div>
        <div id="chart14_div" style="width:800px;height:600px"></div>
        <div class="x-label">Dmin (A)</div>
      </div>
      <div id ="tabs-2215">
        <div class="title"><b>Rmeas, Rsym & PCV v Resolution</b></div>
        <div id="chart15_div" style="width:800px;height:600px"></div>
        <div class="x-label">Dmin (A)</div>
      </div>
      <div id ="tabs-2216">
        <div class="title"><b>Anom & Imean CCs v resolution -</b></div>
        <div id="chart16_div" style="width:800px;height:600px"></div>
        <div class="x-label">Dmin (A)</div>
      </div>
      <div id ="tabs-2217">
        <div class="title"><b>RMS correlation ratio</b></div>
        <div id="chart17_div" style="width:800px;height:600px"></div>
        <div class="x-label">Dmin (A)</div>
      </div>
</div> <!-- End of Tabs -->
    </td>
  </tr>
</table>

<script id="source" language="javascript" type="text/javascript">
$(function () {

    var y0= [];
         y0.push([1,0.091]);
         y0.push([2,0.094]);
         y0.push([3,0.107]);
         y0.push([4,0.101]);
         y0.push([5,0.091]);
         y0.push([6,0.094]);
         y0.push([7,0.091]);
         y0.push([8,0.094]);
         y0.push([9,0.098]);
         y0.push([10,0.092]);
         y0.push([11,0.091]);
         y0.push([12,0.105]);
         y0.push([13,0.094]);
         y0.push([14,0.094]);
         y0.push([15,0.092]);
         y0.push([16,0.098]);
         y0.push([17,0.100]);
         y0.push([18,0.090]);
         y0.push([19,0.093]);
         y0.push([20,0.095]);
         y0.push([21,0.096]);
         y0.push([22,0.098]);
         y0.push([23,0.090]);
         y0.push([24,0.091]);
         y0.push([25,0.104]);
         y0.push([26,0.090]);
         y0.push([27,0.096]);
         y0.push([28,0.103]);
         y0.push([29,0.099]);
         y0.push([30,0.090]);
         y0.push([31,0.096]);
         y0.push([32,0.102]);
         y0.push([33,0.098]);
         y0.push([34,0.097]);
         y0.push([35,0.100]);
         y0.push([36,0.091]);
         y0.push([37,0.091]);
         y0.push([38,0.093]);
         y0.push([39,0.096]);
         y0.push([40,0.096]);
         y0.push([41,0.100]);
         y0.push([42,0.098]);
         y0.push([43,0.099]);
         y0.push([44,0.101]);
         y0.push([45,0.097]);
         y0.push([46,0.099]);
         y0.push([47,0.100]);
         y0.push([48,0.108]);
         y0.push([49,0.091]);
         y0.push([50,0.089]);
         y0.push([51,0.093]);
         y0.push([52,0.088]);
         y0.push([53,0.088]);
         y0.push([54,0.105]);
         y0.push([55,0.099]);
         y0.push([56,0.099]);
         y0.push([57,0.090]);
         y0.push([58,0.095]);
         y0.push([59,0.093]);
         y0.push([60,0.091]);
         y0.push([61,0.111]);
         y0.push([62,0.119]);
         y0.push([63,0.110]);
         y0.push([64,0.100]);
         y0.push([65,0.109]);
         y0.push([66,0.106]);
         y0.push([67,0.111]);
         y0.push([68,0.103]);
         y0.push([69,0.099]);
         y0.push([70,0.102]);
         y0.push([71,0.105]);
         y0.push([72,0.099]);
         y0.push([73,0.100]);
         y0.push([74,0.106]);
         y0.push([75,0.099]);
         y0.push([76,0.107]);
         y0.push([77,0.102]);
         y0.push([78,0.099]);
         y0.push([79,0.101]);
         y0.push([80,0.103]);
         y0.push([81,0.116]);
         y0.push([82,0.097]);
         y0.push([83,0.111]);
         y0.push([84,0.099]);
         y0.push([85,0.102]);
         y0.push([86,0.104]);
         y0.push([87,0.105]);
         y0.push([88,0.107]);
         y0.push([89,0.106]);
         y0.push([90,0.111]);
         y0.push([91,0.101]);
         y0.push([92,0.102]);
         y0.push([93,0.107]);
         y0.push([94,0.098]);
         y0.push([95,0.103]);
         y0.push([96,0.108]);
         y0.push([97,0.110]);
         y0.push([98,0.107]);
         y0.push([99,0.123]);
         y0.push([100,0.100]);
         y0.push([101,0.109]);
         y0.push([102,0.112]);
         y0.push([103,0.122]);
         y0.push([104,0.115]);
         y0.push([105,0.114]);
         y0.push([106,0.120]);
         y0.push([107,0.113]);
         y0.push([108,0.129]);
         y0.push([109,0.118]);
         y0.push([110,0.126]);
         y0.push([111,0.125]);
         y0.push([112,0.122]);
         y0.push([113,0.126]);
         y0.push([114,0.122]);
         y0.push([115,0.129]);
         y0.push([116,0.120]);
         y0.push([117,0.129]);
         y0.push([118,0.124]);
         y0.push([119,0.139]);
         y0.push([120,0.124]);
    var plot3 = $.plot($("#chart3_div"), [
        {data: y0, label:"Rmerge" },
        ],
        { lines: {show: true},
          points: {show: false},
          selection: { mode: 'xy' },
          grid: {hoverable: true, clickable: true },
    });

    var y1 = [], y2= [];
         y1.push([0.0211,11.7]);
         y2.push([0.0211,28.7]);
         y1.push([0.0422,14.6]);
         y2.push([0.0422,30.0]);
         y1.push([0.0633,16.2]);
         y2.push([0.0633,31.8]);
         y1.push([0.0845,14.5]);
         y2.push([0.0845,29.5]);
         y1.push([0.1056,13.4]);
         y2.push([0.1056,26.6]);
         y1.push([0.1267,11.1]);
         y2.push([0.1267,23.1]);
         y1.push([0.1478,10.0]);
         y2.push([0.1478,19.8]);
         y1.push([0.1689,8.7]);
         y2.push([0.1689,17.8]);
         y1.push([0.1900,8.8]);
         y2.push([0.1900,16.8]);
         y1.push([0.2111,8.6]);
         y2.push([0.2111,15.6]);
         y1.push([0.2322,7.8]);
         y2.push([0.2322,13.9]);
         y1.push([0.2534,6.4]);
         y2.push([0.2534,11.7]);
         y1.push([0.2745,5.5]);
         y2.push([0.2745,10.1]);
         y1.push([0.2956,4.2]);
         y2.push([0.2956,8.0]);
         y1.push([0.3167,3.4]);
         y2.push([0.3167,6.5]);
         y1.push([0.3378,2.8]);
         y2.push([0.3378,5.3]);
         y1.push([0.3589,2.1]);
         y2.push([0.3589,4.2]);
         y1.push([0.3800,1.8]);
         y2.push([0.3800,3.5]);
         y1.push([0.4012,1.4]);
         y2.push([0.4012,2.8]);
         y1.push([0.4223,1.2]);
         y2.push([0.4223,1.9]);
    var plot7 = $.plot($("#chart7_div"), [
        {data: y1, label:"I/sigma" },
        {data: y2, label:"Mn(I/sd)" },
        ],
        { lines: {show: true},
          points: {show: false},
          selection: { mode: 'xy' },
          grid: {hoverable: true, clickable: true },
          xaxis: {ticks: [
                         [0.0211,"6.88"],
                         [0.0422,"4.87"],
                         [0.0633,"3.97"],
                         [0.0845,"3.44"],
                         [0.1056,"3.08"],
                         [0.1267,"2.81"],
                         [0.1478,"2.60"],
                         [0.1689,"2.43"],
                         [0.1900,"2.29"],
                         [0.2111,"2.18"],
                         [0.2322,"2.08"],
                         [0.2534,"1.99"],
                         [0.2745,"1.91"],
                         [0.2956,"1.84"],
                         [0.3167,"1.78"],
                         [0.3378,"1.72"],
                         [0.3589,"1.67"],
                         [0.3800,"1.62"],
                         [0.4012,"1.58"],
                         [0.4223,"1.54"],
                  ]},
    });

    var y3 = [], y4 = [], y5= [];
         y3.push([0.0211,0.038]);
         y4.push([0.0211,0.038]);
         y5.push([0.0211,0.020]);
         y3.push([0.0422,0.039]);
         y4.push([0.0422,0.039]);
         y5.push([0.0422,0.022]);
         y3.push([0.0633,0.037]);
         y4.push([0.0633,0.037]);
         y5.push([0.0633,0.022]);
         y3.push([0.0845,0.041]);
         y4.push([0.0845,0.041]);
         y5.push([0.0845,0.027]);
         y3.push([0.1056,0.046]);
         y4.push([0.1056,0.046]);
         y5.push([0.1056,0.030]);
         y3.push([0.1267,0.056]);
         y4.push([0.1267,0.056]);
         y5.push([0.1267,0.034]);
         y3.push([0.1478,0.068]);
         y4.push([0.1478,0.068]);
         y5.push([0.1478,0.039]);
         y3.push([0.1689,0.079]);
         y4.push([0.1689,0.079]);
         y5.push([0.1689,0.042]);
         y3.push([0.1900,0.079]);
         y4.push([0.1900,0.079]);
         y5.push([0.1900,0.043]);
         y3.push([0.2111,0.085]);
         y4.push([0.2111,0.085]);
         y5.push([0.2111,0.048]);
         y3.push([0.2322,0.094]);
         y4.push([0.2322,0.094]);
         y5.push([0.2322,0.054]);
         y3.push([0.2534,0.117]);
         y4.push([0.2534,0.117]);
         y5.push([0.2534,0.063]);
         y3.push([0.2745,0.139]);
         y4.push([0.2745,0.139]);
         y5.push([0.2745,0.076]);
         y3.push([0.2956,0.181]);
         y4.push([0.2956,0.181]);
         y5.push([0.2956,0.100]);
         y3.push([0.3167,0.225]);
         y4.push([0.3167,0.225]);
         y5.push([0.3167,0.123]);
         y3.push([0.3378,0.277]);
         y4.push([0.3378,0.277]);
         y5.push([0.3378,0.148]);
         y3.push([0.3589,0.359]);
         y4.push([0.3589,0.359]);
         y5.push([0.3589,0.199]);
         y3.push([0.3800,0.433]);
         y4.push([0.3800,0.433]);
         y5.push([0.3800,0.231]);
         y3.push([0.4012,0.562]);
         y4.push([0.4012,0.562]);
         y5.push([0.4012,0.305]);
         y3.push([0.4223,0.643]);
         y4.push([0.4223,0.643]);
         y5.push([0.4223,0.465]);
    var plot8 = $.plot($("#chart8_div"), [
        {data: y3, label:"Rmrg" },
        {data: y4, label:"Rfull" },
        {data: y5, label:"Ranom" },
        ],
        { lines: {show: true},
          points: {show: false},
          selection: { mode: 'xy' },
          grid: {hoverable: true, clickable: true },
          xaxis: {ticks: [
                         [0.0211,"6.88"],
                         [0.0422,"4.87"],
                         [0.0633,"3.97"],
                         [0.0845,"3.44"],
                         [0.1056,"3.08"],
                         [0.1267,"2.81"],
                         [0.1478,"2.60"],
                         [0.1689,"2.43"],
                         [0.1900,"2.29"],
                         [0.2111,"2.18"],
                         [0.2322,"2.08"],
                         [0.2534,"1.99"],
                         [0.2745,"1.91"],
                         [0.2956,"1.84"],
                         [0.3167,"1.78"],
                         [0.3378,"1.72"],
                         [0.3589,"1.67"],
                         [0.3800,"1.62"],
                         [0.4012,"1.58"],
                         [0.4223,"1.54"],
                  ]},
    });

    var y6 = [], y7 = [], y8= [];
         y6.push([0.0211,774]);
         y7.push([0.0211,66]);
         y8.push([0.0211,47]);
         y6.push([0.0422,846]);
         y7.push([0.0422,58]);
         y8.push([0.0422,52]);
         y6.push([0.0633,1385]);
         y7.push([0.0633,86]);
         y8.push([0.0633,84]);
         y6.push([0.0845,1233]);
         y7.push([0.0845,85]);
         y8.push([0.0845,77]);
         y6.push([0.1056,832]);
         y7.push([0.1056,62]);
         y8.push([0.1056,57]);
         y6.push([0.1267,578]);
         y7.push([0.1267,52]);
         y8.push([0.1267,45]);
         y6.push([0.1478,400]);
         y7.push([0.1478,40]);
         y8.push([0.1478,37]);
         y6.push([0.1689,333]);
         y7.push([0.1689,38]);
         y8.push([0.1689,35]);
         y6.push([0.1900,324]);
         y7.push([0.1900,37]);
         y8.push([0.1900,36]);
         y6.push([0.2111,293]);
         y7.push([0.2111,34]);
         y8.push([0.2111,36]);
         y6.push([0.2322,253]);
         y7.push([0.2322,33]);
         y8.push([0.2322,36]);
         y6.push([0.2534,202]);
         y7.push([0.2534,32]);
         y8.push([0.2534,35]);
         y6.push([0.2745,173]);
         y7.push([0.2745,32]);
         y8.push([0.2745,35]);
         y6.push([0.2956,130]);
         y7.push([0.2956,31]);
         y8.push([0.2956,35]);
         y6.push([0.3167,104]);
         y7.push([0.3167,31]);
         y8.push([0.3167,35]);
         y6.push([0.3378,87]);
         y7.push([0.3378,31]);
         y8.push([0.3378,37]);
         y6.push([0.3589,69]);
         y7.push([0.3589,32]);
         y8.push([0.3589,38]);
         y6.push([0.3800,60]);
         y7.push([0.3800,34]);
         y8.push([0.3800,40]);
         y6.push([0.4012,49]);
         y7.push([0.4012,36]);
         y8.push([0.4012,41]);
         y6.push([0.4223,44]);
         y7.push([0.4223,36]);
         y8.push([0.4223,44]);
    var plot9 = $.plot($("#chart9_div"), [
        {data: y6, label:"Av_I" },
        {data: y7, label:"SIGMA" },
        {data: y8, label:"sd" },
        ],
        { lines: {show: true},
          points: {show: false},
          selection: { mode: 'xy' },
          grid: {hoverable: true, clickable: true },
          xaxis: {ticks: [
                         [0.0211,"6.88"],
                         [0.0422,"4.87"],
                         [0.0633,"3.97"],
                         [0.0845,"3.44"],
                         [0.1056,"3.08"],
                         [0.1267,"2.81"],
                         [0.1478,"2.60"],
                         [0.1689,"2.43"],
                         [0.1900,"2.29"],
                         [0.2111,"2.18"],
                         [0.2322,"2.08"],
                         [0.2534,"1.99"],
                         [0.2745,"1.91"],
                         [0.2956,"1.84"],
                         [0.3167,"1.78"],
                         [0.3378,"1.72"],
                         [0.3589,"1.67"],
                         [0.3800,"1.62"],
                         [0.4012,"1.58"],
                         [0.4223,"1.54"],
                  ]},
    });

    var y9 = [], y10 = [], y11 = [], y12= [];
         y9.push([0.021,98.2]);
         y10.push([0.021,98.2]);
         y11.push([0.021,99.3]);
         y12.push([0.021,99.3]);
         y9.push([0.042,99.7]);
         y10.push([0.042,99.2]);
         y11.push([0.042,99.3]);
         y12.push([0.042,99.3]);
         y9.push([0.063,99.9]);
         y10.push([0.063,99.5]);
         y11.push([0.063,99.5]);
         y12.push([0.063,99.5]);
         y9.push([0.084,99.6]);
         y10.push([0.084,99.5]);
         y11.push([0.084,97.7]);
         y12.push([0.084,98.0]);
         y9.push([0.106,99.8]);
         y10.push([0.106,99.6]);
         y11.push([0.106,98.3]);
         y12.push([0.106,98.3]);
         y9.push([0.127,99.9]);
         y10.push([0.127,99.7]);
         y11.push([0.127,97.3]);
         y12.push([0.127,97.3]);
         y9.push([0.148,99.9]);
         y10.push([0.148,99.7]);
         y11.push([0.148,97.9]);
         y12.push([0.148,97.9]);
         y9.push([0.169,100.0]);
         y10.push([0.169,99.8]);
         y11.push([0.169,97.9]);
         y12.push([0.169,97.9]);
         y9.push([0.190,99.9]);
         y10.push([0.190,99.8]);
         y11.push([0.190,98.0]);
         y12.push([0.190,98.1]);
         y9.push([0.211,99.9]);
         y10.push([0.211,99.8]);
         y11.push([0.211,98.0]);
         y12.push([0.211,98.0]);
         y9.push([0.232,99.9]);
         y10.push([0.232,99.8]);
         y11.push([0.232,98.5]);
         y12.push([0.232,98.5]);
         y9.push([0.253,99.8]);
         y10.push([0.253,99.8]);
         y11.push([0.253,97.9]);
         y12.push([0.253,98.0]);
         y9.push([0.274,100.0]);
         y10.push([0.274,99.8]);
         y11.push([0.274,97.9]);
         y12.push([0.274,97.9]);
         y9.push([0.296,99.9]);
         y10.push([0.296,99.9]);
         y11.push([0.296,98.8]);
         y12.push([0.296,98.8]);
         y9.push([0.317,99.9]);
         y10.push([0.317,99.9]);
         y11.push([0.317,99.2]);
         y12.push([0.317,99.2]);
         y9.push([0.338,99.9]);
         y10.push([0.338,99.9]);
         y11.push([0.338,99.2]);
         y12.push([0.338,99.3]);
         y9.push([0.359,99.9]);
         y10.push([0.359,99.9]);
         y11.push([0.359,99.4]);
         y12.push([0.359,99.4]);
         y9.push([0.380,99.6]);
         y10.push([0.380,99.8]);
         y11.push([0.380,99.3]);
         y12.push([0.380,99.5]);
         y9.push([0.401,99.7]);
         y10.push([0.401,99.8]);
         y11.push([0.401,99.5]);
         y12.push([0.401,99.6]);
         y9.push([0.422,99.2]);
         y10.push([0.422,99.8]);
         y11.push([0.422,83.4]);
         y12.push([0.422,83.8]);
    var plot12 = $.plot($("#chart12_div"), [
        {data: y9, label:"%poss" },
        {data: y10, label:"C%poss" },
        {data: y11, label:"AnoCmp" },
        {data: y12, label:"AnoFrc" },
        ],
        { lines: {show: true},
          points: {show: false},
          selection: { mode: 'xy' },
          grid: {hoverable: true, clickable: true },
          xaxis: {ticks: [
                         [0.021,"6.88"],
                         [0.042,"4.87"],
                         [0.063,"3.97"],
                         [0.084,"3.44"],
                         [0.106,"3.08"],
                         [0.127,"2.81"],
                         [0.148,"2.60"],
                         [0.169,"2.43"],
                         [0.190,"2.29"],
                         [0.211,"2.18"],
                         [0.232,"2.08"],
                         [0.253,"1.99"],
                         [0.274,"1.91"],
                         [0.296,"1.84"],
                         [0.317,"1.78"],
                         [0.338,"1.72"],
                         [0.359,"1.67"],
                         [0.380,"1.62"],
                         [0.401,"1.58"],
                         [0.422,"1.54"],
                  ]},
    });

    var y13 = [], y14= [];
         y13.push([0.021,4.3]);
         y14.push([0.021,2.8]);
         y13.push([0.042,4.9]);
         y14.push([0.042,2.7]);
         y13.push([0.063,5.0]);
         y14.push([0.063,2.7]);
         y13.push([0.084,4.8]);
         y14.push([0.084,2.6]);
         y13.push([0.106,4.9]);
         y14.push([0.106,2.6]);
         y13.push([0.127,4.9]);
         y14.push([0.127,2.6]);
         y13.push([0.148,5.0]);
         y14.push([0.148,2.6]);
         y13.push([0.169,5.1]);
         y14.push([0.169,2.6]);
         y13.push([0.190,5.1]);
         y14.push([0.190,2.6]);
         y13.push([0.211,5.1]);
         y14.push([0.211,2.6]);
         y13.push([0.232,5.2]);
         y14.push([0.232,2.6]);
         y13.push([0.253,5.2]);
         y14.push([0.253,2.6]);
         y13.push([0.274,5.2]);
         y14.push([0.274,2.6]);
         y13.push([0.296,5.2]);
         y14.push([0.296,2.5]);
         y13.push([0.317,5.2]);
         y14.push([0.317,2.5]);
         y13.push([0.338,5.2]);
         y14.push([0.338,2.6]);
         y13.push([0.359,5.2]);
         y14.push([0.359,2.5]);
         y13.push([0.380,5.2]);
         y14.push([0.380,2.6]);
         y13.push([0.401,5.2]);
         y14.push([0.401,2.6]);
         y13.push([0.422,3.8]);
         y14.push([0.422,2.1]);
    var plot13 = $.plot($("#chart13_div"), [
        {data: y13, label:"Mlplct" },
        {data: y14, label:"AnoMlt" },
        ],
        { lines: {show: true},
          points: {show: false},
          selection: { mode: 'xy' },
          grid: {hoverable: true, clickable: true },
          xaxis: {ticks: [
                         [0.021,"6.88"],
                         [0.042,"4.87"],
                         [0.063,"3.97"],
                         [0.084,"3.44"],
                         [0.106,"3.08"],
                         [0.127,"2.81"],
                         [0.148,"2.60"],
                         [0.169,"2.43"],
                         [0.190,"2.29"],
                         [0.211,"2.18"],
                         [0.232,"2.08"],
                         [0.253,"1.99"],
                         [0.274,"1.91"],
                         [0.296,"1.84"],
                         [0.317,"1.78"],
                         [0.338,"1.72"],
                         [0.359,"1.67"],
                         [0.380,"1.62"],
                         [0.401,"1.58"],
                         [0.422,"1.54"],
                  ]},
    });

    var y15 = [], y16= [];
         y15.push([0.021,0.028]);
         y16.push([0.021,0.022]);
         y15.push([0.042,0.027]);
         y16.push([0.042,0.021]);
         y15.push([0.063,0.026]);
         y16.push([0.063,0.020]);
         y15.push([0.084,0.029]);
         y16.push([0.084,0.023]);
         y15.push([0.106,0.033]);
         y16.push([0.106,0.026]);
         y15.push([0.127,0.039]);
         y16.push([0.127,0.031]);
         y15.push([0.148,0.047]);
         y16.push([0.148,0.036]);
         y15.push([0.169,0.055]);
         y16.push([0.169,0.041]);
         y15.push([0.190,0.055]);
         y16.push([0.190,0.041]);
         y15.push([0.211,0.059]);
         y16.push([0.211,0.044]);
         y15.push([0.232,0.065]);
         y16.push([0.232,0.049]);
         y15.push([0.253,0.081]);
         y16.push([0.253,0.061]);
         y15.push([0.274,0.097]);
         y16.push([0.274,0.073]);
         y15.push([0.296,0.126]);
         y16.push([0.296,0.095]);
         y15.push([0.317,0.158]);
         y16.push([0.317,0.117]);
         y15.push([0.338,0.194]);
         y16.push([0.338,0.145]);
         y15.push([0.359,0.253]);
         y16.push([0.359,0.189]);
         y15.push([0.380,0.307]);
         y16.push([0.380,0.227]);
         y15.push([0.401,0.397]);
         y16.push([0.401,0.292]);
         y15.push([0.422,0.489]);
         y16.push([0.422,0.403]);
    var plot14 = $.plot($("#chart14_div"), [
        {data: y15, label:"Rpim" },
        {data: y16, label:"RpimO" },
        ],
        { lines: {show: true},
          points: {show: false},
          selection: { mode: 'xy' },
          grid: {hoverable: true, clickable: true },
          xaxis: {ticks: [
                         [0.021,"6.88"],
                         [0.042,"4.87"],
                         [0.063,"3.97"],
                         [0.084,"3.44"],
                         [0.106,"3.08"],
                         [0.127,"2.81"],
                         [0.148,"2.60"],
                         [0.169,"2.43"],
                         [0.190,"2.29"],
                         [0.211,"2.18"],
                         [0.232,"2.08"],
                         [0.253,"1.99"],
                         [0.274,"1.91"],
                         [0.296,"1.84"],
                         [0.317,"1.78"],
                         [0.338,"1.72"],
                         [0.359,"1.67"],
                         [0.380,"1.62"],
                         [0.401,"1.58"],
                         [0.422,"1.54"],
                  ]},
    });

    var y17 = [], y18 = [], y19 = [], y20 = [], y21= [];
         y17.push([0.021,0.048]);
         y18.push([0.021,0.048]);
         y19.push([0.021,0.038]);
         y20.push([0.021,0.054]);
         y21.push([0.021,0.059]);
         y17.push([0.042,0.047]);
         y18.push([0.042,0.047]);
         y19.push([0.042,0.039]);
         y20.push([0.042,0.053]);
         y21.push([0.042,0.055]);
         y17.push([0.063,0.045]);
         y18.push([0.063,0.046]);
         y19.push([0.063,0.037]);
         y20.push([0.063,0.050]);
         y21.push([0.063,0.053]);
         y17.push([0.084,0.050]);
         y18.push([0.084,0.051]);
         y19.push([0.084,0.041]);
         y20.push([0.084,0.056]);
         y21.push([0.084,0.061]);
         y17.push([0.106,0.057]);
         y18.push([0.106,0.058]);
         y19.push([0.106,0.046]);
         y20.push([0.106,0.062]);
         y21.push([0.106,0.068]);
         y17.push([0.127,0.068]);
         y18.push([0.127,0.069]);
         y19.push([0.127,0.056]);
         y20.push([0.127,0.075]);
         y21.push([0.127,0.081]);
         y17.push([0.148,0.083]);
         y18.push([0.148,0.083]);
         y19.push([0.148,0.068]);
         y20.push([0.148,0.093]);
         y21.push([0.148,0.097]);
         y17.push([0.169,0.096]);
         y18.push([0.169,0.095]);
         y19.push([0.169,0.079]);
         y20.push([0.169,0.108]);
         y21.push([0.169,0.110]);
         y17.push([0.190,0.096]);
         y18.push([0.190,0.095]);
         y19.push([0.190,0.079]);
         y20.push([0.190,0.109]);
         y21.push([0.190,0.112]);
         y17.push([0.211,0.103]);
         y18.push([0.211,0.103]);
         y19.push([0.211,0.085]);
         y20.push([0.211,0.116]);
         y21.push([0.211,0.121]);
         y17.push([0.232,0.115]);
         y18.push([0.232,0.115]);
         y19.push([0.232,0.094]);
         y20.push([0.232,0.128]);
         y21.push([0.232,0.133]);
         y17.push([0.253,0.143]);
         y18.push([0.253,0.142]);
         y19.push([0.253,0.117]);
         y20.push([0.253,0.159]);
         y21.push([0.253,0.165]);
         y17.push([0.274,0.171]);
         y18.push([0.274,0.170]);
         y19.push([0.274,0.139]);
         y20.push([0.274,0.192]);
         y21.push([0.274,0.200]);
         y17.push([0.296,0.222]);
         y18.push([0.296,0.220]);
         y19.push([0.296,0.181]);
         y20.push([0.296,0.251]);
         y21.push([0.296,0.261]);
         y17.push([0.317,0.277]);
         y18.push([0.317,0.274]);
         y19.push([0.317,0.225]);
         y20.push([0.317,0.314]);
         y21.push([0.317,0.329]);
         y17.push([0.338,0.341]);
         y18.push([0.338,0.339]);
         y19.push([0.338,0.277]);
         y20.push([0.338,0.383]);
         y21.push([0.338,0.406]);
         y17.push([0.359,0.442]);
         y18.push([0.359,0.441]);
         y19.push([0.359,0.359]);
         y20.push([0.359,0.492]);
         y21.push([0.359,0.520]);
         y17.push([0.380,0.534]);
         y18.push([0.380,0.530]);
         y19.push([0.380,0.433]);
         y20.push([0.380,0.599]);
         y21.push([0.380,0.627]);
         y17.push([0.401,0.692]);
         y18.push([0.401,0.682]);
         y19.push([0.401,0.562]);
         y20.push([0.401,0.770]);
         y21.push([0.401,0.791]);
         y17.push([0.422,0.813]);
         y18.push([0.422,0.827]);
         y19.push([0.422,0.643]);
         y20.push([0.422,0.907]);
         y21.push([0.422,0.982]);
    var plot15 = $.plot($("#chart15_div"), [
        {data: y17, label:"Rmeas" },
        {data: y18, label:"Rmeas0" },
        {data: y19, label:"(Rsym)" },
        {data: y20, label:"PCV" },
        {data: y21, label:"PCV0" },
        ],
        { lines: {show: true},
          points: {show: false},
          selection: { mode: 'xy' },
          grid: {hoverable: true, clickable: true },
          xaxis: {ticks: [
                         [0.021,"6.88"],
                         [0.042,"4.87"],
                         [0.063,"3.97"],
                         [0.084,"3.44"],
                         [0.106,"3.08"],
                         [0.127,"2.81"],
                         [0.148,"2.60"],
                         [0.169,"2.43"],
                         [0.190,"2.29"],
                         [0.211,"2.18"],
                         [0.232,"2.08"],
                         [0.253,"1.99"],
                         [0.274,"1.91"],
                         [0.296,"1.84"],
                         [0.317,"1.78"],
                         [0.338,"1.72"],
                         [0.359,"1.67"],
                         [0.380,"1.62"],
                         [0.401,"1.58"],
                         [0.422,"1.54"],
                  ]},
    });

    var y22 = [], y23 = [], y24= [];
         y22.push([0.0211,0.030]);
         y23.push([0.0211,0.088]);
         y24.push([0.0211,0.998]);
         y22.push([0.0422,-0.058]);
         y23.push([0.0422,-0.162]);
         y24.push([0.0422,0.998]);
         y22.push([0.0633,0.011]);
         y23.push([0.0633,-0.009]);
         y24.push([0.0633,0.998]);
         y22.push([0.0845,0.151]);
         y23.push([0.0845,0.278]);
         y24.push([0.0845,0.997]);
         y22.push([0.1056,0.141]);
         y23.push([0.1056,-0.469]);
         y24.push([0.1056,0.996]);
         y22.push([0.1267,0.076]);
         y23.push([0.1267,-0.150]);
         y24.push([0.1267,0.995]);
         y22.push([0.1478,0.038]);
         y23.push([0.1478,0.079]);
         y24.push([0.1478,0.993]);
         y22.push([0.1689,-0.013]);
         y23.push([0.1689,-0.132]);
         y24.push([0.1689,0.991]);
         y22.push([0.1900,0.070]);
         y23.push([0.1900,0.161]);
         y24.push([0.1900,0.992]);
         y22.push([0.2111,0.052]);
         y23.push([0.2111,0.251]);
         y24.push([0.2111,0.991]);
         y22.push([0.2322,0.048]);
         y23.push([0.2322,0.020]);
         y24.push([0.2322,0.990]);
         y22.push([0.2534,0.014]);
         y23.push([0.2534,-0.316]);
         y24.push([0.2534,0.986]);
         y22.push([0.2745,0.018]);
         y23.push([0.2745,0.186]);
         y24.push([0.2745,0.981]);
         y22.push([0.2956,0.011]);
         y23.push([0.2956,-0.338]);
         y24.push([0.2956,0.970]);
         y22.push([0.3167,-0.008]);
         y23.push([0.3167,0.267]);
         y24.push([0.3167,0.952]);
         y22.push([0.3378,0.016]);
         y23.push([0.3378,0.033]);
         y24.push([0.3378,0.926]);
         y22.push([0.3589,0.047]);
         y23.push([0.3589,-0.634]);
         y24.push([0.3589,0.895]);
         y22.push([0.3800,0.023]);
         y23.push([0.3800,0.059]);
         y24.push([0.3800,0.856]);
         y22.push([0.4012,0.015]);
         y23.push([0.4012,-0.225]);
         y24.push([0.4012,0.781]);
         y22.push([0.4223,0.032]);
         y24.push([0.4223,0.642]);
    var plot16 = $.plot($("#chart16_div"), [
        {data: y22, label:"CC_anom" },
        {data: y23, label:"CC_cen" },
        {data: y24, label:"CC_Imean" },
        ],
        { lines: {show: true},
          points: {show: false},
          selection: { mode: 'xy' },
          grid: {hoverable: true, clickable: true },
          xaxis: {ticks: [
                         [0.0211,"6.88"],
                         [0.0422,"4.87"],
                         [0.0633,"3.97"],
                         [0.0845,"3.44"],
                         [0.1056,"3.08"],
                         [0.1267,"2.81"],
                         [0.1478,"2.60"],
                         [0.1689,"2.43"],
                         [0.1900,"2.29"],
                         [0.2111,"2.18"],
                         [0.2322,"2.08"],
                         [0.2534,"1.99"],
                         [0.2745,"1.91"],
                         [0.2956,"1.84"],
                         [0.3167,"1.78"],
                         [0.3378,"1.72"],
                         [0.3589,"1.67"],
                         [0.3800,"1.62"],
                         [0.4012,"1.58"],
                         [0.4223,"1.54"],
                  ]},
    });

    var y25 = [], y26= [];
         y25.push([0.0211,1.024]);
         y26.push([0.0211,1.081]);
         y25.push([0.0422,0.945]);
         y26.push([0.0422,0.849]);
         y25.push([0.0633,1.010]);
         y26.push([0.0633,0.993]);
         y25.push([0.0845,1.170]);
         y26.push([0.0845,1.260]);
         y25.push([0.1056,1.150]);
         y26.push([0.1056,0.613]);
         y25.push([0.1267,1.078]);
         y26.push([0.1267,0.882]);
         y25.push([0.1478,1.039]);
         y26.push([0.1478,1.055]);
         y25.push([0.1689,0.988]);
         y26.push([0.1689,0.863]);
         y25.push([0.1900,1.073]);
         y26.push([0.1900,1.187]);
         y25.push([0.2111,1.053]);
         y26.push([0.2111,1.230]);
         y25.push([0.2322,1.049]);
         y26.push([0.2322,0.999]);
         y25.push([0.2534,1.013]);
         y26.push([0.2534,0.699]);
         y25.push([0.2745,1.019]);
         y26.push([0.2745,1.292]);
         y25.push([0.2956,1.010]);
         y26.push([0.2956,0.734]);
         y25.push([0.3167,0.992]);
         y26.push([0.3167,0.575]);
         y25.push([0.3378,1.017]);
         y26.push([0.3378,1.018]);
         y25.push([0.3589,1.048]);
         y26.push([0.3589,0.773]);
         y25.push([0.3800,1.023]);
         y26.push([0.3800,0.963]);
         y25.push([0.4012,1.015]);
         y26.push([0.4012,0.775]);
         y25.push([0.4223,1.032]);
    var plot17 = $.plot($("#chart17_div"), [
        {data: y25, label:"RCR_anom" },
        {data: y26, label:"RCR_cen" },
        ],
        { lines: {show: true},
          points: {show: false},
          selection: { mode: 'xy' },
          grid: {hoverable: true, clickable: true },
          xaxis: {ticks: [
                         [0.0211,"6.88"],
                         [0.0422,"4.87"],
                         [0.0633,"3.97"],
                         [0.0845,"3.44"],
                         [0.1056,"3.08"],
                         [0.1267,"2.81"],
                         [0.1478,"2.60"],
                         [0.1689,"2.43"],
                         [0.1900,"2.29"],
                         [0.2111,"2.18"],
                         [0.2322,"2.08"],
                         [0.2534,"1.99"],
                         [0.2745,"1.91"],
                         [0.2956,"1.84"],
                         [0.3167,"1.78"],
                         [0.3378,"1.72"],
                         [0.3589,"1.67"],
                         [0.3800,"1.62"],
                         [0.4012,"1.58"],
                         [0.4223,"1.54"],
                  ]},
    });


    function showTooltip(x, y, contents) {
        $('<div id=tooltip>' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y + 5,
            left: x + 5,
            border: '1px solid #fdd',
            padding: '2px',
            'background-color': '#fee',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    }

    var previousPoint = null;
    $("#chart3_div").bind("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (true) {
            if (item) {
                if (previousPoint != item.datapoint) {
                    previousPoint = item.datapoint;

                    $("#tooltip").remove();
                    var x = item.datapoint[0].toFixed(2),
                        y = item.datapoint[1].toFixed(2);

                    showTooltip(item.pageX, item.pageY,
                                item.series.label + " at " + x + " = " + y);
                }
            }
            else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        }
    });
    $("#chart7_div").bind("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (true) {
            if (item) {
                if (previousPoint != item.datapoint) {
                    previousPoint = item.datapoint;

                    $("#tooltip").remove();
                    var x = (Math.sqrt(1/item.datapoint[0])).toFixed(2),
                        y = item.datapoint[1].toFixed(2);

                    showTooltip(item.pageX, item.pageY,
                                item.series.label + " at " + x + " = " + y);
                }
            }
            else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        }
    });
    $("#chart8_div").bind("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (true) {
            if (item) {
                if (previousPoint != item.datapoint) {
                    previousPoint = item.datapoint;

                    $("#tooltip").remove();
                    var x = (Math.sqrt(1/item.datapoint[0])).toFixed(2),
                        y = item.datapoint[1].toFixed(2);

                    showTooltip(item.pageX, item.pageY,
                                item.series.label + " at " + x + " = " + y);
                }
            }
            else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        }
    });
    $("#chart9_div").bind("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (true) {
            if (item) {
                if (previousPoint != item.datapoint) {
                    previousPoint = item.datapoint;

                    $("#tooltip").remove();
                    var x = (Math.sqrt(1/item.datapoint[0])).toFixed(2),
                        y = item.datapoint[1].toFixed(2);

                    showTooltip(item.pageX, item.pageY,
                                item.series.label + " at " + x + " = " + y);
                }
            }
            else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        }
    });
    $("#chart12_div").bind("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (true) {
            if (item) {
                if (previousPoint != item.datapoint) {
                    previousPoint = item.datapoint;

                    $("#tooltip").remove();
                    var x = (Math.sqrt(1/item.datapoint[0])).toFixed(2),
                        y = item.datapoint[1].toFixed(2);

                    showTooltip(item.pageX, item.pageY,
                                item.series.label + " at " + x + " = " + y);
                }
            }
            else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        }
    });
    $("#chart13_div").bind("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (true) {
            if (item) {
                if (previousPoint != item.datapoint) {
                    previousPoint = item.datapoint;

                    $("#tooltip").remove();
                    var x = (Math.sqrt(1/item.datapoint[0])).toFixed(2),
                        y = item.datapoint[1].toFixed(2);

                    showTooltip(item.pageX, item.pageY,
                                item.series.label + " at " + x + " = " + y);
                }
            }
            else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        }
    });
    $("#chart14_div").bind("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (true) {
            if (item) {
                if (previousPoint != item.datapoint) {
                    previousPoint = item.datapoint;

                    $("#tooltip").remove();
                    var x = (Math.sqrt(1/item.datapoint[0])).toFixed(2),
                        y = item.datapoint[1].toFixed(2);

                    showTooltip(item.pageX, item.pageY,
                                item.series.label + " at " + x + " = " + y);
                }
            }
            else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        }
    });
    $("#chart15_div").bind("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (true) {
            if (item) {
                if (previousPoint != item.datapoint) {
                    previousPoint = item.datapoint;

                    $("#tooltip").remove();
                    var x = (Math.sqrt(1/item.datapoint[0])).toFixed(2),
                        y = item.datapoint[1].toFixed(2);

                    showTooltip(item.pageX, item.pageY,
                                item.series.label + " at " + x + " = " + y);
                }
            }
            else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        }
    });
    $("#chart16_div").bind("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (true) {
            if (item) {
                if (previousPoint != item.datapoint) {
                    previousPoint = item.datapoint;

                    $("#tooltip").remove();
                    var x = (Math.sqrt(1/item.datapoint[0])).toFixed(2),
                        y = item.datapoint[1].toFixed(2);

                    showTooltip(item.pageX, item.pageY,
                                item.series.label + " at " + x + " = " + y);
                }
            }
            else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        }
    });
    $("#chart17_div").bind("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (true) {
            if (item) {
                if (previousPoint != item.datapoint) {
                    previousPoint = item.datapoint;

                    $("#tooltip").remove();
                    var x = (Math.sqrt(1/item.datapoint[0])).toFixed(2),
                        y = item.datapoint[1].toFixed(2);

                    showTooltip(item.pageX, item.pageY,
                                item.series.label + " at " + x + " = " + y);
                }
            }
            else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        }
    });

});
</script>
 </body>
</html>

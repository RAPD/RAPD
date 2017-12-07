var express    = require('express');
var router     = express.Router();
const config   = require('../config');
const mongoose = require('mongoose');

const Activity = require('../models/activity');
const Login = require('../models/login');
const Result = require('../models/result');

// Redis
// const redis = require('redis');
// var redis_client = redis.createClient(config.redis_port, config.redis_host);


/*

Count of all results by day
db.results.aggregate([{$match:{timestamp:{$exists:true}}},{$group:{_id : { month: { $month: "$timestamp" }, day: { $dayOfMonth: "$timestamp" }, year: { $year: "$timestamp" } }, count: { $sum: 1 }}}])


Some time-based searches
var today = new Date();
var lastWeekStart = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 7);
var lastWeekEnd = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 7);
var start = new Date(lastWeekStart.setHours(0,0,0,0));
var end = new Date(lastWeekEnd.setHours(23,59,59,999));

RESULTS
=======
ALL
db.results.aggregate([{$match:{timestamp:{$gte:lastWeekStart}}},{$group:{_id : { month: { $month: "$timestamp" }, day: { $dayOfMonth: "$timestamp" }, year: { $year: "$timestamp" } }, count: { $sum: 1 }}}])

BY plugin_type
db.results.aggregate([{$match:{timestamp:{$gte:lastWeekStart}}},{$group:{_id : { month: { $month: "$timestamp" }, day: { $dayOfMonth: "$timestamp" }, year: { $year: "$timestamp" } , plugin_type:"$plugin_type"}, count: { $sum: 1 }}}])


LOGINS
======
Grouped by success true/false
db.logins.aggregate([{$match:{timestamp:{$gte:lastWeekStart}}},{$group:{_id:{month: { $month: "$timestamp" },day: { $dayOfMonth: "$timestamp" },year: { $year: "$timestamp" },success:"$success"  },count: { $sum: 1 }}}])

*/

// routes that end with jobs
// ----------------------------------------------------
// These are redis-based queries
// route to return all current requests (GET http://localhost:3000/api/requests)
router.route('/dashboard/results')

  // get all the current available overwatch data
  .get(function(req, res) {

    // Set date to start
    let today = new Date();
    let twoWeekStart = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 14);

    // Aggregate results
    Result.aggregate([
      {$match:{
        timestamp:{$gte:twoWeekStart}
      }},
      {$group:{
        _id:{
          day:{$dayOfMonth:'$timestamp'},
          month:{$month:'$timestamp'},
          year:{$year:'$timestamp'},
          plugin_type:'$plugin_type'
        },
        count:{$sum:1}
      }}
    ], function(err, results) {
      if (err) {
        console.error(err);
        res.status(500).json({
          success:false,
          message:err
        });
      } else {

        // Organize to a more plotable form
        let return_obj = {datasets:[], labels:[]}
            staging_obj = {};

        config.plugin_types.forEach(function(plugin_type) {
          staging_obj[plugin_type] = {};
        });

        while (twoWeekStart < today) {
          let month = twoWeekStart.getMonth()+1,
              date = twoWeekStart.getDate();
          return_obj.labels.push(`${month}-${date}`)
          config.plugin_types.forEach(function(plugin_type) {
            staging_obj[plugin_type][`${month}-${date}`] = 0;
          });
          twoWeekStart.setDate(date+1);
        }

        // Put the results into an object
        results.forEach(function(result) {
          try {
            staging_obj[result._id.plugin_type.toLowerCase()][`${result._id.month}-${result._id.day}`] = result.count;
          } catch (e) {
            console.error(e);
          }
        });

        // Now put it all together
        config.plugin_types.forEach(function(plugin_type) {
          twoWeekStart = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 14);
          let my_dataset = {label:plugin_type, data:[]};
          while (twoWeekStart < today) {
            let month = twoWeekStart.getMonth()+1,
                date = twoWeekStart.getDate();
                my_dataset.data.push(staging_obj[plugin_type][`${month}-${date}`]);
            twoWeekStart.setDate(date+1);
          }
          return_obj.datasets.push(my_dataset);
        });

        // console.log('return_obj', return_obj);
        // console.log(return_obj);
        res.status(200).json({
          success:true,
          results:return_obj
        });
      }
    });
  }); // End of .get(function(req, res) {

router.route('/dashboard/logins')

// get all the current available overwatch data
.get(function(req, res) {

  // Set date to start
  let today = new Date();
  let twoWeekStart = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 14);

  // Aggregate results
  Login.aggregate([
    {$match:{
      timestamp:{$gte:twoWeekStart}
    }},
    {$group:{
      _id:{
        day:{$dayOfMonth:'$timestamp'},
        month:{$month:'$timestamp'},
        year:{$year:'$timestamp'},
        success:'$success'
      },
      count:{$sum:1}
    }}
  ], function(err, results) {
    if (err) {
      console.error(err);
      res.status(500).json({
        success:false,
        message:err
      });
    } else {

      // Organize to a more plotable form
      let return_obj = {datasets:[], labels:[]}
          staging_obj = {'success':{},'fail':{}},
          states = ['success', 'fail'],
          colors = {success:'rgba(0, 256, 0, 1)',fail:'rgba(256, 0, 0, 1)'};

      // console.log(staging_obj);
      // console.log(return_obj);

      while (twoWeekStart < today) {
        let month = twoWeekStart.getMonth()+1,
            date = twoWeekStart.getDate();
        return_obj.labels.push(`${month}-${date}`)
        states.forEach(function(state) {
          staging_obj[state][`${month}-${date}`] = 0;
        });
        twoWeekStart.setDate(date+1);
      }
      // console.log(staging_obj);
      // console.log(return_obj);

      // Put the results into the staging object
      results.forEach(function(result) {
        // console.log('result', result);
        if (result._id.success == true) {
          staging_obj.success[`${result._id.month}-${result._id.day}`] = result.count;
        } else {
          staging_obj.fail[`${result._id.month}-${result._id.day}`] = result.count;
        }
      });

      // Now put it all together
      states.forEach(function(state) {
        twoWeekStart = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 14);
        let my_dataset = {label:state, data:[]};
        while (twoWeekStart < today) {
          let month = twoWeekStart.getMonth()+1,
              date = twoWeekStart.getDate();
              my_dataset.data.push(staging_obj[state][`${month}-${date}`]);
          twoWeekStart.setDate(date+1);
        }
        return_obj.datasets.push(my_dataset);
      });

      // console.log('return_obj', return_obj);
      res.status(200).json({
        success:true,
        logins:return_obj
      });
    }
  });
}); // End of .get(function(req, res) {

  router.route('/dashboard/server_activities')

  // get all the current available overwatch data
  .get(function(req, res) {

    // Set date to start
    let today = new Date();
    let twoWeekStart = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 14);

    // Aggregate results
    Activity.aggregate([
      {$match:{
        timestamp:{$gte:twoWeekStart}
      }},
      {$group:{
        _id:{
          day:{$dayOfMonth:'$timestamp'},
          month:{$month:'$timestamp'},
          year:{$year:'$timestamp'},
          source:'$source'
        },
        count:{$sum:1}
      }}
    ], function(err, results) {
      if (err) {
        console.error(err);
        res.status(500).json({
          success:false,
          message:err
        });
      } else {

        // Organize to a more plotable form
        let return_obj = {datasets:[], labels:[]}
            staging_obj = {'rest':{},'websocket':{}},
            sources = ['rest', 'websocket'],
            colors = {rest:'rgb(255, 159, 64)', websocket:'rgb(153, 102, 255)'};

        // console.log(staging_obj);
        // console.log(return_obj);

        while (twoWeekStart < today) {
          let month = twoWeekStart.getMonth()+1,
              date = twoWeekStart.getDate();
          return_obj.labels.push(`${month}-${date}`)
          sources.forEach(function(source) {
            staging_obj[source][`${month}-${date}`] = 0;
          });
          twoWeekStart.setDate(date+1);
        }
        // console.log(staging_obj);
        // console.log(return_obj);

        // Put the results into the staging object
        results.forEach(function(result) {
          // console.log('result', result);
          try {
            staging_obj[result._id.source][`${result._id.month}-${result._id.day}`] = result.count;
          } catch (e) {
            console.error(e);
          }

        });

        // Now put it all together
        sources.forEach(function(source) {
          twoWeekStart = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 14);
          let my_dataset = {label:source, fill:false, data:[]};
          while (twoWeekStart < today) {
            let month = twoWeekStart.getMonth()+1,
                date = twoWeekStart.getDate();
                my_dataset.data.push(staging_obj[source][`${month}-${date}`]);
            twoWeekStart.setDate(date+1);
          }
          return_obj.datasets.push(my_dataset);
        });

        // console.log('return_obj', return_obj);
        res.status(200).json({
          success:true,
          activities:return_obj
        });
      }
    });
  }); // End of .get(function(req, res) {
// db.activities.aggregate([{$match:{timestamp:{$gte:twoWeekStart}}},{$group:{_id:{day:{$dayOfMonth:'$timestamp'},month:{$month:'$timestamp'},year:{$year:'$timestamp'},source:'$source' },count:{$sum:1}}} ])
module.exports = router;

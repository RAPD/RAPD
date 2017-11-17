var express    = require('express');
var router     = express.Router();
const config   = require('../config');
const mongoose = require('mongoose');

// Redis
const redis = require('redis');
var redis_client = redis.createClient(config.redis_port, config.redis_host);


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


  }); // End of .get(function(req, res) {
module.exports = router;

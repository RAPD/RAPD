var express  = require('express');
var router   = express.Router();
// var mongoose = require('../models/mongoose');
const config = require('../config');

// Redis
const redis  = require('redis');
var redis_client = redis.createClient(config.redis_port, config.redis_host);

// routes that end with jobs
// ----------------------------------------------------
// These are redis-based queries
// route to return all current requests (GET http://localhost:3000/api/requests)
router.route('/jobs/submit')

  // add a request for a process to launch (accessed at PUT api/requests)
  .put(function(req, res) {

    let request = req.body.request;

    console.log(request);

    redis_client.lpush('RAPD_JOBS', JSON.stringify(request), function(err, queue_length) {
      if (err) {
        console.error(err);
        res.status(500).json({
          success: false,
          error: err
        });
      } else {
        console.log('Job added to RAPD_JOBS queue length:', queue_length);
        res.status(200).json({
          success: true,
          queue_length: queue_length
        });
      }
    });
  }); // End .put(function(req,res) {

module.exports = router;

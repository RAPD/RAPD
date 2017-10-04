var express = require('express');
var router = express.Router();

// routes that end with jobs
// ----------------------------------------------------
// These are redis-based queries
// route to return all current requests (GET http://localhost:3000/api/requests)
router.route('/requests')

  // add a request for a process to launch (accessed at PUT http://localhost:3000/api/requests)
  .put(function(req,res) {

    console.log('PUT request');

    let request = req.body.request;

    redis_client.lpush('RAPD_CLIENT_REQUESTS', JSON.stringify(request), function(err, queue_length) {
      if (err) {
        console.error(err);
        let params = {
          success: false,
          error: err
        };
        res.json(params);
      } else {
        console.log('queue length:', queue_length);
        let params = {
          success: true,
          queue_length: queue_length
        };
        res.json(params);
      }
    });
  }); // End .put(function(req,res) {

module.exports = router;

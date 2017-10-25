var express = require('express');
var router = express.Router();
const config = require('../config');

// routes that end with jobs
// ----------------------------------------------------
// These are redis-based queries
// route to return all current requests (GET http://localhost:3000/api/requests)
router.route('/jobs/submit')

  // add a request for a process to launch (accessed at PUT api/requests)
  .put(function(req, res) {

    let request = req.body.request;

    console.log(request);

    res.status(200).json({
            success: true,
            queue_length: 1
    });

    // redis_client.lpush('RAPD_CLIENT_REQUESTS', JSON.stringify(request), function(err, queue_length) {
    //   if (err) {
    //     console.error(err);
    //     let params = {
    //       success: false,
    //       error: err
    //     };
    //     res.json(params);
    //   } else {
    //     console.log('queue length:', queue_length);
    //     let params = {
    //       success: true,
    //       queue_length: queue_length
    //     };
    //     res.json(params);
    //   }
    // });
  }); // End .put(function(req,res) {

module.exports = router;

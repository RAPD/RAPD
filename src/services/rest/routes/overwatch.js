var express  = require('express');
var router   = express.Router();
const config = require('../config');

// Redis
const redis  = require('redis');
var redis_client = redis.createClient(config.redis_port, config.redis_host);

// routes that end with jobs
// ----------------------------------------------------
// These are redis-based queries
// route to return all current requests (GET http://localhost:3000/api/requests)
router.route('/overwatches')

  // get all the current available overwatch data
  .get(function(req, res) {

    let return_hash = {};

    redis_client.keys('OW:*', function(err, ow_keys) {
      if (err) {
        console.error(err);
        res.status(500).json({
          success: false,
          message: err
        });
      } else {
        ow_keys.forEach(function(ow_key) {
          redis_client.hgetall(ow_key, function(err, ow_hash) {
            if (err) {
              console.error(err);
              res.status(500).json({
                success: false,
                message: err
              });
            } else {
              console.log(ow_key);
              if (ow_hash.ow_type === 'overwatcher') {
                console.log('New overwatcher', ow_hash.id);
                ow_hash.children = [];
                Object.entries(return_hash).forEach(([key, maybe_child]) => {
                  // console.log(maybe_child.id);
                  if (ow_hash.id === maybe_child.ow_id) {
                    console.log('  found child', maybe_child.id);
                    ow_hash.children.push(maybe_child);
                    delete return_hash[key];
                  }
                });
                return_hash[ow_key] = ow_hash;
              } else {
                console.log('New child', ow_hash.id);
                let found = false;
                Object.entries(return_hash).forEach(([key, maybe_parent]) => {
                  if (ow_hash.ow_id === maybe_parent.id) {
                    console.log('  found parent', maybe_parent.id);
                    found = true;
                    maybe_parent.children.push(ow_hash);
                  }
                });
                if (! found) {
                  console.log('  parent not found', ow_hash.id)
                  return_hash[ow_key] = ow_hash;
                }
              }
            }
          });
        });
        // Return the components
        console.log('Returning found components', return_hash);
        res.status(200).json(
          {success:true,
          overwatches:return_hash
        });
      }
    });

  }); // end of .get

  // add a request for a process to launch (accessed at PUT api/requests)
  // .put(function(req, res) {
  //
  //   let request = req.body.request;
  //
  //   console.log(request);
  //
  //   redis_client.lpush('RAPD_JOBS', JSON.stringify(request), function(err, queue_length) {
  //     if (err) {
  //       console.error(err);
  //       res.status(500).json({
  //         success: false,
  //         error: err
  //       });
  //     } else {
  //       console.log('Job added to RAPD_JOBS queue length:', queue_length);
  //       res.status(200).json({
  //         success: true,
  //         queue_length: queue_length
  //       });
  //     }
  //   });
  // }); // End .put(function(req,res) {

module.exports = router;

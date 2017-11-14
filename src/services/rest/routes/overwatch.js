// const bluebird = require('bluebird');
var express    = require('express');
var router     = express.Router();
const config   = require('../config');

// Redis
const redis = require('redis');
// Add promise layer to redis calls
// bluebird.promisifyAll(redis.RedisClient.prototype);
// bluebird.promisifyAll(redis.Multi.prototype);
var redis_client = redis.createClient(config.redis_port, config.redis_host);

// routes that end with jobs
// ----------------------------------------------------
// These are redis-based queries
// route to return all current requests (GET http://localhost:3000/api/requests)
router.route('/overwatches')

  // get all the current available overwatch data
  .get(function(req, res) {

    let return_hash = {};
    let child_hash = {};

    redis_client.keys('OW:*', function(err, ow_keys) {
      if (err) {
        console.error(err);
        res.status(500).json({
          success: false,
          message: err
        });
      } else {
        let num_keys = ow_keys.length;
        console.log('num_keys =', num_keys);
        let key_counter = 0;
        ow_keys.forEach(function(ow_key) {
          if (ow_key.length > 40) {
            console.log('Ignoring', ow_key)
            key_counter += 1;
          } else {
            redis_client.hgetall(ow_key, function(err, ow_hash) {
              key_counter += 1;
              if (err) {
                console.error(err);
                res.status(500).json({
                  success: false,
                  message: err
                });
              } else {

                // Manipulate dates
                ow_hash.timestamp  = ow_hash.timestamp * 1000;
                ow_hash.start_time = ow_hash.start_time * 1000;

                // An overwatcher
                if (ow_hash.ow_type === 'overwatcher') {
                  console.log('New overwatcher', ow_hash.id);
                  // Create a place to put children
                  ow_hash.children = [];
                  // Look for child processes`
                  Object.entries(child_hash).forEach(([key, maybe_child]) => {
                    if (ow_hash.id === maybe_child.ow_id) {
                      console.log('  found child', maybe_child.id);
                      ow_hash.children.push(maybe_child);
                      delete return_hash[key];
                    }
                  });
                  // Save the hash
                  return_hash[ow_key] = ow_hash;

                // A managed process
                } else {
                  console.log('New child', ow_hash.id);
                  let found = false;
                  // Look for a parental process
                  Object.entries(return_hash).forEach(([key, maybe_parent]) => {
                    if (ow_hash.ow_id === maybe_parent.id) {
                      console.log('  found parent', maybe_parent.id);
                      found = true;
                      maybe_parent.children.push(ow_hash);
                    }
                  });
                  // No parent found yet
                  if (! found) {
                    console.log('  parent not found', ow_hash.id)
                    child_hash[ow_key] = ow_hash;
                  }
                }
                // If we are done, send back the data
                if (key_counter === num_keys) {
                  // Return the components
                  console.log('Returning found components', return_hash);
                  res.status(200).json({
                    success:true,
                    overwatches:Object.values(return_hash)
                  });
                }
              }
            }); // END redis_client.hgetall(ow_key, function(err, ow_hash) {
          }
        }); // END ow_keys.forEach(function(ow_key) {
      }
    }); // END redis_client.keys('OW:*', function(err, ow_keys) {
  }); // end of .get


module.exports = router;

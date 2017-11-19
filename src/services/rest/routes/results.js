var express = require('express');
var router = express.Router();

// const Group = require('../models/group');
const Activity = require('../models/activity');
const Session  = require('../models/session');
const Result   = require('../models/result');

// on routes that end in /results
// ----------------------------------------------------
router.route('/resultsbysession/:session_id')

    // get the session with that id (accessed at GET http://localhost:8080/api/bears/:bear_id)
    .get(function(req, res) {
        Result.find({session_id:req.params.session_id}, function(err, results) {
          if (err) {
            console.error(err);
            res.status(500).json({
              success: false,
              message: err
            });
          } else {
            console.log(results.length, 'results found for session', req.params.session_id);
            res.status(200).json({
              success: true,
              results: results
            });
            // console.log(req.decoded._doc);
            // let new_activity = new Activity({
            //   activity_type:'get_resultsbysession'
            // }).save();
          }
        });
    });

module.exports = router;

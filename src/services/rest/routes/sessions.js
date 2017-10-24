var express = require('express');
var router = express.Router();
var mongoose = require('mongoose');

// const Group = require('../models/group');
const Session = require('../models/session');
// const Result = require('../models/result');

// on routes that end in /sessions
// ----------------------------------------------------
router.route('/sessions')

    // create a session (accessed at POST api/sessions)
    .post(function(req, res) {

        var session = new Session(JSON.parse(req.body.session));     // create a new instance of the Session model

        // save the bear and check for errors
        session.save(function(err) {
            if (err)
                res.send(err);

            res.json({ message: 'Session created!' });
        });

    })

    // get all the sessions (accessed at GET api/sessions)
    .get(function(req, res) {

      var find_search = { group: { $in: req.decoded._doc.groups}};
      if (req.decoded._doc.role === 'site_admin') {
        find_search = {}
      }

      Session.
        find(find_search).
        populate('group', 'groupname').
        sort({end: -1}).
        exec(function(err, sessions) {
          if (err) {
            console.error(err);
            res.send(err);
          } else {
            console.log(sessions);
            res.json(sessions);
          }
        });
    });

// on routes that end in /sessions/:session_id
// ----------------------------------------------------
router.route('/sessions/:session_id')

    // get the session with that id (accessed at GET http://localhost:8080/api/sessinos/:session_id)
    .get(function(req, res) {
      Session.findById(req.params.session_id, function(err, session) {
        if (err)
          res.send(err);
        res.json(session);
      });
    })

    // update the bear with this id (accessed at PUT http://localhost:8080/api/sessions/:session_id)
    .put(function(req, res) {

      let session = req.body.session;

      if (session._id) {
        // use our bear model to find the session we want
        Session.findByIdAndUpdate(session._id, session, {new:true})
               .populate('group', 'groupname')
               .exec(function(err, return_session) {
                 // Error
                 if (err) {
                   console.error(err);
                   res.status(500).send(err);

                 // No error
                 } else {
                   let params = {
                     success: true,
                     operation: 'edit',
                     session: return_session
                   };
                   res.status(200).json(params);
                 }
               });
      } else {

        Session.findOneAndUpdate({_id:mongoose.Types.ObjectId()}, session, {new: true, upsert: true})
               .populate('group', 'groupname')
               .exec(function(err, new_session) {
                 if (err) {
                   console.error(err);
                   res.status(500).send(err);
                 } else {
                   console.log(new_session);
                   let params = {
                     success: true,
                     operation: 'add',
                     session: new_session
                   };
                   res.status(200).json(params);
                 }
               });

      }
    })

    // delete the session with this id (accessed at DELETE http://localhost:8080/api/sessions/:session_id)
    .delete(function(req, res) {

        console.log('delete', req.params.session_id);

        Session.remove({
            _id: req.params.session_id
        }, function(err, session) {
            if (err) {
              console.error(err)
              res.status(500).send(err);
            } else {
                res.json({
                  success: true,
                  operation: 'delete',
                  _id: req.params.session_id
                });
            }
        });
    });

  // on routes that end in /results
  // ----------------------------------------------------
  router.route('/results/:session_id')

      // get the session with that id (accessed at GET http://localhost:8080/api/bears/:bear_id)
      .get(function(req, res) {
          Session.find({session_id:req.params.session_id}, function(err, sessions) {
              if (err)
                  res.send(err);
              // console.log(sessions);
              res.json(sessions);
          });
      });

module.exports = router;

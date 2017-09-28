var express = require('express');
var router = express.Router();

// const Group = require('../models/group');
const Session = require('../models/session');

// on routes that end in /sessions
// ----------------------------------------------------
router.route('/sessions')

    // create a session (accessed at POST http://localhost:3000/api/sessions)
    .post(function(req, res) {

        var session = new Session(JSON.parse(req.body.session));     // create a new instance of the Session model

        // save the bear and check for errors
        session.save(function(err) {
            if (err)
                res.send(err);

            res.json({ message: 'Session created!' });
        });

    })

    // get all the sessions (accessed at GET http://localhost:3000/api/sessions)
    .get(function(req, res) {

      var find_search = { group: { $in: req.decoded._doc.groups}};
      if (req.decoded._doc.role == 'site_admin') {
        find_search = {}
      }

      Session.
        find(find_search).
        populate('group', 'groupname').
        sort({end: -1}).
        exec(function(err, sessions) {
          if (err)
              res.send(err);
          console.log(sessions);
          res.json(sessions);
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

      // console.log(session);

      // Make sure group is only an _id
      session.group = session.group._id;

      // use our bear model to find the session we want
      Session.findById(session._id, function(err, saved_session) {

        // Error
        if (err) {
          res.send(err);
        }

        if (saved_session) {
          // Update the document
          saved_session.set(session);

          // save the bear
          saved_session.save(function(err) {
            if (err) {
              res.send(err);
            }

          Session.
            findById(session._id).
            populate('group', 'groupname').
            exec(function(err, return_session) {
              // console.log(return_session);
              let params = {
                success: true,
                operation: 'edit',
                session: return_session
              };
              res.json(params);
            });
          });
        } else {
          // create a new session
          var new_session = new Session(session);

          // save the sample user
          new_session.save(function(err, return_session, numAffected) {
            if (err) {
              throw err;
            }

            console.log('Session saved successfully');

            Session.
              findById({_id: return_session._id}).
              populate('group', 'groupname').
              exec(function(err, new_session) {
                // console.log(new_session);
                let params = {
                  success: true,
                  operation: 'add',
                  user: new_session
                }
                res.json(params);
              });
          });
        }
      });
    })

    // delete the session with this id (accessed at DELETE http://localhost:8080/api/sessions/:session_id)
    .delete(function(req, res) {

        // console.log(req.params.session_id);

        Session.remove({
            _id: req.params.session_id
        }, function(err, session) {
            if (err)
                res.send(err);

            res.json({ message: 'Successfully deleted' });
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

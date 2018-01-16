var express = require('express');
var router = express.Router();
var mongoose = require('../models/mongoose');

// Models connect to specific database instances
const Group = mongoose.auth_conn.model('Group', require('../models/group').GroupSchema);
const Session =  mongoose.ctrl_conn.model('Session', require('../models/session').SessionSchema);

// on routes that end in /sessions
// ----------------------------------------------------
router.route('/sessions')

  // get all the sessions (accessed at GET api/sessions)
  .get(function(req, res) {

    console.log('In /sessions');
    console.log(req.decoded);

    // Sessions for the user's groups
    let query_params = { group: { $in: req.decoded._doc.groups}};
    // Site admins get all sessions
    if (req.decoded._doc.role === 'site_admin') {
      query_params = {}
    }

    Session.
      find(query_params).
      // populate('group', 'groupname').
      sort({last_process: -1}).
      exec(function(err, sessions) {
        if (err) {
          console.error(err);
          res.status(500).json({
            success: false,
            message: err
          });
        } else {
          const session_count = sessions.length;
          let return_sessions = [],
              counter = 0;
          sessions.forEach(function(session) {
            session._doc.group = {
              _id: session._doc.group,
            };
            if (session._doc.group._id) {
              console.log(counter, session._doc.group._id);
              Group.findOne({_id:session._doc.group._id}, {groupname:1})
              .exec(function(error, group) {
                counter += 1;
                console.log(group);
                session._doc.group.groupname = group.groupname;
                return_sessions.push(session);
                if (counter === session_count) {
                  console.log(return_sessions);
                  console.log('Returning', return_sessions.length, 'sessions');
                  res.status(200).json({
                    success: true,
                    sessions: return_sessions
                  });
                }
              });
            } else {
              counter += 1;
              return_sessions.push(session);
              if (counter === session_count) {
                console.log(return_sessions);
                console.log('Returning', return_sessions.length, 'sessions');
                res.status(200).json({
                  success: true,
                  sessions: return_sessions
                });
              }
            }
          });
        }
      });
  });

// on routes that end in /sessions/:session_id
// ----------------------------------------------------
router.route('/sessions/:session_id')

    // get the session with this id (accessed at GET api/sessions/:session_id)
    .get(function(req, res) {
      Session.findById(req.params.session_id, function(err, session) {
        if (err) {
          console.error(err);
          res.status(500).json({
            success: false,
            message: err
          });
        } else {
          user.password = undefined;
          console.log('Returning session', session);
          res.status(200).json({
            success: true,
            session: session
          });
        }
      });
    })

    // update the session with this id (accessed at PUT api/sessions/:session_id)
    .put(function(req, res) {

      let session = req.body.session;

      // Updating
      if (session._id) {
        // use our bear model to find the session we want
        Session.findByIdAndUpdate(session._id, session, {new:true})
               .populate('group', 'groupname')
               .exec(function(err, return_session) {
                 if (err) {
                   console.error(err);
                   res.status(500).send(err);
                 } else {
                   let params = {
                     success: true,
                     operation: 'edit',
                     session: return_session
                   };
                   res.status(200).json(params);
                 }
               });

      // Creating
      } else {
        // Set the creator
        session.creator = req.decoded._doc._id;

        Session.findOneAndUpdate(
          {_id:mongoose.Types.ObjectId()},
          session,
          {new:true, upsert:true}
        )
        .populate('group', 'groupname')
        .exec(function(err, new_session) {
          if (err) {
            console.error(err);
            res.status(500).send(err);
          } else {
            console.log('Session created successfully created', new_session);
            res.status(200).json({
              success: true,
              operation: 'add',
              session: new_session
            });
          }
        });
      }
    })

    // delete the session with this id (accessed at DELETE http://localhost:8080/api/sessions/:session_id)
    .delete(function(req, res) {
        Session.remove({_id:req.params.session_id}, function(err) {
            if (err) {
              console.error(err)
              res.status(500).json({
                success: false,
                message: err
              });
            } else {
              console.log('Session deleted successfully', req.params.session_id);
              res.status(200).json({
                success: true,
                operation: 'delete',
                _id: req.params.session_id
              });
            }
        });
    });

module.exports = router;

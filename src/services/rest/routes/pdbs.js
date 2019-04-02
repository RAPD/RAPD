var express = require('express');
var router = express.Router();
var mongoose = require('../models/mongoose');

const Activity = mongoose.ctrl_conn.model('Activity', require('../models/activity').ActivitySchema);
const Group = mongoose.auth_conn.model('Group', require('../models/group').GroupSchema);
const Pdb  = mongoose.ctrl_conn.model('Pdb', require('../models/pdb').PdbSchema);
const Session  = mongoose.ctrl_conn.model('Session', require('../models/session').SessionSchema);

// on routes that end in /pdbs
// ----------------------------------------------------
router.route('/pdbs/by_session/:session_id')
      .get(function(req, res) {
        console.log(req.params);

        Session.findOne({_id:req.params.session_id}, function(err, result) {
          console.log(result);
        })

        Pdb.find({session:req.params.session_id}, function(err, result) {
          // console.log(result);
          if (err) {
            console.error(err);
            res.status(500).json({
              success: false,
              message: err
            });
          } else {
            console.log('Returning result:', result);
            res.status(200).json({
              success: true,
              result: result
            });
          }
        })

        // console.log(res);
        // Result.findOne({_id:req.params.result_id}, function(err, result) {
        //   if (err) {
        //     console.error(err);
        //     res.status(500).json({
        //       success: false,
        //       message: err
        //     });
        //   } else {
        //     console.log('Returning result:', result);
        //     res.status(200).json({
        //       success: true,
        //       result: result
        //     });
        //   }
        //  });
      });

// // resultsbysession
// // ----------------------------------------------------
// router.route('/resultsbysession/:session_id')

//     // get the session with that id (accessed at GET http://localhost:8080/api/bears/:bear_id)
//     .get(function(req, res) {
//         Result.find({session_id:req.params.session_id}, function(err, results) {
//           if (err) {
//             console.error(err);
//             res.status(500).json({
//               success: false,
//               message: err
//             });
//           } else {
//             // console.log(results.length, 'results found for session', req.params.session_id);
//             res.status(200).json({
//               success: true,
//               results: results
//             });
//           }
//         });
//     });

module.exports = router;

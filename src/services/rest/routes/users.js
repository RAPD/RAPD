var express = require('express');
const nodemailer =    require('nodemailer');
const smtpTransport = require('nodemailer-smtp-transport');
var router = express.Router();

const config = require('../config');
const User =    require('../models/user');

// Email Configuration
var smtp_transport = nodemailer.createTransport(smtpTransport({
  host: 'mailhost.anl.gov'
}));

// Create connection to LDAP
// if (config.authenticate_mode === 'ldap') {
//   const ldap =  require('ldapjs');
//   var ldap_client = ldap.createClient({
//     url: 'ldap://'+config.ldap_server
//   });
// }

// routes that end with users
// ----------------------------------------------------
// route to return all users (GET api/users)
router.route('/users')
  .get(function(req, res) {

    // MONGO
    if (config.authenticate_mode === 'mongo') {
      User.
        find({}).
        populate('groups', 'groupname').
        exec(function(err, users) {
          // Do not return the password
          for (let user of users) {
            user.password = undefined;
          }
          res.json(users);
        });

    // LDAP - no users
    } else if (config.authenticate_mode === 'ldap') {
      // SERCAT uses LDAP per group
      res.json([]);
    }
  });

router.route('/users/:user_id')
  // edit or create the user with _id (PUT api/users/:user_id)
  .put(function(req,res) {

    // Passed as JSON
    let user = req.body.user;

    // Updating
    if (user._id) {
      User.findByIdAndUpdate(user._id, user, {new:true})
          .populate('groups', 'groupname')
          .exec(function(err, return_user) {
            if (err) {
              console.error(err);
              res.status(500).json({
                success: false,
                operation: 'edit',
                message: err
              });
            } else {
              // Blank out the password
              return_user.password = undefined;
              console.log('User edited successfully', return_user);
              res.status(200).json({
                success: true,
                operation: 'edit',
                user: return_user
              });
            }
          });

    // Creating
    } else {
      // Create the user
      let new_user = new User({
        creator:req.decoded._doc._id,
        email: user.email,
        groups: user.groups,
        role: user.role,
        status: user.status,
        username: user.username
      });

      // Save and return the user
      new_user.save(function(err, return_user) {
        if (err) {
          console.error(err);
          res.status(500).json({
            success: false,
            operation: 'add',
            message: err
          });
        } else {
          console.log('User saved successfully', return_user);
          res.status(200).json({
            success: true,
            operation: 'add',
            user: return_user
          });
        }
      });
    }
  })

  // Delete the user with _id (DELETE api/users/:user_id)
  .delete(function(req, res) {
    User.remove({_id:req.params.user_id}, function(err) {
      if (err) {
        console.error(err);
        res.send(err);
      } else {
        console.log('User deleted successfully', req.params.user_id)
        res.json({
          operation: 'delete',
          success: true,
          _id: req.params.user_id,
          message: 'Successfully deleted'});
      }
    });
  });

// Route to handle changing password (POST api/changepass)
router.post('/changepass', function(req, res) {

  User.
  findOne({email: req.body.email})
  .exec(function(err, user) {
    if (err) {
      console.error(err);
      res.status(500).json({
        success: false,
        message: err
      });
    } else {
      if (user) {
        let new_pass_raw = req.body.password;
        user.password =  new_pass_raw;
        // Expire in 1 year
        user.pass_expire = Date.now() + 31622240;
        user.pass_force_change = false;
        user.save(function(err, saved_user) {
          if (err) {
            console.error(err);
            res.status(500).json({
              success: false,
              message: err
            });
          } else {
            // Set up the email options
            let mailOptions = {
              from: config.admin_email,
              to: user.email,
              cc: config.admin_email,
              subject: 'RAPD password change',
              text: 'Your RAPD password has been updated.\nIf this is an unauthorized change, please contactthe RAPD administrator at '+config.admin_email};
            // Send the email
            smtp_transport.sendMail(mailOptions);
            console.log('Changed password for', req.body.email);
            // Reply to client
            res.json({success: true});
          }
        });
      } else {
        console.error('No user found for email', req.body.email);
        res.status(404).json({
          success: false,
          message: 'No user found for email '+req.body.email
        });
      }
    }
  });
});

module.exports = router;

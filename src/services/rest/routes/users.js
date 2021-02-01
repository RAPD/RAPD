var express = require('express');
const nodemailer =    require('nodemailer');
const smtpTransport = require('nodemailer-smtp-transport');
var router = express.Router();
var mongoose = require('../models/mongoose');
var bcrypt = require('bcryptjs');
const moment = require("moment");

const config = require('../config');
const User = mongoose.auth_conn.model('User', require('../models/user').UserSchema);

// const User = require('../models/user').User;

// Email Configuration
var smtp_transport = nodemailer.createTransport(smtpTransport({
  host: config.mailhost
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

    //req.decoded._id is the requesting user's _id
    // console.log(req.decoded);

    // MONGO
    if (config.authenticate_mode === 'mongo') {
      let query_params = {_id:mongoose.Types.ObjectId(req.decoded._id)};
      if (req.decoded.role === 'site_admin') {
        query_params = {};
      } else if (req.decoded.role === 'group_admin') {
        query_params = {groups:{'$elemMatch':{'$in':req.decoded.groups.map(function(e){return e._id;})}}};
      }

        User.
          find(query_params).
          populate('groups', 'groupname').
          exec(function(err, users) {
            if (err) {
              console.error(err);
              res.status(500).json({
                success: false,
                message: err
              });
            } else {
              // Do not return the password
              for (let user of users) {
                user.password = undefined;
              }
              console.log('Returning', users.length, 'users');
              res.status(200).json({
                success: true,
                users: users
              });
            }
          });

    // LDAP - no users
    } else if (config.authenticate_mode === 'ldap') {
      // SERCAT uses LDAP per group
      res.json([]);
    }
  });

router.route('/users/:user_id')

  // get the user with that id (accessed at GET api/users/:user_id)
  .get(function(req, res) {
    User.findById(req.params.user_id, function(err, user) {
      if (err) {
        console.error(err);
        res.status(500).json({
          success: false,
          message: err
        });
      } else {
        user.password = undefined;
        console.log('Returning user', user);
        res.status(200).json({
          success: true,
          user: user
        });
      }
    });
  })

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

      // Set the creator
      user.creator = req.decoded._id;

      // Save and return the user
      User.findOneAndUpdate(
        {_id:mongoose.Types.ObjectId()},
        user,
        {new: true, upsert: true}
      )
      .populate('groups', 'groupname')
      .exec(function(err, return_user) {
        if (err) {
          console.error(err);
          res.status(500).json({
            success: false,
            operation: 'add',
            message: err.message
          });
        } else {
          // Set up the email options
          let mailOptions = {
            from: config.admin_email,
            to: user.email,
            cc: config.admin_email,
            subject: 'RAPD user account created',
            text: `A RAPD user account has been created for you using the email
address ${ user.email }. Please navigate to ${ config.rapd_url } to
start using RAPD. \n
If this in error, please contact ${ config.admin_email }.`
          };
          // Send the email
          smtp_transport.sendMail(mailOptions);
          console.log('User created successfully', return_user);
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
        res.status(500).json({
          success: false,
          message: err
        });
      } else {
        console.log('User deleted successfully', req.params.user_id);
        res.status(200).json({
          operation: 'delete',
          success: true,
          _id: req.params.user_id
        });
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
        const password = req.body.password,
          salt = bcrypt.genSaltSync(10),
          new_hash = bcrypt.hashSync(password, salt)
        user.pass =  new_hash;
        // Expire in 1 year
        user.pass_expire = moment().utc().add(1,"y").toDate()
        // user.pass_expire = Date.now() + 31622240;
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
            console.log(`Changed password for ${req.body.email}`);
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

var express = require('express');
const ldap =          require('ldapjs');
var router = express.Router();

const config = require('../config');
const User =    require('../models/user');

// Create connection to LDAP
if (config.authenticate_mode === 'ldap') {
  var ldap_client = ldap.createClient({
    url: 'ldap://'+config.ldap_server
  });
}

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
    // LDAP
    } else if (config.authenticate_mode === 'ldap') {
      // SERCAT uses LDAP per group
      var users = [];
      ldap_client.search(config.ldap_dn, {  //}"dc=ser,dc=aps,dc=anl,dc=gov", {
        scope:'sub',
        filter:'objectclass=*'
      }, function(err, ldap_result) {
        if (err) {
          console.error(err);
          res.json({success:false,
                    message:err});
        } else {
          ldap_result.on('searchEntry', function(entry) {
            console.log('entry: ' + JSON.stringify(entry.object));
            users.push(entry.object);
          });
          ldap_result.on('searchReference', function(referral) {
            console.log('referral: ' + referral.uris.join());
          });
          ldap_result.on('error', function(err) {
            console.error('error: ' + err.message);
          });
          ldap_result.on('end', function(result) {
            console.log('status: ' + result.status);
            res.json(users);
          });
        }
      });
    }
  });

router.route('/users/:user_id')
  // edit or create the user with _id (PUT api/users/:user_id)
  .put(function(req,res) {
    // Passed as JSON
    let user = req.body.user;
    // Make sure groups are only _ids
    for (let g of user.groups) {
      delete g.groupname
    }
    // Updating
    if (user._id) {
      User.findById(user._id, function(err, saved_user) {

        if (err) {
          console.log(err);
          res.send(err);

        } else {
          // Update the entry
          saved_user.username = user.username;
          saved_user.email = user.email;
          saved_user.status = user.status;
          saved_user.groups = user.groups;
          saved_user.role = user.role;

          // Save the user with changes
          saved_user.save(function(err, return_user) {
            if (err) {
              console.error(err);
              res.send(err);
            } else {
              // User.
              //   findById({_id: user._id}).
              //   populate('groups', 'groupname').
              //   exec(function(err, return_user) {
              //     console.log(return_user);
              // Blank out the password
              return_user.password = undefined;
              res.json({
                success: true,
                operation: 'edit',
                user: return_user
              });
            }
          });
        }
      });

    // Creating
    } else {
      let new_user = new User({
        creator:req.decoded._doc._id,
        email: user.email,
        groups: user.groups,
        role: user.role,
        status: user.status,
        username: user.username
      });

      new_user.save(function(err, return_user) {
        if (err) {
          console.error(err);
          res.send(err);
        } else {
          console.log('User saved successfully', return_user);
          res.json({
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

  // console.log('changepass');
  // console.log(req.body);

  User.
  findOne({email: req.body.email}).
  exec(function(err, user) {
    if (err) {
      console.error(err);
      res.send(err);
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
            res.send(err);
          } else {
            console.log('Changed password for', req.body.email);
            // Set up the email options
            let mailOptions = {
              from: 'fmurphy@anl.gov',
              to: user.email,
              cc: 'fmurphy@anl.gov',
              subject: 'RAPD password change',
              text: 'Your RAPD password has been updated.\nIf this is an unauthorized change, please contactthe RAPD administrator at XXX'};
            // Send the email
            smtp_transport.sendMail(mailOptions);
            // Reply to client
            res.json({success: true});
          }
        });
      } else {
        console.error('No user found for email', req.body.email);
        res.send('No user found for email', req.body.email);
      }
    }
  });
});

module.exports = router;

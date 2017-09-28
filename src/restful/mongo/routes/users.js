var express = require('express');
var router = express.Router();

const User =    require('../models/user');

// routes that end with users
// ----------------------------------------------------
// route to return all users (GET http://localhost:8080/api/users)
router.route('/users')
  .get(function(req, res) {
    User.
      find({}).
      populate('groups', 'groupname').
      exec(function(err, users) {
        console.log(users);
        for (let user of users) {
          user.password = undefined;
        }
        res.json(users);
      });
  });

router.route('/users/:user_id')

  // edit the user with _id (accessed ad PUT http://localhost:8080/api/users/:user_id)
  .put(function(req,res) {

    console.log('PUT users');
    // console.log(req.body.user);

    let user = req.body.user;

    // Make sure groups are only _ids
    for (let g of user.groups) {
      // console.log(g);
      delete g.groupname
    }

    console.log(user);

    // Updating
    if (user._id) {

      User.findById(user._id, function(err, saved_user) {
        if (err) {
          console.log(err);
          res.send(err);
        }

        console.log('saved_user', saved_user);

        //
        // Update the entry
        saved_user.username = user.username;
        saved_user.email = user.email;
        saved_user.status = user.status;
        saved_user.groups = user.groups;
        saved_user.role = user.role;
        //
        saved_user.save(function(err) {
          if (err) {
            res.send(err);
          }
          User.
            findById({_id: user._id}).
            populate('groups', 'groupname').
            exec(function(err, return_user) {
              console.log(return_user);
              return_user.password = undefined;
              let params = {
                success: true,
                operation: 'edit',
                user: return_user
              }
              res.json(params);
            });
        });
      });
    } else {

      console.log('New user');
      // create a sample user
      var new_user = new User({
        username: user.username,
        // password: 'groovylovebugbed',
        role: 'site_admin',
        groups: user.groups,
        email: user.email,
        status: user.status
      });

      // save the sample user
      new_user.save(function(err, return_user, numAffected) {
        if (err) throw err;

        console.log('User saved successfully');
        res.json({
          success: true,
          operation: 'add',
          user: return_user
        });
      });
    }
  })


  // delete the user with _id (accessed at DELETE http://localhost:8080/api/users/:user_id)
  .delete(function(req, res) {

      console.log(req.params.user_id);

      User.remove({
          _id: req.params.user_id
      }, function(err, user) {
          if (err) {
            res.send(err);
          }

          res.json({
            operation: 'delete',
            success: true,
            _id: req.params.user_id,
            message: 'Successfully deleted'});
      });
  });

  router.route('/user')

    .post(function(req, res) {
      console.log('POST user');
      console.log(req.body);
      let user = req.body;

      // Make sure groups are only _ids
      for (let g of user.groups) {
        console.log(g);
        delete g.groupname
      }

      console.log(user);

      // Updating
      if (user._id) {
        User.findById(user._id, function(err, saved_user) {
          if (err) {
            console.log(err);
            res.send(err);
          }

          console.log(saved_user);

          //
          // Update the entry
          saved_user.username = user.username;
          saved_user.email = user.email;
          saved_user.status = user.status;
          saved_user.groups = user.groups;
          saved_user.role = user.role;
          //
          saved_user.save(function(err) {
            if (err) {
              res.send(err);
            }
            User.
              findById({_id: user._id}).
              populate('groups', 'groupname').
              exec(function(err, return_user) {
                console.log(return_user);
                return_user.password = undefined;
                let params = {
                  success: true,
                  user: return_user
                }
                res.json(params);
              });
          });
        });
      } else {

        console.log('New user');

      }
    });

module.exports = router;

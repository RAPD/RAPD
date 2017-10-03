var express = require('express');
var router = express.Router();

const config = require('../config');

// MongoDB model
var Group = require('../models/group');

// Create connection to LDAP
if (config.authenticate_mode === 'ldap') {
  const ldap =  require('ldapjs');
  var ldap_client = ldap.createClient({
    url: 'ldap://'+config.ldap_server
  });
}

// Routes
router.route('/groups')
  // route to return all groups (GET api/groups)
  .get(function(req, res) {
      Group.find({}, function(err, groups) {
        res.json(groups);
      });
  });

router.route('/groups/:group_id')
  // edit or add the group with _id (PUT api/groups/:group_id)
  .put(function(req, res) {
    // Passed as JSON
    let group = req.body.group;
    // Updating
    if (group._id) {
      Group.findById(group._id, function(err, saved_group) {

        if (err) {
          console.error(err);
          res.send(err);
        }
        // Update the entry
        saved_group.groupname = group.groupname;
        saved_group.institution = group.institution;
        saved_group.status = group.status;

        // Save the group with changes
        saved_group.save(function(err, return_group) {
          if (err) {
            console.error(err);
            res.send(err);
          } else {
            console.log('Group updated successfully', return_group);
            res.json({
              success:true,
              operation:'edit',
              group:return_group
            });
          }
        });
      });

    // Creating
    } else {
      let new_group = new Group({
        groupname:group.groupname,
        institution:group.institution,
        uid:group.uid,
        gid:group.gid,
        status:group.status,
        creator:req.decoded._doc._id
      });

      new_group.save(function(err, return_group) {
        if (err) {
          console.error(err);
          res.send(err);
        } else {
          console.log('Group saved successfully', return_group);
          res.json({
            success:true,
            operation:'add',
            group:return_group
          });
        }
      });
    }
  })

  // Delete the group with _id (DELETE api/groups/:group_id)
  .delete(function(req, res) {
    Group.remove({_id: req.params.group_id}, function(err) {
        if (err) {
          console.error(err);
          res.send(err);
        } else {
          console.log('Group deleted successfully', req.params.group_id)
          res.json({
            operation:'delete',
            success:true,
            _id:req.params.group_id,
            message:'Successfully deleted'});
        }
    });
  });

module.exports = router;

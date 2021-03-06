var express = require('express');
var router = express.Router();
var mongoose = require('../models/mongoose');

const config = require('../config');

// MongoDB model
// var Group = require('../models/group').Group;
const Group = mongoose.auth_conn.model('Group', require('../models/group').GroupSchema);

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
        console.log('Return', groups.length, 'groups');
        res.json({
          success: true,
          groups: groups
        });
      });
  });

router.route('/groups/:group_id')
  // edit or add the group with _id (PUT api/groups/:group_id)
  .put(function(req, res) {

    // Passed as JSON
    let group = req.body.group;

    // Updating
    if (group._id) {

      Group.findByIdAndUpdate(group._id, group, {new:true}, function(err, return_group) {

        if (err) {
          console.error(err);
          res.status(500).send(err);
        } else {
          console.log('Group updated successfully', return_group);
          res.status(200).json({
            success:true,
            operation:'edit',
            group:return_group
          });
        }
      });

    // Creating
    } else {
      let new_group = new Group({
        groupname:group.groupname,
        institution:group.institution,
        uid:group.uid,
        gid:group.gid,
        status:group.status,
        creator:req.decoded._id
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

  router.route('/groups/populate')
   // populate all groups from LDAP server (GET api/groups/populate)
   .get(function(req, res) {
     ldap_client.search(config.ldap_dn,{
         scope:'sub',
         filter:'objectclass=*',
         // sizeLimit:10
       },  function(err, res) {
         res.on('searchEntry', function(entry) {
           console.log('entry: ' + JSON.stringify(entry.object));
           Group.find({uid:entry.object.uid}, function(err, groups) {
             if (! groups[0]) {
               console.log('  No entry for', entry.object.uid);
               let new_group = Group({
                 email:entry.object.mail,
                 gidNumber:entry.object.gidNumber,
                 groupname:entry.object.cn,
                 role:'user',
                 status:'active',
                 uid:entry.object.uid,
                 uidNumber:entry.object.uidNumber
               });
               new_group.save(function(err, return_group) {
                 if (err) {
                   console.error(err);
                 } else {
                   console.log('  Made group:', return_group);
                 }
               });
             } else {
               console.log('  Have entry for', groups[0].uid, groups[0]._id)
             }
           });
         });
         res.on('searchReference', function(referral) {
           console.log('referral: ' + referral.uris.join());
         });
         res.on('error', function(err) {
           console.error('error: ' + err.message);
         });
         res.on('end', function(result) {
           console.log('status: ' + result.status);
         });
       });
       res.json({success:'true'});
   });




module.exports = router;

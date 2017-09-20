var express = require('express');
var router = express.Router();

// MongoDB Models
var Project = require('../models/project');

// Routes that end with projects
// ----------------------------------------------------
// route to return all users (GET http://localhost:8080/api/users)
router.route('/projects')
  .get(function(req, res) {
    console.log('GET /projects');
    console.log(req.decoded._doc);

    let find_search = { group: { $in: req.decoded._doc.groups}};
    if (req.decoded._doc.role == 'site_admin') {
      find_search = {};
    }

    Project.
      find(find_search).
      populate('group', 'groupname').
      exec(function(err, projects) {
        console.log(projects);
        res.json(projects);
      });
  });

module.exports = router;

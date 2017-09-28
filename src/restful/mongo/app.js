const debug =         require('debug')('backend:server');
const http =          require('http');
const express =       require('express');
const session =       require('express-session');
const RedisStore =    require('connect-redis')(session);
const path =          require('path');
const favicon =       require('serve-favicon');
const morgan =        require('morgan');
const cookieParser =  require('cookie-parser');
const randomstring =  require("randomstring");
const nodemailer =    require('nodemailer');
const smtpTransport = require('nodemailer-smtp-transport');
const bodyParser =    require('body-parser');
const Wss =           require('./ws_server');
const jwt =           require('jsonwebtoken');

// Configuration
const config = require('./config'); // get our config file

// Routing
const routes =          require('./routes/index');
const projects_routes = require('./routes/projects');
const sessions_routes = require('./routes/sessions');
const users_routes =    require('./routes/users');


// Redis
const redis =      require('redis');
var redis_client = redis.createClient(config.redis_host);

// MongoDB Models
const Session = require('./models/session');
const User =    require('./models/user');
const Group =   require('./models/group');
const Image =   require('./models/image');
const Run =     require('./models/run');
// MongoDB connection
const q =      require('q');
var mongoose = require('mongoose');
// Fix the promise issue in Mongoose
mongoose.Promise = require('q').Promise;
// Connect to MongoDB
mongoose.connect(config.database, {
  useMongoClient: true,
}, function(error) {
  console.error(error);
});

// Email Configuration
var smtp_transport = nodemailer.createTransport(smtpTransport({
  host: 'mailhost.anl.gov'
}));

// Create the express app instance
let app = express();
let server = http.createServer(app);

// Add session handling
let app_session = session({
  store: new RedisStore({}),
  secret: 'keyboard cat',
  resave: false,
  saveUninitialized: true
});
app.use(app_session);

// Create the socket.io server
var wss = new Wss({morgan:morgan,
                   server:server});


app.set('superSecret', config.secret);

// configure app to use bodyParser()
// this will let us get the data from a POST
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// use morgan to log requests to the console
app.use(morgan('dev'));

// ROUTES FOR OUR API
// =============================================================================
var apiRoutes = express.Router();              // get an instance of the express Router

// middleware to use for all requests
apiRoutes.use(function(req, res, next) {

    // Testing sessions
    // req.session.working = 'yes!';
    // console.log('working =', req.session.working);
    // console.log(req.session);

    // do logging
    console.log('Something is happening.');
    // res.header("Access-Control-Allow-Origin", "*");
    // res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");

    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Credentials", "true");
    res.setHeader("Access-Control-Allow-Methods", "GET,HEAD,OPTIONS,POST,PUT,DELETE");
    res.setHeader("Access-Control-Allow-Headers", "Access-Control-Allow-Headers, Authorization, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers");
    // next(); // make sure we go to the next routes and don't stop here
    // intercepts OPTIONS method from http://johnzhang.io/options-request-in-express
    if ('OPTIONS' === req.method) {
      //respond with 200
      res.sendStatus(200);
    }
    else {
    //move on
      next();
    }
});

// route to authenticate a user (POST http://localhost:8080/api/authenticate)
apiRoutes.post('/authenticate', function(req, res) {

  console.log('authenticate');
  console.log(req.body);

  User.getAuthenticated(req.body.email, req.body.password, function(err, user, reason) {

    // console.log(err);
    console.log('2>>>>>', user);

    // login was successful if we have a user
    if (user) {
      // create a token
      var token = jwt.sign(user, app.get('superSecret'), {
        expiresIn: 86400 // expires in 24 hours
      });

      // return the information including token as JSON
      console.log('returning token');
      res.json({
        success: true,
        message: 'Enjoy your token!',
        token: token,
        pass_force_change: user.pass_force_change
      });
    // otherwise we can determine why we failed
    } else {
      var reasons = User.failedLogin;
      switch (reason) {
          case reasons.NOT_FOUND:
              res.json({ success: false, message: 'Authentication failed. No such user.' });
              break;
          case reasons.PASSWORD_INCORRECT:
              res.json({ success: false, message: 'Authentication failed. Wrong password.' });
              // note: these cases are usually treated the same - don't tell
              // the user *why* the login failed, only that it did
              break;
          case reasons.MAX_ATTEMPTS:
              res.json({ success: false, message: 'Authentication failed. Too many failed attempts' });
              // send email or otherwise notify user that account is
              // temporarily locked
              break;
      }
    }
  });
});

// route to authenticate a user (POST http://localhost:8080/api/requestpass)
apiRoutes.post('/requestpass', function(req, res) {

  console.log('requestpass');
  console.log(req.body);

  User.
  findOne({email: req.body.email}).
  exec(function(err, user) {
    if (err)
        res.send(err);

    if (user) {
      let new_pass_raw = randomstring.generate(12);
      console.log('new_pass_raw', new_pass_raw);
      user.password =  new_pass_raw;
      // Expire in 60 minutes
      user.pass_expire = Date.now() + 3600;
      user.pass_force_change = true;
      user.save(function(err, saved_user) {
        if (err) {
          res.send(err);
        }
        // Set up the email options
        let mailOptions = {
          from: 'fmurphy@anl.gov',
          to: user.email,
          cc: 'fmurphy@anl.gov',
          subject: 'RAPD password recovery',
          text: 'Your new temporary password is '+new_pass_raw+'\nIt is authorized for 60 minutes.'};
        // Send the email
        smtp_transport.sendMail(mailOptions);

        res.json({success: true});
      });
    }
    // res.json(sessions);
  });
});

// Setup route
app.get('/setup', function(req, res) {

  // create a sample user
  var fm = new User({
    username: 'Frank Murphy',
    password: 'groovylovebugbed',
    role: 'site_admin',
    group: null,
    email: 'fmurphy@anl.gov',
    status: 'active'
  });

  // save the sample user
  fm.save(function(err) {
    if (err) throw err;

    console.log('User saved successfully');
  });

  // // create a sample group
  var necat = new Group({
    groupname: 'NECAT',
    institution: 'Cornell University',
    status: 'active',
    uid: 'necat',
    gidNumber: 1,
    uidNumber: 1
  });

  // save the sample user
  necat.save(function(err) {
    if (err) throw err;

    console.log('Group saved successfully');
  });

  res.json({ success: true });

});

// test route to make sure everything is working (accessed at GET http://localhost:8080/api)
// apiRoutes.use(jwtCheck);
apiRoutes.get('/', function(req, res) {
    res.json({ message: 'Welcome to the RAPD api!' });
});


// route middleware to verify a token
apiRoutes.use(function(req, res, next) {

  // console.log(req.body);
  // console.log(req.query);
  // console.log(req.headers);

  // check header or url parameters or post parameters for token
  var token = req.headers.authorization.replace('Bearer ', '');

  // decode token
  if (token) {

    // verifies secret and checks exp
    jwt.verify(token, app.get('superSecret'), function(err, decoded) {
      if (err) {
        return res.json({ success: false, message: 'Failed to authenticate token.' });
      } else {
        let now = Date.now()/1000;
        // console.log(decoded.iat, decoded.exp, (decoded.exp-now)/(60));
        // if everything is good, save to request for use in other routes

        if (decoded.iat <= now && decoded.exp >= now) {
          req.decoded = decoded;
          next();
        }

      }
    });

  } else {

    // if there is no token
    // return an error
    return res.status(403).send({
        success: false,
        message: 'No token provided.'
    });
  }
});



// Route to handle changing password (POST http://localhost:8080/api/changepass)
apiRoutes.post('/changepass', function(req, res) {

  console.log('changepass');
  console.log(req.body);

  User.
  findOne({email: req.body.email}).
  exec(function(err, user) {
    if (err)
        res.send(err);
    if (user) {
      let new_pass_raw = req.body.password;
      user.password =  new_pass_raw;
      // Expire in 1 year
      user.pass_expire = Date.now() + 31622240;
      user.pass_force_change = false;
      user.save(function(err, saved_user) {
        if (err) {
          res.send(err);
        }
        // Set up the email options
        let mailOptions = {
          from: 'fmurphy@anl.gov',
          to: user.email,
          cc: 'fmurphy@anl.gov',
          subject: 'RAPD password change',
          text: 'Your RAPD password has been updated.\nIf this is an unauthorized change, please contactthe RAPD administrator at XXX'};
        // Send the email
        smtp_transport.sendMail(mailOptions);

        res.json({success: true});
      });
    }
  });
});

// routes that end with users
// ----------------------------------------------------
// route to return all users (GET http://localhost:8080/api/users)
apiRoutes.route('/users')
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

apiRoutes.route('/users/:user_id')

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

  apiRoutes.route('/user')

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

// routes that end with groups
// ----------------------------------------------------
// route to return all groups (GET http://localhost:8080/api/groups)
apiRoutes.route('/groups')

  .get(function(req, res) {
    Group.find({}, function(err, groups) {
      console.log(groups);
      res.json(groups);
    });
  });

apiRoutes.route('/groups/:group_id')

  // edit or add the group with _id (accessed ad PUT http://localhost:8080/api/groups/:group_id)
  .put(function(req,res) {

    console.log('PUT groups');

    let group = req.body.group;

    console.log(group);

    // Updating
    if (group._id) {

      Group.findById(group._id, function(err, saved_group) {
        if (err) {
          console.log(err);
          res.send(err);
        }

        console.log('saved_group', saved_group);

        //
        // Update the entry
        saved_group.groupname = group.groupname;
        saved_group.institution = group.institution;
        saved_group.status = group.status;

        //
        saved_group.save(function(err, return_group, numAffected) {
          if (err) {
            res.send(err);
          }

          console.log('return_group', return_group);

          let params = {
                success: true,
                operation: 'edit',
                group: return_group
              }
          res.json(params);
        });
      });
    } else {

      console.log('New group');
      // create a sample user
      var new_group = new Group({
        groupname: group.groupname,
        institution: group.institution,
        uid: group.uid,
        gid: group.gid,
        status: group.status
      });

      // save the sample user
      new_group.save(function(err, return_group, numAffected) {
        if (err) throw err;

        console.log('Group saved successfully');
        res.json({
          success: true,
          operation: 'add',
          group: return_group
        });
      });
    }
  })

  // delete the group with _id (accessed at DELETE http://localhost:8080/api/groups/:group_id)
  .delete(function(req, res) {

      console.log('DELETE group:',req.params.group_id);

      Group.remove({
          _id: req.params.group_id
      }, function(err, group) {
          if (err) {
            res.send(err);
          }

          res.json({
            operation: 'delete',
            success: true,
            _id: req.params.group_id,
            message: 'Successfully deleted'});
      });
  });

// Routes that end with images
// -----------------------------------------------------------------------------
// route to return image data given an id (GET http://localhost:8080/api/images/:image_id)
apiRoutes.route('/images/:image_id')
  .get(function(req, res) {

    console.log('GET image:', req.params.image_id);

    Image.
      findOne({_id:req.params.image_id}).
      exec(function(err, image) {
        console.log(image);
        res.json(image);
      })

  });


  // Routes that end with runs
  // -----------------------------------------------------------------------------
  // route to return image data given an id (GET http://localhost:8080/api/runs/:run_id)
  apiRoutes.route('/runs/:run_id')
    .get(function(req, res) {

      console.log('GET run:', req.params.run_id);

      Run.
        findOne({_id:req.params.run_id}).
        exec(function(err, run) {
          console.log(run);
          res.json(run);
        })

    });


// // Routes that end with projects
// // ----------------------------------------------------
// // route to return all users (GET http://localhost:8080/api/users)
// apiRoutes.route('/projects')
//   .get(function(req, res) {
//     Project.
//       find({}).
//       populate('groups', 'groupname').
//       exec(function(err, users) {
//         console.log(users);
//         for (let user of users) {
//           user.password = undefined;
//         }
//         res.json(users);
//       });
//   });


// routes that end with jobs
// ----------------------------------------------------
// These are redis-based queries
// route to return all current requests (GET http://localhost:3000/api/requests)
apiRoutes.route('/requests')

  // add a request for a process to launch (accessed at PUT http://localhost:3000/api/requests)
  .put(function(req,res) {

    console.log('PUT request');

    let request = req.body.request;

    redis_client.lpush('RAPD_CLIENT_REQUESTS', JSON.stringify(request), function(err, queue_length) {
      if (err) {
        console.error(err);
        let params = {
          success: false,
          error: err
        };
        res.json(params);
      } else {
        console.log('queue length:', queue_length);
        let params = {
          success: true,
          queue_length: queue_length
        };
        res.json(params);
      }
    });
  }); // End .put(function(req,res) {



    // // Updating
    // if (group._id) {
    //
    //   Group.findById(group._id, function(err, saved_group) {
    //     if (err) {
    //       console.log(err);
    //       res.send(err);
    //     }
    //
    //     console.log('saved_group', saved_group);
    //
    //     //
    //     // Update the entry
    //     saved_group.groupname = group.groupname;
    //     saved_group.institution = group.institution;
    //     saved_group.status = group.status;
    //
    //     //
    //     saved_group.save(function(err, return_group, numAffected) {
    //       if (err) {
    //         res.send(err);
    //       }
    //
    //       console.log('return_group', return_group);
    //
    //       let params = {
    //             success: true,
    //             operation: 'edit',
    //             group: return_group
    //           }
    //       res.json(params);
    //     });
    //   });
    // } else {
    //
    //   console.log('New group');
    //   // create a sample user
    //   var new_group = new Group({
    //     groupname: group.groupname,
    //     institution: group.institution,
    //     uid: group.uid,
    //     gid: group.gid,
    //     status: group.status
    //   });
    //
    //   // save the sample user
    //   new_group.save(function(err, return_group, numAffected) {
    //     if (err) throw err;
    //
    //     console.log('Group saved successfully');
    //     res.json({
    //       success: true,
    //       operation: 'add',
    //       group: return_group
    //     });
    //   });
    // }
  // });


// REGISTER OUR ROUTES -------------------------------

// basic route
app.get('/', function(req, res) {
    res.send('Hello! The API is at http://localhost:' + app.get('port') + '/api');
});



// all of our routes will be prefixed with /api
app.use('/api', apiRoutes);

// Imported routes
app.use('/api', projects_routes);
app.use('/api', sessions_routes);

module.exports = app;


var port = normalizePort(process.env.PORT || '3000');
app.set('port', port);

server.listen(port);
server.on('error', onError);
server.on('listening', onListening);


/**
 * Normalize a port into a number, string, or false.
 */

function normalizePort(val) {
  var port = parseInt(val, 10);

  if (isNaN(port)) {
    // named pipe
    return val;
  }

  if (port >= 0) {
    // port number
    return port;
  }

  return false;
}

/**
 * Event listener for HTTP server "error" event.
 */

function onError(error) {
  if (error.syscall !== 'listen') {
    throw error;
  }

  var bind = typeof port === 'string'
    ? 'Pipe ' + port
    : 'Port ' + port;

  // handle specific listen errors with friendly messages
  switch (error.code) {
    case 'EACCES':
      console.error(bind + ' requires elevated privileges');
      process.exit(1);
      break;
    case 'EADDRINUSE':
      console.error(bind + ' is already in use');
      process.exit(1);
      break;
    default:
      throw error;
  }
}

/**
 * Event listener for HTTP server "listening" event.
 */

function onListening() {
  var addr = server.address();
  var bind = typeof addr === 'string'
    ? 'pipe ' + addr
    : 'port ' + addr.port;
  debug('Listening on ' + bind);
}

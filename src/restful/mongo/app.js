const bodyParser =    require('body-parser');
const cookieParser =  require('cookie-parser');
const debug =         require('debug')('backend:server');
const express =       require('express');
const session =       require('express-session');
const RedisStore =    require('connect-redis')(session);
const http =          require('http');
const favicon =       require('serve-favicon');
const jwt =           require('jsonwebtoken');
const ldap =          require('ldapjs');
const morgan =        require('morgan');
const nodemailer =    require('nodemailer');
const smtpTransport = require('nodemailer-smtp-transport');
const path =          require('path');
const randomstring =  require('randomstring');

// RAPD websocket server
const Wss =           require('./ws_server');

// Configuration
const config = require('./config'); // get our config file

// Routing
const groups_routes =   require('./routes/groups');
const images_routes =   require('./routes/images');
const jobs_routes =     require('./routes/jobs');
const projects_routes = require('./routes/projects');
const runs_routes =     require('./routes/runs');
const sessions_routes = require('./routes/sessions');
const users_routes =    require('./routes/users');

// Redis
const redis =      require('redis');
var redis_client = redis.createClient(config.redis_port, config.redis_host);

// MongoDB Models
// const Session = require('./models/session');
const User =    require('./models/user');
const Group =   require('./models/group');
const Run =     require('./models/run');
// MongoDB connection
var mongoose = require('mongoose');
// Fix the promise issue in Mongoose
mongoose.Promise = require('q').Promise;
// Connect to MongoDB
mongoose.connect(config.database, {
  useMongoClient: true,
}, function(error) {
  console.error(error);
});

// LDAP
if (config.authenticate_mode === 'ldap') {
  var ldap_client = ldap.createClient({
    url: 'ldap://'+config.ldap_server
  });
}

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
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Credentials", "true");
    res.setHeader("Access-Control-Allow-Methods", "GET,HEAD,OPTIONS,POST,PUT,DELETE");
    res.setHeader("Access-Control-Allow-Headers", "Access-Control-Allow-Headers, Authorization, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers");
    // intercepts OPTIONS method from http://johnzhang.io/options-request-in-express
    if ('OPTIONS' === req.method) {
      //respond with 200
      res.sendStatus(200);
    }
    else {
      next();
    }
});

// route to authenticate a user (POST http://localhost:8080/api/authenticate)
apiRoutes.post('/authenticate', function(req, res) {

  console.log('authenticate');
  console.log(req.body);

  if (config.authenticate_mode === 'mongo') {
    User.getAuthenticated(req.body.email, req.body.password, function(err, user, reason) {
      if (err) {
        console.error(err);
        res.json({ success: false, message: err });
      // login was successful if we have a user
      } else if (user) {
        // create a token
        var token = jwt.sign(user, app.get('superSecret'), {
          expiresIn: 86400 // expires in 24 hours
        });
        // Return the information including token as JSON
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
  } else if (config.authenticate_mode === 'ldap') {
    // Authenticate
    ldap_client.bind('uid='+req.body.uid+','+config.ldap_dn, req.body.password, function(err) {

      // REJECTION
      if (err) {
        console.error(err);
        var reason = err.name.toString();
        res.json({success:false,
                  message:'Authentication failed. ' + reason});

      // AUTHENTICATED
      } else {
        // Fetch user
        ldap_client.search('uid='+req.body.uid+',ou=People,dc=ser,dc=aps,dc=anl,dc=gov', {
          scope:'sub',
          filter:'objectclass=*',
          sizeLimit:1
          }, function(err, result) {

            // LDAP error
            if (err) {
              console.error(err);
              res.json({success:false,
                        message:err});
            }

            var user = undefined;

            result.on('searchEntry', function(entry) {

              // The user information
              let user = entry.object;

              // Look for a group that corresponds to this user
              Group.find({uid:user.uid, uidNumber:user.uidNumber}, function(err, groups) {
                console.log('looking for group....');
                console.log(err);
                console.log(groups);

                // Mark user as being from LDAP
                user.ldap = true;

                // A group has been returned
                if (groups) {
                  user.group = groups[0];

                  // create a token
                  var token = jwt.sign(user, app.get('superSecret'), {
                    expiresIn: 86400 // expires in 24 hours
                  });

                  // return the information including token as JSON
                  res.json({success:true,
                            message:'Enjoy your token!',
                            token:token,
                            pass_force_change:false});

                // No groups returned
                } else {
                  // Create a new group with the info from LDAP
                  let new_group = new Group({
                    groupname:user.cn,
                    institution:'',
                    uid:user.uid,
                    uidNumber:user.uidNumber,
                    gidNumber:user.gidNumber,
                    status:'active'
                  });
                  new_group.save(function(err, return_group) {
                    if (err) {
                      console.error(err);
                      res.send(err);
                    } else {
                      console.log('Group saved successfully', return_group);

                      user.group = return_group;

                      // create a token
                      var token = jwt.sign(user, app.get('superSecret'), {
                        expiresIn: 86400 // expires in 24 hours
                      });

                      // return the information including token as JSON
                      res.json({success:true,
                                message:'Enjoy your token!',
                                token:token,
                                pass_force_change:false});

                    }
                  });
                }
              });
            });
            result.on('searchReference', function(referral) {
              console.log('referral: ' + referral.uris.join());
            });
            result.on('error', function(err) {
              console.error('error: ' + err.message);
              res.json({success:false,
                        message:err});
            });
            result.on('end', function(end) {
              console.log(user);
              console.log('status: ' + end.status);

            });
          });
      }
    });
  }
});

// route to authenticate a user (POST api/requestpass)
apiRoutes.post('/requestpass', function(req, res) {

  // console.log('requestpass');
  // console.log(req.body);

  User.
  findOne({email: req.body.email}).
  exec(function(err, user) {
    if (err) {
      console.error(err);
        console.error(err)
        res.send({success: false,
                  message: err});
    } else if (user) {
      let new_pass_raw = randomstring.generate(12);
      // console.log('new_pass_raw', new_pass_raw);
      user.password =  new_pass_raw;
      // Expire in 60 minutes
      user.pass_expire = Date.now() + 3600;
      user.pass_force_change = true;
      user.save(function(err, saved_user) {
        if (err) {
          console.error(err);
          res.send({success: false,
                    message: err});
        } else {
          // Set up the email options
          let mailOptions = {
            from: 'fmurphy@anl.gov',
            to: user.email,
            cc: 'fmurphy@anl.gov',
            subject: 'RAPD password recovery',
            text: 'Your new temporary password is '+new_pass_raw+'\nIt is authorized for 60 minutes.'};
          // Send the email
          smtp_transport.sendMail(mailOptions);
          // Reply to client
          res.json({success: true});
        }
      });
    } else {
      console.error('No user found in password request');
      res.send({success: false,
                message: 'No user found for email '+req.body.email});
    }
  });
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

    // Verifies secret and checks exp
    jwt.verify(token, app.get('superSecret'), function(err, decoded) {
      if (err) {
        return res.json({success: false,
                         message: 'Failed to authenticate token.'});
      } else {
        let now = Date.now()/1000;
        // if everything is good, save to request for use in other routes
        if (decoded.iat <= now && decoded.exp >= now) {
          req.decoded = decoded;
          next();
        }
      }
    });

  // If there is no token return an error
  } else {
    return res.status(403).send({
        success: false,
        message: 'No token provided.'
    });
  }
});

// REGISTER OUR ROUTES -------------------------------

// all of our routes will be prefixed with /api
app.use('/api', apiRoutes);

// Imported routes
app.use('/api', groups_routes);
app.use('/api', images_routes);
app.use('/api', jobs_routes);
app.use('/api', projects_routes);
app.use('/api', runs_routes);
app.use('/api', sessions_routes);
app.use('/api', users_routes);

module.exports = app;



var port = normalizePort(process.env.PORT || config.port);
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


// // Setup route
// app.get('/setup', function(req, res) {
//
//   // create a sample user
//   var fm = new User({
//     username: 'Frank Murphy',
//     password: 'groovylovebugbed',
//     role: 'site_admin',
//     group: null,
//     email: 'fmurphy@anl.gov',
//     status: 'active'
//   });
//
//   // save the sample user
//   fm.save(function(err) {
//     if (err) throw err;
//
//     console.log('User saved successfully');
//   });
//
//   // // create a sample group
//   var necat = new Group({
//     groupname: 'NECAT',
//     institution: 'Cornell University',
//     status: 'active',
//     uid: 'necat',
//     gidNumber: 1,
//     uidNumber: 1
//   });
//
//   // save the sample user
//   necat.save(function(err) {
//     if (err) throw err;
//
//     console.log('Group saved successfully');
//   });
//
//   res.json({ success: true });
//
// });

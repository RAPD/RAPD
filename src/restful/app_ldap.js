var bodyParser = require('body-parser');
var config = require('./config'); // get our config file
var cookieParser = require('cookie-parser');
var debug = require('debug')('backend:server');
var express = require('express');
var session = require('express-session');
var http = require('http');
var jwt = require('jsonwebtoken');
var ldap = require('ldapjs');
var mongoose = require('mongoose');
var morgan = require('morgan');
var nodemailer = require('nodemailer');
var smtpTransport = require('nodemailer-smtp-transport');
var path = require('path');
var randomstring = require("randomstring");
var favicon = require('serve-favicon');

var RedisStore = require('connect-redis')(session);

var Wss = require('./ws_server');

// Routing
// var routes = require('./routes/index');
// var users = require('./routes/users');

// MongoDB Models
var Session = require('./models/session');
var User = require('./models/user');
var Group = require('./models/group');

// LDAP client
var ldap_client = ldap.createClient({
  url: 'ldap://'+config.ldap_server
});

// Email Configuration
var smtp_transport = nodemailer.createTransport(smtpTransport({
  host: 'mailhost.anl.gov'
}));

// Create the express app instance
var app = express();
var server = http.createServer(app);

// Add session handling
let app_session = session({
  // store: new RedisStore({
  //   host: config.redis_host
  // }),
  secret: 'keyboard cat',
  resave: false,
  saveUninitialized: true
});
app.use(app_session);

// Create the socket.io server
var wss = new Wss({morgan:morgan,
                   server:server});

// Connect to MongoDB
mongoose.connect(config.database);
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
    req.session.working = 'yes!';
    console.log('working =', req.session.working);
    console.log(req.session);
    console.log(req.url);

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
      res.send(200);
    }
    else {
    //move on
      next();
    }
});

// route to authenticate a user (POST http://localhost:8080/api/authenticate)
apiRoutes.post('/authenticate', function(req, res) {

  console.log('authenticate');
  // console.log(req.body);

  // Authenticate
  ldap_client.bind('uid='+req.body.uid+','+config.ldap_dn, req.body.password, function(err) {
    // REJECTION
    if (err) {
      console.log(err);
      var reason = err.name.toString();
      console.log(reason);
      res.json({ success: false, message: 'Authentication failed. ' + reason});

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
          console.log(err);
        }

        var user = undefined;

        result.on('searchEntry', function(entry) {

          // The user information
          user = entry.object;
          console.log(user);

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
        });
        result.on('searchReference', function(referral) {
          console.log('referral: ' + referral.uris.join());
        });
        result.on('error', function(err) {
          console.error('error: ' + err.message);
        });
        result.on('end', function(end) {
          console.log(user);
          console.log('status: ' + end.status);

        });
      });
    }
  });
});

// route middleware to verify a token
apiRoutes.use(function(req, res, next) {

  console.log(req.body);
  console.log(req.query);
  console.log(req.headers);

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
        console.log(decoded.iat, decoded.exp, (decoded.exp-now)/(60));
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

// test route to make sure everything is working (accessed at GET http://localhost:8080/api)
// apiRoutes.use(jwtCheck);

apiRoutes.get('/', function(req, res) {
    res.json({ message: 'Welcome to the RAPD api!' });
});

// on routes that end in /sessions
// ----------------------------------------------------
apiRoutes.route('/sessions')

  // get all the sessions (accessed at GET http://localhost:3000/api/sessions)
  .get(function(req, res) {

    var find_search = { group: { $in: req.decoded._doc.groups}};
    if (req.decoded._doc.role == 'site_admin') {
      find_search = {}
    }

    Session.
      find(find_search).
      populate('group', 'groupname').
      sort({end: -1}).
      exec(function(err, sessions) {
        if (err) {
          res.send(err);
        } else {
          res.json(sessions);
        }
      });
  })

  // create a session (accessed at POST http://localhost:3000/api/sessions)
  .post(function(req, res) {

    var session = new Session(JSON.parse(req.body.session));     // create a new instance of the Session model

    // save the bear and check for errors
    session.save(function(err) {
      if (err) {
        res.send(err);
      } else {
        res.json({ message: 'Session created!' });
      }
    });

  });

// on routes that end in /sessions/:session_id
// ----------------------------------------------------
apiRoutes.route('/sessions/:session_id')

  // get the session with that id (accessed at GET http://localhost:8080/api/sessinos/:session_id)
  .get(function(req, res) {
    Session.findById(req.params.session_id, function(err, session) {
      if (err)
        res.send(err);
      res.json(session);
    });
  })

  // update the bear with this id (accessed at PUT http://localhost:8080/api/sessions/:session_id)
  .put(function(req, res) {

    let session = req.body.session;

    // Make sure group is only an _id
    session.group = session.group._id;

    // use our bear model to find the session we want
    Session.findById(session._id, function(err, saved_session) {

      if (err)
        res.send(err);

      // Update the document
      saved_session.set(session);

      // save the bear
      saved_session.save(function(err) {
        if (err) {
          res.send(err);
        }

        Session.
          findById(session._id).
          populate('group', 'groupname').
          exec(function(err, return_session) {
            console.log(return_session);
            let params = {
              success: true,
              operation: 'edit',
              session: return_session
            };
            res.json(params);
          });
      });
    });
  })

  // delete the session with this id (accessed at DELETE http://localhost:8080/api/sessions/:session_id)
  .delete(function(req, res) {

    console.log(req.params.session_id);

    Session.remove({
      _id: req.params.session_id
    }, function(err, session) {
      if (err) {
        res.send(err);
      } else {
        res.json({ message: 'Successfully deleted' });
      }
    });
  });

// on routes that end in /results
// ----------------------------------------------------
apiRoutes.route('/results/:session_id')

    // get the session with that id (accessed at GET http://localhost:8080/api/bears/:bear_id)
    .get(function(req, res) {
        Session.find({session_id:req.params.session_id}, function(err, sessions) {
            if (err)
                res.send(err);
            console.log(sessions);
            res.json(sessions);
        });
    });

// routes that end with users
// ----------------------------------------------------
// route to return all users (GET http://localhost:8080/api/users)
apiRoutes.route('/users')
  .get(function(req, res) {

    // SERCAT uses LDAP per group
    var users = [];
    ldap_client.search(config.ldap_dn, {  //}"dc=ser,dc=aps,dc=anl,dc=gov", {
      scope:'sub',
      filter:'objectclass=*'
    }, function(err, ldap_result) {
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
    });
  });

/**
 * @api {get} /users/populate Populate users into MongoDB from LDAP server
 * @apiName PopulateUsers
 * @apiGroup User
 *
 * @apiSuccess {Boolean} success or failure.
 */
apiRoutes.route('/users/populate')
  .get(function(req, res) {

    // Search for all users in LDAP
    var ldap_users = [];
    ldap_client.search("dc=ser,dc=aps,dc=anl,dc=gov", {
      scope:'sub',
      filter:'objectclass=*'
    }, function(err, res) {
      res.on('searchEntry', function(entry) {
        ldap_users.push(entry.object);
        // console.log('entry: ' + JSON.stringify(entry.object));
        // create a group
        var ldap_user = entry.object;
        var new_user = new Group({
          uid: ldap_user.uid,
          uidNumber: ldap_user.uidNumber,
          gidNumber: ldap_user.gidNumber,
        });
        new_user.save(function(err) {});
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

    // Now process each user
    for (let ldap_user of ldap_users) {
      console.log(ldap_user);

      // create a group
      var new_user = new Group({
        uid: ldap_user.uid,
        uidNumber: ldap_user.uidNumber,
        gidNumber: ldap_user.gidNumber,
      });

      new_user.save(function(err) {
        console.log(err);
      });

      console.log(new_user);
    }
  });

apiRoutes.route('/users/:uid')

  // Retrieve user information by uid
  .get(function(req, res) {

    console.log('GET user');

    // Fetch user
    ldap_client.search('uid='+req.params.uid+',ou=People,dc=ser,dc=aps,dc=anl,dc=gov', {
      scope:'sub',
      filter:'objectclass=*',
      sizeLimit:1
    }, function(err, result) {

      // LDAP error
      if (err) {
        console.log(err);
      }

      var user = undefined;

      result.on('searchEntry', function(entry) {
        // The user information
        user = entry.object;
        console.log(user);
      });
      result.on('searchReference', function(referral) {
        console.log('referral: ' + referral.uris.join());
      });
      result.on('error', function(err) {
        console.error('error: ' + err.message);
      });
      result.on('end', function(end) {
        console.log(user);
        console.log('status: ' + end.status);
        res.json(user);
      });
    });
  });

// REGISTER OUR ROUTES -------------------------------

// basic route
/**
 * @api {get} / Feedback that server is up
 * @apiName Base
 * @apiGroup Admin
 *
 * @apiSuccess {String} message Message in the format "Hello! The API is at http://localhost:3000/api".
 */
app.get('/', function(req, res) {
    res.send('Hello! The API is at http://localhost:' + app.get('port') + '/api');
});



// all of our routes will be prefixed with /api
app.use('/api', apiRoutes);

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

const bodyParser = require("body-parser");
// const cookieParser =  require('cookie-parser');
const debug = require("debug")("backend:server");
const express = require("express");
const session = require("express-session");
const RedisStore = require("connect-redis")(session);
const http = require("http");
// const favicon =       require('serve-favicon');
const jwt = require("jsonwebtoken");
const morgan = require("morgan");
const nodemailer = require("nodemailer");
const smtpTransport = require("nodemailer-smtp-transport");
// const path =          require('path');
const randomstring = require("randomstring");
const useragent = require("express-useragent");

// RAPD websocket server
const Wss = require("./ws_server");

// Configuration
const config = require("./config"); // get our config file

// Create the express app instance
let app = express();
let server = http.createServer(app);
// app.use(cors);

// Routing
const dashboard_routes = require("./routes/dashboard");
const downloads_routes = require("./routes/downloads");
const groups_routes = require("./routes/groups");
const images_routes = require("./routes/images");
const jobs_routes = require("./routes/jobs");
const overwatch_routes = require("./routes/overwatch");
const pdb_routes = require("./routes/pdbs");
const projects_routes = require("./routes/projects");
const results_routes = require("./routes/results");
const result_details_routes = require("./routes/result_details");
const runs_routes = require("./routes/runs");
const sessions_routes = require("./routes/sessions");
const upload_routes = require('./routes/upload');
const users_routes = require("./routes/users");

// Redis
var Redis = require("ioredis");
var redis_client = new Redis(config.redis_connection);

// MongoDB connection
var mongoose = require("./models/mongoose");
// mongoose.set("debug", true);

// Connect to ctrl_conn
const Activity = mongoose.ctrl_conn.model(
  "Activity",
  require("./models/activity").ActivitySchema
);
const Login = mongoose.ctrl_conn.model(
  "Login",
  require("./models/login").LoginSchema
);

// User and Group uses auth_conn
const User = mongoose.auth_conn.model(
  "User",
  require("./models/user").UserSchema
);
const Group = mongoose.auth_conn.model(
  "Group",
  require("./models/group").GroupSchema
);

// LDAP
if (config.authenticate_mode === "ldap") {
  const ldap = require("ldapjs");
  var ldap_client = ldap.createClient({
    url: "ldap://" + config.ldap_server
  });
}

// Email Configuration
var smtp_transport = nodemailer.createTransport(
  smtpTransport({
    host: config.mailhost
  })
);

// Add session handling
let app_session = session({
  store: new RedisStore({ client: redis_client }),
  secret: "keyboard cat",
  resave: false,
  saveUninitialized: true
});
app.use(app_session);

// Add useragent to make some stuff simpler
app.use(useragent.express());

// Create the websocket server
var wss = new Wss({
  morgan: morgan,
  server: server
});

app.set("superSecret", config.secret);

// configure app to use bodyParser()
// this will let us get the data from a POST
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// use morgan to log requests to the console
app.use(morgan("dev"));

// Logging of REST requests
let screened_urls = {
  "/api/dashboard/logins": 1,
  "/api/dashboard/results": 1,
  "/api/overwatches": 1,
  "/api//upload": 1
};
var myLogger = function(req, res, next) {
  // console.log('req.url', req.url);
  if (!(req.url in screened_urls)) {
    let activity = new Activity({
      source: "rest",
      type: req.url
    }).save();
  }
  next();
};
app.use(myLogger);

// ROUTES FOR OUR API
// =============================================================================
var apiRoutes = express.Router(); // get an instance of the express Router

// middleware to use for all requests
apiRoutes.use(function(req, res, next) {
  console.log(req.method);
  console.log(">>1<<");
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Credentials", "true");
  res.setHeader(
    "Access-Control-Allow-Methods",
    "GET,HEAD,OPTIONS,POST,PUT,DELETE,OPTIONS"
  );
  res.setHeader(
    "Access-Control-Allow-Headers",
    "Access-Control-Allow-Headers, Authorization, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers"
  );
  // intercepts OPTIONS method from http://johnzhang.io/options-request-in-express
  if ("OPTIONS" === req.method) {
    //respond with 200
    res.sendStatus(200);
  } else {
    next();
  }
});

// route to authenticate a user (POST http://localhost:8080/api/authenticate)
apiRoutes.post("/authenticate", function(req, res) {
  console.log("authenticate");

  // Get useragent data
  let ua = req.useragent;

  console.log(req.body);

  if (config.authenticate_mode === "mongo") {
    // console.log("Using Mongo to authenticate");
    User.getAuthenticated(req.body.email, req.body.password, function(
      err,
      user,
      reason
    ) {
      if (err) {
        console.error(err);
        res.json({ success: false, message: err });
        // login was successful if we have a user
      } else if (user) {
        console.log("user:", user);

        // create a token
        user.pass = undefined;
        user.password = undefined;
        user.salt = undefined;
        var token = jwt.sign(user.toJSON(), app.get("superSecret"), {
          expiresIn: 86400 // expires in 24 hours
        });

        // Return the information including token as JSON
        res.json({
          success: true,
          message: "Enjoy your token!",
          token: token,
          pass_force_change: user.pass_force_change
        });

        // Get useragent data
        let ua = req.useragent;

        // Record the login
        let new_login = new Login({
          browser: ua.browser,
          browser_version: ua.version,
          email: req.body.email,
          ip_address: req.connection.remoteAddress,
          os: ua.os,
          platform: ua.platform,
          success: true
        }).save();

        // otherwise we can determine why we failed
      } else {
        var reasons = User.failedLogin,
          message;

        // Turn reason into something understandable
        switch (reason) {
          case reasons.NOT_FOUND:
            message = "Authentication failed. No such user.";
            break;
          case reasons.PASSWORD_INCORRECT:
            message = "Authentication failed. Wrong password.";
            break;
          case reasons.MAX_ATTEMPTS:
            message = "Authentication failed. Too many failed attempts";
            break;
        }

        // Return to client
        console.error(message);
        res.json({
          success: false,
          message: message
        });

        // Log the failure
        let new_login = new Login({
          browser: ua.browser,
          browser_version: ua.version,
          email: req.body.email,
          ip_address: req.connection.remoteAddress,
          os: ua.os,
          platform: ua.platform,
          reason: reason,
          success: false
        }).save();

        return false;
      }
    });
  } else if (config.authenticate_mode === "ldap") {
    // Authenticate
    ldap_client.bind(
      "uid=" + req.body.uid + "," + config.ldap_dn,
      req.body.password,
      function(err) {
        // REJECTION
        if (err) {
          console.error(err);

          let reason = err.name.toString();

          // Return to client
          res.json({
            success: false,
            message: "Authentication failed. " + reason
          });

          // Log the failure
          let new_login = new Login({
            browser: ua.browser,
            browser_version: ua.version,
            email: req.body.email,
            ip_address: req.connection.remoteAddress,
            os: ua.os,
            platform: ua.platform,
            reason: reason,
            success: false
          }).save();

          return false;

        // AUTHENTICATED - now get Mongo info on user/group
        } else {
          // Fetch user
          ldap_client.search(
            "uid=" + req.body.uid + "," + config.ldap_dn,
            {
              scope: "sub",
              filter: "objectclass=*",
              sizeLimit: 1
            },
            function(err, result) {
              // LDAP error
              if (err) {
                console.error(err);

                let reason = err.name.toString();

                // Notify client
                res.json({
                  success: false,
                  message: reason
                });

                // Log the failure
                let new_login = new Login({
                  browser: ua.browser,
                  browser_version: ua.version,
                  uid: req.body.uid,
                  ip_address: req.connection.remoteAddress,
                  os: ua.os,
                  platform: ua.platform,
                  reason: reason,
                  success: false
                }).save();

                return false;
              } else {
                result.on("searchEntry", function(entry) {
                  // The user information
                  let user = entry.object;

                  // Look for a group that corresponds to this user
                  Group.find({ uid: user.uid }, function(err, groups) {
                    if (err) {
                      console.error(err);

                      let reason = err.name.toString();

                      // Notify client
                      res.json({
                        success: false,
                        message: reason
                      });

                      // Log the failure
                      let new_login = new Login({
                        browser: ua.browser,
                        browser_version: ua.version,
                        uid: req.body.uid,
                        ip_address: req.connection.remoteAddress,
                        os: ua.os,
                        platform: ua.platform,
                        reason: reason,
                        success: false
                      }).save();

                      return false;
                    } else {
                      // A group has been returned
                      if (groups[0]) {
                        let return_group = groups[0];
                        console.log("Have group for user", return_group);

                        // Transform group info to user-like object
                        let m_user = {
                          _doc: {
                            _id: return_group._id,
                            username: return_group.groupname,
                            email: return_group.email,
                            creator: return_group.creator,
                            timestamp: return_group.timestamp,
                            status: return_group.status,
                            role: return_group.role,
                            pass_force_change: false,
                            pass_expire: false,
                            loginAttempts: return_group.loginAttempts,
                            groups: [
                              {
                                _id: return_group._id,
                                groupname: return_group.groupname
                              }
                            ],
                            created: return_group.created
                          }
                        };

                        // create a token
                        let token = jwt.sign(m_user, app.get("superSecret"), {
                          expiresIn: 86400 // expires in 24 hours
                        });

                        // Return the information including token as JSON
                        res.json({
                          success: true,
                          message: "Enjoy your token!",
                          token: token,
                          pass_force_change: false
                        });

                        // Record the login
                        let new_login = new Login({
                          browser: ua.browser,
                          browser_version: ua.version,
                          uid: req.body.uid,
                          ip_address: req.connection.remoteAddress,
                          os: ua.os,
                          platform: ua.platform,
                          success: true
                        }).save();

                        return true;

                        // No groups returned
                      } else {
                        // Create a new group with the info from LDAP
                        let new_group = new Group({
                          email: user.mail,
                          gidNumber: user.gidNumber,
                          groupname: user.cn,
                          role: "user",
                          status: "active",
                          uid: user.uid,
                          uidNumber: user.uidNumber
                        });
                        new_group.save(function(err, return_group) {
                          if (err) {
                            console.error(err);

                            let reason = err.name.toString();

                            // Notify client
                            res.json({
                              success: false,
                              message: reason
                            });

                            // Log the failure
                            let new_login = new Login({
                              browser: ua.browser,
                              browser_version: ua.version,
                              uid: req.body.uid,
                              ip_address: req.connection.remoteAddress,
                              os: ua.os,
                              platform: ua.platform,
                              reason: reason,
                              success: false
                            }).save();

                            return false;
                          } else {
                            console.log(
                              "Group saved successfully",
                              return_group
                            );

                            let m_user = {
                              _doc: {
                                _id: return_group._id,
                                username: return_group.groupname,
                                email: return_group.email,
                                creator: return_group.creator,
                                timestamp: return_group.timestamp,
                                status: return_group.status,
                                role: return_group.role,
                                pass_force_change: false,
                                pass_expire: false,
                                loginAttempts: return_group.loginAttempts,
                                groups: [
                                  {
                                    _id: return_group._id,
                                    groupname: return_group.groupname
                                  }
                                ],
                                created: return_group.created
                              }
                            };

                            // create a token
                            let token = jwt.sign(
                              m_user,
                              app.get("superSecret"),
                              {
                                expiresIn: 86400 // expires in 24 hours
                              }
                            );

                            // Return the information including token as JSON
                            res.json({
                              success: true,
                              message: "Enjoy your token!",
                              token: token,
                              pass_force_change: false
                            });

                            // Record the login
                            let new_login = new Login({
                              browser: ua.browser,
                              browser_version: ua.version,
                              email: req.body.email,
                              ip_address: req.connection.remoteAddress,
                              os: ua.os,
                              platform: ua.platform,
                              success: true
                            }).save();

                            return true;
                          }
                        });
                      }
                    }
                  });
                });
                result.on("searchReference", function(referral) {
                  console.log("referral: " + referral.uris.join());
                });
                result.on("error", function(err) {
                  console.error("error: " + err.message);
                  res.json({
                    success: false,
                    message: err
                  });
                });
                result.on("end", function(end) {
                  // console.log(user);
                  console.log("status: " + end.status);
                });
              }
            }
          );
        }
      }
    );
  }
});

// route to authenticate a user (POST api/requestpass)
apiRoutes.post("/requestpass", function(req, res) {
  console.log(">>2<<");
  console.log('requestpass');
  console.log(">>3<<");
  console.log(req.body);
  console.log(">>4<<");
  if (config.authenticate_mode === "mongo") {
    User.findOne({ email: req.body.email }).exec(function(err, user) {
      if (err) {
        console.error(err);
        res.send({
          success: false,
          message: err
        });
      } else if (user) {
        let new_pass_raw = randomstring.generate(12);
        // console.log('new_pass_raw', new_pass_raw);
        user.password = new_pass_raw;
        // Expire in 60 minutes
        user.pass_expire = Date.now() + 3600;
        user.pass_force_change = true;
        user.save(function(err, saved_user) {
          if (err) {
            console.error(err);
            res.send({
              success: false,
              message: err
            });
          } else {
            // Set up the email options
            let mailOptions = {
              from: config.admin_email,
              to: user.email,
              cc: config.admin_email,
              subject: "RAPD password recovery",
              text:
                "Your new temporary password is " +
                new_pass_raw +
                "\nIt is authorized for 60 minutes."
            };
            // Send the email
            smtp_transport.sendMail(mailOptions);
            // Reply to client
            console.log(`Reset password for ${user.email} to ${new_pass_raw}`);
            res.json({ success: true });
          }
        });
      } else {
        console.error("No user found in password request");
        res.send({
          success: false,
          message: "No user found for email " + req.body.email
        });
      }
    });
  } else if (config.authenticate_mode === "ldap") {
    res.send({
      success: false,
      message: "Sorry, cannot fetch passwords for this site"
    });
  }
});

// test route to make sure everything is working (accessed at GET http://localhost:8080/api)
// apiRoutes.use(jwtCheck);
apiRoutes.get("/", function(req, res) {
  res.json({ message: "Welcome to the RAPD api!" });
});

// if (! process.env.NODE_ENV === 'development') {
// route middleware to verify a token
apiRoutes.use(function(req, res, next) {
  console.log(req.body);
  console.log(req.query);
  console.log(req.headers);

  // check header or url parameters or post parameters for token
  var token = req.headers.authorization.replace("Bearer ", "");

  // decode token
  if (token) {
    // Verifies secret and checks exp
    jwt.verify(token, app.get("superSecret"), function(err, decoded) {
      if (err) {
        return res.json({
          success: false,
          message: "Failed to authenticate token."
        });
      } else {
        let now = Date.now() / 1000;
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
      message: "No token provided."
    });
  }
});
// }

// REGISTER OUR ROUTES -------------------------------

// all of our routes will be prefixed with /api
app.use("/api", apiRoutes);

// Imported routes
app.use("/api", dashboard_routes);
app.use("/api", downloads_routes);
app.use("/api", groups_routes);
app.use("/api", images_routes);
app.use("/api", jobs_routes);
app.use("/api", overwatch_routes);
app.use("/api", pdb_routes);
app.use("/api", projects_routes);
app.use("/api", results_routes);
app.use("/api", result_details_routes);
app.use("/api", runs_routes);
app.use("/api", sessions_routes);
app.use("/api", upload_routes);
app.use("/api", users_routes);

module.exports = app;

let port = normalizePort(process.env.PORT || config.port);
app.set("port", port);
console.log('Listening on port', port);
server.listen(port);
server.on("error", onError);
server.on("listening", onListening);

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
  if (error.syscall !== "listen") {
    throw error;
  }

  var bind = typeof port === "string" ? "Pipe " + port : "Port " + port;

  // handle specific listen errors with friendly messages
  switch (error.code) {
    case "EACCES":
      console.error(bind + " requires elevated privileges");
      process.exit(1);
      break;
    case "EADDRINUSE":
      console.error(bind + " is already in use");
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
  var bind = typeof addr === "string" ? "pipe " + addr : "port " + addr.port;
  debug("Listening on " + bind);
}

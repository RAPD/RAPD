// Configuration
const config = require("./config");

// Core modules
var http = require("http");
var url = require("url");
var WebSocketServer = require("ws").Server;
// var SocketIo = require('socket.io');
var mongoose = require("./models/mongoose");
Q = require("q");
// Fix the promise issue in Mongoose
// mongoose.Promise = Q.Promise;
var Schema = mongoose.Schema;

var jwt = require("jsonwebtoken");
var uuid = require("node-uuid");

// Redis
var Redis = require("ioredis");

// Import models
var mongoose = require("./models/mongoose");
const Activity = mongoose.ctrl_conn.model(
  "Activity",
  require("./models/activity").ActivitySchema
);
const Image = mongoose.ctrl_conn.model(
  "Image",
  require("./models/image").ImageSchema
);
const Result = mongoose.ctrl_conn.model(
  "Result",
  require("./models/result").ResultSchema
);

// Definitions of result types
var result_type_trans = {
  mx: {
    snap: ["mx:index+strategy"],
    sweep: ["mx:integrate"],
    merge: [],
    mr: [],
    sad: [],
    mad: []
  }
};

// All the ws_connections
var ws_connections = {};

// Subscribe to redis updates
try {
  var sub = new Redis(config.redis_connection);
} catch (e) {
  console.error("Cannot connect to redis", config.redis_connection);
  throw e;
}

// Handle new message passed from Redis
sub.on("message", function(channel, message) {
  console.log("sub channel " + channel);

  // Decode into oject
  let message_object = JSON.parse(message);

  // Grab out the session_id
  let session_id = false;
  try {
    session_id = message_object.process.session_id;
    console.log("Message session:", session_id);
  } catch (e) {
    if (e instanceof TypeError) {
      console.error("Result has no session_id");
    } else {
      console.error(e);
    }
  }

  // Any connections?
  if (Object.keys(ws_connections).length > 0) {
    // Turn message into messages to send to clients
    parse_message(channel, message_object).then(function(messages_to_send) {
      console.log("messages_to_send", messages_to_send);
      //
      // console.log('Will send', messages_to_send.length, 'messages');
      //
      // Look for websockets that are watching the same session
      if (session_id) {
        Object.keys(ws_connections).forEach(function(socket_id) {
          console.log(ws_connections[socket_id].session);
          if (ws_connections[socket_id].session.session_id === session_id) {
            console.log("Have a live one!");
            messages_to_send.forEach(function(message) {
              console.log(message);
              ws_connections[socket_id].send(
                JSON.stringify({
                  msg_type: message[0],
                  results: message[1]
                })
              );
            });
          }
        });
      }
    });
  }
});

// Subscribe to updates
sub.subscribe("RAPD_RESULTS");

var parse_message = function(channel, message) {
  // console.log('parse_message');

  var deferred = Q.defer();

  // Array to return
  var return_array = [];

  switch (channel) {
    case "RAPD_RESULTS":
      console.log("RAPD_RESULTS");

      // Do nothing for ECHO
      if (message.command === "ECHO") {
        console.log("Echo...");
        deferred.resolve(return_array);

        // Do something for not ECHO
      } else {
        console.log(message.plugin);
        console.log(message.process);
        // { subtype: 'CORE',
        //   version: '2.0.0',
        //   type: 'ANALYSIS',
        //   id: 'f068',
        //   data_type: 'MX' }
        // { status: 50,
        //   parent:
        //   { subtype: 'CORE',
        //     version: '2.0.0',
        //     type: 'INTEGRATE',
        //     id: 'bd11',
        //     data_type: 'MX' },
        //   type: 'plugin',
        //   repr: 'MS01P14ds1_1_[1-1800].cbf',
        //   session_id: '5b38e3a7ad1d602a3d4b3282',
        //   parent_id: '5b3a975af468331c90d4e583',
        //   result_id: '5b3a97f1b77af848335f6ccd' }

        // Create a result
        let result = {
          _id: message.process.result_id,
          data_type: message.plugin.data_type.toLowerCase(),
          parent_id: message.process.parent_id,
          plugin_id: message.plugin.id,
          plugin_type: message.plugin.type.toLowerCase(),
          plugin_version: message.plugin.version,
          projects: [],
          repr: message.process.repr,
          result_id: message._id,
          session_id: message.process.session_id,
          status: message.process.status,
          timestamp: new Date().toISOString()
        };
        return_array.push(["results", [result]]);
        // console.log('  Pushed results object onto return array');

        // Create a detailed result
        Q.all([
          // Image 1
          populate_image(message.process.image1_id),
          // Image 2
          populate_image(message.process.image2_id),
          // Analysis
          populate_child_result(message.results.analysis, "analysis"),
          // PDBQuery
          populate_child_result(message.results.pdbquery, "pdbquery")
        ]).then(function(results) {
          // Assign results to detailed results
          message.image1 = results[0];
          message.image2 = results[1];
          message.results.analysis = results[2];
          message.results.pdbquery = results[3];

          return_array.push(["result_details", message]);

          // If result has a parent create a detailed result
          if (message.process.parent_id) {
            // Get the response to send to the websocket
            get_detailed_result(message.process.parent.data_type, message.process.parent.plugin_type, message.process.parent_id)
            .then(function(response) {
              return_array.push(["result_details", response]);
            });
          }

          // console.log('return_array now has length', return_array.length);
          // console.log('return_array', return_array);
          deferred.resolve(return_array);
        });
      }

      break;

    default:
      console.log("Don't know about this channel.");
      deferred.resolve(return_array);
      break;
  }

  return deferred.promise;
};

/*
 * Populate image data for detailed result
 * 
 */
var populate_image = function(image_key) {
  // Create deferred
  var deferred = Q.defer();

  // Make sure that the value is not false or undefined
  if (image_key) {
    // Get the image
    Image.findOne({
      _id: image_key
    }).exec(function(err, image1) {
      if (err) {
        console.error(err);
        deferred.resolve(false);
      } else {
        deferred.resolve(image1);
      }
    });
  } else {
    deferred.resolve(false);
  }

  // Return promise
  return deferred.promise;
};

/*
 * Populate analysis data for detailed result
 * 
 */
var populate_child_result = function(result_id, mode) {
  // Create deferred
  var deferred = Q.defer();

  // Create a mongoose model for the result
  let collection_name = "Mx_" + mode + "_result";
  var ResultModel;
  try {
    if (mongoose.ctrl_conn.model(collection_name)) {
      ResultModel = mongoose.ctrl_conn.model(collection_name);
    }
  } catch (e) {
    if (e.name === "MissingSchemaError") {
      let schema = new mongoose.Schema(
        {
          _id: {
            type: mongoose.Schema.ObjectId,
            auto: true
          }
        },
        {
          strict: false
        }
      );
      ResultModel = mongoose.ctrl_conn.model(collection_name, schema);
    }
  }

  // If there is a result
  if (result_id) {
    // Get the analysis result
    ResultModel.findOne({
      _id: result_id
    }).exec(function(err, child_result) {
      if (err) {
        console.error(err);
        deferred.resolve(false);
      } else {
        try {
          child_result._doc.command.input_data.db_settings = undefined;
        } catch (e) {
          // console.error(e);
        }
        deferred.resolve(child_result);
      }
    });
  } else {
    deferred.resolve(result_id);
  }

  // Return promise
  return deferred.promise;
};

function get_detailed_result(data_type, plugin_type, result_id) {
  
  console.log('get_detailed_result', data_type, plugin_type, result_id);
  
  var deferred = Q.defer();

  // Create a mongoose model for the result
  let name = (data_type + "_" + plugin_type + "_result").toLowerCase();
  let collection_name = name.charAt(0).toUpperCase() + name.slice(1);
  console.log(name, collection_name);
  var ResultModel;
  try {
    if (mongoose.ctrl_conn.model(collection_name)) {
      ResultModel = mongoose.ctrl_conn.model(collection_name);
    }
  } catch (e) {
    if (e.name === "MissingSchemaError") {
      let schema = new mongoose.Schema(
        {
          _id: {
            type: Schema.ObjectId,
            auto: true
          }
        },
        {
          strict: false
        }
      );
      ResultModel = mongoose.ctrl_conn.model(collection_name, schema);
    }
  }

  // Now get the result
  ResultModel.findOne({
    "process.result_id": mongoose.Types.ObjectId(result_id)
  }).exec(function(err, detailed_result) {
    // Error
    if (err) {
      console.error(err);
      deferred.resolve({
        msg_type: "result_details",
        success: false,
        results: err
      });

    // No error
    } else {
      console.log(detailed_result);
      if (detailed_result) {
        // console.log(Object.keys(detailed_result));
        // console.log(detailed_result._doc);
        // console.log(detailed_result._doc.process);

        // Make sure there is a process
        if ("process" in detailed_result._doc) {
          Q.all([
            // Image 1
            populate_image(detailed_result._doc.process.image1_id),
            // Image 2
            populate_image(detailed_result._doc.process.image2_id),
            // Analysis
            populate_child_result(
              detailed_result._doc.results.analysis,
              "analysis"
            ),
            // PDBQuery
            populate_child_result(
              detailed_result._doc.results.pdbquery,
              "pdbquery"
            )
          ]).then(function(results) {
            // Assign results to detailed results
            detailed_result._doc.image1 = results[0];
            detailed_result._doc.image2 = results[1];
            detailed_result._doc.results.analysis = results[2];
            detailed_result._doc.results.pdbquery = results[3];

            console.log('result_details', detailed_result);

            // Send back
            deferred.resolve({
              msg_type: "result_details",
              success: true,
              results: detailed_result
            });
          });

          // No 'process' in detailed_result._doc
        } else {
          // Send back
          deferred.resolve({
            msg_type: "result_details",
            success: true,
            results: detailed_result
          });
        }
      }
    }
  });

  return deferred.promise;
}

// The websocket code
function Wss(opt, callback) {
  // hide "new"
  if (!(this instanceof Wss)) {
    return new Wss(opt);
  }

  var wss = new WebSocketServer({
    server: opt.server
  });

  // const wss = new WebSocketServer({ port: 8080 });

  console.log('Wss up!');

  wss.on("connection", function connection(ws) {
    
    console.log("Connected");

    // Create a session object
    ws.session = {};

    // Mark the ws and save to list
    ws.id = uuid.v1();
    ws_connections[ws.id] = ws;

    // Create a ping interval to keep websocket connection alive
    let ping_timer = setInterval(function() {
      ws.send("ping");
    }, 45000);

    // Websocket has closed
    ws.on("close", function() {
      console.log("websocket closed");

      // Cancel the ping interval
      clearInterval(ping_timer);

      // Remove the websocket from the storage objects
      delete ws_connections[ws.id];
    });

    ws.on("error", function(err) {
      if (err.code !== "ECONNRESET") {
        // Ignore ECONNRESET and re throw anything else
        throw err;
      }
    });

    // Message incoming from the client
    ws.on("message", function(message) {
      var data = JSON.parse(message);
      // console.log(data);

      // Initializing the websocket
      if (data.request_type === "initialize") {
        jwt.verify(data.token, config.secret, function(err, decoded) {
          if (err) {
            console.error(err);
            ws.send(
              JSON.stringify({
                success: false,
                message: "Failed to authenticate token."
              })
            );
          } else {
            let now = Date.now() / 1000;
            // console.log(now, decoded.iat, decoded.exp, (decoded.exp-now)/(60));
            // The token is valid
            if (decoded.iat <= now && decoded.exp >= now) {
              // Add token to websocket session
              ws.session.token = decoded;
              // console.log(ws.session);
            }
          }
        });
      } else {
        // Guard against non-authorized connections
        if (ws.session === undefined || ws.session === {}) {
          return false;
        }

        switch (data.request_type) {
          // Get results
          case "get_results":
            console.log("get_results");

            var data_type, data_class;

            [data_type, data_class] = data.data_type.split(":");

            if (data_type === "mx") {
              if (data_class === "data") {
                Result.find({
                  session_id: mongoose.Types.ObjectId(data.session_id)
                })
                  .where("result_type")
                  .in(["mx:index", "mx:integrate"])
                  // populate('children').
                  .sort("-timestamp")
                  .exec(function(err, results) {
                    if (err) {
                      return false;
                    }
                    console.log("Found", results.length, "results");
                    // Send back over the websocket
                    ws.send(
                      JSON.stringify({
                        msg_type: "results",
                        results: results
                      })
                    );
                  });
              } else if (data_class === "snap") {
                Result.find({
                  session_id: mongoose.Types.ObjectId(data.session_id)
                })
                  .where("result_type")
                  .in(result_type_trans[data_type][data_class])
                  // populate('children').
                  .sort("-timestamp")
                  .exec(function(err, results) {
                    if (err) {
                      return false;
                    }
                    console.log("Found", results.length, "results");
                    // Send back over the websocket
                    ws.send(
                      JSON.stringify({
                        msg_type: "results",
                        results: results
                      })
                    );
                  });
              } else if (data_class === "sweep") {
                Result.find({
                  session_id: mongoose.Types.ObjectId(data.session_id)
                })
                  .where("result_type")
                  .in(result_type_trans[data_type][data_class])
                  // populate('children').
                  .sort("-timestamp")
                  .exec(function(err, sessions) {
                    if (err) {
                      return false;
                    }
                    console.log("Found", sessions.length, "results");
                    // Send back over the websocket
                    ws.send(
                      JSON.stringify({
                        msg_type: "results",
                        results: sessions
                      })
                    );
                  });
              } else if (data_class === "all") {
                console.log("data.session_id", data.session_id);

                Result.find({
                  session_id: mongoose.Types.ObjectId(data.session_id)
                })
                  // populate('children').
                  .sort("-timestamp")
                  .exec(function(err, results) {
                    if (err) return false;
                    console.log("Found", results.length, "results");
                    // Send back over the websocket
                    ws.send(
                      JSON.stringify({
                        msg_type: "results",
                        results: results
                      })
                    );
                  });
              }
            }

            console.log(ws.session.token);

            // Register activity
            let new_activity = new Activity({
              source: "websocket",
              type: "get_results",
              subtype: data.data_type + "_" + data.plugin_type,
              user: ws.session.token._id
            }).save();

            break;

          // Get result details
          case "get_result_details":
            console.log("get_result_details", data);

            // Get the response to send to the websocket
            get_detailed_result(data.data_type, data.plugin_type, data._id)
            .then(function(response) {
              // Send response over the wire
              console.log('response', response);
              ws.send(JSON.stringify(response));

              // Register activity
              var grd_activity = new Activity({
                source: "websocket",
                type: "get_result_details",
                subtype: data.data_type + "_" + data.plugin_type,
                user: ws.session.token._id
              }).save();
            });
            break;

          // Set the session id for the connected websocket
          case "set_session":
            console.log("Session set to " + data.session_id);
            this.session.session_id = data.session_id;
            break;

          // Unset the session id for the connected websocket
          case "unset_session":
            console.log("Unset session");
            this.session.session_id = undefined;
            break;

          case "update_result":
            console.log("update_result");
            console.log(data.result);

            Result.update(
              {
                _id: data.result._id
              },
              data.result
            ).exec(function(err, res) {
              console.log(err);
              console.log(res);
            });

            break;
        }
      }
    });
  });
}

module.exports = Wss;

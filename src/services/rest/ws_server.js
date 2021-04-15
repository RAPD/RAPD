// Configuration
const config = require("./config");

// Core modules
var http = require("http");
const os = require('os');
var url = require("url");
var WebSocketServer = require("ws").Server;
var mongoose = require("./models/mongoose");
Q = require("q");
// Fix the promise issue in Mongoose
// mongoose.Promise = Q.Promise;
var Schema = mongoose.Schema;

const jwt = require("jsonwebtoken");
const uuid = require("node-uuid");

const Redis = require("ioredis");

// Identifying data
const myId = uuid.v1();
const myHost = os.hostname();

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

console.debug(Result);

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
var activeSessions = [];

// Subscribe to redis updates
try {
  var sub = new Redis(config.redis_connection);
} catch (e) {
  console.error("Cannot connect to redis", config.redis_connection);
  throw e;
}

// Register connection to Redis database
const redis_client = new Redis(config.redis_connection);
redis_client.set("R2:WSS:"+myId, myHost, 'EX', 31);
setInterval(function() {
  // console.log("Updating connection tag on Redis");
  redis_client.set("R2:WSS:"+myId, myHost, 'EX', 31);
}, 30000);

// Handle new message passed from Redis
sub.on("message", function(channel, message) {
  
  console.log("sub channel " + channel);
  // console.log(message);

  // Decode into oject
  let message_object;
  try {
    message_object = JSON.parse(message);
  } catch (e) {
    if (e instanceof SyntaxError) {
      console.error("Failure in parsing message");
    } else {
      console.error("Unknown error parsing message");
      console.error(e);
    }
    // Break out of message handling
    return false;
  }
  
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
    // Break out of message handling
    return false;
  }
    
  // Only publish result if we have a session_id for the result
  // console.log(session_id);
  // console.log(activeSessions);
  if (activeSessions.includes(session_id)) {
    
    console.log("Have a subscribed session");
    
    // Create minimal result
    const minimalResult = getMinimalResult(message_object);
    console.log(minimalResult);
    
    let detailedResult = false;
    // Any webssocket with the session_id gets the minimal result
    Object.keys(ws_connections).forEach((socket_id) => {
      // Same session
      if (ws_connections[socket_id].session.session_id === session_id) {
        console.log("Sending minimal result to", session_id);
        // Send the minimalResult
        ws_connections[socket_id].send(
          JSON.stringify({
            msg_type: "results",
            results: [minimalResult]
          })
        );
        // Check if connection is subscribed to this result
        console.log(ws_connections[socket_id].session.current_results);
        const resultType = (minimalResult.data_type+":"+minimalResult.plugin_type).toUpperCase();
        console.log('resultType', resultType);
        console.log(ws_connections[socket_id].session.current_results[resultType]);
        if (ws_connections[socket_id].session.current_results[resultType]) {
          if (ws_connections[socket_id].session.current_results[resultType]._id === minimalResult._id) {
            console.log("HAVE A WEBSOCKET SUBBSCRIBED TO RESULT")
            if (! detailedResult) {
              getNewDetailedResult(message_object).then((result) => {
                detailedResult = result;
                console.log('Sending', detailedResult);
                ws_connections[socket_id].send(
                  JSON.stringify({
                    msg_type: "result_details",
                    results: detailedResult
                  })
                );
              });
            }
          }
        }
      }
    });

  }
});

// Subscribe to updates
sub.subscribe("RAPD_RESULTS");

// Create a minimal result to send to clients
const getMinimalResult = function(message) {
  const result = {
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
    spoof: message.process.spoof,
    status: message.process.status,
    timestamp: new Date().toISOString()
  };
  return result;
}

const getNewDetailedResult = function(message) {
  const deferred = Q.defer();

  // Do nothing for ECHO
  if (message.command === "ECHO") {
    console.log("Echo...");
    deferred.resolve({});

  // Do something for not ECHO
  } else {
    // Create a detailed result
    Q.all([
      // Image 1
      populateImage(message.process.image1_id),
      // Image 2
      populateImage(message.process.image2_id),
      // Analysis
      populateChildResult(message.results.analysis, "analysis"),
      // PDBQuery
      populateChildResult(message.results.pdbquery, "pdbquery")
    ]).then((results) => {
      // Assign results to detailed results
      message.image1 = results[0];
      message.image2 = results[1];
      message.results.analysis = results[2];
      message.results.pdbquery = results[3];
      deferred.resolve(message);
    });
  }
  return deferred.promise;
}

const parseMessage = function(channel, message) {
  // console.log('parseMessage');

  var deferred = Q.defer();

  // Array to return
  const returnObject = {};

  switch (channel) {
    case "RAPD_RESULTS":
      console.log("RAPD_RESULTS");

      // Do nothing for ECHO
      if (message.command === "ECHO") {
        console.log("Echo...");
        deferred.resolve(returnObject);

        // Do something for not ECHO
      } else {
        // console.log(message.plugin);
        // console.log(message.process);
        
        // message.process:
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

        // Create a result for clients
        let result;
        try {
          result = {
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
          
          // console.log('  Pushed results object onto return array');
          // returnArray.push(["results", [result]]);
          returnObject.minimal = result;

          // Create a detailed result
          Q.all([
            // Image 1
            populateImage(message.process.image1_id),
            // Image 2
            populateImage(message.process.image2_id),
            // Analysis
            populateChildResult(message.results.analysis, "analysis"),
            // PDBQuery
            populateChildResult(message.results.pdbquery, "pdbquery")
          ]).then(function(results) {
            // Assign results to detailed results
            message.image1 = results[0];
            message.image2 = results[1];
            message.results.analysis = results[2];
            message.results.pdbquery = results[3];

            // returnArray.push(["result_details", message]);
            returnObject.full = message;

            // If result has a parent create a detailed result
            if (message.process.parent_id) {
              // Get the response to send to the websocket
              getDetailedResult(message.process.parent.data_type, message.process.parent.plugin_type, message.process.parent_id)
              .then(function(response) {
                // returnArray.push(["result_details", response]);
                returnObject.full_parent = response;
              });
            }

            // console.log('return_array now has length', returnArray.length);
            // console.log('return_array', return_array);
            deferred.resolve(returnObject);
          });

        } catch (e) {
          console.error("Unable to construct result from RAPD_RESULT");
          console.error(e);
          deferred.resolve(false);
        }
      }

      break;

    default:
      console.log("Don't know about this channel.");
      deferred.resolve(returnArray);
      break;
  }

  return deferred.promise;
};

/*
 * Populate image data for detailed result
 */
var populateImage = function(image_key) {
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
 * Populate child result data of detailed result
 */
var populateChildResult = function(result_id, mode) {
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

// Retrieve and populate a detailed result from a plugin
function getDetailedResult(data_type, plugin_type, result_id, ws) {
  
  // console.log('getDetailedResult', data_type, plugin_type, result_id);
  
  var deferred = Q.defer();

  // Create a mongoose model for the result
  let name = (data_type + "_" + plugin_type + "_result").toLowerCase();
  let collection_name = name.charAt(0).toUpperCase() + name.slice(1);
  
  // Retrieve or make a model for this request
  let ResultModel;
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
  ResultModel.findOne(
    {"process.result_id": mongoose.Types.ObjectId(result_id)},)
    .exec(function(err, detailed_result) {
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
        if (detailed_result) {

          // Send part of the ressult back immediately before populating = faster
          if (ws) {
            ws.send(JSON.stringify({
              msg_type: "result_details",
              success: true,
              results: detailed_result,
              // results: {
              //   process:detailed_result._doc.process,
              //   results:{
              //     plots:detailed_result._doc.results.plots,
              //     summary:detailed_result._doc.results.summary,
              //   }
            }));
          }  

          // If there is a process then we add to the result
          if ("process" in detailed_result._doc) {
            Q.all([
              populateImage(detailed_result._doc.process.image1_id),
              populateImage(detailed_result._doc.process.image2_id),
              populateChildResult(
                detailed_result._doc.results.analysis,
                "analysis"
              ),
              populateChildResult(
                detailed_result._doc.results.pdbquery,
                "pdbquery"
              ),
              ]).then((results) => {
                // Assign results to detailed results
                detailed_result._doc.image1 = results[0];
                detailed_result._doc.image2 = results[1];
                detailed_result._doc.results.analysis = results[2];
                detailed_result._doc.results.pdbquery = results[3];
              
                // Send back
                const secondResponse = {
                  msg_type: "result_details",
                  success: true,
                  results: detailed_result
                };
                if (ws) {
                  ws.send(JSON.stringify(secondResponse));
                }
                deferred.resolve(secondResponse);
              });

          // No 'process' in detailed_result._doc
          } else {
            // Send back
            const response = {
              msg_type: "result_details",
              success: true,
              results: detailed_result
            }
            if (ws) {
              ws.send(response);
            }
            deferred.resolve(response);
          }
      }
    }
  });

  // Return the promise to caller
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

  console.log('Wss up!');

  wss.on("connection", function connection(ws) {
    
    console.log("WS Connected");

    // Create a session object
    ws.session = {
      session_id: undefined,
      current_result: undefined,
      current_results: {},
    };

    // Mark the ws and save to ws_connections object
    ws.id = uuid.v1();
    ws_connections[ws.id] = ws;

    // Create a ping interval to keep websocket connection alive
    const ping_timer = setInterval(function() {
      ws.send("ping");
    }, 45000);

    // Register the existencce of this WS cclient connection in Redis
    redis_client.set("R2:WSC:"+ws.id, ws.session.session_id, 'EX', 31);
    const register_interval = setInterval(function() {
      // console.log("Updating connection tag on Redis");
      redis_client.set("R2:WSC:"+ws.id, ws.session.session_id, 'EX', 31);
    }, 30000);


    // Websocket has closed
    ws.on("close", function() {
      console.log("websocket closed");

      // Cancel the ping interval
      clearInterval(ping_timer);
      clearInterval(register_interval)

      // Remove the session from activeSessions
      activeSessions.splice(activeSessions.indexOf(ws.session.session_id), 1);

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
      const data = JSON.parse(message);

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

                // Change to indexings first - load will be faster in UI appearance
                Result.find({
                  session_id: mongoose.Types.ObjectId(data.session_id),
                  plugin_type : "INDEX",
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
                  
                  // And now the integrations
                  Result.find({
                    session_id: mongoose.Types.ObjectId(data.session_id),
                    plugin_type : "INTEGRATE",
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

            // console.log(ws.session.token);

            // Register activity
            try {
              let new_activity = new Activity({
                source: "websocket",
                type: "get_results",
                subtype: data.data_type + "_" + data.plugin_type,
                user: ws.session.token._id
              }).save();
            // TODO error comes when no longer logged in person connects
            } catch (e) {
              console.error(e);
            }

            break;

          // Get result details
          case "get_result_details":
            
            console.log("get_result_details", data);

            this.session.current_results[data.result_type] = data;

            // Send current detailed result over the line
            getDetailedResult(data.data_type, data.plugin_type, data._id, ws)
              .then((response) => { 
                // Subscribe to new results

              });
              
              // Register the activity
              try {
                var grd_activity = new Activity({
                  source: "websocket",
                  type: "get_result_details",
                  subtype: data.data_type + "_" + data.plugin_type,
                  user: ws.session.token._id
                }).save();
              // TODO error comes when no longer logged in person connects
              } catch (e) {
                console.error(e);
              }
            
            break;

          // Set the session id for the connected websocket
          case "set_session":
            console.log("Session set to " + data.session_id);
            this.session.session_id = data.session_id;
            activeSessions.push(data.session_id);
            console.log(activeSessions);
            break;

          // Unset the session id for the connected websocket
          case "unset_session":
            console.log("Unset session");
            // Remove the session from activeSessions
            activeSessions.splice(activeSessions.indexOf(this.session.session_id), 1);
            this.session.session_id = undefined;
            this.session.current_results = {};
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

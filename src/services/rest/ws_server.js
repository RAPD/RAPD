// Configuration
const config = require('./config');

// Core modules
var http = require('http');
var url = require('url');
var WebSocketServer = require('ws').Server;
// var SocketIo = require('socket.io');
var mongoose = require('mongoose');
var jwt = require('jsonwebtoken');
var uuid = require('node-uuid');

// Redis
var redis = require('redis');

// Import models
var Result = require('./models/result');
var Image =  require('./models/image');

// Definitions of result types
var result_type_trans = {
    mx: {
      snap: ['mx:index+strategy'],
      sweep: ['mx:integrate'],
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
  var sub = redis.createClient(config.redis_port, config.redis_host);
} catch (e) {
  console.error("Cannot connect to redis", config.redis_port, config.redis_host);
  throw e;
}


sub.on("message", function (channel, message) {

  // console.log("sub channel " + channel + ": " + message);

  // Decode into oject
  let parsed_message = JSON.parse(message);

  // Grab out the session_id
  let session_id = false;
  try {
    session_id = parsed_message.process.session_id;
    console.log('Message session:', session_id);
  }
  catch (e) {
    if (e instanceof TypeError) {
      console.error('Result has no session_id');
    } else {
      console.error(e);
    }
  }

  // Turn message into messages to send to clients
  let messages_to_send = parse_message(channel, parsed_message);

  // Look for websockets that are watching the same session
  if (session_id) {
    Object.keys(ws_connections).forEach(function(socket_id) {
      // console.log(ws_connections[socket_id].session);
      if (ws_connections[socket_id].session.session_id === session_id) {
        console.log('Have a live one!');
        messages_to_send.forEach(function(message) {
          console.log(message)
          ws_connections[socket_id].send(JSON.stringify({msg_type:message[0],
                                                         results:message[1]}));
        });
      }
    });
  }
});

// Subscribe to updates
sub.subscribe("RAPD_RESULTS");

parse_message = function(channel, message) {
  console.log('parse_message', channel, message);

  switch (channel) {

    case 'RAPD_RESULTS':
      console.log('RAPD_RESULTS');

      // Do nothing for ECHO
      if (message.command === 'ECHO') {
        console.log('Echo...');
        return true;
      }

      // Array to return
      let return_array = [];

      // Create a result
      let result = { _id: message.process.process_id,
        data_type: message.plugin.data_type.toLowerCase(),
        plugin_id: message.plugin.id,
        plugin_type: message.plugin.type.toLowerCase(),
        plugin_version: message.plugin.version,
        projects: [],
        repr: message.process.repr,
        result_id: message._id,
        session_id: message.process.session_id,
        status: message.process.status,
        timestamp: new Date().toISOString()
        // result_type is deprecated
        // result_type: (message.plugin.data_type + ':' + message.plugin.type).toLowerCase(),
        };
      return_array.push(['results', [result]]);

      // Create a detailed result
      // Get image header information
      if ('image1_id' in message.process) {
        Image.
          findOne({_id:message.process.image1_id})
          .exec(function(im1_error, im1_result){
            if (im1_result) {
              message.image1 = im1_result;
              if ('image2_id' in message.process) {
                Image.
                  findOne({_id:message.process.image2_id})
                  .exec(function(im2_error, im2_result){
                    if (im2_result) {
                      message.image2 = im1_result;
                      return_array.push(['result_details', message]);
                    }
                  });
              } else {
                return_array.push(['result_details', message]);
              }
            }
          });
      } else {
        return_array.push(['result_details', message]);
      }

      // Return
      return return_array;
      break;

    default:
      console.log('Don\'t know about this channel.');
      return false;
      break;

  }
};

// The websocket code
function Wss (opt, callback) {

    // hide "new"
    if (!(this instanceof Wss)) {
      return new Wss(opt)
    }

    // Params are optional
    opt = opt || {}

    wss = new WebSocketServer({ server: opt.server });
    // var io = SocketIo(opt.server);


    wss.on('connection', function connection(ws) {

      console.log('Connected');

      // Create a session object
      ws.session = {};

      // Mark the ws and save to list
      ws.id = uuid.v1();
      ws_connections[ws.id] = ws;

      // Websocket has closed
      ws.on('close', function() {

        console.log('websocket closed');

        // Remove the websocket from the storage objects
        delete ws_connections[ws.id];
      });

      // Message incoming from the client
      ws.on('message', function(message) {

        var data = JSON.parse(message);
        console.log(data);

        // Initializing the websocket
        if (data.request_type === 'initialize' ) {
          jwt.verify(data.token, config.secret, function(err, decoded) {
            if (err) {
              console.error(err);
              ws.send(JSON.stringify({success:false,
                                      message:'Failed to authenticate token.'}));
            } else {

              let now = Date.now()/1000;
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

            // Set the session id for the connected websocket
            case 'set_session':
              console.log('Session set to '+data.session_id);
              this.session.session_id = data.session_id;
              break;

            case 'unset_session':
              this.session.session_id = undefined;
              break;

            // Get results
            case 'get_results':

              console.log('get_results');

              var data_type,
                  data_class;

              [data_type, data_class] = data.data_type.split(':')

              if (data_type === 'mx') {

                if (data_class === 'data') {

                  Result.
                    find({'session_id':mongoose.Types.ObjectId(data.session_id)}).
                    where('result_type').in(['mx:index', 'mx:integrate']).
                    sort('-timestamp').
                    exec(function(err, results) {
                        if (err)
                            return false;
                        console.log(results);
                        // Send back over the websocket
                        ws.send(JSON.stringify({msg_type:'results',
                                                results:results}));
                    });
                } else if (data_class === 'snap') {

                  Result.
                    find({'session_id':mongoose.Types.ObjectId(data.session_id)}).
                    where('result_type').in(result_type_trans[data_type][data_class]).
                    sort('-timestamp').
                    exec(function(err, sessions) {
                        if (err)
                            return false;
                        console.log(sessions);
                        // Send back over the websocket
                        ws.send(JSON.stringify({msg_type:'results',
                                                results:sessions}));
                    });
                } else if (data_class === 'sweep') {

                  Result.
                    find({'session_id':mongoose.Types.ObjectId(data.session_id)}).
                    where('result_type').in(result_type_trans[data_type][data_class]).
                    sort('-timestamp').
                    exec(function(err, sessions) {
                        if (err)
                            return false;
                        console.log(sessions);
                        // Send back over the websocket
                        ws.send(JSON.stringify({msg_type:'results',
                                                results:sessions}));
                    });
                } else if (data_class === 'all') {

                  console.log('data.session_id', data.session_id);

                  Result.
                    find({'session_id':mongoose.Types.ObjectId(data.session_id)}).
                    // where('result_type').in(['mx:index+strategy']).
                    sort('-timestamp').
                    exec(function(err, sessions) {
                        if (err)
                            return false;
                        console.log(sessions);
                        // Send back over the websocket
                        ws.send(JSON.stringify({msg_type:'results',
                                                results:sessions}));
                    });
                }

              }

              break;

            case 'update_result':

              console.log('update_result');
              console.log(data.result);

              Result.
                update({_id:data.result._id}, data.result).
                exec(function(err, res) {
                  console.log(err);
                  console.log(res);
                });

              break;

            // Get result details
            case 'get_result_details':
              console.log('get_result_details');
              console.log(data);

              // Create a model
              if (data.result_type.indexOf(':') !== -1) {
                data.result_type = data.result_type.replace(/:/, '_');
                // data.result_type = data.result_type.slice(data.result_type.indexOf(':')+1);
              }

              console.log('Looking in:', data.data_type+'_'+ data.plugin_type +'_results');

              // Create a mongoose model for the result
              let name = data.data_type+'_'+ data.plugin_type +'_result';
              let collection_name = name.charAt(0).toUpperCase() + name.slice(1);
              var ResultModel;
              try {
                if (mongoose.model(collection_name)) {
                  ResultModel = mongoose.model(collection_name);
                }
              } catch(e) {
                if (e.name === 'MissingSchemaError') {
                   let schema = new mongoose.Schema({}, {strict:false});
                   ResultModel = mongoose.model(collection_name, schema);
                }
              }

              // Searhc for a result
              ResultModel.
                findOne({'_id':mongoose.Types.ObjectId(data.result_id)}).
                // where('result_type').in(result_type_trans[data_type][data_class]).
                // sort('-timestamp').
                exec(function(err, result) {
                    if (err)
                        return false;
                    console.log(result);
                    // Send back over the websocket
                    ws.send(JSON.stringify({msg_type:'result_details',
                                            results:result}));
                });

              // ws.send(JSON.stringify({msg_type:'result_details',
              //                         results:'bar'}));

              break;
          }
        }




        // if (data.request_type == 'detailed_result') {
        //
        //   console.log('detailed_result')
        //
        // } else {
        //
        //   var data_type,
        //       data_class;
        //
        //   [data_type, data_class] = data.request_type.split(':')
        //
        //   if (data_type == 'mx') {
        //
        //     if (data_class == 'data') {
        //
        //       Result.
        //         find({'session_id':mongoose.Types.ObjectId(data.session_id)}).
        //         where('result_type').in(['mx:index+strategy', 'mx:integrate']).
        //         sort('-timestamp').
        //         exec(function(err, sessions) {
        //             if (err)
        //                 return false;
        //             console.log(sessions);
        //             // Send back over the websocket
        //             ws.send(JSON.stringify({msg_type:'results',
        //                                     results:sessions}));
        //         });
        //     } else if (data_class == 'snap') {
        //
        //       Result.
        //         find({'session_id':mongoose.Types.ObjectId(data.session_id)}).
        //         where('result_type').in(result_type_trans[data_type][data_class]).
        //         sort('-timestamp').
        //         exec(function(err, sessions) {
        //             if (err)
        //                 return false;
        //             console.log(sessions);
        //             // Send back over the websocket
        //             ws.send(JSON.stringify({msg_type:'results',
        //                                     results:sessions}));
        //         });
        //     } else if (data_class == 'sweep') {
        //
        //       Result.
        //         find({'session_id':mongoose.Types.ObjectId(data.session_id)}).
        //         where('result_type').in(result_type_trans[data_type][data_class]).
        //         sort('-timestamp').
        //         exec(function(err, sessions) {
        //             if (err)
        //                 return false;
        //             console.log(sessions);
        //             // Send back over the websocket
        //             ws.send(JSON.stringify({msg_type:'results',
        //                                     results:sessions}));
        //         });
        //     } else if (data_class == 'all') {
        //
        //       Result.
        //         find({'session_id':mongoose.Types.ObjectId(data.session_id)}).
        //         // where('result_type').in(['mx:index+strategy']).
        //         sort('-timestamp').
        //         exec(function(err, sessions) {
        //             if (err)
        //                 return false;
        //             console.log(sessions);
        //             // Send back over the websocket
        //             ws.send(JSON.stringify({msg_type:'results',
        //                                     results:sessions}));
        //         });
        //     }
        //
        //   }
        // }
      });
    });
}

module.exports = Wss;

// Configuration
var config = require('./config');

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
var redis_client = redis.createClient();

// Import models
var Result = require('./models/result');

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

// All the websocket_connections
var websocket_connections = {}

// Subscribe to redis updates


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

      // console.log(ws);

      // Create a session object
      ws.session = {foo:'bar'};

      // Mark the ws and save to list
      ws.id = uuid.v1();
      websocket_connections[ws.id] = ws;

      // Websocket has closed
      ws.on('close', function() {

        console.log('websocket closed');

        // Remove the websocket from the list
        delete websocket_connections[ws.id];
      });

      // Message incoming from the client
      ws.on('message', function(message) {

        var data = JSON.parse(message);
        console.log(data);

        // Initializing the websocket
        if (data.request_type === 'initialize' ) {
          jwt.verify(data.token, 'ilovescotchyscotch', function(err, decoded) {
            if (err) {
              console.log(err);
              // return res.json({ success: false, message: 'Failed to authenticate token.' });
            } else {
              // console.log(decoded);

              let now = Date.now()/1000;
              // console.log(decoded.iat, decoded.exp, (decoded.exp-now)/(60));
              // The token is valid
              if (decoded.iat <= now && decoded.exp >= now) {
                // console.log(ws.session);
                ws.session.token = decoded;
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
              this.session.session_id = data.session_id;

              break;

            case 'unset_session':
              this.session.session_id = undefined;

              break;

            // Get results
            case 'get_results':

              var data_type,
                  data_class;

              [data_type, data_class] = data.data_type.split(':')

              if (data_type === 'mx') {

                if (data_class === 'data') {

                  Result.
                    find({'session_id':mongoose.Types.ObjectId(data.session_id)}).
                    where('result_type').in(['mx:index+strategy', 'mx:integrate']).
                    sort('-timestamp').
                    exec(function(err, sessions) {
                        if (err)
                            return false;
                        console.log(sessions);
                        // Send back over the websocket
                        ws.send(JSON.stringify({msg_type:'results',
                                                results:sessions}));
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

            // Get result details
            case 'get_result_details':
              console.log('get_result_details');
              console.log(data);

              // Create a model
              if (data.result_type.indexOf(':') !== -1) {
                data.result_type = data.result_type.slice(data.result_type.indexOf(':')+1)
              }

              console.log('Looking in:', data.result_type+'_results');
              let ResultSchema = new mongoose.Schema({}, {strict:false});
              let ResultModel = mongoose.model(data.result_type+'_result', ResultSchema)
              ResultModel.
                find({'_id':mongoose.Types.ObjectId(data.result_id)}).
                // where('result_type').in(result_type_trans[data_type][data_class]).
                // sort('-timestamp').
                exec(function(err, result) {
                    if (err)
                        return false;
                    console.log(result);
                    // Send back over the websocket
                    // ws.send(JSON.stringify({msg_type:'results',
                    //                         results:sessions}));
                });

              ws.send(JSON.stringify({msg_type:'result_details',
                                      results:'bar'}));

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

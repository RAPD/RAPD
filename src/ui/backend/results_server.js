var WebSocketServer = require('ws').Server,
    wss = new WebSocketServer({ port: 8080 });

// Redis
var redis = require("redis"),
    client = redis.createClient();

var mongoose = require('mongoose');
// mongoose.connect('mongodb://localhost:27017/rapd2');
// mongoose.connect('mongodb://remote.nec.aps.anl.gov:27017/rapd2');
var Result = require('./models/result');

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


wss.on('connection', function connection(ws) {
  console.log('Connected');

  ws.on('message', function(message) {
    console.log(message);
    var data = JSON.parse(message);

    if (data.request_type == 'detailed_result') {

      console.log('detailed_result')

    } else {

      var data_type,
          data_class;

      [data_type, data_class] = data.request_type.split(':')

      if (data_type == 'mx') {

        if (data_class == 'data') {

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
        } else if (data_class == 'snap') {

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
        } else if (data_class == 'sweep') {

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
        } else if (data_class == 'all') {

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
  }


    // // get the results for the input session_id
    // Result.find({'session_id':mongoose.Types.ObjectId(data.session_id)}, function(err, sessions) {
    //     if (err)
    //         return false;
    //     console.log(sessions);
    //     // Send back over the websocket
    //     ws.send(JSON.stringify({msg_type:'results',
    //                             results:sessions}));
    // });
  });
})

module.exports = wss;

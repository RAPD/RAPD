var http = require('http'),
    httpProxy = require('http-proxy');

//
// Create a proxy server with custom application logic
//
var proxy = httpProxy.createProxyServer({});

//
// Create your custom server and just call `proxy.web()` to proxy
// a web request to the target passed in the options
// also you can use `proxy.ws()` to proxy a websockets request
var server = http.createServer(function(req, res) {
  // You can define here your custom logic to handle the request
  // and then proxy the request.
  // The REST API
  if (req.url.match(/\/api\//)) {
    proxy.web(req, res, { target: 'http://127.0.0.1:3000' });
  // Everything else
  } else {
    proxy.web(req, res, { target: 'http://127.0.0.1:4200' });
    //proxy.ws(req, res,  { target: 'http://127.0.0.1:3000' });
  }
});

// The websocket
var ws_proxy = new httpProxy.createProxyServer({
  target: {
    host: 'localhost',
    port: 3000
  }
});
server.on('upgrade', function (req, socket, head) {
  ws_proxy.ws(req, socket, head);
});

// Listen on 80
server.listen(80);

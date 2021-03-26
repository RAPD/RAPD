// Configuration
const config = require("./config");

// Redis
var Redis = require("ioredis");

// Connect to redis
try {
    var sub = new Redis(config.redis_connection);
  } catch (e) {
    console.error("Cannot connect to redis", config.redis_connection);
    throw e;
  }

// Handle new message passed from Redis
sub.on("message", function(channel, message) {
    console.log("sub channel " + channel);
    console.log(message);
});




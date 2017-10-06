## Running Services in Docker
Docker is the preferred way to run services for RAPD. This is just because it makes it a lot simpler for installation and cross-platform use.

#### MongDB with persistence
Make a directory to store data in (I have used `/Users/frankmurphy/workspace/data/mongo` on my Mac)  

```shell
run -d -p 27017:27017 --name mongo -v /Users/frankmurphy/workspace/data/mongo:/data/db mongo --storageEngine wiredTiger
```
To then connect to MongoDB in a shell, `docker run -it --link mongo:mongo --rm mongo sh -c 'exec mongo "$MONGO_PORT_27017_TCP_ADDR:$MONGO_PORT_27017_TCP_PORT/test"'`


#### Redis with persistence
```shell
docker run --name redis -d redis -p 6379:6379 redis-server --appendonly yes
```

#### REST and Websocket server
These run on port 3000 by default. Position yourself in the rest directory `cd rapd/src/services/rest`, copy the `example_config.js` to `config.js` and edit it. The example config has settings for MongoDB and Redis to work out of the box with the Docker environment described here.  
```javascript
module.exports = {
  // mongo or ldap
  authenticate_mode: 'mongo',
  // This will be the address cc'ed on admin emails
  admin_email:'fmurphy@anl.gov',
  // can be overidden by process.ENV
  port: 3000,
  // Name for the site
  site: 'NE-CAT',
  // Used for authentication key, etc
  secret: 'mysecret',
  // Connection string for MongoDB
  database: 'mongodb://mongo:27017/rapd',
  // Redis connection info
  redis_host: 'redis',
  redis_port: 6379,
  // Where is my LDAP server?
  ldap_server: '127.0.0.1',
  // String for LDAP to find your users
  ldap_dn: 'ou=People,dc=ser,dc=aps,dc=anl,dc=gov',
};
```
Build and run the application.
```shell

docker build -t rapd_rest .
docker run --name rapd_rest --link redis:redis --link mongo:mongo -p 3000:3000 rapd_rest
```
To test if the server is up, try curling `curl http://127.0.0.1:3000/api`. You should recieve `{"message":"Welcome to the RAPD api!"}`

#### Proxy server
Depending how you want to configure your client interface, a proxy server is handy to minimize ports you have to open, etc.

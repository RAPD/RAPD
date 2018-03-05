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

  // Connection strings for MongoDB
  control_conn: 'mongodb://mongo:27017/rapd',
  auth_conn: 'mongodb://mongo:27017/rapd',

  // Redis connection info
  redis_connection: {
      host: 'redis',
      port: 6379
    },

  // Where is my LDAP server? Used if authenticate_mode == 'ldap'
  ldap_server: '127.0.0.1',
  // String for LDAP to find your users
  ldap_dn: 'ou=People,dc=ser,dc=aps,dc=anl,dc=gov',

  // Plugin types that show up in the MongoDB
  plugin_types: ['index', 'integrate'],

  // ADXV executable
  adxv: '/usr/local/bin/adxv'
};

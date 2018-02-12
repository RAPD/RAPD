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
  control_conn: 'mongodb://mongo:27017/rapd',
  auth_conn: 'mongodb://mongo:27017/rapd',
  // Redis connection info
  // high availability
  redis_connection: {
      sentinels:[{host: '164.54.212.100', port:26379},
                 {host: '164.54.212.101', port:26379},
                 {host: '164.54.212.102', port:26379},
                 {host: '164.54.212.103', port:26379},
                 {host: '164.54.212.104', port:26379}],
      name: 'remote_master'
    },
  // regular
  redis_connection: {
      host: '164.54.212.100',
      port: 6379
    }
  // Where is my LDAP server?
  ldap_server: '127.0.0.1',
  // String for LDAP to find your users
  ldap_dn: 'ou=People,dc=ser,dc=aps,dc=anl,dc=gov',
  // Plugin types that show up in the MongoDB
  plugin_types: ['index', 'integrate']
};

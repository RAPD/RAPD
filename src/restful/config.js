module.exports = {
  admin_email:'fmurphy@anl.gov',
  authenticate_mode: 'mongo',  // mongo or ldap
  'port': 3000,  // can be overidden by process.ENV
  'site': 'NE-CAT',
  'secret': 'ilovescotchyscotch',
  'database': 'mongodb://127.0.0.1:27017/rapd',
  'ldap_server': '127.0.0.1',
  redis_host: '127.0.0.1', //'redis',
  redis_port: 6379,
};

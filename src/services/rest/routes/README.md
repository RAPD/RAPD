# Notes of interest when programming Routes

### req.decoded
req.decoded is an Object that looks like this:
{ role: 'site_admin',  
  groups: [ '59921becef080369c2f07cb3' ],  
  status: 'active',  
  loginAttempts: 0,  
  pass_expire: '2017-08-14T21:53:48.763Z',  
  pass_force_change: false,  
  timestamp: '2017-08-14T21:53:48.763Z',  
  __v: 1,  
  email: 'fmurphy@anl.gov',  
  group: null,  
  username: 'Frank Murphy',  
  _id: '59921becef080369c2f07cb2' }

var ldap = require('ldapjs');
var assert = require("assert");

var client = ldap.createClient({
  url: 'ldap://c191.ser.aps.anl.gov:389'
});

var opts = {
  scope: 'sub',
  filter: '(uidNumber=2905)'
}

client.search('dc=ser,dc=aps,dc=anl,dc=gov', opts, function(err, res) {

  assert.ifError(err);

  res.on('searchEntry', function(entry) {
    console.log('entry: ' + JSON.stringify(entry.object));
  });
  res.on('searchReference', function(referral) {
    console.log('referral: ' + referral.uris.join());
  });
  res.on('error', function(err) {
    console.error('error: ' + err.message);
  });
  res.on('end', function(result) {
    console.log('status: ' + result.status);
  });
});

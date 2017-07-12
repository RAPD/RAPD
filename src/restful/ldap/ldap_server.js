var fs = require('fs');
var ldap = require('ldapjs');
var spawn = require('child_process').spawn;



///--- Shared handlers

function authorize(req, res, next) {
  if (!req.connection.ldap.bindDN.equals('cn=root'))
    return next(new ldap.InsufficientAccessRightsError());

  return next();
}


function loadPasswdFile(req, res, next) {
  fs.readFile('/etc/passwd', 'utf8', function(err, data) {
    if (err)
      return next(new ldap.OperationsError(err.message));

    req.users = {};

    var lines = data.split('\n');
    for (var i = 0; i < lines.length; i++) {
      if (!lines[i] || /^#/.test(lines[i]))
        continue;

      var record = lines[i].split(':');
      if (!record || !record.length)
        continue;

      req.users[record[0]] = {
        dn: 'cn=' + record[0] + ', ou=users, o=myhost',
        attributes: {
          cn: record[0],
          uid: record[2],
          gid: record[3],
          description: record[4],
          homedirectory: record[5],
          shell: record[6] || '',
          objectclass: 'unixUser'
        }
      };
    }

    return next();
  });
}


var pre = [authorize, loadPasswdFile];



///--- Mainline

var server = ldap.createServer();

server.bind('cn=root', function(req, res, next) {
  if (req.dn.toString() !== 'cn=root' || req.credentials !== 'secret')
    return next(new ldap.InvalidCredentialsError());

  res.end();
  return next();
});


server.add('ou=users, o=myhost', pre, function(req, res, next) {
  if (!req.dn.rdns[0].cn)
    return next(new ldap.ConstraintViolationError('cn required'));

  if (req.users[req.dn.rdns[0].cn])
    return next(new ldap.EntryAlreadyExistsError(req.dn.toString()));

  var entry = req.toObject().attributes;

  if (entry.objectclass.indexOf('unixUser') === -1)
    return next(new ldap.ConstraintViolation('entry must be a unixUser'));

  var opts = ['-m'];
  if (entry.description) {
    opts.push('-c');
    opts.push(entry.description[0]);
  }
  if (entry.homedirectory) {
    opts.push('-d');
    opts.push(entry.homedirectory[0]);
  }
  if (entry.gid) {
    opts.push('-g');
    opts.push(entry.gid[0]);
  }
  if (entry.shell) {
    opts.push('-s');
    opts.push(entry.shell[0]);
  }
  if (entry.uid) {
    opts.push('-u');
    opts.push(entry.uid[0]);
  }
  opts.push(entry.cn[0]);
  var useradd = spawn('useradd', opts);

  var messages = [];

  useradd.stdout.on('data', function(data) {
    messages.push(data.toString());
  });
  useradd.stderr.on('data', function(data) {
    messages.push(data.toString());
  });

  useradd.on('exit', function(code) {
    if (code !== 0) {
      var msg = '' + code;
      if (messages.length)
        msg += ': ' + messages.join();
      return next(new ldap.OperationsError(msg));
    }

    res.end();
    return next();
  });
});


server.modify('ou=users, o=myhost', pre, function(req, res, next) {
  if (!req.dn.rdns[0].cn || !req.users[req.dn.rdns[0].cn])
    return next(new ldap.NoSuchObjectError(req.dn.toString()));

  if (!req.changes.length)
    return next(new ldap.ProtocolError('changes required'));

  var user = req.users[req.dn.rdns[0].cn].attributes;
  var mod;

  for (var i = 0; i < req.changes.length; i++) {
    mod = req.changes[i].modification;
    switch (req.changes[i].operation) {
    case 'replace':
      if (mod.type !== 'userpassword' || !mod.vals || !mod.vals.length)
        return next(new ldap.UnwillingToPerformError('only password updates ' +
                                                     'allowed'));
      break;
    case 'add':
    case 'delete':
      return next(new ldap.UnwillingToPerformError('only replace allowed'));
    }
  }

  var passwd = spawn('chpasswd', ['-c', 'MD5']);
  passwd.stdin.end(user.cn + ':' + mod.vals[0], 'utf8');

  passwd.on('exit', function(code) {
    if (code !== 0)
      return next(new ldap.OperationsError('' + code));

    res.end();
    return next();
  });
});


server.del('ou=users, o=myhost', pre, function(req, res, next) {
  if (!req.dn.rdns[0].cn || !req.users[req.dn.rdns[0].cn])
    return next(new ldap.NoSuchObjectError(req.dn.toString()));

  var userdel = spawn('userdel', ['-f', req.dn.rdns[0].cn]);

  var messages = [];
  userdel.stdout.on('data', function(data) {
    messages.push(data.toString());
  });
  userdel.stderr.on('data', function(data) {
    messages.push(data.toString());
  });

  userdel.on('exit', function(code) {
    if (code !== 0) {
      var msg = '' + code;
      if (messages.length)
        msg += ': ' + messages.join();
      return next(new ldap.OperationsError(msg));
    }

    res.end();
    return next();
  });
});


server.search('o=myhost', pre, function(req, res, next) {
  Object.keys(req.users).forEach(function(k) {
    if (req.filter.matches(req.users[k].attributes))
      res.send(req.users[k]);
  });

  res.end();
  return next();
});



// LDAP "standard" listens on 389, but whatever.
server.listen(1389, '127.0.0.1', function() {
  console.log('/etc/passwd LDAP server up at: %s', server.url);
});

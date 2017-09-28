var mongoose = require('mongoose');
var Schema = mongoose.Schema;
var bcrypt = require('bcryptjs');

var UserSchema = new Schema({
  username: {
    type: String,
    required: true
  },
  password: {
    type: String,
    required: false
  },
  role: {
    type: String,
    required: true,
    default: 'user'
  },
  groups: [{
    type: Schema.Types.ObjectId,
    ref: 'Group',
    default: []
  }],
  email: {
    type: String,
    required: true
  },
  status: {
    type: String,
    required: true,
    default: 'active'
  },
  loginAttempts: {
    type: Number,
    required: true,
    default: 0
  },
  lockUntil: {
    type: Date,
  },
  pass_expire: {
    type: Date,
    default:Date.now
  },
  pass_force_change: {
    type: Boolean,
    default: false
  },
  timestamp: {
    type: Date,
    default: Date.now
  },
}, {strict:false});

// How much work for hashing
var SALT_WORK_FACTOR = 10;

// max of 5 attempts, resulting in a 2 hour lock
var MAX_LOGIN_ATTEMPTS = 5;
var LOCK_TIME = 2 * 60 * 60 * 1000;

// expose enum on the model
UserSchema.statics.failedLogin = {
    NOT_FOUND: 0,
    PASSWORD_INCORRECT: 1,
    MAX_ATTEMPTS: 2
};

// Handle password hashing a la
// http://devsmash.com/blog/password-authentication-with-mongoose-and-bcrypt

UserSchema.virtual('isLocked').get(function() {
    // check for a future lockUntil timestamp
    return !!(this.lockUntil && this.lockUntil > Date.now());
});

UserSchema.pre('save', function(next) {
    var user = this;

    // only hash the password if it has been modified (or is new)
    if (!user.isModified('password')) return next();

    // generate a salt
    bcrypt.genSalt(SALT_WORK_FACTOR, function(err, salt) {
        if (err) return next(err);

        // hash the password along with our new salt
        bcrypt.hash(user.password, salt, function(err, hash) {
            if (err) return next(err);

            // override the cleartext password with the hashed one
            user.password = hash;
            next();
        });
    });
});

UserSchema.methods.comparePassword = function(candidatePassword, cb) {
    console.log('comparePassword', this.password);
    bcrypt.compare(candidatePassword, this.password, function(err, isMatch) {
        if (err) return cb(err);
        cb(null, isMatch);
    });
};

UserSchema.methods.incLoginAttempts = function(cb) {
    // if we have a previous lock that has expired, restart at 1
    if (this.lockUntil && this.lockUntil < Date.now()) {
        return this.update({
            $set: { loginAttempts: 1 },
            $unset: { lockUntil: 1 }
        }, cb);
    }
    // otherwise we're incrementing
    var updates = { $inc: { loginAttempts: 1 } };
    // lock the account if we've reached max attempts and it's not locked already
    if (this.loginAttempts + 1 >= MAX_LOGIN_ATTEMPTS && !this.isLocked) {
        updates.$set = { lockUntil: Date.now() + LOCK_TIME };
    }
    return this.update(updates, cb);
};

// expose enum on the model, and provide an internal convenience reference
var reasons = UserSchema.statics.failedLogin = {
    NOT_FOUND: 0,
    PASSWORD_INCORRECT: 1,
    MAX_ATTEMPTS: 2
};

UserSchema.statics.getAuthenticated = function(email, password, cb) {

  console.log('getAuthenticated', email, password);

  this.findOne({email:email}).
       populate('groups', 'groupname').
       exec(function(err, user) {

         console.log(err, user);

         if (err) {
           console.log(err);
           return cb(err);
         }

         // make sure the user exists
         if (!user) {
           console.log('Nonuser');
           return cb(null, null, reasons.NOT_FOUND);
         }

         // check if the account is currently locked
         if (user.isLocked) {
           // just increment login attempts if account is already locked
           return user.incLoginAttempts(function(err) {
             if (err) return cb(err);
             return cb(null, null, reasons.MAX_ATTEMPTS);
           });
         }

         // Test for a matching password
         user.comparePassword(password, function(err, isMatch) {
           if (err) return cb(err);

           // check if the password was a match
           if (isMatch) {
             console.log('match');
             // Remove the password from the returned
             user.password = undefined;
             // if there's no lock or failed attempts, just return the user
             if (!user.loginAttempts && !user.lockUntil) {
               return cb(null, user);
             }
             // reset attempts and lock info
             var updates = {
               $set: { loginAttempts: 0 },
               $unset: { lockUntil: 1 }
             };
             return user.update(updates, function(err) {
               if (err) return cb(err);
               return cb(null, user);
             });
           }

           console.log('Not a match');

           // password is incorrect, so increment login attempts before responding
           user.incLoginAttempts(function(err) {
             if (err) {
               return cb(err);
             }
             return cb(null, null, reasons.PASSWORD_INCORRECT);
           });
         });
       });
};

module.exports = mongoose.model('User', UserSchema);

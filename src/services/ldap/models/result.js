var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var ResultSchema   = new Schema({}, {strict:false});

module.exports = mongoose.model('Results', ResultSchema);

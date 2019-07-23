var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var PdbSchema = new Schema({
      description: {
        type: String,
        required: false
      },
      filename: {
        type: String,
        required: true
      },
      group: {
        type: Schema.Types.ObjectId,
        ref: 'Group',
        required: false,
      },
      originalname: {
        type: String,
        required: true
      },
      path: {
        type: String,
        required: true
      },
      session: {
        type: Schema.Types.ObjectId,
        ref: 'Session',
        required: false,
      },
      uploaded: {
        type: Date,
        required: true,
        default: Date.now
      },
      uploader: {
        type: Schema.Types.ObjectId,
        ref: 'User',
        required: true,
      },
}, {strict:false})

exports.Pdb = mongoose.model('Pdb', PdbSchema);
exports.PdbSchema = PdbSchema;

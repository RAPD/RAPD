var mongoose = require("mongoose");
var Schema = mongoose.Schema;
var ProjectActionSchema = new Schema(
  {
    action_type: {
      type: String,
      required: true
    },
    timestamp: {
      type: Date,
      default: Date.now
    },
    user: {
      type: Schema.Types.ObjectId,
      ref: "User",
      required: false
    }
  },
  { strict: false }
);

exports.ProjectAction = mongoose.model("ProjectAction", ProjectActionSchema);
exports.ProjectActionSchema = ProjectActionSchema;

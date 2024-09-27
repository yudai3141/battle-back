const mongoose = require('mongoose');

const DebateRoundSchema = new mongoose.Schema({
  battleId: { type: mongoose.Schema.Types.ObjectId, ref: 'Battle', required: true },
  roundNumber: { type: Number, required: true },
  speakerId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  content: { type: String, required: true },
  createdAt: { type: Date, default: Date.now },
});

module.exports = mongoose.model('DebateRound', DebateRoundSchema);
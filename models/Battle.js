// models/Battle.js

const mongoose = require('mongoose');

const BattleSchema = new mongoose.Schema({
  postId: { type: mongoose.Schema.Types.ObjectId, ref: 'Post', required: true },
  initiatorId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  opponentId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  rounds: [{ type: mongoose.Schema.Types.ObjectId, ref: 'DebateRound' }], // ラウンドの参照
  currentRound: { type: Number, default: 1 },
  isFinished: { type: Boolean, default: false },
  winnerId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  surrendered: { type: Boolean, default: false },
  createdAt: { type: Date, default: Date.now },
});

module.exports = mongoose.model('Battle', BattleSchema);
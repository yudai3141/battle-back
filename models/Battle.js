// models/Battle.js

const mongoose = require('mongoose');

const BattleSchema = new mongoose.Schema({
  postId: { type: mongoose.Schema.Types.ObjectId, ref: 'Post', required: true },
  initiatorId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  opponentId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  rounds: [{ type: mongoose.Schema.Types.ObjectId, ref: 'DebateRound' }], // ラウンドの参照
  currentRound: { type: Number, default: 1 },
  isFinished: { type: Boolean, default: false },
  isresult: { type: Boolean, default: false },
  winnerId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  surrendered: { type: Boolean, default: false },
  createdAt: { type: Date, default: Date.now },
  reason: {
    winnerId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },  // 勝者のID
    winnerUsername: { type: String },  // 勝者のユーザー名
    loserId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },  // 敗者のID
    loserUsername: { type: String },  // 敗者のユーザー名
    reason: { type: String },  // 勝敗の理由
    pel: { type: String, enum: ['0', '1', '2'], default: '0' },  // 違反があったかどうか（0:なし, 1:あり）
    parent_post: { type: mongoose.Schema.Types.Mixed },  // バトルの起点となった投稿情報（オブジェクトとして保存）
    parent_post_key: { type: mongoose.Schema.Types.ObjectId },  // 親投稿のID
    start_post: { type: mongoose.Schema.Types.Mixed },  // バトルの開始時の投稿情報
    start_post_key: { type: mongoose.Schema.Types.ObjectId },  // 開始時の投稿ID
  },
});

module.exports = mongoose.model('Battle', BattleSchema);
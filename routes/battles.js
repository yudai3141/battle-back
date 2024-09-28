const router = require('express').Router();
const Battle = require('../models/Battle');
const DebateRound = require('../models/DebateRound');
const User = require('../models/User');
const Post = require('../models/Post');
const { spawn } = require('child_process');

// バトル一覧を取得する
router.get('/', async (req, res) => {
  try {
    const battles = await Battle.find()
      .populate('initiatorId', 'username')
      .populate('opponentId', 'username');
    // ユーザー名を取得
    const battlesWithUsernames = battles.map((battle) => ({
      ...battle._doc,
      initiatorUsername: battle.initiatorId.username,
      opponentUsername: battle.opponentId.username,
    }));
    res.status(200).json(battlesWithUsernames);
  } catch (err) {
    res.status(500).json(err);
  }
});

// 特定のバトルを取得する
router.get('/:battleId', async (req, res) => {
  try {
    const battle = await Battle.findById(req.params.battleId)
      .populate('initiatorId', 'username')
      .populate('opponentId', 'username')
      .populate({
        path: 'rounds',
        populate: { path: 'speakerId', select: 'username' },
      });
    res.status(200).json(battle);
  } catch (err) {
    res.status(500).json(err);
  }
});

// バトルのラウンドを取得する
router.get('/:battleId/rounds', async (req, res) => {
  try {
    const rounds = await DebateRound.find({ battleId: req.params.battleId })
      .sort('roundNumber')
      .populate('speakerId', 'username');
    res.status(200).json(rounds);
  } catch (err) {
    res.status(500).json(err);
  }
});

// レスバトルを開始する（主張を受け取る）
router.post('/', async (req, res) => {
  try {
    const { postId, initiatorId, opponentId, content } = req.body;

    // バトルを作成
    const newBattle = new Battle({
      postId,
      initiatorId,
      opponentId,
    });

    const savedBattle = await newBattle.save();

    // 第1ラウンドを作成
    const firstRound = new DebateRound({
      battleId: savedBattle._id,
      roundNumber: 1,
      speakerId: initiatorId,
      content,
    });

    await firstRound.save();

    // バトルにラウンドを追加
    savedBattle.rounds.push(firstRound._id);
    savedBattle.currentRound += 1;
    await savedBattle.save();

    res.status(200).json(savedBattle);
  } catch (err) {
    res.status(500).json(err);
  }
});

// 新しいラウンドを追加する
router.post('/:battleId/round', async (req, res) => {
    try {
      const { battleId } = req.params;
      const { speakerId, content } = req.body;
  
      const battle = await Battle.findById(battleId);
  
      if (battle.isFinished) {
        return res.status(400).json('このバトルは既に終了しています。');
      }
  
      // ターンの確認
      const isInitiatorTurn = battle.rounds.length % 2 === 0; // 0から始まるので奇数偶数が逆
      if (isInitiatorTurn && speakerId !== battle.initiatorId.toString()) {
        return res.status(400).json('あなたのターンではありません。');
      }
      if (!isInitiatorTurn && speakerId !== battle.opponentId.toString()) {
        return res.status(400).json('あなたのターンではありません。');
      }
  
      // 新しいラウンドを作成
      const newRound = new DebateRound({
        battleId,
        roundNumber: battle.rounds.length + 1,
        speakerId,
        content,
      });
  
      await newRound.save();
  
      // バトルを更新
      battle.rounds.push(newRound._id);
      battle.currentRound += 1;
  
      // 5ラウンドに達したらバトルを終了
      if (battle.currentRound > 5) {
        battle.isFinished = true;
      }
  
      await battle.save();
  
      res.status(200).json(battle);
    } catch (err) {
      res.status(500).json(err);
    }
  });

// バトルで降参する
router.post('/:battleId/surrender', async (req, res) => {
  try {
    const { battleId } = req.params;
    const { userId } = req.body;

    const battle = await Battle.findById(battleId);

    if (battle.isFinished) {
      return res.status(400).json('This battle has already finished.');
    }

    battle.isFinished = true;
    battle.winnerId = battle.initiatorId.equals(userId) ? battle.opponentId : battle.initiatorId;
    battle.surrendered = true;

    await battle.save();

    // 勝敗が決まったのでレートを更新
    await updateEloRating(battle.winnerId, userId);

    res.status(200).json(battle);
  } catch (err) {
    res.status(500).json(err);
  }
});

// バトルの終了時に勝者を決定し、レートを更新する
router.post('/:battleId/finish', async (req, res) => {
  try {
    const { battleId } = req.params;
    const { winnerId } = req.body;

    const battle = await Battle.findById(battleId);

    if (battle.isFinished) {
      return res.status(400).json('This battle has already finished.');
    }

    battle.isFinished = true;
    battle.winnerId = winnerId;

    await battle.save();

    // 敗者のIDを取得
    const loserId = battle.initiatorId.equals(winnerId)
      ? battle.opponentId
      : battle.initiatorId;

    // レートを更新
    await updateEloRating(winnerId, loserId);

    res.status(200).json(battle);
  } catch (err) {
    res.status(500).json(err);
  }
});

// バトル結果を処理するエンドポイント
router.get('/:battleId/process', async (req, res) => {
  try {
    const { battleId } = req.params;

    // バトル情報を取得
    const battle = await Battle.findById(battleId)
      .populate('initiatorId', 'username profilePicture')
      .populate('opponentId', 'username profilePicture')
      .populate({
        path: 'rounds',
        populate: { path: 'speakerId', select: 'username' },
      });

    // 元の投稿を取得
    const post = await Post.findById(battle.postId);

    // Pythonスクリプトを実行し、データを渡す
    const pythonProcess = spawn('python3', ['process_battle.py']);

    // Pythonスクリプトにデータを送信
    pythonProcess.stdin.write(JSON.stringify({ battle, post }));
    pythonProcess.stdin.end();

    let pythonOutput = '';
    pythonProcess.stdout.on('data', (data) => {
      pythonOutput += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`stderr: ${data}`);
    });

    pythonProcess.on('close', async (code) => {
      console.log(`Python script exited with code ${code}`);

      // 出力をパース
      const result = JSON.parse(pythonOutput);

      // 勝者情報がある場合、バトル情報を更新し、Eloレートを更新
      if (result.winnerId) {
        battle.winnerId = result.winnerId;
        battle.isFinished = true;
        await battle.save();

        // Eloレートを更新
        await updateEloRating(result.winnerId, result.loserId);

        // 勝者と敗者の情報を取得
        const winner = await User.findById(result.winnerId);
        const loser = await User.findById(result.loserId);

        // 結果にプロフィール画像を追加
        result.winnerProfilePicture = winner.profilePicture;
        result.loserProfilePicture = loser.profilePicture;
      }

      // 結果をフロントエンドに返す
      res.status(200).json(result);
    });
  } catch (err) {
    console.error(err);
    res.status(500).json(err);
  }
});

// Eloレートを更新する関数
const updateEloRating = async (winnerId, loserId) => {
  const K = 32; // 定数K

  const winner = await User.findById(winnerId);
  const loser = await User.findById(loserId);

  // 期待勝率の計算
  const expectedScoreWinner = 1 / (1 + Math.pow(10, (loser.eloRating - winner.eloRating) / 400));
  const expectedScoreLoser = 1 / (1 + Math.pow(10, (winner.eloRating - loser.eloRating) / 400));

  // レートの更新
  winner.eloRating = Math.round(winner.eloRating + K * (1 - expectedScoreWinner));
  loser.eloRating = Math.round(loser.eloRating + K * (0 - expectedScoreLoser));

  await winner.save();
  await loser.save();
};


module.exports = router;
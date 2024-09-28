import sys
import json

def main():
    # 標準入力からデータを受け取る
    input_data = sys.stdin.read()
    data = json.loads(input_data)

    battle = data['battle']
    post = data['post']

    # 必要な情報を抽出
    rounds = battle['rounds']
    initiator = battle['initiatorId']
    opponent = battle['opponentId']

    # 勝者を決定するロジック（ここでは単純な例として、文字数で比較）
    initiator_score = 0
    opponent_score = 0

    for round_info in rounds:
        speaker = round_info['speakerId']
        content = round_info['content']
        content_length = len(content)

        if speaker['_id'] == initiator['_id']:
            initiator_score += content_length
        elif speaker['_id'] == opponent['_id']:
            opponent_score += content_length

    # 勝者の決定
    if initiator_score > opponent_score:
        winner = initiator
        loser = opponent
        reason = "発起人の発言がより長く、説得力がありました。"
    elif opponent_score > initiator_score:
        winner = opponent
        loser = initiator
        reason = "対戦相手の発言がより長く、説得力がありました。"
    else:
        winner = None
        loser = None
        reason = "引き分けです。"

    # 結果データを作成
    result = {
        'winnerId': winner['_id'] if winner else None,
        'winnerUsername': winner['username'] if winner else None,
        'loserId': loser['_id'] if loser else None,
        'loserUsername': loser['username'] if loser else None,
        'reason': reason
    }

    # 結果をJSONとして出力
    print(json.dumps(result))

if __name__ == "__main__":
    main()
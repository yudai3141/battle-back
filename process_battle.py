import sys
import json

def main():
    # 標準入力からデータを受け取る
    input_data = sys.stdin.read()
    data = json.loads(input_data)

    battle = data['battle']
    post = data['post']

    # デバッグ用にデータを表示
    print("Received Battle Data:")
    print(json.dumps(battle, indent=2, ensure_ascii=False))

    print("\nReceived Post Data:")
    print(json.dumps(post, indent=2, ensure_ascii=False))

    # ここでデータの処理を行う（サンプルコードなので省略）

    # 処理結果を出力
    print("\nProcessing complete. Results are ready.")

if __name__ == "__main__":
    main()
import sys
import json
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage  
import os
from dotenv import load_dotenv
import json  # JSONを整形して出力するためにインポート
import re
import os
import base64
from PIL import Image
import io
from openai import AzureOpenAI

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
    cur_node = post['parentPostId']
    while cur_node:#ポストに大元が入る
        post = cur_node
        cur_node = post['parentPostId']
        
    img_fl = 0
    desc_fl = 0
    if post.get('desc'):
        Pdesc = post['desc']
        desc_fl = 1

    if post.get('img'):
        Pimg = post['img']
        img_fl = 1
    
    
    
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    serpapi_api_key = os.getenv("Serp_API_KEY")
    url = os.getenv("REACT_APP_PUBLIC_FOLDER")
    
    chat = ChatOpenAI(
    temperature=0,  # Reduce response randomness
    model="gpt-4",
    openai_api_key=openai_api_key
    )
    
    tools = load_tools(
    ["serpapi","requests_all"],  # Use SerpAPI for Google searches
    llm = chat,
    serpapi_api_key = serpapi_api_key,
    allow_dangerous_tools=True  # Allow potentially dangerous tools
    )
    
    agent = create_react_agent(
    tools=tools,
    model=chat,
    )
    
    client = AzureOpenAI(
    azure_endpoint = "https://e-zuka.openai.azure.com/", # 生成したリソースのエンドポイントです
    api_version = "2023-12-01-preview", # https://learn.microsoft.com/en-us/azure/ai-services/openai/reference を参照してバージョンを指定
    api_key = "ca8f471c510a4bf3ac870daaf80f467f" # 生成したリソースのキーです
    )
    
    def create_image_data(image_path):
        """
        画像をBase64エンコードし、APIリクエスト用のデータを作成します。

        Args:
            image_path (str): 画像ファイルのパス

        Returns:
            dict: 画像データの辞書
        """
        public_dir = "./public/images"
        full_path = os.path.join(public_dir, image_path)

        try:
            with Image.open(full_path) as img:
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                base64_string = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                return {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_string}",
                        "detail": "high"
                    }
                }
                
        except OSError as e:
            print(f"画像の読み込みに失敗しました: {image_path}, {e}")
            return None

    def get_image_analysis(client, image_files, prompt):
        """
        Azure OpenAI APIを使用して、画像を分析します。

        Args:
            client (AzureOpenAI): Azure OpenAIのクライアント
            image_files (list): 画像データのリスト
            prompt (str): 分析に関するプロンプト

        Returns:
            str: 分析結果
        """

        request_messages = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                }
            ] + image_files
        }

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[request_messages],
            max_tokens=1000
        )
        return response.choices[0].message.content


    if img_fl == 1:
        image_files = []
        image_data = create_image_data(Pimg)
        if image_data:
            image_files.append(image_data)
            prompt = "画像について詳細に説明してください"
            img_tx = get_image_analysis(client, image_files, prompt)
    
    
    def serialize_message_object(obj):
        if isinstance(obj, (HumanMessage, AIMessage, ToolMessage)):
            return {
                "content": obj.content,
                "additional_kwargs": obj.additional_kwargs,
                "response_metadata": obj.response_metadata
            }
        elif isinstance(obj, dict):
            return {k: serialize_message_object(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [serialize_message_object(i) for i in obj]
        return obj

    def analyze_conversation(conversation):
        # print("Starting conversation analysis...")
        
        if img_fl == 0 :
            # Use agent to process the conversation and determine key claims
            result = agent.invoke({
                "messages": [
                    HumanMessage(content=f"""
                    以下のポストとそれに関する会話の内容を解析し、それぞれの主張に対して客観的な情報を用いてその正当性を確かめ、
                    勝者を決定し、以下のフォーマットで出力してください。必要に応じてGoogle検索を使用してください。
                    会話内に明らかに他者に対しての誹謗中傷が含まれている場合その時点で誹謗中傷を行った人を負けにし、回答フォーマットの'penalty'の欄を1としてください
                    
                    回答フォーマット
                    WinnerID: (ID), reason: (勝敗の理由を会話に使われている言語と同じもので記述),penalty: (1or0,誹謗中傷を行った者がいた場合1を立てる。デフォルトは0)
                    
                    また会話は以下のように記述します.
                    (例)
                    会話: (user1id):(user1の発言). (user2id):(user2の発言). (user1id):(user1の発言). (user2id):(user2の発言). (user1id):(user1の発言) 
                    
                    ポスト: {Pdesc}
                    会話:{conversation}
                    """)
                ]
            })
        elif desc_fl == 0:
            result = agent.invoke({
                "messages": [
                    HumanMessage(content=f"""
                    以下のポストとそれに関する会話の内容を解析し、それぞれの主張に対して客観的な情報を用いてその正当性を確かめ、
                    勝者を決定し、以下のフォーマットで出力してください。必要に応じてGoogle検索を使用してください。
                    会話内に明らかに他者に対しての誹謗中傷が含まれている場合その時点で誹謗中傷を行った人を負けにしてください。
                    
                    回答フォーマット
                    WinnerID: (ID), reason: (勝敗の理由を会話に使われている言語と同じもので記述),penalty: (1or0,誹謗中傷を行った者がいた場合1を立てる。デフォルトは0)
                    
                    また会話は以下のように記述します.
                    (例)
                    会話: (user1id):(user1の発言). (user2id):(user2の発言). (user1id):(user1の発言). (user2id):(user2の発言). (user1id):(user1の発言) 
                    
                    ポスト:(image) {img_tx}
                    
                    会話:{conversation}
                    """)
                ]
            })
        else:
            result = agent.invoke({
                "messages": [
                    HumanMessage(content=f"""
                    以下のポストとそれに関する会話の内容を解析し、それぞれの主張に対して客観的な情報を用いてその正当性を確かめ、
                    勝者を決定し、以下のフォーマットで出力してください。必要に応じてGoogle検索を使用してください。
                    会話内に明らかに他者に対しての誹謗中傷が含まれている場合その時点で誹謗中傷を行った人を負けにしてください。
                    
                    回答フォーマット
                    WinnerID: (ID), reason: (勝敗の理由を会話に使われている言語と同じもので記述),penalty: (1or0,誹謗中傷を行った者がいた場合1を立てる。デフォルトは0)
                    
                    また会話は以下のように記述します.
                    (例)
                    会話: (user1id):(user1の発言). (user2id):(user2の発言). (user1id):(user1の発言). (user2id):(user2の発言). (user1id):(user1の発言) 
                    
                    ポスト:(image) {img_tx}, (text) {Pdesc}
                    
                    会話:{conversation}
                    """)
                ]
            })

        # Serialize the result for easier display
        serialized_result = serialize_message_object(result)
        # print("Result of analysis:")
        # print(json.dumps(serialized_result, indent=2, ensure_ascii=False))

        # Extract and return the winner's message
        winner_info = result['messages'][-1].content  # Last AI message
        # print(f"Winner determined:\n{winner_info}")
        return winner_info

    conver_arr = []
    conversation = " "
    
    for round_info in rounds:
        speaker = round_info['speakerId']
        content = round_info['content']
        conver = f"{speaker}:{content}. "
        conver_arr.append(conver)
    
    for arr in conver_arr:
        conversation = conversation + arr
        
    # Analyze the conversation and determine the winner
    winner = analyze_conversation(conversation)
    # 正規表現パターン
    pattern = r"WinnerID: (\w+), reason: (.+), penalty: (0|1)"

    # 正規表現でマッチング
    match = re.search(pattern, winner)
    
    userid = ""
    reason = ""
    penalty = 0 

    if match:
        userid = match.group(1)
        reason = match.group(2)
        penalty = int(match.group(3))
    # else:
    #     print("マッチするパターンが見つかりませんでした")
        
    # 結果データを作成
    # result = {
    #     'winnerId': winner['_id'] if winner else None,
    #     'winnerUsername': winner['username'] if winner else None,
    #     'loserId': loser['_id'] if loser else None,
    #     'loserUsername': loser['username'] if loser else None,
    #     'reason': reason
    # }
    if userid == initiator['_id']:#レスバトル開始者が勝者
        winner = initiator
        loser = opponent
    else:
        winner = opponent
        loser = initiator
        
    result = {
        'winnerId': winner['_id'],
        'winnerUsername': winner['username'],
        'loserId': loser['_id'],
        'loserUsername': loser['username'],
        'reason': reason,
        'pel': penalty #違反が合ったかどうか
    }

    # 結果をJSONとして出力
    print(json.dumps(result))

if __name__ == "__main__":
    main()
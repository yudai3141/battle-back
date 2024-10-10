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
import http.client
import uuid

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
    start_1 = post
    while cur_node:#ポストに大元が入る
        post = cur_node
        cur_node = post['parentPostId']
        
    img_fl = 0
    desc_fl = 0
    if start_1.get('desc'):
        Pdesc = start_1['desc']
        desc_fl = 1

    if start_1.get('img'):
        Pimg = start_1['img']
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
            model="gpt-3.5-turbo",
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
    
    def check_ai_generated(text):
        conn = http.client.HTTPSConnection("api.copyleaks.com")

        # スキャンIDとテキストを指定
        payload = json.dumps({
            "text": text,
            "language": "ja"  # 日本語で解析することを指定
        })

        headers = {
            'Authorization': "Bearer 20FB77D32A196F35CE85599B7B930DBBEECAC86ED14F29C33B5CB9EC6F53B059", #有効期限あり
            'Content-Type': "application/json",
            'Accept': "application/json"
        }

        # スキャンIDを指定し、リクエストを送信
        scan_id = str(uuid.uuid4())
        conn.request("POST", f"/v2/writer-detector/{scan_id}/check", payload.encode('utf-8'), headers)

        res = conn.getresponse()
        data = res.read()
        result = json.loads(data.decode("utf-8"))
        if 'summary' in result:
            ai_probability = result['summary']['ai']
            return ai_probability
        else:
            return None

    def analyze_conversation(conversation):
        # print("Starting conversation analysis...")
        
        if img_fl == 0 :
            # Use agent to process the conversation and determine key claims
            result = agent.invoke({
                "messages": [
                    HumanMessage(content=f"""
                    以下のポストとそれに関する会話の内容を解析し、それぞれの主張に対して客観的な情報を用いてその正当性を確かめ、勝者を決定してください。必要に応じて**serpapi**を用いたGoogle検索を使用して情報を収集してください。
                    
                    **特記事項**:
                    - 会話内に明らかに他者に対する誹謗中傷が含まれている場合、その発言を行ったユーザーを自動的に敗者とします。
                    - 必ず勝者を決定してください。
                    - **ポストの内容は user2 の発言として扱い、解析・判定に考慮してください。**
                    - 出力は必ず以下のフォーマットに従ってください。このフォーマット以外の出力は行わないでください。
                    
                    **会話の記述方法**:
                    (user1情報):(user1の発言). (user2情報):(user2発言). (user1情報):(user1の発言). (user2情報):(user2の発言). (user1の情報):(user1の発言).
                    
                    **ポスト**:
                    {Pdesc}
                    ※ ポストは user2 の発言とみなされます。
                    
                    **会話**:
                    {conversation}
                    
                    **出力フォーマット**:
                    勝者: (ID), 理由: (勝敗の理由を記載), 反則:(0or1or2, 誹謗中傷を行ったものがいた場合1を立てる。両者誹謗中傷を行った場合2を立てる。デフォルトは0)
                    
                    **例**:
                    勝者: 66f968dd42a67231aeab721d, 理由: yuの主張は現実的であり、今すぐに対応が必要な問題に対して即効性のある解決策を支持している。一方で、aoの提案する根本的な問題解決は重要だが、それが実現するまでの間に必要な安全策（女性専用車両）を無視することは、現状でリスクが大きいと考えられる。また、監視カメラ案の実効性や即効性に対する限界が明確に指摘されたため、yuの最終反論がより強力であると判断される。, 反則: 0
                    """)
                ]
            })
        elif desc_fl == 0:
            result = agent.invoke({
                "messages": [
                    HumanMessage(content=f"""
                    以下のポストとそれに関する会話の内容を解析し、それぞれの主張に対して客観的な情報を用いてその正当性を確かめ、勝者を決定してください。必要に応じて**serpapi**を用いたGoogle検索を使用して情報を収集してください。
                    
                    **特記事項**:
                    - 会話内に明らかに他者に対する誹謗中傷が含まれている場合、その発言を行ったユーザーを自動的に敗者とします。
                    - 必ず勝者を決定してください。
                    - **ポストの内容は user2 の発言として扱い、解析・判定に考慮してください。**
                    - 出力は必ず以下のフォーマットに従ってください。このフォーマット以外の出力は行わないでください。
                    
                    **会話の記述方法**:
                    (user1情報):(user1の発言). (user2情報):(user2発言). (user1情報):(user1の発言). (user2情報):(user2の発言). (user1の情報):(user1の発言).
                    
                    **ポスト**:
                    -画像: {img_tx}
                    ※ ポストは user2 の発言とみなされます。
                    
                    **会話**:
                    {conversation}
                    
                    **出力フォーマット**:
                    勝者: (ID), 理由: (勝敗の理由を記載), 反則:(0or1or2, 誹謗中傷を行ったものがいた場合1を立てる。両者誹謗中傷を行った場合2を立てる。デフォルトは0)
                    
                    **例**:
                        勝者: 66f968dd42a67231aeab721d, 理由: yuの主張は現実的であり、今すぐに対応が必要な問題に対して即効性のある解決策を支持している。一方で、aoの提案する根本的な問題解決は重要だが、それが実現するまでの間に必要な安全策（女性専用車両）を無視することは、現状でリスクが大きいと考えられる。また、監視カメラ案の実効性や即効性に対する限界が明確に指摘されたため、yuの最終反論がより強力であると判断される。, 反則: 0
                    """)
                ]
            })
        else:
            result = agent.invoke({
                "messages": [
                    HumanMessage(content=f"""
                    以下のポストとそれに関する会話の内容を解析し、それぞれの主張に対して客観的な情報を用いてその正当性を確かめ、勝者を決定してください。必要に応じて**serpapi**を用いたGoogle検索を使用して情報を収集してください。
                    
                    **特記事項**:
                    - 会話内に明らかに他者に対する誹謗中傷が含まれている場合、その発言を行ったユーザーを自動的に敗者とします。
                    - 必ず勝者を決定してください。
                    - **ポストの内容は user2 の発言として扱い、解析・判定に考慮してください。**
                    - 出力は必ず以下のフォーマットに従ってください。このフォーマット以外の出力は行わないでください。
                    
                    **会話の記述方法**:
                    (user1情報):(user1の発言). (user2情報):(user2発言). (user1情報):(user1の発言). (user2情報):(user2の発言). (user1の情報):(user1の発言).
                    
                    **ポスト**:
                    - テキスト:{Pdesc}
                    _ 画像: {img_tx}
                    ※ ポストは user2 の発言とみなされます。
                    
                    **会話**:
                    {conversation}
                    
                    **出力フォーマット**:
                    勝者: (ID), 理由: (勝敗の理由を記載), 反則:(0or1or2, 誹謗中傷を行ったものがいた場合1を立てる。両者誹謗中傷を行った場合2を立てる。デフォルトは0)
                    
                    **例**:
                    勝者: 66f968dd42a67231aeab721d, 理由: yuの主張は現実的であり、今すぐに対応が必要な問題に対して即効性のある解決策を支持している。一方で、aoの提案する根本的な問題解決は重要だが、それが実現するまでの間に必要な安全策（女性専用車両）を無視することは、現状でリスクが大きいと考えられる。また、監視カメラ案の実効性や即効性に対する限界が明確に指摘されたため、yuの最終反論がより強力であると判断される。, 反則: 0
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


    # ユーザーの発言をまとめる
    user1_text = ""
    user2_text = ""

    for round_info in rounds:
        speaker = round_info['speakerId']
        content = round_info['content']
        if speaker['_id'] == initiator['_id']:
            user1_text += content + " "
        elif speaker['_id'] == opponent['_id']:
            user2_text += content + " "

    # ポストの内容をuser2の発言として追加
    if desc_fl == 1:
        user2_text += Pdesc + " "

    # AI生成確率をチェック
    user1_ai_prob = check_ai_generated(user1_text)
    user2_ai_prob = check_ai_generated(user2_text)

    # 必要に応じて反則を適用
    # foul = 0
    # winner = None
    # loser = None
    # reason = ""

    # ユーザー1のAI生成確率を判定
    if (user1_ai_prob is not None and user1_ai_prob > 0.9):
        winner = opponent
        loser = initiator
        foul = 1
        reason = f"{loser['username']}の発言がAIによって生成されたと判定されたため、{winner['username']}の勝利です。"

    # ユーザー2のAI生成確率を判定
    elif (user2_ai_prob is not None and user2_ai_prob > 0.9):
        winner = initiator
        loser = opponent
        foul = 1
        reason = f"{loser['username']}の発言がAIによって生成されたと判定されたため、{winner['username']}の勝利です。"

    # ユーザー1のAI生成確率がNoneで、ユーザー2が0.9以上の場合
    elif (user1_ai_prob is None and user2_ai_prob is not None and user2_ai_prob > 0.9):
        winner = initiator
        loser = opponent
        foul = 1
        reason = f"{loser['username']}の発言がAIによって生成された可能性があるため、{winner['username']}の勝利です。"

    # ユーザー2のAI生成確率がNoneで、ユーザー1が0.9以上の場合
    elif (user2_ai_prob is None and user1_ai_prob is not None and user1_ai_prob > 0.9):
        winner = opponent
        loser = initiator
        foul = 1
        reason = f"{loser['username']}の発言がAIによって生成された可能性があるため、{winner['username']}の勝利です。"
        
    else:
        conver_arr = []
        conversation = " "
        
        for round_info in rounds:
            speaker = round_info['speakerId']
            speak = speaker['_id']
            content = round_info['content']
            conver = f"{speaker}:{content}. "
            conver_arr.append(conver)
        
        for arr in conver_arr:
            conversation = conversation + arr
            # print(f"python : {conversation}")
            
        # Analyze the conversation and determine the winner
        winner = analyze_conversation(conversation)
        
        # 正規表現パターンを定義
        pattern = r'勝者:\s*([^\s,]+),\s*理由:\s*([^,]+),\s*反則:\s*(\d+)'

        # 正規表現を使ってマッチする部分を抽出
        match = re.search(pattern, winner)

        if match:
            userid = match.group(1)
            reason = match.group(2)
            foul = match.group(3)
                
            
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
        'pel': foul, #違反が合ったかどうか
        'parent_post' : post,
        'parent_post_key' : post['_id'],
        'start_post' : start_1,
        'start_post_key' : start_1['_id'],
    }
    
    # print(f"python : {result}")

    # 結果をJSONとして出力
    print(json.dumps(result))

if __name__ == "__main__":
    main()
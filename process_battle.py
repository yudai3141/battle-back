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
    
    chat = ChatOpenAI(
    temperature=0,  # Reduce response randomness
    model="gpt-3.5-turbo",
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
                    会話内に明らかに他者に対しての誹謗中傷が含まれている場合その時点で誹謗中傷を行った人を負けにしてください。
                    
                    回答フォーマット
                    WinnerID: (ID), reason: (勝敗の理由を会話に使われている言語と同じもので記述)
                    
                    また会話は以下のように記述します.
                    (例)
                    会話: (user1id): (user1の発言).(user2id): (user2の発言).(user1id): (user1の発言).(user2id): (user2の発言).(user1id): (user1の発言) 
                    
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
                    WinnerID: (ID), reason: (勝敗の理由を会話に使われている言語と同じもので記述)
                    
                    また会話は以下のように記述します.
                    (例)
                    会話: (user1id): (user1の発言).(user2id): (user2の発言).(user1id): (user1の発言).(user2id): (user2の発言).(user1id): (user1の発言) 
                    
                    ポスト:(image) {Pimg}
                    
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
                    WinnerID: (ID), reason: (勝敗の理由を会話に使われている言語と同じもので記述)
                    
                    また会話は以下のように記述します.
                    (例)
                    会話: (user1id): (user1の発言).(user2id): (user2の発言).(user1id): (user1の発言).(user2id): (user2の発言).(user1id): (user1の発言) 
                    
                    ポスト:(image) {Pimg}, (text) {Pdesc}
                    
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
        conver = f"{speaker}: {content}."
        conver_arr.append(conver)
    
    for arr in conver_arr:
        conversation = conversation + arr
        
    # Analyze the conversation and determine the winner
    winner = analyze_conversation(conversation)
    # 正規表現パターン
    pattern = r"WinnerID: (\w+), reason: (.+)"

    # 正規表現でマッチング
    match = re.search(pattern, winner)
    
    userid = ""
    reason = ""

    if match:
        userid = match.group(1)
        reason = match.group(2)
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
        'reason': reason
    }

    # 結果をJSONとして出力
    print(json.dumps(result))

if __name__ == "__main__":
    main()
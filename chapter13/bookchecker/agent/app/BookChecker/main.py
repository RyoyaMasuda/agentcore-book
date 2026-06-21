"""
BookChecker エージェントのメインエントリーポイント。

技術書の新刊情報をブラウザで調べ、ユーザーの Google カレンダーに
発売日を登録する AI エージェントを AgentCore 上で動かします。
"""

import os, asyncio
from strands import Agent
from strands_tools.browser import AgentCoreBrowser
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from calendar_tool import make_calendar_tool

# デプロイ時に AgentCore が自動設定するメモリ ID を環境変数から読み取る
MEMORY_ID = os.getenv("MEMORY_BOOKCHECKERMEMORY_ID")

# エージェントの役割・手順・出力形式を定義するシステムプロンプト
SYSTEM_PROMPT = """あなたは技術書の新刊情報を調べて、ユーザーのGoogleカレンダーに発売日を登録するアシスタントです。

## 手順
1. ブラウザで新刊カレンダー（ https://www.sbcr.jp/calender/ ）にアクセス
2. 「PC/IT書籍」カテゴリでフィルタして、技術書の新刊一覧を取得
3. ユーザーの好みや指示に合った書籍をピックアップ
4. ユーザーに確認のうえ、発売日をGoogleカレンダーに登録

## ルール
- メモリーにユーザーの好みがあれば、それを参考にレコメンド
- カレンダーの予定名に書籍のタイトル、説明欄に著者や概要を記載
- 終日予定として登録する（end_dateはstart_dateの翌日を指定）

## 出力形式
- Markdownの表は使わず、箇条書きで情報を整理してください
- 絵文字は最小限にして、簡潔で読みやすい文章を心がけてください
"""


# HTTP リクエストを受け付ける AgentCore アプリケーションを作成
app = BedrockAgentCoreApp()


# クライアントからのリクエストを処理するメイン関数（SSE で応答をストリーミング配信）
@app.entrypoint
async def invoke(payload, context):
    # リクエスト JSON からユーザーの入力文とセッション ID を取り出す
    prompt = payload.get("prompt", "")
    session_id = payload.get("session_id")

    # エージェントの応答・ツール実行・認可 URL を非同期で受け渡すためのキュー
    event_queue = asyncio.Queue()

    # ブラウザ操作ツール（新刊サイト閲覧用）とカレンダー登録ツールを準備
    browser = AgentCoreBrowser()
    calendar_tool = make_calendar_tool(event_queue)

    # ユーザーごとの好みを記憶・参照するためのメモリ設定
    memory_config = AgentCoreMemoryConfig(
        memory_id=MEMORY_ID,
        session_id=session_id,
        actor_id="user",
        retrieval_config={
            "/users/{actorId}/preferences": RetrievalConfig(),
        },
    )

    # メモリと会話履歴を Strands エージェントに接続するセッションマネージャー
    session_manager = AgentCoreMemorySessionManager(
        agentcore_memory_config=memory_config,
    )

    # 使用する LLM・ツール・プロンプト・メモリをまとめてエージェントを組み立てる
    agent = Agent(
        model="us.anthropic.claude-sonnet-4-6",
        tools=[browser.browser, calendar_tool],
        system_prompt=SYSTEM_PROMPT,
        session_manager=session_manager,
    )

    # エージェントのストリーミング応答をイベントキューに流し込む内部関数
    async def agent_stream():
        in_tool_use = False
        tool_result = {"type": "tool_result"}
        try:
            # エージェントが返すイベントを1件ずつ処理する
            async for event in agent.stream_async(prompt):
                data = event.get("data")
                if isinstance(data, str):
                    # テキスト応答が来たら、実行中のツールがあれば先に完了通知を送る
                    if in_tool_use:
                        await event_queue.put(tool_result)
                        in_tool_use = False
                    await event_queue.put(
                      {"type": "text", "data": data}
                    )
                elif "current_tool_use" in event:
                    # 新しいツール実行が始まったら、前のツールの完了通知を送ってから開始通知を送る
                    if in_tool_use:
                        await event_queue.put(tool_result)
                    tool_info = event["current_tool_use"]
                    await event_queue.put({
                        "type": "tool_use",
                        "tool_name": tool_info.get("name", "")
                    })
                    in_tool_use = True
        except Exception as e:
            # 想定外のエラーはフロントエンドにエラーイベントとして伝える
            await event_queue.put(
                {"type": "error", "data": str(e)})
        finally:
            # ストリーム終了時、まだ実行中のツールがあれば完了通知を送る
            if in_tool_use:
                await event_queue.put(tool_result)
            # None をキューに入れて、SSE 配信ループの終了を知らせる
            await event_queue.put(None)

    # エージェント処理は別タスクで走らせ、メインループはキューからイベントを取り出して配信する
    task = asyncio.create_task(agent_stream())

    # キューからイベントを取り出し、クライアントへ SSE 形式で yield する
    while True:
        item = await event_queue.get()
        if item is None:
            break
        yield item

    # エージェント処理タスクが完全に終わるまで待つ
    await task

# ローカル実行時（python main.py）に API サーバーを起動
if __name__ == "__main__":
    app.run()

from agents.plan_agent import create_plan_agent
from agents.retrieval_agent import create_retrieval_agent
from agents.review_agent import create_review_agent
from agents.whatsnew_search_agent import create_whatsnew_search_agent
from hooks.tool_logging_hook import ToolLoggingHook
from rich import print
from rich.panel import Panel
from strands import Agent, tool
from strands.models import BedrockModel, CacheConfig
from strands.multiagent import Swarm, SwarmResult
from strands_tools import current_time

# 現在時刻を取得してシステムプロンプトに埋め込む
now = current_time.current_time("Asia/Tokyo")

SYSTEM_PROMPT = f"""あなたは複数のソースから情報を統合するリサーチディレクターです。
現在日時は{now}です。

あなたのタスク：
1. ユーザーの質問を受け取る
2. execute_swarm_searchツールを呼び出して、複数のナレッジソースを検索する
3. 見つけた情報をもとに、Markdownを生成する
4. ソース参照とリンクを含める

見出し、箇条書き、および適切な出典を含む明確なMarkdown形式で出力します。
"""


# 複数エージェントをSwarmで協調させて情報収集するツール
@tool
async def execute_swarm_search(query: str) -> str:
    """複数のソースからマルチエージェントSwarmを使用して情報収集を行います。"""

    # 各役割のサブエージェントを生成する
    plan = create_plan_agent()              # 検索計画を担当
    whatsnew_search = create_whatsnew_search_agent()  # AWS新着情報を検索
    retrieval = create_retrieval_agent()    # AWSドキュメントを検索
    review = create_review_agent()          # 収集結果を品質確認

    # 4エージェントのSwarmを作成し、PlanAgentを起点に実行する
    swarm = Swarm(
        [plan, retrieval, whatsnew_search, review],
        entry_point=plan,
    )

    # Swarm全体の最終結果を格納する変数
    multiagent_result: SwarmResult = None

    # Swarmをストリーミング実行し、発生するイベントを逐次処理する
    async for event in swarm.stream_async(query):
        if event.get("type") == "multiagent_node_start":
            # いずれかのエージェントが処理を開始したイベント
            node_id = event.get("node_id")
            print(f"[bold yellow]multiagent_node_start: {node_id}")

        elif event.get("type") == "multiagent_handoff":
            # あるエージェントから別エージェントへ引き継ぎが起きたイベント
            message = event.get("message")
            from_node_ids = event.get("from_node_ids")
            to_node_ids = event.get("to_node_ids")
            print(
                Panel(
                    message,
                    title=f"Hand off {from_node_ids} -> {to_node_ids}",
                    title_align="left",
                )
            )

        elif event.get("type") == "multiagent_node_stop":
            # いずれかのエージェントが処理を完了したイベント
            node_id = event.get("node_id")
            print(f"[bold yellow]multiagent_node_stop: {node_id}")

        elif event.get("type") == "multiagent_result":
            # Swarm全体が完了し最終回答が確定したイベント
            multiagent_result = event.get("result")

    # 最後に処理したエージェントのノードIDを取得する
    final_node_id = multiagent_result.node_history[-1].node_id
    # そのエージェントが返した最終回答を取り出す
    final_result = multiagent_result.results[final_node_id]

    return final_result.result.message


# OrchestratorAgentを生成する
def create_orchestrator_agent() -> Agent:
    return Agent(
        name="OrchestratorAgent",
        description="複数のソースから情報収集を行い、Markdownレポートを生成",
        system_prompt=SYSTEM_PROMPT,
        model=BedrockModel(
            model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0",
            # プロンプトキャッシュで繰り返し呼び出しのコストを削減
            cache_config=CacheConfig(strategy="auto"),
            additional_request_fields={
                "tool_choice": {
                    # ツールを1つずつ順番に呼び出す設定
                    "disable_parallel_tool_use": True,
                }
            },
        ),
        tools=[execute_swarm_search],
        # デフォルトのストリーミング出力ハンドラーを無効化
        callback_handler=None,
        # ツール呼び出し時にログを出力するフックを設定
        hooks=[ToolLoggingHook()],
    )

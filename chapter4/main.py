import asyncio

# rich: コンソールに色やパネルで見やすく出力するライブラリ
from agents.orchestrator_agent import create_orchestrator_agent
from rich import print
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt


# ユーザーとの対話ループを非同期で実行する
async def main():
    # オーケストレーターエージェントを初期化する
    orchestrator = create_orchestrator_agent()

    # "exit" が入力されるまで繰り返し質問を受け付ける
    while True:
        # コンソールからユーザーの入力を受け取る
        user_input = Prompt.ask("何でも聞いて下さい")

        # "exit" が含まれていたらループを終了する
        if "exit" in user_input:
            break

        # オーケストレーターエージェントに質問を渡して回答を取得
        result = orchestrator(user_input)
        # レスポンスの最後のテキストブロックを取り出す
        final_message = result.message["content"][-1]["text"]

        # Markdown形式でパネルに包んでコンソールに表示する
        print(
            Panel(
                Markdown(final_message, justify="left"),
                title="Orchestrator response",
            )
        )


if __name__ == "__main__":
    asyncio.run(main())

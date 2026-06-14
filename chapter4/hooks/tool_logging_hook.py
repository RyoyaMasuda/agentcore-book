from rich import print
from rich.text import Text
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import BeforeToolCallEvent


# ツール呼び出し前にログをコンソール出力するフック
class ToolLoggingHook(HookProvider):
    # このフッククラスが監視するイベントを登録する
    def register_hooks(self, registry: HookRegistry) -> None:
        # ツール呼び出し直前に on_tool_start を実行するよう登録
        registry.add_callback(BeforeToolCallEvent,
            self.on_tool_start)

    # ツール呼び出し直前に自動的に呼び出されるメソッド
    def on_tool_start(self,
                      event: BeforeToolCallEvent) -> None:
        # イベントからエージェント名・ツール名・入力引数を取得
        agent_name = event.agent.name
        tool_name = event.tool_use["name"]
        tool_input = event.tool_use["input"]

        if tool_name == "handoff_to_agent":
            # handoff はSwarmのストリーミングで別途表示するためスキップ
            pass
        else:
            # エージェント名・ツール名・引数をコンソールに出力する
            print(Text(
            f"🔧 {agent_name} : {tool_name} : {tool_input}"))

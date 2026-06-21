"""
Google カレンダーへの予定登録ツール。

AgentCore Identity を使って OAuth 認可を行い、
エージェントから Google Calendar API を呼び出せるようにします。
"""

import os, requests
from strands import tool
from bedrock_agentcore.identity import requires_access_token

# AgentCore ランタイムが注入する OAuth 関連の環境変数
PROVIDER_NAME = os.getenv("CREDENTIAL_PROVIDER_NAME")
CALLBACK_URL = os.getenv("CALLBACK_URL")

# Google カレンダーへの書き込みに必要な OAuth スコープ
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


# エージェントが使うカレンダー登録ツールを生成するファクトリ関数
def make_calendar_tool(event_queue):
    # Google 認可画面の URL が発行されたとき、フロントエンドへ SSE で通知する
    async def _on_auth_url(url: str):
        await event_queue.put(
            {"type": "auth_url", "url": url}
        )

    # Strands の @tool デコレータで、LLM から呼び出せる関数として公開する
    @tool
    async def add_calendar_event(
        summary: str,
        start_date: str,
        end_date: str,
        description: str = "",
    ):
        """Google Calendarに終日予定を追加する。

        Args:
            summary: 予定のタイトル
            start_date: 開始日（YYYY-MM-DD形式）
            end_date: 終了日（YYYY-MM-DD形式、開始日の翌日）
            description: 予定の詳細説明
        """

        # アクセストークンがなければ OAuth フローを開始し、取得後に API を呼ぶ
        @requires_access_token(
            provider_name=PROVIDER_NAME,
            scopes=CALENDAR_SCOPES,
            auth_flow="USER_FEDERATION",
            on_auth_url=_on_auth_url,
            callback_url=CALLBACK_URL,
        )
        async def call_api(access_token: str = ""):
            # Google Calendar API が期待する終日予定の JSON 形式を組み立てる
            event = {
                "summary": summary,
                "description": description,
                "start": {"date": start_date},
                "end": {"date": end_date},
            }
            # プライマリカレンダーに新しい予定を POST する
            bearer = f"Bearer {access_token}"
            resp = requests.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers={"Authorization": bearer},
                json=event,
            )
            return resp.json()

        # デコレータ経由で認可・API 呼び出しを実行
        result = await call_api()

        # API の成否に応じて、エージェントがユーザーへ返すメッセージを組み立てる
        if "error" in result:
            error_msg = result["error"]["message"]
            return f"カレンダー登録に失敗しました: {error_msg}"
        title = result.get("summary")
        date = result.get("start", {}).get("date")
        return f"カレンダーに登録しました: {title} ({date})"

    return add_calendar_event

"""
AgentCore Memory と Strands セッションを接続するヘルパー。

会話の記憶やユーザー設定を、エージェント実行時に読み書きできるようにします。
"""

import os
import uuid
from typing import Optional

from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

# デプロイ時に設定されるメモリ ID と AWS リージョン
MEMORY_ID = os.getenv("MEMORY_BOOKCHECKERMEMORY_ID")
REGION = os.getenv("AWS_REGION")


# セッション ID とユーザー ID からメモリセッションマネージャーを作成する
def get_memory_session_manager(session_id: Optional[str], actor_id: str) -> Optional[AgentCoreMemorySessionManager]:
    # メモリ ID が未設定の場合はメモリ機能を使わない
    if not MEMORY_ID:
        return None

    # セッション ID が渡されない呼び出し（OAuth など）向けに、UUID で仮 ID を発行する
    session_id = session_id or uuid.uuid4().hex

    # 事実・好み・会話要約それぞれから、関連度の高い記憶を最大3件ずつ取得する設定
    retrieval_config = {
        f"/users/{actor_id}/facts": RetrievalConfig(top_k=3, relevance_score=0.5),
        f"/users/{actor_id}/preferences": RetrievalConfig(top_k=3, relevance_score=0.5),
        f"/summaries/{actor_id}/{session_id}": RetrievalConfig(top_k=3, relevance_score=0.5),
    }

    return AgentCoreMemorySessionManager(
        AgentCoreMemoryConfig(
            memory_id=MEMORY_ID,
            session_id=session_id,
            actor_id=actor_id,
            retrieval_config=retrieval_config,
        ),
        REGION
    )

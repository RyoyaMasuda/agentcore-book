"""
Bedrock 上の LLM クライアントを読み込むユーティリティ。

IAM 認証情報を使って Claude モデルへの接続を準備します。
"""

from strands.models.bedrock import BedrockModel


# Bedrock の Claude モデルクライアントを返す
def load_model() -> BedrockModel:
    """Get Bedrock model client using IAM credentials."""
    return BedrockModel(model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0")

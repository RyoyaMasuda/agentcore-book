"""
MCP（Model Context Protocol）クライアントの設定。

外部 MCP サーバーと Strands エージェントを接続するためのヘルパーです。
"""

import os
import logging
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient

logger = logging.getLogger(__name__)

# Exa AI の MCP エンドポイント（Web 検索・コード検索など。認証不要の例）
EXAMPLE_MCP_ENDPOINT = "https://mcp.exa.ai/mcp"


# HTTP ストリーミング方式の MCP クライアントを Strands 互換で返す
def get_streamable_http_mcp_client() -> MCPClient:
    """Returns an MCP Client compatible with Strands"""
    # Bearer 認証が必要な MCP サーバーの場合は headers={"Authorization": f"Bearer {token}"} を追加する
    return MCPClient(lambda: streamablehttp_client(EXAMPLE_MCP_ENDPOINT))

import boto3

# Bedrock Runtimeを呼び出すクライアントを生成
client = boto3.client("bedrock-runtime")

# Converse APIでモデルにメッセージを送信する
response = client.converse(
    modelId="us.anthropic.claude-sonnet-4-6",
    messages=[
        {
            "role": "user",
            "content": [
                {"text": "こんにちは"},  # 送信プロンプト
            ],
        },
    ],
)

# レスポンスからテキスト部分を取り出してコンソールに出力
print(response["output"]["message"]["content"][0]["text"])

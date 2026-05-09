import { Agent, BedrockModel } from '@strands-agents/sdk'
import { BedrockAgentCoreApp } from 'bedrock-agentcore/runtime'
import { z } from 'zod'

// AIエージェントとAPIサーバーを作成
const agent = new Agent({
    model: new BedrockModel({
        modelId: 'us.anthropic.claude-sonnet-4-6',
    }),
})
const app = new BedrockAgentCoreApp({
    invocationHandler: {
        requestSchema: z.object({
            prompt: z.string(),
        }),
        process: async (request) => {
            // プロンプトを取り出してAIエージェントを呼び出し
            const result = await agent.invoke(request.prompt)
            return result
        },
    },
})

// APIサーバーを起動
app.run()

/**
 * AgentCore インフラを AWS にデプロイする CDK スタック定義。
 *
 * agentcore.json の内容を L3 コンストラクト経由で CloudFormation リソースに変換します。
 */

import {
  AgentCoreApplication,
  AgentCoreMcp,
  type AgentCoreProjectSpec,
  type AgentCoreMcpSpec,
} from '@aws/agentcore-cdk';
import { CfnOutput, Stack, type StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';

// Harness（評価用実行環境）1件分の設定
export interface HarnessConfig {
  name: string;
  executionRoleArn?: string;
  memoryName?: string;
  containerUri?: string;
  hasDockerfile?: boolean;
  dockerfile?: string;
  codeLocation?: string;
  tools?: { type: string; name: string }[];
  apiKeyArn?: string;
}

// このスタックに渡すプロパティ一式
export interface AgentCoreStackProps extends StackProps {
  /**
   * The AgentCore project specification containing agents, memories, and credentials.
   */
  spec: AgentCoreProjectSpec;
  /**
   * The MCP specification containing gateways and servers.
   */
  mcpSpec?: AgentCoreMcpSpec;
  /**
   * Credential provider ARNs from deployed state, keyed by credential name.
   */
  credentials?: Record<string, { credentialProviderArn: string; clientSecretArn?: string }>;
  /**
   * Harness role configurations. Each entry creates an IAM execution role for a harness.
   *
   * When `hasDockerfile` is true and `codeLocation` is provided (without an explicit
   * `containerUri`), the L3 construct builds and pushes a container image via CodeBuild
   * and emits its URI as a stack output for the post-CDK harness deployer.
   */
  harnesses?: HarnessConfig[];
}

/**
 * CDK Stack that deploys AgentCore infrastructure.
 *
 * This is a thin wrapper that instantiates L3 constructs.
 * All resource logic and outputs are contained within the L3 constructs.
 */
export class AgentCoreStack extends Stack {
  /** The AgentCore application containing all agent environments */
  public readonly application: AgentCoreApplication;

  constructor(scope: Construct, id: string, props: AgentCoreStackProps) {
    super(scope, id, props);

    const { spec, mcpSpec, credentials, harnesses } = props;

    // エージェント本体と Harness 用 IAM ロールを含む AgentCore アプリケーションを作成
    this.application = new AgentCoreApplication(this, 'Application', {
      spec,
      harnesses: harnesses?.length ? harnesses : undefined,
    });

    // MCP ゲートウェイが設定されている場合のみ、MCP 関連リソースを追加する
    if (mcpSpec?.agentCoreGateways && mcpSpec.agentCoreGateways.length > 0) {
      new AgentCoreMcp(this, 'Mcp', {
        projectName: spec.name,
        mcpSpec,
        agentCoreApplication: this.application,
        credentials,
        projectTags: spec.tags,
      });
    }

    // デプロイ後にスタック名を確認できるよう、CloudFormation 出力を定義
    new CfnOutput(this, 'StackNameOutput', {
      description: 'Name of the CloudFormation Stack',
      value: this.stackName,
    });
  }
}

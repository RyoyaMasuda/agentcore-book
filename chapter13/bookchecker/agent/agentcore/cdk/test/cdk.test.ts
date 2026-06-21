/**
 * CDK スタックの合成テスト。
 *
 * 最小構成の spec でも CloudFormation テンプレートが正しく生成されることを確認します。
 */

import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { AgentCoreStack } from '../lib/cdk-stack';

test('AgentCoreStack synthesizes with empty spec', () => {
  const app = new cdk.App();

  // リソースが空の最小 spec でスタックを作成
  const stack = new AgentCoreStack(app, 'TestStack', {
    spec: {
      name: 'testproject',
      version: 1,
      managedBy: 'CDK' as const,
      runtimes: [],
      memories: [],
      credentials: [],
      evaluators: [],
      onlineEvalConfigs: [],
      configBundles: [],
      policyEngines: [],
      agentCoreGateways: [],
      mcpRuntimeTools: [],
      unassignedTargets: [],
    },
  });

  // 合成されたテンプレートに StackNameOutput が含まれることを検証
  const template = Template.fromStack(stack);
  template.hasOutput('StackNameOutput', {
    Description: 'Name of the CloudFormation Stack',
  });
});

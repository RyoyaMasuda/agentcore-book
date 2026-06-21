#!/usr/bin/env node

/**
 * AgentCore プロジェクトの CDK エントリーポイント。
 *
 * agentcore.json の設定を読み込み、デプロイ先ごとに CloudFormation スタックを合成します。
 */

import { AgentCoreStack } from '../lib/cdk-stack';
import { ConfigIO, type AwsDeploymentTarget } from '@aws/agentcore-cdk';
import { App, type Environment } from 'aws-cdk-lib';
import * as path from 'path';
import * as fs from 'fs';

// AWS アカウント ID とリージョンを CDK の Environment 形式に変換する
function toEnvironment(target: AwsDeploymentTarget): Environment {
  return {
    account: target.account,
    region: target.region,
  };
}

// CloudFormation で使える名前にアンダースコアをハイフンへ置換する
function sanitize(name: string): string {
  return name.replace(/_/g, '-');
}

// プロジェクト名とデプロイ先名からスタック名を生成する
function toStackName(projectName: string, targetName: string): string {
  return `AgentCore-${sanitize(projectName)}-${sanitize(targetName)}`;
}

async function main() {
  // 設定ファイルのルートは cdk/ の1つ上（agentcore/ ディレクトリ）
  const configRoot = path.resolve(process.cwd(), '..');
  const configIO = new ConfigIO({ baseDir: configRoot });

  // agentcore.json と aws-targets.json を読み込む
  const spec = await configIO.readProjectSpec();
  const targets = await configIO.readAWSDeploymentTargets();

  // MCP ゲートウェイ設定は型定義に未反映の場合があるため、動的に取り出す
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const specAny = spec as any;
  const mcpSpec = specAny.agentCoreGateways?.length
    ? {
        agentCoreGateways: specAny.agentCoreGateways,
        mcpRuntimeTools: specAny.mcpRuntimeTools,
        unassignedTargets: specAny.unassignedTargets,
      }
    : undefined;

  // 初回デプロイ前は存在しない場合もある、認証情報 ARN などのデプロイ済み状態を読み込む
  let deployedState: Record<string, unknown> | undefined;
  try {
    deployedState = JSON.parse(fs.readFileSync(path.join(configRoot, '.cli', 'deployed-state.json'), 'utf8'));
  } catch {
    // ファイルがなければ undefined のまま続行
  }

  if (targets.length === 0) {
    throw new Error('No deployment targets configured. Please define targets in agentcore/aws-targets.json');
  }

  // harness.json を読み込み、IAM ロールやコンテナ設定を収集する
  const projectRoot = path.resolve(configRoot, '..');
  const harnessConfigs: {
    name: string;
    executionRoleArn?: string;
    memoryName?: string;
    containerUri?: string;
    hasDockerfile?: boolean;
    dockerfile?: string;
    codeLocation?: string;
    tools?: { type: string; name: string }[];
    apiKeyArn?: string;
  }[] = [];
  for (const entry of specAny.harnesses ?? []) {
    const harnessDir = path.resolve(projectRoot, entry.path);
    const harnessPath = path.resolve(harnessDir, 'harness.json');
    try {
      const harnessSpec = JSON.parse(fs.readFileSync(harnessPath, 'utf-8'));
      harnessConfigs.push({
        name: entry.name,
        executionRoleArn: harnessSpec.executionRoleArn,
        memoryName: harnessSpec.memory?.name,
        containerUri: harnessSpec.containerUri,
        hasDockerfile: !!harnessSpec.dockerfile,
        dockerfile: harnessSpec.dockerfile,
        codeLocation: harnessSpec.dockerfile ? harnessDir : undefined,
        tools: harnessSpec.tools,
        apiKeyArn: harnessSpec.model?.apiKeyArn,
      });
    } catch (err) {
      throw new Error(
        `Could not read harness.json for "${entry.name}" at ${harnessPath}: ${err instanceof Error ? err.message : err}`
      );
    }
  }

  const app = new App();

  // デプロイ先（アカウント×リージョン）ごとに1つの CDK スタックを作成する
  for (const target of targets) {
    const env = toEnvironment(target);
    const stackName = toStackName(spec.name, target.name);

    // このデプロイ先向けに登録済みの認証情報プロバイダー ARN を取り出す
    const targetState = (deployedState as Record<string, unknown>)?.targets as
      | Record<string, Record<string, unknown>>
      | undefined;
    const targetResources = targetState?.[target.name]?.resources as Record<string, unknown> | undefined;
    const credentials = targetResources?.credentials as
      | Record<string, { credentialProviderArn: string; clientSecretArn?: string }>
      | undefined;

    new AgentCoreStack(app, stackName, {
      spec,
      mcpSpec,
      credentials,
      harnesses: harnessConfigs.length > 0 ? harnessConfigs : undefined,
      env,
      description: `AgentCore stack for ${spec.name} deployed to ${target.name} (${target.region})`,
      tags: {
        'agentcore:project-name': spec.name,
        'agentcore:target-name': target.name,
      },
    });
  }

  // CloudFormation テンプレートを生成する
  app.synth();
}

main().catch((error: unknown) => {
  console.error('AgentCore CDK synthesis failed:', error instanceof Error ? error.message : error);
  process.exitCode = 1;
});

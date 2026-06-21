// Jest の設定: CDK スタックの TypeScript テストを実行する

module.exports = {
  // Node.js 環境でテストを実行
  testEnvironment: 'node',
  // test/ ディレクトリ配下をテスト対象のルートとする
  roots: ['<rootDir>/test'],
  // *.test.ts ファイルのみをテストとして拾う
  testMatch: ['**/*.test.ts'],
  transform: {
    // TypeScript ファイルを ts-jest で JavaScript に変換してから実行
    '^.+\\.tsx?$': 'ts-jest',
  },
  // テスト後に CDK のリソースを自動クリーンアップする
  setupFilesAfterEnv: ['aws-cdk-lib/testhelpers/jest-autoclean'],
};

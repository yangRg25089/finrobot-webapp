# FinRobot WebApp 概要設計文書

<div align="center">
  <a href="概要设计.md">中文</a> | <a href="概要设计_ja.md">日本語</a>
</div>

## 1. プロジェクト概要

### 1.1 プロジェクト紹介
FinRobot WebApp は、FinRobot フレームワークに基づくフルスタック金融分析アプリケーションで、可視化された量化取引戦略実行プラットフォームを提供します。このアプリケーションは複数のAIエージェントを統合し、年次レポート分析、株式予測、RAG質問応答などの機能をサポートし、ユーザーにワンストップの金融データ分析サービスを提供します。

### 1.2 技術スタック
- **バックエンド**: FastAPI + FinRobot + Python 3.10
- **フロントエンド**: React 18 + TypeScript + Vite + Tailwind CSS
- **AIフレームワーク**: FinRobot (AutoGenベース)
- **データストレージ**: ファイルシステム + ChromaDB (ベクトルデータベース)
- **国際化**: react-i18next (中国語、英語、日本語対応)

### 1.3 コア機能
- 🚀 リアルタイムストリーミングスクリプト実行
- 📊 多次元金融データ分析
- 🤖 インテリジェントAIエージェント統合
- 📁 ファイル生成とプレビュー
- 🌍 多言語サポート
- 📈 履歴記録管理
- 🔄 パラメータ化スクリプト設定

## 2. システムアーキテクチャ

### 2.1 全体アーキテクチャ図
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   フロントエンド   │    │   バックエンド     │    │   AIエージェント層 │
│   (React)       │    │   (FastAPI)     │    │                 │
│                 │    │                 │    │                 │
│ • ScriptForm    │◄──►│ • main.py       │◄──►│ • FinRobot      │
│ • ResultViewer  │    │ • script_manager│    │ • AutoGen       │
│ • LogsPanel     │    │ • history_manager│   │ • 各種AIエージェント│
│ • Sidebar       │    │ • utils         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ブラウザストレージ │    │   ファイルシステム   │    │   外部API        │
│                 │    │                 │    │                 │
│ • localStorage  │    │ • static/       │    │ • OpenAI API    │
│ • ユーザー設定   │    │ • history/      │    │ • SEC API       │
│ • スクリプト選択 │    │ • output/       │    │ • 金融データAPI  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2.2 コアモジュール

#### 2.2.1 フロントエンドモジュール
- **App.tsx**: メインアプリケーションコンポーネント、グローバル状態管理
- **ScriptForm.tsx**: スクリプトパラメータ設定フォーム
- **ResultViewer.tsx**: 結果表示と履歴記録管理
- **LogsPanel.tsx**: リアルタイムログ表示
- **Sidebar.tsx**: スクリプト選択サイドバー
- **Topbar.tsx**: トップナビゲーションバー

#### 2.2.2 バックエンドモジュール
- **main.py**: FastAPIアプリケーションエントリーポイント、APIルート定義
- **script_manager.py**: スクリプト実行マネージャー、ストリーミング出力サポート
- **history_manager.py**: 対話履歴管理
- **utils.py**: 汎用ユーティリティ関数集合

#### 2.2.3 AIエージェントモジュール
- **tutorials_wrapper/**: カプセル化された金融分析スクリプト
  - **beginner/**: 初級スクリプト
  - **advanced/**: 上級スクリプト

## 3. 機能モジュール設計

### 3.1 スクリプト実行システム

#### 3.1.1 スクリプト管理
```python
# スクリプト統一インターフェース
def run(params: dict, lang: str) -> dict:
    return {
        "result": messages,  # 対話結果
        "generated_files": files_info,  # 生成されたファイル
        "metrics": performance_data  # パフォーマンス指標
    }
```

#### 3.1.2 ストリーミング実行
- Server-Sent Events (SSE) を使用したリアルタイム出力
- stdout/stderr 分離サポート
- エラーハンドリングと例外キャッチ
- 実行状態リアルタイム更新

#### 3.1.3 パラメータ解析
- スクリプトパラメータ定義の自動解析
- 複数のデータ型サポート：string, boolean, date, array
- 動的フォーム生成
- パラメータ検証とデフォルト値処理

### 3.2 結果表示システム

#### 3.2.1 対話履歴
- Markdown形式レンダリング
- メッセージ折りたたみ/展開
- ロール識別表示
- タイムスタンプ記録

#### 3.2.2 ファイル管理
- 自動ファイル収集
- 画像プレビュー機能
- PDF文書プレビュー
- ファイルダウンロードサポート

#### 3.2.3 履歴記録
- スクリプト別分類保存
- タイムスタンプディレクトリ構造
- 履歴記録クエリ
- 記録削除機能

### 3.3 国際化システム

#### 3.3.1 サポート言語
- 中国語 (zh)
- 英語 (en)  
- 日本語 (ja)

#### 3.3.2 翻訳内容
- インターフェーステキスト
- スクリプト説明
- パラメータラベル
- エラーメッセージ

### 3.4 設定管理

#### 3.4.1 API設定
- OpenAI API設定
- SEC API設定
- その他の金融データAPI

#### 3.4.2 モデル設定
- 複数のAIモデルサポート
- 動的モデル選択
- パラメータ設定管理

## 4. データフロー設計

### 4.1 スクリプト実行フロー
```
ユーザーがスクリプト選択 → パラメータ設定 → 実行提出 → ストリーミング出力 → 結果表示 → 履歴保存
     ↓              ↓           ↓          ↓          ↓          ↓
  ScriptForm → ScriptManager → SSE → LogsPanel → ResultViewer → HistoryManager
```

### 4.2 ファイル保存構造
```
backend/
├── static/
│   ├── output/           # スクリプト出力ファイル
│   │   └── {script_name}/
│   │       └── {date}/
│   │           └── {timestamp}/
│   └── history/          # 対話履歴
│       └── {script_name}/
│           └── {date}/
│               └── {timestamp}/
└── tutorials_wrapper/    # スクリプトソースコード
    ├── beginner/
    └── advanced/
```

### 4.3 APIインターフェース設計

#### 4.3.1 コアインターフェース
- `GET /api/tutorial-scripts`: 利用可能なスクリプトリスト取得
- `GET /api/run-script/stream`: ストリーミングスクリプト実行
- `GET /api/models`: 利用可能なモデルリスト取得
- `GET /api/history/{script_name}`: スクリプト履歴取得
- `DELETE /api/history/{script_name}`: 履歴記録削除

#### 4.3.2 データ形式
```typescript
// スクリプト情報
interface ScriptInfo {
  script_name: string;
  folder: string;
  params: Record<string, ParamConfig>;
}

// パラメータ設定
interface ParamConfig {
  type: 'string' | 'boolean' | 'date' | 'string[]' | 'number';
  defaultValue: any;
}

// 実行結果
interface ExecutionResult {
  result: Message[];
  generated_files: FileInfo[];
  error?: string;
}
```

## 5. 技術実装詳細

### 5.1 フロントエンド技術スタック

#### 5.1.1 状態管理
- React Hooks による状態管理
- カスタムHook によるビジネスロジックカプセル化
- ローカルストレージによるユーザー設定永続化

#### 5.1.2 リアルタイム通信
- EventSource API によるSSEストリーム受信
- 自動再接続メカニズム
- エラーハンドリングと状態同期

#### 5.1.3 コンポーネント設計
- 関数型コンポーネント + TypeScript
- レスポンシブレイアウト設計
- アクセシビリティサポート

### 5.2 バックエンド技術スタック

#### 5.2.1 APIフレームワーク
- FastAPI による高性能API提供
- 自動API文書生成
- 型安全なデータ検証

#### 5.2.2 非同期処理
- asyncio による並行処理サポート
- スレッドプールによるCPU集約型タスク実行
- ストリーミングレスポンスによるユーザー体験最適化

#### 5.2.3 ファイル管理
- Pathlib によるパス操作
- 自動ディレクトリ作成とクリーンアップ
- ファイル権限管理

### 5.3 AI統合

#### 5.3.1 FinRobot統合
- 統一エージェントインターフェース
- マルチモデルサポート
- ツール関数統合

#### 5.3.2 対話管理
- メッセージ標準化処理
- 多言語指示サポート
- 履歴コンテキスト管理

## 6. デプロイと運用

### 6.1 開発環境
```bash
# バックエンド起動
cd backend
conda activate finrobot
uvicorn main:app --reload --port 8000

# フロントエンド起動
cd frontend
npm install
npm run dev
```

### 6.2 本番環境
- Docker コンテナ化デプロイ
- Nginx リバースプロキシ
- 環境変数設定管理
- ログ監視とアラート

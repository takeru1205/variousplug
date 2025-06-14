# variousplug[vp] - 様々なDockerホストへのプラグ

`vp`は[fireplug](https://github.com/koheiw/fireplug)をベースに、[vast.ai](https://vast.ai)と[RunPod](https://runpod.io)をサポートするように再構築されたコマンドラインインターフェース（CLI）ツールです。

## 機能

- 🚀 **リモート実行** - vast.aiとRunPodのGPUインスタンスでコードを実行
- 🔄 **BSRSワークフロー** - Build、Sync、Run、Syncの自動化
- 🐳 **Docker統合** - 自動Dockerイメージビルド
- 📁 **ファイル同期** - vast.ai用ネイティブSDK、RunPod用rsync
- ⚙️ **簡単な設定** - インタラクティブセットアップとYAML設定
- 🎯 **プラットフォーム非依存** - 複数のクラウドプラットフォームをサポート
- 🧪 **包括的テスト** - CI/CDを含む完全なテストスイート
- 🔧 **モダンツール** - Ruffリンター、GitHub Actions、Python 3.11+

## はじめに

### 1. プラットフォームアカウントの作成

VariousPlugを使用する前に、プラットフォームのアカウントが必要です：

- **[vast.aiに登録](https://cloud.vast.ai/?ref_id=85456)** *(紹介リンク)* - スポット価格でコスト効率的なGPUインスタンス
  - *直接リンク: [vast.ai](https://vast.ai)*
- **[RunPodに登録](https://runpod.io?ref=jnz0wcmk)** *(紹介リンク)* - 固定価格で信頼性の高いGPUインフラストラクチャ
  - *直接リンク: [runpod.io](https://runpod.io)*

*注：紹介リンクを使用することで、追加費用なしにVariousPlugの開発をサポートしていただけます。*

### 2. インストール

```bash
uv tool install git+https://github.com/takeru1205/variousplug.git
```

### 3. クイックスタート

#### 設定の初期化
```bash
# プロジェクト設定を初期化
vp --init

# または開発用
uv run vp --init
```

#### APIキーの設定
```bash
# プラットフォームのAPIキーを設定
vp config-set --vast-api-key YOUR_VAST_API_KEY
vp config-set --runpod-api-key YOUR_RUNPOD_API_KEY
vp config-set --default-platform vast
```

### 3. リモートホストでコマンドを実行
```bash
# リモートGPUでPythonスクリプトを実行
vp run -- python train_model.py

# 特定のプラットフォームで実行
vp run --platform vast -- python script.py

# 特定のインスタンスで実行
vp run --instance-id 12345 -- python script.py
```

## 使用例

### 基本ワークフロー
```bash
# プロジェクトディレクトリを作成
mkdir my-ml-project && cd my-ml-project

# VariousPlugを初期化
vp --init

# コードを書く
echo "print('Hello from remote GPU!')" > hello.py

# リモートDockerホストで実行
vp run -- python hello.py
```

### 高度な使用法
```bash
# 利用可能なインスタンスをリスト
vp list-instances

# 新しいインスタンスを作成
vp create-instance --platform vast --gpu-type RTX3090

# ファイル同期のみ（実行なし）
vp run --sync-only -- python script.py

# 同期なしで実行（既存ファイルを使用）
vp run --no-sync -- python script.py

# カスタムDockerfile
vp run --dockerfile custom.Dockerfile -- python script.py

# 完了時にインスタンスを破棄
vp destroy-instance INSTANCE_ID
```

### 設定管理
```bash
# 現在の設定を表示
vp config-show

# 設定値を設定
vp config-set --vast-api-key YOUR_KEY
vp config-set --runpod-api-key YOUR_KEY
vp config-set --default-platform runpod
```

## プラットフォーム別の例

### Vast.ai（簡単セットアップ）
```bash
# 1. 設定（APIキーのみ必要）
vp config-set --vast-api-key YOUR_KEY
vp config-set --default-platform vast

# 2. すぐに実行（SSH設定不要）
vp run -- python train.py

# 3. ファイルはSDK経由で自動同期
```

### RunPod（完全セットアップ）
```bash
# 1. 設定
vp config-set --runpod-api-key YOUR_KEY
vp config-set --default-platform runpod

# 2. SSHキーの設定とrsyncのインストール
vp create-instance --platform runpod --gpu-type RTX4000
vp run --no-sync -- "apt update && apt install -y rsync"

# 3. rsyncベースの同期で実行
vp run -- python train.py
```

## 実装概要

VariousPlugはモダンなPythonツールと拡張機能で完全に再実装されました：

### ✅ **実装済みコア機能**
- **完全なCLIインターフェース** - `vp`コマンドによる完全なコマンドライン
- **BSRSワークフロー** - Build-Sync-Run-Sync自動化が完全動作
- **プラットフォーム統合** - vast.aiとRunPodの両方をサポート
- **設定管理** - インタラクティブセットアップ付きYAMLベース設定
- **Docker統合** - 自動Dockerイメージビルドと管理
- **ファイル同期** - vast.ai用ネイティブSDK、RunPod用rsync
- **エラーハンドリング** - リッチ出力による包括的エラーハンドリング
- **インスタンス管理** - インスタンスの作成、リスト、破棄

### 🏗️ **アーキテクチャ**
- **`cli.py`** - Clickベースのコマンドインターフェース
- **`config.py`** - YAML設定管理
- **`executor.py`** - コアBSRSワークフロー実装
- **`vast_client.py`** - Vast.ai SDK統合
- **`runpod_client.py`** - RunPod SDK統合
- **`utils.py`** - ユーティリティ関数とリッチ出力

### 🔧 **依存関係**
- **Click** - CLIフレームワーク
- **PyYAML** - 設定管理
- **Docker SDK** - Dockerイメージビルド
- **Vast.ai SDK** - ネイティブファイル同期付きVast.aiプラットフォーム統合
- **RunPod SDK** - RunPodプラットフォーム統合
- **Rich** - 強化されたターミナル出力
- **Ruff** - モダンなPythonリンターとフォーマッター

### 📊 **テスト状況**
- ✅ CLIインターフェースが完全に機能
- ✅ 設定システムが動作
- ✅ Dockerビルドプロセスがテスト済み
- ✅ BSRSワークフローが検証済み
- ✅ ファイル同期がテスト済み（vast.ai SDK + RunPod rsync）
- ✅ エラーハンドリングが包括的
- ✅ 125以上のパステストでユニットテスト
- ✅ GitHub ActionsでCI/CD

## BSRSワークフロー

VariousPlugは**Build-Sync-Run-Sync**の手順を使用します。

1. **🔨 Build** - ローカルDockerfileからDockerイメージをビルド
2. **📤 Sync** - ローカルファイルをリモートインスタンスにアップロード
   - **vast.ai**: ネイティブSDK `copy()`メソッド（SSH不要）
   - **RunPod**: SSH経由rsync
3. **🚀 Run** - リモートGPU上のDockerコンテナでコマンドを実行
4. **📥 Sync** - 結果をローカルマシンにダウンロード
   - **vast.ai**: ネイティブSDK `copy()`メソッド
   - **RunPod**: SSH経由rsync

### プラットフォーム別同期詳細

**Vast.ai**: SSHセットアップを必要としないシームレスなファイル転送のためにネイティブ`vast_sdk.copy()`メソッドを使用。

**RunPod**: ポッドインスタンスで適切なSSHキー設定を必要とするSSH経由rsyncを使用。

## ドキュメント

- 📚 **[プラットフォーム比較](docs/platform-comparison-ja.md)** - Vast.ai vs RunPodの比較（日本語版）
- 📚 **[Platform Comparison](docs/platform-comparison.md)** - Vast.ai vs RunPod comparison (English)
- 🌟 **[Vast.aiガイド](docs/vast-ai-guide.md)** - 完全なVast.aiセットアップと使用法
- 🚀 **[RunPodガイド](docs/runpod-guide.md)** - 完全なRunPodセットアップと使用法

## 開発

### 開発環境のセットアップ
```bash
# リポジトリをクローン
git clone https://github.com/takeru1205/variousplug.git
cd variousplug

# uvで依存関係をインストール
uv sync

# テストを実行
uv run pytest

# リンターとフォーマッターを実行
uv run ruff check .
uv run ruff format .

# 開発モードでCLIを実行
uv run vp --help
```

### プロジェクト構造
```
src/variousplug/
├── cli.py              # メインCLIインターフェース
├── config.py           # 設定管理
├── executor.py         # BSRSワークフロー実行
├── factory.py          # プラットフォームファクトリーパターン
├── interfaces.py       # 抽象インターフェース
├── vast_client.py      # Vast.ai SDK統合
├── runpod_client.py    # RunPod SDK統合
├── base.py             # ベース実装
└── utils.py            # ユーティリティ関数

tests/
├── unit/               # ユニットテスト
├── conftest.py         # テスト設定
└── pytest.ini         # テスト設定

.github/workflows/      # CI/CDパイプライン
docs/                   # ドキュメント
```

### CI/CDパイプライン
- **GitHub Actions**による自動テスト
- **Python 3.11、3.12、3.13**サポート
- **マルチプラットフォームテスト**（Linux、macOS、Windows）
- **Ruffリンターとフォーマッター**
- **banditとsafety**によるセキュリティスキャン

## プラットフォーム比較

### Vast.ai の利点
- 🚀 **SSH設定ゼロ** - APIキーだけですぐに動作
- 💰 **コスト最適化** - 内蔵の$0.50/時間安全制限
- ⚡ **高速セットアップ** - 5分の設定
- 🔄 **ネイティブ同期** - 信頼性の高いSDKベースファイル転送

### RunPod の利点
- 🏢 **エンタープライズ信頼性** - 専用インフラストラクチャ
- 🔧 **完全制御** - 標準SSH/rsyncツール
- 📊 **予測可能なコスト** - 固定価格ティア
- 🛡️ **セキュリティ** - カスタムSSH設定

## よくある質問

### Q: どちらのプラットフォームを選ぶべきですか？
**A:** 
- **簡単さとコスト重視** → Vast.ai
- **信頼性と予測可能性重視** → RunPod

### Q: ファイル同期でエラーが発生します
**A:**
- **Vast.ai**: APIキーが有効か確認
- **RunPod**: SSHキーが設定されているか、rsyncがインストールされているか確認

### Q: インスタンスの料金を抑えるには？
**A:**
- 使用後は必ずインスタンスを破棄（`vp destroy-instance ID`）
- Vast.aiでは安価なGPUタイプを選択
- RunPodでは適切なインスタンスサイズを選択

## 貢献

プロジェクトへの貢献を歓迎します！

1. このリポジトリをフォーク
2. フィーチャーブランチを作成（`git checkout -b feature/amazing-feature`）
3. 変更をコミット（`git commit -m 'Add amazing feature'`）
4. ブランチにプッシュ（`git push origin feature/amazing-feature`）
5. プルリクエストを作成

## ライセンス

このプロジェクトはMITライセンスの下でライセンスされています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## サポート

- 🐛 **バグレポート**: [GitHub Issues](https://github.com/takeru1205/variousplug/issues)
- 📝 **ドキュメント**: [docs/](docs/)フォルダ
- 💬 **質問**: GitHub Discussionsまたはissues

## 謝辞

- [fireplug](https://github.com/koheiw/fireplug) - オリジナルのインスピレーション
- [Vast.ai](https://vast.ai/) - コスト効率的なGPUコンピューティング
- [RunPod](https://www.runpod.io/) - 信頼性の高いGPUインフラストラクチャ
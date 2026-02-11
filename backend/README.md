# SPY Credit Spread Dashboard - Backend

FastAPI + ib_insync ベースのバックエンドAPI

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境設定

親ディレクトリ（`spy-credit-spread/`）の `config.py` で設定:

- `USE_MOCK_DATA = True`  # モックモード
- `USE_PAPER_ACCOUNT = True`  # ペーパー口座
- その他の戦略パラメータ

### 3. サーバー起動

#### 方法1: スタートアップスクリプト（推奨）

```bash
./start_server.sh
```

#### 方法2: 手動起動

```bash
export PYTHONPATH="/Users/tirino/ib/spy-credit-spread:$PYTHONPATH"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 方法3: Python直接実行

```bash
export PYTHONPATH="/Users/tirino/ib/spy-credit-spread:$PYTHONPATH"
python3 main.py
```

## トラブルシューティング

### "Attribute 'app' not found in module 'main'" エラー

原因: PYTHONPATHが設定されていない

解決策:
```bash
export PYTHONPATH="/Users/tirino/ib/spy-credit-spread:$PYTHONPATH"
```

または `start_server.sh` を使用してください。

### モジュールインポートエラー

バックエンドは親ディレクトリ（`spy-credit-spread/`）の以下のモジュールに依存しています:

- `config.py` - 設定
- `logger.py` - ロガー
- `connection.py` - IBKR接続
- `mock_data.py` - モックデータ
- `data.py` - マーケットデータ
- `position.py` - ポジション管理

これらのファイルが親ディレクトリに存在することを確認してください。

## APIエンドポイント

### ヘルスチェック
- `GET /api/health` - サーバー状態確認

### 口座
- `GET /api/account` - 基本口座情報
- `GET /api/account/summary` - 詳細サマリー（戦略パラメータ、リスク、ポジション）

### マーケット
- `GET /api/market/spy` - SPY現在価格
- `GET /api/market/vix` - VIX水準（未実装）

## ディレクトリ構造

```
backend/
├── main.py              # FastAPIアプリケーション
├── start_server.sh      # 起動スクリプト
├── requirements.txt     # 依存関係
├── models/
│   ├── __init__.py
│   └── schemas.py       # Pydanticスキーマ
├── routers/
│   ├── __init__.py
│   ├── account.py       # 口座API
│   └── market.py        # マーケットAPI
├── services/            # 将来実装
└── ws/                  # WebSocket（将来実装）
```

## モックモード vs リアルモード

### モックモード（USE_MOCK_DATA = True）
- IBKR接続不要
- ダミーデータで動作確認
- 市場データサブスクリプション不要

### リアルモード（USE_MOCK_DATA = False）
- TWS/Gateway起動必要
- ポート: ペーパー7497 / ライブ7496
- 市場データサブスクリプション必要

## 開発

### ログ確認

```bash
tail -f ../logs/system.log
```

### API ドキュメント

サーバー起動後:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

# テストガイド

## セットアップ

### 必要なパッケージのインストール

```bash
pip install pytest pytest-asyncio httpx
```

## テストの実行

### 全テストを実行

```bash
# プロジェクトルートから実行
pytest tests/ -v
```

### 特定のテストファイルを実行

```bash
pytest tests/test_api_endpoints.py -v
```

### 特定のテストクラスを実行

```bash
pytest tests/test_api_endpoints.py::TestMarketEndpoints -v
```

### 特定のテストケースを実行

```bash
pytest tests/test_api_endpoints.py::TestMarketEndpoints::test_get_spy_price -v
```

### カバレッジレポートを生成

```bash
pip install pytest-cov
pytest tests/ --cov=backend --cov-report=html
```

カバレッジレポートは `htmlcov/index.html` に生成されます。

## テスト構成

### test_api_endpoints.py

主要なAPIエンドポイントのテストを含みます：

- **ヘルスチェック**: `/api/health`
- **マーケットデータ**: `/api/market/spy`, `/api/market/vix`
- **オプション**: `/api/options/chain`, `/api/options/spreads`
- **戦略**: `/api/strategy/next-entry`, `/api/strategy/status`
- **アカウント**: `/api/account/summary`, `/api/account/positions`
- **為替レート**: `/api/fx/rate`, `/api/fx/rate/tts`

## テストの追加

新しいテストを追加する場合：

1. `tests/` ディレクトリに `test_*.py` ファイルを作成
2. テストクラスを `Test*` で始める
3. テストメソッドを `test_*` で始める
4. `pytest.mark.asyncio` デコレータを非同期テストに追加

例：

```python
class TestNewFeature:
    @pytest.mark.asyncio
    async def test_new_endpoint(self, client):
        response = await client.get("/api/new-endpoint")
        assert response.status_code == 200
```

## 注意事項

- テストは**モックモード**で実行されます（`USE_MOCK_DATA=True`）
- リアルTWS接続は不要です
- テストデータは `tests/fixtures/` に配置できます（将来の拡張用）

## CI/CD統合

### GitHub Actions

`.github/workflows/test.yml` を作成：

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx pytest-cov
      - name: Run tests
        run: pytest tests/ -v --cov=backend
```

## トラブルシューティング

### `ModuleNotFoundError`

プロジェクトルートから実行していることを確認：

```bash
cd /Users/tirino/ib/spy-credit-spread
pytest tests/ -v
```

### テストが失敗する

- サーバーが起動していないか確認
- モックモードが有効か確認（`USE_MOCK_DATA=True`）
- 依存パッケージがインストールされているか確認

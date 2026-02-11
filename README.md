# SPY Bull Put Credit Spread 自動取引システム

IBKR TWS API経由でSPYのBull Put Credit Spreadを自動実行するシステム

---

## 📁 プロジェクト構成

```
spy-credit-spread/
├── backend/                    # FastAPI ダッシュボードバックエンド
│   ├── main.py                # FastAPIアプリケーション
│   ├── requirements.txt       # Python依存関係
│   ├── routers/               # APIルーター
│   │   ├── account.py        # 口座情報API
│   │   └── market.py         # マーケットデータAPI
│   ├── models/
│   │   └── schemas.py        # Pydanticスキーマ
│   ├── services/              # ビジネスロジック
│   └── ws/                    # WebSocket管理
│
├── frontend/                   # Next.js ダッシュボード（未実装）
│
├── logs/                       # ログディレクトリ
│   ├── system.log             # システムログ
│   ├── trades.csv             # 取引ログ（税務対応）
│   ├── market_data.csv        # マーケットデータログ
│   └── positions.json         # ポジション管理
│
├── config.py                   # 戦略パラメータ設定
├── logger.py                   # ログ管理
├── connection.py               # IBKR接続管理
├── data.py                     # マーケットデータ取得
├── fx_rate.py                  # 為替レート取得
├── mock_data.py                # モックデータ生成
│
├── strategy.py                 # スプレッド選択ロジック
├── order.py                    # 注文発注・管理
├── mock_order.py               # モック注文
├── position.py                 # ポジション管理
├── monitor.py                  # リスク管理
│
├── main.py                     # Step 3: マーケットデータ取得
├── main_step4.py               # Step 4: 自動取引実行
└── requirements.txt            # Python依存関係
```

---

## ✅ 実装完了済み

### Step 3: マーケットデータ取得
- ✅ SPY価格取得
- ✅ オプションチェーン取得
- ✅ Greeks（デルタ、IV）取得
- ✅ Bull Put Spread候補選択
- ✅ USD/JPY為替レート取得
- ✅ マーケットデータログ記録
- ✅ モックデータモード対応

### Step 4: 自動取引実行
- ✅ 最適スプレッド選択アルゴリズム
- ✅ スプレッド検証（デルタ、プレミアム、R/R比）
- ✅ ポジションサイズ自動計算
- ✅ ポートフォリオリスク管理
- ✅ 注文発注（リアル + モック）
- ✅ ポジション追跡（positions.json）
- ✅ 取引ログ（税務対応、CSV）
- ✅ 円換算表示

### ダッシュボード（Phase A: 基礎）
- ✅ FastAPIバックエンド基礎
  - main.py（アプリケーションエントリーポイント）
  - Pydanticスキーマ
  - account.py（口座情報API）
  - market.py（マーケットデータAPI）
- ⏳ Next.jsフロントエンド（次回実装）
- ⏳ WebSocket（リアルタイム配信）（次回実装）
- ⏳ Claude APIチャット機能（次回実装）

---

## 🚀 クイックスタート

### 1. 依存関係インストール

```bash
# Python依存関係
pip install -r requirements.txt

# FastAPI依存関係（バックエンド用）
pip install -r backend/requirements.txt
```

### 2. Step 3: マーケットデータ取得テスト

```bash
# モックデータモードで実行
python3 main.py
```

**結果**: SPY価格、オプションチェーン、Bull Put Spread候補を表示

### 3. Step 4: 自動取引実行テスト

```bash
# モックデータ + モック注文モードで実行
python3 main_step4.py
```

**結果**:
- 最適スプレッド選択
- リスクチェック
- 注文発注（モック）
- ポジション記録
- 取引ログ記録

### 4. FastAPIダッシュボード起動

```bash
cd backend
python3 main.py
```

**アクセス**:
- API: http://localhost:8000
- ドキュメント: http://localhost:8000/docs
- ヘルスチェック: http://localhost:8000/api/health

**利用可能なAPI**:
- `GET /api/account` - 口座情報
- `GET /api/account/summary` - 詳細サマリー
- `GET /api/market/spy` - SPY価格

---

## ⚙️ 設定

### config.py

```python
# モックデータモード（開発・テスト用）
USE_MOCK_DATA = True  # False = リアルIBKR接続

# ペーパー/リアル口座
USE_PAPER_ACCOUNT = True  # False = リアル口座

# 戦略パラメータ
SYMBOL = 'SPY'
SPREAD_WIDTH = 5          # $5スプレッド
TARGET_DELTA = 0.20       # 売りプットのデルタ目標
DELTA_RANGE = (0.15, 0.25)
RISK_PER_TRADE = 0.08     # 1取引あたり資金の8%

# 満期設定
MIN_DTE = 1               # 最小DTE
MAX_DTE = 7               # 最大DTE（1週間以内）
```

---

## 📊 ログファイル

### logs/trades.csv
取引履歴（税務対応）。確定申告に必要な情報をすべて記録：
- 取引日時（UTC、ET、JST）
- オプション詳細（ストライク、満期、プレミアム）
- 手数料
- USD/JPYレート（取引時点 + TTSレート）
- 円換算金額

### logs/positions.json
オープンポジション管理。リアルタイムで更新：
- スプレッドID
- エントリー情報（価格、日時）
- 最大利益・損失
- ステータス（open/closed/expired）

### logs/market_data.csv
マーケットデータ履歴。分析用：
- SPY価格
- 選択されたストライク
- デルタ、IV
- スプレッドプレミアム
- R/R比

---

## 🎯 次のステップ

### フロントエンド実装（優先）

1. **Next.jsプロジェクトセットアップ**
   ```bash
   cd spy-credit-spread
   npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir
   cd frontend
   npm install recharts lucide-react clsx date-fns
   ```

2. **基本コンポーネント作成**
   - Layout（Header, Sidebar, StatusBar）
   - AccountCard（口座情報表示）
   - SpyPriceCard（SPY価格、リアルタイム）
   - SpreadCandidates（スプレッド候補テーブル）

3. **APIクライアント実装**
   - `lib/api.ts` - FastAPI呼び出し
   - `lib/websocket.ts` - WebSocket接続
   - `hooks/useMarketData.ts` - マーケットデータフック

4. **Claude APIチャット機能**
   - フロントエンドにチャットウィンドウ追加
   - Claude API統合（ユーザーが提供したAPIキー使用）

### バックエンド拡張

5. **追加APIルーター**
   - options.py（オプションチェーン、スプレッド候補）
   - positions.py（ポジション管理、P&L計算）
   - trades.py（取引履歴、税務サマリー）
   - fx.py（為替レート、TTS入力）

6. **WebSocket実装**
   - ws/manager.py（接続管理）
   - リアルタイム価格配信（1秒間隔）
   - オプションデータ更新（5秒間隔）

---

## ⚠️ 重要な注意事項

### リアルモードでの実行前に

1. **TWSマーケットデータサブスクリプション申請**
   - US Securities Snapshot Bundle
   - OPRA (US Options)

2. **config.py設定変更**
   ```python
   USE_MOCK_DATA = False  # リアルデータ
   USE_PAPER_ACCOUNT = True  # 最初はペーパー口座
   ```

3. **TWSを起動して待機**
   - File → Global Configuration → API → Settings
   - "Enable ActiveX and Socket Clients" ✓
   - "Read-Only API" のチェックを外す

4. **ペーパー口座で十分にテスト**
   - 少なくとも1-2週間の動作確認
   - ログの検証
   - リスク管理の確認

5. **リアル口座移行**
   ```python
   USE_PAPER_ACCOUNT = False  # リアル口座
   ```
   - 最初は1契約から開始
   - 徐々にサイズを増やす

---

## 📚 参考資料

- [IBKR API Documentation](https://interactivebrokers.github.io/tws-api/)
- [ib_insync Documentation](https://ib-insync.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

---

## 📝 ライセンス

個人使用のみ。実際の取引は自己責任で行ってください。

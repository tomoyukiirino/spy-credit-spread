# CLAUDE.md — SPY Credit Spread Auto-Trading System

## プロジェクト概要

SPY（S&P 500 ETF）のBull Put Credit Spreadを自動化するオプション取引システム。
IBKR（Interactive Brokers）TWS API経由で、ペーパートレードからリアルトレードへ段階的に移行する。

### アーキテクチャ

```
Next.js (:3000) → FastAPI (:8000) → IBKR TWS API (:7497/7496)
```

- **フロントエンド**: Next.js + TypeScript + Tailwind（ダークモード・トレーディング画面風）
- **バックエンド**: FastAPI（REST + WebSocket）
- **ブローカー接続**: ib_insync（Python）
- **データ配信**: WebSocket（SPY価格1秒、オプション5秒、為替30秒間隔）

---

## 技術スタック

| レイヤー | 技術 | バージョン |
|---------|------|-----------|
| OS | macOS (Intel) | - |
| Python | Python | 3.11.9 |
| Node.js | Node.js | 最新LTS |
| ブローカーAPI | ib_insync | >=0.9.86 |
| バックエンド | FastAPI + uvicorn | >=0.109 |
| フロントエンド | Next.js (App Router) | latest |
| スタイリング | Tailwind CSS | latest |
| チャート | recharts | latest |
| 型定義 | Pydantic (BE) / TypeScript (FE) | - |

---

## ディレクトリ構造

```
spy-credit-spread/
├── backend/
│   ├── main.py                # FastAPIアプリ起動（lifespan でIBKR接続管理）
│   ├── config.py              # 全パラメータ設定
│   ├── routers/               # APIエンドポイント
│   │   ├── account.py         # GET /api/account
│   │   ├── market.py          # GET /api/market/spy, /api/market/vix
│   │   ├── options.py         # GET /api/options/chain, /api/options/spreads
│   │   ├── positions.py       # GET/POST /api/positions
│   │   ├── trades.py          # GET /api/trades, /api/trades/tax-summary
│   │   └── fx.py              # GET/POST /api/fx/rate
│   ├── services/              # ビジネスロジック
│   │   ├── ibkr_service.py    # ib_insyncシングルトン接続管理
│   │   ├── market_service.py  # マーケットデータ取得
│   │   ├── options_service.py # オプションチェーン・スプレッド計算
│   │   ├── trade_service.py   # 取引実行・ログ記録
│   │   └── fx_service.py      # 為替レート取得（IBKR→API→手動フォールバック）
│   ├── models/
│   │   └── schemas.py         # Pydanticスキーマ
│   ├── ws/
│   │   └── manager.py         # WebSocket接続管理・価格配信
│   └── requirements.txt
├── frontend/                  # Next.js App Router
│   ├── src/
│   │   ├── app/               # ページ: /, /positions, /trades
│   │   ├── components/        # UI コンポーネント
│   │   ├── hooks/             # useWebSocket, useMarketData 等
│   │   ├── lib/               # api.ts, formatters.ts, websocket.ts
│   │   └── types/             # TypeScript型（Pydantic対応）
│   └── package.json
├── logs/                      # ログ出力先
│   ├── system.log
│   ├── trades.csv             # 税務申告対応の取引ログ
│   └── market_data.csv
└── CLAUDE.md
```

---

## 戦略パラメータ

```python
SYMBOL = 'SPY'
SPREAD_WIDTH = 5           # $5 スプレッド
TARGET_DELTA = 0.20        # 売りプットのデルタ目標（勝率≒80%）
DELTA_RANGE = (0.15, 0.25) # 許容デルタ範囲
RISK_PER_TRADE = 0.08      # 1取引あたり資金の8%
MIN_DTE = 1                # 満期まで最短1日
MAX_DTE = 7                # 満期まで最長7日
```

- 元金: $10,000 USD
- 月間目標リターン: 2〜5%
- SPYは月・水・金に週次満期あり

---

## 接続情報

| 環境 | ポート | 用途 |
|------|--------|------|
| TWS ペーパー | 7497 | テスト用 |
| TWS リアル | 7496 | 本番用 |
| FastAPI | 8000 | バックエンドAPI |
| Next.js | 3000 | フロントエンド |

ペーパー口座ID: DUP843993

---

## 開発フェーズ

### 現在の進捗
- ✅ Step 1: IBKR口座セットアップ
- ✅ Step 2: Python環境構築・API接続確認
- 🔄 Step 3: マーケットデータ取得 + 税務対応ログ基盤
- ⬜ Step 4: ペーパートレード自動発注
- ⬜ Step 5: リアルトレード移行

### フロントエンド実装順序
- Phase A: 基盤（FastAPI + IBKR接続 + AccountCard + SpyPriceCard）
- Phase B: オプションデータ（OptionChainTable + SpreadCandidates + SpreadDetail）
- Phase C: リアルタイム化（WebSocket + 価格フラッシュアニメーション）
- Phase D: ポジション・取引ログ（PositionTable + PnlChart + TradeLog）
- Phase E: 為替・税務（FxRateCard + TaxSummary + CSV出力）

### 将来構想
- Phase 3以降でマルチ市場対応を検討（日本→欧州→米国のリレー式24h自動取引）
- まずはSPYクレジットスプレッドを安定させることが最優先

---

## 重要な実装ルール

### ib_insync 固有の注意
- `ib.qualifyContracts(contract)` を必ず呼んでからデータリクエスト
- オプションContract: `lastTradeDateOrContractMonth` はYYYYMMDD形式
- `reqMktData` 後、Greeksが返るまで `ib.sleep(2)` で待機が必要
- ペーパー口座では `ib.reqMarketDataType(3)` でdelayed data（15分遅延）を許可
- オプションチェーンはバッチ処理（5〜10銘柄ずつ、間に `ib.sleep(1)`）
- ib_insyncはスレッドセーフではない → FastAPIからは `run_in_executor` 経由

### FastAPI + ib_insync 統合
- `nest_asyncio` でイベントループをネスト、または ib_insync を別スレッドで実行
- IBKR接続はシングルトンパターンで管理（`ibkr_service.py`）
- CORS: localhost:3000 のみ許可
- 発注系APIは `confirm=true` パラメータ必須

### 税務対応（日本の確定申告）
- 雑所得として申告（年間20万円超の利益で申告義務）
- 取引ログに必ず記録するもの:
  - timestamp_jst（JST基準の約定時刻）
  - trade_date_jst（税務年度判定用、12月31日締め）
  - fx_rate_usd_jpy（取引時点の実勢レート）
  - fx_rate_tts（TTSレート — 三菱UFJ対顧客電信売相場、参考値）
  - net_amount_jpy（円換算金額）
  - commission_usd（手数料、円換算して経費計上可能）
- 実勢レートとTTSレートの両方を記録し、申告時に選択可能にする
- spread_id で売り足・買い足を紐付け

### 為替レート取得の優先順位
1. IBKR API（USD.JPY Forexペア）
2. 無料為替API（フォールバック）
3. 前営業日のログから取得（フォールバック）
4. 手動入力を促す（全て失敗時）

---

## コーディング規約

### Python（バックエンド）
- docstring・コメントは日本語
- 型ヒント（type hints）必須
- 具体的な例外をキャッチ（bare except 禁止）
- f-string 使用
- pandas DataFrame + tabulate でテーブル表示

### TypeScript（フロントエンド）
- strict mode
- コメントは日本語OK
- React Server Components デフォルト、インタラクティブなものだけ `"use client"`
- カスタムフック: `use` プレフィックス、loading/error 状態を必ず返す
- 数値表示は等幅フォント（JetBrains Mono）

### UI デザイン
- ダークモード固定（トレーディング画面風）
- 背景: `#0a0e17`（メイン）/ `#111827`（カード）
- 利益=緑 `#22c55e` / 損失=赤 `#ef4444`
- 価格フラッシュアニメーション（上昇=緑、下降=赤、0.5秒フェード）
- 接続状態ドット: 緑=接続中、赤=切断、黄=再接続中

---

## 起動方法

```bash
# ターミナル1: TWS起動（GUI）

# ターミナル2: FastAPI バックエンド
cd spy-credit-spread/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# ターミナル3: Next.js フロントエンド
cd spy-credit-spread/frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## 主要ファイルの役割（迷ったとき用）

| ファイル | 何をするか |
|---------|-----------|
| `backend/services/ibkr_service.py` | IBKR接続のシングルトン管理。全サービスがここ経由 |
| `backend/services/options_service.py` | オプションチェーン取得・スプレッド候補計算 |
| `backend/models/schemas.py` | 全APIのリクエスト/レスポンス型定義 |
| `backend/ws/manager.py` | WebSocketで価格・オプション・為替をリアルタイム配信 |
| `frontend/src/hooks/useWebSocket.ts` | WebSocket接続管理（再接続ロジック含む） |
| `frontend/src/components/options/SpreadCandidates.tsx` | ★最重要UI — スプレッド候補テーブル |
| `frontend/src/components/trades/TaxSummary.tsx` | 税務サマリー（円換算・申告ステータス） |
| `logs/trades.csv` | 全取引の税務申告対応ログ |

---

## 参考リンク

- [ib_insync ドキュメント](https://ib-insync.readthedocs.io/)
- [IBKR マーケットデータ料金](https://www.interactivebrokers.com/en/pricing/research-news-marketdata.php)
- [決算カレンダー](https://earningswhispers.com)
- [FastAPI ドキュメント](https://fastapi.tiangolo.com/)
- [Next.js App Router](https://nextjs.org/docs/app)
- [recharts](https://recharts.org/)

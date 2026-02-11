# SPY Credit Spread API仕様書

## ベースURL

```
http://localhost:8000/api
```

## 認証

現在、認証は実装されていません。ローカル環境での使用を想定しています。

---

## エンドポイント一覧

### 1. ヘルスチェック

#### `GET /health`

システムの状態を確認します。

**レスポンス例**：
```json
{
    "status": "ok",
    "ibkr_connected": true,
    "mode": "mock",
    "timestamp": "2026-02-11T17:21:14.426817+00:00"
}
```

**フィールド**：
- `status`: システム状態（`ok` / `error`）
- `ibkr_connected`: IBKR接続状態
- `mode`: 動作モード（`mock` / `real`）
- `timestamp`: レスポンス生成時刻（UTC）

---

### 2. マーケットデータ

#### `GET /market/spy`

SPYの現在価格を取得します。

**レスポンス例**：
```json
{
    "last": 583.5,
    "bid": 583.45,
    "ask": 583.55,
    "mid": 583.5,
    "timestamp": "2026-02-11T17:21:14.472357Z",
    "is_delayed": true
}
```

**フィールド**：
- `last`: 最終取引価格
- `bid`: ビッド価格
- `ask`: アスク価格
- `mid`: ミッド価格（bid + ask / 2）
- `timestamp`: データ取得時刻（UTC）
- `is_delayed`: 遅延データかどうか

#### `GET /market/vix`

VIX指数の現在値を取得します。

**レスポンス例**：
```json
{
    "vix": 18.5,
    "bid": 18.4,
    "ask": 18.6,
    "timestamp": "2026-02-11T17:22:09.285101+00:00",
    "is_mock": true,
    "is_delayed": true
}
```

**フィールド**：
- `vix`: VIX値
- `bid`: ビッド価格（リアルモードのみ）
- `ask`: アスク価格（リアルモードのみ）
- `timestamp`: データ取得時刻（UTC）
- `is_mock`: モックデータかどうか
- `is_delayed`: 遅延データかどうか

---

### 3. オプションデータ

#### `GET /options/chain`

オプションチェーンを取得します。

**クエリパラメータ**：
- `symbol`: シンボル（デフォルト: `SPY`）
- `dte_min`: 最小DTE（デフォルト: `1`）
- `dte_max`: 最大DTE（デフォルト: `7`）

**レスポンス例**：
```json
{
    "symbol": "SPY",
    "dte_range": [1, 7],
    "options_count": 45,
    "options": [
        {
            "strike": 520.0,
            "expiry": "20260216",
            "exp_date": "2026-02-16",
            "dte": 4,
            "bid": 2.4046875,
            "ask": 2.6578125,
            "mid": 2.53125,
            "delta": 0.17352185089974292,
            "gamma": null,
            "theta": null,
            "iv": 23.441302485004286,
            "volume": null,
            "open_interest": null
        }
    ]
}
```

**フィールド**：
- `symbol`: シンボル
- `dte_range`: DTEの範囲
- `options_count`: オプション数
- `options[]`: オプションデータの配列
  - `strike`: ストライク価格
  - `expiry`: 満期日（YYYYMMDD形式）
  - `exp_date`: 満期日（YYYY-MM-DD形式）
  - `dte`: 満期までの日数
  - `bid`: ビッド価格
  - `ask`: アスク価格
  - `mid`: ミッド価格
  - `delta`: デルタ
  - `gamma`: ガンマ
  - `theta`: セータ
  - `iv`: インプライドボラティリティ（%）
  - `volume`: 出来高
  - `open_interest`: オープンインタレスト

#### `GET /options/spreads`

スプレッド候補を取得します。

**レスポンス例**：
```json
{
    "candidates_count": 9,
    "candidates": [
        {
            "short_strike": 520.0,
            "long_strike": 515.0,
            "expiry": "20260216",
            "exp_date": "2026-02-16",
            "dte": 4,
            "short_delta": 0.17352185089974292,
            "long_delta": 0.14781491002570696,
            "spread_width": 5.0,
            "net_premium": 0.375,
            "max_loss": 4.625,
            "max_profit": 0.375,
            "risk_reward_ratio": 12.333333333333334,
            "probability_of_profit": 7.5
        }
    ]
}
```

**フィールド**：
- `candidates_count`: 候補数
- `candidates[]`: スプレッド候補の配列
  - `short_strike`: ショートストライク
  - `long_strike`: ロングストライク
  - `expiry`: 満期日
  - `dte`: 満期までの日数
  - `short_delta`: ショートのデルタ
  - `long_delta`: ロングのデルタ
  - `spread_width`: スプレッド幅
  - `net_premium`: 受取プレミアム
  - `max_loss`: 最大損失
  - `max_profit`: 最大利益
  - `risk_reward_ratio`: リスク/リワード比
  - `probability_of_profit`: 利益確率（%）

#### `POST /options/calculate-spread`

スプレッドの指標を計算します。

**リクエストボディ**：
```json
{
    "short_strike": 520.0,
    "long_strike": 515.0,
    "short_premium": 2.53,
    "long_premium": 2.15
}
```

**レスポンス例**：
```json
{
    "spread_width": 5.0,
    "net_premium": 0.38,
    "max_loss": 4.62,
    "max_profit": 0.38,
    "breakeven": 519.62,
    "risk_reward_ratio": 12.16,
    "probability_of_profit": 7.6
}
```

---

### 4. 戦略

#### `GET /strategy/next-entry`

次回エントリーのプレビューを取得します（発注はしません）。

**レスポンス例**：
```json
{
    "recommended": true,
    "skip_reason": null,
    "vix": 18.5,
    "adjusted_delta": 0.2,
    "fear_greed": {
        "score": 50,
        "rating": "Neutral",
        "timestamp": "2026-02-12T02:23:33.202172",
        "is_mock": true
    },
    "selected_expiry": "20260220",
    "spread": null,
    "max_loss": null,
    "within_risk_limit": false,
    "event_warnings": []
}
```

**フィールド**：
- `recommended`: エントリー推奨かどうか
- `skip_reason`: スキップ理由（`VIX_TOO_HIGH` / `ERROR` / null）
- `vix`: 現在のVIX値
- `adjusted_delta`: VIX調整後のデルタ
- `fear_greed`: Fear & Greed Index
  - `score`: スコア（0-100）
  - `rating`: 評価（`Extreme Fear` / `Fear` / `Neutral` / `Greed` / `Extreme Greed`）
  - `timestamp`: 取得時刻
  - `is_mock`: モックデータかどうか
- `selected_expiry`: 選択された満期日
- `spread`: 選択されたスプレッド情報
- `max_loss`: 最大損失
- `within_risk_limit`: リスク限度内かどうか
- `event_warnings[]`: イベント警告の配列

#### `GET /strategy/status`

現在の戦略ステータスを取得します。

**レスポンス例**：
```json
{
    "is_active": false,
    "next_entry_date": null,
    "next_entry_time": null,
    "current_vix": null,
    "adjusted_delta": null,
    "position_size_factor": 1.0,
    "fear_greed_score": null,
    "fear_greed_rating": null,
    "open_positions_count": 0,
    "skip_reason": null
}
```

#### `GET /strategy/event-calendar`

経済イベントカレンダーを取得します。

**レスポンス例**：
```json
{
    "events": {
        "FOMC": [
            "2026-01-28",
            "2026-03-18",
            "2026-05-06"
        ],
        "NFP": [
            "2026-01-02",
            "2026-02-06"
        ],
        "CPI": [
            "2026-01-13",
            "2026-02-11"
        ]
    },
    "year": 2026
}
```

---

### 5. アカウント

#### `GET /account/summary`

アカウント概要を取得します。

**レスポンス例**：
```json
{
    "account": {
        "net_liquidation": 10000.0,
        "total_cash": 8500.0,
        "buying_power": 25000.0
    },
    "strategy_params": {
        "symbol": "SPY",
        "spread_width": 5,
        "target_delta": 0.2,
        "delta_range": [0.15, 0.25],
        "risk_per_trade": 0.08,
        "min_dte": 1,
        "max_dte": 7
    },
    "risk_limits": {
        "max_risk_per_trade": 800.0,
        "max_portfolio_risk": 3000.0,
        "current_portfolio_risk": 0,
        "available_risk": 3000.0
    },
    "positions": {
        "total_positions": 0,
        "open_positions": 0,
        "closed_positions": 0,
        "total_open_risk": 0,
        "total_open_potential_profit": 0,
        "total_realized_pnl_usd": 0
    }
}
```

#### `GET /account/positions`

現在のポジション一覧を取得します。

**レスポンス例**：
```json
{
    "positions": [],
    "count": 0
}
```

---

### 6. 為替レート

#### `GET /fx/rate`

USD/JPY為替レートを取得します。

**レスポンス例**：
```json
{
    "usd_jpy": 155.5,
    "tts_rate": 156.5,
    "source": "manual",
    "timestamp": "2026-02-11T17:00:00Z"
}
```

#### `POST /fx/rate/manual`

手動で為替レートを設定します。

**リクエストボディ**：
```json
{
    "usd_jpy": 155.5,
    "tts_rate": 156.5
}
```

**レスポンス例**：
```json
{
    "message": "FX rate set successfully",
    "rate": {
        "usd_jpy": 155.5,
        "tts_rate": 156.5,
        "source": "manual",
        "timestamp": "2026-02-11T17:00:00Z"
    }
}
```

#### `GET /fx/rate/tts`

スポットレートからTTSレートを計算します。

**クエリパラメータ**：
- `spot_rate`: スポットレート（必須）
- `margin`: マージン（デフォルト: `1.0`）

**レスポンス例**：
```json
{
    "spot_rate": 155.5,
    "margin": 1.0,
    "tts_rate": 156.5
}
```

---

## エラーレスポンス

すべてのエンドポイントは、エラー発生時に以下の形式でレスポンスを返します：

```json
{
    "detail": "エラーの詳細メッセージ"
}
```

### HTTPステータスコード

- `200 OK`: 成功
- `500 Internal Server Error`: サーバーエラー
- `503 Service Unavailable`: IBKR未接続

---

## 開発モード

### モックモード

```python
# config.py
USE_MOCK_DATA = True
```

モックデータを使用して開発・テストを行います。TWS接続は不要です。

### リアルモード

```python
# config.py
USE_MOCK_DATA = False
```

実際のIBKR TWS APIに接続してリアルデータを取得します。TWS/IB Gatewayが起動している必要があります。

---

## レート制限

現在、レート制限は実装されていません。

---

## WebSocket

現在、WebSocketエンドポイントは実装されていますが、ドキュメント化されていません。

---

## バージョン

API Version: 1.0.0
Last Updated: 2026-02-11

---

## サポート

問題や質問がある場合は、GitHubのIssuesページで報告してください。

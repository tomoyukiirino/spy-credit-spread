"""
Pydanticスキーマ: API リクエスト/レスポンスのデータモデル
"""

from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List


# --- 口座 ---
class AccountInfo(BaseModel):
    """口座情報"""
    net_liquidation: float
    total_cash: float
    buying_power: float
    currency: str = "USD"


# --- マーケットデータ ---
class SpyPrice(BaseModel):
    """SPY価格"""
    last: Optional[float]
    bid: Optional[float]
    ask: Optional[float]
    mid: Optional[float]
    timestamp: datetime
    is_delayed: bool = False


# --- オプション ---
class OptionData(BaseModel):
    """オプションデータ"""
    strike: float
    expiry: str  # YYYYMMDD
    bid: Optional[float] = None
    ask: Optional[float] = None
    mid: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    iv: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None


class SpreadCandidate(BaseModel):
    """スプレッド候補"""
    short_strike: float
    long_strike: float
    expiry: str
    exp_date: str
    dte: int
    short_delta: Optional[float]
    short_iv: Optional[float]
    spread_premium_mid: Optional[float]
    max_profit: Optional[float]
    max_loss: Optional[float]
    risk_reward_ratio: Optional[float]
    win_probability: Optional[float] = None  # 1 - |delta|
    score: Optional[float] = None


# --- ポジション ---
class Position(BaseModel):
    """ポジション"""
    spread_id: str
    symbol: str
    short_strike: float
    long_strike: float
    expiration: str
    exp_date: str
    dte_at_entry: int
    quantity: int
    entry_premium: float
    max_profit: float
    max_loss: float
    opened_at_utc: str
    opened_at_jst: str
    status: str  # open / closed / expired
    fx_rate_usd_jpy: Optional[float] = None
    closed_at: Optional[str] = None
    exit_premium: Optional[float] = None
    realized_pnl_usd: Optional[float] = None
    realized_pnl_jpy: Optional[float] = None
    unrealized_pnl_usd: Optional[float] = None


# --- 取引ログ（税務対応）---
class TradeRecord(BaseModel):
    """取引記録"""
    trade_id: str
    timestamp_utc: str
    timestamp_et: str
    timestamp_jst: str
    trade_date_jst: str
    symbol: str
    action: str  # SELL / BUY
    option_type: str
    strike: float
    expiry: str
    quantity: int
    premium_per_contract: float
    total_premium_usd: float
    commission_usd: float
    net_amount_usd: float
    fx_rate_usd_jpy: Optional[float]
    fx_rate_tts: Optional[float]
    net_amount_jpy: Optional[float]
    spread_id: str
    leg: str  # short / long
    position_status: str
    notes: str = ""


# --- 為替 ---
class FxRate(BaseModel):
    """為替レート"""
    usd_jpy: float
    source: str  # "IBKR" / "API" / "manual"
    timestamp: datetime
    tts_rate: Optional[float] = None


# --- 税務サマリー ---
class TaxSummary(BaseModel):
    """税務サマリー"""
    year: int
    total_premium_received_usd: float
    total_premium_paid_usd: float
    total_commission_usd: float
    net_profit_usd: float
    net_profit_jpy: float
    total_trades: int
    win_count: int
    loss_count: int
    win_rate: float


# --- WebSocket ---
class WsMarketUpdate(BaseModel):
    """WebSocketマーケット更新"""
    type: str  # "spy_price" / "option_update" / "fx_rate"
    data: dict
    timestamp: datetime


# --- ヘルスチェック ---
class HealthCheck(BaseModel):
    """ヘルスチェック"""
    status: str
    ibkr_connected: bool
    mode: str  # "mock" / "real"
    timestamp: datetime


# === Step 4: 戦略関連スキーマ ===

class StrategyStatus(BaseModel):
    """戦略ステータス"""
    is_active: bool
    next_entry_date: Optional[str] = None
    next_entry_time: Optional[str] = None
    current_vix: Optional[float] = None
    adjusted_delta: Optional[float] = None
    position_size_factor: float = 1.0  # 1.0 or 0.5
    fear_greed_score: Optional[int] = None
    fear_greed_rating: Optional[str] = None
    open_positions_count: int = 0
    skip_reason: Optional[str] = None  # "VIX_TOO_HIGH" / "EVENT_DAY" / None


class EntryPreview(BaseModel):
    """エントリープレビュー（/api/strategy/next-entry）"""
    recommended: bool
    skip_reason: Optional[str] = None
    vix: float
    adjusted_delta: float
    fear_greed: Optional[dict] = None
    selected_expiry: str
    spread: Optional[SpreadCandidate] = None
    max_loss: Optional[float] = None
    within_risk_limit: bool = False
    event_warnings: List[str] = []  # 近接中のイベント警告


class ResumeReport(BaseModel):
    """Resume機能のレポート"""
    ibkr_positions: List[dict]
    local_positions: List[dict]
    mismatches: List[str]
    auto_fixed: List[str]
    needs_manual: List[str]
    timestamp: datetime


class OrderResult(BaseModel):
    """注文結果"""
    success: bool
    spread_id: Optional[str] = None
    order_status: str  # filled / cancelled / timeout / error
    fill_price: Optional[float] = None
    message: str

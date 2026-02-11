/**
 * TypeScript型定義
 * バックエンドのPydanticスキーマと対応
 */

// --- 口座 ---
export interface AccountInfo {
  net_liquidation: number;
  total_cash: number;
  buying_power: number;
  currency: string;
}

export interface AccountSummary {
  account: {
    net_liquidation: number;
    total_cash: number;
    buying_power: number;
  };
  strategy_params: {
    symbol: string;
    spread_width: number;
    target_delta: number;
    delta_range: [number, number];
    risk_per_trade: number;
    min_dte: number;
    max_dte: number;
  };
  risk_limits: {
    max_risk_per_trade: number;
    max_portfolio_risk: number;
    current_portfolio_risk: number;
    available_risk: number;
  };
  positions: PositionSummary;
}

// --- マーケットデータ ---
export interface SpyPrice {
  last: number | null;
  bid: number | null;
  ask: number | null;
  mid: number | null;
  timestamp: string;
  is_delayed: boolean;
}

// --- オプション ---
export interface OptionData {
  strike: number;
  expiry: string;
  exp_date?: string;
  dte?: number;
  bid: number | null;
  ask: number | null;
  mid: number | null;
  delta: number | null;
  gamma: number | null;
  theta: number | null;
  iv: number | null;
  volume: number | null;
  open_interest: number | null;
}

export interface SpreadCandidate {
  short_strike: number;
  long_strike: number;
  expiry: string;
  exp_date: string;
  dte: number;
  short_delta: number | null;
  short_iv: number | null;
  spread_premium_mid: number | null;
  max_profit: number | null;
  max_loss: number | null;
  risk_reward_ratio: number | null;
  win_probability: number | null;
  score: number | null;
}

// --- ポジション ---
export interface Position {
  spread_id: string;
  symbol: string;
  short_strike: number;
  long_strike: number;
  expiration: string;
  exp_date: string;
  dte_at_entry: number;
  quantity: number;
  entry_premium: number;
  max_profit: number;
  max_loss: number;
  opened_at_utc: string;
  opened_at_jst: string;
  status: 'open' | 'closed' | 'expired';
  fx_rate_usd_jpy: number | null;
  closed_at: string | null;
  exit_premium: number | null;
  realized_pnl_usd: number | null;
  realized_pnl_jpy: number | null;
  unrealized_pnl_usd: number | null;
}

export interface PositionSummary {
  total_positions: number;
  open_positions: number;
  closed_positions?: number;
  total_open_risk: number;
  total_open_potential_profit?: number;
  total_max_profit?: number;
  total_unrealized_pnl?: number;
  total_realized_pnl_usd?: number;
}

// --- 取引ログ ---
export interface TradeRecord {
  trade_id: string;
  timestamp_utc: string;
  timestamp_et: string;
  timestamp_jst: string;
  trade_date_jst: string;
  symbol: string;
  action: 'SELL' | 'BUY';
  option_type: string;
  strike: number;
  expiry: string;
  quantity: number;
  premium_per_contract: number;
  total_premium_usd: number;
  commission_usd: number;
  net_amount_usd: number;
  fx_rate_usd_jpy: number | null;
  fx_rate_tts: number | null;
  net_amount_jpy: number | null;
  spread_id: string;
  leg: 'short' | 'long';
  position_status: string;
  notes: string;
}

// --- 為替 ---
export interface FxRate {
  usd_jpy: number;
  source: 'IBKR' | 'API' | 'manual';
  timestamp: string;
  tts_rate: number | null;
}

// --- 損益チャート ---
export interface PnlData {
  date: string;
  realized_pnl: number;
  unrealized_pnl: number;
  total_pnl: number;
}

// --- 税務サマリー ---
export interface TaxSummary {
  year: number;
  total_premium_received_usd: number;
  total_premium_paid_usd: number;
  total_commission_usd: number;
  net_profit_usd: number;
  net_profit_jpy: number;
  total_trades: number;
  win_count: number;
  loss_count: number;
  win_rate: number;
}

// --- ヘルスチェック ---
export interface HealthCheck {
  status: string;
  ibkr_connected: boolean;
  mode: 'mock' | 'real';
  timestamp: string;
}

// --- UI状態 ---
export interface ApiError {
  detail: string;
}

/**
 * FastAPI クライアント
 * バックエンドAPIとの通信を管理
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * API エラー
 */
export class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(detail);
    this.name = 'ApiError';
  }
}

/**
 * Fetch ラッパー
 */
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new ApiError(response.status, errorData.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // ネットワークエラーなど
    throw new ApiError(0, error instanceof Error ? error.message : 'Network error');
  }
}

// --- ヘルスチェック ---
export async function getHealth() {
  return fetchApi<{
    status: string;
    ibkr_connected: boolean;
    mode: string;
    timestamp: string;
  }>('/api/health');
}

// --- 口座 ---
export async function getAccountInfo() {
  return fetchApi<{
    net_liquidation: number;
    total_cash: number;
    buying_power: number;
    currency: string;
  }>('/api/account');
}

export async function getAccountSummary() {
  return fetchApi<{
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
    positions: {
      total_positions: number;
      open_positions: number;
      total_open_risk: number;
      total_max_profit: number;
      total_unrealized_pnl: number;
    };
  }>('/api/account/summary');
}

// --- マーケット ---
export async function getSpyPrice() {
  return fetchApi<{
    last: number | null;
    bid: number | null;
    ask: number | null;
    mid: number | null;
    timestamp: string;
    is_delayed: boolean;
  }>('/api/market/spy');
}

export async function getVixLevel() {
  return fetchApi<{
    vix: number | null;
    message: string;
  }>('/api/market/vix');
}

// --- オプション（将来実装予定）---
export async function getOptionsChain(symbol: string, dte_min: number, dte_max: number) {
  return fetchApi<any>(`/api/options/chain?symbol=${symbol}&dte_min=${dte_min}&dte_max=${dte_max}`);
}

export async function getSpreadCandidates() {
  return fetchApi<any[]>('/api/options/spreads');
}

// --- ポジション（将来実装予定）---
export async function getPositions() {
  return fetchApi<any[]>('/api/positions');
}

export async function closePosition(spreadId: string) {
  return fetchApi<any>(`/api/positions/${spreadId}/close`, {
    method: 'POST',
  });
}

// --- 取引ログ（将来実装予定）---
export async function getTrades(limit?: number) {
  const query = limit ? `?limit=${limit}` : '';
  return fetchApi<any[]>(`/api/trades${query}`);
}

export async function getTaxSummary(year: number) {
  return fetchApi<any>(`/api/trades/tax-summary?year=${year}`);
}

// --- 為替（将来実装予定）---
export async function getFxRate() {
  return fetchApi<{
    usd_jpy: number;
    source: string;
    timestamp: string;
    tts_rate: number | null;
  }>('/api/fx/rate');
}

export async function setManualFxRate(usd_jpy: number, tts_rate?: number) {
  return fetchApi<any>('/api/fx/rate/manual', {
    method: 'POST',
    body: JSON.stringify({ usd_jpy, tts_rate }),
  });
}

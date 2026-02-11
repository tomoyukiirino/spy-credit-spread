'use client';

import { Wallet, TrendingUp, DollarSign } from 'lucide-react';
import { formatUSD, formatPercent } from '@/lib/formatters';
import type { AccountSummary } from '@/types';

interface AccountCardProps {
  data: AccountSummary | null;
  loading?: boolean;
}

export default function AccountCard({ data, loading }: AccountCardProps) {
  if (loading || !data) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Wallet size={20} className="text-accent-primary" />
          口座情報
        </h2>
        <div className="text-gray-500">読み込み中...</div>
      </div>
    );
  }

  const { account, risk_limits, positions } = data;
  const riskUsagePercent = (risk_limits.current_portfolio_risk / risk_limits.max_portfolio_risk) * 100;

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Wallet size={20} className="text-accent-primary" />
        口座情報
      </h2>

      <div className="space-y-4">
        {/* 口座残高 */}
        <div>
          <div className="text-sm text-gray-400 mb-1">純資産</div>
          <div className="text-2xl font-bold font-mono">{formatUSD(account.net_liquidation)}</div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-400 mb-1">現金残高</div>
            <div className="text-lg font-mono">{formatUSD(account.total_cash)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-400 mb-1">購買力</div>
            <div className="text-lg font-mono">{formatUSD(account.buying_power)}</div>
          </div>
        </div>

        {/* リスク管理 */}
        <div className="pt-4 border-t border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp size={16} className="text-accent-secondary" />
            <span className="text-sm font-semibold">リスク管理</span>
          </div>

          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">ポートフォリオリスク</span>
                <span className="font-mono">{formatPercent(riskUsagePercent / 100, 1)}</span>
              </div>
              <div className="w-full bg-dark-surface rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    riskUsagePercent > 80
                      ? 'bg-accent-danger'
                      : riskUsagePercent > 60
                      ? 'bg-accent-warning'
                      : 'bg-accent-success'
                  }`}
                  style={{ width: `${Math.min(riskUsagePercent, 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>{formatUSD(risk_limits.current_portfolio_risk)}</span>
                <span>{formatUSD(risk_limits.max_portfolio_risk)}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <div className="text-gray-400">利用可能リスク</div>
                <div className="font-mono text-accent-success">{formatUSD(risk_limits.available_risk)}</div>
              </div>
              <div>
                <div className="text-gray-400">1取引あたり上限</div>
                <div className="font-mono">{formatUSD(risk_limits.max_risk_per_trade)}</div>
              </div>
            </div>
          </div>
        </div>

        {/* ポジションサマリー */}
        <div className="pt-4 border-t border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <DollarSign size={16} className="text-accent-warning" />
            <span className="text-sm font-semibold">ポジション</span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <div className="text-gray-400">オープン</div>
              <div className="font-mono text-lg">{positions.open_positions}</div>
            </div>
            <div>
              <div className="text-gray-400">最大利益</div>
              <div className="font-mono text-accent-success">{formatUSD(positions.total_open_potential_profit)}</div>
            </div>
            <div>
              <div className="text-gray-400">総リスク</div>
              <div className="font-mono text-accent-danger">{formatUSD(positions.total_open_risk)}</div>
            </div>
            <div>
              <div className="text-gray-400">実現損益</div>
              <div className={`font-mono ${(positions.total_realized_pnl_usd ?? 0) >= 0 ? 'text-accent-success' : 'text-accent-danger'}`}>
                {formatUSD(positions.total_realized_pnl_usd ?? 0)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

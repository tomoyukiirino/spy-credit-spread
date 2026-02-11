'use client';

import { X, TrendingUp, TrendingDown, Target, Calendar, DollarSign } from 'lucide-react';
import { formatUSD, formatDateTime, formatPercent } from '@/lib/formatters';
import type { Position } from '@/types';

interface PositionDetailProps {
  position: Position | null;
  onClose: () => void;
  onClosePosition?: (spreadId: string) => void;
}

export default function PositionDetail({ position, onClose, onClosePosition }: PositionDetailProps) {
  if (!position) return null;

  const unrealizedPnl = position.unrealized_pnl_usd ?? 0;
  const pnlPercentage = position.max_profit > 0
    ? (unrealizedPnl / position.max_profit) * 100
    : 0;
  const isOpen = position.status === 'open';
  const isClosed = position.status === 'closed';

  const calculateDTE = (expiration: string): number => {
    const expiryDate = new Date(expiration);
    const today = new Date();
    const diffTime = expiryDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const dte = calculateDTE(position.expiration);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-card border border-dark-border rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* ヘッダー */}
        <div className="flex items-center justify-between p-6 border-b border-dark-border">
          <h3 className="text-xl font-semibold">ポジション詳細</h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-dark-hover rounded-lg transition-colors"
          >
            <X size={20} className="text-gray-400" />
          </button>
        </div>

        {/* コンテンツ */}
        <div className="p-6 space-y-6">
          {/* 基本情報 */}
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
              <Calendar size={16} />
              基本情報
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-400">Spread ID</div>
                <div className="text-lg font-mono">{position.spread_id}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">ステータス</div>
                <div className="text-lg">
                  {position.status === 'open' && <span className="badge badge-success">OPEN</span>}
                  {position.status === 'closed' && <span className="badge bg-blue-500/20 text-blue-400">CLOSED</span>}
                  {position.status === 'expired' && <span className="badge bg-gray-500/20 text-gray-400">EXPIRED</span>}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-400">エントリー日時</div>
                <div className="text-sm font-mono">{formatDateTime(position.opened_at_jst)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">満期日</div>
                <div className="text-sm font-mono">
                  {position.exp_date} ({dte}日)
                </div>
              </div>
            </div>
          </div>

          {/* ストライク情報 */}
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
              <Target size={16} />
              ストライク
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-dark-surface rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-2">売りプット (Short)</div>
                <div className="text-2xl font-mono font-bold">${position.short_strike}</div>
              </div>
              <div className="bg-dark-surface rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-2">買いプット (Long)</div>
                <div className="text-2xl font-mono font-bold">${position.long_strike}</div>
              </div>
            </div>
            <div className="mt-2 text-sm text-gray-400">
              スプレッド幅: <span className="font-mono text-white">${position.short_strike - position.long_strike}</span>
            </div>
          </div>

          {/* エントリー情報 */}
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
              <DollarSign size={16} />
              エントリー情報
            </h4>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-accent-success/10 border border-accent-success/20 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">受取プレミアム</div>
                <div className="text-xl font-mono font-bold text-accent-success">
                  {formatUSD(position.entry_premium)}
                </div>
              </div>
              <div className="bg-accent-success/10 border border-accent-success/20 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">最大利益</div>
                <div className="text-xl font-mono font-bold text-accent-success">
                  {formatUSD(position.max_profit)}
                </div>
              </div>
              <div className="bg-accent-danger/10 border border-accent-danger/20 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">最大損失</div>
                <div className="text-xl font-mono font-bold text-accent-danger">
                  {formatUSD(position.max_loss)}
                </div>
              </div>
            </div>
          </div>

          {/* 損益情報 */}
          {isOpen && (
            <div>
              <h4 className="text-sm font-semibold text-gray-400 mb-3">現在の損益</h4>
              <div className="bg-dark-surface rounded-lg p-4">
                <div className="flex items-baseline justify-between mb-2">
                  <span className="text-sm text-gray-400">未実現損益</span>
                  <span className={`text-3xl font-mono font-bold ${
                    unrealizedPnl >= 0 ? 'text-accent-success' : 'text-accent-danger'
                  }`}>
                    {formatUSD(unrealizedPnl)}
                  </span>
                </div>
                <div className="w-full bg-dark-border rounded-full h-2 mt-3">
                  <div
                    className={`h-2 rounded-full ${
                      pnlPercentage >= 0 ? 'bg-accent-success' : 'bg-accent-danger'
                    }`}
                    style={{ width: `${Math.min(Math.abs(pnlPercentage), 100)}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  最大利益の {formatPercent(pnlPercentage / 100, 1)}
                </div>
              </div>
            </div>
          )}

          {/* クローズ情報 */}
          {isClosed && (
            <div>
              <h4 className="text-sm font-semibold text-gray-400 mb-3">クローズ情報</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-400">クローズ日時</div>
                  <div className="text-sm font-mono">
                    {position.closed_at ? formatDateTime(position.closed_at) : '-'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-400">クローズプレミアム</div>
                  <div className="text-lg font-mono">
                    {position.exit_premium !== null ? formatUSD(position.exit_premium) : '-'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-400">実現損益 (USD)</div>
                  <div className={`text-xl font-mono font-bold ${
                    (position.realized_pnl_usd ?? 0) >= 0 ? 'text-accent-success' : 'text-accent-danger'
                  }`}>
                    {position.realized_pnl_usd !== null ? formatUSD(position.realized_pnl_usd) : '-'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-400">実現損益 (JPY)</div>
                  <div className={`text-xl font-mono font-bold ${
                    (position.realized_pnl_jpy ?? 0) >= 0 ? 'text-accent-success' : 'text-accent-danger'
                  }`}>
                    {position.realized_pnl_jpy !== null ? `¥${position.realized_pnl_jpy.toFixed(0)}` : '-'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 為替情報 */}
          {position.fx_rate_usd_jpy && (
            <div>
              <h4 className="text-sm font-semibold text-gray-400 mb-3">為替レート</h4>
              <div className="text-sm font-mono">
                1 USD = ¥{position.fx_rate_usd_jpy.toFixed(2)}
              </div>
            </div>
          )}
        </div>

        {/* フッター */}
        <div className="p-6 border-t border-dark-border flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 btn bg-dark-hover text-gray-300 hover:bg-dark-border"
          >
            閉じる
          </button>
          {isOpen && onClosePosition && (
            <button
              onClick={() => {
                if (confirm('このポジションをクローズしますか？')) {
                  onClosePosition(position.spread_id);
                  onClose();
                }
              }}
              className="flex-1 btn btn-danger"
            >
              ポジションクローズ
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

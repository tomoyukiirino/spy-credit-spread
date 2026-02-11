'use client';

import { TrendingUp, Info, XCircle } from 'lucide-react';
import { formatUSD, formatDateTime, formatPercent } from '@/lib/formatters';
import type { Position } from '@/types';

interface PositionTableProps {
  positions: Position[];
  loading?: boolean;
  onSelectPosition?: (position: Position) => void;
  onClosePosition?: (spreadId: string) => void;
}

export default function PositionTable({
  positions,
  loading,
  onSelectPosition,
  onClosePosition,
}: PositionTableProps) {
  if (loading) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <TrendingUp size={20} className="text-accent-primary" />
          オープンポジション
        </h3>
        <div className="text-gray-500 text-center py-8">読み込み中...</div>
      </div>
    );
  }

  if (positions.length === 0) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <TrendingUp size={20} className="text-accent-primary" />
          オープンポジション
        </h3>
        <div className="text-gray-500 text-center py-8">ポジションがありません</div>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'open':
        return <span className="badge badge-success">OPEN</span>;
      case 'closed':
        return <span className="badge bg-blue-500/20 text-blue-400">CLOSED</span>;
      case 'expired':
        return <span className="badge bg-gray-500/20 text-gray-400">EXPIRED</span>;
      default:
        return <span className="badge bg-gray-500/20 text-gray-400">{status}</span>;
    }
  };

  const calculateDTE = (expiration: string): number => {
    const expiryDate = new Date(expiration);
    const today = new Date();
    const diffTime = expiryDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <TrendingUp size={20} className="text-accent-primary" />
          オープンポジション
        </h3>
        <span className="text-sm text-gray-400">{positions.length}件</span>
      </div>

      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th>Spread ID</th>
              <th>エントリー日時</th>
              <th>満期日</th>
              <th>DTE</th>
              <th>ストライク</th>
              <th className="text-right">プレミアム</th>
              <th className="text-right">最大利益</th>
              <th className="text-right">未実現損益</th>
              <th>ステータス</th>
              <th className="text-right">アクション</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((position) => {
              const dte = calculateDTE(position.expiration);
              const unrealizedPnl = position.unrealized_pnl_usd ?? 0;
              const pnlColor = unrealizedPnl >= 0 ? 'text-accent-success' : 'text-accent-danger';
              const isOpen = position.status === 'open';

              return (
                <tr
                  key={position.spread_id}
                  className="hover:bg-dark-surface cursor-pointer transition-colors"
                  onClick={() => onSelectPosition?.(position)}
                >
                  <td className="font-mono text-sm">{position.spread_id}</td>
                  <td className="font-mono text-sm">
                    {formatDateTime(position.opened_at_jst).split(' ')[0]}
                  </td>
                  <td className="font-mono text-sm">{position.exp_date}</td>
                  <td className="font-mono">
                    <span className={dte <= 1 ? 'text-accent-warning' : ''}>
                      {dte}日
                    </span>
                  </td>
                  <td className="font-mono font-semibold">
                    {position.short_strike} / {position.long_strike}
                  </td>
                  <td className="font-mono text-right text-accent-success">
                    {formatUSD(position.entry_premium)}
                  </td>
                  <td className="font-mono text-right text-accent-success">
                    {formatUSD(position.max_profit)}
                  </td>
                  <td className={`font-mono text-right font-semibold ${pnlColor}`}>
                    {formatUSD(unrealizedPnl)}
                  </td>
                  <td>{getStatusBadge(position.status)}</td>
                  <td className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectPosition?.(position);
                        }}
                        className="text-xs text-accent-primary hover:text-accent-primary/80"
                      >
                        <Info size={16} />
                      </button>
                      {isOpen && onClosePosition && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (confirm('このポジションをクローズしますか？')) {
                              onClosePosition(position.spread_id);
                            }
                          }}
                          className="text-xs text-accent-danger hover:text-accent-danger/80"
                        >
                          <XCircle size={16} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

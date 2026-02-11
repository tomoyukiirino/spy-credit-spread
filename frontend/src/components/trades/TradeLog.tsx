'use client';

import { FileText, Download, Info } from 'lucide-react';
import { formatUSD, formatDateTime } from '@/lib/formatters';
import type { TradeRecord } from '@/types';

interface TradeLogProps {
  trades: TradeRecord[];
  loading?: boolean;
  onSelectTrade?: (trade: TradeRecord) => void;
  onExport?: () => void;
}

export default function TradeLog({ trades, loading, onSelectTrade, onExport }: TradeLogProps) {
  if (loading) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileText size={20} className="text-accent-primary" />
          取引履歴
        </h3>
        <div className="text-gray-500 text-center py-8">読み込み中...</div>
      </div>
    );
  }

  if (trades.length === 0) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileText size={20} className="text-accent-primary" />
          取引履歴
        </h3>
        <div className="text-gray-500 text-center py-8">取引履歴がありません</div>
      </div>
    );
  }

  const getActionBadge = (action: string) => {
    if (action === 'SELL') {
      return <span className="badge bg-red-500/20 text-red-400">SELL</span>;
    }
    return <span className="badge bg-green-500/20 text-green-400">BUY</span>;
  };

  const getLegBadge = (leg: string) => {
    if (leg === 'short') {
      return <span className="text-xs bg-orange-500/20 text-orange-400 px-2 py-1 rounded">Short</span>;
    }
    return <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded">Long</span>;
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <FileText size={20} className="text-accent-primary" />
          取引履歴
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-400">{trades.length}件</span>
          {onExport && (
            <button
              onClick={onExport}
              className="btn btn-primary flex items-center gap-2 text-xs"
            >
              <Download size={14} />
              CSV出力
            </button>
          )}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th>取引日</th>
              <th>時刻 (JST)</th>
              <th>アクション</th>
              <th>銘柄</th>
              <th>ストライク</th>
              <th>満期日</th>
              <th>レッグ</th>
              <th className="text-right">数量</th>
              <th className="text-right">単価</th>
              <th className="text-right">合計額</th>
              <th className="text-right">手数料</th>
              <th className="text-right">純額</th>
              <th>Spread ID</th>
              <th className="text-right">詳細</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade) => {
              const isCredit = trade.net_amount_usd > 0;
              const netAmountColor = isCredit ? 'text-accent-success' : 'text-accent-danger';

              return (
                <tr
                  key={trade.trade_id}
                  className="hover:bg-dark-surface cursor-pointer transition-colors"
                  onClick={() => onSelectTrade?.(trade)}
                >
                  <td className="font-mono text-sm">{trade.trade_date_jst}</td>
                  <td className="font-mono text-sm">
                    {formatDateTime(trade.timestamp_jst).split(' ')[1]}
                  </td>
                  <td>{getActionBadge(trade.action)}</td>
                  <td className="font-mono font-semibold">{trade.symbol}</td>
                  <td className="font-mono">${trade.strike}</td>
                  <td className="font-mono text-sm">{trade.expiry}</td>
                  <td>{getLegBadge(trade.leg)}</td>
                  <td className="font-mono text-right">{trade.quantity}</td>
                  <td className="font-mono text-right">
                    {formatUSD(trade.premium_per_contract)}
                  </td>
                  <td className="font-mono text-right">
                    {formatUSD(Math.abs(trade.total_premium_usd))}
                  </td>
                  <td className="font-mono text-right text-accent-danger">
                    {formatUSD(trade.commission_usd)}
                  </td>
                  <td className={`font-mono text-right font-semibold ${netAmountColor}`}>
                    {formatUSD(trade.net_amount_usd)}
                  </td>
                  <td className="font-mono text-xs text-gray-400">
                    {trade.spread_id.split('-').slice(1, 3).join('-')}
                  </td>
                  <td className="text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectTrade?.(trade);
                      }}
                      className="text-accent-primary hover:text-accent-primary/80"
                    >
                      <Info size={16} />
                    </button>
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

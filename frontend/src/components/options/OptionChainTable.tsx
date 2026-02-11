'use client';

import { formatStrike, formatDelta, formatIV, formatUSD } from '@/lib/formatters';
import type { OptionData } from '@/types';

interface OptionChainTableProps {
  options: OptionData[];
  loading?: boolean;
  onSelectOption?: (option: OptionData) => void;
}

export default function OptionChainTable({ options, loading, onSelectOption }: OptionChainTableProps) {
  if (loading) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">オプションチェーン</h3>
        <div className="text-gray-500 text-center py-8">読み込み中...</div>
      </div>
    );
  }

  if (options.length === 0) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">オプションチェーン</h3>
        <div className="text-gray-500 text-center py-8">データがありません</div>
      </div>
    );
  }

  // 満期日でグループ化
  const optionsByExpiry = options.reduce((acc, option) => {
    if (!acc[option.expiry]) {
      acc[option.expiry] = [];
    }
    acc[option.expiry].push(option);
    return acc;
  }, {} as Record<string, OptionData[]>);

  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-4">オプションチェーン</h3>

      {Object.entries(optionsByExpiry).map(([expiry, expiryOptions]) => {
        const firstOption = expiryOptions[0];
        const expDate = firstOption.exp_date;
        const dte = firstOption.dte;

        return (
          <div key={expiry} className="mb-6 last:mb-0">
            <h4 className="text-sm font-semibold mb-3 text-gray-400">
              {expDate} (DTE: {dte}日)
            </h4>

            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>ストライク</th>
                    <th>デルタ</th>
                    <th>IV</th>
                    <th className="text-right">Bid</th>
                    <th className="text-right">Ask</th>
                    <th className="text-right">Mid</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {expiryOptions
                    .sort((a, b) => b.strike - a.strike)
                    .map((option, index) => (
                      <tr
                        key={`${expiry}-${option.strike}`}
                        className="hover:bg-dark-surface cursor-pointer transition-colors"
                        onClick={() => onSelectOption?.(option)}
                      >
                        <td className="font-mono font-semibold">{formatStrike(option.strike)}</td>
                        <td className="font-mono">
                          <span className={option.delta && option.delta >= 0.15 && option.delta <= 0.25 ? 'text-accent-success' : ''}>
                            {formatDelta(option.delta)}
                          </span>
                        </td>
                        <td className="font-mono">{formatIV(option.iv)}</td>
                        <td className="font-mono text-right text-gray-400">{formatUSD(option.bid)}</td>
                        <td className="font-mono text-right text-gray-400">{formatUSD(option.ask)}</td>
                        <td className="font-mono text-right">{formatUSD(option.mid)}</td>
                        <td className="text-right">
                          {onSelectOption && (
                            <button className="text-xs text-accent-primary hover:text-accent-primary/80">
                              選択
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
    </div>
  );
}

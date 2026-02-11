'use client';

import { TrendingUp } from 'lucide-react';
import { formatStrike, formatDelta, formatUSD, formatPercent, formatIV } from '@/lib/formatters';
import type { SpreadCandidate } from '@/types';

interface SpreadCandidatesProps {
  candidates: SpreadCandidate[];
  loading?: boolean;
  onSelectSpread?: (spread: SpreadCandidate) => void;
}

export default function SpreadCandidates({ candidates, loading, onSelectSpread }: SpreadCandidatesProps) {
  if (loading) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <TrendingUp size={20} className="text-accent-success" />
          スプレッド候補
        </h3>
        <div className="text-gray-500 text-center py-8">読み込み中...</div>
      </div>
    );
  }

  if (candidates.length === 0) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <TrendingUp size={20} className="text-accent-success" />
          スプレッド候補
        </h3>
        <div className="text-gray-500 text-center py-8">候補がありません</div>
      </div>
    );
  }

  // スコアでソート
  const sortedCandidates = [...candidates].sort((a, b) => {
    const scoreA = a.score ?? 0;
    const scoreB = b.score ?? 0;
    return scoreB - scoreA;
  });

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <TrendingUp size={20} className="text-accent-success" />
          スプレッド候補
        </h3>
        <span className="text-sm text-gray-400">{candidates.length}件</span>
      </div>

      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th>満期日</th>
              <th>DTE</th>
              <th>ストライク</th>
              <th>δ</th>
              <th>IV</th>
              <th className="text-right">プレミアム</th>
              <th className="text-right">最大利益</th>
              <th className="text-right">R/R</th>
              <th className="text-right">勝率</th>
              <th className="text-right">スコア</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sortedCandidates.map((candidate, index) => {
              const isTopPick = index === 0;
              const scoreColor = (candidate.score ?? 0) >= 70 ? 'text-accent-success' :
                                 (candidate.score ?? 0) >= 50 ? 'text-accent-warning' :
                                 'text-gray-400';

              return (
                <tr
                  key={`${candidate.expiry}-${candidate.short_strike}`}
                  className={`hover:bg-dark-surface cursor-pointer transition-colors ${
                    isTopPick ? 'bg-accent-success/5' : ''
                  }`}
                  onClick={() => onSelectSpread?.(candidate)}
                >
                  <td className="font-mono text-sm">{candidate.exp_date}</td>
                  <td className="font-mono">{candidate.dte}</td>
                  <td className="font-mono font-semibold">
                    {formatStrike(candidate.short_strike)} / {formatStrike(candidate.long_strike)}
                  </td>
                  <td className="font-mono">
                    <span className="text-accent-success">{formatDelta(candidate.short_delta)}</span>
                  </td>
                  <td className="font-mono text-sm">{formatIV(candidate.short_iv)}</td>
                  <td className="font-mono text-right">{formatUSD(candidate.spread_premium_mid)}</td>
                  <td className="font-mono text-right text-accent-success">
                    {formatUSD(candidate.max_profit)}
                  </td>
                  <td className="font-mono text-right text-sm">
                    {candidate.risk_reward_ratio?.toFixed(2)}
                  </td>
                  <td className="font-mono text-right">
                    {candidate.win_probability ? formatPercent(candidate.win_probability, 0) : '-'}
                  </td>
                  <td className={`font-mono text-right font-semibold ${scoreColor}`}>
                    {candidate.score?.toFixed(0)}
                  </td>
                  <td className="text-right">
                    {isTopPick && (
                      <span className="text-xs bg-accent-success text-white px-2 py-1 rounded">
                        推奨
                      </span>
                    )}
                    {onSelectSpread && !isTopPick && (
                      <button className="text-xs text-accent-primary hover:text-accent-primary/80">
                        詳細
                      </button>
                    )}
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

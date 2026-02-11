'use client';

import { X, TrendingUp, TrendingDown, Target, Calendar, DollarSign } from 'lucide-react';
import { formatStrike, formatDelta, formatUSD, formatPercent, formatIV, formatExpiry } from '@/lib/formatters';
import type { SpreadCandidate } from '@/types';

interface SpreadDetailProps {
  spread: SpreadCandidate | null;
  onClose: () => void;
  onExecute?: (spread: SpreadCandidate) => void;
}

export default function SpreadDetail({ spread, onClose, onExecute }: SpreadDetailProps) {
  if (!spread) return null;

  const winProbability = spread.win_probability ?? 0;
  const riskRewardRatio = spread.risk_reward_ratio ?? 0;
  const score = spread.score ?? 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-card border border-dark-border rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* ヘッダー */}
        <div className="flex items-center justify-between p-6 border-b border-dark-border">
          <h3 className="text-xl font-semibold">Bull Put Spread 詳細</h3>
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
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-sm text-gray-400">満期日</div>
                <div className="text-lg font-mono">{formatExpiry(spread.expiry)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">DTE</div>
                <div className="text-lg font-mono">{spread.dte}日</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">スプレッド幅</div>
                <div className="text-lg font-mono">
                  ${(spread.short_strike - spread.long_strike).toFixed(0)}
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
                <div className="text-2xl font-mono font-bold mb-2">{formatStrike(spread.short_strike)}</div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">デルタ</span>
                  <span className="font-mono text-accent-success">{formatDelta(spread.short_delta)}</span>
                </div>
                <div className="flex justify-between text-sm mt-1">
                  <span className="text-gray-400">IV</span>
                  <span className="font-mono">{formatIV(spread.short_iv)}</span>
                </div>
              </div>

              <div className="bg-dark-surface rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-2">買いプット (Long)</div>
                <div className="text-2xl font-mono font-bold mb-2">{formatStrike(spread.long_strike)}</div>
                <div className="text-sm text-gray-400">
                  保護レベル
                </div>
              </div>
            </div>
          </div>

          {/* P&L情報 */}
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
              <DollarSign size={16} />
              損益プロファイル
            </h4>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-accent-success/10 border border-accent-success/20 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">プレミアム</div>
                <div className="text-xl font-mono font-bold text-accent-success">
                  {formatUSD(spread.spread_premium_mid)}
                </div>
              </div>

              <div className="bg-accent-success/10 border border-accent-success/20 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1 flex items-center gap-1">
                  <TrendingUp size={14} />
                  最大利益
                </div>
                <div className="text-xl font-mono font-bold text-accent-success">
                  {formatUSD(spread.max_profit)}
                </div>
              </div>

              <div className="bg-accent-danger/10 border border-accent-danger/20 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1 flex items-center gap-1">
                  <TrendingDown size={14} />
                  最大損失
                </div>
                <div className="text-xl font-mono font-bold text-accent-danger">
                  {formatUSD(spread.max_loss)}
                </div>
              </div>
            </div>
          </div>

          {/* 評価指標 */}
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-3">評価指標</h4>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">リスク/リワード比</span>
                  <span className="font-mono">{riskRewardRatio.toFixed(2)}</span>
                </div>
                <div className="w-full bg-dark-surface rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      riskRewardRatio <= 3 ? 'bg-accent-success' :
                      riskRewardRatio <= 5 ? 'bg-accent-warning' :
                      'bg-accent-danger'
                    }`}
                    style={{ width: `${Math.min((3 / riskRewardRatio) * 100, 100)}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">勝率（推定）</span>
                  <span className="font-mono">{formatPercent(winProbability, 0)}</span>
                </div>
                <div className="w-full bg-dark-surface rounded-full h-2">
                  <div
                    className="h-2 rounded-full bg-accent-success"
                    style={{ width: `${winProbability * 100}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">総合スコア</span>
                  <span className={`font-mono font-semibold ${
                    score >= 70 ? 'text-accent-success' :
                    score >= 50 ? 'text-accent-warning' :
                    'text-gray-400'
                  }`}>
                    {score.toFixed(0)} / 100
                  </span>
                </div>
                <div className="w-full bg-dark-surface rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      score >= 70 ? 'bg-accent-success' :
                      score >= 50 ? 'bg-accent-warning' :
                      'bg-gray-500'
                    }`}
                    style={{ width: `${score}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* フッター */}
        <div className="p-6 border-t border-dark-border flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 btn bg-dark-hover text-gray-300 hover:bg-dark-border"
          >
            キャンセル
          </button>
          {onExecute && (
            <button
              onClick={() => onExecute(spread)}
              className="flex-1 btn btn-success"
            >
              この銘柄で発注
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

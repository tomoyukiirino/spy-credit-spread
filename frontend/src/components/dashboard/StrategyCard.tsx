'use client';

import { Target, Calendar, DollarSign } from 'lucide-react';
import type { AccountSummary } from '@/types';

interface StrategyCardProps {
  data: AccountSummary | null;
  loading?: boolean;
}

export default function StrategyCard({ data, loading }: StrategyCardProps) {
  if (loading || !data) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Target size={20} className="text-accent-secondary" />
          戦略パラメータ
        </h2>
        <div className="text-gray-500">読み込み中...</div>
      </div>
    );
  }

  const { strategy_params } = data;

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Target size={20} className="text-accent-secondary" />
        戦略パラメータ
      </h2>

      <div className="space-y-4">
        {/* 基本設定 */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-400 mb-1">シンボル</div>
            <div className="text-lg font-semibold">{strategy_params.symbol}</div>
          </div>
          <div>
            <div className="text-sm text-gray-400 mb-1">スプレッド幅</div>
            <div className="text-lg font-mono">${strategy_params.spread_width}</div>
          </div>
        </div>

        {/* デルタ設定 */}
        <div className="pt-3 border-t border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <Target size={14} className="text-accent-primary" />
            <span className="text-sm font-semibold">デルタ</span>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-400 mb-1">目標値</div>
              <div className="text-lg font-mono">{strategy_params.target_delta.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400 mb-1">許容範囲</div>
              <div className="text-lg font-mono">
                {strategy_params.delta_range[0].toFixed(2)} - {strategy_params.delta_range[1].toFixed(2)}
              </div>
            </div>
          </div>
        </div>

        {/* DTE設定 */}
        <div className="pt-3 border-t border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <Calendar size={14} className="text-accent-warning" />
            <span className="text-sm font-semibold">DTE（満期日数）</span>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-400 mb-1">最小</div>
              <div className="text-lg font-mono">{strategy_params.min_dte}日</div>
            </div>
            <div>
              <div className="text-sm text-gray-400 mb-1">最大</div>
              <div className="text-lg font-mono">{strategy_params.max_dte}日</div>
            </div>
          </div>
        </div>

        {/* リスク設定 */}
        <div className="pt-3 border-t border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <DollarSign size={14} className="text-accent-danger" />
            <span className="text-sm font-semibold">リスク</span>
          </div>
          <div>
            <div className="text-sm text-gray-400 mb-1">1取引あたり</div>
            <div className="text-lg font-mono">{(strategy_params.risk_per_trade * 100).toFixed(0)}%</div>
          </div>
        </div>
      </div>
    </div>
  );
}

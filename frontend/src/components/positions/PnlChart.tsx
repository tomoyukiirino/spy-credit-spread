'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { TrendingUp } from 'lucide-react';
import { formatUSD } from '@/lib/formatters';
import type { PnlData } from '@/types';

interface PnlChartProps {
  data: PnlData[];
  loading?: boolean;
  timeRange?: 'day' | 'week' | 'month' | 'all';
  onTimeRangeChange?: (range: 'day' | 'week' | 'month' | 'all') => void;
}

export default function PnlChart({ data, loading, timeRange = 'week', onTimeRangeChange }: PnlChartProps) {
  if (loading) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <TrendingUp size={20} className="text-accent-success" />
          損益チャート
        </h3>
        <div className="text-gray-500 text-center py-8">読み込み中...</div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <TrendingUp size={20} className="text-accent-success" />
          損益チャート
        </h3>
        <div className="text-gray-500 text-center py-8">データがありません</div>
      </div>
    );
  }

  // 最新の損益
  const latestData = data[data.length - 1];
  const totalPnl = latestData?.total_pnl ?? 0;
  const realizedPnl = latestData?.realized_pnl ?? 0;
  const unrealizedPnl = latestData?.unrealized_pnl ?? 0;

  // カスタムツールチップ
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-dark-card border border-dark-border rounded-lg p-3 shadow-lg">
          <div className="text-sm font-mono mb-2">{data.date}</div>
          <div className="space-y-1">
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-gray-400">実現損益:</span>
              <span className={`text-sm font-mono font-semibold ${
                data.realized_pnl >= 0 ? 'text-accent-success' : 'text-accent-danger'
              }`}>
                {formatUSD(data.realized_pnl)}
              </span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-gray-400">未実現損益:</span>
              <span className={`text-sm font-mono font-semibold ${
                data.unrealized_pnl >= 0 ? 'text-accent-success' : 'text-accent-danger'
              }`}>
                {formatUSD(data.unrealized_pnl)}
              </span>
            </div>
            <div className="flex items-center justify-between gap-4 pt-1 border-t border-dark-border">
              <span className="text-xs text-gray-400">合計:</span>
              <span className={`text-sm font-mono font-bold ${
                data.total_pnl >= 0 ? 'text-accent-success' : 'text-accent-danger'
              }`}>
                {formatUSD(data.total_pnl)}
              </span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <TrendingUp size={20} className="text-accent-success" />
          損益チャート
        </h3>
        {onTimeRangeChange && (
          <div className="flex gap-2">
            {(['day', 'week', 'month', 'all'] as const).map((range) => (
              <button
                key={range}
                onClick={() => onTimeRangeChange(range)}
                className={`px-3 py-1 text-xs rounded transition-colors ${
                  timeRange === range
                    ? 'bg-accent-primary text-white'
                    : 'bg-dark-hover text-gray-400 hover:text-white'
                }`}
              >
                {range === 'day' && '日'}
                {range === 'week' && '週'}
                {range === 'month' && '月'}
                {range === 'all' && '全期間'}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* サマリー */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-dark-surface rounded-lg p-3">
          <div className="text-xs text-gray-400 mb-1">実現損益</div>
          <div className={`text-xl font-mono font-bold ${
            realizedPnl >= 0 ? 'text-accent-success' : 'text-accent-danger'
          }`}>
            {formatUSD(realizedPnl)}
          </div>
        </div>
        <div className="bg-dark-surface rounded-lg p-3">
          <div className="text-xs text-gray-400 mb-1">未実現損益</div>
          <div className={`text-xl font-mono font-bold ${
            unrealizedPnl >= 0 ? 'text-accent-success' : 'text-accent-danger'
          }`}>
            {formatUSD(unrealizedPnl)}
          </div>
        </div>
        <div className="bg-dark-surface rounded-lg p-3">
          <div className="text-xs text-gray-400 mb-1">合計損益</div>
          <div className={`text-xl font-mono font-bold ${
            totalPnl >= 0 ? 'text-accent-success' : 'text-accent-danger'
          }`}>
            {formatUSD(totalPnl)}
          </div>
        </div>
      </div>

      {/* チャート */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="date"
              stroke="#9ca3af"
              style={{ fontSize: '12px', fontFamily: 'monospace' }}
            />
            <YAxis
              stroke="#9ca3af"
              style={{ fontSize: '12px', fontFamily: 'monospace' }}
              tickFormatter={(value) => `$${value}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="3 3" />
            <Line
              type="monotone"
              dataKey="realized_pnl"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ fill: '#3b82f6', r: 3 }}
              name="実現損益"
            />
            <Line
              type="monotone"
              dataKey="unrealized_pnl"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={{ fill: '#f59e0b', r: 3 }}
              name="未実現損益"
            />
            <Line
              type="monotone"
              dataKey="total_pnl"
              stroke="#10b981"
              strokeWidth={3}
              dot={{ fill: '#10b981', r: 4 }}
              name="合計損益"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center gap-6 mt-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500" />
          <span className="text-gray-400">実現損益</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <span className="text-gray-400">未実現損益</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-gray-400">合計損益</span>
        </div>
      </div>
    </div>
  );
}

'use client';

import { TrendingUp, Clock, Wifi } from 'lucide-react';
import { formatUSD, formatRelativeTime } from '@/lib/formatters';
import PriceFlash from '@/components/common/PriceFlash';
import type { SpyPrice } from '@/types';

interface SpyPriceCardProps {
  data: SpyPrice | null;
  loading?: boolean;
  priceChange?: 'up' | 'down' | null;
  isLive?: boolean;
}

export default function SpyPriceCard({ data, loading, priceChange, isLive }: SpyPriceCardProps) {
  if (loading || !data) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <TrendingUp size={20} className="text-accent-success" />
          SPY 価格
        </h2>
        <div className="text-gray-500">読み込み中...</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <TrendingUp size={20} className="text-accent-success" />
          SPY 価格
        </h2>
        <div className="flex items-center gap-2">
          {isLive && (
            <span className="text-xs text-accent-success flex items-center gap-1">
              <Wifi size={12} className="animate-pulse" />
              Live
            </span>
          )}
          {data.is_delayed && (
            <span className="text-xs text-accent-warning">遅延</span>
          )}
        </div>
      </div>

      <div className="space-y-4">
        {/* 現在価格 */}
        <div>
          <div className="text-sm text-gray-400 mb-1">Last</div>
          <PriceFlash direction={priceChange || null}>
            <div className="text-3xl font-bold font-mono">
              {data.last !== null ? formatUSD(data.last) : '-'}
            </div>
          </PriceFlash>
        </div>

        {/* Bid/Ask/Mid */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-xs text-gray-400 mb-1">Bid</div>
            <div className="text-lg font-mono">
              {data.bid !== null ? formatUSD(data.bid) : '-'}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-1">Ask</div>
            <div className="text-lg font-mono">
              {data.ask !== null ? formatUSD(data.ask) : '-'}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-1">Mid</div>
            <div className="text-lg font-mono">
              {data.mid !== null ? formatUSD(data.mid) : '-'}
            </div>
          </div>
        </div>

        {/* タイムスタンプ */}
        <div className="pt-3 border-t border-dark-border flex items-center gap-2 text-xs text-gray-500">
          <Clock size={12} />
          <span>{formatRelativeTime(data.timestamp)}</span>
        </div>
      </div>
    </div>
  );
}

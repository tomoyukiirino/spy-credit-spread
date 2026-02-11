'use client';

import { Clock, DollarSign } from 'lucide-react';
import { useEffect, useState } from 'react';
import { formatDateTime, formatUSD } from '@/lib/formatters';

interface StatusBarProps {
  spyPrice?: number | null;
  fxRate?: number | null;
}

export default function StatusBar({ spyPrice, fxRate }: StatusBarProps) {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="h-10 bg-dark-surface border-t border-dark-border flex items-center justify-between px-6 text-sm">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <Clock size={14} className="text-gray-500" />
          <span className="text-gray-400" suppressHydrationWarning>
            {mounted ? formatDateTime(currentTime.toISOString()) : ''}
          </span>
        </div>

        {spyPrice !== null && spyPrice !== undefined && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500">SPY:</span>
            <span className="text-white font-mono">{formatUSD(spyPrice)}</span>
          </div>
        )}

        {fxRate !== null && fxRate !== undefined && (
          <div className="flex items-center gap-2">
            <DollarSign size={14} className="text-gray-500" />
            <span className="text-gray-500">USD/JPY:</span>
            <span className="text-white font-mono">¥{fxRate.toFixed(2)}</span>
          </div>
        )}
      </div>

      <div className="text-gray-500 text-xs">
        Ready
      </div>
    </div>
  );
}

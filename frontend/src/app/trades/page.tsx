'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import Sidebar from '@/components/layout/Sidebar';
import StatusBar from '@/components/layout/StatusBar';
import TradeLog from '@/components/trades/TradeLog';
import TradeDetail from '@/components/trades/TradeDetail';
import { getHealth } from '@/lib/api';
import { useSpyPrice, useFxRate } from '@/hooks/useWebSocket';
import type { TradeRecord, SpyPrice } from '@/types';

export default function TradesPage() {
  const [healthData, setHealthData] = useState<{
    ibkr_connected: boolean;
    mode: 'mock' | 'real';
  } | null>(null);
  const [spyData, setSpyData] = useState<SpyPrice | null>(null);
  const [trades, setTrades] = useState<TradeRecord[]>([]);
  const [selectedTrade, setSelectedTrade] = useState<TradeRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // WebSocketでリアルタイム更新
  const { spyPrice: liveSpyPrice } = useSpyPrice();
  const { fxRate: liveFxRate } = useFxRate();

  // データ取得
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        const [health, tradesRes] = await Promise.all([
          getHealth(),
          fetch('http://localhost:8000/api/trades').then(r => r.json()),
        ]);

        setHealthData({
          ibkr_connected: health.ibkr_connected,
          mode: health.mode as 'mock' | 'real',
        });
        setTrades(tradesRes.trades || []);
      } catch (err) {
        console.error('Failed to fetch data:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const handleSelectTrade = (trade: TradeRecord) => {
    setSelectedTrade(trade);
  };

  const handleCloseDetail = () => {
    setSelectedTrade(null);
  };

  const handleExport = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/trades/export-csv');

      if (!response.ok) {
        throw new Error('Failed to export CSV');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `trades_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      alert('CSVファイルをダウンロードしました');
    } catch (err) {
      console.error('Failed to export CSV:', err);
      alert('CSV出力に失敗しました');
    }
  };

  return (
    <div className="h-screen flex flex-col">
      <Header
        ibkrConnected={healthData?.ibkr_connected ?? false}
        mode={healthData?.mode ?? 'mock'}
      />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar currentPage="trades" />

        <main className="flex-1 overflow-auto p-6">
          {error ? (
            <div className="card bg-accent-danger/10 border-accent-danger text-accent-danger">
              <h3 className="font-semibold mb-2">エラー</h3>
              <p>{error}</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* 取引ログ */}
              <TradeLog
                trades={trades}
                loading={loading}
                onSelectTrade={handleSelectTrade}
                onExport={handleExport}
              />
            </div>
          )}
        </main>
      </div>

      <StatusBar
        spyPrice={liveSpyPrice ?? spyData?.last ?? null}
        fxRate={liveFxRate}
      />

      {/* 取引詳細モーダル */}
      {selectedTrade && (
        <TradeDetail
          trade={selectedTrade}
          onClose={handleCloseDetail}
        />
      )}
    </div>
  );
}

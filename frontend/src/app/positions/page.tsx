'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import Sidebar from '@/components/layout/Sidebar';
import StatusBar from '@/components/layout/StatusBar';
import PositionTable from '@/components/positions/PositionTable';
import PositionDetail from '@/components/positions/PositionDetail';
import PnlChart from '@/components/positions/PnlChart';
import { getHealth } from '@/lib/api';
import { useSpyPrice, useFxRate } from '@/hooks/useWebSocket';
import type { Position, PnlData, SpyPrice } from '@/types';

export default function PositionsPage() {
  const [healthData, setHealthData] = useState<{
    ibkr_connected: boolean;
    mode: 'mock' | 'real';
  } | null>(null);
  const [spyData, setSpyData] = useState<SpyPrice | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [pnlData, setPnlData] = useState<PnlData[]>([]);
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<'day' | 'week' | 'month' | 'all'>('week');

  // WebSocketでリアルタイム更新
  const { spyPrice: liveSpyPrice } = useSpyPrice();
  const { fxRate: liveFxRate } = useFxRate();

  // データ取得
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        const [health, positionsRes, pnlRes] = await Promise.all([
          getHealth(),
          fetch('http://localhost:8000/api/positions?status=open').then(r => r.json()),
          fetch('http://localhost:8000/api/positions/pnl-history?range=week').then(r => r.json()),
        ]);

        setHealthData({
          ibkr_connected: health.ibkr_connected,
          mode: health.mode as 'mock' | 'real',
        });
        setPositions(positionsRes.positions || []);
        setPnlData(pnlRes.data || []);
      } catch (err) {
        console.error('Failed to fetch data:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  // 定期更新（30秒ごと）
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [health, positionsRes] = await Promise.all([
          getHealth(),
          fetch('http://localhost:8000/api/positions?status=open').then(r => r.json()),
        ]);

        setHealthData({
          ibkr_connected: health.ibkr_connected,
          mode: health.mode as 'mock' | 'real',
        });
        setPositions(positionsRes.positions || []);
      } catch (err) {
        console.error('Failed to refresh data:', err);
      }
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // 時間範囲変更時にP&Lデータを再取得
  useEffect(() => {
    async function fetchPnlData() {
      try {
        const pnlRes = await fetch(
          `http://localhost:8000/api/positions/pnl-history?range=${timeRange}`
        ).then(r => r.json());
        setPnlData(pnlRes.data || []);
      } catch (err) {
        console.error('Failed to fetch P&L data:', err);
      }
    }

    fetchPnlData();
  }, [timeRange]);

  const handleSelectPosition = (position: Position) => {
    setSelectedPosition(position);
  };

  const handleCloseDetail = () => {
    setSelectedPosition(null);
  };

  const handleClosePosition = async (spreadId: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/positions/${spreadId}/close`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to close position');
      }

      // ポジションリストを更新
      const positionsRes = await fetch(
        'http://localhost:8000/api/positions?status=open'
      ).then(r => r.json());
      setPositions(positionsRes.positions || []);

      alert('ポジションをクローズしました');
    } catch (err) {
      console.error('Failed to close position:', err);
      alert('ポジションのクローズに失敗しました');
    }
  };

  return (
    <div className="h-screen flex flex-col">
      <Header
        ibkrConnected={healthData?.ibkr_connected ?? false}
        mode={healthData?.mode ?? 'mock'}
      />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar currentPage="positions" />

        <main className="flex-1 overflow-auto p-6">
          {error ? (
            <div className="card bg-accent-danger/10 border-accent-danger text-accent-danger">
              <h3 className="font-semibold mb-2">エラー</h3>
              <p>{error}</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* P&Lチャート */}
              <PnlChart
                data={pnlData}
                loading={loading}
                timeRange={timeRange}
                onTimeRangeChange={setTimeRange}
              />

              {/* ポジションテーブル */}
              <PositionTable
                positions={positions}
                loading={loading}
                onSelectPosition={handleSelectPosition}
                onClosePosition={handleClosePosition}
              />
            </div>
          )}
        </main>
      </div>

      <StatusBar
        spyPrice={liveSpyPrice ?? spyData?.last ?? null}
        fxRate={liveFxRate}
      />

      {/* ポジション詳細モーダル */}
      {selectedPosition && (
        <PositionDetail
          position={selectedPosition}
          onClose={handleCloseDetail}
          onClosePosition={handleClosePosition}
        />
      )}
    </div>
  );
}

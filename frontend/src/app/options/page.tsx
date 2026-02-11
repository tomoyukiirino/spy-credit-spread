'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import Sidebar from '@/components/layout/Sidebar';
import StatusBar from '@/components/layout/StatusBar';
import OptionChainTable from '@/components/options/OptionChainTable';
import SpreadCandidates from '@/components/options/SpreadCandidates';
import SpreadDetail from '@/components/options/SpreadDetail';
import { getHealth, getSpyPrice } from '@/lib/api';
import { useSpyPrice, useFxRate } from '@/hooks/useWebSocket';
import type { OptionData, SpreadCandidate, SpyPrice } from '@/types';

export default function OptionsPage() {
  const [healthData, setHealthData] = useState<{
    ibkr_connected: boolean;
    mode: 'mock' | 'real';
  } | null>(null);
  const [spyData, setSpyData] = useState<SpyPrice | null>(null);
  const [options, setOptions] = useState<OptionData[]>([]);
  const [candidates, setCandidates] = useState<SpreadCandidate[]>([]);
  const [selectedSpread, setSelectedSpread] = useState<SpreadCandidate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // WebSocketでリアルタイム更新
  const { spyPrice: liveSpyPrice, isConnected: wsConnected } = useSpyPrice();
  const { fxRate: liveFxRate } = useFxRate();

  // データ取得
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        const [health, spy, optionsRes, candidatesRes] = await Promise.all([
          getHealth(),
          getSpyPrice(),
          fetch('http://localhost:8000/api/options/chain?dte_min=1&dte_max=7').then(r => r.json()),
          fetch('http://localhost:8000/api/options/spreads').then(r => r.json()),
        ]);

        setHealthData({
          ibkr_connected: health.ibkr_connected,
          mode: health.mode as 'mock' | 'real',
        });
        setSpyData(spy);
        setOptions(optionsRes.options || []);
        setCandidates(candidatesRes.candidates || []);
      } catch (err) {
        console.error('Failed to fetch data:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  // WebSocketからの価格更新をspyDataに反映
  useEffect(() => {
    if (liveSpyPrice !== null && spyData) {
      setSpyData({
        ...spyData,
        last: liveSpyPrice,
        mid: liveSpyPrice,
        timestamp: new Date().toISOString(),
      });
    }
  }, [liveSpyPrice]);

  // 定期更新（1分ごと - オプションチェーンとヘルス情報のみ）
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [health, optionsRes, candidatesRes] = await Promise.all([
          getHealth(),
          fetch('http://localhost:8000/api/options/chain?dte_min=1&dte_max=7').then(r => r.json()),
          fetch('http://localhost:8000/api/options/spreads').then(r => r.json()),
        ]);

        setHealthData({
          ibkr_connected: health.ibkr_connected,
          mode: health.mode as 'mock' | 'real',
        });
        setOptions(optionsRes.options || []);
        setCandidates(candidatesRes.candidates || []);
      } catch (err) {
        console.error('Failed to refresh data:', err);
      }
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  const handleSelectSpread = (spread: SpreadCandidate) => {
    setSelectedSpread(spread);
  };

  const handleCloseDetail = () => {
    setSelectedSpread(null);
  };

  const handleExecuteSpread = (spread: SpreadCandidate) => {
    // TODO: 注文実行処理
    console.log('Execute spread:', spread);
    alert('注文機能は未実装です');
    setSelectedSpread(null);
  };

  return (
    <div className="h-screen flex flex-col">
      <Header
        ibkrConnected={healthData?.ibkr_connected ?? false}
        mode={healthData?.mode ?? 'mock'}
      />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar currentPage="options" />

        <main className="flex-1 overflow-auto p-6">
          {error ? (
            <div className="card bg-accent-danger/10 border-accent-danger text-accent-danger">
              <h3 className="font-semibold mb-2">エラー</h3>
              <p>{error}</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* スプレッド候補 */}
              <SpreadCandidates
                candidates={candidates}
                loading={loading}
                onSelectSpread={handleSelectSpread}
              />

              {/* オプションチェーン */}
              <OptionChainTable
                options={options}
                loading={loading}
              />
            </div>
          )}
        </main>
      </div>

      <StatusBar
        spyPrice={liveSpyPrice ?? spyData?.last ?? null}
        fxRate={liveFxRate}
      />

      {/* スプレッド詳細モーダル */}
      {selectedSpread && (
        <SpreadDetail
          spread={selectedSpread}
          onClose={handleCloseDetail}
          onExecute={handleExecuteSpread}
        />
      )}
    </div>
  );
}

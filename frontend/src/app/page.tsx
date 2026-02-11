'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import Sidebar from '@/components/layout/Sidebar';
import StatusBar from '@/components/layout/StatusBar';
import AccountCard from '@/components/dashboard/AccountCard';
import SpyPriceCard from '@/components/dashboard/SpyPriceCard';
import StrategyCard from '@/components/dashboard/StrategyCard';
import { getHealth, getAccountSummary, getSpyPrice } from '@/lib/api';
import { useSpyPrice, useFxRate } from '@/hooks/useWebSocket';
import type { AccountSummary, SpyPrice } from '@/types';

export default function Home() {
  const [healthData, setHealthData] = useState<{
    ibkr_connected: boolean;
    mode: 'mock' | 'real';
  } | null>(null);
  const [accountData, setAccountData] = useState<AccountSummary | null>(null);
  const [spyData, setSpyData] = useState<SpyPrice | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // WebSocketでリアルタイム更新
  const { spyPrice: liveSpyPrice, priceChange, isConnected: wsConnected } = useSpyPrice();
  const { fxRate: liveFxRate } = useFxRate();

  // 初回データ取得
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        const [health, account, spy] = await Promise.all([
          getHealth(),
          getAccountSummary(),
          getSpyPrice(),
        ]);

        setHealthData({
          ibkr_connected: health.ibkr_connected,
          mode: health.mode as 'mock' | 'real',
        });
        setAccountData(account);
        setSpyData(spy);
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

  // 定期更新（口座情報のみ、30秒ごと）
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [health, account] = await Promise.all([
          getHealth(),
          getAccountSummary(),
        ]);

        setHealthData({
          ibkr_connected: health.ibkr_connected,
          mode: health.mode as 'mock' | 'real',
        });
        setAccountData(account);
      } catch (err) {
        console.error('Failed to refresh data:', err);
      }
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-screen flex flex-col">
      <Header
        ibkrConnected={healthData?.ibkr_connected ?? false}
        mode={healthData?.mode ?? 'mock'}
      />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar currentPage="dashboard" />

        <main className="flex-1 overflow-auto p-6">
          {error ? (
            <div className="card bg-accent-danger/10 border-accent-danger text-accent-danger">
              <h3 className="font-semibold mb-2">エラー</h3>
              <p>{error}</p>
              <p className="text-sm mt-2">バックエンドが起動しているか確認してください。</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* 左カラム: 口座情報 */}
              <div className="lg:col-span-2">
                <AccountCard data={accountData} loading={loading} />
              </div>

              {/* 右カラム: SPY価格 + 戦略パラメータ */}
              <div className="space-y-6">
                <SpyPriceCard
                  data={spyData}
                  loading={loading}
                  priceChange={priceChange}
                  isLive={wsConnected}
                />
                <StrategyCard data={accountData} loading={loading} />
              </div>

              {/* フルワイド: ポジションテーブル（将来実装）*/}
              <div className="lg:col-span-3">
                <div className="card">
                  <h2 className="text-lg font-semibold mb-4">オープンポジション</h2>
                  <div className="text-gray-500 text-center py-8">
                    ポジションがありません
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      <StatusBar
        spyPrice={liveSpyPrice ?? spyData?.last ?? null}
        fxRate={liveFxRate}
      />
    </div>
  );
}

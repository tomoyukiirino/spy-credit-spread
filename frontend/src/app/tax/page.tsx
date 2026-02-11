'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import Sidebar from '@/components/layout/Sidebar';
import StatusBar from '@/components/layout/StatusBar';
import FxRateCard from '@/components/fx/FxRateCard';
import TaxSummary from '@/components/tax/TaxSummary';
import { getHealth } from '@/lib/api';
import { useSpyPrice, useFxRate } from '@/hooks/useWebSocket';
import type { FxRate, TaxSummary as TaxSummaryType, SpyPrice } from '@/types';

export default function TaxPage() {
  const [healthData, setHealthData] = useState<{
    ibkr_connected: boolean;
    mode: 'mock' | 'real';
  } | null>(null);
  const [spyData, setSpyData] = useState<SpyPrice | null>(null);
  const [fxRateData, setFxRateData] = useState<FxRate | null>(null);
  const [taxSummaryData, setTaxSummaryData] = useState<TaxSummaryType | null>(null);
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

        const [health, fxRateRes, taxSummaryRes] = await Promise.all([
          getHealth(),
          fetch('http://localhost:8000/api/fx/rate').then(r => r.json()),
          fetch('http://localhost:8000/api/trades/tax-summary').then(r => r.json()),
        ]);

        setHealthData({
          ibkr_connected: health.ibkr_connected,
          mode: health.mode as 'mock' | 'real',
        });
        setFxRateData(fxRateRes);
        setTaxSummaryData(taxSummaryRes);
      } catch (err) {
        console.error('Failed to fetch data:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  // 為替レート更新
  useEffect(() => {
    if (liveFxRate !== null) {
      setFxRateData({
        usd_jpy: liveFxRate,
        source: 'IBKR',
        timestamp: new Date().toISOString(),
        tts_rate: liveFxRate * 1.01, // 簡易的なTTS計算（実際は1円加算等）
      });
    }
  }, [liveFxRate]);

  const handleRefreshFxRate = async () => {
    try {
      const fxRateRes = await fetch('http://localhost:8000/api/fx/rate').then(r => r.json());
      setFxRateData(fxRateRes);
    } catch (err) {
      console.error('Failed to refresh FX rate:', err);
      alert('為替レートの更新に失敗しました');
    }
  };

  const handleManualUpdateFxRate = async (rate: number) => {
    try {
      const response = await fetch('http://localhost:8000/api/fx/rate/manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ usd_jpy: rate }),
      });

      if (!response.ok) {
        throw new Error('Failed to update FX rate');
      }

      const fxRateRes = await response.json();
      setFxRateData(fxRateRes);
      alert('為替レートを更新しました');
    } catch (err) {
      console.error('Failed to update FX rate:', err);
      alert('為替レートの更新に失敗しました');
    }
  };

  const handleExportTaxCsv = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/trades/export-tax-csv');

      if (!response.ok) {
        throw new Error('Failed to export CSV');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const year = taxSummaryData?.year ?? new Date().getFullYear();
      a.download = `tax_report_${year}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      alert('税務申告用CSVファイルをダウンロードしました');
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
        <Sidebar currentPage="tax" />

        <main className="flex-1 overflow-auto p-6">
          {error ? (
            <div className="card bg-accent-danger/10 border-accent-danger text-accent-danger">
              <h3 className="font-semibold mb-2">エラー</h3>
              <p>{error}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* 左カラム: 税務サマリー */}
              <div className="lg:col-span-2">
                <TaxSummary
                  data={taxSummaryData}
                  loading={loading}
                  onExportCsv={handleExportTaxCsv}
                />
              </div>

              {/* 右カラム: 為替レート */}
              <div>
                <FxRateCard
                  data={fxRateData}
                  loading={loading}
                  onRefresh={handleRefreshFxRate}
                  onManualUpdate={handleManualUpdateFxRate}
                />
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

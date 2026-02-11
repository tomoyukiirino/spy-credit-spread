'use client';

import { useState } from 'react';
import { DollarSign, RefreshCw, Edit3, Check, X } from 'lucide-react';
import type { FxRate } from '@/types';

interface FxRateCardProps {
  data: FxRate | null;
  loading?: boolean;
  onRefresh?: () => void;
  onManualUpdate?: (rate: number) => void;
}

export default function FxRateCard({ data, loading, onRefresh, onManualUpdate }: FxRateCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [manualRate, setManualRate] = useState('');

  const handleStartEdit = () => {
    setManualRate(data?.usd_jpy?.toString() ?? '');
    setIsEditing(true);
  };

  const handleSaveEdit = () => {
    const rate = parseFloat(manualRate);
    if (!isNaN(rate) && rate > 0) {
      onManualUpdate?.(rate);
      setIsEditing(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setManualRate('');
  };

  const getSourceBadge = (source: string) => {
    switch (source) {
      case 'IBKR':
        return <span className="badge badge-success">IBKR API</span>;
      case 'API':
        return <span className="badge bg-blue-500/20 text-blue-400">外部API</span>;
      case 'manual':
        return <span className="badge badge-warning">手動設定</span>;
      default:
        return <span className="badge bg-gray-500/20 text-gray-400">{source}</span>;
    }
  };

  if (loading) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <DollarSign size={20} className="text-accent-warning" />
          USD/JPY 為替レート
        </h2>
        <div className="text-gray-500">読み込み中...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <DollarSign size={20} className="text-accent-warning" />
          USD/JPY 為替レート
        </h2>
        <div className="text-gray-500">データがありません</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <DollarSign size={20} className="text-accent-warning" />
          USD/JPY 為替レート
        </h2>
        <div className="flex items-center gap-2">
          {getSourceBadge(data.source)}
          {onRefresh && !isEditing && (
            <button
              onClick={onRefresh}
              className="p-2 hover:bg-dark-hover rounded-lg transition-colors"
              title="更新"
            >
              <RefreshCw size={16} className="text-gray-400" />
            </button>
          )}
          {onManualUpdate && !isEditing && (
            <button
              onClick={handleStartEdit}
              className="p-2 hover:bg-dark-hover rounded-lg transition-colors"
              title="手動設定"
            >
              <Edit3 size={16} className="text-gray-400" />
            </button>
          )}
        </div>
      </div>

      <div className="space-y-4">
        {/* 為替レート表示・編集 */}
        <div>
          <div className="text-sm text-gray-400 mb-2">実勢レート</div>
          {isEditing ? (
            <div className="flex items-center gap-2">
              <div className="flex-1 flex items-center bg-dark-surface rounded-lg px-3 py-2">
                <span className="text-gray-400 mr-2">¥</span>
                <input
                  type="number"
                  value={manualRate}
                  onChange={(e) => setManualRate(e.target.value)}
                  className="flex-1 bg-transparent border-none outline-none text-2xl font-mono font-bold"
                  placeholder="152.34"
                  step="0.01"
                  autoFocus
                />
              </div>
              <button
                onClick={handleSaveEdit}
                className="p-2 bg-accent-success hover:bg-accent-success/80 rounded-lg transition-colors"
                title="保存"
              >
                <Check size={20} className="text-white" />
              </button>
              <button
                onClick={handleCancelEdit}
                className="p-2 bg-dark-hover hover:bg-dark-border rounded-lg transition-colors"
                title="キャンセル"
              >
                <X size={20} className="text-gray-400" />
              </button>
            </div>
          ) : (
            <div className="text-4xl font-bold font-mono">
              ¥{data.usd_jpy.toFixed(2)}
            </div>
          )}
        </div>

        {/* TTSレート */}
        {data.tts_rate && (
          <div className="pt-4 border-t border-dark-border">
            <div className="text-sm text-gray-400 mb-1">TTSレート（参考）</div>
            <div className="text-2xl font-mono font-bold text-gray-300">
              ¥{data.tts_rate.toFixed(2)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              三菱UFJ対顧客電信売相場（参考値）
            </div>
          </div>
        )}

        {/* タイムスタンプ */}
        <div className="pt-3 border-t border-dark-border">
          <div className="text-xs text-gray-500">
            更新日時: {new Date(data.timestamp).toLocaleString('ja-JP', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            })}
          </div>
        </div>

        {/* 説明 */}
        <div className="pt-3 border-t border-dark-border">
          <div className="text-xs text-gray-400">
            <p className="mb-1">📌 為替レート取得順序:</p>
            <ol className="list-decimal list-inside space-y-1 ml-2">
              <li>IBKR API（USD.JPY Forexペア）</li>
              <li>外部為替API（フォールバック）</li>
              <li>前営業日のログ（フォールバック）</li>
              <li>手動入力（全て失敗時）</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}
